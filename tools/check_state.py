"""Run hot-turn or full-boundary sanity checks over a RePoG Lite campaign."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_FILES = [
    "setup_profile.yaml",
    "world.md",
    "research_dossier.md",
    "next_act_prep.md",
    "boundaries.md",
    "appearance_guide.md",
    "visual_style.md",
    "visual_gallery.md",
    "storytelling.md",
    "knowledge_boundaries.md",
    "opening_brief.md",
    "player.md",
    "player_ties.md",
    "current_state.yaml",
    "threads.md",
    "session_log.md",
    "rules.md",
]

RECOMMENDED_FILES = [
    "world_dynamics.md",
    "style_state.json",
]

HOT_REQUIRED_FILES = [
    "setup_profile.yaml",
    "current_state.yaml",
    "active_cast.md",
    "location_graph.md",
    "relationship_map.md",
    "session_brief.md",
    "knowledge_boundaries.md",
    "session_log.md",
]

V2_FILES = [
    "active_cast.md",
    "location_graph.md",
    "relationship_map.md",
    "session_brief.md",
]

REQUIRED_DIRS = [
    "characters",
    "places",
    "factions",
    "visuals",
    "visuals/characters",
    "visuals/places",
    "visuals/factions",
    "visuals/items",
    "visuals/scenes",
    "visuals/_drafts",
    "snapshots",
]

TOP_LEVEL_KEYS = [
    "campaign_id",
    "mode",
    "status",
    "persistence",
    "player",
    "current_scene",
    "inventory",
    "conditions",
    "active_clocks",
    "active_threats",
    "notes_for_next_turn",
]

PLAYER_KEYS = [
    "name",
    "concept",
    "level_band",
    "condition",
    "current_goal",
    "stats",
    "capabilities",
]

SCENE_KEYS = [
    "title",
    "location",
    "summary",
    "present_npcs",
    "immediate_pressure",
    "open_choices",
]

STAT_COUNT = 8
STAT_MIN = 1
STAT_MAX = 5
FACTION_CAPABILITY_COUNT = 7

IMPORTANT_TIERS = {"t2", "t3"}
SETUP_PACKS = {
    "character_foundation",
    "group",
    "world_fabric",
    "location_network",
    "faction_information",
    "campaign_architecture",
    "mechanics_progression",
    "source_grounding",
}
TURN_PROTOCOL_PRESETS = {
    "fast": {
        "cold_distill_policy": "scene_or_5_durable",
        "validation_policy": "hot_each_durable_full_on_distill",
        "dashboard_refresh_policy": "scene_and_major_visible_change",
        "style_review_policy": "sampled_and_distill",
    },
    "balanced": {
        "cold_distill_policy": "scene_or_3_durable",
        "validation_policy": "hot_each_durable_full_on_distill",
        "dashboard_refresh_policy": "every_visible_change",
        "style_review_policy": "every_2_durable_and_distill",
    },
    "maximum_continuity": {
        "cold_distill_policy": "every_durable",
        "validation_policy": "full_each_durable",
        "dashboard_refresh_policy": "every_visible_change",
        "style_review_policy": "every_durable",
    },
}
TURN_PROTOCOLS = set(TURN_PROTOCOL_PRESETS) | {"custom"}
COLD_DISTILL_POLICIES = {
    "every_durable",
    "scene_or_3_durable",
    "scene_or_5_durable",
    "scene_only",
}
VALIDATION_POLICIES = {
    "hot_each_durable_full_on_distill",
    "full_each_durable",
}
DASHBOARD_REFRESH_POLICIES = {
    "scene_and_major_visible_change",
    "every_visible_change",
    "scene_only",
    "manual",
}
STYLE_REVIEW_POLICIES = {
    "sampled_and_distill",
    "every_2_durable_and_distill",
    "every_durable",
}
LATENCY_NOTICE_POLICIES = {"exceptional_only", "always", "off"}
DIFFICULTY_VALUES = {"trivial", "routine", "challenging", "hard", "extreme"}
HIGH_POWER_WORDS = {
    "elite",
    "regional",
    "legendary",
    "endgame",
    "major",
    "exceptional",
    "world",
}

LEVEL_BUDGETS = {
    "beginner": (16, 3),
    "local_rookie": (16, 3),
    "local_rookie_beginner": (16, 3),
    "competent": (20, 4),
    "rising": (20, 4),
    "rising_rookie": (20, 4),
    "rising_competent": (20, 4),
    "advanced": (24, 4),
    "notorious": (24, 4),
    "notorious_rookie": (24, 4),
    "notorious_advanced": (24, 4),
    "elite": (28, 5),
    "veteran": (28, 5),
    "veteran_elite": (28, 5),
}


def _add(findings: list[dict], severity: str, rule: str, message: str, path: Path | None = None) -> None:
    findings.append(
        {
            "severity": severity,
            "rule": rule,
            "message": message,
            "path": str(path) if path else None,
        }
    )


def _read(path: Path, findings: list[dict]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        _add(findings, "error", "read_failed", str(exc), path)
        return ""


def _clean_scalar(value: str) -> str:
    return value.strip().strip("'\"")


def _yaml_list(value: str) -> list[str]:
    value = value.strip()
    if value == "[]" or not value:
        return []
    if not (value.startswith("[") and value.endswith("]")):
        return []
    return [_clean_scalar(item) for item in value[1:-1].split(",") if _clean_scalar(item)]


def _check_setup_profile(campaign_path: Path, findings: list[dict]) -> None:
    path = campaign_path / "setup_profile.yaml"
    if not path.is_file():
        return
    text = _read(path, findings)
    values = _top_level_values(text)
    status = _clean_scalar(values.get("status", ""))
    mode = _clean_scalar(values.get("session_zero_mode", ""))
    ready = _clean_scalar(values.get("ready_for_play", "false")).lower() == "true"
    workspace_mode = _clean_scalar(values.get("workspace_mode", ""))
    activated = set(_yaml_list(values.get("activated_packs", "[]")))
    completed = set(_yaml_list(values.get("completed_packs", "[]")))
    defaulted = set(_yaml_list(values.get("defaulted_packs", "[]")))
    turn_protocol = _clean_scalar(values.get("turn_protocol", ""))
    cold_policy = _clean_scalar(values.get("cold_distill_policy", ""))
    validation_policy = _clean_scalar(values.get("validation_policy", ""))
    dashboard_policy = _clean_scalar(values.get("dashboard_refresh_policy", ""))
    style_policy = _clean_scalar(values.get("style_review_policy", ""))
    latency_policy = _clean_scalar(values.get("latency_notice_policy", ""))
    estimate_value = _clean_scalar(values.get("performance_estimate_acknowledged", "false")).lower()
    estimate_acknowledged = estimate_value == "true"

    try:
        schema_version = int(_clean_scalar(values.get("schema_version", "0")))
        questions_completed = int(_clean_scalar(values.get("questions_completed", "-1")))
        last_checkpoint = int(_clean_scalar(values.get("last_checkpoint", "-1")))
    except ValueError:
        schema_version = questions_completed = last_checkpoint = -1
        _add(findings, "error", "setup_number_invalid", "Setup numeric fields must be integers.", path)

    if schema_version not in {1, 2}:
        _add(findings, "error", "setup_schema_invalid", "setup_profile schema_version must be 1 or 2.", path)
    if questions_completed < 0 or last_checkpoint < 0 or last_checkpoint > questions_completed:
        _add(findings, "error", "setup_progress_invalid", "Question and checkpoint progress is inconsistent.", path)
    unknown_packs = (activated | completed) - SETUP_PACKS
    if unknown_packs:
        _add(findings, "error", "setup_pack_invalid", f"Unknown setup packs: {', '.join(sorted(unknown_packs))}", path)

    if workspace_mode not in {"standalone", "repository"}:
        _add(findings, "error", "setup_workspace_mode_invalid", "workspace_mode must be standalone or repository.", path)
    if status not in {"pending", "in_progress", "complete"}:
        _add(findings, "error", "setup_status_invalid", "status must be pending, in_progress, or complete.", path)
    if status == "pending" and mode:
        _add(findings, "error", "setup_pending_has_mode", "A pending profile must not preselect Session 0 depth.", path)
    if status != "pending" and mode not in {"quick", "standard", "deep"}:
        _add(findings, "error", "setup_mode_invalid", "Choose quick, standard, or deep before setup continues.", path)
    if ready and status != "complete":
        _add(findings, "error", "setup_ready_mismatch", "ready_for_play requires status: complete.", path)
    if status == "complete" and not ready:
        _add(findings, "error", "setup_ready_mismatch", "Completed Session 0 must set ready_for_play: true.", path)
    session_zero = campaign_path / "session_zero.md"
    if ready and session_zero.is_file() and re.search(r"(?im)^- .+: open\s*$", _read(session_zero, findings)):
        _add(findings, "error", "setup_modules_open", "ready_for_play cannot be true while Session 0 modules remain open.", session_zero)
    if mode == "deep" and not activated <= (completed | defaulted):
        missing = ", ".join(sorted(activated - completed - defaulted))
        _add(findings, "error", "deep_pack_incomplete", f"Activated Deep packs remain unresolved: {missing}", path)
    if mode == "quick" and status == "complete" and not defaulted:
        _add(findings, "error", "quick_defaults_missing", "Completed Quick setup must record visible defaults.", path)

    if schema_version == 1:
        _add(
            findings,
            "info",
            "turn_protocol_legacy",
            "Legacy setup has no Turn Protocol; preserve its existing full-update behavior until a safe OOC migration.",
            path,
        )
        return

    if estimate_value not in {"true", "false"}:
        _add(
            findings,
            "error",
            "performance_ack_invalid",
            "performance_estimate_acknowledged must be true or false.",
            path,
        )
    if latency_policy not in LATENCY_NOTICE_POLICIES:
        _add(
            findings,
            "error",
            "latency_notice_policy_invalid",
            "latency_notice_policy must be exceptional_only, always, or off.",
            path,
        )
    if turn_protocol and turn_protocol not in TURN_PROTOCOLS:
        _add(
            findings,
            "error",
            "turn_protocol_invalid",
            "turn_protocol must be fast, balanced, maximum_continuity, or custom.",
            path,
        )
    if ready and not turn_protocol:
        _add(findings, "error", "turn_protocol_missing", "Ready campaigns must select a Turn Protocol.", path)
    if ready and not estimate_acknowledged:
        _add(
            findings,
            "error",
            "performance_estimate_unacknowledged",
            "Ready campaigns must acknowledge the displayed timing estimates and caveat.",
            path,
        )

    policy_values = {
        "cold_distill_policy": (cold_policy, COLD_DISTILL_POLICIES),
        "validation_policy": (validation_policy, VALIDATION_POLICIES),
        "dashboard_refresh_policy": (dashboard_policy, DASHBOARD_REFRESH_POLICIES),
        "style_review_policy": (style_policy, STYLE_REVIEW_POLICIES),
    }
    if turn_protocol:
        for field, (value, allowed) in policy_values.items():
            if not value:
                _add(findings, "error", "turn_policy_missing", f"{field} must be materialized after profile selection.", path)
            elif value not in allowed:
                _add(findings, "error", "turn_policy_invalid", f"Invalid {field}: {value}", path)

    expected = TURN_PROTOCOL_PRESETS.get(turn_protocol)
    if expected:
        actual = {
            "cold_distill_policy": cold_policy,
            "validation_policy": validation_policy,
            "dashboard_refresh_policy": dashboard_policy,
            "style_review_policy": style_policy,
        }
        for field, expected_value in expected.items():
            if actual[field] and actual[field] != expected_value:
                _add(
                    findings,
                    "error",
                    "turn_preset_mismatch",
                    f"{turn_protocol} requires {field}: {expected_value}.",
                    path,
                )

    if ready:
        system_fit_path = campaign_path / "system_fit.md"
        session_zero_path = campaign_path / "session_zero.md"
        system_fit = _read(system_fit_path, findings) if system_fit_path.is_file() else ""
        session_zero = _read(session_zero_path, findings) if session_zero_path.is_file() else ""
        profile_pattern = rf"(?im)^-\s+Profile:\s*`?{re.escape(turn_protocol)}`?\s*$"
        summary_pattern = rf"(?im)^-\s+Turn protocol:\s*`?{re.escape(turn_protocol)}`?\s*$"
        if not re.search(profile_pattern, system_fit):
            _add(findings, "error", "turn_profile_summary_missing", "system_fit.md does not mirror the selected Turn Protocol.", system_fit_path)
        if not re.search(summary_pattern, session_zero):
            _add(findings, "error", "turn_profile_summary_missing", "session_zero.md does not mirror the selected Turn Protocol.", session_zero_path)
        if not re.search(r"(?im)^-\s+Estimate caveat acknowledged:\s*(yes|true)\s*$", system_fit):
            _add(findings, "error", "performance_ack_summary_missing", "system_fit.md does not record the timing-estimate acknowledgement.", system_fit_path)
        if not re.search(r"(?im)^-\s+Performance estimate acknowledged:\s*(yes|true)\s*$", session_zero):
            _add(findings, "error", "performance_ack_summary_missing", "session_zero.md does not record the timing-estimate acknowledgement.", session_zero_path)


def _check_visual_handoff(campaign_path: Path, findings: list[dict]) -> None:
    visual_path = campaign_path / "visual_style.md"
    if not visual_path.is_file():
        return
    visual_text = _read(visual_path, findings)
    pending = bool(re.search(r"(?im)^- Pending visual review:\s*(yes|true)\s*$", visual_text))
    dashboard_requested = bool(
        re.search(r"(?im)^- Dashboard placement requested:\s*(yes|true)\s*$", visual_text)
    )
    dashboard_completed = bool(
        re.search(r"(?im)^- Dashboard placement completed:\s*(yes|true)\s*$", visual_text)
    )
    setup_path = campaign_path / "setup_profile.yaml"
    setup_text = _read(setup_path, findings) if setup_path.is_file() else ""
    ready = _clean_scalar(_top_level_values(setup_text).get("ready_for_play", "false")).lower() == "true"
    if pending and ready:
        _add(
            findings,
            "error",
            "visual_review_pending_at_play",
            "Session 0 cannot be ready for play while a visual review is pending.",
            visual_path,
        )
    if dashboard_requested and not dashboard_completed and not pending:
        _add(
            findings,
            "warning",
            "visual_dashboard_handoff_incomplete",
            "Accepted visual placement was requested but is not recorded as complete.",
            visual_path,
        )


def _top_level_values(yaml_text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in yaml_text.splitlines():
        if line.startswith(" ") or not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip()
    return values


def _block(yaml_text: str, key: str) -> str:
    lines = yaml_text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if re.match(rf"^{re.escape(key)}:\s*$", line):
            start = index + 1
            break
    if start is None:
        return ""

    block_lines: list[str] = []
    for line in lines[start:]:
        if line and not line.startswith(" ") and re.match(r"^[A-Za-z_][A-Za-z0-9_-]*:", line):
            break
        block_lines.append(line)
    return "\n".join(block_lines)


def _nested_values(block_text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in block_text.splitlines():
        match = re.match(r"^\s{2}([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip()
    return values


def _nested_mapping(block_text: str, key: str) -> dict[str, str]:
    values: dict[str, str] = {}
    lines = block_text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if re.match(rf"^\s{{2}}{re.escape(key)}:\s*$", line):
            start = index + 1
            break
    if start is None:
        return values

    for line in lines[start:]:
        if line and re.match(r"^\s{2}\S", line):
            break
        match = re.match(r"^\s{4}([^:]+):\s*(.*?)\s*$", line)
        if match:
            values[match.group(1).strip()] = _clean_scalar(match.group(2))
    return values


def _parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if not value or value == "[]":
        return []
    if not (value.startswith("[") and value.endswith("]")):
        return []
    inner = value[1:-1].strip()
    if not inner:
        return []
    items = []
    for item in inner.split(","):
        cleaned = item.strip().strip("'\"")
        if cleaned:
            items.append(cleaned)
    return items


def _parse_block_list(yaml_text: str, key: str) -> list[str]:
    lines = yaml_text.splitlines()
    for index, line in enumerate(lines):
        if re.match(rf"^{re.escape(key)}:\s*$", line):
            items: list[str] = []
            for child in lines[index + 1 :]:
                if child and not child.startswith(" "):
                    break
                match = re.match(r"^\s*-\s+(.+?)\s*$", child)
                if match:
                    items.append(match.group(1).strip().strip("'\""))
            return items

        inline = re.match(rf"^{re.escape(key)}:\s*(\[.*\])\s*$", line)
        if inline:
            return _parse_inline_list(inline.group(1))
    return []


def _parse_nested_block_list(yaml_text: str, parent: str, key: str) -> list[str]:
    block = _block(yaml_text, parent)
    lines = block.splitlines()
    for index, line in enumerate(lines):
        inline = re.match(rf"^\s{{2}}{re.escape(key)}:\s*(\[.*\])\s*$", line)
        if inline:
            return _parse_inline_list(inline.group(1))
        if not re.match(rf"^\s{{2}}{re.escape(key)}:\s*$", line):
            continue
        items: list[str] = []
        for child in lines[index + 1 :]:
            if child and re.match(r"^\s{2}\S", child):
                break
            match = re.match(r"^\s{4}-\s+(.+?)\s*$", child)
            if match:
                items.append(_clean_scalar(match.group(1)))
        return items
    return []


def _check_persistence(
    campaign_path: Path,
    state_text: str,
    *,
    revision: int,
    scope: str,
    findings: list[dict],
) -> None:
    setup_path = campaign_path / "setup_profile.yaml"
    setup_text = _read(setup_path, findings) if setup_path.is_file() else ""
    setup_values = _top_level_values(setup_text)
    try:
        setup_schema = int(_clean_scalar(setup_values.get("schema_version", "1")))
    except ValueError:
        setup_schema = 0
    protocol = _clean_scalar(setup_values.get("turn_protocol", ""))
    cold_policy = _clean_scalar(setup_values.get("cold_distill_policy", ""))

    block = _block(state_text, "persistence")
    state_path = campaign_path / "current_state.yaml"
    if not block:
        _add(
            findings,
            "error" if setup_schema >= 2 else "warning",
            "persistence_status_missing",
            "current_state.yaml has no persistence status block.",
            state_path,
        )
        return

    values = _nested_values(block)
    try:
        last_distilled = int(_clean_scalar(values.get("last_distilled_revision", "-1")))
        durable_turns = int(_clean_scalar(values.get("durable_turns_since_distill", "-1")))
    except ValueError:
        _add(findings, "error", "persistence_number_invalid", "Persistence revision and turn fields must be integers.", state_path)
        return

    pending = _parse_nested_block_list(state_text, "persistence", "pending_cold_targets")
    if last_distilled < 0 or last_distilled > revision:
        _add(
            findings,
            "error",
            "persistence_revision_invalid",
            "last_distilled_revision must be between zero and continuity_revision.",
            state_path,
        )
    if durable_turns < 0:
        _add(findings, "error", "persistence_turn_count_invalid", "durable_turns_since_distill cannot be negative.", state_path)
    if len({_slug(item) for item in pending}) != len(pending):
        _add(findings, "error", "persistence_pending_duplicate", "pending_cold_targets must be deduplicated.", state_path)
    if pending and durable_turns == 0:
        _add(findings, "warning", "persistence_pending_without_turn", "Pending cold targets exist while the durable-turn counter is zero.", state_path)

    if protocol and last_distilled >= 0 and durable_turns >= 0:
        expected_turns = revision - last_distilled
        if durable_turns != expected_turns:
            _add(
                findings,
                "error",
                "persistence_counter_mismatch",
                f"durable_turns_since_distill is {durable_turns}, expected {expected_turns} from revisions.",
                state_path,
            )

    threshold = {
        "every_durable": 0,
        "scene_or_3_durable": 3,
        "scene_or_5_durable": 5,
    }.get(cold_policy)
    if threshold is not None and durable_turns > threshold:
        _add(
            findings,
            "error",
            "persistence_distill_overdue",
            f"{cold_policy} allows at most {threshold} undistilled durable turns; found {durable_turns}.",
            state_path,
        )

    log_path = campaign_path / "session_log.md"
    log_text = _read(log_path, findings) if log_path.is_file() else ""
    durable_revision_list = [
        int(value) for value in re.findall(r"(?im)^###\s+Durable Revision\s+(\d+)\s*$", log_text)
    ]
    distilled_revision_list = [
        int(value) for value in re.findall(r"(?im)^###\s+Distilled Through Revision\s+(\d+)\s*$", log_text)
    ]
    durable_revisions = set(durable_revision_list)
    distilled_revisions = set(distilled_revision_list)
    duplicate_events = sorted(
        value for value in durable_revisions if durable_revision_list.count(value) > 1
    )
    if duplicate_events:
        _add(
            findings,
            "error",
            "durable_event_duplicate",
            f"Duplicate durable revision event(s): {', '.join(str(value) for value in duplicate_events)}.",
            log_path,
        )
    future = sorted(value for value in durable_revisions | distilled_revisions if value > revision)
    if future:
        _add(findings, "error", "persistence_log_ahead", f"Session log contains revisions ahead of current state: {future}", log_path)
    if protocol and last_distilled > 0 and last_distilled not in distilled_revisions:
        _add(
            findings,
            "error",
            "distill_marker_missing",
            f"No distilled-through marker records last_distilled_revision {last_distilled}.",
            log_path,
        )
    if protocol and revision > last_distilled:
        missing = sorted(set(range(last_distilled + 1, revision + 1)) - durable_revisions)
        if missing:
            _add(
                findings,
                "error",
                "durable_event_missing",
                f"Missing durable revision event(s): {', '.join(str(value) for value in missing)}.",
                log_path,
            )

    if scope == "full" and (pending or durable_turns > 0):
        arc_path = campaign_path / "arc_closure.md"
        arc_text = _read(arc_path, findings) if arc_path.is_file() else ""
        if re.search(r"(?im)^-\s+Fiction continuation locked until advancement:\s*yes\s*$", arc_text):
            _add(
                findings,
                "error",
                "pending_cold_at_advancement",
                "Pending cold work must be distilled before an advancement-locked continuation.",
                state_path,
            )


def _slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def _normalize_level(value: str) -> str:
    return _slug(value.replace("/", " "))


def _campaign_recommended_max(level_band: str) -> int | None:
    budget = LEVEL_BUDGETS.get(_normalize_level(level_band))
    if budget is None:
        return None
    return budget[1]


def _note_exists(folder: Path, value: str) -> bool:
    if not value:
        return False
    slug = _slug(value)
    for path in folder.glob("*.md"):
        if path.name.startswith("_"):
            continue
        stem = _slug(path.stem)
        if stem == slug or slug in stem or stem in slug:
            return True
        try:
            text = path.read_text(encoding="utf-8").lower()
        except OSError:
            continue
        if value.lower() in text:
            return True
    return False


def _markdown_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(path for path in folder.glob("*.md") if not path.name.startswith("_"))


def _markdown_field(text: str, field_name: str) -> str:
    match = re.search(rf"(?im)^\s*{re.escape(field_name)}:\s*(.*?)\s*$", text)
    return _clean_scalar(match.group(1)) if match else ""


def _markdown_section(text: str, heading: str, level: int = 2) -> str:
    heading_marks = "#" * level
    pattern = re.compile(rf"(?im)^{re.escape(heading_marks)}\s+{re.escape(heading)}\s*$")
    match = pattern.search(text)
    if not match:
        return ""

    start = match.end()
    next_heading = re.search(rf"(?m)^#{{1,{level}}}\s+", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def _markdown_key_values(section_text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in section_text.splitlines():
        match = re.match(r"^\s*-\s+([^:]+):\s*(.*?)\s*$", line)
        if match:
            values[match.group(1).strip()] = _clean_scalar(match.group(2))
    return values


def _meaningful_text(section_text: str) -> str:
    meaningful_lines: list[str] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            meaningful_lines.append(stripped)
    return " ".join(meaningful_lines).strip()


def _markdown_table(text: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return []
    headers = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        row = dict(zip(headers, cells))
        if any(value for value in row.values()):
            rows.append(row)
    return rows


def _markdown_revision(text: str, label: str) -> int | None:
    match = re.search(rf"(?im)^{re.escape(label)}:\s*(\d+)\s*$", text)
    return int(match.group(1)) if match else None


def _entity_tier(folder: Path, name: str) -> str:
    slug = _slug(name)
    for path in _markdown_files(folder):
        text = path.read_text(encoding="utf-8")
        title = re.search(r"(?m)^#\s+(.+?)\s*$", text)
        if _slug(path.stem) == slug or (title and _slug(title.group(1)) == slug):
            return _slug(_markdown_field(text, "Tier"))
    return ""


def _ledger_contains(campaign_path: Path, name: str) -> bool:
    path = campaign_path / "creation_ledger.md"
    if not path.is_file():
        return False
    return bool(re.search(rf"(?im)^-\s+{re.escape(name)}(?:\s|:|/)", path.read_text(encoding="utf-8")))


def _check_dashboard(campaign_path: Path, findings: list[dict]) -> None:
    dashboard_dir = campaign_path / "dashboard"
    if not dashboard_dir.exists():
        return
    if not dashboard_dir.is_dir():
        _add(findings, "error", "dashboard_not_directory", "dashboard exists but is not a directory.", dashboard_dir)
        return
    index_path = dashboard_dir / "index.html"
    state_path = dashboard_dir / "dashboard_state.json"
    assets_path = dashboard_dir / "assets"
    if not index_path.is_file():
        _add(findings, "error", "dashboard_index_missing", "dashboard/index.html is missing.", index_path)
    if not assets_path.is_dir():
        _add(findings, "warning", "dashboard_assets_missing", "dashboard/assets directory is missing.", assets_path)
    if not state_path.is_file():
        _add(findings, "error", "dashboard_state_missing", "dashboard/dashboard_state.json is missing.", state_path)
        return
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _add(findings, "error", "dashboard_state_invalid", f"Dashboard state is not valid JSON: {exc}", state_path)
        return
    if not isinstance(state, dict):
        _add(findings, "error", "dashboard_state_not_object", "Dashboard state should be a JSON object.", state_path)
        return
    for key in ("schema_version", "campaign", "scene", "player", "map", "visuals"):
        if key not in state:
            _add(findings, "warning", "dashboard_key_missing", f"Dashboard state missing key: {key}", state_path)


def _validate_numeric_map(
    findings: list[dict],
    path: Path,
    values: dict[str, str],
    *,
    context: str,
    expected_count: int | None = None,
) -> dict[str, int]:
    if expected_count is not None and len(values) != expected_count:
        _add(
            findings,
            "warning",
            "mechanic_stat_count",
            f"{context} should contain {expected_count} numeric entries; found {len(values)}.",
            path,
        )

    parsed: dict[str, int] = {}
    for name, raw_value in values.items():
        if not raw_value:
            _add(findings, "warning", "mechanic_stat_blank", f"{context} has blank stat/capability: {name}", path)
            continue

        try:
            value = int(raw_value)
        except ValueError:
            _add(findings, "error", "mechanic_stat_not_integer", f"{context} is not an integer: {name}", path)
            continue

        parsed[name] = value
        if value < STAT_MIN or value > STAT_MAX:
            _add(
                findings,
                "error",
                "mechanic_stat_out_of_range",
                f"{context} {name}={value} is outside {STAT_MIN}-{STAT_MAX}.",
                path,
            )

    return parsed


def _check_early_stage_power(
    findings: list[dict],
    path: Path,
    parsed: dict[str, int],
    *,
    context: str,
    tier: str,
    power_band: str,
    level_band: str,
) -> None:
    recommended_max = _campaign_recommended_max(level_band)
    if recommended_max is None or recommended_max >= STAT_MAX:
        return

    band_text = power_band.lower()
    high_power_justified = any(word in band_text for word in HIGH_POWER_WORDS)
    high_stats = sorted(name for name, value in parsed.items() if value > recommended_max)
    elite_stats = sorted(name for name, value in parsed.items() if value >= STAT_MAX)

    if tier == "t2" and high_stats and not high_power_justified:
        _add(
            findings,
            "warning",
            "early_stage_power_spike",
            f"{context} has stats above the {level_band} recommended max without a high-power band: {', '.join(high_stats)}.",
            path,
        )

    if elite_stats and not high_power_justified:
        _add(
            findings,
            "warning",
            "elite_stat_without_power_band",
            f"{context} has elite stat value(s) without an elite/regional/legendary power band: {', '.join(elite_stats)}.",
            path,
        )

    if level_band and _normalize_level(level_band) in {"beginner", "local_rookie", "local_rookie_beginner"}:
        very_high_count = sum(1 for value in parsed.values() if value >= 4)
        if very_high_count > 1 and not high_power_justified:
            _add(
                findings,
                "warning",
                "early_stage_power_inflation",
                f"{context} has {very_high_count} stats at 4+ in a beginner-stage campaign without a high-power band.",
                path,
            )


def _check_character_notes(campaign_path: Path, level_band: str, findings: list[dict]) -> None:
    for path in _markdown_files(campaign_path / "characters"):
        text = _read(path, findings)
        tier = _slug(_markdown_field(text, "Tier"))
        if tier not in IMPORTANT_TIERS:
            continue

        power_band = _markdown_field(text, "Power Band")
        if not power_band:
            _add(findings, "warning", "character_power_band_missing", "T2+ character is missing Power Band.", path)

        for heading, rule in (
            ("Routine And Availability", "character_routine_missing"),
            ("Current Mundane Agenda", "character_agenda_missing"),
            ("Private Motive", "character_motive_missing"),
            ("Last Meaningful Interaction", "character_last_interaction_missing"),
        ):
            if not _meaningful_text(_markdown_section(text, heading)):
                _add(findings, "warning", rule, f"T2+ character is missing {heading}.", path)

        stats = _markdown_key_values(_markdown_section(text, "Stats"))
        if not stats:
            _add(findings, "warning", "character_stats_missing", "T2+ character is missing a numeric Stats block.", path)
            continue

        parsed = _validate_numeric_map(
            findings,
            path,
            stats,
            context=f"{path.stem} character stats",
            expected_count=STAT_COUNT,
        )
        _check_early_stage_power(
            findings,
            path,
            parsed,
            context=f"{path.stem} character",
            tier=tier,
            power_band=power_band,
            level_band=level_band,
        )


def _obstacle_blocks(section_text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    matches = list(re.finditer(r"(?m)^###\s+(.+?)\s*$", section_text))
    for index, match in enumerate(matches):
        name = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section_text)
        blocks.append((name, section_text[start:end].strip()))
    return blocks


def _check_place_obstacles(campaign_path: Path, findings: list[dict]) -> None:
    for path in _markdown_files(campaign_path / "places"):
        text = _read(path, findings)
        obstacle_section = _markdown_section(text, "Common Obstacles And Difficulties")
        if not obstacle_section:
            continue

        for obstacle_name, block in _obstacle_blocks(obstacle_section):
            if _slug(obstacle_name) == "obstacle_name":
                continue

            values = _markdown_key_values(block)
            relevant_stat = values.get("Relevant stat", "")
            difficulty = values.get("Difficulty", "").lower().rstrip(". ;")

            if not relevant_stat:
                _add(
                    findings,
                    "warning",
                    "obstacle_relevant_stat_missing",
                    f"Obstacle '{obstacle_name}' is missing Relevant stat.",
                    path,
                )

            if not difficulty:
                _add(
                    findings,
                    "warning",
                    "obstacle_difficulty_missing",
                    f"Obstacle '{obstacle_name}' is missing Difficulty.",
                    path,
                )
            elif not any(re.search(rf"\b{re.escape(value)}\b", difficulty) for value in DIFFICULTY_VALUES):
                _add(
                    findings,
                    "error",
                    "obstacle_difficulty_invalid",
                    f"Obstacle '{obstacle_name}' has invalid Difficulty: {difficulty}",
                    path,
                )

            for outcome_key in ("Clean success", "Partial success", "Failure"):
                if not values.get(outcome_key, ""):
                    _add(
                        findings,
                        "warning",
                        "obstacle_outcome_missing",
                        f"Obstacle '{obstacle_name}' is missing {outcome_key}.",
                        path,
                    )


def _check_place_notes(campaign_path: Path, findings: list[dict]) -> None:
    for path in _markdown_files(campaign_path / "places"):
        text = _read(path, findings)
        tier = _slug(_markdown_field(text, "Tier"))
        if tier not in IMPORTANT_TIERS:
            continue
        for heading, rule in (
            ("Baseline Routine", "place_routine_missing"),
            ("Presence Logic", "place_presence_logic_missing"),
        ):
            if not _meaningful_text(_markdown_section(text, heading)):
                _add(findings, "warning", rule, f"T2+ place is missing {heading}.", path)


def _check_faction_notes(campaign_path: Path, level_band: str, findings: list[dict]) -> None:
    for path in _markdown_files(campaign_path / "factions"):
        text = _read(path, findings)
        tier = _slug(_markdown_field(text, "Tier"))
        if tier not in IMPORTANT_TIERS:
            continue

        power_band = _markdown_field(text, "Faction Power Band")
        if not power_band:
            _add(findings, "warning", "faction_power_band_missing", "T2+ faction is missing Faction Power Band.", path)

        for heading, rule in (
            ("Representative Face", "faction_representative_missing"),
            ("Key Places", "faction_key_places_missing"),
            ("Current Move", "faction_current_move_missing"),
            ("Next Move If Ignored", "faction_next_move_missing"),
            ("Pressure Clock Or Escalation", "faction_pressure_missing"),
        ):
            if not _meaningful_text(_markdown_section(text, heading)):
                _add(findings, "warning", rule, f"T2+ faction is missing {heading}.", path)

        profile = _markdown_key_values(_markdown_section(text, "Faction Capability Profile"))
        if not profile:
            _add(
                findings,
                "warning",
                "faction_capability_profile_missing",
                "T2+ faction is missing numeric Faction Capability Profile.",
                path,
            )
        else:
            parsed_profile = _validate_numeric_map(
                findings,
                path,
                profile,
                context=f"{path.stem} faction capability profile",
                expected_count=FACTION_CAPABILITY_COUNT,
            )
            _check_early_stage_power(
                findings,
                path,
                parsed_profile,
                context=f"{path.stem} faction capability profile",
                tier=tier,
                power_band=power_band,
                level_band=level_band,
            )

        typical_stats = _markdown_key_values(_markdown_section(text, "Typical Member Stats"))
        if not typical_stats:
            _add(
                findings,
                "warning",
                "faction_typical_stats_missing",
                "T2+ faction is missing numeric Typical Member Stats.",
                path,
            )
        else:
            parsed_stats = _validate_numeric_map(
                findings,
                path,
                typical_stats,
                context=f"{path.stem} faction typical member stats",
                expected_count=STAT_COUNT,
            )
            _check_early_stage_power(
                findings,
                path,
                parsed_stats,
                context=f"{path.stem} faction typical member",
                tier=tier,
                power_band=power_band,
                level_band=level_band,
            )

        for heading, rule in (
            ("Specialist Stats", "faction_specialist_stats_missing"),
            ("Elite / Leader Stats", "faction_elite_stats_missing"),
        ):
            section_text = _meaningful_text(_markdown_section(text, heading))
            if not section_text or section_text.lower().startswith("what a "):
                _add(findings, "warning", rule, f"T2+ faction is missing {heading}.", path)


def _check_markdown_mechanics(campaign_path: Path, level_band: str, findings: list[dict]) -> None:
    _check_character_notes(campaign_path, level_band, findings)
    _check_place_notes(campaign_path, findings)
    _check_place_obstacles(campaign_path, findings)
    _check_faction_notes(campaign_path, level_band, findings)


def _check_v2_memory(
    campaign_path: Path,
    *,
    revision: int,
    location: str,
    present_npcs: list[str],
    scope: str,
    findings: list[dict],
) -> None:
    active_path = campaign_path / "active_cast.md"
    graph_path = campaign_path / "location_graph.md"
    relationship_path = campaign_path / "relationship_map.md"
    brief_path = campaign_path / "session_brief.md"

    active_text = _read(active_path, findings)
    active_rows = _markdown_table(active_text)
    active_revision = _markdown_revision(active_text, "As of revision")
    if active_revision is None:
        _add(findings, "warning", "active_cast_revision_missing", "Active cast has no revision.", active_path)
    elif scope == "full" and active_revision < revision:
        _add(findings, "warning", "active_cast_stale", f"Active cast revision {active_revision} trails state revision {revision}.", active_path)

    active_by_name = {_slug(row.get("NPC", "")): row for row in active_rows if row.get("NPC") and _slug(row.get("NPC", "")) != "example_npc"}
    for npc in present_npcs:
        tier = _entity_tier(campaign_path / "characters", npc)
        if tier in IMPORTANT_TIERS:
            row = active_by_name.get(_slug(npc))
            if not row:
                _add(findings, "error", "present_important_npc_untracked", f"Present {tier.upper()} NPC has no active cast row: {npc}", active_path)
                continue
            required = ["Current location", "Current activity", "Immediate objective", "Availability", "Reason here", "Next move if ignored"]
            missing = [name for name in required if not row.get(name)]
            if missing:
                _add(findings, "error", "active_cast_presence_incomplete", f"Active cast row for {npc} is missing: {', '.join(missing)}", active_path)
            row_location = row.get("Current location", "")
            if location and row_location and _slug(location) != _slug(row_location):
                _add(findings, "error", "active_cast_location_conflict", f"Present NPC {npc} is tracked at {row_location}, not current location {location}.", active_path)

    graph_text = _read(graph_path, findings)
    graph_rows = _markdown_table(graph_text)
    graph_revision = _markdown_revision(graph_text, "As of revision")
    if scope == "full" and graph_revision is not None and graph_revision < revision:
        _add(findings, "warning", "location_graph_stale", f"Location graph revision {graph_revision} trails state revision {revision}.", graph_path)
    seen_current_location = False
    for row in graph_rows:
        source = row.get("From", "")
        target = row.get("To", "")
        if _slug(source) == "example_place":
            continue
        if row.get("Direction") not in {"<->", "->"}:
            _add(findings, "error", "location_graph_direction_invalid", f"Invalid location graph direction: {row.get('Direction', '')}", graph_path)
        for endpoint in (source, target):
            if endpoint and not _note_exists(campaign_path / "places", endpoint):
                _add(findings, "error", "location_graph_endpoint_missing", f"Location graph endpoint has no place note: {endpoint}", graph_path)
        if _slug(location) in {_slug(source), _slug(target)}:
            seen_current_location = True
    if location and not seen_current_location:
        _add(findings, "error", "current_location_unmapped", f"Current location has no location graph connection: {location}", graph_path)

    relationship_text = _read(relationship_path, findings)
    relationship_rows = _markdown_table(relationship_text)
    seen_pairs: set[tuple[str, str]] = set()
    for row in relationship_rows:
        source = _slug(row.get("From", ""))
        target = _slug(row.get("To", ""))
        if source == "character_a" or not source or not target:
            continue
        pair = (source, target) if row.get("Direction") == "->" else tuple(sorted((source, target)))
        if pair in seen_pairs:
            _add(findings, "error", "relationship_current_duplicate", f"Duplicate current relationship pair: {row.get('From')} / {row.get('To')}", relationship_path)
        seen_pairs.add(pair)

    if scope == "full":
        brief_text = _read(brief_path, findings)
        brief_revision = _markdown_revision(brief_text, "Prepared from revision")
        if brief_revision is None:
            _add(findings, "warning", "session_brief_revision_missing", "Session brief has no source revision.", brief_path)
        elif brief_revision < revision:
            _add(findings, "warning", "session_brief_stale", f"Session brief revision {brief_revision} trails state revision {revision}; current state remains authoritative.", brief_path)

        dynamics_path = campaign_path / "world_dynamics.md"
        if dynamics_path.is_file():
            dynamics_text = _read(dynamics_path, findings)
            if re.search(r"(?im)^-\s+Due:\s+yes\s*$", dynamics_text):
                _add(findings, "warning", "world_domain_due", "A world domain is due for triggered evaluation.", dynamics_path)

    knowledge_path = campaign_path / "knowledge_boundaries.md"
    if knowledge_path.is_file():
        knowledge_text = _read(knowledge_path, findings)
        if re.search(r"(?ims)^##\s+Player And Character Knowledge.*?^\s*-\s+Status:\s+superseded\s*$", knowledge_text):
            _add(findings, "warning", "superseded_active_knowledge", "Superseded fact remains in the active player/character knowledge section.", knowledge_path)

    research_path = campaign_path / "research_dossier.md"
    session_zero_path = campaign_path / "session_zero.md"
    if scope == "full" and research_path.is_file() and session_zero_path.is_file():
        research_text = _read(research_path, findings)
        session_zero_text = _read(session_zero_path, findings)
        if re.search(r"(?im)^-\s+Status:\s+`?needed_pending`?\s*$", research_text):
            locked = re.search(r"(?im)^-\s+(World Truths|Factions):\s+locked\s*$", session_zero_text)
            accepted = re.search(r"(?im)risk acceptance|risk accepted|risk kabul", research_text)
            if locked and not accepted:
                _add(findings, "warning", "research_gate_locked_while_pending", "World truths or factions are locked while research remains pending without explicit risk acceptance.", session_zero_path)


def _check_optional_json_state(campaign_path: Path, findings: list[dict]) -> None:
    for filename in ("style_state.json", "mechanics_state.json"):
        path = campaign_path / filename
        if not path.is_file():
            continue
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            _add(findings, "error", "optional_state_invalid", f"{filename} is not valid JSON: {exc}", path)
            continue
        if not isinstance(state, dict):
            _add(findings, "error", "optional_state_not_object", f"{filename} should be a JSON object.", path)
            continue
        if filename == "style_state.json":
            maximum = state.get("max_history", 8)
            history = state.get("history", [])
            if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 1:
                _add(findings, "error", "style_history_limit_invalid", "style_state max_history must be positive.", path)
            if not isinstance(history, list):
                _add(findings, "error", "style_history_invalid", "style_state history must be a list.", path)
            elif isinstance(maximum, int) and len(history) > maximum:
                _add(findings, "warning", "style_history_too_long", "style_state history exceeds max_history.", path)
            elif any(isinstance(entry, dict) and any(key in entry for key in ("text", "narration", "full_text")) for entry in history):
                _add(findings, "warning", "style_state_full_prose", "style_state should store fingerprints, not full narration.", path)
        else:
            if not isinstance(state.get("enabled"), bool):
                _add(findings, "error", "mechanics_enabled_invalid", "mechanics_state enabled must be boolean.", path)
            revision = state.get("revision")
            if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
                _add(findings, "error", "mechanics_revision_invalid", "mechanics_state revision must be non-negative.", path)
            actors = state.get("actors")
            if not isinstance(actors, dict):
                _add(findings, "error", "mechanics_actors_invalid", "mechanics_state actors must be an object.", path)
                actors = {}
            operations = state.get("applied_operations")
            if not isinstance(operations, list):
                _add(findings, "error", "mechanics_operations_invalid", "applied_operations must be a list.", path)
            elif len(operations) != len(set(value for value in operations if isinstance(value, str))):
                _add(findings, "error", "mechanics_operations_duplicate", "applied_operations contains duplicate ids.", path)
            for actor_id, actor in actors.items():
                if not isinstance(actor, dict):
                    _add(findings, "error", "mechanics_actor_invalid", f"Actor {actor_id} must be an object.", path)
                    continue
                resources = actor.get("resources", {})
                if not isinstance(resources, dict):
                    _add(findings, "error", "mechanics_resources_invalid", f"Actor {actor_id} resources must be an object.", path)
                    continue
                for resource_id, resource in resources.items():
                    if not isinstance(resource, dict):
                        _add(findings, "error", "mechanics_resource_invalid", f"Resource {actor_id}.{resource_id} must be an object.", path)
                        continue
                    values = [resource.get(key) for key in ("minimum", "current", "maximum")]
                    if not all(isinstance(value, int) and not isinstance(value, bool) for value in values):
                        _add(findings, "error", "mechanics_resource_bounds_invalid", f"Resource {actor_id}.{resource_id} needs integer minimum/current/maximum.", path)
                        continue
                    minimum, current, maximum = values
                    if minimum > maximum or not minimum <= current <= maximum:
                        _add(findings, "error", "mechanics_resource_out_of_bounds", f"Resource {actor_id}.{resource_id} is outside its configured bounds.", path)


def _check_player_state(state_text: str, state_path: Path, findings: list[dict]) -> None:
    player_block = _block(state_text, "player")
    if not player_block:
        _add(findings, "error", "player_block_missing", "current_state.yaml is missing player block.", state_path)
        return

    player_values = _nested_values(player_block)
    for key in PLAYER_KEYS:
        if key not in player_values:
            _add(findings, "warning", "player_key_missing", f"Missing player key: {key}", state_path)

    stats = _nested_mapping(player_block, "stats")
    if not stats:
        _add(findings, "error", "player_stats_missing", "player.stats is missing or empty.", state_path)
        return

    if len(stats) != STAT_COUNT:
        _add(
            findings,
            "error",
            "player_stats_count",
            f"player.stats should contain exactly {STAT_COUNT} stats; found {len(stats)}.",
            state_path,
        )

    parsed_stats: dict[str, int] = {}
    for name, raw_value in stats.items():
        try:
            value = int(raw_value)
        except ValueError:
            _add(findings, "error", "player_stat_not_integer", f"Stat is not an integer: {name}", state_path)
            continue

        parsed_stats[name] = value
        if value < STAT_MIN or value > STAT_MAX:
            _add(
                findings,
                "error",
                "player_stat_out_of_range",
                f"Stat {name}={value} is outside {STAT_MIN}-{STAT_MAX}.",
                state_path,
            )

    if not parsed_stats:
        return

    level_band = _clean_scalar(player_values.get("level_band", ""))
    if not level_band:
        _add(findings, "warning", "level_band_missing", "player.level_band is blank.", state_path)
        return

    level_key = _normalize_level(level_band)
    budget = LEVEL_BUDGETS.get(level_key)
    if budget is None:
        _add(
            findings,
            "warning",
            "level_budget_unknown",
            f"No stat budget is known for level_band: {level_band}",
            state_path,
        )
        return

    max_total, recommended_max = budget
    total = sum(parsed_stats.values())
    budget_policy = _clean_scalar(player_values.get("stat_budget_policy", "standard"))
    budget_note = _clean_scalar(player_values.get("stat_budget_note", ""))
    custom_policy = budget_policy == "custom_arc_earned" and bool(budget_note)
    if budget_policy not in {"standard", "custom_arc_earned"}:
        _add(findings, "error", "stat_budget_policy_invalid", f"Unknown stat_budget_policy: {budget_policy}", state_path)
    if budget_policy == "custom_arc_earned" and not budget_note:
        _add(findings, "error", "stat_budget_note_missing", "custom_arc_earned requires stat_budget_note.", state_path)
    if total > max_total:
        _add(
            findings,
            "info" if custom_policy else "warning",
            "stat_budget_custom" if custom_policy else "stat_budget_exceeded",
            f"Stat total {total} exceeds {level_band} budget {max_total}.",
            state_path,
        )

    too_high = sorted(name for name, value in parsed_stats.items() if value > recommended_max)
    for name in too_high:
        _add(
            findings,
            "info" if custom_policy else "warning",
            "stat_level_custom" if custom_policy else "stat_level_max_exceeded",
            f"Stat {name} exceeds recommended max {recommended_max} for {level_band}.",
            state_path,
        )


def check_campaign(campaign_path: Path, *, scope: str = "full") -> dict:
    campaign_path = campaign_path.resolve()
    findings: list[dict] = []

    if scope not in {"hot", "full"}:
        _add(findings, "error", "check_scope_invalid", "scope must be hot or full.", campaign_path)
        return _result(campaign_path, findings, scope=scope)

    if not campaign_path.exists() or not campaign_path.is_dir():
        _add(findings, "error", "campaign_path_not_found", "Campaign path is missing.", campaign_path)
        return _result(campaign_path, findings, scope=scope)

    required_files = REQUIRED_FILES if scope == "full" else HOT_REQUIRED_FILES
    for relative in required_files:
        path = campaign_path / relative
        if not path.is_file():
            _add(findings, "error", "required_file_missing", f"Missing required file: {relative}", path)

    if scope == "full":
        for relative in RECOMMENDED_FILES:
            path = campaign_path / relative
            if not path.is_file():
                _add(findings, "warning", "recommended_file_missing", f"Missing recommended file: {relative}", path)

    required_dirs = REQUIRED_DIRS if scope == "full" else ["characters", "places"]
    for relative in required_dirs:
        path = campaign_path / relative
        if not path.is_dir():
            _add(findings, "error", "required_dir_missing", f"Missing required directory: {relative}", path)

    _check_setup_profile(campaign_path, findings)
    if scope == "full":
        _check_visual_handoff(campaign_path, findings)

        _check_dashboard(campaign_path, findings)
        _check_optional_json_state(campaign_path, findings)

    state_path = campaign_path / "current_state.yaml"
    state_text = _read(state_path, findings) if state_path.is_file() else ""
    if not state_text:
        return _result(campaign_path, findings, scope=scope)

    if re.search("[\\u00c3\\u00c4\\u00c5]", state_text):
        _add(findings, "error", "mojibake", "current_state.yaml contains likely encoding corruption.", state_path)

    top_values = _top_level_values(state_text)
    for key in TOP_LEVEL_KEYS:
        if key not in top_values:
            _add(findings, "warning", "top_level_key_missing", f"Missing top-level key: {key}", state_path)

    mode = _clean_scalar(top_values.get("mode", ""))
    if mode and mode != "lite":
        _add(findings, "error", "wrong_mode", "current_state.yaml mode should be 'lite'.", state_path)

    campaign_id = _clean_scalar(top_values.get("campaign_id", ""))
    if not campaign_id or campaign_id == "replace_me":
        _add(findings, "warning", "campaign_id_placeholder", "Campaign id is still blank or replace_me.", state_path)

    memory_version_raw = _clean_scalar(top_values.get("memory_version", ""))
    revision_raw = _clean_scalar(top_values.get("continuity_revision", ""))
    try:
        memory_version = int(memory_version_raw) if memory_version_raw else 1
    except ValueError:
        memory_version = 0
        _add(findings, "error", "memory_version_invalid", "memory_version must be an integer.", state_path)
    try:
        continuity_revision = int(revision_raw) if revision_raw else 0
    except ValueError:
        continuity_revision = -1
        _add(findings, "error", "continuity_revision_invalid", "continuity_revision must be a non-negative integer.", state_path)
    if continuity_revision < 0:
        _add(findings, "error", "continuity_revision_invalid", "continuity_revision must be a non-negative integer.", state_path)
    if memory_version < 2:
        _add(findings, "warning", "memory_v2_pending", "Campaign has not been migrated to Lite memory V2.", state_path)
    else:
        for relative in V2_FILES:
            path = campaign_path / relative
            if not path.is_file():
                _add(findings, "error", "v2_file_missing", f"Lite V2 requires: {relative}", path)

    if continuity_revision >= 0:
        _check_persistence(
            campaign_path,
            state_text,
            revision=continuity_revision,
            scope=scope,
            findings=findings,
        )

    _check_player_state(state_text, state_path, findings)
    player_values = _nested_values(_block(state_text, "player"))
    level_band = _clean_scalar(player_values.get("level_band", ""))

    scene_values = _nested_values(_block(state_text, "current_scene"))
    for key in SCENE_KEYS:
        if key not in scene_values:
            _add(findings, "warning", "scene_key_missing", f"Missing current_scene key: {key}", state_path)

    location = _clean_scalar(scene_values.get("location", ""))
    if location:
        if not _note_exists(campaign_path / "places", location):
            _add(
                findings,
                "error" if memory_version >= 2 else "warning",
                "location_note_missing",
                f"Current location has no matching place note: {location}",
                campaign_path / "places",
            )
    else:
        _add(findings, "info", "location_blank", "Current location is blank; expected for a fresh template.", state_path)

    present_npcs = _parse_nested_block_list(state_text, "current_scene", "present_npcs")
    for npc in present_npcs:
        if not _note_exists(campaign_path / "characters", npc) and not _ledger_contains(campaign_path, npc):
            _add(
                findings,
                "error" if memory_version >= 2 else "warning",
                "npc_note_missing",
                f"Present NPC has no matching character note: {npc}",
                campaign_path / "characters",
            )

    inventory = _parse_block_list(state_text, "inventory")
    duplicates = sorted({item for item in inventory if inventory.count(item) > 1})
    for item in duplicates:
        _add(findings, "warning", "duplicate_inventory_item", f"Inventory lists duplicate item: {item}", state_path)

    if scope == "full":
        _check_markdown_mechanics(campaign_path, level_band, findings)

    if memory_version >= 2 and all((campaign_path / relative).is_file() for relative in V2_FILES):
        _check_v2_memory(
            campaign_path,
            revision=continuity_revision,
            location=location,
            present_npcs=present_npcs,
            scope=scope,
            findings=findings,
        )

    return _result(campaign_path, findings, scope=scope)


def _result(campaign_path: Path, findings: list[dict], *, scope: str = "full") -> dict:
    error_count = sum(1 for finding in findings if finding["severity"] == "error")
    warning_count = sum(1 for finding in findings if finding["severity"] == "warning")
    info_count = sum(1 for finding in findings if finding["severity"] == "info")
    return {
        "ok": error_count == 0,
        "campaign_path": str(campaign_path),
        "scope": scope,
        "error_count": error_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_path", help="Path to a Lite campaign folder.")
    parser.add_argument(
        "--scope",
        choices=("hot", "full"),
        default="full",
        help="Use hot for per-durable-turn checks or full at distill/audit boundaries.",
    )
    args = parser.parse_args(argv)

    result = check_campaign(Path(args.campaign_path), scope=args.scope)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())

"""Run hot-turn or full-boundary sanity checks over a RePoG Lite campaign."""

from __future__ import annotations

import argparse
import importlib.util
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
        "cold_distill_policy": "scene_checkpoint_or_5_durable",
        "validation_policy": "hot_each_durable_full_on_distill",
        "dashboard_refresh_policy": "scene_and_major_visible_change",
        "style_review_policy": "sampled_and_distill",
    },
    "balanced": {
        "cold_distill_policy": "scene_checkpoint_or_3_durable",
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
LEGACY_TURN_PROTOCOL_PRESETS = {
    "fast": {**TURN_PROTOCOL_PRESETS["fast"], "cold_distill_policy": "scene_or_5_durable"},
    "balanced": {**TURN_PROTOCOL_PRESETS["balanced"], "cold_distill_policy": "scene_or_3_durable"},
    "maximum_continuity": TURN_PROTOCOL_PRESETS["maximum_continuity"],
}
TURN_PROTOCOLS = set(TURN_PROTOCOL_PRESETS) | {"custom"}
COLD_DISTILL_POLICIES = {
    "every_durable",
    "scene_checkpoint_or_3_durable",
    "scene_checkpoint_or_5_durable",
    "scene_checkpoint_only",
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
SETTING_LENSES = {"fantasy", "realistic", "cyberpunk"}
PLAY_LENSES = {"survival"}
MECHANIC_MODULES = {
    "bounded_resources",
    "abilities_costs",
    "strict_consumables",
    "wounds",
    "clocks",
    "dice_resolution",
    "structured_travel",
}
DICE_MODES = {"judgment_only", "player_rolls", "open_gm_rolls", "hidden_gm_rolls", "hybrid"}
RESOLUTION_GROUNDINGS = {"fictional", "bands", "numeric"}
INVENTORY_TRACKING = {"abstract", "quantified", "encumbrance"}
TIME_TRACKING = {"scene", "coarse", "step"}
TRAVEL_TRACKING = {"abstract", "route_time"}
WOUND_TRACKING = {"narrative", "conditions"}
POINTS_OF_VIEW = {"first", "second", "third"}
TENSES = {"present", "past"}
CAMERA_DISTANCES = {"close", "medium", "wide"}
PROSE_DENSITIES = {"lean", "balanced", "lush"}
RESPONSE_LENGTHS = {"brief", "dynamic", "expansive"}
OPTION_PROMPTING = {"natural", "gentle_choices", "tactical_menu"}
DIALOGUE_STYLES = {"plain", "balanced", "heightened"}
DENSITY_VALUES = {"low", "balanced", "high"}
PACING_VALUES = {"dynamic", "deliberate", "urgent"}
INTERIORITY_POLICIES = {"player_owned", "shared_when_invited", "guided"}
DIALOGUE_BALANCES = {"dialogue_forward", "balanced", "narration_forward"}
HUMOR_VALUES = {"minimal", "situational", "frequent"}
EMOTIONAL_DISTANCES = {"close", "moderate", "detached"}
BREATHER_FREQUENCIES = {"sparse", "balanced", "generous"}
BREATHER_EXIT_POLICIES = {
    "player_led",
    "player_led_with_established_triggers",
    "world_led",
}
SCENE_MODES = {"ambient", "focused", "crisis", "aftermath", "transition", "breather"}
ADVANCEMENT_CADENCES = {"none", "session", "scenario", "arc", "campaign"}
ADVANCEMENT_PRESENTATIONS = {"none", "explicit_ooc", "automatic_fictional"}
DASHBOARD_MODES = {"off", "on"}
DASHBOARD_TILES = {
    "setup_progress",
    "scene",
    "character",
    "stats",
    "resources",
    "clocks",
    "conditions",
    "companions",
    "people",
    "threads",
    "clues",
    "inventory",
    "map",
    "gallery",
}
VISUAL_MODES = {"off", "manual_only", "major_only", "curated", "rich"}
VISUAL_PLACEMENTS = {"gallery_only", "dashboard_after_approval"}
RESEARCH_STATUSES = {
    "not_needed",
    "needed_pending",
    "partial_complete",
    "complete",
    "unavailable_risk_accepted",
}
RESEARCH_MODES = {"none", "web", "designer_sources", "mixed", "unavailable"}
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

AGENCY_CARD_FIELDS = (
    "Local role",
    "Independent project",
    "Current mundane task",
    "Pressure decision rule",
    "Misbelief or recurring mistake",
    "Hard boundary",
    "Non-player obligation",
    "Voice rhythm",
    "Social tactic",
    "Routine and availability",
    "Next move if ignored",
    "Evaluation trigger",
    "Visible consequence channel",
    "Offscreen trajectory status",
)
OFFSCREEN_TRAJECTORY_STATUSES = {"inactive", "active", "needs_review"}
OFFSCREEN_TRAJECTORY_FIELDS = (
    "Goal and method",
    "Obstacle or resource",
    "Time horizon",
    "Result shape",
    "Visible channel",
    "Last evaluation id",
)
STYLE_CATEGORICAL_FIELDS = (
    "dramatic_beat",
    "gm_move",
    "ending_form",
    "sensory_channel",
    "complication_type",
    "npc_social_tactic",
    "metaphor_family",
)

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
    return value.strip().strip("'\"`")


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
    activated = set(_parse_block_list(text, "activated_packs"))
    completed = set(_parse_block_list(text, "completed_packs"))
    defaulted = set(_parse_block_list(text, "defaulted_packs"))
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
        setup_revision = int(_clean_scalar(values.get("setup_revision", "0")))
    except ValueError:
        schema_version = questions_completed = last_checkpoint = setup_revision = -1
        _add(findings, "error", "setup_number_invalid", "Setup numeric fields must be integers.", path)

    if schema_version not in {1, 2, 3}:
        _add(findings, "error", "setup_schema_invalid", "setup_profile schema_version must be 1, 2, or 3.", path)
    if questions_completed < 0 or last_checkpoint < 0 or last_checkpoint > questions_completed:
        _add(findings, "error", "setup_progress_invalid", "Question and checkpoint progress is inconsistent.", path)
    if schema_version >= 3 and setup_revision < 0:
        _add(findings, "error", "setup_revision_invalid", "setup_revision must be a non-negative integer.", path)
    unknown_packs = (activated | completed | defaulted) - SETUP_PACKS
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
    resolved_without_activation = (completed | defaulted) - activated
    if resolved_without_activation:
        _add(
            findings,
            "error",
            "setup_pack_not_activated",
            f"Completed/defaulted packs were not activated: {', '.join(sorted(resolved_without_activation))}",
            path,
        )
    if mode == "quick" and status == "complete" and not 6 <= questions_completed <= 8:
        _add(findings, "error", "quick_question_target", "Completed Quick setup must record 6–8 decisions.", path)
    if mode in {"standard", "deep"} and status == "complete" and questions_completed < 17:
        _add(findings, "error", "setup_question_target", "Completed Standard/Deep setup needs at least 17 decisions.", path)
    if mode == "deep" and questions_completed >= 8 and last_checkpoint == 0:
        _add(findings, "warning", "deep_checkpoint_missing", "Deep setup should record a checkpoint after 8–10 decisions.", path)
    for pack, filename in {
        "character_foundation": "character_foundation.md",
        "group": "group.md",
    }.items():
        if pack in completed and not (campaign_path / filename).is_file():
            _add(findings, "error", "deep_pack_output_missing", f"Completed {pack} requires {filename}.", campaign_path / filename)
    if "world_fabric" in completed:
        world_path = campaign_path / "world.md"
        content = _meaningful_text(_markdown_section(_read(world_path, findings), "World Operating Model")) if world_path.is_file() else ""
        if not content or content.lower().startswith("record the"):
            _add(findings, "error", "deep_pack_output_missing", "Completed world_fabric requires a materialized World Operating Model.", world_path)
    if "location_network" in completed:
        graph_path = campaign_path / "location_graph.md"
        graph = _read(graph_path, findings) if graph_path.is_file() else ""
        if not graph or "| Example Place |" in graph or len(_markdown_table(graph)) == 0:
            _add(findings, "error", "deep_pack_output_missing", "Completed location_network requires at least one real graph connection.", graph_path)
    if "faction_information" in completed:
        faction_dir = campaign_path / "factions"
        notes = [item for item in faction_dir.glob("*.md") if not item.name.startswith("_")] if faction_dir.is_dir() else []
        if not notes:
            _add(findings, "error", "deep_pack_output_missing", "Completed faction_information requires at least one campaign faction note.", faction_dir)
    if "campaign_architecture" in completed:
        threads_path = campaign_path / "threads.md"
        threads = _read(threads_path, findings) if threads_path.is_file() else ""
        compass = _markdown_section(threads, "Arc Compass")
        if not _markdown_field(compass, "Dramatic question"):
            _add(findings, "error", "deep_pack_output_missing", "Completed campaign_architecture requires an Arc Compass dramatic question.", threads_path)
    if "source_grounding" in completed:
        dossier_path = campaign_path / "research_dossier.md"
        dossier = _read(dossier_path, findings) if dossier_path.is_file() else ""
        if _markdown_field(dossier, "Status") in {"", "needed_pending"}:
            _add(findings, "error", "deep_pack_output_missing", "Completed source_grounding requires a resolved research gate.", dossier_path)
    if "mechanics_progression" in completed:
        profile_path = campaign_path / "play_profile.yaml"
        profile_text = _read(profile_path, findings) if profile_path.is_file() else ""
        advancement = _nested_values(_block(profile_text, "advancement"))
        if not _clean_scalar(advancement.get("cadence", "")):
            _add(findings, "error", "deep_pack_output_missing", "Completed mechanics_progression requires a materialized advancement cadence.", profile_path)

    # Schema v3 keeps setup progress here and materializes runtime behavior in
    # play_profile.yaml. Legacy v1/v2 campaigns retain their existing checks.
    if schema_version >= 3:
        return

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

    expected = LEGACY_TURN_PROTOCOL_PRESETS.get(turn_protocol)
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


def _setup_status(campaign_path: Path, findings: list[dict]) -> tuple[str, str, bool]:
    path = campaign_path / "setup_profile.yaml"
    if not path.is_file():
        return "", "", False
    values = _top_level_values(_read(path, findings))
    status = _clean_scalar(values.get("status", ""))
    mode = _clean_scalar(values.get("session_zero_mode", ""))
    ready = _boolean(values.get("ready_for_play", "false")) is True
    return status, mode, ready


def _check_play_profile(campaign_path: Path, findings: list[dict]) -> dict[str, object]:
    path = campaign_path / "play_profile.yaml"
    if not path.is_file():
        return {}
    text = _read(path, findings)
    top = _top_level_values(text)
    _, _, ready = _setup_status(campaign_path, findings)
    required = ready

    try:
        schema_version = int(_clean_scalar(top.get("schema_version", "0")))
    except ValueError:
        schema_version = 0
    if schema_version not in {1, 2}:
        _add(findings, "error", "play_profile_schema_invalid", "play_profile schema_version must be 1 or 2.", path)
    elif schema_version == 1:
        _add(
            findings,
            "warning",
            "play_profile_v2_pending",
            "Legacy play_profile schema v1 remains playable; migrate when a snapshot is available.",
            path,
        )

    profile_status = _clean_scalar(top.get("profile_status", ""))
    if profile_status not in {"pending", "locked"}:
        _add(findings, "error", "play_profile_status_invalid", "profile_status must be pending or locked.", path)
    try:
        source_setup_revision = int(_clean_scalar(top.get("source_setup_revision", "-1")))
    except ValueError:
        source_setup_revision = -1
    if source_setup_revision < 0:
        _add(findings, "error", "play_profile_revision_invalid", "source_setup_revision must be a non-negative integer.", path)
    setup_path = campaign_path / "setup_profile.yaml"
    setup_text = _read(setup_path, findings) if setup_path.is_file() else ""
    try:
        setup_revision = int(_clean_scalar(_top_level_values(setup_text).get("setup_revision", "0")))
    except ValueError:
        setup_revision = -1
    if ready and profile_status != "locked":
        _add(findings, "error", "play_profile_not_locked", "Ready play requires profile_status: locked.", path)
    if ready and source_setup_revision != setup_revision:
        _add(
            findings,
            "error",
            "play_profile_revision_stale",
            f"play_profile revision {source_setup_revision} does not match setup revision {setup_revision}.",
            path,
        )

    setting_lenses = _parse_block_list(text, "setting_lenses")
    play_lenses = _parse_block_list(text, "play_lenses")
    invalid_setting = sorted(value for value in setting_lenses if not _valid_lens(value, SETTING_LENSES))
    invalid_play = sorted(value for value in play_lenses if not _valid_lens(value, PLAY_LENSES))
    if invalid_setting:
        _add(findings, "error", "setting_lens_invalid", f"Unknown setting lens: {', '.join(invalid_setting)}", path)
    if invalid_play:
        _add(findings, "error", "play_lens_invalid", f"Unknown play lens: {', '.join(invalid_play)}", path)
    if len(setting_lenses) != len(set(setting_lenses)) or len(play_lenses) != len(set(play_lenses)):
        _add(findings, "error", "play_lens_duplicate", "Lens lists must be deduplicated.", path)

    mechanics = _nested_values(_block(text, "mechanics"))
    modules = _parse_nested_block_list(text, "mechanics", "modules")
    unknown_modules = sorted(set(modules) - MECHANIC_MODULES)
    if unknown_modules:
        _add(findings, "error", "mechanic_module_invalid", f"Unknown mechanic modules: {', '.join(unknown_modules)}", path)
    if len(modules) != len(set(modules)):
        _add(findings, "error", "mechanic_module_duplicate", "Mechanic modules must be deduplicated.", path)

    mechanic_fields = {
        "mechanics.resolution_grounding": (
            _clean_scalar(mechanics.get("resolution_grounding", "")),
            RESOLUTION_GROUNDINGS,
        ),
        "mechanics.inventory_tracking": (_clean_scalar(mechanics.get("inventory_tracking", "")), INVENTORY_TRACKING),
        "mechanics.time_tracking": (_clean_scalar(mechanics.get("time_tracking", "")), TIME_TRACKING),
        "mechanics.travel_tracking": (_clean_scalar(mechanics.get("travel_tracking", "")), TRAVEL_TRACKING),
        "mechanics.wound_tracking": (_clean_scalar(mechanics.get("wound_tracking", "")), WOUND_TRACKING),
        "mechanics.dice_mode": (_clean_scalar(mechanics.get("dice_mode", "")), DICE_MODES),
    }
    for context, (value, allowed) in mechanic_fields.items():
        field_required = schema_version >= 2 if context == "mechanics.resolution_grounding" else required
        _enum_field(
            findings,
            path,
            context=context,
            value=value,
            allowed=allowed,
            required=field_required,
        )

    if "strict_consumables" in modules and mechanic_fields["mechanics.inventory_tracking"][0] not in {"quantified", "encumbrance"}:
        _add(findings, "error", "strict_consumables_tracking", "strict_consumables requires quantified or encumbrance inventory tracking.", path)
    if "wounds" in modules and mechanic_fields["mechanics.wound_tracking"][0] != "conditions":
        _add(findings, "error", "wounds_tracking", "wounds requires conditions wound tracking.", path)
    if "structured_travel" in modules and mechanic_fields["mechanics.travel_tracking"][0] != "route_time":
        _add(findings, "error", "structured_travel_tracking", "structured_travel requires route_time tracking.", path)
    dice_mode = mechanic_fields["mechanics.dice_mode"][0]
    if dice_mode and dice_mode != "judgment_only" and "dice_resolution" not in modules:
        _add(findings, "error", "dice_module_missing", "A dice mode requires the dice_resolution module.", path)

    narration = _nested_values(_block(text, "narration"))
    narration_fields = {
        "narration.point_of_view": (_clean_scalar(narration.get("point_of_view", narration.get("pov", ""))), POINTS_OF_VIEW),
        "narration.tense": (_clean_scalar(narration.get("tense", "")), TENSES),
        "narration.camera": (_clean_scalar(narration.get("camera", "")), CAMERA_DISTANCES),
        "narration.prose_density": (_clean_scalar(narration.get("prose_density", "")), PROSE_DENSITIES),
        "narration.response_length": (_clean_scalar(narration.get("response_length", "")), RESPONSE_LENGTHS),
        "narration.option_prompting": (_clean_scalar(narration.get("option_prompting", "")), OPTION_PROMPTING),
        "narration.dialogue_style": (_clean_scalar(narration.get("dialogue_style", "")), DIALOGUE_STYLES),
        "narration.challenge_density": (_clean_scalar(narration.get("challenge_density", "")), DENSITY_VALUES),
        "narration.clue_density": (_clean_scalar(narration.get("clue_density", "")), DENSITY_VALUES),
        "narration.pacing": (_clean_scalar(narration.get("pacing", "")), PACING_VALUES),
    }
    for context, (value, allowed) in narration_fields.items():
        _enum_field(findings, path, context=context, value=value, allowed=allowed, required=required)

    signature = _child_block(_block(text, "narration"), "narrative_signature", indent=2)
    signature_values = _values_at_indent(signature, indent=4)
    anchors = _list_at_indent(signature, "anchors", indent=4)
    avoid_habits = _list_at_indent(signature, "avoid_habits", indent=4)
    sensory_focus = _list_at_indent(signature, "sensory_focus", indent=4)
    if schema_version >= 2:
        if not signature:
            _add(findings, "error", "narrative_signature_missing", "Schema v2 requires narration.narrative_signature.", path)
        for context, values, maximum in (
            ("narrative_signature.anchors", anchors, 3),
            ("narrative_signature.avoid_habits", avoid_habits, 3),
            ("narrative_signature.sensory_focus", sensory_focus, 2),
        ):
            if len(values) > maximum:
                _add(findings, "error", "narrative_signature_list_too_long", f"{context} allows at most {maximum} entries.", path)
            if any(not value.strip() for value in values):
                _add(findings, "error", "narrative_signature_entry_blank", f"{context} contains a blank entry.", path)
        if ready and (
            len(anchors) != 3
            or any(not _meaningful_contract_value(value) for value in anchors)
        ):
            _add(
                findings,
                "error",
                "ready_narrative_signature_incomplete",
                "Ready profile v2 requires exactly three meaningful Narrative Signature anchors.",
                path,
            )
        for context, value, allowed in (
            (
                "narrative_signature.interiority_policy",
                _clean_scalar(signature_values.get("interiority_policy", "")),
                INTERIORITY_POLICIES,
            ),
            (
                "narrative_signature.dialogue_balance",
                _clean_scalar(signature_values.get("dialogue_balance", "")),
                DIALOGUE_BALANCES,
            ),
            (
                "narrative_signature.humor",
                _clean_scalar(signature_values.get("humor", "")),
                HUMOR_VALUES,
            ),
            (
                "narrative_signature.emotional_distance",
                _clean_scalar(signature_values.get("emotional_distance", "")),
                EMOTIONAL_DISTANCES,
            ),
            (
                "narration.breather_frequency",
                _clean_scalar(narration.get("breather_frequency", "")),
                BREATHER_FREQUENCIES,
            ),
            (
                "narration.breather_exit_policy",
                _clean_scalar(narration.get("breather_exit_policy", "")),
                BREATHER_EXIT_POLICIES,
            ),
        ):
            _enum_field(findings, path, context=context, value=value, allowed=allowed, required=True)

    advancement = _nested_values(_block(text, "advancement"))
    _enum_field(
        findings,
        path,
        context="advancement.cadence",
        value=_clean_scalar(advancement.get("cadence", "")),
        allowed=ADVANCEMENT_CADENCES,
        required=required,
    )
    _enum_field(
        findings,
        path,
        context="advancement.presentation",
        value=_clean_scalar(advancement.get("presentation", "")),
        allowed=ADVANCEMENT_PRESENTATIONS,
        required=required,
    )

    dashboard = _nested_values(_block(text, "dashboard"))
    dashboard_mode = _clean_scalar(dashboard.get("mode", ""))
    _enum_field(findings, path, context="dashboard.mode", value=dashboard_mode, allowed=DASHBOARD_MODES, required=required)
    refresh_policy = _clean_scalar(dashboard.get("refresh_policy", ""))
    _enum_field(
        findings,
        path,
        context="dashboard.refresh_policy",
        value=refresh_policy,
        allowed=DASHBOARD_REFRESH_POLICIES,
        required=required and dashboard_mode == "on",
    )
    dashboard_tiles = _parse_nested_block_list(text, "dashboard", "tiles")
    invalid_tiles = sorted(set(dashboard_tiles) - DASHBOARD_TILES)
    if invalid_tiles:
        _add(findings, "error", "dashboard_tile_invalid", f"Unknown dashboard tiles: {', '.join(invalid_tiles)}", path)
    if len(dashboard_tiles) != len(set(dashboard_tiles)):
        _add(findings, "error", "dashboard_tile_duplicate", "Dashboard tile list must be deduplicated.", path)
    if required and dashboard_mode == "on" and not dashboard_tiles:
        _add(findings, "error", "dashboard_tiles_missing", "Enabled dashboard needs at least one tile.", path)

    visuals = _nested_values(_block(text, "visuals"))
    visual_mode = _clean_scalar(visuals.get("mode", ""))
    placement = _clean_scalar(visuals.get("dashboard_placement", ""))
    _enum_field(findings, path, context="visuals.mode", value=visual_mode, allowed=VISUAL_MODES, required=required)
    _enum_field(findings, path, context="visuals.dashboard_placement", value=placement, allowed=VISUAL_PLACEMENTS, required=required)
    if placement == "dashboard_after_approval" and dashboard_mode == "off":
        _add(findings, "error", "visual_dashboard_disabled", "Dashboard placement requires dashboard.mode: on.", path)

    performance = _nested_values(_block(text, "performance"))
    turn_protocol = _clean_scalar(performance.get("turn_protocol", ""))
    cold_policy = _clean_scalar(performance.get("cold_distill_policy", ""))
    validation_policy = _clean_scalar(performance.get("validation_policy", ""))
    style_policy = _clean_scalar(performance.get("style_review_policy", ""))
    latency_policy = _clean_scalar(performance.get("latency_notice_policy", ""))
    estimate_ack = _boolean(performance.get("estimate_acknowledged", "false"))
    for context, value, allowed in (
        ("performance.turn_protocol", turn_protocol, TURN_PROTOCOLS),
        ("performance.cold_distill_policy", cold_policy, COLD_DISTILL_POLICIES),
        ("performance.validation_policy", validation_policy, VALIDATION_POLICIES),
        ("performance.style_review_policy", style_policy, STYLE_REVIEW_POLICIES),
        ("performance.latency_notice_policy", latency_policy, LATENCY_NOTICE_POLICIES),
    ):
        _enum_field(findings, path, context=context, value=value, allowed=allowed, required=required)
    if required and estimate_ack is not True:
        _add(findings, "error", "performance_estimate_unacknowledged", "Ready campaigns must acknowledge the timing-estimate caveat.", path)
    legacy_cold = cold_policy in {"scene_or_3_durable", "scene_or_5_durable"}
    if schema_version >= 2 and legacy_cold:
        _add(
            findings,
            "error",
            "legacy_scene_distill_policy",
            "Schema v2 uses scene_checkpoint_or_3_durable or scene_checkpoint_or_5_durable; a scene checkpoint is not a full distill.",
            path,
        )
    expected = (TURN_PROTOCOL_PRESETS if schema_version >= 2 else LEGACY_TURN_PROTOCOL_PRESETS).get(turn_protocol)
    if expected:
        actual = {
            "cold_distill_policy": cold_policy,
            "validation_policy": validation_policy,
            "dashboard_refresh_policy": refresh_policy,
            "style_review_policy": style_policy,
        }
        for field, expected_value in expected.items():
            if actual.get(field) and actual[field] != expected_value:
                _add(findings, "error", "turn_preset_mismatch", f"{turn_protocol} requires {field}: {expected_value}.", path)
    if required:
        system_fit_path = campaign_path / "system_fit.md"
        session_zero_path = campaign_path / "session_zero.md"
        system_fit = _read(system_fit_path, findings) if system_fit_path.is_file() else ""
        session_zero = _read(session_zero_path, findings) if session_zero_path.is_file() else ""
        if turn_protocol and not re.search(rf"(?im)^-\s+Profile:\s*`?{re.escape(turn_protocol)}`?\s*$", system_fit):
            _add(findings, "error", "turn_profile_summary_missing", "system_fit.md does not mirror the selected Turn Protocol.", system_fit_path)
        if turn_protocol and not re.search(rf"(?im)^-\s+Turn protocol:\s*`?{re.escape(turn_protocol)}`?\s*$", session_zero):
            _add(findings, "error", "turn_profile_summary_missing", "session_zero.md does not mirror the selected Turn Protocol.", session_zero_path)

    mechanics_path = campaign_path / "mechanics_state.json"
    if required and modules and mechanics_path.is_file():
        try:
            enabled = json.loads(mechanics_path.read_text(encoding="utf-8")).get("enabled") is True
        except (OSError, json.JSONDecodeError, AttributeError):
            enabled = False
        stateful_modules = set(modules) - {"dice_resolution"}
        if stateful_modules and not enabled:
            _add(findings, "error", "mechanics_state_disabled", "Approved stateful mechanic modules require mechanics_state enabled.", mechanics_path)

    return {
        "ready": ready,
        "schema_version": schema_version,
        "setting_lenses": setting_lenses,
        "play_lenses": play_lenses,
        "modules": modules,
        "resolution_grounding": (
            _clean_scalar(mechanics.get("resolution_grounding", ""))
            or ("numeric" if schema_version == 1 else "")
        ),
        "dashboard_mode": dashboard_mode,
        "dashboard_refresh_policy": refresh_policy,
        "visual_mode": visual_mode,
        "visual_placement": placement,
        "turn_protocol": turn_protocol,
        "cold_distill_policy": cold_policy,
        "validation_policy": validation_policy,
        "style_review_policy": style_policy,
        "advancement_cadence": _clean_scalar(advancement.get("cadence", "")),
        "advancement_presentation": _clean_scalar(advancement.get("presentation", "")),
    }


def _check_research_gate(campaign_path: Path, findings: list[dict], *, ready: bool) -> None:
    path = campaign_path / "research_dossier.md"
    if not path.is_file():
        return
    text = _read(path, findings)
    status = _markdown_field(text, "Status")
    mode = _markdown_field(text, "Research mode") or _markdown_field(text, "Mode")
    risk = _boolean(_markdown_field(text, "Risk accepted"))
    lock_permitted = _boolean(_markdown_field(text, "Current-scale lock permitted"))

    if status not in RESEARCH_STATUSES:
        _add(findings, "error", "research_status_invalid", f"Invalid research status: {status or '(blank)'}", path)
    if mode and mode not in RESEARCH_MODES:
        _add(findings, "error", "research_mode_invalid", f"Invalid research mode: {mode}", path)
    if risk is None:
        _add(findings, "error", "research_risk_field_invalid", "Risk accepted must be yes/no.", path)
    if lock_permitted is None:
        _add(findings, "error", "research_lock_field_invalid", "Current-scale lock permitted must be yes/no.", path)
    if status == "needed_pending" and ready:
        _add(findings, "error", "research_pending_at_play", "Session 0 cannot complete while required research is pending.", path)
    if status == "needed_pending":
        lock_pattern = re.compile(r"(?im)^\s*-\s*(?:Status:\s*locked|Locked:\s*(?:yes|true))\s*$")
        lock_paths = [campaign_path / "world_truths.md"]
        faction_dir = campaign_path / "factions"
        if faction_dir.is_dir():
            lock_paths.extend(sorted(faction_dir.glob("*.md")))
        for lock_path in lock_paths:
            if lock_path.is_file() and lock_pattern.search(_read(lock_path, findings)):
                _add(
                    findings,
                    "error",
                    "research_truth_locked_while_pending",
                    "World or faction truth cannot be locked while required research is pending.",
                    lock_path,
                )
    if status == "partial_complete" and ready and lock_permitted is not True:
        _add(findings, "error", "research_partial_not_locked", "Partial research needs explicit current-scale lock permission before play.", path)
    if status == "unavailable_risk_accepted" and (risk is not True or lock_permitted is not True):
        _add(findings, "error", "research_risk_not_accepted", "Unavailable research requires explicit risk acceptance and current-scale lock permission.", path)
    if status in {"not_needed", "complete"} and lock_permitted is False and ready:
        _add(findings, "error", "research_lock_not_permitted", "Ready play requires current-scale lock permission.", path)


def _section_is_template(text: str, heading: str) -> bool:
    content = _meaningful_text(_markdown_section(text, heading)).lower()
    if not content:
        return True
    prefixes = {
        "where": "the place where",
        "what kind of place": "describe what this place",
        "when and how the character arrived": "for a first campaign opening",
        "player-known context": "facts the character",
        "immediate visible situation": "what is happening",
        "neutral action space": "natural things the character",
        "pressure or hook": "a small pressure",
        "player-facing opening draft": "draft the first",
    }
    return content.startswith(prefixes.get(heading.lower(), "\0"))


def _section_enum_value(text: str, heading: str, allowed: set[str]) -> str:
    section = _markdown_section(text, heading)
    pattern = "|".join(re.escape(value) for value in sorted(allowed, key=len, reverse=True))
    match = re.search(rf"(?im)^\s*`?({pattern})`?\s*$", section)
    return match.group(1).lower() if match else ""


def _check_ready_for_play(
    campaign_path: Path,
    state_text: str,
    *,
    ready: bool,
    dashboard_mode: str,
    findings: list[dict],
) -> None:
    if not ready:
        return
    state_path = campaign_path / "current_state.yaml"
    top = _top_level_values(state_text)
    player = _nested_values(_block(state_text, "player"))
    scene = _nested_values(_block(state_text, "current_scene"))
    if _clean_scalar(top.get("campaign_id", "")) in {"", "new_campaign", "replace_me"}:
        _add(findings, "error", "ready_campaign_id_placeholder", "Ready campaign needs a permanent campaign_id.", state_path)
    for field in ("name", "concept"):
        if not _clean_scalar(player.get(field, "")):
            _add(findings, "error", "ready_player_missing", f"Ready campaign is missing player {field}.", state_path)
    for field in ("title", "location", "summary"):
        if not _clean_scalar(scene.get(field, "")):
            _add(findings, "error", "ready_scene_missing", f"Ready campaign is missing current_scene.{field}.", state_path)
    scene_mode = _clean_scalar(_nested_values(_block(state_text, "scene_frame")).get("mode", ""))
    if scene_mode == "crisis" and not _clean_scalar(scene.get("immediate_pressure", "")):
        _add(
            findings,
            "error",
            "ready_scene_missing",
            "A crisis scene needs current_scene.immediate_pressure; other scene modes may be calm when campaign-level pressure is established elsewhere.",
            state_path,
        )
    if not _campaign_pressure_materialized(campaign_path, state_text):
        _add(
            findings,
            "error",
            "ready_campaign_pressure_missing",
            "Ready play needs at least one campaign-level issue, thread pressure, threat, clock, or active world domain even when the live scene is calm.",
            campaign_path / "issues.md",
        )

    opening_path = campaign_path / "opening_brief.md"
    opening = _read(opening_path, findings) if opening_path.is_file() else ""
    opening_status = _markdown_field(opening, "Opening status").lower()
    opening_is_live = opening_status == "active" or not opening_status
    if opening_is_live:
        opening_mode = _section_enum_value(opening, "Scene Mode", SCENE_MODES)
        for heading in (
            "Where",
            "What Kind Of Place",
            "When And How The Character Arrived",
            "Player-Known Context",
            "Immediate Visible Situation",
            "Neutral Action Space",
            "Pressure Or Hook",
            "Player-Facing Opening Draft",
        ):
            if heading == "Pressure Or Hook" and opening_mode == "breather":
                continue
            if _section_is_template(opening, heading):
                _add(findings, "error", "ready_opening_incomplete", f"Opening section is incomplete: {heading}", opening_path)

    snapshot_root = campaign_path / "snapshots"
    manifests = list(snapshot_root.glob("*/snapshot_manifest.json")) if snapshot_root.is_dir() else []
    if not manifests:
        _add(findings, "error", "ready_snapshot_missing", "Ready campaign needs a starting snapshot.", snapshot_root)

    world_path = campaign_path / "world.md"
    world_text = _read(world_path, findings) if world_path.is_file() else ""
    operating_model = _meaningful_text(_markdown_section(world_text, "World Operating Model"))
    if not operating_model or operating_model.lower().startswith("record the"):
        _add(findings, "error", "world_operating_model_missing", "Ready campaign needs a World Operating Model.", world_path)

    if dashboard_mode == "on" and not (campaign_path / "dashboard" / "dashboard_state.json").is_file():
        _add(findings, "error", "ready_dashboard_missing", "Enabled dashboard is not prepared.", campaign_path / "dashboard")


def _campaign_pressure_materialized(campaign_path: Path, state_text: str) -> bool:
    if _parse_block_list(state_text, "active_threats") or _parse_block_list(state_text, "active_clocks"):
        return True

    opening_path = campaign_path / "opening_brief.md"
    if opening_path.is_file():
        opening = _read(opening_path, [])
        opening_status = _markdown_field(opening, "Opening status").lower()
        if opening_status in {"", "active"} and not _section_is_template(opening, "Pressure Or Hook"):
            return True

    threads_path = campaign_path / "threads.md"
    if threads_path.is_file():
        compass = _markdown_section(_read(threads_path, []), "Arc Compass")
        if _meaningful_contract_value(_markdown_field(compass, "Active pressures")):
            return True
        active_threads = _markdown_section(_read(threads_path, []), "Active Threads")
        if any(
            _slug(name) != "thread_title" and _meaningful_contract_value(_markdown_field(body, "Pressure"))
            for name, body in _markdown_subsections(active_threads)
        ):
            return True

    issues_path = campaign_path / "issues.md"
    if issues_path.is_file():
        issues_text = _read(issues_path, [])
        for section_name, pressure_field in (
            ("Current Issues", "What is wrong"),
            ("Impending Issues", "What is about to get worse"),
        ):
            if any(
                _slug(name) != "issue_name" and _meaningful_contract_value(_markdown_field(body, pressure_field))
                for name, body in _markdown_subsections(_markdown_section(issues_text, section_name))
            ):
                return True

    dynamics_path = campaign_path / "world_dynamics.md"
    if dynamics_path.is_file():
        active = _markdown_section(_read(dynamics_path, []), "Active Domains")
        if any(
            _slug(name) != "domain_name"
            and _markdown_field(body, "Status").lower() in {"shifting", "volatile"}
            for name, body in _markdown_subsections(active)
        ):
            return True
    return False


def _check_opening_coherence(
    campaign_path: Path,
    *,
    current_location: str,
    present_npcs: list[str],
    findings: list[dict],
) -> None:
    path = campaign_path / "opening_brief.md"
    if not path.is_file():
        return
    text = _read(path, findings)
    opening_status = _markdown_field(text, "Opening status").lower()
    if not opening_status:
        _add(
            findings,
            "warning",
            "opening_status_legacy",
            "Legacy opening brief has no lifecycle status; treating it as live for compatibility.",
            path,
        )
    elif opening_status not in {"pending", "active", "consumed"}:
        _add(findings, "error", "opening_status_invalid", f"Invalid Opening status: {opening_status}", path)
        return
    elif opening_status in {"pending", "consumed"}:
        return
    where = _markdown_section(text, "Where")
    opening_location = _markdown_field(where, "Location")
    if not opening_location:
        lines = [_clean_scalar(line) for line in where.splitlines() if line.strip()]
        if len(lines) == 1 and len(lines[0]) <= 100 and not lines[0].lower().startswith("the place where"):
            opening_location = lines[0]
    if current_location and opening_location:
        current_slug = _slug(current_location)
        opening_slug = _slug(opening_location)
        if current_slug not in opening_slug and opening_slug not in current_slug:
            _add(findings, "error", "opening_location_conflict", f"Opening location {opening_location!r} conflicts with current location {current_location!r}.", path)

    raw_npcs = _markdown_field(text, "Present NPCs")
    if not raw_npcs:
        return
    opening_npcs = _parse_inline_list(raw_npcs) if raw_npcs.startswith("[") else [
        _clean_scalar(value) for value in raw_npcs.split(",") if _clean_scalar(value)
    ]
    for npc in opening_npcs:
        if not _note_exists(campaign_path / "characters", npc) and not _ledger_contains(campaign_path, npc):
            _add(findings, "error", "opening_npc_reference_missing", f"Opening NPC has no character reference: {npc}", path)
    if present_npcs and {_slug(value) for value in opening_npcs} != {_slug(value) for value in present_npcs}:
        _add(findings, "error", "opening_present_npc_conflict", "Structurally listed opening NPCs conflict with current_scene.present_npcs.", path)


def _check_first_session_lifecycle(
    campaign_path: Path,
    *,
    ready: bool,
    contract_v2: bool,
    findings: list[dict],
) -> None:
    path = campaign_path / "first_session.md"
    if not path.is_file():
        return
    status = _markdown_field(_read(path, findings), "Prep status").lower()
    if not status and not contract_v2:
        _add(findings, "warning", "first_session_status_legacy", "Legacy first-session prep has no lifecycle status.", path)
    elif status not in {"drafting", "materialized", "consumed"}:
        _add(findings, "error", "first_session_status_invalid", f"Invalid first-session Prep status: {status or '(blank)'}", path)
    elif ready and status == "drafting":
        _add(findings, "error", "first_session_not_materialized", "Ready play requires first-session prep to be materialized into opening_brief.md.", path)

    opening_path = campaign_path / "opening_brief.md"
    if not contract_v2 or not opening_path.is_file() or status not in {"drafting", "materialized", "consumed"}:
        return
    opening_status = _markdown_field(_read(opening_path, findings), "Opening status").lower()
    opening_text = _read(opening_path, findings)
    opening_type = _section_enum_value(
        opening_text,
        "Opening Type",
        {"first_campaign_opening", "post_arc_opening"},
    )
    if opening_type == "post_arc_opening":
        return
    if not opening_type:
        _add(
            findings,
            "warning",
            "opening_type_legacy",
            "Opening Type is missing; assuming first_campaign_opening for legacy lifecycle compatibility.",
            opening_path,
        )
    expected = {
        "drafting": "pending",
        "materialized": "active",
        "consumed": "consumed",
    }[status]
    if opening_status and opening_status != expected:
        _add(
            findings,
            "error",
            "opening_lifecycle_conflict",
            f"first_session Prep status {status} requires opening_brief Opening status {expected}, not {opening_status}.",
            opening_path,
        )


def _check_visual_state(campaign_path: Path, findings: list[dict]) -> None:
    path = campaign_path / "visual_state.json"
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _add(findings, "error", "visual_state_invalid", str(exc), path)
        return
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        _add(findings, "error", "visual_state_schema_invalid", "visual_state must be a schema-version 1 object.", path)
        return
    if not _strict_int(data.get("revision"), minimum=0):
        _add(findings, "error", "visual_state_revision_invalid", "visual_state revision must be non-negative.", path)
    history = data.get("history")
    if not isinstance(history, list):
        _add(findings, "error", "visual_history_invalid", "visual_state.history must be a list.", path)
        history = []
    for index, entry in enumerate(history):
        if not isinstance(entry, dict):
            _add(findings, "error", "visual_history_entry_invalid", f"visual history entry {index} must be an object.", path)
            continue
        if entry.get("status") == "accepted":
            asset = str(entry.get("asset", "")).replace("\\", "/")
            if not asset.startswith("visuals/") or "/_drafts/" in f"/{asset}" or not (campaign_path / asset).is_file():
                _add(findings, "error", "visual_accepted_asset_missing", f"Accepted visual asset is missing or unsafe: {asset}", path)
            if entry.get("dashboard_placement_completed") is True:
                dashboard_asset = str(entry.get("dashboard_asset", "")).replace("\\", "/")
                if not dashboard_asset.startswith("dashboard/assets/") or not (campaign_path / dashboard_asset).is_file():
                    _add(findings, "error", "visual_dashboard_asset_missing", f"Accepted dashboard asset is missing: {dashboard_asset}", path)
    pending = data.get("pending")
    if pending is None:
        return
    if not isinstance(pending, dict):
        _add(findings, "error", "visual_pending_invalid", "visual_state.pending must be null or an object.", path)
        return
    required = {
        "transaction_id",
        "interrupted_context",
        "last_meaningful_beat",
        "return_anchor",
        "next_step",
        "dashboard_placement_requested",
    }
    missing = sorted(
        key
        for key in required
        if pending.get(key) is None or (isinstance(pending.get(key), str) and not pending.get(key).strip())
    )
    if missing:
        _add(findings, "error", "visual_return_anchor_incomplete", f"Pending visual is missing: {', '.join(missing)}", path)
    target = pending.get("target")
    split_target = pending.get("target_kind") and pending.get("target_id")
    if (not isinstance(target, str) or not target.strip()) and not split_target:
        _add(findings, "error", "visual_target_missing", "Pending visual needs a target item.", path)
    draft_path = str(pending.get("draft_path", "")).replace("\\", "/")
    if draft_path and (
        not draft_path.startswith("visuals/_drafts/") or not (campaign_path / draft_path).is_file()
    ):
        _add(findings, "error", "visual_draft_missing", "Attached draft must exist under visuals/_drafts/.", path)
    context = str(pending.get("interrupted_context", "")).strip().lower()
    _, _, ready = _setup_status(campaign_path, findings)
    if ready and context == "session_zero":
        _add(findings, "error", "visual_review_pending_at_play", "Session 0 cannot complete with a pending visual transaction.", path)


def _run_dashboard_check(
    campaign_path: Path,
    *,
    expected_revision: int | None,
    require_current: bool,
    findings: list[dict],
) -> None:
    checker_path = Path(__file__).with_name("check_dashboard.py")
    state_path = campaign_path / "dashboard" / "dashboard_state.json"
    if not checker_path.is_file() or not state_path.is_file():
        return
    try:
        spec = importlib.util.spec_from_file_location("repog_dashboard_check", checker_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("dashboard checker could not be loaded")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        try:
            result = module.check_dashboard(
                state_path,
                campaign_path=campaign_path,
                expected_revision=expected_revision,
                require_current=require_current,
            )
        except TypeError:
            result = module.check_dashboard(state_path)
    except Exception as exc:  # pragma: no cover - defensive integration guard
        _add(findings, "error", "dashboard_checker_failed", str(exc), checker_path)
        return
    for finding in result.get("findings", []):
        findings.append(
            {
                "severity": finding.get("severity", "error"),
                "rule": finding.get("rule", "dashboard_invalid"),
                "message": finding.get("message", "Dashboard check failed."),
                "path": finding.get("path") or str(state_path),
            }
        )


def _check_visual_handoff(campaign_path: Path, findings: list[dict]) -> None:
    if (campaign_path / "visual_state.json").is_file():
        return
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


def _child_block(block_text: str, key: str, *, indent: int = 2) -> str:
    """Return one direct YAML-like mapping child without requiring PyYAML."""

    lines = block_text.splitlines()
    start: int | None = None
    prefix = " " * indent
    for index, line in enumerate(lines):
        if re.match(rf"^{re.escape(prefix)}{re.escape(key)}:\s*$", line):
            start = index + 1
            break
    if start is None:
        return ""
    children: list[str] = []
    for line in lines[start:]:
        if line.strip() and len(line) - len(line.lstrip(" ")) <= indent:
            break
        children.append(line)
    return "\n".join(children)


def _values_at_indent(block_text: str, *, indent: int) -> dict[str, str]:
    values: dict[str, str] = {}
    prefix = " " * indent
    for line in block_text.splitlines():
        match = re.match(
            rf"^{re.escape(prefix)}([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$",
            line,
        )
        if match:
            values[match.group(1)] = match.group(2).strip()
    return values


def _list_at_indent(block_text: str, key: str, *, indent: int) -> list[str]:
    lines = block_text.splitlines()
    prefix = " " * indent
    for index, line in enumerate(lines):
        inline = re.match(rf"^{re.escape(prefix)}{re.escape(key)}:\s*(\[.*\])\s*$", line)
        if inline:
            return _parse_inline_list(inline.group(1))
        if not re.match(rf"^{re.escape(prefix)}{re.escape(key)}:\s*$", line):
            continue
        items: list[str] = []
        for child in lines[index + 1 :]:
            child_indent = len(child) - len(child.lstrip(" "))
            if child.strip() and child_indent <= indent:
                break
            match = re.match(rf"^\s{{{indent + 2}}}-\s*(.*?)\s*$", child)
            if match:
                items.append(_clean_scalar(match.group(1)))
        return items
    return []


def _boolean(value: str) -> bool | None:
    cleaned = _clean_scalar(value).lower()
    if cleaned in {"true", "yes"}:
        return True
    if cleaned in {"false", "no"}:
        return False
    return None


def _valid_lens(value: str, allowed: set[str]) -> bool:
    return value in allowed or bool(re.fullmatch(r"custom:[a-z0-9][a-z0-9_-]*", value))


def _enum_field(
    findings: list[dict],
    path: Path,
    *,
    context: str,
    value: str,
    allowed: set[str],
    required: bool,
) -> None:
    if not value:
        if required:
            _add(findings, "error", "play_profile_field_missing", f"Missing {context}.", path)
        return
    if value not in allowed:
        _add(findings, "error", "play_profile_field_invalid", f"Invalid {context}: {value}", path)


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
    if setup_schema >= 3:
        profile_path = campaign_path / "play_profile.yaml"
        profile_text = _read(profile_path, findings) if profile_path.is_file() else ""
        performance = _nested_values(_block(profile_text, "performance"))
        protocol = _clean_scalar(performance.get("turn_protocol", ""))
        cold_policy = _clean_scalar(performance.get("cold_distill_policy", ""))
    else:
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
        "scene_checkpoint_or_3_durable": 3,
        "scene_checkpoint_or_5_durable": 5,
        "scene_or_3_durable": 3,
        "scene_or_5_durable": 5,
    }.get(cold_policy)
    overdue = threshold is not None and (
        durable_turns > 0 if threshold == 0 else durable_turns >= threshold
    )
    if overdue:
        _add(
            findings,
            "error",
            "persistence_distill_overdue",
            f"{cold_policy} requires a full distill on durable turn {threshold}; found {durable_turns} undistilled.",
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

    # A scene checkpoint is a resumability write, not a propagation boundary
    # in the v2 Fast/Balanced contract.  Only flag logs that explicitly record
    # both operations for the same revision and name the scene/checkpoint as
    # the distill trigger; other legitimate full-distill triggers remain valid.
    if cold_policy.startswith("scene_checkpoint_or_"):
        checkpoint_revisions = {
            int(value)
            for value in re.findall(
                r"(?im)^###\s+Scene Checkpoint(?:\s+Revision)?\s+(\d+)\s*$",
                log_text,
            )
        }
        for match in re.finditer(
            r"(?ims)^###\s+Distilled Through Revision\s+(\d+)\s*$\s*(.*?)(?=^###\s+|\Z)",
            log_text,
        ):
            marker_revision = int(match.group(1))
            trigger = _markdown_field(match.group(2), "Trigger").lower()
            if (
                marker_revision in checkpoint_revisions
                and ("scene" in trigger or "checkpoint" in trigger)
                and not any(
                    reason in trigger
                    for reason in ("session", "arc", "advancement", "research", "conflict", "manual")
                )
            ):
                _add(
                    findings,
                    "error",
                    "scene_checkpoint_forced_full_distill",
                    f"Scene checkpoint {marker_revision} was also full-distilled only because of the scene boundary.",
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
    match = re.search(rf"(?im)^\s*(?:-\s+)?{re.escape(field_name)}:\s*(.*?)\s*$", text)
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


def _markdown_subsections(section_text: str, *, level: int = 3) -> list[tuple[str, str]]:
    marks = "#" * level
    matches = list(re.finditer(rf"(?m)^{re.escape(marks)}\s+(.+?)\s*$", section_text))
    result: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section_text)
        result.append((match.group(1).strip(), section_text[match.end() : end].strip()))
    return result


def _check_knowledge_authority(campaign_path: Path, findings: list[dict]) -> None:
    path = campaign_path / "knowledge_boundaries.md"
    if not path.is_file():
        return
    text = _read(path, findings)
    player_section = _markdown_section(text, "Player And Character Knowledge")
    protected = _markdown_section(text, "Protected Proper Nouns")
    for name, body in _markdown_subsections(protected):
        if _slug(name) == "protected_name":
            continue
        status = _markdown_field(body, "Status").lower()
        if status in {"gm-only", "foreshadowable"} and re.search(rf"(?i)\b{re.escape(name)}\b", player_section):
            _add(findings, "error", "knowledge_authority_conflict", f"Protected {status} name also appears as active player/character knowledge: {name}", path)

    for section_name, folder in (
        ("Companion Knowledge", "characters"),
        ("NPC And Faction Knowledge", "both"),
    ):
        section = _markdown_section(text, section_name)
        for name, _ in _markdown_subsections(section):
            if _slug(name) in {"companion_name", "npc_or_faction_name"}:
                continue
            exists = _note_exists(campaign_path / "characters", name)
            if folder == "both":
                exists = exists or _note_exists(campaign_path / "factions", name)
            if not exists and not _ledger_contains(campaign_path, name):
                _add(findings, "error", "knowledge_actor_reference_missing", f"Knowledge authority names an unknown actor: {name}", path)


def _check_world_evaluation_identity(campaign_path: Path, findings: list[dict]) -> None:
    path = campaign_path / "world_dynamics.md"
    if not path.is_file():
        return
    text = _read(path, findings)
    active = _markdown_section(text, "Active Domains")
    trigger_ids: dict[str, str] = {}
    for name, body in _markdown_subsections(active):
        if _slug(name) == "domain_name":
            continue
        due = _markdown_field(body, "Due").lower() in {"yes", "true"}
        pending_id = _markdown_field(body, "Pending evaluation id")
        last_id = _markdown_field(body, "Last evaluation id")
        trigger = _markdown_field(body, "Trigger")
        if due and not pending_id:
            _add(findings, "error", "world_evaluation_id_missing", f"Due domain {name} needs a stable Pending evaluation id.", path)
        if last_id and not _markdown_field(body, "Causal result before uncertainty"):
            _add(findings, "error", "world_evaluation_result_missing", f"Evaluated domain {name} lacks its causal result.", path)
        if trigger and (last_id or pending_id):
            evaluation_id = last_id or pending_id
            trigger_key = f"{_slug(name)}:{_slug(trigger)}"
            previous = trigger_ids.setdefault(trigger_key, evaluation_id)
            if previous != evaluation_id:
                _add(findings, "error", "world_evaluation_identity_conflict", f"Trigger {trigger!r} maps to both {previous!r} and {evaluation_id!r}.", path)

    events = _markdown_section(text, "Notable World Events")
    event_results: dict[str, str] = {}
    for name, body in _markdown_subsections(events):
        if _slug(name) == "event_title":
            continue
        evaluation_id = _markdown_field(body, "Evaluation id")
        if not evaluation_id:
            _add(findings, "error", "world_event_evaluation_id_missing", f"World event {name} lacks Evaluation id.", path)
            continue
        normalized = " ".join(body.split())
        previous = event_results.setdefault(evaluation_id, normalized)
        if previous != normalized:
            _add(findings, "error", "world_evaluation_identity_conflict", f"Evaluation id {evaluation_id!r} has conflicting persisted event results.", path)


def _check_advancement_contract(campaign_path: Path, profile: dict[str, object], findings: list[dict]) -> None:
    cadence = str(profile.get("advancement_cadence", ""))
    presentation = str(profile.get("advancement_presentation", ""))
    if not cadence and not presentation:
        return
    if cadence == "none" and presentation != "none":
        _add(findings, "error", "advancement_presentation_conflict", "advancement.cadence none requires presentation none.", campaign_path / "play_profile.yaml")
    if cadence and cadence != "none" and presentation == "none":
        _add(findings, "error", "advancement_presentation_conflict", "An enabled advancement cadence requires explicit_ooc or automatic_fictional presentation.", campaign_path / "play_profile.yaml")

    path = campaign_path / "arc_closure.md"
    if not path.is_file():
        return
    text = _read(path, findings)
    live = _markdown_section(text, "Current Progression State") or text
    status = (_markdown_field(live, "Advancement status") or _markdown_field(live, "Status")).lower()
    allowed_statuses = {"not_due", "due", "offered", "chosen", "deferred", "applied"}
    if status and status not in allowed_statuses:
        _add(findings, "error", "advancement_status_invalid", f"Invalid live Advancement status: {status}", path)

    arc_presentation = _markdown_field(live, "Advancement presentation").lower()
    if arc_presentation:
        if arc_presentation not in ADVANCEMENT_PRESENTATIONS:
            _add(findings, "error", "advancement_presentation_invalid", f"Invalid live Advancement presentation: {arc_presentation}", path)
        elif presentation and arc_presentation != presentation:
            _add(findings, "error", "advancement_presentation_conflict", "arc_closure live presentation must match play_profile advancement.presentation.", path)

    lock_value = _boolean(_markdown_field(live, "Fiction continuation locked until advancement"))
    if lock_value is None:
        legacy_continue = _boolean(_markdown_field(live, "Fiction may continue"))
        locked = legacy_continue is False
    else:
        locked = lock_value is True

    ooc_status = _markdown_field(live, "OOC interlude status").lower()
    legacy_interlude = _boolean(_markdown_field(live, "OOC interlude offered"))
    if not ooc_status and legacy_interlude is not None:
        ooc_status = (
            "offered"
            if legacy_interlude
            else ("not_applicable" if presentation in {"none", "automatic_fictional"} else "not_offered")
        )
    allowed_ooc = {"not_applicable", "not_offered", "offered", "deferred", "resolved"}
    if ooc_status and ooc_status not in allowed_ooc:
        _add(findings, "error", "advancement_ooc_status_invalid", f"Invalid OOC interlude status: {ooc_status}", path)

    unresolved_choice = status in {"due", "offered"}
    if cadence == "none":
        if status in {"due", "offered"}:
            _add(findings, "error", "advancement_gate_forbidden", "cadence none cannot leave advancement due or offered.", path)
        if ooc_status in {"offered", "deferred", "resolved"} or legacy_interlude is True:
            _add(findings, "error", "advancement_gate_forbidden", "cadence none cannot open an OOC advancement interlude.", path)
        if locked:
            _add(findings, "error", "advancement_gate_forbidden", "cadence none cannot lock normal fiction for advancement.", path)
    if presentation in {"automatic_fictional", "none"}:
        if ooc_status and ooc_status != "not_applicable":
            _add(findings, "error", "advancement_presentation_conflict", f"{presentation} requires OOC interlude status not_applicable.", path)
        if locked:
            _add(findings, "error", "advancement_presentation_conflict", f"{presentation} cannot lock fiction for an OOC interlude.", path)
    if presentation == "explicit_ooc":
        if locked and not (unresolved_choice and ooc_status == "offered"):
            _add(findings, "error", "advancement_gate_without_choice", "explicit_ooc may lock only while a due/offered choice has OOC status offered.", path)
        if ooc_status == "deferred" and locked:
            _add(findings, "error", "advancement_deferred_still_locked", "Deferring the OOC choice must clear the fiction lock.", path)


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


def _check_character_notes(
    campaign_path: Path,
    level_band: str,
    findings: list[dict],
    *,
    resolution_grounding: str,
    ready: bool,
    contract_v3: bool,
) -> None:
    active_path = campaign_path / "active_cast.md"
    active_rows = _markdown_table(_read(active_path, findings)) if active_path.is_file() else []
    active_names = {
        _slug(row.get("NPC", ""))
        for row in active_rows
        if row.get("NPC") and _slug(row.get("NPC", "")) != "example_npc"
    }
    for path in _markdown_files(campaign_path / "characters"):
        text = _read(path, findings)
        tier = _slug(_markdown_field(text, "Tier"))
        if tier not in IMPORTANT_TIERS:
            continue

        power_band = _markdown_field(text, "Power Band")
        if not power_band:
            _add(findings, "warning", "character_power_band_missing", "T2+ character is missing Power Band.", path)

        card = _markdown_key_values(_markdown_section(text, "At-The-Table Agency Card"))
        card_missing = [
            field
            for field in AGENCY_CARD_FIELDS
            if field not in card
            or (
                field != "Offscreen trajectory status"
                and not _meaningful_contract_value(card.get(field, ""))
            )
            or (
                field == "Offscreen trajectory status"
                and _clean_scalar(card.get(field, "")) not in OFFSCREEN_TRAJECTORY_STATUSES
            )
        ]
        status = _clean_scalar(card.get("Offscreen trajectory status", ""))
        if status and status not in OFFSCREEN_TRAJECTORY_STATUSES:
            _add(
                findings,
                "error",
                "offscreen_trajectory_status_invalid",
                f"Invalid Offscreen trajectory status: {status}",
                path,
            )
        if status == "active":
            trajectory = _markdown_key_values(_markdown_section(text, "Offscreen Trajectory"))
            trajectory_missing = [
                field
                for field in OFFSCREEN_TRAJECTORY_FIELDS
                if not _meaningful_contract_value(trajectory.get(field, ""))
            ]
            if trajectory_missing:
                _add(
                    findings,
                    "error" if contract_v3 else "warning",
                    "active_offscreen_trajectory_incomplete",
                    f"Active offscreen trajectory needs: {', '.join(trajectory_missing)}",
                    path,
                )
        title_match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
        entity_slug = _slug(title_match.group(1)) if title_match else _slug(path.stem)
        is_active = entity_slug in active_names or _slug(path.stem) in active_names
        if card_missing:
            strict = contract_v3 and (ready or is_active)
            _add(
                findings,
                "error" if strict else "warning",
                "character_agency_card_incomplete",
                f"T2/T3 Agency Card needs meaningful values for: {', '.join(card_missing)}",
                path,
            )

        if not card:
            for heading, rule in (
                ("Routine And Availability", "character_routine_missing"),
                ("Current Mundane Agenda", "character_agenda_missing"),
                ("Private Motive", "character_motive_missing"),
                ("Last Meaningful Interaction", "character_last_interaction_missing"),
            ):
                if not _meaningful_text(_markdown_section(text, heading)):
                    _add(findings, "warning", rule, f"T2+ character is missing {heading}.", path)

        if resolution_grounding != "numeric":
            continue
        stats = _markdown_key_values(
            _markdown_section(text, "Stats (Numeric Grounding Only)")
            or _markdown_section(text, "Stats")
        )
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


def _check_faction_notes(
    campaign_path: Path,
    level_band: str,
    findings: list[dict],
    *,
    resolution_grounding: str,
) -> None:
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
        ):
            if not _meaningful_text(_markdown_section(text, heading)):
                _add(findings, "warning", rule, f"T2+ faction is missing {heading}.", path)

        for heading, rule, placeholder in (
            ("Stable Capability", "faction_stable_capability_missing", "describe the faction's durable"),
            ("Stable Desire", "faction_stable_desire_missing", "what the faction really wants"),
            ("Stable Methods", "faction_stable_methods_missing", "how it usually gets"),
        ):
            section_text = _meaningful_text(_markdown_section(text, heading))
            if heading == "Stable Capability" and resolution_grounding == "numeric":
                continue
            if not section_text or section_text.casefold().startswith(placeholder):
                _add(findings, "warning", rule, f"T2+ faction is missing authored {heading}.", path)

        domain_values = _markdown_key_values(_markdown_section(text, "Current World Domain Reference"))
        domain_id = _clean_scalar(domain_values.get("Domain id", ""))
        if not _meaningful_contract_value(domain_id):
            _add(
                findings,
                "warning",
                "faction_world_domain_reference_missing",
                "T2+ faction needs a Current World Domain Reference instead of a duplicated current move.",
                path,
            )
        else:
            dynamics_path = campaign_path / "world_dynamics.md"
            dynamics = _read(dynamics_path, findings) if dynamics_path.is_file() else ""
            if not re.search(rf"(?im)^-\s+Domain id:\s*`?{re.escape(domain_id)}`?\s*$", dynamics):
                _add(
                    findings,
                    "error",
                    "faction_world_domain_reference_missing",
                    f"Faction references unknown world domain id: {domain_id}",
                    path,
                )

        if resolution_grounding != "numeric":
            continue

        profile = _markdown_key_values(_markdown_section(text, "Stable Capability"))
        if not profile:
            _add(
                findings,
                "warning",
                "faction_capability_profile_missing",
                "T2+ faction is missing numeric Stable Capability values.",
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

        typical_stats = _markdown_key_values(
            _markdown_section(text, "Typical Member Stats (Numeric Grounding Only)")
            or _markdown_section(text, "Typical Member Stats")
        )
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


def _check_markdown_mechanics(
    campaign_path: Path,
    level_band: str,
    findings: list[dict],
    *,
    resolution_grounding: str,
    ready: bool,
    contract_v3: bool,
) -> None:
    _check_character_notes(
        campaign_path,
        level_band,
        findings,
        resolution_grounding=resolution_grounding,
        ready=ready,
        contract_v3=contract_v3,
    )
    _check_place_notes(campaign_path, findings)
    _check_place_obstacles(campaign_path, findings)
    _check_faction_notes(
        campaign_path,
        level_band,
        findings,
        resolution_grounding=resolution_grounding,
    )


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
    required_active_fields = ["Current location", "Current activity", "Immediate objective", "Availability", "Reason here", "Next move if ignored"]
    for row in active_rows:
        if _slug(row.get("NPC", "")) == "example_npc":
            continue
        tier = _slug(row.get("Tier", ""))
        if tier not in IMPORTANT_TIERS:
            continue
        missing = [name for name in required_active_fields if not row.get(name)]
        if missing:
            _add(
                findings,
                "error",
                "active_cast_incomplete",
                f"Active {tier.upper()} NPC {row.get('NPC', '')} is missing: {', '.join(missing)}",
                active_path,
            )
    for npc in present_npcs:
        tier = _entity_tier(campaign_path / "characters", npc)
        if tier in IMPORTANT_TIERS:
            row = active_by_name.get(_slug(npc))
            if not row:
                _add(findings, "error", "present_important_npc_untracked", f"Present {tier.upper()} NPC has no active cast row: {npc}", active_path)
                continue
            missing = [name for name in required_active_fields if not row.get(name)]
            if missing:
                _add(findings, "error", "active_cast_presence_incomplete", f"Active cast row for {npc} is missing: {', '.join(missing)}", active_path)
            row_location = row.get("Current location", "")
            if location and row_location and _slug(location) != _slug(row_location):
                _add(findings, "error", "active_cast_location_conflict", f"Present NPC {npc} is tracked at {row_location}, not current location {location}.", active_path)
        elif tier == "t1" and _slug(npc) not in active_by_name:
            _add(findings, "warning", "present_t1_presence_untracked", f"Present recurring T1 NPC has no active presence row: {npc}", active_path)

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
                if location and _slug(endpoint) == _slug(location):
                    _add(findings, "warning", "location_graph_incidental_endpoint", f"Current incidental endpoint has no place note: {endpoint}", graph_path)
                else:
                    _add(findings, "error", "location_graph_endpoint_missing", f"Location graph endpoint has no place note: {endpoint}", graph_path)
        if _slug(location) in {_slug(source), _slug(target)}:
            seen_current_location = True
    if location and not seen_current_location:
        _add(findings, "error", "current_location_unmapped", f"Current location has no location graph connection: {location}", graph_path)

    relationship_text = _read(relationship_path, findings)
    relationship_rows = _markdown_table(relationship_text)
    relationship_revision = _markdown_revision(relationship_text, "As of revision")
    if relationship_revision is None:
        _add(findings, "warning", "relationship_revision_missing", "Relationship map has no revision.", relationship_path)
    elif scope == "full" and relationship_revision < revision:
        _add(findings, "warning", "relationship_map_stale", f"Relationship map revision {relationship_revision} trails state revision {revision}.", relationship_path)
    state_text = _read(campaign_path / "current_state.yaml", findings)
    player_name = _clean_scalar(_nested_values(_block(state_text, "player")).get("name", ""))
    required_relationship_fields = (
        "From",
        "Direction",
        "To",
        "Relation",
        "Status",
        "Trust / debt / tension",
        "Knowledge asymmetry",
        "Player-known",
        "Last changed",
        "Revision",
    )

    def endpoint_exists(name: str) -> bool:
        if player_name and _slug(name) == _slug(player_name):
            return True
        if _slug(name) in {"player", "player_character", "pc"}:
            return True
        return (
            _note_exists(campaign_path / "characters", name)
            or _note_exists(campaign_path / "factions", name)
            or _ledger_contains(campaign_path, name)
        )

    seen_pairs: set[tuple[str, str]] = set()
    for row in relationship_rows:
        source = _slug(row.get("From", ""))
        target = _slug(row.get("To", ""))
        if source == "character_a" or not source or not target:
            continue
        missing_cells = [field for field in required_relationship_fields if not row.get(field)]
        if missing_cells:
            _add(findings, "error", "relationship_row_incomplete", f"Relationship row is missing: {', '.join(missing_cells)}", relationship_path)
        if row.get("Direction") not in {"->", "<->"}:
            _add(findings, "error", "relationship_direction_invalid", f"Invalid relationship direction: {row.get('Direction', '')}", relationship_path)
        for endpoint in (row.get("From", ""), row.get("To", "")):
            if endpoint and not endpoint_exists(endpoint):
                _add(findings, "error", "relationship_endpoint_missing", f"Relationship endpoint has no authoritative entity: {endpoint}", relationship_path)
        raw_row_revision = row.get("Revision", "")
        try:
            row_revision = int(raw_row_revision)
        except ValueError:
            _add(findings, "error", "relationship_row_revision_invalid", f"Relationship revision is not an integer: {raw_row_revision}", relationship_path)
        else:
            if row_revision < 0 or row_revision > revision:
                _add(findings, "error", "relationship_row_revision_invalid", f"Relationship revision {row_revision} is outside 0-{revision}.", relationship_path)
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

def _strict_int(value: object, *, minimum: int | None = None) -> bool:
    return type(value) is int and (minimum is None or value >= minimum)


def _check_style_state(state: dict, path: Path, findings: list[dict]) -> None:
    schema = state.get("schema_version", 1)
    if not _strict_int(schema, minimum=1) or schema not in {1, 2, 3}:
        _add(findings, "error", "style_schema_invalid", "style_state schema_version must be 1, 2, or 3.", path)
    elif schema < 3:
        _add(findings, "warning", "style_schema_legacy", "Legacy style state remains readable; schema v3 adds sampled categorical history.", path)
    maximum = state.get("max_history", 8)
    history = state.get("history", [])
    if not _strict_int(maximum, minimum=1):
        _add(findings, "error", "style_history_limit_invalid", "style_state max_history must be positive.", path)
    if not isinstance(history, list):
        _add(findings, "error", "style_history_invalid", "style_state history must be a list.", path)
        history = []
    elif _strict_int(maximum, minimum=1) and len(history) > maximum:
        _add(findings, "warning", "style_history_too_long", "style_state history exceeds max_history.", path)
    if any(isinstance(entry, dict) and any(key in entry for key in ("text", "narration", "full_text")) for entry in history):
        _add(findings, "warning", "style_state_full_prose", "style_state should store fingerprints, not full narration.", path)
    avoid_phrases = state.get("avoid_phrases", [])
    if not isinstance(avoid_phrases, list) or any(not isinstance(value, str) for value in avoid_phrases):
        _add(findings, "error", "style_avoid_phrases_invalid", "avoid_phrases must be a list of strings.", path)
    if schema == 1:
        return
    for field in ("last_beat_id", "last_scene_id"):
        value = state.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            _add(findings, "error", "style_anchor_invalid", f"{field} must be a non-empty string or null.", path)
    last_speaker = state.get("last_speaker")
    if last_speaker is not None:
        if not isinstance(last_speaker, dict):
            _add(findings, "error", "style_speaker_invalid", "last_speaker must be an object or null.", path)
        else:
            speaker_type = last_speaker.get("type")
            speaker_id = last_speaker.get("id")
            if speaker_type not in {"narrator", "npc", "companion", "mixed", "other"}:
                _add(findings, "error", "style_speaker_invalid", "last_speaker.type is invalid.", path)
            if speaker_type in {"npc", "companion"} and (not isinstance(speaker_id, str) or not speaker_id.strip()):
                _add(findings, "error", "style_speaker_id_missing", "NPC/companion style state needs a speaker id.", path)
            elif speaker_id is not None and not isinstance(speaker_id, str):
                _add(findings, "error", "style_speaker_id_invalid", "last_speaker.id must be a string or null.", path)
    for index, entry in enumerate(history):
        if not isinstance(entry, dict):
            _add(findings, "error", "style_fingerprint_invalid", f"history[{index}] must be an object.", path)
            continue
        speaker_type = entry.get("speaker_type", "narrator")
        if speaker_type not in {"narrator", "npc", "companion", "mixed", "other"}:
            _add(findings, "error", "style_fingerprint_invalid", f"history[{index}].speaker_type is invalid.", path)
        if speaker_type in {"npc", "companion"} and not str(entry.get("speaker_id") or "").strip():
            _add(findings, "error", "style_speaker_id_missing", f"history[{index}] needs a speaker_id.", path)
        for field in ("word_count", "paragraph_count", "sentence_count"):
            if field in entry and not _strict_int(entry[field], minimum=0):
                _add(findings, "error", "style_fingerprint_invalid", f"history[{index}].{field} must be a non-negative integer.", path)
        for field in ("sentence_starters", "four_grams"):
            if field in entry and (
                not isinstance(entry[field], list) or any(not isinstance(value, str) for value in entry[field])
            ):
                _add(findings, "error", "style_fingerprint_invalid", f"history[{index}].{field} must be a string list.", path)

    if schema != 3:
        return
    categorical_maximum = state.get("max_categorical_history", 8)
    categorical_history = state.get("categorical_history", [])
    if not _strict_int(categorical_maximum, minimum=1) or categorical_maximum > 8:
        _add(findings, "error", "style_categorical_limit_invalid", "max_categorical_history must be an integer from 1 through 8.", path)
    if not isinstance(categorical_history, list):
        _add(findings, "error", "style_categorical_history_invalid", "categorical_history must be a list.", path)
        return
    if len(categorical_history) > 8 or (
        _strict_int(categorical_maximum, minimum=1) and len(categorical_history) > categorical_maximum
    ):
        _add(findings, "warning", "style_categorical_history_too_long", "categorical_history exceeds its bounded limit.", path)
    for index, entry in enumerate(categorical_history):
        if not isinstance(entry, dict):
            _add(findings, "error", "style_categorical_entry_invalid", f"categorical_history[{index}] must be an object.", path)
            continue
        present = 0
        for field in STYLE_CATEGORICAL_FIELDS:
            value = entry.get(field)
            if value is None:
                continue
            present += 1
            if not isinstance(value, str) or not value.strip():
                _add(findings, "error", "style_categorical_entry_invalid", f"categorical_history[{index}].{field} must be a non-empty string.", path)
        if present == 0:
            _add(findings, "error", "style_categorical_entry_invalid", f"categorical_history[{index}] has no categorical fingerprint.", path)
        speaker_type = entry.get("speaker_type", "narrator")
        if speaker_type not in {"narrator", "npc", "companion", "mixed", "other"}:
            _add(findings, "error", "style_categorical_entry_invalid", f"categorical_history[{index}].speaker_type is invalid.", path)


def _check_mechanics_state(state: dict, path: Path, findings: list[dict]) -> None:
    schema = state.get("schema_version", 1)
    if not _strict_int(schema, minimum=1) or schema not in {1, 2}:
        _add(findings, "error", "mechanics_schema_invalid", "mechanics_state schema_version must be 1 or 2.", path)
        return
    if not isinstance(state.get("enabled"), bool):
        _add(findings, "error", "mechanics_enabled_invalid", "mechanics_state enabled must be boolean.", path)
    revision = state.get("revision")
    if not _strict_int(revision, minimum=0):
        _add(findings, "error", "mechanics_revision_invalid", "mechanics_state revision must be non-negative.", path)

    if schema == 1:
        operations = state.get("applied_operations")
        if not isinstance(operations, list) or any(not isinstance(value, str) or not value for value in operations):
            _add(findings, "error", "mechanics_operations_invalid", "applied_operations must be a list of non-empty strings.", path)
        elif len(operations) != len(set(operations)):
            _add(findings, "error", "mechanics_operations_duplicate", "applied_operations contains duplicate ids.", path)
    else:
        continuity_revision = state.get("continuity_revision")
        sequence = state.get("operation_sequence")
        registry = state.get("operation_registry")
        if not _strict_int(continuity_revision, minimum=0):
            _add(findings, "error", "mechanics_continuity_revision_invalid", "continuity_revision must be non-negative.", path)
        if not _strict_int(sequence, minimum=0):
            _add(findings, "error", "mechanics_sequence_invalid", "operation_sequence must be non-negative.", path)
        if not isinstance(registry, dict):
            _add(findings, "error", "mechanics_registry_invalid", "operation_registry must be an object.", path)
            registry = {}
        seen_sequences: set[int] = set()
        for operation_id, record in registry.items():
            if not isinstance(operation_id, str) or not operation_id.strip() or not isinstance(record, dict):
                _add(findings, "error", "mechanics_registry_record_invalid", f"Invalid operation registry entry: {operation_id!r}.", path)
                continue
            record_sequence = record.get("sequence")
            record_revision = record.get("revision")
            request_hash = record.get("request_hash")
            if not _strict_int(record_sequence, minimum=1) or (_strict_int(sequence, minimum=0) and record_sequence > sequence):
                _add(findings, "error", "mechanics_registry_sequence_invalid", f"Registry sequence is invalid for {operation_id}.", path)
            elif record_sequence in seen_sequences:
                _add(findings, "error", "mechanics_registry_sequence_duplicate", "operation_registry contains duplicate sequences.", path)
            else:
                seen_sequences.add(record_sequence)
            if not _strict_int(record_revision, minimum=1) or (_strict_int(revision, minimum=0) and record_revision > revision):
                _add(findings, "error", "mechanics_registry_revision_invalid", f"Registry revision is invalid for {operation_id}.", path)
            if request_hash is not None and (not isinstance(request_hash, str) or not request_hash):
                _add(findings, "error", "mechanics_registry_hash_invalid", f"Registry request_hash is invalid for {operation_id}.", path)
        last = state.get("last_operation")
        if last is not None:
            if not isinstance(last, dict):
                _add(findings, "error", "mechanics_last_operation_invalid", "last_operation must be an object or null.", path)
            else:
                last_id = last.get("operation_id")
                if not isinstance(last_id, str) or not last_id.strip():
                    _add(findings, "error", "mechanics_last_operation_invalid", "last_operation needs operation_id.", path)
                if last.get("sequence") != sequence or last.get("revision") != revision:
                    _add(findings, "error", "mechanics_last_operation_stale", "last_operation must match current sequence and revision.", path)
                if isinstance(registry, dict) and isinstance(last_id, str):
                    record = registry.get(last_id)
                    if not isinstance(record, dict) or record.get("sequence") != last.get("sequence"):
                        _add(findings, "error", "mechanics_last_operation_unregistered", "last_operation must match operation_registry.", path)

    actors = state.get("actors")
    if not isinstance(actors, dict):
        _add(findings, "error", "mechanics_actors_invalid", "mechanics_state actors must be an object.", path)
        actors = {}
    for actor_id, actor in actors.items():
        if not isinstance(actor_id, str) or not actor_id or not isinstance(actor, dict):
            _add(findings, "error", "mechanics_actor_invalid", f"Actor {actor_id!r} must be a named object.", path)
            continue
        containers: dict[str, dict] = {}
        for name in ("resources", "abilities", "inventory", "conditions"):
            value = actor.get(name, {})
            if not isinstance(value, dict):
                _add(findings, "error", f"mechanics_{name}_invalid", f"Actor {actor_id} {name} must be an object.", path)
                value = {}
            containers[name] = value
        resources = containers["resources"]
        for resource_id, resource in resources.items():
            if not isinstance(resource, dict):
                _add(findings, "error", "mechanics_resource_invalid", f"Resource {actor_id}.{resource_id} must be an object.", path)
                continue
            values = [resource.get(key) for key in ("minimum", "current", "maximum")]
            if not all(_strict_int(value) for value in values):
                _add(findings, "error", "mechanics_resource_bounds_invalid", f"Resource {actor_id}.{resource_id} needs integer minimum/current/maximum.", path)
            else:
                minimum, current, maximum = values
                if minimum > maximum or not minimum <= current <= maximum:
                    _add(findings, "error", "mechanics_resource_out_of_bounds", f"Resource {actor_id}.{resource_id} is outside its configured bounds.", path)
            regen = resource.get("regen")
            if regen is not None and (
                not isinstance(regen, dict)
                or not _strict_int(regen.get("amount"), minimum=0)
                or not isinstance(regen.get("unit"), str)
                or not regen.get("unit", "").strip()
            ):
                _add(findings, "error", "mechanics_regen_invalid", f"Resource {actor_id}.{resource_id} has invalid regen.", path)
        for ability_id, ability in containers["abilities"].items():
            if not isinstance(ability, dict) or not isinstance(ability.get("known"), bool):
                _add(findings, "error", "mechanics_ability_invalid", f"Ability {actor_id}.{ability_id} needs boolean known.", path)
                continue
            costs = ability.get("costs", {})
            if not isinstance(costs, dict) or any(
                resource_id not in resources or not _strict_int(cost, minimum=0)
                for resource_id, cost in (costs.items() if isinstance(costs, dict) else [])
            ):
                _add(findings, "error", "mechanics_ability_cost_invalid", f"Ability {actor_id}.{ability_id} has invalid costs.", path)
            cooldown = ability.get("cooldown")
            if cooldown is not None:
                valid_cooldown = (
                    isinstance(cooldown, dict)
                    and _strict_int(cooldown.get("duration"), minimum=0)
                    and _strict_int(cooldown.get("remaining"), minimum=0)
                    and cooldown["remaining"] <= cooldown["duration"]
                    and isinstance(cooldown.get("unit"), str)
                    and bool(cooldown.get("unit", "").strip())
                )
                if not valid_cooldown:
                    _add(findings, "error", "mechanics_cooldown_invalid", f"Ability {actor_id}.{ability_id} has invalid cooldown.", path)
        for item_id, item in containers["inventory"].items():
            valid_item = isinstance(item, dict) and _strict_int(item.get("quantity"), minimum=0)
            if valid_item and "consumable" in item:
                valid_item = isinstance(item["consumable"], bool)
            if valid_item and "maximum" in item:
                valid_item = _strict_int(item["maximum"], minimum=0) and item["quantity"] <= item["maximum"]
            if not valid_item:
                _add(findings, "error", "mechanics_inventory_item_invalid", f"Inventory item {actor_id}.{item_id} is invalid.", path)
        for condition_id, condition in containers["conditions"].items():
            valid_condition = isinstance(condition, dict) and _strict_int(condition.get("level"), minimum=1)
            duration = condition.get("duration") if isinstance(condition, dict) else None
            if valid_condition and duration is not None:
                valid_condition = (
                    isinstance(duration, dict)
                    and _strict_int(duration.get("remaining"), minimum=0)
                    and isinstance(duration.get("unit"), str)
                    and bool(duration.get("unit", "").strip())
                )
            if not valid_condition:
                _add(findings, "error", "mechanics_condition_invalid", f"Condition {actor_id}.{condition_id} is invalid.", path)

    clocks = state.get("clocks", {})
    if not isinstance(clocks, dict):
        _add(findings, "error", "mechanics_clocks_invalid", "clocks must be an object.", path)
        clocks = {}
    for clock_id, clock in clocks.items():
        valid_clock = (
            isinstance(clock, dict)
            and _strict_int(clock.get("current"), minimum=0)
            and _strict_int(clock.get("maximum"), minimum=1)
            and clock["current"] <= clock["maximum"]
        )
        if not valid_clock:
            _add(findings, "error", "mechanics_clock_invalid", f"Clock {clock_id} is invalid.", path)
    elapsed = state.get("elapsed_time", {})
    if not isinstance(elapsed, dict) or any(
        not isinstance(unit, str) or not unit or not _strict_int(amount, minimum=0)
        for unit, amount in (elapsed.items() if isinstance(elapsed, dict) else [])
    ):
        _add(findings, "error", "mechanics_elapsed_time_invalid", "elapsed_time must map units to non-negative integers.", path)


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
            _check_style_state(state, path, findings)
        else:
            _check_mechanics_state(state, path, findings)


def _meaningful_contract_value(value: str) -> bool:
    cleaned = _clean_scalar(value).strip()
    if not cleaned:
        return False
    folded = cleaned.casefold()
    return folded not in {
        "needs_review",
        "todo",
        "tbd",
        "unknown",
        "replace_me",
        "none yet",
        "n/a",
    } and not bool(re.fullmatch(r"[<\[].+?[>\]]", cleaned))


def _check_scene_frame(
    state_text: str,
    state_path: Path,
    *,
    memory_version: int,
    ready: bool,
    findings: list[dict],
) -> None:
    if memory_version < 3:
        if memory_version == 2:
            _add(
                findings,
                "warning",
                "memory_v3_pending",
                "Legacy memory v2 remains playable; migrate when a snapshot is available.",
                state_path,
            )
        return

    if not re.search(r"(?m)^scene_frame:\s*$", state_text):
        _add(findings, "error", "scene_frame_missing", "Memory v3 requires a top-level scene_frame.", state_path)
        return
    block = _block(state_text, "scene_frame")
    values = _nested_values(block)
    required_keys = {
        "scene_id",
        "mode",
        "ongoing_process",
        "disruption",
        "last_causal_beat",
        "pending_consequences",
        "resume_anchor",
    }
    missing = sorted(required_keys - set(values))
    if missing:
        _add(findings, "error", "scene_frame_shape_invalid", f"scene_frame is missing: {', '.join(missing)}", state_path)

    mode = _clean_scalar(values.get("mode", ""))
    if mode and mode not in SCENE_MODES:
        _add(findings, "error", "scene_mode_invalid", f"Invalid scene_frame.mode: {mode}", state_path)

    causal = _nested_mapping(block, "last_causal_beat")
    causal_fields = {"player_intent", "world_response", "changed_fact", "returned_control_at"}
    missing_causal = sorted(causal_fields - set(causal))
    if missing_causal:
        _add(
            findings,
            "error",
            "causal_beat_shape_invalid",
            f"last_causal_beat is missing: {', '.join(missing_causal)}",
            state_path,
        )

    pending = _parse_nested_block_list(state_text, "scene_frame", "pending_consequences")
    if len(pending) > 3:
        _add(findings, "error", "pending_consequence_limit", "scene_frame permits at most three pending consequences.", state_path)
    if any(not _meaningful_contract_value(item) for item in pending):
        _add(findings, "error", "pending_consequence_invalid", "Pending consequences must be meaningful non-blank strings.", state_path)

    if ready:
        required_values = {
            "scene_id": values.get("scene_id", ""),
            "ongoing_process": values.get("ongoing_process", ""),
            "resume_anchor": values.get("resume_anchor", ""),
            "last_causal_beat.returned_control_at": causal.get("returned_control_at", ""),
        }
        incomplete = [name for name, value in required_values.items() if not _meaningful_contract_value(value)]
        if incomplete:
            _add(
                findings,
                "error",
                "ready_scene_frame_incomplete",
                f"Ready scene frame is not resumable; fill: {', '.join(incomplete)}",
                state_path,
            )
        if not mode:
            _add(findings, "error", "ready_scene_frame_incomplete", "Ready scene frame requires a scene mode.", state_path)


def _check_player_state(
    state_text: str,
    state_path: Path,
    findings: list[dict],
    *,
    resolution_grounding: str,
) -> None:
    player_block = _block(state_text, "player")
    if not player_block:
        _add(findings, "error", "player_block_missing", "current_state.yaml is missing player block.", state_path)
        return

    player_values = _nested_values(player_block)
    for key in PLAYER_KEYS:
        if key not in player_values:
            _add(findings, "warning", "player_key_missing", f"Missing player key: {key}", state_path)

    stats = _nested_mapping(player_block, "stats")
    if resolution_grounding != "numeric":
        return
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

    setup_path = campaign_path / "setup_profile.yaml"
    setup_text = _read(setup_path, findings) if setup_path.is_file() else ""
    try:
        setup_schema = int(_clean_scalar(_top_level_values(setup_text).get("schema_version", "1")))
    except ValueError:
        setup_schema = 0
    new_contract_files = ["play_profile.yaml"] + (["visual_state.json"] if scope == "full" else [])
    for relative in new_contract_files:
        path = campaign_path / relative
        if setup_schema >= 3 and not path.is_file():
            _add(findings, "error", "v3_file_missing", f"Session contract v3 requires: {relative}", path)

    _check_setup_profile(campaign_path, findings)
    profile = _check_play_profile(campaign_path, findings)
    _check_advancement_contract(campaign_path, profile, findings)
    ready = bool(profile.get("ready"))
    _check_first_session_lifecycle(
        campaign_path,
        ready=ready,
        contract_v2=int(profile.get("schema_version", 0) or 0) >= 2,
        findings=findings,
    )
    _check_research_gate(campaign_path, findings, ready=ready)
    if scope == "full":
        _check_visual_handoff(campaign_path, findings)
        _check_visual_state(campaign_path, findings)
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
    if memory_version < 3 and "notes_for_next_turn" not in top_values:
        _add(findings, "warning", "top_level_key_missing", "Missing legacy top-level key: notes_for_next_turn", state_path)

    if continuity_revision >= 0:
        _check_persistence(
            campaign_path,
            state_text,
            revision=continuity_revision,
            scope=scope,
            findings=findings,
        )
        if scope == "full" and (campaign_path / "dashboard" / "dashboard_state.json").is_file():
            _run_dashboard_check(
                campaign_path,
                expected_revision=(continuity_revision if profile.get("dashboard_mode") == "on" else None),
                require_current=ready and profile.get("dashboard_mode") == "on",
                findings=findings,
            )

    resolution_grounding = str(profile.get("resolution_grounding", "numeric"))
    _check_player_state(
        state_text,
        state_path,
        findings,
        resolution_grounding=resolution_grounding,
    )
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

    _check_scene_frame(
        state_text,
        state_path,
        memory_version=memory_version,
        ready=ready,
        findings=findings,
    )

    if scope == "full":
        _check_markdown_mechanics(
            campaign_path,
            level_band,
            findings,
            resolution_grounding=resolution_grounding,
            ready=ready,
            contract_v3=memory_version >= 3 and int(profile.get("schema_version", 0) or 0) >= 2,
        )
        _check_knowledge_authority(campaign_path, findings)
        _check_world_evaluation_identity(campaign_path, findings)

    if memory_version >= 2 and all((campaign_path / relative).is_file() for relative in V2_FILES):
        _check_v2_memory(
            campaign_path,
            revision=continuity_revision,
            location=location,
            present_npcs=present_npcs,
            scope=scope,
            findings=findings,
        )

    _check_opening_coherence(
        campaign_path,
        current_location=location,
        present_npcs=present_npcs,
        findings=findings,
    )

    _check_ready_for_play(
        campaign_path,
        state_text,
        ready=ready,
        dashboard_mode=str(profile.get("dashboard_mode", "")),
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

"""Migrate a RePoG Lite campaign to the bounded GM runtime contracts.

The dry run is read-only.  Applying requires an existing campaign snapshot and
uses atomic replacement for every changed file.  The migration adds contract
metadata only; it never rewrites established fiction prose.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


POLICY_MIGRATIONS = {
    "scene_or_5_durable": "scene_checkpoint_or_5_durable",
    "scene_or_3_durable": "scene_checkpoint_or_3_durable",
    "scene_only": "scene_checkpoint_only",
}

AGENCY_CARD = """## At-The-Table Agency Card

- Local role:
- Independent project:
- Current mundane task:
- Pressure decision rule:
- Misbelief or recurring mistake:
- Hard boundary:
- Non-player obligation:
- Voice rhythm:
- Social tactic:
- Routine and availability:
- Next move if ignored:
- Evaluation trigger:
- Visible consequence channel:
- Offscreen trajectory status: needs_review
"""


def _atomic_write(path: Path, text: str) -> None:
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def _clean(value: str) -> str:
    return value.strip().strip("'\"`")


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return value or "scene"


def _yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _top(text: str, key: str, default: str = "") -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    return _clean(match.group(1)) if match else default


def _mapping(text: str, parent: str) -> dict[str, str]:
    match = re.search(rf"(?m)^{re.escape(parent)}:\s*$", text)
    if not match:
        return {}
    start = match.end()
    tail = text[start:]
    end_match = re.search(r"(?m)^\S[^:]*:\s*", tail)
    block = tail[: end_match.start()] if end_match else tail
    values: dict[str, str] = {}
    for line in block.splitlines():
        field = re.match(r"^\s{2}([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if field:
            values[field.group(1)] = _clean(field.group(2))
    return values


def _numeric_player_stats(state_text: str) -> bool:
    player_match = re.search(r"(?m)^player:\s*$", state_text)
    if not player_match:
        return False
    tail = state_text[player_match.end() :]
    end = re.search(r"(?m)^\S[^:]*:\s*", tail)
    player = tail[: end.start()] if end else tail
    stats_match = re.search(r"(?m)^\s{2}stats:\s*$", player)
    if not stats_match:
        return False
    stats_tail = player[stats_match.end() :]
    values = re.findall(r"(?m)^\s{4}[^:]+:\s*([1-5])\s*$", stats_tail)
    return len(values) == 8


def _narrative_anchors(profile_text: str) -> list[str]:
    inline = re.search(r"(?m)^\s{4}anchors:\s*\[(.*?)\]\s*$", profile_text)
    if inline:
        return [
            _clean(value)
            for value in inline.group(1).split(",")
            if _clean(value)
        ]
    block = re.search(r"(?m)^\s{4}anchors:\s*$", profile_text)
    if not block:
        return []
    tail = profile_text[block.end() :]
    end = re.search(r"(?m)^\s{0,4}\S", tail)
    body = tail[: end.start()] if end else tail
    return [
        _clean(match.group(1))
        for match in re.finditer(r"(?m)^\s{6}-\s*(.*?)\s*$", body)
        if _clean(match.group(1))
    ]


def _migrate_profile(text: str, state_text: str) -> tuple[str, list[str]]:
    actions: list[str] = []
    result = text
    schema = _top(result, "schema_version", "1")
    if schema == "1":
        result = re.sub(r"(?m)^schema_version:\s*1\s*$", "schema_version: 2", result, count=1)
        actions.append("upgrade play_profile schema 1 -> 2")

    for old, new in POLICY_MIGRATIONS.items():
        updated = re.sub(
            rf"(?m)^(\s*cold_distill_policy:\s*){re.escape(old)}\s*$",
            rf"\g<1>{new}",
            result,
        )
        if updated != result:
            actions.append(f"map cold_distill_policy {old} -> {new}")
            result = updated

    if not re.search(r"(?m)^\s{2}resolution_grounding:\s*", result):
        grounding = "numeric" if _numeric_player_stats(state_text) else "fictional"
        module_line = re.search(r"(?m)^\s{2}modules:.*$", result)
        if module_line:
            result = result[: module_line.end()] + f"\n  resolution_grounding: {grounding}" + result[module_line.end() :]
        else:
            mechanics = re.search(r"(?m)^mechanics:\s*$", result)
            if mechanics:
                result = result[: mechanics.end()] + f"\n  resolution_grounding: {grounding}" + result[mechanics.end() :]
        actions.append(f"set resolution_grounding from existing state: {grounding}")

    if not re.search(r"(?m)^\s{2}narrative_signature:\s*$", result):
        signature = (
            "\n  narrative_signature:\n"
            "    anchors: []\n"
            "    avoid_habits: []\n"
            "    interiority_policy: player_owned\n"
            "    sensory_focus: []\n"
            "    dialogue_balance: balanced\n"
            "    humor: situational\n"
            "    emotional_distance: close\n"
            "  breather_frequency: balanced\n"
            "  breather_exit_policy: player_led_with_established_triggers"
        )
        pacing = re.search(r"(?m)^\s{2}pacing:.*$", result)
        if pacing:
            result = result[: pacing.end()] + signature + result[pacing.end() :]
            actions.append("add Narrative Signature and breather defaults")
    else:
        # A partial hand-authored v2 contract is left intact rather than
        # overwriting judgment.  Surface it for human review in the report.
        for field, default in (
            ("breather_frequency", "balanced"),
            ("breather_exit_policy", "player_led_with_established_triggers"),
        ):
            if not re.search(rf"(?m)^\s{{2}}{field}:\s*", result):
                signature = re.search(r"(?m)^\s{2}narrative_signature:\s*$", result)
                if signature:
                    result = result[: signature.start()] + f"  {field}: {default}\n" + result[signature.start() :]
                    actions.append(f"add narration.{field}")

    return result, actions


def _migrate_state(text: str) -> tuple[str, list[str], list[str]]:
    actions: list[str] = []
    review: list[str] = []
    result = text
    version = _top(result, "memory_version", "1")
    if version in {"1", "2"}:
        if re.search(r"(?m)^memory_version:\s*\d+\s*$", result):
            result = re.sub(r"(?m)^memory_version:\s*\d+\s*$", "memory_version: 3", result, count=1)
        else:
            first_line = result.find("\n")
            result = result[: first_line + 1] + "memory_version: 3\n" + result[first_line + 1 :]
        actions.append(f"upgrade current_state memory {version} -> 3")

    if not re.search(r"(?m)^scene_frame:\s*$", result):
        scene = _mapping(result, "current_scene")
        player = _mapping(result, "player")
        revision = _top(result, "continuity_revision", "0")
        title = scene.get("title", "")
        location = scene.get("location", "")
        summary = scene.get("summary", "")
        pressure = scene.get("immediate_pressure", "")
        goal = player.get("current_goal", "")
        materialized = bool(title or location or summary)
        scene_id = f"scene-{_slug(location or title)}-r{revision}" if materialized else ""
        mode = "focused" if pressure else "ambient"
        uncertain = "needs_review" if materialized else ""
        frame = (
            "scene_frame:\n"
            f"  scene_id: {_yaml_quote(scene_id)}\n"
            f"  mode: {mode}\n"
            f"  ongoing_process: {_yaml_quote(summary or uncertain)}\n"
            f"  disruption: {_yaml_quote(pressure)}\n"
            "  last_causal_beat:\n"
            f"    player_intent: {_yaml_quote(goal or uncertain)}\n"
            f"    world_response: {_yaml_quote(summary or uncertain)}\n"
            f"    changed_fact: {_yaml_quote(uncertain)}\n"
            f"    returned_control_at: {_yaml_quote(uncertain)}\n"
            "  pending_consequences: []\n"
            f"  resume_anchor: {_yaml_quote(summary or uncertain)}\n\n"
        )
        insertion = re.search(r"(?m)^inventory:", result)
        position = insertion.start() if insertion else len(result)
        result = result[:position] + frame + result[position:]
        actions.append("derive bounded scene_frame from current scene truth")
        if materialized:
            review.append("scene_frame causal fields need review")
    return result, actions, review


def _migrate_style(text: str) -> tuple[str, list[str]]:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("style_state.json must contain an object")
    actions: list[str] = []
    if data.get("schema_version") != 3:
        data["schema_version"] = 3
        actions.append("upgrade style_state schema -> 3")
    if data.get("max_categorical_history") != 8:
        data["max_categorical_history"] = 8
        actions.append("bound categorical style history at 8")
    if "categorical_history" not in data:
        data["categorical_history"] = []
        actions.append("add empty categorical style history")
    return json.dumps(data, indent=2, ensure_ascii=True) + "\n", actions


def _migrate_character(text: str) -> tuple[str, bool]:
    tier = _top(text, "Tier").casefold()
    if tier not in {"t2", "t3"} or re.search(r"(?im)^##\s+At-The-Table Agency Card\s*$", text):
        return text, False
    power = re.search(r"(?m)^Power Band:.*$", text)
    if power:
        result = text[: power.end()] + "\n\n" + AGENCY_CARD.rstrip() + text[power.end() :]
    else:
        title = re.search(r"(?m)^#\s+.+$", text)
        position = title.end() if title else 0
        result = text[:position] + "\n\n" + AGENCY_CARD.rstrip() + "\n" + text[position:]
    return result, True


def _section(text: str, heading: str) -> str:
    match = re.search(rf"(?im)^##\s+{re.escape(heading)}\s*$", text)
    if not match:
        return ""
    tail = text[match.end() :]
    next_heading = re.search(r"(?m)^#{1,2}\s+", tail)
    return tail[: next_heading.start()] if next_heading else tail


def _bullet_values(section: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in section.splitlines():
        match = re.match(r"^\s*-\s+([^:]+):\s*(.*?)\s*$", line)
        if match:
            values[match.group(1).strip()] = _clean(match.group(2))
    return values


def _ownership_review(campaign: Path) -> list[str]:
    review: list[str] = []
    first_session = campaign / "first_session.md"
    if first_session.is_file() and not re.search(r"(?im)^Prep status:\s*`?(drafting|materialized|consumed)`?\s*$", first_session.read_text(encoding="utf-8")):
        review.append("first_session.md: legacy opening lifecycle needs review")

    legacy_knowledge_headings = (
        "What They Know About The Player",
        "What They Suspect",
        "Evidence They Have",
        "What The Faction Knows About The Player",
        "What The Faction Suspects",
    )
    legacy_relationship_headings = (
        "Relationships",
        "Current Relationships",
        "Relationship With Player",
        "Player Relationship",
    )
    for folder in ("characters", "factions"):
        root = campaign / folder
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.md")):
            if path.name.startswith("_"):
                continue
            text = path.read_text(encoding="utf-8")
            if any(re.search(rf"(?im)^##\s+{re.escape(heading)}\s*$", text) for heading in legacy_knowledge_headings):
                review.append(f"{folder}/{path.name}: move duplicated current knowledge into knowledge_boundaries.md")
            if any(re.search(rf"(?im)^##\s+{re.escape(heading)}\s*$", text) for heading in legacy_relationship_headings):
                review.append(f"{folder}/{path.name}: reconcile duplicated current relationship truth with relationship_map.md")

            if folder == "characters":
                card = _bullet_values(_section(text, "At-The-Table Agency Card"))
                if card.get("Offscreen trajectory status") == "active":
                    trajectory = _bullet_values(_section(text, "Offscreen Trajectory"))
                    required = (
                        "Goal and method",
                        "Obstacle or resource",
                        "Time horizon",
                        "Result shape",
                        "Visible channel",
                        "Last evaluation id",
                    )
                    if any(not trajectory.get(field) for field in required):
                        review.append(f"characters/{path.name}: active offscreen trajectory lacks required detail")
            else:
                legacy_move = any(
                    re.search(rf"(?im)^##\s+{re.escape(heading)}\s*$", text)
                    for heading in ("Current Move", "Next Move If Ignored", "Pressure Clock Or Escalation")
                )
                domain = _bullet_values(_section(text, "Current World Domain Reference")).get("Domain id", "")
                if legacy_move or not domain:
                    review.append(f"factions/{path.name}: reconcile current-move ownership with world_dynamics.md domain reference")
    return review


def _has_snapshot(campaign: Path) -> bool:
    snapshots = campaign / "snapshots"
    return snapshots.is_dir() and any(snapshots.glob("*/snapshot_manifest.json"))


def migrate(campaign_path: Path, *, apply: bool = False) -> dict[str, Any]:
    campaign = campaign_path.resolve()
    if not campaign.is_dir():
        return {"ok": False, "error": "campaign_path_not_found", "campaign_path": str(campaign)}
    if apply and not _has_snapshot(campaign):
        return {
            "ok": False,
            "error": "snapshot_required",
            "message": "Create a campaign snapshot before applying this migration.",
            "campaign_path": str(campaign),
        }

    planned: dict[Path, str] = {}
    actions: list[dict[str, str]] = []
    needs_review: list[str] = []
    try:
        profile_path = campaign / "play_profile.yaml"
        state_path = campaign / "current_state.yaml"
        profile_text = profile_path.read_text(encoding="utf-8")
        state_text = state_path.read_text(encoding="utf-8")
        legacy_profile = _top(profile_text, "schema_version", "1") == "1"
        profile_new, profile_actions = _migrate_profile(profile_text, state_text)
        state_new, state_actions, state_review = _migrate_state(state_text)
        if profile_new != profile_text:
            planned[profile_path] = profile_new
        if state_new != state_text:
            planned[state_path] = state_new
        actions.extend({"path": str(profile_path), "action": value} for value in profile_actions)
        actions.extend({"path": str(state_path), "action": value} for value in state_actions)
        needs_review.extend(state_review)
        meaningful_anchors = [
            value
            for value in _narrative_anchors(profile_new)
            if value.casefold() not in {"needs_review", "todo", "tbd", "unknown", "replace_me"}
        ]
        if legacy_profile and len(meaningful_anchors) < 3:
            needs_review.append("play_profile.yaml: Narrative Signature anchors need review")

        style_path = campaign / "style_state.json"
        if style_path.is_file():
            style_text = style_path.read_text(encoding="utf-8")
            style_new, style_actions = _migrate_style(style_text)
            if style_new != style_text:
                planned[style_path] = style_new
            actions.extend({"path": str(style_path), "action": value} for value in style_actions)

        characters = campaign / "characters"
        if characters.is_dir():
            for path in sorted(characters.glob("*.md")):
                if path.name.startswith("_"):
                    continue
                old = path.read_text(encoding="utf-8")
                new, changed = _migrate_character(old)
                if changed:
                    planned[path] = new
                    actions.append({"path": str(path), "action": "add Agency Card skeleton"})
                    needs_review.append(f"{path.name}: Agency Card and offscreen trajectory")
        needs_review.extend(_ownership_review(campaign))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": "migration_read_failed", "message": str(exc), "campaign_path": str(campaign)}

    if apply:
        try:
            for path, content in planned.items():
                _atomic_write(path, content)
        except OSError as exc:
            return {"ok": False, "error": "migration_write_failed", "message": str(exc), "campaign_path": str(campaign)}

    return {
        "ok": True,
        "mode": "apply" if apply else "dry-run",
        "campaign_path": str(campaign),
        "changed": bool(planned),
        "changed_files": [str(path) for path in planned],
        "actions": actions,
        "needs_review": sorted(set(needs_review)),
    }


def _print_human(result: dict[str, Any]) -> None:
    if not result.get("ok"):
        print(f"Migration blocked: {result.get('error')}: {result.get('message', '')}")
        return
    print(f"GM contract migration ({result['mode']}): {'changes planned' if result['changed'] else 'already current'}")
    for item in result["actions"]:
        print(f"- {item['action']} ({item['path']})")
    for item in result["needs_review"]:
        print(f"- NEEDS REVIEW: {item}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_path", help="Path to a RePoG Lite campaign.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Report changes without writing (default).")
    mode.add_argument("--apply", action="store_true", help="Apply after verifying that a snapshot already exists.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)
    result = migrate(Path(args.campaign_path), apply=args.apply)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        _print_human(result)
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())

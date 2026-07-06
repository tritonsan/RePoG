"""Run a small sanity check over a RePoG Lite campaign folder."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_FILES = [
    "world.md",
    "research_dossier.md",
    "next_act_prep.md",
    "boundaries.md",
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

REQUIRED_DIRS = [
    "characters",
    "places",
    "factions",
    "snapshots",
]

TOP_LEVEL_KEYS = [
    "campaign_id",
    "mode",
    "status",
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


def _slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def _normalize_level(value: str) -> str:
    return _slug(value.replace("/", " "))


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
    if total > max_total:
        _add(
            findings,
            "warning",
            "stat_budget_exceeded",
            f"Stat total {total} exceeds {level_band} budget {max_total}.",
            state_path,
        )

    too_high = sorted(name for name, value in parsed_stats.items() if value > recommended_max)
    for name in too_high:
        _add(
            findings,
            "warning",
            "stat_level_max_exceeded",
            f"Stat {name} exceeds recommended max {recommended_max} for {level_band}.",
            state_path,
        )


def check_campaign(campaign_path: Path) -> dict:
    campaign_path = campaign_path.resolve()
    findings: list[dict] = []

    if not campaign_path.exists() or not campaign_path.is_dir():
        _add(findings, "error", "campaign_path_not_found", "Campaign path is missing.", campaign_path)
        return _result(campaign_path, findings)

    for relative in REQUIRED_FILES:
        path = campaign_path / relative
        if not path.is_file():
            _add(findings, "error", "required_file_missing", f"Missing required file: {relative}", path)

    for relative in REQUIRED_DIRS:
        path = campaign_path / relative
        if not path.is_dir():
            _add(findings, "error", "required_dir_missing", f"Missing required directory: {relative}", path)

    state_path = campaign_path / "current_state.yaml"
    state_text = _read(state_path, findings) if state_path.is_file() else ""
    if not state_text:
        return _result(campaign_path, findings)

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

    _check_player_state(state_text, state_path, findings)

    scene_values = _nested_values(_block(state_text, "current_scene"))
    for key in SCENE_KEYS:
        if key not in scene_values:
            _add(findings, "warning", "scene_key_missing", f"Missing current_scene key: {key}", state_path)

    location = _clean_scalar(scene_values.get("location", ""))
    if location:
        if not _note_exists(campaign_path / "places", location):
            _add(
                findings,
                "warning",
                "location_note_missing",
                f"Current location has no matching place note: {location}",
                campaign_path / "places",
            )
    else:
        _add(findings, "info", "location_blank", "Current location is blank; expected for a fresh template.", state_path)

    present_npcs = _parse_inline_list(scene_values.get("present_npcs", ""))
    for npc in present_npcs:
        if not _note_exists(campaign_path / "characters", npc):
            _add(
                findings,
                "warning",
                "npc_note_missing",
                f"Present NPC has no matching character note: {npc}",
                campaign_path / "characters",
            )

    inventory = _parse_block_list(state_text, "inventory")
    duplicates = sorted({item for item in inventory if inventory.count(item) > 1})
    for item in duplicates:
        _add(findings, "warning", "duplicate_inventory_item", f"Inventory lists duplicate item: {item}", state_path)

    return _result(campaign_path, findings)


def _result(campaign_path: Path, findings: list[dict]) -> dict:
    error_count = sum(1 for finding in findings if finding["severity"] == "error")
    warning_count = sum(1 for finding in findings if finding["severity"] == "warning")
    info_count = sum(1 for finding in findings if finding["severity"] == "info")
    return {
        "ok": error_count == 0,
        "campaign_path": str(campaign_path),
        "error_count": error_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_path", help="Path to a Lite campaign folder.")
    args = parser.parse_args(argv)

    result = check_campaign(Path(args.campaign_path))
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())

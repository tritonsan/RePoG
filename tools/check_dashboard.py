"""Check a RePoG dashboard_state.json file for shape and player-safe text."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = {
    "schema_version",
    "updated_at",
    "refresh_interval_ms",
    "campaign",
    "theme",
    "scene",
    "player",
    "companions",
    "visible_npcs",
    "active_threads",
    "known_clues",
    "inventory",
    "map",
    "visuals",
}

REQUIRED_OBJECTS = {
    "campaign": {"title", "pitch", "tone"},
    "theme": {"accent", "background", "mood"},
    "scene": {"title", "location", "time", "summary", "pressure", "image"},
    "player": {"name", "concept", "condition", "goal", "stats", "capabilities"},
    "map": {"nodes", "edges"},
}

REQUIRED_LISTS = {
    "companions",
    "visible_npcs",
    "active_threads",
    "known_clues",
    "inventory",
    "visuals",
}

TECHNICAL_TEXT = re.compile(
    r"(?i)\b("
    r"gm-only|protected proper noun|protected name|prompt|tool|script|"
    r"agents\.md|skill\.md|yaml|markdown|validator|validation|"
    r"current_state|session_log|knowledge_boundaries|creation_ledger|"
    r"relationship_map|dashboard_state|check_state|check_dashboard|"
    r"implementation|internal id|raw id"
    r")\b"
)

RAW_ID = re.compile(r"\b[a-z][a-z0-9]+(?:_[a-z0-9]+)+\b")
MOJIBAKE = re.compile("[\\u00c3\\u00c4\\u00c5]")
ABSOLUTE_OR_EXTERNAL_PATH = re.compile(r"(?i)^(?:[a-z]:\\|/|https?://|file://)")


def _add(findings: list[dict], severity: str, rule: str, message: str, path: str) -> None:
    findings.append(
        {
            "severity": severity,
            "rule": rule,
            "message": message,
            "path": path,
        }
    )


def _is_asset_field(path: str) -> bool:
    parts = path.lower().split(".")
    return bool(parts and parts[-1] in {"image", "src", "asset", "thumbnail"})


def _check_asset_path(value: str, path: str, findings: list[dict]) -> bool:
    if not value:
        return True
    if value.startswith("assets/"):
        return True
    if ABSOLUTE_OR_EXTERNAL_PATH.search(value):
        _add(
            findings,
            "error",
            "dashboard_asset_external_or_absolute",
            "Dashboard image references should use relative assets/... paths.",
            path,
        )
        return False
    _add(
        findings,
        "warning",
        "dashboard_asset_nonstandard",
        "Dashboard image references should usually live under assets/.",
        path,
    )
    return True


def _scan_string(value: str, path: str, findings: list[dict]) -> None:
    if _is_asset_field(path) and _check_asset_path(value.strip(), path, findings):
        return

    if TECHNICAL_TEXT.search(value):
        _add(findings, "error", "dashboard_technical_leakage", "Player board text contains technical language.", path)

    if RAW_ID.search(value):
        _add(findings, "warning", "dashboard_raw_id", "Player board text looks like it contains a raw id.", path)

    if MOJIBAKE.search(value):
        _add(findings, "error", "dashboard_mojibake", "Player board text contains likely encoding corruption.", path)


def _walk_strings(value: Any, path: str, findings: list[dict]) -> None:
    if isinstance(value, str):
        _scan_string(value, path, findings)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_strings(item, f"{path}[{index}]", findings)
    elif isinstance(value, dict):
        for key, item in value.items():
            _walk_strings(item, f"{path}.{key}" if path else str(key), findings)


def check_dashboard(path: Path) -> dict:
    findings: list[dict] = []
    path = path.resolve()

    if not path.is_file():
        _add(findings, "error", "dashboard_state_missing", "Dashboard state file is missing.", str(path))
        return _result(path, findings)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _add(findings, "error", "dashboard_state_invalid_json", str(exc), str(path))
        return _result(path, findings)

    if not isinstance(data, dict):
        _add(findings, "error", "dashboard_state_not_object", "Dashboard state must be a JSON object.", str(path))
        return _result(path, findings)

    for key in sorted(REQUIRED_TOP_LEVEL - data.keys()):
        _add(findings, "error", "dashboard_key_missing", f"Missing top-level key: {key}", key)

    for key, required in REQUIRED_OBJECTS.items():
        value = data.get(key)
        if not isinstance(value, dict):
            _add(findings, "error", "dashboard_object_missing", f"{key} must be an object.", key)
            continue
        for child in sorted(required - value.keys()):
            _add(findings, "warning", "dashboard_child_key_missing", f"Missing key: {key}.{child}", f"{key}.{child}")

    for key in sorted(REQUIRED_LISTS):
        if key in data and not isinstance(data[key], list):
            _add(findings, "error", "dashboard_list_expected", f"{key} must be a list.", key)

    interval = data.get("refresh_interval_ms")
    if not isinstance(interval, int) or interval < 1500:
        _add(
            findings,
            "warning",
            "dashboard_refresh_interval",
            "refresh_interval_ms should be an integer of at least 1500.",
            "refresh_interval_ms",
        )

    stats = data.get("player", {}).get("stats") if isinstance(data.get("player"), dict) else None
    if stats is not None and not isinstance(stats, dict):
        _add(findings, "error", "dashboard_player_stats", "player.stats must be an object when present.", "player.stats")

    _walk_strings(data, "", findings)
    return _result(path, findings)


def _result(path: Path, findings: list[dict]) -> dict:
    error_count = sum(1 for finding in findings if finding["severity"] == "error")
    warning_count = sum(1 for finding in findings if finding["severity"] == "warning")
    info_count = sum(1 for finding in findings if finding["severity"] == "info")
    return {
        "ok": error_count == 0,
        "dashboard_path": str(path),
        "error_count": error_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dashboard_state", help="Path to dashboard_state.json.")
    args = parser.parse_args(argv)

    result = check_dashboard(Path(args.dashboard_state))
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())

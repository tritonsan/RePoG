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

V2_MAP_KEYS = {
    "mode",
    "summary",
    "background_image",
    "bounds",
    "current_node_id",
    "nodes",
    "edges",
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
    return bool(parts and parts[-1] in {"image", "portrait", "src", "asset", "thumbnail", "background_image"})


def _is_structural_field(path: str) -> bool:
    parts = path.lower().split(".")
    if not parts:
        return False
    return parts[-1] in {"id", "current_node_id", "from", "to", "mode"}


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

    if _is_structural_field(path):
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


def _check_v2_map(data: dict, findings: list[dict]) -> None:
    version = data.get("dashboard_version", 1)
    if version in ("", None):
        version = 1

    try:
        version_number = int(version)
    except (TypeError, ValueError):
        _add(findings, "error", "dashboard_version_invalid", "dashboard_version should be an integer.", "dashboard_version")
        return

    if version_number < 2:
        return

    map_data = data.get("map")
    if not isinstance(map_data, dict):
        return

    for key in sorted(V2_MAP_KEYS - map_data.keys()):
        _add(findings, "error", "dashboard_v2_map_key_missing", f"Missing V2 map key: map.{key}", f"map.{key}")

    mode = map_data.get("mode")
    if mode != "leaflet_simple":
        _add(findings, "error", "dashboard_v2_map_mode", "V2 map.mode should be 'leaflet_simple'.", "map.mode")

    bounds = map_data.get("bounds")
    if not isinstance(bounds, dict):
        _add(findings, "error", "dashboard_v2_map_bounds", "V2 map.bounds must be an object.", "map.bounds")
    else:
        for key in ["width", "height"]:
            value = bounds.get(key)
            if not isinstance(value, (int, float)) or value <= 0:
                _add(
                    findings,
                    "error",
                    "dashboard_v2_map_bounds_value",
                    f"V2 map.bounds.{key} must be a positive number.",
                    f"map.bounds.{key}",
                )

    nodes = map_data.get("nodes")
    if isinstance(nodes, list):
        for index, node in enumerate(nodes):
            if not isinstance(node, dict):
                _add(findings, "error", "dashboard_v2_map_node", "V2 map node must be an object.", f"map.nodes[{index}]")
                continue
            for key in ["id", "label", "x", "y"]:
                if key not in node:
                    _add(
                        findings,
                        "warning",
                        "dashboard_v2_map_node_key_missing",
                        f"V2 map node should include {key}.",
                        f"map.nodes[{index}].{key}",
                    )
            for key in ["x", "y"]:
                if key in node and not isinstance(node[key], (int, float)):
                    _add(
                        findings,
                        "error",
                        "dashboard_v2_map_node_coordinate",
                        f"V2 map node {key} must be a number.",
                        f"map.nodes[{index}].{key}",
                    )

    edges = map_data.get("edges")
    if isinstance(edges, list):
        for index, edge in enumerate(edges):
            if not isinstance(edge, dict):
                _add(findings, "error", "dashboard_v2_map_edge", "V2 map edge must be an object.", f"map.edges[{index}]")
                continue
            for key in ["from", "to"]:
                if key not in edge:
                    _add(
                        findings,
                        "warning",
                        "dashboard_v2_map_edge_key_missing",
                        f"V2 map edge should include {key}.",
                        f"map.edges[{index}].{key}",
                    )


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

    _check_v2_map(data, findings)
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

"""Validate a player-safe RePoG dashboard state (V2 or tile-based V3)."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ALLOWED_TILE_TYPES = {
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
    "documents",
}
ALLOWED_REFRESH_STATUS = {"setup_pending", "current", "stale", "refreshing", "error", "disabled"}
ATLAS_SCALE_MODES = {"region", "city", "interior", "network"}
ATLAS_PROJECTIONS = {"spatial", "schematic"}
ATLAS_SKINS = {"auto", "minimal", "survey", "civic", "field", "systems"}
ATLAS_STYLE_ROLES = {
    "place",
    "landmark",
    "route",
    "boundary",
    "water",
    "region",
    "terrain",
    "structure",
    "hazard",
    "neutral",
}
ATLAS_KNOWLEDGE_STATES = {"confirmed", "reported", "inferred", "stale", "unknown"}
ATLAS_ACCESS_STATES = {"open", "conditional", "blocked", "unknown"}
ATLAS_RISK_STATES = {"none", "caution", "danger", "unknown"}
ATLAS_GEOMETRY_TYPES = {"point", "line", "area"}
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
RAW_ID = re.compile(r"\b[a-z][a-z0-9]+(?:_[a-z0-9]+)+\b")
MOJIBAKE = re.compile("[\u00c3\u00c4\u00c5]")
ABSOLUTE_OR_EXTERNAL_PATH = re.compile(r"(?i)^(?:[a-z]:[\\/]|/|https?://|file://)")
TECHNICAL_TEXT = re.compile(
    r"(?i)(?:\bgm[- ]only\b|\bprotected (?:proper )?name\b|\binternal id\b|"
    r"\bagents\.md\b|\bskill\.md\b|\bcurrent_state\b|\bsession_log\b|"
    r"\bknowledge_boundaries\b|\bcreation_ledger\b|\brelationship_map\b|"
    r"\bdashboard_state\b|\bcheck_state\b|\bcheck_dashboard\b)"
)
ASSET_KEYS = {"image", "portrait", "src", "asset", "thumbnail", "background_image", "catalog_path"}
STRUCTURAL_KEYS = {
    "id",
    "type",
    "status",
    "current_node_id",
    "current_feature_id",
    "from",
    "to",
    "mode",
    "scene_id",
    "origin",
    "style_role",
    "knowledge_state",
    "access_state",
    "risk_state",
}
FORBIDDEN_KEYS = {
    "gm_only", "secret", "hidden_truth", "protected_name", "unrevealed",
    "epistemic_basis", "claim_basis", "claim_class", "fact_id", "fact_ids",
    "actual_provenance", "operation_id", "source_event_ref", "holders",
}


def _add(findings: list[dict], severity: str, rule: str, message: str, path: str) -> None:
    findings.append({"severity": severity, "rule": rule, "message": message, "path": path})


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _asset_path(
    value: str,
    path: str,
    findings: list[dict],
    dashboard_dir: Path | None,
    require_assets: bool,
) -> None:
    clean = value.strip().replace("\\", "/")
    if not clean:
        return
    if ABSOLUTE_OR_EXTERNAL_PATH.search(clean) or not clean.startswith("assets/"):
        _add(findings, "error", "dashboard_asset_path", "Assets must use a relative assets/... path.", path)
        return
    parts = Path(clean).parts
    if ".." in parts or any(part.lower() in {"_drafts", "drafts"} for part in parts):
        _add(findings, "error", "dashboard_asset_unsafe", "Draft or escaping asset paths are not player-safe.", path)
        return
    if require_assets and dashboard_dir is not None and not (dashboard_dir / Path(clean)).is_file():
        _add(findings, "error", "dashboard_asset_missing", "Referenced dashboard asset does not exist.", path)


def _walk(
    value: Any,
    path: str,
    findings: list[dict],
    dashboard_dir: Path | None,
    require_assets: bool,
) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}" if path else str(key)
            if key.lower() in FORBIDDEN_KEYS:
                _add(findings, "error", "dashboard_hidden_field", "Hidden or GM-only fields cannot enter the player board.", child)
            if isinstance(item, str) and key.lower() in ASSET_KEYS:
                _asset_path(item, child, findings, dashboard_dir, require_assets)
            else:
                _walk(item, child, findings, dashboard_dir, require_assets)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _walk(item, f"{path}[{index}]", findings, dashboard_dir, require_assets)
        return
    if not isinstance(value, str):
        return
    leaf = path.rsplit(".", 1)[-1].split("[", 1)[0]
    if leaf in STRUCTURAL_KEYS:
        return
    if TECHNICAL_TEXT.search(value):
        _add(findings, "error", "dashboard_technical_leakage", "Player board text contains internal campaign language.", path)
    if MOJIBAKE.search(value):
        _add(findings, "error", "dashboard_mojibake", "Player board text contains likely encoding corruption.", path)
    if RAW_ID.search(value):
        _add(findings, "warning", "dashboard_raw_id", "Player board text looks like it contains a raw id.", path)


def _protected_names(campaign_path: Path) -> list[str]:
    path = campaign_path / "knowledge_boundaries.md" if campaign_path.is_dir() else campaign_path
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    section = re.search(r"(?ms)^## Protected Proper Nouns\s*$\n(?P<body>.*?)(?=^##\s|\Z)", text)
    if section is None:
        return []
    body = section.group("body")
    headings = list(re.finditer(r"(?m)^###\s+(.+?)\s*$", body))
    names: list[str] = []
    for index, heading in enumerate(headings):
        name = heading.group(1).strip().strip("`*_ ")
        if name.casefold() in {"protected name", "name", "example"}:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        entry = body[heading.end() : end]
        match = re.search(r"(?mi)^\s*-\s*Status:\s*(.+?)\s*$", entry)
        status = match.group(1).strip().strip("`*_ ").casefold() if match else ""
        if not any(re.match(rf"^{re.escape(safe)}\b", status) for safe in ("revealed", "pc-known", "player-known", "confirmed")):
            names.append(name)
    return sorted(set(names), key=str.casefold)


def _walk_protected(value: Any, path: str, names: list[str], findings: list[dict]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _walk_protected(item, f"{path}.{key}" if path else str(key), names, findings)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_protected(item, f"{path}[{index}]", names, findings)
    elif isinstance(value, str):
        for name in names:
            if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", value, re.IGNORECASE):
                _add(
                    findings,
                    "error",
                    "dashboard_protected_name",
                    "Player board contains an unrevealed campaign-protected name.",
                    path,
                )


def _check_theme(theme: Any, findings: list[dict]) -> None:
    if not isinstance(theme, dict):
        _add(findings, "error", "dashboard_theme", "theme must be an object.", "theme")
        return
    for key in ("accent", "background"):
        value = theme.get(key)
        if not isinstance(value, str) or not HEX_COLOR.fullmatch(value):
            _add(findings, "error", "dashboard_theme_color", f"theme.{key} must be a six-digit hex color.", f"theme.{key}")
    if not isinstance(theme.get("mood", ""), str):
        _add(findings, "error", "dashboard_theme_mood", "theme.mood must be text.", "theme.mood")


def _check_stats(stats: Any, path: str, findings: list[dict]) -> None:
    if not isinstance(stats, dict):
        _add(findings, "error", "dashboard_stats", "Stats must be an object.", path)
        return
    for name, value in stats.items():
        if not isinstance(name, str) or not name.strip():
            _add(findings, "error", "dashboard_stat_name", "Every stat needs a visible label.", path)
        if not _is_number(value):
            _add(findings, "error", "dashboard_stat_value", "Stat values must be finite numbers.", f"{path}.{name}")


def _check_legacy_map(map_data: dict, path: str, findings: list[dict]) -> None:
    """Validate the original Dashboard V2/V3 node-and-edge map contract."""

    bounds = map_data.get("bounds")
    if not isinstance(bounds, dict):
        _add(findings, "error", "dashboard_map_bounds", "Map bounds must be an object.", f"{path}.bounds")
        return
    width, height = bounds.get("width"), bounds.get("height")
    if not _is_number(width) or width <= 0 or not _is_number(height) or height <= 0:
        _add(findings, "error", "dashboard_map_bounds", "Map width and height must be positive numbers.", f"{path}.bounds")
        return

    nodes = map_data.get("nodes")
    edges = map_data.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        _add(findings, "error", "dashboard_map_lists", "Map nodes and edges must be lists.", path)
        return

    ids: set[str] = set()
    for index, node in enumerate(nodes):
        node_path = f"{path}.nodes[{index}]"
        if not isinstance(node, dict):
            _add(findings, "error", "dashboard_map_node", "Map nodes must be objects.", node_path)
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id.strip():
            _add(findings, "error", "dashboard_map_node_id", "Map nodes need a non-empty id.", f"{node_path}.id")
        elif node_id in ids:
            _add(findings, "error", "dashboard_map_duplicate_node", "Map node ids must be unique.", f"{node_path}.id")
        else:
            ids.add(node_id)
        if not isinstance(node.get("label"), str) or not node.get("label", "").strip():
            _add(findings, "error", "dashboard_map_node_label", "Map nodes need a visible label.", f"{node_path}.label")
        x, y = node.get("x"), node.get("y")
        if not _is_number(x) or not _is_number(y):
            _add(findings, "error", "dashboard_map_coordinate", "Map coordinates must be finite numbers.", node_path)
        elif not (0 <= x <= width and 0 <= y <= height):
            _add(findings, "error", "dashboard_map_out_of_bounds", "Map node lies outside the declared bounds.", node_path)

    current = map_data.get("current_node_id", "")
    if current and current not in ids:
        _add(findings, "error", "dashboard_map_current_node", "current_node_id must reference a map node.", f"{path}.current_node_id")
    seen_edges: set[tuple[str, str]] = set()
    for index, edge in enumerate(edges):
        edge_path = f"{path}.edges[{index}]"
        if not isinstance(edge, dict):
            _add(findings, "error", "dashboard_map_edge", "Map edges must be objects.", edge_path)
            continue
        start, end = edge.get("from"), edge.get("to")
        if start not in ids or end not in ids:
            _add(findings, "error", "dashboard_map_edge_endpoint", "Every map edge endpoint must reference an existing node.", edge_path)
            continue
        key = (str(start), str(end))
        if key in seen_edges:
            _add(findings, "error", "dashboard_map_duplicate_edge", "Duplicate map edges are not allowed.", edge_path)
        seen_edges.add(key)


def _atlas_coordinate(
    value: Any,
    path: str,
    findings: list[dict],
    width: float | int | None,
    height: float | int | None,
) -> bool:
    if not isinstance(value, list) or len(value) != 2 or not all(_is_number(item) for item in value):
        _add(
            findings,
            "error",
            "dashboard_atlas_coordinate",
            "Atlas coordinates must be finite [x, y] number pairs.",
            path,
        )
        return False
    x, y = value
    if width is not None and height is not None and not (0 <= x <= width and 0 <= y <= height):
        _add(
            findings,
            "error",
            "dashboard_atlas_out_of_bounds",
            "Atlas coordinate lies outside the declared coordinate space.",
            path,
        )
        return False
    return True


def _check_atlas_map(map_data: dict, path: str, findings: list[dict]) -> None:
    coordinate_space = map_data.get("coordinate_space")
    width: float | int | None = None
    height: float | int | None = None
    if not isinstance(coordinate_space, dict):
        _add(
            findings,
            "error",
            "dashboard_atlas_coordinate_space",
            "Atlas coordinate_space must be an object.",
            f"{path}.coordinate_space",
        )
    else:
        if coordinate_space.get("type") != "cartesian":
            _add(
                findings,
                "error",
                "dashboard_atlas_coordinate_space",
                "Atlas coordinate_space.type must be cartesian.",
                f"{path}.coordinate_space.type",
            )
        if coordinate_space.get("origin") != "top_left":
            _add(
                findings,
                "error",
                "dashboard_atlas_coordinate_space",
                "Atlas coordinate_space.origin must be top_left.",
                f"{path}.coordinate_space.origin",
            )
        candidate_width, candidate_height = coordinate_space.get("width"), coordinate_space.get("height")
        if not _is_number(candidate_width) or candidate_width <= 0:
            _add(
                findings,
                "error",
                "dashboard_atlas_coordinate_bounds",
                "Atlas coordinate_space.width must be a positive finite number.",
                f"{path}.coordinate_space.width",
            )
        else:
            width = candidate_width
        if not _is_number(candidate_height) or candidate_height <= 0:
            _add(
                findings,
                "error",
                "dashboard_atlas_coordinate_bounds",
                "Atlas coordinate_space.height must be a positive finite number.",
                f"{path}.coordinate_space.height",
            )
        else:
            height = candidate_height

    for key, allowed, rule in (
        ("scale_mode", ATLAS_SCALE_MODES, "dashboard_atlas_scale_mode"),
        ("projection", ATLAS_PROJECTIONS, "dashboard_atlas_projection"),
        ("skin", ATLAS_SKINS, "dashboard_atlas_skin"),
    ):
        if map_data.get(key) not in allowed:
            _add(
                findings,
                "error",
                rule,
                f"Atlas {key} must be one of: {', '.join(sorted(allowed))}.",
                f"{path}.{key}",
            )

    features = map_data.get("features")
    if not isinstance(features, list):
        _add(
            findings,
            "error",
            "dashboard_atlas_features",
            "Atlas features must be a list.",
            f"{path}.features",
        )
        return

    ids: set[str] = set()
    geometry_types: dict[str, str] = {}
    route_refs: list[tuple[str, Any, Any]] = []
    for index, feature in enumerate(features):
        feature_path = f"{path}.features[{index}]"
        if not isinstance(feature, dict):
            _add(findings, "error", "dashboard_atlas_feature", "Atlas features must be objects.", feature_path)
            continue

        feature_id = feature.get("id")
        valid_id = isinstance(feature_id, str) and bool(feature_id.strip())
        if not valid_id:
            _add(
                findings,
                "error",
                "dashboard_atlas_feature_id",
                "Atlas features need a non-empty id.",
                f"{feature_path}.id",
            )
        elif feature_id in ids:
            _add(
                findings,
                "error",
                "dashboard_atlas_duplicate_feature",
                "Atlas feature ids must be unique.",
                f"{feature_path}.id",
            )
        else:
            ids.add(feature_id)

        presentation_value = feature.get("presentation_only", False)
        presentation_only = presentation_value is True
        if "presentation_only" in feature and not isinstance(presentation_value, bool):
            _add(
                findings,
                "error",
                "dashboard_atlas_presentation_only",
                "Atlas presentation_only must be true or false.",
                f"{feature_path}.presentation_only",
            )
        if presentation_only and feature.get("style_role") != "neutral":
            _add(
                findings,
                "error",
                "dashboard_atlas_presentation_only",
                "Presentation-only Atlas features must use the neutral style_role.",
                f"{feature_path}.style_role",
            )
        label_visible = isinstance(feature.get("label"), str) and bool(feature.get("label", "").strip())
        if not label_visible and not (presentation_only and feature.get("style_role") == "neutral"):
            _add(
                findings,
                "error",
                "dashboard_atlas_feature_label",
                "Atlas features need a visible label.",
                f"{feature_path}.label",
            )

        if "style_role" in feature and feature.get("style_role") not in ATLAS_STYLE_ROLES:
            _add(
                findings,
                "error",
                "dashboard_atlas_style_role",
                f"Atlas style_role must be one of: {', '.join(sorted(ATLAS_STYLE_ROLES))}.",
                f"{feature_path}.style_role",
            )
        for key, allowed, rule in (
            ("knowledge_state", ATLAS_KNOWLEDGE_STATES, "dashboard_atlas_knowledge_state"),
            ("access_state", ATLAS_ACCESS_STATES, "dashboard_atlas_access_state"),
            ("risk_state", ATLAS_RISK_STATES, "dashboard_atlas_risk_state"),
        ):
            if key in feature and feature.get(key) not in allowed:
                _add(
                    findings,
                    "error",
                    rule,
                    f"Atlas {key} must be one of: {', '.join(sorted(allowed))}.",
                    f"{feature_path}.{key}",
                )
        if feature.get("knowledge_state") == "unknown":
            _add(
                findings,
                "error",
                "dashboard_atlas_unknown_feature",
                "Features with unknown knowledge must be omitted from the player Atlas.",
                f"{feature_path}.knowledge_state",
            )

        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            _add(
                findings,
                "error",
                "dashboard_atlas_geometry",
                "Atlas feature geometry must be an object.",
                f"{feature_path}.geometry",
            )
            continue
        geometry_type = geometry.get("type")
        if geometry_type not in ATLAS_GEOMETRY_TYPES:
            _add(
                findings,
                "error",
                "dashboard_atlas_geometry_type",
                "Atlas geometry.type must be point, line, or area.",
                f"{feature_path}.geometry.type",
            )
            continue
        if valid_id and feature_id not in geometry_types:
            geometry_types[feature_id] = geometry_type
        coordinates = geometry.get("coordinates")
        if geometry_type == "point":
            _atlas_coordinate(coordinates, f"{feature_path}.geometry.coordinates", findings, width, height)
        else:
            minimum = 2 if geometry_type == "line" else 3
            if not isinstance(coordinates, list) or len(coordinates) < minimum:
                _add(
                    findings,
                    "error",
                    "dashboard_atlas_geometry_coordinates",
                    f"Atlas {geometry_type} geometry needs at least {minimum} coordinate pairs.",
                    f"{feature_path}.geometry.coordinates",
                )
            else:
                for coordinate_index, coordinate in enumerate(coordinates):
                    _atlas_coordinate(
                        coordinate,
                        f"{feature_path}.geometry.coordinates[{coordinate_index}]",
                        findings,
                        width,
                        height,
                    )

        has_from, has_to = "from" in feature, "to" in feature
        if presentation_only and (has_from or has_to):
            _add(
                findings,
                "error",
                "dashboard_atlas_presentation_route",
                "Presentation-only Atlas features cannot have route endpoints.",
                feature_path,
            )
        elif has_from or has_to:
            if geometry_type != "line" or not has_from or not has_to:
                _add(
                    findings,
                    "error",
                    "dashboard_atlas_route_refs",
                    "Atlas route from/to references must appear together on a line feature.",
                    feature_path,
                )
            else:
                route_refs.append((feature_path, feature.get("from"), feature.get("to")))

    current = map_data.get("current_feature_id", "")
    if not isinstance(current, str):
        _add(
            findings,
            "error",
            "dashboard_atlas_current_feature",
            "current_feature_id must be text when provided.",
            f"{path}.current_feature_id",
        )
    elif current and current not in ids:
        _add(
            findings,
            "error",
            "dashboard_atlas_current_feature",
            "current_feature_id must reference an Atlas feature.",
            f"{path}.current_feature_id",
        )
    elif current and geometry_types.get(current) != "point":
        _add(
            findings,
            "error",
            "dashboard_atlas_current_feature_geometry",
            "current_feature_id must reference a point feature.",
            f"{path}.current_feature_id",
        )

    for feature_path, start, end in route_refs:
        for key, endpoint in (("from", start), ("to", end)):
            if not isinstance(endpoint, str) or not endpoint.strip() or endpoint not in ids:
                _add(
                    findings,
                    "error",
                    "dashboard_atlas_route_endpoint",
                    "Atlas route endpoints must reference existing features.",
                    f"{feature_path}.{key}",
                )
            elif geometry_types.get(endpoint) != "point":
                _add(
                    findings,
                    "error",
                    "dashboard_atlas_route_endpoint_geometry",
                    "Atlas route endpoints must reference point features.",
                    f"{feature_path}.{key}",
                )


def _check_map(map_data: Any, path: str, findings: list[dict]) -> None:
    if not isinstance(map_data, dict):
        _add(findings, "error", "dashboard_map", "Map tile data must be an object.", path)
        return
    if "atlas_version" not in map_data:
        _check_legacy_map(map_data, path, findings)
        return
    atlas_version = map_data.get("atlas_version")
    if isinstance(atlas_version, bool) or atlas_version != 1:
        _add(
            findings,
            "error",
            "dashboard_atlas_version",
            "atlas_version must be the integer 1.",
            f"{path}.atlas_version",
        )
        return
    _check_atlas_map(map_data, path, findings)


def _check_items(items: Any, path: str, findings: list[dict]) -> None:
    if not isinstance(items, list):
        _add(findings, "error", "dashboard_tile_items", "Tile data.items must be a list.", path)


def _check_documents(data: dict, path: str, findings: list[dict]) -> None:
    allowed = {"catalog_path", "summary", "default_view"}
    if set(data) - allowed:
        _add(findings, "error", "dashboard_documents_contract", "Documents tile contains unsupported fields.", path)
    if data.get("catalog_path") != "assets/world_voices/catalog.json":
        _add(findings, "error", "dashboard_documents_catalog", "Documents tile must use the bounded player-safe World Voices catalog.", f"{path}.catalog_path")
    if data.get("default_view", "inbox") not in {"inbox", "public", "archive", "threads"}:
        _add(findings, "error", "dashboard_documents_default_view", "Documents default_view must be inbox, public, archive, or threads.", f"{path}.default_view")
    if "summary" in data and (not isinstance(data["summary"], str) or len(data["summary"]) > 500):
        _add(findings, "error", "dashboard_documents_summary", "Documents summary must be bounded text.", f"{path}.summary")


def _check_v3(data: dict, findings: list[dict]) -> None:
    for key in ("schema_version", "dashboard_version", "dashboard_revision", "source_revision", "scene_id", "updated_at", "refresh_interval_ms", "refresh", "campaign", "theme", "tiles"):
        if key not in data:
            _add(findings, "error", "dashboard_key_missing", f"Missing V3 key: {key}", key)
    revision = data.get("source_revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        _add(findings, "error", "dashboard_revision", "source_revision must be a non-negative integer.", "source_revision")
    dashboard_revision = data.get("dashboard_revision")
    if not isinstance(dashboard_revision, int) or isinstance(dashboard_revision, bool) or dashboard_revision < 0:
        _add(findings, "error", "dashboard_revision", "dashboard_revision must be a non-negative integer.", "dashboard_revision")
    if not isinstance(data.get("scene_id"), str):
        _add(findings, "error", "dashboard_scene_id", "scene_id must be text (blank is valid during setup).", "scene_id")
    stamp = data.get("updated_at")
    if not isinstance(stamp, str):
        _add(findings, "error", "dashboard_updated_at", "updated_at must be an ISO timestamp or blank during setup.", "updated_at")
    elif stamp:
        try:
            datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError:
            _add(findings, "error", "dashboard_updated_at", "updated_at must be a valid ISO timestamp.", "updated_at")
    refresh = data.get("refresh")
    if not isinstance(refresh, dict):
        _add(findings, "error", "dashboard_refresh", "refresh must be an object.", "refresh")
    else:
        if refresh.get("status") not in ALLOWED_REFRESH_STATUS:
            _add(findings, "error", "dashboard_refresh_status", "refresh.status is not supported.", "refresh.status")
        if not isinstance(refresh.get("reason"), str) or not refresh.get("reason", "").strip():
            _add(findings, "error", "dashboard_refresh_reason", "refresh.reason must explain the board state.", "refresh.reason")
    interval = data.get("refresh_interval_ms")
    if not isinstance(interval, int) or isinstance(interval, bool) or not 1500 <= interval <= 60000:
        _add(findings, "error", "dashboard_refresh_interval", "refresh_interval_ms must be an integer from 1500 to 60000.", "refresh_interval_ms")
    campaign = data.get("campaign")
    if not isinstance(campaign, dict) or any(not isinstance(campaign.get(key), str) for key in ("title", "pitch", "tone")):
        _add(findings, "error", "dashboard_campaign", "campaign needs text title, pitch, and tone fields.", "campaign")
    _check_theme(data.get("theme"), findings)

    tiles = data.get("tiles")
    if not isinstance(tiles, list):
        _add(findings, "error", "dashboard_tiles", "tiles must be a list.", "tiles")
        return
    tile_ids: set[str] = set()
    for index, tile in enumerate(tiles):
        tile_path = f"tiles[{index}]"
        if not isinstance(tile, dict):
            _add(findings, "error", "dashboard_tile", "Every tile must be an object.", tile_path)
            continue
        tile_id, tile_type = tile.get("id"), tile.get("type")
        if not isinstance(tile_id, str) or not tile_id.strip():
            _add(findings, "error", "dashboard_tile_id", "Every tile needs a non-empty id.", f"{tile_path}.id")
        elif tile_id in tile_ids:
            _add(findings, "error", "dashboard_duplicate_tile", "Tile ids must be unique.", f"{tile_path}.id")
        else:
            tile_ids.add(tile_id)
        if tile_type not in ALLOWED_TILE_TYPES:
            _add(findings, "error", "dashboard_tile_type", "Tile type is not in the V3 allow-list.", f"{tile_path}.type")
        if not isinstance(tile.get("title"), str) or not tile.get("title", "").strip():
            _add(findings, "error", "dashboard_tile_title", "Every tile needs a visible title.", f"{tile_path}.title")
        if "order" in tile and (not isinstance(tile["order"], int) or isinstance(tile["order"], bool)):
            _add(findings, "error", "dashboard_tile_order", "Tile order must be an integer.", f"{tile_path}.order")
        tile_data = tile.get("data")
        if not isinstance(tile_data, dict):
            _add(findings, "error", "dashboard_tile_data", "Every tile needs a data object.", f"{tile_path}.data")
            continue
        if tile_type == "stats":
            _check_stats(tile_data.get("stats"), f"{tile_path}.data.stats", findings)
        elif tile_type == "map":
            _check_map(tile_data, f"{tile_path}.data", findings)
        elif tile_type == "documents":
            _check_documents(tile_data, f"{tile_path}.data", findings)
        elif tile_type in {"resources", "clocks", "conditions", "companions", "people", "threads", "clues", "inventory", "gallery"}:
            _check_items(tile_data.get("items"), f"{tile_path}.data.items", findings)
        if tile_type == "gallery" and isinstance(tile_data.get("items"), list):
            for item_index, item in enumerate(tile_data["items"]):
                item_path = f"{tile_path}.data.items[{item_index}]"
                if not isinstance(item, dict) or item.get("status", "accepted") != "accepted":
                    _add(findings, "error", "dashboard_gallery_draft", "Only accepted visual objects may appear in a gallery tile.", item_path)
                elif not isinstance(item.get("name"), str) or not item.get("name", "").strip() or not isinstance(item.get("image"), str) or not item.get("image", "").strip():
                    _add(findings, "error", "dashboard_gallery_item", "Accepted gallery items need a visible name and image.", item_path)


def _check_v2(data: dict, findings: list[dict]) -> None:
    required = {"schema_version", "updated_at", "refresh_interval_ms", "campaign", "theme", "scene", "player", "companions", "visible_npcs", "active_threads", "known_clues", "inventory", "map", "visuals"}
    for key in sorted(required - data.keys()):
        _add(findings, "error", "dashboard_key_missing", f"Missing V2 key: {key}", key)
    _check_theme(data.get("theme"), findings)
    player = data.get("player")
    if not isinstance(player, dict):
        _add(findings, "error", "dashboard_player", "player must be an object.", "player")
    elif "stats" in player:
        _check_stats(player["stats"], "player.stats", findings)
    _check_map(data.get("map"), "map", findings)
    for key in ("companions", "visible_npcs", "active_threads", "known_clues", "inventory", "visuals"):
        if not isinstance(data.get(key), list):
            _add(findings, "error", "dashboard_list", f"{key} must be a list.", key)


def check_dashboard_data(
    data: Any,
    dashboard_path: Path | None = None,
    *,
    require_assets: bool = True,
) -> dict:
    findings: list[dict] = []
    if not isinstance(data, dict):
        _add(findings, "error", "dashboard_state_not_object", "Dashboard state must be a JSON object.", "")
        return _result(dashboard_path, findings)
    version = data.get("dashboard_version", 1)
    if isinstance(version, bool) or not isinstance(version, int):
        _add(findings, "error", "dashboard_version", "dashboard_version must be an integer.", "dashboard_version")
    elif version >= 3:
        _check_v3(data, findings)
    else:
        _check_v2(data, findings)
    directory = dashboard_path.parent if dashboard_path else None
    _walk(data, "", findings, directory, require_assets)
    return _result(dashboard_path, findings)


def check_dashboard(
    path: Path,
    *,
    campaign_path: Path | None = None,
    expected_revision: int | None = None,
    require_current: bool = False,
    require_assets: bool = True,
) -> dict:
    path = path.resolve()
    if not path.is_file():
        findings: list[dict] = []
        _add(findings, "error", "dashboard_state_missing", "Dashboard state file is missing.", str(path))
        return _result(path, findings)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings = []
        _add(findings, "error", "dashboard_state_invalid_json", str(exc), str(path))
        return _result(path, findings)
    result = check_dashboard_data(data, path, require_assets=require_assets)
    findings = list(result["findings"])
    if expected_revision is not None and data.get("dashboard_version", 1) >= 3:
        if data.get("source_revision") != expected_revision:
            _add(
                findings,
                "error",
                "dashboard_revision_stale",
                f"Dashboard source_revision must match campaign revision {expected_revision}.",
                "source_revision",
            )
    if require_current and data.get("dashboard_version", 1) >= 3:
        refresh = data.get("refresh", {})
        if not isinstance(refresh, dict) or refresh.get("status") != "current":
            _add(findings, "error", "dashboard_not_current", "Dashboard must be marked current for this check.", "refresh.status")
        if not isinstance(data.get("scene_id"), str) or not data.get("scene_id", "").strip():
            _add(findings, "error", "dashboard_scene_missing", "A current dashboard needs a scene_id.", "scene_id")
    if campaign_path is not None:
        try:
            _walk_protected(data, "", _protected_names(campaign_path.resolve()), findings)
        except OSError as exc:
            _add(findings, "error", "dashboard_knowledge_read_failed", str(exc), str(campaign_path))
        if any(isinstance(tile, dict) and tile.get("type") == "documents" for tile in data.get("tiles", [])):
            checker_path = Path(__file__).with_name("check_world_voices.py")
            try:
                spec = importlib.util.spec_from_file_location("repog_dashboard_world_voices_check", checker_path)
                if spec is None or spec.loader is None:
                    raise RuntimeError("World Voices projection checker could not be loaded")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                projection_findings = module.validate_projection(campaign_path.resolve(), full=False)
                for finding in projection_findings:
                    findings.append(finding)
            except Exception as exc:
                _add(findings, "error", "dashboard_documents_validation_failed", str(exc), str(checker_path))
    return _result(path, findings)


def _result(path: Path | None, findings: list[dict]) -> dict:
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    infos = sum(item["severity"] == "info" for item in findings)
    return {
        "ok": errors == 0,
        "dashboard_path": str(path.resolve()) if path else "<memory>",
        "error_count": errors,
        "warning_count": warnings,
        "info_count": infos,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dashboard_state", help="Path to dashboard_state.json.")
    parser.add_argument("--campaign", help="Campaign folder for protected-name checks.")
    parser.add_argument("--expected-revision", type=int)
    parser.add_argument("--require-current", action="store_true")
    parser.add_argument("--no-assets", action="store_true", help="Skip referenced asset existence checks.")
    args = parser.parse_args(argv)
    result = check_dashboard(
        Path(args.dashboard_state),
        campaign_path=Path(args.campaign) if args.campaign else None,
        expected_revision=args.expected_revision,
        require_current=args.require_current,
        require_assets=not args.no_assets,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())

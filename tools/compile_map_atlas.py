"""Compile player-known location truth into a stable Dashboard V3 Atlas tile.

The compiler is deliberately cartographic, not narrative. It may place known
locations and bend known routes for a readable schematic, but it never creates
new semantic places, routes, terrain, hazards, or discoveries.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

from check_dashboard import check_dashboard_data
from update_dashboard import DashboardUpdateError, apply_dashboard_patch


class AtlasCompileError(Exception):
    def __init__(self, category: str, message: str, *, exit_code: int = 2) -> None:
        super().__init__(message)
        self.category = category
        self.exit_code = exit_code


SCALE_MODES = {"region", "city", "interior", "network"}
PROJECTIONS = {"schematic", "spatial"}
SKINS = {"auto", "minimal", "survey", "civic", "field", "systems"}
STYLE_ROLES = {"place", "landmark", "route", "boundary", "water", "region", "terrain", "structure", "hazard", "neutral"}
KNOWLEDGE_STATES = {"confirmed", "reported", "inferred", "stale", "unknown"}
ACCESS_STATES = {"open", "conditional", "blocked", "unknown"}
RISK_STATES = {"none", "caution", "danger", "unknown"}
SAFE_FEATURE_KEYS = {
    "id", "label", "style_role", "knowledge_state", "access_state", "risk_state",
    "summary", "importance", "duration_label", "conditions", "direction", "from",
    "to", "geometry", "presentation_only",
}


def _read_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AtlasCompileError("source_invalid", f"Cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise AtlasCompileError("source_invalid", f"{label} must contain a JSON object.")
    return value


def _atomic_write_json(path: Path, value: dict) -> None:
    payload = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _block(text: str, name: str) -> str:
    match = re.search(rf"(?ms)^{re.escape(name)}:\s*\n(?P<body>(?:^[ \t]+.*(?:\n|$)|^\s*$)*)", text)
    return match.group("body") if match else ""


def _scalar(text: str, name: str, default: str = "") -> str:
    match = re.search(rf"(?m)^\s*{re.escape(name)}:\s*(.*?)\s*$", text)
    if not match:
        return default
    return match.group(1).strip().strip('"\'` ')


def _profile_policy(campaign: Path) -> dict[str, Any]:
    path = campaign / "play_profile.yaml"
    if not path.is_file():
        return {"mode": "off", "skin": "auto", "tiles": []}
    text = path.read_text(encoding="utf-8")
    dashboard = _block(text, "dashboard")
    mode = _scalar(dashboard, "mode", "off")
    skin = _scalar(dashboard, "map_skin", "auto")
    inline = re.search(r"(?m)^\s*tiles:\s*\[(.*?)\]\s*$", dashboard)
    if inline:
        tiles = [item.strip().strip('"\'` ') for item in inline.group(1).split(",") if item.strip()]
    else:
        tail = re.search(r"(?ms)^\s*tiles:\s*$\n(?P<body>(?:^\s+-\s+.*(?:\n|$))*)", dashboard)
        tiles = re.findall(r"(?m)^\s+-\s+([^#\n]+?)\s*$", tail.group("body") if tail else "")
        tiles = [item.strip().strip('"\'` ') for item in tiles]
    return {"mode": mode, "skin": skin if skin in SKINS else "auto", "tiles": tiles}


def _state_context(campaign: Path) -> tuple[int, str]:
    path = campaign / "current_state.yaml"
    if not path.is_file():
        return 0, ""
    text = path.read_text(encoding="utf-8")
    revision_text = _scalar(text, "continuity_revision", "0")
    try:
        revision = max(0, int(revision_text))
    except ValueError:
        revision = 0
    scene = _block(text, "current_scene")
    return revision, _scalar(scene, "location", "")


def _known(value: str) -> bool:
    clean = value.strip().casefold()
    return clean in {"yes", "true", "known", "player-known", "player known", "confirmed", "evet"}


def _table_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise AtlasCompileError("location_graph_missing", f"Location graph does not exist: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in lines:
        if not line.strip().startswith("|"):
            if header is not None and rows:
                break
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if header is None:
            lowered = [cell.casefold() for cell in cells]
            if "from" in lowered and "to" in lowered and "player-known" in lowered:
                header = cells
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        if len(cells) != len(header):
            continue
        row = dict(zip(header, cells))
        start, end = row.get("From", "").strip(), row.get("To", "").strip()
        if not start or not end or start.casefold().startswith("example ") or end.casefold().startswith("example "):
            continue
        rows.append(row)
    return rows


def _slug(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").casefold()
    slug = re.sub(r"[^a-z0-9]+", "-", folded).strip("-") or "place"
    return slug[:56]


def _unique_id(base: str, used: set[str], seed: str) -> str:
    candidate = base
    if candidate not in used:
        used.add(candidate)
        return candidate
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8]
    candidate = f"{base[:47]}-{digest}"
    counter = 2
    while candidate in used:
        candidate = f"{base[:43]}-{digest}-{counter}"
        counter += 1
    used.add(candidate)
    return candidate


def _number(value: Any, fallback: float) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) else fallback


def _space(source: dict) -> dict[str, Any]:
    raw = source.get("coordinate_space") if isinstance(source.get("coordinate_space"), dict) else {}
    width, height = _number(raw.get("width"), 1000), _number(raw.get("height"), 640)
    if width <= 0 or height <= 0:
        raise AtlasCompileError("atlas_invalid", "Atlas coordinate-space width and height must be positive.")
    return {"type": "cartesian", "width": width, "height": height, "origin": "top_left"}


def _point_xy(feature: dict) -> tuple[float, float] | None:
    geometry = feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
    coordinates = geometry.get("coordinates")
    if geometry.get("type") != "point" or not isinstance(coordinates, list) or len(coordinates) != 2:
        return None
    if not all(isinstance(item, (int, float)) and not isinstance(item, bool) and math.isfinite(float(item)) for item in coordinates):
        return None
    return float(coordinates[0]), float(coordinates[1])


def _valid_line_geometry(feature: dict, space: dict[str, Any]) -> bool:
    geometry = feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
    coordinates = geometry.get("coordinates")
    if geometry.get("type") != "line" or not isinstance(coordinates, list) or len(coordinates) < 2:
        return False
    width, height = float(space["width"]), float(space["height"])
    for coordinate in coordinates:
        if not isinstance(coordinate, list) or len(coordinate) != 2:
            return False
        x, y = coordinate
        if not all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) for value in (x, y)):
            return False
        if not (0 <= float(x) <= width and 0 <= float(y) <= height):
            return False
    return True


def _route_parts(row: dict[str, str]) -> tuple[str, str, str, str]:
    start_name, end_name = row["From"].strip(), row["To"].strip()
    direction = row.get("Direction", "<->").strip() or "<->"
    if direction == "<-":
        start_name, end_name, direction = end_name, start_name, "->"
    if direction not in {"<->", "->"}:
        raise AtlasCompileError(
            "location_graph_invalid",
            f"Unsupported route direction between {start_name!r} and {end_name!r}: {direction!r}.",
        )
    route_ref = f"{start_name.casefold()}|{direction}|{end_name.casefold()}"
    return start_name, end_name, direction, route_ref


def _layout_points(names: list[str], existing: dict[str, tuple[float, float]], space: dict[str, Any], seed: str) -> dict[str, tuple[float, float]]:
    width, height = float(space["width"]), float(space["height"])
    margin_x, margin_y = min(90.0, width * .12), min(75.0, height * .14)
    usable_w, usable_h = max(1.0, width - 2 * margin_x), max(1.0, height - 2 * margin_y)
    result = dict(existing)
    ordered = sorted((name for name in names if name.casefold() not in result), key=str.casefold)
    total = max(1, len(ordered))
    for index, name in enumerate(ordered):
        digest = hashlib.sha256(f"{seed}|{name}".encode("utf-8")).digest()
        phase = int.from_bytes(digest[:4], "big") / 2**32 * math.tau
        ring = .33 + .55 * ((index + 1) / (total + 1)) ** .58
        angle = phase + index * 2.399963229728653
        x = width / 2 + math.cos(angle) * usable_w * .5 * ring
        y = height / 2 + math.sin(angle) * usable_h * .5 * ring
        # Pick the least crowded deterministic candidate without moving saved points.
        candidates = []
        for offset in range(12):
            a = angle + offset * math.tau / 12
            cx = min(width - margin_x, max(margin_x, width / 2 + math.cos(a) * usable_w * .5 * ring))
            cy = min(height - margin_y, max(margin_y, height / 2 + math.sin(a) * usable_h * .5 * ring))
            distance = min((math.hypot(cx - px, cy - py) for px, py in result.values()), default=max(width, height))
            candidates.append((distance, -offset, cx, cy))
        _, _, x, y = max(candidates)
        result[name.casefold()] = (round(x, 2), round(y, 2))
    return result


def _access(value: str) -> str:
    clean = value.casefold()
    if any(word in clean for word in ("block", "closed", "locked", "sealed")):
        return "blocked"
    if any(word in clean for word in ("restrict", "permit", "guard", "conditional", "toll", "private")):
        return "conditional"
    if "unknown" in clean or not clean.strip():
        return "unknown" if "unknown" in clean else "open"
    return "open"


def _risk(value: str) -> str:
    clean = value.casefold().strip()
    if not clean or clean in {"none", "no", "n/a", "-"}:
        return "none"
    if "unknown" in clean:
        return "unknown"
    if any(word in clean for word in ("deadly", "danger", "lethal", "fatal", "severe")):
        return "danger"
    return "caution"


def _curve(start: tuple[float, float], end: tuple[float, float], seed: str, space: dict[str, Any]) -> list[list[float]]:
    x1, y1 = start; x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    distance = max(1.0, math.hypot(dx, dy))
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    sign = -1 if digest[0] & 1 else 1
    amount = min(distance * (.08 + digest[1] / 2550), min(float(space["width"]), float(space["height"])) * .11)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    cx = min(float(space["width"]), max(0.0, mx - dy / distance * amount * sign))
    cy = min(float(space["height"]), max(0.0, my + dx / distance * amount * sign))
    return [[round(x1, 2), round(y1, 2)], [round(cx, 2), round(cy, 2)], [round(x2, 2), round(y2, 2)]]


def _context_envelope(points: list[tuple[float, float]], space: dict[str, Any], seed: str) -> dict | None:
    if not points:
        return None
    width, height = float(space["width"]), float(space["height"])
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    rx = max(120.0, (max(xs) - min(xs)) / 2 + width * .09)
    ry = max(95.0, (max(ys) - min(ys)) / 2 + height * .11)
    coordinates: list[list[float]] = []
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    for index in range(16):
        angle = index * math.tau / 16
        jitter = .9 + digest[index] / 2550
        x = min(width, max(0.0, cx + math.cos(angle) * rx * jitter))
        y = min(height, max(0.0, cy + math.sin(angle) * ry * jitter))
        coordinates.append([round(x, 2), round(y, 2)])
    return {
        "id": "atlas-context",
        "style_role": "neutral",
        "presentation_only": True,
        "geometry": {"type": "area", "coordinates": coordinates},
    }


def _normalise_source(source: dict) -> dict:
    if source.get("schema_version") != 1:
        raise AtlasCompileError("atlas_invalid", "map_atlas.json schema_version must be 1.")
    scale = source.get("scale_mode", "region")
    projection = source.get("projection", "schematic")
    skin = source.get("skin", "auto")
    if scale not in SCALE_MODES or projection not in PROJECTIONS or skin not in SKINS:
        raise AtlasCompileError("atlas_invalid", "Atlas scale_mode, projection, or skin is invalid.")
    features = source.get("features")
    if not isinstance(features, list) or any(not isinstance(item, dict) for item in features):
        raise AtlasCompileError("atlas_invalid", "map_atlas.json features must be a list of objects.")
    feature_ids: set[str] = set()
    for index, feature in enumerate(features):
        feature_id = feature.get("id")
        if not isinstance(feature_id, str) or not feature_id.strip():
            raise AtlasCompileError("atlas_invalid", f"map_atlas.json features[{index}] needs a non-empty id.")
        if feature_id == "atlas-context":
            raise AtlasCompileError("atlas_invalid", "atlas-context is reserved for generated presentation geometry.")
        if feature_id in feature_ids:
            raise AtlasCompileError("atlas_invalid", f"Duplicate map_atlas.json feature id: {feature_id!r}.")
        feature_ids.add(feature_id)
    result = copy.deepcopy(source)
    result["coordinate_space"] = _space(source)
    result["features"] = features
    return result


def _compile_source(campaign: Path, source: dict, rows: list[dict[str, str]], profile: dict[str, Any], current_location: str) -> tuple[dict, dict, list[str]]:
    source = _normalise_source(source)
    space = source["coordinate_space"]
    warnings: list[str] = []
    known_rows = [row for row in rows if _known(row.get("Player-known", ""))]
    names = sorted({row[side].strip() for row in known_rows for side in ("From", "To")}, key=str.casefold)

    source_features = [copy.deepcopy(item) for item in source["features"] if item.get("id") != "atlas-context"]
    used_ids = {str(item.get("id")) for item in source_features if isinstance(item.get("id"), str) and item.get("id")}
    point_by_name: dict[str, dict] = {}
    existing_xy: dict[str, tuple[float, float]] = {}
    for feature in source_features:
        ref = feature.get("location_ref")
        if not isinstance(ref, str) or not ref.strip():
            continue
        geometry = feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
        # Non-point geometry may use location_ref only as provenance. It must
        # not replace the canonical location marker for that place.
        if geometry.get("type") not in {None, "point"}:
            continue
        ref_key = ref.casefold()
        if ref_key in point_by_name:
            raise AtlasCompileError("atlas_invalid", f"Duplicate point location_ref in map_atlas.json: {ref!r}.")
        point_by_name[ref_key] = feature
        xy = _point_xy(feature)
        if xy is not None:
            existing_xy[ref_key] = xy

    positions = _layout_points(names, existing_xy, space, str(source.get("atlas_id", "campaign-atlas")))
    for name in names:
        key = name.casefold()
        feature = point_by_name.get(key)
        if feature is None:
            feature = {
                "id": _unique_id(_slug(name), used_ids, name),
                "label": name,
                "location_ref": name,
                "style_role": "place",
                "knowledge_state": "confirmed",
                "access_state": "open",
                "risk_state": "none",
                "importance": "secondary",
                "geometry": {"type": "point", "coordinates": list(positions[key])},
            }
            source_features.append(feature)
            point_by_name[key] = feature
        elif _point_xy(feature) is None:
            feature["geometry"] = {"type": "point", "coordinates": list(positions[key])}
        feature.setdefault("label", name)
        feature.setdefault("style_role", "place")
        feature.setdefault("knowledge_state", "confirmed")
        feature.setdefault("access_state", "open")
        feature.setdefault("risk_state", "none")

    route_by_ref: dict[str, dict] = {}
    for feature in source_features:
        route_ref = feature.get("route_ref")
        if not isinstance(route_ref, str):
            continue
        if route_ref in route_by_ref:
            raise AtlasCompileError("atlas_invalid", f"Duplicate route_ref in map_atlas.json: {route_ref!r}.")
        geometry = feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
        if geometry.get("type") not in {None, "line"}:
            raise AtlasCompileError("atlas_invalid", f"route_ref {route_ref!r} must use line geometry.")
        route_by_ref[route_ref] = feature
    for row in known_rows:
        start_name, end_name, direction, route_ref = _route_parts(row)
        start, end = point_by_name[start_name.casefold()], point_by_name[end_name.casefold()]
        route = route_by_ref.get(route_ref)
        if route is None:
            route_id = _unique_id(f"route-{_slug(start_name)}-{_slug(end_name)}", used_ids, route_ref)
            route = {"id": route_id, "route_ref": route_ref}
            source_features.append(route)
            route_by_ref[route_ref] = route
        route.update({
            "label": f"{start_name} {'↔' if direction == '<->' else '→'} {end_name}",
            "style_role": "route",
            "knowledge_state": "confirmed",
            "access_state": _access(row.get("Access", "")),
            "risk_state": _risk(row.get("Conditions", "")),
            "from": start["id"],
            "to": end["id"],
            "direction": "bidirectional" if direction == "<->" else "forward",
        })
        # Authored linework is durable cartographic truth. Generate a curve only
        # when the route has no usable geometry, so later compiles do not redraw
        # a player-recognisable map.
        if not _valid_line_geometry(route, space):
            start_xy, end_xy = _point_xy(start), _point_xy(end)
            if start_xy is None or end_xy is None:  # Defensive; point creation above guarantees these.
                raise AtlasCompileError("atlas_invalid", f"Route {route_ref!r} has an endpoint without coordinates.")
            route["geometry"] = {"type": "line", "coordinates": _curve(start_xy, end_xy, route_ref, space)}
        travel = row.get("Travel", "").strip()
        conditions = row.get("Conditions", "").strip()
        if travel:
            route["duration_label"] = travel
        else:
            route.pop("duration_label", None)
        if conditions and conditions.casefold() not in {"none", "n/a", "-"}:
            route["conditions"] = conditions
        else:
            route.pop("conditions", None)

    known_name_keys = {name.casefold() for name in names}
    known_route_refs = {_route_parts(row)[3] for row in known_rows}
    compiled_features: list[dict] = []
    for feature in source_features:
        if feature.get("knowledge_state") == "unknown" or feature.get("player_known") is False:
            continue
        geometry = feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
        geometry_type = geometry.get("type")
        location_ref = feature.get("location_ref")
        route_ref = feature.get("route_ref")
        presentation = feature.get("presentation_only") is True
        anchored = (
            presentation
            or (isinstance(location_ref, str) and location_ref.casefold() in known_name_keys)
            or (isinstance(route_ref, str) and route_ref in known_route_refs)
        )
        if not anchored:
            warnings.append(f"Ignored unanchored Atlas feature: {feature.get('id', '<missing id>')}")
            continue
        if geometry_type not in {"point", "line", "area"}:
            warnings.append(f"Ignored Atlas feature with invalid geometry: {feature.get('id', '<missing id>')}")
            continue
        clean = {key: copy.deepcopy(value) for key, value in feature.items() if key in SAFE_FEATURE_KEYS}
        clean.setdefault("knowledge_state", "confirmed")
        clean.setdefault("access_state", "open")
        clean.setdefault("risk_state", "none")
        compiled_features.append(clean)

    points = [_point_xy(feature) for feature in source_features if isinstance(feature.get("location_ref"), str) and feature.get("location_ref", "").casefold() in known_name_keys]
    if source["projection"] == "schematic":
        envelope = _context_envelope([point for point in points if point is not None], space, str(source.get("atlas_id", "campaign-atlas")))
        if envelope:
            compiled_features.insert(0, envelope)

    current_id = ""
    if current_location and current_location.casefold() in point_by_name:
        current_id = str(point_by_name[current_location.casefold()]["id"])
    elif isinstance(source.get("current_feature_id"), str):
        candidate = source.get("current_feature_id", "")
        if any(feature.get("id") == candidate and feature.get("geometry", {}).get("type") == "point" for feature in compiled_features):
            current_id = candidate

    selected_skin = profile.get("skin", "auto")
    skin = selected_skin if selected_skin != "auto" else source.get("skin", "auto")
    compiled = {
        "atlas_version": 1,
        "summary": "Known spatial context. Distances are approximate." if source["projection"] == "schematic" else "Known spatial context.",
        "coordinate_space": copy.deepcopy(space),
        "scale_mode": source["scale_mode"],
        "projection": source["projection"],
        "skin": skin if skin in SKINS else "auto",
        "current_feature_id": current_id,
        "features": compiled_features,
    }
    background = source.get("background_image")
    if isinstance(background, str) and background.strip():
        compiled["background_image"] = background.strip()
    updated_source = copy.deepcopy(source)
    updated_source["features"] = source_features
    updated_source["current_feature_id"] = current_id
    return updated_source, compiled, warnings


def _tile(source: dict, compiled: dict, tile_id: str | None, title: str | None) -> dict:
    metadata = source.get("tile") if isinstance(source.get("tile"), dict) else {}
    return {
        "id": tile_id or str(metadata.get("id") or "atlas"),
        "type": "map",
        "title": title or str(metadata.get("title") or "Known Atlas"),
        "order": int(metadata.get("order", 60)) if isinstance(metadata.get("order", 60), int) else 60,
        "data": compiled,
    }


def _candidate_dashboard(current: dict, request: dict) -> dict:
    candidate = copy.deepcopy(current)
    by_id = {tile.get("id"): index for index, tile in enumerate(candidate.get("tiles", [])) if isinstance(tile, dict)}
    for operation in request["operations"]:
        tile = operation["tile"]
        if tile["id"] in by_id:
            candidate["tiles"][by_id[tile["id"]]] = copy.deepcopy(tile)
        else:
            candidate.setdefault("tiles", []).append(copy.deepcopy(tile))
    candidate["source_revision"] = request["source_revision"]
    candidate["dashboard_revision"] = request["expected_revision"] + 1
    candidate["refresh"] = copy.deepcopy(request["refresh"])
    return candidate


def compile_campaign(
    campaign: Path,
    *,
    apply: bool = True,
    force: bool = False,
    source_revision: int | None = None,
    tile_id: str | None = None,
    title: str | None = None,
) -> dict:
    campaign = campaign.resolve()
    atlas_path = campaign / "map_atlas.json"
    graph_path = campaign / "location_graph.md"
    dashboard_path = campaign / "dashboard" / "dashboard_state.json"
    if not atlas_path.is_file() or not dashboard_path.is_file():
        raise AtlasCompileError("source_missing", "map_atlas.json and dashboard/dashboard_state.json are required.")
    profile = _profile_policy(campaign)
    if not force and (profile["mode"] != "on" or "map" not in profile["tiles"]):
        raise AtlasCompileError("dashboard_map_disabled", "Dashboard map tile is not enabled in play_profile.yaml.")
    source = _read_json(atlas_path, "map_atlas.json")
    dashboard = _read_json(dashboard_path, "dashboard state")
    if dashboard.get("dashboard_version") != 3:
        raise AtlasCompileError("dashboard_version", "Atlas compilation requires Dashboard V3.")
    state_revision, current_location = _state_context(campaign)
    revision = state_revision if source_revision is None else source_revision
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise AtlasCompileError("revision_invalid", "source_revision must be a non-negative integer.")
    if revision < int(dashboard.get("source_revision", 0)):
        raise AtlasCompileError("revision_invalid", "source_revision cannot move backwards.")
    updated_source, compiled, warnings = _compile_source(campaign, source, _table_rows(graph_path), profile, current_location)
    tile = _tile(updated_source, compiled, tile_id, title)
    request = {
        "expected_revision": int(dashboard.get("dashboard_revision", 0)),
        "source_revision": revision,
        "refresh": {"status": "current", "reason": "Player-known atlas changed"},
        "operations": [{"op": "upsert", "tile": tile}],
    }
    validation = check_dashboard_data(_candidate_dashboard(dashboard, request), dashboard_path, require_assets=True)
    if not validation["ok"]:
        raise AtlasCompileError("compiled_atlas_invalid", json.dumps(validation["findings"], ensure_ascii=False))

    current_tile = next((item for item in dashboard.get("tiles", []) if isinstance(item, dict) and item.get("id") == tile["id"]), None)
    source_changed = updated_source != source
    dashboard_changed = current_tile != tile or revision != dashboard.get("source_revision")
    result = {
        "ok": True,
        "changed": source_changed or dashboard_changed,
        "atlas_path": str(atlas_path),
        "dashboard_path": str(dashboard_path),
        "source_revision": revision,
        "feature_count": len(compiled["features"]),
        "semantic_feature_count": sum(feature.get("presentation_only") is not True for feature in compiled["features"]),
        "warnings": warnings,
        "request": request,
        "tile": tile,
    }
    if not apply or not result["changed"]:
        result["applied"] = False
        return result

    original_source = copy.deepcopy(source)
    try:
        if source_changed:
            _atomic_write_json(atlas_path, updated_source)
        update_result = apply_dashboard_patch(dashboard_path, request) if dashboard_changed else {"changed_tile_ids": []}
    except Exception:
        if source_changed:
            _atomic_write_json(atlas_path, original_source)
        raise
    result["applied"] = True
    result["dashboard_update"] = update_result
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", nargs="?", default="campaign", help="Campaign directory.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Validate and show the planned tile without writing.")
    mode.add_argument("--emit-request", action="store_true", help="Print only the Dashboard patch request without writing.")
    parser.add_argument("--source-revision", type=int)
    parser.add_argument("--tile-id")
    parser.add_argument("--title")
    parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true", help="Emit stable JSON output (the default output is also JSON).")
    args = parser.parse_args(argv)
    try:
        result = compile_campaign(
            Path(args.campaign),
            apply=not (args.dry_run or args.emit_request),
            force=args.force,
            source_revision=args.source_revision,
            tile_id=args.tile_id,
            title=args.title,
        )
        payload = result["request"] if args.emit_request else result
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    except (AtlasCompileError, DashboardUpdateError) as exc:
        category = getattr(exc, "category", "atlas_compile_failed")
        exit_code = getattr(exc, "exit_code", 2)
        print(json.dumps({"ok": False, "failure_category": category, "failure_reason": str(exc)}, indent=2, ensure_ascii=False))
        return exit_code
    except OSError as exc:
        print(json.dumps({"ok": False, "failure_category": "write_failed", "failure_reason": str(exc)}, indent=2, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT


def _load_check_dashboard():
    path = PUBLIC / "tools" / "check_dashboard.py"
    spec = importlib.util.spec_from_file_location("atlas_check_dashboard", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_dashboard = _load_check_dashboard()


def _valid_atlas() -> dict:
    return {
        "atlas_version": 1,
        "coordinate_space": {
            "type": "cartesian",
            "width": 100,
            "height": 80,
            "origin": "top_left",
        },
        "scale_mode": "city",
        "projection": "spatial",
        "skin": "civic",
        "current_feature_id": "quay",
        "features": [
            {
                "id": "quay",
                "label": "Lantern Quay",
                "style_role": "place",
                "knowledge_state": "confirmed",
                "access_state": "open",
                "risk_state": "none",
                "geometry": {"type": "point", "coordinates": [10, 60]},
            },
            {
                "id": "gate",
                "label": "North Gate",
                "style_role": "landmark",
                "geometry": {"type": "point", "coordinates": [85, 10]},
            },
            {
                "id": "road",
                "label": "Salt Road",
                "style_role": "route",
                "knowledge_state": "reported",
                "access_state": "conditional",
                "risk_state": "caution",
                "from": "quay",
                "to": "gate",
                "geometry": {
                    "type": "line",
                    "coordinates": [[10, 60], [40, 45], [85, 10]],
                },
            },
            {
                "id": "ward",
                "label": "Old Ward",
                "style_role": "region",
                "knowledge_state": "inferred",
                "access_state": "blocked",
                "risk_state": "danger",
                "geometry": {
                    "type": "area",
                    "coordinates": [[5, 5], [45, 5], [45, 35], [5, 35]],
                },
            },
        ],
    }


def _dashboard(map_data: dict) -> dict:
    data = json.loads((PUBLIC / "campaign" / "dashboard" / "dashboard_state.json").read_text(encoding="utf-8"))
    data["tiles"] = [
        {
            "id": "atlas",
            "type": "map",
            "title": "Local Atlas",
            "order": 60,
            "data": map_data,
        }
    ]
    return data


def _check(map_data: dict) -> dict:
    return check_dashboard.check_dashboard_data(_dashboard(map_data), require_assets=False)


def _rules(result: dict) -> set[str]:
    return {item["rule"] for item in result["findings"]}


def test_atlas_v1_accepts_all_geometries_and_omitted_state_defaults() -> None:
    result = _check(_valid_atlas())
    assert result["ok"], result["findings"]
    assert result["warning_count"] == 0


def test_atlas_allows_only_neutral_presentation_geometry_to_omit_label() -> None:
    atlas = _valid_atlas()
    atlas["features"].append(
        {
            "id": "coast-shape",
            "presentation_only": True,
            "style_role": "neutral",
            "geometry": {
                "type": "area",
                "coordinates": [[50, 50], [70, 50], [70, 70], [50, 70]],
            },
        }
    )
    assert _check(atlas)["ok"]

    atlas["features"][-1]["presentation_only"] = False
    assert "dashboard_atlas_feature_label" in _rules(_check(atlas))

    atlas["features"][-1]["presentation_only"] = True
    atlas["features"][-1]["style_role"] = "region"
    rules = _rules(_check(atlas))
    assert "dashboard_atlas_presentation_only" in rules
    assert "dashboard_atlas_feature_label" in rules


def test_atlas_presentation_geometry_cannot_carry_route_endpoints() -> None:
    atlas = _valid_atlas()
    atlas["features"].append(
        {
            "id": "decorative-line",
            "presentation_only": True,
            "style_role": "neutral",
            "from": "quay",
            "to": "gate",
            "geometry": {"type": "line", "coordinates": [[10, 60], [85, 10]]},
        }
    )
    assert "dashboard_atlas_presentation_route" in _rules(_check(atlas))


def test_legacy_node_edge_map_remains_valid() -> None:
    legacy = {
        "bounds": {"width": 100, "height": 80},
        "current_node_id": "quay",
        "nodes": [
            {"id": "quay", "label": "Lantern Quay", "x": 10, "y": 60},
            {"id": "gate", "label": "North Gate", "x": 85, "y": 10},
        ],
        "edges": [{"from": "quay", "to": "gate", "label": "Salt Road"}],
    }
    result = _check(legacy)
    assert result["ok"], result["findings"]


@pytest.mark.parametrize(
    ("field", "value", "rule"),
    [
        ("scale_mode", "galaxy", "dashboard_atlas_scale_mode"),
        ("projection", "perspective", "dashboard_atlas_projection"),
        ("skin", "neon", "dashboard_atlas_skin"),
    ],
)
def test_atlas_rejects_invalid_map_enums(field: str, value: str, rule: str) -> None:
    atlas = _valid_atlas()
    atlas[field] = value
    assert rule in _rules(_check(atlas))


@pytest.mark.parametrize(
    ("field", "value", "rule"),
    [
        ("style_role", "quest_marker", "dashboard_atlas_style_role"),
        ("knowledge_state", "secret", "dashboard_atlas_knowledge_state"),
        ("access_state", "guarded", "dashboard_atlas_access_state"),
        ("risk_state", "extreme", "dashboard_atlas_risk_state"),
    ],
)
def test_atlas_rejects_invalid_feature_enums(field: str, value: str, rule: str) -> None:
    atlas = _valid_atlas()
    atlas["features"][0][field] = value
    assert rule in _rules(_check(atlas))


def test_atlas_omits_unknown_features_instead_of_exposing_their_geometry() -> None:
    atlas = _valid_atlas()
    atlas["features"][0]["knowledge_state"] = "unknown"
    assert "dashboard_atlas_unknown_feature" in _rules(_check(atlas))


@pytest.mark.parametrize(
    ("geometry", "rule"),
    [
        ({"type": "point", "coordinates": [101, 20]}, "dashboard_atlas_out_of_bounds"),
        ({"type": "point", "coordinates": [float("inf"), 20]}, "dashboard_atlas_coordinate"),
        ({"type": "line", "coordinates": [[10, 10]]}, "dashboard_atlas_geometry_coordinates"),
        ({"type": "area", "coordinates": [[10, 10], [20, 20]]}, "dashboard_atlas_geometry_coordinates"),
        ({"type": "circle", "coordinates": [10, 10]}, "dashboard_atlas_geometry_type"),
    ],
)
def test_atlas_rejects_invalid_geometry(geometry: dict, rule: str) -> None:
    atlas = _valid_atlas()
    atlas["features"][0]["geometry"] = geometry
    assert rule in _rules(_check(atlas))


def test_atlas_rejects_duplicate_and_dangling_feature_references() -> None:
    atlas = _valid_atlas()
    duplicate = copy.deepcopy(atlas["features"][0])
    duplicate["label"] = "Duplicate Quay"
    atlas["features"].append(duplicate)
    atlas["current_feature_id"] = "missing-place"
    atlas["features"][2]["to"] = "missing-place"

    rules = _rules(_check(atlas))
    assert "dashboard_atlas_duplicate_feature" in rules
    assert "dashboard_atlas_current_feature" in rules
    assert "dashboard_atlas_route_endpoint" in rules


def test_atlas_current_feature_must_resolve_to_point_geometry() -> None:
    atlas = _valid_atlas()
    atlas["current_feature_id"] = "ward"

    result = _check(atlas)
    finding = next(
        item for item in result["findings"] if item["rule"] == "dashboard_atlas_current_feature_geometry"
    )
    assert finding["path"] == "tiles[0].data.current_feature_id"


def test_atlas_route_endpoints_must_resolve_to_point_geometry() -> None:
    atlas = _valid_atlas()
    atlas["features"][2]["from"] = "ward"
    atlas["features"][2]["to"] = "road"

    findings = [
        item for item in _check(atlas)["findings"] if item["rule"] == "dashboard_atlas_route_endpoint_geometry"
    ]
    assert {item["path"] for item in findings} == {
        "tiles[0].data.features[2].from",
        "tiles[0].data.features[2].to",
    }


def test_atlas_route_references_must_be_paired_on_line_features() -> None:
    atlas = _valid_atlas()
    atlas["features"][0]["from"] = "quay"
    del atlas["features"][2]["to"]
    assert "dashboard_atlas_route_refs" in _rules(_check(atlas))


def test_atlas_still_uses_shared_player_text_and_asset_safety_walk() -> None:
    atlas = _valid_atlas()
    atlas["background_image"] = "https://example.invalid/secret-map.png"
    atlas["features"][0]["label"] = "current_state cache"

    rules = _rules(_check(atlas))
    assert "dashboard_asset_path" in rules
    assert "dashboard_technical_leakage" in rules


def test_atlas_version_and_coordinate_space_are_strict() -> None:
    atlas = _valid_atlas()
    atlas["atlas_version"] = True
    assert "dashboard_atlas_version" in _rules(_check(atlas))

    atlas = _valid_atlas()
    atlas["coordinate_space"] = {"type": "polar", "width": 0, "height": 80, "origin": "bottom_left"}
    rules = _rules(_check(atlas))
    assert "dashboard_atlas_coordinate_space" in rules
    assert "dashboard_atlas_coordinate_bounds" in rules

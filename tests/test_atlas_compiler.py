from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT
sys.path.insert(0, str(PUBLIC / "tools"))


def _load_compiler():
    path = PUBLIC / "tools" / "compile_map_atlas.py"
    spec = importlib.util.spec_from_file_location("repog_atlas_compiler", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compiler = _load_compiler()


@pytest.fixture()
def campaign(tmp_path: Path) -> Path:
    target = tmp_path / "campaign"
    shutil.copytree(PUBLIC / "campaign", target)
    return target


def _enable_map(campaign: Path, *, skin: str = "auto") -> None:
    profile = campaign.joinpath("play_profile.yaml").read_text(encoding="utf-8")
    profile = profile.replace('  mode: "off"\n  refresh_policy:', '  mode: "on"\n  refresh_policy:', 1)
    profile = profile.replace("  map_skin: auto", f"  map_skin: {skin}", 1)
    profile = profile.replace("  tiles: []", "  tiles: [scene, map]", 1)
    campaign.joinpath("play_profile.yaml").write_text(profile, encoding="utf-8")


def _write_graph(campaign: Path, rows: list[str]) -> None:
    campaign.joinpath("location_graph.md").write_text(
        """# Location Graph

| From | Direction | To | Travel | Access | Visibility | Ordinary traffic | Conditions | Player-known | Last changed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
""" + "\n".join(rows) + "\n",
        encoding="utf-8",
    )


def _set_state(campaign: Path, *, revision: int, location: str) -> None:
    path = campaign / "current_state.yaml"
    text = path.read_text(encoding="utf-8")
    text = text.replace("continuity_revision: 0", f"continuity_revision: {revision}", 1)
    text = text.replace('  location: ""', f'  location: "{location}"', 1)
    path.write_text(text, encoding="utf-8")


def _tile(campaign: Path) -> dict:
    dashboard = json.loads(campaign.joinpath("dashboard", "dashboard_state.json").read_text(encoding="utf-8"))
    return next(item for item in dashboard["tiles"] if item["id"] == "atlas")


def _semantic_features(result: dict) -> list[dict]:
    return [item for item in result["tile"]["data"]["features"] if item.get("presentation_only") is not True]


def test_dry_run_compiles_known_graph_without_writing(campaign: Path) -> None:
    _enable_map(campaign)
    _set_state(campaign, revision=4, location="Lantern Quay")
    _write_graph(
        campaign,
        [
            "| Lantern Quay | <-> | North Gate | 20 minutes | public | open | fishers | rain | yes | 4 |",
            "| North Gate | -> | Hidden Vault | 1 hour | sealed | concealed | none | deadly | no | 4 |",
        ],
    )
    before_atlas = campaign.joinpath("map_atlas.json").read_bytes()
    before_dashboard = campaign.joinpath("dashboard", "dashboard_state.json").read_bytes()

    result = compiler.compile_campaign(campaign, apply=False)

    assert result["changed"] is True
    assert result["applied"] is False
    assert result["source_revision"] == 4
    assert result["tile"]["data"]["current_feature_id"] == "lantern-quay"
    assert {item["label"] for item in _semantic_features(result)} == {
        "Lantern Quay",
        "North Gate",
        "Lantern Quay ↔ North Gate",
    }
    assert "Hidden Vault" not in json.dumps(result["tile"], ensure_ascii=False)
    envelope = result["tile"]["data"]["features"][0]
    assert envelope == {
        "id": "atlas-context",
        "style_role": "neutral",
        "presentation_only": True,
        "geometry": {"type": "area", "coordinates": envelope["geometry"]["coordinates"]},
    }
    assert campaign.joinpath("map_atlas.json").read_bytes() == before_atlas
    assert campaign.joinpath("dashboard", "dashboard_state.json").read_bytes() == before_dashboard


def test_apply_is_idempotent_and_does_not_bump_dashboard_twice(campaign: Path) -> None:
    _enable_map(campaign, skin="survey")
    _set_state(campaign, revision=7, location="Lantern Quay")
    _write_graph(campaign, ["| Lantern Quay | <-> | North Gate | short walk | public | open | workers | none | yes | 7 |"])

    first = compiler.compile_campaign(campaign)
    after_first = json.loads(campaign.joinpath("dashboard", "dashboard_state.json").read_text(encoding="utf-8"))
    second = compiler.compile_campaign(campaign)
    after_second = json.loads(campaign.joinpath("dashboard", "dashboard_state.json").read_text(encoding="utf-8"))

    assert first["applied"] is True
    assert after_first["dashboard_revision"] == 1
    assert after_first["source_revision"] == 7
    assert _tile(campaign)["data"]["skin"] == "survey"
    assert second["changed"] is False
    assert second["applied"] is False
    assert after_second == after_first


def test_existing_coordinates_and_authored_route_geometry_remain_stable(campaign: Path) -> None:
    _enable_map(campaign)
    _write_graph(campaign, ["| Lantern Quay | <-> | North Gate | short walk | public | open | workers | none | yes | 1 |"])
    compiler.compile_campaign(campaign)
    atlas_path = campaign / "map_atlas.json"
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    quay = next(item for item in atlas["features"] if item.get("location_ref") == "Lantern Quay")
    road = next(item for item in atlas["features"] if item.get("route_ref"))
    original_point = copy.deepcopy(quay["geometry"])
    road["geometry"] = {"type": "line", "coordinates": [[90, 90], [500, 110], [900, 420]]}
    atlas_path.write_text(json.dumps(atlas, indent=2) + "\n", encoding="utf-8")
    _write_graph(
        campaign,
        [
            "| Lantern Quay | <-> | North Gate | short walk | public | open | workers | none | yes | 1 |",
            "| North Gate | -> | Hill Shrine | 40 minutes | guarded | open | pilgrims | steep | yes | 2 |",
        ],
    )

    compiler.compile_campaign(campaign)
    updated = json.loads(atlas_path.read_text(encoding="utf-8"))
    updated_quay = next(item for item in updated["features"] if item.get("location_ref") == "Lantern Quay")
    updated_road = next(item for item in updated["features"] if item.get("route_ref") == "lantern quay|<->|north gate")

    assert updated_quay["geometry"] == original_point
    assert updated_road["geometry"]["coordinates"] == [[90, 90], [500, 110], [900, 420]]


def test_reverse_graph_direction_is_canonical_and_compiled(campaign: Path) -> None:
    _enable_map(campaign)
    _write_graph(campaign, ["| Old Mill | <- | River Port | 1 day | toll | open | barges | fog | yes | 2 |"])

    result = compiler.compile_campaign(campaign, apply=False)
    route = next(item for item in _semantic_features(result) if item["style_role"] == "route")

    assert route["label"] == "River Port → Old Mill"
    assert route["direction"] == "forward"
    assert route["access_state"] == "conditional"
    assert route["risk_state"] == "caution"


def test_unanchored_semantic_source_feature_is_not_player_visible(campaign: Path) -> None:
    _enable_map(campaign)
    _write_graph(campaign, ["| Quay | <-> | Gate | short walk | public | open | workers | none | yes | 1 |"])
    atlas_path = campaign / "map_atlas.json"
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    atlas["features"].append(
        {
            "id": "secret-island",
            "label": "Secret Island",
            "style_role": "region",
            "knowledge_state": "confirmed",
            "geometry": {"type": "area", "coordinates": [[1, 1], [10, 1], [10, 10]]},
        }
    )
    atlas_path.write_text(json.dumps(atlas, indent=2) + "\n", encoding="utf-8")

    result = compiler.compile_campaign(campaign, apply=False)

    assert "Secret Island" not in json.dumps(result["tile"], ensure_ascii=False)
    assert result["warnings"] == ["Ignored unanchored Atlas feature: secret-island"]


def test_location_anchored_area_does_not_replace_its_place_marker(campaign: Path) -> None:
    _enable_map(campaign)
    _write_graph(campaign, ["| Quay | <-> | Gate | short walk | public | open | workers | none | yes | 1 |"])
    atlas_path = campaign / "map_atlas.json"
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    area_geometry = {"type": "area", "coordinates": [[80, 80], [260, 80], [260, 220], [80, 220]]}
    atlas["features"].append(
        {
            "id": "quay-district",
            "label": "Quay District",
            "location_ref": "Quay",
            "style_role": "region",
            "geometry": area_geometry,
        }
    )
    atlas_path.write_text(json.dumps(atlas, indent=2) + "\n", encoding="utf-8")

    result = compiler.compile_campaign(campaign, apply=False)
    semantic = _semantic_features(result)

    assert next(item for item in semantic if item["id"] == "quay-district")["geometry"] == area_geometry
    assert next(item for item in semantic if item["label"] == "Quay")["geometry"]["type"] == "point"


def test_duplicate_route_provenance_is_rejected(campaign: Path) -> None:
    _enable_map(campaign)
    _write_graph(campaign, ["| Quay | <-> | Gate | short walk | public | open | workers | none | yes | 1 |"])
    compiler.compile_campaign(campaign)
    atlas_path = campaign / "map_atlas.json"
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    route = copy.deepcopy(next(item for item in atlas["features"] if item.get("route_ref")))
    route["id"] = "duplicate-route"
    atlas["features"].append(route)
    atlas_path.write_text(json.dumps(atlas, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(compiler.AtlasCompileError) as error:
        compiler.compile_campaign(campaign, apply=False)

    assert error.value.category == "atlas_invalid"
    assert "Duplicate route_ref" in str(error.value)


def test_disabled_map_policy_refuses_compilation(campaign: Path) -> None:
    _write_graph(campaign, ["| Quay | <-> | Gate | short walk | public | open | workers | none | yes | 1 |"])

    with pytest.raises(compiler.AtlasCompileError) as error:
        compiler.compile_campaign(campaign, apply=False)

    assert error.value.category == "dashboard_map_disabled"


def test_compiler_rejects_invalid_direction(campaign: Path) -> None:
    _enable_map(campaign)
    _write_graph(campaign, ["| Quay | sideways | Gate | short walk | public | open | workers | none | yes | 1 |"])

    with pytest.raises(compiler.AtlasCompileError) as error:
        compiler.compile_campaign(campaign, apply=False)

    assert error.value.category == "location_graph_invalid"

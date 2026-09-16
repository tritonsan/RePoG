from __future__ import annotations

import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest


PRODUCT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str):
    path = PRODUCT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


check_state = _load("preflight_check_state", "tools/check_state.py")
snapshot = _load("preflight_snapshot", "tools/snapshot.py")


def _replace_top(text: str, key: str, value: str) -> str:
    return re.sub(rf"(?m)^{re.escape(key)}:.*$", f"{key}: {value}", text, count=1)


def _rules(result: dict) -> set[str]:
    return {item["rule"] for item in result["findings"]}


@pytest.fixture()
def campaign(tmp_path: Path) -> Path:
    target = tmp_path / "campaign"
    shutil.copytree(PRODUCT / "campaign", target)
    setup_path = target / "setup_profile.yaml"
    setup = setup_path.read_text(encoding="utf-8")
    for key, value in (
        ("schema_version", "3"),
        ("status", "in_progress"),
        ("setup_revision", "0"),
        ("experience_mode", "rpg"),
        ("session_zero_mode", "quick"),
        ("questions_completed", "0"),
        ("ready_for_play", "false"),
    ):
        setup = _replace_top(setup, key, value)
    setup_path.write_text(setup, encoding="utf-8")
    return target


def test_preflight_validates_ready_content_without_requiring_final_flags_or_snapshot(campaign: Path) -> None:
    normal_rules = _rules(check_state.check_campaign(campaign, scope="full"))
    preflight_rules = _rules(check_state.check_campaign(campaign, scope="full", preflight_ready=True))

    assert "ready_player_missing" not in normal_rules
    assert "ready_player_missing" in preflight_rules
    assert "ready_opening_incomplete" in preflight_rules
    assert "world_operating_model_missing" in preflight_rules
    assert "quick_defaults_missing" in preflight_rules
    assert "play_profile_not_locked" not in preflight_rules
    assert "setup_ready_mismatch" not in preflight_rules
    assert "ready_snapshot_missing" not in preflight_rules
    assert "ready_dashboard_missing" not in preflight_rules


def test_preflight_requires_an_in_progress_draft(campaign: Path) -> None:
    setup_path = campaign / "setup_profile.yaml"
    setup = _replace_top(setup_path.read_text(encoding="utf-8"), "status", "pending")
    setup_path.write_text(setup, encoding="utf-8")

    rules = _rules(check_state.check_campaign(campaign, scope="hot", preflight_ready=True))

    assert "preflight_requires_in_progress" in rules


def test_preflight_flag_does_not_weaken_an_already_ready_campaign(campaign: Path) -> None:
    setup_path = campaign / "setup_profile.yaml"
    setup = setup_path.read_text(encoding="utf-8")
    setup = _replace_top(setup, "status", "complete")
    setup = _replace_top(setup, "ready_for_play", "true")
    setup_path.write_text(setup, encoding="utf-8")

    rules = _rules(check_state.check_campaign(campaign, scope="full", preflight_ready=True))

    assert "ready_snapshot_missing" in rules
    assert "play_profile_not_locked" in rules


def test_companion_preflight_requires_permanent_campaign_id(campaign: Path) -> None:
    setup_path = campaign / "setup_profile.yaml"
    setup = _replace_top(setup_path.read_text(encoding="utf-8"), "experience_mode", "companion")
    setup_path.write_text(setup, encoding="utf-8")

    rules = _rules(check_state.check_campaign(campaign, scope="hot", preflight_ready=True))

    assert "ready_campaign_id_placeholder" in rules


def _write_identity_campaign(
    root: Path,
    *,
    experience_mode: str = "rpg",
    ready: bool = True,
    setup_revision: int = 7,
    continuity_revision: int = 9,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "setup_profile.yaml").write_text(
        "\n".join(
            (
                "schema_version: 4",
                f"status: {'complete' if ready else 'in_progress'}",
                f"setup_revision: {setup_revision}",
                f"experience_mode: {experience_mode}",
                f"ready_for_play: {str(ready).lower()}",
                "",
            )
        ),
        encoding="utf-8",
    )
    (root / "current_state.yaml").write_text(
        f"campaign_id: snapshot_test\ncontinuity_revision: {continuity_revision}\n",
        encoding="utf-8",
    )
    (root / "companion_state.json").write_text(
        json.dumps({"continuity_revision": continuity_revision}),
        encoding="utf-8",
    )


@pytest.mark.parametrize("experience_mode", ("rpg", "companion"))
def test_snapshot_writes_revision_bound_v2_identity(tmp_path: Path, experience_mode: str) -> None:
    campaign = tmp_path / experience_mode
    _write_identity_campaign(campaign, experience_mode=experience_mode)

    result = snapshot.create_snapshot(campaign, "start")

    assert result["ok"] is True
    manifest_path = next((campaign / "snapshots").glob("*/snapshot_manifest.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 2
    assert manifest["campaign_id"] == "snapshot_test"
    assert manifest["setup_revision"] == 7
    assert manifest["continuity_revision"] == 9
    assert manifest["ready_for_play"] is True
    assert manifest["setup_status"] == "complete"
    assert manifest["experience_mode"] == experience_mode


def _snapshot_rules(campaign: Path) -> set[str]:
    findings: list[dict] = []
    check_state._check_ready_snapshot(
        campaign,
        setup={
            "setup_revision": 7,
            "experience_mode": "rpg",
        },
        findings=findings,
    )
    return {item["rule"] for item in findings}


def _write_manifest(campaign: Path, name: str, data: dict) -> None:
    path = campaign / "snapshots" / name / "snapshot_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_ready_snapshot_accepts_matching_v2_manifest(tmp_path: Path) -> None:
    campaign = tmp_path / "campaign"
    _write_identity_campaign(campaign)
    _write_manifest(
        campaign,
        "matching",
        {
            "manifest_version": 2,
            "campaign_id": "snapshot_test",
            "setup_revision": 7,
            "continuity_revision": 9,
            "ready_for_play": True,
            "setup_status": "complete",
            "experience_mode": "rpg",
        },
    )
    assert "ready_snapshot_stale" not in _snapshot_rules(campaign)


def test_legacy_only_ready_snapshot_is_unverified_warning(tmp_path: Path) -> None:
    campaign = tmp_path / "campaign"
    _write_identity_campaign(campaign)
    _write_manifest(campaign, "legacy", {"created_at": "old", "files": []})
    rules = _snapshot_rules(campaign)
    assert "snapshot_revision_unverified" in rules
    assert "ready_snapshot_stale" not in rules


def test_stale_v2_snapshot_cannot_be_masked_by_legacy_manifest(tmp_path: Path) -> None:
    campaign = tmp_path / "campaign"
    _write_identity_campaign(campaign)
    _write_manifest(campaign, "legacy", {"created_at": "old", "files": []})
    _write_manifest(
        campaign,
        "stale_v2",
        {
            "manifest_version": 2,
            "campaign_id": "snapshot_test",
            "setup_revision": 7,
            "continuity_revision": 8,
            "ready_for_play": False,
            "setup_status": "in_progress",
            "experience_mode": "rpg",
        },
    )
    rules = _snapshot_rules(campaign)
    assert "ready_snapshot_stale" in rules
    assert "snapshot_revision_unverified" not in rules

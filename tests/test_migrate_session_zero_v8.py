from __future__ import annotations

import importlib.util
import json
import re
import re
import shutil
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


migrator = _load(
    "migrate_session_zero_v8",
    PUBLIC / "tools" / "migrate_session_zero_v8.py",
)
state_tool = _load(
    "session_zero_state_for_migration",
    PUBLIC / "tools" / "session_zero_state.py",
)


@pytest.fixture()
def campaign(tmp_path: Path) -> Path:
    target = tmp_path / "campaign"
    shutil.copytree(PUBLIC / "campaign", target)
    setup = target / "setup_profile.yaml"
    text = setup.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^schema_version: [0-9]+$", "schema_version: 7", text, count=1)
    setup.write_text(text, encoding="utf-8")
    (target / "session_zero_state.json").unlink(missing_ok=True)
    return target


def _setup(campaign: Path, **changes: str) -> None:
    path = campaign / "setup_profile.yaml"
    text = path.read_text(encoding="utf-8")
    for key, value in changes.items():
        pattern = rf"(?m)^{re.escape(key)}:\s*.*?$"
        assert re.search(pattern, text), key
        text = re.sub(pattern, f"{key}: {value}", text, count=1)
    path.write_text(text, encoding="utf-8")


def _module_status(campaign: Path, number: int, status: str) -> None:
    path = campaign / "session_zero.md"
    text = path.read_text(encoding="utf-8")
    heading = text.index("## RPG Standard / Deep Reciprocity Module Status")
    end = text.index("\n## ", heading + 1)
    block = text[heading:end]
    pattern = rf"(?m)^(-\s+{number}\.\s+.+?):\s*open\s*$"
    assert re.search(pattern, block), number
    block = re.sub(pattern, rf"\1: {status}", block, count=1)
    path.write_text(text[:heading] + block + text[end:], encoding="utf-8")


def _snapshot(campaign: Path) -> None:
    folder = campaign / "snapshots" / "before_v8"
    folder.mkdir(parents=True, exist_ok=True)
    files = [
        {"path": path.relative_to(campaign).as_posix()}
        for path in campaign.rglob("*")
        if path.is_file() and (campaign / "snapshots") not in path.parents
    ]
    (folder / "snapshot_manifest.json").write_text(
        json.dumps(
            {
                "kind": "full-campaign-snapshot",
                "files": files,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _without_managed_summary(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    match = re.search(
        r"(?ms)^## RPG Deep v8 Stage Summary\s*$.*?(?=^##\s+|\Z)", text
    )
    if not match:
        return text.rstrip()
    return text[: match.start()].rstrip() + "\n" + text[match.end() :].lstrip()


def test_pending_blank_dry_run_is_read_only_and_apply_is_idempotent(campaign: Path) -> None:
    setup_path = campaign / "setup_profile.yaml"
    before = setup_path.read_bytes()

    dry = migrator.migrate(campaign, apply=False)
    assert dry["ok"] and dry["eligible"] and dry["routing_only"]
    assert dry["would_migrate"] and not dry["migrated"]
    assert setup_path.read_bytes() == before
    assert not (campaign / "session_zero_state.json").exists()

    applied = migrator.migrate(campaign, apply=True)
    assert applied["ok"] and applied["migrated"]
    assert "schema_version: 8" in setup_path.read_text(encoding="utf-8")
    state = json.loads((campaign / "session_zero_state.json").read_text(encoding="utf-8"))
    assert state["flow_id"] == "rpg_deep_v8"
    assert state["current_stage"] == "01_north_star_authority"
    assert state["stages"]["01_north_star_authority"]["status"] == "active"
    assert state["decisions"] == []

    again = migrator.migrate(campaign, apply=True)
    assert again["ok"] and not again["changed"]
    assert again["reason"] == "already_v8"


def test_pending_deep_apply_produces_canonical_valid_state(campaign: Path) -> None:
    _setup(
        campaign,
        experience_mode="rpg",
        session_zero_mode="deep",
        status="in_progress",
    )
    result = migrator.migrate(campaign, apply=True)
    assert result["ok"] and result["routing_only"] and result["migrated"], result
    validation = state_tool.validate_campaign_state(campaign)
    assert validation["ok"], validation["findings"]
    state = validation["state"]
    assert state["fatigue"]["last_checkpoint_decision_count"] == 0
    assert "## RPG Deep v8 Stage Summary" in (
        campaign / "session_zero.md"
    ).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("experience", "depth", "reason"),
    (
        ("rpg", "quick", "quick_untouched"),
        ("rpg", "standard", "standard_untouched"),
        ("companion", "deep", "companion_untouched"),
    ),
)
def test_non_deep_routes_are_untouched(
    campaign: Path, experience: str, depth: str, reason: str
) -> None:
    _setup(campaign, experience_mode=experience, session_zero_mode=depth, status="in_progress")
    before = (campaign / "setup_profile.yaml").read_bytes()
    result = migrator.migrate(campaign, apply=True)
    assert result["ok"] and not result["eligible"] and not result["changed"]
    assert result["reason"] == reason
    assert (campaign / "setup_profile.yaml").read_bytes() == before
    assert not (campaign / "session_zero_state.json").exists()


def test_completed_deep_v7_stays_v7(campaign: Path) -> None:
    _setup(
        campaign,
        experience_mode="rpg",
        session_zero_mode="deep",
        status="complete",
        ready_for_play="true",
    )
    before = (campaign / "setup_profile.yaml").read_bytes()
    result = migrator.migrate(campaign, apply=True)
    assert result["ok"] and result["reason"] == "completed_v7_preserved"
    assert not result["changed"]
    assert (campaign / "setup_profile.yaml").read_bytes() == before


def test_in_progress_deep_requires_snapshot_before_apply(campaign: Path) -> None:
    _setup(
        campaign,
        experience_mode="rpg",
        session_zero_mode="deep",
        status="in_progress",
        questions_completed="3",
        setup_revision="5",
    )
    _module_status(campaign, 1, "locked")
    result = migrator.migrate(campaign, apply=True)
    assert not result["ok"] and result["error"] == "snapshot_required"
    assert result["snapshot"]["required"] is True
    assert result["snapshot"]["command"][-1] == "before_session_zero_v8"

    fake = campaign / "snapshots" / "incomplete"
    fake.mkdir(parents=True)
    (fake / "snapshot_manifest.json").write_text(
        json.dumps({"files": ["setup_profile.yaml", "session_zero.md"]}) + "\n",
        encoding="utf-8",
    )
    still_blocked = migrator.migrate(campaign, apply=True)
    assert not still_blocked["ok"] and still_blocked["error"] == "snapshot_required"
    assert "schema_version: 7" in (campaign / "setup_profile.yaml").read_text(encoding="utf-8")
    assert not (campaign / "session_zero_state.json").exists()


def test_in_progress_maps_reliable_decisions_reviews_splits_and_preserves_fiction(
    campaign: Path,
) -> None:
    _setup(
        campaign,
        experience_mode="rpg",
        session_zero_mode="deep",
        status="in_progress",
        questions_completed="8",
        setup_revision="11",
        design_direction_approved_revision="10",
        preparation_approved_revision="10",
        activated_packs="[source_grounding, mechanics_progression]",
        completed_packs="[source_grounding]",
    )
    for number, status in (
        (1, "locked"),
        (2, "locked"),
        (3, "locked"),
        (4, "locked"),
        (5, "locked_with_open_questions"),
        (6, "defaulted"),
        (8, "locked"),
        (15, "locked"),
        (16, "locked"),
        (20, "locked"),
    ):
        _module_status(campaign, number, status)
    _snapshot(campaign)

    world_path = campaign / "world.md"
    session_path = campaign / "session_zero.md"
    world_before = world_path.read_bytes()
    session_before = session_path.read_bytes()

    dry = migrator.migrate(campaign, apply=False)
    assert dry["ok"] and str(session_path) in dry["changed_files"]
    assert session_path.read_bytes() == session_before

    result = migrator.migrate(campaign, apply=True)
    assert result["ok"] and result["migrated"], result
    assert result["mapped_decisions"] == 11
    assert world_path.read_bytes() == world_before
    session_after = session_path.read_text(encoding="utf-8")
    assert _without_managed_summary(session_after) == _without_managed_summary(
        session_before.decode("utf-8")
    )
    assert "- Setup revision: 11" in session_after
    assert "- Decisions recorded: 11" in session_after
    assert "(`01_north_star_authority`)" in session_after

    setup_text = (campaign / "setup_profile.yaml").read_text(encoding="utf-8")
    assert "schema_version: 8" in setup_text
    assert "design_direction_approved_revision: null" in setup_text
    assert "preparation_approved_revision: null" in setup_text
    assert "activated_packs: []" in setup_text
    assert "deep_flow_id: rpg_deep_v8" in setup_text
    assert "session_zero_state_path: session_zero_state.json" in setup_text

    state = json.loads((campaign / "session_zero_state.json").read_text(encoding="utf-8"))
    ids = {item["decision_id"] for item in state["decisions"]}
    assert "v7_module_01_campaign_promise_player_fantasy" in ids
    module_six = next(item for item in state["decisions"] if item["decision_id"].startswith("v7_module_06_"))
    assert module_six["status"] == "defaulted"
    assert state["stages"]["05_character_realization_mechanics"]["status"] == "needs_review"
    assert state["stages"]["07_runtime_experience_contract"]["status"] == "needs_review"
    assert state["stages"]["02_research_canon_grounding"]["status"] == "needs_review"
    assert state["stages"]["08_reciprocity_campaign_horizon"]["status"] == "needs_review"
    assert state["stages"]["09_first_act_preparation"]["status"] == "needs_review"
    assert set(state["extensions"]) == {
        "character_interior",
        "world_fabric",
        "mechanics_detail",
        "location_network",
        "faction_information",
        "group",
        "character_embedding",
        "advancement_detail",
        "campaign_architecture",
    }
    assert all(item["status"] == "not_applicable" for item in state["extensions"].values())
    assert all(item["activated_by"] == [] for item in state["extensions"].values())
    assert any(item["decision_id"] == "v7_pack_mechanics_progression" for item in state["decisions"])
    assert any(item["decision_id"] == "v7_pack_source_grounding" for item in state["decisions"])
    assert not any(item["decision_id"].startswith("v7_module_20_") for item in state["decisions"])
    assert all(gate["status"] == "pending" for gate in state["gates"].values())
    assert all(gate["revision"] is None for gate in state["gates"].values())
    assert all(item["created_revision"] == 11 for item in state["decisions"])
    assert state["fatigue"]["last_checkpoint_decision_count"] == 0
    validation = state_tool.validate_campaign_state(campaign)
    assert validation["ok"], validation["findings"]


def test_routing_only_after_experience_choice_migrates_without_snapshot(campaign: Path) -> None:
    _setup(
        campaign,
        experience_mode="rpg",
        session_zero_mode='""',
        status="in_progress",
        setup_revision="1",
    )
    result = migrator.migrate(campaign, apply=True)
    assert result["ok"] and result["routing_only"] and result["migrated"]
    setup = (campaign / "setup_profile.yaml").read_text(encoding="utf-8")
    assert "experience_mode: rpg" in setup
    assert 'session_zero_mode: ""' in setup


def test_apply_rolls_back_setup_when_state_write_fails(
    campaign: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    setup_path = campaign / "setup_profile.yaml"
    before = setup_path.read_bytes()
    original = migrator._atomic_text
    failed = False

    def flaky_write(path: Path, text: str) -> None:
        nonlocal failed
        if path.name == "session_zero_state.json" and not failed:
            failed = True
            raise OSError("simulated state write failure")
        original(path, text)

    monkeypatch.setattr(migrator, "_atomic_text", flaky_write)
    result = migrator.migrate(campaign, apply=True)
    assert not result["ok"] and result["error"] == "migration_write_failed"
    assert setup_path.read_bytes() == before
    assert not (campaign / "session_zero_state.json").exists()


def test_main_requires_explicit_mode(campaign: Path) -> None:
    with pytest.raises(SystemExit):
        migrator.main(["--campaign", str(campaign)])
    with pytest.raises(SystemExit):
        migrator.main(["--campaign", str(campaign), "--dry-run", "--apply"])

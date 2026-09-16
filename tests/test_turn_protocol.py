from __future__ import annotations

import importlib.util
import re
import shutil
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


check_state = _load("public_turn_protocol_check_state", PUBLIC / "tools" / "check_state.py")
migrator = _load("public_turn_protocol_migrator", PUBLIC / "tools" / "migrate_gm_contract.py")


@pytest.fixture()
def campaign(tmp_path: Path) -> Path:
    target = tmp_path / "campaign"
    shutil.copytree(PUBLIC / "campaign", target)
    return target


def _rules(result: dict) -> set[str]:
    return {finding["rule"] for finding in result["findings"]}


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new), encoding="utf-8")


def _select_fast(campaign: Path) -> None:
    path = campaign / "play_profile.yaml"
    replacements = {
        'turn_protocol: ""': "turn_protocol: fast",
        'cold_distill_policy: ""': "cold_distill_policy: scene_checkpoint_or_5_durable",
        'validation_policy: ""': "validation_policy: full_on_distill",
        'style_review_policy: ""': "style_review_policy: sampled_and_distill",
    }
    text = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        assert old in text
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def _set_pending_revisions(campaign: Path, count: int) -> None:
    state_path = campaign / "current_state.yaml"
    text = state_path.read_text(encoding="utf-8")
    text = text.replace("continuity_revision: 0", f"continuity_revision: {count}")
    text = text.replace("durable_turns_since_distill: 0", f"durable_turns_since_distill: {count}")
    state_path.write_text(text, encoding="utf-8")

    log_path = campaign / "session_log.md"
    with log_path.open("a", encoding="utf-8") as handle:
        for revision in range(1, count + 1):
            handle.write(
                f"\n### Durable Revision {revision}\n\n"
                f"- Event: test event {revision}\n"
                "- Immediate files: current_state.yaml\n"
                "- Pending cold targets: none\n"
            )


def test_blank_schema_v2_template_passes_hot_and_full(campaign: Path) -> None:
    assert check_state.check_campaign(campaign, scope="hot")["error_count"] == 0
    assert check_state.check_campaign(campaign, scope="full")["error_count"] == 0


def test_check_state_cli_accepts_hot_scope(campaign: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert check_state.main([str(campaign), "--scope", "hot"]) == 0
    assert '"scope": "hot"' in capsys.readouterr().out


def test_session_zero_copy_discloses_profiles_and_visual_costs() -> None:
    worldbuild = (PUBLIC / "workflows" / "worldbuild" / "WORKFLOW.md").read_text(encoding="utf-8")
    brief = (PUBLIC / "briefs" / "campaign_creation_interview.md").read_text(encoding="utf-8")
    for text in (worldbuild, brief):
        assert "Fast" in text
        assert "Balanced" in text
        assert "Maximum Continuity" in text
        assert "1–2 minutes" in text
        assert "1–3+ minutes" in text


def test_fast_preset_materializes_expected_policies(campaign: Path) -> None:
    _select_fast(campaign)
    result = check_state.check_campaign(campaign, scope="hot")
    assert result["error_count"] == 0
    assert "turn_preset_mismatch" not in _rules(result)


def test_fast_preset_rejects_policy_drift(campaign: Path) -> None:
    _select_fast(campaign)
    _replace(
        campaign / "play_profile.yaml",
        "cold_distill_policy: scene_checkpoint_or_5_durable",
        "cold_distill_policy: scene_checkpoint_only",
    )
    assert "turn_preset_mismatch" in _rules(check_state.check_campaign(campaign, scope="hot"))


def test_custom_rejects_disabled_validation(campaign: Path) -> None:
    path = campaign / "play_profile.yaml"
    text = path.read_text(encoding="utf-8")
    text = text.replace('turn_protocol: ""', "turn_protocol: custom")
    text = text.replace('cold_distill_policy: ""', "cold_distill_policy: scene_only")
    text = text.replace('validation_policy: ""', "validation_policy: disabled")
    text = text.replace('style_review_policy: ""', "style_review_policy: sampled_and_distill")
    path.write_text(text, encoding="utf-8")
    assert "play_profile_field_invalid" in _rules(check_state.check_campaign(campaign, scope="hot"))


def test_ready_campaign_requires_estimate_acknowledgement(campaign: Path) -> None:
    _select_fast(campaign)
    path = campaign / "setup_profile.yaml"
    text = path.read_text(encoding="utf-8")
    text = text.replace("status: pending", "status: complete")
    text = text.replace('session_zero_mode: ""', "session_zero_mode: standard")
    text = text.replace("ready_for_play: false", "ready_for_play: true")
    path.write_text(text, encoding="utf-8")
    assert "performance_estimate_unacknowledged" in _rules(
        check_state.check_campaign(campaign, scope="hot")
    )


def test_pending_fast_profile_is_valid(campaign: Path) -> None:
    _select_fast(campaign)
    result = check_state.check_campaign(campaign, scope="hot")
    assert result["error_count"] == 0


def test_fast_allows_four_pending_durable_turns(campaign: Path) -> None:
    _select_fast(campaign)
    _set_pending_revisions(campaign, 4)
    result = check_state.check_campaign(campaign, scope="hot")
    assert result["error_count"] == 0
    assert "persistence_distill_overdue" not in _rules(result)


def test_fast_requires_distill_on_fifth_durable_turn(campaign: Path) -> None:
    _select_fast(campaign)
    _set_pending_revisions(campaign, 5)
    assert "persistence_distill_overdue" in _rules(
        check_state.check_campaign(campaign, scope="hot")
    )


def test_scene_checkpoint_alone_never_counts_as_full_distill(campaign: Path) -> None:
    _select_fast(campaign)
    _set_pending_revisions(campaign, 1)
    with (campaign / "session_log.md").open("a", encoding="utf-8") as handle:
        handle.write("\n### Scene Checkpoint Revision 1\n\n- Resume anchor: player still has control\n")
    result = check_state.check_campaign(campaign, scope="hot")
    assert "scene_checkpoint_forced_full_distill" not in _rules(result)
    state = (campaign / "current_state.yaml").read_text(encoding="utf-8")
    assert "last_distilled_revision: 0" in state


def test_missing_durable_event_is_an_error(campaign: Path) -> None:
    _select_fast(campaign)
    _replace(campaign / "current_state.yaml", "continuity_revision: 0", "continuity_revision: 1")
    _replace(
        campaign / "current_state.yaml",
        "durable_turns_since_distill: 0",
        "durable_turns_since_distill: 1",
    )
    assert "durable_event_missing" in _rules(check_state.check_campaign(campaign, scope="hot"))


def test_duplicate_durable_event_is_an_error(campaign: Path) -> None:
    _select_fast(campaign)
    _set_pending_revisions(campaign, 1)
    with (campaign / "session_log.md").open("a", encoding="utf-8") as handle:
        handle.write("\n### Durable Revision 1\n\n- Event: duplicate\n")
    assert "durable_event_duplicate" in _rules(
        check_state.check_campaign(campaign, scope="hot")
    )


def test_distill_marker_resets_persistence(campaign: Path) -> None:
    _select_fast(campaign)
    _replace(campaign / "current_state.yaml", "continuity_revision: 0", "continuity_revision: 5")
    _replace(
        campaign / "current_state.yaml",
        "last_distilled_revision: 0",
        "last_distilled_revision: 5",
    )
    with (campaign / "session_log.md").open("a", encoding="utf-8") as handle:
        handle.write("\n### Distilled Through Revision 5\n\n- Trigger: scene boundary\n- Files reconciled: all pending\n")
    result = check_state.check_campaign(campaign, scope="hot")
    assert result["error_count"] == 0


def test_hot_scope_skips_cold_freshness_warnings(campaign: Path) -> None:
    _select_fast(campaign)
    _set_pending_revisions(campaign, 1)
    hot_rules = _rules(check_state.check_campaign(campaign, scope="hot"))
    full_rules = _rules(check_state.check_campaign(campaign, scope="full"))
    assert "session_brief_stale" not in hot_rules
    assert "session_brief_stale" in full_rules


def test_schema_v1_campaign_preserves_legacy_behavior(campaign: Path) -> None:
    setup = campaign / "setup_profile.yaml"
    lines = setup.read_text(encoding="utf-8").splitlines()
    legacy_keys = {
        "turn_protocol",
        "cold_distill_policy",
        "validation_policy",
        "dashboard_refresh_policy",
        "style_review_policy",
        "latency_notice_policy",
        "performance_estimate_acknowledged",
    }
    lines = [
        "schema_version: 1" if line.startswith("schema_version:") else line
        for line in lines
        if line.split(":", 1)[0] not in legacy_keys
    ]
    setup.write_text("\n".join(lines) + "\n", encoding="utf-8")

    state = campaign / "current_state.yaml"
    text = state.read_text(encoding="utf-8")
    start = text.index("persistence:\n")
    end = text.index("fictional_time:\n")
    state.write_text(text[:start] + text[end:], encoding="utf-8")

    result = check_state.check_campaign(campaign, scope="hot")
    assert result["error_count"] == 0
    assert {"turn_protocol_legacy", "persistence_status_missing"} <= _rules(result)


def test_legacy_hot_validation_alias_is_accepted_without_preset_drift(campaign: Path) -> None:
    _select_fast(campaign)
    _replace(
        campaign / "play_profile.yaml",
        "validation_policy: full_on_distill",
        "validation_policy: hot_each_durable_full_on_distill",
    )
    result = check_state.check_campaign(campaign, scope="hot")
    rules = _rules(result)
    assert result["error_count"] == 0
    assert "legacy_hot_validation_policy" in rules
    assert "turn_preset_mismatch" not in rules


def test_transaction_journal_entry_requires_recovery_but_empty_directory_is_valid(
    campaign: Path,
) -> None:
    journal = campaign / ".repog-transactions"
    journal.mkdir()
    assert "rpg_transaction_recovery_required" not in _rules(
        check_state.check_campaign(campaign, scope="hot")
    )

    (journal / "pending").mkdir()
    result = check_state.check_campaign(campaign, scope="hot")
    assert "rpg_transaction_recovery_required" in _rules(result)
    assert result["error_count"] >= 1


def test_legacy_validation_policy_migrates_only_through_explicit_migration(
    campaign: Path,
) -> None:
    _select_fast(campaign)
    profile = campaign / "play_profile.yaml"
    _replace(
        profile,
        "validation_policy: full_on_distill",
        "validation_policy: hot_each_durable_full_on_distill",
    )
    before = profile.read_text(encoding="utf-8")

    dry_run = migrator.migrate(campaign, apply=False)
    assert dry_run["ok"] and dry_run["changed"]
    assert any(
        item["action"]
        == "map validation_policy hot_each_durable_full_on_distill -> full_on_distill"
        for item in dry_run["actions"]
    )
    assert profile.read_text(encoding="utf-8") == before

    snapshot = campaign / "snapshots" / "before_validation_policy_migration"
    snapshot.mkdir(parents=True)
    (snapshot / "snapshot_manifest.json").write_text("{}\n", encoding="utf-8")
    applied = migrator.migrate(campaign, apply=True)
    assert applied["ok"] and applied["changed"]
    assert "validation_policy: full_on_distill" in profile.read_text(encoding="utf-8")
    assert migrator.migrate(campaign, apply=True)["changed"] is False

"""Versioned setup accounting must not silently change existing campaigns."""

from pathlib import Path

import pytest

from test_workspace_contracts import (
    campaign, check_state, _write_setup_profile, _setup_rules, _replace_status_block,
)


def profile(campaign: Path, *, mode="quick", target=9, completed=9,
            revision=9, design=8, preparation=9, schema=9):
    _write_setup_profile(
        campaign, schema_version=schema, session_zero_mode=mode,
        question_target=target, questions_completed=completed,
        setup_revision=revision, design_approved_revision=design,
        preparation_approved_revision=preparation, defaults_reviewed=True,
    )
    path = campaign / "setup_profile.yaml"
    path.write_text(path.read_text(encoding="utf-8") +
                    "deep_flow_id: rpg_deep_v8\nsession_zero_state_path: session_zero_state.json\n",
                    encoding="utf-8")


def test_quick_v9_combined_review_passes_without_tenth_decision(campaign: Path):
    profile(campaign)
    _replace_status_block(campaign, "RPG Quick v9 Decision Slot Status", "locked")
    rules = _setup_rules(campaign, preflight_ready=True)
    assert not rules & {
        "setup_question_target_invalid", "quick_question_target", "setup_modules_open",
        "setup_preparation_approval_missing", "setup_preparation_approval_stale",
        "setup_approval_order_invalid", "setup_defaults_not_reviewed",
    }


@pytest.mark.parametrize(("preparation", "revision", "expected"), [
    (None, 9, "setup_preparation_approval_missing"),
    (9, 10, "setup_preparation_approval_stale"),
    (8, 9, "setup_approval_order_invalid"),
])
def test_combined_review_still_requires_current_ordered_approval(
    campaign: Path, preparation, revision, expected
):
    profile(campaign, preparation=preparation, revision=revision)
    assert expected in _setup_rules(campaign, preflight_ready=True)


def test_v9_cannot_reuse_completed_legacy_status_block(campaign: Path):
    profile(campaign)
    _replace_status_block(campaign, "RPG Quick Decision Slot Status", "locked")
    assert "setup_modules_open" in _setup_rules(campaign, preflight_ready=True)


@pytest.mark.parametrize(("target", "valid"), [(19, False), (20, True), (29, True), (30, False)])
def test_standard_v9_target_has_twenty_core_decisions(campaign: Path, target, valid):
    profile(campaign, mode="standard", target=target, completed=20,
            revision=20, design=19, preparation=20)
    _replace_status_block(campaign, "RPG Standard v9 Module Status", "locked")
    rules = _setup_rules(campaign, preflight_ready=True)
    assert ("setup_question_target_invalid" not in rules) == valid
    assert "setup_modules_open" not in rules
    assert "setup_preparation_approval_missing" not in rules


@pytest.mark.parametrize("schema", [6, 7, 8])
def test_legacy_quick_does_not_silently_lose_final_decision(campaign: Path, schema):
    profile(campaign, schema=schema, target=9)
    rules = _setup_rules(campaign, preflight_ready=True)
    assert "setup_question_target_invalid" in rules
    assert "quick_question_target" in rules
    profile(campaign, schema=schema, target=10, completed=10, revision=10, preparation=10)
    _replace_status_block(campaign, "RPG Quick Decision Slot Status", "locked")
    assert not _setup_rules(campaign, preflight_ready=True) & {
        "setup_question_target_invalid", "quick_question_target", "setup_modules_open",
    }


def test_idle_shared_lock_and_empty_journal_are_not_unfinished_work(campaign: Path):
    import file_transaction
    with file_transaction.campaign_lock(campaign):
        file_transaction.commit_files(campaign, {"test-owner.md": b"Synthetic fixture\n"})
    findings = []
    check_state._check_rpg_transaction_journal(campaign, findings)
    assert not findings
    (campaign / ".repog-transactions" / "files" / "unfinished").mkdir()
    check_state._check_rpg_transaction_journal(campaign, findings)
    assert findings[0]["rule"] == "rpg_transaction_recovery_required"

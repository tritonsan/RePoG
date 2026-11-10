"""Materialized Quick/Standard handoff through real persistence, not an LLM interview."""
import json
import re

import pytest
import check_state
import snapshot
import rpg_state
import file_transaction

from test_deep_session_zero_v8_integration import (
    manifest, ready_deep_seed, ready_deep_campaign, _set_setup, _set_profile,
)


@pytest.mark.parametrize("mode", ["quick", "standard"])
def test_materialized_route_preflight_start_play_and_ooc_configuration(ready_deep_campaign, mode):
    # Reuse synthetic materialized owners, not the Deep route's acceptance:
    # give the selected route its own ordered approvals, locks and snapshot.
    campaign = ready_deep_campaign
    _set_setup(campaign, schema_version=10, session_zero_mode=mode, status="in_progress",
               ready_for_play="false", setup_revision=102, questions_completed=36, last_checkpoint=0,
               design_direction_approved_revision=101, preparation_approved_revision=102,
               defaults_reviewed="true", question_target='""')
    for filename, status in (("play_profile.yaml", "pending"), ("companion_profile.yaml", "inactive")):
        _set_profile(campaign, filename, profile_status=status, source_setup_revision=102)
    path = campaign / "session_zero.md"
    text = path.read_text(encoding="utf-8")
    heading = check_state._selected_status_heading("rpg", mode, 10)
    rows = "\n".join(f"- {i}. {name}: locked" for i, name in enumerate(check_state.RPG_V10_REQUIRED_DECISIONS[mode], 1))
    pattern = rf"(?ms)^## {re.escape(heading)}\s*\n.*?(?=^## |\Z)"
    text, count = re.subn(pattern, f"## {heading}\n\n{rows}\n\n", text)
    if count == 0:
        text += f"\n## {heading}\n\n{rows}\n"
    path.write_text(text, encoding="utf-8")
    report = check_state.check_campaign(campaign, scope="full", preflight_ready=True)
    assert report["error_count"] == 0, report["findings"]
    _set_profile(campaign, "play_profile.yaml", profile_status="locked")
    _set_setup(campaign, status="complete", ready_for_play="true")
    result = snapshot.create_snapshot(campaign, f"session-zero-start-{mode}")
    assert result["ok"], result
    report = check_state.check_campaign(campaign, scope="full")
    assert report["error_count"] == 0, report["findings"]

    threads = (campaign / "threads.md").read_text(encoding="utf-8")
    payload = {
        "operation_id": f"{mode}-first-delivery", "expected_continuity_revision": 0,
        "boundary": "ordinary", "cause": "The player accepted a delivery.",
        "resume_impact": "The agreed delivery remains open.",
        "changes": [{"id": "delivery", "kind": "thread", "established_delta": "The player agreed to deliver a letter.",
                     "owners": ["threads.md"], "cold_targets": []}],
        "mutations": [{"path": "threads.md", "exact_replacements": [{"old": threads,
                        "new": threads + "\n- Agreed delivery: Carry a letter to the harbor office.\n"}]}],
    }
    committed = rpg_state.commit_durable(campaign, payload)
    assert committed["ok"] and committed["narration_allowed"]
    assert rpg_state.commit_durable(campaign, payload)["idempotent"]

    def validate():
        report = check_state.check_campaign(campaign, scope="full")
        assert report["error_count"] == 0, report["findings"]

    with file_transaction.campaign_lock(campaign):
        changes = {}
        for filename, old, new in (
            ("opening_brief.md", "Opening status: `active`", "Opening status: `consumed`"),
            ("first_session.md", "Prep status: `materialized`", "Prep status: `consumed`"),
        ):
            text = (campaign / filename).read_text(encoding="utf-8")
            assert old in text
            changes[filename] = text.replace(old, new).encode("utf-8")
        changes["boundaries.md"] = (campaign / "boundaries.md").read_bytes() + b"\nOOC handoff explained before opening.\n"
        file_transaction.commit_files(campaign, changes, validate_applied=validate)
    before_state = (campaign / "current_state.yaml").read_bytes()
    before_log = (campaign / "session_log.md").read_bytes()
    with file_transaction.campaign_lock(campaign):
        text = (campaign / "play_profile.yaml").read_text(encoding="utf-8")
        assert "response_length: dynamic" in text
        file_transaction.commit_files(campaign, {"play_profile.yaml": text.replace("response_length: dynamic", "response_length: brief").encode("utf-8")}, validate_applied=validate)
    assert (campaign / "current_state.yaml").read_bytes() == before_state
    assert (campaign / "session_log.md").read_bytes() == before_log
    validate()

    # Turn on tracking as one configuration batch, without inventing elapsed
    # time, then exercise the first genuinely durable mechanical operation.
    with file_transaction.campaign_lock(campaign):
        file_transaction.recover(campaign)
        profile = (campaign / "play_profile.yaml").read_text(encoding="utf-8")
        ledger = json.loads((campaign / "mechanics_state.json").read_text(encoding="utf-8"))
        before_ledger = dict(ledger)
        assert "time_tracking: coarse" in profile
        ledger["enabled"] = True
        file_transaction.commit_files(campaign, {
            "play_profile.yaml": profile.replace("time_tracking: coarse", "time_tracking: step").encode("utf-8"),
            "mechanics_state.json": (json.dumps(ledger) + "\n").encode("utf-8"),
        }, validate_applied=validate)
    assert {key: value for key, value in ledger.items() if key != "enabled"} == {
        key: value for key, value in before_ledger.items() if key != "enabled"
    }
    assert (campaign / "current_state.yaml").read_bytes() == before_state
    assert (campaign / "session_log.md").read_bytes() == before_log
    time_payload = {
        "operation_id": f"{mode}-recorded-work", "expected_continuity_revision": 1,
        "boundary": "ordinary", "cause": "The player completed a measured work interval.",
        "resume_impact": "One work interval has elapsed.",
        "changes": [{"id": "time", "kind": "mechanics", "established_delta": "One work interval elapsed.",
                     "owners": ["mechanics_state.json"], "cold_targets": []}],
        "mutations": [],
        "mechanic_operations": [{"operation_id": f"{mode}-time-one", "operation": "advance_time",
                                  "steps": 1, "unit": "work_interval"}],
    }
    result = rpg_state.commit_durable(campaign, time_payload)
    assert result["ok"] and result["continuity_revision"] == 2
    ledger = json.loads((campaign / "mechanics_state.json").read_text(encoding="utf-8"))
    assert ledger["elapsed_time"]["work_interval"] == 1
    assert rpg_state.commit_durable(campaign, time_payload)["idempotent"]
    validate()

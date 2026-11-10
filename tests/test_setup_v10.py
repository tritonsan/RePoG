"""Required decisions replace answer quotas without weakening accepted consent."""
import json
from pathlib import Path

import pytest

from test_workspace_contracts import campaign, check_state, _write_setup_profile, _setup_rules, _write_profile
import check_world_voices
import world_voices


def setup(campaign: Path, mode="quick", *, count=36, design=40, preparation=41, revision=41):
    _write_setup_profile(
        campaign, schema_version=10, session_zero_mode=mode, question_target='""',
        questions_completed=count, setup_revision=revision, design_approved_revision=design,
        preparation_approved_revision=preparation, defaults_reviewed=True,
    )
    path = campaign / "setup_profile.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("[quick_core_inference]", "[]") +
                    "deep_flow_id: rpg_deep_v8\nsession_zero_state_path: session_zero_state.json\n", encoding="utf-8")
    heading = check_state._selected_status_heading("rpg", mode, 10)
    lines = [f"## {heading}", ""] + [f"- {i}. {name}: locked" for i, name in enumerate(check_state.RPG_V10_REQUIRED_DECISIONS[mode], 1)]
    (campaign / "session_zero.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (campaign / "threads.md").write_text(
        "## Arc Compass\n- Dramatic question: Can the workshop reopen?\n"
        "- Closure conditions: The workshop's immediate future is decided.\n"
        "- Places this act can reach: Harbor and nearby workshops.\n", encoding="utf-8")
    (campaign / "boundaries.md").write_text(
        "## Good GM Behavior\n- Let routine skilled repairs succeed cleanly.\n"
        "## Bad GM Behavior\n- Do not manufacture family betrayal.\n", encoding="utf-8")


@pytest.mark.parametrize("mode", ["quick", "standard"])
@pytest.mark.parametrize("count", [9, 36])
def test_required_coverage_not_answer_quota(campaign, mode, count):
    setup(campaign, mode, count=count)
    findings = []
    check_state._check_setup_profile(campaign, findings, preflight_ready=True)
    assert not [f for f in findings if f["severity"] == "error"], findings


@pytest.mark.parametrize("damage", ["missing", "duplicate", "defaulted", "open"])
def test_required_boundary_cannot_be_omitted_or_defaulted(campaign, damage):
    setup(campaign)
    path = campaign / "session_zero.md"
    text = path.read_text(encoding="utf-8")
    line = "- 2. Agency, Authorship, And Boundaries: locked"
    replacement = {"missing": "", "duplicate": line + "\n" + line,
                   "defaulted": line.replace("locked", "defaulted"), "open": line.replace("locked", "open")}[damage]
    path.write_text(text.replace(line, replacement), encoding="utf-8")
    assert _setup_rules(campaign, preflight_ready=True) & {"setup_required_decisions_invalid", "setup_modules_open"}


@pytest.mark.parametrize(("design", "preparation", "revision", "rule"), [
    (None, 41, 41, "setup_approval_order_invalid"),
    (40, None, 41, "setup_preparation_approval_missing"),
    (40, 40, 41, "setup_approval_order_invalid"),
    (40, 41, 42, "setup_preparation_approval_stale"),
])
def test_v10_approval_still_explicit_ordered_and_current(campaign, design, preparation, revision, rule):
    setup(campaign, design=design, preparation=preparation, revision=revision)
    assert rule in _setup_rules(campaign, preflight_ready=True)


@pytest.mark.parametrize("completed", [0, 1])
def test_premise_before_depth_does_not_choose_route(campaign, completed):
    path = campaign / "setup_profile.yaml"
    template = Path(__file__).resolve().parents[1] / "campaign/setup_profile.yaml"
    path.write_text(template.read_text(encoding="utf-8").replace('experience_mode: ""', 'experience_mode: rpg'), encoding="utf-8")
    (campaign / "session_zero.md").write_text("## Intake Notes\nQuiet workshop inquiry; depth not chosen.\n", encoding="utf-8")
    assert "setup_content_before_depth" not in _setup_rules(campaign)
    path.write_text(path.read_text(encoding="utf-8").replace("questions_completed: 0", f"questions_completed: {completed}")
                    .replace("setup_revision: 0", "setup_revision: 1"), encoding="utf-8")
    assert "setup_content_before_depth" in _setup_rules(campaign)


@pytest.mark.parametrize(("key", "old", "selected"), [
    ("inventory_tracking", "abstract", "quantified"),
    ("inventory_tracking", "abstract", "encumbrance"),
    ("time_tracking", "coarse", "step"),
    ("time_tracking", "coarse", "scene"),
    ("wound_tracking", "narrative", "conditions"),
    ("travel_tracking", "abstract", "route_time"),
])
def test_accepted_tracking_needs_operable_ledger_even_without_modules(campaign, key, old, selected):
    _write_profile(campaign)
    path = campaign / "play_profile.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace(f"{key}: {old}", f"{key}: {selected}"), encoding="utf-8")
    findings = []
    check_state._check_play_profile(campaign, findings, preflight_ready=True)
    assert "mechanics_state_disabled" in {f["rule"] for f in findings}
    ledger = campaign / "mechanics_state.json"
    data = json.loads(ledger.read_text(encoding="utf-8"))
    data["enabled"] = True
    ledger.write_text(json.dumps(data), encoding="utf-8")
    findings = []
    check_state._check_play_profile(campaign, findings, preflight_ready=True)
    assert "mechanics_state_disabled" not in {f["rule"] for f in findings}


def test_dormant_voices_does_not_need_unrelated_turn_writes(campaign):
    current = campaign / "current_state.yaml"
    current.write_text(current.read_text(encoding="utf-8").replace("continuity_revision: 0", "continuity_revision: 5"), encoding="utf-8")
    assert not check_world_voices.validate_manifest(campaign)[0]
    payload = {"expected_revision": 0, "expected_continuity_revision": 5,
               "operation_id": "after-unrelated-turns", "operation_sequence": 1}
    _, candidate, *_ = world_voices._prepare(campaign, "propose", payload)
    assert candidate["_pending_continuity_revision"] == 5
    with pytest.raises(world_voices.WorldVoicesError, match="current campaign"):
        world_voices._prepare(campaign, "propose", dict(payload, expected_continuity_revision=0))


def test_dormant_voices_does_not_hide_corrupt_or_future_records(campaign):
    path = campaign / "world_voices/index.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["continuity_revision"] = 2
    data["artifacts"] = {"broken": {}}
    path.write_text(json.dumps(data), encoding="utf-8")
    rules = {f["rule"] for f in check_world_voices.validate_manifest(campaign)[0]}
    assert "world_voices_continuity_stale" in rules
    assert "world_voices_artifact_field_missing" in rules

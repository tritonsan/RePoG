from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
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


check_state = _load("workspace_check_state", PUBLIC / "tools" / "check_state.py")
check_dashboard = _load("workspace_check_dashboard", PUBLIC / "tools" / "check_dashboard.py")
roll_dice = _load("workspace_roll_dice", PUBLIC / "tools" / "roll_dice.py")
resolve_mechanic = _load("workspace_resolve_mechanic", PUBLIC / "tools" / "resolve_mechanic.py")
verify_workspace = _load("workspace_verify_workspace", PUBLIC / "tools" / "verify_workspace.py")
sys.path.insert(0, str(PUBLIC / "tools"))
visual_handoff = _load("workspace_visual_handoff", PUBLIC / "tools" / "visual_handoff.py")


@pytest.fixture()
def campaign(tmp_path: Path) -> Path:
    target = tmp_path / "campaign"
    shutil.copytree(PUBLIC / "campaign", target)
    return target


def _rules(result: dict) -> set[str]:
    return {item["rule"] for item in result["findings"]}


def _write_profile(
    campaign: Path,
    *,
    setting_lenses: str = "[]",
    play_lenses: str = "[]",
    modules: str = "[]",
    inventory: str = "abstract",
) -> None:
    (campaign / "play_profile.yaml").write_text(
        f"""schema_version: 1
profile_status: pending
source_setup_revision: 0
performance:
  turn_protocol: ""
  cold_distill_policy: ""
  validation_policy: ""
  style_review_policy: ""
  latency_notice_policy: exceptional_only
  estimate_acknowledged: false
setting_lenses: {setting_lenses}
play_lenses: {play_lenses}
lens_conflicts_resolved: []
mechanics:
  modules: {modules}
  inventory_tracking: {inventory}
  time_tracking: coarse
  travel_tracking: abstract
  wound_tracking: narrative
  dice_mode: judgment_only
narration:
  point_of_view: second
  tense: present
  camera: close
  prose_density: balanced
  response_length: dynamic
  option_prompting: natural
  challenge_density: balanced
  clue_density: balanced
  dialogue_style: plain
  pacing: dynamic
advancement:
  cadence: ""
  presentation: ""
dashboard:
  mode: off
  refresh_policy: scene_and_major_visible_change
  tiles: []
visuals:
  mode: off
  dashboard_placement: gallery_only
""",
        encoding="utf-8",
    )


def _write_setup_profile(
    campaign: Path,
    *,
    schema_version: int = 6,
    experience_mode: str = "rpg",
    session_zero_mode: str = "quick",
    status: str = "in_progress",
    question_target: int = 10,
    questions_completed: int = 0,
    setup_revision: int = 0,
    design_approved_revision: int | None = None,
    preparation_approved_revision: int | None = None,
    defaults_reviewed: bool = False,
    ready_for_play: bool = False,
    last_checkpoint: int = 0,
    activated_packs: str = "[]",
    completed_packs: str = "[]",
    defaulted_packs: str = "[]",
) -> None:
    approval_fields = ""
    if schema_version >= 6:
        design_value = "null" if design_approved_revision is None else str(design_approved_revision)
        preparation_value = "null" if preparation_approved_revision is None else str(preparation_approved_revision)
        approval_fields = (
            f"design_direction_approved_revision: {design_value}\n"
            f"preparation_approved_revision: {preparation_value}\n"
        )
    (campaign / "setup_profile.yaml").write_text(
        f"""schema_version: {schema_version}
workspace_mode: standalone
status: {status}
setup_revision: {setup_revision}
{approval_fields}experience_mode: {experience_mode}
session_zero_mode: {session_zero_mode}
question_target: {question_target}
questions_completed: {questions_completed}
defaulted_decisions: [quick_core_inference]
deferred_decisions: []
defaults_reviewed: {str(defaults_reviewed).lower()}
activated_packs: {activated_packs}
completed_packs: {completed_packs}
defaulted_packs: {defaulted_packs}
deep_extension_approved: false
last_checkpoint: {last_checkpoint}
ready_for_play: {str(ready_for_play).lower()}
""",
        encoding="utf-8",
    )


def _setup_rules(campaign: Path, *, preflight_ready: bool = False) -> set[str]:
    findings: list[dict] = []
    check_state._check_setup_profile(campaign, findings, preflight_ready=preflight_ready)
    return {item["rule"] for item in findings}


def _replace_status_block(campaign: Path, heading: str, replacement: str | None) -> None:
    path = campaign / "session_zero.md"
    text = path.read_text(encoding="utf-8")
    marker = f"## {heading}"
    start = text.index(marker)
    end = text.find("\n## ", start + len(marker))
    if end == -1:
        end = len(text)
    if replacement is None:
        updated = text[:start] + text[end + (1 if end < len(text) else 0) :]
    else:
        block = text[start:end].replace(": open", f": {replacement}")
        updated = text[:start] + block + text[end:]
    path.write_text(updated, encoding="utf-8")


def test_public_workspace_has_dependency_free_smoke_check() -> None:
    result = verify_workspace.verify_workspace(PUBLIC)
    assert result["ok"], result["findings"]
    assert {item["id"] for item in result["checks"]} == {"layout", "python", "campaign", "dashboard"}


def test_fantasy_lens_does_not_enable_mana_or_hp(campaign: Path) -> None:
    _write_profile(campaign, setting_lenses="[fantasy]")
    result = check_state.check_campaign(campaign, scope="full")
    rules = _rules(result)
    assert "setting_lens_invalid" not in rules
    assert "mechanics_state_disabled" not in rules
    profile = (campaign / "play_profile.yaml").read_text(encoding="utf-8")
    assert "modules: []" in profile
    assert "mana" not in profile.lower()
    assert "hp" not in profile.lower()


def test_mixed_fantasy_survival_lenses_are_preserved(campaign: Path) -> None:
    _write_profile(campaign, setting_lenses="[fantasy]", play_lenses="[survival]")
    rules = _rules(check_state.check_campaign(campaign, scope="full"))
    assert "setting_lens_invalid" not in rules
    assert "play_lens_invalid" not in rules


def test_strict_consumables_requires_quantified_inventory(campaign: Path) -> None:
    _write_profile(campaign, play_lenses="[survival]", modules="[strict_consumables]")
    assert "strict_consumables_tracking" in _rules(check_state.check_campaign(campaign, scope="full"))


def test_pending_research_and_blank_readiness_are_rejected(campaign: Path) -> None:
    _write_setup_profile(
        campaign,
        status="complete",
        question_target=10,
        questions_completed=10,
        setup_revision=10,
        design_approved_revision=8,
        preparation_approved_revision=10,
        defaults_reviewed=True,
        ready_for_play=True,
    )
    rules = _rules(check_state.check_campaign(campaign, scope="full"))
    assert "research_pending_at_play" in rules
    assert "ready_player_missing" in rules
    assert "ready_scene_missing" in rules
    assert "first_session_not_materialized" in rules
    assert "ready_snapshot_missing" in rules


def test_schema6_rpg_quick_requires_exactly_ten_decision_slots(campaign: Path) -> None:
    _write_setup_profile(
        campaign,
        question_target=8,
        questions_completed=8,
        setup_revision=8,
        design_approved_revision=8,
    )
    assert "setup_question_target_invalid" in _setup_rules(campaign)

    _write_setup_profile(
        campaign,
        question_target=10,
        questions_completed=8,
        setup_revision=9,
        design_approved_revision=8,
    )
    assert "setup_design_approval_stale" in _setup_rules(campaign)

    _write_setup_profile(
        campaign,
        question_target=10,
        questions_completed=8,
        setup_revision=7,
        design_approved_revision=7,
    )
    assert "setup_revision_progress_invalid" in _setup_rules(campaign)

    _write_setup_profile(
        campaign,
        question_target=10,
        questions_completed=9,
        setup_revision=9,
        design_approved_revision=9,
    )
    assert "setup_preparation_review_revision_missing" in _setup_rules(campaign)

    _write_setup_profile(
        campaign,
        question_target=10,
        questions_completed=8,
        setup_revision=8,
        design_approved_revision=8,
    )
    rules = _setup_rules(campaign)
    assert "setup_question_target_invalid" not in rules
    assert "setup_design_approval_stale" not in rules
    assert "setup_preparation_approval_missing" not in rules


def test_schema6_rpg_quick_preflight_requires_current_ordered_preparation_approval(
    campaign: Path,
) -> None:
    _write_setup_profile(
        campaign,
        questions_completed=10,
        setup_revision=10,
        design_approved_revision=8,
        preparation_approved_revision=None,
        defaults_reviewed=True,
    )
    assert "setup_preparation_approval_missing" in _setup_rules(campaign, preflight_ready=True)

    _write_setup_profile(
        campaign,
        questions_completed=10,
        setup_revision=10,
        design_approved_revision=8,
        preparation_approved_revision=9,
        defaults_reviewed=True,
    )
    assert "setup_preparation_approval_stale" in _setup_rules(campaign, preflight_ready=True)

    _write_setup_profile(
        campaign,
        questions_completed=10,
        setup_revision=10,
        design_approved_revision=8,
        preparation_approved_revision=10,
        defaults_reviewed=True,
    )
    rules = _setup_rules(campaign, preflight_ready=True)
    assert "setup_preparation_approval_stale" not in rules
    assert "setup_preparation_approval_missing" not in rules
    assert "setup_approval_order_invalid" not in rules
    assert "quick_question_target" not in rules

    _write_setup_profile(
        campaign,
        questions_completed=10,
        setup_revision=10,
        design_approved_revision=10,
        preparation_approved_revision=10,
        defaults_reviewed=True,
    )
    assert "setup_approval_order_invalid" in _setup_rules(campaign, preflight_ready=True)


def test_schema6_quick_preflight_uses_ten_slot_status_block(campaign: Path) -> None:
    _write_setup_profile(
        campaign,
        questions_completed=10,
        setup_revision=10,
        design_approved_revision=8,
        preparation_approved_revision=10,
        defaults_reviewed=True,
    )
    assert "setup_modules_open" in _setup_rules(campaign, preflight_ready=True)

    _replace_status_block(campaign, "RPG Quick Decision Slot Status", "locked")

    assert "setup_modules_open" not in _setup_rules(campaign, preflight_ready=True)


def test_schema6_quick_keeps_companion_and_legacy_budgets_compatible(campaign: Path) -> None:
    _write_setup_profile(
        campaign,
        schema_version=5,
        question_target=6,
        questions_completed=6,
        setup_revision=6,
    )
    assert "setup_question_target_invalid" not in _setup_rules(campaign)

    _write_setup_profile(
        campaign,
        schema_version=6,
        experience_mode="companion",
        question_target=7,
        questions_completed=7,
        setup_revision=7,
    )
    rules = _setup_rules(campaign)
    assert "setup_question_target_invalid" not in rules
    assert "setup_design_approval_missing" not in rules
    assert "setup_preparation_approval_missing" not in rules

    _write_setup_profile(
        campaign,
        schema_version=6,
        experience_mode="rpg",
        session_zero_mode="standard",
        question_target=17,
        questions_completed=17,
        setup_revision=17,
    )
    rules = _setup_rules(campaign)
    assert "setup_question_target_invalid" not in rules
    assert "setup_design_approval_missing" not in rules
    assert "setup_preparation_approval_missing" not in rules
    assert "setup_approval_route_invalid" not in rules

    _write_setup_profile(
        campaign,
        schema_version=7,
        experience_mode="companion",
        session_zero_mode="standard",
        question_target=15,
        questions_completed=15,
        setup_revision=15,
    )
    rules = _setup_rules(campaign)
    assert "setup_question_target_invalid" not in rules
    assert "setup_design_approval_missing" not in rules
    assert "setup_preparation_approval_missing" not in rules
    assert "setup_approval_route_invalid" not in rules


def test_schema7_rpg_standard_uses_twenty_one_to_thirty_decisions(campaign: Path) -> None:
    _write_setup_profile(
        campaign,
        schema_version=7,
        session_zero_mode="standard",
        question_target=17,
        questions_completed=17,
        setup_revision=17,
    )
    assert "setup_question_target_invalid" in _setup_rules(campaign)

    _write_setup_profile(
        campaign,
        schema_version=7,
        session_zero_mode="standard",
        question_target=21,
        questions_completed=21,
        setup_revision=21,
    )
    rules = _setup_rules(campaign)
    assert "setup_question_target_invalid" not in rules
    assert "setup_question_target" not in rules
    assert "setup_approval_route_invalid" not in rules

    _write_setup_profile(
        campaign,
        schema_version=7,
        session_zero_mode="standard",
        question_target=21,
        questions_completed=21,
        setup_revision=20,
    )
    assert "setup_revision_progress_invalid" in _setup_rules(campaign)


def test_schema7_standard_preflight_requires_ordered_current_approvals(
    campaign: Path,
) -> None:
    _replace_status_block(
        campaign,
        "RPG Standard / Deep Reciprocity Module Status",
        "locked",
    )

    _write_setup_profile(
        campaign,
        schema_version=7,
        session_zero_mode="standard",
        question_target=21,
        questions_completed=21,
        setup_revision=23,
        defaults_reviewed=True,
    )
    rules = _setup_rules(campaign, preflight_ready=True)
    assert "setup_design_approval_missing" in rules
    assert "setup_preparation_approval_missing" in rules

    _write_setup_profile(
        campaign,
        schema_version=7,
        session_zero_mode="standard",
        question_target=21,
        questions_completed=21,
        setup_revision=23,
        design_approved_revision=19,
        preparation_approved_revision=22,
        defaults_reviewed=True,
    )
    assert "setup_preparation_approval_stale" in _setup_rules(
        campaign,
        preflight_ready=True,
    )

    _write_setup_profile(
        campaign,
        schema_version=7,
        session_zero_mode="standard",
        question_target=21,
        questions_completed=21,
        setup_revision=23,
        design_approved_revision=23,
        preparation_approved_revision=23,
        defaults_reviewed=True,
    )
    assert "setup_approval_order_invalid" in _setup_rules(
        campaign,
        preflight_ready=True,
    )

    _write_setup_profile(
        campaign,
        schema_version=7,
        session_zero_mode="standard",
        question_target=21,
        questions_completed=21,
        setup_revision=23,
        design_approved_revision=19,
        preparation_approved_revision=23,
        defaults_reviewed=True,
    )
    rules = _setup_rules(campaign, preflight_ready=True)
    assert "setup_design_approval_missing" not in rules
    assert "setup_preparation_approval_missing" not in rules
    assert "setup_preparation_approval_stale" not in rules
    assert "setup_approval_order_invalid" not in rules
    assert "setup_modules_open" not in rules


def test_schema7_standard_selects_reciprocity_status_block(campaign: Path) -> None:
    _replace_status_block(
        campaign,
        "RPG Standard / Deep Reciprocity Module Status",
        "locked",
    )
    _write_setup_profile(
        campaign,
        schema_version=7,
        session_zero_mode="standard",
        question_target=21,
        questions_completed=21,
        setup_revision=23,
        design_approved_revision=19,
        preparation_approved_revision=23,
        defaults_reviewed=True,
    )
    rules = _setup_rules(campaign, preflight_ready=True)
    assert "setup_modules_open" not in rules
    assert "setup_status_block_missing" not in rules

    _replace_status_block(
        campaign,
        "RPG Standard / Deep Reciprocity Module Status",
        None,
    )
    assert "setup_status_block_missing" in _setup_rules(
        campaign,
        preflight_ready=True,
    )


def test_schema7_deep_rejects_design_approval_until_packs_resolve(
    campaign: Path,
) -> None:
    common = {
        "schema_version": 7,
        "session_zero_mode": "deep",
        "question_target": 30,
        "questions_completed": 21,
        "setup_revision": 21,
        "design_approved_revision": 21,
        "last_checkpoint": 21,
        "activated_packs": "[location_network]",
    }
    _write_setup_profile(campaign, **common)
    rules = _setup_rules(campaign)
    assert "setup_question_target_invalid" not in rules
    assert "deep_design_approval_before_pack_resolution" in rules

    _write_setup_profile(
        campaign,
        **common,
        completed_packs="[location_network]",
    )
    rules = _setup_rules(campaign)
    assert "deep_design_approval_before_pack_resolution" not in rules
    assert "setup_pack_not_activated" not in rules

    _write_setup_profile(
        campaign,
        **common,
        defaulted_packs="[location_network]",
    )
    rules = _setup_rules(campaign)
    assert "deep_design_approval_before_pack_resolution" not in rules
    assert "setup_pack_not_activated" not in rules


def test_deep_pack_completion_must_match_activation(campaign: Path) -> None:
    (campaign / "setup_profile.yaml").write_text(
        """schema_version: 3
workspace_mode: standalone
status: in_progress
setup_revision: 2
session_zero_mode: deep
question_target: 30
questions_completed: 8
activated_packs: [location_network]
completed_packs: [group]
defaulted_packs: []
deferred_decisions: []
last_checkpoint: 8
ready_for_play: false
""",
        encoding="utf-8",
    )
    rules = _rules(check_state.check_campaign(campaign, scope="full"))
    assert "deep_pack_incomplete" in rules
    assert "setup_pack_not_activated" in rules


def test_hot_scope_does_not_require_cold_storytelling_file(campaign: Path) -> None:
    (campaign / "storytelling.md").unlink()
    result = check_state.check_campaign(campaign, scope="hot")
    storytelling_findings = [
        item for item in result["findings"] if item["rule"] == "missing_file" and str(item.get("path", "")).endswith("storytelling.md")
    ]
    assert storytelling_findings == []
    assert not any(item["rule"] == "v3_file_missing" and str(item.get("path", "")).endswith("play_profile.yaml") for item in result["findings"])


def test_dice_is_reproducible_and_bounded() -> None:
    payload = {"expression": "3d8-2", "seed": "same-turn", "roll_id": "turn-7"}
    assert roll_dice.roll(payload) == roll_dice.roll(payload)
    with pytest.raises(roll_dice.DiceError):
        roll_dice.roll({"expression": "101d6", "seed": "too-many"})
    with pytest.raises(roll_dice.DiceError):
        roll_dice.roll({"expression": "2d1", "seed": "invalid-sides"})


def test_monotonic_operation_registry_survives_more_than_200_operations() -> None:
    state = {
        "schema_version": 2,
        "enabled": True,
        "revision": 0,
        "continuity_revision": 0,
        "operation_sequence": 0,
        "operation_registry": {},
        "last_operation": None,
        "actors": {},
        "clocks": {},
        "elapsed_time": {},
    }
    first_payload = None
    for sequence in range(1, 206):
        payload = {
            "operation_id": f"turn-{sequence}",
            "operation_sequence": sequence,
            "expected_revision": sequence - 1,
            "expected_continuity_revision": sequence - 1,
            "resulting_continuity_revision": sequence,
            "operation": "advance_time",
            "steps": 1,
            "unit": "turn",
        }
        first_payload = first_payload or payload.copy()
        state, outcome = resolve_mechanic.apply_operation(state, payload)
        assert outcome["duplicate"] is False

    assert len(state["operation_registry"]) == 205
    elapsed_before = dict(state["elapsed_time"])
    state_after_retry, retry = resolve_mechanic.apply_operation(state, first_payload)
    assert retry["duplicate"] is True
    assert state_after_retry["elapsed_time"] == elapsed_before

    changed_retry = dict(first_payload, steps=2)
    with pytest.raises(resolve_mechanic.MechanicError):
        resolve_mechanic.apply_operation(state, changed_retry)


def test_mechanics_reject_numeric_strings() -> None:
    state = {
        "schema_version": 2,
        "enabled": True,
        "revision": 0,
        "continuity_revision": 0,
        "operation_sequence": 0,
        "operation_registry": {},
        "last_operation": None,
        "actors": {},
        "clocks": {},
        "elapsed_time": {},
    }
    payload = {
        "operation_id": "bad-sequence",
        "operation_sequence": "1",
        "expected_revision": 0,
        "expected_continuity_revision": 0,
        "resulting_continuity_revision": 1,
        "operation": "advance_time",
        "steps": 1,
        "unit": "turn",
    }
    with pytest.raises(resolve_mechanic.MechanicError):
        resolve_mechanic.apply_operation(state, payload)


def test_pending_visual_requires_a_return_anchor(campaign: Path) -> None:
    visual_state = {
        "schema_version": 1,
        "revision": 1,
        "pending": {
            "transaction_id": "visual-1",
            "target_kind": "character",
            "target_id": "hero",
            "interrupted_context": "play",
            "last_meaningful_beat": "The door opens.",
            "return_anchor": "",
            "next_step": "Return to the open door.",
            "dashboard_placement_requested": False,
        },
        "history": [],
    }
    (campaign / "visual_state.json").write_text(json.dumps(visual_state), encoding="utf-8")
    assert "visual_return_anchor_incomplete" in _rules(check_state.check_campaign(campaign, scope="full"))


def test_dashboard_v3_blank_state_is_honest_and_revision_aware(tmp_path: Path) -> None:
    source = PUBLIC / "campaign" / "dashboard" / "dashboard_state.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    assert [tile["type"] for tile in data["tiles"]] == ["setup_progress"]
    assert check_dashboard.check_dashboard_data(data, source, require_assets=False)["ok"]

    target = tmp_path / "dashboard_state.json"
    target.write_text(json.dumps(data), encoding="utf-8")
    stale = check_dashboard.check_dashboard(target, expected_revision=1, require_assets=False)
    assert "dashboard_revision_stale" in _rules(stale)


def _begin_and_attach_visual(campaign: Path, transaction_id: str = "visual-test") -> Path:
    visual_handoff.begin(
        campaign,
        {
            "transaction_id": transaction_id,
            "target": "Player portrait",
            "interrupted_context": "play",
            "last_meaningful_beat": "The harbor bell rings.",
            "return_anchor": "Harbor scene after the bell",
            "next_step": "Return control to the player.",
            "dashboard_placement_requested": True,
        },
    )
    draft = campaign / "visuals" / "_drafts" / f"{transaction_id}.png"
    draft.write_bytes(b"not-a-rendered-png-but-sufficient-for-file-transaction-tests")
    visual_handoff.attach(
        campaign,
        {"transaction_id": transaction_id, "draft_path": f"visuals/_drafts/{transaction_id}.png"},
    )
    return draft


def test_visual_accept_writes_campaign_and_dashboard_assets_atomically(campaign: Path) -> None:
    _begin_and_attach_visual(campaign)
    result = visual_handoff.accept(
        campaign,
        {
            "transaction_id": "visual-test",
            "destination": "assets/characters/hero-v1.png",
            "campaign_destination": "visuals/characters/hero-v1.png",
            "name": "Hero",
            "visual_type": "character",
            "linked_element": "player.md",
            "canon_notes": "A red travel coat.",
        },
    )
    assert result["asset"] == "visuals/characters/hero-v1.png"
    assert result["dashboard_asset"] == "dashboard/assets/characters/hero-v1.png"
    assert (campaign / result["asset"]).is_file()
    assert (campaign / result["dashboard_asset"]).is_file()
    state = json.loads((campaign / "visual_state.json").read_text(encoding="utf-8"))
    assert state["pending"] is None
    dashboard = json.loads((campaign / "dashboard" / "dashboard_state.json").read_text(encoding="utf-8"))
    assert any(tile["type"] == "gallery" for tile in dashboard["tiles"])


def test_visual_accept_failure_rolls_back_and_preserves_anchor(
    campaign: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _begin_and_attach_visual(campaign, "visual-rollback")
    real_atomic = visual_handoff._atomic_bytes
    calls = 0

    def fail_during_commit(path: Path, payload: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("injected gallery write failure")
        real_atomic(path, payload)

    monkeypatch.setattr(visual_handoff, "_atomic_bytes", fail_during_commit)
    with pytest.raises(visual_handoff.VisualError):
        visual_handoff.accept(
            campaign,
            {
                "transaction_id": "visual-rollback",
                "destination": "assets/characters/rollback.png",
                "campaign_destination": "visuals/characters/rollback.png",
                "name": "Rollback Hero",
                "visual_type": "character",
            },
        )
    assert not (campaign / "dashboard" / "assets" / "characters" / "rollback.png").exists()
    assert not (campaign / "visuals" / "characters" / "rollback.png").exists()
    state = json.loads((campaign / "visual_state.json").read_text(encoding="utf-8"))
    assert state["pending"]["return_anchor"] == "Harbor scene after the bell"


def test_dashboard_rejects_campaign_protected_name(campaign: Path) -> None:
    knowledge = (campaign / "knowledge_boundaries.md").read_text(encoding="utf-8")
    knowledge = knowledge.replace(
        "### Protected Name",
        "### Night Queen\n\n- Status: GM-only\n\n### Protected Name",
        1,
    )
    (campaign / "knowledge_boundaries.md").write_text(knowledge, encoding="utf-8")
    dashboard_path = campaign / "dashboard" / "dashboard_state.json"
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    dashboard["campaign"]["pitch"] = "The Night Queen is waiting."
    dashboard_path.write_text(json.dumps(dashboard), encoding="utf-8")
    result = check_dashboard.check_dashboard(dashboard_path, campaign_path=campaign)
    assert "dashboard_protected_name" in _rules(result)


def test_dashboard_polling_and_accessibility_contracts_remain_present() -> None:
    html = (PUBLIC / "campaign" / "dashboard" / "index.html").read_text(encoding="utf-8")
    unchanged_guard = re.search(
        r"sourceRevision\s*===\s*appliedSourceRevision.*?clearTimeout\(refreshTimer\);\s*"
        r"refreshTimer\s*=\s*setTimeout\(loadState,\s*interval\)",
        html,
        re.DOTALL,
    )
    assert unchanged_guard, "An unchanged fetch must schedule the next poll."
    assert "@media (prefers-reduced-motion: reduce)" in html
    assert 'role="dialog"' in html and 'aria-modal="true"' in html
    assert "lightboxReturnFocus.focus()" in html
    assert "Map locations and routes (text alternative)" in html


def test_blank_markdown_field_does_not_absorb_the_next_line() -> None:
    # A newline-tolerant value capture made an empty field read as populated,
    # which silently satisfied completion gates that only test for emptiness.
    text = "- Dramatic question:\n- Active pressures: pursuit\n"
    assert check_state._markdown_field(text, "Dramatic question") == ""
    assert check_state._markdown_field(text, "Active pressures") == "pursuit"


def test_blank_arc_compass_blocks_campaign_architecture_completion(campaign: Path) -> None:
    _write_setup_profile(
        campaign,
        activated_packs="[campaign_architecture]",
        completed_packs="[campaign_architecture]",
    )
    # The shipped Arc Compass has every field blank.
    assert "deep_pack_output_missing" in _setup_rules(campaign)

    threads = campaign / "threads.md"
    threads.write_text(
        threads.read_text(encoding="utf-8").replace(
            "- Dramatic question:",
            "- Dramatic question: Does keeping the promise preserve him or hollow him out?",
        ),
        encoding="utf-8",
    )
    assert "deep_pack_output_missing" not in _setup_rules(campaign)


def test_ready_rpg_play_requires_an_arc_compass(campaign: Path) -> None:
    # next_act_prep.md frames every act after the first and first_session.md covers
    # only the opening scene, so readiness is the one gate that can require the
    # first act's compass. Without a closure condition nothing defines when an act
    # ends, which leaves the accepted progression unreachable.
    _write_setup_profile(campaign, ready_for_play=True)
    assert "arc_compass_incomplete" in _setup_rules(campaign)

    threads = campaign / "threads.md"
    text = threads.read_text(encoding="utf-8")
    text = text.replace(
        "- Dramatic question:",
        "- Dramatic question: Does keeping the promise preserve him or hollow him out?",
    )
    text = text.replace(
        "- Closure conditions:",
        "- Closure conditions: The harbour's ownership is settled in either direction.",
    )
    text = text.replace(
        "- Places this act can reach:",
        "- Places this act can reach: Rope Harbour, the tide flats, the outer anchorage",
    )
    threads.write_text(text, encoding="utf-8")
    assert "arc_compass_incomplete" not in _setup_rules(campaign)


def test_ready_rpg_play_requires_gm_behavior_records(campaign: Path) -> None:
    # These two records had no owning module and shipped empty, so the narration
    # instruction the GM actually held was whatever it happened to remember. Both
    # sections carry their own guidance text, so the gate looks for a filled list
    # item rather than for any content at all.
    _write_setup_profile(campaign, ready_for_play=True)
    assert "gm_behavior_record_missing" in _setup_rules(campaign)

    boundaries = campaign / "boundaries.md"
    text = boundaries.read_text(encoding="utf-8")
    text = text.replace(
        "## Good GM Behavior\n",
        "## Good GM Behavior\n\n- Returns control at a concrete moment.\n",
        1,
    )
    text = text.replace(
        "## Bad GM Behavior\n",
        "## Bad GM Behavior\n\n- Every NPC speaking in the same register.\n",
        1,
    )
    boundaries.write_text(text, encoding="utf-8")
    assert "gm_behavior_record_missing" not in _setup_rules(campaign)

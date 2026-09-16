"""Changed owners must be structurally valid before any game state is written."""

from pathlib import Path

import pytest

from test_rpg_state import campaign, rpg_state  # shared realistic transaction fixture


def change(old: str, new: str) -> dict:
    return {
        "operation_id": "scene-change-001",
        "expected_continuity_revision": 0,
        "boundary": "ordinary",
        "cause": "The player inspected the witness's route.",
        "resume_impact": "The next question remains with the player.",
        "changes": [{
            "id": "scene-update", "kind": "scene",
            "established_delta": "The current scene changed.",
            "owners": ["current_state.yaml"], "cold_targets": [],
        }],
        "mutations": [{"path": "current_state.yaml", "exact_replacements": [{"old": old, "new": new}]}],
    }


@pytest.mark.parametrize(("old", "new", "rule"), [
    ("  mode: focused", "  mode: not_a_scene_mode", "scene_mode_invalid"),
    ("  mode: focused", "  mode: focused\n  mode: crisis", "state_key_duplicate"),
    ("  resume_anchor: The witness waits for the next question.", "  resume_anchor: \"\"", "ready_scene_frame_incomplete"),
    ("inventory: []", "inventory: unavailable", "state_list_invalid"),
    ("  pending_consequences: []", "  pending_consequences: false", "state_list_invalid"),
    ("  returned_control_at: The witness waits.", "  other_field: The witness waits.", "causal_beat_shape_invalid"),
])
def test_invalid_scene_is_rejected_without_owner_revision_or_log_changes(campaign: Path, old: str, new: str, rule: str):
    before = {path: path.read_bytes() for path in campaign.rglob("*") if path.is_file()}
    with pytest.raises(rpg_state.RPGStateError, match=rule) as error:
        rpg_state.commit_durable(campaign, change(old, new))
    assert error.value.category == "candidate_invalid"
    assert all(path.read_bytes() == payload for path, payload in before.items())


def test_valid_scene_uses_only_candidate_checks_and_remains_idempotent(campaign: Path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("An ordinary commit must not scan the full campaign.")
    monkeypatch.setattr(rpg_state._candidate_checker(), "check_campaign", forbidden)
    payload = change("  mode: focused", "  mode: breather")
    result = rpg_state.commit_durable(campaign, payload)
    assert result["ok"] and result["narration_allowed"]
    assert result["continuity_revision"] == 1
    assert rpg_state.commit_durable(campaign, payload)["idempotent"]


def test_block_scalar_prose_is_not_interpreted_as_duplicate_mapping_keys(campaign: Path):
    payload = change(
        "  summary: The interview is unresolved.",
        "  summary: |\n    Witness: uncertain.\n    Witness: asks for time.",
    )
    assert rpg_state.commit_durable(campaign, payload)["ok"]


def test_separate_inventory_objects_can_repeat_mapping_keys(campaign: Path):
    payload = change("inventory: []", "inventory:\n  - name: key\n    quantity: 1\n  - name: coin\n    quantity: 2")
    assert rpg_state.commit_durable(campaign, payload)["ok"]


def test_duplicate_within_one_inventory_object_is_rejected(campaign: Path):
    payload = change("inventory: []", "inventory:\n  - name: key\n    quantity: 1\n    quantity: 2")
    with pytest.raises(rpg_state.RPGStateError, match="state_key_duplicate"):
        rpg_state.commit_durable(campaign, payload)

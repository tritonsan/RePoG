"""Portable schema conformance against real compiled and resolved seat data."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from agent_seat import AgentSeatError, initial_state, open_beat, get_next_turn, submit_turn, resolve_turn
from compile_agent_brief import BriefError, compile_pack, compile_state_brief, import_intent, export_resolution
from test_agent_seat import open_request, turn_request


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "contracts" / "agent-seat" / "v1"


def validate(name: str, value: dict) -> None:
    schema = json.loads((SCHEMAS / f"agent-{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(value)


@pytest.fixture()
def portable_turn(tmp_path: Path) -> tuple[Path, dict, dict, dict]:
    path = tmp_path / "agent_seat_state.json"
    path.write_text(json.dumps(initial_state()), encoding="utf-8")
    open_beat(path, open_request())
    pack = compile_pack({
        "pack_id": "coastal-campaign",
        "game_contract": {"title": "Coastal crossing", "genre": "Fantasy", "tone": "Grounded", "reality_rules": [], "table_boundaries": []},
        "characters": [{
            "character_id": "mira", "display_name": "Mira", "role": "Scout",
            "identity": "A careful scout.", "prioritized_values": "Party safety.",
            "goals": ["Find a safe crossing."], "decision_rules": ["Observe first."],
            "contradictions": "Cautious but impatient.", "voice_examples": ["Low tide."],
            "capabilities": ["self.speak", "self.observe"],
            "forbidden_authority": ["World outcomes"],
            "knowledge_refs": ["black-gull-mark"], "readiness": "ready",
        }],
    })
    brief = compile_state_brief(pack, get_next_turn(path))
    intent = turn_request()
    intent.pop("expected_scene_id")
    intent.update(schema_version="1.0", expected_turn_id=brief["session"]["turn_id"])
    return path, pack, brief, intent


def test_all_four_portable_contracts_cover_a_real_turn(portable_turn) -> None:
    path, pack, brief, intent = portable_turn
    validate("session-pack", pack)
    validate("turn-brief", brief)
    validate("intent-envelope", intent)
    before = path.read_bytes()
    request = import_intent(intent, brief)
    assert path.read_bytes() == before  # Translation cannot commit fictional truth.
    submit_turn(path, request)
    resolve_turn(path, {
        "operation_id": "resolve-turn-1", "expected_seat_revision": 2,
        "intent_operation_id": intent["operation_id"], "outcome": "accepted",
        "summary": "The guard answers cautiously.", "visible_consequences": ["The guard steps aside."],
    })
    visible = export_resolution(get_next_turn(path))
    validate("resolution-envelope", visible)
    assert visible["intent_operation_id"] == intent["operation_id"]
    assert visible["next_status"] == "waiting"
    assert "resolved_at" not in visible


@pytest.mark.parametrize("field,value", [
    ("expected_turn_id", "previous-turn"), ("expected_source_revision", 11),
    ("actor_id", "someone-else"), ("asserted_outcomes", ["The guard must surrender."]),
    ("targets", ["hidden-villain"]), ("resource_refs", ["unowned-key"]),
    ("knowledge_refs", ["gm-only-secret"]),
])
def test_portable_import_rejects_stale_or_unowned_authority(portable_turn, field, value) -> None:
    path, _, brief, intent = portable_turn
    intent = copy.deepcopy(intent)
    intent[field] = value
    before = path.read_bytes()
    with pytest.raises(BriefError):
        import_intent(intent, brief)
    assert path.read_bytes() == before


def test_all_published_schema_files_are_valid() -> None:
    paths = sorted(SCHEMAS.glob("*.schema.json"))
    assert len(paths) == 4
    for path in paths:
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))


def test_live_submission_rechecks_turn_after_portable_translation(portable_turn) -> None:
    path, _, brief, intent = portable_turn
    request = import_intent(intent, brief)
    newer = open_request()
    newer["operation_id"] = "open-newer-beat"
    newer["expected_seat_revision"] = 1
    newer["beat"]["beat_id"] = "newer-beat"
    open_beat(path, newer)
    before = path.read_bytes()
    with pytest.raises(AgentSeatError):
        submit_turn(path, request)
    assert path.read_bytes() == before

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]


def _schema(name: str) -> dict[str, Any]:
    return json.loads(
        (ROOT / "contracts" / "agent-seat" / "v1" / name).read_text(
            encoding="utf-8"
        )
    )


def validate_contract(value: dict[str, Any], name: str) -> None:
    errors = sorted(
        Draft202012Validator(_schema(name)).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise RuntimeError(f"hosted_contract_invalid:{name}:{errors[0].json_path}")


def validate_bootstrap(value: dict[str, Any]) -> None:
    if set(value) != {"manifest", "initial_turn"}:
        raise RuntimeError("golden_bootstrap_invalid")
    for payload, name in ((value["manifest"], "agent-session-pack.schema.json"), (value["initial_turn"], "agent-turn-brief.schema.json")):
        try:
            validate_contract(payload, name)
        except RuntimeError as exc:
            raise RuntimeError("golden_bootstrap_invalid") from exc
    characters = value["manifest"].get("characters", [])
    seat = value["initial_turn"].get("seat", {})
    if not any(character.get("character_id") == seat.get("character_id") and character.get("readiness") == "ready" for character in characters):
        raise RuntimeError("golden_agent_seat_not_ready")


def validate_resolution(state: dict[str, Any], value: dict[str, Any]) -> None:
    next_turn = value.get("next_turn")
    if not isinstance(next_turn, dict):
        raise RuntimeError("next_turn_invalid")
    validate_contract(next_turn, "agent-turn-brief.schema.json")
    current_session = state["turn_brief"]["session"]
    next_session = next_turn["session"]
    if next_session["session_id"] != current_session["session_id"]:
        raise RuntimeError("next_turn_session_changed")
    if int(next_session["turn_number"]) != int(current_session["turn_number"]) + 1:
        raise RuntimeError("next_turn_number_invalid")
    if int(next_session["revision"]) != int(current_session["revision"]) + 1:
        raise RuntimeError("next_turn_revision_invalid")
    if next_session["turn_id"] == current_session["turn_id"]:
        raise RuntimeError("next_turn_id_reused")
    if next_turn["seat"]["character_id"] != state["turn_brief"]["seat"]["character_id"]:
        raise RuntimeError("next_turn_character_changed")

"""Compile and validate bounded RPG Agent Seat context.

The compiler is read-only. It accepts explicit, already-authorized projections
and never searches campaign files for additional facts. Roster validation may
read only referenced character notes below the supplied campaign directory.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
ROLE_VALUES = {"party_companion", "party_member", "persistent_ally", "guest"}
CAPABILITY_VALUES = {
    "self.speak",
    "self.move",
    "self.use_owned_resource",
    "self.personal_commitment",
    "self.observe",
    "self.recall",
}
KNOWLEDGE_STATUSES = {"observed", "heard", "inferred", "suspected", "disproven", "misremembered"}
READY_FIELDS = (
    "Candidate role",
    "Prioritized values",
    "Short-term goal",
    "Long-term goal",
    "Decision rules under pressure",
    "Contradictions and recurring mistakes",
    "Self-authority",
    "Forbidden authority",
    "Knowledge-boundary refs",
    "Voice calibration examples",
    "Stop/replan conditions",
    "Readiness status",
    "Prepared at continuity revision",
)
LIST_LIMITS = {
    "perceivable_facts": 12,
    "relevant_knowledge": 12,
    "relevant_memories": 12,
    "affordances": 8,
    "voice_examples": 3,
    "decision_rules": 8,
    "authority": 8,
    "forbidden_authority": 8,
    "capabilities": 8,
    "knowledge_refs": 32,
    "reality_rules": 24,
    "table_boundaries": 24,
    "stop_conditions": 12,
    "goals": 8,
}


class BriefError(ValueError):
    pass


def _id(value: Any, name: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise BriefError(f"{name} must be a lowercase stable identifier")
    return value


def _text(value: Any, name: str, maximum: int = 1200) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BriefError(f"{name} must be non-empty text")
    clean = value.strip()
    if len(clean) > maximum:
        raise BriefError(f"{name} exceeds {maximum} characters")
    return clean


def _items(source: dict[str, Any], name: str, *, item_maximum: int = 500) -> list[str]:
    value = source.get(name, [])
    limit = LIST_LIMITS[name]
    if not isinstance(value, list) or len(value) > limit:
        raise BriefError(f"{name} must contain at most {limit} items")
    return [_text(item, f"{name}[{index}]", item_maximum) for index, item in enumerate(value)]


def _knowledge_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > 32:
        raise BriefError("knowledge_index must contain at most 32 items")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise BriefError(f"knowledge_index[{index}] must be an object")
        fact_id = _id(item.get("fact_id"), f"knowledge_index[{index}].fact_id")
        if fact_id in seen:
            raise BriefError(f"knowledge_index[{index}].fact_id is duplicate")
        seen.add(fact_id)
        status = item.get("status")
        if status not in KNOWLEDGE_STATUSES:
            raise BriefError(f"knowledge_index[{index}].status is invalid")
        confidence = item.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            raise BriefError(f"knowledge_index[{index}].confidence must be between 0 and 1")
        learned = item.get("learned_at_revision")
        if not isinstance(learned, int) or isinstance(learned, bool) or learned < 0:
            raise BriefError(f"knowledge_index[{index}].learned_at_revision is invalid")
        result.append(
            {
                "fact_id": fact_id,
                "text": _text(item.get("text"), f"knowledge_index[{index}].text", 500),
                "status": status,
                "source": _text(item.get("source"), f"knowledge_index[{index}].source", 180),
                "confidence": float(confidence),
                "learned_at_revision": learned,
                "last_confirmed_revision": int(item.get("last_confirmed_revision", learned)),
            }
        )
    return result


def validate_pack(pack: Any) -> dict[str, Any]:
    if not isinstance(pack, dict):
        raise BriefError("pack must be an object")
    errors: list[str] = []
    if pack.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    try:
        _id(pack.get("pack_id"), "pack_id")
    except BriefError as exc:
        errors.append(str(exc))
    game = pack.get("game_contract")
    if not isinstance(game, dict):
        errors.append("game_contract must be an object")
    else:
        for name in ("title", "genre", "tone"):
            try:
                _text(game.get(name), f"game_contract.{name}", 300)
            except BriefError as exc:
                errors.append(str(exc))
        for name in ("reality_rules", "table_boundaries"):
            try:
                _items(game, name, item_maximum=500)
            except BriefError as exc:
                errors.append(str(exc))
    characters = pack.get("characters")
    if not isinstance(characters, list) or not 1 <= len(characters) <= 16:
        errors.append("characters must contain between 1 and 16 entries")
        characters = []
    seen: set[str] = set()
    ready_count = 0
    for index, character in enumerate(characters):
        prefix = f"characters[{index}]"
        if not isinstance(character, dict):
            errors.append(f"{prefix} must be an object")
            continue
        try:
            character_id = _id(character.get("character_id"), f"{prefix}.character_id")
            if character_id in seen:
                errors.append(f"{prefix}.character_id is duplicate")
            seen.add(character_id)
        except BriefError as exc:
            errors.append(str(exc))
        for name in ("display_name", "role", "identity", "prioritized_values", "contradictions"):
            try:
                _text(character.get(name), f"{prefix}.{name}", 600)
            except BriefError as exc:
                errors.append(str(exc))
        capabilities = character.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities or len(capabilities) != len(set(capabilities)) or not set(capabilities) <= CAPABILITY_VALUES:
            errors.append(f"{prefix}.capabilities contains unsupported or duplicate values")
        if character.get("readiness") not in {"ready", "paused"}:
            errors.append(f"{prefix}.readiness is invalid")
        elif character.get("readiness") == "ready":
            ready_count += 1
    policy = pack.get("session_policy")
    if not isinstance(policy, dict):
        errors.append("session_policy must be an object")
    else:
        if policy.get("max_active_seats") != 1:
            errors.append("session_policy.max_active_seats must be 1")
        if policy.get("run_policy") != "continue_until_pause_or_complete":
            errors.append("session_policy.run_policy is invalid")
        if policy.get("ordinary_turn_approval") != "not_required":
            errors.append("session_policy.ordinary_turn_approval is invalid")
    return {"ok": not errors, "error_count": len(errors), "ready_count": ready_count, "errors": errors}


def compile_pack(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise BriefError("request must be an object")
    game = request.get("game_contract")
    characters = request.get("characters")
    if not isinstance(game, dict) or not isinstance(characters, list):
        raise BriefError("game_contract and characters are required")
    normalized_characters: list[dict[str, Any]] = []
    for index, character in enumerate(characters):
        if not isinstance(character, dict):
            raise BriefError(f"characters[{index}] must be an object")
        capabilities = character.get("capabilities", [])
        if not isinstance(capabilities, list):
            raise BriefError(f"characters[{index}].capabilities must be a list")
        normalized_characters.append(
            {
                "character_id": _id(character.get("character_id"), f"characters[{index}].character_id"),
                "display_name": _text(character.get("display_name"), f"characters[{index}].display_name", 100),
                "role": _text(character.get("role"), f"characters[{index}].role", 120),
                "identity": _text(character.get("identity"), f"characters[{index}].identity", 600),
                "prioritized_values": _text(character.get("prioritized_values"), f"characters[{index}].prioritized_values", 600),
                "goals": _items(character, "goals", item_maximum=500),
                "decision_rules": _items(character, "decision_rules", item_maximum=300),
                "contradictions": _text(character.get("contradictions"), f"characters[{index}].contradictions", 600),
                "voice_examples": _items(character, "voice_examples", item_maximum=300),
                "capabilities": [_text(item, f"characters[{index}].capabilities", 80) for item in capabilities],
                "forbidden_authority": _items(character, "forbidden_authority", item_maximum=300),
                "knowledge_refs": [_id(item, f"characters[{index}].knowledge_refs") for item in character.get("knowledge_refs", [])],
                "readiness": character.get("readiness", "ready"),
            }
        )
    pack = {
        "schema_version": "1.0",
        "pack_id": _id(request.get("pack_id"), "pack_id"),
        "game_contract": {
            "title": _text(game.get("title"), "game_contract.title", 300),
            "genre": _text(game.get("genre"), "game_contract.genre", 300),
            "tone": _text(game.get("tone"), "game_contract.tone", 300),
            "reality_rules": _items(game, "reality_rules"),
            "table_boundaries": _items(game, "table_boundaries"),
        },
        "characters": normalized_characters,
        "session_policy": {
            "max_active_seats": 1,
            "run_policy": "continue_until_pause_or_complete",
            "ordinary_turn_approval": "not_required",
            "stop_conditions": _items(
                {"stop_conditions": request.get("stop_conditions", ["session_paused", "session_complete", "clarification_required", "repeated_authority_rejection"])},
                "stop_conditions",
                item_maximum=160,
            ),
        },
    }
    result = validate_pack(pack)
    if not result["ok"]:
        raise BriefError("; ".join(result["errors"]))
    return pack


def compile_brief(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise BriefError("request must be an object")
    session = request.get("session")
    seat = request.get("seat")
    scene = request.get("scene")
    character = request.get("character")
    if not all(isinstance(item, dict) for item in (session, seat, scene, character)):
        raise BriefError("session, seat, scene, and character must be objects")
    revision = session.get("revision")
    turn_number = session.get("turn_number")
    if not isinstance(revision, int) or revision < 0 or not isinstance(turn_number, int) or turn_number < 1:
        raise BriefError("session revision and turn_number are invalid")
    return {
        "schema_version": "1.0",
        "session": {
            "session_id": _id(session.get("session_id"), "session.session_id"),
            "turn_id": _id(session.get("turn_id"), "session.turn_id"),
            "turn_number": turn_number,
            "revision": revision,
        },
        "scene": {
            "scene_id": _id(scene.get("scene_id"), "scene.scene_id"),
            "summary": _text(scene.get("summary"), "scene.summary"),
            "pressure": _text(scene.get("pressure"), "scene.pressure", 600),
            "perceivable_facts": _items(scene, "perceivable_facts"),
            "affordances": _items(scene, "affordances", item_maximum=240),
        },
        "seat": {
            "seat_id": _id(seat.get("seat_id"), "seat.seat_id"),
            "character_id": _id(seat.get("character_id", seat.get("seat_id")), "seat.character_id"),
            "character_ref": _text(seat.get("character_ref"), "seat.character_ref", 180),
            "role": _text(seat.get("role"), "seat.role", 120),
            "authority": _items(seat, "authority", item_maximum=240),
            "forbidden_authority": _items(seat, "forbidden_authority", item_maximum=300),
            "capabilities": [_text(item, "seat.capabilities", 80) for item in seat.get("capabilities", ["self.speak", "self.move", "self.observe", "self.recall"])],
        },
        "play_contract": {
            "identity": _text(character.get("identity"), "character.identity", 600),
            "prioritized_values": _text(character.get("prioritized_values"), "character.prioritized_values", 600),
            "short_term_goal": _text(character.get("short_term_goal"), "character.short_term_goal", 500),
            "long_term_goal": _text(character.get("long_term_goal"), "character.long_term_goal", 500),
            "contradictions": _text(character.get("contradictions"), "character.contradictions", 600),
            "decision_rules": _items(character, "decision_rules", item_maximum=300),
            "voice_examples": _items(character, "voice_examples", item_maximum=300),
        },
        "epistemic_projection": {
            "relevant_knowledge": _items(request, "relevant_knowledge"),
            "relevant_memories": _items(request, "relevant_memories"),
            "knowledge_index": _knowledge_items(request.get("knowledge_index", [])),
        },
        "continuity": {
            "last_action": str(request.get("last_action", "")).strip()[:600],
            "last_visible_result": str(request.get("last_visible_result", "")).strip()[:900],
            "current_condition": str(request.get("current_condition", "")).strip()[:500],
            "unresolved_personal_business": str(request.get("unresolved_personal_business", "")).strip()[:600],
        },
    }


def validate_roster(campaign: Path) -> dict[str, Any]:
    root = campaign.resolve()
    roster_path = root / "agent_roster.json"
    try:
        roster = json.loads(roster_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BriefError(f"cannot read agent_roster.json: {exc}") from exc
    errors: list[str] = []
    if roster.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    if roster.get("mode") not in {"off", "on_demand"}:
        errors.append("mode must be off or on_demand")
    if roster.get("max_active_seats") != 1:
        errors.append("max_active_seats must be 1")
    characters = roster.get("characters")
    if not isinstance(characters, list):
        errors.append("characters must be a list")
        characters = []
    ready_count = 0
    seen: set[str] = set()
    for index, entry in enumerate(characters):
        prefix = f"characters[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        ref = entry.get("character_ref")
        status = entry.get("status")
        role = entry.get("role")
        if not isinstance(ref, str) or not ref.startswith("characters/") or Path(ref).suffix != ".md":
            errors.append(f"{prefix}.character_ref must reference characters/*.md")
            continue
        target = (root / ref).resolve()
        target_key = str(target)
        if root not in target.parents or target_key in seen:
            errors.append(f"{prefix}.character_ref is duplicate or outside campaign")
            continue
        seen.add(target_key)
        if status not in {"candidate", "preparing", "ready", "paused", "revoked"}:
            errors.append(f"{prefix}.status is invalid")
        if status == "ready":
            ready_count += 1
            if role not in ROLE_VALUES:
                errors.append(f"{prefix}.role is not party-capable")
            try:
                note = target.read_text(encoding="utf-8")
            except OSError as exc:
                errors.append(f"{prefix} cannot read character note: {exc}")
                continue
            if not re.search(r"(?m)^Tier:\s*T3\s*$", note):
                errors.append(f"{prefix} ready character must be T3")
            if "## Agent Playability Card" not in note:
                errors.append(f"{prefix} lacks Agent Playability Card")
            for label in READY_FIELDS:
                match = re.search(rf"(?m)^- {re.escape(label)}:\s*(.+)$", note)
                if not match or not match.group(1).strip():
                    errors.append(f"{prefix} missing {label}")
    return {"ok": not errors, "error_count": len(errors), "ready_count": ready_count, "errors": errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    compile_parser = sub.add_parser("compile")
    compile_parser.add_argument("--input-json", required=True)
    pack_parser = sub.add_parser("compile-pack")
    pack_parser.add_argument("--input-json", required=True)
    validate_pack_parser = sub.add_parser("validate-pack")
    validate_pack_parser.add_argument("--input-json", required=True)
    roster_parser = sub.add_parser("validate-roster")
    roster_parser.add_argument("campaign")
    args = parser.parse_args(argv)
    try:
        if args.command == "compile":
            result = {"ok": True, "brief": compile_brief(json.loads(args.input_json))}
        elif args.command == "compile-pack":
            result = {"ok": True, "pack": compile_pack(json.loads(args.input_json))}
        elif args.command == "validate-pack":
            result = validate_pack(json.loads(args.input_json))
        else:
            result = validate_roster(Path(args.campaign))
    except (BriefError, json.JSONDecodeError) as exc:
        result = {"ok": False, "failure_category": "agent_brief_invalid", "failure_reason": str(exc)}
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())

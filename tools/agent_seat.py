"""Manage the bounded Agent Seat projection and turn-intent queue.

This helper owns operational participant state only.  It never mutates RPG
campaign truth, resolves an action, or invents narration.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


SCHEMA_VERSION = "2.0"
LEGACY_SCHEMA_VERSION = "1.0"
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
PROJECTION_LISTS = (
    "perceivable_facts",
    "self_knowledge",
    "known_facts",
    "party_public_facts",
    "allowed_actions",
)
CAPABILITY_VALUES = {
    "self.speak",
    "self.move",
    "self.use_owned_resource",
    "self.personal_commitment",
    "self.observe",
    "self.recall",
}
ACTION_CAPABILITIES = {
    "speak": "self.speak",
    "move": "self.move",
    "use_resource": "self.use_owned_resource",
    "commit": "self.personal_commitment",
    "observe": "self.observe",
    "recall": "self.recall",
    "act": "self.move",
    "social_test": "self.speak",
    "investigate": "self.observe",
    "assist": "self.move",
}
MAX_LEDGER = 64
MAX_TURN_HISTORY = 32


class AgentSeatError(Exception):
    def __init__(self, category: str, message: str, *, exit_code: int = 2) -> None:
        super().__init__(message)
        self.category = category
        self.exit_code = exit_code


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise AgentSeatError("input_invalid", f"{name} must be a lowercase stable identifier.")
    return value


def _text(value: Any, name: str, *, maximum: int, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise AgentSeatError("input_invalid", f"{name} must be text.")
    clean = value.strip()
    if not clean and not allow_empty:
        raise AgentSeatError("input_invalid", f"{name} must not be empty.")
    if len(clean) > maximum:
        raise AgentSeatError("input_invalid", f"{name} exceeds {maximum} characters.")
    if any(unicodedata.category(char) in {"Cc", "Cf"} and char not in "\n\t" for char in clean):
        raise AgentSeatError("input_invalid", f"{name} contains unsupported control characters.")
    return clean


def _revision(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise AgentSeatError("input_invalid", f"{name} must be a non-negative integer.")
    return value


def _text_list(value: Any, name: str, *, maximum_items: int = 32, maximum_text: int = 500) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum_items:
        raise AgentSeatError("input_invalid", f"{name} must be a list with at most {maximum_items} items.")
    return [_text(item, f"{name}[{index}]", maximum=maximum_text) for index, item in enumerate(value)]


def _id_list(value: Any, name: str, *, maximum_items: int = 16) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum_items:
        raise AgentSeatError("input_invalid", f"{name} must be a list with at most {maximum_items} items.")
    result = [_identifier(item, f"{name}[{index}]") for index, item in enumerate(value)]
    if len(result) != len(set(result)):
        raise AgentSeatError("input_invalid", f"{name} must not contain duplicates.")
    return result


def validate_intent_authority(state: dict[str, Any], intent: dict[str, Any]) -> None:
    """Validate declared authority without interpreting fictional prose."""
    seat = state["seat"]
    projection = state["projection"]
    if intent["actor_id"] != seat["seat_id"]:
        raise AgentSeatError("authority_violation", "The intent actor does not own the active Agent Seat.", exit_code=3)
    capabilities = set(seat.get("capabilities", ["self.speak", "self.move", "self.observe", "self.recall"]))
    required = ACTION_CAPABILITIES.get(intent["action_type"])
    if required is None or required not in capabilities:
        raise AgentSeatError("authority_violation", "The action type is outside this character's declared capabilities.", exit_code=3)
    allowed_targets = set(projection.get("entity_refs", []))
    if any(target not in allowed_targets for target in intent["targets"]):
        raise AgentSeatError("authority_violation", "The intent targets an entity outside the current safe projection.", exit_code=3)
    owned_resources = set(projection.get("owned_resource_refs", []))
    if any(resource not in owned_resources for resource in intent["resource_refs"]):
        raise AgentSeatError("authority_violation", "The intent uses a resource the character does not own or control.", exit_code=3)
    known_refs = {item.get("fact_id") for item in projection.get("knowledge_index", []) if isinstance(item, dict)}
    if any(ref not in known_refs for ref in intent["knowledge_refs"]):
        raise AgentSeatError("knowledge_violation", "The intent cites knowledge outside the character projection.", exit_code=3)
    if intent["asserted_outcomes"]:
        raise AgentSeatError("authority_violation", "Agents may request effects but cannot assert world outcomes.", exit_code=3)


def _digest(action: str, request: dict[str, Any]) -> str:
    canonical = json.dumps({"action": action, "request": request}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def initial_state() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "seat_revision": 0,
        "updated_at": "",
        "session": {
            "session_id": "",
            "status": "idle",
            "session_revision": 0,
            "current_turn_number": 0,
            "started_at": "",
            "paused_at": "",
        },
        "seat": {
            "seat_id": "",
            "character_ref": "",
            "display_name": "",
            "role": "",
            "status": "unconfigured",
            "persona": {"goals": [], "voice_anchors": [], "boundaries": []},
            "capabilities": [],
        },
        "beat": {"beat_id": "", "scene_id": "", "source_revision": 0, "status": "closed", "opened_at": ""},
        "projection": {
            "summary": "",
            "perceivable_facts": [],
            "self_knowledge": [],
            "known_facts": [],
            "party_public_facts": [],
            "allowed_actions": [],
            "entity_refs": [],
            "owned_resource_refs": [],
            "knowledge_index": [],
        },
        "intent": None,
        "resolution": None,
        "turn_history": [],
        "operation_ledger": [],
    }


def migrate_legacy_state(data: Any) -> tuple[dict[str, Any], bool]:
    if not isinstance(data, dict) or data.get("schema_version") != LEGACY_SCHEMA_VERSION:
        return data, False
    migrated = copy.deepcopy(data)
    configured = isinstance(migrated.get("seat"), dict) and migrated["seat"].get("status") != "unconfigured"
    migrated["schema_version"] = SCHEMA_VERSION
    migrated["session"] = {
        "session_id": "legacy-session" if configured else "",
        "status": "active" if configured else "idle",
        "session_revision": int(migrated.get("seat_revision", 0)),
        "current_turn_number": 1 if configured else 0,
        "started_at": migrated.get("updated_at", "") if configured else "",
        "paused_at": "",
    }
    migrated["turn_history"] = []
    return migrated, True


def validate_state(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["state must be an object"]
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if not isinstance(data.get("seat_revision"), int) or isinstance(data.get("seat_revision"), bool) or data.get("seat_revision", -1) < 0:
        errors.append("seat_revision must be a non-negative integer")
    session = data.get("session")
    if not isinstance(session, dict) or session.get("status") not in {"idle", "active", "paused", "complete"}:
        errors.append("session.status is invalid")
    elif not isinstance(session.get("session_revision"), int) or session.get("session_revision", -1) < 0:
        errors.append("session.session_revision must be a non-negative integer")
    seat = data.get("seat")
    if not isinstance(seat, dict) or seat.get("status") not in {"unconfigured", "awaiting", "submitted", "resolved", "closed"}:
        errors.append("seat.status is invalid")
    beat = data.get("beat")
    if not isinstance(beat, dict) or beat.get("status") not in {"closed", "open", "resolved"}:
        errors.append("beat.status is invalid")
    projection = data.get("projection")
    if not isinstance(projection, dict):
        errors.append("projection must be an object")
    else:
        for key in PROJECTION_LISTS:
            if not isinstance(projection.get(key), list) or not all(isinstance(item, str) for item in projection.get(key, [])):
                errors.append(f"projection.{key} must be a list of strings")
        for key in ("entity_refs", "owned_resource_refs"):
            if key in projection and (not isinstance(projection.get(key), list) or not all(isinstance(item, str) for item in projection.get(key, []))):
                errors.append(f"projection.{key} must be a list of identifiers")
        if "knowledge_index" in projection and not isinstance(projection.get("knowledge_index"), list):
            errors.append("projection.knowledge_index must be a list")
    if data.get("intent") is not None and not isinstance(data.get("intent"), dict):
        errors.append("intent must be null or an object")
    if data.get("resolution") is not None and not isinstance(data.get("resolution"), dict):
        errors.append("resolution must be null or an object")
    history = data.get("turn_history")
    if not isinstance(history, list) or len(history) > MAX_TURN_HISTORY:
        errors.append(f"turn_history must contain at most {MAX_TURN_HISTORY} entries")
    ledger = data.get("operation_ledger")
    if not isinstance(ledger, list) or len(ledger) > MAX_LEDGER:
        errors.append(f"operation_ledger must contain at most {MAX_LEDGER} entries")
    return errors


def load_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AgentSeatError("state_missing", f"Agent Seat state does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentSeatError("state_invalid", str(exc)) from exc
    data, _ = migrate_legacy_state(data)
    errors = validate_state(data)
    if errors:
        raise AgentSeatError("state_invalid", "; ".join(errors))
    return data


def check_state(path: Path) -> dict[str, Any]:
    try:
        data = load_state(path.resolve())
    except AgentSeatError as exc:
        return {"ok": False, "failure_category": exc.category, "failure_reason": str(exc)}
    return {
        "ok": True,
        "state_path": str(path.resolve()),
        "seat_revision": data["seat_revision"],
        "seat_status": data["seat"]["status"],
        "beat_status": data["beat"]["status"],
        "session_status": data["session"]["status"],
        "session_revision": data["session"]["session_revision"],
        "current_turn_number": data["session"]["current_turn_number"],
    }


def _replay(state: dict[str, Any], operation_id: str, digest: str) -> dict[str, Any] | None:
    for entry in reversed(state["operation_ledger"]):
        if entry.get("operation_id") != operation_id:
            continue
        if entry.get("payload_digest") != digest:
            raise AgentSeatError("operation_conflict", "operation_id was already used with a different payload.", exit_code=3)
        result = copy.deepcopy(entry.get("result", {}))
        result["idempotent"] = True
        return result
    return None


def _record(state: dict[str, Any], operation_id: str, action: str, digest: str, result: dict[str, Any]) -> None:
    state["operation_ledger"].append(
        {"operation_id": operation_id, "action": action, "payload_digest": digest, "completed_at": _now(), "result": copy.deepcopy(result)}
    )
    state["operation_ledger"] = state["operation_ledger"][-MAX_LEDGER:]


def _update(path: Path, callback: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    path = path.resolve()
    lock_path = path.with_name(f".{path.name}.lock")
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise AgentSeatError("update_busy", "Another Agent Seat update is in progress.", exit_code=4) from exc
    try:
        state = load_state(path)
        result = callback(state)
        errors = validate_state(state)
        if errors:
            raise AgentSeatError("state_invalid", "; ".join(errors))
        if not result.get("idempotent"):
            _atomic_write(path, state)
        return result
    finally:
        try:
            os.close(lock_fd)
        finally:
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def open_beat(path: Path, request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise AgentSeatError("input_invalid", "Open-beat request must be an object.")
    operation_id = _identifier(request.get("operation_id"), "operation_id")
    expected_revision = _revision(request.get("expected_seat_revision"), "expected_seat_revision")
    payload_digest = _digest("open_beat", request)

    def apply(state: dict[str, Any]) -> dict[str, Any]:
        replay = _replay(state, operation_id, payload_digest)
        if replay is not None:
            return replay
        if state["seat_revision"] != expected_revision:
            raise AgentSeatError("revision_conflict", f"Expected seat revision {expected_revision}, found {state['seat_revision']}.", exit_code=3)
        if state["session"]["status"] == "paused":
            raise AgentSeatError("session_paused", "Resume the Agent Seat session before opening a beat.", exit_code=3)
        if state["session"]["status"] == "complete":
            raise AgentSeatError("session_complete", "Start a new Agent Seat session before opening another beat.", exit_code=3)
        seat_request = request.get("seat")
        beat_request = request.get("beat")
        projection_request = request.get("projection")
        if not isinstance(seat_request, dict) or not isinstance(beat_request, dict) or not isinstance(projection_request, dict):
            raise AgentSeatError("input_invalid", "seat, beat, and projection must be objects.")
        persona_request = seat_request.get("persona", {})
        if not isinstance(persona_request, dict):
            raise AgentSeatError("input_invalid", "seat.persona must be an object.")
        seat = {
            "seat_id": _identifier(seat_request.get("seat_id"), "seat.seat_id"),
            "character_ref": _text(seat_request.get("character_ref"), "seat.character_ref", maximum=160),
            "display_name": _text(seat_request.get("display_name"), "seat.display_name", maximum=80),
            "role": _text(seat_request.get("role", "Participant"), "seat.role", maximum=120),
            "status": "awaiting",
            "persona": {
                "goals": _text_list(persona_request.get("goals", []), "seat.persona.goals", maximum_items=8, maximum_text=300),
                "voice_anchors": _text_list(persona_request.get("voice_anchors", []), "seat.persona.voice_anchors", maximum_items=8, maximum_text=200),
                "boundaries": _text_list(persona_request.get("boundaries", []), "seat.persona.boundaries", maximum_items=8, maximum_text=300),
            },
            "capabilities": _id_list(
                seat_request.get("capabilities", ["self.speak", "self.move", "self.observe", "self.recall"]),
                "seat.capabilities",
                maximum_items=8,
            ),
        }
        beat = {
            "beat_id": _identifier(beat_request.get("beat_id"), "beat.beat_id"),
            "scene_id": _identifier(beat_request.get("scene_id"), "beat.scene_id"),
            "source_revision": _revision(beat_request.get("source_revision"), "beat.source_revision"),
            "status": "open",
            "opened_at": _now(),
        }
        projection = {
            "summary": _text(projection_request.get("summary", ""), "projection.summary", maximum=1200, allow_empty=True),
            "pressure": _text(projection_request.get("pressure", ""), "projection.pressure", maximum=600, allow_empty=True),
        }
        for key in PROJECTION_LISTS:
            projection[key] = _text_list(projection_request.get(key, []), f"projection.{key}")
        projection["entity_refs"] = _id_list(projection_request.get("entity_refs", []), "projection.entity_refs", maximum_items=32)
        projection["owned_resource_refs"] = _id_list(projection_request.get("owned_resource_refs", []), "projection.owned_resource_refs", maximum_items=32)
        knowledge_index = projection_request.get("knowledge_index", [])
        if not isinstance(knowledge_index, list) or len(knowledge_index) > 32:
            raise AgentSeatError("input_invalid", "projection.knowledge_index must contain at most 32 items.")
        projection["knowledge_index"] = copy.deepcopy(knowledge_index)
        previous_intent = state.get("intent")
        previous_resolution = state.get("resolution")
        if state["beat"].get("status") == "resolved" and isinstance(previous_intent, dict):
            state["turn_history"].append(
                {
                    "turn_number": state["session"]["current_turn_number"],
                    "beat": copy.deepcopy(state["beat"]),
                    "intent": copy.deepcopy(previous_intent),
                    "resolution": copy.deepcopy(previous_resolution),
                }
            )
            state["turn_history"] = state["turn_history"][-MAX_TURN_HISTORY:]
        if state["session"]["status"] == "idle":
            state["session"].update(
                {
                    "session_id": f"session-{operation_id}",
                    "status": "active",
                    "started_at": _now(),
                    "paused_at": "",
                }
            )
        state["session"]["current_turn_number"] += 1
        state["session"]["session_revision"] += 1
        state["seat"] = seat
        state["beat"] = beat
        state["projection"] = projection
        state["intent"] = None
        state["resolution"] = None
        state["seat_revision"] += 1
        state["updated_at"] = _now()
        result = {
            "ok": True,
            "operation_id": operation_id,
            "seat_revision": state["seat_revision"],
            "seat_status": "awaiting",
            "beat_id": beat["beat_id"],
            "session_id": state["session"]["session_id"],
            "session_revision": state["session"]["session_revision"],
            "turn_number": state["session"]["current_turn_number"],
            "idempotent": False,
        }
        _record(state, operation_id, "open_beat", payload_digest, result)
        return result

    return _update(path, apply)


def get_context(path: Path) -> dict[str, Any]:
    state = load_state(path.resolve())
    available = state["seat"]["status"] != "unconfigured" and state["beat"]["status"] in {"open", "resolved"}
    return {
        "ok": True,
        "available": available,
        "seat_revision": state["seat_revision"],
        "session": copy.deepcopy(state["session"]),
        "seat": copy.deepcopy(state["seat"]),
        "beat": copy.deepcopy(state["beat"]),
        "perspective": copy.deepcopy(state["projection"]) if available else None,
    }


def get_next_turn(path: Path, after_revision: int | None = None) -> dict[str, Any]:
    state = load_state(path.resolve())
    session = state["session"]
    if session["status"] == "paused":
        status = "paused"
    elif session["status"] == "complete":
        status = "complete"
    elif after_revision is not None and after_revision == session["session_revision"]:
        status = "waiting"
    elif state["beat"]["status"] == "open" and state["seat"]["status"] == "awaiting":
        status = "ready"
    elif state["beat"]["status"] == "resolved":
        status = "resolved"
    else:
        status = "waiting"
    result = {
        "ok": True,
        "status": status,
        "session": copy.deepcopy(session),
        "seat_revision": state["seat_revision"],
        "beat": copy.deepcopy(state["beat"]),
    }
    if status == "ready":
        result["seat"] = copy.deepcopy(state["seat"])
        result["perspective"] = copy.deepcopy(state["projection"])
    if status == "resolved":
        result["resolution"] = copy.deepcopy(state["resolution"])
    return result


def submit_turn(path: Path, request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise AgentSeatError("input_invalid", "Turn request must be an object.")
    operation_id = _identifier(request.get("operation_id"), "operation_id")
    expected_scene_id = _identifier(request.get("expected_scene_id"), "expected_scene_id")
    expected_source_revision = _revision(request.get("expected_source_revision"), "expected_source_revision")
    action = _text(request.get("action"), "action", maximum=1200)
    approach = _text(request.get("approach", ""), "approach", maximum=600, allow_empty=True)
    speech = _text(request.get("speech", ""), "speech", maximum=1200, allow_empty=True)
    actor_id = _identifier(request.get("actor_id", request.get("seat_id", "legacy-seat")), "actor_id")
    action_type = _identifier(request.get("action_type", "act"), "action_type")
    targets = _id_list(request.get("targets", []), "targets")
    resource_refs = _id_list(request.get("resource_refs", []), "resource_refs")
    knowledge_refs = _id_list(request.get("knowledge_refs", []), "knowledge_refs")
    requested_effect = _text(request.get("requested_effect", ""), "requested_effect", maximum=500, allow_empty=True)
    asserted_outcomes = _text_list(request.get("asserted_outcomes", []), "asserted_outcomes", maximum_items=8, maximum_text=300)
    normalized = {
        "operation_id": operation_id,
        "expected_scene_id": expected_scene_id,
        "expected_source_revision": expected_source_revision,
        "action": action,
        "approach": approach,
        "speech": speech,
        "actor_id": actor_id,
        "action_type": action_type,
        "targets": targets,
        "resource_refs": resource_refs,
        "knowledge_refs": knowledge_refs,
        "requested_effect": requested_effect,
        "asserted_outcomes": asserted_outcomes,
    }
    payload_digest = _digest("submit_turn", normalized)

    def apply(state: dict[str, Any]) -> dict[str, Any]:
        replay = _replay(state, operation_id, payload_digest)
        if replay is not None:
            return replay
        if state["beat"]["status"] != "open":
            raise AgentSeatError("beat_closed", "This beat is not accepting turns.", exit_code=3)
        if state["beat"]["scene_id"] != expected_scene_id or state["beat"]["source_revision"] != expected_source_revision:
            raise AgentSeatError("stale_turn", "The scene or source revision has changed; refresh perspective before acting.", exit_code=3)
        if state["intent"] is not None:
            raise AgentSeatError("intent_exists", "This seat already submitted a turn for the active beat.", exit_code=3)
        normalized["actor_id"] = state["seat"]["seat_id"] if actor_id == "legacy-seat" else actor_id
        validate_intent_authority(state, normalized)
        submitted_at = _now()
        state["intent"] = {
            "operation_id": operation_id,
            "beat_id": state["beat"]["beat_id"],
            "scene_id": expected_scene_id,
            "source_revision": expected_source_revision,
            "status": "pending",
            "action": action,
            "approach": approach,
            "speech": speech,
            "actor_id": normalized["actor_id"],
            "action_type": action_type,
            "targets": targets,
            "resource_refs": resource_refs,
            "knowledge_refs": knowledge_refs,
            "requested_effect": requested_effect,
            "submitted_at": submitted_at,
        }
        state["seat"]["status"] = "submitted"
        state["seat_revision"] += 1
        state["updated_at"] = submitted_at
        result = {
            "ok": True,
            "operation_id": operation_id,
            "seat_revision": state["seat_revision"],
            "status": "pending",
            "message": "Turn committed to the active RePoG beat; no world truth has changed yet.",
            "idempotent": False,
        }
        _record(state, operation_id, "submit_turn", payload_digest, result)
        return result

    return _update(path, apply)


def get_turn_status(path: Path, operation_id: str) -> dict[str, Any]:
    operation_id = _identifier(operation_id, "operation_id")
    state = load_state(path.resolve())
    intent = state.get("intent")
    if not isinstance(intent, dict) or intent.get("operation_id") != operation_id:
        for archived in reversed(state.get("turn_history", [])):
            archived_intent = archived.get("intent") if isinstance(archived, dict) else None
            if isinstance(archived_intent, dict) and archived_intent.get("operation_id") == operation_id:
                result = {
                    "ok": True,
                    "operation_id": operation_id,
                    "status": archived_intent["status"],
                    "seat_revision": state["seat_revision"],
                    "beat_id": archived_intent["beat_id"],
                    "archived": True,
                }
                if isinstance(archived.get("resolution"), dict):
                    result["resolution"] = copy.deepcopy(archived["resolution"])
                return result
        return {"ok": True, "operation_id": operation_id, "status": "not_found", "seat_revision": state["seat_revision"]}
    result: dict[str, Any] = {
        "ok": True,
        "operation_id": operation_id,
        "status": intent["status"],
        "seat_revision": state["seat_revision"],
        "beat_id": intent["beat_id"],
    }
    if isinstance(state.get("resolution"), dict) and state["resolution"].get("intent_operation_id") == operation_id:
        result["resolution"] = copy.deepcopy(state["resolution"])
    return result


def resolve_turn(path: Path, request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise AgentSeatError("input_invalid", "Resolve request must be an object.")
    operation_id = _identifier(request.get("operation_id"), "operation_id")
    expected_revision = _revision(request.get("expected_seat_revision"), "expected_seat_revision")
    intent_operation_id = _identifier(request.get("intent_operation_id"), "intent_operation_id")
    outcome = request.get("outcome")
    if outcome not in {"accepted", "altered", "rejected", "skipped", "expired"}:
        raise AgentSeatError("input_invalid", "outcome is invalid.")
    summary = _text(request.get("summary"), "summary", maximum=1200)
    visible_consequences = _text_list(request.get("visible_consequences", []), "visible_consequences", maximum_items=16)
    normalized = {
        "operation_id": operation_id,
        "expected_seat_revision": expected_revision,
        "intent_operation_id": intent_operation_id,
        "outcome": outcome,
        "summary": summary,
        "visible_consequences": visible_consequences,
    }
    payload_digest = _digest("resolve_turn", normalized)

    def apply(state: dict[str, Any]) -> dict[str, Any]:
        replay = _replay(state, operation_id, payload_digest)
        if replay is not None:
            return replay
        if state["seat_revision"] != expected_revision:
            raise AgentSeatError("revision_conflict", f"Expected seat revision {expected_revision}, found {state['seat_revision']}.", exit_code=3)
        intent = state.get("intent")
        if not isinstance(intent, dict) or intent.get("operation_id") != intent_operation_id:
            raise AgentSeatError("intent_missing", "The referenced pending intent does not exist.", exit_code=3)
        if intent.get("status") != "pending":
            raise AgentSeatError("intent_closed", "The referenced intent is no longer pending.", exit_code=3)
        resolved_at = _now()
        intent["status"] = "resolved" if outcome in {"accepted", "altered", "rejected"} else outcome
        state["resolution"] = {
            "intent_operation_id": intent_operation_id,
            "outcome": outcome,
            "summary": summary,
            "visible_consequences": visible_consequences,
            "resolved_at": resolved_at,
        }
        state["beat"]["status"] = "resolved"
        state["seat"]["status"] = "resolved"
        state["seat_revision"] += 1
        state["updated_at"] = resolved_at
        result = {
            "ok": True,
            "operation_id": operation_id,
            "intent_operation_id": intent_operation_id,
            "seat_revision": state["seat_revision"],
            "status": intent["status"],
            "idempotent": False,
        }
        _record(state, operation_id, "resolve_turn", payload_digest, result)
        return result

    return _update(path, apply)


def set_session_status(path: Path, request: dict[str, Any], target: str) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise AgentSeatError("input_invalid", "Session request must be an object.")
    operation_id = _identifier(request.get("operation_id"), "operation_id")
    expected_revision = _revision(request.get("expected_session_revision"), "expected_session_revision")
    if target not in {"active", "paused", "complete"}:
        raise AgentSeatError("input_invalid", "target session status is invalid")
    normalized = {"operation_id": operation_id, "expected_session_revision": expected_revision, "target": target}
    payload_digest = _digest("session_status", normalized)

    def apply(state: dict[str, Any]) -> dict[str, Any]:
        replay = _replay(state, operation_id, payload_digest)
        if replay is not None:
            return replay
        session = state["session"]
        if session["session_revision"] != expected_revision:
            raise AgentSeatError("revision_conflict", f"Expected session revision {expected_revision}, found {session['session_revision']}.", exit_code=3)
        allowed = {
            "active": {"paused"},
            "paused": {"active"},
            "complete": {"active", "paused"},
        }
        if session["status"] not in allowed[target]:
            raise AgentSeatError("session_transition_invalid", f"Cannot change session from {session['status']} to {target}.", exit_code=3)
        session["status"] = target
        session["session_revision"] += 1
        session["paused_at"] = _now() if target == "paused" else ""
        state["updated_at"] = _now()
        result = {
            "ok": True,
            "operation_id": operation_id,
            "status": target,
            "session_revision": session["session_revision"],
            "idempotent": False,
        }
        _record(state, operation_id, "session_status", payload_digest, result)
        return result

    return _update(path, apply)


def migrate_state_file(path: Path) -> dict[str, Any]:
    path = path.resolve()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentSeatError("state_invalid", str(exc)) from exc
    migrated, changed = migrate_legacy_state(raw)
    errors = validate_state(migrated)
    if errors:
        raise AgentSeatError("state_invalid", "; ".join(errors))
    if changed:
        _atomic_write(path, migrated)
    return {"ok": True, "migrated": changed, "schema_version": migrated["schema_version"]}


def _load_request(args: argparse.Namespace) -> dict[str, Any]:
    if getattr(args, "input_json", None):
        try:
            value = json.loads(args.input_json)
        except json.JSONDecodeError as exc:
            raise AgentSeatError("input_invalid", f"Invalid --input-json: {exc}") from exc
    elif getattr(args, "input_file", None):
        try:
            value = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AgentSeatError("input_invalid", f"Cannot read --input-file: {exc}") from exc
    else:
        try:
            value = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            raise AgentSeatError("input_invalid", f"Invalid JSON on stdin: {exc}") from exc
    if not isinstance(value, dict):
        raise AgentSeatError("input_invalid", "Request must be a JSON object.")
    return value


def _request_source(parser: argparse.ArgumentParser) -> None:
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input-json", help="Request as JSON.")
    source.add_argument("--input-file", help="Path to a JSON request.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", help="Path to agent_seat_state.json.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="Validate and summarize Agent Seat state.")
    commands.add_parser("context", help="Read the current player-safe seat perspective.")
    next_parser = commands.add_parser("next-turn", help="Read the next durable session state.")
    next_parser.add_argument("--after-revision", type=int)
    commands.add_parser("migrate", help="Atomically migrate a legacy Agent Seat state file.")
    status_parser = commands.add_parser("turn-status", help="Read one submitted turn status.")
    status_parser.add_argument("--operation-id", required=True)
    for name in ("open-beat", "submit-turn", "resolve-turn", "pause-session", "resume-session", "complete-session"):
        _request_source(commands.add_parser(name))
    args = parser.parse_args(argv)
    path = Path(args.state)
    try:
        if args.command == "status":
            result = check_state(path)
        elif args.command == "context":
            result = get_context(path)
        elif args.command == "next-turn":
            result = get_next_turn(path, args.after_revision)
        elif args.command == "migrate":
            result = migrate_state_file(path)
        elif args.command == "turn-status":
            result = get_turn_status(path, args.operation_id)
        elif args.command == "open-beat":
            result = open_beat(path, _load_request(args))
        elif args.command == "submit-turn":
            result = submit_turn(path, _load_request(args))
        elif args.command == "resolve-turn":
            result = resolve_turn(path, _load_request(args))
        elif args.command == "pause-session":
            result = set_session_status(path, _load_request(args), "paused")
        elif args.command == "resume-session":
            result = set_session_status(path, _load_request(args), "active")
        else:
            result = set_session_status(path, _load_request(args), "complete")
    except AgentSeatError as exc:
        print(json.dumps({"ok": False, "failure_category": exc.category, "failure_reason": str(exc)}, indent=2, ensure_ascii=True))
        return exc.exit_code
    except OSError as exc:
        print(json.dumps({"ok": False, "failure_category": "write_failed", "failure_reason": str(exc)}, indent=2, ensure_ascii=True))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())

"""Apply small deterministic campaign mechanics without deciding narrative outcomes.

Schema v2 uses a monotonic ``operation_sequence``.  A retry of the most recent
operation is idempotent; older or out-of-order operations are rejected instead
of becoming valid again after a bounded id history rolls over.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2
SUPPORTED_OPERATIONS = {
    "use",
    "use_ability",
    "spend",
    "gain",
    "set",
    "set_ability_known",
    "set_cooldown",
    "add_item",
    "remove_item",
    "consume_item",
    "set_item_quantity",
    "add_condition",
    "remove_condition",
    "advance_clock",
    "set_clock",
    "advance_time",
}


class MechanicError(ValueError):
    """Raised when a deterministic mechanic request violates the ledger contract."""


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=True)
            stream.write("\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def _integer(value: Any, name: str, minimum: int | None = None, maximum: int | None = None) -> int:
    if type(value) is not int:  # bool, numeric strings, and floats are deliberately rejected.
        raise MechanicError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise MechanicError(f"{name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise MechanicError(f"{name} must be at most {maximum}")
    return value


def _identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MechanicError(f"{name} must be a non-empty string")
    return value.strip()


def _actor(state: dict[str, Any], actor_id: str) -> dict[str, Any]:
    actors = state.get("actors")
    if not isinstance(actors, dict) or actor_id not in actors or not isinstance(actors[actor_id], dict):
        raise MechanicError(f"unknown actor: {actor_id}")
    return actors[actor_id]


def _resource(actor: dict[str, Any], resource_id: str) -> dict[str, Any]:
    resources = actor.get("resources")
    if not isinstance(resources, dict) or resource_id not in resources:
        raise MechanicError(f"unknown resource: {resource_id}")
    resource = resources[resource_id]
    if not isinstance(resource, dict):
        raise MechanicError(f"resource must be an object: {resource_id}")
    for key in ("current", "minimum", "maximum"):
        _integer(resource.get(key), f"{resource_id}.{key}")
    if resource["minimum"] > resource["maximum"]:
        raise MechanicError(f"{resource_id} minimum exceeds maximum")
    if not resource["minimum"] <= resource["current"] <= resource["maximum"]:
        raise MechanicError(f"{resource_id} current is outside its bounds")
    regen = resource.get("regen")
    if regen is not None:
        if not isinstance(regen, dict):
            raise MechanicError(f"{resource_id}.regen must be an object")
        _integer(regen.get("amount"), f"{resource_id}.regen.amount", 0)
        _identifier(regen.get("unit"), f"{resource_id}.regen.unit")
    return resource


def _ability(actor: dict[str, Any], ability_id: str) -> dict[str, Any]:
    abilities = actor.get("abilities")
    if not isinstance(abilities, dict) or ability_id not in abilities or not isinstance(abilities[ability_id], dict):
        raise MechanicError(f"unknown ability: {ability_id}")
    ability = abilities[ability_id]
    if not isinstance(ability.get("known"), bool):
        raise MechanicError(f"{ability_id}.known must be boolean")
    costs = ability.get("costs", {})
    if not isinstance(costs, dict):
        raise MechanicError(f"{ability_id}.costs must be an object")
    for resource_id, cost in costs.items():
        _identifier(resource_id, f"{ability_id}.cost resource id")
        _integer(cost, f"{ability_id}.costs.{resource_id}", 0)
        _resource(actor, resource_id)
    cooldown = ability.get("cooldown")
    if cooldown is not None:
        if not isinstance(cooldown, dict):
            raise MechanicError(f"{ability_id}.cooldown must be an object")
        duration = _integer(cooldown.get("duration"), f"{ability_id}.cooldown.duration", 0)
        remaining = _integer(cooldown.get("remaining"), f"{ability_id}.cooldown.remaining", 0)
        if remaining > duration:
            raise MechanicError(f"{ability_id}.cooldown.remaining exceeds duration")
        _identifier(cooldown.get("unit"), f"{ability_id}.cooldown.unit")
    return ability


def _item(actor: dict[str, Any], item_id: str) -> dict[str, Any]:
    inventory = actor.get("inventory")
    if not isinstance(inventory, dict) or item_id not in inventory or not isinstance(inventory[item_id], dict):
        raise MechanicError(f"unknown item: {item_id}")
    item = inventory[item_id]
    _integer(item.get("quantity"), f"{item_id}.quantity", 0)
    if "consumable" in item and not isinstance(item["consumable"], bool):
        raise MechanicError(f"{item_id}.consumable must be boolean")
    if "maximum" in item:
        maximum = _integer(item["maximum"], f"{item_id}.maximum", 0)
        if item["quantity"] > maximum:
            raise MechanicError(f"{item_id}.quantity exceeds maximum")
    return item


def _condition(actor: dict[str, Any], condition_id: str) -> dict[str, Any]:
    conditions = actor.get("conditions")
    if not isinstance(conditions, dict) or condition_id not in conditions or not isinstance(conditions[condition_id], dict):
        raise MechanicError(f"unknown condition: {condition_id}")
    condition = conditions[condition_id]
    _integer(condition.get("level"), f"{condition_id}.level", 1)
    duration = condition.get("duration")
    if duration is not None:
        if not isinstance(duration, dict):
            raise MechanicError(f"{condition_id}.duration must be an object")
        _integer(duration.get("remaining"), f"{condition_id}.duration.remaining", 0)
        _identifier(duration.get("unit"), f"{condition_id}.duration.unit")
    return condition


def _clock(state: dict[str, Any], clock_id: str) -> dict[str, Any]:
    clocks = state.get("clocks")
    if not isinstance(clocks, dict) or clock_id not in clocks or not isinstance(clocks[clock_id], dict):
        raise MechanicError(f"unknown clock: {clock_id}")
    clock = clocks[clock_id]
    current = _integer(clock.get("current"), f"{clock_id}.current", 0)
    maximum = _integer(clock.get("maximum"), f"{clock_id}.maximum", 1)
    if current > maximum:
        raise MechanicError(f"{clock_id}.current exceeds maximum")
    return clock


def _validate_state(state: dict[str, Any]) -> None:
    if _integer(state.get("schema_version"), "schema_version", 1) != SCHEMA_VERSION:
        raise MechanicError(f"unsupported mechanics schema_version: {state.get('schema_version')}")
    if not isinstance(state.get("enabled"), bool):
        raise MechanicError("enabled must be boolean")
    _integer(state.get("revision"), "revision", 0)
    _integer(state.get("continuity_revision"), "continuity_revision", 0)
    _integer(state.get("operation_sequence"), "operation_sequence", 0)
    registry = state.get("operation_registry")
    if not isinstance(registry, dict):
        raise MechanicError("operation_registry must be an object")
    registered_sequences: set[int] = set()
    for operation_id, record in registry.items():
        _identifier(operation_id, "operation_registry id")
        if not isinstance(record, dict):
            raise MechanicError(f"operation_registry.{operation_id} must be an object")
        sequence = _integer(record.get("sequence"), f"operation_registry.{operation_id}.sequence", 1)
        record_revision = _integer(record.get("revision"), f"operation_registry.{operation_id}.revision", 1)
        if sequence > state["operation_sequence"] or record_revision > state["revision"]:
            raise MechanicError(f"operation_registry.{operation_id} points beyond current state")
        if sequence in registered_sequences:
            raise MechanicError("operation_registry contains duplicate sequences")
        registered_sequences.add(sequence)
        request_hash = record.get("request_hash")
        if request_hash is not None and (not isinstance(request_hash, str) or not request_hash):
            raise MechanicError(f"operation_registry.{operation_id}.request_hash must be a string or null")
    last = state.get("last_operation")
    if last is not None:
        if not isinstance(last, dict):
            raise MechanicError("last_operation must be an object or null")
        sequence = _integer(last.get("sequence"), "last_operation.sequence", 1)
        if sequence != state["operation_sequence"]:
            raise MechanicError("last_operation.sequence must match operation_sequence")
        _identifier(last.get("operation_id"), "last_operation.operation_id")
        last_revision = _integer(last.get("revision"), "last_operation.revision", 1)
        if last_revision != state["revision"]:
            raise MechanicError("last_operation.revision must match revision")
        if "request_hash" in last:
            request_hash = last["request_hash"]
            if not isinstance(request_hash, str) or not request_hash:
                raise MechanicError("last_operation.request_hash must be a non-empty string")
        registered_last = registry.get(last["operation_id"])
        if not isinstance(registered_last, dict) or registered_last.get("sequence") != last["sequence"]:
            raise MechanicError("last_operation must match operation_registry")
    actors = state.get("actors")
    if not isinstance(actors, dict):
        raise MechanicError("actors must be an object")
    for actor_id, actor in actors.items():
        _identifier(actor_id, "actor id")
        if not isinstance(actor, dict):
            raise MechanicError(f"actor must be an object: {actor_id}")
        for container_name in ("resources", "abilities", "inventory", "conditions"):
            container = actor.get(container_name, {})
            if not isinstance(container, dict):
                raise MechanicError(f"{actor_id}.{container_name} must be an object")
        for resource_id in actor.get("resources", {}):
            _resource(actor, resource_id)
        for ability_id in actor.get("abilities", {}):
            _ability(actor, ability_id)
        for item_id in actor.get("inventory", {}):
            _item(actor, item_id)
        for condition_id in actor.get("conditions", {}):
            _condition(actor, condition_id)
    clocks = state.get("clocks", {})
    if not isinstance(clocks, dict):
        raise MechanicError("clocks must be an object")
    for clock_id in clocks:
        _clock(state, clock_id)
    elapsed = state.get("elapsed_time", {})
    if not isinstance(elapsed, dict):
        raise MechanicError("elapsed_time must be an object")
    for unit, amount in elapsed.items():
        _identifier(unit, "elapsed_time unit")
        _integer(amount, f"elapsed_time.{unit}", 0)


def _migrate_v1(state: dict[str, Any]) -> dict[str, Any]:
    """Convert a v1 ledger in memory; its existing revision becomes the sequence floor."""
    migrated = copy.deepcopy(state)
    revision = _integer(migrated.get("revision", 0), "revision", 0)
    legacy = migrated.pop("applied_operations", [])
    if not isinstance(legacy, list) or any(not isinstance(item, str) or not item for item in legacy):
        raise MechanicError("applied_operations must contain non-empty strings")
    if len(legacy) != len(set(legacy)):
        raise MechanicError("applied_operations contains duplicate ids")
    if len(legacy) > revision:
        raise MechanicError("applied_operations cannot exceed revision")
    first_legacy_sequence = revision - len(legacy) + 1
    legacy_registry = {
        operation_id: {
            "sequence": first_legacy_sequence + index,
            "revision": first_legacy_sequence + index,
            "request_hash": None,
        }
        for index, operation_id in enumerate(legacy)
    }
    migrated.update(
        {
            "schema_version": SCHEMA_VERSION,
            "continuity_revision": 0,
            "operation_sequence": revision,
            "operation_registry": legacy_registry,
            "last_operation": (
                {"sequence": revision, "operation_id": legacy[-1], "revision": revision}
                if revision > 0 and legacy
                else None
            ),
            "clocks": {},
            "elapsed_time": {},
        }
    )
    return migrated


def _normalise_state(state: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    version = state.get("schema_version", 1)
    if type(version) is not int:
        raise MechanicError("schema_version must be an integer")
    if version == 1:
        migrated = _migrate_v1(state)
        _validate_state(migrated)
        return migrated, True
    if version != SCHEMA_VERSION:
        raise MechanicError(f"unsupported mechanics schema_version: {version}")
    normalized = copy.deepcopy(state)
    _validate_state(normalized)
    return normalized, False


def _change_resource(actor: dict[str, Any], resource_id: str, amount: int, changes: list[dict[str, Any]]) -> None:
    resource = _resource(actor, resource_id)
    before = resource["current"]
    after = before + amount
    if after < resource["minimum"]:
        raise MechanicError(f"insufficient {resource_id}")
    after = min(after, resource["maximum"])
    resource["current"] = after
    changes.append({"kind": "resource", "resource": resource_id, "before": before, "after": after})


def _use_ability(actor: dict[str, Any], ability_id: str, changes: list[dict[str, Any]]) -> None:
    ability = _ability(actor, ability_id)
    if ability["known"] is not True:
        raise MechanicError(f"ability is not known: {ability_id}")
    cooldown = ability.get("cooldown")
    if cooldown and cooldown["remaining"] > 0:
        raise MechanicError(f"ability is on cooldown: {ability_id}")
    for resource_id, cost in ability.get("costs", {}).items():
        resource = _resource(actor, resource_id)
        if resource["current"] - cost < resource["minimum"]:
            raise MechanicError(f"insufficient {resource_id}")
    for resource_id, cost in ability.get("costs", {}).items():
        _change_resource(actor, resource_id, -cost, changes)
    if cooldown is not None:
        before = cooldown["remaining"]
        cooldown["remaining"] = cooldown["duration"]
        changes.append({"kind": "cooldown", "ability": ability_id, "before": before, "after": cooldown["duration"]})


def _change_item(actor: dict[str, Any], item_id: str, amount: int, changes: list[dict[str, Any]]) -> None:
    item = _item(actor, item_id)
    before = item["quantity"]
    after = before + amount
    if after < 0:
        raise MechanicError(f"insufficient {item_id}")
    if "maximum" in item and after > item["maximum"]:
        raise MechanicError(f"{item_id}.quantity would exceed maximum")
    item["quantity"] = after
    changes.append({"kind": "inventory", "item": item_id, "before": before, "after": after})


def _advance_time(state: dict[str, Any], payload: dict[str, Any], changes: list[dict[str, Any]]) -> None:
    steps = _integer(payload.get("steps", 1), "steps", 1)
    unit = _identifier(payload.get("unit"), "unit")
    elapsed = state.setdefault("elapsed_time", {})
    before_elapsed = elapsed.get(unit, 0)
    _integer(before_elapsed, f"elapsed_time.{unit}", 0)
    elapsed[unit] = before_elapsed + steps
    changes.append({"kind": "time", "unit": unit, "before": before_elapsed, "after": elapsed[unit]})

    for actor_id, actor in state["actors"].items():
        for resource_id, resource in actor.get("resources", {}).items():
            regen = resource.get("regen")
            if isinstance(regen, dict) and regen.get("unit") == unit:
                local: list[dict[str, Any]] = []
                _change_resource(actor, resource_id, regen["amount"] * steps, local)
                for change in local:
                    change["actor"] = actor_id
                changes.extend(local)
        for ability_id, ability in actor.get("abilities", {}).items():
            cooldown = ability.get("cooldown")
            if isinstance(cooldown, dict) and cooldown.get("unit") == unit:
                before = cooldown["remaining"]
                after = max(0, before - steps)
                if after != before:
                    cooldown["remaining"] = after
                    changes.append({"kind": "cooldown", "actor": actor_id, "ability": ability_id, "before": before, "after": after})
        expired: list[str] = []
        for condition_id, condition in actor.get("conditions", {}).items():
            duration = condition.get("duration")
            if isinstance(duration, dict) and duration.get("unit") == unit:
                before = duration["remaining"]
                after = max(0, before - steps)
                duration["remaining"] = after
                changes.append({"kind": "condition_duration", "actor": actor_id, "condition": condition_id, "before": before, "after": after})
                if after == 0:
                    expired.append(condition_id)
        for condition_id in expired:
            del actor["conditions"][condition_id]
            changes.append({"kind": "condition_removed", "actor": actor_id, "condition": condition_id, "reason": "duration_elapsed"})


def _apply_actor_operation(state: dict[str, Any], operation: str, payload: dict[str, Any], changes: list[dict[str, Any]]) -> None:
    actor_id = _identifier(payload.get("actor_id"), "actor_id")
    actor = _actor(state, actor_id)
    if operation in {"use", "use_ability"}:
        _use_ability(actor, _identifier(payload.get("action_id"), "action_id"), changes)
    elif operation in {"spend", "gain", "set"}:
        resource_id = _identifier(payload.get("resource_id"), "resource_id")
        resource = _resource(actor, resource_id)
        if operation == "set":
            value = _integer(payload.get("value"), "value")
            if not resource["minimum"] <= value <= resource["maximum"]:
                raise MechanicError(f"value for {resource_id} is outside its bounds")
            before = resource["current"]
            resource["current"] = value
            changes.append({"kind": "resource", "resource": resource_id, "before": before, "after": value})
        else:
            amount = _integer(payload.get("amount"), "amount", 0)
            _change_resource(actor, resource_id, -amount if operation == "spend" else amount, changes)
    elif operation == "set_ability_known":
        ability_id = _identifier(payload.get("action_id"), "action_id")
        ability = _ability(actor, ability_id)
        known = payload.get("known")
        if not isinstance(known, bool):
            raise MechanicError("known must be boolean")
        before = ability["known"]
        ability["known"] = known
        changes.append({"kind": "ability_known", "ability": ability_id, "before": before, "after": known})
    elif operation == "set_cooldown":
        ability_id = _identifier(payload.get("action_id"), "action_id")
        ability = _ability(actor, ability_id)
        cooldown = ability.get("cooldown")
        if not isinstance(cooldown, dict):
            raise MechanicError(f"ability has no cooldown: {ability_id}")
        remaining = _integer(payload.get("remaining"), "remaining", 0, cooldown["duration"])
        before = cooldown["remaining"]
        cooldown["remaining"] = remaining
        changes.append({"kind": "cooldown", "ability": ability_id, "before": before, "after": remaining})
    elif operation in {"add_item", "remove_item", "consume_item", "set_item_quantity"}:
        item_id = _identifier(payload.get("item_id"), "item_id")
        if operation == "add_item" and item_id not in actor.setdefault("inventory", {}):
            quantity = _integer(payload.get("amount", 1), "amount", 1)
            maximum = payload.get("maximum")
            if maximum is not None:
                _integer(maximum, "maximum", quantity)
            consumable = payload.get("consumable", False)
            if not isinstance(consumable, bool):
                raise MechanicError("consumable must be boolean")
            actor["inventory"][item_id] = {"quantity": quantity, "consumable": consumable}
            if maximum is not None:
                actor["inventory"][item_id]["maximum"] = maximum
            changes.append({"kind": "inventory", "item": item_id, "before": 0, "after": quantity})
        elif operation == "set_item_quantity":
            item = _item(actor, item_id)
            value = _integer(payload.get("quantity"), "quantity", 0)
            if "maximum" in item and value > item["maximum"]:
                raise MechanicError(f"{item_id}.quantity would exceed maximum")
            before = item["quantity"]
            item["quantity"] = value
            changes.append({"kind": "inventory", "item": item_id, "before": before, "after": value})
        else:
            item = _item(actor, item_id)
            if operation == "consume_item" and item.get("consumable") is not True:
                raise MechanicError(f"item is not consumable: {item_id}")
            amount = _integer(payload.get("amount", 1), "amount", 1)
            _change_item(actor, item_id, -amount if operation in {"remove_item", "consume_item"} else amount, changes)
    elif operation in {"add_condition", "remove_condition"}:
        condition_id = _identifier(payload.get("condition_id"), "condition_id")
        conditions = actor.setdefault("conditions", {})
        if not isinstance(conditions, dict):
            raise MechanicError("conditions must be an object")
        if operation == "remove_condition":
            _condition(actor, condition_id)
            before = copy.deepcopy(conditions.pop(condition_id))
            changes.append({"kind": "condition_removed", "condition": condition_id, "before": before})
        else:
            if condition_id in conditions:
                raise MechanicError(f"condition already exists: {condition_id}")
            level = _integer(payload.get("level", 1), "level", 1)
            condition: dict[str, Any] = {"level": level}
            if "remaining" in payload or "unit" in payload:
                remaining = _integer(payload.get("remaining"), "remaining", 1)
                unit = _identifier(payload.get("unit"), "unit")
                condition["duration"] = {"remaining": remaining, "unit": unit}
            conditions[condition_id] = condition
            changes.append({"kind": "condition_added", "condition": condition_id, "after": copy.deepcopy(condition)})
    else:
        raise MechanicError(f"unsupported actor operation: {operation}")
    for change in changes:
        change.setdefault("actor", actor_id)


def apply_operation(state: dict[str, Any], payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized, migrated = _normalise_state(state)
    if normalized["enabled"] is not True:
        raise MechanicError("deterministic mechanics are not enabled for this campaign")
    operation_id = _identifier(payload.get("operation_id"), "operation_id")
    request_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    current_sequence = normalized["operation_sequence"]
    supplied_sequence = payload.get("operation_sequence")
    registered = normalized["operation_registry"].get(operation_id)
    if registered is not None:
        sequence = (
            registered["sequence"]
            if supplied_sequence is None and migrated
            else _integer(supplied_sequence, "operation_sequence", 1)
        )
        if sequence != registered["sequence"]:
            raise MechanicError(
                f"operation_id was already used at sequence {registered['sequence']}: {operation_id}"
            )
        previous_hash = registered.get("request_hash")
        if previous_hash is not None and previous_hash != request_hash:
            raise MechanicError("operation retry payload differs from the recorded operation")
        return normalized, {
            "ok": True,
            "duplicate": True,
            "operation_id": operation_id,
            "operation_sequence": sequence,
            "revision": normalized["revision"],
            "continuity_revision": normalized["continuity_revision"],
            "changes": [],
        }
    if supplied_sequence is None and migrated:
        sequence = current_sequence + 1
    else:
        sequence = _integer(supplied_sequence, "operation_sequence", 1)

    if sequence <= current_sequence:
        raise MechanicError(f"stale operation_sequence: {sequence}; current is {current_sequence}")
    if sequence != current_sequence + 1:
        raise MechanicError(f"operation_sequence gap: expected {current_sequence + 1}, found {sequence}")

    raw_expected_revision = payload.get("expected_revision", normalized["revision"] if migrated else None)
    expected_revision = _integer(raw_expected_revision, "expected_revision", 0)
    if expected_revision != normalized["revision"]:
        raise MechanicError(f"revision mismatch: expected {expected_revision}, found {normalized['revision']}")
    raw_expected_continuity = payload.get(
        "expected_continuity_revision", normalized["continuity_revision"] if migrated else None
    )
    expected_continuity = _integer(raw_expected_continuity, "expected_continuity_revision", 0)
    if expected_continuity != normalized["continuity_revision"]:
        raise MechanicError(
            f"continuity revision mismatch: expected {expected_continuity}, found {normalized['continuity_revision']}"
        )
    resulting_continuity = payload.get("resulting_continuity_revision", expected_continuity)
    resulting_continuity = _integer(resulting_continuity, "resulting_continuity_revision", expected_continuity)

    operation = payload.get("operation")
    if operation not in SUPPORTED_OPERATIONS:
        raise MechanicError("unsupported operation")
    updated = copy.deepcopy(normalized)
    changes: list[dict[str, Any]] = []
    if operation == "advance_time":
        _advance_time(updated, payload, changes)
    elif operation in {"advance_clock", "set_clock"}:
        clock_id = _identifier(payload.get("clock_id"), "clock_id")
        clock = _clock(updated, clock_id)
        before = clock["current"]
        if operation == "advance_clock":
            amount = _integer(payload.get("amount", 1), "amount", 0)
            after = min(clock["maximum"], before + amount)
        else:
            after = _integer(payload.get("value"), "value", 0, clock["maximum"])
        clock["current"] = after
        changes.append({"kind": "clock", "clock": clock_id, "before": before, "after": after})
    else:
        _apply_actor_operation(updated, operation, payload, changes)

    updated["revision"] += 1
    updated["continuity_revision"] = resulting_continuity
    updated["operation_sequence"] = sequence
    updated["operation_registry"][operation_id] = {
        "sequence": sequence,
        "revision": updated["revision"],
        "request_hash": request_hash,
    }
    updated["last_operation"] = {
        "sequence": sequence,
        "operation_id": operation_id,
        "revision": updated["revision"],
        "request_hash": request_hash,
    }
    _validate_state(updated)
    return updated, {
        "ok": True,
        "duplicate": False,
        "migrated_from_schema_v1": migrated,
        "operation_id": operation_id,
        "operation_sequence": sequence,
        "revision": updated["revision"],
        "continuity_revision": updated["continuity_revision"],
        "changes": changes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state_path", help="Path to mechanics_state.json.")
    parser.add_argument("--input-json", required=True, help="Mechanic operation as one JSON object.")
    args = parser.parse_args(argv)
    path = Path(args.state_path).resolve()
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        payload = json.loads(args.input_json)
        if not isinstance(state, dict) or not isinstance(payload, dict):
            raise MechanicError("state and input must be JSON objects")
        updated, result = apply_operation(state, payload)
        if not result["duplicate"]:
            _atomic_write(path, updated)
    except (OSError, json.JSONDecodeError, MechanicError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

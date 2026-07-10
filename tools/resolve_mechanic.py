"""Apply optional deterministic resource, ability, cooldown, and time updates."""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


MAX_OPERATION_HISTORY = 200


class MechanicError(ValueError):
    pass


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


def _integer(value: Any, name: str, minimum: int | None = None) -> int:
    if isinstance(value, bool):
        raise MechanicError(f"{name} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise MechanicError(f"{name} must be an integer") from exc
    if minimum is not None and parsed < minimum:
        raise MechanicError(f"{name} must be at least {minimum}")
    return parsed


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
        resource[key] = _integer(resource.get(key), f"{resource_id}.{key}")
    if resource["minimum"] > resource["maximum"]:
        raise MechanicError(f"{resource_id} minimum exceeds maximum")
    if not resource["minimum"] <= resource["current"] <= resource["maximum"]:
        raise MechanicError(f"{resource_id} current is outside its bounds")
    return resource


def _change_resource(
    actor: dict[str, Any], resource_id: str, amount: int, changes: list[dict[str, Any]]
) -> None:
    resource = _resource(actor, resource_id)
    before = resource["current"]
    after = before + amount
    if after < resource["minimum"]:
        raise MechanicError(f"insufficient {resource_id}")
    after = min(after, resource["maximum"])
    resource["current"] = after
    changes.append({"kind": "resource", "resource": resource_id, "before": before, "after": after})


def _use(actor: dict[str, Any], payload: dict[str, Any], changes: list[dict[str, Any]]) -> None:
    action_id = payload.get("action_id")
    abilities = actor.get("abilities")
    if not isinstance(action_id, str) or not action_id:
        raise MechanicError("action_id is required for use")
    if not isinstance(abilities, dict) or action_id not in abilities or not isinstance(abilities[action_id], dict):
        raise MechanicError(f"unknown ability: {action_id}")

    ability = abilities[action_id]
    if ability.get("known") is not True:
        raise MechanicError(f"ability is not known: {action_id}")

    cooldown = ability.get("cooldown")
    if isinstance(cooldown, dict):
        remaining = _integer(cooldown.get("remaining", 0), f"{action_id}.cooldown.remaining", 0)
        if remaining > 0:
            raise MechanicError(f"ability is on cooldown: {action_id}")

    costs = ability.get("costs", {})
    if not isinstance(costs, dict):
        raise MechanicError(f"ability costs must be an object: {action_id}")
    for resource_id, raw_cost in costs.items():
        cost = _integer(raw_cost, f"{action_id}.costs.{resource_id}", 0)
        resource = _resource(actor, resource_id)
        if resource["current"] - cost < resource["minimum"]:
            raise MechanicError(f"insufficient {resource_id}")

    for resource_id, raw_cost in costs.items():
        _change_resource(actor, resource_id, -_integer(raw_cost, "cost", 0), changes)

    if isinstance(cooldown, dict):
        duration = _integer(cooldown.get("duration", 0), f"{action_id}.cooldown.duration", 0)
        before = _integer(cooldown.get("remaining", 0), f"{action_id}.cooldown.remaining", 0)
        cooldown["remaining"] = duration
        changes.append({"kind": "cooldown", "ability": action_id, "before": before, "after": duration})


def _advance_time(state: dict[str, Any], payload: dict[str, Any], changes: list[dict[str, Any]]) -> None:
    steps = _integer(payload.get("steps", 1), "steps", 1)
    unit = payload.get("unit")
    if not isinstance(unit, str) or not unit:
        raise MechanicError("unit is required for advance_time")

    actors = state.get("actors", {})
    if not isinstance(actors, dict):
        raise MechanicError("actors must be an object")

    for actor_id, actor in actors.items():
        if not isinstance(actor, dict):
            continue
        resources = actor.get("resources", {})
        if isinstance(resources, dict):
            for resource_id, resource in resources.items():
                if not isinstance(resource, dict):
                    continue
                regen = resource.get("regen")
                if isinstance(regen, dict) and regen.get("unit") == unit:
                    amount = _integer(regen.get("amount", 0), f"{resource_id}.regen.amount", 0) * steps
                    local_changes: list[dict[str, Any]] = []
                    _change_resource(actor, resource_id, amount, local_changes)
                    for change in local_changes:
                        change["actor"] = actor_id
                    changes.extend(local_changes)

        abilities = actor.get("abilities", {})
        if isinstance(abilities, dict):
            for ability_id, ability in abilities.items():
                if not isinstance(ability, dict):
                    continue
                cooldown = ability.get("cooldown")
                if not isinstance(cooldown, dict) or cooldown.get("unit") != unit:
                    continue
                before = _integer(cooldown.get("remaining", 0), f"{ability_id}.cooldown.remaining", 0)
                after = max(0, before - steps)
                if after != before:
                    cooldown["remaining"] = after
                    changes.append(
                        {
                            "kind": "cooldown",
                            "actor": actor_id,
                            "ability": ability_id,
                            "before": before,
                            "after": after,
                        }
                    )


def apply_operation(state: dict[str, Any], payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if state.get("enabled") is not True:
        raise MechanicError("deterministic mechanics are not enabled for this campaign")

    operation_id = payload.get("operation_id")
    if not isinstance(operation_id, str) or not operation_id.strip():
        raise MechanicError("operation_id must be a non-empty string")

    applied = state.setdefault("applied_operations", [])
    if not isinstance(applied, list):
        raise MechanicError("applied_operations must be a list")
    if operation_id in applied:
        return state, {
            "ok": True,
            "duplicate": True,
            "operation_id": operation_id,
            "revision": state.get("revision", 0),
            "changes": [],
        }

    revision = _integer(state.get("revision", 0), "revision", 0)
    expected = payload.get("expected_revision")
    if expected is not None and _integer(expected, "expected_revision", 0) != revision:
        raise MechanicError(f"revision mismatch: expected {expected}, found {revision}")

    operation = payload.get("operation")
    if operation not in {"use", "spend", "gain", "set", "advance_time"}:
        raise MechanicError("operation must be use, spend, gain, set, or advance_time")

    updated = copy.deepcopy(state)
    changes: list[dict[str, Any]] = []
    if operation == "advance_time":
        _advance_time(updated, payload, changes)
    else:
        actor_id = payload.get("actor_id")
        if not isinstance(actor_id, str) or not actor_id:
            raise MechanicError("actor_id is required")
        actor = _actor(updated, actor_id)
        if operation == "use":
            _use(actor, payload, changes)
        else:
            resource_id = payload.get("resource_id")
            if not isinstance(resource_id, str) or not resource_id:
                raise MechanicError("resource_id is required")
            resource = _resource(actor, resource_id)
            before = resource["current"]
            if operation == "spend":
                _change_resource(actor, resource_id, -_integer(payload.get("amount"), "amount", 0), changes)
            elif operation == "gain":
                _change_resource(actor, resource_id, _integer(payload.get("amount"), "amount", 0), changes)
            else:
                value = _integer(payload.get("value"), "value")
                if not resource["minimum"] <= value <= resource["maximum"]:
                    raise MechanicError(f"value for {resource_id} is outside its bounds")
                resource["current"] = value
                changes.append({"kind": "resource", "resource": resource_id, "before": before, "after": value})

    updated["revision"] = revision + 1
    updated.setdefault("applied_operations", []).append(operation_id)
    updated["applied_operations"] = updated["applied_operations"][-MAX_OPERATION_HISTORY:]
    return updated, {
        "ok": True,
        "duplicate": False,
        "operation_id": operation_id,
        "revision": updated["revision"],
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

"""Apply small deterministic campaign mechanics without deciding narrative outcomes.

Schema v2 uses a monotonic ``operation_sequence``.  A retry of the most recent
operation is idempotent; older or out-of-order operations are rejected instead
of becoming valid again after a bounded id history rolls over.

Downtime support (all optional, so older v2 ledgers stay valid unchanged):

- A clock may carry ``owner`` (one line), ``tick: {unit, amount}`` and
  ``on_fill`` (one line).  ``advance_time`` ticks every clock whose tick unit
  matches, capped at its maximum, and marks the change ``filled`` when the
  clock reaches its maximum.  ``add_clock`` starts a new clock during play and
  ``remove_clock`` retires a resolved one, reporting the clock it removed.
- ``obligations`` records recurring costs such as wages or rent, paid from
  one holding of the actor: a resource (``resource_id``) or an inventory item
  counted by quantity (``item_id``), such as coins kept in a purse.
  ``settle_obligation`` spends from that holding at most once per
  period key, so a time skip cannot charge the same wages twice.  A key is
  stored trimmed and NFC-normalised as given, and compared without case or
  compatibility differences: "Week-3", "week-3" and a fullwidth or no-break
  space variant name the same period.  The comparison is the same in every
  language and locale because every dotted and dotless i (I, i, the Turkish
  capital dotted I and dotless i) folds to a plain "i" first.

The helper never decides what a filled clock or an unpaid debt means in the
fiction; it only reports the numbers.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2
MAX_LINE_TEXT = 2_000
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
    "add_clock",
    "advance_clock",
    "set_clock",
    "remove_clock",
    "advance_time",
    "add_obligation",
    "settle_obligation",
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


def _one_line(value: Any, name: str) -> str:
    text = _identifier(value, name)
    # splitlines() also catches \v, \f, \x1c-\x1e, \x85, U+2028 and U+2029.
    if len(text.splitlines()) != 1:
        raise MechanicError(f"{name} must be one line")
    if len(text) > MAX_LINE_TEXT:
        raise MechanicError(f"{name} exceeds {MAX_LINE_TEXT} characters")
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        raise MechanicError(f"{name} must be valid Unicode text (it contains a lone surrogate)") from None
    return text


def _brief(value: Any) -> str:
    """A bounded repr for error messages about arbitrary input values."""
    text = repr(value)
    return text if len(text) <= 80 else f"{text[:77]}..."


def _id_list(container: Any) -> str:
    """Up to ten sorted ids of a mapping for an error message; empty when it holds none."""
    ids = sorted(str(key) for key in container) if isinstance(container, dict) else []
    return ", ".join(ids[:10]) + (", ..." if len(ids) > 10 else "")


def _period_key(value: Any, name: str) -> str:
    """Return a settled-period key as it is stored: trimmed, one line, NFC."""
    key = unicodedata.normalize("NFC", _one_line(value, name))
    # NFC can lengthen a few strings, so the cap applies to the stored form.
    if len(key) > MAX_LINE_TEXT:
        raise MechanicError(f"{name} exceeds {MAX_LINE_TEXT} characters")
    return key


# Locales disagree about the letter i: Turkish pairs I with dotless i and the
# dotted capital I with i.  Folding all of them to "i" keeps one rule for all.
_DOTLESS_I = str.maketrans({"I": "i", "\N{LATIN SMALL LETTER DOTLESS I}": "i"})


def _period_fold(key: str) -> str:
    """Comparison form of a period key: caseless and the same in every locale."""
    # NFKD splits the dotted capital I into I + a combining dot (dropped below) and
    # maps compatibility forms, such as a no-break space, to their plain letters.
    text = unicodedata.normalize("NFKD", key).translate(_DOTLESS_I).casefold()
    return unicodedata.normalize("NFKC", text.replace("i\N{COMBINING DOT ABOVE}", "i"))


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
    if not isinstance(clocks, dict) or clock_id not in clocks:
        known = _id_list(clocks)
        hint = f"known: {known}" if known else "no clocks are recorded"
        raise MechanicError(f"unknown clock: {clock_id} ({hint})")
    clock = clocks[clock_id]
    if not isinstance(clock, dict):
        raise MechanicError(f"clock {clock_id} must be an object")
    current = _integer(clock.get("current"), f"{clock_id}.current", 0)
    maximum = _integer(clock.get("maximum"), f"{clock_id}.maximum", 1)
    if current > maximum:
        raise MechanicError(f"{clock_id}.current exceeds maximum")
    # Optional downtime fields; a null value counts as absent.
    if clock.get("owner") is not None:
        _one_line(clock["owner"], f"{clock_id}.owner")
    if clock.get("on_fill") is not None:
        _one_line(clock["on_fill"], f"{clock_id}.on_fill")
    tick = clock.get("tick")
    if tick is not None:
        if not isinstance(tick, dict):
            raise MechanicError(f"{clock_id}.tick must be an object")
        _identifier(tick.get("unit"), f"{clock_id}.tick.unit")
        _integer(tick.get("amount"), f"{clock_id}.tick.amount", 1)
    return clock


def _clock_change(clock_id: str, clock: dict[str, Any], before: int, after: int) -> dict[str, Any]:
    """Describe one clock movement; ``filled`` appears only when it reaches its maximum."""
    change: dict[str, Any] = {"kind": "clock", "clock": clock_id, "before": before, "after": after}
    if clock.get("owner") is not None:
        change["owner"] = clock["owner"]
    if after == clock["maximum"] and before < after:
        change["filled"] = True
        if clock.get("on_fill") is not None:
            change["on_fill"] = clock["on_fill"]
    return change


# An obligation spends from exactly one holding of its actor: a resource with
# bounds, or an inventory item counted by quantity (coins kept in a purse).
SPEND_KEYS = ("resource_id", "item_id")


def _spend_target(source: dict[str, Any], prefix: str, owner: str) -> tuple[str, str]:
    """``(key, id)`` of the holding named by exactly one of resource_id or item_id.

    A null value counts as absent, like the other optional fields.
    """
    keys = [key for key in SPEND_KEYS if source.get(key) is not None]
    if len(keys) != 1:
        given = "both are given" if keys else "neither is given"
        raise MechanicError(f"{owner} needs exactly one of resource_id or item_id; {given}")
    return keys[0], _identifier(source[keys[0]], f"{prefix}{keys[0]}")


def _holding(actor_id: str, actor: dict[str, Any], key: str, holding_id: str) -> dict[str, Any]:
    """The validated resource or inventory item an obligation spends from.

    An unknown id names what the actor does hold and, when the id belongs to
    the other kind of holding, the key that names it: money kept as an
    inventory item is an ``item_id``, not a ``resource_id``.
    """
    is_resource = key == "resource_id"
    held = actor.get("resources" if is_resource else "inventory")
    if isinstance(held, dict) and holding_id in held:
        return _resource(actor, holding_id) if is_resource else _item(actor, holding_id)
    message = (
        f"unknown {'resource' if is_resource else 'item'}: {holding_id} "
        f"({actor_id} has resources: {_id_list(actor.get('resources')) or 'none'}; "
        f"items: {_id_list(actor.get('inventory')) or 'none'})"
    )
    elsewhere = actor.get("inventory" if is_resource else "resources")
    if isinstance(elsewhere, dict) and holding_id in elsewhere:
        kind, other_key = ("an inventory item", "item_id") if is_resource else ("a resource", "resource_id")
        message += f"; {holding_id} is {kind}, so name it with {other_key}"
    raise MechanicError(message)


def _obligation(state: dict[str, Any], obligation_id: str) -> dict[str, Any]:
    obligations = state.get("obligations")
    if not isinstance(obligations, dict) or obligation_id not in obligations:
        # Name the recorded ids: a settlement often comes long after the obligation was added.
        known = _id_list(obligations)
        hint = f"known: {known}" if known else "no obligations are recorded"
        raise MechanicError(f"unknown obligation: {obligation_id} ({hint})")
    record = obligations[obligation_id]
    if not isinstance(record, dict):
        raise MechanicError(f"obligation {obligation_id} must be an object")
    _identifier(record.get("actor_id"), f"{obligation_id}.actor_id")
    _spend_target(record, f"{obligation_id}.", f"obligation {obligation_id}")
    _integer(record.get("amount"), f"{obligation_id}.amount", 0)
    _one_line(record.get("period_label"), f"{obligation_id}.period_label")
    settled = record.get("settled")
    if not isinstance(settled, list):
        raise MechanicError(f"{obligation_id}.settled must be a list of non-empty strings")
    seen: dict[str, str] = {}
    for index, period in enumerate(settled):
        key = _period_key(period, f"{obligation_id}.settled[{index}]")
        folded = _period_fold(key)
        if folded in seen:
            raise MechanicError(
                f"{obligation_id}.settled contains duplicate periods: {seen[folded]!r} and {key!r} are the same period"
            )
        seen[folded] = key
    return record


def _settled_periods(record: dict[str, Any]) -> dict[str, str]:
    """Map each settled period's comparison form to its stored key (already validated)."""
    keys = (unicodedata.normalize("NFC", period.strip()) for period in record["settled"])
    return {_period_fold(key): key for key in keys}


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
    obligations = state.get("obligations", {})
    if not isinstance(obligations, dict):
        raise MechanicError("obligations must be an object")
    for obligation_id in obligations:
        _identifier(obligation_id, "obligation id")
        _obligation(state, obligation_id)
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

    for clock_id, clock in state.get("clocks", {}).items():
        tick = clock.get("tick")
        # The unit was validated as non-empty text; a hand-padded " day" still ticks.
        if not isinstance(tick, dict) or tick["unit"].strip() != unit:
            continue
        before = clock["current"]
        after = min(clock["maximum"], before + tick["amount"] * steps)
        if after != before:
            clock["current"] = after
            change = _clock_change(clock_id, clock, before, after)
            change["reason"] = "tick"
            changes.append(change)


def _add_obligation(state: dict[str, Any], payload: dict[str, Any], changes: list[dict[str, Any]]) -> None:
    obligation_id = _one_line(payload.get("obligation_id"), "obligation_id")
    actor_id = _identifier(payload.get("actor_id"), "actor_id")
    key, holding_id = _spend_target(payload, "", "add_obligation")
    _holding(actor_id, _actor(state, actor_id), key, holding_id)
    amount = _integer(payload.get("amount"), "amount", 0)
    period_label = _one_line(payload.get("period_label"), "period_label")
    obligations = state.setdefault("obligations", {})
    if obligation_id in obligations:
        raise MechanicError(f"obligation already exists: {obligation_id}")
    record = {
        "actor_id": actor_id,
        key: holding_id,
        "amount": amount,
        "period_label": period_label,
        "settled": [],
    }
    obligations[obligation_id] = record
    changes.append(
        {"kind": "obligation_added", "obligation": obligation_id, "actor": actor_id, "after": copy.deepcopy(record)}
    )


def _settle_obligation(state: dict[str, Any], payload: dict[str, Any], changes: list[dict[str, Any]]) -> None:
    obligation_id = _identifier(payload.get("obligation_id"), "obligation_id")
    record = _obligation(state, obligation_id)
    period = _period_key(payload.get("period"), "period")
    recorded = _settled_periods(record).get(_period_fold(period))
    if recorded is not None:
        as_recorded = "" if recorded == period else f" (recorded as {recorded!r})"
        raise MechanicError(f"obligation {obligation_id} is already settled for period {period!r}{as_recorded}")
    # A null override counts as absent, like the optional clock fields.
    raw_amount = payload.get("amount")
    amount = record["amount"] if raw_amount is None else _integer(raw_amount, "amount", 0)
    actor_id = record["actor_id"].strip()
    key, holding_id = _spend_target(record, f"{obligation_id}.", f"obligation {obligation_id}")
    try:
        actor = _actor(state, actor_id)
        holding = _holding(actor_id, actor, key, holding_id)
    except MechanicError as exc:
        raise MechanicError(f"obligation {obligation_id} cannot be settled: {exc}") from None
    if key == "resource_id":
        has, floor = holding["current"], holding["minimum"]
        numbers = f"has {has} (minimum {floor})"
    else:
        # An item is counted, so its quantity may reach 0 but never go below it.
        has, floor = holding["quantity"], 0
        numbers = f"has {has}"
    if has - amount < floor:
        raise MechanicError(
            f"insufficient {holding_id} to settle {obligation_id} for period {period!r}: "
            f"needs {amount}, {numbers}, short {amount - (has - floor)}"
        )
    local: list[dict[str, Any]] = []
    if key == "resource_id":
        _change_resource(actor, holding_id, -amount, local)
    else:
        _change_item(actor, holding_id, -amount, local)
    for change in local:
        change["actor"] = actor_id
    changes.extend(local)
    record["settled"].append(period)
    changes.append(
        {
            "kind": "obligation_settled",
            "obligation": obligation_id,
            "actor": actor_id,
            ("resource" if key == "resource_id" else "item"): holding_id,
            "period": period,
            "amount": amount,
        }
    )


def _add_clock(state: dict[str, Any], payload: dict[str, Any], changes: list[dict[str, Any]]) -> None:
    """Start a clock during play, such as a threat that begins ticking mid-scene."""
    clock_id = _one_line(payload.get("clock_id"), "clock_id")
    clocks = state.setdefault("clocks", {})
    if clock_id in clocks:
        raise MechanicError(f"clock already exists: {clock_id}")
    maximum = _integer(payload.get("maximum"), "maximum", 1)
    # The optional fields follow a stored clock: a null value counts as absent.
    current = payload.get("current")
    clock: dict[str, Any] = {
        "current": 0 if current is None else _integer(current, "current", 0, maximum),
        "maximum": maximum,
    }
    if payload.get("owner") is not None:
        clock["owner"] = _one_line(payload["owner"], "owner")
    tick = payload.get("tick")
    if tick is not None:
        if not isinstance(tick, dict):
            raise MechanicError("tick must be an object with unit and amount")
        extra = sorted(str(name) for name in tick if name not in ("unit", "amount"))
        if extra:
            # A stray key such as "every" would otherwise be dropped while the GM relies on it.
            raise MechanicError(f"tick takes only unit and amount, not {', '.join(extra)}")
        clock["tick"] = {
            "unit": _identifier(tick.get("unit"), "tick.unit"),
            "amount": _integer(tick.get("amount"), "tick.amount", 1),
        }
    if payload.get("on_fill") is not None:
        clock["on_fill"] = _one_line(payload["on_fill"], "on_fill")
    clocks[clock_id] = clock
    _clock(state, clock_id)  # the same checks every stored clock passes
    changes.append({"kind": "clock_added", "clock": clock_id, "after": copy.deepcopy(clock)})


def _remove_clock(state: dict[str, Any], payload: dict[str, Any], changes: list[dict[str, Any]]) -> None:
    """Retire a clock whose threat is resolved; the change keeps the removed clock."""
    clock_id = _identifier(payload.get("clock_id"), "clock_id")
    _clock(state, clock_id)
    changes.append({"kind": "clock_removed", "clock": clock_id, "before": state["clocks"].pop(clock_id)})


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
    # A list or object here must not reach the set lookup (TypeError, not a typed error).
    if not isinstance(operation, str) or operation not in SUPPORTED_OPERATIONS:
        raise MechanicError(
            f"unsupported operation: {_brief(operation)}; use one of {', '.join(sorted(SUPPORTED_OPERATIONS))}"
        )
    updated = copy.deepcopy(normalized)
    changes: list[dict[str, Any]] = []
    if operation == "advance_time":
        _advance_time(updated, payload, changes)
    elif operation == "add_obligation":
        _add_obligation(updated, payload, changes)
    elif operation == "settle_obligation":
        _settle_obligation(updated, payload, changes)
    elif operation == "add_clock":
        _add_clock(updated, payload, changes)
    elif operation == "remove_clock":
        _remove_clock(updated, payload, changes)
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
        changes.append(_clock_change(clock_id, clock, before, after))
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


def _load_json(text: str, label: str) -> Any:
    """Parse one JSON document; the error names which input was malformed."""
    try:
        return json.loads(text)
    except RecursionError:
        raise MechanicError(f"{label} is not valid JSON: it is nested too deeply") from None
    except ValueError as exc:  # JSONDecodeError, or an integer literal too long to convert
        raise MechanicError(f"{label} is not valid JSON: {exc}") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state_path", help="Path to mechanics_state.json.")
    parser.add_argument("--input-json", required=True, help="Mechanic operation as one JSON object.")
    args = parser.parse_args(argv)
    path = Path(args.state_path).resolve()
    try:
        try:
            # utf-8-sig tolerates a BOM left by Windows editors; the rewrite drops it.
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as exc:
            raise MechanicError(
                f"{path.name} is not valid UTF-8 ({exc.reason} at byte {exc.start}); re-save it as UTF-8"
            ) from None
        state = _load_json(text, path.name)
        payload = _load_json(args.input_json, "--input-json")
        if not isinstance(state, dict):
            raise MechanicError(f"{path.name} must contain a JSON object")
        if not isinstance(payload, dict):
            raise MechanicError("--input-json must be a JSON object")
        updated, result = apply_operation(state, payload)
        if not result["duplicate"]:
            _atomic_write(path, updated)
    except RecursionError:
        # A pathologically nested ledger can still exhaust the stack while it is copied.
        print(json.dumps({"ok": False, "error": f"{path.name} or --input-json is nested too deeply"}, indent=2))
        return 2
    except (OSError, ValueError) as exc:  # MechanicError is a ValueError
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

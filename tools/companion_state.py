"""Inspect and atomically update RePoG Companion runtime state.

The helper is deliberately semantic-free.  It measures elapsed wall time,
enforces revisions/idempotency, and commits model-authored bounded patches.
It never invents a life event, relationship judgment, or player-facing text.

Schema v2 makes the fast path explicit: ``begin-exchange`` calculates the
*previous* absence and records the user's new contact in one atomic write.
``commit-semantic`` is only needed when the exchange creates durable meaning.
The four v1 command names remain available as compatibility entry points.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


STATE_FILE = "companion_state.json"
MAX_OPERATION_IDS = 256
MAX_ATTENTION = 3
MAX_TENSIONS = 3
MAX_EVIDENCE = 8
MAX_BOUNDARY_REFS = 8

PRESENCE_KEYS = {
    "as_of",
    "place_ref",
    "activity",
    "with_refs",
    "availability",
    "expected_until",
    "source",
}
CONDITION_KEYS = {
    "as_of",
    "energy",
    "social_bandwidth",
    "emotional_weather",
    "active_preoccupation",
    "cause_ref",
    "reevaluate_after",
}
RELATIONAL_KEYS = {
    "companion_posture",
    "reciprocity_pattern",
    "boundary_refs",
    "active_tensions",
    "recent_evidence",
    "last_change_evidence_id",
}
STATE_PATCH_KEYS = {
    "current_presence",
    "current_condition",
    "attention_queue",
    "relational_context",
    "pending_transition",
}
TENSION_KEYS = {"tension_id", "summary", "source_ref", "status"}
EVIDENCE_KEYS = {
    "evidence_id",
    "dimension",
    "direction",
    "interpretation",
    "source_ref",
    "observed_at",
}
ATTENTION_KEYS = {"attention_id", "kind", "subject_ref", "due_at", "source_ref"}
AVAILABILITY = {"unknown", "available", "limited", "busy", "asleep", "offline"}
ENERGY = {"unknown", "low", "steady", "high", "depleted"}
SOCIAL_BANDWIDTH = {"unknown", "closed", "limited", "open"}
ATTENTION_KINDS = {"callback", "life_domain", "user_event", "shared_plan"}
TENSION_STATUSES = {"active", "repairing"}
EVIDENCE_DIMENSIONS = {
    "reliability",
    "candor",
    "emotional_safety",
    "shared_humor",
    "boundary_respect",
    "attraction",
    "rivalry",
    "other",
}
EVIDENCE_DIRECTIONS = {"strengthened", "weakened", "ambiguous"}
GAP_BANDS = {"same_window", "routine", "ordinary_days", "compressed_days", "long_gap"}


class CompanionStateError(ValueError):
    """Typed, user-readable state failure."""


def _strict_int(value: Any, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parse_iso(value: Any, *, field: str, nullable: bool = True) -> datetime | None:
    if value is None and nullable:
        return None
    if not _nonempty(value):
        raise CompanionStateError(f"{field} must be a timezone-aware ISO timestamp")
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CompanionStateError(f"{field} is not a valid ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CompanionStateError(f"{field} must include a UTC offset")
    return parsed


def _offset_timezone(raw: str) -> timezone | None:
    raw = raw.strip()
    if not raw:
        return None
    if raw.upper() in {"UTC", "Z", "+00:00", "-00:00"}:
        return timezone.utc
    match = re.fullmatch(r"([+-])(\d{2}):(\d{2})", raw)
    if not match:
        raise CompanionStateError("configured_utc_offset must use +HH:MM or -HH:MM")
    hours, minutes = int(match.group(2)), int(match.group(3))
    if hours > 14 or minutes > 59 or (hours == 14 and minutes):
        raise CompanionStateError("configured_utc_offset is outside the supported range")
    delta = timedelta(hours=hours, minutes=minutes)
    if match.group(1) == "-":
        delta = -delta
    return timezone(delta)


def _now(state: dict[str, Any], override: str | None) -> datetime:
    if override:
        parsed = _parse_iso(override, field="--now", nullable=False)
        assert parsed is not None
        return parsed
    timezone_name = str(state.get("configured_timezone", "")).strip()
    if timezone_name:
        try:
            return datetime.now(tz=ZoneInfo(timezone_name))
        except ZoneInfoNotFoundError:
            pass
    offset = _offset_timezone(str(state.get("configured_utc_offset", "")))
    return datetime.now(tz=offset) if offset else datetime.now().astimezone()


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _load(campaign: Path) -> tuple[Path, dict[str, Any]]:
    path = campaign.resolve() / STATE_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CompanionStateError(f"missing {STATE_FILE}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise CompanionStateError(f"cannot read {STATE_FILE}: {exc}") from exc
    if not isinstance(data, dict):
        raise CompanionStateError(f"{STATE_FILE} must contain a JSON object")
    return path, data


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        finally:
            raise


def _serialized(data: dict[str, Any]) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _write_temp(path: Path, payload: bytes) -> Path:
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        return temp_path
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _restore_bytes(path: Path, payload: bytes) -> None:
    temp_path = _write_temp(path, payload)
    try:
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _atomic_commit_pair(
    state_path: Path,
    state_data: dict[str, Any],
    view_path: Path,
    view_data: dict[str, Any],
) -> None:
    """Commit state + public projection together, rolling both back on failure."""

    try:
        old_state = state_path.read_bytes()
        old_view = view_path.read_bytes()
    except OSError as exc:
        raise CompanionStateError(f"cannot stage Companion/View transaction: {exc}") from exc
    state_temp = _write_temp(state_path, _serialized(state_data))
    try:
        view_temp = _write_temp(view_path, _serialized(view_data))
    except Exception:
        state_temp.unlink(missing_ok=True)
        raise
    state_replaced = False
    view_replaced = False
    try:
        # Projection first prevents the canonical state from advertising a
        # revision which was never materialized.  Any second-step failure is
        # immediately restored from the byte-exact snapshots above.
        os.replace(view_temp, view_path)
        view_replaced = True
        os.replace(state_temp, state_path)
        state_replaced = True
    except Exception as exc:
        rollback_errors: list[str] = []
        if state_replaced:
            try:
                _restore_bytes(state_path, old_state)
            except Exception as rollback_exc:  # pragma: no cover - OS fault path
                rollback_errors.append(f"state rollback failed: {rollback_exc}")
        if view_replaced:
            try:
                _restore_bytes(view_path, old_view)
            except Exception as rollback_exc:  # pragma: no cover - OS fault path
                rollback_errors.append(f"view rollback failed: {rollback_exc}")
        detail = f"Companion/View transaction failed: {exc}"
        if rollback_errors:
            detail += "; " + "; ".join(rollback_errors)
        raise CompanionStateError(detail) from exc
    finally:
        state_temp.unlink(missing_ok=True)
        view_temp.unlink(missing_ok=True)


def _yaml_scalar(path: Path, key: str) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CompanionStateError(f"cannot read {path.name}: {exc}") from exc
    match = re.search(rf"(?m)^\s*{re.escape(key)}:\s*(.*?)\s*$", text)
    if match is None:
        return ""
    return match.group(1).strip().strip("\"'")


def _companion_view_expected(campaign: Path) -> bool:
    setup = campaign / "setup_profile.yaml"
    profile = campaign / "companion_profile.yaml"
    return (
        _yaml_scalar(setup, "experience_mode") == "companion"
        and _yaml_scalar(setup, "ready_for_play").casefold() == "true"
        and _yaml_scalar(profile, "profile_status") == "locked"
        and _yaml_scalar(profile, "companion_view") == "light"
    )


def _load_view(campaign: Path) -> tuple[Path, dict[str, Any]]:
    path = campaign / "companion_view" / "companion_view_state.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CompanionStateError("Companion View is enabled but its state file is missing") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CompanionStateError(f"cannot read Companion View state: {exc}") from exc
    if not isinstance(data, dict):
        raise CompanionStateError("Companion View state must be a JSON object")
    return path, data


def _apply_public_patch(view: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    allowed = {"identity", "local_clock", "last_shared_status", "shared_cards"}
    unknown = sorted(set(patch) - allowed)
    if unknown:
        raise CompanionStateError(f"unsupported public patch fields: {', '.join(unknown)}")
    candidate = copy.deepcopy(view)
    for key, value in patch.items():
        if key == "identity":
            if not isinstance(value, dict):
                raise CompanionStateError("public identity patch must be an object")
            candidate["identity"] = {**candidate.get("identity", {}), **copy.deepcopy(value)}
        else:
            candidate[key] = copy.deepcopy(value)
    return candidate


def _validate_public_candidate(campaign: Path, path: Path, candidate: dict[str, Any]) -> None:
    checker_path = Path(__file__).with_name("check_companion_view.py")
    if not checker_path.is_file():
        raise CompanionStateError("Companion View checker is missing")
    spec = importlib.util.spec_from_file_location("repog_companion_view_commit_contract", checker_path)
    if spec is None or spec.loader is None:
        raise CompanionStateError("Companion View checker could not be loaded")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        result = module.check_companion_view_data(
            candidate,
            path,
            campaign_path=campaign,
            require_assets=False,
        )
    except Exception as exc:
        raise CompanionStateError(f"Companion View validation failed: {exc}") from exc
    errors = [item for item in result.get("findings", []) if item.get("severity") == "error"]
    if errors:
        first = errors[0]
        raise CompanionStateError(
            f"Companion View patch rejected ({first.get('rule', 'invalid')}): {first.get('message', 'invalid projection')}"
        )


def _gap_band(elapsed_minutes: int) -> tuple[str, int, str]:
    if elapsed_minutes < 4 * 60:
        return "same_window", 0, "no automatic montage"
    if elapsed_minutes < 18 * 60:
        return "routine", 1, "at most one minor beat"
    if elapsed_minutes < 72 * 60:
        return "ordinary_days", 1, "at most one meaningful beat"
    if elapsed_minutes <= 14 * 24 * 60:
        return "compressed_days", 2, "at most two bounded beats"
    return "long_gap", 3, "compressed recap, at most three bounded beats"


def _latest_recorded_time(state: dict[str, Any]) -> tuple[datetime | None, str]:
    candidates: list[tuple[datetime, str]] = []
    scalar_fields = ("last_observation_at", "last_user_contact_at")
    for field in scalar_fields:
        if state.get(field):
            parsed = _parse_iso(state[field], field=field, nullable=False)
            assert parsed is not None
            candidates.append((parsed, field))
    nested_fields = (
        ("current_window", "last_exchange_at"),
        ("current_presence", "as_of"),
        ("current_condition", "as_of"),
    )
    for owner, field in nested_fields:
        value = state.get(owner)
        if isinstance(value, dict) and value.get(field):
            parsed = _parse_iso(value[field], field=f"{owner}.{field}", nullable=False)
            assert parsed is not None
            candidates.append((parsed, f"{owner}.{field}"))
    if not candidates:
        return None, ""
    return max(candidates, key=lambda item: item[0].astimezone(timezone.utc))


def _reject_backwards(state: dict[str, Any], now: datetime) -> None:
    latest, field = _latest_recorded_time(state)
    if latest is not None and now.astimezone(timezone.utc) < latest.astimezone(timezone.utc):
        raise CompanionStateError(
            f"backwards time rejected: --now precedes {field} ({_iso(latest)})"
        )


def _due_signals(state: dict[str, Any], now: datetime) -> dict[str, Any]:
    transition = state.get("pending_transition")
    transition_due = False
    transition_id = None
    if isinstance(transition, dict) and transition.get("due_at"):
        due = _parse_iso(transition["due_at"], field="pending_transition.due_at", nullable=False)
        assert due is not None
        transition_due = due.astimezone(timezone.utc) <= now.astimezone(timezone.utc)
        transition_id = transition.get("transition_id") if transition_due else None

    presence = state.get("current_presence")
    presence_review_due = False
    if isinstance(presence, dict) and presence.get("expected_until"):
        due = _parse_iso(presence["expected_until"], field="current_presence.expected_until", nullable=False)
        assert due is not None
        presence_review_due = due.astimezone(timezone.utc) <= now.astimezone(timezone.utc)

    condition = state.get("current_condition")
    condition_review_due = False
    if isinstance(condition, dict) and condition.get("reevaluate_after"):
        due = _parse_iso(condition["reevaluate_after"], field="current_condition.reevaluate_after", nullable=False)
        assert due is not None
        condition_review_due = due.astimezone(timezone.utc) <= now.astimezone(timezone.utc)

    attention_due_ids: list[str] = []
    for item in state.get("attention_queue", []):
        due = _parse_iso(item.get("due_at"), field="attention_queue.due_at", nullable=False)
        assert due is not None
        if due.astimezone(timezone.utc) <= now.astimezone(timezone.utc):
            attention_due_ids.append(item["attention_id"])

    return {
        "pending_transition_due": transition_due,
        "due_transition_id": transition_id,
        "presence_review_due": presence_review_due,
        "condition_review_due": condition_review_due,
        "attention_due_ids": attention_due_ids,
    }


def _inspection(state: dict[str, Any], now: datetime) -> dict[str, Any]:
    _reject_backwards(state, now)
    anchor_raw = state.get("last_user_contact_at") or state.get("last_observation_at")
    anchor = _parse_iso(anchor_raw, field="last_user_contact_at", nullable=False) if anchor_raw else None
    elapsed = 0 if anchor is None else int(
        (now.astimezone(timezone.utc) - anchor.astimezone(timezone.utc)).total_seconds() // 60
    )
    band, ceiling, guidance = _gap_band(elapsed)
    anchor_token = anchor.isoformat() if anchor else "initial"
    gap_id = "gap_" + hashlib.sha256(anchor_token.encode("utf-8")).hexdigest()[:16]
    last_gap = state.get("last_gap") if isinstance(state.get("last_gap"), dict) else {}
    window = state.get("current_window") if isinstance(state.get("current_window"), dict) else {}
    return {
        "now": _iso(now),
        "state_revision": state.get("state_revision"),
        "continuity_revision": state.get("continuity_revision"),
        "public_surface_revision": state.get("public_surface_revision"),
        "interaction_sequence": state.get("interaction_sequence"),
        "semantic_operation_sequence": state.get("semantic_operation_sequence"),
        "gap_id": gap_id,
        "elapsed_minutes": elapsed,
        "gap_band": band,
        "event_ceiling": ceiling,
        "guidance": guidance,
        "already_reconciled": last_gap.get("gap_id") == gap_id,
        "same_conversation_window": band == "same_window" and bool(window.get("window_id")),
        "current_window": window,
        "current_presence": state.get("current_presence"),
        "current_condition": state.get("current_condition"),
        "pending_transition": state.get("pending_transition"),
        "attention_queue": state.get("attention_queue"),
        "relational_context": state.get("relational_context"),
        "signals": _due_signals(state, now),
    }


def _validate_string_list(
    value: Any,
    *,
    field: str,
    limit: int | None = None,
    allow_empty: bool = True,
) -> str | None:
    if not isinstance(value, list):
        return f"{field} must be a list"
    if limit is not None and len(value) > limit:
        return f"{field} may contain at most {limit} entries"
    if any(not _nonempty(item) for item in value):
        return f"{field} must contain non-empty strings"
    if len(value) != len(set(value)):
        return f"{field} must not contain duplicates"
    if not allow_empty and not value:
        return f"{field} must not be empty"
    return None


def validate_state(data: dict[str, Any]) -> list[dict[str, str]]:
    """Return all structural errors for one schema-v2 state document."""

    findings: list[dict[str, str]] = []

    def add(rule: str, message: str) -> None:
        findings.append({"severity": "error", "rule": rule, "message": message})

    if data.get("schema_version") != 2:
        add("companion_state_schema_invalid", "schema_version must be 2")
    numeric = (
        "state_revision",
        "continuity_revision",
        "public_surface_revision",
        "interaction_sequence",
        "semantic_operation_sequence",
    )
    for key in numeric:
        if not _strict_int(data.get(key)):
            add("companion_state_number_invalid", f"{key} must be a non-negative integer")
    if all(_strict_int(data.get(key)) for key in ("state_revision", "continuity_revision", "public_surface_revision")):
        if data["continuity_revision"] > data["state_revision"]:
            add("companion_revision_invalid", "continuity_revision cannot exceed state_revision")
        if data["public_surface_revision"] > data["state_revision"]:
            add("companion_revision_invalid", "public_surface_revision cannot exceed state_revision")

    semantic_sequence = data.get("semantic_operation_sequence")
    semantic_id = data.get("last_semantic_operation_id")
    if _strict_int(semantic_sequence):
        if semantic_sequence == 0 and semantic_id != "":
            add("companion_semantic_sequence_invalid", "sequence 0 requires an empty last_semantic_operation_id")
        if semantic_sequence > 0 and not _nonempty(semantic_id):
            add("companion_semantic_sequence_invalid", "a committed semantic sequence requires its operation id")
    semantic_ledger = data.get("semantic_operation_ledger")
    if not isinstance(semantic_ledger, list):
        add("companion_semantic_ledger_invalid", "semantic_operation_ledger must be a list")
    else:
        ledger_ids: list[str] = []
        for index, entry in enumerate(semantic_ledger):
            if not isinstance(entry, dict) or set(entry) != {"sequence", "operation_id", "payload_hash"}:
                add("companion_semantic_ledger_invalid", f"semantic_operation_ledger[{index}] has an invalid structure")
                continue
            expected_sequence = index + 1
            if entry.get("sequence") != expected_sequence:
                add("companion_semantic_ledger_invalid", "semantic_operation_ledger sequences must be contiguous from 1")
            if not _nonempty(entry.get("operation_id")):
                add("companion_semantic_ledger_invalid", f"semantic_operation_ledger[{index}].operation_id must be non-empty")
            else:
                ledger_ids.append(entry["operation_id"])
            if not isinstance(entry.get("payload_hash"), str) or not re.fullmatch(r"[0-9a-f]{64}", entry["payload_hash"]):
                add("companion_semantic_ledger_invalid", f"semantic_operation_ledger[{index}].payload_hash must be a SHA-256 hex digest")
        if len(ledger_ids) != len(set(ledger_ids)):
            add("companion_semantic_ledger_duplicate", "semantic operation ids are permanent and must be unique")
        if _strict_int(semantic_sequence) and len(semantic_ledger) != semantic_sequence:
            add("companion_semantic_ledger_invalid", "semantic_operation_ledger length must equal semantic_operation_sequence")
        if semantic_ledger and (
            semantic_ledger[-1].get("sequence") != semantic_sequence
            or semantic_ledger[-1].get("operation_id") != semantic_id
        ):
            add("companion_semantic_ledger_invalid", "last semantic ledger entry must match the committed semantic marker")

    try:
        _offset_timezone(str(data.get("configured_utc_offset", "")))
    except CompanionStateError as exc:
        add("companion_offset_invalid", str(exc))
    for key in ("last_observation_at", "last_user_contact_at"):
        try:
            _parse_iso(data.get(key), field=key)
        except CompanionStateError as exc:
            add("companion_timestamp_invalid", str(exc))
    if "last_response_at" in data:
        add("companion_response_time_forbidden", "last_response_at is not observable state and must not be stored")

    window = data.get("current_window")
    if not isinstance(window, dict):
        add("companion_window_invalid", "current_window must be an object")
    else:
        window_id = window.get("window_id")
        if not isinstance(window_id, str):
            add("companion_window_invalid", "current_window.window_id must be a string")
        for key in ("started_at", "last_exchange_at"):
            try:
                _parse_iso(window.get(key), field=f"current_window.{key}")
            except CompanionStateError as exc:
                add("companion_timestamp_invalid", str(exc))
        if window_id and (window.get("started_at") is None or window.get("last_exchange_at") is None):
            add("companion_window_invalid", "an active window requires started_at and last_exchange_at")

    presence = data.get("current_presence")
    if not isinstance(presence, dict):
        add("companion_presence_invalid", "current_presence must be an object")
    else:
        missing = sorted(PRESENCE_KEYS - set(presence))
        unknown = sorted(set(presence) - PRESENCE_KEYS)
        if missing:
            add("companion_presence_invalid", f"current_presence is missing: {', '.join(missing)}")
        if unknown:
            add("companion_presence_invalid", f"current_presence has unsupported fields: {', '.join(unknown)}")
        if presence.get("availability") not in AVAILABILITY:
            add("companion_availability_invalid", "current_presence.availability is invalid")
        problem = _validate_string_list(presence.get("with_refs"), field="current_presence.with_refs")
        if problem:
            add("companion_presence_refs_invalid", problem)
        for key in ("as_of", "expected_until"):
            try:
                _parse_iso(presence.get(key), field=f"current_presence.{key}")
            except CompanionStateError as exc:
                add("companion_timestamp_invalid", str(exc))

    condition = data.get("current_condition")
    if not isinstance(condition, dict):
        add("companion_condition_invalid", "current_condition must be an object")
    else:
        missing = sorted(CONDITION_KEYS - set(condition))
        unknown = sorted(set(condition) - CONDITION_KEYS)
        if missing:
            add("companion_condition_invalid", f"current_condition is missing: {', '.join(missing)}")
        if unknown:
            add("companion_condition_invalid", f"current_condition has unsupported fields: {', '.join(unknown)}")
        if condition.get("energy") not in ENERGY:
            add("companion_condition_invalid", "current_condition.energy is invalid")
        if condition.get("social_bandwidth") not in SOCIAL_BANDWIDTH:
            add("companion_condition_invalid", "current_condition.social_bandwidth is invalid")
        for key in ("as_of", "reevaluate_after"):
            try:
                _parse_iso(condition.get(key), field=f"current_condition.{key}")
            except CompanionStateError as exc:
                add("companion_timestamp_invalid", str(exc))

    queue = data.get("attention_queue")
    if not isinstance(queue, list):
        add("companion_attention_invalid", "attention_queue must be a list")
    elif len(queue) > MAX_ATTENTION:
        add("companion_attention_invalid", f"attention_queue may contain at most {MAX_ATTENTION} entries")
    else:
        ids: list[str] = []
        for index, item in enumerate(queue):
            if not isinstance(item, dict):
                add("companion_attention_invalid", f"attention_queue[{index}] must be an object")
                continue
            if set(item) != ATTENTION_KEYS:
                add("companion_attention_invalid", f"attention_queue[{index}] must contain exactly: {', '.join(sorted(ATTENTION_KEYS))}")
            for key in ("attention_id", "subject_ref", "source_ref"):
                if not _nonempty(item.get(key)):
                    add("companion_attention_invalid", f"attention_queue[{index}].{key} must be non-empty")
            if item.get("kind") not in ATTENTION_KINDS:
                add("companion_attention_invalid", f"attention_queue[{index}].kind is invalid")
            try:
                _parse_iso(item.get("due_at"), field=f"attention_queue[{index}].due_at", nullable=False)
            except CompanionStateError as exc:
                add("companion_timestamp_invalid", str(exc))
            if _nonempty(item.get("attention_id")):
                ids.append(item["attention_id"])
        if len(ids) != len(set(ids)):
            add("companion_attention_duplicate", "attention_queue attention_id values must be unique")

    relationship = data.get("relational_context")
    if not isinstance(relationship, dict):
        add("companion_relationship_invalid", "relational_context must be an object")
    else:
        missing = sorted(RELATIONAL_KEYS - set(relationship))
        unknown = sorted(set(relationship) - RELATIONAL_KEYS)
        if missing:
            add("companion_relationship_invalid", f"relational_context is missing: {', '.join(missing)}")
        if unknown:
            add("companion_relationship_invalid", f"relational_context has unsupported fields: {', '.join(unknown)}")
        for key in ("companion_posture", "reciprocity_pattern"):
            if not _nonempty(relationship.get(key)):
                add("companion_relationship_invalid", f"relational_context.{key} must be non-empty")
        problem = _validate_string_list(
            relationship.get("boundary_refs"), field="relational_context.boundary_refs", limit=MAX_BOUNDARY_REFS
        )
        if problem:
            add("companion_relationship_invalid", problem)

        tensions = relationship.get("active_tensions")
        tension_ids: list[str] = []
        if not isinstance(tensions, list) or len(tensions) > MAX_TENSIONS:
            add("companion_tension_invalid", f"active_tensions must be a list of at most {MAX_TENSIONS}")
        else:
            for index, item in enumerate(tensions):
                if not isinstance(item, dict) or set(item) != TENSION_KEYS:
                    add("companion_tension_invalid", f"active_tensions[{index}] has an invalid structure")
                    continue
                for key in ("tension_id", "summary", "source_ref"):
                    if not _nonempty(item.get(key)):
                        add("companion_tension_invalid", f"active_tensions[{index}].{key} must be non-empty")
                if item.get("status") not in TENSION_STATUSES:
                    add("companion_tension_invalid", f"active_tensions[{index}].status is invalid")
                if _nonempty(item.get("tension_id")):
                    tension_ids.append(item["tension_id"])
            if len(tension_ids) != len(set(tension_ids)):
                add("companion_tension_duplicate", "active_tensions tension_id values must be unique")

        evidence = relationship.get("recent_evidence")
        evidence_ids: list[str] = []
        if not isinstance(evidence, list) or len(evidence) > MAX_EVIDENCE:
            add("companion_evidence_invalid", f"recent_evidence must be a list of at most {MAX_EVIDENCE}")
        else:
            for index, item in enumerate(evidence):
                if not isinstance(item, dict) or set(item) != EVIDENCE_KEYS:
                    add("companion_evidence_invalid", f"recent_evidence[{index}] has an invalid structure")
                    continue
                for key in ("evidence_id", "interpretation", "source_ref"):
                    if not _nonempty(item.get(key)):
                        add("companion_evidence_invalid", f"recent_evidence[{index}].{key} must be non-empty")
                if item.get("dimension") not in EVIDENCE_DIMENSIONS:
                    add("companion_evidence_invalid", f"recent_evidence[{index}].dimension is invalid")
                if item.get("direction") not in EVIDENCE_DIRECTIONS:
                    add("companion_evidence_invalid", f"recent_evidence[{index}].direction is invalid")
                try:
                    _parse_iso(item.get("observed_at"), field=f"recent_evidence[{index}].observed_at", nullable=False)
                except CompanionStateError as exc:
                    add("companion_timestamp_invalid", str(exc))
                if _nonempty(item.get("evidence_id")):
                    evidence_ids.append(item["evidence_id"])
            if len(evidence_ids) != len(set(evidence_ids)):
                add("companion_evidence_duplicate", "recent_evidence evidence_id values must be unique")
        last_change = relationship.get("last_change_evidence_id")
        if not isinstance(last_change, str):
            add("companion_evidence_invalid", "last_change_evidence_id must be a string")
        elif last_change and last_change not in evidence_ids:
            add("companion_evidence_invalid", "last_change_evidence_id must reference recent_evidence")

    transition = data.get("pending_transition")
    if transition is not None:
        if not isinstance(transition, dict):
            add("companion_transition_invalid", "pending_transition must be null or an object")
        else:
            required = {"transition_id", "due_at", "place_ref", "activity", "cause"}
            missing = sorted(key for key in required if not _nonempty(transition.get(key)))
            if missing:
                add("companion_transition_invalid", f"pending_transition is missing: {', '.join(missing)}")
            try:
                _parse_iso(transition.get("due_at"), field="pending_transition.due_at", nullable=False)
            except CompanionStateError as exc:
                add("companion_timestamp_invalid", str(exc))
            if "with_refs" in transition:
                problem = _validate_string_list(transition.get("with_refs"), field="pending_transition.with_refs")
                if problem:
                    add("companion_transition_refs_invalid", problem)

    last_gap = data.get("last_gap")
    if not isinstance(last_gap, dict):
        add("companion_gap_invalid", "last_gap must be an object")
    else:
        if last_gap.get("band") not in GAP_BANDS:
            add("companion_gap_invalid", "last_gap.band is invalid")
        for key in ("elapsed_minutes", "event_ceiling", "reconciled_revision"):
            if not _strict_int(last_gap.get(key)):
                add("companion_gap_invalid", f"last_gap.{key} must be a non-negative integer")
        ceiling = {"same_window": 0, "routine": 1, "ordinary_days": 1, "compressed_days": 2, "long_gap": 3}
        if last_gap.get("band") in ceiling and last_gap.get("event_ceiling") != ceiling[last_gap["band"]]:
            add("companion_gap_ceiling_invalid", "last_gap.event_ceiling does not match its band")
        if _strict_int(last_gap.get("reconciled_revision")) and _strict_int(data.get("continuity_revision")):
            if last_gap["reconciled_revision"] > data["continuity_revision"]:
                add("companion_gap_invalid", "last_gap.reconciled_revision cannot exceed continuity_revision")

    operations = data.get("recent_operation_ids")
    if not isinstance(operations, list) or len(operations) > MAX_OPERATION_IDS:
        add("companion_operations_invalid", f"recent_operation_ids must be a list of at most {MAX_OPERATION_IDS}")
    elif any(not _nonempty(item) for item in operations):
        add("companion_operations_invalid", "recent_operation_ids must contain non-empty strings")
    elif len(operations) != len(set(operations)):
        add("companion_operation_duplicate", "recent_operation_ids must be unique")

    # Chronological consistency is structural even when no operation is run.
    try:
        last_contact = _parse_iso(data.get("last_user_contact_at"), field="last_user_contact_at")
        window_exchange = None
        if isinstance(window, dict):
            window_exchange = _parse_iso(window.get("last_exchange_at"), field="current_window.last_exchange_at")
        if last_contact and window_exchange and last_contact != window_exchange:
            add("companion_window_time_invalid", "last_user_contact_at must equal current_window.last_exchange_at")
    except CompanionStateError:
        pass
    return findings


def _require_clean_state(state: dict[str, Any]) -> None:
    findings = validate_state(state)
    if findings:
        raise CompanionStateError(findings[0]["message"])


def _check_revision(
    state: dict[str, Any],
    expected_state: int,
    expected_continuity: int | None = None,
    expected_public: int | None = None,
) -> None:
    if state.get("state_revision") != expected_state:
        raise CompanionStateError(f"stale state revision: expected {expected_state}, found {state.get('state_revision')}")
    if expected_continuity is not None and state.get("continuity_revision") != expected_continuity:
        raise CompanionStateError(
            f"stale continuity revision: expected {expected_continuity}, found {state.get('continuity_revision')}"
        )
    if expected_public is not None and state.get("public_surface_revision") != expected_public:
        raise CompanionStateError(
            f"stale public surface revision: expected {expected_public}, found {state.get('public_surface_revision')}"
        )


def _require_operation_id(operation_id: str) -> None:
    if not _nonempty(operation_id):
        raise CompanionStateError("operation_id must be a non-empty string")


def _idempotent(state: dict[str, Any], operation_id: str) -> bool:
    return operation_id in state.get("recent_operation_ids", [])


def _record_operation(state: dict[str, Any], operation_id: str) -> None:
    operations = list(state.get("recent_operation_ids", []))
    operations.append(operation_id)
    state["recent_operation_ids"] = operations[-MAX_OPERATION_IDS:]


def _semantic_payload_hash(
    state_patch: dict[str, Any],
    public_patch: dict[str, Any] | None,
    gap_id: str | None,
) -> str:
    canonical = json.dumps(
        {"state_patch": state_patch, "public_patch": public_patch, "gap_id": gap_id},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def inspect(campaign: Path, *, now_override: str | None = None) -> dict[str, Any]:
    _, state = _load(campaign)
    _require_clean_state(state)
    return {"ok": True, "operation": "inspect", **_inspection(state, _now(state, now_override))}


def begin_exchange(
    campaign: Path,
    *,
    operation_id: str,
    expected_state_revision: int,
    expected_continuity_revision: int | None = None,
    now_override: str | None = None,
) -> dict[str, Any]:
    """Measure the prior gap and record this user contact in one write."""

    _require_operation_id(operation_id)
    path, state = _load(campaign)
    _require_clean_state(state)
    if any(
        entry.get("operation_id") == operation_id
        for entry in state["semantic_operation_ledger"]
    ):
        raise CompanionStateError("operation_id is permanently reserved by a semantic operation")
    if _idempotent(state, operation_id):
        gap = state["last_gap"]
        _, _, guidance = _gap_band(gap["elapsed_minutes"])
        return {
            "ok": True,
            "operation": "begin-exchange",
            "idempotent": True,
            "operation_id": operation_id,
            "state_revision": state["state_revision"],
            "continuity_revision": state["continuity_revision"],
            "public_surface_revision": state["public_surface_revision"],
            "interaction_sequence": state["interaction_sequence"],
            "semantic_operation_sequence": state["semantic_operation_sequence"],
            "gap_id": gap["gap_id"],
            "elapsed_minutes": gap["elapsed_minutes"],
            "gap_band": gap["band"],
            "event_ceiling": gap["event_ceiling"],
            "guidance": guidance,
            "window_id": state["current_window"]["window_id"],
            "current_presence": state["current_presence"],
            "current_condition": state["current_condition"],
            "attention_queue": state["attention_queue"],
            "relational_context": state["relational_context"],
            "signals": _due_signals(state, _now(state, now_override)),
        }
    _check_revision(state, expected_state_revision, expected_continuity_revision)
    now = _now(state, now_override)
    observation = _inspection(state, now)  # Must happen before last_user_contact_at changes.
    sequence = state["interaction_sequence"] + 1
    window = state["current_window"]
    if observation["gap_band"] != "same_window" or not window.get("window_id"):
        window = {
            "window_id": f"window_{sequence:08d}",
            "started_at": _iso(now),
            "last_exchange_at": _iso(now),
        }
    else:
        window = {**window, "last_exchange_at": _iso(now)}

    state["state_revision"] += 1
    state["interaction_sequence"] = sequence
    state["last_user_contact_at"] = _iso(now)
    state["current_window"] = window
    state["last_gap"] = {
        "gap_id": observation["gap_id"],
        "elapsed_minutes": observation["elapsed_minutes"],
        "band": observation["gap_band"],
        "event_ceiling": observation["event_ceiling"],
        "reconciled_revision": state["continuity_revision"],
    }
    _record_operation(state, operation_id)
    _require_clean_state(state)
    _atomic_write(path, state)
    return {
        "ok": True,
        "operation": "begin-exchange",
        "idempotent": False,
        "operation_id": operation_id,
        "gap_id": observation["gap_id"],
        "elapsed_minutes": observation["elapsed_minutes"],
        "gap_band": observation["gap_band"],
        "event_ceiling": observation["event_ceiling"],
        "guidance": observation["guidance"],
        "signals": observation["signals"],
        "state_revision": state["state_revision"],
        "continuity_revision": state["continuity_revision"],
        "public_surface_revision": state["public_surface_revision"],
        "interaction_sequence": sequence,
        "semantic_operation_sequence": state["semantic_operation_sequence"],
        "window_id": window["window_id"],
        "current_presence": state["current_presence"],
        "current_condition": state["current_condition"],
        "attention_queue": state["attention_queue"],
        "relational_context": state["relational_context"],
    }


def commit_contact(
    campaign: Path,
    *,
    operation_id: str,
    expected_state_revision: int,
    now_override: str | None = None,
) -> dict[str, Any]:
    """Compatibility alias for begin_exchange (it records contact, not a response)."""

    result = begin_exchange(
        campaign,
        operation_id=operation_id,
        expected_state_revision=expected_state_revision,
        now_override=now_override,
    )
    return {**result, "operation": "commit-contact"}


def _json_object(raw: str | None, *, label: str) -> dict[str, Any] | None:
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CompanionStateError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise CompanionStateError(f"{label} must be a JSON object")
    return value


def _validate_patch_keys(patch: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(patch) - allowed)
    if unknown:
        raise CompanionStateError(f"unsupported {label} fields: {', '.join(unknown)}")


def _apply_state_patch(state: dict[str, Any], patch: dict[str, Any], now: datetime) -> dict[str, Any]:
    _validate_patch_keys(patch, STATE_PATCH_KEYS, "state patch")
    candidate = copy.deepcopy(state)

    if "current_presence" in patch:
        presence_patch = patch["current_presence"]
        if not isinstance(presence_patch, dict):
            raise CompanionStateError("current_presence patch must be an object")
        _validate_patch_keys(presence_patch, PRESENCE_KEYS, "presence")
        old_presence = candidate["current_presence"]
        new_presence = {**old_presence, **presence_patch}
        moved_or_changed_activity = any(
            key in presence_patch and presence_patch[key] != old_presence.get(key)
            for key in ("place_ref", "activity")
        )
        if moved_or_changed_activity:
            new_presence["as_of"] = _iso(now)
        elif "as_of" in presence_patch and old_presence.get("as_of"):
            old_as_of = _parse_iso(old_presence["as_of"], field="current_presence.as_of", nullable=False)
            new_as_of = _parse_iso(presence_patch["as_of"], field="current_presence.as_of", nullable=False)
            assert old_as_of is not None and new_as_of is not None
            if new_as_of.astimezone(timezone.utc) < old_as_of.astimezone(timezone.utc):
                raise CompanionStateError("current_presence.as_of cannot move backwards")
        candidate["current_presence"] = new_presence

    if "current_condition" in patch:
        condition_patch = patch["current_condition"]
        if not isinstance(condition_patch, dict):
            raise CompanionStateError("current_condition patch must be an object")
        _validate_patch_keys(condition_patch, CONDITION_KEYS, "condition")
        old_condition = candidate["current_condition"]
        new_condition = {**old_condition, **condition_patch}
        meaningful = any(
            key in condition_patch and condition_patch[key] != old_condition.get(key)
            for key in CONDITION_KEYS - {"as_of", "reevaluate_after"}
        )
        if meaningful:
            new_condition["as_of"] = _iso(now)
        candidate["current_condition"] = new_condition

    if "attention_queue" in patch:
        candidate["attention_queue"] = copy.deepcopy(patch["attention_queue"])

    if "relational_context" in patch:
        relationship_patch = patch["relational_context"]
        if not isinstance(relationship_patch, dict):
            raise CompanionStateError("relational_context patch must be an object")
        _validate_patch_keys(relationship_patch, RELATIONAL_KEYS, "relational context")
        old_relationship = candidate["relational_context"]
        new_relationship = {**old_relationship, **copy.deepcopy(relationship_patch)}
        significant_keys = {
            "companion_posture",
            "reciprocity_pattern",
            "boundary_refs",
            "active_tensions",
        }
        significant_change = any(
            key in relationship_patch and relationship_patch[key] != old_relationship.get(key)
            for key in significant_keys
        )
        old_ids = {
            item.get("evidence_id")
            for item in old_relationship.get("recent_evidence", [])
            if isinstance(item, dict)
        }
        new_ids = {
            item.get("evidence_id")
            for item in new_relationship.get("recent_evidence", [])
            if isinstance(item, dict)
        }
        added_ids = {item for item in new_ids - old_ids if _nonempty(item)}
        old_evidence = {
            item["evidence_id"]: item
            for item in old_relationship.get("recent_evidence", [])
            if isinstance(item, dict) and _nonempty(item.get("evidence_id"))
        }
        new_evidence = {
            item["evidence_id"]: item
            for item in new_relationship.get("recent_evidence", [])
            if isinstance(item, dict) and _nonempty(item.get("evidence_id"))
        }
        changed_existing = sorted(
            evidence_id
            for evidence_id in old_ids & new_ids
            if old_evidence.get(evidence_id) != new_evidence.get(evidence_id)
        )
        if changed_existing:
            raise CompanionStateError(
                "relationship evidence is append-only and cannot be rewritten: "
                + ", ".join(changed_existing)
            )
        if old_ids - new_ids and not added_ids:
            raise CompanionStateError("bounded relationship evidence may only be retired when new evidence is added")
        if significant_change:
            last_change = new_relationship.get("last_change_evidence_id")
            if not added_ids or last_change not in added_ids:
                raise CompanionStateError(
                    "a relational change requires new recent_evidence and last_change_evidence_id"
                )
        candidate["relational_context"] = new_relationship

    if "pending_transition" in patch:
        transition = patch["pending_transition"]
        if transition is not None and not isinstance(transition, dict):
            raise CompanionStateError("pending_transition must be null or an object")
        candidate["pending_transition"] = copy.deepcopy(transition)
    for owner, field in (
        ("current_presence", "as_of"),
        ("current_condition", "as_of"),
    ):
        raw = candidate[owner].get(field)
        if raw:
            observed = _parse_iso(raw, field=f"{owner}.{field}", nullable=False)
            assert observed is not None
            if observed.astimezone(timezone.utc) > now.astimezone(timezone.utc):
                raise CompanionStateError(f"{owner}.{field} cannot be in the future")
    for evidence in candidate["relational_context"].get("recent_evidence", []):
        observed = _parse_iso(evidence.get("observed_at"), field="recent_evidence.observed_at", nullable=False)
        assert observed is not None
        if observed.astimezone(timezone.utc) > now.astimezone(timezone.utc):
            raise CompanionStateError("relationship evidence cannot be dated in the future")
    return candidate


def commit_semantic(
    campaign: Path,
    *,
    operation_id: str,
    semantic_sequence: int,
    expected_state_revision: int,
    expected_continuity_revision: int,
    state_patch: dict[str, Any],
    public_patch: dict[str, Any] | None = None,
    expected_public_surface_revision: int | None = None,
    gap_id: str | None = None,
    now_override: str | None = None,
) -> dict[str, Any]:
    """Commit one bounded semantic update and return a public-view candidate."""

    _require_operation_id(operation_id)
    if not isinstance(state_patch, dict):
        raise CompanionStateError("state_patch must be a JSON object")
    if public_patch is not None and not isinstance(public_patch, dict):
        raise CompanionStateError("public_patch must be a JSON object")
    payload_hash = _semantic_payload_hash(state_patch, public_patch, gap_id)
    campaign_root = campaign.resolve()
    path, state = _load(campaign_root)
    _require_clean_state(state)
    prior_semantic = next(
        (
            entry
            for entry in state["semantic_operation_ledger"]
            if entry.get("operation_id") == operation_id
        ),
        None,
    )
    if prior_semantic is not None:
        if semantic_sequence != prior_semantic["sequence"]:
            raise CompanionStateError("operation_id was already committed with a different semantic sequence")
        if payload_hash != prior_semantic["payload_hash"]:
            raise CompanionStateError("operation_id was already committed with a different semantic payload")
        candidate_public = None
        if public_patch:
            candidate_public = {
                "applied": True,
                "already_committed": True,
                "source_state_revision": state["state_revision"],
                "source_continuity_revision": state["continuity_revision"],
                "public_surface_revision": state["public_surface_revision"],
                "patch": public_patch,
            }
        return {
            "ok": True,
            "operation": "commit-semantic",
            "idempotent": True,
            "operation_id": operation_id,
            "state_revision": state["state_revision"],
            "continuity_revision": state["continuity_revision"],
            "public_surface_revision": state["public_surface_revision"],
            "semantic_operation_sequence": state["semantic_operation_sequence"],
            "current_presence": state["current_presence"],
            "current_condition": state["current_condition"],
            "attention_queue": state["attention_queue"],
            "relational_context": state["relational_context"],
            "pending_transition": state["pending_transition"],
            "candidate_public_patch": candidate_public,
        }
    if _idempotent(state, operation_id):
        raise CompanionStateError("operation_id was already used by a non-semantic operation")

    expected_next = state["semantic_operation_sequence"] + 1
    if not _strict_int(semantic_sequence, minimum=1) or semantic_sequence != expected_next:
        raise CompanionStateError(
            f"semantic sequence must be exactly {expected_next}; received {semantic_sequence}"
        )
    public_change = bool(public_patch)
    if not state_patch and not public_change:
        raise CompanionStateError("commit-semantic requires a state patch or non-empty public patch")
    if public_change and expected_public_surface_revision is None:
        raise CompanionStateError("a public patch requires expected_public_surface_revision")
    _check_revision(
        state,
        expected_state_revision,
        expected_continuity_revision,
        expected_public_surface_revision if public_change else None,
    )
    view_path: Path | None = None
    view_candidate: dict[str, Any] | None = None
    if public_change:
        if not _companion_view_expected(campaign_root):
            raise CompanionStateError("public_patch is unavailable while Companion View is disabled")
        view_path, current_view = _load_view(campaign_root)
        if current_view.get("enabled") is not True:
            raise CompanionStateError("public_patch is unavailable while Companion View is disabled")
        if current_view.get("public_surface_revision") != state["public_surface_revision"]:
            raise CompanionStateError(
                "Companion View revision is not aligned with companion_state"
            )
        view_candidate = _apply_public_patch(current_view, public_patch or {})
    now = _now(state, now_override)
    _reject_backwards(state, now)
    if view_candidate is not None and isinstance(view_candidate.get("last_shared_status"), dict):
        shared_at = _parse_iso(
            view_candidate["last_shared_status"].get("shared_at"),
            field="last_shared_status.shared_at",
            nullable=False,
        )
        assert shared_at is not None
        if shared_at.astimezone(timezone.utc) > now.astimezone(timezone.utc):
            raise CompanionStateError("last_shared_status.shared_at cannot be in the future")
    if gap_id is not None:
        known_gap = state.get("last_gap", {}).get("gap_id")
        if gap_id != known_gap:
            observation = _inspection(state, now)
            if gap_id != observation["gap_id"]:
                raise CompanionStateError(f"stale gap id: expected {known_gap or observation['gap_id']}, received {gap_id}")

    candidate = _apply_state_patch(state, state_patch, now)
    candidate["state_revision"] += 1
    if state_patch:
        candidate["continuity_revision"] += 1
        candidate["last_observation_at"] = _iso(now)
    if public_change:
        candidate["public_surface_revision"] += 1
    candidate["semantic_operation_sequence"] = semantic_sequence
    candidate["last_semantic_operation_id"] = operation_id
    candidate["semantic_operation_ledger"].append(
        {
            "sequence": semantic_sequence,
            "operation_id": operation_id,
            "payload_hash": payload_hash,
        }
    )
    if gap_id is not None:
        candidate["last_gap"] = {
            **candidate["last_gap"],
            "reconciled_revision": candidate["continuity_revision"],
        }
    _record_operation(candidate, operation_id)
    _require_clean_state(candidate)
    if public_change:
        assert view_path is not None and view_candidate is not None
        view_candidate["public_surface_revision"] = candidate["public_surface_revision"]
        _validate_public_candidate(campaign_root, view_path, view_candidate)
        _atomic_commit_pair(path, candidate, view_path, view_candidate)
    else:
        _atomic_write(path, candidate)

    candidate_public = None
    if public_change:
        candidate_public = {
            "applied": True,
            "already_committed": False,
            "expected_public_surface_revision": state["public_surface_revision"],
            "public_surface_revision": candidate["public_surface_revision"],
            "source_state_revision": candidate["state_revision"],
            "source_continuity_revision": candidate["continuity_revision"],
            "patch": public_patch,
        }
    return {
        "ok": True,
        "operation": "commit-semantic",
        "idempotent": False,
        "operation_id": operation_id,
        "state_revision": candidate["state_revision"],
        "continuity_revision": candidate["continuity_revision"],
        "public_surface_revision": candidate["public_surface_revision"],
        "semantic_operation_sequence": candidate["semantic_operation_sequence"],
        "current_presence": candidate["current_presence"],
        "current_condition": candidate["current_condition"],
        "attention_queue": candidate["attention_queue"],
        "relational_context": candidate["relational_context"],
        "pending_transition": candidate["pending_transition"],
        "gap_id": candidate["last_gap"]["gap_id"] if gap_id is not None else None,
        "candidate_public_patch": candidate_public,
    }


def commit_presence(
    campaign: Path,
    *,
    operation_id: str,
    expected_state_revision: int,
    expected_continuity_revision: int,
    presence_patch: dict[str, Any],
    relationship_patch: dict[str, Any] | None = None,
    pending_transition: dict[str, Any] | None = None,
    clear_pending_transition: bool = False,
    gap_id: str | None = None,
    now_override: str | None = None,
) -> dict[str, Any]:
    """Compatibility wrapper that writes through the semantic sequence gate."""

    if pending_transition is not None and clear_pending_transition:
        raise CompanionStateError("cannot set and clear pending_transition in one operation")
    _, state = _load(campaign)
    _require_clean_state(state)
    patch: dict[str, Any] = {"current_presence": presence_patch}
    if relationship_patch is not None:
        # The argument name stays stable, but ladder-era fields do not.
        ladder_fields = {"trust_band", "closeness_band"}
        if ladder_fields & set(relationship_patch):
            raise CompanionStateError(
                "trust/closeness ladders were removed in schema v2; use relational_context evidence"
            )
        patch["relational_context"] = relationship_patch
    if pending_transition is not None:
        patch["pending_transition"] = pending_transition
    elif clear_pending_transition:
        patch["pending_transition"] = None
    result = commit_semantic(
        campaign,
        operation_id=operation_id,
        semantic_sequence=state["semantic_operation_sequence"] + 1,
        expected_state_revision=expected_state_revision,
        expected_continuity_revision=expected_continuity_revision,
        state_patch=patch,
        gap_id=gap_id,
        now_override=now_override,
    )
    return {**result, "operation": "commit-presence"}


def validate(campaign: Path) -> dict[str, Any]:
    path, state = _load(campaign)
    findings = validate_state(state)
    return {
        "ok": not findings,
        "operation": "validate",
        "path": str(path),
        "error_count": len(findings),
        "findings": findings,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", help="Path to the active campaign directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Read gap and hot state without writing.")
    inspect_parser.add_argument("--now", help="Fixed timezone-aware ISO timestamp for replay/tests.")

    begin = subparsers.add_parser("begin-exchange", help="Calculate the prior gap and record user contact atomically.")
    begin.add_argument("--operation-id", required=True)
    begin.add_argument("--expected-state-revision", type=int, required=True)
    begin.add_argument("--expected-continuity-revision", type=int)
    begin.add_argument("--now", help="Fixed timezone-aware ISO timestamp for replay/tests.")

    contact = subparsers.add_parser("commit-contact", help="Compatibility alias for begin-exchange.")
    contact.add_argument("--operation-id", required=True)
    contact.add_argument("--expected-state-revision", type=int, required=True)
    contact.add_argument("--now", help="Fixed timezone-aware ISO timestamp for replay/tests.")

    semantic = subparsers.add_parser("commit-semantic", help="Commit one bounded durable semantic update.")
    semantic.add_argument("--operation-id", required=True)
    semantic.add_argument("--semantic-sequence", type=int, required=True)
    semantic.add_argument("--expected-state-revision", type=int, required=True)
    semantic.add_argument("--expected-continuity-revision", type=int, required=True)
    semantic.add_argument("--state-patch-json", required=True)
    semantic.add_argument("--public-patch-json")
    semantic.add_argument("--expected-public-surface-revision", type=int)
    semantic.add_argument("--gap-id")
    semantic.add_argument("--now", help="Fixed timezone-aware ISO timestamp for replay/tests.")

    presence = subparsers.add_parser("commit-presence", help="Compatibility durable presence update.")
    presence.add_argument("--operation-id", required=True)
    presence.add_argument("--expected-state-revision", type=int, required=True)
    presence.add_argument("--expected-continuity-revision", type=int, required=True)
    presence.add_argument("--presence-json", required=True)
    presence.add_argument("--relationship-json")
    presence.add_argument("--pending-transition-json")
    presence.add_argument("--clear-pending-transition", action="store_true")
    presence.add_argument("--gap-id")
    presence.add_argument("--now", help="Fixed timezone-aware ISO timestamp for replay/tests.")

    subparsers.add_parser("validate", help="Validate Companion state without writing.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    campaign = Path(args.campaign)
    try:
        if args.command == "inspect":
            result = inspect(campaign, now_override=args.now)
        elif args.command == "begin-exchange":
            result = begin_exchange(
                campaign,
                operation_id=args.operation_id,
                expected_state_revision=args.expected_state_revision,
                expected_continuity_revision=args.expected_continuity_revision,
                now_override=args.now,
            )
        elif args.command == "commit-contact":
            result = commit_contact(
                campaign,
                operation_id=args.operation_id,
                expected_state_revision=args.expected_state_revision,
                now_override=args.now,
            )
        elif args.command == "commit-semantic":
            result = commit_semantic(
                campaign,
                operation_id=args.operation_id,
                semantic_sequence=args.semantic_sequence,
                expected_state_revision=args.expected_state_revision,
                expected_continuity_revision=args.expected_continuity_revision,
                state_patch=_json_object(args.state_patch_json, label="--state-patch-json") or {},
                public_patch=_json_object(args.public_patch_json, label="--public-patch-json"),
                expected_public_surface_revision=args.expected_public_surface_revision,
                gap_id=args.gap_id,
                now_override=args.now,
            )
        elif args.command == "commit-presence":
            result = commit_presence(
                campaign,
                operation_id=args.operation_id,
                expected_state_revision=args.expected_state_revision,
                expected_continuity_revision=args.expected_continuity_revision,
                presence_patch=_json_object(args.presence_json, label="--presence-json") or {},
                relationship_patch=_json_object(args.relationship_json, label="--relationship-json"),
                pending_transition=_json_object(args.pending_transition_json, label="--pending-transition-json"),
                clear_pending_transition=args.clear_pending_transition,
                gap_id=args.gap_id,
                now_override=args.now,
            )
        else:
            result = validate(campaign)
    except CompanionStateError as exc:
        result = {"ok": False, "operation": args.command, "error": str(exc)}
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())

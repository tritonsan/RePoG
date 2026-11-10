"""Atomically commit model-authored RPG continuity changes.

This helper is deliberately semantic-free. The GM decides which established
facts are durable, which campaign files own them, and which secondary surfaces
may wait. This module validates that declared ownership is accompanied by an
actual mutation, stages every candidate before writing, and commits the batch
with revision, event, idempotency, and crash-recovery guarantees.

It never decides what happened in the fiction and never writes player-facing
narration.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import time
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, Iterator

import curation
import file_transaction
import lang_pack
import name_check
import owner_ops
import repog_runtime
import roll_dice


TRANSACTION_DIR = ".repog-transactions"
LOCK_FILE = ".lock"
MANIFEST_VERSION = 1
MAX_OPERATION_ID = 128
MAX_CHANGES = 32
MAX_MUTATIONS = 32
MAX_REPLACEMENTS = 64
MAX_MECHANIC_OPERATIONS = 16
MAX_LINE_TEXT = 2_000
MAX_FILE_TEXT = 500_000
# Warn well before the hard cap so a growing owner is curated, not truncated.
SIZE_WARNING_TEXT = 300_000
LOG_ROTATION_HINT_TEXT = 400_000
# commit-distill rotates the session log by itself past this size.
LOG_AUTO_ROTATE_TEXT = 150_000
ARCHIVE_DIR = "archive"
MAX_VOID_ROLLS = 16
# A roll the Player made with physical dice has no receipt; it is cited as
# "player:<what was rolled>" and is accepted only where the Player rolls.
PLAYER_ROLL_PREFIX = "player:"
PLAYER_ROLL_MODES = {"player_rolls", "hybrid"}
# Optional owners that older campaigns may lack: a typed edit starts from the
# shipped template instead of failing on the missing file.
TEMPLATE_OWNERS = {"directives.md", "glossary.md"}
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "campaign"
# A staged curation file younger than this may still be being written.
CURATION_SETTLE_SECONDS = 3.0
CURATION_DUE_FILE = "curation_due.json"
# Read by the GM just before the reply, never shown to the Player.
REPLY_NOTE = "send the whole reply now, as text: the Player sees only what you send, never your reasoning"
REPLY_WAIT_NOTE = "finish the distill and repair any full-check error first, then send the whole reply as text"
MAX_OPEN_CHOICES = 5
MAX_OPEN_CHOICE_TEXT = 200
# Content findings a distill may not leave behind: each one's file must be
# changed by the distill or deferred to the curator in deferred_reconcile.
DISTILL_GATE_RULES = frozenset(
    {
        "cast_dead_listed",
        "cast_present_missing",
        "relationship_dead_active",
        "location_unmapped",
        "stacked_sections",
        "now_overflow",
        "minor_romance_history",
    }
)
UNDEFERRABLE_GATE_RULES = frozenset({"minor_romance_history"})
# Full-check warnings after a distill that put their file on the curator's list.
CURATION_DUE_RULES = frozenset(
    {
        "death_projection",
        "cast_dead_listed",
        "relationship_dead_active",
        "now_overflow",
        "records_language_mismatch",
        "stacked_sections",
        "note_core_missing",
    }
)
# A cited roll whose band names one of these left a mark the records must carry.
COST_BAND_TOKENS = ("cost", "partial", "loss", "fail")
# --input-file is UTF-8; these are the fallbacks for a payload a Windows shell
# wrote in the console code page.
INPUT_FALLBACK_CODECS = (("cp1254", "cp1254"), ("latin-1", "latin1"))
# The best language must beat the runner-up by this stopword-ratio margin.
RECORD_LANGUAGE_CONFIDENCE = 0.2

OPERATION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CHANGE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
KIND_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
SCENE_MODES = {"ambient", "focused", "crisis", "aftermath", "transition", "breather", "downtime"}
BOUNDARIES = {"ordinary", "scene_checkpoint", "full_distill"}

# A declared semantic kind implies its authority owner. Only unambiguous tokens
# appear here, so an unrecognized kind stays free-form. The requirement is
# deliberately limited to bookkeeping: it never inspects narration, judges
# semantic quality, or adds a separate validation pass.
KIND_AUTHORITY_TOKENS: tuple[tuple[frozenset[str], str], ...] = (
    (frozenset({"knowledge", "disclosure", "secrecy", "epistemic"}), "knowledge_boundaries.md"),
    (frozenset({"clue", "secret"}), "secrets_and_clues.md"),
    (frozenset({"relationship", "bond"}), "relationship_map.md"),
    (frozenset({"presence", "whereabouts"}), "active_cast.md"),
    (frozenset({"route", "adjacency"}), "location_graph.md"),
    (frozenset({"directive"}), "directives.md"),
)

ROOT_OWNER_FILES = {
    "current_state.yaml",
    "active_cast.md",
    "knowledge_boundaries.md",
    "relationship_map.md",
    "threads.md",
    "world_dynamics.md",
    "issues.md",
    "location_graph.md",
    "creation_ledger.md",
    "arc_closure.md",
    "player.md",
    "player_ties.md",
    "world_truths.md",
    "rules.md",
    "mechanics_state.json",
    "directives.md",
    "glossary.md",
}
ENTITY_OWNER_DIRS = {"characters", "places", "factions"}
SYSTEM_MANAGED_FILES = {"session_log.md"}
NEVER_COLD_FILES = ROOT_OWNER_FILES | SYSTEM_MANAGED_FILES | {
    "setup_profile.yaml",
    "play_profile.yaml",
    "companion_profile.yaml",
    "companion_state.json",
}
# Files a distill may not edit: the writer owns the state and log, mechanics
# change only through mechanic operations, and locked profiles change only
# through their own setup or OOC procedures.
DISTILL_FORBIDDEN_FILES = SYSTEM_MANAGED_FILES | {
    "current_state.yaml",
    "mechanics_state.json",
    "setup_profile.yaml",
    "play_profile.yaml",
    "companion_profile.yaml",
    "companion_state.json",
    "session_zero_state.json",
}
COORDINATOR_MECHANIC_FIELDS = {
    "operation_sequence",
    "expected_revision",
    "expected_continuity_revision",
    "resulting_continuity_revision",
}


class RPGStateError(Exception):
    """Typed failure returned by the RPG transaction surface."""

    def __init__(self, category: str, reason: str, *, exit_code: int = 2, extra: dict[str, Any] | None = None) -> None:
        super().__init__(reason)
        self.category = category
        self.exit_code = exit_code
        # Structured detail merged into the failure JSON (a ready op, a finding list).
        self.extra = extra or {}


def _strict_int(value: Any, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _require_keys(value: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise RPGStateError("input_invalid", f"{label} contains unsupported field(s): {', '.join(unknown)}")


def _reply_note(narration_allowed: bool) -> str:
    return REPLY_NOTE if narration_allowed else REPLY_WAIT_NOTE


def _one_line(value: Any, label: str, *, maximum: int = MAX_LINE_TEXT) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RPGStateError("input_invalid", f"{label} must be non-empty text")
    text = value.strip()
    if "\n" in text or "\r" in text:
        raise RPGStateError("input_invalid", f"{label} must be one line")
    if len(text) > maximum:
        raise RPGStateError("input_invalid", f"{label} exceeds {maximum} characters")
    return text


def _operation_id(value: Any) -> str:
    operation_id = _one_line(value, "operation_id", maximum=MAX_OPERATION_ID)
    if OPERATION_ID_RE.fullmatch(operation_id) is None:
        raise RPGStateError(
            "input_invalid",
            "operation_id must start with an alphanumeric character and contain only letters, numbers, dot, underscore, or dash",
        )
    return operation_id


def _canonical_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _bytes_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        # The hooks read notes while a staged curation is applied; on Windows a
        # reader holding a note open makes a plain os.replace fail at once.
        repog_runtime.replace_file(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    _atomic_bytes(path, (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError as exc:
        raise RPGStateError("campaign_invalid", f"missing {label}: {path.name}") from exc
    except OSError as exc:
        raise RPGStateError("campaign_invalid", f"cannot read {label}: {exc}") from exc


def _read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RPGStateError("campaign_invalid", f"missing {label}: {path.name}") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise RPGStateError("campaign_invalid", f"cannot read {label} as UTF-8: {exc}") from exc


def _campaign_root(campaign: Path) -> Path:
    root = campaign.resolve()
    if not root.is_dir():
        raise RPGStateError("campaign_invalid", f"campaign folder does not exist: {root}")
    return root


def _relative_path(root: Path, value: Any, label: str) -> tuple[str, Path]:
    text = _one_line(value, label, maximum=400)
    if "\\" in text or "\x00" in text:
        raise RPGStateError("path_forbidden", f"{label} must use a campaign-relative POSIX path")
    pure = PurePosixPath(text)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise RPGStateError("path_forbidden", f"{label} must stay inside the campaign folder")
    if ":" in pure.parts[0]:
        raise RPGStateError("path_forbidden", f"{label} must not contain a drive or URI prefix")
    candidate = (root / Path(*pure.parts)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise RPGStateError("path_forbidden", f"{label} escapes the campaign folder") from exc
    relative = pure.as_posix()
    if pure.parts[0] in {TRANSACTION_DIR, "snapshots"}:
        raise RPGStateError("path_forbidden", f"{label} targets a recovery-only area: {relative}")
    return relative, candidate


def _owner_path(root: Path, value: Any, label: str) -> tuple[str, Path]:
    relative, path = _relative_path(root, value, label)
    pure = PurePosixPath(relative)
    nested_entity = (
        len(pure.parts) >= 2
        and pure.parts[0] in ENTITY_OWNER_DIRS
        and pure.suffix.lower() == ".md"
    )
    if relative not in ROOT_OWNER_FILES and not nested_entity:
        raise RPGStateError("path_forbidden", f"{label} is not an RPG immediate-owner path: {relative}")
    return relative, path


def _cold_path(root: Path, value: Any, label: str) -> str:
    relative, _ = _relative_path(root, value, label)
    if relative in NEVER_COLD_FILES:
        raise RPGStateError("input_invalid", f"authoritative hot file cannot be deferred as a cold target: {relative}")
    return relative


def _yaml_scalar(value: str) -> str:
    text = value.strip()
    if " #" in text:
        text = text.split(" #", 1)[0].rstrip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        text = text[1:-1]
    return text


def _top_scalar(text: str, key: str) -> str:
    matches = list(re.finditer(rf"(?m)^{re.escape(key)}:[ \t]*(.*?)[ \t]*$", text))
    if len(matches) != 1:
        raise RPGStateError("campaign_invalid", f"expected exactly one top-level {key} field")
    return _yaml_scalar(matches[0].group(1))


def _block_lines(text: str, parent: str) -> tuple[list[str], int, int]:
    lines = text.splitlines(keepends=True)
    parent_index = -1
    parent_pattern = re.compile(rf"^{re.escape(parent)}:\s*(?:#.*)?(?:\r?\n)?$")
    for index, line in enumerate(lines):
        if parent_pattern.fullmatch(line):
            if parent_index != -1:
                raise RPGStateError("campaign_invalid", f"duplicate {parent} block")
            parent_index = index
    if parent_index == -1:
        raise RPGStateError("campaign_invalid", f"missing {parent} block")
    end = len(lines)
    for index in range(parent_index + 1, len(lines)):
        line = lines[index]
        if line.strip() and not line.startswith((" ", "\t", "#", "\r", "\n")):
            end = index
            break
    return lines, parent_index + 1, end


def _nested_scalar(text: str, parent: str, key: str) -> str:
    lines, start, end = _block_lines(text, parent)
    matches: list[str] = []
    pattern = re.compile(rf"^\s+{re.escape(key)}:\s*(.*?)\s*(?:\r?\n)?$")
    for line in lines[start:end]:
        match = pattern.match(line)
        if match:
            matches.append(_yaml_scalar(match.group(1)))
    if len(matches) != 1:
        raise RPGStateError("campaign_invalid", f"expected exactly one {parent}.{key} field")
    return matches[0]


def _parse_list_scalar(value: str) -> list[str]:
    value = value.strip()
    if value == "[]":
        return []
    if not (value.startswith("[") and value.endswith("]")):
        raise RPGStateError("campaign_invalid", "pending_cold_targets inline value must be a list")
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        decoded = [item.strip().strip("'\"") for item in value[1:-1].split(",") if item.strip()]
    if not isinstance(decoded, list) or any(not isinstance(item, str) or not item.strip() for item in decoded):
        raise RPGStateError("campaign_invalid", "pending_cold_targets must contain non-empty strings")
    return [item.strip() for item in decoded]


def _pending_targets(text: str) -> list[str]:
    lines, start, end = _block_lines(text, "persistence")
    key_index = -1
    inline = ""
    pattern = re.compile(r"^\s+pending_cold_targets:\s*(.*?)\s*(?:\r?\n)?$")
    for index in range(start, end):
        match = pattern.match(lines[index])
        if match:
            if key_index != -1:
                raise RPGStateError("campaign_invalid", "duplicate persistence.pending_cold_targets field")
            key_index = index
            inline = match.group(1).strip()
    if key_index == -1:
        raise RPGStateError("campaign_invalid", "missing persistence.pending_cold_targets field")
    if inline:
        return _parse_list_scalar(inline)
    values: list[str] = []
    item_pattern = re.compile(r"^\s{4,}-\s+(.*?)\s*(?:\r?\n)?$")
    for index in range(key_index + 1, end):
        line = lines[index]
        if line.strip() and len(line) - len(line.lstrip(" ")) <= 2:
            break
        match = item_pattern.match(line)
        if match:
            value = _yaml_scalar(match.group(1))
            if not value:
                raise RPGStateError("campaign_invalid", "pending_cold_targets contains an empty item")
            values.append(value)
        elif line.strip() and not line.lstrip().startswith("#"):
            raise RPGStateError("campaign_invalid", "pending_cold_targets has invalid YAML list content")
    return values


def _state_meta(text: str) -> dict[str, Any]:
    try:
        revision = int(_top_scalar(text, "continuity_revision"))
        last_distilled = int(_nested_scalar(text, "persistence", "last_distilled_revision"))
        durable_turns = int(_nested_scalar(text, "persistence", "durable_turns_since_distill"))
    except ValueError as exc:
        raise RPGStateError("campaign_invalid", "current_state persistence fields must be integers") from exc
    if revision < 0 or last_distilled < 0 or durable_turns < 0 or last_distilled > revision:
        raise RPGStateError("campaign_invalid", "current_state persistence revisions are out of range")
    pending = _pending_targets(text)
    if len(pending) != len(set(pending)):
        raise RPGStateError("campaign_invalid", "pending_cold_targets contains duplicates")
    if durable_turns != revision - last_distilled:
        raise RPGStateError(
            "campaign_invalid",
            f"durable_turns_since_distill is {durable_turns}, expected {revision - last_distilled}",
        )
    return {
        "revision": revision,
        "last_distilled_revision": last_distilled,
        "durable_turns_since_distill": durable_turns,
        "pending_cold_targets": pending,
    }


def _replace_top_scalar(text: str, key: str, value: int) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(key)}:[ \t]*.*?[ \t]*$")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RPGStateError("candidate_invalid", f"cannot update unique top-level {key}")
    return text[: matches[0].start()] + f"{key}: {value}" + text[matches[0].end() :]


def _replace_nested_scalar(text: str, parent: str, key: str, value: int) -> str:
    lines, start, end = _block_lines(text, parent)
    matching = [
        index
        for index in range(start, end)
        if re.match(rf"^\s+{re.escape(key)}:\s*", lines[index])
    ]
    if len(matching) != 1:
        raise RPGStateError("candidate_invalid", f"cannot update unique {parent}.{key}")
    index = matching[0]
    indent = lines[index][: len(lines[index]) - len(lines[index].lstrip(" \t"))]
    newline = "\r\n" if lines[index].endswith("\r\n") else "\n"
    lines[index] = f"{indent}{key}: {value}{newline}"
    return "".join(lines)


def _replace_pending_targets(text: str, targets: list[str]) -> str:
    lines, start, end = _block_lines(text, "persistence")
    matching = [
        index
        for index in range(start, end)
        if re.match(r"^\s+pending_cold_targets:\s*", lines[index])
    ]
    if len(matching) != 1:
        raise RPGStateError("candidate_invalid", "cannot update unique persistence.pending_cold_targets")
    key_index = matching[0]
    remove_end = key_index + 1
    while remove_end < end:
        line = lines[remove_end]
        if not line.strip():
            break
        indent = len(line) - len(line.lstrip(" "))
        if indent <= 2:
            break
        remove_end += 1
    newline = "\r\n" if lines[key_index].endswith("\r\n") else "\n"
    indent_text = lines[key_index][: len(lines[key_index]) - len(lines[key_index].lstrip(" \t"))]
    if not targets:
        replacement = [f"{indent_text}pending_cold_targets: []{newline}"]
    else:
        replacement = [f"{indent_text}pending_cold_targets:{newline}"]
        replacement.extend(
            f"{indent_text}  - {json.dumps(target, ensure_ascii=False)}{newline}" for target in targets
        )
    lines[key_index:remove_end] = replacement
    return "".join(lines)


def _update_state_system(
    text: str,
    *,
    revision: int,
    durable_turns: int,
    pending_targets: list[str],
) -> str:
    updated = _replace_top_scalar(text, "continuity_revision", revision)
    updated = _replace_nested_scalar(updated, "persistence", "durable_turns_since_distill", durable_turns)
    updated = _replace_pending_targets(updated, pending_targets)
    return updated


def _profile_policy(root: Path) -> str:
    setup_text = _read_text(root / "setup_profile.yaml", "setup profile")
    try:
        setup_schema = int(_top_scalar(setup_text, "schema_version"))
    except ValueError as exc:
        raise RPGStateError("campaign_invalid", "setup_profile.schema_version must be an integer") from exc
    experience = _top_scalar(setup_text, "experience_mode")
    if setup_schema < 4 and not experience:
        experience = "rpg"
    if experience != "rpg":
        raise RPGStateError("campaign_invalid", "RPG commits require setup_profile.experience_mode: rpg")
    if _top_scalar(setup_text, "ready_for_play").lower() not in {"true", "yes"}:
        raise RPGStateError("campaign_invalid", "RPG commits require ready_for_play: true")

    profile_text = _read_text(root / "play_profile.yaml", "play profile")
    if _top_scalar(profile_text, "profile_status") != "locked":
        raise RPGStateError("campaign_invalid", "RPG commits require play_profile.profile_status: locked")
    protocol = _nested_scalar(profile_text, "performance", "turn_protocol")
    policy = _nested_scalar(profile_text, "performance", "cold_distill_policy")
    if not protocol or not policy:
        raise RPGStateError("campaign_invalid", "locked play profile has no turn protocol or cold-distill policy")
    return policy


def _validate_log(log_text: str, meta: dict[str, Any]) -> None:
    revisions = [int(value) for value in re.findall(r"(?im)^###\s+Durable Revision\s+(\d+)\s*$", log_text)]
    duplicates = sorted({value for value in revisions if revisions.count(value) > 1})
    if duplicates:
        raise RPGStateError("campaign_invalid", f"duplicate durable revision event(s): {duplicates}")
    revision_set = set(revisions)
    current = meta["revision"]
    last_distilled = meta["last_distilled_revision"]
    future = sorted(value for value in revision_set if value > current)
    if future:
        raise RPGStateError("campaign_invalid", f"session log is ahead of current state: {future}")
    missing = sorted(set(range(last_distilled + 1, current + 1)) - revision_set)
    if missing:
        raise RPGStateError("campaign_invalid", f"session log is missing durable revision event(s): {missing}")
    if last_distilled > 0:
        markers = {
            int(value)
            for value in re.findall(r"(?im)^###\s+Distilled Through Revision\s+(\d+)\s*$", log_text)
        }
        if last_distilled not in markers:
            raise RPGStateError(
                "campaign_invalid",
                f"session log has no distilled-through marker for revision {last_distilled}",
            )


def _runtime(root: Path) -> tuple[str, str, dict[str, Any]]:
    policy = _profile_policy(root)
    state_text = _read_text(root / "current_state.yaml", "current state")
    meta = _state_meta(state_text)
    log_text = _read_text(root / "session_log.md", "session log")
    _validate_log(log_text, meta)
    return state_text, log_text, {**meta, "cold_distill_policy": policy}


def _threshold(policy: str) -> int | None:
    return {
        "every_durable": 1,
        "scene_checkpoint_or_3_durable": 3,
        "scene_checkpoint_or_5_durable": 5,
        "scene_or_3_durable": 3,
        "scene_or_5_durable": 5,
    }.get(policy)


def _distill_requirement(
    policy: str,
    durable_turns: int,
    *,
    boundary: str,
    checkpoint: bool,
) -> tuple[bool, str | None]:
    if boundary == "full_distill":
        return True, "explicit_boundary"
    threshold = _threshold(policy)
    if threshold is not None and durable_turns >= threshold:
        return True, "cadence_limit"
    if checkpoint and policy in {"scene_only", "scene_or_3_durable", "scene_or_5_durable"}:
        return True, "legacy_scene_boundary"
    return False, None


def _receipt_blocks(log_text: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"(?ms)^###\s+(Durable Revision|Scene Checkpoint Revision)\s+(\d+)\s*$\n(.*?)(?=^###\s|\Z)"
    )
    receipts: list[dict[str, Any]] = []
    for match in pattern.finditer(log_text):
        body = match.group(3)
        operation_match = re.search(r"(?m)^- Operation:\s*([^\s]+)\s*$", body)
        if operation_match is None:
            continue
        hash_match = re.search(r"(?m)^- Payload hash:\s*sha256:([0-9a-f]{64})\s*$", body)
        receipts.append(
            {
                "kind": "durable" if match.group(1) == "Durable Revision" else "checkpoint",
                "revision": int(match.group(2)),
                "operation_id": operation_match.group(1),
                "payload_hash": hash_match.group(1) if hash_match else None,
            }
        )
    return receipts


def _prior_receipt(
    log_text: str,
    operation_id: str,
    payload_hash: str,
    *,
    expected_revision: int,
    current_revision: int,
    expected_kind: str,
) -> dict[str, Any] | None:
    matches = [receipt for receipt in _receipt_blocks(log_text) if receipt["operation_id"] == operation_id]
    if not matches:
        return None
    if len(matches) != 1:
        raise RPGStateError("operation_conflict", f"operation_id appears more than once: {operation_id}")
    receipt = matches[0]
    if receipt["payload_hash"] != payload_hash or receipt["kind"] != expected_kind:
        raise RPGStateError("operation_conflict", "operation_id was already committed with a different payload or operation type")
    expected_result = expected_revision + (1 if expected_kind == "durable" else 0)
    if receipt["revision"] != expected_result or current_revision != expected_result:
        raise RPGStateError("stale_revision", "operation retry is no longer the latest continuity operation")
    return receipt


def _stale_error(expected: Any, found: int) -> RPGStateError:
    return RPGStateError(
        "stale_revision",
        f"expected continuity revision {expected}, found {found}",
        extra={"next_expected_revision": found},
    )


def _parse_open_choices(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_OPEN_CHOICES:
        raise RPGStateError("input_invalid", f"{label} must list 1 to {MAX_OPEN_CHOICES} short choices")
    return [
        _one_line(item, f"{label}[{position}]", maximum=MAX_OPEN_CHOICE_TEXT) for position, item in enumerate(value)
    ]


def _parse_checkpoint(value: Any, label: str = "checkpoint", *, scene_boundary: bool = False) -> dict[str, Any]:
    """A checkpoint's scene frame; a scene-checkpoint boundary must also name its open choices."""

    if not isinstance(value, dict):
        raise RPGStateError("input_invalid", f"{label} must be an object")
    _require_keys(value, {"scene_id", "scene_mode", "resume_anchor", "active_cast_handoff", "open_choices"}, label)
    scene_mode = _one_line(value.get("scene_mode"), f"{label}.scene_mode", maximum=40)
    if scene_mode not in SCENE_MODES:
        raise RPGStateError(
            "input_invalid", f"{label}.scene_mode is invalid; use one of: {', '.join(sorted(SCENE_MODES))}"
        )
    parsed: dict[str, Any] = {
        "scene_id": _one_line(value.get("scene_id"), f"{label}.scene_id", maximum=160),
        "scene_mode": scene_mode,
        "resume_anchor": _one_line(value.get("resume_anchor"), f"{label}.resume_anchor"),
        "active_cast_handoff": _one_line(value.get("active_cast_handoff"), f"{label}.active_cast_handoff"),
    }
    if value.get("open_choices") is not None:
        parsed["open_choices"] = _parse_open_choices(value["open_choices"], f"{label}.open_choices")
    elif scene_boundary:
        raise RPGStateError(
            "checkpoint_open_choices_missing",
            f"a scene checkpoint must carry {label}.open_choices: 1 to {MAX_OPEN_CHOICES} short lines naming "
            "what the Player can do next; they replace current_scene.open_choices",
        )
    return parsed


CONTEST_TOKENS = frozenset({"contest", "contested", "conflict", "clash", "duel", "roll"})


def _dice_mode(root: Path) -> str:
    """Read the campaign's dice mode.

    Returns an empty string when the profile or its mechanics block is absent, so
    legacy campaigns without the block keep their previous behavior.
    """
    try:
        profile_text = _read_text(root / "play_profile.yaml", "play profile")
        return _nested_scalar(profile_text, "mechanics", "dice_mode")
    except RPGStateError:
        return ""


def _required_authorities(kind: str) -> list[str]:
    tokens = {token for token in re.split(r"[_-]+", kind) if token}
    return [owner for keywords, owner in KIND_AUTHORITY_TOKENS if tokens & keywords]


def _parse_changes(root: Path, value: Any) -> tuple[list[dict[str, Any]], set[str], list[str]]:
    if not isinstance(value, list) or not value:
        raise RPGStateError("input_invalid", "changes must be a non-empty array")
    if len(value) > MAX_CHANGES:
        raise RPGStateError("input_invalid", f"changes exceeds the limit of {MAX_CHANGES}")
    parsed: list[dict[str, Any]] = []
    ids: set[str] = set()
    owners: set[str] = set()
    all_cold: list[str] = []
    rolls_expected = _dice_mode(root) not in {"", "judgment_only"}
    for index, raw in enumerate(value):
        label = f"changes[{index}]"
        if not isinstance(raw, dict):
            raise RPGStateError("input_invalid", f"{label} must be an object")
        _require_keys(raw, {"id", "kind", "established_delta", "owners", "cold_targets", "roll_reference", "outcome"}, label)
        change_id = _one_line(raw.get("id"), f"{label}.id", maximum=80)
        if CHANGE_ID_RE.fullmatch(change_id) is None or change_id in ids:
            raise RPGStateError("input_invalid", f"{label}.id must be a unique safe identifier")
        ids.add(change_id)
        kind = _one_line(raw.get("kind"), f"{label}.kind", maximum=64)
        if KIND_RE.fullmatch(kind) is None:
            raise RPGStateError("input_invalid", f"{label}.kind must be a lowercase slug")
        delta = _one_line(raw.get("established_delta"), f"{label}.established_delta")
        raw_owners = raw.get("owners")
        if not isinstance(raw_owners, list) or not raw_owners:
            raise RPGStateError("input_invalid", f"{label}.owners must be a non-empty array")
        parsed_owners: list[str] = []
        for owner_index, owner in enumerate(raw_owners):
            relative, _ = _owner_path(root, owner, f"{label}.owners[{owner_index}]")
            if relative in parsed_owners:
                raise RPGStateError("input_invalid", f"{label}.owners contains duplicate path {relative}")
            parsed_owners.append(relative)
            owners.add(relative)
        roll_reference = ""
        if raw.get("roll_reference") is not None:
            roll_reference = _one_line(raw.get("roll_reference"), f"{label}.roll_reference", maximum=200)
        outcome = ""
        if raw.get("outcome") is not None:
            outcome = _one_line(raw.get("outcome"), f"{label}.outcome", maximum=80)
            if not roll_reference:
                raise RPGStateError("input_invalid", f"{label}.outcome names a roll band, so it needs roll_reference")
        if rolls_expected and {token for token in re.split(r"[_-]+", kind) if token} & CONTEST_TOKENS and not roll_reference:
            raise RPGStateError(
                "input_invalid",
                f"{label}.kind '{kind}' records a contested outcome while dice resolution is active, "
                f"so it requires roll_reference from the recorded roll. Roll first, or use a kind that "
                f"matches an uncontested result.",
            )
        for authority in _required_authorities(kind):
            if authority not in parsed_owners:
                raise RPGStateError(
                    "input_invalid",
                    f"{label}.kind '{kind}' requires {authority} in owners: add {authority} to this change's "
                    f"owners and include its mutation in the same commit; a cold target does not satisfy it.",
                )
        raw_cold = raw.get("cold_targets", [])
        if not isinstance(raw_cold, list):
            raise RPGStateError("input_invalid", f"{label}.cold_targets must be an array")
        parsed_cold: list[dict[str, str]] = []
        seen_cold: set[str] = set()
        for cold_index, cold in enumerate(raw_cold):
            cold_label = f"{label}.cold_targets[{cold_index}]"
            if not isinstance(cold, dict):
                raise RPGStateError("input_invalid", f"{cold_label} must be an object")
            _require_keys(cold, {"path", "reason"}, cold_label)
            path = _cold_path(root, cold.get("path"), f"{cold_label}.path")
            if path in seen_cold:
                raise RPGStateError("input_invalid", f"{label}.cold_targets contains duplicate path {path}")
            seen_cold.add(path)
            reason = _one_line(cold.get("reason"), f"{cold_label}.reason")
            parsed_cold.append({"path": path, "reason": reason})
            all_cold.append(path)
        parsed.append(
            {
                "id": change_id,
                "kind": kind,
                "established_delta": delta,
                "owners": parsed_owners,
                "cold_targets": parsed_cold,
                "roll_reference": roll_reference,
                "outcome": outcome,
            }
        )
    return parsed, owners, all_cold


def _note_title(text: str) -> str:
    match = re.search(r"(?m)^#[ \t]+(.+?)[ \t]*$", text)
    return match.group(1).strip() if match else ""


def _entity_titles(root: Path, *, exclude: str) -> list[str]:
    titles: list[str] = []
    for directory in sorted(ENTITY_OWNER_DIRS):
        folder = root / directory
        if not folder.is_dir():
            continue
        for note in sorted(folder.glob("*.md")):
            relative = note.relative_to(root).as_posix()
            if note.name.startswith("_") or relative == exclude:
                continue
            title = _note_title(repog_runtime.read_text(note)) or note.stem.replace("_", " ")
            titles.append(title)
    return titles


def _table_names(text: str, columns: tuple[int, ...]) -> list[str]:
    names: list[str] = []
    for line in text.splitlines():
        if not line.lstrip().startswith("|") or re.fullmatch(r"\s*\|[\s:|-]+\|?\s*", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        names.extend(cells[index] for index in columns if index < len(cells) and cells[index])
    return names


def _known_names(root: Path, *, exclude: str, own_title: str) -> list[str]:
    """Names already in use: note titles, ledger entries, cast and relationship rows."""

    names = _entity_titles(root, exclude=exclude)
    ledger = repog_runtime.read_text(root / "creation_ledger.md")
    names.extend(match.group(1).strip() for match in re.finditer(r"(?m)^-\s+([^|\n]+?)\s*\|", ledger))
    names.extend(_table_names(repog_runtime.read_text(root / "active_cast.md"), (0,)))
    names.extend(_table_names(repog_runtime.read_text(root / "relationship_map.md"), (0, 2)))
    header_words = {"npc", "from", "to", "name", "example npc", "-", "—"}
    seen: set[str] = set()
    unique: list[str] = []
    for name in names:
        key = name.casefold()
        if key in header_words or key == own_title.casefold() or key in seen or len(name) > 80:
            continue
        seen.add(key)
        unique.append(name)
    return unique


def _play_language(root: Path, sample: str) -> str:
    code = repog_runtime.runtime_settings(root).get("language", "auto")
    if code not in {"", "auto"}:
        return code
    lint = repog_runtime.read_json(root / repog_runtime.RUNTIME_DIR / "lint_last.json", {})
    if isinstance(lint, dict) and isinstance(lint.get("language"), str) and lint["language"]:
        return lint["language"]
    return lang_pack.detect_language(sample)[0] or "en"


def _note_findings(root: Path, relative: str, text: str) -> list[dict[str, str]]:
    """The full check's note rules, run on a new character note right away.

    A note the writer accepts would otherwise fail the full check only at the
    next distill, when its gaps are expensive to fix. Advisory here: the GM
    fills the named fields in the next commit that touches the note.
    """

    if PurePosixPath(relative).parts[0] != "characters":
        return []
    import tempfile as _tempfile

    checker = _candidate_checker()
    state = repog_runtime.read_text(root / "current_state.yaml")
    profile = repog_runtime.read_text(root / "play_profile.yaml")
    level_band = repog_runtime.block_scalars(state, "player").get("level_band", "")
    grounding = repog_runtime.block_scalars(profile, "mechanics").get("resolution_grounding", "fictional")
    # The note is checked in a scratch folder, so pass the campaign's own tier
    # caps and stat scale; otherwise a 0-20 campaign would get 1-5 warnings the
    # full check never reports.
    try:
        caps = checker._content_checks().tier_caps(repog_runtime.read_text(root / "rules.md"))
    except Exception:
        caps = {}
    findings: list[dict] = []
    with _tempfile.TemporaryDirectory() as temporary, checker._configured_stat_scale(root):
        folder = Path(temporary) / "characters"
        folder.mkdir()
        (folder / PurePosixPath(relative).name).write_bytes(text.encode("utf-8"))
        checker._check_character_notes(
            Path(temporary),
            level_band,
            findings,
            resolution_grounding=grounding or "fictional",
            ready=True,
            contract_v3=True,
            caps=caps,
        )
    return [
        {
            "rule": "note_incomplete",
            "path": relative,
            "message": f"{item.get('rule', 'note')}: {item.get('message', '')}",
        }
        for item in findings
        if item.get("severity") in {"error", "warning"}
    ]


def _name_warnings(root: Path, relative: str, text: str) -> list[dict[str, str]]:
    """Advisory checks for a new entity; never blocks a commit.

    Flags a name that equals a common word of the play language (a character
    called "Tam" in Turkish reads as "exactly"), a name one or two letters away
    from one already in use (Corran / Corlan), and note fields the full check
    will require.
    """

    try:
        title = _note_title(text) or PurePosixPath(relative).stem.replace("_", " ")
        code = _play_language(root, text)
        existing = _known_names(root, exclude=relative, own_title=title)
        findings = name_check.check_name(title, existing, lang_pack.load_pack(code))
    except Exception:  # an advisory check must never break a commit
        return []
    warnings = [
        {"rule": str(item.get("rule", "name_check")), "path": relative, "message": str(item.get("message", ""))}
        for item in findings
        if item.get("level", "warning") == "warning"
    ]
    try:
        warnings.extend(_note_findings(root, relative, text))
    except Exception:  # advisory only
        pass
    return warnings


LABEL_PREFIX_RE = re.compile(r"^\s*(?:[-*+]\s+)?(?:\*\*)?[^\s:|#][^:|\n]{0,48}:(?:\*\*)?[ \t]+")


def _prose_sample(text: str, template: frozenset[str] = frozenset()) -> str:
    """Record text without its structure, for language detection.

    Drops comments, fenced blocks, headings, table headers and separators, and
    `- Label:` prefixes, which stay in English by design. `template` holds the
    record template's lines: guidance a note keeps verbatim is not content.
    """

    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    kept: list[str] = []
    fenced = False
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if owner_ops.FENCE_RE.match(line):
            fenced = not fenced
            continue
        if fenced or owner_ops.HEADING_RE.match(stripped):
            continue
        from_template = " ".join(stripped.split()) in template
        if stripped.startswith("|"):
            if in_table and not owner_ops.TABLE_SEPARATOR_RE.match(stripped) and not from_template:
                kept.append(" ".join(stripped.strip("|").split("|")))
            in_table = True  # the first row of a table is its header
            continue
        in_table = False
        if not from_template:
            kept.append(LABEL_PREFIX_RE.sub("", line))
    return "\n".join(kept)


def _template_sources(relative: str) -> tuple[str, ...]:
    """The templates a record starts from: its folder's note templates, or its own."""

    if "/" in relative:
        folder = relative.split("/", 1)[0]
        return f"{folder}/_template.md", f"{folder}/_companion_template.md"
    return (relative,)


@lru_cache(maxsize=32)
def _template_lines(source: str) -> frozenset[str]:
    """A shipped template's lines, whitespace-normalized; empty when there is no such template."""

    text = repog_runtime.read_text(TEMPLATE_DIR / source)
    return frozenset(" ".join(line.split()) for line in text.splitlines() if line.strip())


def _record_template(relative: str) -> frozenset[str]:
    return frozenset().union(*(_template_lines(source) for source in _template_sources(relative)))


def _records_language(root: Path) -> str:
    """The code record content is written in, or "" when it cannot be known.

    `narration.records_language`, or the play language when that field is
    `same` or missing; an `auto` play language falls back to the language the
    presentation lint last saw in the replies.
    """

    # One resolver for the writer and the full check, so they cannot drift.
    return lang_pack.campaign_records_language(root)


def _other_language(text: str, expected: str, template: frozenset[str] = frozenset()) -> str:
    """The pack language `text` is confidently written in when it is not `expected`; else ""."""

    if not expected or expected not in lang_pack.available_codes():
        return ""
    code, confidence = lang_pack.detect_language(_prose_sample(text, template))
    if code and code != expected and confidence >= RECORD_LANGUAGE_CONFIDENCE:
        return code
    return ""


def _mutation_texts(raw: dict[str, Any]) -> list[str]:
    """The new prose a mutation writes: its create_text, or its replace_section and append text."""

    if isinstance(raw.get("create_text"), str):
        return [raw["create_text"]]
    ops = raw.get("ops") if isinstance(raw.get("ops"), list) else []
    return [
        op["text"]
        for op in ops
        if isinstance(op, dict) and op.get("op") in {"replace_section", "append"} and isinstance(op.get("text"), str)
    ]


def _foreign_title_words(title: str, play_code: str) -> dict[str, list[str]]:
    """Title words that are function or common words of another pack language, by code."""

    play_pack = lang_pack.load_pack(play_code)
    own = set(lang_pack.words(" ".join(play_pack.get("stopwords", []) + play_pack.get("common_words", [])), play_pack))
    found: dict[str, list[str]] = {}
    for code in lang_pack.available_codes():
        if code == play_code:
            continue
        pack = lang_pack.load_pack(code)
        vocabulary = set(lang_pack.words(" ".join(pack.get("stopwords", []) + pack.get("common_words", [])), pack))
        hits = [word for word in lang_pack.words(title, pack) if len(word) > 1 and word in vocabulary and word not in own]
        if hits:
            found[code] = hits
    return found


def _glossary_suggestion(root: Path, relative: str, text: str) -> list[dict[str, Any]]:
    """Advisory: a new note named or written in another language gets a ready glossary row."""

    title = _note_title(text) or PurePosixPath(relative).stem.replace("_", " ")
    if title.casefold() in repog_runtime.read_text(root / "glossary.md").casefold():
        return []
    play_code = lang_pack.normalize_code(_play_language(root, text))
    foreign = _foreign_title_words(title, play_code)
    if foreign:
        reason = "the title uses " + ", ".join(f"{code} word(s) {', '.join(words)}" for code, words in foreign.items())
    else:
        code = _other_language(text, play_code, _record_template(relative))
        if not code:
            return []
        reason = f"the note is written in {code}, not {play_code}"
    return [
        {
            "rule": "glossary_suggest",
            "path": relative,
            "message": (
                f"'{title}': {reason}; if the name recurs, add this row to glossary.md Terms with the "
                f"{play_code} form in Preferred"
            ),
            "row": {"Term": title, "Preferred": "", "Variants": "", "Notes": f"first named in {relative}"},
        }
    ]


def _mutation_advice(root: Path, relative: str, raw: dict[str, Any], records_code: str) -> list[dict[str, Any]]:
    """Advisory warnings about how a mutation writes, never about what it says."""

    warnings: list[dict[str, Any]] = []
    texts = _mutation_texts(raw)
    try:
        code = _other_language("\n".join(texts), records_code, _record_template(relative)) if texts else ""
        if code:
            warnings.append(
                {
                    "rule": "record_language",
                    "path": relative,
                    "message": (
                        f"{relative}: the new text reads as {code}, but records are written in {records_code}; "
                        "write the content in the records language and keep headings, labels and enum values as they are"
                    ),
                }
            )
        if "create_text" in raw:
            warnings.extend(_glossary_suggestion(root, relative, raw["create_text"]))
    except Exception:  # an advisory check must never break a commit
        pass
    return warnings


def _parse_void_rolls(value: Any) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > MAX_VOID_ROLLS:
        raise RPGStateError("input_invalid", f"void_rolls must be an array of at most {MAX_VOID_ROLLS} objects")
    parsed: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw in enumerate(value):
        label = f"void_rolls[{index}]"
        if not isinstance(raw, dict):
            raise RPGStateError("input_invalid", f"{label} must be an object with roll_id and reason")
        _require_keys(raw, {"roll_id", "reason"}, label)
        roll_id = _one_line(raw.get("roll_id"), f"{label}.roll_id", maximum=80)
        if roll_id in seen:
            raise RPGStateError("input_invalid", f"{label}.roll_id repeats {roll_id}")
        seen.add(roll_id)
        parsed.append({"roll_id": roll_id, "reason": _one_line(raw.get("reason"), f"{label}.reason", maximum=300)})
    return parsed


def _receipt(root: Path, roll_id: str) -> dict[str, Any] | None:
    try:
        return roll_dice.find_receipt(root, roll_id)
    except roll_dice.RollCallError as exc:
        raise RPGStateError("campaign_invalid", f"roll receipts cannot be read: {exc}") from exc


def _usable_receipt(root: Path, roll_id: str, label: str, *, base_revision: int) -> dict[str, Any]:
    receipt = _receipt(root, roll_id)
    if receipt is None:
        raise RPGStateError(
            "input_invalid",
            f"{label} '{roll_id}' names no recorded roll; make the roll with roll_dice --campaign first",
        )
    if receipt.get("revision") != base_revision:
        raise RPGStateError(
            "input_invalid",
            f"{label} '{roll_id}' was rolled at revision {receipt.get('revision')}, but this turn starts at "
            f"revision {base_revision}; roll again under a new roll id",
        )
    if receipt.get("consumed_revision") is not None:
        raise RPGStateError(
            "input_invalid",
            f"{label} '{roll_id}' was already used by revision {receipt.get('consumed_revision')}",
        )
    return receipt


def _verify_rolls(
    root: Path,
    changes: list[dict[str, Any]],
    voided: list[dict[str, str]],
    *,
    base_revision: int,
) -> tuple[list[str], list[dict[str, str]]]:
    """Tie every roll made this turn to the commit that uses or voids it.

    A cited roll must be a recorded receipt from this turn, unused, and the
    change must name the band the roll produced; that is what stops a success
    from being narrated as a setback. A roll made this turn and neither cited
    nor voided with a reason is refused, so a result cannot be quietly
    re-rolled. Campaigns that never recorded a receipt keep the older
    free-text references, with a warning.
    """

    warnings: list[dict[str, str]] = []
    store_exists = roll_dice.receipts_path(root).is_file()
    player_rolls = _dice_mode(root) in PLAYER_ROLL_MODES
    cited: list[str] = []
    for change in changes:
        reference = change.get("roll_reference")
        if not reference:
            continue
        label = f"change {change['id']} roll_reference"
        if reference.casefold().startswith(PLAYER_ROLL_PREFIX):
            if not player_rolls:
                raise RPGStateError(
                    "input_invalid",
                    f"{label} '{reference}' names a Player's own roll, but dice_mode does not let the Player roll; "
                    "make the roll with roll_dice --campaign",
                )
            if not change.get("outcome"):
                raise RPGStateError(
                    "input_invalid",
                    f"change {change['id']} cites the Player's roll; set outcome to the band that result reached",
                )
            continue
        if not store_exists and not change.get("outcome"):
            warnings.append(
                {
                    "rule": "roll_unrecorded",
                    "path": "",
                    "message": f"change {change['id']} cites '{reference}', which is not a recorded roll receipt",
                }
            )
            continue
        receipt = _usable_receipt(root, reference, label, base_revision=base_revision)
        band = str(receipt.get("band", ""))
        if not change.get("outcome"):
            raise RPGStateError(
                "input_invalid",
                f"change {change['id']} cites roll '{reference}' (band '{band}'); set outcome to '{band}'",
            )
        if change["outcome"] != band:
            raise RPGStateError(
                "input_invalid",
                f"change {change['id']}: outcome '{change['outcome']}' does not match roll '{reference}' band "
                f"'{band}'; narrate and record the band the roll produced",
            )
        # One roll may decide several changes of the same commit.
        if receipt["roll_id"] not in cited:
            cited.append(receipt["roll_id"])
    voided_ids: list[str] = []
    for item in voided:
        receipt = _usable_receipt(root, item["roll_id"], "void_rolls entry", base_revision=base_revision)
        if receipt["roll_id"] in cited:
            raise RPGStateError("input_invalid", f"roll '{item['roll_id']}' is both cited and voided")
        voided_ids.append(receipt["roll_id"])
    if store_exists:
        try:
            pending = roll_dice.open_receipts(root, base_revision)
        except roll_dice.RollCallError as exc:
            raise RPGStateError("campaign_invalid", f"roll receipts cannot be read: {exc}") from exc
        unaccounted = sorted({str(receipt.get("roll_id")) for receipt in pending} - set(cited) - set(voided_ids))
        if unaccounted:
            raise RPGStateError(
                "rolls_unaccounted",
                f"roll(s) made this turn are not accounted for: {', '.join(unaccounted)}; cite each in a change's "
                "roll_reference with its outcome, or list it in void_rolls with a reason",
            )
    return cited + voided_ids, warnings


def _distill_path(root: Path, value: Any, label: str) -> tuple[str, Path]:
    relative, path = _relative_path(root, value, label)
    if relative in DISTILL_FORBIDDEN_FILES:
        raise RPGStateError(
            "path_forbidden",
            f"{label} cannot be edited by a distill: {relative}; new truth needs commit-durable",
        )
    if PurePosixPath(relative).parts[0] == ARCHIVE_DIR or not relative.endswith(".md"):
        raise RPGStateError("path_forbidden", f"{label} must be a campaign Markdown file outside {ARCHIVE_DIR}/")
    return relative, path


def _parse_mutations(
    root: Path,
    value: Any,
    *,
    placeholders: owner_ops.PlaceholderContext,
    distill: bool = False,
    notes: list[dict[str, str]] | None = None,
) -> tuple[dict[str, bytes], set[str]]:
    """Materialize every mutation in memory; nothing is written here.

    A mutation uses exactly one mode: `ops` (typed edits addressed by key,
    heading, or table row), `exact_replacements`, or `create_text` for a new
    entity note. `{{revision}}` and `{{next_id:PREFIX}}` placeholders resolve
    in new text for every mode.
    """

    if not isinstance(value, list):
        raise RPGStateError("input_invalid", "mutations must be an array")
    if len(value) > MAX_MUTATIONS:
        raise RPGStateError("input_invalid", f"mutations exceeds the limit of {MAX_MUTATIONS}")
    candidates: dict[str, bytes] = {}
    paths: set[str] = set()
    records_code = _records_language(root) if notes is not None else ""
    for index, raw in enumerate(value):
        label = f"mutations[{index}]"
        if not isinstance(raw, dict):
            raise RPGStateError("input_invalid", f"{label} must be an object")
        _require_keys(raw, {"path", "ops", "exact_replacements", "create_text"}, label)
        if distill:
            relative, path = _distill_path(root, raw.get("path"), f"{label}.path")
        else:
            relative, path = _owner_path(root, raw.get("path"), f"{label}.path")
        if relative == "mechanics_state.json":
            raise RPGStateError("input_invalid", "mechanics_state.json must be changed through mechanic_operations")
        paths.add(relative)
        modes = [mode for mode in ("ops", "exact_replacements", "create_text") if mode in raw]
        if not modes or ("create_text" in modes and len(modes) > 1):
            raise RPGStateError("input_invalid", f"{label} needs ops, exact_replacements, or create_text alone")
        if modes[0] == "create_text":
            if relative in candidates:
                raise RPGStateError("input_invalid", f"{label}: create_text cannot follow another edit of {relative}")
            if distill:
                raise RPGStateError("input_invalid", "a distill cannot create notes; creation is a durable change")
            pure = PurePosixPath(relative)
            if pure.parts[0] not in ENTITY_OWNER_DIRS or len(pure.parts) < 2:
                raise RPGStateError("path_forbidden", "create_text is limited to typed entity-note directories")
            if path.exists():
                raise RPGStateError("candidate_invalid", f"create target already exists: {relative}")
            if not path.parent.is_dir():
                raise RPGStateError("candidate_invalid", f"create target parent does not exist: {relative}")
            text = raw.get("create_text")
            if not isinstance(text, str) or not text.strip():
                raise RPGStateError("input_invalid", f"{label}.create_text must be non-empty text")
            text = placeholders.resolve(text, path=relative, file_text="")
            if len(text) > MAX_FILE_TEXT:
                raise RPGStateError("input_invalid", f"{label}.create_text exceeds {MAX_FILE_TEXT} characters")
            if not text.endswith("\n"):
                text += "\n"
            candidates[relative] = text.encode("utf-8")
            if notes is not None:
                notes.extend(_name_warnings(root, relative, text))
                notes.extend(_mutation_advice(root, relative, raw, records_code))
            continue

        if relative in candidates:
            # A second mutation of the same owner continues from the first.
            text = candidates[relative].decode("utf-8")
        elif relative in TEMPLATE_OWNERS and not path.exists():
            # Campaigns created before these owners existed start from the
            # blank template the first time the GM records one.
            text = _read_text(TEMPLATE_DIR / relative, f"{relative} template")
        else:
            text = _read_text(path, relative)
        original_meta = _state_meta(text) if relative == "current_state.yaml" else None
        if "exact_replacements" in modes:
            replacements = raw.get("exact_replacements")
            if not isinstance(replacements, list) or not replacements:
                raise RPGStateError("input_invalid", f"{label}.exact_replacements must be a non-empty array")
            if len(replacements) > MAX_REPLACEMENTS:
                raise RPGStateError("input_invalid", f"{label}.exact_replacements exceeds {MAX_REPLACEMENTS}")
            original_text = text
            for replacement_index, replacement in enumerate(replacements):
                replacement_label = f"{label}.exact_replacements[{replacement_index}]"
                if not isinstance(replacement, dict):
                    raise RPGStateError("input_invalid", f"{replacement_label} must be an object")
                _require_keys(replacement, {"old", "new"}, replacement_label)
                old = replacement.get("old")
                new = replacement.get("new")
                if not isinstance(old, str) or not old:
                    raise RPGStateError("input_invalid", f"{replacement_label}.old must be non-empty text")
                if not isinstance(new, str):
                    raise RPGStateError("input_invalid", f"{replacement_label}.new must be text")
                new = placeholders.resolve(new, path=relative, file_text=original_text)
                if old == new:
                    continue  # nothing to do, and not worth a refused commit
                occurrences = text.count(old)
                if occurrences != 1:
                    raise RPGStateError(
                        "candidate_invalid",
                        f"{replacement_label}.old matched {occurrences} times in {relative}; expected exactly one",
                    )
                text = text.replace(old, new, 1)
                if len(text) > MAX_FILE_TEXT:
                    raise RPGStateError("candidate_invalid", f"candidate file exceeds {MAX_FILE_TEXT} characters: {relative}")
        if "ops" in modes:
            try:
                ops = owner_ops.parse_ops(raw.get("ops"), relative=relative, label=label)
                text = owner_ops.apply_ops(text, ops, relative=relative, label=label, placeholders=placeholders)
            except owner_ops.OwnerOpError as exc:
                raise RPGStateError(exc.category, f"{relative}: {exc}") from exc
            if len(text) > MAX_FILE_TEXT:
                raise RPGStateError("candidate_invalid", f"candidate file exceeds {MAX_FILE_TEXT} characters: {relative}")
        if original_meta is not None and _state_meta(text) != original_meta:
            raise RPGStateError(
                "input_invalid",
                "current_state continuity_revision and persistence fields are helper-managed and cannot be mutated directly",
            )
        candidates[relative] = text.encode("utf-8")
        if notes is not None:
            notes.extend(_mutation_advice(root, relative, raw, records_code))
    return candidates, paths


def _fold_now(relative: str, text: str) -> tuple[str, list[dict[str, str]]]:
    """Keep an entity note's `## Now` within budget by moving old dated entries to `## History`."""

    folded, moved = owner_ops.fold_now(text)
    warnings: list[dict[str, str]] = []
    if moved:
        warnings.append(
            {
                "rule": "now_overflow_folded",
                "path": relative,
                "message": f"{relative}: moved {moved} older dated entr{'y' if moved == 1 else 'ies'} from ## Now to ## History",
                "count": moved,
            }
        )
    if owner_ops.now_over_budget(folded):
        warnings.append(
            {
                "rule": "now_overflow",
                "path": relative,
                "message": (
                    f"{relative}: ## Now is over {owner_ops.NOW_MAX_CHARS} characters with no dated entry left to "
                    "move; replace it with the current state only"
                ),
            }
        )
    return folded, warnings


def _finish_candidates(
    candidates: dict[str, bytes],
    mutation_paths: set[str],
    *,
    stamp_revision: int,
) -> list[dict[str, str]]:
    """Fold and stamp mutated Markdown owners and collect advisory curation warnings.

    An entity note's `## Now` that outgrew its budget gives its oldest dated
    entries to `## History`. A mutated owner that carries one `As of revision:
    N` line now reflects this revision, so the writer sets the stamp instead of
    the GM. Warnings never block a commit; they tell the GM which owner needs
    curating before it reaches the hard size cap or keeps contradicting itself.
    """

    warnings: list[dict[str, str]] = []
    for relative in sorted(mutation_paths):
        if not relative.endswith(".md") or relative not in candidates:
            continue
        text = candidates[relative].decode("utf-8")
        if PurePosixPath(relative).parts[0] in ENTITY_OWNER_DIRS:
            text, fold_warnings = _fold_now(relative, text)
            warnings.extend(fold_warnings)
        text = owner_ops.stamp_revision(text, stamp_revision)
        candidates[relative] = text.encode("utf-8")
        if len(text) > SIZE_WARNING_TEXT:
            warnings.append(
                {
                    "rule": "owner_size_budget",
                    "path": relative,
                    "message": (
                        f"{relative} holds {len(text)} characters (hard cap {MAX_FILE_TEXT}); "
                        "consolidate or archive superseded entries at the next distill"
                    ),
                }
            )
        if PurePosixPath(relative).parts[0] in ENTITY_OWNER_DIRS:
            for title, count in owner_ops.stacked_headings(text):
                warnings.append(
                    {
                        "rule": "stacked_sections",
                        "path": relative,
                        "message": (
                            f"{relative} has {count} sections like '{title}'; replace the current one "
                            "with replace_section instead of adding layers"
                        ),
                    }
                )
    return warnings


def _load_mechanic_module() -> Any:
    module_path = Path(__file__).with_name("resolve_mechanic.py")
    spec = importlib.util.spec_from_file_location("_repog_rpg_state_resolve_mechanic", module_path)
    if spec is None or spec.loader is None:
        raise RPGStateError("campaign_invalid", "cannot load resolve_mechanic.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _mechanic_candidate(
    root: Path,
    value: Any,
    *,
    resulting_continuity_revision: int,
) -> tuple[bytes | None, list[dict[str, Any]]]:
    if value is None:
        return None, []
    if not isinstance(value, list):
        raise RPGStateError("input_invalid", "mechanic_operations must be an array")
    if len(value) > MAX_MECHANIC_OPERATIONS:
        raise RPGStateError("input_invalid", f"mechanic_operations exceeds {MAX_MECHANIC_OPERATIONS}")
    if not value:
        return None, []
    state_path = root / "mechanics_state.json"
    try:
        state = json.loads(_read_text(state_path, "mechanics state"))
    except json.JSONDecodeError as exc:
        raise RPGStateError("campaign_invalid", f"mechanics_state.json is invalid JSON: {exc}") from exc
    if not isinstance(state, dict):
        raise RPGStateError("campaign_invalid", "mechanics_state.json must contain an object")
    module = _load_mechanic_module()
    results: list[dict[str, Any]] = []
    candidate = copy.deepcopy(state)
    for index, raw in enumerate(value):
        label = f"mechanic_operations[{index}]"
        if not isinstance(raw, dict):
            raise RPGStateError("input_invalid", f"{label} must be an object")
        forbidden = sorted(set(raw) & COORDINATOR_MECHANIC_FIELDS)
        if forbidden:
            raise RPGStateError(
                "input_invalid",
                f"{label} contains coordinator-managed field(s): {', '.join(forbidden)}",
            )
        payload = copy.deepcopy(raw)
        payload["operation_sequence"] = candidate.get("operation_sequence", 0) + 1
        payload["expected_revision"] = candidate.get("revision")
        payload["expected_continuity_revision"] = candidate.get("continuity_revision", 0)
        payload["resulting_continuity_revision"] = resulting_continuity_revision
        try:
            candidate, result = module.apply_operation(candidate, payload)
        except Exception as exc:
            raise RPGStateError("candidate_invalid", f"{label} failed: {exc}") from exc
        if result.get("duplicate"):
            raise RPGStateError("operation_conflict", f"{label} reuses an existing mechanic operation_id")
        results.append(result)
    return (json.dumps(candidate, indent=2, ensure_ascii=False) + "\n").encode("utf-8"), results


def _append_block(log_text: str, block: str) -> str:
    base = log_text.rstrip()
    return f"{base}\n\n{block.strip()}\n"


def _receipt_line(label: str, value: str) -> list[str]:
    """`- Label: value`, or nothing when the value is empty or `none`.

    Receipts carry only what happened. Older logs still hold `- Deferred
    propagation: none` and similar lines; every log reader accepts both forms.
    """

    text = value.strip()
    if not text or re.fullmatch(r"(?i)none(?:\s*[—–-].*)?", text):
        return []
    return [f"- {label}: {text}"]


def _durable_event(
    *,
    revision: int,
    operation_id: str,
    payload_hash: str,
    cause: str,
    changes: list[dict[str, Any]],
    boundary: str,
    resume_impact: str,
    voided: list[dict[str, str]] | None = None,
) -> str:
    lines = [
        f"### Durable Revision {revision}",
        "",
        f"- Operation: {operation_id}",
        *_receipt_line("Cause", cause),
        "- Established changes:",
    ]
    for change in changes:
        suffix = ""
        if change.get("roll_reference"):
            band = f" -> {change['outcome']}" if change.get("outcome") else ""
            suffix = f" (roll: {change['roll_reference']}{band})"
        lines.append(f"  - {change['id']} [{change['kind']}]: {change['established_delta']}{suffix}")
    lines.append("- Immediate authorities:")
    for change in changes:
        for owner in change["owners"]:
            lines.append(f"  - {change['id']} -> `{owner}`")
    cold_rows = [
        (change["id"], target["path"], target["reason"])
        for change in changes
        for target in change["cold_targets"]
    ]
    if cold_rows:
        lines.append("- Deferred propagation:")
        for change_id, path, reason in cold_rows:
            lines.append(f"  - {change_id} -> `{path}` — {reason}")
    if voided:
        lines.append("- Voided rolls:")
        for item in voided:
            lines.append(f"  - {item['roll_id']} — {item['reason']}")
    lines.append(f"- Boundary: {boundary}")
    lines.extend(_receipt_line("Resume impact", resume_impact))
    lines.append(f"- Payload hash: sha256:{payload_hash}")
    return "\n".join(lines)


def _checkpoint_event(
    *,
    revision: int,
    operation_id: str,
    payload_hash: str,
    checkpoint: dict[str, str],
    paired_durable: bool,
) -> str:
    operation_label = "Source operation" if paired_durable else "Operation"
    hash_label = "Source payload hash" if paired_durable else "Payload hash"
    return "\n".join(
        [
            f"### Scene Checkpoint Revision {revision}",
            "",
            f"- {operation_label}: {operation_id}",
            f"- Scene id: {checkpoint['scene_id']}",
            f"- Scene mode: {checkpoint['scene_mode']}",
            f"- Resume anchor: {checkpoint['resume_anchor']}",
            *_receipt_line("Active-cast handoff", checkpoint["active_cast_handoff"]),
            f"- {hash_label}: sha256:{payload_hash}",
        ]
    )


def _journal_root(root: Path) -> Path:
    return root / TRANSACTION_DIR


def _pid_alive(pid: int) -> bool:
    """Probe legacy lock ownership without sending a signal on Windows."""
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
        if not handle:
            return ctypes.get_last_error() != 87  # Invalid PID is certainly gone.
        try:
            return kernel.WaitForSingleObject(handle, 0) != 0
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


@contextlib.contextmanager
def _transaction_lock(root: Path) -> Iterator[None]:
    try:
        with file_transaction.campaign_lock(root):
            legacy_lock = _journal_root(root) / LOCK_FILE
            if legacy_lock.exists():
                if legacy_lock.is_symlink():
                    raise RPGStateError("recovery_required", "legacy transaction lock cannot be a link")
                try:
                    owner_pid = int(legacy_lock.read_text(encoding="ascii").strip())
                except (OSError, ValueError):
                    raise RPGStateError("recovery_required", "legacy lock owner is unreadable; inspect before recovery")
                if _pid_alive(owner_pid):
                    raise RPGStateError("transaction_busy", f"a legacy RPG writer may still be running (pid {owner_pid})")
                legacy_lock.unlink()
            yield
    except file_transaction.FileTransactionError as exc:
        raise RPGStateError(exc.category, str(exc)) from exc


def _transaction_path(root: Path, operation_id: str) -> Path:
    digest = hashlib.sha256(operation_id.encode("utf-8")).hexdigest()[:24]
    return _journal_root(root) / digest


def _prepare_journal(
    root: Path,
    operation_id: str,
    payload_hash: str,
    candidates: dict[str, bytes],
) -> tuple[Path, dict[str, Any]]:
    tx_path = _transaction_path(root, operation_id)
    if tx_path.exists():
        raise RPGStateError("recovery_required", f"transaction journal already exists for {operation_id}")
    tx_path.mkdir(parents=False)
    targets: list[dict[str, Any]] = []
    try:
        for relative in sorted(candidates):
            _, target = _relative_path(root, relative, "transaction target")
            original_exists = target.is_file()
            original = target.read_bytes() if original_exists else b""
            candidate = candidates[relative]
            original_path = tx_path / "originals" / Path(*PurePosixPath(relative).parts)
            candidate_path = tx_path / "candidates" / Path(*PurePosixPath(relative).parts)
            if original_exists:
                _atomic_bytes(original_path, original)
            _atomic_bytes(candidate_path, candidate)
            targets.append(
                {
                    "path": relative,
                    "original_exists": original_exists,
                    "original_sha256": _bytes_hash(original) if original_exists else None,
                    "candidate_sha256": _bytes_hash(candidate),
                }
            )
        manifest = {
            "manifest_version": MANIFEST_VERSION,
            "operation_id": operation_id,
            "payload_hash": payload_hash,
            "status": "prepared",
            "targets": targets,
        }
        _atomic_json(tx_path / "manifest.json", manifest)
        return tx_path, manifest
    except BaseException:
        # No campaign target is touched before the prepared manifest exists.
        shutil.rmtree(tx_path, ignore_errors=True)
        raise


def _manifest(tx_path: Path) -> dict[str, Any]:
    try:
        value = json.loads((tx_path / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RPGStateError("recovery_required", f"cannot read transaction manifest {tx_path.name}: {exc}") from exc
    if not isinstance(value, dict) or value.get("manifest_version") != MANIFEST_VERSION:
        raise RPGStateError("recovery_required", f"invalid transaction manifest: {tx_path.name}")
    if value.get("status") not in {"prepared", "committed"} or not isinstance(value.get("targets"), list):
        raise RPGStateError("recovery_required", f"invalid transaction manifest state: {tx_path.name}")
    return value


def _journal_file(tx_path: Path, family: str, relative: str) -> Path:
    return tx_path / family / Path(*PurePosixPath(relative).parts)


def _restore_manifest(root: Path, tx_path: Path, manifest: dict[str, Any], *, strict: bool) -> None:
    for record in manifest["targets"]:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise RPGStateError("recovery_required", "transaction manifest has an invalid target record")
        relative, target = _relative_path(root, record["path"], "recovery target")
        original_exists = record.get("original_exists") is True
        original_path = _journal_file(tx_path, "originals", relative)
        candidate_path = _journal_file(tx_path, "candidates", relative)
        try:
            candidate = candidate_path.read_bytes()
            original = original_path.read_bytes() if original_exists else None
        except OSError as exc:
            raise RPGStateError("recovery_required", f"transaction journal payload is missing: {relative}: {exc}") from exc
        if _bytes_hash(candidate) != record.get("candidate_sha256"):
            raise RPGStateError("recovery_required", f"transaction candidate hash mismatch: {relative}")
        if original is not None and _bytes_hash(original) != record.get("original_sha256"):
            raise RPGStateError("recovery_required", f"transaction original hash mismatch: {relative}")
        if strict:
            current = target.read_bytes() if target.is_file() else None
            allowed = {record.get("candidate_sha256")}
            if original is not None:
                allowed.add(record.get("original_sha256"))
            elif current is None:
                allowed.add(None)
            current_hash = _bytes_hash(current) if current is not None else None
            if current_hash not in allowed:
                raise RPGStateError("recovery_required", f"campaign target changed outside the unfinished transaction: {relative}")
        if original is None:
            target.unlink(missing_ok=True)
        else:
            _atomic_bytes(target, original)


def _verify_committed(root: Path, tx_path: Path, manifest: dict[str, Any]) -> None:
    for record in manifest["targets"]:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise RPGStateError("recovery_required", "committed transaction manifest has an invalid target")
        relative, target = _relative_path(root, record["path"], "committed target")
        try:
            current = target.read_bytes()
        except OSError as exc:
            raise RPGStateError("recovery_required", f"committed target is missing: {relative}: {exc}") from exc
        if _bytes_hash(current) != record.get("candidate_sha256"):
            raise RPGStateError("recovery_required", f"committed target hash mismatch: {relative}")
        candidate_path = _journal_file(tx_path, "candidates", relative)
        try:
            candidate = candidate_path.read_bytes()
        except OSError as exc:
            raise RPGStateError("recovery_required", f"committed candidate is missing: {relative}: {exc}") from exc
        if _bytes_hash(candidate) != record.get("candidate_sha256"):
            raise RPGStateError("recovery_required", f"committed candidate hash mismatch: {relative}")


def _recover_transactions(root: Path) -> list[str]:
    journal_root = _journal_root(root)
    if not journal_root.exists():
        return []
    recovered: list[str] = []
    for tx_path in sorted(path for path in journal_root.iterdir() if path.is_dir()):
        if tx_path.name == file_transaction.JOURNAL_DIR:
            continue
        if (
            tx_path.is_symlink()
            or tx_path.resolve() != journal_root.resolve() / tx_path.name
            or not re.fullmatch(r"[0-9a-f]{24}", tx_path.name)
        ):
            raise RPGStateError("recovery_required", "unexpected legacy transaction storage entry")
        manifest_path = tx_path / "manifest.json"
        if not manifest_path.is_file():
            # Staging cannot touch campaign targets before this manifest exists.
            shutil.rmtree(tx_path, ignore_errors=True)
            continue
        manifest = _manifest(tx_path)
        operation_id = str(manifest.get("operation_id", tx_path.name))
        if manifest["status"] == "prepared":
            _restore_manifest(root, tx_path, manifest, strict=True)
        else:
            _verify_committed(root, tx_path, manifest)
        try:
            shutil.rmtree(tx_path)
        except OSError as exc:
            raise RPGStateError("recovery_required", f"cannot clean recovered transaction {operation_id}: {exc}") from exc
        recovered.append(operation_id)
    recovered.extend(file_transaction.recover(root))
    return recovered


def _apply_candidate_file(path: Path, payload: bytes) -> None:
    """Replace one campaign target; isolated for failure-injection tests."""

    _atomic_bytes(path, payload)


@lru_cache(maxsize=1)
def _candidate_checker() -> Any:
    module_path = Path(__file__).with_name("check_state.py")
    spec = importlib.util.spec_from_file_location("_repog_candidate_checks", module_path)
    if spec is None or spec.loader is None:
        raise RPGStateError("campaign_invalid", "cannot load changed-owner structural validation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _commit_candidates(
    root: Path,
    *,
    operation_id: str,
    payload_hash: str,
    candidates: dict[str, bytes],
    prevalidated: frozenset[str] = frozenset(),
) -> None:
    # `prevalidated` owners were checked by the caller in a way the one-step
    # owner check cannot express (an act closing and its successor opening).
    checked = {relative: payload for relative, payload in candidates.items() if relative not in prevalidated}
    findings = _candidate_checker().check_changed_owners(root, checked)
    errors = [finding for finding in findings if finding["severity"] == "error"]
    if errors:
        detail = "; ".join(f"{item['rule']}: {item['message']}" for item in errors)
        raise RPGStateError("candidate_invalid", detail)
    tx_path, manifest = _prepare_journal(root, operation_id, payload_hash, candidates)
    order = sorted(candidates, key=lambda item: (item == "current_state.yaml", item))
    try:
        for relative in order:
            _, target = _relative_path(root, relative, "commit target")
            _apply_candidate_file(target, candidates[relative])
        committed = {**manifest, "status": "committed"}
        _atomic_json(tx_path / "manifest.json", committed)
    except Exception as exc:
        try:
            _restore_manifest(root, tx_path, manifest, strict=False)
            shutil.rmtree(tx_path)
        except Exception as rollback_exc:
            raise RPGStateError(
                "recovery_required",
                f"RPG commit failed and rollback was incomplete: {exc}; rollback error: {rollback_exc}",
            ) from exc
        raise RPGStateError("commit_rolled_back", f"RPG commit failed and was rolled back: {exc}") from exc
    try:
        shutil.rmtree(tx_path)
    except OSError:
        # The committed marker makes deferred cleanup deterministic and safe.
        pass


def _merge_pending(existing: list[str], additions: list[str]) -> list[str]:
    merged = list(existing)
    seen = set(existing)
    for item in additions:
        if item not in seen:
            merged.append(item)
            seen.add(item)
    return merged


DURABLE_PAYLOAD_FIELDS = {
    "operation_id",
    "expected_continuity_revision",
    "boundary",
    "cause",
    "resume_impact",
    "changes",
    "mutations",
    "checkpoint",
    "mechanic_operations",
    "void_rolls",
}
CHECKPOINT_PAYLOAD_FIELDS = {"operation_id", "expected_continuity_revision", "mutations", "checkpoint"}


def _durable_identity(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate only fields needed before retry/recovery materializes mutations."""

    _require_keys(payload, DURABLE_PAYLOAD_FIELDS, "commit-durable payload")
    operation_id = _operation_id(payload.get("operation_id"))
    expected = payload.get("expected_continuity_revision")
    if not _strict_int(expected):
        raise RPGStateError("input_invalid", "expected_continuity_revision must be a non-negative integer")
    boundary = _one_line(payload.get("boundary"), "boundary", maximum=40)
    if boundary not in BOUNDARIES:
        raise RPGStateError("input_invalid", f"boundary must be one of: {', '.join(sorted(BOUNDARIES))}")
    checkpoint = payload.get("checkpoint") is not None
    if boundary == "scene_checkpoint" and not checkpoint:
        raise RPGStateError("input_invalid", "scene_checkpoint boundary requires checkpoint data")
    if boundary == "ordinary" and checkpoint:
        raise RPGStateError("input_invalid", "ordinary boundary cannot include a checkpoint")
    return {
        "operation_id": operation_id,
        "expected_revision": expected,
        "boundary": boundary,
        "checkpoint": checkpoint,
    }


def _checkpoint_identity(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate checkpoint identity before retry/recovery reads mutation targets."""

    _require_keys(payload, CHECKPOINT_PAYLOAD_FIELDS, "commit-checkpoint payload")
    operation_id = _operation_id(payload.get("operation_id"))
    expected = payload.get("expected_continuity_revision")
    if not _strict_int(expected):
        raise RPGStateError("input_invalid", "expected_continuity_revision must be a non-negative integer")
    return {"operation_id": operation_id, "expected_revision": expected}


def _names_in(name: str, text: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text, re.IGNORECASE) is not None


def _handoff_error(root: Path, handoff: str) -> RPGStateError:
    """The refusal for a handoff without an active_cast.md mutation, carrying a ready op.

    The op has one `upsert_row` per cast-row or character name the handoff
    mentions, prefilled with that row's current cells, so the GM edits only
    what changed. It never guesses where anyone went.
    """

    header, rows = owner_ops.table_rows(repog_runtime.read_text(root / "active_cast.md"))
    width = len(header)
    known = {row[0]: row for row in rows if row and row[0]}
    folder = root / "characters"
    for note in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        if not note.name.startswith("_"):
            known.setdefault(_note_title(repog_runtime.read_text(note)) or note.stem.replace("_", " "), [])
    ops: list[dict[str, Any]] = []
    for name, row in known.items():
        if width and _names_in(name, handoff):
            cells = (row + [""] * width)[:width] if row else [name] + [""] * (width - 1)
            ops.append({"op": "upsert_row", "key": name, "cells": cells})
    if width and not ops:
        ops.append({"op": "upsert_row", "key": "<name>", "cells": ["<name>"] + [""] * (width - 1)})
    mutation = {"path": "active_cast.md", "ops": ops}
    reason = "non-empty active-cast handoff requires an active_cast.md mutation"
    if ops:
        reason += (
            f"; add this mutation with the changed cells filled in (columns: {' | '.join(header)}): "
            + json.dumps(mutation, ensure_ascii=False)
        )
    return RPGStateError("input_invalid", reason, extra={"suggested_mutation": mutation} if ops else None)


def _validate_durable_payload(
    root: Path,
    payload: dict[str, Any],
    *,
    revision: int,
    act_mutations: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    identity = _durable_identity(payload)
    operation_id = identity["operation_id"]
    expected = identity["expected_revision"]
    boundary = identity["boundary"]
    cause = _one_line(payload.get("cause"), "cause")
    # Optional: the scene frame's resume anchor usually says it already.
    resume_impact = "" if payload.get("resume_impact") in (None, "") else _one_line(payload["resume_impact"], "resume_impact")
    changes, owners, cold_targets = _parse_changes(root, payload.get("changes"))
    notes: list[dict[str, str]] = []
    mutations, mutation_paths = _parse_mutations(
        root,
        payload.get("mutations", []),
        placeholders=owner_ops.PlaceholderContext(revision),
        notes=notes,
    )
    for relative, candidate in (act_mutations or {}).items():
        if relative in mutation_paths:
            raise RPGStateError("input_invalid", f"commit-act writes {relative} itself; remove that mutation")
        mutations[relative] = candidate
        mutation_paths.add(relative)
    void_rolls = _parse_void_rolls(payload.get("void_rolls"))
    checkpoint_raw = payload.get("checkpoint")
    checkpoint = (
        _parse_checkpoint(checkpoint_raw, scene_boundary=boundary == "scene_checkpoint")
        if checkpoint_raw is not None
        else None
    )
    if boundary == "scene_checkpoint" and checkpoint is None:
        raise RPGStateError("input_invalid", "scene_checkpoint boundary requires checkpoint data")
    if boundary == "ordinary" and checkpoint is not None:
        raise RPGStateError("input_invalid", "ordinary boundary cannot include a checkpoint")
    if checkpoint is not None:
        # The writer copies scene_id, mode, and resume anchor into the scene
        # frame itself, so a checkpoint no longer needs its own state mutation.
        if checkpoint["active_cast_handoff"].lower() != "none" and "active_cast.md" not in mutation_paths:
            raise _handoff_error(root, checkpoint["active_cast_handoff"])
    mechanic_operations = payload.get("mechanic_operations", [])
    if mechanic_operations is None:
        mechanic_operations = []
    if not isinstance(mechanic_operations, list):
        raise RPGStateError("input_invalid", "mechanic_operations must be an array")
    effective_paths = set(mutation_paths)
    if mechanic_operations:
        effective_paths.add("mechanics_state.json")
    missing_owners = sorted(owners - effective_paths)
    if missing_owners:
        raise RPGStateError("input_invalid", f"declared owner has no immediate mutation: {', '.join(missing_owners)}")
    permitted_unowned = {"current_state.yaml", "active_cast.md"} if checkpoint is not None else set()
    unowned_mutations = sorted(mutation_paths - owners - permitted_unowned)
    if unowned_mutations:
        raise RPGStateError("input_invalid", f"mutation has no established-change owner: {', '.join(unowned_mutations)}")
    if mechanic_operations and "mechanics_state.json" not in owners:
        raise RPGStateError("input_invalid", "mechanic_operations require mechanics_state.json as a declared owner")
    return {
        "operation_id": operation_id,
        "expected_revision": expected,
        "boundary": boundary,
        "cause": cause,
        "resume_impact": resume_impact,
        "changes": changes,
        "cold_targets": cold_targets,
        "mutations": mutations,
        "mutation_paths": mutation_paths,
        "checkpoint": checkpoint,
        "mechanic_operations": mechanic_operations,
        "void_rolls": void_rolls,
        "notes": notes,
    }


def _validate_checkpoint_payload(root: Path, payload: dict[str, Any], *, revision: int) -> dict[str, Any]:
    identity = _checkpoint_identity(payload)
    operation_id = identity["operation_id"]
    expected = identity["expected_revision"]
    checkpoint = _parse_checkpoint(payload.get("checkpoint"))
    notes: list[dict[str, str]] = []
    mutations, mutation_paths = _parse_mutations(
        root,
        payload.get("mutations", []),
        placeholders=owner_ops.PlaceholderContext(revision),
        notes=notes,
    )
    # Directives and glossary rows are table preferences, not fiction, so an
    # OOC-only change can ride a checkpoint instead of a durable revision.
    invalid_paths = sorted(mutation_paths - {"current_state.yaml", "active_cast.md", "directives.md", "glossary.md"})
    if invalid_paths:
        raise RPGStateError("input_invalid", f"soft checkpoint cannot mutate durable owner files: {', '.join(invalid_paths)}")
    if checkpoint["active_cast_handoff"].lower() != "none" and "active_cast.md" not in mutation_paths:
        raise _handoff_error(root, checkpoint["active_cast_handoff"])
    return {
        "operation_id": operation_id,
        "expected_revision": expected,
        "checkpoint": checkpoint,
        "mutations": mutations,
        "notes": notes,
    }


def _idempotent_result(
    *,
    operation: str,
    operation_id: str,
    meta: dict[str, Any],
    boundary: str,
    checkpoint: bool,
    recovered: list[str],
) -> dict[str, Any]:
    required, reason = _distill_requirement(
        meta["cold_distill_policy"],
        meta["durable_turns_since_distill"],
        boundary=boundary,
        checkpoint=checkpoint,
    )
    return {
        "ok": True,
        "operation": operation,
        "idempotent": True,
        "operation_id": operation_id,
        "continuity_revision": meta["revision"],
        "next_expected_revision": meta["revision"],
        "durable_turns_since_distill": meta["durable_turns_since_distill"],
        "pending_cold_targets": meta["pending_cold_targets"],
        "checkpoint_committed": checkpoint,
        "full_distill_required": required,
        "narration_allowed": not required,
        "distill_reason": reason,
        "reply": _reply_note(not required),
        "changed_files": [],
        "mechanic_results": [],
        "recovered_transactions": recovered,
        "warnings": [],
    }


def _sync_scene_frame(candidates: dict[str, bytes], state_text: str, checkpoint: dict[str, Any]) -> None:
    """Write the checkpoint's scene id, mode, anchor, and open choices into current_state.yaml."""

    base = candidates["current_state.yaml"].decode("utf-8") if "current_state.yaml" in candidates else state_text
    try:
        synced = owner_ops.set_scene_frame(
            base,
            scene_id=checkpoint["scene_id"],
            scene_mode=checkpoint["scene_mode"],
            resume_anchor=checkpoint["resume_anchor"],
        )
        if "open_choices" in checkpoint:
            synced = owner_ops.set_open_choices(synced, checkpoint["open_choices"])
    except owner_ops.OwnerOpError as exc:
        raise RPGStateError(exc.category, f"current_state.yaml: {exc}") from exc
    candidates["current_state.yaml"] = synced.encode("utf-8")


def _status_word(text: str) -> str:
    """The first word of a note's Core status: "dead" from "dead (drowned)"."""

    words = owner_ops.core_status(text).split()
    return words[0].strip(".,;:()") if words else ""


def _death_projection(root: Path, candidates: dict[str, bytes], mutation_paths: set[str]) -> list[dict[str, Any]]:
    """Advisory: a note newly marked dead or missing whose name still fills unchanged rows.

    Looks only at `active_cast.md` and `relationship_map.md` rows this payload
    left untouched; what those rows should now say is the GM's call.
    """

    warnings: list[dict[str, Any]] = []
    for relative in sorted(mutation_paths):
        if PurePosixPath(relative).parts[0] not in ENTITY_OWNER_DIRS or relative not in candidates:
            continue
        text = candidates[relative].decode("utf-8")
        status = _status_word(text)
        if status not in {"dead", "missing"} or _status_word(repog_runtime.read_text(root / relative)) == status:
            continue
        title = _note_title(text) or PurePosixPath(relative).stem.replace("_", " ")
        rows: list[dict[str, str]] = []
        for owner in ("active_cast.md", "relationship_map.md"):
            original = repog_runtime.read_text(root / owner)
            current = candidates[owner].decode("utf-8") if owner in candidates else original
            unchanged = set(original.splitlines())
            rows.extend(
                {"path": owner, "row": line.strip()}
                for line in current.splitlines()
                if line.lstrip().startswith("|") and line in unchanged and _names_in(title, line)
            )
        if rows:
            listed = "; ".join(f"{item['path']}: {item['row']}" for item in rows)
            warnings.append(
                {
                    "rule": "death_projection",
                    "path": relative,
                    "message": f"{title} is now {status}, but these rows still name them unchanged: {listed}",
                    "rows": rows,
                }
            )
    return warnings


def _tracked_items(root: Path, mechanics_candidate: bytes | None) -> list[str]:
    """Inventory item and resource ids `mechanics_state.json` counts for any actor."""

    raw = mechanics_candidate.decode("utf-8") if mechanics_candidate else repog_runtime.read_text(root / "mechanics_state.json")
    try:
        state = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return []
    actors = state.get("actors") if isinstance(state, dict) else None
    names: set[str] = set()
    for actor in actors.values() if isinstance(actors, dict) else []:
        for container in ("inventory", "resources"):
            held = actor.get(container) if isinstance(actor, dict) else None
            if isinstance(held, dict):
                names.update(str(key) for key in held)
    return sorted(names)


def _inventory_warnings(
    root: Path, state_before: str, state_after: str, mechanics_candidate: bytes | None
) -> list[dict[str, str]]:
    """Advisory: a new inventory line counting an item the mechanics already count."""

    before = owner_ops.key_block(state_before, "inventory") or ""
    after = owner_ops.key_block(state_after, "inventory") or ""
    if before == after:
        return []
    items = _tracked_items(root, mechanics_candidate)
    old_lines = set(before.splitlines())
    warnings: list[dict[str, str]] = []
    for line in after.splitlines():
        if line in old_lines or not re.search(r"\d", line):
            continue
        for item in items:
            name = re.sub(r"[_-]+", " ", item).casefold()
            if re.search(rf"(?<!\w){re.escape(name)}", line.casefold()):
                warnings.append(
                    {
                        "rule": "inventory_count_duplicate",
                        "path": "current_state.yaml",
                        "message": (
                            f"inventory line {line.strip()} carries a number for '{item}', which mechanics_state.json "
                            "counts; name the item only and let the mechanics hold the count"
                        ),
                    }
                )
                break
    return warnings


COST_STATE_KEYS = ("player.condition", "player.conditions", "conditions", "scene_frame.pending_consequences")


def _cost_warnings(
    changes: list[dict[str, Any]],
    *,
    state_before: str,
    state_after: str,
    mechanic_operations: list[Any],
    mutation_paths: set[str],
) -> list[dict[str, str]]:
    """Advisory: a roll that cost something, cited by a commit that records no cost anywhere."""

    costly = [
        change
        for change in changes
        if change.get("roll_reference") and any(token in change.get("outcome", "").casefold() for token in COST_BAND_TOKENS)
    ]
    if not costly or mechanic_operations or any(PurePosixPath(path).parts[0] == "characters" for path in mutation_paths):
        return []
    if any(owner_ops.key_block(state_before, key) != owner_ops.key_block(state_after, key) for key in COST_STATE_KEYS):
        return []
    return [
        {
            "rule": "cost_unrecorded",
            "path": "",
            "message": (
                f"change {change['id']} cites roll {change['roll_reference']} with band {change['outcome']}, but this "
                "commit records no cost: change player.condition, conditions or scene_frame.pending_consequences, "
                "a mechanic, or a character note"
            ),
        }
        for change in costly
    ]


def commit_durable(
    campaign: Path,
    payload: dict[str, Any],
    *,
    act: dict[str, Any] | None = None,
    payload_hash: str | None = None,
) -> dict[str, Any]:
    """Commit one model-authored durable result and its optional checkpoint.

    `act` and `payload_hash` are set only by `commit_act`. Its threads.md
    transition is built here, under the same lock and revision as the rest of
    the commit, and its retries are matched on the hash of the commit-act
    payload, which holds fields this envelope leaves out.
    """

    root = _campaign_root(campaign)
    parsed = _durable_identity(payload)
    payload_hash = payload_hash or _canonical_hash(payload)
    operation = "commit-act" if act is not None else "commit-durable"
    with _transaction_lock(root):
        recovered = _recover_transactions(root)
        state_text, log_text, meta = _runtime(root)
        prior = _prior_receipt(
            log_text,
            parsed["operation_id"],
            payload_hash,
            expected_revision=parsed["expected_revision"],
            current_revision=meta["revision"],
            expected_kind="durable",
        )
        if prior is not None:
            return _idempotent_result(
                operation=operation,
                operation_id=parsed["operation_id"],
                meta=meta,
                boundary=parsed["boundary"],
                checkpoint=parsed["checkpoint"],
                recovered=recovered,
            )
        if parsed["expected_revision"] != meta["revision"]:
            raise _stale_error(parsed["expected_revision"], meta["revision"])
        # Retry and stale-revision decisions happen before exact replacements
        # are materialized; committed files no longer contain their old text.
        new_revision = meta["revision"] + 1
        act_texts = _act_threads(root, act, revision=new_revision) if act is not None else None
        parsed = _validate_durable_payload(
            root,
            payload,
            revision=new_revision,
            act_mutations={"threads.md": act_texts[1].encode("utf-8")} if act_texts else None,
        )
        already_due, due_reason = _distill_requirement(
            meta["cold_distill_policy"],
            meta["durable_turns_since_distill"],
            boundary="ordinary",
            checkpoint=False,
        )
        if already_due:
            raise RPGStateError("distill_required", f"full distill is already required: {due_reason}")
        consumed_rolls, roll_warnings = _verify_rolls(
            root,
            parsed["changes"],
            parsed["void_rolls"],
            base_revision=meta["revision"],
        )

        mechanics_candidate, mechanic_results = _mechanic_candidate(
            root,
            parsed["mechanic_operations"],
            resulting_continuity_revision=new_revision,
        )
        candidates = dict(parsed["mutations"])
        warnings = _finish_candidates(candidates, parsed["mutation_paths"], stamp_revision=new_revision)
        warnings.extend(roll_warnings)
        warnings.extend(parsed["notes"])
        warnings.extend(_death_projection(root, candidates, parsed["mutation_paths"]))
        if parsed["checkpoint"] is not None:
            _sync_scene_frame(candidates, state_text, parsed["checkpoint"])
        if mechanics_candidate is not None:
            candidates["mechanics_state.json"] = mechanics_candidate

        original_meta = _state_meta(state_text)
        semantic_state_text = (
            candidates["current_state.yaml"].decode("utf-8")
            if "current_state.yaml" in candidates
            else state_text
        )
        if _state_meta(semantic_state_text) != original_meta:
            raise RPGStateError("candidate_invalid", "current_state semantic mutation changed helper-managed persistence fields")
        warnings.extend(_inventory_warnings(root, state_text, semantic_state_text, mechanics_candidate))
        warnings.extend(
            _cost_warnings(
                parsed["changes"],
                state_before=state_text,
                state_after=semantic_state_text,
                mechanic_operations=parsed["mechanic_operations"],
                mutation_paths=parsed["mutation_paths"],
            )
        )
        pending = _merge_pending(meta["pending_cold_targets"], parsed["cold_targets"])
        updated_state = _update_state_system(
            semantic_state_text,
            revision=new_revision,
            durable_turns=meta["durable_turns_since_distill"] + 1,
            pending_targets=pending,
        )
        candidates["current_state.yaml"] = updated_state.encode("utf-8")

        event = _durable_event(
            revision=new_revision,
            operation_id=parsed["operation_id"],
            payload_hash=payload_hash,
            cause=parsed["cause"],
            changes=parsed["changes"],
            boundary=parsed["boundary"],
            resume_impact=parsed["resume_impact"],
            voided=parsed["void_rolls"],
        )
        updated_log = _append_block(log_text, event)
        if parsed["checkpoint"] is not None:
            updated_log = _append_block(
                updated_log,
                _checkpoint_event(
                    revision=new_revision,
                    operation_id=parsed["operation_id"],
                    payload_hash=payload_hash,
                    checkpoint=parsed["checkpoint"],
                    paired_durable=True,
                ),
            )
        candidates["session_log.md"] = updated_log.encode("utf-8")
        if act_texts is not None:
            _check_act_transition(root, act_texts[0], candidates["threads.md"].decode("utf-8"), revision=new_revision)
        _commit_candidates(
            root,
            operation_id=parsed["operation_id"],
            payload_hash=payload_hash,
            candidates=candidates,
            prevalidated=frozenset({"threads.md"}) if act_texts is not None else frozenset(),
        )

        if consumed_rolls:
            try:
                roll_dice.mark_consumed(root, consumed_rolls, new_revision)
            except roll_dice.RollCallError as exc:
                # The commit stands; an unmarked receipt is refused later because
                # its revision no longer matches the turn that would cite it.
                warnings.append({"rule": "roll_receipt_unmarked", "path": "", "message": str(exc)})

        new_meta = _state_meta(updated_state)
        required, reason = _distill_requirement(
            meta["cold_distill_policy"],
            new_meta["durable_turns_since_distill"],
            boundary=parsed["boundary"],
            checkpoint=parsed["checkpoint"] is not None,
        )
        if len(updated_log) > LOG_ROTATION_HINT_TEXT:
            warnings.append(
                {
                    "rule": "session_log_size",
                    "path": "session_log.md",
                    "message": f"session_log.md holds {len(updated_log)} characters; the next commit-distill rotates it",
                }
            )
        return {
            "ok": True,
            "operation": operation,
            "idempotent": False,
            "operation_id": parsed["operation_id"],
            "continuity_revision": new_revision,
            "next_expected_revision": new_revision,
            "durable_turns_since_distill": new_meta["durable_turns_since_distill"],
            "pending_cold_targets": pending,
            "checkpoint_committed": parsed["checkpoint"] is not None,
            "full_distill_required": required,
            "narration_allowed": not required,
            "distill_reason": reason,
            "reply": _reply_note(not required),
            "changed_files": sorted(candidates),
            "mechanic_results": mechanic_results,
            "recovered_transactions": recovered,
            "warnings": warnings,
        }


def commit_checkpoint(campaign: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Commit a resumability-only checkpoint without a continuity revision."""

    root = _campaign_root(campaign)
    parsed = _checkpoint_identity(payload)
    payload_hash = _canonical_hash(payload)
    with _transaction_lock(root):
        recovered = _recover_transactions(root)
        state_text, log_text, meta = _runtime(root)
        prior = _prior_receipt(
            log_text,
            parsed["operation_id"],
            payload_hash,
            expected_revision=parsed["expected_revision"],
            current_revision=meta["revision"],
            expected_kind="checkpoint",
        )
        if prior is not None:
            return _idempotent_result(
                operation="commit-checkpoint",
                operation_id=parsed["operation_id"],
                meta=meta,
                boundary="scene_checkpoint",
                checkpoint=True,
                recovered=recovered,
            )
        if parsed["expected_revision"] != meta["revision"]:
            raise _stale_error(parsed["expected_revision"], meta["revision"])
        parsed = _validate_checkpoint_payload(root, payload, revision=meta["revision"])
        already_due, due_reason = _distill_requirement(
            meta["cold_distill_policy"],
            meta["durable_turns_since_distill"],
            boundary="ordinary",
            checkpoint=False,
        )
        if already_due:
            raise RPGStateError("distill_required", f"full distill is already required: {due_reason}")

        candidates = dict(parsed["mutations"])
        warnings = _finish_candidates(candidates, set(parsed["mutations"]), stamp_revision=meta["revision"])
        warnings.extend(parsed["notes"])
        _sync_scene_frame(candidates, state_text, parsed["checkpoint"])
        candidate_state = candidates["current_state.yaml"].decode("utf-8")
        if _state_meta(candidate_state) != _state_meta(state_text):
            raise RPGStateError("candidate_invalid", "checkpoint changed helper-managed persistence fields")
        updated_log = _append_block(
            log_text,
            _checkpoint_event(
                revision=meta["revision"],
                operation_id=parsed["operation_id"],
                payload_hash=payload_hash,
                checkpoint=parsed["checkpoint"],
                paired_durable=False,
            ),
        )
        candidates["session_log.md"] = updated_log.encode("utf-8")
        _commit_candidates(
            root,
            operation_id=parsed["operation_id"],
            payload_hash=payload_hash,
            candidates=candidates,
        )
        required, reason = _distill_requirement(
            meta["cold_distill_policy"],
            meta["durable_turns_since_distill"],
            boundary="scene_checkpoint",
            checkpoint=True,
        )
        return {
            "ok": True,
            "operation": "commit-checkpoint",
            "idempotent": False,
            "operation_id": parsed["operation_id"],
            "continuity_revision": meta["revision"],
            "next_expected_revision": meta["revision"],
            "durable_turns_since_distill": meta["durable_turns_since_distill"],
            "pending_cold_targets": meta["pending_cold_targets"],
            "checkpoint_committed": True,
            "full_distill_required": required,
            "narration_allowed": not required,
            "distill_reason": reason,
            "reply": _reply_note(not required),
            "changed_files": sorted(candidates),
            "mechanic_results": [],
            "recovered_transactions": recovered,
            "warnings": warnings,
        }


DISTILL_PAYLOAD_FIELDS = {
    "operation_id",
    "expected_continuity_revision",
    "trigger",
    "summary",
    "mutations",
    "rotate_log",
    "deferred_reconcile",
}


def _distill_marker(
    *,
    revision: int,
    operation_id: str,
    payload_hash: str,
    trigger: str,
    reconciled: list[str],
) -> str:
    files = ", ".join(reconciled) if reconciled else "none (records already current)"
    return "\n".join(
        [
            f"### Distilled Through Revision {revision}",
            "",
            f"- Trigger: {trigger}",
            f"- Files reconciled: {files}",
            f"- Operation: {operation_id}",
            f"- Payload hash: sha256:{payload_hash}",
        ]
    )


def _prior_distill(log_text: str, operation_id: str, payload_hash: str) -> int | None:
    """Return the marker revision of an identical earlier distill, if any."""

    pattern = re.compile(r"(?ms)^###\s+Distilled Through Revision\s+(\d+)\s*$\n(.*?)(?=^###\s|\Z)")
    for match in pattern.finditer(log_text):
        body = match.group(2)
        if re.search(rf"(?m)^- Operation:\s*{re.escape(operation_id)}\s*$", body) is None:
            continue
        if re.search(rf"(?m)^- Payload hash:\s*sha256:{payload_hash}\s*$", body) is None:
            raise RPGStateError("operation_conflict", "operation_id was already used for a different distill payload")
        return int(match.group(1))
    return None


def _rotate_log(log_text: str, through: int) -> tuple[str, str]:
    """Split off history before the distilled-through marker for `through`.

    The active log keeps its header, the latest marker, and every event after
    it. Those are what the writer and the full check read; older history moves
    to an archive file unchanged.
    """

    marker = re.search(rf"(?m)^###\s+Distilled Through Revision\s+{through}\s*$", log_text)
    first_entry = re.search(r"(?m)^###\s", log_text)
    if marker is None or first_entry is None or marker.start() <= first_entry.start():
        return log_text, ""
    # Keep a summary that directly precedes the marker with the marker.
    cut = marker.start()
    summary = None
    for summary in re.finditer(r"(?m)^###\s+Session.*Summary.*$", log_text[: marker.start()]):
        pass
    if summary is not None and not re.search(r"(?m)^###\s", log_text[summary.end() : marker.start()]):
        cut = summary.start()
    header = log_text[: first_entry.start()]
    archived = log_text[first_entry.start() : cut].rstrip() + "\n"
    kept = header + log_text[cut:]
    return kept, archived


def _finding_path(root: Path, value: Any) -> str:
    """A full-check finding's file as a campaign-relative path, so the GM knows
    which note to curate; "" when the finding names no file."""

    if not value:
        return ""
    try:
        return Path(str(value)).resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return str(value)


def _archive_path(root: Path, through: int) -> str:
    """The archive name for log history through `through`; a taken name gets -2, -3, …"""

    stem = f"{ARCHIVE_DIR}/session_log_through_r{through}"
    candidate, suffix = f"{stem}.md", 2
    while (root / candidate).exists():
        candidate, suffix = f"{stem}-{suffix}.md", suffix + 1
    return candidate


def _parse_deferred(root: Path, value: Any) -> dict[str, str]:
    """deferred_reconcile: files the curator reconciles later, by path, with the GM's reason."""

    if value is None:
        return {}
    if not isinstance(value, list) or len(value) > MAX_MUTATIONS:
        raise RPGStateError("input_invalid", f"deferred_reconcile must be an array of at most {MAX_MUTATIONS} objects")
    deferred: dict[str, str] = {}
    for index, raw in enumerate(value):
        label = f"deferred_reconcile[{index}]"
        if not isinstance(raw, dict):
            raise RPGStateError("input_invalid", f"{label} must be an object with path and reason")
        _require_keys(raw, {"path", "reason"}, label)
        relative, path = _relative_path(root, raw.get("path"), f"{label}.path")
        problem = curation.path_error(root, relative)
        if problem or not path.is_file():
            raise RPGStateError(
                "input_invalid",
                f"{label}.path {relative} cannot go to the curator: it {problem or 'does not exist'}",
            )
        if relative in deferred:
            raise RPGStateError("input_invalid", f"{label}.path repeats {relative}")
        deferred[relative] = _one_line(raw.get("reason"), f"{label}.reason", maximum=300)
    return deferred


def _distill_editable(root: Path, relative: str) -> bool:
    """True when a distill could change this file, so a gated finding on it can be reconciled here."""

    if not relative.endswith(".md"):
        return False
    try:
        _, path = _distill_path(root, relative, "finding path")
    except RPGStateError:
        return False
    return path.is_file()


def _distill_gate(
    root: Path, mutation_paths: set[str], deferred: dict[str, str]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Gated full-check findings this distill leaves unreconciled, and gate warnings.

    A finding is reconciled when the distill changes its file or defers that
    file to the curator. A finding on a file no distill can edit is left to
    the full check, so the gate can never block every way forward.
    """

    try:
        check = _candidate_checker().check_campaign(root, scope="full")
    except Exception as exc:  # a broken check must not make the distill impossible
        return [], [{"rule": "distill_gate_unavailable", "path": "", "message": f"{type(exc).__name__}: {exc}"}]
    unreconciled: list[dict[str, str]] = []
    for item in check.get("findings", []):
        if item.get("rule") not in DISTILL_GATE_RULES or item.get("severity") not in {"error", "warning"}:
            continue
        relative = _finding_path(root, item.get("path"))
        if not _distill_editable(root, relative) or relative in mutation_paths:
            continue
        if relative in deferred and item["rule"] not in UNDEFERRABLE_GATE_RULES:
            continue
        unreconciled.append({"path": relative, "rule": str(item["rule"]), "message": str(item.get("message", ""))})
    return unreconciled, []


def _gate_error(unreconciled: list[dict[str, str]]) -> RPGStateError:
    listed = "; ".join(f"{item['path']} ({item['rule']})" for item in unreconciled[:12])
    reason = (
        f"the distill leaves {len(unreconciled)} finding(s) unreconciled: {listed}. Change each file in this "
        "distill's mutations, or list it in deferred_reconcile with a reason for the curator"
    )
    undeferrable = sorted({item["rule"] for item in unreconciled} & UNDEFERRABLE_GATE_RULES)
    if undeferrable:
        reason += f"; {', '.join(undeferrable)} cannot be deferred"
    return RPGStateError("distill_unreconciled", reason, extra={"unreconciled": unreconciled})


def _curation_due_path(root: Path) -> Path:
    return root / repog_runtime.RUNTIME_DIR / CURATION_DUE_FILE


def _read_curation_due(root: Path) -> list[dict[str, str]]:
    data = repog_runtime.read_json(_curation_due_path(root), {})
    targets = data.get("targets") if isinstance(data, dict) else None
    return [item for item in targets if isinstance(item, dict) and isinstance(item.get("path"), str)] if isinstance(
        targets, list
    ) else []


def _write_curation_due(root: Path, targets: list[dict[str, str]], revision: int) -> list[dict[str, str]]:
    """Store the curator's list; the file exists only while a target remains."""

    path = _curation_due_path(root)
    if targets:
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        repog_runtime.write_json_atomic(path, {"at": stamp, "revision": revision, "targets": targets})
    else:
        path.unlink(missing_ok=True)
    return targets


def _curatable(root: Path, relative: str) -> bool:
    return bool(relative) and curation.path_error(root, relative) is None and (root / relative).is_file()


def _finding_targets(root: Path, item: dict[str, Any]) -> list[str]:
    """The curatable notes a full-check finding is about.

    Its own path when that is a note; else the files an aggregated finding
    lists in `paths`, which its message may clip; else the notes its message
    names, by path or, for a finding on an entity folder, by note title.
    """

    relative = _finding_path(root, item.get("path"))
    if _curatable(root, relative):
        return [relative]
    if isinstance(item.get("paths"), list):
        listed = (_finding_path(root, value) for value in item["paths"])
        return list(dict.fromkeys(path for path in listed if _curatable(root, path)))
    message = str(item.get("message", ""))
    found = [match for match in re.findall(r"[\w][\w./-]*\.md\b", message) if _curatable(root, match)]
    if relative in ENTITY_OWNER_DIRS and (root / relative).is_dir():
        found.extend(_titled_notes(root, relative, message))
    return list(dict.fromkeys(found))


def _titled_notes(root: Path, folder: str, message: str) -> list[str]:
    """The curatable notes of an entity folder that a message names by title.

    Longer titles are matched first and blanked out, so "Ali" is not found
    inside "Ali Reis".
    """

    notes = [
        (_note_title(repog_runtime.read_text(note)) or note.stem.replace("_", " "), note.relative_to(root).as_posix())
        for note in sorted((root / folder).glob("*.md"))
        if not note.name.startswith("_")
    ]
    named: set[str] = set()
    for title, note_path in sorted(notes, key=lambda item: -len(item[0])):
        pattern = rf"(?<!\w){re.escape(title)}(?!\w)"
        if title and re.search(pattern, message, re.IGNORECASE):
            named.add(note_path)
            message = re.sub(pattern, " ", message, flags=re.IGNORECASE)
    return [note_path for _, note_path in notes if note_path in named and _curatable(root, note_path)]


def _merge_targets(*groups: list[dict[str, str]]) -> list[dict[str, str]]:
    """One target per file, as a curation packet requires; later reasons for a file are appended."""

    merged: dict[str, dict[str, str]] = {}
    for group in groups:
        for item in group:
            known = merged.get(item["path"])
            reason = item.get("reason", "")
            if known is None:
                merged[item["path"]] = {"path": item["path"], "rule": item.get("rule", ""), "reason": reason}
            elif reason and reason not in known["reason"]:
                known["reason"] = f"{known['reason']}; {reason}"[:600]
    return list(merged.values())


def _update_curation_due(
    root: Path,
    *,
    changed: set[str],
    deferred: dict[str, str],
    findings: list[dict[str, Any]],
    revision: int,
) -> list[dict[str, str]]:
    """Drop targets the distill changed; add its deferrals and the curation rules the full check found."""

    kept = [item for item in _read_curation_due(root) if item["path"] not in changed]
    found: list[dict[str, str]] = []
    for item in findings:
        if item.get("rule") in CURATION_DUE_RULES and item.get("severity") in {"error", "warning"}:
            reason = " ".join(str(item.get("message", "")).split())[:300]
            found.extend({"path": path, "rule": str(item["rule"]), "reason": reason} for path in _finding_targets(root, item))
    deferrals = [{"path": path, "rule": "deferred_reconcile", "reason": reason} for path, reason in deferred.items()]
    targets = [item for item in _merge_targets(kept, found, deferrals) if _curatable(root, item["path"])]
    return _write_curation_due(root, targets, revision)


def _lint_report(root: Path) -> dict[str, Any] | None:
    """presentation_lint.report_summary for the last 20 replies; None when unavailable."""

    try:
        import presentation_lint

        summary = getattr(presentation_lint, "report_summary", None)
        return summary(root, last=20) if callable(summary) else None
    except Exception:  # the report is advisory; a lint failure must not fail the distill
        return None


def commit_distill(campaign: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Close a full distill in one transaction, without a continuity revision.

    The GM still decides what to reconcile and writes the new text. This step
    refuses to close while a gated content finding is neither fixed nor
    deferred, applies the edits to secondary records, appends the summary and
    the distilled-through marker, resets the persistence counters, moves old
    log history to an archive when asked or when the log is large, runs the
    full structural check, and hands deferred and flagged notes to the curator
    through `curation_due.json`.
    """

    root = _campaign_root(campaign)
    _require_keys(payload, DISTILL_PAYLOAD_FIELDS, "commit-distill payload")
    operation_id = _operation_id(payload.get("operation_id"))
    expected = payload.get("expected_continuity_revision")
    if expected != "current" and not _strict_int(expected):
        raise RPGStateError(
            "input_invalid", 'expected_continuity_revision must be a non-negative integer or "current"'
        )
    trigger = _one_line(payload.get("trigger"), "trigger", maximum=300)
    summary = payload.get("summary")
    if summary is not None and (not isinstance(summary, str) or not summary.strip()):
        raise RPGStateError("input_invalid", "summary must be non-empty text when present")
    rotate_requested = payload.get("rotate_log")
    if rotate_requested is not None and not isinstance(rotate_requested, bool):
        raise RPGStateError("input_invalid", "rotate_log must be true or false")
    deferred = _parse_deferred(root, payload.get("deferred_reconcile"))
    payload_hash = _canonical_hash(payload)
    with _transaction_lock(root):
        recovered = _recover_transactions(root)
        state_text, log_text, meta = _runtime(root)
        prior = _prior_distill(log_text, operation_id, payload_hash)
        if prior is not None:
            if prior != meta["last_distilled_revision"] or meta["revision"] != prior:
                raise RPGStateError("stale_revision", "distill retry is no longer the latest continuity operation")
            return {
                "ok": True,
                "operation": "commit-distill",
                "idempotent": True,
                "operation_id": operation_id,
                "continuity_revision": meta["revision"],
                "next_expected_revision": meta["revision"],
                "distilled_through": prior,
                "reply": REPLY_NOTE,
                "changed_files": [],
                "recovered_transactions": recovered,
                "warnings": [],
            }
        if expected != "current" and expected != meta["revision"]:
            raise _stale_error(expected, meta["revision"])
        revision = meta["revision"]
        notes: list[dict[str, str]] = []
        candidates, mutation_paths = _parse_mutations(
            root,
            payload.get("mutations", []),
            placeholders=owner_ops.PlaceholderContext(revision),
            distill=True,
            notes=notes,
        )
        unreconciled_findings, warnings = _distill_gate(root, mutation_paths, deferred)
        if unreconciled_findings:
            raise _gate_error(unreconciled_findings)
        warnings.extend(_finish_candidates(candidates, mutation_paths, stamp_revision=revision))
        warnings.extend(notes)

        state = _replace_nested_scalar(state_text, "persistence", "last_distilled_revision", revision)
        state = _replace_nested_scalar(state, "persistence", "durable_turns_since_distill", 0)
        state = _replace_pending_targets(state, [])
        candidates["current_state.yaml"] = state.encode("utf-8")

        updated_log = log_text
        archived_path = None
        # rotate_log: false still keeps the log whole; absent, a large log rotates.
        rotate = rotate_requested if rotate_requested is not None else len(log_text) > LOG_AUTO_ROTATE_TEXT
        if rotate and meta["last_distilled_revision"] > 0:
            updated_log, archived = _rotate_log(log_text, meta["last_distilled_revision"])
            if archived:
                archived_path = _archive_path(root, meta["last_distilled_revision"])
                heading = f"# Session Log Archive Through Revision {meta['last_distilled_revision']}\n\n"
                candidates[archived_path] = (heading + archived).encode("utf-8")
        if summary is not None:
            updated_log = _append_block(
                updated_log,
                f"### Session Summary Through Revision {revision}\n\n{summary.strip()}",
            )
        updated_log = _append_block(
            updated_log,
            _distill_marker(
                revision=revision,
                operation_id=operation_id,
                payload_hash=payload_hash,
                trigger=trigger,
                reconciled=sorted(mutation_paths),
            ),
        )
        candidates["session_log.md"] = updated_log.encode("utf-8")
        _commit_candidates(root, operation_id=operation_id, payload_hash=payload_hash, candidates=candidates)

    unreconciled = [
        target for target in meta["pending_cold_targets"] if target not in mutation_paths and target not in deferred
    ]
    check = _candidate_checker().check_campaign(root, scope="full")
    findings = [
        {
            "severity": item["severity"],
            "rule": item["rule"],
            "message": item["message"],
            "path": _finding_path(root, item.get("path")),
        }
        for item in check["findings"]
        if item["severity"] in {"error", "warning"}
    ]
    try:
        with _transaction_lock(root):
            curation_due = _update_curation_due(
                root, changed=mutation_paths, deferred=deferred, findings=check["findings"], revision=revision
            )
    except (OSError, RPGStateError) as exc:  # the distill stands; the list is rebuilt at the next one
        curation_due = []
        warnings.append({"rule": "curation_due_unwritten", "path": "", "message": str(exc)})
    return {
        "ok": True,
        "operation": "commit-distill",
        "idempotent": False,
        "operation_id": operation_id,
        "continuity_revision": revision,
        "next_expected_revision": revision,
        "distilled_through": revision,
        "changed_files": sorted(candidates),
        "archived_log": archived_path,
        "unreconciled_targets": unreconciled,
        "curation_due": curation_due,
        "full_check": {
            "ok": check["ok"],
            "error_count": check["error_count"],
            "warning_count": check["warning_count"],
            "findings": findings[:20],
        },
        "lint_report": _lint_report(root),
        "narration_allowed": check["ok"],
        "reply": _reply_note(check["ok"]),
        "recovered_transactions": recovered,
        "warnings": warnings,
    }


CURATION_BLOCK_RE = re.compile(r"(?ms)^###\s+Curation Applied At Revision\s+\d+\s*$\n(.*?)(?=^###\s|\Z)")


def _curation_event(*, revision: int, curation_id: str, reason: str, files: list[str], payload_hash: str) -> str:
    return "\n".join(
        [
            f"### Curation Applied At Revision {revision}",
            "",
            f"- Curation: {curation_id}",
            f"- Reason: {reason}",
            f"- Files curated: {', '.join(files) if files else 'none (nothing safe to change)'}",
            f"- Payload hash: sha256:{payload_hash}",
        ]
    )


def _applied_curations(log_text: str) -> set[tuple[str, str]]:
    """(curation id, payload hash) of every proposal the session log records as applied."""

    found: set[tuple[str, str]] = set()
    for match in CURATION_BLOCK_RE.finditer(log_text):
        body = match.group(1)
        curation_id = re.search(r"(?m)^- Curation:\s*(\S+)\s*$", body)
        digest = re.search(r"(?m)^- Payload hash:\s*sha256:([0-9a-f]{64})\s*$", body)
        if curation_id is not None and digest is not None:
            found.add((curation_id.group(1), digest.group(1)))
    return found


def _stage_errors(root: Path, path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Read and check one staged file once, under the lock: its payload, or the reasons to reject it.

    Freshness and the dry run are checked separately (`_apply_errors`), after
    the log has been asked whether this exact proposal was applied already.
    """

    try:
        return curation.load_staged(root, path)
    except Exception as exc:  # a file that breaks the check must not block the files after it
        return None, [f"internal_error: {type(exc).__name__}: {exc}"]


def _apply_errors(root: Path, payload: dict[str, Any], revision: int) -> list[str]:
    """Why a well-formed proposal cannot be applied to the current files; [] when it can."""

    try:
        fresh, stale = curation.split_by_freshness(root, payload)
        if stale:
            # All or nothing: a proposal written against text that changed since is
            # never applied in part, because its edits may depend on each other.
            return [f"target changed since the proposal was written: {', '.join(stale)}"]
        return curation.dry_run(root, fresh, revision=revision)
    except Exception as exc:  # see _stage_errors
        return [f"internal_error: {type(exc).__name__}: {exc}"]


def _staged_unchanged(path: Path, payload_hash: str) -> bool:
    """True when the staging file still holds exactly the payload that was applied."""

    try:
        return _canonical_hash(curation.read_staged(path)) == payload_hash
    except curation.CurationError:
        return False


def _file_staged(root: Path, path: Path, outcome: str, warnings: list[dict[str, str]]) -> None:
    """Move a processed staging file into `outcome/`; a failed move never undoes or repeats the work.

    Only a file directly in this campaign's staging folder is moved: a
    `--staged` path naming another campaign's proposal is reported, not
    touched. An applied file that cannot move (Windows refuses while another
    process holds it) is recognised by its log entry on the next run and
    filed then.
    """

    try:
        here = Path(path).resolve().parent
        folder = curation.curation_dir(root).resolve()
    except (OSError, ValueError):
        return
    if os.path.normcase(str(here)) != os.path.normcase(str(folder)):
        return
    try:
        curation.move_processed(path, outcome)
    except curation.CurationError:
        pass  # not a staging file (a `--staged` path elsewhere) or already gone; its reasons say why
    except OSError as exc:
        if path.exists():
            warnings.append(
                {
                    "rule": "curation_file_not_moved",
                    "path": "",
                    "message": f"{path.name} stays staged until the next run files it in {outcome}/: {exc}",
                }
            )


def commit_curation(
    campaign: Path,
    *,
    staged: list[Path] | None = None,
    settle_seconds: float = CURATION_SETTLE_SECONDS,
) -> dict[str, Any]:
    """Apply staged curator proposals whose target files are unchanged.

    Each staged file is one transaction: its typed edits to secondary records
    and notes are applied only when every target still has the hash the
    curator read, then the file moves to `applied/`. Anything stale or invalid
    moves to `rejected/` with its reasons. A commit that fails on file I/O
    and rolls back leaves its file staged for the next run (`deferred`), and
    a file whose exact payload the log already records as applied is only
    filed away (`repeat`), never applied twice. Curation creates no revision,
    no distill marker, and no new truth; it only records what it tidied.
    """

    root = _campaign_root(campaign)
    applied: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    deferred: list[dict[str, str]] = []
    waiting: list[str] = []
    warnings: list[dict[str, str]] = []
    with _transaction_lock(root):
        recovered = _recover_transactions(root)
        _, log_text, meta = _runtime(root)
        done = _applied_curations(log_text)
        files = [Path(item) for item in staged] if staged is not None else curation.list_staged(root)
        now = time.time()
        for path in files:
            if staged is None:
                try:
                    if now - path.stat().st_mtime < settle_seconds:
                        waiting.append(path.name)
                        continue
                except OSError:
                    continue
            payload, errors = _stage_errors(root, path)
            curation_id = str((payload or {}).get("curation_id") or path.stem)
            if payload is not None:
                payload_hash = _canonical_hash(payload)
                if (curation_id, payload_hash) in done:
                    # Applied by an earlier run that could not file this copy away.
                    _file_staged(root, path, "applied", warnings)
                    files_curated = sorted({str(item.get("path")) for item in payload["mutations"]})
                    applied.append({"curation_id": curation_id, "files": files_curated, "repeat": True})
                    continue
                errors = _apply_errors(root, payload, meta["revision"])
            if payload is not None and not errors:
                try:
                    candidates, paths = _parse_mutations(
                        root,
                        payload["mutations"],
                        placeholders=owner_ops.PlaceholderContext(meta["revision"]),
                        distill=True,
                    )
                    file_warnings = _finish_candidates(candidates, paths, stamp_revision=meta["revision"])
                    files_curated = sorted(paths)
                    updated_log = _append_block(
                        log_text,
                        _curation_event(
                            revision=meta["revision"],
                            curation_id=curation_id,
                            reason=str(payload.get("reason", "")).strip(),
                            files=files_curated,
                            payload_hash=payload_hash,
                        ),
                    )
                    candidates["session_log.md"] = updated_log.encode("utf-8")
                    _commit_candidates(
                        root,
                        operation_id=f"curation-{curation_id}"[:MAX_OPERATION_ID],
                        payload_hash=payload_hash,
                        candidates=candidates,
                    )
                except RPGStateError as exc:
                    if exc.category == "recovery_required":
                        raise
                    if exc.category == "commit_rolled_back":
                        # A file I/O failure, rolled back whole: the proposal is still
                        # valid, so it stays staged and the next run tries again.
                        deferred.append({"curation_id": curation_id, "reason": f"{exc.category}: {exc}"})
                        continue
                    errors = [f"{exc.category}: {exc}"]
                except OSError as exc:
                    # The journal could not be prepared, so no campaign file changed.
                    deferred.append({"curation_id": curation_id, "reason": f"io_error: {exc}"})
                    continue
                else:
                    log_text = updated_log
                    done.add((curation_id, payload_hash))
                    if _staged_unchanged(path, payload_hash):
                        _file_staged(root, path, "applied", warnings)
                    else:
                        # The curator saved another draft over the file meanwhile; that
                        # draft was not applied, so it stays staged for the next run.
                        warnings.append(
                            {
                                "rule": "curation_restaged",
                                "path": "",
                                "message": f"{path.name} changed after it was applied; the new draft waits for the next run",
                            }
                        )
                    applied.append({"curation_id": curation_id, "files": files_curated})
                    warnings.extend(file_warnings)
                    continue
            _file_staged(root, path, "rejected", warnings)
            rejected.append({"curation_id": curation_id, "reasons": errors[:6]})
        curated = {file for item in applied for file in item["files"]}
        due = _read_curation_due(root)
        if curated and any(item["path"] in curated for item in due):
            try:
                _write_curation_due(root, [item for item in due if item["path"] not in curated], meta["revision"])
            except OSError as exc:  # the curation stands; the next distill rebuilds the list
                warnings.append({"rule": "curation_due_unwritten", "path": "", "message": str(exc)})
    return {
        "ok": True,
        "operation": "commit-curation",
        "continuity_revision": meta["revision"],
        "next_expected_revision": meta["revision"],
        "applied": applied,
        "rejected": rejected,
        "deferred": deferred,
        "waiting": waiting,
        "recovered_transactions": recovered,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# commit-act: one typed act transition
# ---------------------------------------------------------------------------


ACT_PAYLOAD_FIELDS = {"operation_id", "expected_continuity_revision", "close", "open", "checkpoint", "changes", "mutations"}
ACT_ID_RE = re.compile(r"^[\w][\w.-]{0,127}$")
ACT_SCOPE_FIELDS = (
    ("places", "Places this act can reach"),
    ("people", "People who belong to it"),
    ("in_motion", "What is already in motion as it opens"),
    ("if_ignored", "What stays true if the character does nothing"),
)
# Further Compass fields of the threads.md template; a new act starts with them
# empty unless the payload fills them, and the GM completes them later.
ACT_OPEN_FIELDS = (
    "Active pressures",
    "Setups awaiting payoff",
    "Climax availability conditions",
    "Closure conditions",
    "Player interest signals",
    "Horizon reference",
    "Link to current player choices",
    "Independent space",
)
FIELD_LINE_RE = re.compile(r"^\s*[-*]\s+[\w][\w /()–-]*:")


@lru_cache(maxsize=1)
def _act_checks() -> Any:
    """narrative_memory.py, which holds the act rules the full check applies to threads.md."""

    module_path = Path(__file__).with_name("narrative_memory.py")
    spec = importlib.util.spec_from_file_location("_repog_rpg_state_narrative_memory", module_path)
    if spec is None or spec.loader is None:
        raise RPGStateError("campaign_invalid", "cannot load the act rules in narrative_memory.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _act_id(value: Any, label: str) -> str:
    text = _one_line(value, label, maximum=128)
    if ACT_ID_RE.fullmatch(text) is None or text.casefold() == "none":
        raise RPGStateError("input_invalid", f"{label} must be an identifier without spaces, such as act-2")
    return text


def _act_text(value: Any, label: str) -> str:
    """One line from text, or from a list of texts joined with '; '."""

    if isinstance(value, list):
        if not value:
            raise RPGStateError("input_invalid", f"{label} must not be empty")
        return "; ".join(_one_line(item, f"{label}[{index}]", maximum=600) for index, item in enumerate(value))
    return _one_line(value, label, maximum=MAX_LINE_TEXT)


def _parse_act(payload: dict[str, Any]) -> dict[str, Any]:
    _require_keys(payload, ACT_PAYLOAD_FIELDS, "commit-act payload")
    close, opening = payload.get("close"), payload.get("open")
    if not isinstance(close, dict):
        raise RPGStateError("input_invalid", "close must be an object with act_id, outcome, and summary")
    if not isinstance(opening, dict):
        raise RPGStateError(
            "input_invalid",
            "open must be an object with act_id, title, dramatic_question, scope, and closure_conditions",
        )
    _require_keys(close, {"act_id", "outcome", "summary"}, "close")
    _require_keys(
        opening, {"act_id", "title", "dramatic_question", "scope", "closure_conditions", "prepared_expectations"}, "open"
    )
    scope = opening.get("scope")
    if not isinstance(scope, dict):
        raise RPGStateError("input_invalid", "open.scope must be an object with places, people, in_motion, and if_ignored")
    _require_keys(scope, {key for key, _ in ACT_SCOPE_FIELDS}, "open.scope")
    for field in ("changes", "mutations"):
        if payload.get(field) is not None and not isinstance(payload[field], list):
            raise RPGStateError("input_invalid", f"{field} must be an array")
    act = {
        "close_id": _act_id(close.get("act_id"), "close.act_id"),
        "outcome": _one_line(close.get("outcome"), "close.outcome", maximum=300),
        "summary": _one_line(close.get("summary"), "close.summary", maximum=600),
        "open_id": _act_id(opening.get("act_id"), "open.act_id"),
        "title": _one_line(opening.get("title"), "open.title", maximum=200),
        "question": _one_line(opening.get("dramatic_question"), "open.dramatic_question", maximum=600),
        "scope": {label: _act_text(scope.get(key), f"open.scope.{key}") for key, label in ACT_SCOPE_FIELDS},
        "closure_conditions": _act_text(opening.get("closure_conditions"), "open.closure_conditions"),
        "prepared": (
            _act_text(opening["prepared_expectations"], "open.prepared_expectations")
            if opening.get("prepared_expectations")
            else ""
        ),
    }
    if act["open_id"] == act["close_id"]:
        raise RPGStateError("input_invalid", "open.act_id must differ from close.act_id; act ids are never reused")
    return act


def _act_durable_payload(payload: dict[str, Any], act: dict[str, Any]) -> dict[str, Any]:
    """The commit-durable envelope an act transition commits as, at a scene-checkpoint boundary."""

    change = {
        "id": "act-transition",
        "kind": "act_transition",
        "established_delta": f"Act {act['close_id']} closed ({act['outcome']}); act {act['open_id']} opened: {act['title']}.",
        "owners": ["threads.md"],
    }
    return {
        "operation_id": payload.get("operation_id"),
        "expected_continuity_revision": payload.get("expected_continuity_revision"),
        "boundary": "scene_checkpoint",
        "cause": act["summary"],
        "resume_impact": f"Play continues in act {act['open_id']}: {act['question']}",
        "changes": [change, *(payload.get("changes") or [])],
        "mutations": list(payload.get("mutations") or []),
        "checkpoint": payload.get("checkpoint"),
    }


def _leading_prose(section: list[str]) -> list[str]:
    """The guidance lines a Compass section opens with, before its first field or subsection."""

    prose: list[str] = []
    for line in section:
        if FIELD_LINE_RE.match(line) or line.startswith("#"):
            break
        prose.append(line.rstrip("\r\n"))
    while prose and not prose[0].strip():
        prose.pop(0)
    while prose and not prose[-1].strip():
        prose.pop()
    return prose


def _compass_body(act: dict[str, Any], prose: list[str], *, revision: int) -> str:
    """The successor's Arc Compass: identity, question, scope, and an empty Closure Record."""

    fields = {
        "Act id": act["open_id"],
        "Act status": "active",
        "Previous act id": act["close_id"],
        "Opened at revision": str(revision),
        "Act name": act["title"],
        "Dramatic question": act["question"],
        **{field: "" for field in ACT_OPEN_FIELDS},
    }
    fields["Setups awaiting payoff"] = act["prepared"]
    fields["Closure conditions"] = act["closure_conditions"]
    lines = prose + [""] if prose else []
    lines.extend(f"- {field}: {value}".rstrip() for field, value in fields.items())
    lines += ["", "### Act Scope", ""]
    lines.extend(f"- {label}: {act['scope'][label]}" for _, label in ACT_SCOPE_FIELDS)
    lines += ["", "### Closure Record", "", "- Closing action:", "- Condition met or foreclosed:", "- Recorded at revision:"]
    return "\n".join(lines)


def _act_threads(root: Path, act: dict[str, Any], *, revision: int) -> tuple[str, str]:
    """threads.md with the current act closed, and then with it archived and its successor open.

    The first text is the intermediate step the act rules check separately: a
    Compass already closed by the decisive turn keeps its Closure Record.
    """

    text = _read_text(root / "threads.md", "threads.md")
    checks = _act_checks()
    current, archive, _ = checks._act_data(text)
    current_id = current.get("Act id", "")
    if not current_id or current_id.casefold() == "none":
        raise RPGStateError(
            "candidate_invalid",
            "the Arc Compass has no Act id; record the current act's Act id and Opened at revision in a durable "
            "commit before using commit-act",
        )
    if current_id != act["close_id"]:
        raise RPGStateError("input_invalid", f"close.act_id is {act['close_id']}, but the Arc Compass holds act {current_id}")
    if act["open_id"] in {fields.get("Act id") for _, fields in archive}:
        raise RPGStateError("input_invalid", f"open.act_id {act['open_id']} is already archived; act ids are never reused")
    try:
        closed = text
        if current.get("Act status") != "closed":
            closure = {
                "Act status": "closed",
                "Closing action": act["summary"],
                "Condition met or foreclosed": act["outcome"],
                "Recorded at revision": str(revision),
            }
            closed = owner_ops.set_fields(text, "Arc Compass", closure)
        closed_fields = checks._act_data(closed)[0]
        duplicated = sorted(field for field, value in closed_fields.items() if "\n" in value)
        if duplicated:
            raise RPGStateError("candidate_invalid", f"the Arc Compass repeats field(s): {', '.join(duplicated)}")
        # The archive entry keeps every Compass field as a flat line, which is
        # how the act rules compare it with the Compass it came from.
        entry = "\n".join(f"- {field}: {value}".rstrip() for field, value in closed_fields.items())
        prose = _leading_prose(owner_ops.section_body(closed, "Arc Compass") or [])
        ops: list[dict[str, Any]] = []
        if owner_ops.section_body(closed, "Act Archive") is None:
            ops.append({"op": "insert_section", "heading": "## Act Archive", "text": "Closed acts, oldest first."})
        ops += [
            {"op": "insert_section", "heading": f"### {act['close_id']}", "under": "## Act Archive", "text": entry},
            {"op": "replace_section", "heading": "## Arc Compass", "text": _compass_body(act, prose, revision=revision)},
        ]
        final = owner_ops.apply_markdown_ops(closed, ops, label="commit-act threads.md")
    except owner_ops.OwnerOpError as exc:
        raise RPGStateError(exc.category, f"threads.md: {exc}") from exc
    return closed, final


def _check_act_transition(root: Path, closed: str, final: str, *, revision: int) -> None:
    """Apply the full check's act rules to both steps of the transition."""

    checks = _act_checks()
    path = root / "threads.md"
    before = _read_text(path, "threads.md")
    findings: list[dict[str, Any]] = []
    if closed != before:
        findings += checks.check_thread_transition(before, closed, path, revision=revision)
    findings += checks.check_thread_transition(closed, final, path, revision=revision)
    findings += checks.check_threads(final, path, ready=True)
    errors = [item for item in findings if item.get("severity") == "error"]
    if errors:
        raise RPGStateError("candidate_invalid", "; ".join(f"{item['rule']}: {item['message']}" for item in errors))


def commit_act(campaign: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Close the current act and open its successor in one durable scene-checkpoint commit.

    The writer builds the threads.md change itself: the closed Compass moves to
    Act Archive and the new act takes the Compass, exactly as the full check's
    act rules require. Every other durable rule applies unchanged.
    """

    act = _parse_act(payload)
    return commit_durable(campaign, _act_durable_payload(payload, act), act=act, payload_hash=_canonical_hash(payload))


# ---------------------------------------------------------------------------
# template: a read-only payload skeleton
# ---------------------------------------------------------------------------


TEMPLATE_KINDS = ("durable", "checkpoint", "distill", "act")


def _safe_id(value: str, fallback: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")[:60]
    return text or fallback


def template(campaign: Path, kind: str) -> dict[str, Any]:
    """A payload skeleton for one commit kind, with the facts needed to fill it. Writes nothing."""

    if kind not in TEMPLATE_KINDS:
        raise RPGStateError("input_invalid", f"kind must be one of: {', '.join(TEMPLATE_KINDS)}")
    root = _campaign_root(campaign)
    state_text = _read_text(root / "current_state.yaml", "current state")
    revision = _state_meta(state_text)["revision"]
    frame = repog_runtime.block_scalars(state_text, "scene_frame")
    scene_id = frame.get("scene_id", "")
    checkpoint = {
        "scene_id": scene_id,
        "scene_mode": frame.get("mode", ""),
        "resume_anchor": "",
        "active_cast_handoff": "none",
        "open_choices": [""],
    }
    if kind == "durable":
        payload: dict[str, Any] = {
            "operation_id": f"turn-{revision + 1}",
            "expected_continuity_revision": revision,
            "boundary": "ordinary",
            "cause": "",
            "changes": [{"id": "c1", "kind": "", "established_delta": "", "owners": []}],
            "mutations": [{"path": "", "ops": []}],
        }
    elif kind == "checkpoint":
        payload = {
            "operation_id": f"checkpoint-{revision}-{_safe_id(scene_id, 'scene')}",
            "expected_continuity_revision": revision,
            "checkpoint": checkpoint,
            "mutations": [],
        }
    elif kind == "distill":
        payload = {
            "operation_id": f"distill-{revision}",
            "expected_continuity_revision": "current",
            "trigger": "",
            "summary": "",
            "mutations": [],
            "deferred_reconcile": [],
        }
    else:
        compass = _act_checks()._act_data(repog_runtime.read_text(root / "threads.md"))[0]
        payload = {
            "operation_id": f"act-{revision + 1}",
            "expected_continuity_revision": revision,
            "close": {"act_id": compass.get("Act id", ""), "outcome": "", "summary": ""},
            "open": {
                "act_id": "",
                "title": "",
                "dramatic_question": "",
                "scope": {key: "" for key, _ in ACT_SCOPE_FIELDS},
                "closure_conditions": [""],
                "prepared_expectations": [],
            },
            "checkpoint": checkpoint,
        }
    reference: dict[str, Any] = {
        "boundaries": sorted(BOUNDARIES),
        "scene_modes": sorted(SCENE_MODES),
        "current_state_keys": re.findall(r"(?m)^([A-Za-z_][\w-]*):", state_text),
        "active_cast_columns": owner_ops.table_rows(repog_runtime.read_text(root / "active_cast.md"))[0],
        "relationship_map_columns": owner_ops.table_rows(repog_runtime.read_text(root / "relationship_map.md"))[0],
        "kind_owners": {token: owner for tokens, owner in KIND_AUTHORITY_TOKENS for token in sorted(tokens)},
    }
    if kind == "durable":
        reference["checkpoint_at_scene_end"] = {"boundary": "scene_checkpoint", "checkpoint": checkpoint}
    return {
        "ok": True,
        "operation": "template",
        "kind": kind,
        "continuity_revision": revision,
        "next_expected_revision": revision,
        "payload": payload,
        "reference": reference,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", help="Path to the active campaign folder")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("commit-durable", "commit-checkpoint", "commit-distill", "commit-act"):
        subparser = subparsers.add_parser(command)
        source = subparser.add_mutually_exclusive_group(required=True)
        source.add_argument("--input-json", help="One JSON transaction envelope")
        source.add_argument(
            "--input-file",
            help="Read the JSON envelope from a UTF-8 file, or from standard input when the value is -",
        )
    curation_parser = subparsers.add_parser("commit-curation")
    target = curation_parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--apply-staged", action="store_true", help="Apply every settled staged curation file")
    target.add_argument("--staged", action="append", help="Apply this staged file (repeatable)")
    template_parser = subparsers.add_parser("template", help="Print a read-only payload skeleton")
    template_parser.add_argument("--kind", required=True, choices=TEMPLATE_KINDS)
    return parser


def _decode_input(data: bytes) -> tuple[str, list[dict[str, str]]]:
    """UTF-8 with or without a BOM; else the Turkish console code page, then latin-1, with a warning."""

    try:
        return data.decode("utf-8-sig"), []
    except UnicodeDecodeError:
        pass
    for codec, name in INPUT_FALLBACK_CODECS:
        try:
            text = data.decode(codec)
        except UnicodeDecodeError:
            continue
        return text, [
            {
                "rule": f"input_decoded_{name}",
                "path": "",
                "message": f"the input was not UTF-8 and was read as {codec}; check non-English letters in the result",
            }
        ]
    raise UnicodeError("input cannot be decoded")  # latin-1 decodes every byte, so this is unreachable


def _read_input(args: argparse.Namespace) -> tuple[str, list[dict[str, str]]]:
    if args.input_json is not None:
        return args.input_json, []
    if args.input_file == "-":
        return _decode_input(sys.stdin.buffer.read())
    return _decode_input(Path(args.input_file).read_bytes())


def _emit(result: dict[str, Any]) -> None:
    # UTF-8 bytes, not the console code page: Windows pipes default to cp1252,
    # which cannot encode most non-English names and would crash after a commit.
    sys.stdout.buffer.write((json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    sys.stdout.flush()


def _failure(exc: RPGStateError) -> dict[str, Any]:
    return {"ok": False, "failure_category": exc.category, "failure_reason": str(exc), **exc.extra}


def _curation_main(args: argparse.Namespace) -> int:
    try:
        staged = None if args.apply_staged else [Path(item) for item in args.staged]
        result = commit_curation(Path(args.campaign), staged=staged)
        exit_code = 0
    except RPGStateError as exc:
        result = _failure(exc)
        exit_code = exc.exit_code
    except (OSError, UnicodeError) as exc:
        result = {"ok": False, "failure_category": "io_error", "failure_reason": str(exc)}
        exit_code = 2
    _emit(result)
    return exit_code


COMMANDS = {
    "commit-durable": commit_durable,
    "commit-checkpoint": commit_checkpoint,
    "commit-distill": commit_distill,
    "commit-act": commit_act,
}


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "commit-curation":
        return _curation_main(args)
    input_warnings: list[dict[str, str]] = []
    try:
        if args.command == "template":
            result = template(Path(args.campaign), args.kind)
        else:
            text, input_warnings = _read_input(args)
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise RPGStateError("input_invalid", "input JSON must be an object")
            result = COMMANDS[args.command](Path(args.campaign), payload)
    except json.JSONDecodeError as exc:
        result = {"ok": False, "failure_category": "input_invalid", "failure_reason": f"invalid JSON: {exc}"}
        exit_code = 2
    except RPGStateError as exc:
        result = _failure(exc)
        exit_code = exc.exit_code
    except (OSError, UnicodeError) as exc:
        result = {"ok": False, "failure_category": "io_error", "failure_reason": str(exc)}
        exit_code = 2
    else:
        exit_code = 0
    if input_warnings:
        result["warnings"] = input_warnings + list(result.get("warnings", []))
    _emit(result)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

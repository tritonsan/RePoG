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

    def __init__(self, category: str, reason: str, *, exit_code: int = 2) -> None:
        super().__init__(reason)
        self.category = category
        self.exit_code = exit_code


def _strict_int(value: Any, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _require_keys(value: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise RPGStateError("input_invalid", f"{label} contains unsupported field(s): {', '.join(unknown)}")


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
        os.replace(temporary, path)
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


def _parse_checkpoint(value: Any, label: str = "checkpoint") -> dict[str, str]:
    if not isinstance(value, dict):
        raise RPGStateError("input_invalid", f"{label} must be an object")
    _require_keys(value, {"scene_id", "scene_mode", "resume_anchor", "active_cast_handoff"}, label)
    scene_mode = _one_line(value.get("scene_mode"), f"{label}.scene_mode", maximum=40)
    if scene_mode not in SCENE_MODES:
        raise RPGStateError("input_invalid", f"{label}.scene_mode is invalid")
    return {
        "scene_id": _one_line(value.get("scene_id"), f"{label}.scene_id", maximum=160),
        "scene_mode": scene_mode,
        "resume_anchor": _one_line(value.get("resume_anchor"), f"{label}.resume_anchor"),
        "active_cast_handoff": _one_line(value.get("active_cast_handoff"), f"{label}.active_cast_handoff"),
    }


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
                    f"{label}.kind '{kind}' requires {authority} in owners; a cold target does not satisfy it. "
                    f"Add the authority as an immediate owner, or declare a kind that matches the actual change.",
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


def _name_warnings(root: Path, relative: str, text: str) -> list[dict[str, str]]:
    """Advisory checks for a new entity's name; never blocks a commit.

    Flags a name that equals a common word of the play language (a character
    called "Tam" in Turkish reads as "exactly") and a name one or two letters
    away from an existing one (Corran / Corlan).
    """

    try:
        title = _note_title(text) or PurePosixPath(relative).stem.replace("_", " ")
        code = repog_runtime.runtime_settings(root).get("language", "auto")
        if code in {"", "auto"}:
            code = lang_pack.detect_language(text)[0] or "en"
        findings = name_check.check_name(title, _entity_titles(root, exclude=relative), lang_pack.load_pack(code))
    except Exception:  # an advisory check must never break a commit
        return []
    return [
        {"rule": str(item.get("rule", "name_check")), "path": relative, "message": str(item.get("message", ""))}
        for item in findings
        if item.get("level", "warning") == "warning"
    ]


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
        if receipt["roll_id"] in cited:
            raise RPGStateError("input_invalid", f"roll '{reference}' is cited by more than one change")
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
        if relative in paths:
            raise RPGStateError("input_invalid", f"duplicate mutation path: {relative}")
        paths.add(relative)
        modes = [mode for mode in ("ops", "exact_replacements", "create_text") if mode in raw]
        if len(modes) != 1:
            raise RPGStateError("input_invalid", f"{label} requires exactly one mutation mode: ops, exact_replacements, or create_text")
        if modes[0] == "create_text":
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
            continue

        if relative in TEMPLATE_OWNERS and not path.exists():
            # Campaigns created before these owners existed start from the
            # blank template the first time the GM records one.
            text = _read_text(TEMPLATE_DIR / relative, f"{relative} template")
        else:
            text = _read_text(path, relative)
        original_meta = _state_meta(text) if relative == "current_state.yaml" else None
        if modes[0] == "ops":
            try:
                ops = owner_ops.parse_ops(raw.get("ops"), relative=relative, label=label)
                text = owner_ops.apply_ops(text, ops, relative=relative, label=label, placeholders=placeholders)
            except owner_ops.OwnerOpError as exc:
                raise RPGStateError(exc.category, f"{relative}: {exc}") from exc
            if len(text) > MAX_FILE_TEXT:
                raise RPGStateError("candidate_invalid", f"candidate file exceeds {MAX_FILE_TEXT} characters: {relative}")
        else:
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
                    raise RPGStateError("input_invalid", f"{replacement_label} does not change content")
                occurrences = text.count(old)
                if occurrences != 1:
                    raise RPGStateError(
                        "candidate_invalid",
                        f"{replacement_label}.old matched {occurrences} times in {relative}; expected exactly one",
                    )
                text = text.replace(old, new, 1)
                if len(text) > MAX_FILE_TEXT:
                    raise RPGStateError("candidate_invalid", f"candidate file exceeds {MAX_FILE_TEXT} characters: {relative}")
        if original_meta is not None and _state_meta(text) != original_meta:
            raise RPGStateError(
                "input_invalid",
                "current_state continuity_revision and persistence fields are helper-managed and cannot be mutated directly",
            )
        candidates[relative] = text.encode("utf-8")
    return candidates, paths


def _finish_candidates(
    candidates: dict[str, bytes],
    mutation_paths: set[str],
    *,
    stamp_revision: int,
) -> list[dict[str, str]]:
    """Stamp mutated Markdown owners and collect advisory curation warnings.

    A mutated owner that carries one `As of revision: N` line now reflects this
    revision, so the writer sets the stamp instead of the GM. Warnings never
    block a commit; they tell the GM which owner needs curating before it
    reaches the hard size cap or keeps contradicting itself.
    """

    warnings: list[dict[str, str]] = []
    for relative in sorted(mutation_paths):
        if not relative.endswith(".md") or relative not in candidates:
            continue
        text = owner_ops.stamp_revision(candidates[relative].decode("utf-8"), stamp_revision)
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
        f"- Cause: {cause}",
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
    else:
        lines.append("- Deferred propagation: none — no secondary surface affected")
    if voided:
        lines.append("- Voided rolls:")
        for item in voided:
            lines.append(f"  - {item['roll_id']} — {item['reason']}")
    lines.extend(
        [
            f"- Boundary: {boundary}",
            f"- Resume impact: {resume_impact}",
            f"- Payload hash: sha256:{payload_hash}",
        ]
    )
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
            f"- Active-cast handoff: {checkpoint['active_cast_handoff']}",
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
) -> None:
    findings = _candidate_checker().check_changed_owners(root, candidates)
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


def _validate_durable_payload(root: Path, payload: dict[str, Any], *, revision: int) -> dict[str, Any]:
    identity = _durable_identity(payload)
    operation_id = identity["operation_id"]
    expected = identity["expected_revision"]
    boundary = identity["boundary"]
    cause = _one_line(payload.get("cause"), "cause")
    resume_impact = _one_line(payload.get("resume_impact"), "resume_impact")
    changes, owners, cold_targets = _parse_changes(root, payload.get("changes"))
    notes: list[dict[str, str]] = []
    mutations, mutation_paths = _parse_mutations(
        root,
        payload.get("mutations", []),
        placeholders=owner_ops.PlaceholderContext(revision),
        notes=notes,
    )
    void_rolls = _parse_void_rolls(payload.get("void_rolls"))
    checkpoint_raw = payload.get("checkpoint")
    checkpoint = _parse_checkpoint(checkpoint_raw) if checkpoint_raw is not None else None
    if boundary == "scene_checkpoint" and checkpoint is None:
        raise RPGStateError("input_invalid", "scene_checkpoint boundary requires checkpoint data")
    if boundary == "ordinary" and checkpoint is not None:
        raise RPGStateError("input_invalid", "ordinary boundary cannot include a checkpoint")
    if checkpoint is not None:
        # The writer copies scene_id, mode, and resume anchor into the scene
        # frame itself, so a checkpoint no longer needs its own state mutation.
        if checkpoint["active_cast_handoff"].lower() != "none" and "active_cast.md" not in mutation_paths:
            raise RPGStateError("input_invalid", "non-empty active-cast handoff requires an active_cast.md mutation")
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
    mutations, mutation_paths = _parse_mutations(
        root,
        payload.get("mutations", []),
        placeholders=owner_ops.PlaceholderContext(revision),
    )
    invalid_paths = sorted(mutation_paths - {"current_state.yaml", "active_cast.md"})
    if invalid_paths:
        raise RPGStateError("input_invalid", f"soft checkpoint cannot mutate durable owner files: {', '.join(invalid_paths)}")
    if checkpoint["active_cast_handoff"].lower() != "none" and "active_cast.md" not in mutation_paths:
        raise RPGStateError("input_invalid", "non-empty active-cast handoff requires an active_cast.md mutation")
    return {
        "operation_id": operation_id,
        "expected_revision": expected,
        "checkpoint": checkpoint,
        "mutations": mutations,
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
        "durable_turns_since_distill": meta["durable_turns_since_distill"],
        "pending_cold_targets": meta["pending_cold_targets"],
        "checkpoint_committed": checkpoint,
        "full_distill_required": required,
        "narration_allowed": not required,
        "distill_reason": reason,
        "changed_files": [],
        "mechanic_results": [],
        "recovered_transactions": recovered,
        "warnings": [],
    }


def _sync_scene_frame(candidates: dict[str, bytes], state_text: str, checkpoint: dict[str, str]) -> None:
    """Write the checkpoint's scene id, mode, and anchor into the scene frame."""

    base = candidates["current_state.yaml"].decode("utf-8") if "current_state.yaml" in candidates else state_text
    try:
        synced = owner_ops.set_scene_frame(
            base,
            scene_id=checkpoint["scene_id"],
            scene_mode=checkpoint["scene_mode"],
            resume_anchor=checkpoint["resume_anchor"],
        )
    except owner_ops.OwnerOpError as exc:
        raise RPGStateError(exc.category, f"current_state.yaml: {exc}") from exc
    candidates["current_state.yaml"] = synced.encode("utf-8")


def commit_durable(campaign: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Commit one model-authored durable result and its optional checkpoint."""

    root = _campaign_root(campaign)
    parsed = _durable_identity(payload)
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
            expected_kind="durable",
        )
        if prior is not None:
            return _idempotent_result(
                operation="commit-durable",
                operation_id=parsed["operation_id"],
                meta=meta,
                boundary=parsed["boundary"],
                checkpoint=parsed["checkpoint"],
                recovered=recovered,
            )
        if parsed["expected_revision"] != meta["revision"]:
            raise RPGStateError(
                "stale_revision",
                f"expected continuity revision {parsed['expected_revision']}, found {meta['revision']}",
            )
        # Retry and stale-revision decisions happen before exact replacements
        # are materialized; committed files no longer contain their old text.
        new_revision = meta["revision"] + 1
        parsed = _validate_durable_payload(root, payload, revision=new_revision)
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
        _commit_candidates(
            root,
            operation_id=parsed["operation_id"],
            payload_hash=payload_hash,
            candidates=candidates,
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
                    "message": f"session_log.md holds {len(updated_log)} characters; pass rotate_log at the next commit-distill",
                }
            )
        return {
            "ok": True,
            "operation": "commit-durable",
            "idempotent": False,
            "operation_id": parsed["operation_id"],
            "continuity_revision": new_revision,
            "durable_turns_since_distill": new_meta["durable_turns_since_distill"],
            "pending_cold_targets": pending,
            "checkpoint_committed": parsed["checkpoint"] is not None,
            "full_distill_required": required,
            "narration_allowed": not required,
            "distill_reason": reason,
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
            raise RPGStateError(
                "stale_revision",
                f"expected continuity revision {parsed['expected_revision']}, found {meta['revision']}",
            )
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
            "durable_turns_since_distill": meta["durable_turns_since_distill"],
            "pending_cold_targets": meta["pending_cold_targets"],
            "checkpoint_committed": True,
            "full_distill_required": required,
            "narration_allowed": not required,
            "distill_reason": reason,
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


def commit_distill(campaign: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Close a full distill in one transaction, without a continuity revision.

    The GM still decides what to reconcile and writes the new text. This step
    applies those edits to secondary records, appends the summary and the
    distilled-through marker, resets the persistence counters, optionally moves
    old log history to an archive, and runs the full structural check.
    """

    root = _campaign_root(campaign)
    _require_keys(payload, DISTILL_PAYLOAD_FIELDS, "commit-distill payload")
    operation_id = _operation_id(payload.get("operation_id"))
    expected = payload.get("expected_continuity_revision")
    if not _strict_int(expected):
        raise RPGStateError("input_invalid", "expected_continuity_revision must be a non-negative integer")
    trigger = _one_line(payload.get("trigger"), "trigger", maximum=300)
    summary = payload.get("summary")
    if summary is not None and (not isinstance(summary, str) or not summary.strip()):
        raise RPGStateError("input_invalid", "summary must be non-empty text when present")
    rotate = payload.get("rotate_log", False)
    if not isinstance(rotate, bool):
        raise RPGStateError("input_invalid", "rotate_log must be true or false")
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
                "distilled_through": prior,
                "changed_files": [],
                "recovered_transactions": recovered,
                "warnings": [],
            }
        if expected != meta["revision"]:
            raise RPGStateError("stale_revision", f"expected continuity revision {expected}, found {meta['revision']}")
        revision = meta["revision"]
        candidates, mutation_paths = _parse_mutations(
            root,
            payload.get("mutations", []),
            placeholders=owner_ops.PlaceholderContext(revision),
            distill=True,
        )
        warnings = _finish_candidates(candidates, mutation_paths, stamp_revision=revision)

        state = _replace_nested_scalar(state_text, "persistence", "last_distilled_revision", revision)
        state = _replace_nested_scalar(state, "persistence", "durable_turns_since_distill", 0)
        state = _replace_pending_targets(state, [])
        candidates["current_state.yaml"] = state.encode("utf-8")

        updated_log = log_text
        archived_path = None
        if rotate and meta["last_distilled_revision"] > 0:
            updated_log, archived = _rotate_log(log_text, meta["last_distilled_revision"])
            if archived:
                archived_path = f"{ARCHIVE_DIR}/session_log_through_r{meta['last_distilled_revision']}.md"
                target = root / ARCHIVE_DIR / f"session_log_through_r{meta['last_distilled_revision']}.md"
                if target.exists():
                    raise RPGStateError("candidate_invalid", f"archive already exists: {archived_path}")
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

    unreconciled = [target for target in meta["pending_cold_targets"] if target not in mutation_paths]
    check = _candidate_checker().check_campaign(root, scope="full")
    findings = [
        {"severity": item["severity"], "rule": item["rule"], "message": item["message"]}
        for item in check["findings"]
        if item["severity"] in {"error", "warning"}
    ]
    return {
        "ok": True,
        "operation": "commit-distill",
        "idempotent": False,
        "operation_id": operation_id,
        "continuity_revision": revision,
        "distilled_through": revision,
        "changed_files": sorted(candidates),
        "archived_log": archived_path,
        "unreconciled_targets": unreconciled,
        "full_check": {
            "ok": check["ok"],
            "error_count": check["error_count"],
            "warning_count": check["warning_count"],
            "findings": findings[:20],
        },
        "narration_allowed": check["ok"],
        "recovered_transactions": recovered,
        "warnings": warnings,
    }


def _curation_event(*, revision: int, curation_id: str, reason: str, files: list[str]) -> str:
    return "\n".join(
        [
            f"### Curation Applied At Revision {revision}",
            "",
            f"- Curation: {curation_id}",
            f"- Reason: {reason}",
            f"- Files curated: {', '.join(files) if files else 'none (nothing safe to change)'}",
        ]
    )


def _stage_errors(root: Path, path: Path, revision: int) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate one staged file under the lock; return its payload or the reasons to reject it."""

    errors = curation.validate_file(root, path)
    if errors:
        return None, errors
    try:
        payload = curation.read_staged(path)
    except curation.CurationError as exc:
        return None, [str(exc)]
    fresh, stale = curation.split_by_freshness(root, payload)
    if stale:
        # All or nothing: a proposal written against text that changed since is
        # never applied in part, because its edits may depend on each other.
        return None, [f"target changed since the proposal was written: {', '.join(stale)}"]
    errors = curation.dry_run(root, fresh, revision=revision)
    return (None, errors) if errors else (payload, [])


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
    moves to `rejected/` with its reasons. Curation creates no revision, no
    distill marker, and no new truth; it only records what it tidied.
    """

    root = _campaign_root(campaign)
    applied: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    waiting: list[str] = []
    warnings: list[dict[str, str]] = []
    with _transaction_lock(root):
        recovered = _recover_transactions(root)
        _, log_text, meta = _runtime(root)
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
            payload, errors = _stage_errors(root, path, meta["revision"])
            curation_id = str((payload or {}).get("curation_id") or path.stem)
            if payload is not None:
                try:
                    candidates, paths = _parse_mutations(
                        root,
                        payload["mutations"],
                        placeholders=owner_ops.PlaceholderContext(meta["revision"]),
                        distill=True,
                    )
                    file_warnings = _finish_candidates(candidates, paths, stamp_revision=meta["revision"])
                    files_curated = sorted(paths)
                    log_text = _append_block(
                        log_text,
                        _curation_event(
                            revision=meta["revision"],
                            curation_id=curation_id,
                            reason=str(payload.get("reason", "")).strip(),
                            files=files_curated,
                        ),
                    )
                    candidates["session_log.md"] = log_text.encode("utf-8")
                    _commit_candidates(
                        root,
                        operation_id=f"curation-{curation_id}"[:MAX_OPERATION_ID],
                        payload_hash=_canonical_hash(payload),
                        candidates=candidates,
                    )
                except RPGStateError as exc:
                    if exc.category == "recovery_required":
                        raise
                    log_text = _read_text(root / "session_log.md", "session log")
                    errors = [f"{exc.category}: {exc}"]
                else:
                    curation.move_processed(path, "applied")
                    applied.append({"curation_id": curation_id, "files": files_curated})
                    warnings.extend(file_warnings)
                    continue
            try:
                curation.move_processed(path, "rejected")
            except curation.CurationError:
                pass
            rejected.append({"curation_id": curation_id, "reasons": errors[:6]})
    return {
        "ok": True,
        "operation": "commit-curation",
        "continuity_revision": meta["revision"],
        "applied": applied,
        "rejected": rejected,
        "waiting": waiting,
        "recovered_transactions": recovered,
        "warnings": warnings,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", help="Path to the active campaign folder")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("commit-durable", "commit-checkpoint", "commit-distill"):
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
    return parser


def _read_input(args: argparse.Namespace) -> str:
    if args.input_json is not None:
        return args.input_json
    if args.input_file == "-":
        return sys.stdin.buffer.read().decode("utf-8-sig")
    return Path(args.input_file).read_text(encoding="utf-8-sig")


def _emit(result: dict[str, Any]) -> None:
    # UTF-8 bytes, not the console code page: Windows pipes default to cp1252,
    # which cannot encode most non-English names and would crash after a commit.
    sys.stdout.buffer.write((json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    sys.stdout.flush()


def _curation_main(args: argparse.Namespace) -> int:
    try:
        staged = None if args.apply_staged else [Path(item) for item in args.staged]
        result = commit_curation(Path(args.campaign), staged=staged)
        exit_code = 0
    except RPGStateError as exc:
        result = {"ok": False, "failure_category": exc.category, "failure_reason": str(exc)}
        exit_code = exc.exit_code
    except (OSError, UnicodeError) as exc:
        result = {"ok": False, "failure_category": "io_error", "failure_reason": str(exc)}
        exit_code = 2
    _emit(result)
    return exit_code


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "commit-curation":
        return _curation_main(args)
    try:
        payload = json.loads(_read_input(args))
        if not isinstance(payload, dict):
            raise RPGStateError("input_invalid", "input JSON must be an object")
        if args.command == "commit-durable":
            result = commit_durable(Path(args.campaign), payload)
        elif args.command == "commit-checkpoint":
            result = commit_checkpoint(Path(args.campaign), payload)
        else:
            result = commit_distill(Path(args.campaign), payload)
    except json.JSONDecodeError as exc:
        result = {"ok": False, "failure_category": "input_invalid", "failure_reason": f"invalid JSON: {exc}"}
        exit_code = 2
    except RPGStateError as exc:
        result = {"ok": False, "failure_category": exc.category, "failure_reason": str(exc)}
        exit_code = exc.exit_code
    except (OSError, UnicodeError) as exc:
        result = {"ok": False, "failure_category": "io_error", "failure_reason": str(exc)}
        exit_code = 2
    else:
        exit_code = 0
    _emit(result)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

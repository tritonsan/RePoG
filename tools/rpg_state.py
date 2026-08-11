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
from pathlib import Path, PurePosixPath
from typing import Any, Iterator


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

OPERATION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CHANGE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
KIND_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
SCENE_MODES = {"ambient", "focused", "crisis", "aftermath", "transition", "breather"}
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
}
ENTITY_OWNER_DIRS = {"characters", "places", "factions"}
SYSTEM_MANAGED_FILES = {"session_log.md"}
NEVER_COLD_FILES = ROOT_OWNER_FILES | SYSTEM_MANAGED_FILES | {
    "setup_profile.yaml",
    "play_profile.yaml",
    "companion_profile.yaml",
    "companion_state.json",
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
        _require_keys(raw, {"id", "kind", "established_delta", "owners", "cold_targets", "roll_reference"}, label)
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
            }
        )
    return parsed, owners, all_cold


def _parse_mutations(root: Path, value: Any) -> tuple[dict[str, bytes], set[str]]:
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
        _require_keys(raw, {"path", "exact_replacements", "create_text"}, label)
        relative, path = _owner_path(root, raw.get("path"), f"{label}.path")
        if relative == "mechanics_state.json":
            raise RPGStateError("input_invalid", "mechanics_state.json must be changed through mechanic_operations")
        if relative in paths:
            raise RPGStateError("input_invalid", f"duplicate mutation path: {relative}")
        paths.add(relative)
        has_replacements = "exact_replacements" in raw
        has_create = "create_text" in raw
        if has_replacements == has_create:
            raise RPGStateError("input_invalid", f"{label} requires exactly one mutation mode")
        if has_create:
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
            if len(text) > MAX_FILE_TEXT:
                raise RPGStateError("input_invalid", f"{label}.create_text exceeds {MAX_FILE_TEXT} characters")
            if not text.endswith("\n"):
                text += "\n"
            candidates[relative] = text.encode("utf-8")
            continue

        replacements = raw.get("exact_replacements")
        if not isinstance(replacements, list) or not replacements:
            raise RPGStateError("input_invalid", f"{label}.exact_replacements must be a non-empty array")
        if len(replacements) > MAX_REPLACEMENTS:
            raise RPGStateError("input_invalid", f"{label}.exact_replacements exceeds {MAX_REPLACEMENTS}")
        text = _read_text(path, relative)
        original_meta = _state_meta(text) if relative == "current_state.yaml" else None
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
) -> str:
    lines = [
        f"### Durable Revision {revision}",
        "",
        f"- Operation: {operation_id}",
        f"- Cause: {cause}",
        "- Established changes:",
    ]
    for change in changes:
        suffix = f" (roll: {change['roll_reference']})" if change.get("roll_reference") else ""
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
    if pid <= 0:
        return False
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
    journal_root = _journal_root(root)
    journal_root.mkdir(exist_ok=True)
    lock_path = journal_root / LOCK_FILE
    descriptor: int | None = None
    for _ in range(2):
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, f"{os.getpid()}\n".encode("ascii"))
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = None
            break
        except FileExistsError:
            try:
                raw = lock_path.read_text(encoding="ascii").strip()
                owner_pid = int(raw)
            except (OSError, ValueError):
                owner_pid = -1
            if _pid_alive(owner_pid):
                raise RPGStateError("transaction_busy", f"another RPG transaction holds the campaign lock (pid {owner_pid})")
            try:
                lock_path.unlink()
            except OSError as exc:
                raise RPGStateError("transaction_busy", f"cannot clear stale RPG transaction lock: {exc}") from exc
    else:
        raise RPGStateError("transaction_busy", "cannot acquire the RPG transaction lock")
    try:
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            lock_path.unlink(missing_ok=True)
        except OSError:
            pass


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
    return recovered


def _apply_candidate_file(path: Path, payload: bytes) -> None:
    """Replace one campaign target; isolated for failure-injection tests."""

    _atomic_bytes(path, payload)


def _commit_candidates(
    root: Path,
    *,
    operation_id: str,
    payload_hash: str,
    candidates: dict[str, bytes],
) -> None:
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


def _validate_durable_payload(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    identity = _durable_identity(payload)
    operation_id = identity["operation_id"]
    expected = identity["expected_revision"]
    boundary = identity["boundary"]
    cause = _one_line(payload.get("cause"), "cause")
    resume_impact = _one_line(payload.get("resume_impact"), "resume_impact")
    changes, owners, cold_targets = _parse_changes(root, payload.get("changes"))
    mutations, mutation_paths = _parse_mutations(root, payload.get("mutations", []))
    checkpoint_raw = payload.get("checkpoint")
    checkpoint = _parse_checkpoint(checkpoint_raw) if checkpoint_raw is not None else None
    if boundary == "scene_checkpoint" and checkpoint is None:
        raise RPGStateError("input_invalid", "scene_checkpoint boundary requires checkpoint data")
    if boundary == "ordinary" and checkpoint is not None:
        raise RPGStateError("input_invalid", "ordinary boundary cannot include a checkpoint")
    if checkpoint is not None:
        if "current_state.yaml" not in mutation_paths:
            raise RPGStateError("input_invalid", "checkpoint requires a current_state.yaml scene-frame mutation")
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
    }


def _validate_checkpoint_payload(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    identity = _checkpoint_identity(payload)
    operation_id = identity["operation_id"]
    expected = identity["expected_revision"]
    checkpoint = _parse_checkpoint(payload.get("checkpoint"))
    mutations, mutation_paths = _parse_mutations(root, payload.get("mutations", []))
    if "current_state.yaml" not in mutation_paths:
        raise RPGStateError("input_invalid", "checkpoint requires a current_state.yaml scene-frame mutation")
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
    }


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
        parsed = _validate_durable_payload(root, payload)
        already_due, due_reason = _distill_requirement(
            meta["cold_distill_policy"],
            meta["durable_turns_since_distill"],
            boundary="ordinary",
            checkpoint=False,
        )
        if already_due:
            raise RPGStateError("distill_required", f"full distill is already required: {due_reason}")

        new_revision = meta["revision"] + 1
        mechanics_candidate, mechanic_results = _mechanic_candidate(
            root,
            parsed["mechanic_operations"],
            resulting_continuity_revision=new_revision,
        )
        candidates = dict(parsed["mutations"])
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

        new_meta = _state_meta(updated_state)
        required, reason = _distill_requirement(
            meta["cold_distill_policy"],
            new_meta["durable_turns_since_distill"],
            boundary=parsed["boundary"],
            checkpoint=parsed["checkpoint"] is not None,
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
        parsed = _validate_checkpoint_payload(root, payload)
        already_due, due_reason = _distill_requirement(
            meta["cold_distill_policy"],
            meta["durable_turns_since_distill"],
            boundary="ordinary",
            checkpoint=False,
        )
        if already_due:
            raise RPGStateError("distill_required", f"full distill is already required: {due_reason}")

        candidates = dict(parsed["mutations"])
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
        }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", help="Path to the active campaign folder")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("commit-durable", "commit-checkpoint"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--input-json", required=True, help="One JSON transaction envelope")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = json.loads(args.input_json)
        if not isinstance(payload, dict):
            raise RPGStateError("input_invalid", "input JSON must be an object")
        if args.command == "commit-durable":
            result = commit_durable(Path(args.campaign), payload)
        else:
            result = commit_checkpoint(Path(args.campaign), payload)
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
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

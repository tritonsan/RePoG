"""Apply transactional World Voices lifecycle changes to authored artifacts.

The caller supplies all semantic content. This helper only validates ids,
revisions, lifecycle transitions, idempotency, paths, and the player-safe
Dashboard projection.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from check_world_voices import (
    ARTIFACT_FAMILIES,
    CLAIM_CLASSES,
    DISTRIBUTION_STATUSES,
    EPISTEMIC_LAYERS,
    EVENT_KINDS,
    PRODUCTION_STATUSES,
    SAFE_ID,
    SOURCE_KINDS,
    check_world_voices,
)


ACQUIRED_STATUSES = {"delivered", "discovered", "intercepted", "leaked", "copied", "quoted", "archived"}
TRANSITIONS = {
    "dispatch": "in_transit",
    "deliver": "delivered",
    "discover": "discovered",
    "intercept": "intercepted",
    "lose": "lost",
    "leak": "leaked",
    "copy": "copied",
    "quote": "quoted",
    "alter": "altered",
    "forge": "forged",
    "archive_distribution": "archived",
}
SKINS = {
    "personal": "personal",
    "public_media": "newspaper",
    "faction_institutional": "faction",
    "legal_official": "official",
    "intelligence_covert": "intelligence",
    "cultural_academic_commercial": "neutral",
    "custom": "neutral",
}


class WorldVoicesError(ValueError):
    def __init__(self, category: str, message: str, *, exit_code: int = 2) -> None:
        super().__init__(message)
        self.category = category
        self.exit_code = exit_code


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def _commit(changes: dict[Path, bytes]) -> None:
    snapshots: dict[Path, bytes | None] = {}
    written: list[Path] = []
    try:
        for path, payload in changes.items():
            snapshots[path] = path.read_bytes() if path.exists() else None
            _atomic_bytes(path, payload)
            written.append(path)
    except Exception as exc:
        errors: list[str] = []
        for path in reversed(written):
            try:
                if snapshots[path] is None:
                    path.unlink(missing_ok=True)
                else:
                    _atomic_bytes(path, snapshots[path] or b"")
            except Exception as rollback_exc:  # pragma: no cover
                errors.append(str(rollback_exc))
        suffix = f" Rollback errors: {'; '.join(errors)}" if errors else ""
        raise WorldVoicesError("write_failed_rolled_back", f"World Voices write failed and was rolled back: {exc}.{suffix}") from exc


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorldVoicesError("state_invalid", f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise WorldVoicesError("state_invalid", f"{path.name} must contain an object.")
    return value


def _required(payload: dict[str, Any], field: str, *, limit: int = 1000) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise WorldVoicesError("input_invalid", f"{field} must be non-empty text.")
    value = value.strip()
    if len(value) > limit:
        raise WorldVoicesError("input_invalid", f"{field} exceeds {limit} characters.")
    return value


def _id(payload: dict[str, Any], field: str) -> str:
    value = _required(payload, field, limit=80)
    if not SAFE_ID.fullmatch(value):
        raise WorldVoicesError("input_invalid", f"{field} must be a lowercase stable id.")
    return value


def _integer(payload: dict[str, Any], field: str, minimum: int = 0) -> int:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise WorldVoicesError("input_invalid", f"{field} must be an integer of at least {minimum}.")
    return value


def _digest(action: str, payload: dict[str, Any]) -> str:
    semantic = {key: value for key, value in payload.items() if key not in {"expected_revision", "expected_continuity_revision"}}
    raw = json.dumps({"action": action, "payload": semantic}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _prepare(root: Path, action: str, payload: dict[str, Any]) -> tuple[Path, dict[str, Any], str, int, str]:
    index_path = root / "world_voices" / "index.json"
    state = _load(index_path)
    operation_id = _id(payload, "operation_id")
    sequence = _integer(payload, "operation_sequence", 1)
    digest = _digest(action, payload)
    completed = state.get("completed_operations")
    if not isinstance(completed, dict):
        raise WorldVoicesError("state_invalid", "completed_operations must be an object.")
    if operation_id in completed:
        record = completed[operation_id]
        if isinstance(record, dict) and record.get("digest") == digest:
            raise WorldVoicesError("idempotent_replay", json.dumps({"operation_id": operation_id, "sequence": record.get("sequence"), "artifact_id": record.get("artifact_id")}), exit_code=0)
        raise WorldVoicesError("operation_id_conflict", "The operation id was already completed with different content.", exit_code=3)
    expected = _integer(payload, "expected_revision")
    if state.get("revision") != expected:
        raise WorldVoicesError("stale_revision", f"Expected World Voices revision {expected}, found {state.get('revision')}.", exit_code=3)
    expected_continuity = _integer(payload, "expected_continuity_revision")
    if state.get("continuity_revision") != expected_continuity:
        raise WorldVoicesError("stale_continuity", f"Expected continuity revision {expected_continuity}, found {state.get('continuity_revision')}.", exit_code=3)
    result_continuity = payload.get("result_continuity_revision", expected_continuity)
    if isinstance(result_continuity, bool) or not isinstance(result_continuity, int) or result_continuity not in {expected_continuity, expected_continuity + 1}:
        raise WorldVoicesError("input_invalid", "result_continuity_revision must preserve or advance continuity by exactly one.")
    state["_pending_continuity_revision"] = result_continuity
    if sequence != state.get("operation_sequence", 0) + 1:
        raise WorldVoicesError("operation_sequence_conflict", f"Next operation_sequence must be {state.get('operation_sequence', 0) + 1}.", exit_code=3)
    return index_path, copy.deepcopy(state), operation_id, sequence, digest


def _finish(index_path: Path, state: dict[str, Any], operation_id: str, sequence: int, digest: str, action: str, artifact_id: str, changes: dict[Path, bytes] | None = None) -> dict[str, Any]:
    state["continuity_revision"] = state.pop("_pending_continuity_revision", state["continuity_revision"])
    state["revision"] = int(state["revision"]) + 1
    state["operation_sequence"] = sequence
    state["completed_operations"][operation_id] = {
        "sequence": sequence,
        "action": action,
        "artifact_id": artifact_id,
        "digest": digest,
        "completed_at": _now(),
    }
    pending = dict(changes or {})
    pending[index_path] = _json_bytes(state)
    _commit(pending)
    return {
        "ok": True,
        "action": action,
        "artifact_id": artifact_id,
        "operation_id": operation_id,
        "operation_sequence": sequence,
        "revision": state["revision"],
        "continuity_revision": state["continuity_revision"],
    }


def _artifact(state: dict[str, Any], artifact_id: str) -> dict[str, Any]:
    artifacts = state.get("artifacts")
    if not isinstance(artifacts, dict) or artifact_id not in artifacts or not isinstance(artifacts[artifact_id], dict):
        raise WorldVoicesError("artifact_missing", f"Unknown artifact: {artifact_id}", exit_code=3)
    return artifacts[artifact_id]


def _propose(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    index_path, state, operation_id, sequence, digest = _prepare(root, "propose", payload)
    artifact_id = _id(payload, "artifact_id")
    if artifact_id in state.get("artifacts", {}):
        raise WorldVoicesError("artifact_exists", f"Artifact already exists: {artifact_id}", exit_code=3)
    body = _required(payload, "body_markdown", limit=120_000)
    family = _required(payload, "family", limit=50)
    if family not in ARTIFACT_FAMILIES:
        raise WorldVoicesError("input_invalid", "family is outside the approved extensible registry.")
    author = payload.get("author")
    if not isinstance(author, dict) or author.get("kind") not in SOURCE_KINDS:
        raise WorldVoicesError("input_invalid", "author needs an approved kind, ref, and label.")
    author = {"kind": author["kind"], "ref": _required(author, "ref", limit=160), "label": _required(author, "label", limit=160)}
    if author["kind"] == "player" and payload.get("player_wording_approved") is not True:
        raise WorldVoicesError("player_authorship_unapproved", "Player-authored wording requires explicit approval before persistence.", exit_code=3)
    source_event = payload.get("source_event")
    if not isinstance(source_event, dict) or source_event.get("kind") not in EVENT_KINDS:
        raise WorldVoicesError("input_invalid", "source_event needs an approved kind and ref.")
    source_event = {"kind": source_event["kind"], "ref": _id(source_event, "ref")}
    if source_event["kind"] == "artifact" and source_event["ref"] not in state.get("artifacts", {}):
        raise WorldVoicesError("source_event_missing", "The causal source artifact does not exist.")
    if source_event["kind"] == "durable_revision":
        revision_match = re.search(r"(?:^|[-_])(?:rev|revision)[-_]?(\d+)$", source_event["ref"])
        if revision_match is None or int(revision_match.group(1)) > state.get("continuity_revision", -1):
            raise WorldVoicesError("source_event_missing", "Durable source refs must end in an existing rev-N or revision-N.")
    claims = payload.get("claim_basis", [])
    if not isinstance(claims, list):
        raise WorldVoicesError("input_invalid", "claim_basis must be a private list.")
    normalized_claims: list[dict[str, Any]] = []
    claim_ids: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict):
            raise WorldVoicesError("input_invalid", "Each claim_basis entry must be an object.")
        claim_id = _id(claim, "claim_id")
        if claim_id in claim_ids or claim.get("classification") not in CLAIM_CLASSES:
            raise WorldVoicesError("input_invalid", "Claims need unique ids and approved classifications.")
        claim_ids.add(claim_id)
        item = {"claim_id": claim_id, "classification": claim["classification"], "basis": _required(claim, "basis", limit=2000)}
        if claim.get("fact_id") is not None:
            item["fact_id"] = _required(claim, "fact_id", limit=160)
        normalized_claims.append(item)
    epistemic = payload.get("epistemic_basis")
    if not isinstance(epistemic, dict) or set(epistemic) != EPISTEMIC_LAYERS:
        raise WorldVoicesError("input_invalid", "epistemic_basis must contain exactly the ten bounded perspective layers.")
    for key, value in epistemic.items():
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            raise WorldVoicesError("input_invalid", "Each epistemic_basis layer must be a list of bounded notes.")
    thread_id = payload.get("thread_id") or artifact_id
    if not isinstance(thread_id, str) or not SAFE_ID.fullmatch(thread_id):
        raise WorldVoicesError("input_invalid", "thread_id must be a lowercase stable id.")
    root_artifact_id = payload.get("root_artifact_id") or artifact_id
    if root_artifact_id != artifact_id and root_artifact_id not in state.get("artifacts", {}):
        raise WorldVoicesError("input_invalid", "root_artifact_id must reference an existing artifact.")
    reply_to = payload.get("reply_to")
    if reply_to is not None and reply_to not in state.get("artifacts", {}):
        raise WorldVoicesError("input_invalid", "reply_to must reference an existing artifact.")
    links = payload.get("player_safe_links", [])
    if not isinstance(links, list) or any(not isinstance(link, dict) or set(link) != {"kind", "label"} or not all(isinstance(link[key], str) and link[key].strip() for key in link) for link in links):
        raise WorldVoicesError("input_invalid", "player_safe_links must contain only kind and label.")
    body_path = f"world_voices/artifacts/{artifact_id}.md"
    artifact = {
        "artifact_id": artifact_id,
        "title": _required(payload, "title", limit=240),
        "family": family,
        "artifact_type": _required(payload, "artifact_type", limit=80),
        "author": author,
        "source_event": source_event,
        "thread_id": thread_id,
        "root_artifact_id": root_artifact_id,
        "reply_to": reply_to,
        "version": 1,
        "supersedes": None,
        "superseded_by": None,
        "retraction_artifact_id": None,
        "authored_time": _required(payload, "authored_time", limit=160),
        "authored_time_index": _integer(payload, "authored_time_index"),
        "authored_place": _required(payload, "authored_place", limit=200),
        "intended_audience": _required(payload, "intended_audience", limit=400),
        "intent": _required(payload, "intent", limit=100),
        "channel": _required(payload, "channel", limit=160),
        "production_status": "proposed",
        "actual_provenance": _required(payload, "actual_provenance", limit=1000),
        "perceived_provenance": _required(payload, "perceived_provenance", limit=1000),
        "epistemic_basis": epistemic,
        "claim_basis": normalized_claims,
        "player_safe_links": links,
        "body_path": body_path,
        "distributions": [],
        "created_by_operation_id": operation_id,
        "created_revision": int(state.get("_pending_continuity_revision", state["continuity_revision"])),
        "player_wording_approved": True if author["kind"] == "player" else None,
    }
    state["artifacts"][artifact_id] = artifact
    result = _finish(index_path, state, operation_id, sequence, digest, "propose", artifact_id, {root / body_path: (body.rstrip() + "\n").encode("utf-8")})
    result["production_status"] = "proposed"
    result["requires_review"] = True
    result["dashboard_refresh_required"] = False
    return result


def _status_change(root: Path, action: str, payload: dict[str, Any], allowed: set[str], target: str) -> dict[str, Any]:
    index_path, state, operation_id, sequence, digest = _prepare(root, action, payload)
    artifact_id = _id(payload, "artifact_id")
    artifact = _artifact(state, artifact_id)
    if artifact.get("production_status") not in allowed:
        raise WorldVoicesError("lifecycle_invalid", f"Cannot {action} an artifact in {artifact.get('production_status')} status.", exit_code=3)
    artifact["production_status"] = target
    result = _finish(index_path, state, operation_id, sequence, digest, action, artifact_id)
    result["production_status"] = target
    result["dashboard_refresh_required"] = False
    return result


def _schedule(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    index_path, state, operation_id, sequence, digest = _prepare(root, "schedule", payload)
    artifact_id = _id(payload, "artifact_id")
    artifact = _artifact(state, artifact_id)
    if artifact.get("production_status") != "approved":
        raise WorldVoicesError("lifecycle_invalid", "Only an approved artifact may enter distribution.", exit_code=3)
    distribution_id = _id(payload, "distribution_id")
    if any(distribution_id == record.get("distribution_id") for item in state["artifacts"].values() for record in item.get("distributions", [])):
        raise WorldVoicesError("distribution_exists", f"Distribution already exists: {distribution_id}", exit_code=3)
    recipients = payload.get("recipients")
    if not isinstance(recipients, list) or not recipients or any(not isinstance(item, str) or not item.strip() for item in recipients):
        raise WorldVoicesError("input_invalid", "recipients must be a non-empty list of actor or public refs.")
    public = payload.get("public", False)
    if not isinstance(public, bool):
        raise WorldVoicesError("input_invalid", "public must be boolean.")
    artifact["distributions"].append({
        "distribution_id": distribution_id,
        "status": "scheduled",
        "channel": _required(payload, "channel", limit=160),
        "recipients": [item.strip() for item in recipients],
        "public": public,
        "scheduled_time": _required(payload, "scheduled_time", limit=160),
        "scheduled_time_index": _integer(payload, "scheduled_time_index"),
        "completed_time": None,
        "completed_time_index": None,
        "causal_basis": _required(payload, "causal_basis", limit=1000),
        "player_access": False,
        "dashboard_eligible": False,
        "acquisition_context": "",
        "operation_id": operation_id,
        "history": [{"status": "scheduled", "time": _required(payload, "scheduled_time", limit=160), "time_index": _integer(payload, "scheduled_time_index"), "operation_id": operation_id}],
        "knowledge_revision": None,
    })
    result = _finish(index_path, state, operation_id, sequence, digest, "schedule", artifact_id)
    result.update({"distribution_id": distribution_id, "distribution_status": "scheduled", "dashboard_refresh_required": False})
    return result


def _distribution_transition(root: Path, action: str, payload: dict[str, Any]) -> dict[str, Any]:
    index_path, state, operation_id, sequence, digest = _prepare(root, action, payload)
    artifact_id = _id(payload, "artifact_id")
    artifact = _artifact(state, artifact_id)
    distribution_id = _id(payload, "distribution_id")
    distribution = next((item for item in artifact.get("distributions", []) if item.get("distribution_id") == distribution_id), None)
    if not isinstance(distribution, dict):
        raise WorldVoicesError("distribution_missing", f"Unknown distribution: {distribution_id}", exit_code=3)
    current = distribution.get("status")
    target = TRANSITIONS[action]
    if action == "dispatch":
        allowed_current = {"scheduled"}
    elif action == "archive_distribution":
        allowed_current = ACQUIRED_STATUSES.union({"lost", "altered", "forged"}) - {"archived"}
    else:
        allowed_current = {"scheduled", "in_transit"}
    if current not in allowed_current:
        raise WorldVoicesError("lifecycle_invalid", f"Cannot {action} a distribution in {current} status.", exit_code=3)
    if action == "archive_distribution":
        archive_time = _required(payload, "completed_time", limit=160)
        archive_time_index = _integer(payload, "completed_time_index")
        latest_time_index = max((int(item.get("time_index", 0)) for item in distribution.get("history", [])), default=int(distribution["scheduled_time_index"]))
        if archive_time_index < latest_time_index:
            raise WorldVoicesError("input_invalid", "Archive time cannot precede the distribution's latest lifecycle event.")
        distribution.update({
            "status": target,
            "operation_id": operation_id,
        })
        distribution.setdefault("history", []).append({"status": target, "time": archive_time, "time_index": archive_time_index, "operation_id": operation_id})
        result = _finish(index_path, state, operation_id, sequence, digest, action, artifact_id)
        result.update({
            "distribution_id": distribution_id,
            "distribution_status": target,
            "dashboard_refresh_required": bool(distribution.get("dashboard_eligible")),
            "knowledge_update_confirmed": bool(distribution.get("player_access")),
        })
        return result
    player_access = payload.get("player_access", False)
    dashboard_eligible = payload.get("dashboard_eligible", False)
    if not isinstance(player_access, bool) or not isinstance(dashboard_eligible, bool) or dashboard_eligible and not player_access:
        raise WorldVoicesError("input_invalid", "Dashboard eligibility requires explicit player_access.")
    if player_access and target not in ACQUIRED_STATUSES:
        raise WorldVoicesError("lifecycle_invalid", "This transition cannot grant player access.")
    acquisition = ""
    knowledge_revision = None
    if player_access:
        acquisition = _required(payload, "acquisition_context", limit=1200)
        if payload.get("knowledge_update_confirmed") is not True:
            raise WorldVoicesError("knowledge_update_required", "Confirm the matching knowledge-boundary update before granting player access.", exit_code=3)
        knowledge_revision = _integer(payload, "knowledge_revision")
        expected_result = payload.get("result_continuity_revision", payload.get("expected_continuity_revision"))
        if knowledge_revision != expected_result:
            raise WorldVoicesError("knowledge_revision_mismatch", "knowledge_revision must match this durable continuity change.", exit_code=3)
    distribution.update({
        "status": target,
        "completed_time": _required(payload, "completed_time", limit=160),
        "completed_time_index": _integer(payload, "completed_time_index"),
        "player_access": player_access,
        "dashboard_eligible": dashboard_eligible,
        "acquisition_context": acquisition,
        "operation_id": operation_id,
        "knowledge_revision": knowledge_revision,
    })
    if distribution["completed_time_index"] < distribution["scheduled_time_index"]:
        raise WorldVoicesError("input_invalid", "completed_time_index cannot precede scheduled_time_index.")
    distribution.setdefault("history", []).append({"status": target, "time": distribution["completed_time"], "time_index": distribution["completed_time_index"], "operation_id": operation_id})
    result = _finish(index_path, state, operation_id, sequence, digest, action, artifact_id)
    result.update({
        "distribution_id": distribution_id,
        "distribution_status": target,
        "dashboard_refresh_required": bool(dashboard_eligible),
        "knowledge_update_confirmed": bool(player_access),
    })
    return result


def _link_version(root: Path, action: str, payload: dict[str, Any]) -> dict[str, Any]:
    index_path, state, operation_id, sequence, digest = _prepare(root, action, payload)
    artifact_id = _id(payload, "artifact_id")
    linked_field = "retraction_artifact_id" if action == "retract" else "superseded_by"
    linked_id = _id(payload, linked_field)
    original = _artifact(state, artifact_id)
    linked = _artifact(state, linked_id)
    if artifact_id == linked_id or linked.get("production_status") != "approved":
        raise WorldVoicesError("lifecycle_invalid", "The linked correction must be a distinct approved artifact.", exit_code=3)
    if original.get("production_status") not in {"approved", "archived"}:
        raise WorldVoicesError("lifecycle_invalid", "Only approved or archived artifacts may be retracted or superseded.", exit_code=3)
    if original.get("thread_id") != linked.get("thread_id"):
        raise WorldVoicesError("lifecycle_invalid", "Version links must remain in the same thread.", exit_code=3)
    original[linked_field] = linked_id
    original["production_status"] = "retracted" if action == "retract" else "superseded"
    linked["supersedes"] = artifact_id
    linked["version"] = max(int(original.get("version", 1)) + 1, int(linked.get("version", 1)))
    result = _finish(index_path, state, operation_id, sequence, digest, action, artifact_id)
    result.update({"linked_artifact_id": linked_id, "dashboard_refresh_required": any(d.get("dashboard_eligible") for d in original.get("distributions", []))})
    return result


def _projection_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def _profile_world_voices(root: Path) -> dict[str, str]:
    path = root / "play_profile.yaml"
    if not path.is_file():
        return {"mode": "off", "approval_policy": "review_each", "dashboard_policy": "off"}
    text = path.read_text(encoding="utf-8")
    block = re.search(r"(?ms)^world_voices:\s*$\n(?P<body>(?:^[ \t]+.*(?:\n|\Z))*)", text)
    if block is None:
        return {"mode": "off", "approval_policy": "review_each", "dashboard_policy": "off"}
    values: dict[str, str] = {}
    for key in ("mode", "approval_policy", "dashboard_policy"):
        match = re.search(rf"(?m)^\s+{key}:\s*[\"']?([a-z_]+)", block.group("body"))
        values[key] = match.group(1) if match else ("review_each" if key == "approval_policy" else "off")
    return values


def _project(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    state = _load(root / "world_voices" / "index.json")
    expected = _integer(payload, "expected_revision")
    if state.get("revision") != expected:
        raise WorldVoicesError("stale_revision", f"Expected World Voices revision {expected}, found {state.get('revision')}.", exit_code=3)
    expected_source = _integer(payload, "expected_source_revision")
    if expected_source != state.get("continuity_revision"):
        raise WorldVoicesError("stale_continuity", "Projection source revision does not match World Voices continuity revision.", exit_code=3)
    dashboard_policy = _profile_world_voices(root)["dashboard_policy"]
    if dashboard_policy == "off":
        raise WorldVoicesError("projection_disabled", "World Voices Dashboard policy is off.", exit_code=3)
    visible: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for artifact in state.get("artifacts", {}).values():
        eligible = [record for record in artifact.get("distributions", []) if record.get("player_access") and record.get("dashboard_eligible") and record.get("status") in ACQUIRED_STATUSES]
        if dashboard_policy == "delivered_only":
            eligible = [record for record in eligible if not record.get("public")]
        if eligible:
            visible.append((artifact, max(eligible, key=lambda item: int(item.get("completed_time_index", 0)))))
    visible.sort(key=lambda pair: (int(pair[1].get("completed_time_index", 0)), int(pair[0].get("authored_time_index", 0)), str(pair[0].get("artifact_id"))), reverse=True)
    projection_root = root / "dashboard" / "assets" / "world_voices"
    projection_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".world_voices_projection.", dir=projection_root.parent))
    try:
        (temporary / "pages").mkdir()
        (temporary / "documents").mkdir()
        summaries: list[dict[str, Any]] = []
        key_by_id = {artifact["artifact_id"]: _projection_key(artifact["artifact_id"]) for artifact, _ in visible}
        for artifact, acquisition in visible:
            key = key_by_id[artifact["artifact_id"]]
            body_path = root / artifact["body_path"]
            body = body_path.read_text(encoding="utf-8")
            if len(body) > 120_000:
                raise WorldVoicesError("projection_too_large", f"Artifact body exceeds projection bound: {artifact['artifact_id']}")
            thread_key = _projection_key(str(artifact["thread_id"]))
            compare_group = _projection_key(f"event:{artifact['source_event']['kind']}:{artifact['source_event']['ref']}")
            path = f"assets/world_voices/documents/{key}.json"
            document = {
                "document_version": 1,
                "key": key,
                "title": artifact["title"],
                "family": artifact["family"],
                "artifact_type": artifact["artifact_type"],
                "source_label": artifact["author"]["label"],
                "authored_time": artifact["authored_time"],
                "authored_order": artifact["authored_time_index"],
                "authored_place": artifact["authored_place"],
                "intended_audience": artifact["intended_audience"],
                "channel": acquisition["channel"],
                "skin": SKINS.get(artifact["family"], "neutral"),
                "body_text": body,
                "acquisition_context": acquisition["acquisition_context"],
                "thread_key": thread_key,
                "reply_to_key": key_by_id.get(artifact.get("reply_to"), ""),
                "supersedes_key": key_by_id.get(artifact.get("supersedes"), ""),
                "status": artifact["production_status"],
                "compare_group": compare_group,
                "links": artifact.get("player_safe_links", []),
                "access_scope": "public" if acquisition.get("public") else "personal",
                "received_order": acquisition["completed_time_index"],
            }
            _atomic_bytes(temporary / "documents" / f"{key}.json", _json_bytes(document))
            summaries.append({
                "key": key,
                "path": path,
                "title": artifact["title"],
                "family": artifact["family"],
                "artifact_type": artifact["artifact_type"],
                "source_label": artifact["author"]["label"],
                "authored_time": artifact["authored_time"],
                "authored_order": artifact["authored_time_index"],
                "received_time": acquisition["completed_time"],
                "received_order": acquisition["completed_time_index"],
                "thread_key": thread_key,
                "compare_group": compare_group,
                "status": artifact["production_status"],
                "unread_hint": True,
                "acquisition_summary": acquisition["acquisition_context"],
                "access_scope": "public" if acquisition.get("public") else "personal",
            })
        page_size = 40
        pages: list[dict[str, Any]] = []
        for index in range(0, len(summaries), page_size):
            number = index // page_size + 1
            chunk = summaries[index:index + page_size]
            page_name = f"page-{number:04d}.json"
            _atomic_bytes(temporary / "pages" / page_name, _json_bytes({"page_version": 1, "generated_revision": expected_source, "page": number, "documents": chunk}))
            pages.append({"path": f"assets/world_voices/pages/{page_name}", "count": len(chunk)})
        if len(pages) > 128:
            raise WorldVoicesError("projection_too_large", "Player-safe World Voices projection exceeds 128 bounded pages.")
        catalog = {"projection_version": 1, "generated_revision": expected_source, "page_size": page_size, "visible_count": len(summaries), "pages": pages}
        _atomic_bytes(temporary / "catalog.json", _json_bytes(catalog))
        backup = projection_root.with_name(f".{projection_root.name}.backup")
        if backup.exists():
            shutil.rmtree(backup)
        if projection_root.exists():
            os.replace(projection_root, backup)
        try:
            os.replace(temporary, projection_root)
            result = check_world_voices(root, projection="full")
            if not result["ok"]:
                raise WorldVoicesError("projection_invalid", "Generated projection did not pass World Voices validation.")
        except Exception:
            if projection_root.exists():
                shutil.rmtree(projection_root, ignore_errors=True)
            if backup.exists():
                os.replace(backup, projection_root)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {"ok": True, "action": "project", "revision": expected, "source_revision": expected_source, "visible_count": len(summaries), "catalog_path": "assets/world_voices/catalog.json"}


def apply(root: Path, action: str, payload: dict[str, Any]) -> dict[str, Any]:
    root = root.resolve()
    if not (root / "world_voices" / "index.json").is_file():
        raise WorldVoicesError("world_voices_missing", "Campaign has no World Voices memory. Missing configuration remains off for compatibility.")
    profile = _profile_world_voices(root)
    if action not in {"validate", "project"} and profile["mode"] == "off":
        raise WorldVoicesError("world_voices_disabled", "World Voices is off in the materialized play profile.", exit_code=3)
    if action == "propose":
        return _propose(root, payload)
    if action == "approve":
        if payload.get("semantic_review_confirmed") is not True:
            raise WorldVoicesError("semantic_review_required", "Confirm the GPT-5.6 bounded-perspective safety review before approval.", exit_code=3)
        if profile["approval_policy"] == "review_each" and payload.get("approval_confirmed") is not True:
            raise WorldVoicesError("approval_required", "This campaign requires explicit review before canonization.", exit_code=3)
        return _status_change(root, action, payload, {"proposed"}, "approved")
    if action == "reject":
        return _status_change(root, action, payload, {"proposed"}, "rejected")
    if action == "schedule":
        return _schedule(root, payload)
    if action in TRANSITIONS:
        return _distribution_transition(root, action, payload)
    if action in {"retract", "supersede"}:
        return _link_version(root, action, payload)
    if action == "archive":
        return _status_change(root, action, payload, {"approved", "retracted", "superseded"}, "archived")
    if action == "project":
        return _project(root, payload)
    if action == "validate":
        return check_world_voices(root, projection=str(payload.get("projection", "full")))
    raise WorldVoicesError("action_invalid", f"Unsupported action: {action}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign")
    parser.add_argument("action", choices=("propose", "approve", "reject", "schedule", *TRANSITIONS, "retract", "supersede", "archive", "project", "validate"))
    parser.add_argument("--input-json", default="{}")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input_json)
        if not isinstance(payload, dict):
            raise WorldVoicesError("input_invalid", "--input-json must contain an object.")
        result = apply(Path(args.campaign), args.action, payload)
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0 if result.get("ok") else 2
    except json.JSONDecodeError as exc:
        error = WorldVoicesError("input_invalid", f"Invalid JSON: {exc}")
    except WorldVoicesError as exc:
        error = exc
    if error.category == "idempotent_replay" and error.exit_code == 0:
        replay = json.loads(str(error))
        print(json.dumps({"ok": True, "action": args.action, "idempotent_replay": True, **replay}, indent=2))
        return 0
    print(json.dumps({"ok": False, "failure_category": error.category, "failure_reason": str(error)}, indent=2))
    return error.exit_code


if __name__ == "__main__":
    sys.exit(main())

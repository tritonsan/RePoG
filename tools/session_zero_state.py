"""Manage the canonical RPG Deep Session 0 v8 decision state.

The helper is intentionally semantic-free.  The coordinator decides what a
Player answer means and supplies controlled trigger tags from the Deep v8
manifest.  This module only enforces ordering, revisions, idempotency,
extension completion evidence, approval dependencies, and the small
``setup_profile.yaml`` progress mirror.

All mutating commands use an operation id plus an expected setup revision and
commit ``session_zero_state.json`` and ``setup_profile.yaml`` as one
rollback-protected operation.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any, Iterator


STATE_FILE = "session_zero_state.json"
SETUP_FILE = "setup_profile.yaml"
SUMMARY_FILE = "session_zero.md"
SUMMARY_HEADING = "## RPG Deep v8 Stage Summary"
FLOW_ID = "rpg_deep_v8"
STATE_SCHEMA_VERSION = 1
MANIFEST_RELATIVE = Path("workflows/worldbuild/deep_v8/manifest.json")

STAGE_STATUSES = {"not_started", "active", "needs_review", "complete", "stale"}
DECISION_STATUSES = {"locked", "defaulted", "deferred"}
DECISION_SOURCES = {"player", "derived", "defaulted", "deferred"}
EXTENSION_STATUSES = {"not_applicable", "active", "complete", "defaulted"}
EXTENSION_DEPTHS = {"not_applicable", "baseline", "deep"}
GATE_STATUSES = {"pending", "complete", "stale"}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SHA256_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")

STAGE_IDS = (
    "01_north_star_authority",
    "02_research_canon_grounding",
    "03_character_core",
    "04_thin_world_kernel",
    "05_character_realization_mechanics",
    "06_living_world_ecology",
    "07_runtime_experience_contract",
    "08_reciprocity_campaign_horizon",
    "09_first_act_preparation",
)
STAGE_TITLES = {
    "01_north_star_authority": "North Star And Authority",
    "02_research_canon_grounding": "Research, Canon, And Grounding",
    "03_character_core": "Character Core",
    "04_thin_world_kernel": "Thin World Kernel",
    "05_character_realization_mechanics": "Character Realization And Mechanics",
    "06_living_world_ecology": "Living World Ecology",
    "07_runtime_experience_contract": "Runtime Experience Contract",
    "08_reciprocity_campaign_horizon": "Reciprocity And Campaign Horizon",
    "09_first_act_preparation": "First Act Preparation",
}
GATE_IDS = (
    "research_scope_locked",
    "stages_1_8_complete",
    "first_act_design_complete",
    "design_direction_approved",
    "preparation_materialized",
    "cross_read_passed",
    "integrated_review_accepted",
    "preparation_approved",
    "draft_preflight_passed",
    "ready_and_snapshotted",
)

# Used only when a copied campaign is inspected without the workflow corpus.
# A present but malformed manifest is never hidden by this fallback.
FALLBACK_MANIFEST: dict[str, Any] = {
    "schema_version": 8,
    "workflow_id": FLOW_ID,
    "stages": [
        {
            "id": stage_id,
            "title": STAGE_TITLES[stage_id],
            "prerequisites": ([] if index == 0 else [STAGE_IDS[index - 1]]),
            "decisions": [],
        }
        for index, stage_id in enumerate(STAGE_IDS)
    ],
    "extensions": {
        "character_interior": {"stages": ["03_character_core"], "owner_refs": []},
        "world_fabric": {"stages": ["04_thin_world_kernel"], "owner_refs": []},
        "mechanics_detail": {"stages": ["05_character_realization_mechanics"], "owner_refs": []},
        "location_network": {"stages": ["06_living_world_ecology"], "owner_refs": []},
        "faction_information": {"stages": ["06_living_world_ecology"], "owner_refs": []},
        "group": {"stages": ["06_living_world_ecology"], "owner_refs": []},
        "character_embedding": {"stages": ["06_living_world_ecology"], "owner_refs": []},
        "advancement_detail": {"stages": ["08_reciprocity_campaign_horizon"], "owner_refs": []},
        "campaign_architecture": {
            "stages": ["08_reciprocity_campaign_horizon", "09_first_act_preparation"],
            "owner_refs": [],
        },
    },
    "controlled_trigger_tags": {},
    "gates": [{"id": gate_id, "prerequisites": []} for gate_id in GATE_IDS],
}


class StateError(ValueError):
    """Typed structural state failure suitable for CLI and validator use."""

    def __init__(self, category: str, reason: str) -> None:
        super().__init__(reason)
        self.category = category


def _strict_int(value: Any, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _safe_id(value: Any, label: str) -> str:
    if not _nonempty(value) or SAFE_ID.fullmatch(value.strip()) is None:
        raise StateError("input_invalid", f"{label} must be a short stable id")
    return value.strip()


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StateError("file_missing", f"missing {label}: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StateError("state_invalid", f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise StateError("state_invalid", f"{label} must contain a JSON object")
    return value


def _campaign_root(campaign: Path) -> Path:
    root = campaign.resolve()
    if not root.is_dir():
        raise StateError("campaign_invalid", f"campaign folder does not exist: {root}")
    return root


def _manifest_path(root: Path) -> Path | None:
    candidates = (
        root.parent / MANIFEST_RELATIVE,
        Path(__file__).resolve().parents[1] / MANIFEST_RELATIVE,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def load_manifest(campaign: Path, *, require_full: bool = False) -> dict[str, Any]:
    """Load and minimally normalize the Deep v8 manifest.

    A standalone copied campaign may omit workflow sources, in which case the
    bundled structural fallback keeps state inspection and migration usable.
    """

    root = _campaign_root(campaign)
    path = _manifest_path(root)
    if path is None and require_full:
        raise StateError(
            "manifest_missing",
            "Deep v8 mutations and readiness checks require workflows/worldbuild/deep_v8/manifest.json",
        )
    manifest = copy.deepcopy(FALLBACK_MANIFEST) if path is None else _read_json(path, "Deep v8 manifest")
    if manifest.get("workflow_id", manifest.get("flow_id")) != FLOW_ID:
        raise StateError("manifest_invalid", f"Deep v8 manifest must identify {FLOW_ID}")
    raw_stages = manifest.get("stages")
    if not isinstance(raw_stages, list):
        raise StateError("manifest_invalid", "Deep v8 manifest stages must be a list")
    stage_ids = [item.get("id") for item in raw_stages if isinstance(item, dict)]
    if stage_ids != list(STAGE_IDS):
        raise StateError("manifest_invalid", "Deep v8 manifest must contain the canonical nine stages in order")
    extensions = manifest.get("extensions", {})
    owners = manifest.get("owner_refs", {})
    if not isinstance(owners, dict):
        raise StateError("manifest_invalid", "Deep v8 manifest owner_refs must be an object")
    for owner_id, owner_path in owners.items():
        _safe_id(owner_id, "manifest owner id")
        if not _nonempty(owner_path) or not owner_path.startswith("campaign/"):
            raise StateError("manifest_invalid", f"owner {owner_id} must point inside campaign/")
    for stage in raw_stages:
        for decision in stage.get("decisions", []):
            refs = decision.get("owner_refs", []) if isinstance(decision, dict) else []
            if not isinstance(refs, list) or any(ref not in owners for ref in refs):
                raise StateError("manifest_invalid", f"stage {stage.get('id')} has an unknown decision owner")
    if not isinstance(extensions, dict):
        raise StateError("manifest_invalid", "Deep v8 manifest extensions must be an object")
    for extension_id, definition in extensions.items():
        _safe_id(extension_id, "manifest extension id")
        if not isinstance(definition, dict):
            raise StateError("manifest_invalid", f"extension {extension_id} must be an object")
        stage_refs = definition.get("stages", definition.get("stage_ids", []))
        if not isinstance(stage_refs, list) or not stage_refs or any(ref not in STAGE_IDS for ref in stage_refs):
            raise StateError("manifest_invalid", f"extension {extension_id} has invalid stages")
        owner_refs = definition.get("owner_refs", [])
        if not isinstance(owner_refs, list) or any(item not in owners for item in owner_refs):
            raise StateError("manifest_invalid", f"extension {extension_id} has invalid owner refs")
    tags = manifest.get("controlled_trigger_tags", {})
    if not isinstance(tags, dict):
        raise StateError("manifest_invalid", "controlled_trigger_tags must be an object")
    for tag, rule in tags.items():
        _safe_id(tag, "controlled trigger tag")
        if isinstance(rule, dict):
            activate = rule.get("activate", [])
        elif isinstance(rule, list):
            activate = rule
        else:
            raise StateError("manifest_invalid", f"trigger rule {tag} must be an object or list")
        if not isinstance(activate, list) or any(item not in extensions for item in activate):
            raise StateError("manifest_invalid", f"trigger rule {tag} activates an unknown extension")
        if isinstance(rule, dict) and activate and rule.get("depth") not in {"baseline", "deep"}:
            raise StateError("manifest_invalid", f"trigger rule {tag} must declare baseline or deep depth")
    gate_ids = [gate.get("id") for gate in manifest.get("gates", []) if isinstance(gate, dict)]
    if gate_ids != list(GATE_IDS):
        raise StateError("manifest_invalid", "Deep v8 manifest must contain the canonical gate chain")
    return manifest


def _stage_definitions(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in manifest["stages"]}


def _extension_stage_ids(definition: dict[str, Any]) -> list[str]:
    return list(definition.get("stages", definition.get("stage_ids", [])))


def initial_state(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = copy.deepcopy(manifest or FALLBACK_MANIFEST)
    stages: dict[str, Any] = {}
    for index, stage_id in enumerate(STAGE_IDS):
        stages[stage_id] = {
            "status": "active" if index == 0 else "not_started",
            "completed_revision": None,
            "output_refs": [],
            "output_digest": "",
            "invalidation_reason": "",
        }
    extensions: dict[str, Any] = {}
    for extension_id, definition in manifest.get("extensions", {}).items():
        stage_ids = _extension_stage_ids(definition)
        extensions[extension_id] = {
            "status": "not_applicable",
            "depth": "not_applicable",
            "stage_ids": stage_ids,
            "activated_by": [],
            "stages": {
                stage_id: {
                    "status": "not_applicable",
                    "revision": None,
                    "output_refs": [],
                    "output_digest": "",
                    "acceptance_decision_id": "",
                    "invalidation_reason": "",
                }
                for stage_id in stage_ids
            },
        }
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "flow_id": FLOW_ID,
        "setup_revision": 0,
        "current_stage": STAGE_IDS[0],
        "stages": stages,
        "decisions": [],
        "extensions": extensions,
        "gates": {
            gate_id: {
                "status": "pending",
                "revision": None,
                "input_digest": "",
                "output_digest": "",
                "decided_by": "",
                "evidence": {},
                "invalidation_reason": "",
            }
            for gate_id in GATE_IDS
        },
        "operation_registry": {},
        "last_operation": None,
        "fatigue": {
            "decision_count": 0,
            "decisions_since_checkpoint": 0,
            "last_checkpoint_revision": 0,
            "last_checkpoint_decision_count": 0,
        },
    }


def _relative_ref(value: Any, label: str) -> str:
    if not _nonempty(value) or "\\" in value or "\x00" in value:
        raise StateError("input_invalid", f"{label} must be a campaign-relative POSIX reference")
    pure = PurePosixPath(value.strip())
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise StateError("input_invalid", f"{label} must stay inside the campaign")
    return pure.as_posix()


def _refs(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        raise StateError("input_invalid", f"{label} must be a list")
    result = [_relative_ref(item, f"{label} item") for item in value]
    if len(result) != len(set(result)):
        raise StateError("input_invalid", f"{label} contains duplicates")
    return result


def _validate_digest(value: Any, label: str, *, allow_empty: bool = True) -> str:
    if value == "" and allow_empty:
        return ""
    if not _nonempty(value) or SHA256_DIGEST.fullmatch(value.strip()) is None:
        raise StateError("input_invalid", f"{label} must be a sha256:<64 lowercase hex> digest")
    return value.strip()


def compute_output_digest(campaign: Path, output_refs: list[str]) -> str:
    """Hash sorted campaign-relative paths plus their current bytes."""

    root = _campaign_root(campaign)
    refs = _refs(output_refs, "output_refs")
    if not refs:
        raise StateError("output_missing", "at least one output reference is required")
    entries: list[dict[str, Any]] = []
    for relative in sorted(refs):
        path = (root / Path(*PurePosixPath(relative).parts)).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:  # defensive; _relative_ref already rejects traversal
            raise StateError("path_forbidden", f"output reference escapes the campaign: {relative}") from exc
        if not path.is_file():
            raise StateError("output_missing", f"materialized output does not exist: {relative}")
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise StateError("output_missing", f"cannot read materialized output {relative}: {exc}") from exc
        entries.append(
            {
                "path": relative,
                "size": len(payload),
                "content_sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return _canonical_hash(entries)


def _campaign_owner_path(manifest: dict[str, Any], owner_id: str) -> str:
    owners = manifest.get("owner_refs", {})
    raw = owners.get(owner_id) if isinstance(owners, dict) else None
    if not _nonempty(raw) or not raw.startswith("campaign/"):
        raise StateError("manifest_invalid", f"owner ref {owner_id} must point inside campaign/")
    return raw.removeprefix("campaign/")


def _ref_matches_owner(relative: str, owner_path: str) -> bool:
    owner_path = owner_path.strip()
    if owner_path.endswith("/"):
        if not relative.startswith(owner_path) or relative == owner_path:
            return False
        basename = PurePosixPath(relative).name.casefold()
        return basename not in {
            "_template.md",
            "_companion_template.md",
            "readme.md",
            ".gitkeep",
        }
    return relative == owner_path


def _safe_manifest_pattern(value: Any, label: str) -> str:
    if not _nonempty(value) or "\\" in value or "\x00" in value:
        raise StateError("manifest_invalid", f"{label} must be a campaign-relative POSIX glob")
    pure = PurePosixPath(value.strip())
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise StateError("manifest_invalid", f"{label} must stay inside the campaign")
    return pure.as_posix()


def _bounded_output_refs(
    manifest: dict[str, Any],
    refs: list[str],
    *,
    owner_ids: list[str],
    patterns: list[str] | None = None,
    label: str,
) -> None:
    owner_paths = [_campaign_owner_path(manifest, owner_id) for owner_id in owner_ids]
    safe_patterns = [_safe_manifest_pattern(item, f"{label} evidence pattern") for item in (patterns or [])]
    for relative in refs:
        owner_match = any(_ref_matches_owner(relative, owner_path) for owner_path in owner_paths)
        pattern_match = any(PurePosixPath(relative).match(pattern) for pattern in safe_patterns)
        if not owner_match and not pattern_match:
            raise StateError(
                "output_ref_unowned",
                f"{label} evidence is outside its manifest owners: {relative}",
            )


def _stage_evidence_contract(
    manifest: dict[str, Any], stage_id: str, decisions: dict[str, dict[str, Any]] | None = None
) -> tuple[list[str], list[str]]:
    definition = _stage_definitions(manifest)[stage_id]
    explicit = definition.get("evidence_owner_refs")
    if explicit is not None:
        if not isinstance(explicit, list) or any(not _nonempty(item) for item in explicit):
            raise StateError("manifest_invalid", f"stage {stage_id} evidence_owner_refs is invalid")
        owner_ids = list(explicit)
    else:
        owner_ids = []
        for decision in definition.get("decisions", []):
            if not isinstance(decision, dict):
                continue
            if decisions is not None and decisions.get(decision.get("id"), {}).get("status") == "deferred":
                continue
            for owner_id in decision.get("owner_refs", []):
                if owner_id not in {"setup_progress", "decision_log", "snapshot"} and owner_id not in owner_ids:
                    owner_ids.append(owner_id)
    patterns = definition.get("evidence_ref_patterns", [])
    if not isinstance(patterns, list):
        raise StateError("manifest_invalid", f"stage {stage_id} evidence_ref_patterns must be a list")
    return owner_ids, list(patterns)


def _validate_stage_output_refs(
    manifest: dict[str, Any],
    stage_id: str,
    refs: list[str],
    decisions: dict[str, dict[str, Any]] | None = None,
) -> None:
    owner_ids, patterns = _stage_evidence_contract(manifest, stage_id, decisions)
    _bounded_output_refs(
        manifest,
        refs,
        owner_ids=owner_ids,
        patterns=patterns,
        label=f"stage {stage_id}",
    )
    for owner_id in owner_ids:
        owner_path = _campaign_owner_path(manifest, owner_id)
        if not any(_ref_matches_owner(relative, owner_path) for relative in refs):
            raise StateError(
                "output_owner_missing",
                f"stage {stage_id} has no materialized evidence for owner {owner_id}",
            )


def _validate_extension_output_refs(
    manifest: dict[str, Any], extension_id: str, stage_id: str, refs: list[str]
) -> None:
    definition = manifest.get("extensions", {}).get(extension_id, {})
    stage_owners = definition.get("stage_owner_refs", {}) if isinstance(definition, dict) else {}
    owner_ids = (
        stage_owners.get(stage_id, definition.get("owner_refs", []))
        if isinstance(stage_owners, dict)
        else []
    )
    patterns = definition.get("evidence_ref_patterns", []) if isinstance(definition, dict) else []
    if not isinstance(owner_ids, list) or not isinstance(patterns, list):
        raise StateError("manifest_invalid", f"extension {extension_id} evidence contract is invalid")
    owner_ids = [item for item in owner_ids if item not in {"setup_progress", "decision_log", "snapshot"}]
    _bounded_output_refs(
        manifest,
        refs,
        owner_ids=owner_ids,
        patterns=patterns,
        label=f"extension {extension_id}",
    )
    for owner_id in owner_ids:
        owner_path = _campaign_owner_path(manifest, owner_id)
        if not any(_ref_matches_owner(relative, owner_path) for relative in refs):
            raise StateError(
                "output_owner_missing",
                f"extension {extension_id} has no materialized evidence for owner {owner_id}",
            )


def _decision_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["decision_id"]: item for item in state["decisions"]}


def _structured_contracts(manifest: dict[str, Any]) -> dict[str, Any]:
    value = manifest.get("structured_contracts", {})
    if not isinstance(value, dict):
        raise StateError("manifest_invalid", "structured_contracts must be an object")
    return value


def _object_value(decision: dict[str, Any], label: str) -> dict[str, Any]:
    value = decision.get("value")
    if not isinstance(value, dict):
        raise StateError("decision_contract", f"{label} must use a structured object value")
    return value


def _decision_contract_error(message: str, *, state_validation: bool) -> None:
    raise StateError("state_invalid" if state_validation else "decision_contract", message)


def _validate_structured_decisions(
    decisions: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
    *,
    state_validation: bool,
) -> None:
    """Validate only manifest-declared structural semantics.

    This deliberately does not inspect prose or infer tags from keywords.  The
    coordinator supplies enum-valued decisions and controlled trigger tags;
    this layer merely proves that those values agree with the manifest.
    """

    contracts = _structured_contracts(manifest)
    authority = contracts.get("creation_authority", {})
    if authority:
        decision_id = authority.get("decision_id")
        decision = decisions.get(decision_id)
        modes = authority.get("modes", {})
        if not _nonempty(decision_id) or not isinstance(modes, dict) or not modes:
            raise StateError("manifest_invalid", "creation authority contract is malformed")
        if decision is not None:
            value = _object_value(decision, decision_id)
            mode = value.get("mode")
            if mode not in modes:
                _decision_contract_error(
                    f"{decision_id}.mode must be one of: {', '.join(modes)}",
                    state_validation=state_validation,
                )
            if decision.get("source") != "player" or decision.get("status") != "locked":
                _decision_contract_error(
                    f"{decision_id} must be a locked Player decision",
                    state_validation=state_validation,
                )
        generative_ids = authority.get("world_generative_decision_ids", [])
        if not isinstance(generative_ids, list) or any(not _nonempty(item) for item in generative_ids):
            raise StateError("manifest_invalid", "world_generative_decision_ids must be stable ids")
        for generative_id in generative_ids:
            generative = decisions.get(generative_id)
            if generative is None or generative.get("source") not in {"derived", "defaulted"}:
                continue
            if decision is None:
                _decision_contract_error(
                    f"derived world decision {generative_id} requires {decision_id}",
                    state_validation=state_validation,
                )
            mode_rule = modes.get(_object_value(decision, decision_id).get("mode"), {})
            if not isinstance(mode_rule, dict) or not mode_rule.get("allow_derived_world_generation", False):
                _decision_contract_error(
                    f"creation authority mode does not permit derived world decision {generative_id}",
                    state_validation=state_validation,
                )
            if decision_id not in generative.get("depends_on", []):
                _decision_contract_error(
                    f"derived world decision {generative_id} must depend on {decision_id}",
                    state_validation=state_validation,
                )

    research = contracts.get("research", {})
    if research:
        status_id = research.get("status_decision_id")
        lock_id = research.get("lock_decision_id")
        statuses = research.get("statuses", [])
        permissions = research.get("permissions", [])
        status_decision = decisions.get(status_id)
        if status_decision is not None:
            value = _object_value(status_decision, status_id)
            if value.get("status") not in statuses or value.get("permission") not in permissions:
                _decision_contract_error(
                    f"{status_id} has an invalid research status or permission",
                    state_validation=state_validation,
                )
        lock_decision = decisions.get(lock_id)
        if lock_decision is not None:
            value = _object_value(lock_decision, lock_id)
            if type(value.get("risk_accepted")) is not bool or type(
                value.get("current_scale_lock_permitted")
            ) is not bool:
                _decision_contract_error(
                    f"{lock_id} must record boolean risk_accepted and current_scale_lock_permitted",
                    state_validation=state_validation,
                )
            if status_decision is None or status_id not in lock_decision.get("depends_on", []):
                _decision_contract_error(
                    f"{lock_id} must depend on {status_id}",
                    state_validation=state_validation,
                )

    topology = contracts.get("topology", {})
    if topology:
        intent_id = topology.get("intent_decision_id")
        activation_id = topology.get("activation_decision_id")
        topology_defs = manifest.get("topologies", {})
        intent = decisions.get(intent_id)
        if intent is not None:
            value = _object_value(intent, intent_id)
            selected = value.get("primary_topology")
            if selected not in topology_defs:
                _decision_contract_error(
                    f"{intent_id}.primary_topology is not manifest-declared",
                    state_validation=state_validation,
                )
            if selected == "mixed" and value.get("primary_branch") not in {
                item for item in topology_defs if item != "mixed"
            }:
                _decision_contract_error(
                    f"{intent_id} mixed topology requires a non-mixed primary_branch",
                    state_validation=state_validation,
                )
        activation = decisions.get(activation_id)
        if activation is not None:
            value = _object_value(activation, activation_id)
            if intent is None or intent_id not in activation.get("depends_on", []):
                _decision_contract_error(
                    f"{activation_id} must depend on {intent_id}",
                    state_validation=state_validation,
                )
            intent_value = _object_value(intent, intent_id)
            selected = intent_value.get("primary_topology")
            if value.get("primary_topology") != selected:
                _decision_contract_error(
                    f"{activation_id} topology must match Stage 1",
                    state_validation=state_validation,
                )
            if selected == "mixed" and value.get("primary_branch") != intent_value.get("primary_branch"):
                _decision_contract_error(
                    f"{activation_id} mixed primary branch must match Stage 1",
                    state_validation=state_validation,
                )
            expected_order = topology_defs.get(selected, {}).get("build_order")
            if value.get("build_order") != expected_order:
                _decision_contract_error(
                    f"{activation_id}.build_order must match the manifest topology order",
                    state_validation=state_validation,
                )
            trigger_topology = intent_value.get("primary_branch") if selected == "mixed" else selected
            required_tag = topology_defs.get(trigger_topology, {}).get("activation_trigger")
            if required_tag and required_tag not in activation.get("trigger_tags", []):
                _decision_contract_error(
                    f"{activation_id} must include topology trigger {required_tag}",
                    state_validation=state_validation,
                )


def _validate_extension_entry(extension_id: str, entry: Any, definition: dict[str, Any]) -> None:
    if not isinstance(entry, dict):
        raise StateError("state_invalid", f"extension {extension_id} must be an object")
    if entry.get("status") not in EXTENSION_STATUSES:
        raise StateError("state_invalid", f"extension {extension_id} has invalid status")
    if entry.get("depth") not in EXTENSION_DEPTHS:
        raise StateError("state_invalid", f"extension {extension_id} has invalid depth")
    if (entry.get("status") == "not_applicable") != (entry.get("depth") == "not_applicable"):
        raise StateError("state_invalid", f"extension {extension_id} status and depth disagree")
    expected_stages = _extension_stage_ids(definition)
    if entry.get("stage_ids") != expected_stages:
        raise StateError("state_invalid", f"extension {extension_id} stage_ids do not match the manifest")
    if not isinstance(entry.get("activated_by"), list):
        raise StateError("state_invalid", f"extension {extension_id}.activated_by must be a list")
    portions = entry.get("stages")
    if not isinstance(portions, dict) or list(portions) != expected_stages:
        raise StateError("state_invalid", f"extension {extension_id} stage portions do not match the manifest")
    for stage_id, portion in portions.items():
        if not isinstance(portion, dict) or portion.get("status") not in EXTENSION_STATUSES:
            raise StateError("state_invalid", f"extension {extension_id}/{stage_id} has invalid status")
        revision = portion.get("revision")
        if revision is not None and not _strict_int(revision, minimum=1):
            raise StateError("state_invalid", f"extension {extension_id}/{stage_id} revision is invalid")
        if not isinstance(portion.get("output_refs"), list):
            raise StateError("state_invalid", f"extension {extension_id}/{stage_id} output_refs must be a list")
        for ref in portion["output_refs"]:
            _relative_ref(ref, f"extension {extension_id}/{stage_id} output ref")
        _validate_digest(portion.get("output_digest"), f"extension {extension_id}/{stage_id} digest")
        if portion.get("status") in {"complete", "defaulted"}:
            if revision is None or not portion["output_refs"] or not portion["output_digest"]:
                raise StateError(
                    "state_invalid",
                    f"resolved extension {extension_id}/{stage_id} lacks revision-bound output evidence",
                )


def _validate_state(state: dict[str, Any], manifest: dict[str, Any], *, require_ready: bool = False) -> None:
    if state.get("schema_version") != STATE_SCHEMA_VERSION or state.get("flow_id") != FLOW_ID:
        raise StateError("state_invalid", "session_zero_state.json must use the Deep v8 state contract")
    revision = state.get("setup_revision")
    if not _strict_int(revision):
        raise StateError("state_invalid", "setup_revision must be a non-negative integer")
    stages = state.get("stages")
    if not isinstance(stages, dict) or list(stages) != list(STAGE_IDS):
        raise StateError("state_invalid", "state must contain the canonical nine stages in order")
    active_ids: list[str] = []
    actionable_ids: list[str] = []
    for stage_id, entry in stages.items():
        if not isinstance(entry, dict) or entry.get("status") not in STAGE_STATUSES:
            raise StateError("state_invalid", f"stage {stage_id} has invalid status")
        if entry.get("status") == "active":
            active_ids.append(stage_id)
        if entry.get("status") in {"active", "needs_review"}:
            actionable_ids.append(stage_id)
        completed_revision = entry.get("completed_revision")
        if completed_revision is not None and not _strict_int(completed_revision, minimum=1):
            raise StateError("state_invalid", f"stage {stage_id} completed_revision is invalid")
        if completed_revision is not None and completed_revision > revision:
            raise StateError("state_invalid", f"stage {stage_id} completed_revision exceeds setup_revision")
        if not isinstance(entry.get("output_refs"), list):
            raise StateError("state_invalid", f"stage {stage_id} output_refs must be a list")
        for ref in entry["output_refs"]:
            _relative_ref(ref, f"stage {stage_id} output ref")
        _validate_digest(entry.get("output_digest"), f"stage {stage_id} digest")
        if entry.get("status") == "complete":
            if completed_revision is None or not entry["output_refs"] or not entry["output_digest"]:
                raise StateError("state_invalid", f"complete stage {stage_id} lacks revision-bound output evidence")
        if entry.get("status") == "stale" and not _nonempty(entry.get("invalidation_reason")):
            raise StateError("state_invalid", f"stale stage {stage_id} lacks an invalidation reason")
    current_stage = state.get("current_stage")
    if current_stage not in STAGE_IDS:
        raise StateError("state_invalid", "current_stage must reference one of the nine stages")
    if len(active_ids) > 1:
        raise StateError("state_invalid", "only one stage may be active")
    if actionable_ids and current_stage != actionable_ids[0]:
        raise StateError("state_invalid", "current_stage must identify the earliest active or needs-review stage")
    if active_ids and active_ids[0] != actionable_ids[0]:
        raise StateError("state_invalid", "an active stage cannot appear after an earlier needs-review stage")
    if not actionable_ids:
        incomplete = [stage_id for stage_id in STAGE_IDS if stages[stage_id]["status"] != "complete"]
        expected_current = incomplete[0] if incomplete else STAGE_IDS[-1]
        if current_stage != expected_current:
            raise StateError("state_invalid", "current_stage must identify the earliest incomplete stage")

    decisions = state.get("decisions")
    if not isinstance(decisions, list):
        raise StateError("state_invalid", "decisions must be a list")
    seen: set[str] = set()
    controlled_tags = manifest.get("controlled_trigger_tags", {})
    for decision in decisions:
        if not isinstance(decision, dict):
            raise StateError("state_invalid", "every decision must be an object")
        decision_id = _safe_id(decision.get("decision_id"), "decision_id")
        if decision_id in seen:
            raise StateError("state_invalid", f"duplicate decision id: {decision_id}")
        seen.add(decision_id)
        if decision.get("stage_id") not in STAGE_IDS:
            raise StateError("state_invalid", f"decision {decision_id} has an unknown stage")
        if decision.get("status") not in DECISION_STATUSES or decision.get("source") not in DECISION_SOURCES:
            raise StateError("state_invalid", f"decision {decision_id} has invalid status or source")
        if not _strict_int(decision.get("created_revision"), minimum=1) or not _strict_int(
            decision.get("revision"), minimum=1
        ):
            raise StateError("state_invalid", f"decision {decision_id} has an invalid revision")
        if decision["revision"] > revision or decision["created_revision"] > decision["revision"]:
            raise StateError("state_invalid", f"decision {decision_id} revision exceeds setup_revision")
        if not isinstance(decision.get("depends_on"), list) or not isinstance(decision.get("trigger_tags"), list):
            raise StateError("state_invalid", f"decision {decision_id} dependency/tag fields must be lists")
        if any(not _nonempty(item) for item in decision["depends_on"]):
            raise StateError("state_invalid", f"decision {decision_id} has an invalid dependency id")
        if any(not _nonempty(tag) or tag not in controlled_tags for tag in decision["trigger_tags"]):
            raise StateError("state_invalid", f"decision {decision_id} contains an uncontrolled trigger tag")
        if decision_id in decision["depends_on"]:
            raise StateError("state_invalid", f"decision {decision_id} cannot depend on itself")
        known_definition = {
            item.get("id"): item
            for item in _stage_definitions(manifest)[decision["stage_id"]].get("decisions", [])
            if isinstance(item, dict)
        }.get(decision_id)
        if decision["status"] == "deferred" and known_definition and not known_definition.get("defer_allowed", False):
            raise StateError("state_invalid", f"decision {decision_id} is not deferrable")
    for decision in decisions:
        unknown = sorted(set(decision["depends_on"]) - seen)
        if unknown:
            raise StateError("state_invalid", f"decision {decision['decision_id']} has unknown dependencies: {', '.join(unknown)}")
        for dependency_id in decision["depends_on"]:
            dependency = next(item for item in decisions if item["decision_id"] == dependency_id)
            if STAGE_IDS.index(dependency["stage_id"]) > STAGE_IDS.index(decision["stage_id"]):
                raise StateError("state_invalid", f"decision {decision['decision_id']} depends on a later stage")

    graph = {decision["decision_id"]: decision["depends_on"] for decision in decisions}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(decision_id: str) -> None:
        if decision_id in visiting:
            raise StateError("state_invalid", "decision dependency graph contains a cycle")
        if decision_id in visited:
            return
        visiting.add(decision_id)
        for dependency_id in graph[decision_id]:
            visit(dependency_id)
        visiting.remove(decision_id)
        visited.add(decision_id)

    for decision_id in graph:
        visit(decision_id)

    _validate_structured_decisions(_decision_map(state), manifest, state_validation=True)
    decisions_by_id = _decision_map(state)
    for stage_id, entry in stages.items():
        if entry["output_refs"]:
            _validate_stage_output_refs(manifest, stage_id, entry["output_refs"], decisions_by_id)

    extensions = state.get("extensions")
    definitions = manifest.get("extensions", {})
    if not isinstance(extensions, dict) or list(extensions) != list(definitions):
        raise StateError("state_invalid", "state extensions do not match the Deep v8 manifest")
    for extension_id, definition in definitions.items():
        _validate_extension_entry(extension_id, extensions[extension_id], definition)
        for stage_id, portion in extensions[extension_id]["stages"].items():
            if portion["output_refs"]:
                _validate_extension_output_refs(manifest, extension_id, stage_id, portion["output_refs"])

    expected_activators: dict[str, list[dict[str, str]]] = {extension_id: [] for extension_id in definitions}
    rules = manifest.get("controlled_trigger_tags", {})
    for decision in decisions:
        if decision["status"] == "deferred":
            continue
        for tag in decision["trigger_tags"]:
            rule = rules[tag]
            targets = rule.get("activate", []) if isinstance(rule, dict) else rule
            depth = rule.get("depth", "baseline") if isinstance(rule, dict) else "baseline"
            for extension_id in targets:
                expected_activators[extension_id].append(
                    {"decision_id": decision["decision_id"], "trigger_tag": tag, "depth": depth}
                )
    for extension_id, extension in extensions.items():
        if extension["activated_by"] != expected_activators[extension_id]:
            raise StateError("state_invalid", f"extension {extension_id} activation evidence is stale")
        if not extension["activated_by"] and extension["status"] != "not_applicable":
            raise StateError("state_invalid", f"extension {extension_id} is active without a controlled trigger")
        if extension["activated_by"] and extension["status"] == "not_applicable":
            raise StateError("state_invalid", f"extension {extension_id} ignored a controlled trigger")
        expected_depth = "not_applicable"
        if extension["activated_by"]:
            expected_depth = (
                "deep"
                if any(item["depth"] == "deep" for item in extension["activated_by"])
                else "baseline"
            )
        if extension["depth"] != expected_depth:
            raise StateError("state_invalid", f"extension {extension_id} depth is stale")
        for portion in extension["stages"].values():
            if portion["revision"] is not None and portion["revision"] > revision:
                raise StateError("state_invalid", f"extension {extension_id} revision exceeds setup_revision")
            if portion["status"] == "defaulted":
                acceptance = _decision_map(state).get(portion.get("acceptance_decision_id"))
                if acceptance is None or acceptance["status"] not in {"locked", "defaulted"}:
                    raise StateError("state_invalid", f"defaulted extension {extension_id} lacks accepted evidence")
        aggregate = copy.deepcopy(extension)
        _recalculate_extension_status(aggregate)
        if aggregate["status"] != extension["status"]:
            raise StateError("state_invalid", f"extension {extension_id} aggregate status is stale")

    gates = state.get("gates")
    if not isinstance(gates, dict) or list(gates) != list(GATE_IDS):
        raise StateError("state_invalid", "state must contain the canonical gate chain")
    gate_prefix_open = False
    for gate_id, gate in gates.items():
        if not isinstance(gate, dict) or gate.get("status") not in GATE_STATUSES:
            raise StateError("state_invalid", f"gate {gate_id} has invalid status")
        gate_revision = gate.get("revision")
        if gate_revision is not None and not _strict_int(gate_revision, minimum=1):
            raise StateError("state_invalid", f"gate {gate_id} revision is invalid")
        if gate_revision is not None and gate_revision > revision:
            raise StateError("state_invalid", f"gate {gate_id} revision exceeds setup_revision")
        _validate_digest(gate.get("input_digest"), f"gate {gate_id} input_digest")
        _validate_digest(gate.get("output_digest"), f"gate {gate_id} output_digest")
        if gate.get("status") == "complete":
            if gate_prefix_open:
                raise StateError("state_invalid", f"complete gate {gate_id} appears after an incomplete gate")
            if (
                gate_revision is None
                or not _nonempty(gate.get("input_digest"))
                or not _nonempty(gate.get("output_digest"))
                or not _nonempty(gate.get("decided_by"))
            ):
                raise StateError("state_invalid", f"complete gate {gate_id} lacks revision-bound evidence")
            if gate_id == "ready_and_snapshotted" and not isinstance(gate.get("evidence"), dict):
                raise StateError("state_invalid", "final readiness gate lacks structured evidence")
            if gate_id == "ready_and_snapshotted":
                evidence = _validate_ready_evidence_shape(gate.get("evidence"), manifest, revision)
                if gate["output_digest"] != evidence["snapshot_digest"]:
                    raise StateError("state_invalid", "final gate output must equal its snapshot digest")
        else:
            gate_prefix_open = True
        if gate.get("status") == "stale" and not _nonempty(gate.get("invalidation_reason")):
            raise StateError("state_invalid", f"stale gate {gate_id} lacks an invalidation reason")

    for stage_id, stage in stages.items():
        if stage["status"] == "complete" and not _stage_prerequisites_complete(state, manifest, stage_id):
            raise StateError("state_invalid", f"complete stage {stage_id} has incomplete prerequisites")
    if (
        stages["09_first_act_preparation"]["status"] == "complete"
        and stages["09_first_act_preparation"]["output_digest"]
        != gates["preparation_approved"]["output_digest"]
    ):
        raise StateError("state_invalid", "First Act Preparation digest changed after Player approval")
    for gate_id, gate in gates.items():
        if gate["status"] == "complete":
            allowed, reason = _gate_prerequisites(state, gate_id)
            if not allowed:
                raise StateError("state_invalid", f"complete gate {gate_id} violates its prerequisites: {reason}")
            gate_index = GATE_IDS.index(gate_id)
            if gate_id == "research_scope_locked":
                if gate["input_digest"] != stages["02_research_canon_grounding"]["output_digest"]:
                    raise StateError("state_invalid", "research gate input does not match Stage 2 output")
            elif gate_index > 0:
                predecessor_id = "cross_read_passed" if gate_id in {
                    "integrated_review_accepted",
                    "preparation_approved",
                } else GATE_IDS[gate_index - 1]
                predecessor = gates[predecessor_id]
                if gate["input_digest"] != predecessor["output_digest"]:
                    raise StateError("state_invalid", f"gate {gate_id} input digest breaks the approval chain")
            if gate_id in {"cross_read_passed", "integrated_review_accepted", "preparation_approved"}:
                if gate["output_digest"] != gate["input_digest"]:
                    raise StateError(
                        "state_invalid",
                        f"gate {gate_id} must preserve the reviewed preparation digest",
                    )

    decisions_by_id = _decision_map(state)
    approval_dependencies = {
        "09_design_direction_review": "first_act_design_complete",
        "09_preparation_approval": "cross_read_passed",
    }
    for decision_id, gate_id in approval_dependencies.items():
        decision = decisions_by_id.get(decision_id)
        if decision is None:
            continue
        gate = gates[gate_id]
        if gate["status"] != "complete" or gate["revision"] is None or decision["created_revision"] <= gate["revision"]:
            raise StateError("state_invalid", f"decision {decision_id} was recorded before gate {gate_id}")

    registry = state.get("operation_registry")
    if not isinstance(registry, dict):
        raise StateError("state_invalid", "operation_registry must be an object")
    fatigue = state.get("fatigue")
    if not isinstance(fatigue, dict):
        raise StateError("state_invalid", "fatigue must be an object")
    if fatigue.get("decision_count") != len(decisions):
        raise StateError("state_invalid", "fatigue.decision_count must be derived from the decision ledger")
    for key in ("decisions_since_checkpoint", "last_checkpoint_revision", "last_checkpoint_decision_count"):
        if not _strict_int(fatigue.get(key)):
            raise StateError("state_invalid", f"fatigue.{key} must be a non-negative integer")
    if require_ready:
        if any(item["status"] != "complete" for item in stages.values()):
            raise StateError("not_ready", "all nine Deep v8 stages must be complete")
        if any(item["status"] != "complete" for item in gates.values()):
            raise StateError("not_ready", "all Deep v8 readiness gates must have passed")


def _top_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:[ \t]*(.*?)[ \t]*(?:#.*)?$", text)
    if match is None:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value


def _file_digest(root: Path, relative: str) -> str:
    return compute_output_digest(root, [relative])


def _read_ready_json(root: Path, relative: str, label: str) -> dict[str, Any]:
    safe = _relative_ref(relative, label)
    return _read_json(root / Path(*PurePosixPath(safe).parts), label)


def _validate_ready_evidence_shape(evidence: Any, manifest: dict[str, Any], revision: int) -> dict[str, Any]:
    if not isinstance(evidence, dict):
        raise StateError("readiness_evidence_invalid", "final gate evidence must be an object")
    required = {
        "snapshot_ref",
        "snapshot_digest",
        "selected_profile_ref",
        "selected_profile_digest",
        "unused_profile_ref",
        "unused_profile_digest",
        "aggregate_check_ref",
        "aggregate_check_digest",
    }
    if set(evidence) != required:
        missing = sorted(required - set(evidence))
        extra = sorted(set(evidence) - required)
        detail = ", ".join(([f"missing {item}" for item in missing] + [f"unexpected {item}" for item in extra]))
        raise StateError("readiness_evidence_invalid", f"final gate evidence fields are invalid: {detail}")
    contract = manifest.get("final_readiness_contract", {})
    if not isinstance(contract, dict):
        raise StateError("manifest_invalid", "final_readiness_contract must be an object")
    for key in ("snapshot_ref", "selected_profile_ref", "unused_profile_ref", "aggregate_check_ref"):
        evidence[key] = _relative_ref(evidence[key], key)
    for key in ("snapshot_digest", "selected_profile_digest", "unused_profile_digest", "aggregate_check_digest"):
        evidence[key] = _validate_digest(evidence[key], key, allow_empty=False)
    snapshot_owner = _campaign_owner_path(manifest, contract.get("snapshot_owner_ref", ""))
    if not _ref_matches_owner(evidence["snapshot_ref"], snapshot_owner):
        raise StateError("readiness_evidence_invalid", "snapshot_ref is outside the manifest snapshot owner")
    snapshot_patterns = contract.get("snapshot_manifest_patterns", [])
    if not isinstance(snapshot_patterns, list) or not any(
        PurePosixPath(evidence["snapshot_ref"]).match(_safe_manifest_pattern(pattern, "snapshot pattern"))
        for pattern in snapshot_patterns
    ):
        raise StateError("readiness_evidence_invalid", "snapshot_ref is not a session-zero-start manifest")
    selected = str(contract.get("selected_profile_ref", "")).removeprefix("campaign/")
    unused = str(contract.get("unused_profile_ref", "")).removeprefix("campaign/")
    if evidence["selected_profile_ref"] != selected or evidence["unused_profile_ref"] != unused:
        raise StateError("readiness_evidence_invalid", "profile evidence refs do not match the manifest")
    patterns = contract.get("aggregate_report_patterns", [])
    if not isinstance(patterns, list) or not any(
        PurePosixPath(evidence["aggregate_check_ref"]).match(_safe_manifest_pattern(pattern, "aggregate pattern"))
        for pattern in patterns
    ):
        raise StateError("readiness_evidence_invalid", "aggregate_check_ref is not manifest-authorized")
    if not _strict_int(revision, minimum=1):
        raise StateError("readiness_evidence_invalid", "final readiness requires a positive setup revision")
    return evidence


def _validate_ready_evidence_files(
    root: Path,
    state: dict[str, Any],
    manifest: dict[str, Any],
    evidence: Any,
    *,
    before_transition: bool,
) -> dict[str, Any]:
    checked = _validate_ready_evidence_shape(copy.deepcopy(evidence), manifest, state["setup_revision"])
    digest_pairs = (
        ("snapshot_ref", "snapshot_digest"),
        ("selected_profile_ref", "selected_profile_digest"),
        ("unused_profile_ref", "unused_profile_digest"),
        ("aggregate_check_ref", "aggregate_check_digest"),
    )
    for ref_key, digest_key in digest_pairs:
        if _file_digest(root, checked[ref_key]) != checked[digest_key]:
            raise StateError("readiness_evidence_stale", f"{ref_key} no longer matches {digest_key}")

    setup_text = (root / SETUP_FILE).read_text(encoding="utf-8")
    expected_status = "in_progress" if before_transition else "complete"
    expected_ready = "false" if before_transition else "true"
    if _top_scalar(setup_text, "status") != expected_status or _top_scalar(setup_text, "ready_for_play") != expected_ready:
        raise StateError(
            "readiness_evidence_invalid",
            f"final readiness setup must be {expected_status} with ready_for_play {expected_ready}",
        )

    selected_text = (root / checked["selected_profile_ref"]).read_text(encoding="utf-8")
    unused_text = (root / checked["unused_profile_ref"]).read_text(encoding="utf-8")
    if _top_scalar(selected_text, "profile_status") != "locked":
        raise StateError("readiness_evidence_invalid", "selected RPG profile must be locked")
    if _top_scalar(unused_text, "profile_status") != "inactive":
        raise StateError("readiness_evidence_invalid", "unused Companion profile must be inactive")
    if _top_scalar(selected_text, "source_setup_revision") != str(state["setup_revision"]):
        raise StateError("readiness_evidence_invalid", "locked profile revision must match setup_revision")

    contract = manifest["final_readiness_contract"]
    snapshot = _read_ready_json(root, checked["snapshot_ref"], "session-zero start snapshot manifest")
    files = snapshot.get("files")
    records = snapshot.get("file_records")
    if (
        snapshot.get("manifest_version") != 2
        or snapshot.get("label") != contract.get("snapshot_label")
        or snapshot.get("setup_revision") != state["setup_revision"]
        or snapshot.get("ready_for_play") is not False
        or snapshot.get("setup_status") != "in_progress"
        or snapshot.get("experience_mode") != "rpg"
        or not isinstance(files, list)
        or not isinstance(records, list)
    ):
        raise StateError("readiness_evidence_invalid", "snapshot manifest identity is invalid")
    required_snapshot_files = {
        SETUP_FILE,
        STATE_FILE,
        SUMMARY_FILE,
        checked["selected_profile_ref"],
        checked["unused_profile_ref"],
    }
    if not required_snapshot_files <= set(item for item in files if isinstance(item, str)):
        raise StateError("readiness_evidence_invalid", "snapshot is not a full Session 0 campaign snapshot")
    record_map: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or not _nonempty(record.get("path")):
            raise StateError("readiness_evidence_invalid", "snapshot file_records are malformed")
        record_map[record["path"]] = record
    if set(record_map) != set(files):
        raise StateError("readiness_evidence_invalid", "snapshot files and file_records disagree")
    snapshots_dir = root / "snapshots"
    transaction_dir = root / ".repog-transactions"
    live_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and path != root / ".session-zero-state.lock"
        and path != snapshots_dir
        and snapshots_dir not in path.parents
        and path != transaction_dir
        and transaction_dir not in path.parents
    }
    if live_files != set(files):
        raise StateError(
            "readiness_evidence_stale",
            "campaign file set changed after the Session 0 start snapshot",
        )
    snapshot_dir = (root / Path(*PurePosixPath(checked["snapshot_ref"]).parts)).parent
    transition_owned = {SETUP_FILE, STATE_FILE, SUMMARY_FILE} if not before_transition else set()
    for relative, record in record_map.items():
        copied = snapshot_dir / Path(*PurePosixPath(relative).parts)
        if not copied.is_file():
            raise StateError("readiness_evidence_invalid", f"snapshot copy is missing: {relative}")
        payload = copied.read_bytes()
        if record.get("size") != len(payload) or record.get("sha256") != hashlib.sha256(payload).hexdigest():
            raise StateError("readiness_evidence_invalid", f"snapshot copy digest is invalid: {relative}")
        if relative not in transition_owned:
            current = root / Path(*PurePosixPath(relative).parts)
            current_payload = current.read_bytes()
            if (
                record.get("size") != len(current_payload)
                or record.get("sha256") != hashlib.sha256(current_payload).hexdigest()
            ):
                raise StateError(
                    "readiness_evidence_stale",
                    f"campaign file changed after the Session 0 start snapshot: {relative}",
                )
    expected_content_digest = "sha256:" + hashlib.sha256(
        json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if snapshot.get("content_digest") != expected_content_digest:
        raise StateError("readiness_evidence_invalid", "snapshot aggregate content digest is invalid")
    copied_state = _read_json(snapshot_dir / STATE_FILE, "snapshotted Deep v8 state")
    copied_prep = copied_state.get("gates", {}).get("preparation_approved", {})
    if copied_prep.get("output_digest") != state["gates"]["preparation_approved"]["output_digest"]:
        raise StateError("readiness_evidence_invalid", "snapshot does not contain the approved preparation")
    selected_payload = (root / checked["selected_profile_ref"]).read_bytes()
    if record_map[checked["selected_profile_ref"]].get("sha256") != hashlib.sha256(selected_payload).hexdigest():
        raise StateError("readiness_evidence_invalid", "snapshot profile differs from the locked profile")
    aggregate = _read_ready_json(root, checked["aggregate_check_ref"], "aggregate readiness report")
    if (
        aggregate.get("kind") != contract.get("aggregate_report_kind")
        or aggregate.get("flow_id") != FLOW_ID
        or aggregate.get("setup_revision") != state["setup_revision"]
        or aggregate.get("status") != "passed"
        or aggregate.get("error_count") != 0
        or aggregate.get("snapshot_ref") != checked["snapshot_ref"]
        or aggregate.get("snapshot_digest") != checked["snapshot_digest"]
        or aggregate.get("profile_digest") != checked["selected_profile_digest"]
    ):
        raise StateError("readiness_evidence_invalid", "aggregate report is not a zero-error candidate-ready attestation")
    return checked


def _replace_top_scalar(text: str, key: str, value: Any) -> str:
    pattern = re.compile(rf"(?m)^({re.escape(key)}:[ \t]*)([^#\r\n]*?)([ \t]*(?:#.*)?)$")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise StateError("setup_invalid", f"setup_profile.yaml must contain exactly one top-level {key}")
    return pattern.sub(lambda match: f"{match.group(1)}{value}{match.group(3)}", text, count=1)


def _validate_setup(text: str, state: dict[str, Any]) -> None:
    required = {
        "schema_version": "8",
        "experience_mode": "rpg",
        "session_zero_mode": "deep",
        "deep_flow_id": FLOW_ID,
        "session_zero_state_path": STATE_FILE,
    }
    for key, expected in required.items():
        if _top_scalar(text, key) != expected:
            raise StateError("setup_invalid", f"setup_profile.yaml {key} must be {expected}")
    mirrors = {
        "setup_revision": str(state["setup_revision"]),
        "questions_completed": str(len(state["decisions"])),
        "last_checkpoint": str(state["fatigue"]["last_checkpoint_decision_count"]),
    }
    for key, expected in mirrors.items():
        if _top_scalar(text, key) != expected:
            raise StateError("mirror_stale", f"setup_profile.yaml {key} must equal {expected}")
    final_ready = state["gates"]["ready_and_snapshotted"]["status"] == "complete"
    if final_ready:
        if _top_scalar(text, "status") != "complete" or _top_scalar(text, "ready_for_play") != "true":
            raise StateError("mirror_stale", "final Deep v8 gate requires complete/ready setup state")


def _summary_markdown(state: dict[str, Any]) -> str:
    lines = [
        SUMMARY_HEADING,
        "",
        f"- Flow: `{FLOW_ID}`",
        f"- Setup revision: {state['setup_revision']}",
        f"- Current stage: {STAGE_TITLES[state['current_stage']]} (`{state['current_stage']}`)",
        f"- Decisions recorded: {len(state['decisions'])}",
        "",
        "### Deep v8 Stages",
        "",
        "| Stage | Status | Decisions |",
        "| --- | --- | ---: |",
    ]
    for stage_id in STAGE_IDS:
        count = sum(decision["stage_id"] == stage_id for decision in state["decisions"])
        lines.append(f"| {STAGE_TITLES[stage_id]} | {state['stages'][stage_id]['status']} | {count} |")
    lines.extend(["", "### Deep v8 Extensions", ""])
    for extension_id, extension in state["extensions"].items():
        lines.append(f"- `{extension_id}`: {extension['status']} / {extension['depth']}")
    lines.extend(["", "### Defaults And Deferrals", ""])
    visible = [decision for decision in state["decisions"] if decision["status"] in {"defaulted", "deferred"}]
    if visible:
        for decision in visible:
            lines.append(f"- `{decision['decision_id']}`: {decision['status']}")
    else:
        lines.append("- None")
    lines.extend(["", "### Deep v8 Gates", ""])
    for gate_id in GATE_IDS:
        lines.append(f"- `{gate_id}`: {state['gates'][gate_id]['status']}")
    return "\n".join(lines) + "\n"


def _summary_matches(existing_text: str, state: dict[str, Any]) -> bool:
    pattern = re.compile(rf"(?ms)^{re.escape(SUMMARY_HEADING)}[ \t]*(?:\r?\n|$).*?(?=^##[ \t]+|\Z)")
    matches = list(pattern.finditer(existing_text))
    if len(matches) != 1:
        return False
    actual = matches[0].group(0).replace("\r\n", "\n").rstrip() + "\n"
    expected = _summary_markdown(state).rstrip() + "\n"
    return actual == expected


def project_session_zero_text(existing_text: str, state: dict[str, Any]) -> str:
    """Replace only the managed Deep v8 summary section."""

    if not isinstance(existing_text, str):
        raise StateError("summary_invalid", "session_zero.md must be UTF-8 text")
    newline = "\r\n" if "\r\n" in existing_text else "\n"
    rendered = _summary_markdown(state).replace("\n", newline).rstrip("\r\n")
    pattern = re.compile(rf"(?ms)^{re.escape(SUMMARY_HEADING)}[ \t]*(?:\r?\n|$).*?(?=^##[ \t]+|\Z)")
    matches = list(pattern.finditer(existing_text))
    if len(matches) > 1:
        raise StateError("summary_invalid", f"{SUMMARY_FILE} contains duplicate managed Deep v8 sections")
    if not matches:
        prefix = existing_text.rstrip("\r\n")
        return f"{prefix}{newline * 2 if prefix else ''}{rendered}{newline}"
    match = matches[0]
    suffix = existing_text[match.end() :].lstrip("\r\n")
    separator = newline * 2 if suffix else newline
    return existing_text[: match.start()] + rendered + separator + suffix


def _validated_campaign_state(campaign: Path, *, require_ready: bool = False) -> dict[str, Any]:
    root = _campaign_root(campaign)
    manifest = load_manifest(root, require_full=require_ready)
    state = _read_json(root / STATE_FILE, STATE_FILE)
    _validate_state(state, manifest, require_ready=require_ready)
    try:
        setup_text = (root / SETUP_FILE).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError) as exc:
        raise StateError("file_missing", f"cannot read {SETUP_FILE}: {exc}") from exc
    _validate_setup(setup_text, state)
    ready_gate = state["gates"]["ready_and_snapshotted"]
    if ready_gate["status"] == "complete":
        _validate_ready_evidence_files(
            root,
            state,
            manifest,
            ready_gate.get("evidence"),
            before_transition=False,
        )
    try:
        summary_text = (root / SUMMARY_FILE).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError) as exc:
        raise StateError("file_missing", f"cannot read {SUMMARY_FILE}: {exc}") from exc
    if not _summary_matches(summary_text, state):
        raise StateError("summary_stale", f"{SUMMARY_FILE} Deep v8 managed section does not match canonical state")
    for stage_id, stage in state["stages"].items():
        if stage["status"] == "complete":
            actual_digest = compute_output_digest(root, stage["output_refs"])
            # Stages 1-8 record completion evidence, not immutable snapshots.
            # Their owner files are deliberately enriched by later stages, so
            # re-comparing historical aggregate digests would reject valid
            # dependency-ordered materialization.  The final reviewed Stage 9
            # package is different: it is frozen by the Player approval and is
            # therefore the only stage whose current bytes must still match.
            if stage_id == "09_first_act_preparation" and actual_digest != stage["output_digest"]:
                raise StateError("output_drift", f"stage {stage_id} reviewed preparation digest is stale")
    for extension_id, extension in state["extensions"].items():
        for stage_id, portion in extension["stages"].items():
            if portion["status"] in {"complete", "defaulted"}:
                # Extension owner files may likewise be enriched downstream.
                # Computing the digest still validates that every bounded
                # campaign-relative reference exists and remains readable.
                compute_output_digest(root, portion["output_refs"])
    return copy.deepcopy(state)


def validate_campaign_state(campaign: Path, *, require_ready: bool = False) -> dict[str, Any]:
    """Return a stable validator report for ``check_state.py`` and callers.

    Mutating APIs continue to raise :class:`StateError`; this read-only public
    surface deliberately returns findings so an aggregate validator can merge
    them without coupling itself to exception control flow.
    """

    try:
        state = _validated_campaign_state(campaign, require_ready=require_ready)
    except StateError as exc:
        return {
            "ok": False,
            "findings": [
                {
                    "severity": "error",
                    "code": exc.category,
                    "message": str(exc),
                }
            ],
            "state": None,
        }
    return {"ok": True, "findings": [], "state": state}


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


def _atomic_bundle(
    state_path: Path,
    state: dict[str, Any],
    setup_path: Path,
    setup_text: str,
    summary_path: Path,
    summary_text: str,
) -> None:
    snapshots = {
        state_path: state_path.read_bytes(),
        setup_path: setup_path.read_bytes(),
        summary_path: summary_path.read_bytes(),
    }
    written: list[Path] = []
    try:
        _atomic_bytes(setup_path, setup_text.encode("utf-8"))
        written.append(setup_path)
        _atomic_bytes(summary_path, summary_text.encode("utf-8"))
        written.append(summary_path)
        _atomic_bytes(state_path, _json_bytes(state))
        written.append(state_path)
    except Exception as exc:
        rollback_errors: list[str] = []
        for path in reversed(written):
            try:
                _atomic_bytes(path, snapshots[path])
            except Exception as rollback_exc:  # pragma: no cover - exceptional filesystem failure
                rollback_errors.append(f"{path}: {rollback_exc}")
        detail = f"; rollback errors: {'; '.join(rollback_errors)}" if rollback_errors else ""
        raise StateError("commit_failed", f"state commit failed and was rolled back: {exc}{detail}") from exc


@contextmanager
def _mutation_lock(root: Path) -> Iterator[None]:
    path = root / ".session-zero-state.lock"
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise StateError("state_busy", "another Deep Session 0 state mutation is in progress") from exc
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.close(descriptor)
        yield
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
        path.unlink(missing_ok=True)


def _load_for_mutation(root: Path) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    manifest = load_manifest(root, require_full=True)
    state = _read_json(root / STATE_FILE, STATE_FILE)
    _validate_state(state, manifest)
    try:
        setup_text = (root / SETUP_FILE).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError) as exc:
        raise StateError("file_missing", f"cannot read {SETUP_FILE}: {exc}") from exc
    _validate_setup(setup_text, state)
    try:
        summary_text = (root / SUMMARY_FILE).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError) as exc:
        raise StateError("file_missing", f"cannot read {SUMMARY_FILE}: {exc}") from exc
    if not _summary_matches(summary_text, state):
        raise StateError("summary_stale", f"{SUMMARY_FILE} Deep v8 managed section does not match canonical state")
    return manifest, state, setup_text, summary_text


def _payload_hash(command: str, payload: dict[str, Any]) -> str:
    return _canonical_hash({"command": command, "payload": payload})


def _operation_result(state: dict[str, Any], operation_id: str, payload_hash: str) -> dict[str, Any] | None:
    previous = state["operation_registry"].get(operation_id)
    if previous is None:
        return None
    if previous.get("payload_hash") != payload_hash:
        raise StateError("operation_conflict", f"operation_id {operation_id} was already used with different input")
    return {
        "ok": True,
        "idempotent": True,
        "operation_id": operation_id,
        "operation_revision": previous["resulting_revision"],
        "setup_revision": state["setup_revision"],
        "current_stage": state["current_stage"],
        "decision_count": len(state["decisions"]),
    }


def _prepare_operation(state: dict[str, Any], payload: dict[str, Any], command: str) -> tuple[str, str, int]:
    operation_id = _safe_id(payload.get("operation_id"), "operation_id")
    expected = payload.get("expected_revision")
    if not _strict_int(expected):
        raise StateError("input_invalid", "expected_revision must be a non-negative integer")
    digest = _payload_hash(command, payload)
    return operation_id, digest, expected


def _sync_fatigue(state: dict[str, Any]) -> None:
    fatigue = state["fatigue"]
    fatigue["decision_count"] = len(state["decisions"])
    checkpoint = fatigue["last_checkpoint_revision"]
    fatigue["decisions_since_checkpoint"] = sum(
        1 for decision in state["decisions"] if decision["created_revision"] > checkpoint
    )


def _setup_candidate(text: str, state: dict[str, Any]) -> str:
    text = _replace_top_scalar(text, "setup_revision", state["setup_revision"])
    text = _replace_top_scalar(text, "questions_completed", len(state["decisions"]))
    text = _replace_top_scalar(text, "last_checkpoint", state["fatigue"]["last_checkpoint_decision_count"])
    final_ready = state["gates"]["ready_and_snapshotted"]["status"] == "complete"
    text = _replace_top_scalar(text, "status", "complete" if final_ready else "in_progress")
    text = _replace_top_scalar(text, "ready_for_play", "true" if final_ready else "false")
    return text


def _commit_operation(
    root: Path,
    state: dict[str, Any],
    setup_text: str,
    summary_text: str,
    *,
    operation_id: str,
    payload_hash: str,
    command: str,
) -> dict[str, Any]:
    state["operation_registry"][operation_id] = {
        "command": command,
        "payload_hash": payload_hash,
        "resulting_revision": state["setup_revision"],
    }
    state["last_operation"] = {
        "operation_id": operation_id,
        "command": command,
        "revision": state["setup_revision"],
    }
    _sync_fatigue(state)
    manifest = load_manifest(root)
    _validate_state(state, manifest)
    new_setup = _setup_candidate(setup_text, state)
    _validate_setup(new_setup, state)
    new_summary = project_session_zero_text(summary_text, state)
    if not _summary_matches(new_summary, state):  # pragma: no cover - internal invariant
        raise StateError("summary_invalid", "generated Deep v8 summary did not round-trip")
    _atomic_bundle(
        root / STATE_FILE,
        state,
        root / SETUP_FILE,
        new_setup,
        root / SUMMARY_FILE,
        new_summary,
    )
    return {
        "ok": True,
        "idempotent": False,
        "operation_id": operation_id,
        "setup_revision": state["setup_revision"],
        "current_stage": state["current_stage"],
        "decision_count": len(state["decisions"]),
    }


def _gate_invalidation_start(stage_id: str, decision_id: str = "") -> int:
    if stage_id in STAGE_IDS[:2]:
        return 0
    if stage_id in STAGE_IDS[2:8]:
        return 1
    if decision_id == "09_design_direction_review":
        return 3
    if decision_id == "09_preparation_approval":
        return 6
    return 2


def _invalidate_gates(state: dict[str, Any], start: int, reason: str) -> None:
    for gate_id in GATE_IDS[start:]:
        gate = state["gates"][gate_id]
        if gate["status"] == "complete":
            gate["status"] = "stale"
            gate["invalidation_reason"] = reason


def _recalculate_extension_status(entry: dict[str, Any]) -> None:
    statuses = [portion["status"] for portion in entry["stages"].values()]
    if any(status == "active" for status in statuses):
        entry["status"] = "active"
    elif all(status == "not_applicable" for status in statuses):
        entry["status"] = "not_applicable"
    elif any(status == "complete" for status in statuses):
        entry["status"] = "complete"
    else:
        entry["status"] = "defaulted"


def _activate_extensions(state: dict[str, Any], manifest: dict[str, Any], reason: str) -> None:
    activators: dict[str, list[dict[str, str]]] = {extension_id: [] for extension_id in state["extensions"]}
    rules = manifest.get("controlled_trigger_tags", {})
    for decision in state["decisions"]:
        if decision["status"] == "deferred":
            continue
        for tag in decision["trigger_tags"]:
            rule = rules[tag]
            targets = rule.get("activate", []) if isinstance(rule, dict) else rule
            depth = rule.get("depth", "baseline") if isinstance(rule, dict) else "baseline"
            for extension_id in targets:
                activators[extension_id].append(
                    {"decision_id": decision["decision_id"], "trigger_tag": tag, "depth": depth}
                )
    for extension_id, entry in state["extensions"].items():
        old = entry["activated_by"]
        old_depth = entry.get("depth", "not_applicable")
        new = activators[extension_id]
        new_depth = (
            "not_applicable"
            if not new
            else ("deep" if any(item["depth"] == "deep" for item in new) else "baseline")
        )
        entry["activated_by"] = new
        entry["depth"] = new_depth
        if not new:
            for portion in entry["stages"].values():
                portion.update(
                    status="not_applicable",
                    revision=None,
                    output_refs=[],
                    output_digest="",
                    acceptance_decision_id="",
                    invalidation_reason="",
                )
            _recalculate_extension_status(entry)
            continue
        if new != old or new_depth != old_depth:
            for stage_id, portion in entry["stages"].items():
                portion["status"] = "active"
                portion["invalidation_reason"] = reason
                if state["stages"][stage_id]["status"] == "complete":
                    state["stages"][stage_id]["status"] = "stale"
                    state["stages"][stage_id]["invalidation_reason"] = reason
            _recalculate_extension_status(entry)


def _invalidate_from_stage(state: dict[str, Any], stage_id: str, reason: str) -> None:
    start = STAGE_IDS.index(stage_id)
    for index, candidate_id in enumerate(STAGE_IDS[start:], start=start):
        stage = state["stages"][candidate_id]
        if stage["status"] == "complete":
            stage["status"] = "stale"
            stage["invalidation_reason"] = reason
        elif index > start and stage["status"] in {"active", "needs_review"}:
            stage["status"] = "stale"
            stage["invalidation_reason"] = reason
        elif index == start and stage["status"] == "not_started":
            stage["status"] = "needs_review"
            stage["invalidation_reason"] = reason
    source = state["stages"][stage_id]
    if source["status"] == "stale":
        source["status"] = "needs_review"
    state["current_stage"] = stage_id


def _stage_prerequisites_complete(state: dict[str, Any], manifest: dict[str, Any], stage_id: str) -> bool:
    definition = _stage_definitions(manifest)[stage_id]
    for prerequisite in definition.get("prerequisites", []):
        if prerequisite in state["stages"] and state["stages"][prerequisite]["status"] != "complete":
            return False
        if prerequisite in state["gates"] and state["gates"][prerequisite]["status"] != "complete":
            return False
    return True


def _advance_current_stage(state: dict[str, Any], manifest: dict[str, Any]) -> None:
    for stage_id in STAGE_IDS:
        stage = state["stages"][stage_id]
        if stage["status"] in {"active", "needs_review", "stale"}:
            state["current_stage"] = stage_id
            if stage["status"] == "stale" and _stage_prerequisites_complete(state, manifest, stage_id):
                stage["status"] = "needs_review"
            return
        if stage["status"] == "not_started":
            state["current_stage"] = stage_id
            if _stage_prerequisites_complete(state, manifest, stage_id):
                stage["status"] = "active"
            return
    state["current_stage"] = STAGE_IDS[-1]


def status(campaign: Path) -> dict[str, Any]:
    state = _validated_campaign_state(campaign)
    return {
        "ok": True,
        "operation": "status",
        "flow_id": state["flow_id"],
        "setup_revision": state["setup_revision"],
        "current_stage": state["current_stage"],
        "current_stage_title": STAGE_TITLES[state["current_stage"]],
        "decision_count": len(state["decisions"]),
        "fatigue": state["fatigue"],
        "stages": state["stages"],
        "active_extensions": [
            extension_id for extension_id, entry in state["extensions"].items() if entry["status"] == "active"
        ],
        "gates": {gate_id: gate["status"] for gate_id, gate in state["gates"].items()},
    }


def record_decision(campaign: Path, payload: dict[str, Any]) -> dict[str, Any]:
    root = _campaign_root(campaign)
    with _mutation_lock(root):
        manifest, state, setup_text, summary_text = _load_for_mutation(root)
        operation_id, payload_hash, expected = _prepare_operation(state, payload, "record-decision")
        replay = _operation_result(state, operation_id, payload_hash)
        if replay is not None:
            return {**replay, "operation": "record-decision"}
        if expected != state["setup_revision"]:
            raise StateError("stale_revision", f"expected revision {expected}, current revision is {state['setup_revision']}")

        decision_id = _safe_id(payload.get("decision_id"), "decision_id")
        stage_id = payload.get("stage_id")
        if stage_id not in STAGE_IDS:
            raise StateError("input_invalid", "stage_id must reference a Deep v8 stage")
        status_value = payload.get("status")
        source = payload.get("source")
        if status_value not in DECISION_STATUSES or source not in DECISION_SOURCES:
            raise StateError("input_invalid", "decision status or source is invalid")
        definitions = _stage_definitions(manifest)[stage_id]
        known = {item.get("id"): item for item in definitions.get("decisions", []) if isinstance(item, dict)}
        if status_value == "deferred" and decision_id in known and not known[decision_id].get("defer_allowed", False):
            raise StateError("decision_blocked", f"decision {decision_id} cannot be deferred")
        depends_on = payload.get("depends_on", [])
        trigger_tags = payload.get("trigger_tags", [])
        if not isinstance(depends_on, list) or any(not _nonempty(item) for item in depends_on):
            raise StateError("input_invalid", "depends_on must be a list of decision ids")
        if not isinstance(trigger_tags, list) or any(
            not _nonempty(tag) or tag not in manifest.get("controlled_trigger_tags", {}) for tag in trigger_tags
        ):
            raise StateError("input_invalid", "trigger_tags contains an uncontrolled tag")
        if len(depends_on) != len(set(depends_on)) or len(trigger_tags) != len(set(trigger_tags)):
            raise StateError("input_invalid", "decision dependencies and trigger tags must not contain duplicates")
        decisions = _decision_map(state)
        missing = sorted(set(depends_on) - set(decisions))
        if missing:
            raise StateError("dependency_missing", f"decision dependencies are missing: {', '.join(missing)}")
        if any(decisions[item]["status"] == "deferred" for item in depends_on):
            raise StateError("dependency_deferred", "a decision cannot depend on a deferred decision")
        existing = decisions.get(decision_id)
        if existing is None and stage_id != state["current_stage"]:
            raise StateError("stage_order", "new decisions may only be recorded in the current stage")
        if existing is None and state["stages"][stage_id]["status"] not in {"active", "needs_review"}:
            raise StateError("stage_order", "the target stage is not open for decisions")
        if existing is not None and existing["stage_id"] != stage_id:
            raise StateError("input_invalid", "an existing decision cannot move between stages")
        approval_gate = {
            "09_design_direction_review": "first_act_design_complete",
            "09_preparation_approval": "cross_read_passed",
        }.get(decision_id)
        if approval_gate and state["gates"][approval_gate]["status"] != "complete":
            raise StateError("gate_blocked", f"decision {decision_id} requires gate {approval_gate}")

        next_revision = state["setup_revision"] + 1
        entry = {
            "decision_id": decision_id,
            "stage_id": stage_id,
            "status": status_value,
            "source": source,
            "value": copy.deepcopy(payload.get("value")),
            "depends_on": list(depends_on),
            "trigger_tags": list(trigger_tags),
            "created_revision": existing["created_revision"] if existing else next_revision,
            "revision": next_revision,
        }
        candidate_decisions = dict(decisions)
        candidate_decisions[decision_id] = entry
        _validate_structured_decisions(candidate_decisions, manifest, state_validation=False)
        if existing is not None:
            comparable = {key: value for key, value in existing.items() if key not in {"created_revision", "revision"}}
            new_comparable = {key: value for key, value in entry.items() if key not in {"created_revision", "revision"}}
            if comparable == new_comparable:
                raise StateError("no_change", f"decision {decision_id} already has that value")
            state["decisions"][state["decisions"].index(existing)] = entry
            reason = f"decision {decision_id} changed at revision {next_revision}"
            _invalidate_from_stage(state, stage_id, reason)
            _invalidate_gates(state, _gate_invalidation_start(stage_id, decision_id), reason)
        else:
            state["decisions"].append(entry)
        state["setup_revision"] = next_revision
        _activate_extensions(state, manifest, f"controlled trigger set changed at revision {next_revision}")
        _advance_current_stage(state, manifest)
        result = _commit_operation(
            root,
            state,
            setup_text,
            summary_text,
            operation_id=operation_id,
            payload_hash=payload_hash,
            command="record-decision",
        )
        return {**result, "operation": "record-decision", "decision_id": decision_id}


def _required_stage_decisions(state: dict[str, Any], manifest: dict[str, Any], stage_id: str) -> None:
    definitions = _stage_definitions(manifest)[stage_id].get("decisions", [])
    recorded = _decision_map(state)
    missing = [item["id"] for item in definitions if item.get("id") not in recorded]
    if missing:
        raise StateError("stage_incomplete", f"stage {stage_id} is missing decisions: {', '.join(missing)}")
    wrong_stage = [item["id"] for item in definitions if recorded[item["id"]]["stage_id"] != stage_id]
    if wrong_stage:
        raise StateError("stage_incomplete", f"stage decisions have the wrong owner stage: {', '.join(wrong_stage)}")


def _apply_extension_evidence(
    root: Path, state: dict[str, Any], stage_id: str, evidence: Any, next_revision: int
) -> None:
    if evidence is None:
        evidence = {}
    if not isinstance(evidence, dict):
        raise StateError("input_invalid", "extensions must be an object")
    relevant = {
        extension_id: entry
        for extension_id, entry in state["extensions"].items()
        if stage_id in entry["stage_ids"]
    }
    unknown = sorted(set(evidence) - set(relevant))
    if unknown:
        raise StateError("input_invalid", f"extension evidence is not owned by this stage: {', '.join(unknown)}")
    decisions = _decision_map(state)
    for extension_id, entry in relevant.items():
        portion = entry["stages"][stage_id]
        if portion["status"] == "not_applicable":
            if extension_id in evidence:
                raise StateError("input_invalid", f"extension {extension_id} was not activated")
            continue
        update = evidence.get(extension_id)
        if not isinstance(update, dict):
            raise StateError("extension_incomplete", f"active extension {extension_id} needs completion evidence")
        target_status = update.get("status")
        if target_status not in {"complete", "defaulted"}:
            raise StateError("input_invalid", f"extension {extension_id} must become complete or defaulted")
        output_refs = _refs(update.get("output_refs", []), f"extension {extension_id} output_refs")
        if update.get("depth") != entry["depth"]:
            raise StateError(
                "extension_incomplete",
                f"extension {extension_id} evidence depth must equal its controlled {entry['depth']} depth",
            )
        output_digest = _validate_digest(update.get("output_digest"), f"extension {extension_id} output_digest", allow_empty=False)
        if not output_refs:
            raise StateError("extension_incomplete", f"extension {extension_id} requires at least one materialized output")
        _validate_extension_output_refs(load_manifest(root), extension_id, stage_id, output_refs)
        computed_digest = compute_output_digest(root, output_refs)
        if output_digest != computed_digest:
            raise StateError("output_digest_mismatch", f"extension {extension_id} digest does not match its files")
        acceptance = str(update.get("acceptance_decision_id", "")).strip()
        if target_status == "defaulted":
            if acceptance not in decisions or decisions[acceptance]["status"] not in {"locked", "defaulted"}:
                raise StateError("extension_incomplete", f"defaulted extension {extension_id} needs an accepted decision")
            if decisions[acceptance]["source"] not in {"player", "defaulted"}:
                raise StateError("extension_incomplete", f"defaulted extension {extension_id} needs explicit Player acceptance")
        portion.update(
            status=target_status,
            revision=next_revision,
            output_refs=output_refs,
            output_digest=output_digest,
            acceptance_decision_id=acceptance,
            invalidation_reason="",
        )
        _recalculate_extension_status(entry)


def complete_stage(campaign: Path, payload: dict[str, Any]) -> dict[str, Any]:
    root = _campaign_root(campaign)
    with _mutation_lock(root):
        manifest, state, setup_text, summary_text = _load_for_mutation(root)
        operation_id, payload_hash, expected = _prepare_operation(state, payload, "complete-stage")
        replay = _operation_result(state, operation_id, payload_hash)
        if replay is not None:
            return {**replay, "operation": "complete-stage"}
        if expected != state["setup_revision"]:
            raise StateError("stale_revision", f"expected revision {expected}, current revision is {state['setup_revision']}")
        stage_id = payload.get("stage_id")
        if stage_id not in STAGE_IDS:
            raise StateError("input_invalid", "stage_id must reference a Deep v8 stage")
        stage = state["stages"][stage_id]
        is_rematerialization = stage.get("completed_revision") is not None
        if stage["status"] == "complete":
            raise StateError("stage_complete", f"stage {stage_id} is already complete")
        if stage["status"] not in {"active", "needs_review", "stale"}:
            raise StateError("stage_order", f"stage {stage_id} is not open for completion")
        if not _stage_prerequisites_complete(state, manifest, stage_id):
            raise StateError("stage_order", f"stage {stage_id} prerequisites are incomplete")
        _required_stage_decisions(state, manifest, stage_id)
        if stage_id == "09_first_act_preparation" and state["gates"]["preparation_approved"]["status"] != "complete":
            raise StateError("gate_blocked", "First Act Preparation cannot complete before preparation approval")
        output_refs = _refs(payload.get("output_refs", []), "output_refs")
        output_digest = _validate_digest(payload.get("output_digest"), "output_digest", allow_empty=False)
        if not output_refs:
            raise StateError("stage_incomplete", "stage completion needs at least one materialized output")
        _validate_stage_output_refs(manifest, stage_id, output_refs, _decision_map(state))
        computed_digest = compute_output_digest(root, output_refs)
        if output_digest != computed_digest:
            raise StateError("output_digest_mismatch", f"stage {stage_id} digest does not match its files")
        if (
            stage_id == "09_first_act_preparation"
            and output_digest != state["gates"]["preparation_approved"]["output_digest"]
        ):
            raise StateError(
                "output_digest_mismatch",
                "First Act Preparation outputs changed after Player approval",
            )
        next_revision = state["setup_revision"] + 1
        _apply_extension_evidence(root, state, stage_id, payload.get("extensions"), next_revision)
        state["setup_revision"] = next_revision
        stage.update(
            status="complete",
            completed_revision=next_revision,
            output_refs=output_refs,
            output_digest=output_digest,
            invalidation_reason="",
        )
        state["fatigue"]["last_checkpoint_revision"] = next_revision
        state["fatigue"]["last_checkpoint_decision_count"] = len(state["decisions"])
        state["fatigue"]["decisions_since_checkpoint"] = 0
        if is_rematerialization:
            _invalidate_gates(state, _gate_invalidation_start(stage_id), f"stage {stage_id} rematerialized")
        _advance_current_stage(state, manifest)
        result = _commit_operation(
            root,
            state,
            setup_text,
            summary_text,
            operation_id=operation_id,
            payload_hash=payload_hash,
            command="complete-stage",
        )
        return {**result, "operation": "complete-stage", "completed_stage": stage_id}


def _decision_terminal(state: dict[str, Any], decision_id: str) -> bool:
    decision = _decision_map(state).get(decision_id)
    return decision is not None and decision["status"] in {"locked", "defaulted"}


def _extensions_resolved_through(state: dict[str, Any], stage_ids: tuple[str, ...]) -> bool:
    for entry in state["extensions"].values():
        for stage_id, portion in entry["stages"].items():
            if stage_id in stage_ids and portion["status"] == "active":
                return False
    return True


def _gate_prerequisites(state: dict[str, Any], gate_id: str) -> tuple[bool, str]:
    gate_index = GATE_IDS.index(gate_id)
    if gate_id == "research_scope_locked":
        if state["stages"]["02_research_canon_grounding"]["status"] != "complete":
            return False, "Research and Canon Grounding must be complete"
        decisions = _decision_map(state)
        status = decisions.get("02_research_need_and_permission", {}).get("value", {})
        lock = decisions.get("02_current_scale_lock", {}).get("value", {})
        research_status = status.get("status") if isinstance(status, dict) else None
        if research_status == "needed_pending":
            return False, "pending research cannot lock the current playable scale"
        if not isinstance(lock, dict) or lock.get("current_scale_lock_permitted") is not True:
            return False, "current-scale lock permission must be explicit"
        risk_required = research_status in {"partial_complete", "unavailable_risk_accepted"}
        if risk_required and lock.get("risk_accepted") is not True:
            return False, "partial or unavailable research requires explicit risk acceptance"
        return True, ""
    if gate_id == "stages_1_8_complete":
        ok = all(state["stages"][stage_id]["status"] == "complete" for stage_id in STAGE_IDS[:8])
        ok = ok and _extensions_resolved_through(state, STAGE_IDS[:8])
        return ok, "Stages 1 through 8 and their active extensions must be complete"
    # preparation_approved may atomically materialize the internal integrated
    # review gate from the same second Player approval; see record_gate().
    previous_gate = GATE_IDS[gate_index - 1] if gate_index > 0 else ""
    if gate_id == "preparation_approved":
        previous_gate = "cross_read_passed"
    if previous_gate and state["gates"][previous_gate]["status"] != "complete":
        return False, f"gate {previous_gate} must be complete"
    required_decision = {
        "first_act_design_complete": ("09_first_act_frame", "09_opening_shape"),
        "design_direction_approved": ("09_design_direction_review",),
        "integrated_review_accepted": ("09_preparation_approval",),
        "preparation_approved": ("09_preparation_approval",),
    }.get(gate_id, ())
    if required_decision and not all(_decision_terminal(state, decision_id) for decision_id in required_decision):
        return False, f"gate {gate_id} is missing its accepted Player decision"
    if gate_id == "draft_preflight_passed" and state["stages"]["09_first_act_preparation"]["status"] != "complete":
        return False, "First Act Preparation stage must be complete before draft preflight"
    return True, ""


def record_gate(campaign: Path, payload: dict[str, Any]) -> dict[str, Any]:
    root = _campaign_root(campaign)
    with _mutation_lock(root):
        manifest, state, setup_text, summary_text = _load_for_mutation(root)
        operation_id, payload_hash, expected = _prepare_operation(state, payload, "record-gate")
        replay = _operation_result(state, operation_id, payload_hash)
        if replay is not None:
            return {**replay, "operation": "record-gate"}
        if expected != state["setup_revision"]:
            raise StateError("stale_revision", f"expected revision {expected}, current revision is {state['setup_revision']}")
        gate_id = payload.get("gate_id")
        if gate_id not in GATE_IDS:
            raise StateError("input_invalid", "gate_id must reference the Deep v8 gate chain")
        if gate_id == "integrated_review_accepted":
            raise StateError(
                "gate_blocked",
                "integrated_review_accepted is internal and only closes with preparation_approved",
            )
        allowed, reason = _gate_prerequisites(state, gate_id)
        if not allowed:
            raise StateError("gate_blocked", reason)
        gate = state["gates"][gate_id]
        if gate["status"] == "complete":
            raise StateError("gate_complete", f"gate {gate_id} is already complete")
        input_digest = _validate_digest(payload.get("input_digest"), "input_digest", allow_empty=False)
        output_digest = _validate_digest(payload.get("output_digest"), "output_digest", allow_empty=False)
        decided_by = str(payload.get("decided_by", "")).strip()
        if not decided_by:
            raise StateError("input_invalid", "decided_by must identify the Player or validating coordinator")
        if gate_id in {"design_direction_approved", "preparation_approved"} and decided_by.lower() != "player":
            raise StateError("gate_blocked", f"gate {gate_id} requires decided_by=player")
        gate_index = GATE_IDS.index(gate_id)
        if gate_id == "research_scope_locked":
            stage_digest = state["stages"]["02_research_canon_grounding"]["output_digest"]
            if input_digest != stage_digest:
                raise StateError(
                    "gate_digest_mismatch",
                    "research_scope_locked input must match Stage 2 materialization",
                )
        elif gate_index > 0:
            predecessor_id = "cross_read_passed" if gate_id == "preparation_approved" else GATE_IDS[gate_index - 1]
            predecessor_digest = state["gates"][predecessor_id]["output_digest"]
            if input_digest != predecessor_digest:
                raise StateError("gate_digest_mismatch", f"gate {gate_id} input must match {predecessor_id} output")
        if gate_id in {"cross_read_passed", "preparation_approved"} and output_digest != input_digest:
            raise StateError(
                "gate_digest_mismatch",
                f"gate {gate_id} must preserve the reviewed preparation digest",
            )
        evidence: dict[str, Any] = {}
        if gate_id == "ready_and_snapshotted":
            evidence = _validate_ready_evidence_files(
                root,
                state,
                manifest,
                payload.get("evidence"),
                before_transition=True,
            )
            if output_digest != evidence["snapshot_digest"]:
                raise StateError("gate_digest_mismatch", "final gate output must equal the snapshot digest")
        # The final attestation is revision-neutral: the locked profile,
        # snapshot, and aggregate report were all produced against this exact
        # revision.  Incrementing here would stale that evidence immediately.
        next_revision = state["setup_revision"] if gate_id == "ready_and_snapshotted" else state["setup_revision"] + 1
        state["setup_revision"] = next_revision
        dual_review = gate_id in {"integrated_review_accepted", "preparation_approved"}
        completed_gates = [gate_id]
        if dual_review:
            completed_gates = ["integrated_review_accepted", "preparation_approved"]
        for completed_gate_id in completed_gates:
            state["gates"][completed_gate_id].update(
                status="complete",
                revision=next_revision,
                input_digest=input_digest,
                output_digest=output_digest,
                decided_by=decided_by,
                evidence=copy.deepcopy(evidence),
                invalidation_reason="",
            )
        invalidation_start = GATE_IDS.index("preparation_approved") + 1 if dual_review else GATE_IDS.index(gate_id) + 1
        _invalidate_gates(state, invalidation_start, f"upstream gate {gate_id} was recorded again")
        _advance_current_stage(state, manifest)
        result = _commit_operation(
            root,
            state,
            setup_text,
            summary_text,
            operation_id=operation_id,
            payload_hash=payload_hash,
            command="record-gate",
        )
        return {**result, "operation": "record-gate", "completed_gate": gate_id, "completed_gates": completed_gates}


def _prepare_ready_evidence_locked(
    campaign: Path,
    *,
    operation_id: str,
    snapshot_ref: str,
    aggregate_check_ref: str,
) -> dict[str, Any]:
    """Run the real full candidate-ready check and materialize its attestation."""

    root = _campaign_root(campaign)
    manifest = load_manifest(root, require_full=True)
    state = _validated_campaign_state(root)
    if state["gates"]["draft_preflight_passed"]["status"] != "complete":
        raise StateError("gate_blocked", "draft_preflight_passed must complete before final evidence")
    contract = manifest.get("final_readiness_contract", {})
    snapshot_ref = _relative_ref(snapshot_ref, "snapshot_ref")
    aggregate_check_ref = _relative_ref(aggregate_check_ref, "aggregate_check_ref")
    snapshot_patterns = contract.get("snapshot_manifest_patterns", [])
    aggregate_patterns = contract.get("aggregate_report_patterns", [])
    if not any(PurePosixPath(snapshot_ref).match(pattern) for pattern in snapshot_patterns):
        raise StateError("readiness_evidence_invalid", "snapshot_ref is not manifest-authorized")
    if not any(PurePosixPath(aggregate_check_ref).match(pattern) for pattern in aggregate_patterns):
        raise StateError("readiness_evidence_invalid", "aggregate_check_ref is not manifest-authorized")

    selected_ref = str(contract["selected_profile_ref"]).removeprefix("campaign/")
    unused_ref = str(contract["unused_profile_ref"]).removeprefix("campaign/")
    snapshot_digest = _file_digest(root, snapshot_ref)
    selected_digest = _file_digest(root, selected_ref)
    unused_digest = _file_digest(root, unused_ref)
    checker = Path(__file__).with_name("check_state.py")
    process = subprocess.run(
        [sys.executable or "python", str(checker), str(root), "--scope", "full", "--preflight-ready"],
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise StateError("aggregate_check_failed", f"check_state did not return JSON: {exc}") from exc
    if process.returncode != 0 or result.get("error_count") != 0 or result.get("ok") is not True:
        error_rules = [
            str(finding.get("rule", "unknown"))
            for finding in result.get("findings", [])
            if isinstance(finding, dict) and finding.get("severity") == "error"
        ]
        rule_suffix = f"; first rules: {', '.join(error_rules[:8])}" if error_rules else ""
        raise StateError(
            "aggregate_check_failed",
            f"candidate-ready aggregate check has {result.get('error_count', 'unknown')} error(s){rule_suffix}",
        )
    report = {
        "kind": contract.get("aggregate_report_kind"),
        "flow_id": FLOW_ID,
        "setup_revision": state["setup_revision"],
        "operation_id": operation_id,
        "status": "passed",
        "error_count": 0,
        "warning_count": result.get("warning_count", 0),
        "scope": result.get("scope", "full"),
        "snapshot_ref": snapshot_ref,
        "snapshot_digest": snapshot_digest,
        "profile_digest": selected_digest,
    }
    target = root / Path(*PurePosixPath(aggregate_check_ref).parts)
    original = target.read_bytes() if target.is_file() else None
    _atomic_bytes(target, _json_bytes(report))
    evidence = {
        "snapshot_ref": snapshot_ref,
        "snapshot_digest": snapshot_digest,
        "selected_profile_ref": selected_ref,
        "selected_profile_digest": selected_digest,
        "unused_profile_ref": unused_ref,
        "unused_profile_digest": unused_digest,
        "aggregate_check_ref": aggregate_check_ref,
        "aggregate_check_digest": _file_digest(root, aggregate_check_ref),
    }
    try:
        _validate_ready_evidence_files(root, state, manifest, evidence, before_transition=True)
    except Exception:
        if original is None:
            target.unlink(missing_ok=True)
        else:
            _atomic_bytes(target, original)
        raise
    return {
        "ok": True,
        "idempotent": False,
        "operation": "prepare-ready-evidence",
        "operation_id": operation_id,
        "evidence": evidence,
        "report": report,
    }


def _find_ready_operation_report(
    root: Path,
    manifest: dict[str, Any],
    operation_id: str,
) -> tuple[str, dict[str, Any]] | None:
    """Find an existing manifest-authorized readiness operation globally.

    ``prepare-ready-evidence`` does not advance the Session 0 revision, so its
    operation id cannot live in the normal state mutation registry.  Scan the
    bounded report namespace instead, preventing the same operation id from
    being reused at a second authorized path.
    """

    contract = manifest.get("final_readiness_contract", {})
    patterns = contract.get("aggregate_report_patterns", [])
    if not isinstance(patterns, list):
        raise StateError("manifest_invalid", "aggregate_report_patterns must be a list")
    safe_patterns = [_safe_manifest_pattern(pattern, "aggregate pattern") for pattern in patterns]
    for path in sorted(root.rglob("*.json")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if not any(PurePosixPath(relative).match(pattern) for pattern in safe_patterns):
            continue
        try:
            report = _read_json(path, "aggregate readiness report")
        except StateError:
            continue
        if report.get("operation_id") == operation_id:
            return relative, report
    return None


def prepare_ready_evidence(
    campaign: Path,
    *,
    operation_id: str,
    expected_revision: int,
    snapshot_ref: str,
    aggregate_check_ref: str,
) -> dict[str, Any]:
    root = _campaign_root(campaign)
    operation_id = _safe_id(operation_id, "operation_id")
    if not _strict_int(expected_revision):
        raise StateError("input_invalid", "expected_revision must be a non-negative integer")
    with _mutation_lock(root):
        state = _validated_campaign_state(root)
        if expected_revision != state["setup_revision"]:
            raise StateError(
                "stale_revision",
                f"expected revision {expected_revision}, current revision is {state['setup_revision']}",
            )
        manifest = load_manifest(root, require_full=True)
        target_ref = _relative_ref(aggregate_check_ref, "aggregate_check_ref")
        previous = _find_ready_operation_report(root, manifest, operation_id)
        if previous is not None and previous[0] != target_ref:
            raise StateError(
                "operation_conflict",
                f"operation_id {operation_id} already owns aggregate report {previous[0]}",
            )
        target = root / Path(*PurePosixPath(target_ref).parts)
        if target.is_file():
            try:
                existing = _read_json(target, "aggregate readiness report")
            except StateError as exc:
                raise StateError(
                    "operation_conflict",
                    f"aggregate report target already exists but is unreadable: {target_ref}",
                ) from exc
            if existing.get("operation_id") == operation_id:
                contract = manifest["final_readiness_contract"]
                selected_ref = str(contract["selected_profile_ref"]).removeprefix("campaign/")
                unused_ref = str(contract["unused_profile_ref"]).removeprefix("campaign/")
                evidence = {
                    "snapshot_ref": _relative_ref(snapshot_ref, "snapshot_ref"),
                    "snapshot_digest": _file_digest(root, snapshot_ref),
                    "selected_profile_ref": selected_ref,
                    "selected_profile_digest": _file_digest(root, selected_ref),
                    "unused_profile_ref": unused_ref,
                    "unused_profile_digest": _file_digest(root, unused_ref),
                    "aggregate_check_ref": target_ref,
                    "aggregate_check_digest": _file_digest(root, target_ref),
                }
                _validate_ready_evidence_files(
                    root,
                    state,
                    manifest,
                    evidence,
                    before_transition=True,
                )
                return {
                    "ok": True,
                    "idempotent": True,
                    "operation": "prepare-ready-evidence",
                    "operation_id": operation_id,
                    "evidence": evidence,
                    "report": existing,
                }
        return _prepare_ready_evidence_locked(
            root,
            operation_id=operation_id,
            snapshot_ref=snapshot_ref,
            aggregate_check_ref=target_ref,
        )


def render_summary(campaign: Path) -> dict[str, Any]:
    state = _validated_campaign_state(campaign)
    return {"ok": True, "operation": "render-summary", "markdown": _summary_markdown(state)}


def _json_value(raw: str, label: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StateError("input_invalid", f"{label} is not valid JSON: {exc}") from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", help="Path to the active campaign directory")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="Validate and summarize the current Deep v8 state")
    subparsers.add_parser("render-summary", help="Render a player-readable progress summary without writing")

    ready = subparsers.add_parser(
        "prepare-ready-evidence",
        help="Run full candidate-ready validation and write the canonical aggregate report",
    )
    ready.add_argument("--snapshot-ref", required=True)
    ready.add_argument("--aggregate-check-ref", required=True)
    ready.add_argument("--operation-id", required=True)
    ready.add_argument("--expected-revision", type=int, required=True)

    decision = subparsers.add_parser("record-decision", help="Record or revise one accepted decision")
    decision.add_argument("--operation-id", required=True)
    decision.add_argument("--expected-revision", type=int, required=True)
    decision.add_argument("--decision-id", required=True)
    decision.add_argument("--stage-id", required=True)
    decision.add_argument("--status", choices=sorted(DECISION_STATUSES), required=True)
    decision.add_argument("--source", choices=sorted(DECISION_SOURCES), required=True)
    decision.add_argument("--value-json", required=True)
    decision.add_argument("--depends-on-json", default="[]")
    decision.add_argument("--trigger-tags-json", default="[]")

    complete = subparsers.add_parser("complete-stage", help="Record one materialized stage boundary")
    complete.add_argument("--operation-id", required=True)
    complete.add_argument("--expected-revision", type=int, required=True)
    complete.add_argument("--stage-id", required=True)
    complete.add_argument("--output-refs-json", required=True)
    complete.add_argument("--output-digest", required=True)
    complete.add_argument("--extensions-json", default="{}")

    gate = subparsers.add_parser("record-gate", help="Record one revision-bound approval or validation gate")
    gate.add_argument("--operation-id", required=True)
    gate.add_argument("--expected-revision", type=int, required=True)
    gate.add_argument("--gate-id", required=True)
    gate.add_argument("--input-digest", required=True)
    gate.add_argument("--output-digest", required=True)
    gate.add_argument("--decided-by", required=True)
    gate.add_argument("--evidence-json", default="{}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    campaign = Path(args.campaign)
    try:
        if args.command == "status":
            result = status(campaign)
        elif args.command == "render-summary":
            result = render_summary(campaign)
        elif args.command == "prepare-ready-evidence":
            result = prepare_ready_evidence(
                campaign,
                operation_id=args.operation_id,
                expected_revision=args.expected_revision,
                snapshot_ref=args.snapshot_ref,
                aggregate_check_ref=args.aggregate_check_ref,
            )
        elif args.command == "record-decision":
            result = record_decision(
                campaign,
                {
                    "operation_id": args.operation_id,
                    "expected_revision": args.expected_revision,
                    "decision_id": args.decision_id,
                    "stage_id": args.stage_id,
                    "status": args.status,
                    "source": args.source,
                    "value": _json_value(args.value_json, "--value-json"),
                    "depends_on": _json_value(args.depends_on_json, "--depends-on-json"),
                    "trigger_tags": _json_value(args.trigger_tags_json, "--trigger-tags-json"),
                },
            )
        elif args.command == "complete-stage":
            result = complete_stage(
                campaign,
                {
                    "operation_id": args.operation_id,
                    "expected_revision": args.expected_revision,
                    "stage_id": args.stage_id,
                    "output_refs": _json_value(args.output_refs_json, "--output-refs-json"),
                    "output_digest": args.output_digest,
                    "extensions": _json_value(args.extensions_json, "--extensions-json"),
                },
            )
        else:
            result = record_gate(
                campaign,
                {
                    "operation_id": args.operation_id,
                    "expected_revision": args.expected_revision,
                    "gate_id": args.gate_id,
                    "input_digest": args.input_digest,
                    "output_digest": args.output_digest,
                    "decided_by": args.decided_by,
                    "evidence": _json_value(args.evidence_json, "--evidence-json"),
                },
            )
    except StateError as exc:
        result = {"ok": False, "operation": args.command, "error_category": exc.category, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())

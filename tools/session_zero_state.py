"""Manage the canonical RPG Deep Session 0 v8 decision state.

The helper is intentionally semantic-free.  The coordinator decides what a
Player answer means and supplies controlled trigger tags from the Deep v8
manifest.  This module only enforces ordering, revisions, idempotency,
extension completion evidence, approval dependencies, and the small
``setup_profile.yaml`` progress mirror.

All mutating commands use an operation id plus an expected setup revision and
commit ``session_zero_state.json`` and ``setup_profile.yaml`` as one
rollback-protected operation.

Setup aids around the ledger: ``set-depth`` and ``set-language`` replace hand
edits of the routing and play-language selectors, ``digest`` and
``stage-owners`` are read-only, and ``finalize`` runs the Deep readiness
sequence in one call, stopping at the first failing step.
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

import lang_pack
import snapshot as snapshot_tool
from file_transaction import FileTransactionError, assert_readable, campaign_lock, commit_files, recover


STATE_FILE = "session_zero_state.json"
SETUP_FILE = "setup_profile.yaml"
PROFILE_FILE = "play_profile.yaml"
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
APPROVAL_DEPENDENCIES = {
    "09_design_direction_review": "first_act_design_complete",
    "09_preparation_approval": "cross_read_passed",
}
# A stage whose completion is immediately followed by a gate. complete-stage
# proves that gate can pass before it writes, so a completed stage never waits
# behind a decision that must be re-recorded (which would reopen the stage).
STAGE_GATES = {
    "02_research_canon_grounding": "research_scope_locked",
    "08_reciprocity_campaign_horizon": "stages_1_8_complete",
}
SETUP_DEPTHS = ("quick", "standard", "deep")
PLAY_LANGUAGE_HINT = (
    "settle the play language before Stage 1 content: run session_zero_state.py <campaign> "
    "set-language --language <code> (play_profile.yaml narration.language is unset or auto)"
)

# Content Boundaries rows the helper can verify by exact text: the fixed rows
# keep the Setting `never (fixed)`, and two rows have a closed set of options.
CONTENT_SECTION = "Content Boundaries"
FIXED_CONTENT_SETTING = "never (fixed)"
FIXED_CONTENT_ROWS = (
    "Anyone under 18 in a sexual or romantic context, including backstory",
    "Graphic violence against children on the page",
)
CONTENT_SETTINGS = {
    "sexual content": ("avoid", "fade before it starts", "implied, no explicit description"),
    "harm to children": ("mentioned or offscreen", "avoid"),
}
ANCHOR_FILE = "world_truths.md"
ANCHOR_HEADING = "Price And Bounty Anchors"

FINALIZE_STEPS = (
    "preflight",
    "draft_preflight_passed",
    "lock_profiles",
    "snapshot",
    "ready_evidence",
    "ready_and_snapshotted",
)
# Warnings that readiness does not carry into play: NPC cards above the
# accepted scale (a stat above a rules.md Tier Cap is reported as
# early_stage_power_spike), and the age rule, which blocks even when a
# directive has turned it into info. Records in another language are only
# reported: the content step keeps its category and setting words in English.
CALIBRATION_RULES = frozenset({
    "power_band_mismatch",
    "early_stage_power_spike",
    "early_stage_power_inflation",
    "elite_stat_without_power_band",
    "character_power_band_missing",
})
ADVISORY_RULES = frozenset({"records_language_mismatch"})
ALWAYS_BLOCKING_RULES = frozenset({"minor_romance_history"})

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
    """Typed structural state failure suitable for CLI and validator use.

    ``problems`` lists every contract problem found at once, each as
    ``{"category", "message"}``; ``details`` carries step context for the CLI.
    """

    def __init__(
        self,
        category: str,
        reason: str,
        *,
        problems: list[dict[str, str]] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(reason)
        self.category = category
        self.problems = list(problems or [])
        self.details = dict(details or {})


def _problems_error(problems: list[tuple[str, str]]) -> StateError:
    """One error naming every problem; its category is the first problem's."""

    listed = [{"category": category, "message": message} for category, message in problems]
    if len(problems) == 1:
        return StateError(problems[0][0], problems[0][1], problems=listed)
    numbered = "; ".join(f"{index}) {message}" for index, (_, message) in enumerate(problems, start=1))
    return StateError(problems[0][0], f"{len(problems)} problems: {numbered}", problems=listed)


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
    # New decisions apply only to newly selected setup contracts. Loading the
    # current corpus must never add an unanswered requirement to an old setup.
    setup_path = root / SETUP_FILE
    setup_schema = _top_scalar(setup_path.read_text(encoding="utf-8"), "schema_version") if setup_path.is_file() else "8"
    try:
        setup_version = int(setup_schema or "8")
    except ValueError as exc:
        raise StateError("setup_invalid", "setup schema_version must be an integer") from exc

    def applies_to_setup(definition: Any) -> bool:
        if not isinstance(definition, dict) or not _strict_int(definition.get("required_from_setup_schema", 0)):
            raise StateError("manifest_invalid", "versioned definitions need a non-negative required_from_setup_schema")
        return definition.get("required_from_setup_schema", 0) <= setup_version

    for stage in raw_stages:
        stage["decisions"] = [
            decision for decision in stage.get("decisions", [])
            if applies_to_setup(decision)
        ]
    manifest["structured_contracts"] = {
        key: contract for key, contract in _structured_contracts(manifest).items()
        if applies_to_setup(contract)
    }
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


def _structured_decision_problems(
    decisions: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
    *,
    recorded_id: str = "",
) -> list[str]:
    """Every manifest-declared structural problem, in contract order.

    This deliberately does not inspect prose or infer tags from keywords.  The
    coordinator supplies enum-valued decisions and controlled trigger tags;
    this layer merely proves that those values agree with the manifest.
    ``recorded_id`` names the decision being recorded now: a requirement added
    after a ledger was written applies only when that decision is recorded
    again, so an older ledger never gains an unanswered requirement.
    """

    problems: list[str] = []
    contracts = _structured_contracts(manifest)

    def object_value(decision_id: str) -> dict[str, Any] | None:
        value = decisions[decision_id].get("value")
        if isinstance(value, dict):
            return value
        problems.append(f"{decision_id} must use a structured object value")
        return None

    seats = contracts.get("agent_seats", {})
    seat_id = seats.get("decision_id") if seats else None
    if seat_id in decisions:
        decision = decisions[seat_id]
        value = object_value(seat_id)
        modes = seats.get("modes", [])
        if value is not None and (
            value.get("mode") not in modes
            or decision.get("source") != "player"
            or decision.get("status") != "locked"
        ):
            problems.append(f"{seat_id} requires a locked Player choice of {' or '.join(modes)}")

    authority = contracts.get("creation_authority", {})
    if authority:
        decision_id = authority.get("decision_id")
        modes = authority.get("modes", {})
        generative_ids = authority.get("world_generative_decision_ids", [])
        if not _nonempty(decision_id) or not isinstance(modes, dict) or not modes:
            raise StateError("manifest_invalid", "creation authority contract is malformed")
        if not isinstance(generative_ids, list) or any(not _nonempty(item) for item in generative_ids):
            raise StateError("manifest_invalid", "world_generative_decision_ids must be stable ids")
        decision = decisions.get(decision_id)
        mode = None
        if decision is not None:
            value = object_value(decision_id)
            if value is not None:
                mode = value.get("mode")
                if not isinstance(mode, str) or mode not in modes:
                    problems.append(f"{decision_id}.mode must be one of: {', '.join(modes)}")
            if decision.get("source") != "player" or decision.get("status") != "locked":
                problems.append(f"{decision_id} must be a locked Player decision")
        for generative_id in generative_ids:
            generative = decisions.get(generative_id)
            if generative is None or generative.get("source") not in {"derived", "defaulted"}:
                continue
            if decision is None:
                problems.append(f"derived world decision {generative_id} requires {decision_id}")
            elif isinstance(mode, str) and mode in modes:
                mode_rule = modes[mode]
                if not isinstance(mode_rule, dict) or not mode_rule.get("allow_derived_world_generation", False):
                    problems.append(f"creation authority mode does not permit derived world decision {generative_id}")
            if decision_id not in generative.get("depends_on", []):
                problems.append(f"derived world decision {generative_id} must depend on {decision_id}")

    research = contracts.get("research", {})
    if research:
        status_id = research.get("status_decision_id")
        lock_id = research.get("lock_decision_id")
        statuses = research.get("statuses", [])
        permissions = research.get("permissions", [])
        power_scales = research.get("npc_power_scales", [])
        status_decision = decisions.get(status_id)
        if status_decision is not None:
            value = object_value(status_id)
            if value is not None and (
                value.get("status") not in statuses or value.get("permission") not in permissions
            ):
                problems.append(
                    f"{status_id} has an invalid research status or permission "
                    f"(status: {' | '.join(statuses)}; permission: {' | '.join(permissions)})"
                )
        lock_decision = decisions.get(lock_id)
        if lock_decision is not None:
            value = object_value(lock_id)
            if value is not None:
                if type(value.get("risk_accepted")) is not bool or type(
                    value.get("current_scale_lock_permitted")
                ) is not bool:
                    problems.append(f"{lock_id} must record boolean risk_accepted and current_scale_lock_permitted")
                if power_scales and recorded_id == lock_id and value.get("npc_power_scale") not in power_scales:
                    problems.append(f"{lock_id}.npc_power_scale must be one of: {', '.join(power_scales)}")
            if status_decision is None or status_id not in lock_decision.get("depends_on", []):
                problems.append(f"{lock_id} must depend on {status_id}")

    topology = contracts.get("topology", {})
    if topology:
        intent_id = topology.get("intent_decision_id")
        activation_id = topology.get("activation_decision_id")
        topology_defs = manifest.get("topologies", {})
        branches = [item for item in topology_defs if item != "mixed"]
        intent = decisions.get(intent_id)
        intent_value = object_value(intent_id) if intent is not None else None
        selected = intent_value.get("primary_topology") if intent_value is not None else None
        if intent_value is not None and (not isinstance(selected, str) or selected not in topology_defs):
            problems.append(f"{intent_id}.primary_topology must be one of: {', '.join(topology_defs)}")
            selected = None
        if selected == "mixed" and intent_value.get("primary_branch") not in branches:
            problems.append(f"{intent_id} mixed topology requires a primary_branch of: {', '.join(branches)}")
        activation = decisions.get(activation_id)
        if activation is not None:
            value = object_value(activation_id)
            if intent is None or intent_id not in activation.get("depends_on", []):
                problems.append(f"{activation_id} must depend on {intent_id}")
            if value is not None and selected is not None:
                problems.extend(_topology_activation_problems(activation_id, activation, value, intent_value, manifest))
    return problems


def _topology_activation_problems(
    activation_id: str,
    activation: dict[str, Any],
    value: dict[str, Any],
    intent_value: dict[str, Any],
    manifest: dict[str, Any],
) -> list[str]:
    """Stage 6 must restate the Stage 1 topology with its manifest build order and trigger."""

    topology_defs = manifest.get("topologies", {})
    selected = intent_value["primary_topology"]
    problems: list[str] = []
    if value.get("primary_topology") != selected:
        problems.append(f"{activation_id}.primary_topology must match Stage 1 ({selected})")
    if selected == "mixed" and value.get("primary_branch") != intent_value.get("primary_branch"):
        problems.append(f"{activation_id} mixed primary branch must match Stage 1")
    expected_order = topology_defs[selected].get("build_order")
    if value.get("build_order") != expected_order:
        problems.append(f"{activation_id}.build_order must be the manifest order: {json.dumps(expected_order)}")
    trigger_topology = intent_value.get("primary_branch") if selected == "mixed" else selected
    trigger_rule = topology_defs.get(trigger_topology, {}) if isinstance(trigger_topology, str) else {}
    required_tag = trigger_rule.get("activation_trigger")
    if required_tag and required_tag not in activation.get("trigger_tags", []):
        problems.append(f"{activation_id} must include topology trigger {required_tag}")
    return problems


def _validate_structured_decisions(
    decisions: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
    *,
    state_validation: bool,
) -> None:
    problems = _structured_decision_problems(decisions, manifest)
    if problems:
        category = "state_invalid" if state_validation else "decision_contract"
        raise _problems_error([(category, message) for message in problems])


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


def _validate_history(entry: dict[str, Any], label: str, revision: int) -> None:
    history = entry.get("history", [])
    if not isinstance(history, list) or any(
        not isinstance(item, dict)
        or not _strict_int(item.get("revision"), minimum=1)
        or item["revision"] > revision
        or "history" in item
        for item in history
    ):
        raise StateError("state_invalid", f"{label} history must contain prior revision records")


def _archive_entry(entry: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        *copy.deepcopy(entry.get("history", [])),
        copy.deepcopy({key: value for key, value in entry.items() if key != "history"}),
    ]


def _approval_basis(state: dict[str, Any], decision_id: str) -> dict[str, Any] | None:
    gate_id = APPROVAL_DEPENDENCIES.get(decision_id)
    if gate_id is None:
        return None
    gate = state["gates"][gate_id]
    if gate["status"] != "complete":
        return None
    return {"gate_id": gate_id, "revision": gate["revision"], "output_digest": gate["output_digest"]}


def _approval_current(state: dict[str, Any], decision: dict[str, Any]) -> bool:
    basis = _approval_basis(state, decision["decision_id"])
    if basis is None or decision["revision"] <= basis["revision"]:
        return False
    # Legacy approvals have no explicit basis. Their current revision, never
    # their original creation revision, must follow the latest reviewed gate.
    return decision.get("approval_basis", basis) == basis


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
        _validate_history(decision, f"decision {decision_id}", revision)
        basis = decision.get("approval_basis")
        if basis is not None:
            if (
                not isinstance(basis, dict)
                or basis.get("gate_id") != APPROVAL_DEPENDENCIES.get(decision_id)
                or not _strict_int(basis.get("revision"), minimum=1)
                or basis["revision"] >= decision["revision"]
            ):
                raise StateError("state_invalid", f"decision {decision_id} approval basis is invalid")
            _validate_digest(basis.get("output_digest"), "approval basis digest", allow_empty=False)
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
        _validate_history(gate, f"gate {gate_id}", revision)
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
    # An invalidated approval stays in the ledger as historical evidence. Only
    # a complete approval gate claims that it is current; its prerequisites
    # above enforce a fresh decision bound to the reviewed upstream output.
    for stage in manifest["stages"]:
        if stages[stage["id"]]["status"] == "complete":
            for definition in stage.get("decisions", []):
                if definition.get("required_from_setup_schema") and definition["id"] not in decisions_by_id:
                    raise StateError("stage_incomplete", f"stage {stage['id']} is missing decision {definition['id']}")

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


def _validate_materialized_agent_seats(
    profile_text: str, state: dict[str, Any], manifest: dict[str, Any]
) -> None:
    contract = _structured_contracts(manifest).get("agent_seats")
    if not contract:
        return
    decision = _decision_map(state).get(contract["decision_id"])
    mode = _block_scalar(profile_text, "agent_seats", "mode")
    if decision is None or mode != decision.get("value", {}).get("mode"):
        raise StateError("decision_materialization_mismatch", "play_profile agent_seats.mode must match accepted 07_agent_seats")


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
        ("aggregate_check_ref", "aggregate_check_digest"),
    )
    if before_transition:
        digest_pairs += (
            ("selected_profile_ref", "selected_profile_digest"),
            ("unused_profile_ref", "unused_profile_digest"),
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

    snapshot_dir = (root / Path(*PurePosixPath(checked["snapshot_ref"]).parts)).parent
    profile_root = root if before_transition else snapshot_dir
    for ref_key, digest_key in (
        ("selected_profile_ref", "selected_profile_digest"),
        ("unused_profile_ref", "unused_profile_digest"),
    ):
        if _file_digest(profile_root, checked[ref_key]) != checked[digest_key]:
            raise StateError("readiness_evidence_stale", f"historical {ref_key} no longer matches {digest_key}")
    selected_text = (profile_root / checked["selected_profile_ref"]).read_text(encoding="utf-8")
    unused_text = (profile_root / checked["unused_profile_ref"]).read_text(encoding="utf-8")
    _validate_materialized_agent_seats(selected_text, state, manifest)
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
    if before_transition:
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
    for relative, record in record_map.items():
        copied = snapshot_dir / Path(*PurePosixPath(relative).parts)
        if not copied.is_file():
            raise StateError("readiness_evidence_invalid", f"snapshot copy is missing: {relative}")
        payload = copied.read_bytes()
        if record.get("size") != len(payload) or record.get("sha256") != hashlib.sha256(payload).hexdigest():
            raise StateError("readiness_evidence_invalid", f"snapshot copy digest is invalid: {relative}")
        if before_transition:
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
    selected_payload = (profile_root / checked["selected_profile_ref"]).read_bytes()
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


def _replace_top_scalar(text: str, key: str, value: Any, *, label: str = SETUP_FILE) -> str:
    pattern = re.compile(rf"(?m)^({re.escape(key)}:[ \t]*)([^#\r\n]*?)([ \t]*(?:#[^\r\n]*)?)(?=\r?$)")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        category = "setup_invalid" if label == SETUP_FILE else "profile_invalid"
        raise StateError(category, f"{label} must contain exactly one top-level {key}")
    return pattern.sub(lambda match: f"{match.group(1)}{value}{match.group(3)}", text, count=1)


def _block_span(text: str, block: str) -> tuple[int, int] | None:
    """Offsets of the indented body under a top-level ``block:`` line."""

    match = re.search(rf"(?ms)^{re.escape(block)}:[^\n]*\n(.*?)(?=^[A-Za-z_][\w-]*:|\Z)", text)
    return match.span(1) if match else None


def _block_scalar(text: str, block: str, key: str) -> str | None:
    span = _block_span(text, block)
    if span is None:
        return None
    return _top_scalar(re.sub(r"(?m)^  ", "", text[span[0] : span[1]]), key)


def _replace_block_scalar(text: str, block: str, key: str, value: Any, *, label: str) -> str:
    """Replace one two-space-indented ``key:`` directly under ``block:``."""

    span = _block_span(text, block)
    pattern = re.compile(rf"(?m)^(  {re.escape(key)}:[ \t]*)([^#\r\n]*?)([ \t]*(?:#[^\r\n]*)?)(?=\r?$)")
    body = text[span[0] : span[1]] if span else ""
    if span is None or len(pattern.findall(body)) != 1:
        raise StateError("profile_invalid", f"{label} must contain exactly one {block}.{key}")
    body = pattern.sub(lambda match: f"{match.group(1)}{value}{match.group(3)}", body, count=1)
    return text[: span[0]] + body + text[span[1] :]


def _set_block_scalar(text: str, block: str, key: str, value: Any, *, label: str) -> str:
    """Replace ``key:`` under ``block:``, or add it as the block's first line when absent.

    An older profile's block may predate the key. The added line takes the
    block line's ending; a missing block or a repeated key stays an error.
    """

    span = _block_span(text, block)
    body = text[span[0] : span[1]] if span else ""
    header = re.search(rf"(?m)^{re.escape(block)}:[ \t]*(?:#[^\r\n]*)?(\r?\n)", text)
    first_child = re.search(r"(?m)^([ \t]+)[^\s#]", body)
    two_space = first_child is None or first_child.group(1) == "  "
    if span is None or header is None or not two_space or re.search(rf"(?m)^[ \t]+{re.escape(key)}:", body):
        return _replace_block_scalar(text, block, key, value, label=label)
    return text[: header.end()] + f"  {key}: {value}{header.group(1)}" + text[header.end() :]


def _validate_setup(text: str, state: dict[str, Any]) -> None:
    if _top_scalar(text, "schema_version") not in {"8", "9", "10"}:
        raise StateError("setup_invalid", "setup_profile.yaml schema_version must be 8, 9, or 10")
    required = {
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


def _assert_readable_state(root: Path) -> None:
    try:
        # The readiness checker runs under its parent's held writer lock.
        # Refuse persisted incomplete batches without rejecting that check.
        assert_readable(root, check_lock=False)
    except FileTransactionError as exc:
        raise StateError(exc.category, str(exc)) from exc


def _validated_campaign_state(campaign: Path, *, require_ready: bool = False) -> dict[str, Any]:
    root = _campaign_root(campaign)
    _assert_readable_state(root)
    manifest = load_manifest(root, require_full=require_ready)
    state = _read_json(root / STATE_FILE, STATE_FILE)
    _validate_state(state, manifest, require_ready=require_ready)
    try:
        setup_text = (root / SETUP_FILE).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError) as exc:
        raise StateError("file_missing", f"cannot read {SETUP_FILE}: {exc}") from exc
    _validate_setup(setup_text, state)
    ready_gate = state["gates"]["ready_and_snapshotted"]
    evidence_root = root
    if ready_gate["status"] == "complete":
        _validate_ready_evidence_files(
            root,
            state,
            manifest,
            ready_gate.get("evidence"),
            before_transition=False,
        )
        # Once play begins, stage files are historical materialization
        # evidence. Their immutable snapshot is checked above; the live owners
        # may legitimately change, be consumed, or be retired through play.
        evidence_root = (root / ready_gate["evidence"]["snapshot_ref"]).parent
    if (
        state["stages"]["07_runtime_experience_contract"]["status"] == "complete"
        and _structured_contracts(manifest).get("agent_seats")
    ):
        _file_digest(evidence_root, "play_profile.yaml")
        _validate_materialized_agent_seats(
            (evidence_root / "play_profile.yaml").read_text(encoding="utf-8"), state, manifest
        )
    try:
        summary_text = (root / SUMMARY_FILE).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError) as exc:
        raise StateError("file_missing", f"cannot read {SUMMARY_FILE}: {exc}") from exc
    if not _summary_matches(summary_text, state):
        raise StateError("summary_stale", f"{SUMMARY_FILE} Deep v8 managed section does not match canonical state")
    for stage_id, stage in state["stages"].items():
        if stage["status"] == "complete":
            actual_digest = compute_output_digest(evidence_root, stage["output_refs"])
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
                compute_output_digest(evidence_root, portion["output_refs"])
    _assert_readable_state(root)
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
    _commit_files(state_path.parent, {
        setup_path: setup_text.encode("utf-8"),
        summary_path: summary_text.encode("utf-8"),
        state_path: _json_bytes(state),
    })


def _commit_files(root: Path, changes: dict[Path, bytes]) -> None:
    """Write a small file batch as one rollback-protected transaction."""

    try:
        with campaign_lock(root):
            recover(root)
            commit_files(root, changes, apply_file=_atomic_bytes)
    except FileTransactionError as exc:
        category = "commit_failed" if exc.category == "commit_rolled_back" else exc.category
        raise StateError(category, str(exc)) from exc


@contextmanager
def _mutation_lock(root: Path) -> Iterator[None]:
    try:
        with campaign_lock(root):
            legacy = root / ".session-zero-state.lock"
            if legacy.exists():
                raise StateError("recovery_required", "legacy lock .session-zero-state.lock remains; confirm the old process stopped before removing it")
            recover(root)
            yield
    except FileTransactionError as exc:
        category = "state_busy" if exc.category == "transaction_busy" else exc.category
        raise StateError(category, str(exc)) from exc


def _load_for_mutation(root: Path) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    manifest = load_manifest(root, require_full=True)
    state = _read_json(root / STATE_FILE, STATE_FILE)
    _validate_state(state, manifest)
    # Both files are written back, so they are read with their line endings.
    setup_text = _read_text(root / SETUP_FILE, SETUP_FILE)
    _validate_setup(setup_text, state)
    summary_text = _read_text(root / SUMMARY_FILE, SUMMARY_FILE)
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
            gate["history"] = _archive_entry(gate)
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


def _read_optional(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _play_language(root: Path) -> str:
    """The settled play language code, or "" while it is unset or ``auto``."""

    value = _block_scalar(_read_optional(root / PROFILE_FILE), "narration", "language") or ""
    return lang_pack.normalize_code(value)


def _markdown_section(text: str, heading: str) -> str:
    """The body under the first heading named ``heading`` (any level), up to
    the next heading of the same or a higher level."""

    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", line)
        if match is None or match.group(2).casefold() != heading.casefold():
            continue
        level = len(match.group(1))
        body: list[str] = []
        for following in lines[index + 1 :]:
            next_heading = re.match(r"^(#{1,6})[ \t]", following)
            if next_heading and len(next_heading.group(1)) <= level:
                break
            body.append(following)
        return "\n".join(body)
    return ""


def _table_rows(section: str) -> list[list[str]]:
    """Data rows of the Markdown tables in ``section``, header rows dropped."""

    def cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    def separator(line: str) -> bool:
        return all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells(line))

    lines = [line for line in section.splitlines() if line.strip().startswith("|")]
    rows: list[list[str]] = []
    for index, line in enumerate(lines):
        is_header = index + 1 < len(lines) and separator(lines[index + 1])
        if not separator(line) and not is_header:
            rows.append(cells(line))
    return rows


def _content_boundary_problems(text: str) -> list[str]:
    """Both fixed rows kept, and the two closed-option rows set to an allowed value."""

    rows = _table_rows(_markdown_section(text, CONTENT_SECTION))
    settings = {" ".join(row[0].split()).casefold(): row[1] for row in rows if len(row) >= 2}
    problems: list[str] = []
    for category in FIXED_CONTENT_ROWS:
        if settings.get(category.casefold(), "").casefold() != FIXED_CONTENT_SETTING:
            problems.append(
                f"boundaries.md {CONTENT_SECTION} must keep the fixed row `{category}` "
                f"with the Setting `{FIXED_CONTENT_SETTING}`"
            )
    for category, allowed in CONTENT_SETTINGS.items():
        value = settings.get(category)
        if value is None:
            problems.append(f"boundaries.md {CONTENT_SECTION} is missing its `{category}` row")
        elif value.casefold() not in allowed:
            problems.append(f"the `{category}` setting must be one of: {' | '.join(allowed)} (found `{value}`)")
    return problems


def _anchor_rows(root: Path) -> int:
    """Rows of the price and bounty anchor table that name a value."""

    rows = _table_rows(_markdown_section(_read_optional(root / ANCHOR_FILE), ANCHOR_HEADING))
    return sum(1 for row in rows if len(row) >= 2 and row[0] and row[1])


def _stage_completion_problems(root: Path, stage_id: str) -> list[tuple[str, str]]:
    """Stage materialization the helper can detect without judging meaning."""

    problems: list[tuple[str, str]] = []
    if stage_id == "01_north_star_authority":
        if not _play_language(root):
            problems.append(("play_language_unset", PLAY_LANGUAGE_HINT))
        problems.extend(
            ("content_boundaries_incomplete", message)
            for message in _content_boundary_problems(_read_optional(root / "boundaries.md"))
        )
    if stage_id == "04_thin_world_kernel" and not _anchor_rows(root):
        problems.append((
            "anchor_table_missing",
            f"Stage 4 needs at least one row under {ANCHOR_FILE} ### {ANCHOR_HEADING} "
            "(| Anchor | Value | Notes |): everyday prices and the region's reward or bounty scale",
        ))
    return problems


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
        "play_language": _play_language(_campaign_root(campaign)),
        "fatigue": state["fatigue"],
        "stages": state["stages"],
        "active_extensions": [
            extension_id for extension_id, entry in state["extensions"].items() if entry["status"] == "active"
        ],
        "gates": {gate_id: gate["status"] for gate_id, gate in state["gates"].items()},
    }


def _manifest_decision(manifest: dict[str, Any], decision_id: str) -> tuple[str, dict[str, Any]] | None:
    """The owning stage id and definition of a manifest-declared decision."""

    for stage in manifest["stages"]:
        for definition in stage.get("decisions", []):
            if isinstance(definition, dict) and definition.get("id") == decision_id:
                return stage["id"], definition
    return None


def _decision_entry(
    root: Path, manifest: dict[str, Any], state: dict[str, Any], payload: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Build the candidate ledger entry, reporting every contract problem at once."""

    problems: list[tuple[str, str]] = []
    decisions = _decision_map(state)

    raw_id = payload.get("decision_id")
    decision_id = raw_id.strip() if _nonempty(raw_id) and SAFE_ID.fullmatch(raw_id.strip()) else ""
    if not decision_id:
        problems.append(("input_invalid", "decision_id must be a short stable id"))
    stage_id = payload.get("stage_id") if payload.get("stage_id") in STAGE_IDS else ""
    if not stage_id:
        problems.append(("input_invalid", f"stage_id must be one of: {', '.join(STAGE_IDS)}"))
    status_value, source = payload.get("status"), payload.get("source")
    if not isinstance(status_value, str) or status_value not in DECISION_STATUSES:
        problems.append(("input_invalid", f"status must be one of: {', '.join(sorted(DECISION_STATUSES))}"))
    if not isinstance(source, str) or source not in DECISION_SOURCES:
        problems.append(("input_invalid", f"source must be one of: {', '.join(sorted(DECISION_SOURCES))}"))
    declared = _manifest_decision(manifest, decision_id) if decision_id else None
    if declared and stage_id and declared[0] != stage_id:
        problems.append(("input_invalid", f"decision {decision_id} belongs to stage {declared[0]}"))
    if status_value == "deferred" and declared and not declared[1].get("defer_allowed", False):
        problems.append(("decision_blocked", f"decision {decision_id} cannot be deferred"))

    depends_on = payload.get("depends_on", [])
    if not isinstance(depends_on, list) or any(not _nonempty(item) for item in depends_on):
        problems.append(("input_invalid", "depends_on must be a list of decision ids"))
        depends_on = []
    trigger_tags = payload.get("trigger_tags", [])
    if not isinstance(trigger_tags, list) or any(not _nonempty(tag) for tag in trigger_tags):
        problems.append(("input_invalid", "trigger_tags must be a list of manifest trigger tags"))
        trigger_tags = []
    uncontrolled = [tag for tag in trigger_tags if tag not in manifest.get("controlled_trigger_tags", {})]
    if uncontrolled:
        problems.append(("input_invalid", f"trigger_tags are not manifest trigger tags: {', '.join(uncontrolled)}"))
    if len(depends_on) != len(set(depends_on)) or len(trigger_tags) != len(set(trigger_tags)):
        problems.append(("input_invalid", "decision dependencies and trigger tags must not contain duplicates"))
    missing = sorted(set(depends_on) - set(decisions))
    if missing:
        problems.append(("dependency_missing", f"decision dependencies are missing: {', '.join(missing)}"))
    deferred = sorted(item for item in set(depends_on) & set(decisions) if decisions[item]["status"] == "deferred")
    if deferred:
        problems.append(("dependency_deferred", f"a decision cannot depend on a deferred decision: {', '.join(deferred)}"))
    if decision_id in depends_on:
        problems.append(("input_invalid", f"decision {decision_id} cannot depend on itself"))
    if stage_id:
        later = sorted(
            item for item in set(depends_on) & set(decisions)
            if STAGE_IDS.index(decisions[item]["stage_id"]) > STAGE_IDS.index(stage_id)
        )
        if later:
            problems.append(("dependency_order", f"a decision cannot depend on a later stage: {', '.join(later)}"))

    existing = decisions.get(decision_id)
    if existing is None and stage_id:
        if stage_id != state["current_stage"]:
            problems.append(("stage_order", f"new decisions may only be recorded in the current stage {state['current_stage']}"))
        elif state["stages"][stage_id]["status"] not in {"active", "needs_review"}:
            problems.append(("stage_order", "the target stage is not open for decisions"))
        if stage_id == STAGE_IDS[0] and not _play_language(root):
            problems.append(("play_language_unset", PLAY_LANGUAGE_HINT))
    if existing is not None and stage_id and existing["stage_id"] != stage_id:
        problems.append(("input_invalid", "an existing decision cannot move between stages"))
    approval_gate = APPROVAL_DEPENDENCIES.get(decision_id)
    if approval_gate and state["gates"][approval_gate]["status"] != "complete":
        problems.append(("gate_blocked", f"decision {decision_id} requires gate {approval_gate}"))

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
    if approval_gate:
        entry["approval_basis"] = _approval_basis(state, decision_id)
    if decision_id and stage_id:
        candidate = {**decisions, decision_id: entry}
        problems.extend(
            ("decision_contract", message)
            for message in _structured_decision_problems(candidate, manifest, recorded_id=decision_id)
        )
    if problems:
        raise _problems_error(problems)
    return entry, existing


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

        entry, existing = _decision_entry(root, manifest, state, payload)
        decision_id, stage_id, next_revision = entry["decision_id"], entry["stage_id"], entry["revision"]
        approval_gate = APPROVAL_DEPENDENCIES.get(decision_id)
        if existing is not None:
            ignored = {"created_revision", "revision", "history", "approval_basis"}
            comparable = {key: value for key, value in existing.items() if key not in ignored}
            new_comparable = {key: value for key, value in entry.items() if key not in ignored}
            if comparable == new_comparable and (not approval_gate or _approval_current(state, existing)):
                raise StateError("no_change", f"decision {decision_id} already has that value")
            entry["history"] = _archive_entry(existing)
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


def _require_next_gate_open(state: dict[str, Any], stage_id: str) -> None:
    """Refuse, before anything is written, a completion its next gate would block.

    The gate itself is still recorded separately; this only proves on the
    candidate state that it can pass, so fixing a decision never has to reopen
    a stage that was just completed.
    """

    gate_id = STAGE_GATES.get(stage_id)
    if gate_id is None or state["gates"][gate_id]["status"] == "complete":
        return
    allowed, reason = _gate_prerequisites(state, gate_id)
    if not allowed:
        raise StateError(
            "gate_blocked",
            f"completing {stage_id} would leave {gate_id} blocked: {reason}; "
            "correct the stage decisions first (nothing was written)",
        )


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
        if stage_id == "07_runtime_experience_contract" and _structured_contracts(manifest).get("agent_seats"):
            _file_digest(root, "play_profile.yaml")
            _validate_materialized_agent_seats(
                (root / "play_profile.yaml").read_text(encoding="utf-8"), state, manifest
            )
        if stage_id == "09_first_act_preparation" and state["gates"]["preparation_approved"]["status"] != "complete":
            raise StateError("gate_blocked", "First Act Preparation cannot complete before preparation approval")
        completion_problems = _stage_completion_problems(root, stage_id)
        if completion_problems:
            raise _problems_error(completion_problems)
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
        if is_rematerialization and stage_id != "09_first_act_preparation":
            _invalidate_gates(state, _gate_invalidation_start(stage_id), f"stage {stage_id} rematerialized")
        _require_next_gate_open(state, stage_id)
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
    return (
        decision is not None
        and decision["status"] in {"locked", "defaulted"}
        and (decision_id not in APPROVAL_DEPENDENCIES or _approval_current(state, decision))
    )


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


def _run_full_check(root: Path) -> dict[str, Any]:
    """Run ``check_state.py --scope full --preflight-ready`` in a fresh interpreter."""

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
    if not isinstance(result, dict):
        raise StateError("aggregate_check_failed", "check_state did not return a JSON object")
    if process.returncode != 0 and result.get("ok") is True:
        result["ok"] = False
    return result


def _brief_findings(findings: list[dict[str, Any]], limit: int = 12) -> list[dict[str, str]]:
    return [
        {
            "rule": str(finding.get("rule", "unknown")),
            "message": str(finding.get("message", ""))[:200],
            "path": str(finding.get("path", "")),
        }
        for finding in findings[:limit]
    ]


def _require_zero_errors(result: dict[str, Any], category: str, label: str) -> dict[str, Any]:
    findings = [item for item in result.get("findings", []) if isinstance(item, dict)]
    errors = [item for item in findings if item.get("severity") == "error"]
    if result.get("error_count") != 0 or result.get("ok") is not True or errors:
        rules = [str(item.get("rule", "unknown")) for item in errors]
        rule_suffix = f"; first rules: {', '.join(rules[:8])}" if rules else ""
        raise StateError(
            category,
            f"{label} has {result.get('error_count', 'unknown')} error(s){rule_suffix}",
            details={"findings": _brief_findings(errors)},
        )
    return result


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
    result = _require_zero_errors(_run_full_check(root), "aggregate_check_failed", "candidate-ready aggregate check")
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


def _read_text(path: Path, label: str) -> str:
    """A file's text with its line endings as stored, so a rewrite keeps them.

    The scalar helpers match ``\\r?$``; text read with newline translation
    would turn every CRLF line into LF when it is written back.
    """

    try:
        return path.read_bytes().decode("utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError) as exc:
        raise StateError("file_missing", f"cannot read {label}: {exc}") from exc


def _require_rpg_draft(setup_text: str) -> None:
    """Setup selectors may change only for an RPG that is not ready yet."""

    if _top_scalar(setup_text, "ready_for_play") == "true":
        raise StateError("setup_ready", "setup is ready for play; change settings through the GM configuration workflow")
    experience = _top_scalar(setup_text, "experience_mode") or ""
    if not experience:
        raise StateError("experience_unset", "ask RPG Campaign or AI Companion first and persist experience_mode")
    if experience != "rpg":
        raise StateError("experience_invalid", "this helper covers RPG setups; Companion setup follows companion_setup.md")


def _setup_schema(setup_text: str) -> int:
    try:
        return int(_top_scalar(setup_text, "schema_version") or "")
    except ValueError as exc:
        raise StateError("setup_invalid", "setup schema_version must be an integer") from exc


def _language_change(root: Path, language: str) -> tuple[dict[Path, bytes], str]:
    """The play-profile write that settles ``narration.language``, and its code."""

    code = lang_pack.normalize_code(language)
    if not code:
        raise StateError("input_invalid", "language must be a language code such as tr or en, not auto")
    path = root / PROFILE_FILE
    text = _read_text(path, PROFILE_FILE)
    if _top_scalar(text, "profile_status") == "locked":
        raise StateError("profile_locked", f"{PROFILE_FILE} is locked; change the language through the GM configuration workflow")
    updated = _set_block_scalar(text, "narration", "language", code, label=PROFILE_FILE)
    return ({path: updated.encode("utf-8")} if updated != text else {}), code


def _language_result(code: str) -> dict[str, Any]:
    return {"language": code, "language_pack": code in lang_pack.available_codes()}


def set_depth(campaign: Path, depth: str, *, language: str = "") -> dict[str, Any]:
    """Persist the Player's explicit Session 0 depth for an RPG setup.

    This replaces hand edits of ``setup_profile.yaml``. Deep also initializes
    the ledger mirrors and the managed summary, so the first
    ``record-decision`` finds a consistent workspace. Routing advances no
    revision; changing an already started depth is an explicit migration.
    """

    if depth not in SETUP_DEPTHS:
        raise StateError("input_invalid", f"depth must be one of: {', '.join(SETUP_DEPTHS)}")
    root = _campaign_root(campaign)
    with _mutation_lock(root):
        setup_text = _read_text(root / SETUP_FILE, SETUP_FILE)
        _require_rpg_draft(setup_text)
        minimum = 8 if depth == "deep" else 10
        if _setup_schema(setup_text) < minimum:
            raise StateError(
                "schema_unsupported",
                f"set-depth {depth} needs setup schema_version {minimum} or later; follow the active legacy playbook",
            )
        current = _top_scalar(setup_text, "session_zero_mode") or ""
        started = any(_top_scalar(setup_text, key) not in {None, "", "0"} for key in ("setup_revision", "questions_completed"))
        if current not in {"", depth} and started:
            raise StateError(
                "depth_locked",
                f"setup already records decisions at depth {current}; changing depth is an explicit migration",
            )
        changes: dict[Path, bytes] = {}
        new_setup = setup_text
        # Before the first decision this also heals a partial hand edit (the
        # depth set but status left pending, or a stale question_target).
        if current != depth or not started:
            new_setup = _replace_top_scalar(new_setup, "session_zero_mode", depth)
            new_setup = _replace_top_scalar(new_setup, "status", "in_progress")
            new_setup = _replace_top_scalar(new_setup, "question_target", '""')
        if depth == "deep":
            manifest = load_manifest(root, require_full=True)
            state_path = root / STATE_FILE
            state = _read_json(state_path, STATE_FILE) if state_path.is_file() else initial_state(manifest)
            if not state_path.is_file():
                changes[state_path] = _json_bytes(state)
            _validate_state(state, manifest)
            new_setup = _replace_top_scalar(new_setup, "deep_flow_id", FLOW_ID)
            new_setup = _replace_top_scalar(new_setup, "session_zero_state_path", STATE_FILE)
            new_setup = _setup_candidate(new_setup, state)
            _validate_setup(new_setup, state)
            summary_text = _read_text(root / SUMMARY_FILE, SUMMARY_FILE)
            new_summary = project_session_zero_text(summary_text, state)
            if new_summary != summary_text:
                changes[root / SUMMARY_FILE] = new_summary.encode("utf-8")
        if new_setup != setup_text:
            changes[root / SETUP_FILE] = new_setup.encode("utf-8")
        language_result: dict[str, Any] = {}
        if language:
            language_changes, code = _language_change(root, language)
            changes.update(language_changes)
            language_result = _language_result(code)
        if changes:
            _commit_files(root, changes)
        return {
            "ok": True,
            "operation": "set-depth",
            "depth": depth,
            "changed": sorted(path.relative_to(root).as_posix() for path in changes),
            **language_result,
        }


def set_language(campaign: Path, language: str) -> dict[str, Any]:
    """Settle the play language in ``play_profile.yaml`` ``narration.language``."""

    root = _campaign_root(campaign)
    with _mutation_lock(root):
        _require_rpg_draft(_read_text(root / SETUP_FILE, SETUP_FILE))
        changes, code = _language_change(root, language)
        if changes:
            _commit_files(root, changes)
        return {"ok": True, "operation": "set-language", "changed": bool(changes), **_language_result(code)}


def _optional_state(root: Path) -> dict[str, Any] | None:
    """The ledger for read-only aids, or None when it is missing or unreadable."""

    try:
        return _read_json(root / STATE_FILE, STATE_FILE)
    except StateError:
        return None


def digest(campaign: Path, refs: Any, *, stage_id: str = "") -> dict[str, Any]:
    """Print the output digest of campaign-relative files, optionally owner-checked."""

    root = _campaign_root(campaign)
    output_refs = _refs(refs, "refs")
    if stage_id:
        if stage_id not in STAGE_IDS:
            raise StateError("input_invalid", f"stage_id must be one of: {', '.join(STAGE_IDS)}")
        state = _optional_state(root)
        decisions = _decision_map(state) if state else None
        _validate_stage_output_refs(load_manifest(root, require_full=True), stage_id, output_refs, decisions)
    return {
        "ok": True,
        "operation": "digest",
        "output_refs": output_refs,
        "output_digest": compute_output_digest(root, output_refs),
    }


def _owner_list(manifest: dict[str, Any], owner_ids: list[str]) -> list[dict[str, str]]:
    return [{"owner": owner_id, "path": _campaign_owner_path(manifest, owner_id)} for owner_id in owner_ids]


def _decision_requirements(manifest: dict[str, Any], decision_id: str) -> dict[str, Any]:
    """The value fields and dependencies the helper enforces for one decision."""

    contracts = _structured_contracts(manifest)
    required: dict[str, Any] = {}
    seats = contracts.get("agent_seats", {})
    if seats.get("decision_id") == decision_id:
        required.update(value={"mode": seats.get("modes", [])}, status="locked", source="player")
    authority = contracts.get("creation_authority", {})
    if authority.get("decision_id") == decision_id:
        required.update(value={"mode": list(authority.get("modes", {}))}, status="locked", source="player")
    if decision_id in authority.get("world_generative_decision_ids", []):
        required["when_derived_or_defaulted"] = {
            "depends_on": [authority["decision_id"]],
            "authority_modes": [
                mode for mode, rule in authority.get("modes", {}).items()
                if isinstance(rule, dict) and rule.get("allow_derived_world_generation")
            ],
        }
    research = contracts.get("research", {})
    if research.get("status_decision_id") == decision_id:
        required["value"] = {"status": research.get("statuses", []), "permission": research.get("permissions", [])}
    if research.get("lock_decision_id") == decision_id:
        value: dict[str, Any] = {"risk_accepted": "true | false", "current_scale_lock_permitted": "true | false"}
        if research.get("npc_power_scales"):
            value["npc_power_scale"] = research["npc_power_scales"]
        required.update(value=value, depends_on=[research["status_decision_id"]])
    topology = contracts.get("topology", {})
    topologies = manifest.get("topologies", {})
    if topology.get("intent_decision_id") == decision_id:
        required["value"] = {
            "primary_topology": list(topologies),
            "primary_branch": "only for mixed: one of " + ", ".join(item for item in topologies if item != "mixed"),
        }
    if topology.get("activation_decision_id") == decision_id:
        required.update(
            value={
                "primary_topology": f"the {topology['intent_decision_id']} value",
                "primary_branch": "only for mixed: the Stage 1 primary_branch",
                "build_order": {name: rule.get("build_order") for name, rule in topologies.items()},
            },
            depends_on=[topology["intent_decision_id"]],
            trigger_tags={
                name: rule["activation_trigger"] for name, rule in topologies.items() if rule.get("activation_trigger")
            },
        )
    if decision_id in APPROVAL_DEPENDENCIES:
        required["requires_gate"] = APPROVAL_DEPENDENCIES[decision_id]
    return required


def stage_owners(campaign: Path, stage_id: str) -> dict[str, Any]:
    """List what one stage may reference and what its decisions must carry."""

    if stage_id not in STAGE_IDS:
        raise StateError("input_invalid", f"stage_id must be one of: {', '.join(STAGE_IDS)}")
    root = _campaign_root(campaign)
    manifest = load_manifest(root, require_full=True)
    state = _optional_state(root)
    recorded = _decision_map(state) if state else {}
    owner_ids, patterns = _stage_evidence_contract(manifest, stage_id, recorded or None)
    extensions: dict[str, Any] = {}
    for extension_id, definition in manifest.get("extensions", {}).items():
        if stage_id not in _extension_stage_ids(definition):
            continue
        stage_owner_refs = definition.get("stage_owner_refs", {})
        ids = stage_owner_refs.get(stage_id, definition.get("owner_refs", []))
        entry = (state or {}).get("extensions", {}).get(extension_id, {})
        extensions[extension_id] = {
            "status": entry.get("stages", {}).get(stage_id, {}).get("status", "not_applicable"),
            "depth": entry.get("depth", "not_applicable"),
            "owners": _owner_list(manifest, [item for item in ids if item not in {"setup_progress", "decision_log", "snapshot"}]),
        }
    definition = _stage_definitions(manifest)[stage_id]
    decisions = [
        {
            "decision_id": item["id"],
            "critical": bool(item.get("critical")),
            "defer_allowed": bool(item.get("defer_allowed")),
            "owners": _owner_list(manifest, item.get("owner_refs", [])),
            "recorded": recorded.get(item["id"], {}).get("status"),
            **_decision_requirements(manifest, item["id"]),
        }
        for item in definition.get("decisions", [])
        if isinstance(item, dict)
    ]
    return {
        "ok": True,
        "operation": "stage-owners",
        "stage_id": stage_id,
        "title": STAGE_TITLES[stage_id],
        "prerequisites": definition.get("prerequisites", []),
        "evidence_owners": _owner_list(manifest, owner_ids),
        "evidence_patterns": patterns,
        "extensions": extensions,
        "decisions": decisions,
        "next_gate": STAGE_GATES.get(stage_id, ""),
    }


def _profile_refs(manifest: dict[str, Any]) -> tuple[str, str]:
    contract = manifest["final_readiness_contract"]
    return (
        str(contract["selected_profile_ref"]).removeprefix("campaign/"),
        str(contract["unused_profile_ref"]).removeprefix("campaign/"),
    )


def _set_profile_fields(root: Path, relative: str, fields: dict[str, Any]) -> dict[Path, bytes]:
    path = root / relative
    text = _read_text(path, relative)
    updated = text
    for key, value in fields.items():
        updated = _replace_top_scalar(updated, key, value, label=relative)
    return {path: updated.encode("utf-8")} if updated != text else {}


def _profile_changes(
    root: Path, selected_ref: str, unused_ref: str, revision: int, *, lock: bool
) -> dict[Path, bytes]:
    """Both profiles mirror ``revision``; locking also sets their final statuses."""

    selected: dict[str, Any] = {"source_setup_revision": revision}
    unused: dict[str, Any] = {"source_setup_revision": revision}
    if lock:
        selected["profile_status"] = "locked"
        unused["profile_status"] = "inactive"
    return {**_set_profile_fields(root, selected_ref, selected), **_set_profile_fields(root, unused_ref, unused)}


def _require_clean_preflight(root: Path) -> list[dict[str, Any]]:
    """Zero errors, and none of the warnings readiness does not carry into play.

    Returns the advisory warnings (records in another language), which are
    reported with the result and never block readiness.
    """

    result = _require_zero_errors(_run_full_check(root), "preflight_failed", "draft preflight")
    findings = [item for item in result.get("findings", []) if isinstance(item, dict)]
    blocking = [
        item for item in findings
        if item.get("rule") in ALWAYS_BLOCKING_RULES
        or (item.get("rule") in CALIBRATION_RULES and item.get("severity") == "warning")
    ]
    if blocking:
        rules = sorted({str(item["rule"]) for item in blocking})
        hint = (
            "calibrate the NPC cards to the accepted scale, "
            "and correct any history that implies a minor in a romantic or sexual context"
        )
        raise StateError(
            "preflight_blocked",
            f"draft preflight has warnings readiness does not carry into play ({', '.join(rules)}): {hint}",
            details={"findings": _brief_findings(blocking)},
        )
    return [item for item in findings if item.get("rule") in ADVISORY_RULES and item.get("severity") == "warning"]


def _finalize_steps(root: Path, operation_id: str, stop_after: str) -> dict[str, Any]:
    """Run the readiness steps in order; ``done`` records each completed step."""

    manifest = load_manifest(root, require_full=True)
    selected_ref, unused_ref = _profile_refs(manifest)
    label = manifest["final_readiness_contract"]["snapshot_label"]
    done: list[str] = []
    progress: dict[str, Any] = {"completed_steps": done}

    def finished(step: str) -> bool:
        done.append(step)
        return step == stop_after

    def step_error(exc: StateError, step: str) -> StateError:
        exc.details.update(failed_step=step, completed_steps=list(done))
        if "advisories" in progress:
            exc.details.setdefault("advisories", progress["advisories"])
        exc.details.setdefault("setup_revision", _read_json(root / STATE_FILE, STATE_FILE)["setup_revision"])
        return exc

    state = _read_json(root / STATE_FILE, STATE_FILE)
    if state["gates"]["draft_preflight_passed"]["status"] != "complete":
        step = "preflight"
        try:
            allowed, reason = _gate_prerequisites(state, "draft_preflight_passed")
            if not allowed:
                raise StateError("gate_blocked", reason)
            # Both profiles mirror the current revision during preflight; the
            # full check refuses a stale revision on either one.
            changes = _profile_changes(root, selected_ref, unused_ref, state["setup_revision"], lock=False)
            if changes:
                _commit_files(root, changes)
            advisories = _require_clean_preflight(root)
            if advisories:
                progress["advisories"] = _brief_findings(advisories)
            if finished(step):
                return progress
            step = "draft_preflight_passed"
            preparation = state["gates"]["preparation_approved"]["output_digest"]
            record_gate(root, {
                "operation_id": f"{operation_id[:96]}.preflight",
                "expected_revision": state["setup_revision"],
                "gate_id": "draft_preflight_passed",
                "input_digest": preparation,
                "output_digest": preparation,
                "decided_by": "coordinator",
                "evidence": {},
            })
        except StateError as exc:
            raise step_error(exc, step) from None
        if finished(step):
            return progress
    else:
        progress["resumed_after"] = "draft_preflight_passed"
        if stop_after in FINALIZE_STEPS[:2]:
            return progress

    state = _read_json(root / STATE_FILE, STATE_FILE)
    revision = state["setup_revision"]
    step = "lock_profiles"
    try:
        changes = _profile_changes(root, selected_ref, unused_ref, revision, lock=True)
        if changes:
            _commit_files(root, changes)
        if finished(step):
            return progress
        step = "snapshot"
        created = snapshot_tool.create_snapshot(root, label)
        if not created.get("ok"):
            raise StateError("snapshot_failed", f"session-zero-start snapshot failed: {created.get('error', 'unknown')}")
        snapshot_dir = Path(created["snapshot_path"]).resolve()
        snapshot_ref = (snapshot_dir / "snapshot_manifest.json").relative_to(root).as_posix()
        progress["snapshot_ref"] = snapshot_ref
        if finished(step):
            return progress
        step = "ready_evidence"
        stamp = snapshot_dir.name.split("_", 1)[0]
        evidence_result = prepare_ready_evidence(
            root,
            operation_id=f"{operation_id[:96]}.evidence.{stamp}",
            expected_revision=revision,
            snapshot_ref=snapshot_ref,
            aggregate_check_ref=f"snapshots/{snapshot_dir.name}_readiness.json",
        )
        evidence = evidence_result["evidence"]
        progress["aggregate_check_ref"] = evidence["aggregate_check_ref"]
        if finished(step):
            return progress
        step = "ready_and_snapshotted"
        record_gate(root, {
            "operation_id": f"{operation_id[:96]}.ready.{stamp}",
            "expected_revision": revision,
            "gate_id": "ready_and_snapshotted",
            "input_digest": state["gates"]["draft_preflight_passed"]["output_digest"],
            "output_digest": evidence["snapshot_digest"],
            "decided_by": "coordinator",
            "evidence": evidence,
        })
        progress["evidence"] = evidence
        finished(step)
    except StateError as exc:
        raise step_error(exc, step) from None
    return progress


def finalize(
    campaign: Path,
    *,
    operation_id: str,
    expected_revision: int,
    stop_after: str = "",
) -> dict[str, Any]:
    """Run the Deep readiness sequence in one call.

    Steps: preflight, ``draft_preflight_passed``, profile locks, the
    session-zero-start snapshot, the ready evidence, and
    ``ready_and_snapshotted``. It stops at the first failing step with that
    step's typed error and the steps already completed. A later call resumes:
    a passed preflight gate is never recorded again, and a failed snapshot or
    evidence step is retried with a fresh snapshot. Preflight warnings that do
    not block readiness (records in another language) come back under
    ``advisories``.
    """

    root = _campaign_root(campaign)
    operation_id = _safe_id(operation_id, "operation_id")
    if not _strict_int(expected_revision):
        raise StateError("input_invalid", "expected_revision must be a non-negative integer")
    if stop_after and stop_after not in FINALIZE_STEPS:
        raise StateError("input_invalid", f"stop_after must be one of: {', '.join(FINALIZE_STEPS)}")
    with _mutation_lock(root):
        state = _validated_campaign_state(root)
        base = {"operation": "finalize", "operation_id": operation_id}
        if state["gates"]["ready_and_snapshotted"]["status"] == "complete":
            return {"ok": True, "idempotent": True, **base, "setup_revision": state["setup_revision"]}
        if expected_revision != state["setup_revision"]:
            raise StateError(
                "stale_revision",
                f"expected revision {expected_revision}, current revision is {state['setup_revision']}",
            )
        progress = _finalize_steps(root, operation_id, stop_after)
        state = _read_json(root / STATE_FILE, STATE_FILE)
        ready = state["gates"]["ready_and_snapshotted"]["status"] == "complete"
        result = {"ok": True, "idempotent": False, **base, "setup_revision": state["setup_revision"], **progress}
        last = (progress["completed_steps"] or [progress.get("resumed_after", "")])[-1]
        result["next"] = (
            "send the OOC line and the opening narration as text, then one commit"
            if ready
            else f"finish the work after {last}, then run finalize again with the current revision"
        )
        return result


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

    depth = subparsers.add_parser("set-depth", help="Persist the Player's explicit RPG Session 0 depth")
    depth.add_argument("--depth", choices=SETUP_DEPTHS, required=True)
    depth.add_argument("--language", default="", help="Also settle the play language (a code such as tr or en)")

    language = subparsers.add_parser("set-language", help="Settle the play language (narration.language)")
    language.add_argument("--language", required=True)

    digest_parser = subparsers.add_parser("digest", help="Print the output digest of campaign-relative files")
    digest_parser.add_argument("--refs-json", required=True)
    digest_parser.add_argument("--stage-id", default="", help="Also check the refs against this stage's owners")

    owners = subparsers.add_parser("stage-owners", help="List a stage's owner files and decision contracts")
    owners.add_argument("--stage-id", required=True)

    final = subparsers.add_parser("finalize", help="Run the Deep readiness sequence in one call")
    final.add_argument("--operation-id", required=True)
    final.add_argument("--expected-revision", type=int, required=True)
    final.add_argument("--stop-after", choices=FINALIZE_STEPS, default="")
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
        elif args.command == "record-gate":
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
        elif args.command == "set-depth":
            result = set_depth(campaign, args.depth, language=args.language)
        elif args.command == "set-language":
            result = set_language(campaign, args.language)
        elif args.command == "digest":
            result = digest(campaign, _json_value(args.refs_json, "--refs-json"), stage_id=args.stage_id)
        elif args.command == "stage-owners":
            result = stage_owners(campaign, args.stage_id)
        else:
            result = finalize(
                campaign,
                operation_id=args.operation_id,
                expected_revision=args.expected_revision,
                stop_after=args.stop_after,
            )
    except StateError as exc:
        result = {"ok": False, "operation": args.command, "error_category": exc.category, "error": str(exc)}
        if exc.problems:
            result["problems"] = exc.problems
        result.update({key: value for key, value in exc.details.items() if key not in result})
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())

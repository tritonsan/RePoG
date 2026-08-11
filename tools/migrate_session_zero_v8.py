"""Migrate eligible RePoG RPG Deep Session 0 campaigns from v7 to v8.

The migration is deliberately structural.  It preserves every existing
campaign/fiction file, records reliable legacy decisions in the v8 ledger,
and leaves ambiguous cross-stage material for player review.  A substantive
in-progress setup requires a full campaign snapshot before ``--apply``;
pending/routing-only setups can be migrated without one.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


FLOW_ID = "rpg_deep_v8"
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

# A legacy module can be preserved as a decision without pretending that it
# satisfies every new v8 prerequisite.  ``affected`` names every v8 stage that
# must be reviewed where the old module crossed new ownership boundaries.
MODULE_MAP: dict[int, dict[str, Any]] = {
    1: {"stage": STAGE_IDS[0], "slug": "campaign_promise_player_fantasy"},
    2: {"stage": STAGE_IDS[1], "slug": "research_need_source_boundary"},
    3: {"stage": STAGE_IDS[0], "slug": "agency_authorship_content_boundaries"},
    4: {"stage": STAGE_IDS[2], "slug": "character_identity_desire_why_now"},
    5: {
        "stage": STAGE_IDS[4],
        "slug": "competence_limitation_social_position_change",
        "affected": (STAGE_IDS[2], STAGE_IDS[4]),
    },
    6: {
        "stage": STAGE_IDS[6],
        "slug": "play_system_contract",
        "affected": (STAGE_IDS[4], STAGE_IDS[6]),
    },
    7: {"stage": STAGE_IDS[6], "slug": "presentation_visual_contract"},
    8: {"stage": STAGE_IDS[1], "slug": "canon_policy"},
    9: {"stage": STAGE_IDS[3], "slug": "palette"},
    10: {"stage": STAGE_IDS[3], "slug": "world_truths_operating_model"},
    11: {
        "stage": STAGE_IDS[3],
        "slug": "scale_everyday_life_access_routes",
        "affected": (STAGE_IDS[3], STAGE_IDS[5]),
    },
    12: {"stage": STAGE_IDS[5], "slug": "independent_issues_world_dynamics"},
    13: {"stage": STAGE_IDS[5], "slug": "factions_institutions"},
    14: {"stage": STAGE_IDS[5], "slug": "faces_places_independent_relationships"},
    15: {"stage": STAGE_IDS[7], "slug": "progression_rewards"},
    16: {"stage": STAGE_IDS[7], "slug": "character_world_reciprocity"},
    17: {"stage": STAGE_IDS[8], "slug": "starting_situation_design"},
    18: {
        "stage": STAGE_IDS[0],
        "slug": "continuity_ownership_preparation_contract",
        "affected": (STAGE_IDS[0], STAGE_IDS[6], STAGE_IDS[8]),
    },
    19: {
        "stage": STAGE_IDS[8],
        "slug": "reciprocity_design_review",
        "affected": (STAGE_IDS[8],),
        "approval": True,
    },
    20: {
        "stage": STAGE_IDS[8],
        "slug": "integrated_materialized_preparation_review",
        "affected": (STAGE_IDS[8],),
        "approval": True,
    },
    21: {
        "stage": STAGE_IDS[8],
        "slug": "preparation_approval",
        "affected": (STAGE_IDS[8],),
        "approval": True,
    },
}

EXTENSION_STAGES = {
    "character_interior": (STAGE_IDS[2],),
    "world_fabric": (STAGE_IDS[3],),
    "mechanics_detail": (STAGE_IDS[4],),
    "location_network": (STAGE_IDS[5],),
    "faction_information": (STAGE_IDS[5],),
    "group": (STAGE_IDS[5],),
    "character_embedding": (STAGE_IDS[5],),
    "advancement_detail": (STAGE_IDS[7],),
    "campaign_architecture": (STAGE_IDS[7], STAGE_IDS[8]),
}

LEGACY_PACK_EXTENSIONS = {
    "character_foundation": ("character_interior", "character_embedding"),
    "world_fabric": ("world_fabric",),
    "mechanics_progression": ("mechanics_detail", "advancement_detail"),
    "location_network": ("location_network",),
    "faction_information": ("faction_information",),
    "group": ("group",),
    "campaign_architecture": ("campaign_architecture",),
}

AMBIGUOUS_PACK_STAGES = {
    "character_foundation": (STAGE_IDS[2], STAGE_IDS[5]),
    "mechanics_progression": (STAGE_IDS[4], STAGE_IDS[7]),
    "campaign_architecture": (STAGE_IDS[7], STAGE_IDS[8]),
}

RESOLVED_MODULE_STATUSES = {
    "locked": "locked",
    "defaulted": "defaulted",
    "defer": "deferred",
    "deferred": "deferred",
    "locked_with_open_questions": "locked",
}


def _clean(value: str) -> str:
    return value.strip().strip("'\"`")


def _top_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if match:
            values[match.group(1)] = _clean(match.group(2))
    return values


def _integer(value: object, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _boolean(value: object) -> bool:
    return str(value).strip().casefold() in {"true", "yes", "1"}


def _inline_list(value: str) -> list[str]:
    value = value.strip()
    if not value or value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [_clean(item) for item in value.split(",") if _clean(item)]


def _top_list(text: str, key: str) -> list[str]:
    inline = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    if not inline:
        return []
    value = inline.group(1).strip()
    if value:
        return _inline_list(value)
    tail = text[inline.end() :]
    end = re.search(r"(?m)^\S", tail)
    body = tail[: end.start()] if end else tail
    return [
        _clean(match.group(1))
        for match in re.finditer(r"(?m)^\s+-\s*(.*?)\s*$", body)
        if _clean(match.group(1))
    ]


def _module_statuses(text: str) -> dict[int, dict[str, str]]:
    heading = re.search(
        r"(?im)^##\s+RPG Standard / Deep Reciprocity Module Status\s*$", text
    )
    if not heading:
        return {}
    tail = text[heading.end() :]
    end = re.search(r"(?m)^##\s+", tail)
    block = tail[: end.start()] if end else tail
    statuses: dict[int, dict[str, str]] = {}
    for match in re.finditer(
        r"(?m)^-\s+(\d+)\.\s+(.+?):\s*([a-z][a-z0-9_-]*)\s*$", block
    ):
        statuses[int(match.group(1))] = {
            "label": match.group(2).strip(),
            "status": match.group(3).casefold(),
        }
    return statuses


def _replace_top_scalar(text: str, key: str, value: str) -> str:
    pattern = rf"(?m)^{re.escape(key)}:\s*.*?$"
    if re.search(pattern, text):
        return re.sub(pattern, f"{key}: {value}", text, count=1)
    suffix = "" if text.endswith("\n") else "\n"
    return text + suffix + f"{key}: {value}\n"


def _replace_top_list(text: str, key: str, values: list[str]) -> str:
    rendered = "[" + ", ".join(values) + "]"
    pattern = rf"(?ms)^{re.escape(key)}:\s*(?:\[[^\n]*\]|[^\n]*)\n(?:\s+-\s*[^\n]*\n)*"
    if re.search(pattern, text):
        return re.sub(pattern, f"{key}: {rendered}\n", text, count=1)
    suffix = "" if text.endswith("\n") else "\n"
    return text + suffix + f"{key}: {rendered}\n"


def _load_state_module() -> Any | None:
    """Load the sibling state helper when present, without making it mandatory."""

    path = Path(__file__).with_name("session_zero_state.py")
    if not path.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("repog_session_zero_state", path)
        if not spec or not spec.loader:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except (ImportError, OSError, AttributeError):
        return None


def _fallback_state(setup_revision: int, *, active: bool) -> dict[str, Any]:
    stages: dict[str, dict[str, Any]] = {}
    for index, stage_id in enumerate(STAGE_IDS):
        status = "active" if active and index == 0 else "not_started"
        stages[stage_id] = {
            "status": status,
            "completed_revision": None,
            "output_refs": [],
            "output_digest": "",
            "invalidation_reason": "",
        }
    gates = {
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
    }
    return {
        "schema_version": 1,
        "flow_id": FLOW_ID,
        "setup_revision": setup_revision,
        "current_stage": STAGE_IDS[0] if active else "",
        "stages": stages,
        "decisions": [],
        "extensions": {
            name: _empty_extension(stage_ids)
            for name, stage_ids in EXTENSION_STAGES.items()
        },
        "outputs": {},
        "gates": gates,
        "operation_registry": {},
        "last_operation": None,
        "fatigue": {
            "decision_count": 0,
            "decisions_since_checkpoint": 0,
            "last_checkpoint_revision": 0,
            "last_checkpoint_decision_count": 0,
        },
    }


def _initial_state(campaign: Path, setup_revision: int, *, active: bool) -> dict[str, Any]:
    helper = _load_state_module()
    if helper is not None:
        factory = getattr(helper, "initial_state", None)
        load_manifest = getattr(helper, "load_manifest", None)
        if callable(factory) and callable(load_manifest):
            try:
                state = factory(load_manifest(campaign))
            except (OSError, ValueError):
                state = None
            if isinstance(state, dict) and state.get("flow_id") == FLOW_ID:
                state["setup_revision"] = setup_revision
                if not active:
                    state["current_stage"] = STAGE_IDS[0]
                return state
    return _fallback_state(setup_revision, active=active)


def _set_stage_status(
    state: dict[str, Any], stage_id: str, status: str, revision: int, reason: str = ""
) -> None:
    stages = state.setdefault("stages", {})
    stage = stages.setdefault(stage_id, {})
    stage["status"] = status
    stage["completed_revision"] = revision if status == "complete" else None
    stage.setdefault("output_refs", [])
    stage.setdefault("output_digest", "")
    stage["invalidation_reason"] = reason


def _empty_extension(stage_ids: tuple[str, ...]) -> dict[str, Any]:
    return {
        "status": "not_applicable",
        "depth": "not_applicable",
        "stage_ids": list(stage_ids),
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


def _reset_extensions(state: dict[str, Any]) -> None:
    state["extensions"] = {
        name: _empty_extension(stage_ids)
        for name, stage_ids in EXTENSION_STAGES.items()
    }


def _decision(
    module_number: int,
    label: str,
    legacy_status: str,
    setup_revision: int,
) -> dict[str, Any]:
    mapping = MODULE_MAP[module_number]
    status = RESOLVED_MODULE_STATUSES[legacy_status]
    source = "player"
    if status == "defaulted":
        source = "defaulted"
    elif status == "deferred":
        source = "deferred"
    decision_revision = max(1, setup_revision)
    return {
        "decision_id": f"v7_module_{module_number:02d}_{mapping['slug']}",
        "stage_id": mapping["stage"],
        "status": status,
        "source": source,
        "value": f"Preserved from v7 module {module_number}: {label}",
        "depends_on": [],
        # Migration evidence never activates a v8 extension. Controlled tags
        # are recorded only by the live v8 interview after player review.
        "trigger_tags": [],
        "created_revision": decision_revision,
        "revision": decision_revision,
    }


def _append_legacy_label_decisions(
    state: dict[str, Any], labels: list[str], *, status: str, setup_revision: int
) -> None:
    existing = {item.get("decision_id") for item in state.get("decisions", []) if isinstance(item, dict)}
    for index, label in enumerate(labels, start=1):
        slug = re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_") or str(index)
        decision_id = f"v7_{status}_{slug}"
        if decision_id in existing:
            continue
        state.setdefault("decisions", []).append(
            {
                "decision_id": decision_id,
                "stage_id": STAGE_IDS[0],
                "status": status,
                "source": status,
                "value": f"Preserved legacy {status} label: {label}",
                "depends_on": [],
                "trigger_tags": [],
                "created_revision": max(1, setup_revision),
                "revision": max(1, setup_revision),
            }
        )


def _build_migrated_state(
    campaign: Path,
    setup: dict[str, str],
    setup_text: str,
    module_statuses: dict[int, dict[str, str]],
    *,
    routing_only: bool,
) -> tuple[dict[str, Any], list[str], int]:
    revision = max(0, _integer(setup.get("setup_revision"), 0))
    state = _initial_state(campaign, revision, active=True)
    state["schema_version"] = 1
    state["flow_id"] = FLOW_ID
    state["setup_revision"] = revision
    state["current_stage"] = STAGE_IDS[0]
    state.setdefault("decisions", [])
    state["decisions"] = []
    state.setdefault("outputs", {})
    state["outputs"] = {}
    state["operation_registry"] = {}
    state["last_operation"] = None
    _reset_extensions(state)

    review_stages: set[str] = set()
    mapped = 0
    if not routing_only:
        for number in sorted(module_statuses):
            legacy = module_statuses[number]
            legacy_status = legacy["status"]
            if number not in MODULE_MAP or legacy_status not in RESOLVED_MODULE_STATUSES:
                continue
            mapping = MODULE_MAP[number]
            if mapping.get("approval"):
                # V8 approvals are digest-bound gates, not reusable content
                # decisions. In particular, the old standalone integrated
                # review has no v8 decision counterpart.
                review_stages.update(mapping.get("affected", (STAGE_IDS[8],)))
                continue
            state["decisions"].append(
                _decision(number, legacy["label"], legacy_status, revision)
            )
            mapped += 1
            affected = mapping.get("affected", ())
            if affected or legacy_status == "locked_with_open_questions":
                review_stages.update(affected or (mapping["stage"],))

        defaults = _top_list(setup_text, "defaulted_decisions")
        deferred = _top_list(setup_text, "deferred_decisions")
        _append_legacy_label_decisions(
            state, defaults, status="defaulted", setup_revision=revision
        )
        _append_legacy_label_decisions(
            state, deferred, status="deferred", setup_revision=revision
        )
        if defaults or deferred:
            review_stages.add(STAGE_IDS[0])

    activated = set(_top_list(setup_text, "activated_packs"))
    completed = set(_top_list(setup_text, "completed_packs"))
    defaulted = set(_top_list(setup_text, "defaulted_packs"))
    for legacy_name, extension_names in LEGACY_PACK_EXTENSIONS.items():
        if legacy_name in defaulted:
            legacy_status = "defaulted"
        elif legacy_name in completed:
            legacy_status = "complete"
        elif legacy_name in activated:
            legacy_status = "active"
        else:
            legacy_status = "not_applicable"
        if legacy_status != "not_applicable":
            primary_stage = EXTENSION_STAGES[extension_names[0]][0]
            decision_status = "defaulted" if legacy_status == "defaulted" else "locked"
            state["decisions"].append(
                {
                    "decision_id": f"v7_pack_{legacy_name}",
                    "stage_id": primary_stage,
                    "status": decision_status,
                    "source": "defaulted" if decision_status == "defaulted" else "derived",
                    "value": (
                        f"Preserved v7 pack lifecycle: {legacy_name} was {legacy_status}; "
                        "review before activating its v8 extension mapping."
                    ),
                    "depends_on": [],
                    "trigger_tags": [],
                    "created_revision": max(1, revision),
                    "revision": max(1, revision),
                }
            )
            for extension_name in extension_names:
                review_stages.update(EXTENSION_STAGES[extension_name])
        if legacy_status != "not_applicable" and legacy_name in AMBIGUOUS_PACK_STAGES:
            review_stages.update(AMBIGUOUS_PACK_STAGES[legacy_name])

    # Source Grounding is no longer an extension. Completed/defaulted work is
    # preserved as core Stage-02 evidence; unresolved work reopens that stage.
    source_status = None
    if "source_grounding" in defaulted:
        source_status = "defaulted"
    elif "source_grounding" in completed:
        source_status = "locked"
    elif "source_grounding" in activated:
        review_stages.add(STAGE_IDS[1])
    if source_status:
        state["decisions"].append(
            {
                "decision_id": "v7_pack_source_grounding",
                "stage_id": STAGE_IDS[1],
                "status": source_status,
                "source": "defaulted" if source_status == "defaulted" else "derived",
                "value": "Preserved Stage-02 evidence from the v7 Source Grounding pack.",
                "depends_on": [],
                "trigger_tags": [],
                "created_revision": max(1, revision),
                "revision": max(1, revision),
            }
        )

    if routing_only:
        _set_stage_status(state, STAGE_IDS[0], "active", revision)
    else:
        progressed_stages = {
            item["stage_id"]
            for item in state["decisions"]
            if isinstance(item, dict) and item.get("stage_id") in STAGE_IDS
        }
        for stage_id in STAGE_IDS:
            if stage_id in review_stages:
                _set_stage_status(
                    state,
                    stage_id,
                    "needs_review",
                    revision,
                    "v7 material crossed v8 stage ownership or approval boundaries",
                )
            elif stage_id in progressed_stages:
                _set_stage_status(
                    state,
                    stage_id,
                    "needs_review",
                    revision,
                    "v7 decision preserved; v8 completion evidence requires review",
                )
            else:
                _set_stage_status(state, stage_id, "not_started", 0)

        # A sequential flow cannot silently skip an earlier unreviewed stage.
        current = next(
            (
                stage_id
                for stage_id in STAGE_IDS
                if state["stages"][stage_id].get("status") != "complete"
            ),
            STAGE_IDS[-1],
        )
        state["current_stage"] = current
        if state["stages"][current].get("status") == "not_started":
            _set_stage_status(state, current, "active", revision)

    gates = state.setdefault("gates", {})
    for gate_id in GATE_IDS:
        gate = gates.setdefault(gate_id, {})
        gate.update(
            {
                "status": "pending",
                "revision": None,
                "input_digest": "",
                "output_digest": "",
                "decided_by": "",
                "evidence": {},
                "invalidation_reason": "cleared by v7 to v8 migration",
            }
        )

    decision_count = len(state["decisions"])
    checkpoint = max(0, _integer(setup.get("last_checkpoint"), 0))
    fatigue = state.setdefault("fatigue", {})
    fatigue.update(
        {
            "decision_count": decision_count,
            "decisions_since_checkpoint": max(0, decision_count - min(checkpoint, decision_count)),
            "last_checkpoint_revision": revision if checkpoint else 0,
            "last_checkpoint_decision_count": min(checkpoint, decision_count),
        }
    )
    return state, sorted(review_stages), len(state["decisions"])


def _substantive_progress(
    setup: dict[str, str], setup_text: str, statuses: dict[int, dict[str, str]]
) -> bool:
    if _integer(setup.get("questions_completed"), 0) > 0:
        return True
    if any(item["status"] != "open" for item in statuses.values()):
        return True
    for key in (
        "defaulted_decisions",
        "deferred_decisions",
        "activated_packs",
        "completed_packs",
        "defaulted_packs",
    ):
        if _top_list(setup_text, key):
            return True
    return any(
        setup.get(key, "").casefold() not in {"", "null", "none"}
        for key in (
            "design_direction_approved_revision",
            "preparation_approved_revision",
        )
    )


def _managed_stage_summary(state: dict[str, Any]) -> str:
    decisions = [item for item in state.get("decisions", []) if isinstance(item, dict)]
    extensions = state.get("extensions", {})
    gates = state.get("gates", {})
    fatigue = state.get("fatigue", {})
    completed_stages = sum(
        isinstance(item, dict) and item.get("status") == "complete"
        for item in state.get("stages", {}).values()
    )
    active_extensions = [
        f"{name} ({item.get('status')})"
        for name, item in extensions.items()
        if isinstance(item, dict) and item.get("status") != "not_applicable"
    ]
    defaulted = [item.get("decision_id", "") for item in decisions if item.get("status") == "defaulted"]
    deferred = [item.get("decision_id", "") for item in decisions if item.get("status") == "deferred"]
    current_gate_id = next(
        (
            gate_id
            for gate_id in GATE_IDS
            if not isinstance(gates.get(gate_id), dict)
            or gates[gate_id].get("status") != "complete"
        ),
        GATE_IDS[-1],
    )
    current_gate = gates.get(current_gate_id, {})
    design_gate = gates.get("design_direction_approved", {})
    preparation_gate = gates.get("preparation_approved", {})
    return "\n".join(
        (
            "## RPG Deep v8 Stage Summary",
            "",
            "This is a managed, human-readable projection of `session_zero_state.json` for",
            "schema-v8 `rpg + deep`. Do not edit stage, extension, decision, or gate state",
            "here. Quick, Standard, Companion, and schema-v7 Deep ignore this section.",
            "",
            f"- Flow: {state.get('flow_id', FLOW_ID)}",
            f"- Source setup revision: {state.get('setup_revision', 0)}",
            f"- Current stage: {state.get('current_stage', STAGE_IDS[0])}",
            f"- Completed decisions: {len(decisions)}",
            f"- Last stage checkpoint: {fatigue.get('last_checkpoint_decision_count', 0)}",
            f"- Stage progress: {completed_stages}/{len(STAGE_IDS)}",
            f"- Active extensions: {', '.join(active_extensions) if active_extensions else 'none'}",
            f"- Defaulted decisions: {', '.join(defaulted) if defaulted else 'none'}",
            f"- Deferred decisions: {', '.join(deferred) if deferred else 'none'}",
            f"- Current gate: {current_gate_id} ({current_gate.get('status', 'pending')})",
            "- Player approvals: "
            f"design {design_gate.get('status', 'pending')}; "
            f"preparation {preparation_gate.get('status', 'pending')}",
        )
    ) + "\n"


def _update_managed_summary(text: str, state: dict[str, Any]) -> str:
    helper = _load_state_module()
    projector = (
        getattr(helper, "project_session_zero_text", None)
        if helper is not None
        else None
    )
    if callable(projector):
        return projector(text, state)

    # Standalone fallback for an older distribution that has the migrator but
    # not the canonical state helper. Current packages always take the branch
    # above so the state validator and projection cannot drift apart.
    rendered = _managed_stage_summary(state).rstrip() + "\n"
    pattern = re.compile(
        r"(?ms)^## RPG Deep v8 Stage Summary\s*$.*?(?=^##\s+|\Z)"
    )
    matches = list(pattern.finditer(text))
    if len(matches) > 1:
        raise ValueError("session_zero.md contains more than one managed Deep v8 summary")
    if matches:
        before = text[: matches[0].start()].rstrip()
        after = text[matches[0].end() :].lstrip("\r\n")
        return before + "\n\n" + rendered + ("\n" + after if after else "")
    prefix = text.rstrip()
    return (prefix + "\n\n" if prefix else "") + rendered


def _has_snapshot(campaign: Path) -> bool:
    root = campaign / "snapshots"
    if not root.is_dir():
        return False
    required = {
        path.relative_to(campaign).as_posix()
        for path in campaign.rglob("*")
        if path.is_file()
        and root not in path.parents
        and (campaign / ".repog-transactions") not in path.parents
    }
    for manifest_path in root.glob("*/snapshot_manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        files = manifest.get("files") if isinstance(manifest, dict) else None
        if not isinstance(files, list):
            continue
        covered: set[str] = set()
        for item in files:
            relative = item.get("path") if isinstance(item, dict) else item
            if isinstance(relative, str):
                covered.add(relative.replace("\\", "/").removeprefix("campaign/"))
        if required and required <= covered:
            return True
    return False


def _snapshot_command(campaign: Path) -> list[str]:
    return [
        sys.executable or "python",
        str(Path(__file__).with_name("snapshot.py")),
        str(campaign),
        "--label",
        "before_session_zero_v8",
    ]


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _apply_all(planned: dict[Path, str], *, validate: Any | None = None) -> None:
    originals = {path: path.read_bytes() if path.is_file() else None for path in planned}
    written: list[Path] = []
    try:
        for path, text in planned.items():
            _atomic_text(path, text)
            written.append(path)
        if callable(validate):
            validate()
    except Exception:
        for path in reversed(written):
            original = originals[path]
            if original is None:
                path.unlink(missing_ok=True)
            else:
                _atomic_text(path, original.decode("utf-8"))
        raise


def _validate_applied_state(campaign: Path) -> None:
    helper = _load_state_module()
    validator = getattr(helper, "validate_campaign_state", None) if helper is not None else None
    if not callable(validator):
        return
    result = validator(campaign)
    if not isinstance(result, dict) or result.get("ok") is not True:
        findings = result.get("findings", []) if isinstance(result, dict) else []
        messages = [str(item.get("message", "state validation failed")) for item in findings if isinstance(item, dict)]
        raise ValueError("; ".join(messages) or "migrated Deep v8 state failed validation")


def _no_migration(
    campaign: Path, mode: str, reason: str, source_schema: int | None = None
) -> dict[str, Any]:
    return {
        "ok": True,
        "mode": mode,
        "campaign_path": str(campaign),
        "eligible": False,
        "changed": False,
        "migrated": False,
        "reason": reason,
        "source_schema_version": source_schema,
        "target_schema_version": 8,
        "changed_files": [],
        "needs_review": [],
    }


def migrate(campaign_path: Path, *, apply: bool = False) -> dict[str, Any]:
    campaign = campaign_path.resolve()
    mode = "apply" if apply else "dry-run"
    if not campaign.is_dir():
        return {
            "ok": False,
            "mode": mode,
            "error": "campaign_path_not_found",
            "campaign_path": str(campaign),
        }

    setup_path = campaign / "setup_profile.yaml"
    session_path = campaign / "session_zero.md"
    state_path = campaign / "session_zero_state.json"
    try:
        setup_text = setup_path.read_text(encoding="utf-8")
        setup = _top_values(setup_text)
        schema = _integer(setup.get("schema_version"), -1)
    except (OSError, UnicodeError) as exc:
        return {
            "ok": False,
            "mode": mode,
            "error": "migration_read_failed",
            "message": str(exc),
            "campaign_path": str(campaign),
        }

    if schema == 8:
        if not state_path.is_file() and setup.get("session_zero_mode", "").casefold() == "deep":
            return {
                "ok": False,
                "mode": mode,
                "error": "v8_state_missing",
                "message": "Deep schema-v8 setup is missing session_zero_state.json.",
                "campaign_path": str(campaign),
            }
        return _no_migration(campaign, mode, "already_v8", schema)
    if schema != 7:
        return _no_migration(campaign, mode, "unsupported_schema", schema)

    experience = setup.get("experience_mode", "").casefold()
    depth = setup.get("session_zero_mode", "").casefold()
    status = setup.get("status", "pending").casefold()
    ready = _boolean(setup.get("ready_for_play", "false"))

    if ready or status == "complete":
        return _no_migration(campaign, mode, "completed_v7_preserved", schema)
    if experience == "companion":
        return _no_migration(campaign, mode, "companion_untouched", schema)
    if depth in {"quick", "standard"}:
        return _no_migration(campaign, mode, f"{depth}_untouched", schema)
    if experience not in {"", "rpg"}:
        return _no_migration(campaign, mode, "unsupported_experience", schema)
    if depth not in {"", "deep"}:
        return _no_migration(campaign, mode, "non_deep_untouched", schema)

    try:
        session_text = session_path.read_text(encoding="utf-8") if session_path.is_file() else ""
        statuses = _module_statuses(session_text)
    except (OSError, UnicodeError) as exc:
        return {
            "ok": False,
            "mode": mode,
            "error": "migration_read_failed",
            "message": str(exc),
            "campaign_path": str(campaign),
        }

    substantive = _substantive_progress(setup, setup_text, statuses)
    routing_only = not substantive
    if not depth and substantive:
        return _no_migration(campaign, mode, "route_unresolved_with_content", schema)
    if substantive and not statuses:
        return {
            "ok": False,
            "mode": mode,
            "error": "legacy_module_state_missing",
            "message": "In-progress Deep v7 setup requires its Standard / Deep module status block.",
            "campaign_path": str(campaign),
        }
    if substantive and _integer(setup.get("setup_revision"), 0) < 1:
        return {
            "ok": False,
            "mode": mode,
            "error": "legacy_revision_invalid",
            "message": "An in-progress v7 setup with durable decisions requires setup_revision >= 1.",
            "campaign_path": str(campaign),
        }
    if substantive and apply and not _has_snapshot(campaign):
        command = _snapshot_command(campaign)
        return {
            "ok": False,
            "mode": mode,
            "error": "snapshot_required",
            "message": "Create a full campaign snapshot before applying the in-progress v7 migration.",
            "campaign_path": str(campaign),
            "snapshot": {"required": True, "found": False, "command": command},
        }

    if state_path.exists():
        return {
            "ok": False,
            "mode": mode,
            "error": "v8_state_conflict",
            "message": "A session_zero_state.json already exists beside schema-v7 setup state.",
            "campaign_path": str(campaign),
        }

    state, review_stages, mapped = _build_migrated_state(
        campaign,
        setup,
        setup_text,
        statuses,
        routing_only=routing_only,
    )
    setup_new = _replace_top_scalar(setup_text, "schema_version", "8")
    setup_new = _replace_top_scalar(setup_new, "design_direction_approved_revision", "null")
    setup_new = _replace_top_scalar(setup_new, "preparation_approved_revision", "null")
    setup_new = _replace_top_scalar(setup_new, "deep_flow_id", FLOW_ID)
    setup_new = _replace_top_scalar(
        setup_new, "session_zero_state_path", "session_zero_state.json"
    )
    if depth == "deep":
        setup_new = _replace_top_list(setup_new, "defaulted_decisions", [])
        setup_new = _replace_top_list(setup_new, "deferred_decisions", [])
        setup_new = _replace_top_list(setup_new, "activated_packs", [])
        setup_new = _replace_top_list(setup_new, "completed_packs", [])
        setup_new = _replace_top_list(setup_new, "defaulted_packs", [])
        setup_new = _replace_top_scalar(setup_new, "defaults_reviewed", "false")
        setup_new = _replace_top_scalar(setup_new, "deep_extension_approved", "false")
        setup_new = _replace_top_scalar(
            setup_new, "questions_completed", str(len(state.get("decisions", [])))
        )
        setup_new = _replace_top_scalar(
            setup_new,
            "last_checkpoint",
            str(min(max(0, _integer(setup.get("last_checkpoint"), 0)), len(state.get("decisions", [])))),
        )

    planned = {
        setup_path: setup_new,
        state_path: json.dumps(state, indent=2, ensure_ascii=False) + "\n",
    }
    session_new = _update_managed_summary(session_text, state)
    if session_new != session_text:
        planned[session_path] = session_new
    if apply:
        try:
            should_validate = experience == "rpg" and depth == "deep"
            _apply_all(
                planned,
                validate=(lambda: _validate_applied_state(campaign)) if should_validate else None,
            )
        except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
            return {
                "ok": False,
                "mode": mode,
                "error": "migration_write_failed",
                "message": str(exc),
                "campaign_path": str(campaign),
            }

    return {
        "ok": True,
        "mode": mode,
        "campaign_path": str(campaign),
        "eligible": True,
        "changed": True,
        "migrated": apply,
        "would_migrate": not apply,
        "reason": "routing_only" if routing_only else "in_progress",
        "source_schema_version": 7,
        "target_schema_version": 8,
        "routing_only": routing_only,
        "mapped_decisions": mapped,
        "changed_files": [str(path) for path in planned],
        "needs_review": review_stages,
        "snapshot": {
            "required": substantive,
            "found": _has_snapshot(campaign),
            "command": _snapshot_command(campaign) if substantive else [],
        },
    }


def _print_human(result: dict[str, Any]) -> None:
    if not result.get("ok"):
        print(f"Session 0 v8 migration blocked: {result.get('error')}: {result.get('message', '')}")
        snapshot = result.get("snapshot")
        if isinstance(snapshot, dict) and snapshot.get("command"):
            print("Create the required snapshot first:")
            print("  " + " ".join(json.dumps(part) for part in snapshot["command"]))
        return
    if not result.get("eligible"):
        print(f"Session 0 v8 migration: no change ({result.get('reason')}).")
        return
    action = "applied" if result.get("migrated") else "planned"
    kind = "routing-only" if result.get("routing_only") else "in-progress"
    print(f"Session 0 v8 migration {action}: {kind} campaign.")
    print(f"- Mapped legacy decisions: {result.get('mapped_decisions', 0)}")
    for stage in result.get("needs_review", []):
        print(f"- NEEDS REVIEW: {stage}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True, help="Path to a RePoG campaign folder.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Report the migration without writing.")
    mode.add_argument("--apply", action="store_true", help="Apply the migration atomically.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    result = migrate(Path(args.campaign), apply=args.apply)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_human(result)
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())

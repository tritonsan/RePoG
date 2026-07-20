"""Verify a clean RePoG player workspace using only the Python standard library.

This is the single public smoke-check entry point.  It checks the distributable
layout, parses every bundled Python helper, runs the campaign validator, and
validates the optional dashboard state.  It does not modify campaign files.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any


REQUIRED_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "OPEN_CAMPAIGN.md",
    "README.md",
    "START_HERE.md",
    "LICENSE",
    "campaign/setup_profile.yaml",
    "campaign/play_profile.yaml",
    "campaign/companion_profile.yaml",
    "campaign/companion_state.json",
    "campaign/companion_view/companion_view_state.json",
    "campaign/companion_view/index.html",
    "campaign/companion_view/app.js",
    "campaign/companion_view/style.css",
    "campaign/companion_view/assets/README.md",
    "campaign/user_context.md",
    "campaign/characters/_companion_template.md",
    "campaign/map_atlas.json",
    "campaign/world_voices/index.json",
    "campaign/world_voices/README.md",
    "campaign/world_voices/artifacts/README.md",
    "campaign/dashboard/assets/world_voices/catalog.json",
    "campaign/current_state.yaml",
    "campaign/visual_state.json",
    "campaign/dashboard/dashboard_state.json",
    "campaign/dashboard/index.html",
    "tools/check_state.py",
    "tools/check_companion.py",
    "tools/check_companion_view.py",
    "tools/companion_state.py",
    "tools/companion_acceptance_suite.json",
    "tools/check_dashboard.py",
    "tools/compile_map_atlas.py",
    "tools/check_world_voices.py",
    "tools/world_voices.py",
    "tools/resolve_mechanic.py",
    "tools/check_style.py",
    "tools/migrate_companion_contract.py",
    "tools/migrate_gm_contract.py",
    "tools/gm_replay_suite.json",
    "tools/roll_dice.py",
    "tools/serve_companion_view.py",
    "tools/serve_dashboard.py",
    "tools/update_dashboard.py",
    "tools/visual_handoff.py",
    "workflows/audit/WORKFLOW.md",
    "workflows/distill/WORKFLOW.md",
    "workflows/gm/WORKFLOW.md",
    "workflows/gm/playbooks/action_conflict.md",
    "workflows/gm/playbooks/breather_aftermath.md",
    "workflows/gm/playbooks/dialogue_social.md",
    "workflows/gm/playbooks/exploration_investigation.md",
    "workflows/gm/playbooks/scene_arc_transition.md",
    "workflows/gm/playbooks/scene_entry_opening.md",
    "workflows/gm/playbooks/travel_downtime.md",
    "workflows/gm/playbooks/visual_handoff.md",
    "workflows/gm/playbooks/world_voices.md",
    "workflows/companion/WORKFLOW.md",
    "workflows/companion/playbooks/ordinary_conversation.md",
    "workflows/companion/playbooks/elapsed_time_life_update.md",
    "workflows/companion/playbooks/disclosure_intimacy.md",
    "workflows/companion/playbooks/conflict_repair.md",
    "workflows/companion/playbooks/callback_initiative.md",
    "workflows/companion/playbooks/identity_ooc_safety.md",
    "workflows/worldbuild/WORKFLOW.md",
    "docs/companion-mode.md",
)

REQUIRED_DIRS = (
    "briefs",
    "briefs/lenses",
    "campaign",
    "campaign/dashboard",
    "campaign/companion_view",
    "campaign/companion_view/assets",
    "campaign/world_voices",
    "campaign/world_voices/artifacts",
    "campaign/dashboard/assets/world_voices",
    "docs",
    "tools",
    "workflows",
    "workflows/gm/playbooks",
    "workflows/companion",
    "workflows/companion/playbooks",
)

REQUIRED_LENSES = ("INDEX.md", "fantasy.md", "realistic.md", "cyberpunk.md", "survival.md")
GM_REPLAY_DIMENSIONS = {
    "intent_fidelity",
    "causality",
    "player_authorship",
    "npc_agency",
    "presence_logic",
    "voice_contrast",
    "knowledge_boundary",
    "pacing",
    "continuation",
}


def _finding(
    severity: str,
    rule: str,
    message: str,
    path: Path | str | None = None,
    *,
    check: str,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "rule": rule,
        "message": message,
        "path": str(path) if path is not None else None,
        "check": check,
    }


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalise_findings(items: Any, *, check: str) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return [
            _finding(
                "error",
                "invalid_check_result",
                "A bundled checker returned findings in an unsupported format.",
                check=check,
            )
        ]
    normalised: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            normalised.append(
                _finding(
                    "error",
                    "invalid_check_finding",
                    "A bundled checker returned a non-object finding.",
                    check=check,
                )
            )
            continue
        normalised.append(
            {
                "severity": str(item.get("severity", "error")),
                "rule": str(item.get("rule", "unknown")),
                "message": str(item.get("message", "")),
                "path": item.get("path"),
                "check": check,
            }
        )
    return normalised


def _check_layout(workspace: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for relative in REQUIRED_FILES:
        path = workspace / relative
        if not path.is_file():
            findings.append(
                _finding("error", "workspace_file_missing", f"Missing workspace file: {relative}", path, check="layout")
            )
    for relative in REQUIRED_DIRS:
        path = workspace / relative
        if not path.is_dir():
            findings.append(
                _finding("error", "workspace_directory_missing", f"Missing workspace directory: {relative}", path, check="layout")
            )
    for filename in REQUIRED_LENSES:
        path = workspace / "briefs" / "lenses" / filename
        if not path.is_file():
            findings.append(
                _finding("error", "lens_brief_missing", f"Missing bundled lens brief: {filename}", path, check="layout")
            )
    findings.extend(_check_gm_replay_fixture(workspace / "tools" / "gm_replay_suite.json"))
    findings.extend(_check_companion_acceptance_fixture(workspace / "tools" / "companion_acceptance_suite.json"))
    return findings


def _check_companion_acceptance_fixture(path: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not path.is_file():
        return findings
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [_finding("error", "companion_acceptance_invalid", str(exc), path, check="layout")]
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return [_finding("error", "companion_acceptance_schema_invalid", "Companion acceptance suite must use schema_version 1.", path, check="layout")]
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) != 20:
        return [_finding("error", "companion_acceptance_count_invalid", "Companion acceptance suite must contain exactly 20 scenarios.", path, check="layout")]
    ids: list[str] = []
    allowed_kinds = {"instruction_replay", "structural", "tool_replay", "state_replay", "semantic_replay", "integration_replay", "regression"}
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            findings.append(_finding("error", "companion_acceptance_case_invalid", f"Scenario {index} must be an object.", path, check="layout"))
            continue
        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            findings.append(_finding("error", "companion_acceptance_case_invalid", f"Scenario {index} needs a stable id.", path, check="layout"))
        else:
            ids.append(scenario_id)
        if scenario.get("kind") not in allowed_kinds:
            findings.append(_finding("error", "companion_acceptance_kind_invalid", f"Scenario {scenario_id or index} has an invalid kind.", path, check="layout"))
        for key in ("stimulus", "expected"):
            if not isinstance(scenario.get(key), str) or not scenario[key].strip():
                findings.append(_finding("error", "companion_acceptance_case_invalid", f"Scenario {scenario_id or index} is missing {key}.", path, check="layout"))
    if len(ids) != len(set(ids)):
        findings.append(_finding("error", "companion_acceptance_id_duplicate", "Companion acceptance scenario ids must be unique.", path, check="layout"))
    return findings


def _check_gm_replay_fixture(path: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not path.is_file():
        return findings
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [_finding("error", "gm_replay_invalid", str(exc), path, check="layout")]
    if not isinstance(data, dict) or data.get("schema_version") != 2:
        findings.append(_finding("error", "gm_replay_schema_invalid", "GM replay fixture must use schema_version 2.", path, check="layout"))
        return findings

    rubric = data.get("rubric")
    dimensions = rubric.get("dimensions") if isinstance(rubric, dict) else None
    if not isinstance(dimensions, dict) or set(dimensions) != GM_REPLAY_DIMENSIONS:
        findings.append(_finding("error", "gm_replay_rubric_invalid", "GM replay rubric must define the nine approved dimensions.", path, check="layout"))
    scoring = data.get("scoring")
    required_formulas = {"scenario_mean_formula", "scenario_pass_formula", "suite_mean_formula", "suite_pass_formula"}
    if not isinstance(scoring, dict) or any(not str(scoring.get(key, "")).strip() for key in required_formulas):
        findings.append(_finding("error", "gm_replay_scoring_invalid", "GM replay scoring formulas are incomplete.", path, check="layout"))

    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) != 12:
        findings.append(_finding("error", "gm_replay_scenarios_invalid", "GM replay fixture must contain exactly 12 scenarios.", path, check="layout"))
        return findings
    ids: list[str] = []
    required = {"id", "initial_state", "setup", "turn_sequence", "expected_observations", "critical_failures", "scoring_record"}
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            findings.append(_finding("error", "gm_replay_scenario_invalid", f"Scenario {index} must be an object.", path, check="layout"))
            continue
        missing = sorted(required - set(scenario))
        if missing:
            findings.append(_finding("error", "gm_replay_scenario_invalid", f"Scenario {index} is missing: {', '.join(missing)}.", path, check="layout"))
        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            findings.append(_finding("error", "gm_replay_scenario_invalid", f"Scenario {index} has no stable id.", path, check="layout"))
        else:
            ids.append(scenario_id)
        turns = scenario.get("turn_sequence")
        if not isinstance(turns, list) or not turns or any(not isinstance(turn, dict) or "turn" not in turn for turn in turns):
            findings.append(_finding("error", "gm_replay_turns_invalid", f"Scenario {scenario_id or index} needs numbered turn fixtures.", path, check="layout"))
        expected = scenario.get("expected_observations")
        if not isinstance(expected, dict) or not expected or not set(expected) <= GM_REPLAY_DIMENSIONS:
            findings.append(_finding("error", "gm_replay_expected_invalid", f"Scenario {scenario_id or index} has invalid expected observations.", path, check="layout"))
        critical = scenario.get("critical_failures")
        if not isinstance(critical, list) or any(not isinstance(item, dict) or not {"id", "category", "description"} <= set(item) for item in critical):
            findings.append(_finding("error", "gm_replay_critical_invalid", f"Scenario {scenario_id or index} has invalid critical failures.", path, check="layout"))
        record = scenario.get("scoring_record")
        if not isinstance(record, dict) or not {"dimension_scores", "critical_failures_observed", "scenario_mean", "status"} <= set(record):
            findings.append(_finding("error", "gm_replay_record_invalid", f"Scenario {scenario_id or index} has an incomplete scoring record.", path, check="layout"))
    if len(ids) != len(set(ids)):
        findings.append(_finding("error", "gm_replay_id_duplicate", "GM replay scenario ids must be unique.", path, check="layout"))
    return findings


def _check_python_sources(workspace: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    tools_dir = workspace / "tools"
    if not tools_dir.is_dir():
        return findings
    for path in sorted(tools_dir.glob("*.py")):
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as exc:
            findings.append(_finding("error", "python_source_invalid", str(exc), path, check="python"))
    return findings


def _campaign_check(workspace: Path, campaign: Path, scope: str) -> list[dict[str, Any]]:
    check_path = workspace / "tools" / "check_state.py"
    if not check_path.is_file():
        return []
    try:
        module = _load_module("repog_verify_check_state", check_path)
        result = module.check_campaign(campaign, scope=scope)
    except Exception as exc:  # A broken public checker is itself a verification failure.
        return [_finding("error", "campaign_check_failed", str(exc), check_path, check="campaign")]
    if not isinstance(result, dict):
        return [_finding("error", "campaign_check_invalid", "Campaign checker returned a non-object result.", check_path, check="campaign")]
    return _normalise_findings(result.get("findings"), check="campaign")


def _dashboard_check(workspace: Path, campaign: Path) -> list[dict[str, Any]]:
    check_path = workspace / "tools" / "check_dashboard.py"
    state_path = campaign / "dashboard" / "dashboard_state.json"
    if not check_path.is_file() or not state_path.is_file():
        return []
    try:
        module = _load_module("repog_verify_check_dashboard", check_path)
        result = module.check_dashboard(state_path, campaign_path=campaign)
    except Exception as exc:
        return [_finding("error", "dashboard_check_failed", str(exc), check_path, check="dashboard")]
    if not isinstance(result, dict):
        return [_finding("error", "dashboard_check_invalid", "Dashboard checker returned a non-object result.", check_path, check="dashboard")]
    return _normalise_findings(result.get("findings"), check="dashboard")


def _companion_contract_check(workspace: Path, campaign: Path) -> list[dict[str, Any]]:
    """Exercise the V2 fast path, durable semantics, privacy, and routing."""

    findings: list[dict[str, Any]] = []
    state_tool = workspace / "tools" / "companion_state.py"
    campaign_checker = workspace / "tools" / "check_state.py"
    view_checker = workspace / "tools" / "check_companion_view.py"
    migration_tool = workspace / "tools" / "migrate_companion_contract.py"
    if not state_tool.is_file() or not campaign_checker.is_file() or not view_checker.is_file() or not migration_tool.is_file():
        return findings
    try:
        state_module = _load_module("repog_verify_companion_state", state_tool)
        check_module = _load_module("repog_verify_companion_route", campaign_checker)
        view_module = _load_module("repog_verify_companion_view", view_checker)
        migration_module = _load_module("repog_verify_companion_migration", migration_tool)
        with tempfile.TemporaryDirectory(prefix="repog-companion-check-") as temp_root:
            root = Path(temp_root)
            clock_campaign = root / "clock"
            clock_campaign.mkdir()
            source_state = json.loads((campaign / "companion_state.json").read_text(encoding="utf-8"))
            source_state.update(
                {
                    "configured_timezone": "Europe/Istanbul",
                    "configured_utc_offset": "+03:00",
                    "last_observation_at": "2026-07-17T12:00:00+03:00",
                    "last_user_contact_at": "2026-07-17T12:00:00+03:00",
                }
            )
            source_state["current_window"] = {
                "window_id": "window_before_gap",
                "started_at": "2026-07-17T12:00:00+03:00",
                "last_exchange_at": "2026-07-17T12:00:00+03:00",
            }
            source_state["current_presence"] = {
                "as_of": "2026-07-17T12:00:00+03:00",
                "place_ref": "home",
                "activity": "finishing lunch",
                "with_refs": [],
                "availability": "limited",
                "expected_until": "2026-07-18T12:00:00+03:00",
                "source": "fixture",
            }
            source_state["current_condition"] = {
                "as_of": "2026-07-17T12:00:00+03:00",
                "energy": "steady",
                "social_bandwidth": "open",
                "emotional_weather": "quietly focused",
                "active_preoccupation": "a work presentation",
                "cause_ref": "domain:daily_work",
                "reevaluate_after": "2026-07-18T12:00:00+03:00",
            }
            source_state["attention_queue"] = [
                {
                    "attention_id": "followup_presentation",
                    "kind": "life_domain",
                    "subject_ref": "daily_work",
                    "due_at": "2026-07-19T12:00:00+03:00",
                    "source_ref": "domain:daily_work",
                }
            ]
            (clock_campaign / "companion_state.json").write_text(
                json.dumps(source_state, indent=2) + "\n", encoding="utf-8"
            )

            first = state_module.begin_exchange(
                clock_campaign,
                operation_id="verify-exchange-1",
                expected_state_revision=0,
                expected_continuity_revision=0,
                now_override="2026-07-20T12:00:00+03:00",
            )
            retry = state_module.begin_exchange(
                clock_campaign,
                operation_id="verify-exchange-1",
                expected_state_revision=0,
                expected_continuity_revision=0,
                now_override="2026-07-20T12:01:00+03:00",
            )
            due = first.get("signals", {})
            if (
                first.get("gap_band") != "compressed_days"
                or first.get("event_ceiling") != 2
                or first.get("state_revision") != 1
                or first.get("continuity_revision") != 0
                or first.get("interaction_sequence") != 1
                or not retry.get("idempotent")
                or retry.get("state_revision") != 1
            ):
                findings.append(_finding("error", "companion_begin_exchange_failed", "One begin-exchange must reconcile the prior gap and record contact exactly once without changing fictional continuity.", state_tool, check="companion"))
            if not due.get("presence_review_due") or not due.get("condition_review_due") or due.get("attention_due_ids") != ["followup_presentation"]:
                findings.append(_finding("error", "companion_due_signal_failed", "Begin-exchange must return bounded due signals without inventing events.", state_tool, check="companion"))

            evidence = {
                "evidence_id": "exchange_candor_1",
                "dimension": "candor",
                "direction": "strengthened",
                "interpretation": "The user answered a difficult question directly.",
                "source_ref": "exchange:verify-exchange-1",
                "observed_at": "2026-07-20T12:05:00+03:00",
            }
            semantic_patch = {
                "relational_context": {
                    "companion_posture": "cautious curiosity",
                    "reciprocity_pattern": "direct questions receive direct answers",
                    "recent_evidence": [evidence],
                    "last_change_evidence_id": "exchange_candor_1",
                }
            }
            durable = state_module.commit_semantic(
                clock_campaign,
                operation_id="verify-semantic-1",
                semantic_sequence=1,
                expected_state_revision=1,
                expected_continuity_revision=0,
                state_patch=semantic_patch,
                gap_id=first["gap_id"],
                now_override="2026-07-20T12:05:00+03:00",
            )
            durable_retry = state_module.commit_semantic(
                clock_campaign,
                operation_id="verify-semantic-1",
                semantic_sequence=1,
                expected_state_revision=1,
                expected_continuity_revision=0,
                state_patch=semantic_patch,
                gap_id=first["gap_id"],
                now_override="2026-07-20T12:06:00+03:00",
            )
            evicted_state_path = clock_campaign / "companion_state.json"
            evicted_state = json.loads(evicted_state_path.read_text(encoding="utf-8"))
            evicted_state["recent_operation_ids"] = [
                value for value in evicted_state.get("recent_operation_ids", []) if value != "verify-semantic-1"
            ]
            evicted_state_path.write_text(json.dumps(evicted_state, indent=2) + "\n", encoding="utf-8")
            ledger_retry = state_module.commit_semantic(
                clock_campaign,
                operation_id="verify-semantic-1",
                semantic_sequence=1,
                expected_state_revision=1,
                expected_continuity_revision=0,
                state_patch=semantic_patch,
                gap_id=first["gap_id"],
                now_override="2026-07-20T12:07:00+03:00",
            )
            if (
                durable.get("continuity_revision") != 1
                or durable.get("semantic_operation_sequence") != 1
                or not durable_retry.get("idempotent")
                or not ledger_retry.get("idempotent")
            ):
                findings.append(_finding("error", "companion_semantic_idempotency_failed", "A retried semantic operation must retain one monotonic semantic sequence and one continuity increment.", state_tool, check="companion"))
            altered_retry_rejected = False
            try:
                state_module.commit_semantic(
                    clock_campaign,
                    operation_id="verify-semantic-1",
                    semantic_sequence=1,
                    expected_state_revision=2,
                    expected_continuity_revision=1,
                    state_patch={"current_condition": {"energy": "high"}},
                    gap_id=first["gap_id"],
                    now_override="2026-07-20T12:08:00+03:00",
                )
            except state_module.CompanionStateError:
                altered_retry_rejected = True
            if not altered_retry_rejected:
                findings.append(_finding("error", "companion_semantic_payload_replay_failed", "A permanently reserved semantic operation id must reject an altered payload after recent-id eviction.", state_tool, check="companion"))

            monotonic_rejected = False
            try:
                state_module.commit_semantic(
                    clock_campaign,
                    operation_id="verify-semantic-skip",
                    semantic_sequence=3,
                    expected_state_revision=2,
                    expected_continuity_revision=1,
                    state_patch={"current_condition": {"energy": "low"}},
                    now_override="2026-07-20T12:10:00+03:00",
                )
            except state_module.CompanionStateError:
                monotonic_rejected = True
            if not monotonic_rejected:
                findings.append(_finding("error", "companion_semantic_sequence_failed", "Semantic commits must reject skipped or reused monotonic sequence numbers.", state_tool, check="companion"))

            backwards_rejected = False
            try:
                state_module.begin_exchange(
                    clock_campaign,
                    operation_id="verify-backwards-contact",
                    expected_state_revision=2,
                    expected_continuity_revision=1,
                    now_override="2026-07-19T12:00:00+03:00",
                )
            except state_module.CompanionStateError:
                backwards_rejected = True
            if not backwards_rejected:
                findings.append(_finding("error", "companion_backwards_time_failed", "Companion state must reject a new exchange whose observed time moves backwards.", state_tool, check="companion"))

            inspection_a = state_module.inspect(clock_campaign, now_override="2026-07-20T12:10:00+03:00")
            inspection_b = state_module.inspect(clock_campaign, now_override="2026-07-20T12:20:00+03:00")
            if inspection_a.get("gap_id") != inspection_b.get("gap_id") or inspection_a.get("current_presence") != inspection_b.get("current_presence"):
                findings.append(_finding("error", "companion_state_stability_failed", "Read-only inspection in one conversation window must preserve gap identity and current presence.", state_tool, check="companion"))

            safe_projection = json.loads((campaign / "companion_view" / "companion_view_state.json").read_text(encoding="utf-8"))
            safe_result = view_module.check_companion_view_data(
                safe_projection,
                campaign / "companion_view" / "companion_view_state.json",
                campaign_path=campaign,
                require_assets=False,
            )
            if safe_result.get("error_count") != 0:
                findings.append(_finding("error", "companion_view_default_failed", "The bundled disabled Companion View projection must be player-safe.", view_checker, check="companion"))
            leaked_projection = {**safe_projection, "trust_score": 8}
            leaked_result = view_module.check_companion_view_data(
                leaked_projection,
                campaign / "companion_view" / "companion_view_state.json",
                campaign_path=campaign,
                require_assets=False,
            )
            leaked_rules = {item.get("rule") for item in leaked_result.get("findings", [])}
            if not {"companion_view_field_forbidden", "companion_view_private_field"} & leaked_rules:
                findings.append(_finding("error", "companion_view_privacy_failed", "Companion View must reject relationship meters, disclosure state, user memory, and other private projection fields.", view_checker, check="companion"))

            migration_campaign = root / "companion_v1_migration"
            shutil.copytree(campaign, migration_campaign)
            legacy_profile_path = migration_campaign / "companion_profile.yaml"
            legacy_profile = legacy_profile_path.read_text(encoding="utf-8")
            legacy_profile = legacy_profile.replace("schema_version: 2", "schema_version: 1", 1)
            legacy_profile = legacy_profile.replace("  model: evidence_context", "  model: organic_qualitative", 1)
            legacy_profile = legacy_profile.replace("  user_policy: contextual_low_risk", "  user_policy: consent_contextual", 1)
            legacy_profile = legacy_profile.replace("  exchange_persistence: single_begin_exchange", "  contact_write: one_per_incoming_message", 1)
            legacy_profile_path.write_text(legacy_profile, encoding="utf-8")
            legacy_state = {
                "schema_version": 1,
                "state_revision": 0,
                "continuity_revision": 0,
                "interaction_sequence": 0,
                "configured_timezone": "Europe/Istanbul",
                "configured_utc_offset": "+03:00",
                "last_observation_at": None,
                "last_contact_at": "2026-07-17T12:00:00+03:00",
                "last_response_at": None,
                "current_window": {"window_id": "window_legacy", "started_at": "2026-07-17T12:00:00+03:00", "last_exchange_at": "2026-07-17T12:00:00+03:00"},
                "current_presence": {"as_of": "2026-07-17T12:00:00+03:00", "place_ref": "home", "activity": "reading", "with_refs": [], "availability": "available", "expected_until": None, "source": "fixture"},
                "pending_transition": None,
                "last_gap": {"gap_id": "", "elapsed_minutes": 0, "band": "same_window", "event_ceiling": 0, "reconciled_revision": 0},
                "primary_relationship": {"companion_stance": "curious", "trust_band": "cautious", "closeness_band": "new", "tension": "none", "reciprocity": "tentative", "boundary_state": "clear", "unresolved_interaction": "", "last_evidence_refs": ["setup:starting_frame"]},
                "recent_operation_ids": [],
                "last_committed_operation_sequence": 0,
            }
            legacy_state_path = migration_campaign / "companion_state.json"
            legacy_state_path.write_text(json.dumps(legacy_state, indent=2) + "\n", encoding="utf-8")
            before_migration = {path: path.read_bytes() for path in (legacy_profile_path, legacy_state_path)}
            dry_run = migration_module.migrate(migration_campaign, apply=False)
            if not dry_run.get("ok") or not dry_run.get("changed") or any(path.read_bytes() != before_migration[path] for path in before_migration):
                findings.append(_finding("error", "companion_migration_dry_run_failed", "V1-to-V2 migration dry-run must plan changes without writing campaign files.", migration_tool, check="companion"))
            blocked_apply = migration_module.migrate(migration_campaign, apply=True)
            if blocked_apply.get("ok") or blocked_apply.get("error") != "snapshot_required":
                findings.append(_finding("error", "companion_migration_snapshot_gate_failed", "Applying a Companion contract migration must require an existing campaign snapshot.", migration_tool, check="companion"))
            snapshot_dir = migration_campaign / "snapshots" / "verify_before_v2"
            snapshot_dir.mkdir(parents=True)
            (snapshot_dir / "snapshot_manifest.json").write_text("{}\n", encoding="utf-8")
            applied = migration_module.migrate(migration_campaign, apply=True)
            second_dry_run = migration_module.migrate(migration_campaign, apply=False)
            migrated_state = json.loads(legacy_state_path.read_text(encoding="utf-8"))
            if (
                not applied.get("ok")
                or not applied.get("changed")
                or not second_dry_run.get("ok")
                or second_dry_run.get("changed")
                or migrated_state.get("schema_version") != 2
                or "primary_relationship" in migrated_state
                or {"trust_band", "closeness_band"} & set(migrated_state.get("relational_context", {}))
            ):
                findings.append(_finding("error", "companion_migration_idempotency_failed", "A snapshotted V1 migration must preserve fiction, remove ladder-era state, and become idempotent after one apply.", migration_tool, check="companion"))

            source_setup_text = (campaign / "setup_profile.yaml").read_text(encoding="utf-8")
            pristine_setup = (
                re.search(r"(?m)^schema_version:\s*4\s*$", source_setup_text) is not None
                and re.search(r"(?m)^status:\s*pending\s*$", source_setup_text) is not None
                and re.search(r'(?m)^experience_mode:\s*""\s*$', source_setup_text) is not None
                and re.search(r'(?m)^session_zero_mode:\s*""\s*$', source_setup_text) is not None
            )
            if not pristine_setup:
                return findings

            bad_gate_campaign = root / "bad_gate"
            shutil.copytree(campaign, bad_gate_campaign)
            bad_setup_path = bad_gate_campaign / "setup_profile.yaml"
            bad_setup = bad_setup_path.read_text(encoding="utf-8").replace("status: pending", "status: in_progress", 1).replace('session_zero_mode: ""', "session_zero_mode: quick", 1)
            bad_setup_path.write_text(bad_setup, encoding="utf-8")
            bad_gate_result = check_module.check_campaign(bad_gate_campaign, scope="full")
            bad_gate_rules = {item.get("rule") for item in bad_gate_result.get("findings", [])}
            if "session_depth_before_experience" not in bad_gate_rules:
                findings.append(_finding("error", "companion_experience_gate_failed", "Session 0 depth must not be accepted before the RPG/Companion experience gate.", campaign_checker, check="companion"))

            branch_campaign = root / "companion_branch"
            shutil.copytree(campaign, branch_campaign)
            setup_path = branch_campaign / "setup_profile.yaml"
            setup_text = setup_path.read_text(encoding="utf-8").replace('experience_mode: ""', "experience_mode: companion", 1)
            setup_path.write_text(setup_text, encoding="utf-8")
            play_path = branch_campaign / "play_profile.yaml"
            play_text = play_path.read_text(encoding="utf-8").replace("profile_status: pending", "profile_status: inactive", 1)
            play_path.write_text(play_text, encoding="utf-8")
            branch_result = check_module.check_campaign(branch_campaign, scope="full")
            if branch_result.get("error_count") != 0:
                findings.append(_finding("error", "companion_mode_route_failed", "A selected but pending Companion setup must bypass RPG readiness checks without errors.", campaign_checker, check="companion"))

            ready_campaign = root / "companion_ready"
            shutil.copytree(campaign, ready_campaign)
            setup_path = ready_campaign / "setup_profile.yaml"
            setup_text = setup_path.read_text(encoding="utf-8")
            for old, new in (
                ("status: pending", "status: complete"),
                ("setup_revision: 0", "setup_revision: 1"),
                ('experience_mode: ""', "experience_mode: companion"),
                ('session_zero_mode: ""', "session_zero_mode: quick"),
                ('question_target: ""', 'question_target: "7"'),
                ("questions_completed: 0", "questions_completed: 7"),
                ("activated_packs: []", "activated_packs: [companion_persona]"),
                ("defaulted_packs: []", "defaulted_packs: [companion_persona]"),
                ("ready_for_play: false", "ready_for_play: true"),
            ):
                setup_text = setup_text.replace(old, new, 1)
            setup_path.write_text(setup_text, encoding="utf-8")

            play_path = ready_campaign / "play_profile.yaml"
            play_text = play_path.read_text(encoding="utf-8").replace("profile_status: pending", "profile_status: inactive", 1).replace("source_setup_revision: 0", "source_setup_revision: 1", 1)
            play_path.write_text(play_text, encoding="utf-8")

            profile_path = ready_campaign / "companion_profile.yaml"
            profile_text = profile_path.read_text(encoding="utf-8")
            replacements = (
                ("profile_status: pending", "profile_status: locked"),
                ("source_setup_revision: 0", "source_setup_revision: 1"),
                ('primary_companion_id: ""', "primary_companion_id: alex"),
                ('  mode: ""', "  mode: fictional_world"),
                ('  city_or_region: ""', "  city_or_region: Evershore"),
                ('  country_or_world: ""', "  country_or_world: Fixture World"),
                ('  timezone: ""', "  timezone: UTC"),
                ('  utc_offset: ""', '  utc_offset: "+00:00"'),
                ('  language: ""', "  language: English"),
                ('  starting_frame: ""', "  starting_frame: new correspondents"),
                ('  allowed_scope: ""', "  allowed_scope: friendship"),
                ("  primary_companion_is_adult: false", "  primary_companion_is_adult: true"),
                ("  boundaries_confirmed: false", "  boundaries_confirmed: true"),
            )
            for old, new in replacements:
                profile_text = profile_text.replace(old, new, 1)
            profile_path.write_text(profile_text, encoding="utf-8")

            ready_state = json.loads((ready_campaign / "companion_state.json").read_text(encoding="utf-8"))
            ready_state.update(
                {
                    "configured_timezone": "UTC",
                    "configured_utc_offset": "+00:00",
                    "last_observation_at": "2026-07-20T09:00:00+00:00",
                    "last_user_contact_at": "2026-07-20T09:00:00+00:00",
                }
            )
            ready_state["current_window"] = {"window_id": "window_setup", "started_at": "2026-07-20T09:00:00+00:00", "last_exchange_at": "2026-07-20T09:00:00+00:00"}
            ready_state["current_presence"] = {"as_of": "2026-07-20T09:00:00+00:00", "place_ref": "home", "activity": "making breakfast", "with_refs": [], "availability": "available", "expected_until": "2026-07-20T10:00:00+00:00", "source": "setup"}
            ready_state["current_condition"] = {"as_of": "2026-07-20T09:00:00+00:00", "energy": "steady", "social_bandwidth": "open", "emotional_weather": "calm curiosity", "active_preoccupation": "the presentation later today", "cause_ref": "domain:daily_work", "reevaluate_after": "2026-07-20T11:00:00+00:00"}
            ready_state["relational_context"] = {
                "companion_posture": "curious but measured",
                "reciprocity_pattern": "friendly questions without assumed intimacy",
                "boundary_refs": ["companion_boundaries_v1"],
                "active_tensions": [],
                "recent_evidence": [{"evidence_id": "setup_starting_frame", "dimension": "emotional_safety", "direction": "ambiguous", "interpretation": "They agreed to begin as new correspondents.", "source_ref": "setup:starting_frame", "observed_at": "2026-07-20T09:00:00+00:00"}],
                "last_change_evidence_id": "setup_starting_frame",
            }
            (ready_campaign / "companion_state.json").write_text(json.dumps(ready_state, indent=2) + "\n", encoding="utf-8")

            template = (ready_campaign / "characters" / "_companion_template.md").read_text(encoding="utf-8")
            template = template.replace("# Primary Companion", "# Alex", 1).replace("Companion id: `replace_me`", "Companion id: `alex`", 1)
            persona_lines: list[str] = []
            for line in template.splitlines():
                match = re.match(r"^(-\s+)([^:]+):\s*$", line)
                if match:
                    label = match.group(2)
                    if label == "Age":
                        value = "29"
                    elif label == "Boundary ref":
                        value = "companion_boundaries_v1"
                    else:
                        value = f"fixture {label.lower()}"
                    line = f"{match.group(1)}{label}: {value}"
                persona_lines.append(line)
            (ready_campaign / "characters" / "alex.md").write_text("\n".join(persona_lines) + "\n", encoding="utf-8")
            (ready_campaign / "characters" / "jamie.md").write_text("# Jamie\n\nTier: T2\n\nA recurring friend from work.\n", encoding="utf-8")
            (ready_campaign / "places" / "home.md").write_text("# Home\n\nTier: T3\n\nA fictional private home.\n", encoding="utf-8")

            user_context = """# User Context\n\n## Memory Policy\n\n- Policy: contextual_low_risk\n- Sensitive facts: explicit consent only\n- Raw transcript storage: never\n\n## Active Memories\n\nNone yet.\n\n## Upcoming Follow-Ups\n\nNone yet.\n\n## Forget Tombstones\n\n| Tombstone id | Forgotten at | Scope |\n| --- | --- | --- |\n"""
            (ready_campaign / "user_context.md").write_text(user_context, encoding="utf-8")
            dynamics_path = ready_campaign / "world_dynamics.md"
            dynamics_path.write_text("""# World Dynamics\n\n## Active Domains\n\n### Daily Work\n\n- Domain id: daily_work\n- Scope: Alex's current project\n- Status: stable\n- Relevant actors: Alex, Jamie\n- Current trajectory: finishing a delayed presentation\n- Refresh triggers: next workday or explicit project update\n- Player-visible channels: what Alex chooses to mention\n- Next move if ignored: rehearse with Jamie\n- Last evaluated real time (Companion only): 2026-07-20T09:00:00+00:00\n\n## Due Checks\n\n- None yet.\n""", encoding="utf-8")
            dynamics_text = dynamics_path.read_text(encoding="utf-8").replace(
                "- Current trajectory: finishing a delayed presentation\n",
                "- Current trajectory: finishing a delayed presentation\n- Desired outcome (Companion only): present it without hiding behind Jamie\n",
                1,
            )
            dynamics_path.write_text(dynamics_text, encoding="utf-8")
            knowledge_path = ready_campaign / "knowledge_boundaries.md"
            knowledge_path.write_text("""# Knowledge Boundaries\n\n## Companion Knowledge\n\n### Alex\n\n- Confirmed fact ids: []\n- Suspicion fact ids: []\n- Explicitly unknown fact ids: []\n- Must-not-imply fact ids: [family_pressure]\n- How they could learn more: Alex may choose to share it in a fitting conversation.\n\n## Companion Disclosure Ledger\n\n### Family Pressure\n\n- Fact id: family_pressure\n- Companion id: alex\n- Topic: family expectations\n- Private truth: Alex worries that accepting the new role will disappoint their family.\n- Stage: private\n- Posture: guarded\n- Reason for posture: It feels too personal for a first conversation.\n- Natural openings: a discussion about work choices or family expectations\n- Evidence refs: [setup:persona]\n- Revision: 0\n- User-facing account:\n- Account truthfulness: not_disclosed\n- Protected category: ordinary\n- Direct lie permitted: no\n- Deception reason:\n- Correction note:\n""", encoding="utf-8")
            boundaries_path = ready_campaign / "boundaries.md"
            boundaries_text = boundaries_path.read_text(encoding="utf-8")
            for old, new in (
                ("- Effective relationship scope:", "- Effective relationship scope: friendship"),
                ("- Last confirmed at:", "- Last confirmed at: 2026-07-20T09:00:00+00:00"),
                ("- Interaction limits:", "- Interaction limits: Friendship with ordinary disagreement and no assumed availability"),
                ("- Romance and intimacy policy:", "- Romance and intimacy policy: friendship only"),
                ("- Disagreement and refusal policy:", "- Disagreement and refusal policy: either person may disagree or end a topic"),
            ):
                boundaries_text = boundaries_text.replace(old, new, 1)
            boundaries_path.write_text(boundaries_text, encoding="utf-8")
            relationship_path = ready_campaign / "relationship_map.md"
            relationship_path.write_text("""# Relationship Map\n\nAs of revision: 0\n\n| From | Direction | To | Relation | Status | Trust / debt / tension | Knowledge asymmetry | Player-known | Last changed | Revision |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |\n| Alex | <-> | Jamie | work friends | active | familiar trust | Jamie knows the project pressure | yes | setup | 0 |\n""", encoding="utf-8")
            session_zero_path = ready_campaign / "session_zero.md"
            session_zero_path.write_text(session_zero_path.read_text(encoding="utf-8").replace(": open", ": defaulted"), encoding="utf-8")
            research_path = ready_campaign / "research_dossier.md"
            research_text = research_path.read_text(encoding="utf-8").replace("- Status: `needed_pending`", "- Status: `not_needed`", 1).replace("- Current-scale lock permitted: no", "- Current-scale lock permitted: yes", 1)
            research_path.write_text(research_text, encoding="utf-8")

            profile_text = profile_path.read_text(encoding="utf-8").replace("  companion_view: off", "  companion_view: light", 1)
            profile_path.write_text(profile_text, encoding="utf-8")
            view_path = ready_campaign / "companion_view" / "companion_view_state.json"
            ready_view = json.loads(view_path.read_text(encoding="utf-8"))
            ready_view.update({"enabled": True, "identity": {"name": "Alex", "pronouns": "they/them", "tagline": "Coffee first, presentation later."}, "local_clock": {"label": "Alex's local time", "timezone": "UTC"}})
            view_path.write_text(json.dumps(ready_view, indent=2) + "\n", encoding="utf-8")

            ready_result = check_module.check_campaign(ready_campaign, scope="full")
            if ready_result.get("error_count") != 0:
                rules = ", ".join(item.get("rule", "unknown") for item in ready_result.get("findings", []) if item.get("severity") == "error")
                findings.append(_finding("error", "companion_ready_fixture_failed", f"A complete valid Companion fixture did not pass: {rules}", campaign_checker, check="companion"))

            memory_off_campaign = root / "companion_memory_off"
            shutil.copytree(ready_campaign, memory_off_campaign)
            memory_profile_path = memory_off_campaign / "companion_profile.yaml"
            memory_profile_path.write_text(
                memory_profile_path.read_text(encoding="utf-8").replace(
                    "  user_policy: contextual_low_risk", "  user_policy: off", 1
                ),
                encoding="utf-8",
            )
            memory_context_path = memory_off_campaign / "user_context.md"
            memory_context_path.write_text(
                memory_context_path.read_text(encoding="utf-8").replace(
                    "- Policy: contextual_low_risk", "- Policy: off", 1
                ),
                encoding="utf-8",
            )
            memory_state_path = memory_off_campaign / "companion_state.json"
            memory_state = json.loads(memory_state_path.read_text(encoding="utf-8"))
            memory_state["attention_queue"] = [
                {
                    "attention_id": "private_user_event",
                    "kind": "user_event",
                    "subject_ref": "user_event",
                    "due_at": "2026-07-21T09:00:00+00:00",
                    "source_ref": "user_context:private_user_event",
                }
            ]
            memory_state_path.write_text(json.dumps(memory_state, indent=2) + "\n", encoding="utf-8")
            memory_off_result = check_module.check_campaign(memory_off_campaign, scope="full")
            memory_off_rules = {item.get("rule") for item in memory_off_result.get("findings", [])}
            if "user_memory_disabled_attention_present" not in memory_off_rules:
                findings.append(_finding("error", "companion_memory_off_queue_failed", "A disabled user-memory policy must reject durable user-event attention state.", campaign_checker, check="companion"))

            before_view = view_path.read_bytes()
            privacy_rejected = False
            try:
                state_module.commit_semantic(
                    ready_campaign,
                    operation_id="verify-private-view-patch",
                    semantic_sequence=1,
                    expected_state_revision=0,
                    expected_continuity_revision=0,
                    expected_public_surface_revision=0,
                    state_patch={},
                    public_patch={"identity": {"tagline": "Trust score 9"}},
                    now_override="2026-07-20T09:05:00+00:00",
                )
            except state_module.CompanionStateError:
                privacy_rejected = True
            if not privacy_rejected or view_path.read_bytes() != before_view:
                findings.append(_finding("error", "companion_view_transaction_privacy_failed", "A private or internal public patch must fail without changing Companion state or View.", state_tool, check="companion"))

            public_result = state_module.commit_semantic(
                ready_campaign,
                operation_id="verify-public-view-patch",
                semantic_sequence=1,
                expected_state_revision=0,
                expected_continuity_revision=0,
                expected_public_surface_revision=0,
                state_patch={},
                public_patch={"last_shared_status": {"text": "Heading out for the presentation.", "shared_at": "2026-07-20T09:05:00+00:00"}},
                now_override="2026-07-20T09:05:00+00:00",
            )
            public_retry = state_module.commit_semantic(
                ready_campaign,
                operation_id="verify-public-view-patch",
                semantic_sequence=1,
                expected_state_revision=0,
                expected_continuity_revision=0,
                expected_public_surface_revision=0,
                state_patch={},
                public_patch={"last_shared_status": {"text": "Heading out for the presentation.", "shared_at": "2026-07-20T09:05:00+00:00"}},
                now_override="2026-07-20T09:06:00+00:00",
            )
            committed_view = json.loads(view_path.read_text(encoding="utf-8"))
            if public_result.get("public_surface_revision") != 1 or not public_retry.get("idempotent") or committed_view.get("public_surface_revision") != 1:
                findings.append(_finding("error", "companion_view_revision_commit_failed", "A visible semantic change must atomically advance the canonical and public Companion revisions exactly once.", state_tool, check="companion"))

            stale_view = dict(committed_view)
            stale_view["public_surface_revision"] = 0
            view_path.write_text(json.dumps(stale_view, indent=2) + "\n", encoding="utf-8")
            stale_result = check_module.check_campaign(ready_campaign, scope="full")
            stale_rules = {item.get("rule") for item in stale_result.get("findings", [])}
            if "companion_view_revision_stale" not in stale_rules:
                findings.append(_finding("error", "companion_view_revision_gate_failed", "A stale Companion View projection must not pass the campaign checker.", campaign_checker, check="companion"))
            view_path.write_text(json.dumps(committed_view, indent=2) + "\n", encoding="utf-8")

            invalid_quick = setup_path.read_text(encoding="utf-8").replace("questions_completed: 7", "questions_completed: 6", 1)
            setup_path.write_text(invalid_quick, encoding="utf-8")
            quick_result = check_module.check_campaign(ready_campaign, scope="full")
            quick_rules = {item.get("rule") for item in quick_result.get("findings", [])}
            if "quick_question_target" not in quick_rules:
                findings.append(_finding("error", "companion_quick_gate_failed", "Companion Quick must reject a non-seven content-decision count.", campaign_checker, check="companion"))
            setup_path.write_text(invalid_quick.replace("questions_completed: 6", "questions_completed: 7", 1), encoding="utf-8")

            invalid_city = profile_path.read_text(encoding="utf-8").replace("mode: fictional_world", "mode: real_city_fictional_private", 1)
            profile_path.write_text(invalid_city, encoding="utf-8")
            city_result = check_module.check_campaign(ready_campaign, scope="full")
            city_rules = {item.get("rule") for item in city_result.get("findings", [])}
            if not {"companion_real_geography_disabled", "companion_real_city_research_missing"} <= city_rules:
                findings.append(_finding("error", "companion_real_city_gate_failed", "Real-city mode must require real public geography and a grounded Research Gate.", campaign_checker, check="companion"))

            legacy_campaign = root / "legacy_rpg"
            shutil.copytree(campaign, legacy_campaign)
            legacy_setup = (legacy_campaign / "setup_profile.yaml").read_text(encoding="utf-8").replace("schema_version: 4", "schema_version: 3", 1)
            legacy_setup = re.sub(r'(?m)^experience_mode:.*\n', "", legacy_setup, count=1)
            (legacy_campaign / "setup_profile.yaml").write_text(legacy_setup, encoding="utf-8")
            for filename in ("companion_profile.yaml", "companion_state.json", "user_context.md"):
                (legacy_campaign / filename).unlink()
            legacy_result = check_module.check_campaign(legacy_campaign, scope="full")
            if legacy_result.get("error_count") != 0:
                findings.append(_finding("error", "companion_legacy_rpg_route_failed", "Schema-v1-v3 workspaces without experience_mode must remain valid RPG workspaces.", campaign_checker, check="companion"))
    except Exception as exc:
        findings.append(_finding("error", "companion_contract_check_failed", str(exc), state_tool, check="companion"))
    return findings


def verify_workspace(workspace: Path, *, campaign: Path | None = None, scope: str = "full") -> dict[str, Any]:
    """Return a structured, read-only verification report."""

    workspace = workspace.resolve()
    campaign_path = (campaign or workspace / "campaign").resolve()
    campaign_findings = _campaign_check(workspace, campaign_path, scope)
    campaign_findings.extend(_companion_contract_check(workspace, campaign_path))
    grouped = {
        "layout": _check_layout(workspace),
        "python": _check_python_sources(workspace),
        "campaign": campaign_findings,
        "dashboard": _dashboard_check(workspace, campaign_path),
    }
    checks: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for check_id, check_findings in grouped.items():
        findings.extend(check_findings)
        errors = sum(item["severity"] == "error" for item in check_findings)
        warnings = sum(item["severity"] == "warning" for item in check_findings)
        infos = sum(item["severity"] == "info" for item in check_findings)
        checks.append(
            {
                "id": check_id,
                "ok": errors == 0,
                "error_count": errors,
                "warning_count": warnings,
                "info_count": infos,
            }
        )
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    infos = sum(item["severity"] == "info" for item in findings)
    return {
        "ok": errors == 0,
        "workspace_path": str(workspace),
        "campaign_path": str(campaign_path),
        "scope": scope,
        "error_count": errors,
        "warning_count": warnings,
        "info_count": infos,
        "checks": checks,
        "findings": findings,
    }


def _print_human(result: dict[str, Any]) -> None:
    print("RePoG workspace verification")
    print(f"Workspace: {result['workspace_path']}")
    for check in result["checks"]:
        status = "PASS" if check["ok"] else "FAIL"
        detail = f"{check['error_count']} errors, {check['warning_count']} warnings"
        print(f"[{status}] {check['id']}: {detail}")
    for item in result["findings"]:
        severity = str(item["severity"]).upper()
        location = f" ({item['path']})" if item.get("path") else ""
        print(f"- {severity} [{item['check']}/{item['rule']}] {item['message']}{location}")
    print(
        f"Result: {'PASS' if result['ok'] else 'FAIL'} "
        f"({result['error_count']} errors, {result['warning_count']} warnings, {result['info_count']} info)"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "workspace",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1]),
        help="Workspace root. Defaults to the parent of this tools directory.",
    )
    parser.add_argument("--campaign", help="Campaign directory. Defaults to <workspace>/campaign.")
    parser.add_argument("--scope", choices=("hot", "full"), default="full")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of the human summary.")
    args = parser.parse_args(argv)
    result = verify_workspace(
        Path(args.workspace),
        campaign=Path(args.campaign) if args.campaign else None,
        scope=args.scope,
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        _print_human(result)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())

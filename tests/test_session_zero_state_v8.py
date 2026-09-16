from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "session_zero_state.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("public_session_zero_state", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


state_tool = _load_module()


SETUP_TEMPLATE = """schema_version: 8
workspace_mode: standalone
status: in_progress
setup_revision: 0
experience_mode: rpg
session_zero_mode: deep
deep_flow_id: rpg_deep_v8
session_zero_state_path: session_zero_state.json
question_target: ""
questions_completed: 0 # derived ledger count
last_checkpoint: 0
ready_for_play: false
"""


@pytest.fixture()
def campaign(tmp_path: Path) -> Path:
    root = tmp_path / "campaign"
    root.mkdir()
    (root / "setup_profile.yaml").write_text(SETUP_TEMPLATE, encoding="utf-8")
    manifest = state_tool.load_manifest(root)
    initial = state_tool.initial_state(manifest)
    (root / "session_zero_state.json").write_text(
        json.dumps(initial, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / "session_zero.md").write_text(
        state_tool.project_session_zero_text("# Session Zero\n\n## Unmanaged Route Notes\n\nKeep me.\n", initial),
        encoding="utf-8",
    )
    return root


def _read_state(campaign: Path) -> dict:
    return json.loads((campaign / "session_zero_state.json").read_text(encoding="utf-8"))


def _write_state(campaign: Path, state: dict) -> None:
    (campaign / "session_zero_state.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _owner_output(campaign: Path, owner_id: str) -> str:
    manifest = state_tool.load_manifest(campaign)
    relative = manifest["owner_refs"][owner_id].removeprefix("campaign/")
    if relative.endswith("/"):
        relative += "_state_test_evidence.md"
    path = campaign.joinpath(*relative.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"materialized {owner_id}\n", encoding="utf-8")
    return relative


def _stage_output_refs(campaign: Path, stage_id: str) -> list[str]:
    manifest = state_tool.load_manifest(campaign)
    stage = next(item for item in manifest["stages"] if item["id"] == stage_id)
    refs: list[str] = []
    for decision in stage["decisions"]:
        for owner_id in decision["owner_refs"]:
            if owner_id in {"setup_progress", "decision_log", "snapshot"}:
                continue
            relative = _owner_output(campaign, owner_id)
            if relative not in refs:
                refs.append(relative)
    return refs


def _structured_value(decision_id: str) -> tuple[object, list[str]]:
    if decision_id == "01_creation_authority":
        return {"mode": "bounded_inference"}, []
    if decision_id == "01_primary_topology_intent":
        return {"primary_topology": "exploration_survival"}, []
    if decision_id == "02_research_need_and_permission":
        return {"status": "not_needed", "permission": "not_needed"}, []
    if decision_id == "02_current_scale_lock":
        return {
            "risk_accepted": False,
            "current_scale_lock_permitted": True,
        }, ["02_research_need_and_permission"]
    if decision_id == "06_topology_activation":
        return {
            "primary_topology": "exploration_survival",
            "build_order": ["places_and_routes", "independent_pressures", "institutions", "npcs"],
        }, ["01_primary_topology_intent"]
    return {"choice": decision_id}, []


def _contract_seed_decisions(revision: int = 1) -> list[dict]:
    definitions = (
        ("01_creation_authority", "01_north_star_authority"),
        ("01_primary_topology_intent", "01_north_star_authority"),
        ("02_research_need_and_permission", "02_research_canon_grounding"),
        ("02_current_scale_lock", "02_research_canon_grounding"),
    )
    result = []
    for decision_id, stage_id in definitions:
        value, dependencies = _structured_value(decision_id)
        result.append(
            {
                "decision_id": decision_id,
                "stage_id": stage_id,
                "status": "locked",
                "source": "player",
                "value": value,
                "depends_on": dependencies,
                "trigger_tags": [],
                "created_revision": revision,
                "revision": revision,
            }
        )
    return result


def _sync_setup(campaign: Path, state: dict) -> None:
    text = (campaign / "setup_profile.yaml").read_text(encoding="utf-8")
    text = state_tool._setup_candidate(text, state)
    (campaign / "setup_profile.yaml").write_text(text, encoding="utf-8")
    summary = (campaign / "session_zero.md").read_text(encoding="utf-8")
    (campaign / "session_zero.md").write_text(
        state_tool.project_session_zero_text(summary, state), encoding="utf-8"
    )


def _decision_payload(
    state: dict,
    decision_id: str,
    stage_id: str,
    *,
    operation_id: str | None = None,
    value: object | None = None,
    status: str = "locked",
    source: str = "player",
    trigger_tags: list[str] | None = None,
) -> dict:
    default_value, default_dependencies = _structured_value(decision_id)
    return {
        "operation_id": operation_id or f"decision-{decision_id}",
        "expected_revision": state["setup_revision"],
        "decision_id": decision_id,
        "stage_id": stage_id,
        "status": status,
        "source": source,
        "value": value if value is not None else default_value,
        "depends_on": default_dependencies,
        "trigger_tags": trigger_tags or [],
    }


def _record_stage_decisions(
    campaign: Path,
    stage_id: str,
    *,
    trigger_for: str = "",
    trigger_tags: list[str] | None = None,
) -> None:
    manifest = state_tool.load_manifest(campaign)
    definition = next(item for item in manifest["stages"] if item["id"] == stage_id)
    for item in definition["decisions"]:
        state = _read_state(campaign)
        state_tool.record_decision(
            campaign,
            _decision_payload(
                state,
                item["id"],
                stage_id,
                trigger_tags=(trigger_tags if item["id"] == trigger_for else []),
            ),
        )


def _complete_stage(campaign: Path, stage_id: str, *, extensions: dict | None = None) -> dict:
    state = _read_state(campaign)
    refs = _stage_output_refs(campaign, stage_id)
    return state_tool.complete_stage(
        campaign,
        {
            "operation_id": f"complete-{stage_id}-{state['setup_revision']}",
            "expected_revision": state["setup_revision"],
            "stage_id": stage_id,
            "output_refs": refs,
            "output_digest": state_tool.compute_output_digest(campaign, refs),
            "extensions": extensions or {},
        },
    )


def test_initial_state_validates_and_summary_is_read_only(campaign: Path) -> None:
    report = state_tool.validate_campaign_state(campaign)
    assert report["ok"] is True
    assert report["findings"] == []
    assert report["state"]["current_stage"] == "01_north_star_authority"

    before = (campaign / "session_zero_state.json").read_bytes()
    rendered = state_tool.render_summary(campaign)
    assert "North Star And Authority" in rendered["markdown"]
    assert (campaign / "session_zero_state.json").read_bytes() == before
    assert "Keep me." in (campaign / "session_zero.md").read_text(encoding="utf-8")


def test_record_decision_syncs_mirrors_and_is_idempotent(campaign: Path) -> None:
    payload = _decision_payload(
        _read_state(campaign),
        "01_campaign_frame_and_reach",
        "01_north_star_authority",
        operation_id="decision-one",
    )
    first = state_tool.record_decision(campaign, payload)
    replay = state_tool.record_decision(campaign, payload)

    assert first["idempotent"] is False
    assert replay["idempotent"] is True
    state = _read_state(campaign)
    assert state["setup_revision"] == 1
    assert state["fatigue"]["decision_count"] == 1
    setup = (campaign / "setup_profile.yaml").read_text(encoding="utf-8")
    assert "setup_revision: 1" in setup
    assert "questions_completed: 1 # derived ledger count" in setup
    summary = (campaign / "session_zero.md").read_text(encoding="utf-8")
    assert "- Setup revision: 1" in summary
    assert "Keep me." in summary


def test_operation_conflict_and_stale_revision_are_rejected(campaign: Path) -> None:
    payload = _decision_payload(
        _read_state(campaign),
        "01_campaign_frame_and_reach",
        "01_north_star_authority",
        operation_id="decision-one",
    )
    state_tool.record_decision(campaign, payload)
    changed = copy.deepcopy(payload)
    changed["value"] = {"choice": "different"}
    with pytest.raises(state_tool.StateError) as conflict:
        state_tool.record_decision(campaign, changed)
    assert conflict.value.category == "operation_conflict"

    stale = _decision_payload(
        _read_state(campaign),
        "01_player_fantasy_tone_and_non_goals",
        "01_north_star_authority",
        operation_id="decision-two",
    )
    stale["expected_revision"] = 0
    with pytest.raises(state_tool.StateError) as revision:
        state_tool.record_decision(campaign, stale)
    assert revision.value.category == "stale_revision"


def test_prepare_ready_operation_id_is_global_across_authorized_reports(campaign: Path) -> None:
    first = campaign / "snapshots" / "first-readiness-report.json"
    first.parent.mkdir(parents=True)
    first.write_text(
        json.dumps({"operation_id": "prepare-ready-global"}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(state_tool.StateError) as conflict:
        state_tool.prepare_ready_evidence(
            campaign,
            operation_id="prepare-ready-global",
            expected_revision=0,
            snapshot_ref="snapshots/unused_session-zero-start/snapshot_manifest.json",
            aggregate_check_ref="snapshots/second-readiness-report.json",
        )
    assert conflict.value.category == "operation_conflict"


def test_new_decision_cannot_skip_the_current_stage(campaign: Path) -> None:
    payload = _decision_payload(
        _read_state(campaign),
        "02_research_need_and_permission",
        "02_research_canon_grounding",
    )
    with pytest.raises(state_tool.StateError) as caught:
        state_tool.record_decision(campaign, payload)
    assert caught.value.category == "stage_order"


def test_controlled_tag_activates_extension_and_stage_requires_evidence(campaign: Path) -> None:
    _record_stage_decisions(
        campaign,
        "01_north_star_authority",
        trigger_for="01_player_fantasy_tone_and_non_goals",
        trigger_tags=["character.inner_life_requested"],
    )
    _complete_stage(campaign, "01_north_star_authority")
    _record_stage_decisions(campaign, "02_research_canon_grounding")
    _complete_stage(campaign, "02_research_canon_grounding")

    state = _read_state(campaign)
    assert state["current_stage"] == "03_character_core"
    assert state["stages"]["03_character_core"]["status"] == "not_started"
    assert state["extensions"]["character_interior"]["status"] == "active"
    state_tool.record_gate(
        campaign,
        {
            "operation_id": "gate-research",
            "expected_revision": state["setup_revision"],
            "gate_id": "research_scope_locked",
            "input_digest": state["stages"]["02_research_canon_grounding"]["output_digest"],
            "output_digest": state_tool._canonical_hash("research-output"),
            "decided_by": "coordinator",
        },
    )
    assert _read_state(campaign)["current_stage"] == "03_character_core"
    _record_stage_decisions(campaign, "03_character_core")

    with pytest.raises(state_tool.StateError) as missing:
        _complete_stage(campaign, "03_character_core")
    assert missing.value.category == "extension_incomplete"

    state = _read_state(campaign)
    interior_refs = [
        _owner_output(campaign, "character_core"),
        _owner_output(campaign, "boundaries"),
    ]
    result = _complete_stage(
        campaign,
        "03_character_core",
        extensions={
            "character_interior": {
                "status": "complete",
                "depth": "baseline",
                "output_refs": interior_refs,
                "output_digest": state_tool.compute_output_digest(campaign, interior_refs),
            }
        },
    )
    assert result["completed_stage"] == "03_character_core"
    assert _read_state(campaign)["extensions"]["character_interior"]["status"] == "complete"
    setup = (campaign / "setup_profile.yaml").read_text(encoding="utf-8")
    assert f"last_checkpoint: {len(state['decisions'])}" in setup

    # Stage 6 may later embed this character into the living world.  The
    # extension digest is completion evidence, not a promise that shared owner
    # files can never be enriched by a downstream stage.
    (campaign / "character_foundation.md").write_text(
        "character foundation enriched downstream\n", encoding="utf-8"
    )
    assert state_tool.validate_campaign_state(campaign)["ok"] is True


def test_unknown_trigger_tag_is_rejected(campaign: Path) -> None:
    payload = _decision_payload(
        _read_state(campaign),
        "01_campaign_frame_and_reach",
        "01_north_star_authority",
        trigger_tags=["model.guessed_a_branch"],
    )
    with pytest.raises(state_tool.StateError) as caught:
        state_tool.record_decision(campaign, payload)
    assert caught.value.category == "input_invalid"


def test_upstream_revision_stales_downstream_and_approval(campaign: Path) -> None:
    _record_stage_decisions(campaign, "01_north_star_authority")
    _complete_stage(campaign, "01_north_star_authority")
    _record_stage_decisions(campaign, "02_research_canon_grounding")
    _complete_stage(campaign, "02_research_canon_grounding")
    state = _read_state(campaign)
    state_tool.record_gate(
        campaign,
        {
            "operation_id": "gate-research",
            "expected_revision": state["setup_revision"],
            "gate_id": "research_scope_locked",
            "input_digest": state["stages"]["02_research_canon_grounding"]["output_digest"],
            "output_digest": state_tool._canonical_hash("out"),
            "decided_by": "coordinator",
        },
    )
    _record_stage_decisions(campaign, "03_character_core")
    _complete_stage(campaign, "03_character_core")

    state = _read_state(campaign)
    existing = next(item for item in state["decisions"] if item["decision_id"] == "01_campaign_frame_and_reach")
    revised = _decision_payload(
        state,
        existing["decision_id"],
        existing["stage_id"],
        operation_id="revise-north-star",
        value={"choice": "revised campaign reach"},
    )
    state_tool.record_decision(campaign, revised)
    changed = _read_state(campaign)

    assert changed["current_stage"] == "01_north_star_authority"
    assert changed["stages"]["01_north_star_authority"]["status"] == "needs_review"
    assert changed["stages"]["02_research_canon_grounding"]["status"] == "stale"
    assert changed["stages"]["03_character_core"]["status"] == "stale"
    assert changed["gates"]["research_scope_locked"]["status"] == "stale"


def test_multiple_needs_review_stages_are_valid_and_earliest_is_current(campaign: Path) -> None:
    state = _read_state(campaign)
    state["stages"]["01_north_star_authority"]["status"] = "needs_review"
    state["stages"]["02_research_canon_grounding"]["status"] = "needs_review"
    state["current_stage"] = "01_north_star_authority"
    _write_state(campaign, state)
    _sync_setup(campaign, state)

    assert state_tool.validate_campaign_state(campaign)["ok"] is True
    state["current_stage"] = "02_research_canon_grounding"
    _write_state(campaign, state)
    _sync_setup(campaign, state)
    report = state_tool.validate_campaign_state(campaign)
    assert report["ok"] is False
    assert report["findings"][0]["code"] == "state_invalid"


def test_complete_evidence_and_setup_mirror_are_validated(campaign: Path) -> None:
    state = _read_state(campaign)
    state["stages"]["01_north_star_authority"]["status"] = "complete"
    state["stages"]["01_north_star_authority"]["completed_revision"] = 1
    state["setup_revision"] = 2
    state["stages"]["02_research_canon_grounding"]["status"] = "active"
    state["current_stage"] = "02_research_canon_grounding"
    _write_state(campaign, state)
    _sync_setup(campaign, state)
    report = state_tool.validate_campaign_state(campaign)
    assert report["ok"] is False
    assert "output evidence" in report["findings"][0]["message"]

    state = state_tool.initial_state(state_tool.load_manifest(campaign))
    _write_state(campaign, state)
    _sync_setup(campaign, state)
    setup = (campaign / "setup_profile.yaml").read_text(encoding="utf-8").replace("questions_completed: 0", "questions_completed: 4")
    (campaign / "setup_profile.yaml").write_text(setup, encoding="utf-8")
    report = state_tool.validate_campaign_state(campaign)
    assert report["ok"] is False
    assert report["findings"][0]["code"] == "mirror_stale"


def test_second_player_approval_can_complete_both_internal_review_gates(campaign: Path) -> None:
    state = _read_state(campaign)
    state["setup_revision"] = 2
    approval_decisions = (
        "09_first_act_frame",
        "09_opening_shape",
        "09_design_direction_review",
        "09_preparation_approval",
    )
    state["decisions"] = _contract_seed_decisions(1) + [
        {
            "decision_id": decision_id,
            "stage_id": "09_first_act_preparation",
            "status": "locked",
            "source": "player",
            "value": {"approved": True},
            "depends_on": [],
            "trigger_tags": [],
            "created_revision": 2,
            "revision": 2,
        }
        for decision_id in approval_decisions
    ]
    state["fatigue"].update(decision_count=len(state["decisions"]), decisions_since_checkpoint=len(state["decisions"]))
    chain_digest = state_tool._canonical_hash("reviewed-chain")
    for stage_id in state_tool.STAGE_IDS[:8]:
        refs = _stage_output_refs(campaign, stage_id)
        state["stages"][stage_id].update(
            status="complete",
            completed_revision=1,
            output_refs=refs,
            output_digest=state_tool.compute_output_digest(campaign, refs),
        )
    state["stages"]["09_first_act_preparation"]["status"] = "active"
    state["current_stage"] = "09_first_act_preparation"
    for gate_id in state_tool.GATE_IDS[:6]:
        gate_input = (
            state["stages"]["02_research_canon_grounding"]["output_digest"]
            if gate_id == "research_scope_locked"
            else chain_digest
        )
        state["gates"][gate_id].update(
            status="complete",
            revision=1,
            input_digest=gate_input,
            output_digest=chain_digest,
            decided_by="coordinator",
        )
    _write_state(campaign, state)
    _sync_setup(campaign, state)

    result = state_tool.record_gate(
        campaign,
        {
            "operation_id": "approve-preparation",
            "expected_revision": 2,
            "gate_id": "preparation_approved",
            "input_digest": chain_digest,
            "output_digest": chain_digest,
            "decided_by": "player",
        },
    )

    assert result["completed_gates"] == ["integrated_review_accepted", "preparation_approved"]
    changed = _read_state(campaign)
    integrated = changed["gates"]["integrated_review_accepted"]
    approved = changed["gates"]["preparation_approved"]
    assert integrated["revision"] == approved["revision"] == 3
    assert integrated["input_digest"] == approved["input_digest"]
    assert integrated["output_digest"] == approved["output_digest"] == chain_digest


def test_internal_review_gate_cannot_close_directly_and_approval_chain_is_strict(campaign: Path) -> None:
    state = _read_state(campaign)
    state["setup_revision"] = 2
    required = (
        "09_first_act_frame",
        "09_opening_shape",
        "09_design_direction_review",
        "09_preparation_approval",
    )
    state["decisions"] = _contract_seed_decisions(1) + [
        {
            "decision_id": decision_id,
            "stage_id": "09_first_act_preparation",
            "status": "locked",
            "source": "player",
            "value": {"approved": True},
            "depends_on": [],
            "trigger_tags": [],
            "created_revision": 2,
            "revision": 2,
        }
        for decision_id in required
    ]
    state["fatigue"].update(decision_count=len(state["decisions"]), decisions_since_checkpoint=len(state["decisions"]))
    for stage_id in state_tool.STAGE_IDS[:8]:
        refs = _stage_output_refs(campaign, stage_id)
        state["stages"][stage_id].update(
            status="complete",
            completed_revision=1,
            output_refs=refs,
            output_digest=state_tool.compute_output_digest(campaign, refs),
        )
    state["stages"]["09_first_act_preparation"]["status"] = "active"
    state["current_stage"] = "09_first_act_preparation"
    chain = state_tool._canonical_hash("reviewed-chain")
    for gate_id in state_tool.GATE_IDS[:6]:
        gate_input = (
            state["stages"]["02_research_canon_grounding"]["output_digest"]
            if gate_id == "research_scope_locked"
            else chain
        )
        state["gates"][gate_id].update(
            status="complete",
            revision=1,
            input_digest=gate_input,
            output_digest=chain,
            decided_by="coordinator",
        )
    _write_state(campaign, state)
    _sync_setup(campaign, state)

    common = {
        "expected_revision": 2,
        "input_digest": chain,
        "output_digest": state_tool._canonical_hash("approved-package"),
        "decided_by": "player",
    }
    with pytest.raises(state_tool.StateError) as internal:
        state_tool.record_gate(
            campaign,
            {**common, "operation_id": "direct-internal", "gate_id": "integrated_review_accepted"},
        )
    assert internal.value.category == "gate_blocked"

    with pytest.raises(state_tool.StateError) as actor:
        state_tool.record_gate(
            campaign,
            {
                **common,
                "operation_id": "non-player-approval",
                "gate_id": "preparation_approved",
                "decided_by": "coordinator",
            },
        )
    assert actor.value.category == "gate_blocked"

    with pytest.raises(state_tool.StateError) as digest:
        state_tool.record_gate(
            campaign,
            {
                **common,
                "operation_id": "wrong-predecessor",
                "gate_id": "preparation_approved",
                "input_digest": state_tool._canonical_hash("wrong"),
            },
        )
    assert digest.value.category == "gate_digest_mismatch"

    with pytest.raises(state_tool.StateError) as changed_package:
        state_tool.record_gate(
            campaign,
            {
                **common,
                "operation_id": "changed-approved-package",
                "gate_id": "preparation_approved",
            },
        )
    assert changed_package.value.category == "gate_digest_mismatch"


def test_require_ready_requires_every_stage_and_gate(campaign: Path) -> None:
    report = state_tool.validate_campaign_state(campaign, require_ready=True)
    assert report["ok"] is False
    assert report["findings"][0]["code"] == "not_ready"


def test_structured_authority_research_and_topology_contracts(campaign: Path) -> None:
    manifest = state_tool.load_manifest(campaign)
    authority = {
        "decision_id": "01_creation_authority",
        "stage_id": "01_north_star_authority",
        "status": "locked",
        "source": "player",
        "value": {"mode": "approval_first"},
        "depends_on": [],
        "trigger_tags": [],
    }
    generated = {
        "decision_id": "04_world_operating_model",
        "stage_id": "04_thin_world_kernel",
        "status": "locked",
        "source": "derived",
        "value": {"accepted": True},
        "depends_on": ["01_creation_authority"],
        "trigger_tags": [],
    }
    with pytest.raises(state_tool.StateError) as blocked:
        state_tool._validate_structured_decisions(
            {"01_creation_authority": authority, "04_world_operating_model": generated},
            manifest,
            state_validation=False,
        )
    assert blocked.value.category == "decision_contract"

    state = state_tool.initial_state(manifest)
    state["stages"]["02_research_canon_grounding"]["status"] = "complete"
    state["decisions"] = _contract_seed_decisions()
    state["decisions"][2]["value"] = {"status": "needed_pending", "permission": "approved"}
    allowed, reason = state_tool._gate_prerequisites(state, "research_scope_locked")
    assert not allowed and "pending" in reason
    state["decisions"][2]["value"] = {"status": "partial_complete", "permission": "approved"}
    allowed, reason = state_tool._gate_prerequisites(state, "research_scope_locked")
    assert not allowed and "risk" in reason

    intent = _contract_seed_decisions()[1]
    activation = {
        "decision_id": "06_topology_activation",
        "stage_id": "06_living_world_ecology",
        "status": "locked",
        "source": "player",
        "value": {
            "primary_topology": "political_intrigue",
            "build_order": manifest["topologies"]["political_intrigue"]["build_order"],
        },
        "depends_on": ["01_primary_topology_intent"],
        "trigger_tags": ["play_focus.political_intrigue"],
    }
    with pytest.raises(state_tool.StateError) as mismatch:
        state_tool._validate_structured_decisions(
            {"01_primary_topology_intent": intent, "06_topology_activation": activation},
            manifest,
            state_validation=False,
        )
    assert mismatch.value.category == "decision_contract"


def test_extension_depths_and_owner_evidence_are_structural(campaign: Path) -> None:
    manifest = state_tool.load_manifest(campaign)
    state = state_tool.initial_state(manifest)
    state["decisions"] = [
        {
            "decision_id": "depth-location",
            "stage_id": "01_north_star_authority",
            "status": "locked",
            "source": "player",
            "value": {},
            "depends_on": [],
            "trigger_tags": ["play_focus.exploration"],
            "created_revision": 1,
            "revision": 1,
        },
        {
            "decision_id": "depth-faction",
            "stage_id": "01_north_star_authority",
            "status": "locked",
            "source": "player",
            "value": {},
            "depends_on": [],
            "trigger_tags": ["information.contested"],
            "created_revision": 1,
            "revision": 1,
        },
    ]
    state_tool._activate_extensions(state, manifest, "test")
    assert state["extensions"]["location_network"]["depth"] == "baseline"
    assert state["extensions"]["faction_information"]["depth"] == "deep"

    with pytest.raises(state_tool.StateError) as unowned:
        state_tool._validate_stage_output_refs(
            manifest,
            "01_north_star_authority",
            ["outputs/fake.md"],
            {},
        )
    assert unowned.value.category == "output_ref_unowned"
    with pytest.raises(state_tool.StateError) as missing:
        state_tool._validate_stage_output_refs(
            manifest,
            "01_north_star_authority",
            ["campaign_one_pager.md"],
            {},
        )
    assert missing.value.category == "output_owner_missing"
    with pytest.raises(state_tool.StateError) as placeholder:
        state_tool._validate_extension_output_refs(
            manifest,
            "location_network",
            "06_living_world_ecology",
            ["location_graph.md", "places/_template.md", "world_dynamics.md", "active_cast.md"],
        )
    assert placeholder.value.category in {"output_ref_unowned", "output_owner_missing"}


def test_downstream_owner_enrichment_does_not_stale_historical_stage_digest(campaign: Path) -> None:
    _record_stage_decisions(campaign, "01_north_star_authority")
    _complete_stage(campaign, "01_north_star_authority")
    output = campaign / _read_state(campaign)["stages"]["01_north_star_authority"]["output_refs"][0]
    output.write_text("legitimately enriched by a downstream stage\n", encoding="utf-8")

    report = state_tool.validate_campaign_state(campaign)
    assert report["ok"] is True


def test_historical_output_references_must_still_exist(campaign: Path) -> None:
    _record_stage_decisions(campaign, "01_north_star_authority")
    _complete_stage(campaign, "01_north_star_authority")
    first_ref = _read_state(campaign)["stages"]["01_north_star_authority"]["output_refs"][0]
    (campaign / first_ref).unlink()

    report = state_tool.validate_campaign_state(campaign)
    assert report["ok"] is False
    assert report["findings"][0]["code"] == "output_missing"


def test_player_approved_stage_nine_preparation_is_frozen(campaign: Path) -> None:
    state = _read_state(campaign)
    package_digest = state_tool._canonical_hash("placeholder")
    for index, stage_id in enumerate(state_tool.STAGE_IDS, start=1):
        refs = _stage_output_refs(campaign, stage_id)
        digest = state_tool.compute_output_digest(campaign, refs)
        state["stages"][stage_id].update(
            status="complete",
            completed_revision=index,
            output_refs=refs,
            output_digest=digest,
        )
        if stage_id == "09_first_act_preparation":
            package_digest = digest

    state["setup_revision"] = 20
    state["current_stage"] = "09_first_act_preparation"
    state["decisions"] = _contract_seed_decisions(1) + [
        {
            "decision_id": "09_first_act_frame",
            "stage_id": "09_first_act_preparation",
            "status": "locked",
            "source": "player",
            "value": {"accepted": True},
            "depends_on": [],
            "trigger_tags": [],
            "created_revision": 10,
            "revision": 10,
        },
        {
            "decision_id": "09_opening_shape",
            "stage_id": "09_first_act_preparation",
            "status": "locked",
            "source": "player",
            "value": {"accepted": True},
            "depends_on": [],
            "trigger_tags": [],
            "created_revision": 10,
            "revision": 10,
        },
        {
            "decision_id": "09_design_direction_review",
            "stage_id": "09_first_act_preparation",
            "status": "locked",
            "source": "player",
            "value": {"accepted": True},
            "depends_on": [],
            "trigger_tags": [],
            "created_revision": 14,
            "revision": 14,
        },
        {
            "decision_id": "09_preparation_approval",
            "stage_id": "09_first_act_preparation",
            "status": "locked",
            "source": "player",
            "value": {"accepted": True},
            "depends_on": [],
            "trigger_tags": [],
            "created_revision": 17,
            "revision": 17,
        },
    ]
    state["fatigue"].update(decision_count=len(state["decisions"]), decisions_since_checkpoint=len(state["decisions"]))
    for index, gate_id in enumerate(state_tool.GATE_IDS[:8], start=11):
        gate_input = (
            state["stages"]["02_research_canon_grounding"]["output_digest"]
            if gate_id == "research_scope_locked"
            else package_digest
        )
        state["gates"][gate_id].update(
            status="complete",
            revision=index,
            input_digest=gate_input,
            output_digest=package_digest,
            decided_by=(
                "player"
                if gate_id in {"design_direction_approved", "preparation_approved"}
                else "coordinator"
            ),
            invalidation_reason="",
        )
    _write_state(campaign, state)
    _sync_setup(campaign, state)
    assert state_tool.validate_campaign_state(campaign)["ok"] is True

    stage_nine_ref = state["stages"]["09_first_act_preparation"]["output_refs"][0]
    (campaign / stage_nine_ref).write_text(
        "changed after Player approval\n",
        encoding="utf-8",
    )
    report = state_tool.validate_campaign_state(campaign)
    assert report["ok"] is False
    assert report["findings"][0]["code"] == "output_drift"


def test_atomic_bundle_rolls_back_setup_and_summary_on_state_failure(
    campaign: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = {
        name: (campaign / name).read_bytes()
        for name in ("session_zero_state.json", "setup_profile.yaml", "session_zero.md")
    }
    original = state_tool._atomic_bytes
    failed = False

    def fail_state_once(path: Path, payload: bytes) -> None:
        nonlocal failed
        if path.name == "session_zero_state.json" and not failed:
            failed = True
            raise OSError("simulated state replacement failure")
        original(path, payload)

    monkeypatch.setattr(state_tool, "_atomic_bytes", fail_state_once)
    payload = _decision_payload(
        _read_state(campaign),
        "01_campaign_frame_and_reach",
        "01_north_star_authority",
    )
    with pytest.raises(state_tool.StateError) as caught:
        state_tool.record_decision(campaign, payload)
    assert caught.value.category == "commit_failed"
    for name, expected in before.items():
        assert (campaign / name).read_bytes() == expected

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT
DEEP_V8 = PUBLIC / "workflows" / "worldbuild" / "deep_v8"
MANIFEST_PATH = DEEP_V8 / "manifest.json"
STATE_TOOL = PUBLIC / "tools" / "session_zero_state.py"
CHECK_STATE_TOOL = PUBLIC / "tools" / "check_state.py"
SNAPSHOT_TOOL = PUBLIC / "tools" / "snapshot.py"

STAGE_IDS = [
    "01_north_star_authority",
    "02_research_canon_grounding",
    "03_character_core",
    "04_thin_world_kernel",
    "05_character_realization_mechanics",
    "06_living_world_ecology",
    "07_runtime_experience_contract",
    "08_reciprocity_campaign_horizon",
    "09_first_act_preparation",
]
GATE_IDS = [
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
]
EXTENSION_STAGES = {
    "character_interior": ["03_character_core"],
    "world_fabric": ["04_thin_world_kernel"],
    "mechanics_detail": ["05_character_realization_mechanics"],
    "location_network": ["06_living_world_ecology"],
    "faction_information": ["06_living_world_ecology"],
    "group": ["06_living_world_ecology"],
    "character_embedding": ["06_living_world_ecology"],
    "advancement_detail": ["08_reciprocity_campaign_horizon"],
    "campaign_architecture": [
        "08_reciprocity_campaign_horizon",
        "09_first_act_preparation",
    ],
}
TOPOLOGIES = {
    "exploration_survival": {
        "build_order": [
            "places_and_routes",
            "independent_pressures",
            "institutions",
            "npcs",
        ],
        "trigger_tag": "play_focus.exploration",
        "extension": "location_network",
    },
    "political_intrigue": {
        "build_order": [
            "independent_pressures",
            "institutions",
            "reach_and_places",
            "representatives",
        ],
        "trigger_tag": "play_focus.political_intrigue",
        "extension": "faction_information",
    },
    "personal_drama": {
        "build_order": [
            "everyday_places",
            "institutions",
            "npc_relationships",
            "independent_pressures",
        ],
        "trigger_tag": "character.deep_personal_integration",
        "extension": "character_embedding",
    },
}


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


session_zero_state = _load_module("repog_session_zero_state_v8", STATE_TOOL)
check_state = _load_module("repog_check_state_v8", CHECK_STATE_TOOL)
snapshot_tool = _load_module("repog_snapshot_v8", SNAPSHOT_TOOL)


@pytest.fixture(scope="module")
def manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _set_setup(campaign: Path, **changes: str | int) -> None:
    path = campaign / "setup_profile.yaml"
    text = path.read_text(encoding="utf-8")
    for key, value in changes.items():
        pattern = rf"(?m)^{re.escape(key)}:\s*.*?$"
        assert re.search(pattern, text), key
        text = re.sub(pattern, f"{key}: {value}", text, count=1)
    path.write_text(text, encoding="utf-8")


def _set_profile(campaign: Path, filename: str, **changes: str | int) -> None:
    path = campaign / filename
    text = path.read_text(encoding="utf-8")
    for key, value in changes.items():
        pattern = rf"(?m)^{re.escape(key)}:\s*.*?$"
        assert re.search(pattern, text), (filename, key)
        text = re.sub(pattern, f"{key}: {value}", text, count=1)
    path.write_text(text, encoding="utf-8")


def _new_deep_campaign(tmp_path: Path, manifest: dict[str, Any]) -> Path:
    campaign = tmp_path / "campaign"
    shutil.copytree(PUBLIC / "campaign", campaign)
    _set_setup(
        campaign,
        status="in_progress",
        experience_mode="rpg",
        session_zero_mode="deep",
        question_target='""',
        setup_revision=0,
        questions_completed=0,
        last_checkpoint=0,
    )
    state = session_zero_state.initial_state(manifest)
    (campaign / "session_zero_state.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary_path = campaign / "session_zero.md"
    summary_path.write_text(
        session_zero_state.project_session_zero_text(
            summary_path.read_text(encoding="utf-8"),
            state,
        ),
        encoding="utf-8",
    )
    report = session_zero_state.validate_campaign_state(campaign)
    assert report["ok"], report["findings"]
    return campaign


def _campaign_ref(owner_path: str) -> str:
    assert owner_path.startswith("campaign/")
    return owner_path.removeprefix("campaign/").rstrip("/")


def _digest(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _owner_output(owner_ref: str, manifest: dict[str, Any]) -> str:
    owner_path = manifest["owner_refs"][owner_ref]
    relative = _campaign_ref(owner_path)
    canonical = PUBLIC / owner_path
    if owner_path.endswith("/") or canonical.is_dir():
        return f"{relative}/_deep_v8_test_evidence.md"
    return relative


def _materialize_outputs(campaign: Path, output_refs: list[str]) -> None:
    for relative in output_refs:
        path = campaign.joinpath(*relative.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            source = PUBLIC / "campaign" / Path(*relative.split("/"))
            if source.is_file():
                shutil.copy2(source, path)
            else:
                path.write_text(f"# {relative}\n\nStable integration-test evidence.\n", encoding="utf-8")


def _owner_outputs(stage: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for decision in stage["decisions"]:
        for owner_ref in decision["owner_refs"]:
            relative = _owner_output(owner_ref, manifest)
            if relative in {"setup_profile.yaml", "session_zero.md", "session_zero_state.json"}:
                continue
            if relative not in refs:
                refs.append(relative)
    assert refs, stage["id"]
    return refs


def _record_stage_decisions(
    campaign: Path,
    stage: dict[str, Any],
    *,
    topology: str,
    topology_trigger: str = "",
    decision_ids: set[str] | None = None,
) -> None:
    manifest = session_zero_state.load_manifest(campaign)
    for definition in stage["decisions"]:
        decision_id = definition["id"]
        if decision_ids is not None and decision_id not in decision_ids:
            continue
        state = session_zero_state.validate_campaign_state(campaign)["state"]
        before_count = len(state["decisions"])
        value: Any = {"accepted": decision_id}
        depends_on: list[str] = []
        trigger_tags: list[str] = []
        if decision_id == "01_creation_authority":
            value = {"mode": "bounded_inference"}
        elif decision_id == "01_primary_topology_intent":
            value = {"primary_topology": topology}
        elif decision_id == "02_research_need_and_permission":
            value = {"status": "not_needed", "permission": "not_needed"}
        elif decision_id == "02_current_scale_lock":
            value = {"risk_accepted": False, "current_scale_lock_permitted": True}
            depends_on = ["02_research_need_and_permission"]
        elif decision_id == "06_topology_activation":
            value = {
                "primary_topology": topology,
                "build_order": TOPOLOGIES[topology]["build_order"],
            }
            depends_on = ["01_primary_topology_intent"]
            trigger_tags = [topology_trigger]
        authority_contract = manifest["structured_contracts"]["creation_authority"]
        if (
            decision_id in authority_contract["world_generative_decision_ids"]
            and not definition["critical"]
        ):
            depends_on.append("01_creation_authority")
        result = session_zero_state.record_decision(
            campaign,
            {
                "operation_id": f"decision-{topology}-{decision_id}",
                "expected_revision": state["setup_revision"],
                "decision_id": decision_id,
                "stage_id": stage["id"],
                "status": "locked",
                "source": "player" if definition["critical"] else "derived",
                "value": value,
                "depends_on": depends_on,
                "trigger_tags": trigger_tags,
            },
        )
        assert result["ok"] and not result["idempotent"]
        assert result["decision_count"] == before_count + 1
        assert result["setup_revision"] == state["setup_revision"] + 1


def _complete_stage(
    campaign: Path,
    stage: dict[str, Any],
    manifest: dict[str, Any],
    *,
    topology: str,
) -> dict[str, Any]:
    state = session_zero_state.validate_campaign_state(campaign)["state"]
    output_refs = _owner_outputs(stage, manifest)
    extension_evidence: dict[str, Any] = {}
    for extension_id in stage["extensions"]:
        portion = state["extensions"][extension_id]["stages"][stage["id"]]
        if portion["status"] != "active":
            continue
        stage_owner_refs = manifest["extensions"][extension_id].get("stage_owner_refs", {})
        extension_owner_ids = stage_owner_refs.get(
            stage["id"], manifest["extensions"][extension_id]["owner_refs"]
        )
        extension_refs = [
            _owner_output(owner_ref, manifest)
            for owner_ref in extension_owner_ids
            if owner_ref not in {"setup_progress", "decision_log", "snapshot"}
        ]
        _materialize_outputs(campaign, extension_refs)
        extension_evidence[extension_id] = {
            "status": "complete",
            "depth": state["extensions"][extension_id]["depth"],
            "output_refs": extension_refs,
            "output_digest": session_zero_state.compute_output_digest(campaign, extension_refs),
            "acceptance_decision_id": "",
        }
    _materialize_outputs(campaign, output_refs)
    result = session_zero_state.complete_stage(
        campaign,
        {
            "operation_id": f"complete-{topology}-{stage['id']}",
            "expected_revision": state["setup_revision"],
            "stage_id": stage["id"],
            "output_refs": output_refs,
            "output_digest": session_zero_state.compute_output_digest(campaign, output_refs),
            "extensions": extension_evidence,
        },
    )
    assert result["ok"] and result["completed_stage"] == stage["id"]
    return result


def _record_gate(
    campaign: Path,
    *,
    topology: str,
    gate_id: str,
    input_digest: str,
    output_digest: str,
    decided_by: str = "coordinator",
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = session_zero_state.validate_campaign_state(campaign)["state"]
    result = session_zero_state.record_gate(
        campaign,
        {
            "operation_id": f"gate-{topology}-{gate_id}",
            "expected_revision": state["setup_revision"],
            "gate_id": gate_id,
            "input_digest": input_digest,
            "output_digest": output_digest,
            "decided_by": decided_by,
            "evidence": evidence or {},
        },
    )
    assert result["ok"] and result["completed_gate"] == gate_id
    return result


def _materialize_ready_runtime_contract(
    campaign: Path,
    topology: str,
    *,
    setup_revision: int,
) -> None:
    """Materialize a small but genuinely playable campaign for final-gate tests.

    The replay used to prove only that Stage 9 files existed.  Deep v8's final
    evidence helper deliberately runs the real full-state checker, so the
    fixture must now satisfy the same runtime contract as a user campaign.
    """

    play_profile = (campaign / "play_profile.yaml").read_text(encoding="utf-8")
    replacements = {
        '  turn_protocol: ""': "  turn_protocol: fast",
        '  cold_distill_policy: ""': "  cold_distill_policy: scene_checkpoint_or_5_durable",
        '  validation_policy: ""': "  validation_policy: hot_each_durable_full_on_distill",
        '  style_review_policy: ""': "  style_review_policy: sampled_and_distill",
        "  estimate_acknowledged: false": "  estimate_acknowledged: true",
        "    anchors: []": (
            "    anchors:\n"
            "      - grounded causal detail\n"
            "      - distinct social voices\n"
            "      - player-owned interiority"
        ),
        '  cadence: ""': "  cadence: arc",
        '  presentation: ""': "  presentation: automatic_fictional",
    }
    for old, new in replacements.items():
        assert old in play_profile, old
        play_profile = play_profile.replace(old, new, 1)
    (campaign / "play_profile.yaml").write_text(play_profile, encoding="utf-8")

    system_fit_path = campaign / "system_fit.md"
    system_fit = system_fit_path.read_text(encoding="utf-8")
    system_fit += "\n- Profile: `fast`\n- Estimate caveat acknowledged: yes\n"
    system_fit_path.write_text(system_fit, encoding="utf-8")

    session_zero_path = campaign / "session_zero.md"
    session_zero = session_zero_path.read_text(encoding="utf-8")
    session_zero += "\n- Turn protocol: `fast`\n- Performance estimate acknowledged: yes\n"
    session_zero_path.write_text(session_zero, encoding="utf-8")

    boundaries_path = campaign / "boundaries.md"
    boundaries = boundaries_path.read_text(encoding="utf-8")
    boundaries = boundaries.replace(
        "\n-\n\n## Bad GM Behavior",
        "\n- Return control after a concrete causal consequence.\n\n## Bad GM Behavior",
        1,
    )
    boundaries = boundaries.rstrip()
    assert boundaries.endswith("-")
    boundaries = boundaries[:-1] + "- Decide the Player character's feelings or choices.\n"
    boundaries_path.write_text(boundaries, encoding="utf-8")

    research_path = campaign / "research_dossier.md"
    research = research_path.read_text(encoding="utf-8")
    research = research.replace("- Status: `needed_pending`", "- Status: `not_needed`", 1)
    research = research.replace("- Current-scale lock permitted: no", "- Current-scale lock permitted: yes", 1)
    research_path.write_text(research, encoding="utf-8")

    (campaign / "current_state.yaml").write_text(
        f"""campaign_id: deep_v8_{topology}
mode: lite
memory_version: 3
continuity_revision: 0
status: active
last_updated: ""

persistence:
  last_distilled_revision: 0
  durable_turns_since_distill: 0
  pending_cold_targets: []

fictional_time:
  day: 1
  phase: morning
  elapsed_index: 0

player:
  name: Mira
  concept: A capable local seeking the truth behind a changing harbor
  level_band: beginner
  stat_budget_policy: standard
  stat_budget_note: ""
  condition: ready
  current_goal: Understand the harbor's disrupted deliveries
  stats: {{}}
  capabilities:
    - careful observation

current_scene:
  title: Morning at Test Harbor
  location: Test Harbor
  summary: Mira stands where ordinary deliveries have begun to falter.
  present_npcs: []
  immediate_pressure: A delayed supply boat is changing the morning routine.
  open_choices: []

scene_frame:
  scene_id: opening-test-harbor
  mode: ambient
  ongoing_process: Dock crews continue sorting delayed deliveries.
  disruption: One expected supply boat has not arrived.
  last_causal_beat:
    player_intent: Arrive and take in the situation.
    world_response: The disrupted harbor routine is visible.
    changed_fact: Mira can now choose how to engage with the delay.
    returned_control_at: Mira has the harbor and its ordinary routes before her.
  pending_consequences: []
  resume_anchor: Mira stands at the public quay while the morning work continues.

inventory: []
conditions: []
active_clocks: []
active_threats: []
""",
        encoding="utf-8",
    )

    (campaign / "threads.md").write_text(
        f"""# Threads

As of revision: 0

## Arc Compass

- Act name: The Missing Morning Boat
- Dramatic question: What changed the harbor's dependable supply route?
- Active pressures: Essential deliveries are beginning to fall behind.
- Setups awaiting payoff: The missing boat and the altered dock routine.
- Climax availability conditions: Mira can identify and reach the cause of the disruption.
- Closure conditions: The route's immediate future is decided through play.
- Player interest signals: Investigation, local relationships, and open movement.

### Act Scope

- Places this act can reach: Test Harbor and the public road inland.
- People who belong to it: Harbor workers and people affected by the delay.
- What is already in motion as it opens: The delivery backlog is growing.
- What stays true if the character does nothing: The harbor adapts without centering Mira.

## Active Threads

### Delayed Deliveries

- Status: active
- Pressure: The harbor's ordinary supply rhythm is slipping.
- Who cares: Workers and residents who rely on the route.
- What the player knows: One expected boat is late.
- What is hidden: Why it is late.
- Related issue or world-domain reference: Harbor supply disruption.
- Next player-relevant question or consequence: Whether Mira investigates, helps, waits, or leaves.
- Last changed revision: 0
""",
        encoding="utf-8",
    )

    (campaign / "issues.md").write_text(
        """# Issues

## Current Issues

### Harbor Supply Disruption

- Status: current
- What is wrong: A dependable delivery route has stopped keeping its schedule.
- Who benefits: Opportunists able to exploit temporary scarcity.
- Who suffers: Workers and residents relying on ordinary deliveries.
- Visible signs: A growing backlog and changed dock routines.
- What happens if ignored: The harbor adapts while shortages spread inland.
- Side conditions, three or four: weather, labor, storage, and rumor affect the outcome.
- Counter-current: Local workers are already finding practical workarounds.
- Open question: What interrupted the route?
- Related places: Test Harbor
""",
        encoding="utf-8",
    )

    world_path = campaign / "world.md"
    world = world_path.read_text(encoding="utf-8")
    start = world.index("## World Operating Model")
    end = world.index("## Macro Frame And Powers")
    operating_model = """## World Operating Model

The harbor survives through ordinary scheduled deliveries. Their interruption
benefits short-term opportunists, costs workers and residents time and money,
and becomes visible through queues, prices, changed routines, and rumor. If no
one intervenes, local institutions improvise unevenly rather than waiting for
the Player. News travels by direct conversation and routine messengers.

"""
    world_path.write_text(world[:start] + operating_model + world[end:], encoding="utf-8")

    place_path = campaign / "places" / "test_harbor.md"
    place_path.write_text(
        """# Test Harbor

Tier: T2

## Baseline Routine

Crews unload scheduled boats, sort deliveries, and exchange local news.

## Presence Logic

Workers, residents, and travelers use the public quay for ordinary business.
""",
        encoding="utf-8",
    )
    (campaign / "places" / "public_road.md").write_text(
        """# Public Road

Tier: T1

## Baseline Routine

Residents and delivery carts travel between the harbor and inland streets.

## Presence Logic

Public traffic uses the road throughout the working day.
""",
        encoding="utf-8",
    )
    (campaign / "location_graph.md").write_text(
        f"""# Location Graph

Campaign id: `deep_v8_{topology}`

As of revision: 0

| From | Direction | To | Travel | Access | Visibility | Ordinary traffic | Conditions | Player-known | Last changed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Test Harbor | <-> | Public Road | short walk | public | open | workers and carts | none | yes | setup |
""",
        encoding="utf-8",
    )

    arc_closure_path = campaign / "arc_closure.md"
    arc_closure = arc_closure_path.read_text(encoding="utf-8")
    arc_closure = arc_closure.replace(
        "- Advancement presentation: none",
        "- Advancement presentation: automatic_fictional",
        1,
    )
    arc_closure_path.write_text(arc_closure, encoding="utf-8")

    first_session = (campaign / "first_session.md").read_text(encoding="utf-8")
    first_session = first_session.replace("Campaign id: `new_campaign`", f"Campaign id: `deep_v8_{topology}`", 1)
    first_session = first_session.replace("Prep status: `drafting`", "Prep status: `materialized`", 1)
    (campaign / "first_session.md").write_text(first_session, encoding="utf-8")

    (campaign / "opening_brief.md").write_text(
        "\n".join(
            [
                "# Opening Brief",
                "",
                f"Campaign id: `deep_v8_{topology}`",
                "",
                "Opening status: `active`",
                "",
                "## Opening Type",
                "",
                "`first_campaign_opening`",
                "",
                "## Scene Mode",
                "",
                "`ambient`",
                "",
                "## Where",
                "",
                "- Location: Test Harbor",
                "",
                "## What Kind Of Place",
                "",
                "A working public quay where crews sort deliveries and neighbors exchange news.",
                "",
                "## When And How The Character Arrived",
                "",
                "Mira came to the harbor this morning on an ordinary personal errand.",
                "",
                "## Player-Known Context",
                "",
                "The morning boat normally arrives before the busiest unloading work begins.",
                "",
                "## Immediate Visible Situation",
                "",
                "The boat is absent, the expected cargo space is empty, and work continues around the delay.",
                "",
                "## Neutral Action Space",
                "",
                "Mira may observe, help with ordinary work, ask around, wait, or leave by the public road.",
                "",
                "## Pressure Or Hook",
                "",
                "A delayed supply boat is beginning to alter the harbor's otherwise familiar routine.",
                "",
                "## Player-Facing Opening Draft",
                "",
                "Morning work continues at Test Harbor around one conspicuously empty berth. Mira has time to decide whether the delay matters to her.",
                "",
                f"- Primary topology: {topology}",
                "- Immediate pressure: A visible situation will worsen if nobody acts.",
                "- Available affordances: observe, approach, withdraw, negotiate, or improvise.",
                "- No fixed outcome: consequences follow the Player's chosen action.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_manifest_and_stage_corpus_are_referentially_closed(manifest: dict[str, Any]) -> None:
    assert manifest["schema_version"] == 8
    assert manifest["workflow_id"] == "rpg_deep_v8"
    assert manifest["statuses"] == {
        "stage": ["not_started", "active", "needs_review", "complete", "stale"],
        "decision": ["locked", "defaulted", "deferred"],
        "extension": ["not_applicable", "active", "complete", "defaulted"],
    }

    stages = manifest["stages"]
    gates = manifest["gates"]
    stage_ids = [stage["id"] for stage in stages]
    gate_ids = [gate["id"] for gate in gates]
    assert stage_ids == STAGE_IDS
    assert gate_ids == GATE_IDS
    assert {
        extension_id: definition["stages"]
        for extension_id, definition in manifest["extensions"].items()
    } == EXTENSION_STAGES
    assert "source_grounding" not in manifest["extensions"]

    owner_refs = manifest["owner_refs"]
    decision_ids: list[str] = []
    stage_extensions: dict[str, list[str]] = {stage_id: [] for stage_id in STAGE_IDS}
    for extension_id, definition in manifest["extensions"].items():
        assert definition["owner_refs"]
        assert set(definition["owner_refs"]) <= set(owner_refs)
        for stage_id in definition["stages"]:
            stage_extensions[stage_id].append(extension_id)

    for owner_id, owner_path in owner_refs.items():
        assert owner_id and owner_path.startswith("campaign/")
        assert (PUBLIC / owner_path).exists(), f"missing owner target: {owner_id} -> {owner_path}"

    known_prerequisites = set(STAGE_IDS) | set(GATE_IDS)
    for stage in stages:
        assert stage["extensions"] == stage_extensions[stage["id"]]
        assert set(stage["prerequisites"]) <= known_prerequisites
        playbook = DEEP_V8 / stage["playbook"]
        assert playbook.is_file()
        playbook_text = playbook.read_text(encoding="utf-8")
        for decision in stage["decisions"]:
            decision_ids.append(decision["id"])
            assert isinstance(decision["critical"], bool)
            assert isinstance(decision["defer_allowed"], bool)
            assert decision["owner_refs"]
            assert set(decision["owner_refs"]) <= set(owner_refs)
            assert decision["id"] in playbook_text
            if decision["critical"]:
                assert decision["owner_refs"], decision["id"]
    assert len(decision_ids) == len(set(decision_ids))
    assert len(decision_ids) == 43

    decisions_by_stage = {
        stage["id"]: [decision["id"] for decision in stage["decisions"]]
        for stage in stages
    }
    assert decisions_by_stage["03_character_core"] == [
        "03_identity_seed",
        "03_current_desire_and_why_now",
        "03_tested_direction_and_protected_growth",
        "03_protected_past_and_relationship_authorship",
    ]
    assert decisions_by_stage["04_thin_world_kernel"] == [
        "04_world_operating_model",
        "04_macro_frame_and_local_channels",
        "04_starting_aperture",
        "04_world_palette",
        "04_independent_pressures",
        "04_everyday_life_and_open_unknowns",
    ]
    decisions_by_id = {
        decision["id"]: decision
        for stage in stages
        for decision in stage["decisions"]
    }
    assert decisions_by_id["01_content_boundaries"]["owner_refs"] == ["boundaries"]
    assert decisions_by_id["01_agency_authorship_and_consequence"]["owner_refs"] == [
        "boundaries"
    ]
    assert decisions_by_id["04_world_palette"]["owner_refs"] == ["palette"]
    assert decisions_by_stage["05_character_realization_mechanics"] == [
        "05_character_surface_and_world_read",
        "05_social_position_access_and_belonging",
        "05_resolution_grounding",
        "05_reliable_competence_and_special_capabilities",
        "05_limitation_cost_and_counterplay",
        "05_simulation_fidelity",
    ]
    assert decisions_by_stage["08_reciprocity_campaign_horizon"] == [
        "08_two_way_reciprocity",
        "08_anchor_or_explicit_isolation",
        "08_advancement_and_reward_rhythm",
        "08_campaign_horizon",
        "08_continuity_and_preparation_contract",
    ]
    assert {
        "03_surface_appearance_and_public_read",
        "03_social_position_and_belonging",
        "05_progression_contract",
    }.isdisjoint(decision_ids)

    triggered_extensions: set[str] = set()
    for tag, rule in manifest["controlled_trigger_tags"].items():
        assert tag and rule["activate"]
        assert set(rule["activate"]) <= set(manifest["extensions"])
        triggered_extensions.update(rule["activate"])
    assert triggered_extensions == set(manifest["extensions"])

    assert manifest["topologies"] == {
        topology: {
            "activation_trigger": definition["trigger_tag"],
            "build_order": definition["build_order"],
        }
        for topology, definition in TOPOLOGIES.items()
    } | {
        "mixed": {
            "build_order": [
                "stage_01_primary_topology",
                "primary_prerequisites_complete",
                "one_secondary_topology",
            ],
            "secondary_limit": 1,
        }
    }

    approval_ids = {
        decision_id
        for decision_id in decision_ids
        if decision_id.endswith("_review") or decision_id.endswith("_approval")
    }
    assert approval_ids == {"09_design_direction_review", "09_preparation_approval"}
    assert "09_integrated_preparation_review" not in decision_ids

    gate_map = {gate["id"]: gate for gate in gates}
    integrated = " ".join(gate_map["integrated_review_accepted"]["prerequisites"])
    preparation = " ".join(gate_map["preparation_approved"]["prerequisites"])
    assert "09_preparation_approval" in integrated
    assert "digest" in integrated.casefold()
    assert "integrated_review_accepted" in preparation
    assert "09_preparation_approval" in preparation
    assert "no content changed" in preparation.casefold()

    stage_nine_text = (DEEP_V8 / "09_first_act_preparation.md").read_text(encoding="utf-8")
    assert stage_nine_text.index("record `draft_preflight_passed`") < stage_nine_text.index(
        "`session-zero-start` snapshot"
    )
    assert stage_nine_text.index("`session-zero-start` snapshot") < stage_nine_text.index(
        "final aggregate check"
    )
    assert stage_nine_text.index("final aggregate check") < stage_nine_text.index(
        "`ready_and_snapshotted`"
    )


@pytest.mark.parametrize("topology", list(TOPOLOGIES))
def test_topology_replay_reaches_ready_through_the_full_lifecycle(
    tmp_path: Path,
    manifest: dict[str, Any],
    topology: str,
) -> None:
    campaign = _new_deep_campaign(tmp_path, manifest)
    stages = {stage["id"]: stage for stage in manifest["stages"]}
    topology_contract = TOPOLOGIES[topology]

    for stage_id in STAGE_IDS[:8]:
        stage = stages[stage_id]
        if stage_id == "06_living_world_ecology":
            before = session_zero_state.validate_campaign_state(campaign)["state"]
            assert before["extensions"][topology_contract["extension"]]["status"] == "not_applicable"
        _record_stage_decisions(
            campaign,
            stage,
            topology=topology,
            topology_trigger=(topology_contract["trigger_tag"] if stage_id == "06_living_world_ecology" else ""),
        )
        if stage_id == "06_living_world_ecology":
            activated = session_zero_state.validate_campaign_state(campaign)["state"]
            assert activated["extensions"][topology_contract["extension"]]["status"] == "active"
        _complete_stage(campaign, stage, manifest, topology=topology)
        if stage_id == "02_research_canon_grounding":
            state = session_zero_state.validate_campaign_state(campaign)["state"]
            _record_gate(
                campaign,
                topology=topology,
                gate_id="research_scope_locked",
                input_digest=state["stages"][stage_id]["output_digest"],
                output_digest=_digest(f"{topology}-research-scope-locked"),
            )

    state = session_zero_state.validate_campaign_state(campaign)["state"]
    research_output = state["gates"]["research_scope_locked"]["output_digest"]
    _record_gate(
        campaign,
        topology=topology,
        gate_id="stages_1_8_complete",
        input_digest=research_output,
        output_digest=_digest(f"{topology}-stages-1-8-complete"),
    )

    stage_nine = stages["09_first_act_preparation"]
    _record_stage_decisions(
        campaign,
        stage_nine,
        topology=topology,
        decision_ids={"09_first_act_frame", "09_opening_shape"},
    )
    state = session_zero_state.validate_campaign_state(campaign)["state"]
    stages_gate_output = state["gates"]["stages_1_8_complete"]["output_digest"]
    _record_gate(
        campaign,
        topology=topology,
        gate_id="first_act_design_complete",
        input_digest=stages_gate_output,
        output_digest=_digest(f"{topology}-first-act-design"),
    )

    _record_stage_decisions(
        campaign,
        stage_nine,
        topology=topology,
        decision_ids={"09_design_direction_review"},
    )
    state = session_zero_state.validate_campaign_state(campaign)["state"]
    first_act_output = state["gates"]["first_act_design_complete"]["output_digest"]
    design_gate = _record_gate(
        campaign,
        topology=topology,
        gate_id="design_direction_approved",
        input_digest=first_act_output,
        output_digest=_digest(f"{topology}-player-approved-design"),
        decided_by="player",
    )
    assert design_gate["completed_gates"] == ["design_direction_approved"]

    stage_nine_refs = _owner_outputs(stage_nine, manifest)
    _materialize_outputs(campaign, stage_nine_refs)
    _materialize_ready_runtime_contract(
        campaign,
        topology,
        setup_revision=session_zero_state.validate_campaign_state(campaign)["state"]["setup_revision"],
    )
    preparation_digest = session_zero_state.compute_output_digest(campaign, stage_nine_refs)
    state = session_zero_state.validate_campaign_state(campaign)["state"]
    design_output = state["gates"]["design_direction_approved"]["output_digest"]
    _record_gate(
        campaign,
        topology=topology,
        gate_id="preparation_materialized",
        input_digest=design_output,
        output_digest=preparation_digest,
    )

    cross_read_digest = preparation_digest
    _record_gate(
        campaign,
        topology=topology,
        gate_id="cross_read_passed",
        input_digest=preparation_digest,
        output_digest=cross_read_digest,
    )
    _record_stage_decisions(
        campaign,
        stage_nine,
        topology=topology,
        decision_ids={"09_preparation_approval"},
    )
    second_approval = _record_gate(
        campaign,
        topology=topology,
        gate_id="preparation_approved",
        input_digest=cross_read_digest,
        output_digest=cross_read_digest,
        decided_by="player",
    )
    assert second_approval["completed_gates"] == [
        "integrated_review_accepted",
        "preparation_approved",
    ]

    _complete_stage(campaign, stage_nine, manifest, topology=topology)
    state = session_zero_state.validate_campaign_state(campaign)["state"]
    preparation_output = state["gates"]["preparation_approved"]["output_digest"]
    draft_preflight_digest = _digest(f"{topology}-draft-preflight")
    _record_gate(
        campaign,
        topology=topology,
        gate_id="draft_preflight_passed",
        input_digest=preparation_output,
        output_digest=draft_preflight_digest,
    )

    state_before_ready = session_zero_state.validate_campaign_state(campaign)["state"]
    final_revision = state_before_ready["setup_revision"]
    _set_profile(
        campaign,
        "play_profile.yaml",
        profile_status="locked",
        source_setup_revision=final_revision,
    )
    _set_profile(
        campaign,
        "companion_profile.yaml",
        profile_status="inactive",
        source_setup_revision=final_revision,
    )
    snapshot_result = snapshot_tool.create_snapshot(campaign, "session-zero-start")
    assert snapshot_result["ok"], snapshot_result
    snapshot_ref = (
        Path(snapshot_result["snapshot_path"]).relative_to(campaign) / "snapshot_manifest.json"
    ).as_posix()
    aggregate_ref = f"snapshots/{topology}-readiness-report.json"
    prepared = session_zero_state.prepare_ready_evidence(
        campaign,
        operation_id=f"prepare-ready-{topology}",
        expected_revision=final_revision,
        snapshot_ref=snapshot_ref,
        aggregate_check_ref=aggregate_ref,
    )
    evidence = prepared["evidence"]
    snapshot_digest = evidence["snapshot_digest"]
    revision_before_gate = session_zero_state.validate_campaign_state(campaign)["state"]["setup_revision"]
    _record_gate(
        campaign,
        topology=topology,
        gate_id="ready_and_snapshotted",
        input_digest=draft_preflight_digest,
        output_digest=snapshot_digest,
        evidence=evidence,
    )
    assert session_zero_state.validate_campaign_state(campaign)["state"]["setup_revision"] == revision_before_gate

    report = session_zero_state.validate_campaign_state(campaign, require_ready=True)
    assert report["ok"], report["findings"]
    state = report["state"]
    decisions = {decision["decision_id"]: decision for decision in state["decisions"]}
    first_choice = decisions["01_primary_topology_intent"]
    activation = decisions["06_topology_activation"]
    assert first_choice["value"] == {"primary_topology": topology}
    assert activation["depends_on"] == ["01_primary_topology_intent"]
    assert activation["value"] == {
        "primary_topology": topology,
        "build_order": topology_contract["build_order"],
    }
    assert activation["trigger_tags"] == [topology_contract["trigger_tag"]]
    assert first_choice["revision"] < activation["revision"]

    stage_six = state["stages"]["06_living_world_ecology"]
    assert stage_six["status"] == "complete"
    assert "world.md" in stage_six["output_refs"]
    assert not any(ref.startswith("topology/") for ref in stage_six["output_refs"])
    assert state["extensions"][topology_contract["extension"]]["status"] == "complete"
    assert state["extensions"][topology_contract["extension"]]["depth"] in {"baseline", "deep"}

    assert all(stage["status"] == "complete" for stage in state["stages"].values())
    assert all(gate["status"] == "complete" for gate in state["gates"].values())
    for index, gate_id in enumerate(GATE_IDS):
        gate = state["gates"][gate_id]
        if gate_id == "research_scope_locked":
            assert gate["input_digest"] == state["stages"]["02_research_canon_grounding"]["output_digest"]
        elif gate_id in {"integrated_review_accepted", "preparation_approved"}:
            assert gate["input_digest"] == state["gates"]["cross_read_passed"]["output_digest"]
        else:
            assert gate["input_digest"] == state["gates"][GATE_IDS[index - 1]]["output_digest"]
    assert state["gates"]["design_direction_approved"]["decided_by"] == "player"
    assert state["gates"]["integrated_review_accepted"]["decided_by"] == "player"
    assert state["gates"]["preparation_approved"]["decided_by"] == "player"
    assert (
        state["gates"]["integrated_review_accepted"]["revision"]
        == state["gates"]["preparation_approved"]["revision"]
    )
    visible_approvals = {
        decision_id
        for decision_id in decisions
        if decision_id.endswith("_review") or decision_id.endswith("_approval")
    }
    assert visible_approvals == {"09_design_direction_review", "09_preparation_approval"}

    opening_ref = _owner_output("opening", manifest)
    assert opening_ref in state["stages"]["09_first_act_preparation"]["output_refs"]
    opening_text = (campaign / opening_ref).read_text(encoding="utf-8")
    assert "Immediate pressure:" in opening_text
    assert "Available affordances:" in opening_text
    assert "No fixed outcome:" in opening_text
    assert state["gates"]["ready_and_snapshotted"]["output_digest"] == snapshot_digest

    cli = subprocess.run(
        [sys.executable, str(STATE_TOOL), str(campaign), "status"],
        cwd=PUBLIC,
        text=True,
        capture_output=True,
        check=False,
    )
    assert cli.returncode == 0, cli.stderr or cli.stdout
    cli_result = json.loads(cli.stdout)
    assert cli_result["ok"] is True
    assert cli_result["current_stage"] == "09_first_act_preparation"
    assert set(cli_result["gates"].values()) == {"complete"}


@pytest.mark.parametrize(
    ("schema_version", "experience_mode", "session_zero_mode", "question_target"),
    [
        (8, "rpg", "quick", 10),
        (8, "rpg", "standard", 21),
        (8, "companion", "standard", 15),
        (7, "rpg", "deep", 30),
    ],
)
def test_non_deep_v8_and_legacy_deep_do_not_require_the_v8_state_ledger(
    tmp_path: Path,
    schema_version: int,
    experience_mode: str,
    session_zero_mode: str,
    question_target: int,
) -> None:
    campaign = tmp_path / "campaign"
    shutil.copytree(PUBLIC / "campaign", campaign)
    (campaign / "session_zero_state.json").unlink(missing_ok=True)
    _set_setup(
        campaign,
        schema_version=schema_version,
        status="in_progress",
        experience_mode=experience_mode,
        session_zero_mode=session_zero_mode,
        question_target=question_target,
        setup_revision=0,
        questions_completed=0,
        last_checkpoint=0,
    )

    result = check_state.check_campaign(campaign, scope="hot")
    state_findings = [
        finding
        for finding in result["findings"]
        if "session_zero_state"
        in ((finding.get("message") or "") + (finding.get("path") or ""))
        or finding.get("rule", "").startswith("deep_v8_state")
    ]
    assert state_findings == []

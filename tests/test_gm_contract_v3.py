from __future__ import annotations

import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_state = _load("gm_contract_check_state", PUBLIC / "tools" / "check_state.py")
check_style = _load("gm_contract_check_style", PUBLIC / "tools" / "check_style.py")
migrator = _load("gm_contract_migrator", PUBLIC / "tools" / "migrate_gm_contract.py")
verify_workspace = _load("gm_contract_verify", PUBLIC / "tools" / "verify_workspace.py")


@pytest.fixture()
def campaign(tmp_path: Path) -> Path:
    target = tmp_path / "campaign"
    shutil.copytree(PUBLIC / "campaign", target)
    return target


def _rules(result: dict) -> set[str]:
    return {item["rule"] for item in result["findings"]}


def test_profile_v2_and_blank_memory_v3_template_are_valid(campaign: Path) -> None:
    result = check_state.check_campaign(campaign, scope="full")
    assert result["error_count"] == 0
    assert "memory_v3_pending" not in _rules(result)


def test_profile_v2_bounds_signature_lists(campaign: Path) -> None:
    path = campaign / "play_profile.yaml"
    text = path.read_text(encoding="utf-8").replace(
        "    anchors: []",
        "    anchors: [grounded, causal, warm, excess]",
    )
    path.write_text(text, encoding="utf-8")
    assert "narrative_signature_list_too_long" in _rules(check_state.check_campaign(campaign, scope="hot"))


def test_dashboard_map_skin_is_validated_without_adding_a_required_question(campaign: Path) -> None:
    path = campaign / "play_profile.yaml"
    path.write_text(
        path.read_text(encoding="utf-8").replace("  map_skin: auto", "  map_skin: genre_locked"),
        encoding="utf-8",
    )
    assert "play_profile_field_invalid" in _rules(check_state.check_campaign(campaign, scope="hot"))


def test_memory_v3_requires_scene_shape_but_not_filled_opening_beat(campaign: Path) -> None:
    state = campaign / "current_state.yaml"
    text = state.read_text(encoding="utf-8").replace("  returned_control_at: \"\"", "  returned_control_at: next choice")
    state.write_text(text, encoding="utf-8")
    assert "causal_beat_shape_invalid" not in _rules(check_state.check_campaign(campaign, scope="hot"))
    state.write_text(re.sub(r"(?m)^\s{4}changed_fact:.*\n", "", text), encoding="utf-8")
    assert "causal_beat_shape_invalid" in _rules(check_state.check_campaign(campaign, scope="hot"))


def test_non_numeric_grounding_does_not_require_eight_stats(campaign: Path) -> None:
    rules = _rules(check_state.check_campaign(campaign, scope="full"))
    assert "player_stats_missing" not in rules
    assert "character_stats_missing" not in rules


def test_active_t2_requires_meaningful_agency_card(campaign: Path) -> None:
    (campaign / "characters" / "nella.md").write_text("# Nella\n\nTier: T2\n\nPower Band: local\n", encoding="utf-8")
    active = campaign / "active_cast.md"
    active.write_text(
        active.read_text(encoding="utf-8").replace(
            "| Example NPC | T2 | Example Place | Working | Finish the shift | evenings | employed here | close and leave | setup | 0 |",
            "| Nella | T2 | Example Place | Working | Finish | evenings | employed here | leave | setup | 0 |",
        ),
        encoding="utf-8",
    )
    assert "character_agency_card_incomplete" in _rules(check_state.check_campaign(campaign, scope="full"))


def test_relationship_endpoints_and_opening_location_are_checked(campaign: Path) -> None:
    relationship = campaign / "relationship_map.md"
    relationship.write_text(
        relationship.read_text(encoding="utf-8").replace("Character A", "Unknown One").replace("Character B", "Unknown Two"),
        encoding="utf-8",
    )
    state = campaign / "current_state.yaml"
    state.write_text(state.read_text(encoding="utf-8").replace('  location: ""', '  location: "Harbor"'), encoding="utf-8")
    (campaign / "places" / "harbor.md").write_text("# Harbor\n\nTier: T1\n", encoding="utf-8")
    opening = campaign / "opening_brief.md"
    opening.write_text(
        opening.read_text(encoding="utf-8")
        .replace("Opening status: `pending`", "Opening status: `active`")
        .replace("The place where the character starts.", "Location: Inland Camp"),
        encoding="utf-8",
    )
    rules = _rules(check_state.check_campaign(campaign, scope="full"))
    assert "relationship_endpoint_missing" in rules
    assert "opening_location_conflict" in rules


def test_style_categories_warn_and_history_is_bounded() -> None:
    prior = {
        "schema_version": 3,
        "max_history": 8,
        "max_categorical_history": 8,
        "avoid_phrases": [],
        "history": [],
        "categorical_history": [
            {"speaker_type": "narrator", "dramatic_beat": "reveal"},
            {"speaker_type": "narrator", "dramatic_beat": "reveal"},
        ],
    }
    findings, fingerprint = check_style.check_style(prior, "The door opens.", dramatic_beat="reveal")
    assert any(item["rule"] == "categorical_repetition" and item["severity"] == "warning" for item in findings)
    assert fingerprint["dramatic_beat"] == "reveal"


def _make_legacy(campaign: Path) -> None:
    profile = campaign / "play_profile.yaml"
    text = profile.read_text(encoding="utf-8")
    text = text.replace("schema_version: 2", "schema_version: 1", 1)
    text = re.sub(r"(?m)^\s{2}resolution_grounding:.*\n", "", text)
    text = re.sub(r"(?ms)^\s{2}narrative_signature:\s*$.*?^\s{2}breather_exit_policy:.*\n", "", text)
    text = text.replace('cold_distill_policy: ""', "cold_distill_policy: scene_or_5_durable")
    profile.write_text(text, encoding="utf-8")

    state = campaign / "current_state.yaml"
    state_text = state.read_text(encoding="utf-8").replace("memory_version: 3", "memory_version: 2", 1)
    state_text = re.sub(r"(?ms)^scene_frame:\s*$.*?(?=^inventory:)", "", state_text)
    state.write_text(state_text, encoding="utf-8")

    style = campaign / "style_state.json"
    data = json.loads(style.read_text(encoding="utf-8"))
    data["schema_version"] = 2
    data.pop("max_categorical_history")
    data.pop("categorical_history")
    style.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_migration_is_snapshot_gated_atomic_and_idempotent(campaign: Path) -> None:
    _make_legacy(campaign)
    legacy_npc = campaign / "characters" / "legacy_npc.md"
    legacy_npc.write_text("# Legacy NPC\n\nTier: T2\n\nPower Band: local\n\n## Public Face\n\nKeeps the ferry.\n", encoding="utf-8")
    before = (campaign / "play_profile.yaml").read_text(encoding="utf-8")
    dry = migrator.migrate(campaign, apply=False)
    assert dry["ok"] and dry["changed"]
    assert "play_profile.yaml: Narrative Signature anchors need review" in dry["needs_review"]
    assert (campaign / "play_profile.yaml").read_text(encoding="utf-8") == before
    assert migrator.migrate(campaign, apply=True)["error"] == "snapshot_required"

    snapshot = campaign / "snapshots" / "before_gm_v3"
    snapshot.mkdir(parents=True)
    (snapshot / "snapshot_manifest.json").write_text("{}\n", encoding="utf-8")
    applied = migrator.migrate(campaign, apply=True)
    assert applied["ok"] and applied["changed"]
    profile = (campaign / "play_profile.yaml").read_text(encoding="utf-8")
    assert "scene_checkpoint_or_5_durable" in profile
    assert "resolution_grounding:" in profile
    migrated_npc = legacy_npc.read_text(encoding="utf-8")
    assert "## At-The-Table Agency Card" in migrated_npc
    assert "Offscreen trajectory status: needs_review" in migrated_npc
    assert "Keeps the ferry." in migrated_npc
    assert migrator.migrate(campaign, apply=True)["changed"] is False


def test_replay_artifact_covers_all_approved_scenarios() -> None:
    data = json.loads((PUBLIC / "tools" / "gm_replay_suite.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == 2
    assert verify_workspace.GM_REPLAY_REQUIRED_IDS <= {item["id"] for item in data["scenarios"]}
    assert len(data["rubric"]["dimensions"]) == 9
    assert verify_workspace._check_gm_replay_fixture(PUBLIC / "tools" / "gm_replay_suite.json") == []


def test_ready_breather_may_be_calm_when_campaign_pressure_exists(campaign: Path) -> None:
    state_path = campaign / "current_state.yaml"
    text = state_path.read_text(encoding="utf-8")
    for old, new in (
        ("campaign_id: new_campaign", "campaign_id: calm_test"),
        ('  name: ""', '  name: "Ari"'),
        ('  concept: ""', '  concept: "Caretaker"'),
        ('  title: ""', '  title: "Quiet Kitchen"'),
        ('  location: ""', '  location: "Home"'),
        ('  summary: ""', '  summary: "Ari repairs a kettle."'),
        ("  mode: ambient", "  mode: breather"),
    ):
        text = text.replace(old, new, 1)
    state_path.write_text(text, encoding="utf-8")
    (campaign / "issues.md").write_text(
        "# Issues\n\n## Current Issues\n\n### Winter Stores\n\n- Status: current\n- What is wrong: The district has only a week of grain.\n",
        encoding="utf-8",
    )
    opening_path = campaign / "opening_brief.md"
    opening = opening_path.read_text(encoding="utf-8")
    opening = opening.replace("Opening status: `pending`", "Opening status: `active`")
    opening = opening.replace("`ambient`", "`breather`", 1)
    opening = re.sub(
        r"(?ms)^## Pressure Or Hook\s*$.*?(?=^## Do Not Reveal Yet\s*$)",
        "## Pressure Or Hook\n\n",
        opening,
    )
    opening_path.write_text(opening, encoding="utf-8")
    findings: list[dict] = []
    check_state._check_ready_for_play(campaign, text, ready=True, dashboard_mode="off", findings=findings)
    assert not any(item["rule"] == "ready_campaign_pressure_missing" for item in findings)
    assert not any(item["rule"] == "ready_scene_missing" and "immediate_pressure" in item["message"] for item in findings)
    assert not any(item["rule"] == "ready_opening_incomplete" and "Pressure Or Hook" in item["message"] for item in findings)


def test_faction_validator_uses_stable_ownership_and_conditional_numbers(campaign: Path) -> None:
    (campaign / "factions" / "harbor_union.md").write_text(
        """# Harbor Union

Tier: T2
Faction Power Band: local institution

## Stable Capability

Controls permits and two warehouses, but depends on elected stewards.

## Stable Desire

Keep dock labor locally governed.

## Stable Methods

Votes, work stoppages, and negotiated access.

## Representative Face

Mera, the elected clerk.

## Key Places

Union hall and east warehouse.

## Current World Domain Reference

- Domain id: harbor_labor
- Active-cast row, if any:
""",
        encoding="utf-8",
    )
    (campaign / "world_dynamics.md").write_text(
        "# World Dynamics\n\n## Active Domains\n\n### Harbor Labor\n\n- Domain id: harbor_labor\n- Status: stable\n",
        encoding="utf-8",
    )
    findings: list[dict] = []
    check_state._check_faction_notes(campaign, "beginner", findings, resolution_grounding="fictional")
    rules = {item["rule"] for item in findings}
    assert not {"faction_current_move_missing", "faction_next_move_missing", "faction_pressure_missing"} & rules
    assert "faction_typical_stats_missing" not in rules
    assert "faction_capability_profile_missing" not in rules
    assert "faction_world_domain_reference_missing" not in rules


def test_consumed_opening_is_not_compared_with_live_scene(campaign: Path) -> None:
    opening = campaign / "opening_brief.md"
    text = opening.read_text(encoding="utf-8").replace("Opening status: `pending`", "Opening status: `consumed`")
    text = text.replace("The place where the character starts.", "Location: Old Harbor")
    opening.write_text(text, encoding="utf-8")
    findings: list[dict] = []
    check_state._check_opening_coherence(campaign, current_location="Mountain Camp", present_npcs=[], findings=findings)
    assert "opening_location_conflict" not in {item["rule"] for item in findings}

    opening.write_text(text.replace("Opening status: `consumed`", "Opening status: `active`"), encoding="utf-8")
    findings = []
    check_state._check_opening_coherence(campaign, current_location="Mountain Camp", present_npcs=[], findings=findings)
    assert "opening_location_conflict" in {item["rule"] for item in findings}


def test_pending_opening_is_future_prep_not_live_coherence(campaign: Path) -> None:
    opening = campaign / "opening_brief.md"
    text = opening.read_text(encoding="utf-8").replace("The place where the character starts.", "Location: Future Port")
    opening.write_text(text, encoding="utf-8")
    findings: list[dict] = []
    check_state._check_opening_coherence(campaign, current_location="Current Village", present_npcs=[], findings=findings)
    assert "opening_location_conflict" not in {item["rule"] for item in findings}

    state = (campaign / "current_state.yaml").read_text(encoding="utf-8")
    findings = []
    check_state._check_ready_for_play(campaign, state, ready=True, dashboard_mode="off", findings=findings)
    assert "ready_opening_incomplete" not in {item["rule"] for item in findings}


def test_post_arc_opening_does_not_reopen_consumed_first_session(campaign: Path) -> None:
    first = campaign / "first_session.md"
    first.write_text(first.read_text(encoding="utf-8").replace("Prep status: `drafting`", "Prep status: `consumed`"), encoding="utf-8")
    opening = campaign / "opening_brief.md"
    text = opening.read_text(encoding="utf-8")
    text = text.replace("Opening status: `pending`", "Opening status: `active`")
    text = text.replace("`first_campaign_opening`", "`post_arc_opening`", 1)
    opening.write_text(text, encoding="utf-8")
    findings: list[dict] = []
    check_state._check_first_session_lifecycle(campaign, ready=True, contract_v2=True, findings=findings)
    assert "opening_lifecycle_conflict" not in {item["rule"] for item in findings}

    opening.write_text(text.replace("`post_arc_opening`", "`first_campaign_opening`", 1), encoding="utf-8")
    findings = []
    check_state._check_first_session_lifecycle(campaign, ready=True, contract_v2=True, findings=findings)
    assert "opening_lifecycle_conflict" in {item["rule"] for item in findings}


def test_cadence_none_rejects_every_live_advancement_gate(campaign: Path) -> None:
    path = campaign / "arc_closure.md"
    path.write_text(
        """# Arc Closure

## Current Progression State

- Advancement presentation: none
- Advancement status: due
- OOC interlude status: offered
- Fiction continuation locked until advancement: yes
""",
        encoding="utf-8",
    )
    findings: list[dict] = []
    check_state._check_advancement_contract(
        campaign,
        {"advancement_cadence": "none", "advancement_presentation": "none"},
        findings,
    )
    assert sum(item["rule"] == "advancement_gate_forbidden" for item in findings) == 3

    path.write_text(
        """# Legacy Arc Closure

## Current Progression State

- Status: offered
- OOC interlude offered: yes
- Fiction may continue: no
""",
        encoding="utf-8",
    )
    findings = []
    check_state._check_advancement_contract(
        campaign,
        {"advancement_cadence": "none", "advancement_presentation": "none"},
        findings,
    )
    assert "advancement_gate_forbidden" in {item["rule"] for item in findings}

    path.write_text(
        "# Legacy Arc Closure\n\n## Current Progression State\n\n- Status: not_due\n- OOC interlude offered: no\n- Fiction may continue: yes\n",
        encoding="utf-8",
    )
    findings = []
    check_state._check_advancement_contract(
        campaign,
        {"advancement_cadence": "none", "advancement_presentation": "none"},
        findings,
    )
    assert not findings


def test_ready_profile_v2_requires_three_meaningful_anchors(campaign: Path) -> None:
    setup = campaign / "setup_profile.yaml"
    setup_text = setup.read_text(encoding="utf-8").replace("ready_for_play: false", "ready_for_play: true")
    setup.write_text(setup_text, encoding="utf-8")
    profile = campaign / "play_profile.yaml"
    profile.write_text(profile.read_text(encoding="utf-8").replace("profile_status: pending", "profile_status: locked"), encoding="utf-8")
    findings: list[dict] = []
    check_state._check_play_profile(campaign, findings)
    assert "ready_narrative_signature_incomplete" in {item["rule"] for item in findings}

    profile.write_text(profile.read_text(encoding="utf-8").replace("    anchors: []", "    anchors: [grounded consequences, ordinary voices, breathing room]"), encoding="utf-8")
    findings = []
    check_state._check_play_profile(campaign, findings)
    assert "ready_narrative_signature_incomplete" not in {item["rule"] for item in findings}


def test_active_offscreen_trajectory_requires_detail(campaign: Path) -> None:
    card = "\n".join(
        ["## At-The-Table Agency Card", ""]
        + [
            f"- {field}: {'active' if field == 'Offscreen trajectory status' else 'specific value'}"
            for field in check_state.AGENCY_CARD_FIELDS
        ]
    )
    (campaign / "characters" / "ilya.md").write_text(
        f"# Ilya\n\nTier: T3\n\nPower Band: local\n\n{card}\n",
        encoding="utf-8",
    )
    findings: list[dict] = []
    check_state._check_character_notes(
        campaign,
        "beginner",
        findings,
        resolution_grounding="fictional",
        ready=False,
        contract_v3=True,
    )
    assert "active_offscreen_trajectory_incomplete" in {item["rule"] for item in findings}


def test_migration_reports_legacy_ownership_and_trajectory_reviews(campaign: Path) -> None:
    first = campaign / "first_session.md"
    first.write_text(re.sub(r"(?m)^Prep status:.*\n", "", first.read_text(encoding="utf-8")), encoding="utf-8")
    (campaign / "characters" / "legacy_agent.md").write_text(
        """# Legacy Agent

Tier: T2
Power Band: local

## At-The-Table Agency Card

- Offscreen trajectory status: active

## What They Know About The Player

The player's current debt.

## Relationships

Currently distrusts the player.
""",
        encoding="utf-8",
    )
    (campaign / "factions" / "legacy_guild.md").write_text(
        """# Legacy Guild

Tier: T2

## Current Move

Seizing the quay.

## What The Faction Knows About The Player

The player's route.
""",
        encoding="utf-8",
    )
    result = migrator.migrate(campaign, apply=False)
    joined = "\n".join(result["needs_review"])
    assert "legacy opening lifecycle" in joined
    assert "current-move ownership" in joined
    assert "duplicated current knowledge" in joined
    assert "duplicated current relationship" in joined
    assert "active offscreen trajectory lacks required detail" in joined

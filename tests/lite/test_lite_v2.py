from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
LITE = ROOT


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


check_state = _load("lite_check_state", LITE / "tools" / "check_state.py")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture()
def campaign(tmp_path: Path) -> Path:
    target = tmp_path / "campaign"
    shutil.copytree(LITE / "templates" / "campaign", target)
    state = (target / "current_state.yaml").read_text(encoding="utf-8")
    state = state.replace("campaign_id: replace_me", "campaign_id: test")
    state = state.replace("continuity_revision: 0", "continuity_revision: 3")
    state = state.replace('  name: ""', '  name: "Hero"', 1)
    state = state.replace('  concept: ""', '  concept: "Tester"', 1)
    state = state.replace('  current_goal: ""', '  current_goal: "Test continuity"', 1)
    state = state.replace('  title: ""', '  title: "Inn"', 1)
    state = state.replace('  location: ""', '  location: "Inn"', 1)
    state = state.replace('  summary: ""', '  summary: "Hero and Nella are at the inn."', 1)
    state = state.replace("  present_npcs: []", "  present_npcs:\n    - Nella")
    state = state.replace('  immediate_pressure: ""', '  immediate_pressure: "Closing time"', 1)
    (target / "current_state.yaml").write_text(state, encoding="utf-8")

    character = """# Nella

Tier: T2
Power Band: local professional

## Stats
- Power: 2
- Agility: 2
- Endurance: 2
- Technique: 2
- Perception: 2
- Wits: 2
- Presence: 2
- Will: 2

## Current Mundane Agenda
Finish supper.
## Routine And Availability
Works at the inn and leaves after closing.
## Private Motive
Save enough money to travel.
## Last Meaningful Interaction
Agreed to help Hero.
"""
    _write(target / "characters" / "nella.md", character)
    place = """# Inn

Tier: T2
## Baseline Routine
Serves travelers from dawn to night.
## Presence Logic
Workers and paying guests have ordinary reasons to be here.
"""
    _write(target / "places" / "inn.md", place)
    _write(target / "places" / "harbor.md", "# Harbor\n\nTier: T1\n")

    _write(
        target / "active_cast.md",
        """# Active Cast
Campaign id: `test`
As of revision: 3
| NPC | Tier | Current location | Current activity | Immediate objective | Availability | Reason here | Next move if ignored | Last seen | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| Nella | T2 | Inn | Eating | Finish supper | before closing | works here | close the inn | now | 3 |
""",
    )
    _write(
        target / "location_graph.md",
        """# Location Graph
Campaign id: `test`
As of revision: 3
| From | Direction | To | Travel | Access | Visibility | Ordinary traffic | Conditions | Player-known | Last changed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Inn | <-> | Harbor | short walk | public | open | workers | none | yes | setup |
""",
    )
    _write(
        target / "relationship_map.md",
        """# Relationship Map
Campaign id: `test`
As of revision: 3
| From | Direction | To | Relation | Status | Trust / debt / tension | Knowledge asymmetry | Player-known | Last changed | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| Hero | <-> | Nella | allies | active | cautious trust | none | yes | setup | 3 |
""",
    )
    _write(target / "session_brief.md", "# Session Brief\n\nCampaign id: `test`\nPrepared from revision: 3\n")
    _write(target / "research_dossier.md", "# Research Dossier\n\n## Research Status\n- Status: `complete`\n")
    return target


def _rules(result: dict) -> set[str]:
    return {finding["rule"] for finding in result["findings"]}


def test_block_list_present_npc_is_parsed_and_valid(campaign: Path) -> None:
    result = check_state.check_campaign(campaign)
    assert "present_important_npc_untracked" not in _rules(result)
    assert result["error_count"] == 0


def test_present_important_npc_requires_presence_reason(campaign: Path) -> None:
    path = campaign / "active_cast.md"
    path.write_text(path.read_text(encoding="utf-8").replace("| works here |", "|  |"), encoding="utf-8")
    assert "active_cast_presence_incomplete" in _rules(check_state.check_campaign(campaign))


def test_location_graph_rejects_missing_endpoint(campaign: Path) -> None:
    path = campaign / "location_graph.md"
    path.write_text(path.read_text(encoding="utf-8").replace("| Harbor |", "| Nowhere |"), encoding="utf-8")
    assert "location_graph_endpoint_missing" in _rules(check_state.check_campaign(campaign))


def test_relationship_graph_rejects_duplicate_current_pair(campaign: Path) -> None:
    path = campaign / "relationship_map.md"
    with path.open("a", encoding="utf-8") as handle:
        handle.write("| Hero | <-> | Nella | allies | active | trust | none | yes | later | 3 |\n")
    assert "relationship_current_duplicate" in _rules(check_state.check_campaign(campaign))


def test_stale_session_brief_and_due_domain_are_warnings(campaign: Path) -> None:
    _write(campaign / "session_brief.md", "# Session Brief\n\nPrepared from revision: 1\n")
    _write(campaign / "world_dynamics.md", "# World Dynamics\n\n## Active Domains\n- Due: yes\n")
    rules = _rules(check_state.check_campaign(campaign))
    assert {"session_brief_stale", "world_domain_due"} <= rules


def test_superseded_active_knowledge_is_reported(campaign: Path) -> None:
    _write(
        campaign / "knowledge_boundaries.md",
        "# Knowledge Boundaries\n\n## Player And Character Knowledge\n- Fact: old truth\n  - Status: superseded\n",
    )
    assert "superseded_active_knowledge" in _rules(check_state.check_campaign(campaign))


def test_pending_research_cannot_silently_lock_world(campaign: Path) -> None:
    _write(campaign / "research_dossier.md", "# Research Dossier\n\n## Research Status\n- Status: `needed_pending`\n")
    _write(campaign / "session_zero.md", "# Session Zero\n\n- World Truths: locked\n- Factions: locked\n")
    assert "research_gate_locked_while_pending" in _rules(check_state.check_campaign(campaign))


def test_documented_arc_stat_policy_downgrades_budget_exceptions(campaign: Path) -> None:
    path = campaign / "current_state.yaml"
    text = path.read_text(encoding="utf-8").replace("stat_budget_policy: standard", "stat_budget_policy: custom_arc_earned")
    text = text.replace('stat_budget_note: ""', 'stat_budget_note: "earned in play"')
    text = text.replace("    Presence: 2", "    Presence: 5")
    path.write_text(text, encoding="utf-8")
    rules = _rules(check_state.check_campaign(campaign))
    assert "stat_level_max_exceeded" not in rules
    assert "stat_level_custom" in rules


def test_pending_setup_profile_is_valid_but_not_ready(campaign: Path) -> None:
    result = check_state.check_campaign(campaign)
    assert "setup_ready_mismatch" not in _rules(result)


def test_incomplete_deep_pack_blocks_readiness(campaign: Path) -> None:
    path = campaign / "setup_profile.yaml"
    path.write_text(
        """schema_version: 1
workspace_mode: standalone
status: complete
session_zero_mode: deep
question_target: 40
questions_completed: 35
activated_packs: [character_foundation, group]
completed_packs: [character_foundation]
defaulted_packs: []
deferred_decisions: []
last_checkpoint: 32
ready_for_play: true
""",
        encoding="utf-8",
    )
    assert "deep_pack_incomplete" in _rules(check_state.check_campaign(campaign))


def test_quick_completion_requires_visible_defaults(campaign: Path) -> None:
    path = campaign / "setup_profile.yaml"
    path.write_text(
        """schema_version: 1
workspace_mode: repository
status: complete
session_zero_mode: quick
question_target: 8
questions_completed: 8
activated_packs: []
completed_packs: []
defaulted_packs: []
deferred_decisions: []
last_checkpoint: 0
ready_for_play: true
""",
        encoding="utf-8",
    )
    assert "quick_defaults_missing" in _rules(check_state.check_campaign(campaign))


def test_pending_visual_review_blocks_ready_for_play(campaign: Path) -> None:
    setup = campaign / "setup_profile.yaml"
    setup.write_text(
        """schema_version: 1
workspace_mode: repository
status: complete
session_zero_mode: standard
question_target: 17
questions_completed: 17
activated_packs: []
completed_packs: []
defaulted_packs: []
deferred_decisions: []
last_checkpoint: 0
ready_for_play: true
""",
        encoding="utf-8",
    )
    session_zero = campaign / "session_zero.md"
    session_zero.write_text(
        session_zero.read_text(encoding="utf-8").replace(": open", ": locked"),
        encoding="utf-8",
    )
    visual = campaign / "visual_style.md"
    visual.write_text(
        visual.read_text(encoding="utf-8").replace(
            "- Pending visual review: no", "- Pending visual review: yes"
        ),
        encoding="utf-8",
    )
    assert "visual_review_pending_at_play" in _rules(check_state.check_campaign(campaign))


def test_completed_review_warns_when_requested_dashboard_handoff_is_missing(campaign: Path) -> None:
    visual = campaign / "visual_style.md"
    text = visual.read_text(encoding="utf-8")
    text = text.replace("- Dashboard placement requested: no", "- Dashboard placement requested: yes")
    visual.write_text(text, encoding="utf-8")
    assert "visual_dashboard_handoff_incomplete" in _rules(check_state.check_campaign(campaign))

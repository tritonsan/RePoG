"""Make helper imports work from a standalone source checkout."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


CURRENT_STATE = """campaign_id: test_campaign
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
  phase: evening
  elapsed_index: 0

player:
  name: Mira
  concept: investigator
  level_band: beginner
  stat_budget_policy: standard
  stat_budget_note: ""
  condition: ready
  current_goal: Find the courier
  # A comment that belongs to the player block.
  stats: {}
  capabilities: []

current_scene:
  title: Warehouse Questions
  location: old_dock
  summary: The interview is unresolved.
  present_npcs: []
  immediate_pressure: ""
  open_choices: []

scene_frame:
  scene_id: dock-interview
  mode: focused
  ongoing_process: The interview continues.
  disruption: ""
  last_causal_beat:
    player_intent: Ask about the courier.
    world_response: The witness hesitates.
    changed_fact: ""
    returned_control_at: The witness waits.
  pending_consequences: []
  resume_anchor: The witness waits for the next question.

inventory: []
conditions: []
active_clocks: []
active_threats: []
"""


@pytest.fixture()
def campaign(tmp_path: Path) -> Path:
    """A small ready RPG campaign with synthetic content only."""

    root = tmp_path / "campaign"
    root.mkdir()
    for directory in ("characters", "places", "factions"):
        (root / directory).mkdir()
    (root / "setup_profile.yaml").write_text(
        "schema_version: 4\nworkspace_mode: standalone\nstatus: complete\nsetup_revision: 3\n"
        "experience_mode: rpg\nsession_zero_mode: standard\nquestion_target: 10\n"
        "questions_completed: 10\nready_for_play: true\n",
        encoding="utf-8",
    )
    (root / "play_profile.yaml").write_text(
        "schema_version: 2\nprofile_status: locked\nsource_setup_revision: 3\nperformance:\n"
        "  semantic_parallelism: off\n  max_parallel_workers: 1\n  turn_protocol: fast\n"
        "  cold_distill_policy: scene_checkpoint_or_5_durable\n"
        "  validation_policy: hot_each_durable_full_on_distill\n"
        "  style_review_policy: sampled_and_distill\n  latency_notice_policy: exceptional_only\n"
        "  estimate_acknowledged: true\n",
        encoding="utf-8",
    )
    (root / "current_state.yaml").write_text(CURRENT_STATE, encoding="utf-8")
    (root / "session_log.md").write_text("# Session Log\n\n## Entries\n", encoding="utf-8")
    (root / "knowledge_boundaries.md").write_text(
        "# Knowledge Boundaries\n\n## Player Knowledge\n\n- Fact: Mira saw the empty dock.\n"
        "  - Fact id: PK-007\n\n## NPC Knowledge\n\n### Witness\n\n- Knows: the courier's face.\n",
        encoding="utf-8",
    )
    (root / "threads.md").write_text("# Threads\n\n- Courier promise: absent\n", encoding="utf-8")
    (root / "active_cast.md").write_text(
        "# Active Cast\n\nAs of revision: 0\n\n| Name | Where | Doing |\n| --- | --- | --- |\n"
        "| Witness | old dock | waiting |\n",
        encoding="utf-8",
    )
    (root / "relationship_map.md").write_text(
        "# Relationship Map\n\nAs of revision: 0\n\n| From | Direction | To | Relation |\n| --- | --- | --- | --- |\n"
        "| Mira | -> | Witness | wary |\n| Mira | -> | Courier | hunting |\n",
        encoding="utf-8",
    )
    (root / "secrets_and_clues.md").write_text("# Secrets and Clues\n", encoding="utf-8")
    (root / "characters" / "witness.md").write_text(
        "# Witness\n\n## Agency Card\n\n- Tier: T2\n\n## Current State\n\nNervous.\n",
        encoding="utf-8",
    )
    (root / "mechanics_state.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "enabled": False,
                "revision": 0,
                "continuity_revision": 0,
                "operation_sequence": 0,
                "operation_registry": {},
                "last_operation": None,
                "actors": {},
                "clocks": {},
                "elapsed_time": {},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return root

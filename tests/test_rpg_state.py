from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "rpg_state.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("public_rpg_state", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rpg_state = _load_module()


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
    root = tmp_path / "campaign"
    root.mkdir()
    for directory in ("characters", "places", "factions"):
        (root / directory).mkdir()
    (root / "setup_profile.yaml").write_text(
        """schema_version: 4
workspace_mode: standalone
status: complete
setup_revision: 3
experience_mode: rpg
session_zero_mode: standard
question_target: 10
questions_completed: 10
ready_for_play: true
""",
        encoding="utf-8",
    )
    (root / "play_profile.yaml").write_text(
        """schema_version: 2
profile_status: locked
source_setup_revision: 3
performance:
  semantic_parallelism: off
  max_parallel_workers: 1
  turn_protocol: fast
  cold_distill_policy: scene_checkpoint_or_5_durable
  validation_policy: hot_each_durable_full_on_distill
  style_review_policy: sampled_and_distill
  latency_notice_policy: exceptional_only
  estimate_acknowledged: true
""",
        encoding="utf-8",
    )
    (root / "current_state.yaml").write_text(CURRENT_STATE, encoding="utf-8")
    (root / "session_log.md").write_text("# Session Log\n\n## Entries\n", encoding="utf-8")
    (root / "knowledge_boundaries.md").write_text(
        "# Knowledge Boundaries\n\n- Mira: unaware of the courier route\n",
        encoding="utf-8",
    )
    (root / "threads.md").write_text("# Threads\n\n- Courier promise: absent\n", encoding="utf-8")
    (root / "active_cast.md").write_text("# Active Cast\n\n- Handoff: none\n", encoding="utf-8")
    (root / "secrets_and_clues.md").write_text("# Secrets and Clues\n", encoding="utf-8")
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


def _durable_payload(operation_id: str = "turn-001", expected_revision: int = 0) -> dict:
    return {
        "operation_id": operation_id,
        "expected_continuity_revision": expected_revision,
        "boundary": "ordinary",
        "cause": "Mira questioned the witness about the courier.",
        "resume_impact": "The witness is waiting for Mira's response.",
        "changes": [
            {
                "id": "c1",
                "kind": "knowledge",
                "established_delta": "Mira now knows the courier used the east gate.",
                "owners": ["knowledge_boundaries.md"],
                "cold_targets": [
                    {
                        "path": "secrets_and_clues.md",
                        "reason": "refresh the clue-status mirror",
                    }
                ],
            }
        ],
        "mutations": [
            {
                "path": "knowledge_boundaries.md",
                "exact_replacements": [
                    {
                        "old": "- Mira: unaware of the courier route",
                        "new": "- Mira: knows the courier used the east gate",
                    }
                ],
            }
        ],
    }


def _state_text(campaign: Path) -> str:
    return (campaign / "current_state.yaml").read_text(encoding="utf-8")


def _set_pending_history(campaign: Path, count: int) -> None:
    state = _state_text(campaign)
    state = state.replace("continuity_revision: 0", f"continuity_revision: {count}")
    state = state.replace("durable_turns_since_distill: 0", f"durable_turns_since_distill: {count}")
    (campaign / "current_state.yaml").write_text(state, encoding="utf-8")
    with (campaign / "session_log.md").open("a", encoding="utf-8") as stream:
        for revision in range(1, count + 1):
            stream.write(
                f"\n### Durable Revision {revision}\n\n"
                f"- Event: legacy test event {revision}\n"
                "- Immediate files: current_state.yaml\n"
                "- Pending cold targets: none\n"
            )


def test_durable_commit_updates_owner_revision_event_and_cold_queue(campaign: Path) -> None:
    result = rpg_state.commit_durable(campaign, _durable_payload())

    assert result["ok"] is True
    assert result["idempotent"] is False
    assert result["continuity_revision"] == 1
    assert result["durable_turns_since_distill"] == 1
    assert result["pending_cold_targets"] == ["secrets_and_clues.md"]
    assert result["full_distill_required"] is False
    assert result["narration_allowed"] is True

    state = _state_text(campaign)
    assert "continuity_revision: 1" in state
    assert "durable_turns_since_distill: 1" in state
    assert '    - "secrets_and_clues.md"' in state
    assert "knows the courier used the east gate" in (
        campaign / "knowledge_boundaries.md"
    ).read_text(encoding="utf-8")

    log = (campaign / "session_log.md").read_text(encoding="utf-8")
    assert "### Durable Revision 1" in log
    assert "- Operation: turn-001" in log
    assert "c1 [knowledge]" in log
    assert "c1 -> `knowledge_boundaries.md`" in log
    assert "c1 -> `secrets_and_clues.md`" in log
    assert "- Payload hash: sha256:" in log


def test_same_operation_and_payload_is_idempotent(campaign: Path) -> None:
    payload = _durable_payload()
    first = rpg_state.commit_durable(campaign, payload)
    second = rpg_state.commit_durable(campaign, payload)

    assert first["idempotent"] is False
    assert second["idempotent"] is True
    assert second["continuity_revision"] == 1
    log = (campaign / "session_log.md").read_text(encoding="utf-8")
    assert log.count("### Durable Revision 1") == 1
    assert log.count("- Operation: turn-001") == 1


def test_same_operation_with_different_payload_is_rejected(campaign: Path) -> None:
    payload = _durable_payload()
    rpg_state.commit_durable(campaign, payload)
    changed = copy.deepcopy(payload)
    changed["cause"] = "A different causal claim."

    with pytest.raises(rpg_state.RPGStateError) as caught:
        rpg_state.commit_durable(campaign, changed)
    assert caught.value.category == "operation_conflict"


def test_stale_revision_is_rejected(campaign: Path) -> None:
    rpg_state.commit_durable(campaign, _durable_payload())
    stale = _durable_payload(operation_id="turn-002", expected_revision=0)
    stale["mutations"][0]["exact_replacements"][0] = {
        "old": "- Mira: knows the courier used the east gate",
        "new": "- Mira: knows the courier used the north road",
    }

    with pytest.raises(rpg_state.RPGStateError) as caught:
        rpg_state.commit_durable(campaign, stale)
    assert caught.value.category == "stale_revision"


def test_declared_owner_requires_an_immediate_mutation(campaign: Path) -> None:
    payload = _durable_payload()
    payload["mutations"] = []

    with pytest.raises(rpg_state.RPGStateError) as caught:
        rpg_state.commit_durable(campaign, payload)
    assert caught.value.category == "input_invalid"
    assert "no immediate mutation" in str(caught.value)


def test_exact_replacement_must_match_once(campaign: Path) -> None:
    payload = _durable_payload()
    payload["mutations"][0]["exact_replacements"][0]["old"] = "missing text"

    with pytest.raises(rpg_state.RPGStateError) as caught:
        rpg_state.commit_durable(campaign, payload)
    assert caught.value.category == "candidate_invalid"
    assert "matched 0 times" in str(caught.value)


def test_normal_write_failure_rolls_every_target_back(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _durable_payload()
    payload["changes"].append(
        {
            "id": "c2",
            "kind": "thread",
            "established_delta": "The witness promised to send the manifest.",
            "owners": ["threads.md"],
            "cold_targets": [],
        }
    )
    payload["mutations"].append(
        {
            "path": "threads.md",
            "exact_replacements": [
                {
                    "old": "- Courier promise: absent",
                    "new": "- Courier promise: witness will send the manifest",
                }
            ],
        }
    )
    original = {path.name: path.read_bytes() for path in campaign.iterdir() if path.is_file()}
    real_apply = rpg_state._apply_candidate_file
    calls = 0

    def fail_second(path: Path, content: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected write failure")
        real_apply(path, content)

    monkeypatch.setattr(rpg_state, "_apply_candidate_file", fail_second)
    with pytest.raises(rpg_state.RPGStateError) as caught:
        rpg_state.commit_durable(campaign, payload)
    assert caught.value.category == "commit_rolled_back"

    for name, content in original.items():
        assert (campaign / name).read_bytes() == content
    assert not any((campaign / rpg_state.TRANSACTION_DIR).glob("*/manifest.json"))


def test_interrupted_commit_is_recovered_before_retry(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _durable_payload()
    real_apply = rpg_state._apply_candidate_file
    calls = 0

    def interrupt_second(path: Path, content: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt("simulated process interruption")
        real_apply(path, content)

    monkeypatch.setattr(rpg_state, "_apply_candidate_file", interrupt_second)
    with pytest.raises(KeyboardInterrupt):
        rpg_state.commit_durable(campaign, payload)
    assert any((campaign / rpg_state.TRANSACTION_DIR).glob("*/manifest.json"))

    monkeypatch.setattr(rpg_state, "_apply_candidate_file", real_apply)
    result = rpg_state.commit_durable(campaign, payload)
    assert result["ok"] is True
    assert result["recovered_transactions"] == ["turn-001"]
    assert "continuity_revision: 1" in _state_text(campaign)
    assert not any((campaign / rpg_state.TRANSACTION_DIR).glob("*/manifest.json"))


def test_existing_pending_targets_are_preserved_and_deduplicated(campaign: Path) -> None:
    state = _state_text(campaign).replace(
        "  pending_cold_targets: []",
        '  pending_cold_targets:\n    - "campaign_one_pager.md"',
    )
    (campaign / "current_state.yaml").write_text(state, encoding="utf-8")
    payload = _durable_payload()
    payload["changes"][0]["cold_targets"].append(
        {"path": "campaign_one_pager.md", "reason": "refresh the public summary"}
    )

    result = rpg_state.commit_durable(campaign, payload)
    assert result["pending_cold_targets"] == [
        "campaign_one_pager.md",
        "secrets_and_clues.md",
    ]
    state = _state_text(campaign)
    assert state.count('"campaign_one_pager.md"') == 1
    assert state.count('"secrets_and_clues.md"') == 1


def test_soft_checkpoint_changes_resume_state_without_revision(campaign: Path) -> None:
    payload = {
        "operation_id": "checkpoint-001",
        "expected_continuity_revision": 0,
        "checkpoint": {
            "scene_id": "dock-interview",
            "scene_mode": "focused",
            "resume_anchor": "Mira stands at the east-gate map.",
            "active_cast_handoff": "none",
        },
        "mutations": [
            {
                "path": "current_state.yaml",
                "exact_replacements": [
                    {
                        "old": "resume_anchor: The witness waits for the next question.",
                        "new": "resume_anchor: Mira stands at the east-gate map.",
                    }
                ],
            }
        ],
    }

    result = rpg_state.commit_checkpoint(campaign, payload)
    assert result["continuity_revision"] == 0
    assert result["durable_turns_since_distill"] == 0
    assert result["checkpoint_committed"] is True
    assert "continuity_revision: 0" in _state_text(campaign)
    log = (campaign / "session_log.md").read_text(encoding="utf-8")
    assert "### Scene Checkpoint Revision 0" in log
    assert "- Operation: checkpoint-001" in log
    assert "### Durable Revision" not in log


def test_durable_checkpoint_uses_one_continuity_revision(campaign: Path) -> None:
    payload = _durable_payload()
    payload["boundary"] = "scene_checkpoint"
    payload["resume_impact"] = "The interview ends at the east-gate map."
    payload["checkpoint"] = {
        "scene_id": "dock-interview",
        "scene_mode": "aftermath",
        "resume_anchor": "Mira stands at the east-gate map.",
        "active_cast_handoff": "none",
    }
    payload["changes"][0]["owners"].append("current_state.yaml")
    payload["mutations"].append(
        {
            "path": "current_state.yaml",
            "exact_replacements": [
                {
                    "old": "resume_anchor: The witness waits for the next question.",
                    "new": "resume_anchor: Mira stands at the east-gate map.",
                }
            ],
        }
    )

    result = rpg_state.commit_durable(campaign, payload)
    assert result["continuity_revision"] == 1
    assert result["checkpoint_committed"] is True
    log = (campaign / "session_log.md").read_text(encoding="utf-8")
    assert log.count("### Durable Revision 1") == 1
    assert log.count("### Scene Checkpoint Revision 1") == 1
    assert "- Source operation: turn-001" in log


def test_fast_fifth_commit_is_saved_then_requires_distill(campaign: Path) -> None:
    _set_pending_history(campaign, 4)
    payload = _durable_payload(expected_revision=4)

    result = rpg_state.commit_durable(campaign, payload)
    assert result["continuity_revision"] == 5
    assert result["durable_turns_since_distill"] == 5
    assert result["full_distill_required"] is True
    assert result["narration_allowed"] is False
    assert result["distill_reason"] == "cadence_limit"
    assert "continuity_revision: 5" in _state_text(campaign)
    assert "### Durable Revision 5" in (campaign / "session_log.md").read_text(encoding="utf-8")


def test_new_commit_is_blocked_while_distill_is_already_due(campaign: Path) -> None:
    _set_pending_history(campaign, 5)
    payload = _durable_payload(operation_id="turn-006", expected_revision=5)

    with pytest.raises(rpg_state.RPGStateError) as caught:
        rpg_state.commit_durable(campaign, payload)
    assert caught.value.category == "distill_required"


def test_mechanic_operation_is_staged_in_the_same_durable_commit(campaign: Path) -> None:
    mechanics_path = campaign / "mechanics_state.json"
    mechanics_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "enabled": True,
                "revision": 0,
                "continuity_revision": 0,
                "operation_sequence": 0,
                "operation_registry": {},
                "last_operation": None,
                "actors": {
                    "player": {
                        "resources": {
                            "focus": {
                                "current": 5,
                                "minimum": 0,
                                "maximum": 5,
                                "regen": None,
                            }
                        },
                        "abilities": {},
                        "inventory": {},
                        "conditions": {},
                    }
                },
                "clocks": {},
                "elapsed_time": {},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    payload = {
        "operation_id": "turn-mechanic-001",
        "expected_continuity_revision": 0,
        "boundary": "ordinary",
        "cause": "Mira maintained focus through the interrogation.",
        "resume_impact": "The witness is still waiting for Mira's response.",
        "changes": [
            {
                "id": "c1",
                "kind": "mechanics",
                "established_delta": "Mira spent two focus.",
                "owners": ["mechanics_state.json"],
                "cold_targets": [],
            }
        ],
        "mutations": [],
        "mechanic_operations": [
            {
                "operation_id": "mechanic-focus-001",
                "operation": "spend",
                "actor_id": "player",
                "resource_id": "focus",
                "amount": 2,
            }
        ],
    }

    result = rpg_state.commit_durable(campaign, payload)
    mechanics = json.loads(mechanics_path.read_text(encoding="utf-8"))
    assert result["continuity_revision"] == 1
    assert result["mechanic_results"][0]["changes"][0]["before"] == 5
    assert result["mechanic_results"][0]["changes"][0]["after"] == 3
    assert mechanics["actors"]["player"]["resources"]["focus"]["current"] == 3
    assert mechanics["continuity_revision"] == 1
    assert mechanics["operation_sequence"] == 1

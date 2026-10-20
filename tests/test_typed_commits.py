from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

import check_state
import rpg_state


def _durable(operation_id: str = "turn-001", expected: int = 0, **overrides) -> dict:
    payload = {
        "operation_id": operation_id,
        "expected_continuity_revision": expected,
        "boundary": "ordinary",
        "cause": "Mira pressed the witness.",
        "resume_impact": "A restart must keep the name the witness gave.",
        "changes": [
            {
                "id": "scene",
                "kind": "scene_progress",
                "established_delta": "The interview moved on to the courier's name.",
                "owners": ["current_state.yaml"],
            },
            {
                "id": "name",
                "kind": "knowledge",
                "established_delta": "Mira learned the courier is called Ilse.",
                "owners": ["knowledge_boundaries.md"],
            },
            {
                "id": "ilse",
                "kind": "presence",
                "established_delta": "Ilse arrived at the dock.",
                "owners": ["active_cast.md", "characters/ilse.md"],
            },
        ],
        "mutations": [
            {
                "path": "current_state.yaml",
                "ops": [
                    {
                        "op": "set",
                        "values": {
                            "current_scene.summary": "The witness named the courier.",
                            "scene_frame.last_causal_beat.changed_fact": "The courier is Ilse.",
                        },
                    },
                    {"op": "list_add", "key": "current_scene.present_npcs", "items": ["Witness", "Ilse"]},
                ],
            },
            {
                "path": "knowledge_boundaries.md",
                "ops": [
                    {
                        "op": "append",
                        "heading": "Player Knowledge",
                        "text": "- Fact: the courier is called Ilse.\n  - Fact id: {{next_id:PK}}\n  - Last confirmed: revision {{revision}}",
                    }
                ],
            },
            {
                "path": "active_cast.md",
                "ops": [{"op": "upsert_row", "key": "Ilse", "cells": ["Ilse", "old dock", "listening"]}],
            },
            {
                "path": "characters/ilse.md",
                "create_text": "# Ilse\n\n- Tier: T2\n- First appeared: revision {{revision}}\n",
            },
        ],
    }
    payload.update(overrides)
    return payload


def _read(campaign: Path, relative: str) -> str:
    return (campaign / relative).read_text(encoding="utf-8")


LOG_RULES = {"durable_event_missing", "durable_event_duplicate", "distill_marker_missing", "persistence_log_ahead"}


def _error_rules(campaign: Path, scope: str) -> set[str]:
    findings = check_state.check_campaign(campaign, scope=scope)["findings"]
    return {item["rule"] for item in findings if item["severity"] == "error"}


def test_typed_durable_commit_places_text_and_stamps(campaign: Path) -> None:
    # The fixture is deliberately minimal, so compare against its own baseline.
    baseline = _error_rules(campaign, "hot")
    result = rpg_state.commit_durable(campaign, _durable())

    assert result["ok"] and result["continuity_revision"] == 1
    # The new T2 note is minimal, so the writer names the fields the full check
    # will require; nothing else warns.
    assert result["warnings"] and {item["rule"] for item in result["warnings"]} == {"note_incomplete"}
    assert any("Power Band" in item["message"] for item in result["warnings"])
    state = _read(campaign, "current_state.yaml")
    assert '  summary: "The witness named the courier."' in state
    assert '    - "Witness"\n    - "Ilse"\n' in state
    knowledge = _read(campaign, "knowledge_boundaries.md")
    assert "- Fact: the courier is called Ilse.\n  - Fact id: PK-008\n  - Last confirmed: revision 1\n" in knowledge
    assert knowledge.index("PK-008") < knowledge.index("## NPC Knowledge")
    cast = _read(campaign, "active_cast.md")
    assert "As of revision: 1" in cast and cast.endswith("| Ilse | old dock | listening |\n")
    assert _error_rules(campaign, "hot") <= baseline


def test_retry_of_a_typed_commit_is_idempotent(campaign: Path) -> None:
    payload = _durable()
    rpg_state.commit_durable(campaign, payload)
    retry = rpg_state.commit_durable(campaign, payload)
    assert retry["idempotent"] is True
    assert _read(campaign, "knowledge_boundaries.md").count("Ilse") == 1


def test_checkpoint_fields_are_copied_into_the_scene_frame(campaign: Path) -> None:
    payload = _durable(
        boundary="scene_checkpoint",
        checkpoint={
            "scene_id": "dock-after",
            "scene_mode": "aftermath",
            "resume_anchor": "Ilse waits for Mira's question.",
            "active_cast_handoff": "Ilse stays at the dock",
        },
    )
    payload["changes"] = [item for item in payload["changes"] if item["id"] != "scene"]
    payload["mutations"] = [item for item in payload["mutations"] if item["path"] != "current_state.yaml"]
    result = rpg_state.commit_durable(campaign, payload)

    assert result["checkpoint_committed"] is True
    state = _read(campaign, "current_state.yaml")
    assert "  scene_id: dock-after\n" not in state  # quoted because of the dash
    assert '  scene_id: "dock-after"\n' in state
    assert "  mode: aftermath\n" in state
    assert '  resume_anchor: "Ilse waits for Mira\'s question."\n' in state


def test_pure_checkpoint_needs_no_state_mutation(campaign: Path) -> None:
    result = rpg_state.commit_checkpoint(
        campaign,
        {
            "operation_id": "cp-001",
            "expected_continuity_revision": 0,
            "checkpoint": {
                "scene_id": "dock_pause",
                "scene_mode": "breather",
                "resume_anchor": "Mira lights a lamp; the witness waits.",
                "active_cast_handoff": "none",
            },
        },
    )
    assert result["ok"] and result["continuity_revision"] == 0
    assert "  scene_id: dock_pause\n" in _read(campaign, "current_state.yaml")


def test_failed_typed_op_writes_nothing(campaign: Path) -> None:
    before = {path.name: path.read_bytes() for path in campaign.iterdir() if path.is_file()}
    payload = _durable()
    payload["mutations"][1]["ops"][0]["heading"] = "Missing Heading"
    with pytest.raises(rpg_state.RPGStateError, match="matched 0 headings"):
        rpg_state.commit_durable(campaign, payload)
    after = {path.name: path.read_bytes() for path in campaign.iterdir() if path.is_file()}
    assert before == after


def test_typed_edit_cannot_touch_persistence_fields(campaign: Path) -> None:
    payload = _durable()
    payload["mutations"][0]["ops"] = [{"op": "set", "key": "persistence.last_distilled_revision", "value": 3}]
    with pytest.raises(rpg_state.RPGStateError, match="managed by the writer"):
        rpg_state.commit_durable(campaign, payload)


def test_entity_note_stacking_and_size_produce_warnings(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    note = campaign / "characters" / "witness.md"
    note.write_text(
        note.read_text(encoding="utf-8") + "\n## Current State (day 2)\n\nCalmer.\n\n## Current State (day 3)\n\nTalking.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(rpg_state, "SIZE_WARNING_TEXT", 50)
    payload = _durable()
    payload["changes"].append(
        {
            "id": "mood",
            "kind": "npc_state",
            "established_delta": "The witness relaxed.",
            "owners": ["characters/witness.md"],
        }
    )
    payload["mutations"].append(
        {"path": "characters/witness.md", "ops": [{"op": "append", "heading": "Agency Card", "text": "- Mood: relaxed"}]}
    )
    result = rpg_state.commit_durable(campaign, payload)
    rules = {(item["rule"], item["path"]) for item in result["warnings"]}
    assert ("stacked_sections", "characters/witness.md") in rules
    assert ("owner_size_budget", "knowledge_boundaries.md") in rules


def test_input_file_from_stdin(campaign: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    raw = json.dumps(_durable(), ensure_ascii=False).encode("utf-8")
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8"))
    code = rpg_state.main([str(campaign), "commit-durable", "--input-file", "-"])
    assert code == 0
    assert json.loads(capsys.readouterr().out)["continuity_revision"] == 1


def _simple(operation_id: str, expected: int, number: int) -> dict:
    """A one-fact durable turn that creates nothing."""

    payload = _durable(operation_id, expected)
    payload["changes"] = [
        {"id": "c", "kind": "knowledge", "established_delta": f"Fact {number}.", "owners": ["knowledge_boundaries.md"]}
    ]
    payload["mutations"] = [
        {
            "path": "knowledge_boundaries.md",
            "ops": [{"op": "append", "heading": "Player Knowledge", "text": f"- Fact: clue {number}.\n  - Fact id: {{{{next_id:PK}}}}"}],
        }
    ]
    return payload


def _commit_turns(campaign: Path, count: int) -> None:
    for number in range(count):
        payload = _simple(f"turn-{number:03d}", number, number)
        if number == 0:
            payload["changes"][0]["cold_targets"] = [{"path": "secrets_and_clues.md", "reason": "mirror the clue"}]
        rpg_state.commit_durable(campaign, payload)


def test_commit_distill_closes_the_boundary(campaign: Path) -> None:
    _commit_turns(campaign, 3)
    payload = {
        "operation_id": "distill-3",
        "expected_continuity_revision": 3,
        "trigger": "session end",
        "summary": "Mira found three clues at the dock.",
        "mutations": [
            {"path": "secrets_and_clues.md", "ops": [{"op": "append", "text": "- Clue 0: found (revision {{revision}})"}]},
            {
                "path": "relationship_map.md",
                "ops": [
                    {
                        "op": "upsert_row",
                        "key": ["Mira", "->", "Witness"],
                        "cells": ["Mira", "->", "Witness", "grudging trust"],
                    }
                ],
            },
        ],
    }
    result = rpg_state.commit_distill(campaign, payload)

    assert result["distilled_through"] == 3 and result["unreconciled_targets"] == []
    assert not {item["rule"] for item in result["full_check"]["findings"]} & LOG_RULES
    state = _read(campaign, "current_state.yaml")
    assert "  last_distilled_revision: 3\n  durable_turns_since_distill: 0\n  pending_cold_targets: []\n" in state
    log = _read(campaign, "session_log.md")
    assert "### Session Summary Through Revision 3\n\nMira found three clues at the dock." in log
    assert "### Distilled Through Revision 3\n\n- Trigger: session end\n" in log
    assert "- Files reconciled: relationship_map.md, secrets_and_clues.md\n" in log
    assert "As of revision: 3" in _read(campaign, "relationship_map.md")
    assert rpg_state.commit_distill(campaign, payload)["idempotent"] is True


def test_commit_distill_rotates_history_before_the_previous_marker(campaign: Path) -> None:
    _commit_turns(campaign, 2)
    rpg_state.commit_distill(
        campaign, {"operation_id": "d-2", "expected_continuity_revision": 2, "trigger": "cadence", "summary": "First."}
    )
    payload = _simple("turn-after", 2, 2)
    rpg_state.commit_durable(campaign, payload)
    result = rpg_state.commit_distill(
        campaign,
        {"operation_id": "d-3", "expected_continuity_revision": 3, "trigger": "cadence", "rotate_log": True},
    )

    assert result["archived_log"] == "archive/session_log_through_r2.md"
    archive = _read(campaign, result["archived_log"])
    log = _read(campaign, "session_log.md")
    assert "### Durable Revision 1" in archive and "### Durable Revision 1" not in log
    assert log.startswith("# Session Log")
    assert "### Session Summary Through Revision 2" in log and "### Distilled Through Revision 2" in log
    assert "### Durable Revision 3" in log and "### Distilled Through Revision 3" in log
    assert not {item["rule"] for item in result["full_check"]["findings"]} & LOG_RULES
    # The writer still accepts the next turn after rotation.
    assert rpg_state.commit_durable(campaign, _simple("turn-next", 3, 3))["continuity_revision"] == 4


@pytest.mark.parametrize("path", ["current_state.yaml", "session_log.md", "play_profile.yaml", "archive/x.md"])
def test_commit_distill_refuses_owner_state_and_log(campaign: Path, path: str) -> None:
    payload = {
        "operation_id": "d-bad",
        "expected_continuity_revision": 0,
        "trigger": "manual",
        "mutations": [{"path": path, "exact_replacements": [{"old": "a", "new": "b"}]}],
    }
    with pytest.raises(rpg_state.RPGStateError):
        rpg_state.commit_distill(campaign, payload)


def test_commit_distill_rejects_a_stale_revision(campaign: Path) -> None:
    with pytest.raises(rpg_state.RPGStateError, match="expected continuity revision 4"):
        rpg_state.commit_distill(campaign, {"operation_id": "d", "expected_continuity_revision": 4, "trigger": "x"})


def test_full_check_reports_stacked_sections_and_log_size(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    note = campaign / "characters" / "witness.md"
    note.write_text(
        note.read_text(encoding="utf-8")
        + "\n## State On Day 2\n\na\n\n## State On Day 3\n\nb\n\n## State On Day 4 (current)\n\nc\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(check_state, "SESSION_LOG_SIZE_WARNING", 10)
    rules = {item["rule"] for item in check_state.check_campaign(campaign, scope="full")["findings"]}
    assert {"stacked_sections", "session_log_size"} <= rules

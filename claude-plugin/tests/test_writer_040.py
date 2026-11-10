"""Writer behavior added in 0.4.0, on synthetic campaigns only."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

import check_state
import owner_ops
import rpg_state


PLUGIN = Path(__file__).resolve().parents[1] / "plugin"
SH = shutil.which("sh")


def _read(campaign: Path, relative: str) -> str:
    return (campaign / relative).read_text(encoding="utf-8")


def _write(campaign: Path, relative: str, text: str) -> None:
    (campaign / relative).write_bytes(text.encode("utf-8"))


def _turn(operation_id: str = "t-1", expected: int = 0, *, owner: str, ops: list[dict], **extra) -> dict:
    """One durable change with one typed mutation."""

    payload = {
        "operation_id": operation_id,
        "expected_continuity_revision": expected,
        "boundary": "ordinary",
        "cause": "Mira kept talking to the witness.",
        "resume_impact": "Keep what changed.",
        "changes": [{"id": "c", "kind": "npc_state", "established_delta": "Something changed.", "owners": [owner]}],
        "mutations": [{"path": owner, "ops": ops}],
    }
    payload.update(extra)
    return payload


def _rules(result: dict) -> list[str]:
    return [item["rule"] for item in result["warnings"]]


def _distill(operation_id: str = "d-1", expected: object = 0, **extra) -> dict:
    return {"operation_id": operation_id, "expected_continuity_revision": expected, "trigger": "manual", **extra}


def _fake_check(monkeypatch: pytest.MonkeyPatch, findings: list[dict]) -> None:
    fake = {"ok": True, "error_count": 0, "warning_count": len(findings), "findings": findings}
    monkeypatch.setattr(rpg_state._candidate_checker(), "check_campaign", lambda root, scope="full": fake)


# ---------------------------------------------------------------------------
# Typed edits: Unicode keys
# ---------------------------------------------------------------------------


STATS = 'player:\n  stats:\n    Algı: 3\n    "Sokak Zekâsı": 2\n    Güç: 1\n'


def test_key_paths_accept_unicode_identifiers_and_quoted_keys() -> None:
    result = owner_ops.apply_yaml_ops(
        STATS,
        [{"op": "set", "values": {"player.stats.Algı": 4, 'player.stats."Sokak Zekâsı"': 5}}],
        label="m",
    )
    assert result == 'player:\n  stats:\n    Algı: 4\n    "Sokak Zekâsı": 5\n    Güç: 1\n'


@pytest.mark.parametrize("key", ["player.stats.", "player..stats", 'player.stats."unclosed', "player.stats.Sokak Zekâsı"])
def test_malformed_key_paths_are_refused(key: str) -> None:
    with pytest.raises(owner_ops.OwnerOpError, match="dot-separated keys"):
        owner_ops.apply_yaml_ops(STATS, [{"op": "set", "key": key, "value": 1}], label="m")


# ---------------------------------------------------------------------------
# Input decoding and the launcher
# ---------------------------------------------------------------------------


def test_a_cp1254_input_file_is_decoded_with_a_warning(campaign: Path, tmp_path: Path, capsysbinary) -> None:
    payload = _turn(
        owner="knowledge_boundaries.md",
        ops=[{"op": "append", "heading": "Player Knowledge", "text": "- Fact: Ilse'nin gemisi Şubat'ta geldi."}],
    )
    payload["changes"][0]["kind"] = "knowledge"
    source = tmp_path / "payload.json"
    source.write_bytes(json.dumps(payload, ensure_ascii=False).encode("cp1254"))

    code = rpg_state.main([str(campaign), "commit-durable", "--input-file", str(source)])

    out = json.loads(capsysbinary.readouterr().out.decode("utf-8"))
    assert code == 0 and out["ok"]
    assert out["warnings"][0]["rule"] == "input_decoded_cp1254"
    assert "Ilse'nin gemisi Şubat'ta geldi." in _read(campaign, "knowledge_boundaries.md")


def test_utf8_input_with_a_bom_needs_no_warning(campaign: Path, tmp_path: Path, capsysbinary) -> None:
    source = tmp_path / "payload.json"
    source.write_bytes(b"\xef\xbb\xbf" + json.dumps({"operation_id": "d-bom", "expected_continuity_revision": 0, "trigger": "x"}).encode())
    assert rpg_state.main([str(campaign), "commit-distill", "--input-file", str(source)]) == 0
    out = json.loads(capsysbinary.readouterr().out.decode("utf-8"))
    assert not [item for item in out["warnings"] if item["rule"].startswith("input_decoded")]


def test_launcher_exports_utf8_settings() -> None:
    script = (PLUGIN / "scripts" / "repog.sh").read_text(encoding="utf-8")
    assert "PYTHONUTF8=1" in script and "PYTHONIOENCODING=utf-8" in script
    assert "export PYTHONUTF8 PYTHONIOENCODING" in script


@pytest.mark.skipif(SH is None, reason="needs a POSIX sh")
def test_launcher_runs_the_template_helper(campaign: Path) -> None:
    completed = subprocess.run(
        [SH, str(PLUGIN / "scripts" / "repog.sh"), "rpg_state", str(campaign), "template", "--kind", "checkpoint"],
        capture_output=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout.decode("utf-8"))["payload"]["expected_continuity_revision"] == 0


# ---------------------------------------------------------------------------
# Results: next_expected_revision, reply, stale revisions
# ---------------------------------------------------------------------------


def test_every_result_names_the_next_expected_revision(campaign: Path) -> None:
    durable = rpg_state.commit_durable(
        campaign,
        _turn(owner="knowledge_boundaries.md", ops=[{"op": "append", "heading": "Player Knowledge", "text": "- Fact: x."}]),
    )
    assert durable["next_expected_revision"] == 1 and durable["reply"] == rpg_state.REPLY_NOTE
    assert "narration_allowed" in durable
    checkpoint = rpg_state.commit_checkpoint(
        campaign,
        {
            "operation_id": "cp-1",
            "expected_continuity_revision": 1,
            "checkpoint": {
                "scene_id": "dock_pause",
                "scene_mode": "breather",
                "resume_anchor": "The witness waits.",
                "active_cast_handoff": "none",
            },
        },
    )
    assert checkpoint["next_expected_revision"] == 1
    distill = rpg_state.commit_distill(campaign, _distill(expected="current"))
    assert distill["next_expected_revision"] == 1 and distill["distilled_through"] == 1
    assert rpg_state.commit_curation(campaign)["next_expected_revision"] == 1


def test_a_stale_revision_failure_carries_the_current_revision(campaign: Path, capsysbinary) -> None:
    payload = _turn(expected=3, owner="knowledge_boundaries.md", ops=[{"op": "append", "text": "x"}])
    assert rpg_state.main([str(campaign), "commit-durable", "--input-json", json.dumps(payload)]) == 2
    out = json.loads(capsysbinary.readouterr().out.decode("utf-8"))
    assert out["failure_category"] == "stale_revision" and out["next_expected_revision"] == 0


def test_current_is_accepted_by_commit_distill_only(campaign: Path) -> None:
    with pytest.raises(rpg_state.RPGStateError, match="non-negative integer"):
        rpg_state.commit_durable(
            campaign, _turn(expected="current", owner="knowledge_boundaries.md", ops=[{"op": "append", "text": "x"}])
        )
    assert rpg_state.commit_distill(campaign, _distill(expected="current"))["distilled_through"] == 0


# ---------------------------------------------------------------------------
# Distill gate and curation_due
# ---------------------------------------------------------------------------


def _cast_finding(campaign: Path, rule: str = "cast_dead_listed", relative: str = "active_cast.md") -> dict:
    return {"severity": "warning", "rule": rule, "message": "Witness is dead but listed", "path": str(campaign / relative)}


def test_the_gate_refuses_an_unreconciled_finding_and_writes_nothing(
    campaign: Path, monkeypatch: pytest.MonkeyPatch, capsysbinary
) -> None:
    _fake_check(monkeypatch, [_cast_finding(campaign)])
    before = _read(campaign, "session_log.md")

    code = rpg_state.main([str(campaign), "commit-distill", "--input-json", json.dumps(_distill())])

    out = json.loads(capsysbinary.readouterr().out.decode("utf-8"))
    assert code == 2 and out["failure_category"] == "distill_unreconciled"
    assert out["unreconciled"] == [
        {"path": "active_cast.md", "rule": "cast_dead_listed", "message": "Witness is dead but listed"}
    ]
    assert _read(campaign, "session_log.md") == before


def test_a_finding_whose_file_the_distill_changes_passes_the_gate(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_check(monkeypatch, [_cast_finding(campaign)])
    payload = _distill(mutations=[{"path": "active_cast.md", "ops": [{"op": "delete_row", "key": "Witness"}]}])
    result = rpg_state.commit_distill(campaign, payload)
    assert result["ok"] and "Witness" not in _read(campaign, "active_cast.md")


def test_a_deferred_finding_goes_to_curation_due(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_check(monkeypatch, [_cast_finding(campaign)])
    payload = _distill(deferred_reconcile=[{"path": "active_cast.md", "reason": "retire the witness row"}])

    result = rpg_state.commit_distill(campaign, payload)

    due = json.loads(_read(campaign, ".repog-runtime/curation_due.json"))
    assert due["revision"] == 0 and due["at"].endswith("Z")
    assert due["targets"] == result["curation_due"]
    assert [(item["path"], item["rule"]) for item in due["targets"]] == [("active_cast.md", "cast_dead_listed")]
    assert "retire the witness row" in due["targets"][0]["reason"]


def test_minor_romance_history_cannot_be_deferred(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_check(monkeypatch, [_cast_finding(campaign, "minor_romance_history", "characters/witness.md")])
    payload = _distill(deferred_reconcile=[{"path": "characters/witness.md", "reason": "later"}])
    with pytest.raises(rpg_state.RPGStateError, match="minor_romance_history cannot be deferred") as caught:
        rpg_state.commit_distill(campaign, payload)
    assert caught.value.category == "distill_unreconciled"


def test_ungated_and_unreachable_findings_do_not_block(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_check(
        monkeypatch,
        [
            _cast_finding(campaign, "owner_size_budget"),  # not a gate rule
            _cast_finding(campaign, "location_unmapped", "location_graph.md"),  # no such file to edit
            _cast_finding(campaign, "cast_present_missing", "current_state.yaml"),  # a distill cannot edit it
            {**_cast_finding(campaign), "severity": "info"},  # acknowledged by a directive
        ],
    )
    assert rpg_state.commit_distill(campaign, _distill())["ok"]


def test_deferral_must_name_a_file_the_curator_can_edit(campaign: Path) -> None:
    for path in ("current_state.yaml", "directives.md", "characters/nobody.md"):
        payload = _distill(deferred_reconcile=[{"path": path, "reason": "later"}])
        with pytest.raises(rpg_state.RPGStateError, match="cannot go to the curator"):
            rpg_state.commit_distill(campaign, payload)


def test_deferred_cold_targets_are_not_unreconciled(campaign: Path) -> None:
    payload = _turn(owner="knowledge_boundaries.md", ops=[{"op": "append", "heading": "Player Knowledge", "text": "- Fact: y."}])
    payload["changes"][0]["kind"] = "knowledge"
    payload["changes"][0]["cold_targets"] = [{"path": "secrets_and_clues.md", "reason": "mirror the clue"}]
    rpg_state.commit_durable(campaign, payload)
    result = rpg_state.commit_distill(
        campaign, _distill(expected=1, deferred_reconcile=[{"path": "secrets_and_clues.md", "reason": "curator mirrors it"}])
    )
    assert result["unreconciled_targets"] == []
    due = {item["path"]: item for item in result["curation_due"]}
    assert due["secrets_and_clues.md"] == {
        "path": "secrets_and_clues.md",
        "rule": "deferred_reconcile",
        "reason": "curator mirrors it",
    }


def test_curation_due_collects_flagged_notes_and_drops_curated_ones(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import hashlib

    _write(campaign, "characters/ilse.md", "# Ilse\n\n- Tier: T2\n")
    _fake_check(
        monkeypatch,
        [
            {"severity": "warning", "rule": "records_language_mismatch", "message": "other language: characters/ilse.md", "path": str(campaign)},
            {"severity": "warning", "rule": "note_core_missing", "message": "1 note(s) have no ## Core: Witness.", "path": str(campaign / "characters")},
        ],
    )
    first = rpg_state.commit_distill(campaign, _distill())
    assert [item["path"] for item in first["curation_due"]] == ["characters/ilse.md", "characters/witness.md"]

    folder = campaign / ".repog-runtime" / "curation"
    folder.mkdir(parents=True)
    note = campaign / "characters" / "witness.md"
    staged = {
        "curation_id": "cur-1",
        "base_revision": 0,
        "reason": "add the Core block",
        "base_hashes": {"characters/witness.md": hashlib.sha256(note.read_bytes()).hexdigest()},
        "mutations": [{"path": "characters/witness.md", "ops": [{"op": "insert_section", "heading": "## Core", "text": "- Status: alive"}]}],
    }
    (folder / "cur-1.json").write_text(json.dumps(staged), encoding="utf-8")
    rpg_state.commit_curation(campaign, settle_seconds=0)
    due = json.loads(_read(campaign, ".repog-runtime/curation_due.json"))
    assert [item["path"] for item in due["targets"]] == ["characters/ilse.md"]

    _fake_check(monkeypatch, [])
    mutation = {"path": "characters/ilse.md", "ops": [{"op": "append", "text": "Tidied."}]}
    assert rpg_state.commit_distill(campaign, _distill("d-2", mutations=[mutation]))["curation_due"] == []
    assert not (campaign / ".repog-runtime" / "curation_due.json").exists()


def test_curation_due_takes_every_file_an_aggregated_finding_lists(
    campaign: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    notes = [f"characters/npc_{index:02d}.md" for index in range(25)]
    for relative in notes:
        _write(campaign, relative, "# Npc\n\n- Tier: T2\n")
    clipped = ", ".join(notes[:20]) + ", and 5 more"  # the message lists at most 20 files
    _fake_check(
        monkeypatch,
        [
            {
                "severity": "warning",
                "rule": "records_language_mismatch",
                "message": f"25 record file(s) read as another language: {clipped}; see characters/witness.md.",
                "path": str(campaign),
                "paths": [str(campaign / relative) for relative in notes],
            }
        ],
    )
    due = rpg_state.commit_distill(campaign, _distill())["curation_due"]
    assert [item["path"] for item in due] == notes  # `paths` wins over the message


def test_a_title_inside_a_longer_title_is_not_a_target(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(campaign, "characters/ali.md", "# Ali\n\n## Core\n\n- Status: alive\n")
    _write(campaign, "characters/ali_reis.md", "# Ali Reis\n\n- Tier: T2\n")
    message = "2 T2/T3 note(s) have no ## Core block (status, kin, address): Ali Reis, Witness."
    _fake_check(
        monkeypatch,
        [{"severity": "warning", "rule": "note_core_missing", "message": message, "path": str(campaign / "characters")}],
    )
    due = rpg_state.commit_distill(campaign, _distill())["curation_due"]
    assert [item["path"] for item in due] == ["characters/ali_reis.md", "characters/witness.md"]


# ---------------------------------------------------------------------------
# Log rotation and receipts
# ---------------------------------------------------------------------------


def _distilled_once(campaign: Path) -> None:
    rpg_state.commit_durable(
        campaign,
        _turn(owner="knowledge_boundaries.md", ops=[{"op": "append", "heading": "Player Knowledge", "text": "- Fact: z."}]),
    )
    rpg_state.commit_distill(campaign, _distill("d-first", expected=1))
    rpg_state.commit_durable(
        campaign,
        _turn("t-2", 1, owner="knowledge_boundaries.md", ops=[{"op": "append", "heading": "Player Knowledge", "text": "- Fact: w."}]),
    )


def _grow_log(campaign: Path) -> None:
    log = _read(campaign, "session_log.md")
    filler = "\n".join(f"Old note line {index} " + "x" * 80 for index in range(1700))
    first = log.index("### Durable Revision 1")
    _write(campaign, "session_log.md", log[:first] + "### Session Notes\n\n" + filler + "\n\n" + log[first:])


def test_a_large_log_rotates_without_being_asked(campaign: Path) -> None:
    _distilled_once(campaign)
    _grow_log(campaign)
    assert len(_read(campaign, "session_log.md")) > rpg_state.LOG_AUTO_ROTATE_TEXT

    result = rpg_state.commit_distill(campaign, _distill("d-auto", expected=2))

    assert result["archived_log"] == "archive/session_log_through_r1.md"
    assert "Old note line 5 " in _read(campaign, result["archived_log"])
    assert len(_read(campaign, "session_log.md")) < rpg_state.LOG_AUTO_ROTATE_TEXT


def test_rotate_log_false_keeps_a_large_log_whole(campaign: Path) -> None:
    _distilled_once(campaign)
    _grow_log(campaign)
    result = rpg_state.commit_distill(campaign, _distill("d-keep", expected=2, rotate_log=False))
    assert result["archived_log"] is None and "Old note line 5 " in _read(campaign, "session_log.md")


def test_an_archive_name_collision_gets_a_suffix(campaign: Path) -> None:
    _distilled_once(campaign)
    (campaign / "archive").mkdir()
    _write(campaign, "archive/session_log_through_r1.md", "# earlier archive\n")
    _write(campaign, "archive/session_log_through_r1-2.md", "# another\n")
    result = rpg_state.commit_distill(campaign, _distill("d-rot", expected=2, rotate_log=True))
    assert result["archived_log"] == "archive/session_log_through_r1-3.md"
    assert _read(campaign, "archive/session_log_through_r1.md") == "# earlier archive\n"


def test_receipts_omit_none_lines(campaign: Path) -> None:
    payload = _turn(owner="knowledge_boundaries.md", ops=[{"op": "append", "heading": "Player Knowledge", "text": "- Fact: q."}])
    payload["resume_impact"] = "none"
    payload["boundary"] = "scene_checkpoint"
    payload["checkpoint"] = {
        "scene_id": "dock",
        "scene_mode": "focused",
        "resume_anchor": "The witness waits.",
        "active_cast_handoff": "none",
        "open_choices": ["Ask again"],
    }
    rpg_state.commit_durable(campaign, payload)
    log = _read(campaign, "session_log.md")
    assert "Deferred propagation" not in log and "Resume impact" not in log and "Active-cast handoff" not in log
    assert "- Boundary: scene_checkpoint\n- Payload hash: sha256:" in log


def test_an_old_receipt_with_none_lines_still_parses_and_retries(campaign: Path) -> None:
    payload = _turn(owner="knowledge_boundaries.md", ops=[{"op": "append", "heading": "Player Knowledge", "text": "- Fact: r."}])
    rpg_state.commit_durable(campaign, payload)
    log = _read(campaign, "session_log.md")
    old_form = log.replace(
        "- Boundary: ordinary\n",
        "- Deferred propagation: none — no secondary surface affected\n- Boundary: ordinary\n",
    )
    assert old_form != log
    _write(campaign, "session_log.md", old_form)

    receipts = rpg_state._receipt_blocks(old_form)
    assert [(item["revision"], item["operation_id"]) for item in receipts] == [(1, "t-1")]
    assert rpg_state.commit_durable(campaign, payload)["idempotent"] is True


# ---------------------------------------------------------------------------
# ## Now budget
# ---------------------------------------------------------------------------


NOTE = """# Ilse

## Core

- Status: alive

## Now

<!--
Guidance that does not count toward the budget.
-->

- Day 1: arrived at the dock.
- Day 3: argued with the witness.
Keeps her coat buttoned to the throat.
- Gün 2: slept in the warehouse.

## Agency Card

- Tier: T2
"""


def _note_turn(text: str, operation_id: str = "n-1", expected: int = 0) -> dict:
    return _turn(operation_id, expected, owner="characters/ilse.md", ops=[{"op": "replace_section", "heading": "Now", "text": text}])


def test_now_overflow_folds_the_oldest_dated_entries_into_history(campaign: Path) -> None:
    _write(campaign, "characters/ilse.md", NOTE)
    text = "- Day 1: arrived.\n- Day 4: hid the ledger.\nKeeps her coat buttoned.\n- Day 2: slept.\n- Day 3: argued (with the witness)."

    result = rpg_state.commit_durable(campaign, _note_turn(text))

    note = _read(campaign, "characters/ilse.md")
    now = note.split("## Now", 1)[1].split("## History", 1)[0]
    history = note.split("## History", 1)[1].split("## Agency Card", 1)[0]
    assert "Day 1: arrived." in history and "Day 1" not in now
    assert "Keeps her coat buttoned." in now and "Day 4" in now
    assert note.index("## Now") < note.index("## History") < note.index("## Agency Card")
    folded = [item for item in result["warnings"] if item["rule"] == "now_overflow_folded"]
    assert folded == [
        {"rule": "now_overflow_folded", "path": "characters/ilse.md", "message": folded[0]["message"], "count": 1}
    ]


def test_dated_entries_in_any_pack_language_and_parentheses_count() -> None:
    text = NOTE.replace("- Gün 2: slept in the warehouse.", "- Gün 2: slept.\n- Tag 5: left.\n- Lost her ring (day 4).")
    assert owner_ops.now_status(text)[1] == 5
    folded, moved = owner_ops.fold_now(text)
    assert moved == 2
    history = folded.split("## History", 1)[1]
    assert history.index("Day 1") < history.index("Gün 2")
    assert "<!--" in folded.split("## History", 1)[0]  # the guidance comment stays in Now


def test_an_existing_history_receives_the_folded_entries(campaign: Path) -> None:
    _write(campaign, "characters/ilse.md", NOTE.replace("## Agency Card", "## History\n\n- Day 0: was born.\n\n## Agency Card"))
    entries = "\n".join(f"- Day {day}: event {day}." for day in range(5, 10))
    rpg_state.commit_durable(campaign, _note_turn(entries))
    note = _read(campaign, "characters/ilse.md")
    assert note.count("## History") == 1
    assert "- Day 0: was born.\n- Day 5: event 5.\n- Day 6: event 6.\n\n## Agency Card" in note


def test_undated_text_over_budget_warns_without_moving_anything(campaign: Path) -> None:
    _write(campaign, "characters/ilse.md", NOTE)
    long_text = "She watches the harbour. " * 40
    result = rpg_state.commit_durable(campaign, _note_turn(long_text))
    assert "now_overflow" in _rules(result) and "now_overflow_folded" not in _rules(result)
    assert "## History" not in _read(campaign, "characters/ilse.md")


def test_appending_to_now_is_the_cheap_way_to_add_an_entry(campaign: Path) -> None:
    _write(campaign, "characters/ilse.md", NOTE)
    payload = _turn(owner="characters/ilse.md", ops=[{"op": "append", "heading": "## Now", "text": "- Day 4: waited."}])
    assert "now_append" not in _rules(rpg_state.commit_durable(campaign, payload))
    assert "- Day 4: waited." in (campaign / "characters/ilse.md").read_text(encoding="utf-8")


def test_ordinal_day_markers_count_as_dated() -> None:
    dated = [
        "- 10. gün: iskelede bekledi.",
        "- 11. günde limana indi.",
        "- 12'nci gün: yattı.",
        "- 13. Tag: ging.",
        "- 14th day: left.",
        "- 15e jour: parti.",
        "- 16º día: salió.",
        "- Yüzüğünü kaybetti (17. gün).",
    ]
    assert owner_ops.now_status("## Now\n\n" + "\n".join(dated) + "\n")[1] == len(dated)
    for undated in ("- 3 gün sonra döndü.", "- 12. Güneş batarken geldi.", "- 3 days later she left."):
        assert owner_ops.now_status(f"## Now\n\n{undated}\n")[1] == 0


def test_turkish_ordinal_days_fold_into_history(campaign: Path) -> None:
    _write(campaign, "characters/ilse.md", NOTE)
    text = "\n".join(f"- {day}. gün: iskelede tanıkla uzun uzun konuştu." for day in range(10, 18))

    result = rpg_state.commit_durable(campaign, _note_turn(text))

    assert "now_overflow_folded" in _rules(result) and "now_overflow" not in _rules(result)
    note = _read(campaign, "characters/ilse.md")
    assert owner_ops.now_status(note)[1] == 3
    assert "- 10. gün:" in note.split("## History", 1)[1]


def test_a_folded_entry_takes_its_nested_lines_along() -> None:
    text = (
        "# Ilse\n\n## Now\n\n- Day 1: arrived.\n  - Lost her ring on the gangway.\n\n    Still looking for it.\n"
        "- Day 2: slept.\n- Day 3: argued.\n- Day 4: hid the ledger.\nKeeps her coat buttoned.\n"
    )
    folded, moved = owner_ops.fold_now(text)
    now, history = folded.split("## Now", 1)[1].split("## History", 1)
    assert moved == 1
    assert "ring" not in now and "Still looking" not in now and "Keeps her coat buttoned." in now
    assert "- Day 1: arrived.\n  - Lost her ring on the gangway.\n\n    Still looking for it.\n" in history
    # A dated line nested under an entry is part of that entry.
    assert owner_ops.now_status("## Now\n\n- Day 1: arrived.\n  - Day 2: slept.\n")[1] == 1


# ---------------------------------------------------------------------------
# Durable advisories
# ---------------------------------------------------------------------------


def test_a_death_lists_the_rows_the_commit_left_unchanged(campaign: Path) -> None:
    _write(campaign, "characters/witness.md", "# Witness\n\n## Core\n\n- Status: alive\n\n## Agency Card\n\n- Tier: T2\n")
    payload = _turn(
        owner="characters/witness.md",
        ops=[{"op": "replace", "old": "- Status: alive", "new": "- Status: dead"}],
    )
    result = rpg_state.commit_durable(campaign, payload)
    projection = [item for item in result["warnings"] if item["rule"] == "death_projection"]
    assert len(projection) == 1 and projection[0]["path"] == "characters/witness.md"
    assert projection[0]["rows"] == [
        {"path": "active_cast.md", "row": "| Witness | old dock | waiting |"},
        {"path": "relationship_map.md", "row": "| Mira | -> | Witness | wary |"},
    ]


def test_rows_changed_in_the_same_commit_are_not_projected(campaign: Path) -> None:
    _write(campaign, "characters/witness.md", "# Witness\n\n## Core\n\n- Status: alive\n")
    payload = _turn(owner="characters/witness.md", ops=[{"op": "replace", "old": "- Status: alive", "new": "- Status: missing"}])
    payload["changes"][0]["owners"].append("active_cast.md")
    payload["mutations"].append({"path": "active_cast.md", "ops": [{"op": "delete_row", "key": "Witness"}]})
    payload["changes"].append(
        {"id": "r", "kind": "relationship", "established_delta": "Ended.", "owners": ["relationship_map.md"]}
    )
    payload["mutations"].append(
        {
            "path": "relationship_map.md",
            "ops": [{"op": "upsert_row", "key": ["Mira", "->", "Witness"], "cells": ["Mira", "->", "Witness", "missing"]}],
        }
    )
    assert "death_projection" not in _rules(rpg_state.commit_durable(campaign, payload))


def _with_coins(campaign: Path) -> None:
    mechanics = json.loads(_read(campaign, "mechanics_state.json"))
    mechanics["actors"] = {"mira": {"inventory": {"silver_coins": {"quantity": 12, "consumable": True}}}}
    _write(campaign, "mechanics_state.json", json.dumps(mechanics, indent=2) + "\n")


def test_an_inventory_count_for_a_tracked_item_warns(campaign: Path) -> None:
    _with_coins(campaign)
    payload = _turn(
        owner="current_state.yaml",
        ops=[{"op": "list_set", "key": "inventory", "items": ["12 silver coins", "a brass key"]}],
    )
    payload["changes"][0]["kind"] = "inventory"
    result = rpg_state.commit_durable(campaign, payload)
    assert _rules(result).count("inventory_count_duplicate") == 1


def test_an_inventory_line_naming_a_tracked_item_without_a_number_is_fine(campaign: Path) -> None:
    _with_coins(campaign)
    payload = _turn(owner="current_state.yaml", ops=[{"op": "list_set", "key": "inventory", "items": ["silver coins", "2 apples"]}])
    assert "inventory_count_duplicate" not in _rules(rpg_state.commit_durable(campaign, payload))


def _player_rolls(campaign: Path) -> None:
    profile = campaign / "play_profile.yaml"
    profile.write_bytes(profile.read_bytes() + b"mechanics:\n  dice_mode: player_rolls\n")


def _costly_turn(**overrides) -> dict:
    payload = _turn(
        owner="knowledge_boundaries.md",
        ops=[{"op": "append", "heading": "Player Knowledge", "text": "- Fact: the lock gave."}],
    )
    payload["changes"][0].update(kind="knowledge", roll_reference="player: 2d6 on the lock", outcome="success_with_cost")
    payload.update(overrides)
    return payload


def test_a_costly_roll_with_no_recorded_cost_warns(campaign: Path) -> None:
    _player_rolls(campaign)
    assert "cost_unrecorded" in _rules(rpg_state.commit_durable(campaign, _costly_turn()))


def test_a_costly_roll_with_a_pending_consequence_is_fine(campaign: Path) -> None:
    _player_rolls(campaign)
    payload = _costly_turn()
    payload["changes"].append({"id": "s", "kind": "scene_progress", "established_delta": "Noise.", "owners": ["current_state.yaml"]})
    payload["mutations"].append(
        {"path": "current_state.yaml", "ops": [{"op": "list_add", "key": "scene_frame.pending_consequences", "items": ["The guard heard the lock."]}]}
    )
    assert "cost_unrecorded" not in _rules(rpg_state.commit_durable(campaign, payload))


def test_a_clean_success_never_asks_for_a_cost(campaign: Path) -> None:
    _player_rolls(campaign)
    payload = _costly_turn()
    payload["changes"][0]["outcome"] = "success"
    assert "cost_unrecorded" not in _rules(rpg_state.commit_durable(campaign, payload))


# ---------------------------------------------------------------------------
# Checkpoints and refusals
# ---------------------------------------------------------------------------


CHECKPOINT = {
    "scene_id": "dock_after",
    "scene_mode": "aftermath",
    "resume_anchor": "The witness waits.",
    "active_cast_handoff": "none",
}


def test_a_scene_checkpoint_needs_open_choices(campaign: Path, capsysbinary) -> None:
    payload = _turn(owner="knowledge_boundaries.md", ops=[{"op": "append", "text": "x"}])
    payload.update(boundary="scene_checkpoint", checkpoint=dict(CHECKPOINT))
    assert rpg_state.main([str(campaign), "commit-durable", "--input-json", json.dumps(payload)]) == 2
    out = json.loads(capsysbinary.readouterr().out.decode("utf-8"))
    assert out["failure_category"] == "checkpoint_open_choices_missing"

    payload["checkpoint"]["open_choices"] = [f"choice {index}" for index in range(6)]
    with pytest.raises(rpg_state.RPGStateError, match="1 to 5"):
        rpg_state.commit_durable(campaign, payload)

    payload["checkpoint"]["open_choices"] = ["Press the witness", "Walk away"]
    rpg_state.commit_durable(campaign, payload)
    assert '  open_choices:\n    - "Press the witness"\n    - "Walk away"\n' in _read(campaign, "current_state.yaml")


def test_open_choices_are_optional_on_a_pure_checkpoint(campaign: Path) -> None:
    payload = {"operation_id": "cp", "expected_continuity_revision": 0, "checkpoint": dict(CHECKPOINT)}
    assert rpg_state.commit_checkpoint(campaign, payload)["ok"]
    assert "  open_choices: []\n" in _read(campaign, "current_state.yaml")


def test_a_handoff_without_a_cast_mutation_returns_a_ready_op(campaign: Path, capsysbinary) -> None:
    payload = {
        "operation_id": "cp-hand",
        "expected_continuity_revision": 0,
        "checkpoint": {**CHECKPOINT, "active_cast_handoff": "The witness goes home; Ilse arrives."},
    }
    _write(campaign, "characters/ilse.md", "# Ilse\n\n- Tier: T2\n")
    assert rpg_state.main([str(campaign), "commit-checkpoint", "--input-json", json.dumps(payload)]) == 2
    out = json.loads(capsysbinary.readouterr().out.decode("utf-8"))
    assert out["failure_category"] == "input_invalid"
    assert out["suggested_mutation"] == {
        "path": "active_cast.md",
        "ops": [
            {"op": "upsert_row", "key": "Witness", "cells": ["Witness", "old dock", "waiting"]},
            {"op": "upsert_row", "key": "Ilse", "cells": ["Ilse", "", ""]},
        ],
    }
    assert '"upsert_row"' in out["failure_reason"]


def test_relationship_ownership_error_says_to_add_the_owner(campaign: Path) -> None:
    payload = _turn(owner="knowledge_boundaries.md", ops=[{"op": "append", "text": "x"}])
    payload["changes"][0]["kind"] = "relationship_shift"
    with pytest.raises(rpg_state.RPGStateError) as caught:
        rpg_state.commit_durable(campaign, payload)
    message = str(caught.value)
    assert "add relationship_map.md to this change's owners" in message
    assert "declare a kind" not in message


# ---------------------------------------------------------------------------
# Language advisories
# ---------------------------------------------------------------------------


def _language(campaign: Path, code: str, records: str | None = None) -> None:
    extra = f"narration:\n  language: {code}\n" + (f"  records_language: {records}\n" if records else "")
    profile = campaign / "play_profile.yaml"
    profile.write_bytes(profile.read_bytes() + extra.encode("utf-8"))


ENGLISH_NOTE = "# Ilse\n\n- Tier: T1\n\nShe is the one who keeps the ledger, and she does not trust anyone at the dock.\n"
TURKISH_NOTE = "# Ilse\n\n- Tier: T1\n\nDefteri o tutuyor ve iskeledeki hiç kimseye güvenmiyor, ama bunu kimseye söylemiyor.\n"


def _create(path: str, text: str) -> dict:
    return {
        "operation_id": "new-note",
        "expected_continuity_revision": 0,
        "boundary": "ordinary",
        "cause": "A new face.",
        "resume_impact": "Keep her.",
        "changes": [{"id": "n", "kind": "creation", "established_delta": "She appears.", "owners": [path]}],
        "mutations": [{"path": path, "create_text": text}],
    }


def test_record_text_in_another_language_warns(campaign: Path) -> None:
    _language(campaign, "tr")
    result = rpg_state.commit_durable(campaign, _create("characters/ilse.md", ENGLISH_NOTE))
    warning = [item for item in result["warnings"] if item["rule"] == "record_language"]
    assert warning and warning[0]["path"] == "characters/ilse.md" and "en" in warning[0]["message"]


def test_record_text_in_the_records_language_is_quiet(campaign: Path) -> None:
    _language(campaign, "tr")
    result = rpg_state.commit_durable(campaign, _create("characters/ilse.md", TURKISH_NOTE))
    assert not {"record_language", "glossary_suggest"} & set(_rules(result))


def test_records_language_can_differ_from_the_play_language(campaign: Path) -> None:
    _language(campaign, "tr", records="en")
    result = rpg_state.commit_durable(campaign, _create("characters/ilse.md", ENGLISH_NOTE))
    assert "record_language" not in _rules(result)


def test_labels_headings_and_table_headers_are_not_language_evidence(campaign: Path) -> None:
    _language(campaign, "tr")
    text = "| Name | Where | Doing |\n| --- | --- | --- |\n| Ilse | iskele | bekliyor |"
    sample = rpg_state._prose_sample("## The Current State Of Things\n\n- Status of the matter: dead\n" + text)
    assert "Current" not in sample and "Status" not in sample and "Where" not in sample
    assert "dead" in sample and "iskele" in sample


def test_a_foreign_title_gets_a_glossary_row(campaign: Path) -> None:
    _language(campaign, "tr")
    text = "# The Red Fox\n\n- Tier: T1\n\nLimandaki meyhane; kapısı gece yarısına kadar açık kalıyor ve herkes orada.\n"
    result = rpg_state.commit_durable(campaign, _create("places/red_fox.md", text))
    suggestion = [item for item in result["warnings"] if item["rule"] == "glossary_suggest"]
    assert suggestion and suggestion[0]["row"] == {
        "Term": "The Red Fox",
        "Preferred": "",
        "Variants": "",
        "Notes": "first named in places/red_fox.md",
    }


def test_a_term_already_in_the_glossary_gets_no_suggestion(campaign: Path) -> None:
    _language(campaign, "tr")
    _write(campaign, "glossary.md", "# Glossary\n\n| Term | Preferred | Variants | Notes |\n| --- | --- | --- | --- |\n| The Red Fox | Kızıl Tilki | | |\n")
    text = "# The Red Fox\n\n- Tier: T1\n\nLimandaki meyhane; kapısı gece yarısına kadar açık kalıyor ve herkes orada.\n"
    assert "glossary_suggest" not in _rules(rpg_state.commit_durable(campaign, _create("places/red_fox.md", text)))


def _from_template(title: str, value: str, now: str) -> str:
    """A character note started from the shipped template, its guidance left in place."""

    text = (PLUGIN / "templates" / "campaign" / "characters" / "_template.md").read_text(encoding="utf-8")
    text = text.replace("# Character Name", f"# {title}", 1).replace("## Now\n", f"## Now\n\n{now}\n", 1)
    return re.sub(r"(?m)^(- [^:\n]+:).*$", lambda match: f"{match.group(1)} {value}", text)


@pytest.mark.parametrize(
    ("value", "now", "warned"),
    [
        ("iskelede bekliyor", "Limanda bekliyor, kimseye güvenmiyor ve gemisini geri almak istiyor.", False),
        ("waiting at the dock", "She keeps the ledger, and she does not trust anyone at the dock or on the ships.", True),
    ],
)
def test_template_guidance_left_in_a_note_is_not_language_evidence(
    campaign: Path, value: str, now: str, warned: bool
) -> None:
    _language(campaign, "tr")
    note = _from_template("Kaptan Ahmet", value, now)
    result = rpg_state.commit_durable(campaign, _create("characters/kaptan_ahmet.md", note))
    assert ("record_language" in _rules(result)) is warned
    assert ("glossary_suggest" in _rules(result)) is warned


# ---------------------------------------------------------------------------
# lint_report passthrough
# ---------------------------------------------------------------------------


def test_lint_report_is_passed_through(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[Path, int]] = []

    def report_summary(root: Path, last: int = 20) -> dict:
        seen.append((Path(root), last))
        return {"replies": 3, "rules": {"stock_beat": 2}, "top": [], "text": "stock_beat (2)"}

    monkeypatch.setitem(sys.modules, "presentation_lint", types.SimpleNamespace(report_summary=report_summary))
    result = rpg_state.commit_distill(campaign, _distill())
    assert result["lint_report"] == {"replies": 3, "rules": {"stock_beat": 2}, "top": [], "text": "stock_beat (2)"}
    assert seen == [(campaign.resolve(), 20)]


def test_lint_report_is_none_when_the_lint_has_no_summary(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "presentation_lint", types.SimpleNamespace())
    assert rpg_state.commit_distill(campaign, _distill())["lint_report"] is None


# ---------------------------------------------------------------------------
# template
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("kind", rpg_state.TEMPLATE_KINDS)
def test_template_prints_a_skeleton_and_writes_nothing(campaign: Path, kind: str, capsysbinary) -> None:
    before = {path: path.read_bytes() for path in campaign.rglob("*") if path.is_file()}

    assert rpg_state.main([str(campaign), "template", "--kind", kind]) == 0

    out = json.loads(capsysbinary.readouterr().out.decode("utf-8"))
    assert {path: path.read_bytes() for path in campaign.rglob("*") if path.is_file()} == before
    assert out["continuity_revision"] == 0 and out["kind"] == kind
    reference = out["reference"]
    assert reference["scene_modes"] == sorted(rpg_state.SCENE_MODES)
    assert reference["active_cast_columns"] == ["Name", "Where", "Doing"]
    assert reference["relationship_map_columns"] == ["From", "Direction", "To", "Relation"]
    assert reference["kind_owners"]["relationship"] == "relationship_map.md"
    assert {"continuity_revision", "persistence", "current_scene", "scene_frame", "inventory"} <= set(reference["current_state_keys"])
    payload = out["payload"]
    assert rpg_state.OPERATION_ID_RE.fullmatch(payload["operation_id"])
    assert payload["expected_continuity_revision"] == ("current" if kind == "distill" else 0)


# ---------------------------------------------------------------------------
# commit-act
# ---------------------------------------------------------------------------


THREADS = """# Threads

As of revision: 0

## Arc Compass

The single current-act owner.

- Act id: act-1
- Act status: active
- Previous act id: none
- Opened at revision: 0
- Act name: The Courier
- Dramatic question: Will Mira find the courier before the ship sails?
- Active pressures: the ship sails at dawn
- Closure conditions: Mira finds the courier or the ship leaves.

### Act Scope

- Places this act can reach: the old dock
- People who belong to it: the witness, the courier
- What is already in motion as it opens: the courier is hiding
- What stays true if the character does nothing: the ship leaves with the cargo

### Closure Record

- Closing action:
- Condition met or foreclosed:
- Recorded at revision:

## Act Archive

Closed acts.

## Active Threads

- Courier promise: absent
"""


def _act_payload(operation_id: str = "act-2", expected: int = 0, **overrides) -> dict:
    payload = {
        "operation_id": operation_id,
        "expected_continuity_revision": expected,
        "close": {"act_id": "act-1", "outcome": "met", "summary": "Mira caught the courier on the gangway."},
        "open": {
            "act_id": "act-2",
            "title": "The Cargo",
            "dramatic_question": "What is in the courier's crates?",
            "scope": {
                "places": ["the warehouse", "the customs house"],
                "people": "the courier, the customs clerk",
                "in_motion": "the clerk is burning papers",
                "if_ignored": "the crates are shipped inland",
            },
            "closure_conditions": ["Mira opens the crates", "the crates leave the city"],
            "prepared_expectations": ["the clerk's ledger"],
        },
        "checkpoint": {**CHECKPOINT, "scene_id": "warehouse_door", "open_choices": ["Open the crates", "Follow the clerk"]},
    }
    payload.update(overrides)
    return payload


def _act_errors(campaign: Path) -> list[dict]:
    findings = check_state.check_campaign(campaign, scope="full")["findings"]
    return [item for item in findings if item["severity"] == "error" and ("act_" in item["rule"] or "arc_" in item["rule"])]


def test_commit_act_archives_the_act_and_opens_its_successor(campaign: Path) -> None:
    _write(campaign, "threads.md", THREADS)
    assert _act_errors(campaign) == []

    result = rpg_state.commit_act(campaign, _act_payload())

    assert result["ok"] and result["operation"] == "commit-act" and result["continuity_revision"] == 1
    assert result["checkpoint_committed"] is True
    threads = _read(campaign, "threads.md")
    compass = threads.split("## Arc Compass", 1)[1].split("## Act Archive", 1)[0]
    archive = threads.split("## Act Archive", 1)[1].split("## Active Threads", 1)[0]
    assert compass.startswith("\n\nThe single current-act owner.\n\n- Act id: act-2\n")
    for line in (
        "- Act status: active",
        "- Previous act id: act-1",
        "- Opened at revision: 1",
        "- Dramatic question: What is in the courier's crates?",
        "- Closure conditions: Mira opens the crates; the crates leave the city",
        "- Setups awaiting payoff: the clerk's ledger",
        "- Places this act can reach: the warehouse; the customs house",
    ):
        assert line in compass
    assert "### act-1\n\n- Act id: act-1\n- Act status: closed\n" in archive
    for line in (
        "- Closing action: Mira caught the courier on the gangway.",
        "- Condition met or foreclosed: met",
        "- Recorded at revision: 1",
        "- Places this act can reach: the old dock",
    ):
        assert line in archive
    assert "- Courier promise: absent" in threads and "As of revision: 1" in threads
    assert _act_errors(campaign) == []
    assert '  open_choices:\n    - "Open the crates"\n' in _read(campaign, "current_state.yaml")
    assert "### Durable Revision 1" in _read(campaign, "session_log.md")
    assert rpg_state.commit_act(campaign, _act_payload())["idempotent"] is True


def test_commit_act_keeps_a_closure_recorded_by_the_decisive_turn(campaign: Path) -> None:
    closed = THREADS.replace("- Act status: active", "- Act status: closed").replace(
        "- Closing action:\n- Condition met or foreclosed:\n- Recorded at revision:",
        "- Closing action: the ship sailed without Mira\n- Condition met or foreclosed: foreclosed\n- Recorded at revision: 0",
    )
    _write(campaign, "threads.md", closed)
    rpg_state.commit_act(campaign, _act_payload())
    archive = _read(campaign, "threads.md").split("## Act Archive", 1)[1]
    assert "- Closing action: the ship sailed without Mira" in archive and "- Recorded at revision: 0" in archive
    assert _act_errors(campaign) == []


def test_commit_act_refuses_a_close_id_that_is_not_the_current_act(campaign: Path) -> None:
    _write(campaign, "threads.md", THREADS)
    payload = _act_payload()
    payload["close"]["act_id"] = "act-9"
    with pytest.raises(rpg_state.RPGStateError, match="holds act act-1"):
        rpg_state.commit_act(campaign, payload)
    assert _read(campaign, "threads.md") == THREADS


def test_commit_act_needs_an_adopted_act_id(campaign: Path) -> None:
    with pytest.raises(rpg_state.RPGStateError, match="no Act id"):
        rpg_state.commit_act(campaign, _act_payload())


def test_commit_act_never_reuses_an_archived_id(campaign: Path) -> None:
    _write(campaign, "threads.md", THREADS)
    rpg_state.commit_act(campaign, _act_payload())
    payload = _act_payload("act-3", 1)
    payload["close"]["act_id"] = "act-2"
    payload["open"]["act_id"] = "act-1"
    with pytest.raises(rpg_state.RPGStateError, match="already archived"):
        rpg_state.commit_act(campaign, payload)


def test_commit_act_carries_a_cast_handoff_and_owns_threads(campaign: Path) -> None:
    _write(campaign, "threads.md", THREADS)
    payload = _act_payload()
    payload["checkpoint"]["active_cast_handoff"] = "The witness leaves the dock."
    payload["mutations"] = [{"path": "threads.md", "ops": [{"op": "append", "text": "x"}]}]
    payload["changes"] = [{"id": "t", "kind": "thread_update", "established_delta": "x", "owners": ["threads.md"]}]
    with pytest.raises(rpg_state.RPGStateError, match="writes threads.md itself"):
        rpg_state.commit_act(campaign, payload)
    assert _read(campaign, "threads.md") == THREADS

    del payload["changes"]
    payload["mutations"] = [{"path": "active_cast.md", "ops": [{"op": "delete_row", "key": "Witness"}]}]
    result = rpg_state.commit_act(campaign, payload)
    assert result["ok"] and "Witness" not in _read(campaign, "active_cast.md")
    assert _act_errors(campaign) == []


def test_commit_act_runs_from_the_cli(campaign: Path, capsysbinary) -> None:
    _write(campaign, "threads.md", THREADS)
    code = rpg_state.main([str(campaign), "commit-act", "--input-json", json.dumps(_act_payload())])
    out = json.loads(capsysbinary.readouterr().out.decode("utf-8"))
    assert code == 0 and out["operation"] == "commit-act" and out["next_expected_revision"] == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("scope", {"places": "the lighthouse", "people": "the keeper", "in_motion": "a storm", "if_ignored": "it wrecks"}),
        ("closure_conditions", ["the lamp is lit"]),
        ("prepared_expectations", ["the keeper's log"]),
    ],
)
def test_a_commit_act_retry_with_a_changed_act_is_a_conflict(campaign: Path, field: str, value: object) -> None:
    _write(campaign, "threads.md", THREADS)
    rpg_state.commit_act(campaign, _act_payload())
    committed = _read(campaign, "threads.md")
    payload = _act_payload()
    payload["open"][field] = value
    with pytest.raises(rpg_state.RPGStateError) as caught:
        rpg_state.commit_act(campaign, payload)
    assert caught.value.category == "operation_conflict"
    assert _read(campaign, "threads.md") == committed


def test_new_note_advisory_uses_the_campaign_stat_scale(campaign: Path) -> None:
    """A 0-20 campaign gets no 1-5 range warning that the full check would not give."""

    profile = _read(campaign, "play_profile.yaml")
    _write(campaign, "play_profile.yaml", profile + "mechanics:\n  resolution_grounding: numeric\n")
    note = "# Branak\n\nTier: T2\n\n## Stats (Numeric Grounding Only)\n\n- Güç: 9\n"

    def out_of_range() -> bool:
        findings = rpg_state._note_findings(campaign, "characters/branak.md", note)
        return any("mechanic_stat_out_of_range" in item["message"] for item in findings)

    assert out_of_range(), "without a declared scale the 1-5 default applies"
    rules = (campaign / "rules.md").read_text(encoding="utf-8") if (campaign / "rules.md").is_file() else "# Rules\n"
    _write(campaign, "rules.md", rules + "\n- Numeric scale: 0-20\n")
    assert not out_of_range()


@pytest.mark.parametrize(
    "line",
    ["18-23. günler: rıhtım tahkim edildi.", "18–23. günlerde rıhtım tahkim edildi.", "- Days 18-23: the quay was fortified."],
)
def test_a_day_range_dates_its_now_entry_by_the_first_day(line: str) -> None:
    match = owner_ops.DATED_START_RE.match(line)
    assert match is not None and int(next(day for day in match.groups() if day)) == 18


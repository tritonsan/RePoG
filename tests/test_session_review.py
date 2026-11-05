"""The session review tools (dev/session_review), on synthetic transcripts only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

REVIEW = Path(__file__).resolve().parents[1] / "dev" / "session_review"
if str(REVIEW) not in sys.path:
    sys.path.insert(0, str(REVIEW))

import build_page  # noqa: E402
import compare  # noqa: E402
import extract  # noqa: E402

LAUNCHER = 'sh "${CLAUDE_PLUGIN_ROOT}/scripts/repog.sh"'
NARRATION = "Liman sisli. Halatlar gıcırdıyor, martılar suskun; iskelede kimse yok ve fener sönük kalıyor. " * 4
ENGLISH = "The dock is quiet. Ropes creak, gulls keep still; nobody waits on the pier and the lamp stays dark. " * 3


# ------------------------------------------------------------ transcript rows


def prompt(time: str, text: str, uuid: str | None = None) -> dict:
    return {"type": "user", "timestamp": time, "uuid": uuid, "message": {"role": "user", "content": text}}


def say(time: str, text: str, mid: str, tokens: int = 10) -> dict:
    return {
        "type": "assistant",
        "timestamp": time,
        "message": {"id": mid, "content": [{"type": "text", "text": text}], "usage": {"output_tokens": tokens}},
    }


def bash(time: str, command: str, tool_id: str, mid: str, tokens: int = 10) -> dict:
    block = {"type": "tool_use", "id": tool_id, "name": "Bash", "input": {"command": command, "description": "run"}}
    return {"type": "assistant", "timestamp": time, "message": {"id": mid, "content": [block], "usage": {"output_tokens": tokens}}}


def result(time: str, tool_id: str, text: str, error: bool = False) -> dict:
    block = {"type": "tool_result", "tool_use_id": tool_id, "content": text, "is_error": error}
    return {"type": "user", "timestamp": time, "message": {"role": "user", "content": [block]}}


def compaction(time: str, opener: str | None = None) -> dict:
    metadata: dict = {"trigger": "auto"}
    if opener:
        metadata["runningTurnSends"] = {"openerUuid": opener}
    return {"type": "system", "subtype": "compact_boundary", "timestamp": time, "compactMetadata": metadata}


def lines(rows: list[dict]) -> list[str]:
    return [json.dumps(row, ensure_ascii=False) for row in rows]


def split(rows: list[dict], since=None) -> list[dict]:
    return extract.split(lines(rows), since)[0]


def commit(kind: str = "durable") -> str:
    return f"{LAUNCHER} rpg_state campaign commit-{kind} --input-file - <<'EOF'\n{{\"operation_id\": \"t\"}}\nEOF"


# ------------------------------------------------------------------- helpers


def test_every_helper_in_a_chained_command_counts_once() -> None:
    command = (
        'R="${CLAUDE_PLUGIN_ROOT}/scripts/repog.sh"; sh "$R" roll_dice --campaign campaign call --input-file - <<EOF\n'
        '{"stakes": "sh repog.sh odds campaign"}\nEOF\n'
        'sh "$R" rpg_state campaign commit-durable --input-file p.json && sh ${R} rpg_state campaign commit-distill --input-file d.json'
    )
    assert extract.command_helpers(command) == ["roll_dice call", "rpg_state commit-durable", "rpg_state commit-distill"]


def test_python_calls_count_and_source_reads_do_not() -> None:
    command = (
        r'python -B "D:\Games\My Plugin\tools\rpg_state.py" campaign commit-checkpoint --input-file - '
        "&& py -3 tools/check_state.py campaign --scope full 2>&1 | head"
    )
    assert extract.command_helpers(command) == ["rpg_state commit-checkpoint", "check_state"]
    reads = 'cat "${CLAUDE_PLUGIN_ROOT}/tools/resolve_mechanic.py" | head -50; grep -n roll tools/rpg_state.py'
    assert extract.command_helpers(reads) == []
    assert extract.command_helpers(f"{LAUNCHER} presentation_lint report campaign > out.json") == ["presentation_lint report"]


def test_powershell_launchers_python_options_and_quoted_heredocs_count() -> None:
    powershell = '$R = "$env:CLAUDE_PLUGIN_ROOT/scripts/repog.sh"; sh $R rpg_state campaign commit-durable --input-file p.json'
    assert extract.command_helpers(powershell) == ["rpg_state commit-durable"]
    assert extract.command_helpers('$R="$env:CLAUDE_PLUGIN_ROOT/scripts/repog.sh"; & $R check_state campaign') == ["check_state"]
    utf8 = "python -X utf8 tools/rpg_state.py campaign commit-durable --input-file p.json"
    assert extract.command_helpers(utf8) == ["rpg_state commit-durable"]
    assert extract.command_helpers("python3.10 -W ignore -B tools/check_state.py campaign --scope full") == ["check_state"]
    # A backslash-quoted heredoc is a payload too: the helper named inside it is no call.
    quoted = f'{LAUNCHER} rpg_state campaign commit-durable --input-file - <<\\EOF\n{{"note": "sh repog.sh check_state campaign"}}\nEOF'
    assert extract.command_helpers(quoted) == ["rpg_state commit-durable"]


def test_a_quoted_campaign_path_with_spaces_keeps_the_subcommand() -> None:
    command = f"{LAUNCHER} rpg_state \"D:/Games/my repog play/campaign\" commit-durable --input-file - <<'JSON'\n{{}}\nJSON"
    assert extract.command_helpers(command) == ["rpg_state commit-durable"]
    inline = f"{LAUNCHER} rpg_state 'D:/table top games/campaign' commit-distill --input-json '{{\"note\": \"a b\"}}'"
    assert extract.command_helpers(inline) == ["rpg_state commit-distill"]
    rows = [
        prompt("2026-11-04T10:00:00Z", "Go."),
        bash("2026-11-04T10:00:01Z", command, "c1", "m1"),
        result("2026-11-04T10:00:02Z", "c1", '{"ok": false, "failure_category": "stale_revision"}'),
    ]
    turn = split(rows)[0]
    assert (turn["commit_calls"], turn["commit_failures"], turn["order"]) == (1, 1, "commit_no_long_text")


def test_a_commit_past_the_first_300_characters_sets_the_order() -> None:
    long_commit = "PAYLOAD=" + "x" * 400 + "; " + commit()
    rows = [
        prompt("2026-11-04T10:00:00Z", "I walk to the pier."),
        bash("2026-11-04T10:00:05Z", long_commit, "c1", "m1"),
        result("2026-11-04T10:00:06Z", "c1", '{"ok": true, "operation": "commit-durable"}'),
        say("2026-11-04T10:00:20Z", NARRATION, "m2"),
        prompt("2026-11-04T10:01:00Z", "I wait."),
        say("2026-11-04T10:01:10Z", NARRATION, "m3"),
        bash("2026-11-04T10:01:12Z", commit(), "c2", "m4"),
        result("2026-11-04T10:01:13Z", "c2", '{"ok": true}'),
    ]
    first, second = split(rows)
    assert first["helpers"] == ["rpg_state commit-durable"] and first["order"] == "commit_first"
    assert second["order"] == "narrate_first"
    assert second["narration_wait_s"] == 10.0 and second["wait_s"] == 12.0


def test_usage_counts_once_per_message_id() -> None:
    rows = [
        prompt("2026-11-04T10:00:00Z", "Hello."),
        say("2026-11-04T10:00:01Z", "a", "m1", tokens=100),
        bash("2026-11-04T10:00:02Z", "ls", "t1", "m1", tokens=100),
        bash("2026-11-04T10:00:03Z", "ls", "t2", "m1", tokens=100),
        say("2026-11-04T10:00:04Z", "b", "m2", tokens=40),
        {"type": "assistant", "timestamp": "2026-11-04T10:00:05Z", "message": {"content": [], "usage": {"output_tokens": 5}}},
    ]
    turn = split(rows)[0]
    assert turn["out_tokens"] == 145
    assert sum(turn["efforts"].values()) == 3


def test_thinking_counts_once_per_message_and_a_repeated_row_once() -> None:
    first = dict(say("2026-11-04T10:00:01Z", "a", "m1", tokens=50), thinkingDurationMs=300, uuid="u1")
    second = dict(bash("2026-11-04T10:00:02Z", commit(), "c1", "m1", tokens=80), thinkingDurationMs=300, uuid="u2")
    rows = [
        prompt("2026-11-04T10:00:00Z", "Go.", uuid="p1"),
        first,
        second,
        second,
        prompt("2026-11-04T10:00:00Z", "Go.", uuid="p1"),
        result("2026-11-04T10:00:03Z", "c1", '{"ok": true}'),
        dict(say("2026-11-04T10:00:04Z", "b", "m2", tokens=10), thinkingDurationMs=200),
    ]
    turns = split(rows)
    assert len(turns) == 1
    turn = turns[0]
    assert (turn["out_tokens"], turn["thinking_ms"]) == (90, 500)
    assert turn["helpers"] == ["rpg_state commit-durable"] and turn["commit_calls"] == 1


# ---------------------------------------------------------------- compaction


def test_compaction_attaches_to_the_turn_it_interrupted() -> None:
    rows = [
        prompt("2026-11-04T10:00:00Z", "One.", uuid="p1"),
        say("2026-11-04T10:00:05Z", "a", "m1"),
        prompt("2026-11-04T10:01:00Z", "Two.", uuid="p2"),
        compaction("2026-11-04T10:01:30Z"),
        say("2026-11-04T10:02:00Z", "b", "m2"),
        compaction("2026-11-04T10:02:30Z"),
        say("2026-11-04T10:03:00Z", "c", "m3"),
        prompt("2026-11-04T10:04:00Z", "Three.", uuid="p3"),
        say("2026-11-04T10:04:05Z", "d", "m4"),
    ]
    one, two, three = split(rows)
    assert not one["compaction_before"] and not three["compaction_before"]
    assert two["compaction"] == "before_reply" and two["compaction_before"]
    assert [e[0] for e in two["events"]].count("compaction") == 2

    mid = split(rows[:2] + [compaction("2026-11-04T10:00:30Z")])[0]
    assert mid["compaction"] == "mid_turn"


def test_compaction_follows_the_running_turn_opener() -> None:
    rows = [
        compaction("2026-11-04T09:59:00Z"),
        prompt("2026-11-04T10:00:00Z", "One.", uuid="p1"),
        say("2026-11-04T10:00:05Z", "a", "m1"),
        compaction("2026-11-04T10:00:50Z", opener="p2"),
        prompt("2026-11-04T10:01:00Z", "Two.", uuid="p2"),
        say("2026-11-04T10:01:05Z", "b", "m2"),
    ]
    one, two = split(rows)
    assert one["compaction"] == "before_reply"
    assert two["compaction"] == "before_reply"

    late = split(rows[1:4] + [compaction("2026-11-04T10:01:30Z", opener="p1")])
    assert late[0]["compaction"] == "mid_turn"


# ------------------------------------------------------------- call results


def test_failed_commits_need_an_error_or_a_top_level_ok_false() -> None:
    nested = json.dumps({"ok": True, "operation": "commit-durable", "full_check": {"ok": False}}, indent=2)
    rows = [
        prompt("2026-11-04T10:00:00Z", "Go."),
        bash("2026-11-04T10:00:01Z", commit(), "c1", "m1"),
        result("2026-11-04T10:00:02Z", "c1", "Exit code 1\n{\"ok\": false, \"failure_category\": \"stale_revision\"}", error=True),
        bash("2026-11-04T10:00:03Z", commit(), "c2", "m2"),
        result("2026-11-04T10:00:04Z", "c2", '{"ok": false, "failure_category": "input_invalid"}'),
        bash("2026-11-04T10:00:05Z", commit(), "c3", "m3"),
        result("2026-11-04T10:00:06Z", "c3", nested),
        bash("2026-11-04T10:00:07Z", f"{LAUNCHER} scene_capsule show campaign", "c4", "m4"),
        result("2026-11-04T10:00:08Z", "c4", "oops", error=True),
    ]
    turn = split(rows)[0]
    assert (turn["commit_calls"], turn["commit_failures"]) == (3, 2)
    assert turn["failed_calls"] == ["rpg_state commit-durable", "rpg_state commit-durable", "scene_capsule show"]


def test_each_commit_is_judged_by_its_own_result() -> None:
    distilled = distill_result([], [])
    check_failed = json.dumps({"ok": False, "error_count": 1, "findings": []}, indent=2)
    chained = f"{commit('distill')}\n{LAUNCHER} check_state campaign --scope full"
    both = f"{LAUNCHER} rpg_state campaign commit-durable --input-file a.json; {LAUNCHER} rpg_state campaign commit-distill --input-file b.json"
    rows = [
        prompt("2026-11-04T10:00:00Z", "Go."),
        bash("2026-11-04T10:00:01Z", chained, "c1", "m1"),
        result("2026-11-04T10:00:02Z", "c1", f"Exit code 2\n{distilled}\n{check_failed}", error=True),
        bash("2026-11-04T10:00:03Z", both, "c2", "m2"),
        result(
            "2026-11-04T10:00:04Z",
            "c2",
            '{"ok": true, "operation": "commit-durable"}\n{"ok": false, "failure_category": "distill_unreconciled"}',
            error=True,
        ),
    ]
    turn = split(rows)[0]
    assert (turn["commit_calls"], turn["commit_failures"]) == (3, 1)
    assert turn["failed_calls"] == ["rpg_state commit-distill + check_state", "rpg_state commit-durable + rpg_state commit-distill"]
    assert [d["ok"] for d in turn["distills"]] == [True, False]


def distill_result(changed: list[str], rules: list[str], severity: str = "warning", **extra) -> str:
    findings = [{"severity": severity, "rule": rule, "message": "m", "path": "active_cast.md"} for rule in rules]
    document = {
        "ok": True,
        "operation": "commit-distill",
        "idempotent": False,
        "changed_files": ["current_state.yaml", "session_log.md", *changed],
        "full_check": {"ok": True, "findings": findings},
        **extra,
    }
    return json.dumps(document, indent=2)


def test_distill_results_record_changes_and_stale_findings() -> None:
    outputs = [
        distill_result([], ["active_cast_stale"]),
        distill_result(["archive/session_log_through_r4.md"], ["cast_dead_listed", "power_band_mismatch"]),
        distill_result(["active_cast.md"], ["active_cast_stale"]),
        distill_result([], ["cast_dead_listed"], curation_due=[{"path": "active_cast.md", "rule": "cast_dead_listed"}]),
        '{"ok": false, "failure_category": "distill_unreconciled"}',
        distill_result([], ["active_cast_stale"], severity="info"),  # 0.4.0 revision lag is info
    ]
    rows = [prompt("2026-11-04T10:00:00Z", "Go.")]
    for n, text in enumerate(outputs):
        rows += [bash("2026-11-04T10:00:01Z", commit("distill"), f"d{n}", f"m{n}"), result("2026-11-04T10:00:02Z", f"d{n}", text)]
    summaries = split(rows)[0]["distills"]
    assert [(d["ok"], d["changed_records"], d["stale_rules"]) for d in summaries] == [
        (True, 0, ["active_cast_stale"]),
        (True, 0, ["cast_dead_listed"]),
        (True, 1, ["active_cast_stale"]),
        (True, 0, []),
        (False, 0, []),
        (True, 0, []),
    ]


# ---------------------------------------------------------------- --since


def test_since_keeps_later_turns_with_their_numbers(tmp_path: Path) -> None:
    rows = [
        prompt("2026-11-03T22:00:00Z", "Old turn."),
        compaction("2026-11-03T22:00:10Z"),
        say("2026-11-03T22:00:20Z", NARRATION, "m1"),
        prompt("2026-11-04T10:00:00Z", "New turn."),
        say("2026-11-04T10:00:20Z", NARRATION, "m2"),
    ]
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("\n".join(lines(rows)) + "\n", encoding="utf-8")
    out = tmp_path / "work"
    extract.main([str(transcript), str(out), "--since", "2026-11-04"])

    turns = [json.loads(line) for line in (out / "turns.jsonl").read_text(encoding="utf-8").splitlines()]
    quant = json.loads((out / "quant.json").read_text(encoding="utf-8"))
    assert [t["idx"] for t in turns] == [2]
    assert quant["since"] == "2026-11-04T00:00:00+00:00" and quant["compactions"] == []
    assert (out / "segments" / "seg_01.md").read_text(encoding="utf-8").startswith("### T2 ")
    with pytest.raises(argparse.ArgumentTypeError):
        extract.parse_since("yesterday")
    assert extract.parse_since("2026-11-04T13:00:00+03:00") == extract.parse_since("2026-11-04T10:00:00Z")


# ------------------------------------------------------------------- compare


def play_rows() -> list[dict]:
    """Four play turns: narrated first, committed first with a status line, OOC, and English."""

    return [
        prompt("2026-11-04T10:00:00Z", "Kapıyı itip içeri giriyorum ve masadaki mektubu alıyorum."),
        say("2026-11-04T10:00:15Z", "Kapıyı itiyorsun ve içeri giriyorsun; mektup masada. " + NARRATION, "a1"),
        bash("2026-11-04T10:00:20Z", commit(), "c1", "a2"),
        result("2026-11-04T10:00:21Z", "c1", '{"ok": true}'),
        prompt("2026-11-04T10:01:00Z", "Pencereden limana bakıyorum."),
        bash("2026-11-04T10:01:10Z", commit(), "c2", "b1"),
        result("2026-11-04T10:01:11Z", "c2", '{"ok": false, "failure_category": "stale_revision"}'),
        bash("2026-11-04T10:01:12Z", commit("distill"), "c3", "b2"),
        result("2026-11-04T10:01:13Z", "c3", distill_result([], ["relationship_map_stale"])),
        say("2026-11-04T10:01:40Z", "Kayıtlar tamam, şimdi sahneye dönüyorum.", "b3"),
        say("2026-11-04T10:01:41Z", "Bir an durup " + NARRATION, "b4"),
        prompt("2026-11-04T10:02:00Z", "OOC: kayıt neden başarısız oldu?"),
        say("2026-11-04T10:02:05Z", "commit-durable stale_revision döndü; revision 12 bekleniyordu.", "c1"),
        prompt("2026-11-04T10:03:00Z", "I push the heavy door open and step inside."),
        say("2026-11-04T10:03:30Z", ENGLISH, "d1"),
        bash("2026-11-04T10:03:31Z", commit(), "c4", "d2"),
        result("2026-11-04T10:03:32Z", "c4", '{"ok": true}'),
    ]


PROFILE = """mechanics:
  resolution:
    die: 2d6
    stat_min: 1
    stat_max: 5
    difficulty_min: 4
    difficulty_max: 13
    bands:
      - {at_least: 2, band: clean}
      - {at_least: -1, band: cost}
      - {at_least: -4, band: partial}
      - {at_least: -99, band: failure}
"""


def make_work(
    tmp_path: Path, name: str, rows: list[dict], *, check=None, rolls=None, lint=None, interventions=None, profile=None
) -> Path:
    transcript = tmp_path / f"{name}.jsonl"
    transcript.write_text("\n".join(lines(rows)) + "\n", encoding="utf-8")
    work = tmp_path / name
    extract.main([str(transcript), str(work), "--since", "2026-11-04T09:00:00Z"])
    runtime = work / compare.RUNTIME
    runtime.mkdir(parents=True)
    if profile is not None:
        (work / compare.CAMPAIGN / "play_profile.yaml").write_text(profile, encoding="utf-8")
    for file_name, records in (("rolls.jsonl", rolls), ("lint_history.jsonl", lint)):
        if records is not None:
            (runtime / file_name).write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    if check is not None:
        (work / "check_full.json").write_text(json.dumps(check), encoding="utf-8")
    if interventions is not None:
        (work / "interventions.json").write_text(json.dumps(interventions), encoding="utf-8")
    return work


def receipt(roll_id: str, at: str = "2026-11-04T10:00:10Z", **fields) -> dict:
    return {"roll_id": roll_id, "revision": 3, "die": "2d6", "at": at, **fields}


def test_compare_measures_every_metric(tmp_path: Path) -> None:
    # PROFILE: clean and cost are the success bands (a worst margin below -1 is
    # bad); failure is reached by a worst margin below -4.
    rolls = [
        receipt("r1", p_below_success=0.25, dice=[4, 4], margin=2),  # worst margin -4: partial, not failure
        receipt("r2", p_below_success=0.4, reachable_bands=["clean", "cost", "partial", "failure"]),
        receipt("r3", dice=[1, 2], margin=0),  # worst margin -1 is still cost: no bad band
        receipt("r4", dice=[6, 5], margin=3),  # worst margin -6: failure was reachable
        receipt("r5", auto=True, certain=True),
        receipt("r6", die="3d6kh2", dice=[1, 2, 3], margin=0),  # unknown shape
        {"kind": "reread", "reread_of": "r1", "new_band": "failure", "at": "2026-11-04T10:00:30Z"},
        receipt("old", at="2026-10-01T10:00:00Z", p_below_success=0.5),
    ]
    lint = [
        {"at": f"2026-11-04T10:0{n}:30Z", "prompt_uuid": f"p{n}", "counts": {"pc_authoring": 1 if n == 1 else 0}}
        for n in range(4)
    ]
    lint.append({"at": "2026-11-04T10:03:40Z", "prompt_uuid": "p2", "counts": {"pc_line_rewritten": 1}})  # p2 ended twice
    check = {
        "warning_count": 2,
        "findings": [
            {
                "severity": "warning",
                "rule": "records_language_mismatch",
                "message": "2 record file(s) read as another language",
                "paths": ["C:/game/campaign/characters/ilse.md", "C:/game/campaign/places/dock.md"],
            },
            {"severity": "warning", "rule": "now_overflow", "message": "Now is long"},
            {"severity": "info", "rule": "location_unmapped", "message": "Unmapped (acknowledged by D-003)"},
            {
                "severity": "info",
                "rule": "records_language_mismatch",
                "message": "Record file(s) in another language: characters/old.md (acknowledged by D-004)",
            },
        ],
    }
    interventions = [
        {"turn": 3, "likely_cause": "model_error"},
        {"turn": 1, "likely_cause": "player_preference"},
        {"turn": 99, "likely_cause": "model_error"},
    ]
    work = make_work(
        tmp_path, "g3", play_rows(), check=check, rolls=rolls, lint=lint, interventions=interventions, profile=PROFILE
    )

    cells = compare.measure(work)
    text = {key: cell.text for key, cell in cells.items()}
    assert text["narrated_first"] == "2/3 (67%)"
    assert cells["status_lines"].value == 1
    assert text["narration_wait"] == "30 s"
    assert text["bad_band_rolls"] == "3/4 (75%), worst band 2/4, 1 unknown, 1 auto"
    assert text["empty_distills"] == "1/1"
    assert text["standing_warnings"] == "2 (2 acknowledged)"
    assert text["bir_an_restating"] == "25% of 4 / 33% of 3"
    assert text["pc_authoring"] == "100% late, 50% of 4"
    assert text["model_interventions"] == "1"
    assert text["failed_commits"] == "1/4 (25%)"
    assert text["records_language"] == "2 files (1 acknowledged)"


def test_compare_prints_a_table_with_the_last_dir_judged(tmp_path: Path, capsys) -> None:
    good = [
        prompt("2026-11-04T10:00:00Z", "Pencereden limana bakıyorum."),
        say("2026-11-04T10:00:12Z", NARRATION, "a1"),
        bash("2026-11-04T10:00:20Z", commit(), "c1", "a2"),
        result("2026-11-04T10:00:21Z", "c1", '{"ok": true}'),
    ]
    old = make_work(tmp_path, "g2", play_rows())
    new = make_work(tmp_path, "g3", good, check={"warning_count": 0, "findings": []}, rolls=[receipt("r1", p_below_success=0.3)])
    capsys.readouterr()  # drop extract's own summary

    compare.main([str(old), str(new), "--labels", "G2", "G3"])
    table = capsys.readouterr().out
    assert table.splitlines()[0] == "| Metric | G2 | G3 | Target | Met (G3) |"
    assert "| Committed turns narrated first | 2/3 (67%) | 1/1 (100%) | 90%+ | yes |" in table
    assert "| Rolls with a reachable bad band | n/a | 1/1 (100%) | every roll made | yes |" in table
    assert "| Model-error interventions | n/a (OOC play turns: 1) | n/a (OOC play turns: 0) | under 10 | n/a |" in table

    compare.main([str(new), "--json"])
    data = json.loads(capsys.readouterr().out)
    values = {m["key"]: m["values"][0] for m in data["metrics"]}
    assert values["status_lines"] == {"text": "0", "value": 0, "met": True}
    assert values["pc_authoring"]["met"] is None


def test_status_lines_skip_ooc_dialogue_and_narration() -> None:
    turn = {
        "texts": [
            "Kayıtlar tamam.\n(OOC: kayıt başarısız, revision 4 bekleniyordu.)\n“Kaydettim,” diyor kâtip.\n"
            "Now the distill.\nThe old distillery smokes over the harbor.",
            NARRATION + " threads.md",
        ]
    }
    assert compare.status_lines(turn) == ["Kayıtlar tamam.", "Now the distill."]


def test_status_lines_leave_fiction_about_records_and_quoted_speech() -> None:
    fiction = [
        "The harbourmaster is writing the records by lamplight, slow and careful.",
        "Kâtip başını kaldırıyor: “Adını deftere kaydettim, kaptan.”",
        "Deniz Kuvvetleri'nin kayıtları güncel değil; ödül posteri hâlâ eski yüzünü gösteriyor.",
        "The clerk saved the records from the fire before the roof fell.",
        "Kayıtlar tamamen yanmış; geriye kül kalmış.",
        'The quartermaster mutters, "I\'m updating the records, leave me be."',
        # First-person narration announces record work just as a GM would.
        "I will write the records tomorrow, I promise myself.",
        "Committing the scene to memory, I turn away from the window.",
        "Planında küçük bir revizyon yaptı; the Marines keep state files on him.",
        "_Sessiz._ Rüzgâr _dindi_ ve fener söndü.",
    ]
    assert compare.status_lines({"texts": ["\n".join(fiction)]}) == []
    backend = [
        "Saving the turn to threads.md now.",
        "Running rpg_state commit-durable before we go on.",
        "The commit came back stale_revision; trying again.",
        "“Tamam.” Kayıtlar tamam, sahneye dönüyorum.",
    ]
    assert compare.status_lines({"texts": ["\n".join(backend)]}) == backend


def test_committed_turns_without_narration_count_as_not_narrated_first(tmp_path: Path) -> None:
    rows = [
        prompt("2026-11-04T10:00:00Z", "Bekliyorum."),
        bash("2026-11-04T10:00:05Z", commit(), "c1", "a1"),
        result("2026-11-04T10:00:06Z", "c1", '{"ok": true}'),
        say("2026-11-04T10:00:07Z", "Rüzgâr dindi.", "a2"),
        prompt("2026-11-04T10:01:00Z", "Yürüyorum."),
        say("2026-11-04T10:01:10Z", NARRATION, "b1"),
        bash("2026-11-04T10:01:12Z", commit(), "c2", "b2"),
        result("2026-11-04T10:01:13Z", "c2", '{"ok": true}'),
    ]
    cell = compare.measure(make_work(tmp_path, "g3", rows))["narrated_first"]
    assert (cell.text, cell.value) == ("1/2 (50%), 1 without narration", 0.5)


def test_a_partly_acknowledged_language_warning_still_stands(tmp_path: Path) -> None:
    check = {
        "warning_count": 1,
        "findings": [
            {
                "severity": "warning",
                "rule": "records_language_mismatch",
                "message": (
                    "1 record file(s) read as another language than the records language 'tr': "
                    "characters/ilse.md (en). Rewrite their content in 'tr'. 2 more acknowledged by D-002."
                ),
                "paths": ["C:/game/campaign/characters/ilse.md"],
            },
            {
                "severity": "info",
                "rule": "power_band_mismatch",
                "message": "Branak: Power Band 2 is lower than its highest stat (acknowledged by D-001)",
                "acknowledged_by": "D-001",
            },
        ],
    }
    cells = compare.measure(make_work(tmp_path, "g3", play_rows(), check=check))
    # The warning names acknowledged files, yet it still stands: only info findings are acknowledged.
    assert (cells["standing_warnings"].text, cells["standing_warnings"].value) == ("1 (1 acknowledged)", 1)
    assert (cells["records_language"].text, cells["records_language"].value) == ("1 files (2 acknowledged)", 1)


def test_restating_needs_shared_stems_and_the_second_person() -> None:
    asked = "Kapıyı itip içeri giriyorum ve mektubu alıyorum."
    assert compare.restates(asked, "Kapıyı itiyorsun, içeri giriyorsun. " + NARRATION)
    assert not compare.restates(asked, "Kapı gıcırdıyor; içerisi karanlık. " + NARRATION)
    assert not compare.restates(asked, "Liman sisli ve sessiz. Kapıyı itiyorsun.")
    assert compare.restates("I push the heavy door open.", "You push the heavy door open. " + ENGLISH)
    assert not compare.restates("I push the heavy door open.", ENGLISH)


def test_restating_reads_the_second_person_as_the_lint_does() -> None:
    # Third-person imperatives (olsun, gelsin) and genitives (kurdun) are no address.
    assert not compare.restates("Kurdun izlerini takip ediyorum.", "Kurdun izleri dereye iniyor ve orada kayboluyor.")
    assert not compare.restates(
        "Fenerin ışığına bakıyorum, kim gelirse.", "Fenerin ışığı kapıya vuruyor; kim gelirse gelsin."
    )
    assert not compare.restates(
        "Kaptanın kamarasına girip haritaya bakıyorum.", "Kaptanın kamarası boş, harita masada duruyor olsun ya da olmasın."
    )
    assert compare.restates("Kurdun izlerini takip ediyorum.", "Kurdun izlerini takip ediyorsun; dere boyunca iniyorlar.")
    assert compare.second_person_rules()[1], "the tr and en packs define second_person_patterns"
    assert compare.BIR_AN_RE.search(compare.tr_lower("BİR AN durdu."))
    assert not compare.BIR_AN_RE.search("bir anda döndü ve bir anlığına baktı")


def test_old_receipts_use_their_dice_and_unknown_shapes_stay_unknown() -> None:
    assert compare.bad_band_reachable(receipt("a", dice=[1, 1], margin=0)) is False
    assert compare.bad_band_reachable(receipt("b", dice=[5, 5], margin=1)) is True
    assert compare.bad_band_reachable({"roll_id": "c", "die": "3d6kh2", "dice": [1, 2, 3], "margin": 0}) is None
    assert compare.bad_band_reachable(receipt("d", p_below_success=0, dice=[1, 1], margin=-5)) is False


def test_receipts_are_read_against_the_campaign_bands(tmp_path: Path) -> None:
    work = make_work(tmp_path, "g2", play_rows(), profile=PROFILE)
    bands = compare.campaign_bands(work)
    assert [band["band"] for band in bands] == ["clean", "cost", "partial", "failure"]

    worst_minus_one = receipt("a", dice=[1, 2], margin=0)
    assert compare.bad_band_reachable(worst_minus_one) is True  # default bands: below 0 fails
    assert compare.bad_band_reachable(worst_minus_one, bands) is False  # here -1 lands in cost, a success
    assert compare.worst_band_reachable(receipt("b", dice=[4, 4], margin=2), bands) is False  # -4 is partial
    assert compare.worst_band_reachable(receipt("c", dice=[6, 5], margin=3), bands) is True
    assert compare.worst_band_reachable(receipt("d", reachable_bands=["clean", "cost"]), bands) is False
    one_band = [{"at_least": 0, "band": "done"}]
    assert compare.bad_band_reachable(receipt("e", dice=[1, 1], margin=-9), one_band) is False
    assert compare.worst_band_reachable(receipt("e", dice=[1, 1], margin=-9), one_band) is False

    assert compare.campaign_bands(tmp_path / "missing") == list(compare.DEFAULT_BANDS)
    (work / compare.CAMPAIGN / "play_profile.yaml").write_text("mechanics:\n  resolution:\n    die: zz\n", encoding="utf-8")
    assert compare.campaign_bands(work) == list(compare.DEFAULT_BANDS)


def test_build_page_reads_the_new_turn_records(tmp_path: Path) -> None:
    work = make_work(tmp_path, "g3", play_rows(), rolls=[receipt("r1", band="clean_success"), {"kind": "reread", "reread_of": "r1"}])
    args = argparse.Namespace(
        work=str(work), runtime=str(work / compare.RUNTIME), check=None, report=None, title="Test", play_start=None
    )
    page = build_page.build(args)
    assert "<title>Test</title>" in page and "1/1" in page

"""Scene capsule and hooks for plugin 0.4.0 (package K), on synthetic campaigns only.

Covers the newest `## Now` lines, the stale Agency Card view, the `[state]`,
`[knowledge]`, `[habits]`, `[order]`, and `[curation] due` lines (with a
launched curator still at work), the order phrase in the header, the Stop
hook's reply-order record on synthetic transcripts (once per Player turn), and
the SessionStart notice for each source.
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import pytest

import curation
import hook_entry
import presentation_lint
import repog_runtime
import scene_capsule
from repog_runtime import runtime_settings


SESSION = "session-040"
COMMIT = 'sh "${CLAUDE_PLUGIN_ROOT}/scripts/repog.sh" rpg_state campaign commit-durable --input-file -'
NARRATION = "The fog swallows the harbour lamps one by one. " * 8  # well over 200 characters, and 60 words
NARRATION_WORDS = len(NARRATION.split())
COMPASS = (
    "# Threads\n\n## Arc Compass\n\n- Act id: ACT-02\n- Act status: active\n- Previous act id: ACT-01\n"
    "- Opened at revision: {opened}\n\n### Act Scope\n\n- Places this act can reach: the dock\n\n"
    "## Act Archive\n\n### ACT-01\n\n- Act id: ACT-01\n- Act status: closed\n- Opened at revision: 0\n"
)
VERA = """# Vera Marr

As of revision: {stamp}

## Core

- Status: alive
- Role: banker

## Now

- Day 8: holds the strongbox key.
- Day 51: the vault stands empty.

## Depth

- Voice signature: dry; counts aloud before she answers

## At-The-Table Agency Card

- Hard boundary: never lends to pirates
- Voice rhythm: clipped
- Current mundane task: pays Halloway every week
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _no_project_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)


def _write(path: Path, text: str | bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text if isinstance(text, bytes) else text.encode("utf-8"))
    return path


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    _write(path, text.replace(old, new, 1))


def _present(campaign: Path, *names: str) -> None:
    path = campaign / "current_state.yaml"
    value = json.dumps(list(names), ensure_ascii=False)
    _write(path, re.sub(r"(?m)^(  present_npcs:).*$", lambda match: f"{match.group(1)} {value}", path.read_text(encoding="utf-8")))


def _profile(campaign: Path, extra: str) -> None:
    path = campaign / "play_profile.yaml"
    _write(path, path.read_text(encoding="utf-8") + extra)


def _build(campaign: Path, prompt: str = "", *, session: str = SESSION, full: bool | None = None) -> str:
    return scene_capsule.build_capsule(
        campaign, prompt, session_id=session, settings=runtime_settings(campaign), full=full
    )


def _is_delta(text: str) -> bool:
    return any(line.startswith("Delta:") for line in text.splitlines())


def _block(text: str, title: str) -> list[str]:
    lines = text.splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith(f"- {title} ("))
    block = [lines[start]]
    for line in lines[start + 1 :]:
        if not line.startswith("  "):
            break
        block.append(line)
    return block


def _runtime(campaign: Path) -> Path:
    return campaign / ".repog-runtime"


def _noted_card(campaign: Path, *, stamp: int, opened: int | None) -> Path:
    if opened is not None:
        _write(campaign / "threads.md", COMPASS.format(opened=opened))
    return _write(campaign / "characters" / "vera.md", VERA.format(stamp=stamp))


def _run(handler: str, event: dict, capsysbinary: pytest.CaptureFixture[bytes], monkeypatch: pytest.MonkeyPatch) -> bytes:
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(json.dumps(event).encode("utf-8")), encoding="utf-8"))
    assert hook_entry.main([handler]) == 0
    return capsysbinary.readouterr().out


def _text(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}


def _tool(command: str, name: str = "Bash") -> dict[str, Any]:
    return {"type": "tool_use", "id": "tool-1", "name": name, "input": {"command": command}}


def _transcript(path: Path, *assistant: list[dict[str, Any]], prompt: str = "I wait at the dock.") -> Path:
    """A synthetic transcript: one earlier turn, then the prompt and one assistant row per block list."""

    rows: list[dict[str, Any]] = [
        {"type": "user", "uuid": "u-0", "message": {"role": "user", "content": "Earlier."}},
        {"type": "assistant", "message": {"role": "assistant", "content": [_text("Earlier reply.")]}},
        {"type": "user", "uuid": "u-1", "message": {"role": "user", "content": prompt}},
    ]
    for content in assistant:
        rows.append({"type": "assistant", "message": {"role": "assistant", "content": content}})
        if any(block.get("type") == "tool_use" for block in content):
            rows.append({"type": "user", "message": {"content": [{"type": "tool_result", "content": '{"ok": true}'}]}})
    path.write_bytes(("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n").encode("utf-8"))
    return path


def _order(transcript: Path, last_message: Any = None) -> dict[str, Any]:
    return repog_runtime.turn_order(repog_runtime.last_turn(transcript), last_message)


# ---------------------------------------------------------------------------
# Header and `## Now`
# ---------------------------------------------------------------------------


def test_a_long_place_name_never_cuts_the_order_phrase(campaign: Path) -> None:
    _replace(campaign / "current_state.yaml", "location: old_dock", "location: " + "the long harbour road " * 12)
    first = _build(campaign).splitlines()[0]
    assert len(first) <= scene_capsule.HEADER_CHARS
    assert first.endswith("… · order: reads and rolls → commit every changed fact → whole reply last")


def test_now_shows_its_newest_lines_and_marks_the_older_ones_left_out(campaign: Path) -> None:
    entries = "".join(f"- Day {day}: {'the ledger grows heavier and the vault lighter ' * 2}\n" for day in range(1, 30))
    _write(campaign / "characters" / "vera.md", f"# Vera Marr\n\n## Core\n\n- Status: alive\n\n## Now\n\n{entries}- Day 51: the vault stands empty.\n")
    _present(campaign, "Vera Marr")
    line = next(line for line in _build(campaign).splitlines() if line.startswith("  Now: "))
    assert line.startswith("  Now: … Day ") and line.endswith("Day 51: the vault stands empty.")
    assert "Day 1:" not in line and len(line) <= len("  Now: ") + scene_capsule.NOW_CHARS


def test_one_long_now_paragraph_keeps_its_last_sentences(campaign: Path) -> None:
    paragraph = " ".join(f"On day {day} she moved the gold." for day in range(1, 60)) + " Today the vault is empty."
    _write(campaign / "characters" / "vera.md", f"# Vera Marr\n\n## Core\n\n- Status: alive\n\n## Now\n\n{paragraph}\n")
    _present(campaign, "Vera Marr")
    line = next(line for line in _build(campaign).splitlines() if line.startswith("  Now: "))
    assert line.startswith("  Now: … On day ") and line.endswith("she moved the gold. Today the vault is empty.")
    assert "On day 1 " not in line


def test_a_short_now_is_shown_whole(campaign: Path) -> None:
    _noted_card(campaign, stamp=0, opened=None)
    _present(campaign, "Vera Marr")
    assert "  Now: Day 8: holds the strongbox key. Day 51: the vault stands empty." in _build(campaign)


def test_tail_helper_cuts_an_overlong_newest_sentence_at_its_head() -> None:
    text = scene_capsule._tail(["Old.", "word " * 200], 60)
    assert text.startswith(scene_capsule.OMITTED + "word word") and text.endswith("…") and len(text) <= 60


# ---------------------------------------------------------------------------
# Agency Card older than the current act
# ---------------------------------------------------------------------------


def test_a_card_stamped_before_the_act_opened_is_hidden(campaign: Path) -> None:
    _noted_card(campaign, stamp=12, opened=40)
    _present(campaign, "Vera Marr")
    assert _block(_build(campaign), "Vera Marr") == [
        "- Vera Marr (characters/vera.md)",
        "  Status: alive",
        "  Role: banker",
        "  Agency Card: hidden (note as of rev 12, before this act opened at rev 40)",
        "  Voice signature: dry; counts aloud before she answers",
        "  Now: Day 8: holds the strongbox key. Day 51: the vault stands empty.",
    ]


@pytest.mark.parametrize(("stamp", "opened"), [(40, 40), (55, 40), (12, None)])
def test_a_current_card_or_one_without_an_act_is_shown(campaign: Path, stamp: int, opened: int | None) -> None:
    _noted_card(campaign, stamp=stamp, opened=opened)
    _present(campaign, "Vera Marr")
    block = _block(_build(campaign), "Vera Marr")
    assert "  Voice rhythm: clipped" in block and "  Hard boundary: never lends to pirates" in block
    assert not any(line.startswith(("  Agency Card:", "  Voice signature:")) for line in block)


def test_a_note_without_a_stamp_keeps_its_card(campaign: Path) -> None:
    path = _noted_card(campaign, stamp=12, opened=40)
    _replace(path, "As of revision: 12\n", "")
    _present(campaign, "Vera Marr")
    assert "  Hard boundary: never lends to pirates" in _block(_build(campaign), "Vera Marr")


def test_a_legacy_note_from_an_earlier_act_shows_only_its_state_and_voice(campaign: Path) -> None:
    _write(campaign / "threads.md", COMPASS.format(opened=40))
    _write(
        campaign / "characters" / "grim.md",
        "# Ferid\n\nAs of revision: 3\n\n## Agency Card\n\n- Tier: T2\n- Voice rhythm: slow\n- Social tactic: silence\n\n"
        "## Current State (day 5)\n\nCarries freight at the Broken Anchor.\n",
    )
    _present(campaign, "Ferid")
    assert _block(_build(campaign), "Ferid") == [
        "- Ferid (characters/grim.md)",
        "  Agency Card: hidden (note as of rev 3, before this act opened at rev 40)",
        "  Current State (day 5): Carries freight at the Broken Anchor.",
    ]


def test_a_card_that_goes_stale_is_shown_whole_once_with_nothing_marked_gone(campaign: Path) -> None:
    _noted_card(campaign, stamp=12, opened=10)
    _present(campaign, "Vera Marr")
    assert "  Hard boundary: never lends to pirates" in _build(campaign)
    _replace(campaign / "threads.md", "Opened at revision: 10", "Opened at revision: 40")  # a new act opens
    delta = _build(campaign)
    assert _is_delta(delta)
    block = _block(delta, "Vera Marr")
    assert block[0] == "- Vera Marr (characters/vera.md)"  # whole, not "changed lines only"
    assert "  Agency Card: hidden (note as of rev 12, before this act opened at rev 40)" in block
    assert scene_capsule.GONE_NOTE not in delta
    _replace(campaign / "characters" / "vera.md", "As of revision: 12", "As of revision: 41")  # reviewed this act
    again = _build(campaign)
    assert "  Hard boundary: never lends to pirates" in again and scene_capsule.GONE_NOTE not in again


# ---------------------------------------------------------------------------
# [state], [knowledge], [habits]
# ---------------------------------------------------------------------------


def test_full_capsules_name_the_revision_and_the_state_keys(campaign: Path) -> None:
    full = _build(campaign)
    assert full.splitlines()[1] == (
        "[state] rev 0 · keys: campaign_id, mode, memory_version, continuity_revision, status, last_updated, "
        "persistence, fictional_time, player, current_scene, scene_frame, inventory, conditions, active_clocks, "
        "active_threats"
    )
    assert "[state]" not in _build(campaign)  # deltas leave it out


KNOWLEDGE = """# Knowledge Boundaries

## NPC And Faction Knowledge

### Ilse

- Confirmed fact ids: K-001
- Explicitly unknown fact ids: K-010 (the fruit), K-011; K-012
- Must-not-imply fact ids: K-010, K-013 (the heir)

### Witness

- Explicitly unknown fact ids: none
- Must-not-imply fact ids:

### Edric

- Explicitly unknown fact ids: K-020
"""


def test_present_people_get_what_they_do_not_know(campaign: Path) -> None:
    _write(campaign / "knowledge_boundaries.md", KNOWLEDGE)
    _write(campaign / "characters" / "ilse.md", "# Ilse\n\n## Core\n\n- Status: alive\n")
    _write(campaign / "characters" / "edric.md", "# Edric\n\n## Core\n\n- Status: alive\n")
    _present(campaign, "Ilse", "Witness")
    text = _build(campaign, "Edric watches from the door.")  # Edric is only mentioned
    assert "[knowledge]\n- Ilse does not know: K-010 (the fruit); K-011; K-012 (+1 more)\n" in text + "\n"
    assert "Witness does not know" not in text and "Edric does not know" not in text

    _replace(campaign / "knowledge_boundaries.md", "K-010 (the fruit), K-011; K-012", "K-011")
    delta = _build(campaign, "Edric watches from the door.")
    assert "- Ilse does not know: K-011; K-010; K-013 (the heir)" in delta and "knowledge" in delta.splitlines()[1]

    _replace(campaign / "knowledge_boundaries.md", "- Explicitly unknown fact ids: K-011\n- Must-not-imply fact ids: K-010, K-013 (the heir)\n", "")
    assert "[knowledge] no recorded limits for the present cast." in _build(campaign)


def _habits(items: list[dict[str, Any]]) -> Any:
    calls: list[tuple[Path, int, int]] = []

    def top_habits(campaign: Path, last: int = 20, limit: int = 3) -> list[dict[str, Any]]:
        calls.append((campaign, last, limit))
        return items

    top_habits.calls = calls  # type: ignore[attr-defined]
    return top_habits


def test_habits_show_in_full_capsules_and_in_deltas_only_when_the_list_changes(
    campaign: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    items = [
        {"rule": "avoid_phrase", "label": "bir an", "count": 6, "example": "bir an durdu"},
        {"rule": "gesture_repeat", "label": "lip corner", "count": 4, "example": "dudağının kenarı"},
    ]
    fake = _habits(items)
    monkeypatch.setattr(presentation_lint, "top_habits", fake, raising=False)
    assert "[habits] last 20 replies: bir an (6), lip corner (4)" in _build(campaign)
    assert fake.calls[-1][1:] == (20, 3)
    items[0]["count"] = 7  # the same habits, counted again
    assert "[habits]" not in _build(campaign)
    items.append({"rule": "restatement", "label": "restating openings", "count": 2})
    delta = _build(campaign)
    assert "[habits] last 20 replies: bir an (7), lip corner (4), restating openings (2)" in delta
    items.clear()
    assert f"[habits] none flagged in the last {scene_capsule.HABIT_REPLIES} replies." in _build(campaign)


def test_habits_need_the_lint_reader_and_the_lint_switch(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delattr(presentation_lint, "top_habits", raising=False)
    assert "[habits]" not in _build(campaign, session="no-reader")

    def broken(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("history unreadable")

    monkeypatch.setattr(presentation_lint, "top_habits", broken, raising=False)
    assert "[habits]" not in _build(campaign, session="broken")
    monkeypatch.setattr(presentation_lint, "top_habits", _habits([{"rule": "x", "label": "x", "count": 1}]), raising=False)
    _profile(campaign, "runtime:\n  presentation_lint: off\n")
    assert "[habits]" not in _build(campaign, session="off")


# ---------------------------------------------------------------------------
# [curation] due
# ---------------------------------------------------------------------------


def _due(campaign: Path, *paths: str) -> None:
    targets = [{"path": path, "rule": "now_overflow", "reason": "over budget"} for path in paths]
    _write(_runtime(campaign) / "curation_due.json", json.dumps({"at": "t", "revision": 3, "targets": targets}))


def test_due_curation_is_named_on_every_capsule(campaign: Path) -> None:
    _due(campaign, "characters/vera.md", "active_cast.md", "characters/vera.md")
    line = (
        "[curation] due: 2 files (characters/vera.md, active_cast.md): "
        "build the packet (curation packet) and launch repog:repog-curator in the background"
    )
    assert line in _build(campaign).splitlines()
    assert _build(campaign).splitlines()[1:] == ["Delta: nothing changed since the last capsule.", line]
    (_runtime(campaign) / "curation_due.json").unlink()  # the writer deletes it once nothing is due
    assert "due:" not in _build(campaign)


def test_due_curation_inline_wording_singular_and_long_lists(campaign: Path) -> None:
    _profile(campaign, "runtime:\n  boundary_curator: inline\n")
    _due(campaign, "threads.md")
    assert "[curation] due: 1 file (threads.md): fold them at the next distill" in _build(campaign)
    _due(campaign, *(f"characters/n{index}.md" for index in range(6)))
    line = next(line for line in _build(campaign).splitlines() if "due:" in line)
    assert line.startswith("[curation] due: 6 files (characters/n0.md, characters/n1.md, characters/n2.md, characters/n3.md, …): ")


@pytest.mark.parametrize("content", [b"\xff not json", b"[]", b'{"targets": "x"}', b'{"targets": [{"path": 7}, {"path": " "}]}'])
def test_a_malformed_due_file_shows_nothing(campaign: Path, content: bytes) -> None:
    _write(_runtime(campaign) / "curation_due.json", content)
    assert "due:" not in _build(campaign)


def _issue(campaign: Path, *, ago: float = 0.0) -> dict[str, Any]:
    """Issue a packet for the notes due, as `curation packet` does, `ago` seconds in the past."""

    packet = curation.build_packet(campaign, [])
    curation.record_issue(campaign, packet, now_ns=time.time_ns() - int(ago * 1_000_000_000))
    return packet


def _due_shown(campaign: Path) -> list[str]:
    return [line for line in _build(campaign).splitlines() if "due:" in line]


def test_due_notes_a_launched_curator_holds_say_it_is_running(campaign: Path) -> None:
    _noted_card(campaign, stamp=1, opened=None)
    _due(campaign, "characters/vera.md", "characters/witness.md")
    running = f"curator {_issue(campaign)['curation_id']} running; do not relaunch"
    # Every later prompt while the curator works: no second launch is asked for.
    assert _due_shown(campaign) == [f"[curation] due: 2 files (characters/vera.md, characters/witness.md): {running}"]
    assert _due_shown(campaign) == [f"[curation] due: 2 files (characters/vera.md, characters/witness.md): {running}"]
    # A note a later distill adds, or one changed since the packet, needs a launch of its own.
    _due(campaign, "characters/vera.md", "characters/witness.md", "active_cast.md")
    _replace(campaign / "characters" / "vera.md", "banker", "retired banker")
    assert _due_shown(campaign) == [
        f"[curation] due: 2 files (characters/vera.md, active_cast.md): {scene_capsule.DUE_BACKGROUND}",
        f"[curation] due: 1 file (characters/witness.md): {running}",
    ]


def test_due_notes_of_a_curator_presumed_gone_ask_for_a_launch_again(campaign: Path) -> None:
    _due(campaign, "characters/witness.md")
    _issue(campaign, ago=curation.ISSUE_TTL_SECONDS + 1)
    assert _due_shown(campaign) == [f"[curation] due: 1 file (characters/witness.md): {scene_capsule.DUE_BACKGROUND}"]
    _write(_runtime(campaign) / "curation_issued.json", b"\xff not json")
    assert _due_shown(campaign) == [f"[curation] due: 1 file (characters/witness.md): {scene_capsule.DUE_BACKGROUND}"]


def test_due_notes_a_finished_curator_left_unchanged_wait_for_the_distill(campaign: Path) -> None:
    _due(campaign, "characters/witness.md")
    packet = _issue(campaign, ago=60)
    staged = Path(packet["staging_path"])
    _write(staged, json.dumps({"curation_id": packet["curation_id"], "mutations": []}))
    # Staged and not yet applied, the curator still counts as running.
    assert "running; do not relaunch" in _due_shown(campaign)[0]
    curation.move_processed(staged, "applied")
    assert _due_shown(campaign) == [f"[curation] due: 1 file (characters/witness.md): {scene_capsule.DUE_UNCHANGED}"]


def test_the_prompt_hook_applying_the_proposal_ends_the_running_line(
    campaign: Path, tmp_path: Path, capsysbinary, monkeypatch
) -> None:
    _due(campaign, "characters/witness.md", "active_cast.md")
    packet = _issue(campaign, ago=60)
    fold = {"path": "characters/witness.md", "ops": [{"op": "replace_section", "heading": "Current State", "text": "Calm."}]}
    staged = _write(
        Path(packet["staging_path"]),
        json.dumps(
            {
                "curation_id": packet["curation_id"],
                "base_revision": 0,
                "reason": "fold the state",
                "base_hashes": {"characters/witness.md": packet["base_hashes"]["characters/witness.md"]},
                "mutations": [fold],
            }
        ),
    )
    settled = time.time() - 30  # written after the packet, and settled for the writer
    os.utime(staged, (settled, settled))
    out = _run("prompt", {"cwd": str(tmp_path), "session_id": SESSION, "prompt": "Go on."}, capsysbinary, monkeypatch)
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    # The writer dropped the folded note; the one the curator left alone waits for the distill.
    assert [line for line in context.splitlines() if "due:" in line] == [
        f"[curation] due: 1 file (active_cast.md): {scene_capsule.DUE_UNCHANGED}"
    ]


def test_the_inline_curator_ignores_issued_packets(campaign: Path) -> None:
    _due(campaign, "characters/witness.md")
    _issue(campaign)
    _profile(campaign, "runtime:\n  boundary_curator: inline\n")
    assert _due_shown(campaign) == [f"[curation] due: 1 file (characters/witness.md): {scene_capsule.DUE_INLINE}"]


# ---------------------------------------------------------------------------
# [order]
# ---------------------------------------------------------------------------


def _order_record(campaign: Path, at: str, **fields: Any) -> None:
    """A Stop hook record; each `at` stands for a new Player turn unless `prompt_uuid` says otherwise."""

    record = {
        "at": at,
        "prompt_uuid": f"u-{at}",
        "expected": "commit_then_narrate",
        "observed": "commit_first",
        "final_text": True,
        "reply_words": 240,
    }
    _write(_runtime(campaign) / "order_last.json", json.dumps({**record, **fields}))


def test_order_reminders_are_shown_once_after_the_turn_that_needs_them(campaign: Path) -> None:
    _build(campaign)
    _order_record(campaign, "t1", final_text=False, session_id=SESSION)
    assert _build(campaign).splitlines()[1:] == [
        "Delta: nothing changed since the last capsule.",
        scene_capsule.ORDER_NO_TEXT,
    ]
    assert "[order]" not in _build(campaign)  # the same record is not repeated
    _order_record(campaign, "t2", session_id=SESSION)
    assert "[order]" not in _build(campaign)  # a delivered reply needs no reminder
    _order_record(campaign, "t3", reply_words=21, session_id=SESSION)
    full = _build(campaign, full=True)
    assert full.splitlines()[1] == scene_capsule.ORDER_SHORT_REPLY.format(words=21)
    assert scene_capsule.ORDER_NO_TEXT not in full


def test_order_reminders_follow_the_record_s_session_and_what_was_saved(campaign: Path) -> None:
    _order_record(campaign, "t1", reply_words=21, session_id="another-session")
    assert "[order]" not in _build(campaign)
    _order_record(campaign, "t2", observed="no_commit", reply_words=12, session_id=SESSION)
    assert "[order]" not in _build(campaign)  # a short answer that saved nothing lost nothing
    _order_record(campaign, "t3", observed="no_commit", final_text=False)  # no session recorded: any session
    assert scene_capsule.ORDER_NO_TEXT in _build(campaign)
    _write(_runtime(campaign) / "order_last.json", b"\xff{")
    assert "[order]" not in _build(campaign)


# ---------------------------------------------------------------------------
# Reply order on synthetic transcripts
# ---------------------------------------------------------------------------


def test_narration_before_the_commit(tmp_path: Path) -> None:
    path = _transcript(tmp_path / "t.jsonl", [_text(NARRATION), _tool(COMMIT)], [_text("The fog waits.")])
    assert _order(path) == {"observed": "narrate_first", "final_text": True, "reply_words": NARRATION_WORDS + 3}


def test_commit_before_the_narration(tmp_path: Path) -> None:
    path = _transcript(tmp_path / "t.jsonl", [_tool("sh repog.sh roll_dice --campaign campaign")], [_tool(COMMIT)], [_text(NARRATION)])
    assert _order(path) == {"observed": "commit_first", "final_text": True, "reply_words": NARRATION_WORDS}


def test_a_short_status_line_before_the_commit_is_not_narration(tmp_path: Path) -> None:
    path = _transcript(tmp_path / "t.jsonl", [_text("Saving the scene first."), _tool(COMMIT)], [_text(NARRATION)])
    assert _order(path)["observed"] == "commit_first"


def test_a_turn_without_a_commit(tmp_path: Path) -> None:
    for command in ("sh repog.sh rpg_state campaign template --kind durable", "git commit -m x"):
        path = _transcript(tmp_path / "t.jsonl", [_text(NARRATION), _tool(command)], [_text("Done.")])
        assert _order(path) == {"observed": "no_commit", "final_text": True, "reply_words": NARRATION_WORDS + 1}


def test_a_turn_that_ends_on_the_commit_has_no_final_text(tmp_path: Path) -> None:
    thinking = [{"type": "thinking", "thinking": "Saved; nothing more to say.", "signature": "x"}]
    path = _transcript(tmp_path / "t.jsonl", [_text(NARRATION), _tool(COMMIT)], thinking)
    assert _order(path) == {"observed": "narrate_first", "final_text": False, "reply_words": NARRATION_WORDS}
    assert _order(path, "")["final_text"] is False


def test_the_stop_event_s_last_message_stands_in_for_a_lagging_transcript(tmp_path: Path) -> None:
    path = _transcript(tmp_path / "t.jsonl", [_tool(COMMIT)])
    assert _order(path) == {"observed": "commit_first", "final_text": False, "reply_words": 0}
    assert _order(path, NARRATION) == {"observed": "commit_first", "final_text": True, "reply_words": NARRATION_WORDS}
    assert repog_runtime.turn_order(None) == {"observed": "no_commit", "final_text": False, "reply_words": 0}


def test_last_turn_keeps_text_and_tool_blocks_in_order(tmp_path: Path) -> None:
    path = _transcript(tmp_path / "t.jsonl", [_text("One."), _tool(COMMIT)], [_text("Two.")])
    turn = repog_runtime.last_turn(path)
    assert turn is not None
    assert [block["type"] for block in turn["blocks"]] == ["text", "tool_use", "text"]
    assert turn["assistant_texts"] == ["One.", "Two."] and turn["tool_uses"][0]["input"]["command"] == COMMIT


def test_the_stop_hook_records_the_order_and_the_next_capsule_shows_it(
    campaign: Path, tmp_path: Path, capsysbinary, monkeypatch
) -> None:
    transcript = _transcript(tmp_path / "session.jsonl", [_tool(COMMIT)], [_text(NARRATION)])
    event = {"cwd": str(tmp_path), "session_id": SESSION, "transcript_path": str(transcript)}
    _run("prompt", {**event, "prompt": "I wait."}, capsysbinary, monkeypatch)
    assert _run("stop", {**event, "last_assistant_message": NARRATION}, capsysbinary, monkeypatch) == b""

    record = json.loads((_runtime(campaign) / "order_last.json").read_text(encoding="utf-8"))
    assert set(record) == {"at", "prompt_uuid", "session_id", "expected", "observed", "final_text", "reply_words"}
    assert record["prompt_uuid"] == "u-1" and record["session_id"] == SESSION
    assert (record["expected"], record["observed"], record["final_text"]) == ("commit_then_narrate", "commit_first", True)
    assert record["reply_words"] == NARRATION_WORDS
    assert "fog" not in json.dumps(record)  # flags and a word count only, never the reply's text

    out = _run("prompt", {**event, "prompt": "I wait."}, capsysbinary, monkeypatch)
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "[order]" not in context  # the whole reply went out


def test_the_stop_hook_writes_no_order_record_without_a_transcript(campaign: Path, tmp_path: Path, capsysbinary, monkeypatch) -> None:
    _run("stop", {"cwd": str(tmp_path), "session_id": SESSION, "transcript_path": str(tmp_path / "missing.jsonl")}, capsysbinary, monkeypatch)
    assert not (_runtime(campaign) / "order_last.json").exists()


def _append(transcript: Path, *rows: dict[str, Any]) -> None:
    with transcript.open("ab") as stream:
        stream.write("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode("utf-8"))


def test_a_stop_after_a_task_notification_keeps_the_player_turn_s_record(
    campaign: Path, tmp_path: Path, capsysbinary, monkeypatch
) -> None:
    transcript = _transcript(tmp_path / "session.jsonl", [_text(NARRATION), _tool(COMMIT)], [_text("Ne yaparsın?")])
    event = {"cwd": str(tmp_path), "session_id": SESSION, "transcript_path": str(transcript)}
    _run("stop", {**event, "last_assistant_message": "Ne yaparsın?"}, capsysbinary, monkeypatch)
    path = _runtime(campaign) / "order_last.json"
    recorded = path.read_bytes()
    assert (json.loads(recorded)["observed"], json.loads(recorded)["final_text"]) == ("narrate_first", True)
    assert "[order]" not in _build(campaign)

    # A background curator's completion notice starts a turn the Player did
    # not type, and that turn ends on a tool call with no text.
    _append(
        transcript,
        {"type": "user", "message": {"role": "user", "content": "<task-notification><task-id>c1</task-id></task-notification>"}},
        {"type": "assistant", "message": {"role": "assistant", "content": [_tool("cat notes.md", "Read")]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}},
    )
    _run("stop", {**event, "last_assistant_message": ""}, capsysbinary, monkeypatch)
    assert path.read_bytes() == recorded
    assert "[order]" not in _build(campaign)

    # The Player's next turn is recorded on its own.
    _append(
        transcript,
        {"type": "user", "uuid": "u-2", "message": {"role": "user", "content": "I follow her."}},
        {"type": "assistant", "message": {"role": "assistant", "content": [_tool(COMMIT)]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}},
        {"type": "assistant", "message": {"role": "assistant", "content": [_text("She nods.")]}},
    )
    _run("stop", {**event, "last_assistant_message": "She nods."}, capsysbinary, monkeypatch)
    record = json.loads(path.read_bytes())
    assert (record["prompt_uuid"], record["observed"], record["final_text"]) == ("u-2", "commit_first", True)
    assert scene_capsule.ORDER_SHORT_REPLY.format(words=2) in _build(campaign)


def test_a_player_turn_is_reminded_of_once_however_often_its_record_is_written(campaign: Path) -> None:
    _build(campaign)
    _order_record(campaign, "t1", prompt_uuid="u-7", reply_words=5, session_id=SESSION)
    assert scene_capsule.ORDER_SHORT_REPLY.format(words=5) in _build(campaign)
    _order_record(campaign, "t2", prompt_uuid="u-7", reply_words=5, final_text=False, session_id=SESSION)
    assert "[order]" not in _build(campaign)


# ---------------------------------------------------------------------------
# SessionStart after a compaction or a resume
# ---------------------------------------------------------------------------


TEMPLATE = (Path(scene_capsule.__file__).resolve().parents[1] / "templates" / "campaign" / "storytelling.md").read_text(encoding="utf-8")


def _storytelling(campaign: Path, extra: str = "") -> None:
    text = TEMPLATE.replace(
        "- Accepted sample or evidence reference:",
        "- Accepted sample or evidence reference: Rüzgâr iskeleye vuruyor; Vera başını kaldırmadan sayıyor.",
    )
    _write(campaign / "storytelling.md", text + extra)


@pytest.mark.parametrize("source", ["startup", "clear"])
def test_session_start_prints_nothing_for_a_fresh_or_cleared_session(
    campaign: Path, tmp_path: Path, capsysbinary, monkeypatch, source: str
) -> None:
    _storytelling(campaign, "\n## Örnek Anlatım\n\nSis limanı yutuyor.\n")
    assert _run("session-start", {"cwd": str(tmp_path), "session_id": SESSION, "source": source}, capsysbinary, monkeypatch) == b""


@pytest.mark.parametrize("source", ["compact", "resume"])
def test_session_start_after_a_compaction_or_resume_prints_samples_then_the_locked_order(
    campaign: Path, tmp_path: Path, capsysbinary, monkeypatch, source: str
) -> None:
    _storytelling(campaign, "\n## Örnek Anlatım\n\nSis limanı yutuyor; fenerler birer birer sönüyor.\n\n## Stage 9 Proof\n\nKısa bir kanıt anlatımı.\n")
    _build(campaign)
    out = _run("session-start", {"cwd": str(tmp_path), "session_id": SESSION, "source": source}, capsysbinary, monkeypatch)
    lines = out.decode("utf-8").splitlines()
    assert lines[0] == scene_capsule.SAMPLES_INTRO
    assert lines[-1] == scene_capsule.LOCKED_ORDER
    text = "\n".join(lines)
    # Accepted evidence, sample and proof sections in file order, without template guidance.
    assert text.index("## Accepted Voice Evidence") < text.index("## Örnek Anlatım") < text.index("## Stage 9 Proof")
    assert "Rüzgâr iskeleye vuruyor" in text
    assert "Keep a short accepted sample" not in text and "Point of view:" not in text
    assert not _is_delta(_build(campaign))  # the capsule was marked for a full refresh too


def test_session_start_prints_only_the_order_without_samples_and_nothing_before_play(
    campaign: Path, tmp_path: Path, capsysbinary, monkeypatch
) -> None:
    _write(campaign / "storytelling.md", TEMPLATE)  # the template alone holds no accepted sample
    event = {"cwd": str(tmp_path), "session_id": SESSION, "source": "compact"}
    assert _run("session-start", event, capsysbinary, monkeypatch) == (scene_capsule.LOCKED_ORDER + "\n").encode("utf-8")
    _replace(campaign / "setup_profile.yaml", "ready_for_play: true", "ready_for_play: false")
    assert _run("session-start", event, capsysbinary, monkeypatch) == b""


def test_accepted_samples_come_before_the_voice_selectors(campaign: Path) -> None:
    _storytelling(campaign)
    _replace(campaign / "storytelling.md", "- Preferred texture:", "- Preferred texture: " + "salt, rope and lamp smoke; " * 12)
    accepted, voice = scene_capsule.style_samples(campaign).split("\n\n")
    assert accepted.startswith("## Accepted Voice Evidence\n") and "Rüzgâr iskeleye vuruyor" in accepted
    assert voice.startswith("## Narrative Voice\n- Preferred texture: salt, rope")
    # A budget that holds only the accepted sample spends nothing on the selectors.
    tight = scene_capsule.style_samples(campaign, limit=len(accepted))
    assert "Rüzgâr iskeleye vuruyor" in tight and "Narrative Voice" not in tight and tight.endswith("…")


def test_style_samples_stay_within_their_budget(campaign: Path) -> None:
    _storytelling(campaign, "\n## Voice Samples\n\n" + "Sis limanı yutuyor ve fenerler sönüyor. " * 120 + "\n")
    samples = scene_capsule.style_samples(campaign)
    assert samples.startswith("## Accepted Voice Evidence\n") and "\n\n## Voice Samples\n" in samples
    assert samples.endswith("…")
    assert len(samples) <= scene_capsule.SAMPLE_CHARS
    assert scene_capsule.style_samples(campaign / "missing") == ""

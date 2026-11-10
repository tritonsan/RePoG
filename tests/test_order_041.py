"""The 0.4.1 contract: every turn saves first and sends the whole reply last.

0.4.0 asked for the reply, then the commit, then a closing line. The model drafted
the scene in its reasoning, committed, and sent only the closing line, so the
Player saw one sentence of the turn. These tests hold the shape that replaced it:
one order, a writer note that says what comes next, a tripwire for a turn that
saved a result but sent almost nothing, and a commit small enough to wait for.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

import check_runtime
import owner_ops
import repog_runtime
import resolve_mechanic
import roll_dice
import rpg_state
import scene_capsule


# The standalone workspace root holds the same tree as the plugin folder.
PLUGIN = Path(__file__).resolve().parents[1]
SCENE = "Vera sends him out to watch the steward from the roofs, and the day goes by in tile and heat. " * 6
TABLE = """# Cast

| NPC | Tier | Current activity | Last seen | Revision |
| --- | --- | --- | --- | ---: |
| Mira | T2 | at the pier \\| waiting | the dock | 3 |
| Ilse | T3 | at sea | the dock | 2 |
"""


def _md(text: str, ops: list[dict[str, Any]], *, revision: int = 7) -> str:
    context = owner_ops.PlaceholderContext(revision)
    return owner_ops.apply_ops(text, ops, relative="active_cast.md", label="m", placeholders=context)


def _row(text: str, name: str) -> list[str]:
    line = next(line for line in text.splitlines() if line.startswith(f"| {name} "))
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


# ---------------------------------------------------------------------------
# One order
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["narrate_then_commit", "commit_then_narrate", "", "something_else"])
def test_every_profile_value_means_the_one_order(tmp_path: Path, value: str) -> None:
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    (campaign / "play_profile.yaml").write_text(f"runtime:\n  persistence_order: {value}\n", encoding="utf-8")
    assert repog_runtime.runtime_settings(campaign)["persistence_order"] == "commit_then_narrate"


def test_an_older_profile_value_stays_valid() -> None:
    # A campaign locked to the old value must not gain a finding from this change.
    assert "narrate_then_commit" in check_runtime.RUNTIME_ALLOWED["persistence_order"]


SHIPPED = [
    path
    for pattern in ("AGENTS.md", "README.md", "skills/**/*.md", "workflows/**/*.md", "output-styles/*.md", "agents/*.md", ".claude/output-styles/*.md", ".claude/agents/*.md", "tools/README.md")
    for path in PLUGIN.glob(pattern)
]


@pytest.mark.parametrize(
    "phrase",
    ["hand-back", "hand_back", "handback", "reply first", "Write the reply first", "reply comes first", "Never commit first"],
)
def test_no_shipped_instruction_keeps_the_old_order(phrase: str) -> None:
    assert SHIPPED
    for path in SHIPPED:
        flat = " ".join(path.read_bytes().decode("utf-8").split())
        if path.name == "visuals.md" and phrase == "reply comes first":
            continue  # an image prompt follows the reply; this is not the save order
        assert phrase.casefold() not in flat.casefold(), (path.relative_to(PLUGIN), phrase)


def test_no_shipped_instruction_branches_on_the_old_order() -> None:
    for path in SHIPPED:
        flat = " ".join(path.read_bytes().decode("utf-8").split())
        assert "Under `narrate_then_commit`" not in flat, path.relative_to(PLUGIN)
        assert "under `narrate_then_commit`" not in flat, path.relative_to(PLUGIN)
        assert "Under `commit_then_narrate`" not in flat, path.relative_to(PLUGIN)


def test_the_capsule_names_the_order_and_the_resume_notice_repeats_it() -> None:
    assert scene_capsule.ORDER_PHRASE == "order: reads and rolls → commit every changed fact → whole reply last"
    assert "the whole reply as the turn's last message" in scene_capsule.LOCKED_ORDER


# ---------------------------------------------------------------------------
# The tripwire: a saved result with almost nothing sent
# ---------------------------------------------------------------------------


COMMIT = 'sh "${CLAUDE_PLUGIN_ROOT}/scripts/repog.sh" rpg_state campaign commit-durable --input-file -'


def _turn(*blocks: dict[str, Any]) -> dict[str, Any]:
    return {"blocks": list(blocks)}


def _tool(command: str = COMMIT) -> dict[str, Any]:
    return {"type": "tool_use", "name": "Bash", "input": {"command": command}}


def _text(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}


def test_a_scene_kept_in_the_reasoning_leaves_only_a_few_words() -> None:
    # What the G3 session did: nothing visible before the commit, one line after it.
    order = repog_runtime.turn_order(_turn(_tool(), _text('She weighs the glasses. "Not on the roof."')))
    assert order == {"observed": "commit_first", "final_text": True, "reply_words": 8}
    assert order["reply_words"] < repog_runtime.SHORT_REPLY_WORDS


def test_the_whole_reply_after_the_commit_clears_the_tripwire() -> None:
    order = repog_runtime.turn_order(_turn(_tool(), _text(SCENE)))
    assert order["observed"] == "commit_first" and order["reply_words"] >= repog_runtime.SHORT_REPLY_WORDS


def test_reply_words_count_every_visible_text_of_the_turn() -> None:
    first, second = "One two three.", "Four five."
    assert repog_runtime.turn_order(_turn(_text(first), _tool(), _text(second)))["reply_words"] == 5


def test_a_lagging_transcript_still_counts_the_final_message() -> None:
    order = repog_runtime.turn_order(_turn(_tool()), SCENE)
    assert order["reply_words"] == len(SCENE.split()) and order["final_text"] is True


# ---------------------------------------------------------------------------
# The writer's note
# ---------------------------------------------------------------------------


def _append_turn(operation: str, expected: int, *, owner: str = "characters/ilse.md") -> dict[str, Any]:
    return {
        "operation_id": operation,
        "expected_continuity_revision": expected,
        "boundary": "ordinary",
        "cause": "Vera sent him to the roofs.",
        "changes": [{"id": "c", "kind": "npc_state", "established_delta": "He is sent out.", "owners": [owner]}],
        "mutations": [{"path": owner, "ops": [{"op": "append", "heading": "Now", "text": f"Day {expected + 2}: she sent him out."}]}],
    }


NOTE = """# Ilse

Tier: T2

## Now

Day 1: at the dock.
"""


@pytest.fixture()
def noted(campaign: Path) -> Path:
    (campaign / "characters").mkdir(exist_ok=True)
    (campaign / "characters" / "ilse.md").write_text(NOTE, encoding="utf-8")
    return campaign


def test_a_commit_tells_the_gm_to_send_the_whole_reply(noted: Path) -> None:
    result = rpg_state.commit_durable(noted, _append_turn("t1", 0))
    assert result["reply"] == rpg_state.REPLY_NOTE
    assert "hand_back" not in result


def test_a_due_distill_comes_before_the_reply() -> None:
    assert rpg_state._reply_note(True) == rpg_state.REPLY_NOTE
    assert rpg_state._reply_note(False) == rpg_state.REPLY_WAIT_NOTE


# ---------------------------------------------------------------------------
# A small commit
# ---------------------------------------------------------------------------


def test_resume_impact_is_optional_and_a_receipt_without_it_has_no_line(noted: Path) -> None:
    rpg_state.commit_durable(noted, _append_turn("t1", 0))
    log = (noted / "session_log.md").read_text(encoding="utf-8")
    assert "Vera sent him to the roofs." in log and "Resume impact" not in log


def test_a_given_resume_impact_is_kept(noted: Path) -> None:
    payload = {**_append_turn("t1", 0), "resume_impact": "A restart must keep the watch."}
    rpg_state.commit_durable(noted, payload)
    assert "A restart must keep the watch." in (noted / "session_log.md").read_text(encoding="utf-8")


def test_the_durable_template_no_longer_asks_for_resume_impact(noted: Path) -> None:
    assert "resume_impact" not in rpg_state.template(noted, "durable")["payload"]


def test_now_entries_appended_turn_by_turn_fold_into_history(noted: Path) -> None:
    for turn in range(4):
        rpg_state.commit_durable(noted, _append_turn(f"t{turn}", turn))
    text = (noted / "characters" / "ilse.md").read_text(encoding="utf-8")
    now = text[text.index("## Now") : text.index("## History")]
    history = text[text.index("## History") :]
    assert owner_ops.now_status(text)[1] == owner_ops.NOW_MAX_DATED
    assert "Day 1: at the dock." in history and "Day 1: at the dock." not in now
    assert "Day 5: she sent him out." in now


def test_set_cells_changes_only_the_named_columns_and_stamps_the_revision() -> None:
    text = _md(TABLE, [{"op": "set_cells", "key": "Ilse", "cells": {"Current activity": "back in port"}}])
    assert _row(text, "Ilse") == ["Ilse", "T3", "back in port", "the dock", "7"]
    assert _row(text, "Mira") == ["Mira", "T2", "at the pier \\| waiting", "the dock", "3"]


def test_set_cells_finds_columns_regardless_of_case() -> None:
    text = _md(TABLE, [{"op": "set_cells", "key": "Ilse", "cells": {"last SEEN": "the mill"}}])
    assert _row(text, "Ilse")[3] == "the mill"


def test_set_cells_keeps_an_escaped_pipe_and_a_given_revision() -> None:
    text = _md(TABLE, [{"op": "set_cells", "key": "Mira", "cells": {"Last seen": "the mill", "Revision": "99"}}])
    assert _row(text, "Mira") == ["Mira", "T2", "at the pier \\| waiting", "the mill", "99"]


def test_set_cells_escapes_a_pipe_in_new_text() -> None:
    text = _md(TABLE, [{"op": "set_cells", "key": "Ilse", "cells": {"Last seen": "the mill | the weir"}}])
    assert _row(text, "Ilse")[3] == "the mill \\| the weir"


def test_set_cells_resolves_placeholders() -> None:
    text = _md(TABLE, [{"op": "set_cells", "key": "Ilse", "cells": {"Last seen": "rev {{revision}}"}}])
    assert _row(text, "Ilse")[3] == "rev 7"


def test_set_cells_needs_no_revision_column() -> None:
    table = "| From | To | State |\n| --- | --- | --- |\n| Mira | Ilse | wary |\n"
    text = _md(table, [{"op": "set_cells", "key": ["Mira", "Ilse"], "cells": {"State": "trusting"}}])
    assert "| Mira | Ilse | trusting |" in text


@pytest.mark.parametrize(
    ("op", "message"),
    [
        ({"key": "Nobody", "cells": {"Tier": "T1"}}, "add it with upsert_row"),
        ({"key": "Ilse", "cells": {"Mood": "calm"}}, "no column 'Mood'"),
        ({"key": "Ilse", "cells": {"NPC": "Isla"}}, "part of the key"),
        ({"key": "Ilse", "cells": {}}, "must map column names"),
        ({"key": "Ilse", "cells": ["Ilse"]}, "must map column names"),
    ],
)
def test_set_cells_refuses_what_it_cannot_place(op: dict[str, Any], message: str) -> None:
    with pytest.raises(owner_ops.OwnerOpError, match=message):
        _md(TABLE, [{"op": "set_cells", **op}])


def test_set_cells_runs_through_a_commit(noted: Path) -> None:
    cast = noted / "active_cast.md"
    cast.write_text(TABLE, encoding="utf-8")
    payload = {
        "operation_id": "t1",
        "expected_continuity_revision": 0,
        "boundary": "ordinary",
        "cause": "Ilse came back.",
        "changes": [{"id": "c", "kind": "presence", "established_delta": "Ilse is in port.", "owners": ["active_cast.md"]}],
        "mutations": [{"path": "active_cast.md", "ops": [{"op": "set_cells", "key": "Ilse", "cells": {"Current activity": "in port"}}]}],
    }
    result = rpg_state.commit_durable(noted, payload)
    assert result["ok"] is True
    assert _row(cast.read_text(encoding="utf-8"), "Ilse") == ["Ilse", "T3", "in port", "the dock", "1"]


def test_the_playbook_example_shows_the_small_commit() -> None:
    text = (PLUGIN / "workflows" / "gm" / "playbooks" / "persistence.md").read_bytes().decode("utf-8")
    example = text[text.index("<<'JSON'") : text.index("\nJSON", text.index("<<'JSON'"))].replace("\r\n", "\n")
    payload = json.loads(example.split("\n", 1)[1])
    assert "resume_impact" not in payload
    written = json.dumps(payload["mutations"], ensure_ascii=False)
    assert "scene_frame.resume_anchor" in written and '"heading": "Now"' in written
    assert "last_causal_beat" not in written and "replace_section" not in written


# ---------------------------------------------------------------------------
# A session never looks a call shape up
# ---------------------------------------------------------------------------


def _capsule(campaign: Path, session: str = "s-1") -> str:
    return scene_capsule.build_capsule(campaign, "", session_id=session, settings={"scene_capsule": "on"})


def _card_json(prefix: str) -> dict[str, Any]:
    """The JSON of the card line that starts with `prefix`, its placeholders filled in."""

    line = next(line for line in scene_capsule.format_card() if line.startswith(prefix))
    raw = line[line.index("{") :].replace("<revision+1>", "1").replace("<revision>", "0").replace("<scene>", "dock")
    return json.JSONDecoder().raw_decode(raw)[0]


def test_the_first_capsule_carries_the_card_and_the_next_one_does_not(campaign: Path) -> None:
    first = _capsule(campaign)
    assert first.endswith(scene_capsule.format_card()[-1])
    assert "[formats]" in first
    assert "[formats]" not in _capsule(campaign)


def test_a_reset_brings_the_card_back(campaign: Path) -> None:
    _capsule(campaign)
    scene_capsule.reset(campaign, "s-1")  # a compaction drops it from the context
    assert "[formats]" in _capsule(campaign)


def test_the_card_names_this_install_s_launcher() -> None:
    line = scene_capsule.format_card()[0]
    if not (PLUGIN / "scripts" / "repog.sh").is_file():
        # A standalone workspace runs the helpers with python directly.
        assert "python tools/<helper>.py" in line and 'sh "' not in line
        return
    launcher = Path(line.split('sh "', 1)[1].split('"', 1)[0])
    assert launcher.is_file() and launcher.name == "repog.sh"


def test_the_card_fits_the_host_limit_after_the_fullest_capsule() -> None:
    hook_entry = pytest.importorskip("hook_entry", reason="hook entry ships only with the Claude Code plugin")

    assert scene_capsule.FULL_MAX + len("\n".join(scene_capsule.format_card())) + 1 < hook_entry.MAX_CONTEXT


def test_the_writer_accepts_the_card_s_commit_shape(campaign: Path) -> None:
    (campaign / "characters" / "x.md").write_text("# X\n\n## Now\n\nDay 1: at the dock.\n", encoding="utf-8")
    (campaign / "active_cast.md").write_text(
        "# Cast\n\n| NPC | Current activity | Revision |\n| --- | --- | ---: |\n| Name | waiting | 0 |\n", encoding="utf-8"
    )
    payload = _card_json("rpg_state campaign commit-durable")
    payload["changes"][0]["owners"].append("active_cast.md")
    payload["mutations"][2]["ops"][0]["cells"]["Current activity"] = "at the pier"
    result = rpg_state.commit_durable(campaign, payload)
    assert result["ok"] is True and result["continuity_revision"] == 1
    assert "dated line" in (campaign / "characters" / "x.md").read_text(encoding="utf-8")


def test_the_writer_accepts_the_card_s_distill_shape(campaign: Path) -> None:
    payload = _card_json("A due distill")
    assert set(payload) == {"operation_id", "expected_continuity_revision", "trigger", "summary", "mutations"}
    assert rpg_state.commit_distill(campaign, payload)["operation"] == "commit-distill"


def test_the_card_s_roll_shape_is_the_one_roll_dice_reads() -> None:
    payload = _card_json("roll_dice --campaign campaign")
    assert set(payload) == set(roll_dice.REQUEST_REQUIRED)
    call = payload["call"]
    assert set(roll_dice.CALL_REQUIRED) <= set(call) <= set(roll_dice.CALL_REQUIRED) | set(roll_dice.CALL_OPTIONAL)


def test_the_card_s_mechanic_operations_are_supported() -> None:
    line = next(line for line in scene_capsule.format_card() if line.startswith("Money and items"))
    for operation in ("consume_item", "add_item", "remove_item", "spend", "gain"):
        assert operation in line and operation in resolve_mechanic.SUPPORTED_OPERATIONS


def test_the_full_capsule_shows_what_a_mechanic_operation_addresses(campaign: Path) -> None:
    state = {
        "schema_version": 2,
        "enabled": True,
        "actors": {
            "mira": {
                "resources": {"breath": {"current": 3, "minimum": 0, "maximum": 5}},
                "inventory": {"coin": {"quantity": 500, "consumable": True}},
            }
        },
    }
    (campaign / "mechanics_state.json").write_text(json.dumps(state), encoding="utf-8")
    assert "[mechanics] mira items: coin 500; resources: breath 3/5" in _capsule(campaign)


def test_no_mechanics_line_without_an_enabled_ledger(campaign: Path) -> None:
    (campaign / "mechanics_state.json").write_text(json.dumps({"enabled": False, "actors": {"mira": {}}}), encoding="utf-8")
    assert "[mechanics] " not in _capsule(campaign).replace("[mechanics] lists", "")
    (campaign / "mechanics_state.json").write_bytes(b"\xff{")
    assert "[mechanics] " not in _capsule(campaign, "s-2").replace("[mechanics] lists", "")


def test_one_roll_may_back_several_changes_of_a_commit(campaign: Path) -> None:
    call = {"actor": "Mira", "axis": "insight", "value": 3, "difficulty": 4, "stakes": "the witness clams up"}
    receipt = roll_dice.roll_call(campaign, {"roll_id": "read-1", "die": "1d6", "call": call})
    cited = {"roll_reference": "read-1", "outcome": receipt["band"]}
    payload = {
        "operation_id": "t1",
        "expected_continuity_revision": 0,
        "boundary": "ordinary",
        "cause": "Mira read the witness.",
        "changes": [
            {"id": "a", "kind": "knowledge", "established_delta": "She knows.", "owners": ["knowledge_boundaries.md"], **cited},
            {"id": "b", "kind": "scene_progress", "established_delta": "He talks.", "owners": ["current_state.yaml"], **cited},
        ],
        "mutations": [
            {"path": "knowledge_boundaries.md", "ops": [{"op": "append", "heading": "Player Knowledge", "text": "- Fact: read."}]},
            {"path": "current_state.yaml", "ops": [{"op": "set", "values": {"scene_frame.resume_anchor": "He talks."}}]},
        ],
    }
    assert rpg_state.commit_durable(campaign, payload)["continuity_revision"] == 1
    assert roll_dice.find_receipt(campaign, "read-1")["consumed_revision"] == 1


# ---------------------------------------------------------------------------
# A refused commit costs a round trip: the writer takes what is harmless
# ---------------------------------------------------------------------------


def _note_turn(*mutations: dict[str, Any], operation: str = "t1") -> dict[str, Any]:
    return {
        "operation_id": operation,
        "expected_continuity_revision": 0,
        "boundary": "ordinary",
        "cause": "Ilse came back.",
        "changes": [{"id": "c", "kind": "npc_state", "established_delta": "She is back.", "owners": ["characters/ilse.md"]}],
        "mutations": list(mutations),
    }


def test_two_mutations_of_one_owner_run_in_order(noted: Path) -> None:
    first = {"path": "characters/ilse.md", "ops": [{"op": "append", "heading": "Now", "text": "Day 2: back at the dock."}]}
    second = {"path": "characters/ilse.md", "exact_replacements": [{"old": "back at the dock", "new": "back at the mill"}]}
    assert rpg_state.commit_durable(noted, _note_turn(first, second))["ok"] is True
    assert "Day 2: back at the mill." in (noted / "characters" / "ilse.md").read_text(encoding="utf-8")


def test_ops_and_replacements_may_share_a_mutation(noted: Path) -> None:
    mutation = {
        "path": "characters/ilse.md",
        "exact_replacements": [{"old": "at the dock", "new": "at the mill"}],
        "ops": [{"op": "append", "heading": "Now", "text": "Day 2: left the mill."}],
    }
    assert rpg_state.commit_durable(noted, _note_turn(mutation))["ok"] is True
    text = (noted / "characters" / "ilse.md").read_text(encoding="utf-8")
    assert "Day 1: at the mill." in text and "Day 2: left the mill." in text


def test_a_replacement_that_changes_nothing_is_skipped(noted: Path) -> None:
    mutation = {
        "path": "characters/ilse.md",
        "exact_replacements": [{"old": "Tier: T2", "new": "Tier: T2"}, {"old": "at the dock", "new": "at the mill"}],
    }
    assert rpg_state.commit_durable(noted, _note_turn(mutation))["ok"] is True


def test_a_mutation_still_needs_a_form(noted: Path) -> None:
    with pytest.raises(rpg_state.RPGStateError, match="needs ops, exact_replacements, or create_text"):
        rpg_state.commit_durable(noted, _note_turn({"path": "characters/ilse.md"}))


def test_create_text_stands_alone(noted: Path) -> None:
    new = "characters/new.md"
    both = {"path": new, "create_text": "# New\n", "ops": [{"op": "append", "text": "x"}]}
    with pytest.raises(rpg_state.RPGStateError, match="needs ops, exact_replacements, or create_text"):
        rpg_state.commit_durable(noted, _note_turn(both))
    edit = {"path": "characters/ilse.md", "ops": [{"op": "append", "heading": "Now", "text": "Day 2: left."}]}
    again = {"path": "characters/ilse.md", "create_text": "# Ilse\n"}
    with pytest.raises(rpg_state.RPGStateError, match="create_text cannot follow"):
        rpg_state.commit_durable(noted, _note_turn(edit, again))


def test_a_failing_later_mutation_writes_nothing(noted: Path) -> None:
    before = (noted / "characters" / "ilse.md").read_bytes()
    good = {"path": "characters/ilse.md", "ops": [{"op": "append", "heading": "Now", "text": "Day 2: left."}]}
    bad = {"path": "characters/ilse.md", "exact_replacements": [{"old": "no such text", "new": "x"}]}
    with pytest.raises(rpg_state.RPGStateError, match="matched 0 times"):
        rpg_state.commit_durable(noted, _note_turn(good, bad))
    assert (noted / "characters" / "ilse.md").read_bytes() == before


def test_set_with_a_list_value_on_a_list_key_replaces_the_list(campaign: Path) -> None:
    payload = {
        "operation_id": "t1",
        "expected_continuity_revision": 0,
        "boundary": "ordinary",
        "cause": "Ilse joined.",
        "changes": [{"id": "c", "kind": "scene_progress", "established_delta": "Ilse is here.", "owners": ["current_state.yaml"]}],
        "mutations": [{"path": "current_state.yaml", "ops": [{"op": "set", "values": {"current_scene.present_npcs": ["Ilse"]}}]}],
    }
    assert rpg_state.commit_durable(campaign, payload)["ok"] is True
    assert "- Ilse" in (campaign / "current_state.yaml").read_text(encoding="utf-8") or '"Ilse"' in (
        campaign / "current_state.yaml"
    ).read_text(encoding="utf-8")


def test_set_with_a_scalar_on_a_list_key_is_still_refused(campaign: Path) -> None:
    payload = {
        "operation_id": "t1",
        "expected_continuity_revision": 0,
        "boundary": "ordinary",
        "cause": "Ilse joined.",
        "changes": [{"id": "c", "kind": "scene_progress", "established_delta": "Ilse is here.", "owners": ["current_state.yaml"]}],
        "mutations": [{"path": "current_state.yaml", "ops": [{"op": "set", "values": {"current_scene.present_npcs": "Ilse"}}]}],
    }
    with pytest.raises(rpg_state.RPGStateError, match="is a list"):
        rpg_state.commit_durable(campaign, payload)

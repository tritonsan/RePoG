"""Scene capsule (plugin 0.3.0, component C), on synthetic campaigns only.

Covers full and delta selection, the size caps and their truncation marker,
name matching under each language's case folding (tr, en, de fixtures), the
protected-fact and directive scoping rules, roll receipts, staged curation,
the lint summary, and the hook and CLI entry points, which must never raise.
"""

from __future__ import annotations

import io
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import pytest

import lang_pack
import roll_dice
import scene_capsule
from repog_runtime import runtime_settings


SESSION = "session-1"
DIRECTIVES_HEAD = (
    "# Directives\n\n## Standing Directives\n\n"
    "<!--\ne.g. | D-NNN | global | An example row, not a directive. | OOC | active |\n-->\n\n"
    "| Id | Scope | Directive | Source | Status |\n| --- | --- | --- | --- | --- |\n"
)
KNOWLEDGE = """# Knowledge Boundaries

## Protected Proper Nouns

### The Hollow King

- Fact id: F-007
- Status: GM-only
- NPCs or factions who know: Ilse
- Safe wording before reveal: the old ruler under the hill

### Saltmarsh Pact

- Fact id: F-009
- Status: revealed
- NPCs or factions who know: none

### Red Tithe

- Fact id: `F-011`
- Status: NPC-known, kept from the
  player for now
- NPCs or factions who know: Witness, the Dock Guild
- Companions who know:

### Unnumbered Name

- Fact id:
- Status: GM-only

## NPC And Faction Knowledge

### Witness

- Confirmed fact ids: F-011
- Suspicion fact ids:
- Knows: the courier's face.
"""
LEGACY_NOTE = """# Corran

## Agency Card

- Tier: T3
- Voice rhythm: clipped
- Social tactic: flattery
- Hard boundary: never betrays kin
- Routine and availability: mornings at the forge
- Next move if ignored: leaves town

## Current State (day 22)

Guarding the mill.

## State On Day 72

Back in town; the mill burned.
"""
GLOSSARY = """# Glossary

## Rendering Policy

- Place names: keep the original forms
- Titles and honorifics: Usta follows the name for master craftsmen
- Address forms: NPCs address Mira as "siz" until trust is earned
- Units:

## Terms

| Term | Preferred | Variants | Notes |
| --- | --- | --- | --- |
| span of time | bell | hour | The setting counts bells. |
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(path: Path, text: str | bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text if isinstance(text, bytes) else text.encode("utf-8"))
    return path


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    _write(path, text.replace(old, new, 1))


def _state(campaign: Path, old: str, new: str) -> None:
    _replace(campaign / "current_state.yaml", old, new)


def _present(campaign: Path, *names: str) -> None:
    path = campaign / "current_state.yaml"
    value = json.dumps(list(names), ensure_ascii=False)
    _write(path, re.sub(r"(?m)^(  present_npcs:).*$", lambda match: f"{match.group(1)} {value}", path.read_text(encoding="utf-8")))


def _profile(campaign: Path, extra: str) -> None:
    path = campaign / "play_profile.yaml"
    _write(path, path.read_text(encoding="utf-8") + extra)


def _character(
    campaign: Path,
    stem: str,
    title: str,
    *,
    core: dict[str, str] | None = None,
    now: str | None = None,
    extra: str = "",
) -> Path:
    parts = [f"# {title}\n\nTier: T2\n"]
    if core is not None:
        parts.append("\n## Core\n\n" + "".join(f"- {key}: {value}\n" for key, value in core.items()))
    if now is not None:
        parts.append(f"\n## Now\n\n{now}\n")
    parts.append(extra)
    return _write(campaign / "characters" / f"{stem}.md", "".join(parts))


def _build(
    campaign: Path,
    prompt: str = "",
    *,
    session: str = SESSION,
    full: bool | None = None,
    settings: dict[str, Any] | None = None,
) -> str:
    return scene_capsule.build_capsule(
        campaign,
        prompt,
        session_id=session,
        settings=runtime_settings(campaign) if settings is None else settings,
        full=full,
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


def _names(campaign: Path, text: str) -> list[str]:
    return scene_capsule.names_in_text(campaign, text)


def _roll(campaign: Path, roll_id: str, *, actor: str = "Marcus", axis: str = "street_sense", difficulty: int = 6) -> dict[str, Any]:
    call = {"actor": actor, "axis": axis, "value": 3, "difficulty": difficulty, "stakes": "the bait is seen through"}
    return roll_dice.roll_call(campaign, {"roll_id": roll_id, "die": "1d6", "call": call})


def _runtime(campaign: Path) -> Path:
    return campaign / ".repog-runtime"


# ---------------------------------------------------------------------------
# Full and delta
# ---------------------------------------------------------------------------


def test_full_then_delta_then_full_after_reset(campaign: Path) -> None:
    _present(campaign, "Witness")
    first = _build(campaign, "Who is here?")
    assert not _is_delta(first)
    assert "[cast] in scope: Witness (present)" in first
    assert "[language]" in first

    second = _build(campaign, "Who is here?")
    assert second.splitlines()[1:] == ["Delta: nothing changed since the last capsule."]

    _replace(campaign / "characters" / "witness.md", "Nervous.", "Calmer now.")
    third = _build(campaign, "Who is here?")
    assert "Delta: cast changed; other sections are as last shown." in third
    assert "- Witness (characters/witness.md): changed lines only\n  Current State: Calmer now." in third
    assert "[language]" not in third

    scene_capsule.reset(campaign, SESSION)
    after_reset = _build(campaign, "Who is here?")
    assert not _is_delta(after_reset) and "[cast]" in after_reset
    assert _is_delta(_build(campaign, "Who is here?"))

    assert not _is_delta(_build(campaign, session="other"))
    scene_capsule.reset(campaign)  # no session id: every recorded session
    assert not _is_delta(_build(campaign, session=SESSION))
    assert not _is_delta(_build(campaign, session="other"))


def test_reset_of_an_unknown_session_still_gives_a_full_first_capsule(campaign: Path) -> None:
    scene_capsule.reset(campaign, "fresh")
    assert not _is_delta(_build(campaign, session="fresh"))
    assert _is_delta(_build(campaign, session="fresh"))


def test_scene_change_forces_a_full_capsule(campaign: Path) -> None:
    _build(campaign)
    assert _is_delta(_build(campaign))
    _state(campaign, "scene_id: dock-interview", "scene_id: warehouse-chase")
    changed = _build(campaign)
    assert not _is_delta(changed)
    assert "scene warehouse-chase" in changed.splitlines()[0]
    assert _is_delta(_build(campaign))


def test_every_twelfth_prompt_is_full(campaign: Path) -> None:
    fulls = [number for number in range(1, 26) if not _is_delta(_build(campaign, "Next."))]
    assert fulls == [1, 13, 25]


def test_full_can_be_forced_either_way(campaign: Path) -> None:
    assert _is_delta(_build(campaign, full=False))
    assert not _is_delta(_build(campaign, full=True))
    assert _is_delta(_build(campaign))


def test_sessions_are_counted_separately_and_pruned(campaign: Path) -> None:
    for index in range(scene_capsule.MAX_SESSIONS + 5):
        assert not _is_delta(_build(campaign, session=f"s{index}"))
    state = json.loads((_runtime(campaign) / "capsule_state.json").read_text(encoding="utf-8"))
    assert len(state["sessions"]) == scene_capsule.MAX_SESSIONS
    assert "s0" not in state["sessions"]
    assert f"s{scene_capsule.MAX_SESSIONS + 4}" in state["sessions"]


def test_a_delta_shows_only_changed_lines_with_the_protected_ones(campaign: Path) -> None:
    _character(
        campaign,
        "n1",
        "Sedra Vold",
        core={"Status": "alive", "Kin": "Tavin (brother, dead)", "Role": "ferrywoman"},
        now="Waits at the landing.",
    )
    _write(campaign / "knowledge_boundaries.md", "# Knowledge Boundaries\n\n## NPC Knowledge\n\n### Sedra Vold\n\n- Knows: the tide tables.\n")
    _present(campaign, "Sedra Vold")
    assert "  Role: ferrywoman" in _build(campaign)
    _replace(campaign / "characters" / "n1.md", "Waits at the landing.", "Rows across at dusk.")
    delta = _build(campaign)
    assert _block(delta, "Sedra Vold") == [
        "- Sedra Vold (characters/n1.md): changed lines only",
        "  Status: alive",
        "  Kin: Tavin (brother, dead)",
        "  Now: Rows across at dusk.",
    ]
    assert "Role" not in delta and "Knowledge" not in delta


def test_a_line_removed_from_a_note_is_marked_once(campaign: Path) -> None:
    _character(campaign, "n1", "Sedra Vold", core={"Status": "alive", "Role": "ferrywoman"}, now="Waits at the landing.")
    _present(campaign, "Sedra Vold")
    _build(campaign)
    _replace(campaign / "characters" / "n1.md", "- Role: ferrywoman\n", "")
    assert "\n  Role: (no longer recorded)" in _build(campaign)
    assert _build(campaign).splitlines()[1:] == ["Delta: nothing changed since the last capsule."]


def test_someone_who_leaves_and_returns_unchanged_costs_one_roster_line(campaign: Path) -> None:
    _character(campaign, "n1", "Sedra Vold", core={"Status": "alive"}, now="Waits at the landing.")
    assert "- Sedra Vold (characters/n1.md)" in _build(campaign, "I hail Sedra.")
    _build(campaign, "I wait.")  # she was named last turn, so she is still in scope
    assert "[cast] nobody present or named." in _build(campaign, "I wait.")
    assert _build(campaign, "Sedra, a word.").splitlines()[1:] == [
        "Delta: cast changed; other sections are as last shown.",
        "[cast] in scope: Sedra Vold (mentioned)",
    ]


def test_records_outlive_a_periodic_full_capsule_and_expire_after_twelve_prompts(campaign: Path) -> None:
    _character(campaign, "n1", "Sedra Vold", core={"Status": "alive"}, now="Waits at the landing.")
    for _ in range(9):
        _build(campaign, "I wait.")  # prompts 1 to 9
    assert "- Sedra Vold (characters/n1.md)" in _build(campaign, "I hail Sedra.")  # prompt 10
    _build(campaign, "I wait.")  # 11: still in scope, nothing new
    _build(campaign, "I wait.")  # 12: out of scope
    assert not _is_delta(_build(campaign, "I wait."))  # 13: the periodic full capsule, without her
    back = _build(campaign, "Sedra, again.")  # 14: her briefing from prompt 10 is still in context
    assert "Sedra Vold (mentioned)" in back and "- Sedra Vold (" not in back
    for _ in range(12):
        _build(campaign, "I wait.")  # 15 to 26
    assert "- Sedra Vold (characters/n1.md)\n" in _build(campaign, "Sedra, at last.")  # 27: briefed whole again


def test_blocks_deferred_by_a_full_capsule_after_a_reset_follow_in_the_next_delta(campaign: Path) -> None:
    titles = [f"Keeper {letter}" for letter in "ABCDEFGH"]
    for index, title in enumerate(titles):
        _character(campaign, f"keeper_{index}", title, core={"Status": "alive", "Kin": "cousin (alive), " * 35})
    _present(campaign, *titles)
    full = _build(campaign)
    late = [title for title in titles if f"- {title} (characters/" not in full]
    assert late and "more in scope, shown on the next prompt" in full
    delta = _build(campaign)
    assert all(f"- {title} (characters/" in delta for title in late)

    scene_capsule.reset(campaign, SESSION)  # a compaction: the context lost every earlier capsule
    again = _build(campaign)
    assert not _is_delta(again) and all(f"- {title} (characters/" not in again for title in late)
    after = _build(campaign)
    assert all(f"- {title} (characters/" in after for title in late)


def test_a_reset_writes_nothing_for_sessions_it_does_not_know(campaign: Path) -> None:
    scene_capsule.reset(campaign, "never-seen")
    scene_capsule.reset(campaign)
    assert not _runtime(campaign).exists()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------


def test_header_names_revision_time_place_scene_and_persistence(campaign: Path) -> None:
    assert _build(campaign).splitlines()[0] == (
        "RePoG capsule — rev 0 · day 1 phase evening · old_dock · scene dock-interview · "
        "persistence: narrate_then_commit"
    )
    _profile(campaign, "runtime:\n  persistence_order: commit_then_narrate\n")
    assert _build(campaign, session="other").splitlines()[0].endswith("persistence: commit_then_narrate")


@pytest.mark.parametrize(
    ("policy", "turns", "due"),
    [
        ("scene_checkpoint_or_5_durable", 3, False),
        ("scene_checkpoint_or_5_durable", 4, True),
        ("scene_checkpoint_or_5_durable", 6, True),
        ("every_durable", 0, True),
        ("scene_checkpoint_only", 40, False),
    ],
)
def test_full_distill_due_line(campaign: Path, policy: str, turns: int, due: bool) -> None:
    _replace(campaign / "play_profile.yaml", "scene_checkpoint_or_5_durable", policy)
    _state(campaign, "durable_turns_since_distill: 0", f"durable_turns_since_distill: {turns}")
    text = _build(campaign)
    assert ("Full distill is due after this turn's commit." in text) is due
    assert ("Full distill is due after this turn's commit." in _build(campaign)) is due  # deltas keep the header


# ---------------------------------------------------------------------------
# Cast
# ---------------------------------------------------------------------------


def test_core_fields_relationship_and_knowledge_lines(campaign: Path) -> None:
    _character(
        campaign,
        "edric",
        "Edric",
        core={
            "Status": "alive",
            "Pronouns and address": 'he; apprentices call him "Usta"',
            "Kin": "Ilse (sister, dead), Bram (father, alive)",
            "Role": "miller",
            "Home": "the mill",
            "Speaks": "Common, blunt; calls Mira by name",
            "Aliases": "the Miller",
        },
        now="Back in town; the mill burned.",
    )
    _write(
        campaign / "relationship_map.md",
        "# Relationship Map\n\nAs of revision: 0\n\n"
        "| From | Direction | To | Relation | Status | Trust / debt / tension | Knowledge asymmetry |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n"
        f"| Mira | -> | Edric | ally | active | {'owes a favour ' * 20}| none |\n"
        "| Edric | -> | Courier | fears | active | debt | none |\n",
    )
    _write(campaign / "knowledge_boundaries.md", "# Knowledge Boundaries\n\n## NPC Knowledge\n\n### Edric\n\n- Knows: who set the fire.\n")
    block = _block(_build(campaign, "I ask the Miller about the fire."), "Edric")
    assert block[:8] == [
        "- Edric (characters/edric.md)",
        "  Status: alive",
        '  Pronouns and address: he; apprentices call him "Usta"',
        "  Kin: Ilse (sister, dead), Bram (father, alive)",
        "  Role: miller",
        "  Home: the mill",
        "  Speaks: Common, blunt; calls Mira by name",
        "  Now: Back in town; the mill burned.",
    ]
    relation = block[8]
    assert relation.startswith("  Rel: Mira -> Edric: ally; active; owes a favour")
    assert relation.endswith("…") and len(relation.split("; ", 2)[2]) <= scene_capsule.RELATION_CHARS
    assert block[9:] == ["  Knowledge: Knows: who set the fire."]
    assert "Tier:" not in "\n".join(block)  # Core replaces the legacy lines


def test_legacy_note_falls_back_to_tier_agency_card_and_last_state(campaign: Path) -> None:
    _write(campaign / "characters" / "corran.md", LEGACY_NOTE)
    _present(campaign, "Corran")
    assert _block(_build(campaign), "Corran") == [
        "- Corran (characters/corran.md)",
        "  Tier: T3",
        "  Voice rhythm: clipped",
        "  Social tactic: flattery",
        "  Hard boundary: never betrays kin",
        "  Routine and availability: mornings at the forge",
        "  State On Day 72: Back in town; the mill burned.",
    ]


def test_now_section_wins_over_stacked_legacy_sections(campaign: Path) -> None:
    _character(campaign, "edric", "Edric", now="At the gate.", extra="\n## Current State (day 22)\n\nGuarding the mill.\n")
    text = _build(campaign, "Edric?")
    assert "  Now: At the gate." in text and "Guarding the mill" not in text


def test_unfilled_template_values_are_not_shown(campaign: Path) -> None:
    template = (Path(scene_capsule.__file__).resolve().parents[1] / "templates" / "campaign" / "characters" / "_template.md").read_text(encoding="utf-8")
    _write(campaign / "characters" / "tess.md", template.replace("# Character Name", "# Tess", 1))
    text = _build(campaign, "Tess?")
    assert "- Tess (characters/tess.md)" in text
    assert "alive | dead" not in text and "T1/T2/T3" not in text


def test_present_ids_resolve_to_notes_and_unknown_names_stay_listed(campaign: Path) -> None:
    _character(campaign, "harbor_warden", "Teodor Vask")
    _present(campaign, "npc_witness", "harbor_warden", "Gate guard")
    text = _build(campaign)
    assert "[cast] in scope: Witness (present), Teodor Vask (present), Gate guard (present)" in text
    assert "- Witness (characters/witness.md)" in text
    assert "- Gate guard (no note)" in text


def test_cast_is_capped_at_eight_in_scope_order(campaign: Path) -> None:
    titles = [f"Keeper {letter}" for letter in "ABCDEFGHIJ"]
    for index, title in enumerate(titles):
        _character(campaign, f"keeper_{index}", title)
    _present(campaign, *titles[:3])
    text = _build(campaign, " ".join(reversed(titles)))
    roster = text.splitlines()[1]
    expected = [f"{title} (present)" for title in titles[:3]] + [f"{title} (mentioned)" for title in reversed(titles[3:])][:5]
    assert roster == "[cast] in scope: " + ", ".join(expected)


def test_dead_kin_line_survives_every_cut_verbatim(campaign: Path) -> None:
    kin = "Ilse (sister, dead), Bram (father, alive), Ayşe (annesi, öldü)"
    titles = ["Edric"] + [f"Keeper {letter}" for letter in "ABCDEFG"]
    knowledge = "".join(f"### {title}\n\n- Knows: {'a long rumour about the river ' * 20}\n\n" for title in titles)
    _write(campaign / "knowledge_boundaries.md", f"# Knowledge Boundaries\n\n## NPC Knowledge\n\n{knowledge}")
    for index, title in enumerate(titles):
        core = {"Status": "alive", "Role": "watcher " * 30, "Speaks": "plainly " * 30}
        if title == "Edric":
            core["Kin"] = kin
        _character(campaign, f"n{index}", title, core=core, now="Watches the river. " * 100)
    _present(campaign, *titles)

    full = _build(campaign)
    assert len(full) <= scene_capsule.FULL_MAX
    assert f"\n  Kin: {kin}\n" in full
    assert "…" in full
    assert all(f"- {title} (characters/" in full for title in titles)

    for index in range(len(titles)):
        _replace(campaign / "characters" / f"n{index}.md", "Watches the river.", "Walks the road.")
    delta = _build(campaign)
    assert _is_delta(delta) and len(delta) <= scene_capsule.DELTA_MAX
    assert f"\n  Kin: {kin}" in delta  # a changed block repeats its protected lines
    assert "more lines on the next prompt" in delta  # a delta never cuts a line; it waits whole

    shown = delta.count("\n  Now: Walks the road.")
    for _ in range(len(titles)):
        text = _build(campaign)
        assert len(text) <= scene_capsule.DELTA_MAX
        shown += text.count("\n  Now: Walks the road.")
        if "Delta: nothing changed" in text:
            break
    assert shown == len(titles)  # every changed line arrives, each exactly once


def test_blocks_that_do_not_fit_a_delta_follow_on_the_next_prompts(campaign: Path) -> None:
    titles = [f"Keeper {letter}" for letter in "ABCDEFGH"]
    for index, title in enumerate(titles):
        _character(campaign, f"keeper_{index}", title, core={"Status": "alive", "Kin": "cousin (alive), " * 25})
    _present(campaign, *titles)
    full = _build(campaign)
    assert all(f"- {title} (characters/" in full for title in titles)

    for index in range(len(titles)):
        _replace(campaign / "characters" / f"keeper_{index}.md", "cousin (alive)", "cousin (dead)")
    batches: list[list[str]] = []
    for _ in range(len(titles)):
        text = _build(campaign)
        assert len(text) <= scene_capsule.DELTA_MAX
        batch = [title for title in titles if f"- {title} (characters/" in text]
        if not batch:
            assert text.splitlines()[1] == "Delta: nothing changed since the last capsule."
            break
        if len(batches) == 0:
            assert "more in scope, shown on the next prompt" in text
        batches.append(batch)
    assert 2 <= len(batches) < len(titles)
    assert sorted(title for batch in batches for title in batch) == titles  # each changed block exactly once


def test_a_dated_legacy_state_keeps_its_heading_and_the_newest_wins(campaign: Path) -> None:
    _write(
        campaign / "characters" / "n1.md",
        "# Orla Penn\n\n## Agency Card\n\n- Tier: T2\n\n"
        "## State On Day 300 (current; overrides the older state below)\n\nRuns the mill alone.\n\n"
        "## State On Day 120\n\nApprentice at the mill.\n",
    )
    _present(campaign, "Orla Penn")
    text = _build(campaign)
    assert "  State On Day 300: Runs the mill alone." in text  # never passed off as "Now"
    assert "Apprentice" not in text


def test_an_unfilled_now_section_falls_back_to_the_legacy_state(campaign: Path) -> None:
    _write(
        campaign / "characters" / "n1.md",
        "# Orla Penn\n\n## Core\n\n- Status: alive\n\n## Now\n\n<!--\nOne short paragraph.\n-->\n\n"
        "## Current State (day 41)\n\nMends nets by the weir.\n- Owes the miller a week of work.\n",
    )
    _present(campaign, "Orla Penn")
    assert "  Current State (day 41): Mends nets by the weir. Owes the miller a week of work." in _build(campaign)


def test_each_bullet_of_a_long_state_keeps_its_head(campaign: Path) -> None:
    _write(
        campaign / "characters" / "n1.md",
        "# Orla Penn\n\n## Agency Card\n\n- Tier: T2\n\n## Current State (day 90)\n\n"
        "This section folds the older notes together.\n\n"
        f"- Who she is now: {'the ferry keeper of the lower crossing, ' * 6}\n"
        f"- Her work: {'mends nets and keeps the tolls, ' * 6}\n"
        "- Her mother: died in the flood; buried by the weir.\n"
        f"- Plans: {'to buy a second boat, ' * 6}\n",
    )
    _present(campaign, "Orla Penn")
    line = next(line for line in _build(campaign).splitlines() if line.startswith("  Current State (day 90): "))
    assert len(line) <= len("  Current State (day 90): ") + scene_capsule.NOW_CHARS
    assert "; Her mother: died in the flood" in line  # a fact in a later bullet survives the cut
    assert "Who she is now: the ferry keeper" in line and "Her work: mends nets" in line


@pytest.mark.parametrize("limit", range(12, 95, 3))
def test_a_cut_never_separates_an_item_from_its_bracketed_qualifier(limit: int) -> None:
    text = "Confirmed fact ids: F-011 (her own part; not the informer); F-007; PC-1 to PC-9 (the road)"
    cut = scene_capsule._safe_clip(text, limit)
    assert len(cut) <= limit and (cut == text or cut.endswith("…"))
    if "F-011" in cut:
        assert "F-011 (her own part; not the informer)" in cut
    assert cut.count("(") == cut.count(")")


def test_a_long_kin_line_is_cut_between_relatives_only(campaign: Path) -> None:
    kin = "; ".join(f"Relative {index} (cousin, {'dead' if index % 2 else 'alive'})" for index in range(40))
    _character(campaign, "n1", "Orla Penn", core={"Status": "alive", "Kin": kin})
    _present(campaign, "Orla Penn")
    line = next(line for line in _build(campaign).splitlines() if line.startswith("  Kin: "))
    assert line.endswith("…") and len(line) <= len("  Kin: ") + scene_capsule.KIN_CHARS
    for entry in line[len("  Kin: ") : -1].split("; "):
        assert re.fullmatch(r"Relative \d+ \(cousin, (dead|alive)\)", entry)


def test_the_knowledge_line_keeps_the_head_of_every_field(campaign: Path) -> None:
    confirmed = ", ".join(f"PC-{number:03d}" for number in range(120))
    _write(
        campaign / "knowledge_boundaries.md",
        "# Knowledge Boundaries\n\n## NPC Knowledge\n\n### Witness\n\n"
        f"- Confirmed fact ids: {confirmed}\n- Suspicion fact ids: none\n"
        "- Explicitly unknown fact ids: F-009 (the courier's name)\n- Must-not-imply fact ids: F-010\n",
    )
    _present(campaign, "Witness")
    line = next(line for line in _build(campaign).splitlines() if line.startswith("  Knowledge: "))
    assert len(line) <= len("  Knowledge: ") + scene_capsule.KNOWLEDGE_CHARS
    assert line.startswith("  Knowledge: Confirmed fact ids: PC-000, PC-001")
    assert "; Explicitly unknown fact ids: F-009 (the courier's name); " in line
    assert line.endswith("; Must-not-imply fact ids: F-010")


def test_a_long_relationship_cell_shows_its_summary_and_newest_change(campaign: Path) -> None:
    history = "; ".join(f"event {number} on day {number * 10}" for number in range(1, 30))
    _write(
        campaign / "relationship_map.md",
        "# Relationship Map\n\n| From | Direction | To | Relation | Status | Trust / debt / tension |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        f"| Mira | <-> | Witness | uneasy allies | active | wary trust; {history}; she paid the debt on day 400 |\n",
    )
    _present(campaign, "Witness")
    line = next(line for line in _build(campaign).splitlines() if line.startswith("  Rel: "))
    assert line.startswith("  Rel: Mira <-> Witness: uneasy allies; active; wary trust; …; ")
    assert line.endswith("; she paid the debt on day 400")


def test_a_present_member_without_a_note_shows_relation_and_knowledge(campaign: Path) -> None:
    _write(
        campaign / "relationship_map.md",
        "# Relationship Map\n\n| From | Direction | To | Relation | Status | Trust / debt / tension |\n"
        "| --- | --- | --- | --- | --- | --- |\n| Mira | <-> | Hesk | master and paid man | active | loyal |\n",
    )
    _write(campaign / "knowledge_boundaries.md", "# Knowledge Boundaries\n\n## NPC Knowledge\n\n### Hesk\n\n- Confirmed fact ids: F-002\n")
    _present(campaign, "Hesk")
    assert _block(_build(campaign), "Hesk") == [
        "- Hesk (no note)",
        "  Rel: Mira <-> Hesk: master and paid man; active; loyal",
        "  Knowledge: Confirmed fact ids: F-002",
    ]


def test_a_knowledge_heading_for_someone_else_is_not_used(campaign: Path) -> None:
    _character(campaign, "n1", "Tobin")
    _write(campaign / "knowledge_boundaries.md", "# Knowledge Boundaries\n\n## NPC Knowledge\n\n### Tobin Marsh\n\n- Knows: the smuggler's route.\n")
    assert "smuggler" not in _build(campaign, "Tobin?")
    _write(campaign / "knowledge_boundaries.md", "# Knowledge Boundaries\n\n## NPC Knowledge\n\n### Tobin (the smith)\n\n- Knows: the forge debts.\n")
    assert "  Knowledge: Knows: the forge debts." in _build(campaign, "Tobin?", full=True)


def test_a_note_with_crlf_line_ends_and_stray_bytes_still_shows(campaign: Path) -> None:
    note = (
        b"# Orla Penn\r\n\r\n## Core\r\n\r\n- Status: dead\r\n- Aliases: the Weir Widow\r\n\r\n"
        b"## Now\r\n\r\nBuried by the weir, caf\xe9 owner.\r\n"
    )
    _write(campaign / "characters" / "n1.md", note)  # a cp1252 byte, as an editor on Windows may save
    text = _build(campaign, "I ask the weir widow.")
    assert "[cast] in scope: Orla Penn (mentioned)" in text  # the CRLF Core block still gives the alias
    assert "  Status: dead" in text and "  Now: Buried by the weir, caf� owner." in text


# ---------------------------------------------------------------------------
# Name matching
# ---------------------------------------------------------------------------


def test_turkish_folding_keeps_dotted_and_dotless_i_apart(campaign: Path) -> None:
    _profile(campaign, "narration:\n  language: tr\n")
    # Stems too short to match on their own, so only the titles decide.
    for stem, title in (("c1", "İrem"), ("c2", "Ilse"), ("c3", "Halvar")):
        _character(campaign, stem, title)
    assert _names(campaign, "irem nerede?") == ["İrem"]
    assert _names(campaign, "İREM'i gördün mü?") == ["İrem"]
    assert _names(campaign, "İLSE geldi mi?") == []  # İ folds to i, Ilse's I folds to ı
    assert _names(campaign, "ILSE geldi mi?") == ["Ilse"]
    assert _names(campaign, "HALVAR'ın oğlu geldi") == ["Halvar"]
    assert _names(campaign, "Halvarlar geldi") == []  # not a whole word
    text = _build(campaign, "irem ile HALVAR konuşuyor.")
    assert "[cast] in scope: İrem (mentioned), Halvar (mentioned)" in text


def test_an_ascii_file_stem_matches_a_name_typed_without_turkish_letters(campaign: Path) -> None:
    _profile(campaign, "narration:\n  language: tr\n")
    _character(campaign, "isik", "Işık")
    _character(campaign, "ilse", "Ilse")
    assert _names(campaign, "Işık nerede?") == ["Işık"]
    assert _names(campaign, "isik nerede?") == ["Işık"]
    assert _names(campaign, "İLSE geldi mi?") == ["Ilse"]  # the stem `ilse` folds the same as İLSE


def test_default_folding_matches_a_dotted_capital_i(campaign: Path) -> None:
    _profile(campaign, "narration:\n  language: en\n")
    _character(campaign, "ilse", "Ilse")
    assert _names(campaign, "İLSE came back?") == ["Ilse"]
    assert _names(campaign, "Did ilse come back?") == ["Ilse"]


def test_german_folding_matches_sharp_s_and_umlauts(campaign: Path) -> None:
    _profile(campaign, "narration:\n  language: de\n")
    _character(campaign, "grossmann", "Großmann")
    _character(campaign, "juergen", "Jürgen")
    assert _names(campaign, "Wo ist GROSSMANN? Und jürgen?") == ["Großmann", "Jürgen"]


def test_aliases_stems_and_short_names(campaign: Path) -> None:
    _character(campaign, "harbor_warden", "Teodor Vask", core={"Status": "alive", "Aliases": "the Warden, Old Teo"})
    _character(campaign, "al", "Al")
    assert _names(campaign, "I greet the warden.") == ["Teodor Vask"]
    assert _names(campaign, "Is old teo here?") == ["Teodor Vask"]
    assert _names(campaign, "Ask the harbor warden.") == ["Teodor Vask"]
    assert _names(campaign, "Al waits by the wall.") == []  # names under three letters are ignored
    _present(campaign, "Al")
    assert "[cast] in scope: Al (present)" in _build(campaign)  # the scene list still resolves them


def test_place_and_faction_names_are_matched_too(campaign: Path) -> None:
    _write(campaign / "places" / "old_dock.md", "# Old Dock\n")
    _write(campaign / "factions" / "dock_guild.md", "# Dock Guild\n")
    _write(campaign / "places" / "_template.md", "# Place Name\n")
    assert _names(campaign, "The Dock Guild meets at the old dock.") == ["Dock Guild", "Old Dock"]
    assert _names(campaign, "Place Name") == []


def test_prompt_names_carry_over_exactly_one_turn(campaign: Path) -> None:
    _character(campaign, "edric", "Edric")
    assert "[cast] in scope: Edric (mentioned)" in _build(campaign, "I call Edric over.")
    settings = runtime_settings(campaign)
    preview, _ = scene_capsule.compose(campaign, "What does he say?", session_id=SESSION, settings=settings, full=True)
    assert "[cast] in scope: Edric (mentioned)" in preview  # still in scope one turn later
    second = _build(campaign, "What does he say?")
    assert second.splitlines()[1:] == ["Delta: nothing changed since the last capsule."]  # same cast, nothing resent
    third = _build(campaign, "I wait.")
    assert "Edric" not in third and "[cast] nobody present or named." in third


def test_remember_names_adds_reply_names_to_the_next_scope(campaign: Path) -> None:
    _character(campaign, "edric", "Edric")
    _build(campaign, "Hello.")
    scene_capsule.remember_names(campaign, SESSION, ["Edric", "", "x" * 200, 7])  # type: ignore[list-item]
    text = _build(campaign, "And then?")
    assert "[cast] in scope: Edric (mentioned)" in text
    assert "- Edric (characters/edric.md)" in text
    assert _names(campaign, "Edric and the witness talk.") == ["Edric", "Witness"]


def test_first_names_match_with_turkish_casing_and_suffixes(campaign: Path) -> None:
    _profile(campaign, "narration:\n  language: tr\n")
    # Stems too short to match on their own, so only titles and given names decide.
    _character(campaign, "n1", "Sedra Vold")
    _character(campaign, "n2", "Tavin Vold")
    _character(campaign, "n3", "Nessa of Brenmoor")
    _character(campaign, "n4", "Lord Oren Vold", extra="\nThe lord of the crossing; every lord owes him a toll.\n")
    assert _names(campaign, "Sedra'nın yanına gidiyorum.") == ["Sedra Vold"]
    assert _names(campaign, "NESSA'ya sordum.") == ["Nessa of Brenmoor"]
    assert _names(campaign, "Lord Oren'e haber gönder.") == ["Lord Oren Vold"]
    assert _names(campaign, "Vold'lar geldi.") == []  # a surname two notes share names nobody
    assert _names(campaign, "Lord geldi.") == []  # the notes write "lord" in lower case: a title, not a name
    text = _build(campaign, "Tavin ve Sedra ile konuşuyorum.")
    assert "[cast] in scope: Tavin Vold (mentioned), Sedra Vold (mentioned)" in text


def test_given_names_skip_the_player_name_and_common_words(campaign: Path) -> None:
    _profile(campaign, "narration:\n  language: en\n")
    _character(campaign, "n1", "Mira Holt")  # shares a name with the player character, Mira
    _character(campaign, "n2", "Will Arden")
    assert _names(campaign, "Mira looks around.") == []
    assert _names(campaign, "Holt nods.") == ["Mira Holt"]
    assert _names(campaign, "I will wait for Arden.") == ["Will Arden"]
    assert _names(campaign, "Will is late.") == []  # an English common word is never a name in free text
    assert _names(campaign, "Will Arden is late.") == ["Will Arden"]  # the full name still is


def test_a_german_given_name_matches_in_capitals(campaign: Path) -> None:
    _profile(campaign, "narration:\n  language: de\n")
    _character(campaign, "n1", "Jürgen Falk")
    assert _names(campaign, "Wo ist JÜRGEN?") == ["Jürgen Falk"]
    assert _names(campaign, "Frag Falk.") == ["Jürgen Falk"]


def test_reply_names_never_overwrite_the_capsule_state(campaign: Path) -> None:
    _character(campaign, "n1", "Sedra Vold")
    _build(campaign, "Hello.")
    scene_capsule.reset(campaign, SESSION)  # SessionStart after a compaction
    state = _runtime(campaign) / "capsule_state.json"
    before = state.read_bytes()
    scene_capsule.remember_names(campaign, SESSION, ["Sedra Vold"])  # the asynchronous Stop hook, a moment late
    assert state.read_bytes() == before
    text = _build(campaign, "And then?")
    assert not _is_delta(text) and "[cast] in scope: Sedra Vold (mentioned)" in text
    assert "[cast] nobody present or named." in _build(campaign, "Later.")  # a reply name is used once

    scene_capsule.remember_names(campaign, SESSION, ["Sedra Vold"])
    scene_capsule.remember_names(campaign, SESSION, ["Witness"])  # two replies before the next prompt
    text = _build(campaign, "Go on.")
    assert "Sedra Vold (mentioned)" in text and "Witness (mentioned)" in text
    (_runtime(campaign) / "capsule_names.json").unlink()  # the runtime files may be deleted at any time
    _build(campaign, "Pause.")
    scene_capsule.remember_names(campaign, SESSION, ["Sedra Vold"])
    assert "Sedra Vold (mentioned)" in _build(campaign, "Next.")


# ---------------------------------------------------------------------------
# Secrets and directives
# ---------------------------------------------------------------------------


def test_secrets_list_only_fact_ids_the_cast_does_not_hold(campaign: Path) -> None:
    _write(campaign / "knowledge_boundaries.md", KNOWLEDGE)
    _character(campaign, "ilse", "Ilse")
    _present(campaign, "Witness")
    text = _build(campaign, "Ilse arrives.")
    assert "[secrets]\n- Witness: not a holder of F-007\n- Ilse: not a holder of F-011" in text
    for secret in ("Hollow King", "Saltmarsh", "Red Tithe", "old ruler", "Unnumbered", "F-009"):
        assert secret not in text
    assert "  Knowledge: Confirmed fact ids: F-011; Knows: the courier's face." in text


def test_secrets_clear_in_a_delta_when_the_cast_holds_everything(campaign: Path) -> None:
    _write(campaign / "knowledge_boundaries.md", KNOWLEDGE)
    _character(campaign, "ilse", "Ilse")
    assert "- Ilse: not a holder of F-011" in _build(campaign, "Ilse arrives.")
    _replace(campaign / "knowledge_boundaries.md", "Witness, the Dock Guild", "Witness, Ilse")
    assert "[secrets] nothing to guard for this cast." in _build(campaign, "Ilse stays.")


HOLDERS = """# Knowledge Boundaries

## Protected Proper Nouns

### The Drowned Bell

- Fact id: F-001
- Status: GM-only
- NPCs or factions who know: Kel; the ferrymen

### The Second Ledger

- Fact id: F-002
- Status: PC-known
- NPCs or factions who know: none

### The Weir Debt

- Fact id: F-003
- Status: NPC-known
- NPCs or factions who know: none recorded

## NPC Knowledge

### Dara Venn

- Confirmed fact ids: F-003 (in part)
"""


def test_a_first_name_or_the_member_s_own_confirmed_ids_make_a_holder(campaign: Path) -> None:
    _write(campaign / "knowledge_boundaries.md", HOLDERS)
    _character(campaign, "n1", "Kel Marrow")
    _character(campaign, "n2", "Dara Venn")
    text = _build(campaign, "Kel and Dara wait.")
    assert "- Kel Marrow: not a holder of F-003, F-002" in text  # facts the player character lacks come first
    assert "- Dara Venn: not a holder of F-001, F-002" in text
    for secret in ("Drowned", "Second Ledger", "Weir Debt", "ferrymen"):
        assert secret not in text


def test_a_common_word_given_name_still_names_a_holder(campaign: Path) -> None:
    _profile(campaign, "narration:\n  language: tr\n")
    _write(campaign / "knowledge_boundaries.md", HOLDERS.replace("Kel; the ferrymen", "Kara; the ferrymen"))
    _character(campaign, "n1", "Kara Lisk")
    assert _names(campaign, "Kara bulutlar toplanıyor.") == []  # "kara" is a Turkish common word
    text = _build(campaign, "Lisk geldi.")
    assert "- Kara Lisk: not a holder of F-003, F-002" in text  # yet the holder list's "Kara" is her


def test_secret_lines_are_diffed_per_member_and_never_cut_inside_an_id(campaign: Path) -> None:
    facts = "".join(f"### Name {number}\n\n- Fact id: F-{number:03d}\n- Status: GM-only\n\n" for number in range(40))
    _write(campaign / "knowledge_boundaries.md", f"# Knowledge Boundaries\n\n## Protected Proper Nouns\n\n{facts}")
    _character(campaign, "n1", "Sedra Vold")
    _character(campaign, "n2", "Tavin Vold")
    _present(campaign, "Witness")
    first = _build(campaign, "Sedra waits.")
    assert "- Witness: not a holder of F-000" in first and "- Sedra Vold: not a holder of F-000" in first
    delta = _build(campaign, "Tavin arrives.")
    lines = [line for line in delta.splitlines() if "not a holder of" in line]
    assert [line.split(":")[0] for line in lines] == ["- Tavin Vold"]  # unchanged members are not repeated
    assert re.fullmatch(r"- Tavin Vold: not a holder of (F-\d{3}, ){11}F-\d{3} \(\+28 more\)", lines[0])
    tight = scene_capsule._secret_line("Sedra Vold", [f"F-{number:03d}" for number in range(40)], 60)
    assert len(tight) <= 60 and re.fullmatch(r"- Sedra Vold: not a holder of (F-\d{3}, )*F-\d{3} \(\+\d+ more\)", tight)


def test_directive_scoping_global_scene_entity_and_place(campaign: Path) -> None:
    _write(campaign / "places" / "old_dock.md", "# Old Dock\n")
    _write(campaign / "places" / "harbor.md", "# Harbor\n")
    _write(campaign / "factions" / "dock_guild.md", "# Dock Guild\n")
    rows = [
        ("D-001", "global", "Keep replies short.", "active"),
        ("D-002", "scene:dock-interview", "Mention gulls only when they matter.", "active"),
        ("D-003", "scene:night-market", "Market noise stays low.", "active"),
        ("D-004", "entity:Witness", "The witness speaks formally.", "active"),
        ("D-005", "entity:Edric", "Edric never jokes.", "active"),
        ("D-006", "entity:Old Dock", "The dock smells of tar.", "active"),
        ("D-007", "entity:Harbor", "Ships stay offshore.", "active"),
        ("D-008", "entity:Dock Guild", "Guild members wear grey.", "active"),
        ("D-009", "global", "A retired rule.", "retired"),
        ("D-010", "weather:rain", "An unknown scope.", "active"),
    ]
    table = "".join(f"| {row[0]} | {row[1]} | {row[2]} | OOC request | {row[3]} |\n" for row in rows)
    _write(campaign / "directives.md", DIRECTIVES_HEAD + table)
    _present(campaign, "Witness")

    def shown(prompt: str) -> list[str]:
        return re.findall(r"(?m)^- (D-\d{3}) ", _build(campaign, prompt, full=True))

    # The witness is present, the dock is the current location, the harbor is named.
    assert shown("I look toward the harbor.") == ["D-007", "D-006", "D-004", "D-002", "D-001"]
    # A named faction joins; the harbor named last turn stays in scope for one more prompt.
    assert shown("The Dock Guild sends word.") == ["D-008", "D-007", "D-006", "D-004", "D-002", "D-001"]
    assert shown("I wait.") == ["D-008", "D-006", "D-004", "D-002", "D-001"]
    assert shown("I wait.") == ["D-006", "D-004", "D-002", "D-001"]
    text = _build(campaign, "Edric?", full=True)
    assert "- D-008" not in text and "- D-005" not in text  # no Edric note: nobody by that name is in scope
    assert "- D-006 (entity:Old Dock): The dock smells of tar." in text
    for hidden in ("D-003", "D-009", "D-010", "D-NNN"):
        assert hidden not in text


def test_directives_are_capped_at_twelve_newest_first(campaign: Path) -> None:
    table = "".join(f"| D-{number:03d} | global | Rule {number}. | OOC | active |\n" for number in range(1, 16))
    _write(campaign / "directives.md", DIRECTIVES_HEAD + table)
    shown = re.findall(r"(?m)^- (D-\d{3}) \(global\)", _build(campaign))
    assert shown == [f"D-{number:03d}" for number in range(15, 3, -1)]


# ---------------------------------------------------------------------------
# Language, lint, rolls, curation
# ---------------------------------------------------------------------------


def test_language_section_appears_in_full_capsules_only(campaign: Path) -> None:
    _profile(campaign, "narration:\n  language: tr\n")
    _write(campaign / "glossary.md", GLOSSARY)
    full = _build(campaign)
    assert "[language] tr (configured)" in full
    assert lang_pack.load_pack("tr")["card"][:60] in full
    assert "Titles and honorifics: Usta follows the name for master craftsmen" in full
    assert 'Address forms: NPCs address Mira as "siz" until trust is earned' in full
    assert "Place names" not in full
    assert "[language]" not in _build(campaign)


def test_auto_language_comes_from_the_lint_detection_or_a_long_prompt(campaign: Path) -> None:
    _write(_runtime(campaign) / "lint_last.json", json.dumps({"summary": "", "language": "de"}))
    assert "[language] de (detected)" in _build(campaign)
    (_runtime(campaign) / "lint_last.json").unlink()
    prompt = "Ben de onu gördüm ama o bana hiçbir şey söylemedi ve sonra gitti."
    assert "[language] tr (detected)" in _build(campaign, prompt, session="other")
    assert "[language] tr (detected)" in _build(campaign, "Evet.", session="other", full=True)  # remembered
    assert "[language] auto (not detected yet)" in _build(campaign, "Evet.", session="third")


def test_a_language_detected_after_the_first_prompt_reaches_the_next_delta_once(campaign: Path) -> None:
    assert "[language] auto (not detected yet)" in _build(campaign, "Merhaba.")
    _write(_runtime(campaign) / "lint_last.json", json.dumps({"summary": "", "language": "tr"}))
    delta = _build(campaign, "Devam.")
    assert _is_delta(delta) and "[language] tr (detected)" in delta
    assert lang_pack.load_pack("tr")["card"][:60] in delta
    assert "[language]" not in _build(campaign, "Devam.")


def test_lint_summary_is_shown_once_per_reply(campaign: Path) -> None:
    path = _runtime(campaign) / "lint_last.json"
    summary = 'Last reply: 3x "bir an" (cap 1); opening restates the Player\'s words.'
    _write(path, json.dumps({"summary": summary, "prompt_uuid": "u1"}))
    assert f"[lint] {summary}" in _build(campaign)
    assert "[lint]" not in _build(campaign)  # the same reply's findings are already shown
    _write(path, json.dumps({"summary": summary, "prompt_uuid": "u2"}))
    assert f"[lint] {summary}" in _build(campaign)  # the same habit on a new reply
    _write(path, json.dumps({"summary": "", "prompt_uuid": "u3"}))
    assert "[lint] last reply clean." in _build(campaign)
    _write(path, json.dumps({"summary": "", "prompt_uuid": "u4"}))
    assert "[lint]" not in _build(campaign)


def test_lint_section_follows_the_profile_switch(campaign: Path) -> None:
    _write(_runtime(campaign) / "lint_last.json", json.dumps({"summary": "Last reply: 1 English line."}))
    _profile(campaign, "runtime:\n  presentation_lint: off\n")
    assert "[lint]" not in _build(campaign)


def test_open_roll_receipts_are_listed_until_consumed(campaign: Path) -> None:
    receipt = _roll(campaign, "bait-feint")
    _roll(campaign, "door-kick", actor="Mira", axis="power", difficulty=4)
    roll_dice.mark_consumed(campaign, ["door-kick"], 1)
    text = _build(campaign)
    assert f"[rolls]\n- roll bait-feint (Marcus street_sense vs 6): {receipt['band']}, not yet committed" in text
    assert "door-kick" not in text
    roll_dice.mark_consumed(campaign, ["bait-feint"], 1)
    delta = _build(campaign)
    assert "[rolls] no open receipts." in delta and "bait-feint" not in delta


def test_receipts_from_an_earlier_revision_are_not_open(campaign: Path) -> None:
    _roll(campaign, "old-roll")
    _state(campaign, "continuity_revision: 0", "continuity_revision: 1")
    assert "old-roll" not in _build(campaign)


def test_unreadable_receipt_store_is_reported_not_raised(campaign: Path) -> None:
    (_runtime(campaign) / "rolls.jsonl").mkdir(parents=True)
    assert "[rolls] the roll receipt store could not be read." in _build(campaign)


def test_staged_curation_is_listed_by_id(campaign: Path) -> None:
    folder = _runtime(campaign) / "curation"
    _write(folder / "r0-abc123.json", "{}\n")
    _write(folder / "applied" / "r0-done.json", "{}\n")
    _write(folder / "rejected" / "r0-stale.json", "{}\n")
    text = _build(campaign)
    assert "[curation] staged, waiting to be applied: r0-abc123" in text
    assert "r0-done" not in text and "r0-stale" not in text
    (folder / "r0-abc123.json").unlink()
    assert "[curation] nothing staged." in _build(campaign)


# ---------------------------------------------------------------------------
# Size caps
# ---------------------------------------------------------------------------


def test_size_caps_hold_with_truncation_markers(campaign: Path) -> None:
    titles = [f"Keeper {letter}" for letter in "ABCDEFGH"]
    for index, title in enumerate(titles):
        core = {"Status": "alive", "Kin": f"cousin {index} (alive)", "Role": "role " * 60, "Home": "home " * 60}
        _character(campaign, f"keeper_{index}", title, core=core, now="Busy. " * 200)
    _present(campaign, *titles)
    facts = "".join(f"### Name {number}\n\n- Fact id: F-{number:03d}\n- Status: GM-only\n\n" for number in range(30))
    _write(campaign / "knowledge_boundaries.md", f"# Knowledge Boundaries\n\n## Protected Proper Nouns\n\n{facts}")
    table = "".join(f"| D-{number:03d} | global | {'Keep this rule. ' * 12} | OOC | active |\n" for number in range(1, 21))
    _write(campaign / "directives.md", DIRECTIVES_HEAD + table)
    lint = _runtime(campaign) / "lint_last.json"
    _write(lint, json.dumps({"summary": "Last reply: " + "a repeated habit; " * 40}))
    for number in range(12):
        _roll(campaign, f"roll-{number}", actor="A" * 70, axis="B" * 70)
    for number in range(14):
        _write(_runtime(campaign) / "curation" / f"r0-{'x' * 40}{number:02d}.json", "{}\n")
    _profile(campaign, "narration:\n  language: tr\n")

    full = _build(campaign)
    assert len(full) <= scene_capsule.FULL_MAX
    for label in ("[cast]", "[secrets]", "[directives]", "[language]", "[lint]", "[rolls]", "[curation]"):
        assert label in full
    assert full.count("…") >= 4

    for index in range(len(titles)):
        _replace(campaign / "characters" / f"keeper_{index}.md", "Busy.", "Idle.")
    _write(campaign / "directives.md", DIRECTIVES_HEAD + table.replace("Keep this rule.", "Keep that rule."))
    _write(lint, json.dumps({"summary": "Last reply: " + "another habit; " * 40}))
    _roll(campaign, "roll-extra", actor="C" * 70, axis="D" * 70)
    _write(_runtime(campaign) / "curation" / f"r0-{'y' * 40}.json", "{}\n")
    _replace(campaign / "knowledge_boundaries.md", "F-000", "F-100")
    delta = _build(campaign)
    assert _is_delta(delta)
    assert len(delta) <= scene_capsule.DELTA_MAX
    assert "…" in delta
    assert "[language]" not in delta


def test_a_large_campaign_builds_well_under_a_second(campaign: Path) -> None:
    for index in range(250):
        body = "\n".join(f"- Detail {line}: {'lorem ipsum ' * 6}" for line in range(40))
        _character(campaign, f"npc_{index:03d}", f"Person {index:03d}", core={"Status": "alive"}, now="Busy.", extra=f"\n## Notes\n\n{body}\n")
    for index in range(60):
        _write(campaign / "places" / f"place_{index:02d}.md", f"# Place {index:02d}\n\n{'Quiet streets. ' * 200}\n")
    _present(campaign, *(f"Person {index:03d}" for index in range(8)))
    prompt = "I walk past Person 100 and Person 200 toward Place 07. " * 20
    # The first read of hundreds of just-written files can be held up by the
    # operating system (antivirus scanning on Windows); a hook reads notes that
    # are already on disk, so time a warm full build.
    _build(campaign, prompt, session="warm-up")
    started = time.perf_counter()
    text = _build(campaign, prompt)
    assert time.perf_counter() - started < 1.0
    assert "Person 100 (mentioned)" not in text  # the cast is already full with the eight present
    assert "[cast] in scope: Person 000 (present)" in text


def test_thirty_named_notes_and_a_300_kb_knowledge_file_build_under_a_second(campaign: Path) -> None:
    syllables = ["ka", "lo", "ve", "ri", "tu", "sa", "mo", "ne"]
    titles = [f"{syllables[index % 8].title()}{syllables[index // 8]}n {'Vane' if index % 2 else 'Holt'}" for index in range(30)]
    prose = "The river runs past the mill and the people talk of tolls and weather. " * 60
    for index, title in enumerate(titles):
        _character(campaign, f"n{index:02d}", title, core={"Status": "alive", "Kin": "a sister (alive)"}, now=prose[:700], extra=f"\n## Notes\n\n{prose}\n")
    protected = "".join(
        f"### Secret {number}\n\n- Fact id: F-{number:03d}\n- Status: GM-only\n- NPCs or factions who know: {titles[number % 30].split()[0]}\n\n"
        for number in range(60)
    )
    npcs = "".join(f"### {title}\n\n- Confirmed fact ids: F-{index:03d}\n- Explicitly unknown fact ids: F-{index + 1:03d}\n\n" for index, title in enumerate(titles))
    filler = "".join(f"- Fact: the bridge toll was raised on day {number}.\n  - Fact id: PC-{number:04d}\n" for number in range(4500))
    _write(
        campaign / "knowledge_boundaries.md",
        f"# Knowledge Boundaries\n\n## Protected Proper Nouns\n\n{protected}## Player Knowledge\n\n{filler}\n## NPC Knowledge\n\n{npcs}",
    )
    assert (campaign / "knowledge_boundaries.md").stat().st_size > 300_000
    _present(campaign, *titles[:5])
    prompt = f"I ask {titles[10].split()[0]} and {titles[20].split()[0].upper()} about the toll."
    _build(campaign, prompt, session="warm-up")  # a hook reads files already on disk; time a warm build
    started = time.perf_counter()
    text = _build(campaign, prompt)
    assert time.perf_counter() - started < 1.0
    assert f"{titles[10]} (mentioned), {titles[20]} (mentioned)" in text
    started = time.perf_counter()
    assert scene_capsule.names_in_text(campaign, prose * 3 + titles[7].split()[0]) == [titles[7]]
    assert time.perf_counter() - started < 1.0


# ---------------------------------------------------------------------------
# Robustness, hook, and CLI
# ---------------------------------------------------------------------------


def test_missing_files_never_raise(tmp_path: Path) -> None:
    bare = tmp_path / "bare"
    bare.mkdir()
    text = scene_capsule.build_capsule(bare, "Hello Edric", session_id="s", settings={})
    assert text.splitlines()[0] == "RePoG capsule — rev ? · day ? phase ? · ? · scene ? · persistence: narrate_then_commit"
    ghost = tmp_path / "ghost"
    assert scene_capsule.build_capsule(ghost, "Hello", session_id="s", settings={}).startswith("RePoG capsule")
    scene_capsule.reset(ghost)
    scene_capsule.reset(ghost, "s")
    scene_capsule.remember_names(ghost, "s", ["Edric"])
    assert scene_capsule.names_in_text(ghost, "Edric") == []
    assert not ghost.exists()


def test_corrupt_runtime_and_owner_files_never_raise(campaign: Path) -> None:
    runtime = _runtime(campaign)
    _write(runtime / "capsule_state.json", b"\xff\xfe{not json")
    _write(runtime / "lint_last.json", "[1, 2]")
    _write(campaign / "characters" / "broken.md", b"# Br\xffoken\n")
    _write(campaign / "directives.md", b"\xff\xfe\x00")
    _write(campaign / "knowledge_boundaries.md", b"\x80\x81")
    _write(campaign / "relationship_map.md", "| From | To |\n")
    _write(campaign / "glossary.md", b"\xc3")
    _write(campaign / "play_profile.yaml", b"\xff")
    _present(campaign, "Witness", "Nobody Known")
    text = _build(campaign, "Hello", settings={"scene_capsule": "on", "language": 7})
    assert "[cast] in scope: Witness (present), Nobody Known (present)" in text
    assert "- Nobody Known (no note)" in text
    assert _is_delta(_build(campaign, "Hello", settings={}))  # the state file was rewritten


def test_run_hook_builds_only_in_a_ready_rpg_campaign_with_the_capsule_on(
    campaign: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.chdir(elsewhere)
    event = {"prompt": "Hello", "session_id": "abc", "cwd": str(campaign.parent), "transcript_path": ""}
    assert scene_capsule.run_hook(event).startswith("RePoG capsule")
    assert scene_capsule.run_hook({**event, "cwd": str(elsewhere)}) == ""
    for bad in (None, [], {}, {"cwd": 5}, {"cwd": str(campaign.parent), "prompt": 7, "session_id": None}):
        assert isinstance(scene_capsule.run_hook(bad), str)  # type: ignore[arg-type]

    _replace(campaign / "setup_profile.yaml", "ready_for_play: true", "ready_for_play: false")
    assert scene_capsule.run_hook(event) == ""
    _replace(campaign / "setup_profile.yaml", "ready_for_play: false", "ready_for_play: true")
    _replace(campaign / "setup_profile.yaml", "experience_mode: rpg", "experience_mode: companion")
    assert scene_capsule.run_hook(event) == ""
    _replace(campaign / "setup_profile.yaml", "experience_mode: companion", "experience_mode: rpg")
    _profile(campaign, "runtime:\n  scene_capsule: off\n")
    assert scene_capsule.run_hook(event) == ""


def _stdin(monkeypatch: pytest.MonkeyPatch, data: bytes) -> None:
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(data), encoding="utf-8"))


def test_cli_hook_prints_ascii_json(
    campaign: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.chdir(elsewhere)  # an event without cwd must not find the campaign through the process cwd
    _character(campaign, "irem", "İrem")
    event = {"prompt": "İrem burada mı?", "session_id": "cli", "cwd": str(campaign.parent)}
    _stdin(monkeypatch, json.dumps(event, ensure_ascii=False).encode("utf-8"))
    assert scene_capsule.main(["hook"]) == 0
    raw = capsysbinary.readouterr().out
    raw.decode("ascii")
    assert "[cast] in scope: İrem (mentioned)" in json.loads(raw)["text"]

    _stdin(monkeypatch, b"\xff not json")
    assert scene_capsule.main(["hook"]) == 0
    assert json.loads(capsysbinary.readouterr().out) == {"text": ""}


def test_cli_show_and_reset(campaign: Path, tmp_path: Path, capsysbinary: pytest.CaptureFixture[bytes]) -> None:
    project = campaign.parent
    assert scene_capsule.main(["show", str(project), "--prompt", "Where is the Witness?"]) == 0
    shown = capsysbinary.readouterr().out.decode("utf-8")
    assert shown.startswith("RePoG capsule — rev 0") and "Witness (mentioned)" in shown
    assert not _runtime(campaign).exists()  # show records nothing

    _build(campaign, session="s9")
    assert scene_capsule.main(["show", str(campaign), "--session", "s9"]) == 0
    assert _is_delta(capsysbinary.readouterr().out.decode("utf-8"))
    assert scene_capsule.main(["show", str(campaign), "--session", "s9", "--full"]) == 0
    assert not _is_delta(capsysbinary.readouterr().out.decode("utf-8"))

    assert scene_capsule.main(["reset", "--session", "s9", str(project)]) == 0
    assert json.loads(capsysbinary.readouterr().out) == {"ok": True, "session": "s9"}
    assert not _is_delta(_build(campaign, session="s9"))

    assert scene_capsule.main(["show", str(tmp_path / "nowhere")]) == 2
    assert json.loads(capsysbinary.readouterr().out)["ok"] is False

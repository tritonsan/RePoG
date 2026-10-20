"""Structure checks for the blank campaign templates touched in plugin 0.3.0.

Templates are copied into every new campaign, and runtime tools read them with
small line-based parsers. These tests pin the shapes those parsers rely on:
unique headings, well-formed tables with no example rows, the `## Core` and
`## Now` note blocks, and `runtime:` values the runtime layer accepts.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

import owner_ops
import repog_runtime


TEMPLATES = Path(__file__).resolve().parents[1] / "plugin" / "templates" / "campaign"
MARKDOWN_TEMPLATES = (
    "directives.md",
    "glossary.md",
    "rules.md",
    "characters/_template.md",
    "places/_template.md",
)
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE_RE = re.compile(r"^[ \t]*(```|~~~)")
SEPARATOR_RE = re.compile(r"^\|?[ \t]*:?-{3,}:?[ \t]*(\|[ \t]*:?-{3,}:?[ \t]*)*\|?[ \t]*$")


def _text(relative: str) -> str:
    return (TEMPLATES / relative).read_text(encoding="utf-8")


def _headings(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    fenced = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        match = None if fenced else HEADING_RE.match(line)
        if match:
            found.append((len(match.group(1)), match.group(2).strip()))
    return found


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _tables(text: str) -> list[list[str]]:
    """Every run of lines that starts with `|`, as a naive reader sees it."""

    tables: list[list[str]] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            current.append(line)
        elif current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables


def _section(text: str, heading: str) -> str:
    match = re.search(rf"(?m)^##\s+{re.escape(heading)}\s*$", text)
    assert match, f"missing ## {heading}"
    rest = text[match.end() :]
    following = re.search(r"(?m)^#{1,2}\s+", rest)
    return rest[: following.start()] if following else rest


def _fields(section: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in section.splitlines():
        match = re.match(r"^-\s+([^:]+):[ \t]*(.*?)\s*$", line)
        if match:
            values[match.group(1).strip()] = match.group(2)
    return values


def _apply(text: str, relative: str, ops: list[dict]) -> str:
    return owner_ops.apply_ops(
        text,
        owner_ops.parse_ops(ops, relative=relative, label="m"),
        relative=relative,
        label="m",
        placeholders=owner_ops.PlaceholderContext(1),
    )


# ---------------------------------------------------------------------------
# Shared Markdown shape
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative", MARKDOWN_TEMPLATES)
def test_markdown_template_headings_are_unique(relative: str) -> None:
    text = _text(relative)
    headings = _headings(text)
    # Typed edits may address a heading by its text alone, without its #s.
    titles = [title for _, title in headings]
    duplicates = sorted({title for title in titles if titles.count(title) > 1})
    assert duplicates == []
    assert owner_ops.stacked_headings(text) == []
    assert headings[0][0] == 1, "a template starts with its title heading"


@pytest.mark.parametrize("relative", MARKDOWN_TEMPLATES)
def test_markdown_template_tables_are_well_formed(relative: str) -> None:
    for table in _tables(_text(relative)):
        assert len(table) >= 2, f"table without a separator: {table[0]}"
        assert SEPARATOR_RE.match(table[1].strip()), table[1]
        width = len(_cells(table[0]))
        for row in table[1:]:
            assert len(_cells(row)) == width, row


@pytest.mark.parametrize("relative", ["directives.md", "glossary.md"])
def test_new_templates_are_lf_and_generic(relative: str) -> None:
    data = (TEMPLATES / relative).read_bytes()
    assert b"\r" not in data
    assert data.decode("utf-8").isascii()


# ---------------------------------------------------------------------------
# directives.md
# ---------------------------------------------------------------------------


def test_directives_table_has_the_columns_and_no_rows() -> None:
    text = _text("directives.md")
    tables = _tables(text)
    assert len(tables) == 1
    assert _cells(tables[0][0]) == ["Id", "Scope", "Directive", "Source", "Status"]
    assert len(tables[0]) == 2, "example rows must stay out of the table"
    # The only literal id is the never-assigned D-000 that sets the id width;
    # any other literal id would shift the first allocated one.
    assert re.findall(r"\bD-\d+\b", text) == ["D-000"]
    for word in ("global", "scene:<scene id>", "entity:<name>", "active", "retired"):
        assert word in text


def _directive_row(scope: str, directive: str) -> dict:
    return {
        "op": "append",
        "heading": "Standing Directives",
        "text": f"| {{{{next_id:D}}}} | {scope} | {directive} | OOC request, revision 3 | active |",
    }


def test_directives_next_id_allocates_three_digit_ids_from_d001() -> None:
    # Regression: on the blank template `{{next_id:D}}` used to allocate `D-1`,
    # and every later id kept that unpadded width.
    text = _text("directives.md")
    first_commit = _apply(text, "directives.md", [_directive_row("global", "Keep replies short.")])
    second_commit = _apply(
        first_commit,
        "directives.md",
        [
            _directive_row("entity:İlse Çakır", "She uses the formal address."),
            _directive_row("scene:dock-interview", "No weather talk."),
        ],
    )
    rows = _tables(second_commit)[0][2:]
    assert [_cells(row)[0] for row in rows] == ["D-001", "D-002", "D-003"]
    assert _cells(rows[1])[1] == "entity:İlse Çakır"


def test_directives_template_is_read_by_the_curation_packet(tmp_path: Path) -> None:
    curation = pytest.importorskip("curation")
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    blank = _text("directives.md")
    (campaign / "directives.md").write_text(blank, encoding="utf-8", newline="")
    assert curation.active_directives(campaign) == [], "commented examples are not directives"

    # A Windows editor may save the file with CRLF; rows still append and read.
    crlf = blank.replace("\n", "\r\n")
    updated = _apply(crlf, "directives.md", [_directive_row("global", "Keep replies short.")])
    assert "\n" not in updated.replace("\r\n", "")
    (campaign / "directives.md").write_text(updated, encoding="utf-8", newline="")
    assert curation.active_directives(campaign) == [
        {"id": "D-001", "scope": "global", "directive": "Keep replies short."}
    ]


@pytest.mark.parametrize("relative", ["directives.md", "glossary.md"])
def test_example_comments_are_valid_html_comments(relative: str) -> None:
    text = _text(relative)
    assert text.count("<!--") == text.count("-->") == 1
    body = text.split("<!--", 1)[1].split("-->", 1)[0]
    # `--` inside a comment ends it early in strict HTML renderers.
    assert "--" not in body
    assert all(not line.lstrip().startswith("|") for line in body.splitlines())


def test_directives_examples_are_inside_a_comment() -> None:
    text = _text("directives.md")
    comments = re.findall(r"<!--(.*?)-->", text, flags=re.S)
    assert len(comments) == 1
    examples = [line for line in comments[0].splitlines() if "|" in line]
    assert len(examples) == 3
    assert all(line.startswith("e.g. |") for line in examples)
    scopes = {_cells(line.removeprefix("e.g."))[1].split(":")[0] for line in examples}
    assert scopes == {"global", "entity", "scene"}


def test_directives_template_accepts_typed_rows() -> None:
    text = _text("directives.md")
    upserted = _apply(
        text,
        "directives.md",
        [
            {
                "op": "upsert_row",
                "heading": "Standing Directives",
                "key": "D-001",
                "cells": ["D-001", "global", "Keep replies short.", "OOC request, revision 3", "active"],
            }
        ],
    )
    appended = _apply(
        upserted,
        "directives.md",
        [
            {
                "op": "append",
                "heading": "Standing Directives",
                "text": "| D-002 | scene:dock-interview | No weather talk. | OOC request, revision 4 | active |",
            }
        ],
    )
    tables = _tables(appended)
    assert len(tables) == 1
    assert [_cells(row)[0] for row in tables[0][2:]] == ["D-001", "D-002"]
    assert "e.g. | D-NNN | global |" in appended


def test_directives_scopes_name_what_the_capsule_can_match() -> None:
    # The scene capsule matches `entity:` scopes against character, place, and
    # faction note titles in play, `scene:` against scene_frame.scene_id, and
    # shows every global row too, at most 12.
    text = " ".join(_text("directives.md").split())
    assert "`scene:<scene id>`, where the id is `scene_frame.scene_id` in `current_state.yaml`" in text
    assert "`entity:<name>`, where the name is the title of the character, place, or faction note" in text
    assert "every `global` row" in text and "at most 12, newest first" in text
    assert "Keep `|` out of every cell" in text


# ---------------------------------------------------------------------------
# glossary.md
# ---------------------------------------------------------------------------


def test_glossary_table_and_policy_fields() -> None:
    text = _text("glossary.md")
    tables = _tables(text)
    assert len(tables) == 1
    assert _cells(tables[0][0]) == ["Term", "Preferred", "Variants", "Notes"]
    assert len(tables[0]) == 2, "example rows must stay out of the table"
    policy = _fields(_section(text, "Rendering Policy"))
    assert policy == {"Place names": "", "Titles and honorifics": "", "Address forms": "", "Units": ""}
    # Readers take a policy value from its field line only.
    assert "the field's own line" in _section(text, "Rendering Policy")
    # A `|` inside a cell would split a term row for every table reader.
    assert "Keep `|` out of every cell" in " ".join(_section(text, "Terms").split())


@pytest.mark.parametrize("newline", ["\n", "\r\n"], ids=["lf", "crlf"])
@pytest.mark.parametrize(
    "cells",
    [
        ["harbor master", "Warden", "port lord, harbourmaster", "Title."],
        ["kale ağası", "Ağa", "aga, agha, İlbey", "Unvan; çeyrek saat değil."],
    ],
    ids=["ascii", "turkish"],
)
def test_glossary_template_accepts_an_appended_term(newline: str, cells: list[str]) -> None:
    template = _text("glossary.md").replace("\n", newline)
    row = "| " + " | ".join(cells) + " |"
    result = _apply(template, "glossary.md", [{"op": "append", "heading": "## Terms", "text": row}])
    # The row joins the real table, after the commented examples, in the file's own line ending.
    assert f"| --- | --- | --- | --- |{newline}{row}{newline}" in result
    if newline == "\r\n":
        assert "\n" not in result.replace("\r\n", "")
    else:
        assert "\r" not in result
    tables = _tables(result)
    assert len(tables) == 1
    assert [_cells(line) for line in tables[0][2:]] == [cells]


# ---------------------------------------------------------------------------
# Entity notes
# ---------------------------------------------------------------------------


CHARACTER_SECTIONS_BEFORE_0_3 = [
    "At-The-Table Agency Card",
    "Offscreen Trajectory",
    "Agent Playability Card",
    "Stats (Numeric Grounding Only)",
    "Key Capabilities",
    "Weak Stats / Blind Spots",
    "What They Can Reliably Do",
    "What They Cannot Do",
    "Growth Ceiling For Current Stage",
    "Combat / Social / Influence Positioning",
    "Represents",
    "Table Hook",
    "Appearance",
    "Default Posture",
    "Distinctive Lexicon",
    "Do Not Sound Like",
    "Metaphor Family To Avoid",
    "Plain Speech Sample",
    "Contextual Voice Examples",
    "Earned Disposition Changes",
    "Public Face",
    "Visual Reference",
    "Key Info, If Any",
    "Knowledge References",
    "How They Read People",
    "Inference Limits",
    "How They Test People",
    "Communication Tendencies",
    "Dialogue Boundaries",
    "Private Motive",
    "Leverage And Vulnerability",
    "Status Play",
    "Relationship Behavior And References",
    "Secret-Keeping Behavior And References",
    "Last Meaningful Interaction",
    "GM Use",
    "Promotion Notes",
]


def test_character_template_core_and_now_follow_the_tier_lines() -> None:
    text = _text("characters/_template.md")
    level_two = [title for level, title in _headings(text) if level == 2]
    assert level_two[:3] == ["Core", "Now", "At-The-Table Agency Card"]
    assert level_two[2:] == CHARACTER_SECTIONS_BEFORE_0_3
    assert text.index("Power Band:") < text.index("## Core")

    core = _fields(_section(text, "Core"))
    assert list(core) == ["Status", "Pronouns and address", "Kin", "Role", "Home", "Speaks", "Aliases"]
    assert [value.strip() for value in core["Status"].split("|")] == ["alive", "dead", "missing", "unknown"]
    assert all(value == "" for key, value in core.items() if key != "Status")

    # The first Tier line is still the note's tier; Core adds no competing field.
    assert re.search(r"(?im)^[ \t]*(?:-[ \t]+)?Tier:[ \t]*(.*?)[ \t]*$", text).group(1) == "T1/T2/T3"
    now = _section(text, "Now")
    assert "800 characters" in now and "session_log.md" in now
    assert "- Offscreen trajectory status: inactive" in _section(text, "At-The-Table Agency Card")
    assert "play language" in _section(text, "Plain Speech Sample")
    assert "play language" in _section(text, "Contextual Voice Examples")


def test_place_template_core_and_now() -> None:
    text = _text("places/_template.md")
    level_two = [title for level, title in _headings(text) if level == 2]
    assert level_two[:3] == ["Core", "Now", "Companion Grounding"]
    assert "Current Changes" in level_two and "Promotion Notes" in level_two
    core = _fields(_section(text, "Core"))
    assert list(core)[0] == "Status" and list(core)[-1] == "Aliases"
    assert "Keep each value on one line" in _section(text, "Core")
    assert "## Now" in _section(text, "Current Changes")


@pytest.mark.parametrize(
    ("relative", "owners", "duplicated"),
    [
        (
            "characters/_template.md",
            ("`active_cast.md`", "`knowledge_boundaries.md`", "`relationship_map.md`"),
            "where the character is",
        ),
        (
            "places/_template.md",
            ("`active_cast.md`", "`current_state.yaml`", "`location_graph.md`", "`## Disruption`"),
            "who is here",
        ),
    ],
)
def test_note_now_leaves_other_owners_facts_with_their_owners(
    relative: str, owners: tuple[str, ...], duplicated: str
) -> None:
    # Regression: `## Now` asked for where a character is and what they are doing
    # (a place: who is here), which `active_cast.md` and `current_state.yaml`
    # own. Two current accounts drift apart, and the capsule injects `## Now`.
    now = " ".join(_section(_text(relative), "Now").split())
    assert duplicated not in now
    assert "Facts another owner holds stay there" in now
    for owner in owners:
        assert owner in now, owner


def _template_note(relative: str, title: str, replacements: dict[str, str]) -> str:
    """A note made from a template (LF, as the writer stores new notes)."""

    text = _text(relative)
    text = text.replace(text.splitlines()[0], f"# {title}", 1)
    for old, new in replacements.items():
        assert text.count(old) == 1, old
        text = text.replace(old, new, 1)
    return text


def test_character_core_status_is_one_word_the_full_check_reads(tmp_path: Path) -> None:
    check_runtime = pytest.importorskip("check_runtime")
    if not hasattr(check_runtime, "check_notes"):
        pytest.skip("check_runtime has no check_notes")
    core = " ".join(_section(_text("characters/_template.md"), "Core").split())
    # The full check compares the whole Status value with `dead`, so a cause or
    # date beside the word would silently disable the dead_present error.
    assert "`Status` holds exactly one of the four listed words" in core
    assert "separated by semicolons" in core

    campaign = tmp_path / "campaign"
    (campaign / "characters").mkdir(parents=True)

    def findings(status_line: str) -> list[tuple[str, str]]:
        note = _template_note(
            "characters/_template.md",
            "Edda Vale",
            {"Tier: T1/T2/T3": "Tier: T2", "- Status: alive | dead | missing | unknown": status_line},
        )
        (campaign / "characters" / "edda_vale.md").write_text(note, encoding="utf-8", newline="\n")
        found: list[tuple[str, str]] = []

        def add(severity: str, rule: str, message: str, path: Path) -> None:
            found.append((severity, rule))

        check_runtime.check_notes(campaign, ["Edda Vale"], add)
        return found

    assert findings("- Status: dead") == [("error", "dead_present")]
    # No note_core_missing either: the T2 note's Core block is recognized.
    assert findings("- Status: alive") == []
    # An unfilled enum menu is not a status.
    assert findings("- Status: alive | dead | missing | unknown") == []


def test_place_obstacle_difficulty_format_passes_the_full_check(tmp_path: Path) -> None:
    check_state = pytest.importorskip("check_state")
    text = _text("places/_template.md")
    block = _section(text, "Common Obstacles And Difficulties")
    # Regression: under a numeric resolution scale a bare number such as
    # `Difficulty: 9` is an obstacle_difficulty_invalid error; the template now
    # shows the word-and-number form the full check accepts.
    example = re.search(r"such as `([^`]+)`", " ".join(block.split())).group(1)
    assert re.fullmatch(r"[a-z]+ \(\d+\)", example)
    places = tmp_path / "campaign" / "places"
    places.mkdir(parents=True)

    bullet = re.search(r"(?m)^- Difficulty:.*\n(?:  .*\n)*", text).group(0)

    def rules(difficulty: str) -> set[str]:
        note = _template_note(
            "places/_template.md",
            "Old Mill",
            {"### Obstacle Name": "### Flooded Stair", bullet: f"- Difficulty: {difficulty}\n"},
        )
        (places / "old_mill.md").write_text(note, encoding="utf-8", newline="\n")
        found: list[dict] = []
        check_state._check_place_obstacles(tmp_path / "campaign", found)
        return {finding["rule"] for finding in found if finding["severity"] == "error"}

    assert rules(example) == set()
    assert rules("9") == {"obstacle_difficulty_invalid"}


@pytest.mark.parametrize(
    ("relative", "title"),
    [("characters/_template.md", "# Character Name"), ("places/_template.md", "# Place Name")],
)
def test_note_templates_allow_the_curator_fold(relative: str, title: str) -> None:
    # The curator folds stacked dated sections into one `## Now` plus a short
    # `## History` list. The template must allow that list in words, and must
    # not ship a `## History` heading, which would make its insert_section fail.
    # Use the bytes as shipped: these templates mix CRLF and LF lines.
    text = (TEMPLATES / relative).read_bytes().decode("utf-8")
    assert "`## History`" in " ".join(_section(text, "Now").split())
    assert "History" not in [heading for _, heading in _headings(text)]
    note = text.replace(title, "# Old Mill", 1)
    note = _apply(
        note,
        relative,
        [
            {"op": "insert_section", "heading": "## Current State (day 22)", "text": "Busy."},
            {"op": "insert_section", "heading": "## Current State (day 72)", "text": "Quiet."},
        ],
    )
    folded = _apply(
        note,
        relative,
        [
            {"op": "replace_section", "heading": "## Now", "text": "Quiet."},
            {"op": "remove_section", "heading": "Current State (day 22)"},
            {"op": "remove_section", "heading": "Current State (day 72)"},
            {"op": "insert_section", "heading": "## History", "text": "- Day 22: busy."},
        ],
    )
    titles = [heading for _, heading in _headings(folded)]
    assert titles.count("Now") == 1 and titles.count("History") == 1
    assert not any(heading.startswith("Current State") for heading in titles)
    assert _section(folded, "Now").strip() == "Quiet."
    # New lines take the note's CRLF; the shipped lines keep their own endings.
    assert "## History\r\n\r\n- Day 22: busy.\r\n" in folded
    assert folded.startswith(text.replace(title, "# Old Mill", 1).split("## Core", 1)[0])


def test_new_note_from_template_replaces_now_in_place() -> None:
    note = _text("characters/_template.md").replace("# Character Name", "# Witness", 1)
    once = _apply(note, "characters/witness.md", [{"op": "replace_section", "heading": "## Now", "text": "At the dock."}])
    twice = _apply(once, "characters/witness.md", [{"op": "replace_section", "heading": "## Now", "text": "Gone home."}])
    assert _section(twice, "Now").strip() == "Gone home."
    assert [title for _, title in _headings(twice)].count("Now") == 1


# ---------------------------------------------------------------------------
# play_profile.yaml
# ---------------------------------------------------------------------------


def _uncomment_resolution(text: str) -> str:
    lines: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.strip() == "# resolution:":
            inside = True
        elif inside and not line.strip().startswith("#"):
            inside = False
        lines.append(re.sub(r"^(\s*)# ", r"\1", line, count=1) if inside else line)
    return "\n".join(lines) + "\n"


def test_play_profile_runtime_block_uses_allowed_defaults() -> None:
    text = _text("play_profile.yaml")
    runtime = repog_runtime.block_scalars(text, "runtime")
    assert set(runtime) == set(repog_runtime.RUNTIME_ALLOWED)
    for key, value in runtime.items():
        assert value in repog_runtime.RUNTIME_ALLOWED[key], key
    assert runtime == repog_runtime.RUNTIME_DEFAULTS
    assert repog_runtime.block_scalars(text, "narration")["language"] == "auto"


def test_play_profile_allowed_values_comment_matches_runtime() -> None:
    text = _text("play_profile.yaml")
    documented = {
        match.group(1): {value.strip() for value in match.group(2).split("|")}
        for match in re.finditer(r"(?m)^# runtime\.(\w+): (.+)$", text)
    }
    assert documented == repog_runtime.RUNTIME_ALLOWED


def test_play_profile_existing_blocks_still_parse() -> None:
    text = _text("play_profile.yaml")
    mechanics = repog_runtime.block_scalars(text, "mechanics")
    assert mechanics["dice_mode"] == "judgment_only"
    assert mechanics["resolution_grounding"] == "fictional"
    assert "resolution" not in mechanics
    narration = repog_runtime.block_scalars(text, "narration")
    assert narration["point_of_view"] == "second"
    assert repog_runtime.top_scalar(text, "profile_status") == "pending"
    assert not re.search(r"(?m)^\s*resolution:", text), "the resolution example stays commented"


def test_template_campaign_gets_runtime_defaults(tmp_path: Path) -> None:
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    shutil.copyfile(TEMPLATES / "play_profile.yaml", campaign / "play_profile.yaml")
    assert repog_runtime.runtime_settings(campaign) == {**repog_runtime.RUNTIME_DEFAULTS, "language": "auto"}


def test_play_profile_resolution_example_is_well_formed() -> None:
    uncommented = _uncomment_resolution(_text("play_profile.yaml"))
    block = re.search(r"(?ms)^  resolution:\n(.*?)(?=^\S|^  \S)", uncommented)
    assert block, "the example uncomments into mechanics.resolution"
    values = dict(re.findall(r"(?m)^    (\w+): (\S+)$", block.group(1)))
    assert re.fullmatch(r"\d+d\d+", values["die"])
    numbers = {key: int(values[key]) for key in ("stat_min", "stat_max", "difficulty_min", "difficulty_max")}
    assert numbers["stat_min"] < numbers["stat_max"]
    assert numbers["difficulty_min"] < numbers["difficulty_max"]
    bands = re.findall(r"(?m)^      - \{at_least: (-?\d+), band: (\w+)\}$", block.group(1))
    thresholds = [int(value) for value, _ in bands]
    assert len(bands) >= 2 and thresholds == sorted(thresholds, reverse=True)

    # The illustration must not repeat the exhausted scale it warns about: the
    # top stat still fails the hardest difficulty sometimes, and the lowest stat
    # can still reach the first band against it.
    count, sides = (int(part) for part in values["die"].split("d"))
    hardest = numbers["difficulty_max"]
    assert numbers["stat_max"] + count < hardest + thresholds[0]
    assert numbers["stat_min"] + count * sides >= hardest + thresholds[0]


def test_play_profile_resolution_example_loads_with_odds() -> None:
    odds = pytest.importorskip("odds")
    text = _text("play_profile.yaml")
    assert odds.load_resolution(text) is None
    resolution = odds.load_resolution(_uncomment_resolution(text))
    assert resolution is not None
    assert (resolution["stat_min"], resolution["stat_max"]) == (1, 5)
    assert resolution["auto_success_margin"] == 2
    assert [band["band"] for band in resolution["bands"]][0] == "success"
    # Neither the scale_exhausted warning nor the first_band_unreachable info.
    assert odds.exhaustion(resolution) == []


def test_play_profile_language_comment_lists_every_shipped_pack() -> None:
    packs = TEMPLATES.parents[1] / "packs" / "languages"
    codes = sorted(path.stem for path in packs.glob("*.json"))
    if not codes:
        pytest.skip("no language packs in this tree")
    text = _text("play_profile.yaml")
    match = re.search(r"(?m)^# narration\.language: (.+(?:\r?\n#   .+)*)", text)
    assert match, "narration.language is listed under Allowed values"
    documented = set(re.findall(r"\b[a-z]{2,3}\b", match.group(1)))
    assert "auto" in match.group(1)
    assert set(codes) <= documented


# ---------------------------------------------------------------------------
# rules.md
# ---------------------------------------------------------------------------


def _section_level3(text: str, heading: str) -> str:
    match = re.search(rf"(?m)^###\s+{re.escape(heading)}\s*$", text)
    assert match, f"missing ### {heading}"
    rest = text[match.end() :]
    following = re.search(r"(?m)^#{1,3}\s+", rest)
    return rest[: following.start()] if following else rest


def test_rules_declared_axes_unchanged_and_dice_sections_present() -> None:
    text = _text("rules.md")
    # Same reading as the full check: bullets after the heading, up to the next heading.
    match = re.search(r"(?im)^#{2,4}\s+Declared Stat Axes\s*$", text)
    axes: list[str] = []
    for line in text[match.end() :].splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            break
        if stripped.startswith("- "):
            axes.append(stripped[2:].split(":")[0].split("—")[0].strip())
    assert axes == ["Power", "Agility", "Endurance", "Technique", "Perception", "Wits", "Presence", "Will"]

    subsections = [title for level, title in _headings(text) if level == 3]
    for title in ("Resolution Scale", "Declare Before Rolling", "Roll Calls", "Odds Table", "Scale Migration"):
        assert title in subsections
    dice = _section(text, "Dice")
    assert "mechanics.resolution" in dice and "tools/odds.py" in dice


def test_rules_roll_call_matches_the_dice_tool(capsys: pytest.CaptureFixture[str]) -> None:
    roll_dice = pytest.importorskip("roll_dice")
    text = _text("rules.md")
    roll_calls = re.search(r"(?ms)^### Roll Calls\s*$(.*?)^###? ", text).group(1)
    command = re.search(r"`(?:python )?tools/roll_dice\.py ([^`]+)`", roll_calls).group(1)
    flags = re.findall(r"--[a-z][a-z-]*", command)
    assert flags == ["--campaign", "--input-file"]
    with pytest.raises(SystemExit):
        roll_dice.main(["--help"])
    usage = capsys.readouterr().out
    assert all(flag in usage for flag in flags)
    # Without a resolution block the tool refuses a call that names no die,
    # and a roll id is bound to its revision; the rules must say both.
    flat = " ".join(roll_calls.split())
    assert "names its die in `NdM` form" in flat
    assert "at the same continuity revision" in flat
    data = (TEMPLATES / "rules.md").read_bytes()
    assert b"\r\n" in data and b"\n" not in data.replace(b"\r\n", b""), "rules.md stays CRLF"


def test_rules_roll_call_request_shape_is_the_one_the_tool_accepts(tmp_path: Path) -> None:
    # Regression: the rules said "the call also names its die", but `die` sits
    # beside `call` in the request; inside `call` the tool refuses it.
    roll_dice = pytest.importorskip("roll_dice")
    roll_calls = _section_level3(_text("rules.md"), "Roll Calls")
    named = set(re.findall(r"`([a-z_]+)`", roll_calls))
    for keys in (roll_dice.REQUEST_KEYS, roll_dice.CALL_KEYS, roll_dice.FACTOR_KEYS):
        assert set(keys) <= named, sorted(set(keys) - named)
    assert "as `die`, beside `call`" in " ".join(roll_calls.split())

    campaign = tmp_path / "campaign"
    campaign.mkdir()
    state = campaign / "current_state.yaml"
    state.write_text("campaign_id: synthetic\ncontinuity_revision: 4\n", encoding="utf-8")
    call = {
        "actor": "Mira",
        "axis": "Wits",
        "value": 3,
        "difficulty": 4,
        "factors": [{"label": "knows the docks", "modifier": 1}],
        "stakes": "the courier slips into the crowd",
    }
    first = roll_dice.roll_call(campaign, {"roll_id": "dock-feint", "call": call, "die": "1d6"}, now="t0")
    assert first["ok"] is True and first["repeat"] is False and first["die"] == "1d6"
    # Same roll id and call at the same revision: the same receipt.
    again = roll_dice.roll_call(campaign, {"roll_id": "dock-feint", "call": call, "die": "1d6"}, now="t1")
    assert again["repeat"] is True and again["dice"] == first["dice"] and again["band"] == first["band"]
    with pytest.raises(roll_dice.RollCallError) as inside:
        roll_dice.roll_call(campaign, {"roll_id": "dock-feint-2", "call": {**call, "die": "1d6"}})
    assert inside.value.category == "input_invalid"
    # A roll id is never reused at a later revision.
    state.write_text("campaign_id: synthetic\ncontinuity_revision: 5\n", encoding="utf-8")
    with pytest.raises(roll_dice.RollCallError) as later:
        roll_dice.roll_call(campaign, {"roll_id": "dock-feint", "call": call, "die": "1d6"})
    assert later.value.category == "roll_id_conflict"


def test_rules_scale_migration_follows_the_writer_and_ooc_paths() -> None:
    # Regression: the migration said to change `mechanics.resolution`, rules, and
    # every recorded stat "in the same change". The locked profile changes only
    # through the OOC configuration procedure, which must not carry
    # current_state.yaml or fictional owners, and the durable writer cannot
    # write play_profile.yaml; faction stats were also left out.
    text = _text("rules.md")
    migration = " ".join(_section_level3(text, "Scale Migration").split())
    assert "in the same change" not in migration
    assert "through the OOC configuration procedure" in migration
    assert "through the durable writer" in migration
    assert "NPC and faction stats" in migration and "player character's stats" in migration
    assert "Make no roll call until both writes are done" in migration
    scale = " ".join(_section(text, "Numeric Stat Scale").split())
    assert "rescale the starting budgets" in scale
    resolution = " ".join(_section_level3(text, "Resolution Scale").split())
    assert "which difficulty number each Obstacle Difficulty word stands for" in resolution


# ---------------------------------------------------------------------------
# The blank campaign as a whole
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("resolution_example", [False, True], ids=["as_shipped", "resolution_uncommented"])
def test_blank_template_campaign_passes_the_full_check(tmp_path: Path, resolution_example: bool) -> None:
    check_state = pytest.importorskip("check_state")
    campaign = tmp_path / "campaign"
    shutil.copytree(TEMPLATES, campaign)
    profile = campaign / "play_profile.yaml"
    if resolution_example:
        profile.write_bytes(_uncomment_resolution(_text("play_profile.yaml")).encode("utf-8"))
    findings = check_state.check_campaign(campaign, scope="full")["findings"]
    assert [finding for finding in findings if finding["severity"] == "error"] == []
    new_files = {"directives.md", "glossary.md"}
    assert [finding for finding in findings if Path(str(finding["path"])).name in new_files] == []
    # Neither a runtime switch, the play language, nor the illustrated scale is
    # reported: no unknown setting, no exhausted or unreachable band.
    assert [finding for finding in findings if Path(str(finding["path"])).name == "play_profile.yaml"] == []

    # Positive control: where the full check validates the runtime layer, the
    # same campaign with a bad switch is reported, so the pass above is real.
    try:
        import check_runtime  # noqa: F401
    except ImportError:
        return
    profile.write_bytes(profile.read_bytes().replace(b"presentation_lint: on", b"presentation_lint: maybe"))
    findings = check_state.check_campaign(campaign, scope="full")["findings"]
    assert any("runtime.presentation_lint" in finding["message"] for finding in findings)


@pytest.mark.parametrize(
    ("block", "reported"),
    [
        ("runtime: {scene_capsule: off}\n", True),
        ("runtime: {}\n", False),
        ("runtime:  # switches\n  scene_capsule: off\n", False),
        ("runtime:\n  scene_capsule: off\n", False),
    ],
)
def test_an_inline_runtime_block_is_reported_not_silently_ignored(block: str, reported: bool) -> None:
    import check_runtime

    found: list[tuple[str, str]] = []
    check_runtime.check_profile(block, Path("play_profile.yaml"), lambda severity, rule, message, path: found.append((severity, rule)))
    # The hooks read `runtime:` only as indented `key: value` lines, so an inline
    # mapping leaves every switch at its default without a word.
    assert (("error", "runtime_block_inline") in found) is reported

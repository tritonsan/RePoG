"""Playbooks, templates, and docs for plugin 0.4.0.

The GM reads these files every turn and copies their examples into helper
calls, so the tests pin what each one must say and run the documented payloads
and commands against the real helpers on synthetic campaigns. A check that
needs a helper another package provides is skipped while that helper lacks the
feature, so this file stays runnable on its own.
"""

from __future__ import annotations

import inspect
import json
import re
import shutil
from pathlib import Path

import pytest

import owner_ops
import repog_runtime


PLUGIN = Path(__file__).resolve().parents[1] / "plugin"
TEMPLATES = PLUGIN / "templates" / "campaign"
GM = "workflows/gm/WORKFLOW.md"
PERSISTENCE = "workflows/gm/playbooks/persistence.md"
ACTION = "workflows/gm/playbooks/action_conflict.md"
OOC = "workflows/gm/playbooks/ooc_adjustment.md"
ARC = "workflows/gm/playbooks/scene_arc_transition.md"
TRAVEL = "workflows/gm/playbooks/travel_downtime.md"
VISUALS = "workflows/gm/playbooks/visuals.md"
DISTILL = "workflows/distill/WORKFLOW.md"
CREATION = "workflows/reference/creation.md"
CHARACTER = "templates/campaign/characters/_template.md"
STYLE = "output-styles/repog.md"
README = "README.md"
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")
HEREDOC_JSON_RE = re.compile(r"<<'JSON'\n(.*?)\nJSON\n", re.S)


def _text(relative: str) -> str:
    """A shipped file with its line endings folded, as the GM reads it."""

    return (PLUGIN / relative).read_bytes().decode("utf-8").replace("\r\n", "\n")


def _flat(text: str) -> str:
    return " ".join(text.split())


def _headings(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        match = None if fenced else HEADING_RE.match(line)
        if match:
            found.append((len(match.group(1)), match.group(2)))
    return found


def _section(text: str, heading: str) -> str:
    """The body under `heading` (any level) up to the next heading of the same or a higher level."""

    match = re.search(rf"(?m)^(#{{1,6}})[ \t]+{re.escape(heading)}[ \t]*$", text)
    assert match, f"missing heading {heading!r}"
    level = len(match.group(1))
    rest = text[match.end() :]
    following = re.search(rf"(?m)^#{{1,{level}}}[ \t]+\S", rest)
    return rest[: following.start()] if following else rest


def _numbered(section: str) -> list[str]:
    """The items of the first numbered list in a section, continuation lines joined."""

    items: list[str] = []
    for line in section.splitlines():
        if re.match(r"^\s*\d+\.\s", line):
            items.append(re.sub(r"^\s*\d+\.\s+", "", line))
        elif items and line.startswith("   ") and line.strip():
            items[-1] += " " + line.strip()
        elif items and not line.strip():
            break
    return items


def _fields(section: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in section.splitlines():
        match = re.match(r"^-\s+([^:`]+):[ \t]*(.*?)\s*$", line)
        if match:
            values[match.group(1).strip()] = match.group(2)
    return values


def _json_examples(relative: str) -> list[dict]:
    return [json.loads(block) for block in HEREDOC_JSON_RE.findall(_text(relative))]


def _inline_json(relative: str, start: str) -> dict:
    """The JSON object in the inline code span that begins with `start`."""

    flat = _flat(_text(relative))
    match = re.search(r"`(" + re.escape(start) + r"[^`]*)`", flat)
    assert match, start
    return json.loads(match.group(1))


def _apply(text: str, relative: str, ops: list[dict]) -> str:
    return owner_ops.apply_ops(
        text,
        owner_ops.parse_ops(ops, relative=relative, label="m"),
        relative=relative,
        label="m",
        placeholders=owner_ops.PlaceholderContext(1),
    )


def _with_feature(module_name: str, attribute: str):
    module = pytest.importorskip(module_name)
    if not hasattr(module, attribute):
        pytest.skip(f"{module_name} has no {attribute} yet")
    return module


ORDER_STEPS = ("silent reads and rolls", "one commit", "the whole reply")


def _assert_order_steps(items: list[str]) -> None:
    assert len(items) == 3, items
    for item, keyword in zip(items, ORDER_STEPS):
        assert keyword in item, (keyword, item)
    assert "the turn's last message" in items[2]


# ---------------------------------------------------------------------------
# Persistence order
# ---------------------------------------------------------------------------


def test_gm_spine_persists_then_narrates() -> None:
    text = _text(GM)
    titles = [title for _, title in _headings(text)]
    assert "Route -> Resolve -> Persist -> Narrate" in titles

    section = _section(text, "3. Persist And Narrate")
    _assert_order_steps(_numbered(section))
    flat = _flat(section)
    assert "The Player sees any text written before or between tool calls" in flat
    assert "Never run the commit in the background" in flat
    assert "Your reasoning is invisible" in flat
    assert "Never draft its prose first and never shorten it to a closing line" in flat
    assert "any distill that is due" in flat


def test_persistence_playbook_opens_with_the_order() -> None:
    text = _text(PERSISTENCE)
    level_two = [title for level, title in _headings(text) if level == 2]
    assert level_two[0] == "Order"
    order = _section(text, "Order")
    _assert_order_steps(_numbered(order))
    flat = _flat(order)
    assert "never run the commit in the background" in flat
    assert "the distill must finish before the reply" in flat
    assert "`reply` field" in flat and "`narrate_then_commit`" in flat and "it means this same order" in flat
    # The order is stated once, at the top, not again inside Commit Once.
    assert _flat(text).count("the whole reply, written as text") == 1


def test_reply_notes_match_the_order() -> None:
    rpg_state = _with_feature("rpg_state", "REPLY_NOTE")
    assert "whole reply" in rpg_state.REPLY_NOTE and "reasoning" in rpg_state.REPLY_NOTE
    assert "whole reply" in rpg_state.REPLY_WAIT_NOTE and "distill" in rpg_state.REPLY_WAIT_NOTE
    for note in (rpg_state.REPLY_NOTE, rpg_state.REPLY_WAIT_NOTE):
        assert note.isascii() and len(note) < 120


def test_no_shipped_instruction_ends_a_turn_on_a_tool_call() -> None:
    paths = [PLUGIN / STYLE, PLUGIN / README, PLUGIN / DISTILL, *sorted((PLUGIN / "workflows" / "gm").rglob("*.md"))]
    for path in paths:
        flat = _flat(path.read_bytes().decode("utf-8"))
        for phrase in ("write no text after", "no text after it", "with no text after"):
            assert phrase not in flat, (path.name, phrase)


def test_output_style_reply_last_limits_and_host_nudge() -> None:
    flat = _flat(_text(STYLE))
    assert "any text you write before or between tool calls becomes part of it" in flat
    assert "then write the whole reply as finished prose, the last message of the turn" in flat
    assert "never a summary of it or only its last line" in flat
    assert "one fixed, plain sentence out of character, the same sentence each time" in flat
    assert "never go a little further with each push" in flat
    assert "On the second push, explain plainly out of character" in flat
    nudge = flat[flat.index("The host may remind you") :]
    assert "had no visible output, the Player has seen nothing: send the whole reply now" in nudge
    assert "one natural waiting sentence in the Player's language" in nudge
    for word in ("saving", "records", "files", "checks", "errors", "tools"):
        assert word in nudge.split("then finish the work")[0], word


# ---------------------------------------------------------------------------
# Writer payload items (spec 2.3)
# ---------------------------------------------------------------------------


PERSISTENCE_TOKENS = (
    "next_expected_revision",
    '"expected_continuity_revision": "current"',
    "template --kind durable",
    "open_choices",
    "checkpoint_open_choices_missing",
    "commit-act",
    "upsert_row",
    "never rename the kind",
    "now_overflow_folded",
    "set_cells",
    "takes one appended dated line",
    "death_projection",
    "inventory_count_duplicate",
    "cost_unrecorded",
    "glossary_suggest",
    "record_language",
    "input_decoded_<codec>",
    "cp1254",
    "150,000 characters",
    "`rotate_log: false`",
    "omit lines whose value is `none` or empty",
)


@pytest.mark.parametrize("token", PERSISTENCE_TOKENS)
def test_persistence_documents_each_writer_payload_item(token: str) -> None:
    assert token in _flat(_text(PERSISTENCE))


def test_documented_heredoc_payloads_are_json() -> None:
    found = 0
    for path in [*sorted((PLUGIN / "workflows" / "gm").rglob("*.md")), PLUGIN / DISTILL]:
        relative = path.relative_to(PLUGIN).as_posix()
        for payload in _json_examples(relative):
            assert isinstance(payload, dict) and payload, relative
            found += 1
    assert found >= 3, "the commit-durable, commit-act, and reread examples"


def test_commit_act_prose_names_every_field_the_writer_requires() -> None:
    flat = _flat(_text(PERSISTENCE))
    marker = "`open` needs the new act's"
    prose = flat[flat.index(marker) + len(marker) : flat.index("`prepared_expectations` is optional")]
    documented = set(re.findall(r"`([a-z_]+)`", prose))
    [example] = [payload for payload in _json_examples(PERSISTENCE) if "close" in payload and "open" in payload]
    assert documented == (set(example["open"]) - {"prepared_expectations"}) | set(example["open"]["scope"])
    assert "`close.act_id` is the current Compass's act id" in flat
    rpg_state = _with_feature("rpg_state", "_parse_act")
    rpg_state._parse_act(example)
    # A payload built from the prose alone is accepted: each listed field is required.
    for field in ("act_id", "title", "dramatic_question", "scope", "closure_conditions"):
        missing = {**example, "open": {key: value for key, value in example["open"].items() if key != field}}
        with pytest.raises(rpg_state.RPGStateError):
            rpg_state._parse_act(missing)


def test_death_projection_and_glossary_suggest_follow_ups_match_the_writer() -> None:
    flat = _flat(_text(PERSISTENCE))
    death = flat[flat.index("- `death_projection`:") : flat.index("- `inventory_count_duplicate`:")]
    # The writer keeps no pending record of the warning: the next distill's gate catches the rows.
    assert "lists the path for curation" not in death
    for token in ("`cast_dead_listed`", "`relationship_dead_active`", "`distill_unreconciled`", "`deferred_reconcile`"):
        assert token in death, token
    rpg_state = _with_feature("rpg_state", "DISTILL_GATE_RULES")
    assert {"cast_dead_listed", "relationship_dead_active"} <= set(rpg_state.DISTILL_GATE_RULES)
    glossary = flat[flat.index("- `glossary_suggest`:") : flat.index("- `record_language`:")]
    assert "as it stands" not in glossary
    assert "leaves `Preferred` empty. Fill it with the play-language form" in glossary
    assert '"Preferred": ""' in inspect.getsource(rpg_state)


def test_template_kinds_match_the_writer() -> None:
    rpg_state = _with_feature("rpg_state", "TEMPLATE_KINDS")
    flat = _flat(_text(PERSISTENCE))
    match = re.search(r"template --kind durable` \(or ([^)]*)\)", flat)
    assert match
    documented = {"durable", *re.findall(r"`(\w+)`", match.group(1))}
    assert documented == set(rpg_state.TEMPLATE_KINDS)


def test_unicode_key_example_applies_to_the_state_file() -> None:
    op = _inline_json(PERSISTENCE, '{"op": "set", "values": {"player.stats.Algı"')
    state = "player:\n  stats:\n    Algı: 2\n    Sokak Zekâsı: 1\n    Will: 3\n"
    updated = _apply(state, "current_state.yaml", [op])
    assert "    Algı: 4\n" in updated and "    Sokak Zekâsı: 3\n" in updated
    assert "    Will: 3\n" in updated


def _ready_campaign(campaign: Path, *, revision: int) -> None:
    """The conftest campaign at `revision`, with an active act-2 Compass and the shipped cast tables."""

    state = campaign / "current_state.yaml"
    # Distilled at `revision`, so the durable-turn counter stays consistent with it.
    text = state.read_text(encoding="utf-8")
    for key in ("continuity_revision", "last_distilled_revision"):
        assert text.count(f"{key}: 0\n") == 1, key
        text = text.replace(f"{key}: 0\n", f"{key}: {revision}\n", 1)
    state.write_text(text, encoding="utf-8")
    log = campaign / "session_log.md"
    marker = f"\n### Distilled Through Revision {revision}\n\n- Trigger: test setup\n"
    log.write_text(log.read_text(encoding="utf-8").rstrip("\n") + "\n" + marker, encoding="utf-8")
    threads = (TEMPLATES / "threads.md").read_bytes().decode("utf-8").replace("\r\n", "\n")
    compass = {
        "- Act id:": "- Act id: act-2",
        "- Act status: planned": "- Act status: active",
        "- Opened at revision:": "- Opened at revision: 1",
        "- Act name:": "- Act name: The Council",
        "- Dramatic question:": "- Dramatic question: Will the council answer for the drownings?",
        "- Closure conditions:": "- Closure conditions: The council falls or buys its way out.",
        "- Places this act can reach:": "- Places this act can reach: the council hall, the drowned quarter",
        "- People who belong to it:": "- People who belong to it: the councillor, the harbourmaster",
        "- What is already in motion as it opens:": "- What is already in motion as it opens: the council buys silence",
        "- What stays true if the character does nothing:": "- What stays true if the character does nothing: the drownings are forgotten",
    }
    for old, new in compass.items():
        assert threads.count(old + "\n") >= 1, old
        threads = threads.replace(old + "\n", new + "\n", 1)
    # act-2 follows an archived act-1.
    threads = threads.replace("- Previous act id: none\n", "- Previous act id: act-1\n", 1)
    archive = (
        "### act-1\n\n- Act id: act-1\n- Act status: closed\n- Previous act id: none\n"
        "- Opened at revision: 0\n- Act name: Arrival\n- Dramatic question: Will Mira find work?\n"
        "- Closure conditions: Mira is hired or leaves.\n- Places this act can reach: the docks\n"
        "- People who belong to it: the quartermaster\n- What is already in motion as it opens: the crew is short\n"
        "- What stays true if the character does nothing: the ship sails without her\n- Closing action: Mira signed on.\n"
        "- Condition met or foreclosed: met\n- Recorded at revision: 1\n\n"
    )
    marker = "\n## Planted Expectations\n"
    threads = threads.replace(marker, "\n" + archive + marker.lstrip("\n"), 1)
    (campaign / "threads.md").write_text(threads, encoding="utf-8", newline="\n")


def test_commit_act_example_is_accepted_by_the_writer(campaign: Path) -> None:
    rpg_state = _with_feature("rpg_state", "commit_act")
    examples = [payload for payload in _json_examples(PERSISTENCE) if "close" in payload]
    assert len(examples) == 1
    payload = examples[0]
    assert set(payload) <= set(rpg_state.ACT_PAYLOAD_FIELDS)
    assert payload["checkpoint"]["scene_mode"] in rpg_state.SCENE_MODES
    assert 1 <= len(payload["checkpoint"]["open_choices"]) <= rpg_state.MAX_OPEN_CHOICES

    _ready_campaign(campaign, revision=4)
    result = rpg_state.commit_act(campaign, {**payload, "expected_continuity_revision": 4})
    assert result["ok"] is True
    assert result["next_expected_revision"] == 5
    threads = (campaign / "threads.md").read_text(encoding="utf-8")
    compass = _fields(_section(threads, "Arc Compass"))
    assert compass["Act id"] == "act-3" and compass["Previous act id"] == "act-2"
    assert compass["Opened at revision"] == "5"
    assert "### act-2" in _section(threads, "Act Archive")
    state = (campaign / "current_state.yaml").read_text(encoding="utf-8")
    assert "sell the ledger" in state and "hide the ledger" in state


def test_open_choices_example_is_accepted_at_a_scene_checkpoint(campaign: Path) -> None:
    rpg_state = _with_feature("rpg_state", "MAX_OPEN_CHOICES")
    flat = _flat(_text(PERSISTENCE))
    match = re.search(r'`"checkpoint": (\{[^`]*\})`', flat)
    assert match
    checkpoint = json.loads(match.group(1))
    assert checkpoint["active_cast_handoff"] == "none", "a named handoff would also need an active_cast.md mutation"
    result = rpg_state.commit_checkpoint(
        campaign,
        {"operation_id": "dock-12-pause", "expected_continuity_revision": 0, "checkpoint": checkpoint, "mutations": []},
    )
    assert result["ok"] is True
    state = (campaign / "current_state.yaml").read_text(encoding="utf-8")
    for choice in checkpoint["open_choices"]:
        assert choice in state


# ---------------------------------------------------------------------------
# Distill
# ---------------------------------------------------------------------------


def _distill_gate_rules() -> set[str]:
    gate = _flat(_section(_text(DISTILL), "Distill Gate"))
    listed = gate[gate.index("gates on these rules:") : gate.index("A gated finding")]
    return set(re.findall(r"`([a-z_]+)`", listed))


def test_distill_gate_rules_match_the_spec_and_the_writer() -> None:
    documented = _distill_gate_rules()
    assert documented == {
        "cast_dead_listed",
        "cast_present_missing",
        "relationship_dead_active",
        "location_unmapped",
        "stacked_sections",
        "now_overflow",
        "minor_romance_history",
    }
    gate = _flat(_section(_text(DISTILL), "Distill Gate"))
    assert '"distill_unreconciled"' in gate and "`deferred_reconcile`" in gate
    assert "`minor_romance_history` can never be deferred" in gate
    rpg_state = _with_feature("rpg_state", "DISTILL_GATE_RULES")
    assert documented == set(rpg_state.DISTILL_GATE_RULES)
    if hasattr(rpg_state, "UNDEFERRABLE_GATE_RULES"):
        assert set(rpg_state.UNDEFERRABLE_GATE_RULES) == {"minor_romance_history"}


def test_deferred_reconcile_example_is_well_formed() -> None:
    flat = _flat(_text(DISTILL))
    match = re.search(r'`"deferred_reconcile": (\[[^`]*\])`', flat)
    assert match
    targets = json.loads(match.group(1))
    assert targets and all(set(target) == {"path", "reason"} for target in targets)


def test_curation_due_rules_match_the_writer() -> None:
    curator = _flat(_section(_text(DISTILL), "Boundary Curator"))
    listed = curator[curator.index("post-commit check flags as") : curator.index("While")]
    documented = set(re.findall(r"`([a-z_]+)`", listed))
    assert {"now_overflow", "records_language_mismatch", "stacked_sections", "note_core_missing"} <= documented
    assert "`curation_due`" in curator and "curation_due.json" in curator
    assert "`python tools/curation.py packet campaign`" in curator
    rpg_state = _with_feature("rpg_state", "CURATION_DUE_RULES")
    # `death_projection` is a commit-durable warning that no full check emits,
    # so no distill lists a path for it; its stale rows return as gated findings.
    assert documented == set(rpg_state.CURATION_DUE_RULES) - {"death_projection"}
    for name in ("check_state", "check_content", "check_runtime"):
        assert '"death_projection"' not in inspect.getsource(pytest.importorskip(name)), name


def test_curation_packet_needs_no_target_when_notes_are_due(
    campaign: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    curation = _with_feature("curation", "due_targets")
    runtime = campaign / ".repog-runtime"
    runtime.mkdir(exist_ok=True)
    due = {
        "at": "2026-11-04T10:00:00Z",
        "revision": 0,
        "targets": [{"path": "characters/witness.md", "rule": "stacked_sections", "reason": "fold the dated sections"}],
    }
    (runtime / "curation_due.json").write_text(json.dumps(due), encoding="utf-8")
    # The command exactly as the distill workflow gives it, with no --target.
    assert curation.main(["packet", str(campaign)]) == 0
    packet = json.loads(capsys.readouterr().out)
    assert packet["ok"] is True
    assert "characters/witness.md" in json.dumps(packet)


def test_an_extra_packet_target_keeps_the_notes_due(campaign: Path, capsys: pytest.CaptureFixture[str]) -> None:
    curator = _flat(_section(_text(DISTILL), "Boundary Curator"))
    assert "add `--target PATH=REASON`; the packet holds it beside every due note, never in their place" in curator
    curation = _with_feature("curation", "due_targets")
    (campaign / "places" / "harbor.md").write_text("# Harbor\n\n## Now\n\nQuiet.\n", encoding="utf-8")
    runtime = campaign / ".repog-runtime"
    runtime.mkdir(exist_ok=True)
    due = {
        "at": "2026-11-04T10:00:00Z",
        "revision": 0,
        "targets": [{"path": "characters/witness.md", "rule": "stacked_sections", "reason": "fold the dated sections"}],
    }
    (runtime / "curation_due.json").write_text(json.dumps(due), encoding="utf-8")
    # The extra file the workflow's example names, beside the due note.
    assert curation.main(["packet", str(campaign), "--target", "places/harbor.md=owner_size_budget"]) == 0
    packet = json.loads(capsys.readouterr().out)
    assert {target["path"] for target in packet["targets"]} == {"places/harbor.md", "characters/witness.md"}


def test_distill_runs_before_the_reply_and_reads_whole_results() -> None:
    text = _text(DISTILL)
    full = _flat(_section(text, "Full Distill"))
    assert "A full distill runs before the reply, in the same turn and in the foreground" in full
    assert "never filter helper output through `grep`, `head`, or `tail`" in full
    assert '`expected_continuity_revision` (the number, or `"current"`)' in full
    for field in ("`curation_due`", "`lint_report`", "`next_expected_revision`"):
        assert field in full
    assert "rotates on its own" in full and "`rotate_log: false`" in full
    variety = _flat(_section(text, "Narration Variety Review"))
    assert variety.startswith("With `runtime.presentation_lint: on`, the review is the `lint_report`")
    assert "presentation_lint.py report" not in text
    lint_on = variety[: variety.index("With the lint off")]
    assert "`check_style` and `presentation_lint report` are not separate distill steps" in lint_on
    # check_style runs only with the lint off, the only case the full check warns
    # about an empty style state; under the lint, style_state.json is left alone.
    assert "python tools/check_style.py" not in lint_on and "style_state_inert" not in lint_on
    assert "`style_state.json` stays as it is" in lint_on
    lint_off = variety[variety.index("With the lint off") :]
    assert lint_off.startswith("With the lint off, and only then, `tools/check_style.py` keeps that memory")
    assert "only then can the full check warn `style_state_inert`" in lint_off
    voice = _flat(_section(_text(GM), "Voice Continuity Prerequisites"))
    assert "With the lint off, and only then, `style_state.json` holds that memory" in voice
    assert "only then does the full check warn `style_state_inert`" in voice
    assert "style_state_inert" not in voice[: voice.index("With the lint off")]


def _documented_check_style_argv(state: Path) -> list[str]:
    """The distill workflow's check_style command, placeholders filled, with a sample reply."""

    command = re.search(r"(?m)^python tools/check_style\.py (.*?) --text ", _text(DISTILL))
    assert command, "the Narration Variety Review gives the check_style command"
    fill = {"campaign/style_state.json": str(state), "SCENE_ID": "dock-interview", "BEAT_ID": "b8", "LABEL": "pressure"}
    argv = [fill.get(word, word) for word in command.group(1).split()]
    return [*argv, "--text", "The witness looks at the water and says nothing."]


def test_check_style_runs_only_with_the_lint_off(campaign: Path, capsys: pytest.CaptureFixture[str]) -> None:
    check_state = pytest.importorskip("check_state")
    check_style = pytest.importorskip("check_style")
    _with_feature("check_runtime", "lint_keeps_style_memory")
    state = campaign / "style_state.json"
    shutil.copy(TEMPLATES / "style_state.json", state)
    current = campaign / "current_state.yaml"
    played = current.read_text(encoding="utf-8").replace("continuity_revision: 0", "continuity_revision: 8", 1)
    current.write_text(played.replace("last_distilled_revision: 0", "last_distilled_revision: 8", 1), encoding="utf-8")

    def inert() -> bool:
        findings = check_state.check_campaign(campaign, scope="full")["findings"]
        return any(finding["rule"] == "style_state_inert" for finding in findings)

    # The fixture has no runtime block, so the lint is on and keeps the memory:
    # the empty style state the workflows leave alone draws no warning.
    assert not inert()
    # With the lint off, check_style keeps it: one documented sample clears the warning.
    profile = campaign / "play_profile.yaml"
    profile.write_text(profile.read_text(encoding="utf-8") + "runtime:\n  presentation_lint: off\n", encoding="utf-8")
    assert inert()
    assert check_style.main(_documented_check_style_argv(state)) == 0
    capsys.readouterr()
    assert not inert()


def test_lint_report_summary_matches_the_lint_contract() -> None:
    presentation_lint = _with_feature("presentation_lint", "report_summary")
    parameters = inspect.signature(presentation_lint.report_summary).parameters
    assert parameters["last"].default == 20
    assert "last 20 replies" in _flat(_section(_text(DISTILL), "Narration Variety Review"))


# ---------------------------------------------------------------------------
# Rolls: action and OOC playbooks
# ---------------------------------------------------------------------------


def test_action_conflict_rolls_only_real_risk() -> None:
    text = _text(ACTION)
    when = _flat(_section(text, "When Not To Roll"))
    assert "under about 15%, or nil, do not roll" in when
    assert "returns `certain`, with the warning `roll_certain`" in when
    assert "recorded at its floor band" in when
    declare = _flat(_section(text, "Declare Before Rolling"))
    assert "Factors cut both ways" in declare
    assert "Size each factor 2 to 6" in declare
    assert "describe every band the call can reach below success and no band it cannot reach" in declare
    assert "`stakes_unreachable_band`" in declare and "`stakes_missing_band`" in declare
    assert "show the receipt's `display` line as it stands" in declare
    crowds = _flat(_section(text, "Crowds And Named Enemies"))
    assert "a negative small-edge factor (-2 at the default sizes) for each doubling of the opponents" in crowds
    assert "several exchanges" in crowds and "alarm clock" in crowds
    assert "A named enemy rolls separately from the extras" in crowds


def test_dice_warnings_named_in_the_playbook_exist_in_the_tool() -> None:
    roll_dice = _with_feature("roll_dice", "reread")
    source = inspect.getsource(roll_dice)
    for rule in ("roll_certain", "stakes_unreachable_band", "stakes_missing_band", '"display"', '"certain"'):
        assert rule in source, rule


def test_ooc_dice_change_shows_odds_and_rereads(campaign: Path) -> None:
    text = _text(OOC)
    dice = _flat(_section(text, "Change The Dice Scale"))
    assert "the die, the bands, the automatic-success margin, the factor sizes, or the difficulty formula" in dice
    assert "Show the odds before and after on the campaign's real matchups" in dice
    assert 'Offer "from the next roll" first' in dice
    assert "one reread row, never by editing its receipt" in dice
    rereads = _json_examples(OOC)
    assert len(rereads) == 1 and set(rereads[0]) == {"roll_id", "reason", "new_band"}

    roll_dice = _with_feature("roll_dice", "reread")
    # The documented subcommands parse as written.
    assert "--campaign campaign reread --input-file -" in dice
    with pytest.raises(SystemExit) as parsed:
        roll_dice.main(["--campaign", str(campaign), "reread"])
    assert parsed.value.code == 2, "reread needs a request"
    assert roll_dice.main(["--campaign", str(campaign), "axes", "--since-revision", "0"]) == 0


def test_axes_command_in_the_arc_playbook_runs(campaign: Path, capsys: pytest.CaptureFixture[str]) -> None:
    roll_dice = _with_feature("roll_dice", "axes")
    flat = _flat(_text(ARC))
    command = re.search(r"`python tools/roll_dice\.py ([^`]+)`", flat).group(1)
    assert command == "--campaign campaign axes --since-revision N"
    argv = [{"campaign": str(campaign), "N": "0"}.get(token, token) for token in command.split()]
    assert roll_dice.main(argv) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["ok"] is True and output["axes"] == []


def test_ooc_language_complaint_and_retro_edit() -> None:
    text = _text(OOC)
    language = _flat(_section(text, "Answer A Language Complaint"))
    assert "acknowledge it in one line, then rewrite the last reply in the same turn" in language
    assert "`narration.narrative_signature.avoid_habits`" in language
    assert "as an example under the language directive in `directives.md`" in language
    amend = _flat(_section(text, "Amend The Last Beat"))
    assert '"Write it as if I said it there"' in amend
    assert "amend that beat through one commit" in amend
    assert "show the Player the amended line as it now stands" in amend


# ---------------------------------------------------------------------------
# Act transitions and time skips
# ---------------------------------------------------------------------------


def test_scene_arc_transition_closes_through_commit_act() -> None:
    text = _text(ARC)
    flat = _flat(text)
    assert "Close the act only after the scene that answered it has ended, never in the middle of an exchange" in flat
    assert "Set `Act status: closed` in the same `commit-durable`" not in flat
    activate = _flat(_section(text, "Activate The Successor"))
    assert "make one `commit-act` call" in activate
    assert "Never hand-build the archive or the Compass" in activate
    review = _section(text, "Act-Close Review")
    steps = _numbered(review)
    assert len(steps) == 3
    assert "Agency Card and Depth of every T2/T3 character seen in the act" in steps[0]
    for owner in ("`issues.md`", "`world_dynamics.md`", "Planted Expectations"):
        assert owner in steps[1]
    assert "world_pulse.py" in steps[1] and "`active_clocks`" in steps[1]
    for item in ("before and after the award", "a suggested allocation", "time-skip options"):
        assert item in steps[2]
    assert "`changes` and `mutations` of the `commit-act` call itself" in _flat(review)
    advancement = _flat(_section(text, "Advancement"))
    assert "go only to axes the character actually rolled in it" in advancement
    assert "past the region cap in `progression.md`" in advancement


def test_advancement_playbook_defers_act_awards_to_commit_act() -> None:
    flat = _flat(_text("workflows/gm/playbooks/advancement.md"))
    assert "A stat award goes only to axes the character actually rolled in the closing act" in flat
    assert "never past the region cap in `progression.md`" in flat
    assert "At an act close they ride in that act's `commit-act` call instead" in flat


def test_full_distill_triggers_follow_the_profile_policy() -> None:
    for relative in (ARC, DISTILL):
        flat = _flat(_text(relative))
        assert "Balanced reaches three" not in flat and "three durable turns for Balanced" not in flat
        assert "`scene_checkpoint_or_5_durable` (Fast and Balanced)" in flat
        assert "under `scene_checkpoint_or_3_durable`" in flat


def test_travel_downtime_time_skip_brief() -> None:
    text = _text(TRAVEL)
    brief = _section(text, "Time-Skip Brief")
    assert list(_fields(brief)) == ["Span", "Stops", "Accounts", "In or out"]
    flat = _flat(brief)
    assert "sectioned montage: one short section per stop" in flat
    assert "about 800 words unless the Player asks for more" in flat
    assert "The commit comes first, and the montage is the turn's last message" in flat
    until = _flat(_section(text, "Skip Until Something Happens"))
    assert "until the first established trigger fires" in until and "Nothing is invented" in until
    clocks = _flat(_section(text, "Timed Threats"))
    assert "`active_clocks` entry in `current_state.yaml`" in clocks
    assert "At an act close, run `python tools/world_pulse.py --input-file -`" in clocks
    resolving = _numbered(_section(text, "Resolving The Skip"))
    assert "Commit the skip" in resolving[2] and "`open_choices`" in resolving[2]
    assert "Write the montage as the reply" in resolving[3]


def test_visuals_playbook_is_routed_and_bounded() -> None:
    assert "`playbooks/visuals.md`" in _section(_text(GM), "Triggered Playbooks")
    data = (PLUGIN / VISUALS).read_bytes()
    assert b"\r" not in data
    flat = _flat(data.decode("utf-8"))
    for rule in (
        "State an adult age for every person in the image",
        "Frame everyone clothed and the scene non-explicit",
        "Never depict an intimate scene or its aftermath",
        "Never describe a character in a romantic relationship as young-looking, innocent",
        "Never ask for the likeness of a real person",
        "Write the prompt after the narration it illustrates",
        "Check the prompt against the records before showing it",
        "follow that provider's policy and the Player's account there",
        "Never change the Player's tool configuration",
    ):
        assert rule in flat, rule


def test_every_triggered_playbook_exists() -> None:
    triggered = _section(_text(GM), "Triggered Playbooks")
    names = re.findall(r"`playbooks/([a-z_]+\.md)`", triggered)
    assert "visuals.md" in names
    for name in names:
        assert (PLUGIN / "workflows" / "gm" / "playbooks" / name).is_file(), name


# ---------------------------------------------------------------------------
# Records language and the age rule
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative", [GM, PERSISTENCE, DISTILL, CREATION, CHARACTER, "workflows/reference/authority-map.md"])
def test_records_language_is_documented_where_records_are_written(relative: str) -> None:
    flat = _flat(_text(relative))
    assert "records_language" in flat
    assert "play language when it is `same`" in flat
    assert "headings" in flat and "enum values" in flat


def test_character_template_depth_and_distinct_appearance() -> None:
    text = _text(CHARACTER)
    assert list(_fields(_section(text, "Distinct Appearance"))) == ["Face", "Height", "Build", "Silhouette", "Signature detail"]
    depth = _section(text, "Depth")
    assert list(_fields(depth)) == [
        "Backstory",
        "Contradiction",
        "Want and need",
        "Fear",
        "Dream",
        "Joys and habits",
        "Voice signature",
        "How they could change",
        "GM-only secret",
    ]
    # The age rule is one line in the Depth guidance, inside a comment so its
    # romance terms never sit beside an age the note's own lines give.
    rules = [line for line in depth.splitlines() if line.startswith("<!-- Age rule:")]
    assert len(rules) == 1 and rules[0].endswith(" -->")
    assert "no romantic or sexual relationship in this character's past or present begins before 18" in rules[0]
    assert "recheck every dated line" in rules[0]
    assert "not from a named canon figure" in _flat(depth)
    assert "records_language" in _flat(text.split("## Core", 1)[0])


def test_capsule_reads_the_template_voice_signature() -> None:
    scene_capsule = pytest.importorskip("scene_capsule")
    source = inspect.getsource(scene_capsule)
    if "Voice signature" not in source:
        pytest.skip("scene_capsule does not read the Depth voice signature yet")
    assert "- Voice signature:" in _section(_text(CHARACTER), "Depth")


def test_template_note_is_not_flagged_by_the_age_or_language_checks(tmp_path: Path) -> None:
    check_state = pytest.importorskip("check_state")
    campaign = tmp_path / "campaign"
    shutil.copytree(TEMPLATES, campaign)
    # An English campaign: the template's English guidance is in the records language.
    profile = campaign / "play_profile.yaml"
    profile.write_bytes(profile.read_bytes().replace(b"  language: auto", b"  language: en", 1))
    note = _text(CHARACTER).replace("# Character Name", "# Edda Vale", 1)
    note = note.replace("Tier: T1/T2/T3", "Tier: T2", 1)
    note = note.replace("- Status: alive | dead | missing | unknown", "- Status: alive", 1)
    (campaign / "characters" / "edda_vale.md").write_text(note, encoding="utf-8", newline="\n")
    findings = check_state.check_campaign(campaign, scope="full")["findings"]
    rules = {finding["rule"] for finding in findings if "edda_vale" in str(finding.get("path", ""))}
    assert "minor_romance_history" not in rules
    assert not [finding for finding in findings if finding["rule"] == "records_language_mismatch"]


@pytest.mark.parametrize(
    ("label", "value", "romance"),
    [
        ("Backstory", "Orphaned at twelve on the docks.", "Her first kiss came then."),
        ("Backstory", "On iki yaşında öksüz kaldı, rıhtımda büyüdü.", "İlk öpücüğü de o yıl oldu."),
        ("GM-only secret", "Her brother drowned at fourteen.", "Her first kiss came then."),
    ],
)
def test_a_child_age_in_a_template_note_is_not_a_romance_finding(tmp_path: Path, label: str, value: str, romance: str) -> None:
    check_state = pytest.importorskip("check_state")
    check_content = _with_feature("check_content", "minor_proximity")
    campaign = tmp_path / "campaign"
    shutil.copytree(TEMPLATES, campaign)
    note = _text(CHARACTER).replace("# Character Name", "# Edda Vale", 1)
    note = note.replace("- Status: alive | dead | missing | unknown", "- Status: alive", 1)
    note = note.replace(f"- {label}:\n", f"- {label}: {value}\n", 1)
    assert value in note
    # The check reads this note: a romance term in the same language beside the same age is still found.
    assert check_content.minor_proximity(note.replace(value, f"{value} {romance}", 1))
    (campaign / "characters" / "edda_vale.md").write_text(note, encoding="utf-8", newline="\n")
    findings = check_state.check_campaign(campaign, scope="full")["findings"]
    assert not [finding for finding in findings if finding["rule"] == "minor_romance_history"]


def test_creation_reference_depth_appearance_and_canon() -> None:
    flat = _flat(_text(CREATION))
    assert "`## Distinct Appearance`: face, height, build, silhouette, and one signature detail" in flat
    assert "`## Depth`: backstory, contradiction, want and need, fear, dream, joys and habits, voice signature" in flat
    assert "give no new character a backstory built on a named canon figure, event, or place unless the Player asks" in flat
    assert "No romantic or sexual relationship in the backstory begins before 18" in flat


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


def test_rules_template_scale_tier_caps_and_factors() -> None:
    text = _text("templates/campaign/rules.md")
    scale = _section(text, "Numeric Stat Scale").split("### Declared Stat Axes", 1)[0]
    assert _fields(scale).get("Numeric scale") == ""
    assert "region-anchored open scale" in _flat(scale)
    assert _fields(scale).get("Region anchors") == ""
    # A blank scale line is never followed by digits a reader could take for its value.
    following = scale.split("- Numeric scale:", 1)[1].lstrip()
    assert not following[:1].isdigit()
    assert _fields(_section(text, "Tier Caps")) == {"T1": "", "T2": "", "T3": ""}
    factors = _flat(_section(text, "Factors And Crowds"))
    assert "Factors cut both ways" in factors and "Size each factor 2 to 6" in factors
    assert "(-2 at the default sizes) for each doubling of the opponents" in factors
    assert "A named enemy rolls separately" in factors
    assert "under about 15%" in factors
    resolution = _flat(_section(text, "Resolution Scale"))
    assert "recorded at the band its lowest roll would reach, or at the lowest success band" in resolution
    assert "The lowest success band is the one a margin of zero lands in" in resolution
    assert "minus the lowest roll, one per die" in resolution
    assert "the first band applies without a roll" not in resolution
    assert "first success band" not in resolution
    # 0.4.0 dice never roll a certain call, whatever the margin.
    assert "`certain`: it never rolls, whatever the margin" in resolution
    assert "rolls calls that cannot fail" not in resolution
    assert "a higher one adds nothing, and the full check flags it as `auto_success_dead_zone`" in resolution


def test_rules_tier_caps_are_read_by_the_full_check(tmp_path: Path) -> None:
    check_state = pytest.importorskip("check_state")
    _with_feature("check_content", "tier_caps")
    rules = (TEMPLATES / "rules.md").read_bytes()
    for line in (b"- T1:", b"- T2:", b"- T3:"):
        assert rules.count(line + b"\r\n") == 1

    def warnings(cap: str = "", *, band: str = "", acknowledge: str = "") -> list[dict]:
        """Full-check findings on a T1 note with Power 3, in a numeric copy of the template."""

        campaign = tmp_path / f"t1-{cap}-{band}-{acknowledge}"
        shutil.copytree(TEMPLATES, campaign)
        profile = campaign / "play_profile.yaml"
        numeric = profile.read_bytes().replace(b"resolution_grounding: fictional", b"resolution_grounding: numeric", 1)
        profile.write_bytes(numeric)
        capped = rules.replace(b"- T1:\r\n", f"- T1: {cap}\r\n".encode("utf-8"), 1) if cap else rules
        (campaign / "rules.md").write_bytes(capped)
        note = (
            f"# Edda Vale\n\nTier: T1\n\nPower Band: {band}\n\n## Core\n\n- Status: alive\n\n"
            "## Stats (Numeric Grounding Only)\n\n- Power: 3\n- Wits: 1\n"
        )
        (campaign / "characters" / "edda_vale.md").write_text(note, encoding="utf-8")
        if acknowledge:
            row = f"| D-001 | check | acknowledge {acknowledge} for characters/edda_vale.md | OOC request, revision 2 | active |\n"
            directives = campaign / "directives.md"
            directives.write_bytes(directives.read_bytes() + row.encode("utf-8"))
        findings = check_state.check_campaign(campaign, scope="full")["findings"]
        return [finding for finding in findings if "edda_vale" in str(finding.get("path", ""))]

    # Blank caps keep the defaults, under which a T1 at 3 is ordinary.
    assert not [finding for finding in warnings() if finding["severity"] == "warning"]
    over = [finding for finding in warnings("2") if finding["severity"] == "warning"]
    assert len(over) == 1 and "Power 3" in over[0]["message"]
    # A higher cap, or a Power Band that covers the stat, answers it ...
    assert not [finding for finding in warnings("3") if finding["severity"] == "warning"]
    assert not [finding for finding in warnings("2", band="3") if finding["severity"] == "warning"]
    # ... and so does a `check` directive, which keeps it visible as info.
    acknowledged = warnings("2", acknowledge=over[0]["rule"])
    assert [(finding["severity"], finding.get("acknowledged_by")) for finding in acknowledged] == [("info", "D-001")]


def test_progression_template_awards_region_cap_and_mastery() -> None:
    text = _text("templates/campaign/progression.md")
    awards = _flat(_section(text, "Awards Follow Rolled Axes"))
    assert "go to the axes the character actually rolled in that act" in awards
    assert "`python tools/roll_dice.py --campaign campaign axes --since-revision N`" in awards
    cap = _section(text, "Region Cap")
    assert list(_fields(cap)) == ["Current region", "Axis cap here", "Mastery cap here", "What raises it"]
    assert "unless the Player explicitly accepts the overreach" in _flat(cap)
    mastery = _section(text, "Signature Power Mastery")
    header = next(line for line in mastery.splitlines() if line.startswith("| Level"))
    assert [cell.strip() for cell in header.strip("|").split("|")] == [
        "Level",
        "Reach",
        "What it can affect",
        "How many at once",
        "Largest factor it adds",
    ]
    assert "Use inside the current level costs nothing beyond its fiction" in _flat(mastery)
    assert "leaves a condition such as fatigue" in _flat(mastery)
    assert (TEMPLATES / "progression.md").read_bytes().count(b"\n") == (TEMPLATES / "progression.md").read_bytes().count(b"\r\n")


def test_player_template_wishes() -> None:
    wishes = _section(_text("templates/campaign/player.md"), "Wishes")
    flat = _flat(wishes)
    assert "recorded as the character's own aims" in flat
    assert "A wish is never an NPC promise, a scheduled event, or a guarantee" in flat
    assert list(_fields(wishes)) == ["Wish"]


def test_play_profile_records_language_and_policy_comments() -> None:
    text = (TEMPLATES / "play_profile.yaml").read_bytes().decode("utf-8")
    assert repog_runtime.block_scalars(text, "narration")["records_language"] == "same"
    flat = _flat(text)
    assert "# narration.records_language: same | a language code" in flat
    assert "Fast and Balanced use # scene_checkpoint_or_5_durable" in flat
    comments = _flat(re.sub(r"(?m)^\s*#", "", text))
    assert "The lowest success band is the one a margin of 0 lands in" in comments
    assert "the at_least of the lowest success band (where a margin of 0 lands) minus the lowest roll" in comments
    assert "first band's at_least" not in comments
    assert "rolls calls that cannot fail" not in comments
    assert "a higher one adds nothing, and the full check flags it as auto_success_dead_zone" in comments
    check_content = pytest.importorskip("check_content")
    if hasattr(check_content, "records_language"):
        # `same` follows narration.language, which the blank template leaves on auto.
        assert check_content.records_language(text) == ""
        assert check_content.records_language(text.replace("language: auto", "language: tr", 1)) == "tr"


def test_system_fit_balanced_profile_matches_the_play_profile_comment() -> None:
    flat = _flat(_text("templates/campaign/system_fit.md"))
    assert "after at most five durable turns (`scene_checkpoint_or_5_durable`)" in flat


def test_glossary_seeding_guidance() -> None:
    text = _text("templates/campaign/glossary.md")
    flat = _flat(text.split("## Rendering Policy", 1)[0])
    assert "Seed it at the first translated name" in flat
    assert "`glossary_suggest`" in flat
    # The writer's row leaves Preferred empty; it is not ready to commit as it stands.
    assert "fill its `Preferred` with the play-language form before committing it" in flat
    assert "ready row" not in flat


def test_directives_check_rows_are_documented_and_read(tmp_path: Path) -> None:
    text = _text("templates/campaign/directives.md")
    flat = _flat(text)
    assert "or `check`, for a row addressed to the full check" in flat
    assert "begins with `acknowledge <rule_id>`, optionally followed by `for <path or name>`" in flat
    assert "`(acknowledged by D-NNN)`" in flat
    assert "Only warnings can be acknowledged, never errors" in flat
    row = "| {{next_id:D}} | check | acknowledge power_band_mismatch for characters/branak.md | OOC request, revision 9 | active |"
    updated = _apply(text, "directives.md", [{"op": "append", "heading": "Standing Directives", "text": row}])
    curation = pytest.importorskip("curation")
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    (campaign / "directives.md").write_text(updated, encoding="utf-8", newline="")
    assert curation.active_directives(campaign) == [
        {"id": "D-001", "scope": "check", "directive": "acknowledge power_band_mismatch for characters/branak.md"}
    ]


def test_threads_template_closes_acts_through_commit_act() -> None:
    text = _text("templates/campaign/threads.md")
    record = _flat(_section(text, "Closure Record"))
    assert "by the `commit-act` call made after the scene that answered it has ended" in record
    assert "Mark the Compass `closed` in the same owner transaction" not in record
    assert "one `commit-act` call archives the closing Compass" in _flat(_section(text, "Arc Compass"))


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------


def test_readme_warning_text_in_both_languages() -> None:
    section = _section(_text(README), "Adults Only, Content, And Safety")
    quotes = [" ".join(line.lstrip("> ").strip() for line in block.splitlines()) for block in re.findall(r"(?m)((?:^>.*\n?)+)", section)]
    assert len(quotes) == 2
    english, turkish = quotes
    assert english.startswith("**Before you play.** RePoG is for adults 18+ only")
    assert "Sexual content involving anyone under 18 is never written, not even in a backstory." in english
    assert "rewind with `/rewind` or start a new session" in english
    assert turkish.startswith("**Oynamadan önce.** RePoG yalnızca 18 yaş üstü içindir")
    assert "18 yaşından küçük biriyle ilgili cinsel içerik, geçmiş hikâyede bile olsa, hiçbir koşulda yazılmaz." in turkish
    assert "`/rewind` ile geri al" in turkish
    flat = _flat(section)
    assert "no one under 18 appears in any sexual or romantic context, backstory included" in flat
    assert "open, fade, or avoid" not in flat


def test_readme_hook_disclosure_names_what_is_stored() -> None:
    flat = _flat(_text(README))
    assert "reads the current session's last turn" in flat
    assert "It stores counts and short snippets, never full text" in flat
    assert "your message's language code" in flat
    assert "first 300 characters" not in flat
    assert "`campaign/.repog-runtime/curation_due.json`" in flat
    assert "the last turn's order" in flat and "`order_last.json`" in flat
    assert "After a compaction or a resume it also prints up to 1,500 characters" in flat

"""0.4.0 full-check rules: meaningful staleness, content rules, odds, and acknowledgement.

Every campaign here is synthetic and built inside a temporary folder.
"""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

import pytest

import check_content
import check_runtime
import check_state
import lang_pack
import odds


TOOLS = Path(check_state.__file__).resolve().parent

CAST_HEADER = (
    "| NPC | Tier | Current location | Current activity | Immediate objective | Availability | Reason here "
    "| Next move if ignored | Last seen | Revision |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |\n"
)
RELATION_HEADER = (
    "| From | Direction | To | Relation | Status | Trust / debt / tension | Knowledge asymmetry | Player-known "
    "| Last changed | Revision |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |\n"
)
GRAPH_HEADER = (
    "| From | Direction | To | Travel | Access | Visibility | Ordinary traffic | Conditions | Player-known "
    "| Last changed |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
)
DIRECTIVES_HEADER = "| Id | Scope | Directive | Source | Status |\n| --- | --- | --- | --- | --- |\n"

ENGLISH_BODY = (
    "Edda mends the nets every morning and she waits for the boats that come back late from the reef. "
    "She does not trust the harbor master, but she pays him on time because the fishermen need her work, "
    "and she keeps her own counsel when they ask about the storm."
)
TURKISH_BODY = (
    "Edda her sabah ağları onarıyor ve resiften geç dönen tekneleri bekliyor. Liman reisine güvenmiyor "
    "ama balıkçıların ona ihtiyacı olduğu için parasını zamanında ödüyor. Yine de onu hiç sevmiyor çünkü "
    "geçen kış ona yalan söyledi ve bunu hâlâ unutmadı."
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _rules(findings: list[dict], rule: str) -> list[dict]:
    return [finding for finding in findings if finding["rule"] == rule]


def _full(campaign: Path) -> list[dict]:
    return check_state.check_campaign(campaign, scope="full")["findings"]


def _character(campaign: Path, name: str, *, status: str = "alive", tier: str = "T2", extra: str = "") -> Path:
    path = campaign / "characters" / f"{name.lower().replace(' ', '_')}.md"
    _write(path, f"# {name}\n\nTier: {tier}\n\nPower Band:\n\n## Core\n\n- Status: {status}\n\n{extra}")
    return path


def _set_state(campaign: Path, *, revision: int | None = None, present: list[str] | None = None) -> None:
    path = campaign / "current_state.yaml"
    text = path.read_text(encoding="utf-8")
    if revision is not None:
        text = text.replace("continuity_revision: 0", f"continuity_revision: {revision}", 1)
    if present is not None:
        text = text.replace("  present_npcs: []", "  present_npcs: [" + ", ".join(present) + "]", 1)
    _write(path, text)


def _numeric(campaign: Path) -> None:
    path = campaign / "play_profile.yaml"
    _write(path, path.read_text(encoding="utf-8") + "mechanics:\n  resolution_grounding: numeric\n")


def _profile_language(campaign: Path, language: str, records: str | None = None) -> None:
    path = campaign / "play_profile.yaml"
    narration = f"narration:\n  language: {language}\n" + (f"  records_language: {records}\n" if records else "")
    _write(path, path.read_text(encoding="utf-8") + narration)


@pytest.fixture()
def memory(campaign: Path) -> Path:
    """The shared campaign plus every Lite V2 owner, all at revision 0."""

    _write(campaign / "places" / "old_dock.md", "# Old Dock\n\nTier: T1\n")
    _write(campaign / "places" / "fish_market.md", "# Fish Market\n\nTier: T1\n")
    _write(
        campaign / "active_cast.md",
        "# Active Cast\n\nAs of revision: 0\n\n" + CAST_HEADER
        + "| Witness | T2 | old_dock | waiting | talk | now | interview | leave | r0 | 0 |\n",
    )
    _write(
        campaign / "location_graph.md",
        "# Location Graph\n\nAs of revision: 0\n\n" + GRAPH_HEADER
        + "| old_dock | <-> | Fish Market | short walk | public | open | porters | none | yes | setup |\n",
    )
    _write(
        campaign / "relationship_map.md",
        "# Relationship Map\n\nAs of revision: 0\n\n" + RELATION_HEADER
        + "| Mira | -> | Witness | informant | active | wary | none | yes | setup | 0 |\n",
    )
    _write(campaign / "session_brief.md", "# Session Brief\n\nPrepared from revision: 0\n")
    return campaign


# ---------------------------------------------------------------------------
# Size budget
# ---------------------------------------------------------------------------


def test_check_state_stays_under_its_size_budget() -> None:
    assert (TOOLS / "check_state.py").stat().st_size < 250_000


# ---------------------------------------------------------------------------
# 4.1 Meaningful staleness
# ---------------------------------------------------------------------------


STALE_RULES = ("active_cast_stale", "location_graph_stale", "relationship_map_stale", "session_brief_stale")


def test_revision_lag_alone_is_no_longer_a_warning(memory: Path) -> None:
    _set_state(memory, revision=25)
    findings = _full(memory)
    assert [finding for finding in findings if finding["rule"] in STALE_RULES] == []


def test_revision_lag_over_25_is_info_under_the_old_rule_names(memory: Path) -> None:
    _set_state(memory, revision=26)
    findings = _full(memory)
    stale = {finding["rule"]: finding for finding in findings if finding["rule"] in STALE_RULES}
    assert set(stale) == set(STALE_RULES)
    assert {finding["severity"] for finding in stale.values()} == {"info"}
    assert "by more than 25" in stale["active_cast_stale"]["message"]


def test_cast_dead_listed_flags_a_dead_character_still_present(memory: Path) -> None:
    _character(memory, "Edda Vale", status="dead")
    _character(memory, "Brannoc", status="missing")
    _character(memory, "Corin", status="alive")
    rows = (
        "| Edda Vale | T2 | Fish Market | mending nets | sell | mornings | trade | close | r3 | 3 |\n"
        "| Brannoc | T2 | old_dock | drinking | gossip | evenings | habit | sleep | r3 | 3 |\n"
        "| Corin | T2 | old_dock | waiting | talk | now | interview | leave | r3 | 3 |\n"
    )
    _write(memory / "active_cast.md", (memory / "active_cast.md").read_text(encoding="utf-8") + rows)
    found = _rules(check_content.check_memory(memory, location="old_dock", present_npcs=[]), "cast_dead_listed")
    assert [(finding["severity"], Path(finding["path"]).name) for finding in found] == [
        ("warning", "active_cast.md"),
        ("warning", "active_cast.md"),
    ]
    assert "Edda Vale is dead" in found[0]["message"] and "Brannoc is missing" in found[1]["message"]


@pytest.mark.parametrize(
    "availability",
    ["dead since the raid", "left for the capital", "gone", "öldü", "ayrıldı", "parti pour Paris"],
)
def test_cast_dead_listed_accepts_a_row_marked_gone(memory: Path, availability: str) -> None:
    _character(memory, "Edda Vale", status="dead")
    row = f"| Edda Vale | T2 | Fish Market | - | - | {availability} | - | - | r3 | 3 |\n"
    _write(memory / "active_cast.md", (memory / "active_cast.md").read_text(encoding="utf-8") + row)
    assert _rules(check_content.check_memory(memory, location="old_dock", present_npcs=[]), "cast_dead_listed") == []


def test_cast_present_missing_replaces_the_t1_presence_warning_in_a_full_check(memory: Path) -> None:
    _character(memory, "Corin", tier="T1")
    _set_state(memory, present=["Witness", "Corin"])
    findings = _full(memory)
    missing = _rules(findings, "cast_present_missing")
    assert [finding["severity"] for finding in missing] == ["warning"]
    assert "Corin" in missing[0]["message"] and Path(missing[0]["path"]).name == "active_cast.md"
    assert _rules(findings, "present_t1_presence_untracked") == []
    # The hot check keeps its own warning.
    hot = check_state.check_campaign(memory, scope="hot")["findings"]
    assert _rules(hot, "present_t1_presence_untracked")


def test_cast_present_missing_matches_names_in_any_script(memory: Path) -> None:
    _write(
        memory / "active_cast.md",
        "# Active Cast\n\n" + CAST_HEADER + "| Çağan İlse | T1 | old_dock | x | x | x | x | x | r1 | 1 |\n",
    )
    found = check_content.check_memory(memory, location="old_dock", present_npcs=["çağan ilse", "Ömer"])
    assert [finding["message"].split(",")[0] for finding in _rules(found, "cast_present_missing")] == [
        "current_scene.present_npcs names Ömer"
    ]


def test_relationship_dead_active(memory: Path) -> None:
    _character(memory, "Witness", status="dead")
    found = _rules(check_content.check_memory(memory, location="old_dock", present_npcs=[]), "relationship_dead_active")
    assert len(found) == 1 and Path(found[0]["path"]).name == "relationship_map.md"
    assert "Witness" in found[0]["message"]
    for state in ("dead", "ended", "past", "geçmiş", "sona erdi"):
        _write(
            memory / "relationship_map.md",
            "# Relationship Map\n\n" + RELATION_HEADER + f"| Mira | -> | Witness | informant | {state} | - | - | yes | r4 | 4 |\n",
        )
        assert _rules(check_content.check_memory(memory, location="", present_npcs=[]), "relationship_dead_active") == []


@pytest.mark.parametrize(
    ("availability", "gone"),
    [
        ("öldürüldü", True),
        ("ölmüş, gömüldü", True),
        ("kayboldu", True),
        ("vefat etti", True),
        ("artık yok", True),
        ("died in the raid", True),
        ("killed on day 12", True),
        ("disappeared at sea", True),
        # Look-alike words are not gone.
        ("ölçü alıyor", False),
        ("ölçek tutuyor", False),
        ("Halvar'ı öldürdü", False),
        ("waiting at the quay", False),
    ],
)
def test_inflected_gone_words_mark_a_cast_row_gone(memory: Path, availability: str, gone: bool) -> None:
    _character(memory, "Edda Vale", status="dead")
    row = f"| Edda Vale | T2 | Fish Market | - | - | {availability} | - | - | r3 | 3 |\n"
    _write(memory / "active_cast.md", (memory / "active_cast.md").read_text(encoding="utf-8") + row)
    found = _rules(check_content.check_memory(memory, location="old_dock", present_npcs=[]), "cast_dead_listed")
    assert (found == []) is gone


@pytest.mark.parametrize(
    ("state", "ended"),
    [("öldürüldü", True), ("bitmişti", True), ("boşandılar", True), ("died", True), ("former lovers", True), ("ölçülü", False), ("close", False)],
)
def test_inflected_ended_words_close_a_relationship(memory: Path, state: str, ended: bool) -> None:
    _character(memory, "Witness", status="dead")
    _write(
        memory / "relationship_map.md",
        "# Relationship Map\n\n" + RELATION_HEADER + f"| Mira | -> | Witness | informant | {state} | - | - | yes | r4 | 4 |\n",
    )
    found = _rules(check_content.check_memory(memory, location="", present_npcs=[]), "relationship_dead_active")
    assert (found == []) is ended


def test_location_unmapped(memory: Path) -> None:
    found = check_content.check_memory(memory, location="Lighthouse", present_npcs=[])
    assert [finding["rule"] for finding in found] == ["location_unmapped"]
    assert Path(found[0]["path"]).name == "location_graph.md"
    assert check_content.check_memory(memory, location="fish market", present_npcs=[]) == []
    assert check_content.check_memory(memory, location="", present_npcs=[]) == []


def test_example_rows_are_not_campaign_content(memory: Path) -> None:
    template = (TOOLS.parent / "templates" / "campaign" / "active_cast.md").read_text(encoding="utf-8")
    _write(memory / "active_cast.md", template)
    _character(memory, "Example NPC", status="dead")
    assert _rules(check_content.check_memory(memory, location="", present_npcs=[]), "cast_dead_listed") == []


# ---------------------------------------------------------------------------
# 4.4 `## Now` overflow and knowledge holders
# ---------------------------------------------------------------------------


def _note_with_now(campaign: Path, now: str) -> Path:
    path = campaign / "places" / "harbor.md"
    _write(path, f"# Harbor\n\n## Core\n\n- Status: open\n\n## Now\n\n{now}\n\n## History\n\n- Day 1: built.\n")
    return path


@pytest.mark.parametrize(
    "now, flagged",
    [
        ("The tide is out and the boats wait.", False),
        ("x" * 801, True),
        ("- Day 3: storm.\n- Gün 4: fırtına.\n- Tag 5: Sturm.", False),
        ("- Day 3: storm.\n- Gün 4: fırtına.\n- Tag 5: Sturm.\n- Día 6: tormenta.", True),
        ("- **Jour 7** calm.\n- Quiet again (day 8).\n- Day 9: rain.\n- Day 10: fog.\nUndated line.", True),
        ("<!--\n" + "Guidance. " * 120 + "\n-->\nThe tide is out.", False),
    ],
)
def test_now_overflow(campaign: Path, now: str, flagged: bool) -> None:
    path = _note_with_now(campaign, now)
    found = check_content.check_now(campaign)
    assert bool(found) is flagged
    if flagged:
        assert found[0]["rule"] == "now_overflow" and found[0]["path"] == str(path)


def test_now_budget_counts_dated_entries() -> None:
    assert check_content.now_budget("# A\n\nno now section\n") is None
    assert check_content.now_budget("## Now\n\n- Day 1: a\n- (day 2) b\nplain\n## History\n- Day 0\n")[1] == 2


def test_now_overflow_agrees_with_the_writers_fold(campaign: Path) -> None:
    owner_ops = pytest.importorskip("owner_ops")
    if not hasattr(owner_ops, "fold_now"):
        pytest.skip("the writer has no ## Now fold")
    now = "\n".join(f"- Day {day}: the tide turned." for day in range(1, 7)) + "\nThe harbor is quiet."
    path = _note_with_now(campaign, now)
    assert [finding["rule"] for finding in check_content.check_now(campaign)] == ["now_overflow"]
    folded, moved = owner_ops.fold_now(path.read_text(encoding="utf-8"))
    assert moved == 3
    _write(path, folded)
    assert check_content.check_now(campaign) == []
    # Whatever the writer does not count as dated, the check does not either.
    for sample in (now, "- Day12 storm\n- Gün13 fırtına\n- Tag14 Sturm\n- Día15 tormenta", "x" * 900):
        text = f"# Harbor\n\n## Now\n\n{sample}\n"
        assert check_content.now_budget(text) == owner_ops.now_status(text)


KNOWLEDGE = """# Knowledge Boundaries

## NPC And Faction Knowledge

### Witness

- Confirmed fact ids:
- Explicitly unknown fact ids: F-001, F-002
- Must-not-imply fact ids: `F-003`

## Holder Accounts

### Witness hears the name

- Account id: A-001
- Holder ref: Witness
- Fact id: F-001
- Account: the courier's name
- Stance: {stance}
- Source ref: session_log.md
- Learned at: day 3
- Recorded revision: 4
- Supersedes: none
- Correction ref: none

## Reveal Ledger

- {dated}
"""


def test_knowledge_holder_conflict_from_an_account_and_a_dated_line(campaign: Path) -> None:
    _write(campaign / "knowledge_boundaries.md", KNOWLEDGE.format(stance="confirmed", dated="Day 12: Witness overheard F-003."))
    found = check_content.check_knowledge(campaign)
    assert [(finding["rule"], finding["severity"]) for finding in found] == [("knowledge_holder_conflict", "warning")] * 2
    assert "explicitly unknown for F-001" in found[0]["message"] and "holder account" in found[0]["message"]
    assert "must-not-imply for F-003" in found[1]["message"] and "dated line" in found[1]["message"]


def test_knowledge_holder_conflict_negatives(campaign: Path) -> None:
    # An unknown stance, another holder's dated line, and a longer id that only contains F-003.
    text = KNOWLEDGE.format(stance="unknown", dated="Day 12: Corin overheard F-003.\n- Day 13: Witness heard F-0031.")
    _write(campaign / "knowledge_boundaries.md", text)
    assert check_content.check_knowledge(campaign) == []


def test_knowledge_holder_conflict_says_a_line_mentions_the_fact(campaign: Path) -> None:
    dated = "Day 14: Ilse hides F-003 from Witness; he still does not know it."
    _write(campaign / "knowledge_boundaries.md", KNOWLEDGE.format(stance="unknown", dated=dated))
    (found,) = check_content.check_knowledge(campaign)
    assert "a dated line mentions them with it" in found["message"] and "learned" not in found["message"]


def test_knowledge_holder_conflict_reads_the_holders_own_note(campaign: Path) -> None:
    _write(campaign / "knowledge_boundaries.md", KNOWLEDGE.format(stance="unknown", dated="Day 2: the harbor closed."))
    note = campaign / "characters" / "witness.md"
    _write(note, "# Witness\n\n## History\n\n- Day 40: learned the courier's route.\n")
    assert check_content.check_knowledge(campaign) == []
    _write(note, "# Witness\n\n## History\n\n- Day 40: learned F-002 from the courier.\n")
    (found,) = check_content.check_knowledge(campaign)
    assert "explicitly unknown for F-002" in found["message"] and "characters/witness.md" in found["message"]


# ---------------------------------------------------------------------------
# 2.6 The age rule
# ---------------------------------------------------------------------------


@pytest.fixture()
def fallback_age_rules(monkeypatch: pytest.MonkeyPatch):
    """Use only this module's fallback tables, whatever the shipped packs hold."""

    load = lang_pack.load_pack

    def without_age_keys(code: str) -> dict:
        pack = load(code)
        pack.pop("age_patterns", None)
        pack.pop("romance_terms", None)
        return pack

    monkeypatch.setattr(lang_pack, "load_pack", without_age_keys)
    _clear_age_rules()
    yield
    _clear_age_rules()


def _clear_age_rules() -> None:
    # The full check loads its own copy of check_content.
    for module in (check_content, check_state._content_checks()):
        module._packs.cache_clear()


@pytest.mark.parametrize(
    "text",
    [
        "At fifteen she kissed the stable boy behind the mill.",
        "Her first lover came when she was a 16-year-old apprentice.",
        "She was married at the age of 14 to a merchant.",
        "On beşindeyken bir denizciye âşık oldu.",
        "15 yaşında evlendi.",
        "ON YEDİMDE ilk sevgilim oldu.",
    ],
)
def test_minor_proximity_positive(fallback_age_rules: None, text: str) -> None:
    assert check_content.minor_proximity(text) is not None


@pytest.mark.parametrize(
    "text",
    [
        "Fifteen years ago she married a sailor.",
        "She was twenty-five years old when she married.",
        "At one point she kissed him goodbye.",
        "They met at 15:00 and kissed at the gate.",
        "On beş yıl önce evlendi.",
        "Yirmi beş yaşında evlendi.",
        "Masanın altında sevgilisinin mektubu duruyordu.",
        "Odalardan birinde sevgilisi bekliyordu.",
        "At fifteen she learned to sail. She worked the nets for years. The harbor grew. "
        "Ships came and went through every season of the long war in the north. "
        "Much later, as a grown woman of thirty with a boat of her own and a crew to feed, she married.",
    ],
)
def test_minor_proximity_negative(fallback_age_rules: None, text: str) -> None:
    assert check_content.minor_proximity(text) is None


def test_minor_proximity_uses_pack_patterns_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    load = lang_pack.load_pack

    def with_custom(code: str) -> dict:
        pack = load(code)
        if code == "en":
            pack["age_patterns"] = [r"\bteenaged\b"]
            pack["romance_terms"] = ["sweetheart"]
        return pack

    monkeypatch.setattr(lang_pack, "load_pack", with_custom)
    _clear_age_rules()
    try:
        assert check_content.minor_proximity("The teenaged boy became her sweetheart.") is not None
        # The pack replaces the English fallback, and a plain term is a whole word.
        assert check_content.minor_proximity("At fifteen she kissed him.") is None
        assert check_content.minor_proximity("The teenaged boy wrote to his sweethearts.") is None
    finally:
        _clear_age_rules()


FILLER = (
    "she walked the long coast road past the salt flats and the fishing villages, the old watchtowers, "
    "the ruined chapel on the cliff, the orchards, the quarries, the mills and the ferry crossings, "
    "until the mountains rose ahead of her"
)


def test_minor_proximity_window_is_two_adjacent_sentences_or_220_characters(fallback_age_rules: None) -> None:
    assert len(FILLER) > check_content.AGE_WINDOW_CHARS
    # The next sentence is still near, however long the first one is.
    assert check_content.minor_proximity(f"At fifteen {FILLER}. There she took a lover.") is not None
    # Two sentences on and more than 220 characters away is not.
    far = f"At fifteen {FILLER}. She worked the nets. There she took a lover."
    assert check_content.minor_proximity(far) is None
    # Close in characters counts across any number of short sentences.
    assert check_content.minor_proximity("At fifteen she ran. She hid. She slept. She had a lover.") is not None


def test_romance_terms_take_a_stem_on_any_word(monkeypatch: pytest.MonkeyPatch) -> None:
    load = lang_pack.load_pack

    def with_phrase_stem(code: str) -> dict:
        pack = load(code)
        if code == "en":
            pack["age_patterns"] = [r"\bat\s+(?P<age>fifteen)\b"]
            pack["romance_terms"] = ["sle* with"]
        return pack

    monkeypatch.setattr(lang_pack, "load_pack", with_phrase_stem)
    _clear_age_rules()
    try:
        assert check_content.minor_proximity("At fifteen she slept with the stable boy.") is not None
        assert check_content.minor_proximity("At fifteen she sleeps with the miller's son.") is not None
        assert check_content.minor_proximity("At fifteen she slept beside the stable boy.") is None
    finally:
        _clear_age_rules()


def test_ages_are_read_with_the_pack_number_words(monkeypatch: pytest.MonkeyPatch) -> None:
    load = lang_pack.load_pack

    def with_numbers(code: str) -> dict:
        pack = load(code)
        if code == "en":
            pack["age_patterns"] = [r"\baged\s+(?P<age>[a-z]+)\b"]
            pack["romance_terms"] = ["lover"]
            pack["number_words"] = {**(pack.get("number_words") or {}), "quindecim": 15}
        return pack

    monkeypatch.setattr(lang_pack, "load_pack", with_numbers)
    _clear_age_rules()
    try:
        assert check_content.minor_proximity("Aged quindecim, she had a lover.") is not None
        # A word no table reads is no age at all.
        assert check_content.minor_proximity("Aged duodeviginti, she had a lover.") is None
    finally:
        _clear_age_rules()


def test_minor_romance_history_is_a_warning_that_cannot_be_acknowledged(campaign: Path) -> None:
    note = _character(campaign, "Edda Vale", extra="## History\n\nAt fifteen she had a lover in the guard.\n")
    _write(
        campaign / "directives.md",
        "# Directives\n\n" + DIRECTIVES_HEADER + "| D-001 | check | acknowledge minor_romance_history | OOC, revision 2 | active |\n",
    )
    found = _rules(_full(campaign), "minor_romance_history")
    assert [(finding["severity"], finding["path"]) for finding in found] == [("warning", str(note.resolve()))]
    assert "acknowledged" not in found[0]["message"].split("This cannot")[0]


VERA_HISTORY_TR = (
    "- 35. gün akşam: Delmora'yla geçmişini ve neden ayrıldığını Tolon'a itiraf etti: on beşinden yirmi iki "
    "yaşına, yedi yıl Demir Kilit'teydi; Delmora onu önce himayesine alıp yetiştirdi, Vera ancak on dokuz "
    "yaşında sevgilisi oldu."
)


@pytest.mark.parametrize(
    ("history", "flagged"),
    [
        (VERA_HISTORY_TR, False),
        ("- She worked there from fifteen to twenty-two; she became his lover only at nineteen.", False),
        ("- Yirmi iki yaşında gemiden ayrıldı; ilk sevgilisi on beş yaşındayken olmuştu.", True),
        ("- At twenty-two she left the ship; she had taken her first lover at fifteen.", True),
    ],
)
def test_minor_romance_history_reads_the_closest_age_of_each_term(campaign: Path, history: str, flagged: bool) -> None:
    _character(campaign, "Vera", extra=f"## History\n\n{history}\n")
    assert bool(_rules(_full(campaign), "minor_romance_history")) is flagged


OLD_AGE_RULE_LINE = (
    "Age rule: no romantic or sexual relationship in this character's past or present begins before 18, and no "
    "age or duration written here may imply one; when the character's age changes, recheck every dated line."
)


@pytest.mark.parametrize("backstory", ["Orphaned at twelve on the docks.", "On iki yaşında öksüz kaldı, rıhtımda büyüdü."])
def test_template_guidance_lines_are_no_history(campaign: Path, backstory: str) -> None:
    template = (TOOLS.parent / "templates" / "campaign" / "characters" / "_template.md").read_text(encoding="utf-8")
    guidance = next(line for line in template.splitlines() if line.strip() and "Backstory" in line and not line.startswith("-"))
    # A note made from an earlier template version kept the age rule as a plain line.
    extra = f"## Depth\n\n- Backstory: {backstory}\n\n{OLD_AGE_RULE_LINE}\n{guidance}\n"
    note = _character(campaign, "Edda Vale", extra=extra)
    assert _rules(_full(campaign), "minor_romance_history") == []
    # The same age beside a romance term the note itself writes is still found.
    romance = "İlk öpücüğü de o yıl oldu." if backstory.startswith("On") else "Her first kiss came then."
    _write(note, note.read_text(encoding="utf-8").replace(backstory, f"{backstory} {romance}"))
    assert [finding["rule"] for finding in _rules(_full(campaign), "minor_romance_history")] == ["minor_romance_history"]


def test_age_rule_text_keeps_the_distance_between_lines() -> None:
    template = frozenset({"- Contradiction:"})
    text = "- Backstory: Orphaned at twelve.\n- Contradiction:\n<!-- Age rule: romantic -->\nAge rule: sexual\n- Fear: storms"
    assert check_content.age_rule_text(text, template).split("\n") == [
        "- Backstory: Orphaned at twelve.",
        "-",
        "",
        "-",
        "- Fear: storms",
    ]


# ---------------------------------------------------------------------------
# 2.5 Records language
# ---------------------------------------------------------------------------


def test_records_language_resolution() -> None:
    assert check_content.records_language("narration:\n  language: tr\n") == "tr"
    assert check_content.records_language("narration:\n  language: tr\n  records_language: same\n") == "tr"
    assert check_content.records_language("narration:\n  language: tr\n  records_language: en-GB\n") == "en"
    assert check_content.records_language("narration:\n  language: auto\n") == ""
    assert check_content.records_language("") == ""


def test_records_language_mismatch_lists_files_in_another_language(campaign: Path) -> None:
    _profile_language(campaign, "tr")
    english = _character(campaign, "Edda Vale", extra=f"## Now\n\n{ENGLISH_BODY}\n")
    _character(campaign, "Brannoc", extra=f"## Now\n\n{TURKISH_BODY.replace('Edda', 'Brannoc')}\n")
    found = _rules(_full(campaign), "records_language_mismatch")
    assert len(found) == 1 and found[0]["severity"] == "warning"
    assert found[0]["paths"] == [str(english.resolve())]
    assert "characters/edda_vale.md (en)" in found[0]["message"]


def test_records_language_skips_the_session_zero_summary(campaign: Path) -> None:
    """session_zero.md is rendered by the Session 0 helper, so it may stay English."""

    _profile_language(campaign, "tr")
    (campaign / "session_zero.md").write_text("# Session Zero\n\n" + ENGLISH_BODY + "\n", encoding="utf-8")
    assert not _rules(_full(campaign), "records_language_mismatch")


def test_records_language_ignores_template_text_names_and_structure(campaign: Path) -> None:
    _profile_language(campaign, "tr")
    templates = TOOLS.parent / "templates" / "campaign"
    # English template guidance copied as is, and English labels around Turkish values.
    _write(campaign / "knowledge_boundaries.md", (templates / "knowledge_boundaries.md").read_text(encoding="utf-8"))
    _write(
        campaign / "characters" / "edda_vale.md",
        "# Edda Vale\n\nTier: T2\n\n## Core\n\n- Status: alive\n- Role: the harbor's net mender\n\n"
        f"## Now\n\n{TURKISH_BODY}\n\n| What it is | Where it is | Why it matters |\n| --- | --- | --- |\n",
    )
    assert _rules(_full(campaign), "records_language_mismatch") == []


def _rewrapped(text: str, width: int = 58) -> str:
    """Template text with every prose paragraph wrapped anew, as an older template version reads."""

    paragraphs = []
    for paragraph in text.split("\n\n"):
        lines = paragraph.splitlines()
        if lines and not any(line.lstrip().startswith(("#", "-", "|", "<!--", "`", "*")) for line in lines):
            paragraph = textwrap.fill(" ".join(lines), width)
        paragraphs.append(paragraph)
    return "\n\n".join(paragraphs)


def test_records_language_ignores_guidance_left_by_an_older_template(campaign: Path) -> None:
    _profile_language(campaign, "tr")
    templates = TOOLS.parent / "templates" / "campaign"
    for name in ("rules.md", "threads.md"):
        _write(campaign / name, _rewrapped((templates / name).read_text(encoding="utf-8")))
    rules = campaign / "rules.md"
    # Matching template lines verbatim no longer drops the rewrapped guidance ...
    verbatim_only = check_content.record_body(rules.read_text(encoding="utf-8"), template=check_content._template_for(campaign, rules))
    assert check_content.body_language(verbatim_only, "tr") == "en"
    # ... but lines made of the template's own words still read as template text.
    assert _rules(_full(campaign), "records_language_mismatch") == []
    threads = campaign / "threads.md"
    _write(threads, threads.read_text(encoding="utf-8") + "\n" + ENGLISH_BODY + "\n")
    (finding,) = _rules(_full(campaign), "records_language_mismatch")
    assert finding["paths"] == [str(threads.resolve())]


def test_records_language_tolerates_a_mixed_note_and_reads_either_direction(campaign: Path) -> None:
    _profile_language(campaign, "tr")
    # A Turkish note that kept one English paragraph is not "confidently" English.
    _character(campaign, "Edda Vale", extra=f"## Now\n\n{TURKISH_BODY}\n\n{ENGLISH_BODY}\n")
    assert _rules(_full(campaign), "records_language_mismatch") == []
    _profile_language(campaign, "en")  # the later narration block wins: English records
    (finding,) = _rules(_full(campaign), "records_language_mismatch") or [None]
    assert finding is None  # the same mixed note is not confidently Turkish either
    _character(campaign, "Brannoc", extra=f"## Now\n\n{TURKISH_BODY.replace('Edda', 'Brannoc')}\n")
    (finding,) = _rules(_full(campaign), "records_language_mismatch")
    assert "characters/brannoc.md (tr)" in finding["message"]


def test_records_language_is_skipped_without_a_known_language(campaign: Path) -> None:
    _character(campaign, "Edda Vale", extra=f"## Now\n\n{ENGLISH_BODY}\n")
    _profile_language(campaign, "auto")
    assert _rules(_full(campaign), "records_language_mismatch") == []


@pytest.mark.parametrize(("seen", "flagged"), [("tr", True), ("en", False)])
def test_records_language_under_auto_follows_the_lint(campaign: Path, seen: str, flagged: bool) -> None:
    # `auto` resolves as the writer resolves it: the language the lint last saw in the replies.
    _character(campaign, "Edda Vale", extra=f"## Now\n\n{ENGLISH_BODY}\n")
    _profile_language(campaign, "auto")
    _write(campaign / ".repog-runtime" / "lint_last.json", json.dumps({"language": seen}))
    found = _rules(_full(campaign), "records_language_mismatch")
    assert [finding["severity"] for finding in found] == (["warning"] if flagged else [])


def _settled_boundaries(notes: str = "", prose: str = "") -> str:
    """The boundaries template with every Category row settled to its last option, as Session 0 leaves it."""

    template = (TOOLS.parent / "templates" / "campaign" / "boundaries.md").read_text(encoding="utf-8")
    lines: list[str] = []
    in_table = False
    settled = 0
    for line in template.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")] if line.lstrip().startswith("|") else []
        if cells[:1] == ["Category"]:
            in_table = True
        elif in_table and len(cells) == 3 and not set(line.strip()) <= set("|-: "):
            category, setting, _ = cells
            note = notes if category.casefold().startswith("limits") else ""
            line = f"| {category} | {setting.split(' / ')[-1]} | {note} |"
            settled += 1
        elif not cells:
            in_table = False
        lines.append(line)
    assert settled >= 5, "the boundaries template lost its category table"
    return "\n".join(lines) + f"\n\n{prose}\n"


def test_records_language_reads_boundary_categories_and_settings_as_structure(campaign: Path) -> None:
    _profile_language(campaign, "tr")
    turkish = "Rızasız eylemler asla sahne olarak yazılmaz."
    _write(campaign / "boundaries.md", _settled_boundaries(notes=turkish, prose="Kraliyet ailesi bu adada hiç görülmedi."))
    assert _rules(_full(campaign), "records_language_mismatch") == []
    # The Notes column and the prose are content: written in English, they still count.
    _write(campaign / "boundaries.md", _settled_boundaries(notes="Non-consensual acts are never written as scenes.", prose=ENGLISH_BODY))
    (finding,) = _rules(_full(campaign), "records_language_mismatch")
    assert "boundaries.md (en)" in finding["message"]


@pytest.mark.parametrize(
    ("line", "kept"),
    [
        ("- May be created within accepted boundaries and shown at review: liman bekçisi", "liman bekçisi"),
        ("- Always require renewed approval, regardless of threshold: her yeni tanrı", "her yeni tanrı"),
    ],
)
def test_record_body_strips_long_template_labels(line: str, kept: str) -> None:
    assert check_content.record_body(line).strip() == kept
    # A sentence with a colon after more than 70 characters is prose, not a label.
    sentence = "Edda had waited at the harbor for three long days and three longer nights for the boat: none came."
    assert check_content.record_body(sentence).strip() == sentence


def test_records_language_explicit_code_wins_over_the_play_language(campaign: Path) -> None:
    _profile_language(campaign, "tr", records="en")
    _character(campaign, "Edda Vale", extra=f"## Now\n\n{ENGLISH_BODY}\n")
    assert _rules(_full(campaign), "records_language_mismatch") == []


def test_records_language_acknowledged_per_file_or_whole(campaign: Path) -> None:
    _profile_language(campaign, "tr")
    _character(campaign, "Edda Vale", extra=f"## Now\n\n{ENGLISH_BODY}\n")
    brannoc = _character(campaign, "Brannoc", extra=f"## Now\n\n{ENGLISH_BODY.replace('Edda', 'Brannoc')}\n")
    directives = campaign / "directives.md"
    _write(
        directives,
        "# Directives\n\n" + DIRECTIVES_HEADER
        + "| D-001 | check | acknowledge records_language_mismatch for Edda Vale — imported | OOC, revision 2 | active |\n",
    )
    (finding,) = _rules(_full(campaign), "records_language_mismatch")
    assert finding["severity"] == "warning" and finding["paths"] == [str(brannoc.resolve())]
    assert "1 more acknowledged by D-001" in finding["message"]

    _write(
        directives,
        directives.read_text(encoding="utf-8")
        + "| D-002 | check | acknowledge records_language_mismatch for characters/brannoc.md | OOC, revision 3 | active |\n",
    )
    (finding,) = _rules(_full(campaign), "records_language_mismatch")
    assert finding["severity"] == "info" and len(finding["paths"]) == 2

    _write(directives, "# Directives\n\n" + DIRECTIVES_HEADER + "| D-003 | check | acknowledge records_language_mismatch | OOC | active |\n")
    (finding,) = _rules(_full(campaign), "records_language_mismatch")
    assert finding["severity"] == "info" and finding["message"].endswith("(acknowledged by D-003)")


def test_record_body_strips_structure() -> None:
    text = (
        "# Title\n\n<!-- guidance -->\n- Status: yaralı ama ayakta\n**Role:** liman bekçisi\n"
        "| Head | Other |\n| --- | --- |\n| hücre bir | hücre iki |\n`code span` Edda geldi\n"
    )
    body = check_content.record_body(text, names=["Edda"])
    assert "Title" not in body and "guidance" not in body and "Status" not in body and "Role" not in body
    assert "Head" not in body and "hücre bir hücre iki" in body and "code span" not in body and "Edda" not in body
    assert "yaralı ama ayakta" in body and "liman bekçisi" in body


# ---------------------------------------------------------------------------
# 4.2 Scale-aware power checks
# ---------------------------------------------------------------------------


STATS = "## Stats\n\n- Power: {power}\n- Agility: 2\n- Endurance: 2\n- Technique: 2\n- Perception: 2\n- Wits: 2\n- Presence: 2\n- Will: 2\n"


@pytest.mark.parametrize(
    "band, flagged",
    [("3", True), ("1-3", True), ("(1-3)", True), ("5", False), ("(2-5)", False), ("regional threat", False), ("", False)],
)
def test_power_band_mismatch(campaign: Path, band: str, flagged: bool) -> None:
    path = campaign / "characters" / "edda_vale.md"
    _write(path, f"# Edda Vale\n\nTier: T2\n\nPower Band: {band}\n\n" + STATS.format(power=5))
    found = _rules(check_content.check_power(campaign), "power_band_mismatch")
    assert bool(found) is flagged
    if flagged:
        assert "Power 5" in found[0]["message"] and found[0]["path"] == str(path)


def test_tier_caps_replace_the_level_band_defaults(campaign: Path) -> None:
    _numeric(campaign)
    edda = campaign / "characters" / "edda_vale.md"
    _write(edda, "# Edda Vale\n\nTier: T2\n\nPower Band:\n\n" + STATS.format(power=4))
    _write(campaign / "characters" / "brannoc.md", "# Brannoc\n\nTier: T1\n\nPower Band:\n\n" + STATS.format(power=3))
    # Without caps, the beginner level band flags the T2 note's 4.
    (spike,) = _rules(_full(campaign), "early_stage_power_spike")
    assert spike["path"] == str(edda.resolve()) and "beginner recommended max 3" in spike["message"]
    _write(campaign / "rules.md", "# Rules\n\n## Tier Caps\n\n- T1: 2\n- T2: 4\n")
    # The T2 cap allows the 4; the T1 cap flags Brannoc's 3 under the same rule id.
    (capped,) = _rules(_full(campaign), "early_stage_power_spike")
    assert capped["severity"] == "warning" and "Brannoc (T1) has Power 3 above the T1 cap 2" in capped["message"]


def test_a_stat_above_its_tier_cap_blocks_session_zero_readiness(campaign: Path) -> None:
    import session_zero_state

    _numeric(campaign)
    _write(campaign / "characters" / "edda_vale.md", "# Edda Vale\n\nTier: T2\n\nPower Band:\n\n" + STATS.format(power=4))
    _write(campaign / "rules.md", "# Rules\n\n## Tier Caps\n\n- T2: 3\n")
    (capped,) = _rules(_full(campaign), "early_stage_power_spike")
    assert capped["severity"] == "warning" and "Edda Vale (T2) has Power 4 above the T2 cap 3" in capped["message"]
    # Readiness blocks on this rule id, so declaring caps never lets a card above the scale through.
    assert capped["rule"] in session_zero_state.CALIBRATION_RULES


def test_a_power_band_that_covers_the_stat_answers_its_tier_cap(campaign: Path) -> None:
    _write(campaign / "rules.md", "# Rules\n\n## Tier Caps\n\n- T1: 2\n- T2: 4\n")
    note = campaign / "characters" / "brannoc.md"
    _write(note, "# Brannoc\n\nTier: T1\n\nPower Band: 1-3\n\n" + STATS.format(power=3))
    assert _rules(check_content.check_power(campaign), "early_stage_power_spike") == []
    _write(note, "# Brannoc\n\nTier: T1\n\nPower Band: local tough\n\n" + STATS.format(power=3))
    assert _rules(check_content.check_power(campaign), "early_stage_power_spike")


def test_one_note_checked_outside_its_campaign_takes_the_caps_it_is_given(tmp_path: Path) -> None:
    # The writer checks a new note in a scratch folder that has no rules.md.
    _write(tmp_path / "characters" / "edda_vale.md", "# Edda Vale\n\nTier: T2\n\nPower Band:\n\n" + STATS.format(power=4))

    def spikes(**caps: dict[str, int]) -> list[dict]:
        findings: list[dict] = []
        check_state._check_character_notes(
            tmp_path, "beginner", findings, resolution_grounding="numeric", ready=False, contract_v3=False, **caps
        )
        return _rules(findings, "early_stage_power_spike")

    assert spikes() and spikes(caps={}) and spikes(caps={"t1": 4})
    assert spikes(caps={"t2": 4}) == []


D20_RESOLUTION = (
    "  resolution:\n    die: 1d20\n    stat_min: 1\n    stat_max: 20\n    difficulty_min: 5\n    difficulty_max: 25\n"
    "    bands:\n      - {at_least: 0, band: success}\n      - {at_least: -99, band: failure}\n"
)


@pytest.mark.parametrize("declared_by", ["rules.md scale line", "dice resolution"])
def test_level_band_power_rules_follow_a_declared_stat_range(campaign: Path, declared_by: str) -> None:
    if declared_by == "rules.md scale line":
        _numeric(campaign)
        _write(campaign / "rules.md", "# Rules\n\n- Numeric scale: 1-20\n")
    else:
        profile = campaign / "play_profile.yaml"
        _write(profile, profile.read_text(encoding="utf-8") + "mechanics:\n  resolution_grounding: numeric\n" + D20_RESOLUTION)
    note = campaign / "characters" / "edda_vale.md"
    ordinary = "## Stats\n\n- Power: 8\n- Agility: 6\n- Wits: 5\n- Endurance: 2\n- Technique: 2\n- Perception: 2\n- Presence: 2\n- Will: 2\n"
    _write(note, "# Edda Vale\n\nTier: T2\n\nPower Band:\n\n" + ordinary)
    level_rules = ("early_stage_power_spike", "early_stage_power_inflation")
    assert [finding for finding in _full(campaign) if finding["rule"] in level_rules] == []
    # The beginner ceiling 3 of 1-5 is 10.5 on 1-20, and "4+" is 16+.
    strong = ordinary.replace("Power: 8", "Power: 12").replace("Agility: 6", "Agility: 17").replace("Wits: 5", "Wits: 16")
    _write(note, "# Edda Vale\n\nTier: T2\n\nPower Band:\n\n" + strong)
    findings = _full(campaign)
    (spike,) = _rules(findings, "early_stage_power_spike")
    assert "recommended max 10 " in spike["message"] and spike["message"].endswith("Agility, Power, Wits.")
    (inflation,) = _rules(findings, "early_stage_power_inflation")
    assert "has 2 stats at 16+" in inflation["message"]


def test_the_player_stat_budget_follows_a_declared_stat_range(campaign: Path) -> None:
    _numeric(campaign)
    _write(campaign / "rules.md", "# Rules\n\n- Numeric scale: 1-20\n")
    names = ("Power", "Agility", "Endurance", "Technique", "Perception", "Wits", "Presence", "Will")

    def player_stats(value: int) -> None:
        state = campaign / "current_state.yaml"
        block = "  stats:\n" + "".join(f"    {name}: {value}\n" for name in names)
        _write(state, re.sub(r"(?m)^  stats:(?: \{\}\n|\n(?:    .*\n)*)", lambda _: block, state.read_text(encoding="utf-8"), count=1))

    # Beginner's 16 over eight 1-5 stats is 8 + 8 * 19 / 4 = 46 on 1-20.
    player_stats(5)
    assert _rules(_full(campaign), "stat_budget_exceeded") == []
    player_stats(6)
    (budget,) = _rules(_full(campaign), "stat_budget_exceeded")
    assert budget["message"] == "Stat total 48 exceeds beginner budget 46."
    assert check_runtime.rescaled(16, (1, 5), 8) == 16 and check_runtime.rescaled(3, (1, 5)) == 3
    assert check_runtime.rescaled(3, (1, 20)) == 10.5 and check_runtime.rescaled(16, (1, 20), 8) == 46


def test_power_checks_need_numeric_grounding(campaign: Path) -> None:
    _write(campaign / "rules.md", "# Rules\n\n## Tier Caps\n\n- T2: 3\n")
    _write(campaign / "characters" / "edda_vale.md", "# Edda Vale\n\nTier: T2\n\nPower Band: 3\n\n" + STATS.format(power=5))
    power_rules = ("power_band_mismatch", "early_stage_power_spike")
    profile = campaign / "play_profile.yaml"
    unset = profile.read_text(encoding="utf-8")
    _numeric(campaign)
    assert {finding["rule"] for finding in _full(campaign) if finding["rule"] in power_rules} == set(power_rules)
    for grounding in ("fictional", "bands"):
        _write(profile, unset + f"mechanics:\n  resolution_grounding: {grounding}\n")
        assert [finding for finding in _full(campaign) if finding["rule"] in power_rules] == []


def test_a_numeric_band_that_covers_the_stats_declares_the_power(campaign: Path) -> None:
    _numeric(campaign)
    _write(campaign / "characters" / "edda_vale.md", "# Edda Vale\n\nTier: T2\n\nPower Band: 1-4\n\n" + STATS.format(power=4))
    findings = _full(campaign)
    assert _rules(findings, "early_stage_power_spike") == [] and _rules(findings, "power_band_mismatch") == []
    # Positive control: without the band, the same note is a spike.
    path = campaign / "characters" / "edda_vale.md"
    _write(path, path.read_text(encoding="utf-8").replace("Power Band: 1-4", "Power Band:"))
    assert _rules(_full(campaign), "early_stage_power_spike")


def test_numeric_scale_line_widens_the_stat_range(campaign: Path) -> None:
    _numeric(campaign)
    _write(campaign / "characters" / "edda_vale.md", "# Edda Vale\n\nTier: T2\n\nPower Band: 1-8\n\n" + STATS.format(power=8))
    assert _rules(_full(campaign), "mechanic_stat_out_of_range")
    _write(campaign / "rules.md", "# Rules\n\n## Numeric Stat Scale\n\n- Numeric scale: 1-10\n")
    assert _rules(_full(campaign), "mechanic_stat_out_of_range") == []
    assert check_runtime.stat_range("", "- Numeric scale: 1-10\n") == (1, 10)
    assert check_runtime.stat_range("mechanics:\n  resolution:\n    die: 1d6\n    stat_max: 7\n", "") == (1, 7)
    assert check_runtime.stat_range("", "<!-- - Numeric scale: 1-10 -->\n") == (1, 5)


def test_power_findings_can_be_acknowledged(campaign: Path) -> None:
    _numeric(campaign)
    _write(campaign / "characters" / "edda_vale.md", "# Edda Vale\n\nTier: T2\n\nPower Band: 3\n\n" + STATS.format(power=5))
    _write(
        campaign / "directives.md",
        "# Directives\n\n" + DIRECTIVES_HEADER
        + "| D-004 | check | acknowledge power_band_mismatch for Edda Vale | OOC, revision 9 | active |\n",
    )
    (found,) = _rules(_full(campaign), "power_band_mismatch")
    assert found["severity"] == "info" and found["message"].endswith("(acknowledged by D-004)")
    assert found["acknowledged_by"] == "D-004"


# ---------------------------------------------------------------------------
# 2.4 Acknowledgement
# ---------------------------------------------------------------------------


def _finding(rule: str, path: Path, severity: str = "warning", message: str = "something") -> dict:
    return {"severity": severity, "rule": rule, "message": message, "path": str(path)}


@pytest.mark.parametrize(
    "directive, parsed",
    [
        ("acknowledge now_overflow", ("now_overflow", None)),
        ("acknowledge now_overflow.", ("now_overflow", None)),
        ("Acknowledge now_overflow (Player accepted long notes)", ("now_overflow", None)),
        ("acknowledge now_overflow - accepted", ("now_overflow", None)),
        ("acknowledge now_overflow — the Player keeps long notes.", ("now_overflow", None)),
        ("acknowledge now_overflow; accepted at revision 9", ("now_overflow", None)),
        ("acknowledge now_overflow, the Player said so", ("now_overflow", None)),
        ("acknowledge now_overflow for Branak - accepted", ("now_overflow", "Branak")),
        ("acknowledge now_overflow for Branak.", ("now_overflow", "Branak")),
        ("acknowledge now_overflow for Edda Vale. The Player accepted it.", ("now_overflow", "Edda Vale")),
        ("acknowledge now_overflow for characters/edda_vale.md", ("now_overflow", "characters/edda_vale.md")),
        ("acknowledge now_overflow for characters/edda_vale.md.", ("now_overflow", "characters/edda_vale.md")),
        # Other words after the rule id are not a target, so they acknowledge nothing.
        ("acknowledge now_overflow in Branak's note", None),
        ("keep now_overflow", None),
    ],
)
def test_acknowledge_directive_takes_a_trailing_reason(directive: str, parsed: tuple | None) -> None:
    assert check_content.parse_acknowledgement(directive) == parsed


def test_an_untargeted_row_with_a_reason_acknowledges_in_a_full_check(campaign: Path) -> None:
    _numeric(campaign)
    _write(campaign / "characters" / "edda_vale.md", "# Edda Vale\n\nTier: T2\n\nPower Band: 3\n\n" + STATS.format(power=5))
    _write(
        campaign / "directives.md",
        "# Directives\n\n" + DIRECTIVES_HEADER
        + "| D-004 | check | acknowledge power_band_mismatch (the Player accepted it) | OOC, revision 9 | active |\n",
    )
    (found,) = _rules(_full(campaign), "power_band_mismatch")
    assert found["severity"] == "info" and found["acknowledged_by"] == "D-004"


def test_acknowledgement_rows_and_targets(campaign: Path) -> None:
    note = _character(campaign, "Edda Vale")
    _write(
        campaign / "directives.md",
        "# Directives\n\n" + DIRECTIVES_HEADER
        + "| D-001 | check | acknowledge now_overflow for characters/edda_vale.md | OOC | active |\n"
        + "| D-002 | check | acknowledge stacked_sections | OOC | retired |\n"
        + "| D-003 | global | acknowledge stacked_sections | OOC | active |\n"
        + "| D-004 | check | `acknowledge note_core_missing` | OOC | active |\n"
        + "| D-005 | check | acknowledge dead_present | OOC | active |\n"
        + "| D-006 | check | acknowledge cast_present_missing for Corin (a passer-by) | OOC | active |\n",
    )
    assert check_content.acknowledgements(campaign) == [
        ("D-001", "now_overflow", "characters/edda_vale.md"),
        ("D-004", "note_core_missing", None),
        ("D-005", "dead_present", None),
        ("D-006", "cast_present_missing", "Corin"),
    ]
    findings = [
        _finding("now_overflow", note),
        _finding("now_overflow", campaign / "characters" / "brannoc.md"),
        _finding("stacked_sections", note),
        _finding("note_core_missing", campaign / "characters"),
        _finding("dead_present", note, severity="error"),
        _finding("cast_present_missing", campaign / "active_cast.md", message="present_npcs names Corin, who has no row"),
        _finding("cast_present_missing", campaign / "active_cast.md", message="present_npcs names Corinna, who has no row"),
    ]
    check_content.acknowledge(campaign, findings)
    assert [finding["severity"] for finding in findings] == ["info", "warning", "warning", "info", "error", "info", "warning"]
    assert findings[0]["message"] == "something (acknowledged by D-001)"


def test_an_aggregated_finding_is_acknowledged_once_every_file_is_covered(campaign: Path) -> None:
    _write(campaign / "characters" / "edda_vale.md", "# Edda Vale\n\nTier: T2\n")
    _write(campaign / "characters" / "brannoc.md", "# Brannoc\n\nTier: T3\n")
    (finding,) = _rules(_full(campaign), "note_core_missing")
    others = [Path(path).name for path in finding["paths"] if Path(path).stem != "edda_vale"]
    assert len(others) >= 1
    # One row names a note by title, the others by path.
    targets = ["Edda Vale"] + [f"characters/{name}" for name in others]
    rows = [
        f"| D-{index:03d} | check | acknowledge note_core_missing for {target} | OOC | active |\n"
        for index, target in enumerate(targets, 1)
    ]
    directives = campaign / "directives.md"
    _write(directives, "# Directives\n\n" + DIRECTIVES_HEADER + "".join(rows[:-1]))
    (finding,) = _rules(_full(campaign), "note_core_missing")
    assert finding["severity"] == "warning"
    _write(directives, "# Directives\n\n" + DIRECTIVES_HEADER + "".join(rows))
    (finding,) = _rules(_full(campaign), "note_core_missing")
    expected = ", ".join(f"D-{index:03d}" for index in range(1, len(rows) + 1))
    assert finding["severity"] == "info" and finding["acknowledged_by"] == expected
    assert finding["message"].endswith(f"(acknowledged by {expected})")


def test_acknowledgement_runs_on_the_full_check_only(memory: Path) -> None:
    _set_state(memory, present=["Witness", "Corin"])
    _character(memory, "Corin", tier="T1")
    _write(
        memory / "directives.md",
        "# Directives\n\n" + DIRECTIVES_HEADER + "| D-001 | check | acknowledge cast_present_missing for Corin | OOC | active |\n",
    )
    result = check_state.check_campaign(memory, scope="full")
    (finding,) = _rules(result["findings"], "cast_present_missing")
    assert finding["severity"] == "info"
    assert result["warning_count"] == sum(1 for item in result["findings"] if item["severity"] == "warning")


# ---------------------------------------------------------------------------
# 4.3 Odds findings in the full check
# ---------------------------------------------------------------------------


LIVE_SCALE = """mechanics:
  resolution:
    die: 1d2
    stat_min: 1
    stat_max: 5
    difficulty_min: 1
    difficulty_max: 5
    bands:
      - {at_least: 0, band: success}
      - {at_least: -1, band: partial_small_cost}
      - {at_least: -99, band: partial_heavy_cost}
"""

ROOMY_SCALE = """mechanics:
  resolution:
    die: 1d6
    stat_min: 1
    stat_max: 5
    difficulty_min: 3
    difficulty_max: 12
    bands:
      - {at_least: 0, band: success}
      - {at_least: -99, band: failure}
"""


def _receipt(index: int, value: int, difficulty: int, **extra: object) -> dict:
    call = {"actor": "Mira", "axis": "Wits", "value": value, "difficulty": difficulty, "factors": [], "stakes": "x"}
    return {"roll_id": f"r{index}", "revision": index, "call": call, "die": "1d6", "dice": [3], "band": "x", "auto": False, **extra}


def _rolls(campaign: Path, receipts: list[dict]) -> None:
    _write(
        campaign / ".repog-runtime" / "rolls.jsonl",
        "".join(json.dumps(receipt) + "\n" for receipt in receipts) + "not json\n",
    )


def _odds_findings(campaign: Path, profile: str) -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []
    check_runtime.check_rolls(campaign, profile, campaign / "play_profile.yaml", lambda *args, **_: found.append(args[:3]))
    return found


def test_failure_unreachable_over_recent_receipts(campaign: Path) -> None:
    # 5 + 1d6 vs 3 can never fall below success; four of five calls are like that.
    receipts = [_receipt(index, 5, 3) for index in range(4)] + [_receipt(4, 1, 6)]
    receipts.append({"kind": "reread", "reread_of": "r0", "reason": "x", "new_band": "failure", "revision": 5})
    _rolls(campaign, receipts)
    ((severity, rule, message),) = _odds_findings(campaign, ROOMY_SCALE)
    assert (severity, rule) == ("warning", "failure_unreachable")
    assert "failure could not occur in 4 of the last 5 roll calls (80%)" in message


def test_failure_unreachable_respects_auto_and_reachable_bands(campaign: Path) -> None:
    receipts = [_receipt(index, 1, 6) for index in range(3)]
    receipts += [_receipt(3, 1, 6, auto=True), _receipt(4, 1, 6, reachable_bands=["success"])]
    _rolls(campaign, receipts)
    assert _odds_findings(campaign, ROOMY_SCALE) == []  # 2 of 5 is under 80%
    receipts[0]["reachable_bands"] = ["success"]
    receipts[1]["auto"] = True
    _rolls(campaign, receipts)
    assert [rule for _, rule, _ in _odds_findings(campaign, ROOMY_SCALE)] == ["failure_unreachable"]


def test_failure_unreachable_reads_the_receipts_own_odds(campaign: Path) -> None:
    # An auto call was not rolled, even when its dice could have reached failure.
    autos = [_receipt(index, 5, 3, auto=True, reachable_bands=["success", "failure"]) for index in range(4)]
    _rolls(campaign, autos + [_receipt(4, 1, 6)])
    assert [rule for _, rule, _ in _odds_findings(campaign, ROOMY_SCALE)] == ["failure_unreachable"]
    # A receipt's floor band answers without working the call out again.
    floors = [_receipt(index, 1, 6, floor_band="success") for index in range(4)] + [_receipt(4, 1, 6)]
    _rolls(campaign, floors)
    assert [rule for _, rule, _ in _odds_findings(campaign, ROOMY_SCALE)] == ["failure_unreachable"]
    _rolls(campaign, [_receipt(index, 5, 3, floor_band="failure") for index in range(5)])
    assert _odds_findings(campaign, ROOMY_SCALE) == []


def test_failure_unreachable_falls_back_to_the_scale(campaign: Path) -> None:
    _rolls(campaign, [_receipt(0, 5, 3)])  # too few receipts to judge
    ((_, rule, message),) = _odds_findings(campaign, LIVE_SCALE)
    assert rule == "failure_unreachable" and "partial_heavy_cost could not occur in 22 of the scale's 25" in message
    assert _odds_findings(campaign, ROOMY_SCALE) == []
    assert _odds_findings(campaign, "") == []


def test_full_check_reports_scale_findings_on_the_profile(campaign: Path) -> None:
    profile = campaign / "play_profile.yaml"
    _write(profile, profile.read_text(encoding="utf-8") + LIVE_SCALE.replace("    bands:", "    auto_success_margin: 2\n    bands:"))
    rules = {finding["rule"]: finding for finding in _full(campaign) if finding["path"] == str(profile.resolve())}
    assert rules["auto_success_dead_zone"]["severity"] == "warning"
    assert rules["failure_unreachable"]["severity"] == "warning"
    assert rules["first_band_unreachable"]["severity"] == "info"


# ---------------------------------------------------------------------------
# Profile and note shape
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "records, reported",
    [("same", False), ("tr", False), ("pt-BR", False), ("Turkish please", True), ("", False)],
)
def test_records_language_setting_is_validated(records: str, reported: bool) -> None:
    found: list[tuple[str, str]] = []
    block = "narration:\n  language: tr\n" + (f"  records_language: {records}\n" if records else "")
    check_runtime.check_profile(block, Path("play_profile.yaml"), lambda severity, rule, message, path: found.append((severity, rule)))
    assert (("error", "records_language_invalid") in found) is reported


def test_note_core_missing_lists_its_files(tmp_path: Path) -> None:
    note = tmp_path / "characters" / "edda_vale.md"
    _write(note, "# Edda Vale\n\nTier: T2\n")
    extended: list[dict] = []
    check_runtime.check_notes(tmp_path, [], lambda severity, rule, message, path, **extra: extended.append({"rule": rule, **extra}))
    assert extended == [{"rule": "note_core_missing", "paths": [str(note)]}]
    plain: list[str] = []
    check_runtime.check_notes(tmp_path, [], lambda severity, rule, message, path: plain.append(rule))
    assert plain == ["note_core_missing"]


def test_full_check_keeps_note_core_missing_paths(campaign: Path) -> None:
    _write(campaign / "characters" / "edda_vale.md", "# Edda Vale\n\nTier: T2\n")
    (finding,) = _rules(_full(campaign), "note_core_missing")
    assert str((campaign / "characters" / "edda_vale.md").resolve()) in finding["paths"]


def test_an_empty_style_state_is_inert_only_without_the_lint(campaign: Path) -> None:
    _write(campaign / "style_state.json", (TOOLS.parent / "templates" / "campaign" / "style_state.json").read_text(encoding="utf-8"))
    current = campaign / "current_state.yaml"
    played = current.read_text(encoding="utf-8").replace("continuity_revision: 0", "continuity_revision: 8", 1)
    _write(current, played.replace("last_distilled_revision: 0", "last_distilled_revision: 8", 1))
    # No runtime block: the lint is on, and its history is the repetition memory.
    assert _rules(_full(campaign), "style_state_inert") == []
    profile = campaign / "play_profile.yaml"
    _write(profile, profile.read_text(encoding="utf-8") + "runtime:\n  presentation_lint: off\n")
    (inert,) = _rules(_full(campaign), "style_state_inert")
    assert inert["severity"] == "warning"
    # A lint history kept while the lint was on still holds that memory.
    _write(campaign / ".repog-runtime" / "lint_history.jsonl", '{"rules": {}}\n')
    assert _rules(_full(campaign), "style_state_inert") == []
    assert check_runtime.lint_keeps_style_memory(campaign) is True

"""Full-check content rules added in 0.4.0.

Kept apart from `check_state.py` so that file stays under its size budget.
Every rule here detects, counts and compares text already in the campaign's
records; none decides what a record means, and nothing here writes.

- Meaningful staleness: a dead or missing character still listed as present
  (`cast_dead_listed`), a present NPC without an active-cast row
  (`cast_present_missing`), a live relationship row naming a dead character
  (`relationship_dead_active`), and a current location that is not a node of
  the location graph (`location_unmapped`). Whether a row says gone or ended
  comes from the packs' `gone_terms` and `ended_terms`, stems included
  ("öldürül*" for "öldürüldü"), in every pack language.
- Note shape: a `## Now` section over its budget (`now_overflow`).
- Knowledge: a holder listed as not knowing a fact that a holder account
  records, or that a dated line mentions with the holder, in
  knowledge_boundaries.md or in the holder's own note
  (`knowledge_holder_conflict`).
- The age rule: an under-18 age that is the closest age of a romance or sex
  term in a character note (`minor_romance_history`), read by
  `lang_pack.minor_romance` exactly as the presentation lint reads a reply.
  HTML comments and lines copied from the note's template are left out.
- Records language: record bodies written in another language than the
  records language (`records_language_mismatch`, one aggregated warning).
  The records language is `lang_pack.campaign_records_language`.
- Power: a numeric `Power Band` below the note's highest stat
  (`power_band_mismatch`), and a stat above its tier's cap from `rules.md`,
  reported as the level-band spike the cap replaces (`early_stage_power_spike`).
- Acknowledgement: a `directives.md` row with Scope `check` whose Directive
  begins `acknowledge <rule_id>` (optionally `for <path or name>`, then
  optionally a reason) turns the matching warnings into info.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import check_runtime
import lang_pack
from repog_runtime import read_text

try:  # the writer's own `## Now` count, so this check and its fold agree
    import owner_ops
except ImportError:  # pragma: no cover - shipped beside this file
    owner_ops = None


Finding = dict[str, Any]

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "campaign"
NOTE_FOLDERS = ("characters", "places", "factions")

# `## Now` budget, shared with the writer's fold (spec 2.3).
NOW_MAX_CHARS = 800
NOW_MAX_DATED = 3
DAY_MARKERS = ("day", "gün", "tag", "día", "dia", "jour")
_MARKER = "(?:" + "|".join(DAY_MARKERS) + ")"
DATED_LINE_RE = re.compile(rf"^\s*(?:[-*+]\s+)?(?:[*_]{{1,2}})?{_MARKER}\s*\d+", re.IGNORECASE)
DATED_ANYWHERE_RE = re.compile(rf"\({_MARKER}\s*\d+\)", re.IGNORECASE)

PRESENCE_COLUMNS = ("status", "presence", "availability", "location", "activity", "last_seen")
EXAMPLE_NAMES = {"example_npc", "example_place", "example_neighbor", "character_a", "character_b"}

# The age rule's window and closeness are `lang_pack.minor_romance`'s: an age
# and a term in one sentence or two adjacent ones, or at most 220 characters
# apart, and only a term whose closest age is under 18 counts.
AGE_WINDOW_CHARS = lang_pack.AGE_WINDOW_CHARS
AGE_WINDOW_SENTENCES = lang_pack.AGE_WINDOW_SENTENCES + 1  # sentence breaks: fewer than this
ADULT_AGE = lang_pack.MINOR_AGE

# Language packs carry `age_patterns` (regexes for folded text whose `age`
# group holds the number), `romance_terms`, `affection_terms` and
# `affection_guards` (words; a word ending in `*` is a stem), `number_words`,
# `gone_terms` and `ended_terms`. These tables stand in for a pack without them.
_EN_UNITS = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
_EN_TEENS = ("ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen")
_EN_TENS = ("twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
_TR_UNITS = ("bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz")
_TR_TENS = ("on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan")
# A tens word in front is captured, so "twenty-five" or "yirmi beş" reads as an adult age.
_EN_NUMBER = rf"(?:\d{{1,3}}|(?:(?:{'|'.join(_EN_TENS)})[- ])?(?:{'|'.join(_EN_UNITS + _EN_TEENS)})|{'|'.join(_EN_TENS)})"
_EN_AT_NUMBER = rf"(?:1[0-7]|{'|'.join(_EN_TEENS[:8])})"
_EN_NOT_AN_AGE = r"(?!\s*(?::|o'clock|a\.?m\b|p\.?m\b|noon|midnight|sharp|bells?\b|in the (?:morning|afternoon|evening|night)|years?\b|months?\b|days?\b|hours?\b|minutes?\b|paces\b|percent\b|%))"
_TR_UNIT = r"(?:bir|iki|üç|dör[td]|beş|altı|yedi|sekiz|dokuz)"
_TR_NUMBER = rf"(?:\d{{1,3}}|(?:(?:{'|'.join(_TR_TENS)})\s+)?{_TR_UNIT}|{'|'.join(_TR_TENS)})"
# A day of the month ("ayın on beşinde", "Mayısın on dördünde") is no age.
_TR_NOT_A_DATE = (
    r"(?<!\bayın\s)(?<!\bayının\s)(?<!['’][ıiuü]n\s)(?<!['’]n[ıiuü]n\s)(?<!\b(?:martın|ekimin|ocağın)\s)"
    r"(?<!\b(?:şubatın|nisanın|mayısın|eylülün|kasımın)\s)(?<!\b(?:temmuzun|aralığın)\s)(?<!\b(?:haziranın|ağustosun)\s)"
)
FALLBACK_AGE_PATTERNS = {
    "en": (
        rf"\bat\s+(?P<age>{_EN_AT_NUMBER})\b{_EN_NOT_AN_AGE}",
        rf"\baged\s+(?P<age>{_EN_NUMBER})\b",
        rf"\bat\s+the\s+age\s+of\s+(?P<age>{_EN_NUMBER})\b",
        rf"\b(?P<age>{_EN_NUMBER})[- ]years?[- ]old\b",
    ),
    "tr": (
        rf"\b(?P<age>{_TR_NUMBER})\s+yaş(?:lar)?[ıi][mn][dt][ae]\w*",
        # "on beşimde", "on yedisindeyken": only the teen forms, because a bare
        # "altında" (beneath) or "birinde" (in one of them) is not an age.
        rf"{_TR_NOT_A_DATE}\b(?P<age>on\s+{_TR_UNIT})(?:[ıiuü]?[mn]|s[ıiuü]n)[dt][ae](?:yken)?\b",
    ),
}
FALLBACK_ROMANCE_TERMS = {
    "en": (
        "lover*", "romance", "romances", "romantic*", "sex", "sexual*", "slept with", "affair*", "seduc*",
        "intimate", "intimacy", "girlfriend*", "boyfriend*", "betrothed", "married", "marriage*", "wedding*",
        "courted", "courtship", "first love", "in love", "first kiss*",
    ),
    "tr": (
        "aşık*", "sevgilisi*", "sevgilim*", "sevgilin*", "sevgiliy*", "sevgili oldu*", "öpüş*", "öpücük*", "seks*",
        "cinsel*", "evlen*", "nişanl*", "flört*", "romantik*", "metres*", "birlikte oldu*",
    ),
}
FALLBACK_AFFECTION_TERMS = {"en": ("kiss*",), "tr": ("öp*",)}
FALLBACK_AFFECTION_GUARDS = {
    "en": ("mother*", "father*", "son", "sons", "daughter*", "child", "children", "brother*", "sister*", "forehead*", "cheek*"),
    "tr": ("anne*", "baba*", "oğlu*", "kızım*", "kızını", "kızına", "kızının", "kardeş*", "torun*", "alnından öp*", "elini öp*"),
}
# Words that mark a row as no longer present (active cast) or no longer current
# (relationship state).
FALLBACK_GONE_TERMS = {
    "en": ("dead", "deceased", "died", "killed", "gone", "left", "missing", "departed"),
    "tr": ("ölü", "öldü", "öldüğü*", "ölmüş*", "öldürül*", "vefat*", "kayıp", "kaybol*", "gitti*", "ayrıldı*", "artık yok"),
    "de": ("tot", "verstorben*", "fort", "weg", "gegangen", "vermisst"),
    "es": ("muerto", "muerta", "fallecido", "fallecida", "ido", "desaparecido", "desaparecida"),
    "fr": ("mort", "morte", "décédé*", "parti", "partie", "disparu*"),
}
FALLBACK_ENDED_TERMS = {
    "en": ("dead", "deceased", "died", "ended", "past", "former", "over"),
    "tr": ("ölü", "öldü", "ölmüş*", "öldürül*", "bitti*", "sona er*", "geçmiş", "eski"),
    "de": ("tot", "beendet", "vorbei", "vergangen*", "ehemalig*"),
    "es": ("muerto", "muerta", "terminado", "terminada", "pasado", "pasada", "antiguo", "antigua"),
    "fr": ("mort", "morte", "terminé*", "passé", "passée", "ancien", "ancienne"),
}
_FALLBACKS = (
    ("age_patterns", FALLBACK_AGE_PATTERNS),
    ("romance_terms", FALLBACK_ROMANCE_TERMS),
    ("affection_terms", FALLBACK_AFFECTION_TERMS),
    ("affection_guards", FALLBACK_AFFECTION_GUARDS),
    ("gone_terms", FALLBACK_GONE_TERMS),
    ("ended_terms", FALLBACK_ENDED_TERMS),
)


def _counting(words: str, start: int = 1) -> dict[str, int]:
    """Space-separated words numbered from `start`; `a/b` gives two spellings one number."""

    return {spelling: start + index for index, word in enumerate(words.split()) for spelling in word.split("/")}


# Number words for a pack without its own, so an `age` group can still be read.
_NUMBER_WORDS = {
    **_counting(" ".join(_EN_UNITS + _EN_TEENS)),
    **{word: (index + 2) * 10 for index, word in enumerate(_EN_TENS)},
    **{word: (index + 1) * 10 for index, word in enumerate(_TR_TENS)},
    **{word: index + 1 for index, word in enumerate(_TR_UNITS)},
    "dörd": 4,
    **_counting("ein/eins zwei drei vier fünf sechs sieben acht neun zehn elf zwölf dreizehn vierzehn fünfzehn sechzehn siebzehn achtzehn neunzehn zwanzig"),
    **_counting("un/uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis/dieciseis diecisiete dieciocho diecinueve veinte"),
    **_counting("un deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize"),
    "vingt": 20, "dreissig": 30, "treinta": 30, "trente": 30,
}
# A line of the character template that states the age rule itself, in any
# template version ("Age rule: no romantic or sexual relationship ..."), is
# guidance, not history.
AGE_RULE_GUIDANCE_RE = re.compile(r"^\s*(?:<!--\s*)?(?:[-*]\s+)?(?:\*\*)?age rule:", re.IGNORECASE)

# Records language: a body is judged only when it has enough words, and it is
# reported only when another language wins clearly and the records language's
# function words are a small share of it (shared short words such as Turkish
# "her" or "on" also occur in English prose).
RECORDS_MIN_WORDS = 25
RECORDS_MIN_CONFIDENCE = 0.15
RECORDS_MAX_OWN_SHARE = 0.25
RECORDS_SAMPLE_CHARS = 4000
# The log and the two table files are multilingual by design; session_zero.md
# is rendered by the Session 0 helper, whose managed sections stay in English.
RECORDS_SKIPPED = {"session_log.md", "glossary.md", "directives.md", "session_zero.md"}
# A prose line whose words are mostly the words of its file's template is
# template guidance, possibly from an older template version, not content. Old
# guidance shares at least 73% of its words with the current template; written
# content, even in the template's language, at most about 60%.
TEMPLATE_WORD_SHARE = 2 / 3
# A `- Label:` prefix of up to this many characters is structure ("May be
# created within accepted boundaries and shown at review:" is 61).
LABEL_MAX_CHARS = 70
_LABEL_RE = re.compile(rf"^(?:\*\*)?[^:.!?]{{1,{LABEL_MAX_CHARS}}}:(?:\*\*)?\s*")
# A table cell of one word is an enum value, an id or a number ("alive",
# "fade", "T2"), which the records keep as the templates write them.
CELL_MIN_WORDS = 2
_WORD_RE = re.compile(r"[^\W_]+")

# `acknowledge <rule_id>`, then optionally `for <path or name>`, then optionally
# a reason after a separator: "acknowledge now_overflow.", "acknowledge
# now_overflow (the Player accepted it)", "acknowledge now_overflow for Branak -
# long notes are fine". Any other text after the rule id acknowledges nothing.
ACKNOWLEDGE_RE = re.compile(r"^acknowledge\s+([A-Za-z0-9_]+)\b(.*)$", re.IGNORECASE | re.DOTALL)
ACKNOWLEDGE_REASON_RE = re.compile(r"\s*[—–]\s*|\s+-\s+|[,;:(]|\.(?=\s|$)")
ACKNOWLEDGE_TARGET_RE = re.compile(r"^\s+for\s+(\S.*?)\s*$", re.IGNORECASE | re.DOTALL)
# The age rule is a safety boundary, not a table preference.
NEVER_ACKNOWLEDGED = frozenset({"minor_romance_history"})

TIER_RE = re.compile(r"(?im)^[ \t]*(?:[-*][ \t]+)?Tier:[ \t]*(T\d)\b")
POWER_BAND_RE = re.compile(r"(?im)^[ \t]*(?:[-*][ \t]+)?Power Band:[ \t]*(.*?)[ \t]*$")
BAND_NUMBER_RE = re.compile(r"^\(?\s*(-?\d+)(?:\s*(?:-|–|—|to)\s*(-?\d+))?\s*\)?(?:\s.*)?$")
STAT_LINE_RE = re.compile(r"^\s*[-*]\s+([^:\n]+?):\s*(-?\d+)\b")
TIER_CAP_RE = re.compile(r"(?im)^\s*[-*]\s+(T\d)\s*:\s*(-?\d+)\b")


# ---------------------------------------------------------------------------
# Small text helpers
# ---------------------------------------------------------------------------

# One full check reads many files more than once; while it runs, each file is
# read once.
_TEXTS: dict[Path, str] | None = None


def _finding(severity: str, rule: str, message: str, path: Path | str | None, **extra: Any) -> Finding:
    finding: Finding = {"severity": severity, "rule": rule, "message": message, "path": str(path) if path else None}
    finding.update(extra)
    return finding


def key(text: str) -> str:
    """A comparison key for names in any script: folded, word runs joined by `_`."""

    return re.sub(r"[\W_]+", "_", lang_pack.fold(str(text or ""), None)).strip("_")


def _read(path: Path) -> str:
    if _TEXTS is None:
        return read_text(path) if path.is_file() else ""
    if path not in _TEXTS:
        _TEXTS[path] = read_text(path) if path.is_file() else ""
    return _TEXTS[path]


def _notes(campaign: Path, folder: str) -> list[Path]:
    directory = campaign / folder
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.glob("*.md") if not path.name.startswith("_"))


def _section(text: str, heading: str) -> str:
    """The body of the first `## heading` (case-insensitive), up to the next `#`/`##`."""

    match = re.search(rf"(?im)^##[ \t]+{re.escape(heading)}[ \t]*$", text)
    if match is None:
        return ""
    following = re.search(r"(?m)^#{1,2}[ \t]+\S", text[match.end() :])
    return text[match.end() : match.end() + following.start()] if following else text[match.end() :]


def _without_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def tables(text: str) -> list[list[dict[str, str]]]:
    """Every Markdown table in `text`, each as a list of header -> cell rows."""

    found: list[list[dict[str, str]]] = []
    block: list[str] = []
    for line in [*_without_comments(text).splitlines(), ""]:
        if line.strip().startswith("|"):
            block.append(line)
            continue
        if len(block) >= 2 and set(block[1].replace("|", "").strip()) <= set("-: "):
            headers = _cells(block[0])
            rows = [dict(zip(headers, _cells(row))) for row in block[2:] if len(_cells(row)) == len(headers)]
            found.append([row for row in rows if any(row.values())])
        block = []
    return found


def _table_with(text: str, *columns: str) -> tuple[list[dict[str, str]], str]:
    """The rows of the first table holding one of `columns`, and that column."""

    for rows in tables(text):
        headers = list(rows[0]) if rows else []
        for column in columns:
            if column in headers:
                return rows, column
    return [], ""


@lru_cache(maxsize=1)
def _packs() -> tuple[dict[str, Any], ...]:
    """Every pack, with this module's tables standing in for the keys a pack lacks."""

    codes = [*lang_pack.available_codes()]
    for _, table in _FALLBACKS:
        codes.extend(table)
    packs = []
    for code in dict.fromkeys(codes):
        pack = dict(lang_pack.load_pack(code))
        for name, table in _FALLBACKS:
            if not pack.get(name) and code in table:
                pack[name] = list(table[code])
        if not pack.get("number_words"):
            pack["number_words"] = dict(_NUMBER_WORDS)
        if code == "tr":
            pack.setdefault("casefold", "turkish")
        packs.append(pack)
    return tuple(packs)


def _says(text: str, terms: str) -> bool:
    """True when `text` holds one of the packs' `terms` (`gone_terms`, `ended_terms`), in any language."""

    return lang_pack.says_any(text, terms, _packs())


def _relative(campaign: Path, path: Path) -> str:
    try:
        return path.relative_to(campaign).as_posix()  # the usual case, without touching the disk
    except ValueError:
        pass
    try:
        return path.resolve().relative_to(campaign.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


# ---------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------


def character_statuses(campaign: Path) -> dict[str, tuple[str, str, Path]]:
    """Name key -> (title, first word of the Core `- Status:`, note) for every character note."""

    statuses: dict[str, tuple[str, str, Path]] = {}
    for note in _notes(campaign, "characters"):
        text = _read(note)
        words = check_runtime.core_status(text).split()
        status = words[0].strip(".,;:()") if words else ""
        title = check_runtime.note_title(text, note)
        for name in (title, note.stem):
            statuses.setdefault(key(name), (title, status, note))
    return statuses


def _name_column(rows: list[dict[str, str]]) -> str:
    headers = list(rows[0]) if rows else []
    for column in ("NPC", "Name", "Character"):
        if column in headers:
            return column
    return headers[0] if headers else ""


def check_memory(campaign: Path, *, location: str, present_npcs: Iterable[str]) -> list[Finding]:
    """The content rules that replace the revision-lag staleness warnings."""

    findings: list[Finding] = []
    statuses = character_statuses(campaign)
    absent = {name: entry for name, entry in statuses.items() if entry[1] in {"dead", "missing"}}

    cast_path = campaign / "active_cast.md"
    if cast_path.is_file():
        cast_text = _read(cast_path)
        rows = next((rows for rows in tables(cast_text) if rows), [])
        column = _name_column(rows)
        listed: set[str] = set()
        for row in rows:
            name = row.get(column, "")
            if not name or key(name) in EXAMPLE_NAMES:
                continue
            listed.add(key(name))
            entry = absent.get(key(name))
            if entry is None:
                continue
            presence = [value for header, value in row.items() if any(word in key(header) for word in PRESENCE_COLUMNS)]
            if not presence:
                presence = [value for header, value in row.items() if header != column]
            if not _says(" ; ".join(presence), "gone_terms"):
                findings.append(
                    _finding(
                        "warning",
                        "cast_dead_listed",
                        f"{name} is {entry[1]} in {_relative(campaign, entry[2])} but active_cast.md still lists them "
                        "as present; mark the row gone or remove it.",
                        cast_path,
                    )
                )
        for npc in present_npcs:
            if npc.strip() and key(npc) not in listed:
                findings.append(
                    _finding(
                        "warning",
                        "cast_present_missing",
                        f"current_scene.present_npcs names {npc.strip()}, who has no active_cast.md row; add the row.",
                        cast_path,
                    )
                )

    relationship_path = campaign / "relationship_map.md"
    dead = {name for name, entry in statuses.items() if entry[1] == "dead"}
    if relationship_path.is_file() and dead:
        rows, _ = _table_with(_read(relationship_path), "From", "To")
        for row in rows:
            ends = [row.get("From", ""), row.get("To", "")]
            if any(key(end) in EXAMPLE_NAMES for end in ends):
                continue
            named = [end for end in ends if key(end) in dead]
            state = row.get("Status") or row.get("Relation", "")
            if named and not _says(state, "ended_terms"):
                findings.append(
                    _finding(
                        "warning",
                        "relationship_dead_active",
                        f"The relationship {ends[0]} / {ends[1]} names {named[0]}, who is dead, but its state is "
                        f"'{state}'; record it as dead, ended or past.",
                        relationship_path,
                    )
                )

    graph_path = campaign / "location_graph.md"
    if location.strip() and graph_path.is_file():
        rows, _ = _table_with(_read(graph_path), "From", "To")
        nodes = {key(row.get(end, "")) for row in rows for end in ("From", "To")} - {""} - EXAMPLE_NAMES
        if key(location) not in nodes:
            findings.append(
                _finding(
                    "warning",
                    "location_unmapped",
                    f"current_scene.location {location.strip()} is not a node in location_graph.md; add its connections.",
                    graph_path,
                )
            )
    return findings


# ---------------------------------------------------------------------------
# `## Now` budget
# ---------------------------------------------------------------------------


def is_dated(line: str) -> bool:
    """A line or bullet starting with a day marker, or holding `(day N)`."""

    return bool(DATED_LINE_RE.match(line) or DATED_ANYWHERE_RE.search(line))


def now_budget(text: str) -> tuple[int, int] | None:
    """(characters, dated entries) of a note's `## Now` body, or None without one.

    The writer's count (`owner_ops.now_status`) decides when it is available,
    so a note the writer's fold leaves alone is never reported.
    """

    writer_count = getattr(owner_ops, "now_status", None)
    if writer_count is not None:
        return writer_count(text)
    if re.search(r"(?im)^##[ \t]+Now[ \t]*$", text) is None:
        return None
    body = _without_comments(_section(text, "Now")).strip()
    return len(body), sum(1 for line in body.splitlines() if is_dated(line))


def check_now(campaign: Path) -> list[Finding]:
    findings: list[Finding] = []
    for folder in NOTE_FOLDERS:
        for note in _notes(campaign, folder):
            budget = now_budget(_read(note))
            if budget is None:
                continue
            characters, dated = budget
            if characters > NOW_MAX_CHARS or dated > NOW_MAX_DATED:
                findings.append(
                    _finding(
                        "warning",
                        "now_overflow",
                        f"## Now holds {characters} characters and {dated} dated entries (budget {NOW_MAX_CHARS} "
                        f"and {NOW_MAX_DATED}); keep the current state and move older dated lines to ## History.",
                        note,
                    )
                )
    return findings


# ---------------------------------------------------------------------------
# Knowledge holders
# ---------------------------------------------------------------------------


def _subsections(text: str) -> list[tuple[str, str]]:
    marks = list(re.finditer(r"(?m)^###[ \t]+(.+?)[ \t]*$", text))
    result = []
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
        following = re.search(r"(?m)^#{1,2}[ \t]+\S", text[mark.end() : end])
        result.append((mark.group(1).strip(), text[mark.end() : mark.end() + following.start()] if following else text[mark.end() : end]))
    return result


def _field(body: str, label: str) -> str:
    match = re.search(rf"(?im)^[ \t]*(?:[-*][ \t]+)?{re.escape(label)}:[ \t]*(.*?)[ \t]*$", body)
    return match.group(1).strip().strip("`") if match else ""


def _ids(value: str) -> list[str]:
    ids = [item.strip().strip("`'\"[]()") for item in re.split(r"[,;\s]+", value)]
    return [item for item in ids if item and item.casefold() not in {"none", "-", "n/a", "tbd", "todo"}]


def _holder_notes(campaign: Path) -> dict[str, Path]:
    """Name key -> note, for the character and faction notes a holder can be (title or file stem)."""

    notes: dict[str, Path] = {}
    for folder in ("characters", "factions"):
        for note in _notes(campaign, folder):
            for name in (check_runtime.note_title(_read(note), note), note.stem):
                notes.setdefault(key(name), note)
    return notes


def check_knowledge(campaign: Path) -> list[Finding]:
    path = campaign / "knowledge_boundaries.md"
    text = _without_comments(_read(path))
    if not text:
        return []
    limits: list[tuple[str, str, str]] = []  # (holder, fact id, kind)
    for holder, body in _subsections(text):
        for label, kind in (("Explicitly unknown fact ids", "explicitly unknown"), ("Must-not-imply fact ids", "must-not-imply")):
            limits.extend((holder, fact, kind) for fact in _ids(_field(body, label)))
    if not limits:
        return []
    accounts: dict[tuple[str, str], str] = {}
    for name, body in _subsections(_section(text, "Holder Accounts")):
        holder, fact, stance = _field(body, "Holder ref"), _field(body, "Fact id"), _field(body, "Stance").casefold()
        if holder and fact and stance in {"confirmed", "suspected"}:
            for name_key in {key(holder), key(Path(holder).stem)}:
                accounts.setdefault((name_key, fact.casefold()), f"holder account {name} records it as {stance}")
    dated = [line.strip() for line in text.splitlines() if is_dated(line)]
    holder_notes = _holder_notes(campaign)
    findings: list[Finding] = []
    for holder, fact, kind in limits:
        source = accounts.get((key(holder), fact.casefold()))
        fact_re = re.compile(rf"(?<![\w-]){re.escape(fact)}(?![\w-])")
        if source is None:
            holder_key = f"_{key(holder)}_"
            line = next((line for line in dated if fact_re.search(line) and holder_key in f"_{key(line)}_"), None)
            source = f"a dated line mentions them with it: '{line[:80]}'" if line else None
        note = holder_notes.get(key(holder))
        if source is None and note is not None:
            own = _without_comments(_read(note)).splitlines()
            line = next((line.strip() for line in own if is_dated(line) and fact_re.search(line)), None)
            if line:
                source = f"a dated line of {_relative(campaign, note)} mentions it: '{line[:80]}'"
        if source:
            findings.append(
                _finding(
                    "warning",
                    "knowledge_holder_conflict",
                    f"{holder} is listed as {kind} for {fact}, but {source}; check whether they know it and update "
                    "the holder's lists, the account or the line.",
                    path,
                )
            )
    return findings


# ---------------------------------------------------------------------------
# The age rule
# ---------------------------------------------------------------------------


def minor_proximity(text: str) -> tuple[str, str] | None:
    """The first (age expression, romance term) the age rule reports in `text`, or None.

    `lang_pack.minor_romance` over every pack, this module's tables standing
    in for a pack's missing keys: the same reading as the presentation lint's
    `minor_sexual_proximity`. HTML comments are left out.
    """

    clean = unicodedata.normalize("NFC", _without_comments(str(text or "")))
    pairs = lang_pack.minor_romance(clean, _packs())
    if not pairs:
        return None
    age, term = pairs[0]
    return clean[age[0] : age[1]].strip(), clean[term[0] : term[1]].strip()


def age_rule_text(text: str, template: frozenset[str] = frozenset()) -> str:
    """A note's text as the age rule reads it: comments out, and template lines as bare placeholders.

    A line copied from the note's template (`template`, whitespace-normalized)
    or one stating the age rule itself is guidance: it becomes "-", so the
    lines around it keep their distance and no guidance word ("romantic")
    meets an age the note gives.
    """

    lines = _without_comments(str(text or "")).split("\n")
    return "\n".join(
        "-" if (" ".join(line.split()) in template and line.strip()) or AGE_RULE_GUIDANCE_RE.match(line) else line
        for line in lines
    )


def check_age_rule(campaign: Path) -> list[Finding]:
    findings: list[Finding] = []
    notes = _notes(campaign, "characters") + ([campaign / "player.md"] if (campaign / "player.md").is_file() else [])
    for note in notes:
        text = _read(note)
        pair = minor_proximity(age_rule_text(text, _template_for(campaign, note)))
        if pair is None:
            continue
        findings.append(
            _finding(
                "warning",
                "minor_romance_history",
                f"{check_runtime.note_title(text, note)}: an age under 18 ('{pair[0]}') is the closest age to "
                f"'{pair[1]}'. No romantic or sexual relationship may begin before 18; correct the ages or the "
                f"history, or state the adult age beside the term. If '{pair[0]}' is a date or a clock time, write "
                "it in digits ('15 Mayıs', '11:00'). This cannot be deferred or acknowledged.",
                note,
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Records language
# ---------------------------------------------------------------------------


def records_language(profile_text: str) -> str:
    """The records language code a play profile sets, or "" when it cannot be known (auto or unset).

    A campaign whose profile says `auto` takes the language the presentation
    lint last saw (`lang_pack.campaign_records_language`).
    """

    value = lang_pack.records_language_setting(profile_text)
    return "" if value == "auto" else value


@lru_cache(maxsize=64)
def _template_lines(relative: str) -> frozenset[str]:
    text = read_text(TEMPLATE_DIR / relative)
    return frozenset(" ".join(line.split()) for line in text.splitlines() if line.strip())


@lru_cache(maxsize=64)
def _template_words(relative: str) -> frozenset[str]:
    return frozenset(_words(read_text(TEMPLATE_DIR / relative)))


def _words(text: str) -> list[str]:
    return lang_pack.tokens(lang_pack.fold(text, None))


def _template_sources(campaign: Path, path: Path) -> tuple[str, ...]:
    relative = _relative(campaign, path)
    if "/" in relative:
        folder = relative.split("/", 1)[0]
        return f"{folder}/_template.md", f"{folder}/_companion_template.md"
    return (relative,)


def _template_for(campaign: Path, path: Path) -> frozenset[str]:
    """The template lines of a record's file, whitespace-normalized."""

    return frozenset().union(*(_template_lines(source) for source in _template_sources(campaign, path)))


def _vocabulary_for(campaign: Path, path: Path) -> frozenset[str]:
    """The folded words of a record's template."""

    return frozenset().union(*(_template_words(source) for source in _template_sources(campaign, path)))


def _mostly_template(line: str, vocabulary: frozenset[str]) -> bool:
    words = _words(line)
    return bool(words) and sum(word in vocabulary for word in words) >= TEMPLATE_WORD_SHARE * len(words)


def _record_names(campaign: Path) -> list[str]:
    names: set[str] = set()
    for folder in NOTE_FOLDERS:
        for note in _notes(campaign, folder):
            names.add(check_runtime.note_title(_read(note), note))
    for relative, columns in (("glossary.md", ("Term", "Preferred", "Variants")), ("active_cast.md", ("NPC", "Name"))):
        for rows in tables(_read(campaign / relative)):
            for row in rows:
                for column in columns:
                    names.update(part.strip() for part in row.get(column, "").split(",") if part.strip())
    state = _read(campaign / "current_state.yaml")
    player = re.search(r"(?m)^  name:[ \t]*(.+?)[ \t]*$", state)
    if player:
        names.add(player.group(1).strip().strip("'\""))
    return [name for name in names if len(name) >= 2]


def _name_key(word: str) -> str:
    return unicodedata.normalize("NFC", word).casefold()


@lru_cache(maxsize=8)
def _name_patterns(names: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    """(folded first word, regex for the folded name) for each name, longest first."""

    found = set()
    for name in names:
        words = [_name_key(word) for word in _WORD_RE.findall(name)]
        if words:
            found.add((words[0], r"[\W_]+".join(re.escape(word) for word in words)))
    return tuple(sorted(found, key=lambda item: (-len(item[1]), item[1])))


@lru_cache(maxsize=256)
def _names_regex(bodies: tuple[str, ...]) -> re.Pattern[str]:
    return re.compile(r"(?<![^\W_])(?:" + "|".join(bodies) + r")(?![^\W_])")


def _without_names(body: str, names: Iterable[str]) -> str:
    """`body` with every listed name blanked, as whole words in any case.

    Only the names whose first word occurs in the body at all go into the
    one regex that removes them, so a long name list costs a substring test
    per name.
    """

    patterns = _name_patterns(tuple(sorted({name for name in names if name.strip()})))
    folded = _name_key(body)
    present = tuple(regex for first, regex in patterns if first in folded)
    if not present:
        return body
    matcher = _names_regex(present)
    if len(folded) != len(body):
        return matcher.sub(" ", folded)
    pieces: list[str] = []
    cursor = 0
    for match in matcher.finditer(folded):
        pieces.append(body[cursor : match.start()] + " ")
        cursor = match.end()
    pieces.append(body[cursor:])
    return "".join(pieces)


def record_body(
    text: str,
    *,
    template: frozenset[str] = frozenset(),
    vocabulary: frozenset[str] = frozenset(),
    names: Iterable[str] = (),
) -> str:
    """A record's prose for language detection: structure, template text and names stripped.

    `template` holds the template's lines, dropped when they recur verbatim;
    `vocabulary` its words, which drop a prose line or a table cell made mostly
    of them (a category, an option, an enum value). A one-word cell (an enum
    value, an id, a number) is structure too.
    """

    text = _without_comments(text)
    text = re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1[^\n]*$", "", text)
    kept: list[str] = []
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        is_row = stripped.startswith("|")
        header, in_table = is_row and not in_table, is_row
        if header or (is_row and set(stripped) <= set("|-: ")):
            continue  # a table header or separator
        if not stripped or stripped.startswith("#") or " ".join(stripped.split()) in template:
            continue
        if is_row:
            cells = [
                cell
                for cell in _cells(stripped)
                if len(_WORD_RE.findall(cell)) >= CELL_MIN_WORDS and not (vocabulary and _mostly_template(cell, vocabulary))
            ]
            if cells:
                kept.append(" ".join(cells))
            continue
        stripped = re.sub(r"^(?:[-*+]|\d+\.)\s+", "", stripped)
        stripped = _LABEL_RE.sub("", stripped)  # a `Label:` prefix
        if vocabulary and _mostly_template(stripped, vocabulary):
            continue
        kept.append(stripped)
    body = re.sub(r"`[^`]*`|https?://\S+", " ", "\n".join(kept))[: RECORDS_SAMPLE_CHARS * 2]
    return _without_names(body, names)[:RECORDS_SAMPLE_CHARS]


def body_language(body: str, records_code: str) -> str | None:
    """The other language a body is confidently written in, or None."""

    code, confidence = lang_pack.detect_language(body, min_words=RECORDS_MIN_WORDS)
    if code is None or code == records_code or confidence < RECORDS_MIN_CONFIDENCE:
        return None
    ratios = lang_pack.stopword_ratios(body, [code, records_code], min_words=RECORDS_MIN_WORDS)
    return code if ratios.get(records_code, 0.0) <= RECORDS_MAX_OWN_SHARE * ratios.get(code, 0.0) else None


def _record_files(campaign: Path) -> list[Path]:
    files = [path for path in sorted(campaign.glob("*.md")) if path.name not in RECORDS_SKIPPED]
    for folder in NOTE_FOLDERS:
        files.extend(_notes(campaign, folder))
    return files


def _language_listing(campaign: Path, files: list[tuple[Path, str]]) -> str:
    listed = ", ".join(f"{_relative(campaign, path)} ({detected})" for path, detected in files[:20])
    return listed + (f", and {len(files) - 20} more" if len(files) > 20 else "")


def check_records_language(
    campaign: Path, acknowledged_rows: tuple[tuple[str, str, str | None], ...] | list = ()
) -> list[Finding]:
    """One aggregated `records_language_mismatch`; a row acknowledging one file drops just that file."""

    code = lang_pack.campaign_records_language(campaign)
    if not code or code not in lang_pack.available_codes():
        return []
    names = _record_names(campaign)
    mismatched: list[tuple[Path, str]] = []
    for path in _record_files(campaign):
        body = record_body(
            _read(path),
            template=_template_for(campaign, path),
            vocabulary=_vocabulary_for(campaign, path),
            names=names,
        )
        detected = body_language(body, code)
        if detected:
            mismatched.append((path, detected))
    directive_for: dict[Path, str] = {}
    for path, _ in mismatched:
        for directive, rule, target in acknowledged_rows:
            if rule == "records_language_mismatch" and target and _target_matches(campaign, target, path):
                directive_for.setdefault(path, directive)
    open_files = [item for item in mismatched if item[0] not in directive_for]
    directives = ", ".join(sorted(set(directive_for.values())))
    if not mismatched:
        return []
    if not open_files:
        # Every file is acknowledged by name: the finding stays visible as info.
        return [
            _finding(
                "info",
                "records_language_mismatch",
                f"Record file(s) in another language than the records language '{code}': "
                f"{_language_listing(campaign, mismatched)} (acknowledged by {directives})",
                campaign,
                paths=[str(path) for path, _ in mismatched],
                acknowledged_by=directives,
            )
        ]
    note = f" {len(directive_for)} more acknowledged by {directives}." if directive_for else ""
    return [
        _finding(
            "warning",
            "records_language_mismatch",
            f"{len(open_files)} record file(s) read as another language than the records language '{code}': "
            f"{_language_listing(campaign, open_files)}. Rewrite their content in '{code}' and keep the structure "
            f"(headings, labels, table headers, enum values) as it is.{note}",
            campaign,
            paths=[str(path) for path, _ in open_files],
        )
    ]


# ---------------------------------------------------------------------------
# Power
# ---------------------------------------------------------------------------


def tier_caps(rules_text: str) -> dict[str, int]:
    """`## Tier Caps` lines (`- T1: n`) as {"t1": n}."""

    return {tier.casefold(): int(cap) for tier, cap in TIER_CAP_RE.findall(_section(_without_comments(rules_text), "Tier Caps"))}


def band_upper(power_band: str) -> int | None:
    """The top of a numeric Power Band (`3`, `1-3`, `(1-3)`), or None for a worded band."""

    match = BAND_NUMBER_RE.match(power_band.strip().strip("`"))
    if match is None:
        return None
    return int(match.group(2) or match.group(1))


def note_stats(text: str) -> dict[str, int]:
    """Integer `- Name: n` lines of the note's Stats block."""

    body = _section(text, "Stats (Numeric Grounding Only)") or _section(text, "Stats")
    stats: dict[str, int] = {}
    for line in _without_comments(body).splitlines():
        match = STAT_LINE_RE.match(line)
        if match:
            stats[match.group(1).strip()] = int(match.group(2))
    return stats


def check_power(campaign: Path) -> list[Finding]:
    """`power_band_mismatch` and tier-cap breaches for character notes with numeric stats.

    A tier's cap replaces the level-band ceiling for that tier, so a stat above
    it is reported as `early_stage_power_spike`, the rule Session 0 readiness
    already blocks on. It is answered by a Power Band that covers the stat, as
    `rules.md` Tier Caps says, or by an acknowledging directive.
    """

    caps = tier_caps(_read(campaign / "rules.md"))
    findings: list[Finding] = []
    for note in _notes(campaign, "characters"):
        text = _read(note)
        stats = note_stats(text)
        if not stats:
            continue
        title = check_runtime.note_title(text, note)
        top_name, top = max(stats.items(), key=lambda item: item[1])
        band = POWER_BAND_RE.search(text)
        upper = band_upper(band.group(1)) if band else None
        if upper is not None and upper < top:
            findings.append(
                _finding(
                    "warning",
                    "power_band_mismatch",
                    f"{title}: Power Band {band.group(1).strip()} is lower than its highest stat ({top_name} {top}); "
                    "raise the band or lower the stat.",
                    note,
                )
            )
        tier = TIER_RE.search(text)
        cap = caps.get(tier.group(1).casefold()) if tier else None
        if cap is not None and top > cap and (upper is None or upper < top):
            above = ", ".join(f"{name} {value}" for name, value in stats.items() if value > cap)
            findings.append(
                _finding(
                    "warning",
                    "early_stage_power_spike",
                    f"{title} ({tier.group(1).upper()}) has {above} above the {tier.group(1).upper()} cap {cap} "
                    "from rules.md Tier Caps; give it a Power Band that covers the stat or lower the stat.",
                    note,
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Acknowledgement
# ---------------------------------------------------------------------------


def parse_acknowledgement(directive: str) -> tuple[str, str | None] | None:
    """(rule id, target or None) of an `acknowledge` Directive, or None when it is not one."""

    match = ACKNOWLEDGE_RE.match(directive.replace("`", "").strip())
    if match is None:
        return None
    rest = ACKNOWLEDGE_REASON_RE.split(match.group(2), maxsplit=1)[0]  # the reason is dropped
    if not rest.strip():
        return match.group(1), None
    target = ACKNOWLEDGE_TARGET_RE.match(rest)
    return (match.group(1), target.group(1).strip("'\"")) if target else None


def acknowledgements(campaign: Path) -> list[tuple[str, str, str | None]]:
    """(directive id, rule id, target or None) for each active `check` directive row."""

    rows, _ = _table_with(_read(campaign / "directives.md"), "Directive")
    found: list[tuple[str, str, str | None]] = []
    for row in rows:
        if row.get("Scope", "").strip("` ").casefold() != "check":
            continue
        if row.get("Status", "active").strip("` ").casefold().startswith("retired"):
            continue
        parsed = parse_acknowledgement(row.get("Directive", ""))
        if parsed is not None:
            found.append((row.get("Id", "").strip("` ") or "a directive", *parsed))
    return found


def _target_matches(campaign: Path, target: str, path: Path) -> bool:
    wanted = target.strip().replace("\\", "/").strip("/").casefold()
    if wanted in {_relative(campaign, path).casefold(), path.name.casefold()}:
        return True
    if key(target) and key(target) == key(path.stem):
        return True
    if path.suffix == ".md" and path.is_file():
        return key(target) == key(check_runtime.note_title(_read(path), path))
    return False


def _covers(campaign: Path, target: str, finding: Finding) -> bool:
    """Whether a targeted row covers a finding about one file."""

    path = Path(str(finding.get("path") or ""))
    if finding.get("path") and _target_matches(campaign, target, path):
        return True
    # A name in the message, for a finding about one file (not a folder).
    return bool(key(target)) and path.suffix != "" and f"_{key(target)}_" in f"_{key(finding.get('message', ''))}_"


def _covering(campaign: Path, rows: list[tuple[str, str | None]], finding: Finding) -> list[str]:
    """The directive ids that acknowledge a finding, or [] when it stays a warning.

    A row without a target covers the whole rule. An aggregated finding
    (one that lists `paths`) is covered when targeted rows together match
    every listed file.
    """

    whole = [directive for directive, target in rows if target is None]
    if whole:
        return whole[:1]
    targeted = [(directive, target) for directive, target in rows if target is not None]
    if finding.get("paths"):
        covering = [
            next((directive for directive, target in targeted if _target_matches(campaign, target, Path(path))), None)
            for path in finding["paths"]
        ]
        return sorted(set(covering)) if None not in covering else []
    return next(([directive] for directive, target in targeted if _covers(campaign, target, finding)), [])


def acknowledge(campaign: Path, findings: list[Finding], found: list[tuple[str, str, str | None]] | None = None) -> None:
    """Turn acknowledged warnings into info, in place."""

    found = acknowledgements(campaign) if found is None else found
    if not found:
        return
    for finding in findings:
        if finding.get("severity") != "warning" or finding.get("rule") in NEVER_ACKNOWLEDGED:
            continue
        rows = [(directive, target) for directive, rule, target in found if rule == finding.get("rule")]
        directives = ", ".join(_covering(campaign, rows, finding))
        if directives:
            finding["severity"] = "info"
            finding["message"] = f"{finding.get('message', '')} (acknowledged by {directives})"
            finding["acknowledged_by"] = directives


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def check_campaign_content(
    campaign: Path, *, location: str, present_npcs: Iterable[str], numeric: bool = True
) -> list[Finding]:
    """Every 0.4.0 content rule for a full check (acknowledgement runs separately).

    `numeric` is false when the campaign's resolution grounding is not
    numeric; the power checks then have no stats to compare.
    """

    global _TEXTS
    campaign = Path(campaign)
    outer = _TEXTS
    _TEXTS = {} if outer is None else outer
    try:
        findings = check_memory(campaign, location=location, present_npcs=list(present_npcs))
        findings += check_now(campaign)
        findings += check_knowledge(campaign)
        findings += check_age_rule(campaign)
        findings += check_records_language(campaign, acknowledgements(campaign))
        if numeric:
            findings += check_power(campaign)
    finally:
        _TEXTS = outer
    return findings

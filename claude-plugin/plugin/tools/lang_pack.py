"""Language packs: per-language word lists and patterns kept as data, not code.

Every language-aware runtime check (presentation lint, scene capsule, name
check, the full check's age rule) reads what it knows about a language from
`plugin/packs/languages/<code>.json`. This module only loads packs, folds case
the way a language folds it, splits words and sentences in any script, counts
phrases, guesses a text's language from its function words, and places the
age expressions and romance terms its packs match (`minor_romance`). It never
decides what a sentence means.

Pack keys (all optional except `code`, `name`, `stopwords`): `casefold`
("turkish" or "default"), `stopwords`, `avoid_phrases`, `negated_description`,
`day_patterns`, `near_day_patterns`, `pc_speech_patterns`, `pc_say_patterns`,
`meta_words`, `meta_patterns`, `calques`, `common_words`, `age_patterns`,
`romance_terms`, `affection_terms`, `affection_guards`, `number_words`,
`gesture_families`, `echo_patterns`, `second_person_patterns`,
`secret_words`, `dotless_i_words`, `gone_terms`, `ended_terms`, `card`. Pack
regexes are written for folded text (see `fold`): lower case, German sharp s as
"ss", Turkish dotted and dotless i kept apart.

A few keys carry more than a list of strings. An `avoid_phrases` item with
`rolling_max` is capped over the last ten replies instead of per reply. A
`calques` item may add a `pattern` regex that also catches inflected forms.
`number_words` maps number words, cardinal or ordinal, to their values, so a
`near_day_patterns` match (group `day`) or an `age_patterns` match (group
`age`) can be read as a number. An `age_patterns` match that spans two ages
("from fifteen to twenty-two") puts the first in `age`. An `echo_patterns`
match whose group `quote` takes part is a quotative ("diye"): the words just
before it are speech. `romance_terms`, `affection_terms`,
`affection_guards`, `secret_words`, `gone_terms` (a table row saying someone
is dead, missing or left) and `ended_terms` (a relationship that is over) are
words or phrases; a word ending in `*` is a stem. An `affection_terms` word (a
kiss) counts as a romance term unless an `affection_guards` term (a relative,
a kiss on the forehead) shares its clause. `dotless_i_words` are the folded
stems of words that really start with a dotless ı ("ışık", "ıslak"). Each
`gesture_families` item is `{id, label, patterns, example}`.

A pack may have a Markdown companion, `<code>.md`, with longer model guidance
(`load_guidance`). Nothing here raises on a missing or broken pack: an unknown
language gets an empty pack and every check simply finds nothing. Pack files
are read as UTF-8 with or without a byte-order mark, and only files that the
pack directory actually lists are opened (so a code such as "con" can never
reach a Windows device name).
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import unicodedata
from bisect import bisect_left, bisect_right
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, NamedTuple


PACK_DIR = Path(__file__).resolve().parents[1] / "packs" / "languages"
MIN_DETECT_WORDS = 8
# A guess resting on a single function word is noise: Turkish "et" (meat; the
# verb in "devam et") is also French "et", Turkish "para" (money) is Spanish
# "para". The winning language needs at least this many stopword hits.
MIN_DETECT_HITS = 2
CARD_LIMIT = 600
LIST_KEYS = (
    "stopwords",
    "negated_description",
    "day_patterns",
    "near_day_patterns",
    "pc_speech_patterns",
    "pc_say_patterns",
    "meta_words",
    "meta_patterns",
    "common_words",
    "age_patterns",
    "romance_terms",
    "affection_terms",
    "affection_guards",
    "echo_patterns",
    "second_person_patterns",
    "secret_words",
    "dotless_i_words",
    "gone_terms",
    "ended_terms",
)
ID_RE = re.compile(r"^[a-z0-9_]{1,40}$")
CODE_RE = re.compile(r"^([A-Za-z]{2,3})(?:[-_][A-Za-z0-9]{1,8})*$")

# Sentence boundaries. Western terminators end a sentence only when whitespace
# or the end of the line follows them and their closing marks; the full-width
# and other-script terminators end a sentence on their own.
_TERMINATORS = ".!?…‼⁇⁈⁉"
_WIDE_TERMINATORS = "。！？؟।॥"
# Closing marks that stay with their sentence, including the German closing
# quotes („…“, ‚…‘, »…«), which look like English or French openers.
_CLOSERS = "\"'”’»›」』）)]“‘«‹"
_OPENERS = "\"'“‘„‚«‹»›「『（([—–-¿¡ "
# French sets a (narrow) no-break space before a closing guillemet: « Viens. »
# The terminator run and its closing marks are matched greedily with nothing
# required after them, so the engine never backtracks (a long "!!!!" run stays
# linear); `sentence_split` checks what follows the match.
_BOUNDARY_RE = re.compile(
    rf"([{re.escape(_TERMINATORS)}]+(?:[{re.escape(_CLOSERS)}]|[ \u00a0\u202f]+[»›])*)"
    rf"|([{re.escape(_WIDE_TERMINATORS)}]+[{re.escape(_CLOSERS)}]*)"
)
# Turkish writes the circumflex only to mark vowel length (hâlâ/hala,
# kâğıt/kağıt); usage varies by writer, so folding drops it.
_TURKISH_CIRCUMFLEX = str.maketrans({"â": "a", "Â": "a", "î": "i", "Î": "i", "û": "u", "Û": "u"})


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def normalize_code(code: str) -> str:
    """The BCP-47 primary subtag in lower case ("tr-TR" -> "tr"), or ""."""

    match = CODE_RE.match(str(code or "").strip())
    return match.group(1).lower() if match else ""


def _empty_pack(code: str) -> dict[str, Any]:
    return {"code": code, "stopwords": []}


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _count(value: Any) -> int | None:
    """A whole number of zero or more, else None."""

    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _cap(value: Any) -> int:
    """A per-reply cap: a whole number of zero or more, else the default 1."""

    count = _count(value)
    return 1 if count is None else count


def _strings(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []


def _clip(text: str, limit: int) -> str:
    """`text` cut to at most `limit` characters at a word boundary, marked with "…"."""

    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    space = cut.rfind(" ")
    return (cut[:space] if space > limit // 2 else cut).rstrip() + "…"


def _clean_pack(raw: Any, code: str) -> dict[str, Any]:
    """Keep only well-typed values so a hand-edited pack cannot break a hook."""

    if not isinstance(raw, dict) or not isinstance(raw.get("stopwords"), list):
        return _empty_pack(code)
    pack: dict[str, Any] = {
        "code": code,
        "name": _text(raw.get("name")).strip() or code,
        "casefold": "turkish" if raw.get("casefold") == "turkish" else "default",
    }
    for key in LIST_KEYS:
        pack[key] = _strings(raw.get(key, []))
    pack["avoid_phrases"] = [_avoid_item(item) for item in _dicts(raw.get("avoid_phrases"), "phrase")]
    pack["calques"] = [_calque_item(item) for item in _dicts(raw.get("calques"), "bad")]
    numbers = raw.get("number_words", {})
    pack["number_words"] = {
        word.strip(): value
        for word, value in (numbers.items() if isinstance(numbers, dict) else [])
        if isinstance(word, str) and word.strip() and _count(value) is not None
    }
    pack["gesture_families"] = [
        {
            "id": item["id"],
            "label": _text(item.get("label")).strip() or item["id"],
            "patterns": _strings(item.get("patterns")),
            "example": _text(item.get("example")).strip(),
        }
        for item in _dicts(raw.get("gesture_families"), "id")
        if ID_RE.match(item["id"]) and _strings(item.get("patterns"))
    ]
    pack["card"] = _clip(_text(raw.get("card")).strip(), CARD_LIMIT)
    return pack


def _dicts(value: Any, required: str) -> list[dict[str, Any]]:
    """The mappings in a list value whose `required` key holds a non-empty string."""

    items = value if isinstance(value, list) else []
    return [item for item in items if isinstance(item, dict) and isinstance(item.get(required), str) and item[required].strip()]


def _avoid_item(item: dict[str, Any]) -> dict[str, Any]:
    cleaned = {"phrase": item["phrase"], "max_per_reply": _cap(item.get("max_per_reply")), "note": _text(item.get("note"))}
    rolling = _count(item.get("rolling_max"))
    if rolling is not None:
        cleaned["rolling_max"] = rolling
    return cleaned


def _calque_item(item: dict[str, Any]) -> dict[str, Any]:
    cleaned = {"bad": item["bad"], "better": _text(item.get("better"))}
    if _text(item.get("pattern")).strip():
        cleaned["pattern"] = item["pattern"]
    return cleaned


# Caches are keyed by the pack directory as well as the code, so pointing
# PACK_DIR elsewhere (tests, a future campaign override) never serves stale data.
@lru_cache(maxsize=8)
def _listing(directory: str) -> dict[str, str]:
    """Lower-cased file name -> file name for the regular files in a pack directory.

    Only listed files are ever opened: a code can never become a device name
    ("con.json" on older Windows) or another path, and "TR.json" still serves
    "tr" on a case-sensitive file system. An exact lower-case name wins a clash.
    """

    try:
        names = sorted(entry.name for entry in Path(directory).iterdir() if entry.is_file())
    except OSError:
        return {}
    found: dict[str, str] = {}
    for name in names:
        key = name.lower()
        if key not in found or name == key:
            found[key] = name
    return found


def _pack_file(directory: str, file_name: str) -> Path | None:
    listed = _listing(directory).get(file_name)
    return Path(directory) / listed if listed else None


def _read_text(path: Path | None) -> str | None:
    """A UTF-8 file's text without a byte-order mark, or None when unreadable."""

    if path is None:
        return None
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


@lru_cache(maxsize=32)
def _read_pack(directory: str, code: str) -> dict[str, Any]:
    text = _read_text(_pack_file(directory, f"{code}.json")) if code else None
    if text is None:
        return _empty_pack(code)
    try:
        raw = json.loads(text)
    except (ValueError, RecursionError):
        return _empty_pack(code)
    return _clean_pack(raw, code)


def _cached_pack(code: str) -> dict[str, Any]:
    """The shared, cleaned pack for a normalized code. Never mutate it."""

    return _read_pack(str(PACK_DIR), code)


@lru_cache(maxsize=4)
def _codes_in(directory: str) -> tuple[str, ...]:
    stems = sorted(name[: -len(".json")] for name in _listing(directory) if name.endswith(".json"))
    return tuple(stem for stem in stems if normalize_code(stem) == stem and _read_pack(directory, stem).get("name"))


def load_pack(code: str) -> dict[str, Any]:
    """The pack for a language code; an unknown code gets an empty pack.

    The result is a private copy, so callers may extend it (for example with a
    campaign's own avoid phrases) without affecting other callers.
    """

    normalized = normalize_code(code)
    if not normalized:
        return _empty_pack(str(code))
    return copy.deepcopy(_cached_pack(normalized))


def available_codes() -> list[str]:
    """Codes of every shipped pack that loads, sorted."""

    return list(_codes_in(str(PACK_DIR)))


def load_guidance(code: str) -> str:
    """The pack's Markdown model guidance (`<code>.md`), or "" when absent."""

    normalized = normalize_code(code)
    text = _read_text(_pack_file(str(PACK_DIR), f"{normalized}.md")) if normalized else None
    return text or ""


# ---------------------------------------------------------------------------
# Folding and tokens
# ---------------------------------------------------------------------------


def _fold_mode(pack: dict[str, Any] | None) -> str:
    return "turkish" if isinstance(pack, dict) and pack.get("casefold") == "turkish" else "default"


@lru_cache(maxsize=64)
def _fold(text: str, mode: str) -> str:
    text = unicodedata.normalize("NFC", text)
    # A lower-case i followed by a combining dot is what a non-Turkish
    # lowercasing of "İ" leaves behind; it is a plain "i" in every language.
    text = text.replace("i\u0307", "i")
    if mode == "turkish":
        text = text.replace("I", "ı").replace("İ", "i").translate(_TURKISH_CIRCUMFLEX)
    else:
        text = text.replace("İ", "i")
    return text.casefold()


def fold(text: str, pack: dict[str, Any] | None) -> str:
    """Locale-aware casefold: Turkish maps I->ı and İ->i before folding."""

    return _fold(str(text or ""), _fold_mode(pack))


def _is_word_char(char: str) -> bool:
    if char.isalnum():
        return True
    # Combining marks belong to the word they sit on (Devanagari vowel signs,
    # Hebrew points, an undecomposed dot above).
    return char > "\x7f" and unicodedata.category(char).startswith("M")


@lru_cache(maxsize=64)
def _tokens(text: str) -> tuple[str, ...]:
    found: list[str] = []
    start = -1
    for index, char in enumerate(text):
        if _is_word_char(char):
            if start < 0:
                start = index
        elif start >= 0:
            found.append(text[start:index])
            start = -1
    if start >= 0:
        found.append(text[start:])
    return tuple(found)


def tokens(text: str) -> list[str]:
    """Maximal runs of letters, digits and combining marks, in any script.

    Apostrophes, hyphens and underscores separate tokens, so "Ali'nin" gives
    "Ali" and "nin", and "l'homme" gives "l" and "homme".
    """

    return list(_tokens(unicodedata.normalize("NFC", str(text or ""))))


def words(text: str, pack: dict[str, Any] | None) -> list[str]:
    """Folded tokens of `text`."""

    return list(_tokens(fold(text, pack)))


@lru_cache(maxsize=65536)
def _is_word(token: str) -> bool:
    return not any(char.isdigit() or char.isnumeric() for char in token)


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------


@lru_cache(maxsize=32)
def _stopwords_in(directory: str, code: str) -> frozenset[str]:
    pack = _read_pack(directory, code)
    return frozenset(fold(word, pack) for word in pack.get("stopwords", []))


def _stopword_set(code: str) -> frozenset[str]:
    return _stopwords_in(str(PACK_DIR), code)


def _candidate_codes(candidates: list[str] | str | None) -> list[str]:
    if candidates is None:
        items: list[Any] = available_codes()
    elif isinstance(candidates, str):
        items = [candidates]  # a single code, not its letters
    else:
        items = list(candidates)
    return list(dict.fromkeys(code for code in (normalize_code(item) for item in items) if code))


def _stopword_hits(text: str, candidates: list[str] | str | None, min_words: int) -> tuple[int, dict[str, int]]:
    """Word count and per-candidate stopword hits; no hits below `min_words`.

    Words are letter tokens (no digits). The word count is the same for every
    candidate because folding never changes token boundaries.
    """

    codes = _candidate_codes(candidates)
    if not codes:
        return 0, {}
    by_mode: dict[str, list[str]] = {}
    for code in codes:
        mode = _fold_mode(_cached_pack(code))
        if mode not in by_mode:
            by_mode[mode] = [token for token in _tokens(_fold(str(text or ""), mode)) if _is_word(token)]
    total = len(next(iter(by_mode.values())))
    if total < max(1, min_words):
        return total, {}
    hits: dict[str, int] = {}
    for code in codes:
        stopwords = _stopword_set(code)
        hits[code] = sum(1 for token in by_mode[_fold_mode(_cached_pack(code))] if token in stopwords)
    return total, hits


def stopword_ratios(
    text: str, candidates: list[str] | None = None, *, min_words: int = MIN_DETECT_WORDS
) -> dict[str, float]:
    """Share of words that are each candidate's stopwords; {} below `min_words`."""

    total, hits = _stopword_hits(text, candidates, min_words)
    return {code: count / total for code, count in hits.items()}


def detect_language(
    text: str,
    candidates: list[str] | None = None,
    *,
    min_words: int = MIN_DETECT_WORDS,
    min_hits: int = MIN_DETECT_HITS,
) -> tuple[str | None, float]:
    """Best-matching language code by stopword ratio, with a confidence.

    Confidence is the best ratio minus the second best, so words shared by two
    candidates (Turkish and Spanish "de", English and German "in") cancel out
    and only distinctive function words decide. Returns `(None, 0.0)` for
    fewer than `min_words` words, fewer than `min_hits` stopwords of the best
    language (one shared-looking word such as Turkish "et" or "para" is not
    evidence), or a tie.
    """

    total, hits = _stopword_hits(text, candidates, min_words)
    if not hits:
        return None, 0.0
    ranked = sorted(hits.items(), key=lambda item: (-item[1], item[0]))
    best_code, best = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0
    if best < max(1, min_hits) or best == second:
        return None, 0.0
    return best_code, round(best / total - second / total, 4)


# ---------------------------------------------------------------------------
# Sentences and phrases
# ---------------------------------------------------------------------------


def _continues_sentence(line: str, start: int) -> bool:
    """True when the text from `start` on begins in lower case.

    Covers ordinals ("92. gün"), trailing ellipses ("Ama… belki") and dialogue
    tags after a quote ("Stop!" she said / —¿Qué? —preguntó). Scans in place,
    so many boundaries on one long line stay linear.
    """

    for index in range(start, len(line)):
        char = line[index]
        if char.isspace() or char in _OPENERS:
            continue
        return char.islower()
    return False


def _ends_sentence(line: str, match: re.Match[str]) -> bool:
    if match.group(1) is None:
        return True  # full-width and other-script terminators end a sentence on their own
    end = match.end()
    if end < len(line) and not line[end].isspace():
        return False  # "3.5", "Stop!", or « Viens. », dit-il
    return not _continues_sentence(line, end)


def sentence_split(text: str) -> list[str]:
    """Split text into sentences on `.!?…` (and other scripts' terminators).

    Closing quotes stay with their sentence, line breaks always end one, and a
    terminator followed by a lower-case word, or by a comma after its closing
    quote, does not split.
    """

    sentences: list[str] = []
    for line in str(text or "").splitlines():
        start = 0
        for match in _BOUNDARY_RE.finditer(line):
            if not _ends_sentence(line, match):
                continue
            end = match.end()
            piece = line[start:end].strip()
            if piece:
                sentences.append(piece)
            start = end
        tail = line[start:].strip()
        if tail:
            sentences.append(tail)
    return sentences


def sentence_spans(text: str) -> list[tuple[int, int]]:
    """`(start, end)` offsets in `text` of the sentences `sentence_split` finds, in order."""

    text = str(text or "")
    spans: list[tuple[int, int]] = []
    cursor = 0
    for piece in sentence_split(text):
        start = text.find(piece, cursor)
        if start < 0:
            continue
        cursor = start + len(piece)
        spans.append((start, cursor))
    return spans


def count_phrase(text: str, phrase: str, pack: dict[str, Any] | None) -> int:
    """Non-overlapping, word-bounded, folded occurrences of `phrase` in `text`.

    "bir an" does not match "bir anahtar"; "İçini" matches "içini"; spacing and
    punctuation between the phrase's words do not matter.
    """

    needle = tuple(words(phrase, pack))
    if not needle:
        return 0
    haystack = _tokens(fold(text, pack))
    size = len(needle)
    count = 0
    index = 0
    limit = len(haystack) - size
    while index <= limit:
        if haystack[index] == needle[0] and haystack[index : index + size] == needle:
            count += 1
            index += size
        else:
            index += 1
    return count


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------


@lru_cache(maxsize=64)
def _compile(patterns: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
    compiled: list[re.Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern, re.IGNORECASE))
        except re.error:
            continue  # a broken pattern in a hand-edited pack is skipped, not fatal
    return tuple(compiled)


def compile_patterns(pack: dict[str, Any] | None, key: str) -> list[re.Pattern[str]]:
    """The pack's regex list under `key`, compiled; invalid patterns skipped."""

    values = pack.get(key, []) if isinstance(pack, dict) else []
    if not isinstance(values, list):
        return []
    return list(_compile(tuple(value for value in values if isinstance(value, str) and value)))


def find_patterns(text: str, pack: dict[str, Any] | None, key: str) -> list[str]:
    """Matches of the pack's `key` patterns in the folded text, in text order.

    When two patterns match overlapping spans ("quatre-vingt-douzième jour"
    and "douzième jour"), only the earlier, longer one is kept, so a count of
    the result counts each place once.
    """

    folded = fold(text, pack)
    spans: list[tuple[int, int, str]] = []
    for pattern in compile_patterns(pack, key):
        spans.extend((match.start(), match.end(), match.group(0)) for match in pattern.finditer(folded) if match.group(0))
    kept: list[str] = []
    reached = -1
    for start, end, value in sorted(spans, key=lambda span: (span[0], -span[1])):
        if start >= reached:
            kept.append(value)
            reached = end
    return kept


@lru_cache(maxsize=64)
def _terms_pattern(terms: tuple[str, ...], mode: str) -> re.Pattern[str] | None:
    pack = {"casefold": mode}
    bodies = []
    for term in terms:
        parts = []
        for raw in term.split():
            pieces = [re.escape(piece) for piece in words(raw.rstrip("*"), pack)]
            if pieces and raw.endswith("*"):
                pieces[-1] += r"[^\W_]*"
            if pieces:
                parts.append(r"[\W_]+".join(pieces))
        if parts:
            bodies.append(r"[\W_]+".join(parts))
    if not bodies:
        return None
    bodies.sort(key=len, reverse=True)
    return re.compile(rf"(?<![^\W_])(?:{'|'.join(bodies)})(?![^\W_])")


def terms_regex(pack: dict[str, Any] | None, key: str) -> re.Pattern[str] | None:
    """One regex, for folded text, for the pack's word and phrase terms under `key`; None when it has none.

    A word ending in `*` is a stem that takes any ending ("sevgilisi*"); the
    words of a phrase may be separated by any spacing or punctuation; every
    term is matched as whole words.
    """

    values = pack.get(key) if isinstance(pack, dict) else None
    terms = tuple(term for term in values if isinstance(term, str) and term.strip()) if isinstance(values, list) else ()
    return _terms_pattern(terms, _fold_mode(pack)) if terms else None


@lru_cache(maxsize=32)
def _number_table(items: tuple[tuple[str, int], ...], mode: str) -> dict[str, int]:
    pack = {"casefold": mode}
    return {fold(word, pack): value for word, value in items}


def read_number(text: str, pack: dict[str, Any] | None) -> int | None:
    """The number `text` writes in digits or in the pack's number words ("on beş", "twenty-two"), else None."""

    found = words(text, pack)
    if len(found) == 1 and found[0].isdecimal():
        return int(found[0])
    numbers = pack.get("number_words") if isinstance(pack, dict) else None
    items = (
        tuple(sorted((word, value) for word, value in numbers.items() if isinstance(word, str) and _count(value) is not None))
        if isinstance(numbers, dict)
        else ()
    )
    table = _number_table(items, _fold_mode(pack))
    total = current = 0
    for word in found:
        value = table.get(word)
        if value is None:
            return None
        if value >= 1000:
            total += max(current, 1) * value
            current = 0
        elif value >= 100:
            current = max(current, 1) * value
        else:
            current += value
    return total + current if found else None


# ---------------------------------------------------------------------------
# The age rule: an under-18 age next to a romance or sex term
# ---------------------------------------------------------------------------

MINOR_AGE = 18
# A term's window: its own sentence and the one before and after it, or this
# many characters on either side.
AGE_WINDOW_SENTENCES = 1
AGE_WINDOW_CHARS = 220
# Inside a sentence these close a phrase; a semicolon or a colon also closes a clause.
_PHRASE_BREAK_RE = re.compile(r"[,;:()\[\]{}—–]|\s-\s")
_CLAUSE_BREAK_RE = re.compile(r"[;:]")


class _Sentence(NamedTuple):
    start: int
    end: int
    phrases: tuple[int, ...]  # offsets of the phrase breaks inside it
    clauses: tuple[int, ...]  # offsets of the clause breaks inside it


class _Mention(NamedTuple):
    start: int
    end: int
    sentence: int
    clause: int
    phrase: int
    minor: bool  # an age under MINOR_AGE (always False for a term)


class _AgeRules(NamedTuple):
    pack: dict[str, Any]
    ages: tuple[re.Pattern[str], ...]
    romance: re.Pattern[str] | None
    affection: re.Pattern[str] | None
    guards: re.Pattern[str] | None
    needles: tuple[str, ...]  # one folded word of every term: a text holding none has no term


def _fold_map(text: str, mode: str) -> tuple[str, list[int] | None, list[int] | None]:
    """`text` folded, with each folded character's source start and end in `text` (None when one to one).

    Only "i" plus a combining dot shrinks when folded, and a fold never
    shrinks otherwise, so equal lengths without that dot mean one to one.
    """

    folded = _fold(text, mode)
    if len(folded) == len(text) and "\u0307" not in text:
        return folded, None, None
    pieces: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    index = 0
    while index < len(text):
        size = 2 if text.startswith("i\u0307", index) else 1
        piece = "i" if size == 2 else _fold(text[index], mode)
        pieces.append(piece)
        starts.extend([index] * len(piece))
        ends.extend([index + size] * len(piece))
        index += size
    return "".join(pieces), starts, ends


@lru_cache(maxsize=64)
def _needles(terms: tuple[str, ...], mode: str) -> tuple[str, ...]:
    """The longest folded word of each term: every match of the term contains it."""

    pack = {"casefold": mode}
    found = []
    for term in terms:
        pieces = [piece for raw in term.split() for piece in words(raw.rstrip("*"), pack)]
        if pieces:
            found.append(max(pieces, key=len))
    return tuple(dict.fromkeys(found))


def _age_rules(pack: dict[str, Any]) -> _AgeRules | None:
    ages = tuple(compile_patterns(pack, "age_patterns"))
    romance = terms_regex(pack, "romance_terms")
    affection = terms_regex(pack, "affection_terms")
    if not ages or (romance is None and affection is None):
        return None
    terms = tuple(
        term
        for key in ("romance_terms", "affection_terms")
        for term in (pack.get(key) if isinstance(pack.get(key), list) else [])
        if isinstance(term, str) and term.strip()
    )
    needles = _needles(terms, _fold_mode(pack))
    return _AgeRules(pack, ages, romance, affection, terms_regex(pack, "affection_guards"), needles)


def _stated_minor(match: re.Match[str], pack: dict[str, Any]) -> bool | None:
    """Whether an age-pattern match states an age under MINOR_AGE; None when its number cannot be read.

    A pattern without an `age` group names an under-18 age by itself ("underage").
    """

    if "age" not in match.re.groupindex or match.group("age") is None:
        return True
    value = read_number(match.group("age"), pack)
    return None if value is None else value < MINOR_AGE


def _disjoint(spans: list[tuple[int, int, bool]]) -> list[tuple[int, int, bool]]:
    """The earlier, longer span where spans overlap, as `find_patterns` keeps them."""

    kept: list[tuple[int, int, bool]] = []
    reached = -1
    for span in sorted(spans, key=lambda item: (item[0], -item[1])):
        if span[1] > span[0] and span[0] >= reached:
            kept.append(span)
            reached = span[1]
    return kept


def _near_terms(text: str, spans: list[tuple[int, int]], rules: _AgeRules, whole: str) -> list[int]:
    """Indices of the sentences that can hold a term or an age in a term's window, in order.

    Reads the terms off the whole folded text when its offsets are the
    text's; otherwise every sentence.
    """

    if len(whole) != len(text) or "\u0307" in text:
        return list(range(len(spans)))
    starts = [start for start, _ in spans]
    ends = [end for _, end in spans]
    wanted: set[int] = set()
    for regex in (rules.romance, rules.affection):
        for match in regex.finditer(whole) if regex is not None else ():
            index = max(0, bisect_right(starts, match.start()) - 1)
            wanted.update(range(max(0, index - AGE_WINDOW_SENTENCES), min(len(spans), index + AGE_WINDOW_SENTENCES + 1)))
            wanted.update(range(bisect_right(ends, match.start() - AGE_WINDOW_CHARS), bisect_left(starts, match.end() + AGE_WINDOW_CHARS)))
    return sorted(wanted)


def _mentions(text: str, spans: list[tuple[int, int]], rules: _AgeRules, whole: str) -> tuple[list[_Mention], list[_Mention]]:
    """The pack's age expressions and romance terms in `text`, sentence by sentence, near its terms only."""

    mode = _fold_mode(rules.pack)
    ages: list[_Mention] = []
    terms: list[_Mention] = []
    for index in _near_terms(text, spans, rules, whole):
        start, end = spans[index]
        piece = text[start:end]
        sentence = _Sentence(
            start,
            end,
            tuple(start + match.start() for match in _PHRASE_BREAK_RE.finditer(piece)),
            tuple(start + match.start() for match in _CLAUSE_BREAK_RE.finditer(piece)),
        )
        folded, starts, ends = _fold_map(piece, mode)

        def placed(low: int, high: int, minor: bool) -> _Mention:
            if starts is None or ends is None:
                start, end = sentence.start + low, sentence.start + high
            else:
                start, end = sentence.start + starts[low], sentence.start + ends[high - 1]
            clause = bisect_right(sentence.clauses, start)
            return _Mention(start, end, index, clause, bisect_right(sentence.phrases, start), minor)

        found = []
        for pattern in rules.ages:
            for match in pattern.finditer(folded):
                minor = _stated_minor(match, rules.pack) if match.end() > match.start() else None
                if minor is not None:
                    found.append((match.start(), match.end(), minor))
        ages.extend(placed(low, high, minor) for low, high, minor in _disjoint(found))

        loves = [(match.start(), match.end(), False) for match in rules.romance.finditer(folded)] if rules.romance else []
        kisses = [(match.start(), match.end(), False) for match in rules.affection.finditer(folded)] if rules.affection else []
        if kisses and rules.guards is not None:
            guarded = {placed(match.start(), match.end(), False).clause for match in rules.guards.finditer(folded)}
            kisses = [kiss for kiss in kisses if placed(*kiss).clause not in guarded]
        terms.extend(placed(low, high, False) for low, high, _ in _disjoint(loves + kisses))
    return ages, terms


def _gap(first: tuple[int, int] | _Mention, second: tuple[int, int] | _Mention) -> int:
    """Characters between two spans; 0 when they overlap."""

    return max(0, second[0] - first[1], first[0] - second[1])


def _closest_minors(ages: list[_Mention], terms: list[_Mention]) -> dict[tuple[int, int], tuple[int, int]]:
    """Each under-18 age that is the closest age of some term in its window, with its nearest such term.

    Closest means in the term's own phrase first, then in its own clause,
    then the fewest characters away; on a tie the under-18 age wins.
    """

    pairs: dict[tuple[int, int], tuple[int, int]] = {}
    for term in terms:
        near = [
            age
            for age in ages
            if abs(age.sentence - term.sentence) <= AGE_WINDOW_SENTENCES or _gap(age, term) <= AGE_WINDOW_CHARS
        ]
        if not near:
            continue
        closest = min(
            near,
            key=lambda age: (
                not (age.sentence == term.sentence and age.phrase == term.phrase),
                not (age.sentence == term.sentence and age.clause == term.clause),
                _gap(age, term),
                not age.minor,
            ),
        )
        if not closest.minor:
            continue
        span = (closest.start, closest.end)
        if span not in pairs or _gap(span, term) < _gap(span, pairs[span]):
            pairs[span] = (term.start, term.end)
    return pairs


def all_packs(first: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """`first` (when given), then every other shipped pack, for the rules that read every language.

    The shipped packs are the shared cached copies; callers must not change them.
    """

    packs = [first] if isinstance(first, dict) else []
    skip = normalize_code(str(first.get("code") or "")) if isinstance(first, dict) else ""
    packs.extend(_cached_pack(code) for code in available_codes() if code != skip)
    return packs


def minor_romance(text: str, packs: Iterable[dict[str, Any]]) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Ages under 18 placed next to a romance or sex term, as `[(age span, term span)]` in text order.

    Each pack is read on its own: its `age_patterns` (a match is an age, under
    18 or not, when its `age` group reads as a number), its `romance_terms`,
    and its `affection_terms` (a kiss) unless an `affection_guards` term (a
    relative, a forehead) shares the clause. Every term is resolved against the
    closest age in its window (the same or an adjacent sentence, or
    AGE_WINDOW_CHARS characters): one in its own phrase first, then in its
    own clause, then the nearest. Only a term whose closest age is under 18
    counts, so "on dokuz yaşında sevgilisi oldu" after a childhood age, or
    "his lover only at nineteen", is not reported. A span ("on beşinden yirmi
    iki yaşına", "from fifteen to twenty-two") is one expression that starts
    at its first age. Spans index the NFC form of `text`; each age is listed
    once, with its nearest term.
    """

    text = unicodedata.normalize("NFC", str(text or ""))
    pairs: dict[tuple[int, int], tuple[int, int]] = {}
    spans: list[tuple[int, int]] | None = None
    for pack in packs:
        rules = _age_rules(pack) if isinstance(pack, dict) else None
        if rules is None:
            continue
        whole = fold(text, rules.pack)
        if not any(needle in whole for needle in rules.needles):  # a quick substring test first
            continue
        if not any(regex is not None and regex.search(whole) for regex in (rules.romance, rules.affection)):
            continue
        if spans is None:
            spans = sentence_spans(text)
        ages, terms = _mentions(text, spans, rules, whole)
        for age, term in _closest_minors(ages, terms).items():
            if not any(age[0] < kept[1] and kept[0] < age[1] for kept in pairs):
                pairs[age] = term
    return sorted(pairs.items())


def states_minor_age(text: str, packs: Iterable[dict[str, Any]]) -> bool:
    """Whether `text` states an age under 18 by any pack's `age_patterns` ("on beş yaşında", "at fifteen").

    The capsule uses it to mark a cast member whose note holds years under 18.
    """

    text = unicodedata.normalize("NFC", str(text or ""))
    for pack in packs:
        if not isinstance(pack, dict):
            continue
        patterns = compile_patterns(pack, "age_patterns")
        if not patterns:
            continue
        folded = fold(text, pack)
        for pattern in patterns:
            for match in pattern.finditer(folded):
                if match.end() > match.start() and _stated_minor(match, pack):
                    return True
    return False


def says_any(text: str, key: str, packs: Iterable[dict[str, Any]] | None = None) -> bool:
    """True when `text` holds one of the `key` terms of any pack (every shipped pack by default)."""

    for pack in all_packs() if packs is None else packs:
        regex = terms_regex(pack, key) if isinstance(pack, dict) else None
        if regex is not None and regex.search(fold(text, pack)):
            return True
    return False


# ---------------------------------------------------------------------------
# Records language
# ---------------------------------------------------------------------------


def records_language_setting(profile_text: str) -> str:
    """What `play_profile.yaml` sets for record content: a language code, "auto", or "" when unset.

    `narration.records_language` when it names a language, else the play
    language (`narration.language`), which `same` or a missing field means.
    """

    from repog_runtime import block_scalars  # local: this module needs no campaign helpers otherwise

    narration = block_scalars(str(profile_text or ""), "narration")
    value = narration.get("records_language", "").strip()
    if value.casefold() in {"", "same"}:
        value = narration.get("language", "").strip()
    if value.casefold() == "auto":
        return "auto"
    return normalize_code(value) if value else ""


def campaign_records_language(campaign: Path | str) -> str:
    """The code a campaign's records are written in, or "" when it cannot be known.

    The profile's setting (`records_language_setting`); when that is `auto`
    or unset, the language the presentation lint last saw in the replies
    (`.repog-runtime/lint_last.json`), as the writer resolves it.
    """

    from repog_runtime import RUNTIME_DIR, read_json, read_text

    root = Path(campaign)
    code = records_language_setting(read_text(root / "play_profile.yaml"))
    if code in {"", "auto"}:
        last = read_json(root / RUNTIME_DIR / "lint_last.json", {})
        code = normalize_code(last.get("language") or "") if isinstance(last, dict) and isinstance(last.get("language"), str) else ""
    return code


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("codes", help="list the shipped language packs")
    detect = commands.add_parser("detect", help="detect the language of text read from stdin")
    detect.add_argument("--candidates", nargs="*", default=None)
    args = parser.parse_args(argv)
    if args.command == "codes":
        result: dict[str, Any] = {"codes": available_codes()}
    else:
        text = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        code, confidence = detect_language(text, args.candidates)
        result = {"language": code, "confidence": confidence}
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

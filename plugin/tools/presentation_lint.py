"""Presentation lint: deterministic, warning-only checks on the reply the Player just saw.

After each reply in a ready RPG campaign the Stop hook runs this lint over
everything the turn showed the Player: every assistant text block and the
visible tool-call descriptions. It looks for presentation failures that long
sessions showed in every language: lines in another language, backend
vocabulary, tracker numbers in prose, overused phrases, phrases repeated across
replies, an opening that echoes the Player's own words, narration that writes
the player character's words or acts, protected names, negated descriptions,
glossary variants, and calques. What a language looks like comes from its pack
(`lang_pack`) and from campaign files, never from this code.

The visibility rules (another language, backend vocabulary, protected names)
read everything the Player saw. The narration rules read only the prose:
out-of-character blocks and Markdown structure (headings, list items, tables,
block quotes) are left out, so an OOC time-skip plan that counts days is not a
tracker leak and a stat list is not a repeated phrase. The rules on the
narrator's own words (the player character's words, negated descriptions) also
skip speech: quoted, or a dialogue line opened with a dash as Turkish, Spanish
and French write it ("— On adam dedin, der.").

The lint never judges meaning, never blocks, and never writes campaign truth.
Findings go to `campaign/.repog-runtime/lint_last.json`, whose short English
summary reaches the GM in the next scene capsule; a compact per-reply record
(rule counts and n-gram fingerprints, newest 400) goes to `lint_history.jsonl`
for the repetition rule and the distill review.

CLI:
    python tools/presentation_lint.py hook                     (Stop hook event JSON on stdin; prints nothing)
    python tools/presentation_lint.py report <campaign> [--last N]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import lang_pack
from lang_pack import (
    available_codes,
    compile_patterns,
    count_phrase,
    detect_language,
    fold,
    load_pack,
    normalize_code,
    sentence_split,
    tokens,
    words,
)
from repog_runtime import (
    RUNTIME_DIR,
    append_jsonl,
    find_campaign,
    is_ready_rpg,
    last_turn,
    read_json,
    read_jsonl,
    read_text,
    runtime_dir,
    runtime_settings,
    state_summary,
    write_json_atomic,
)


LINT_LAST = "lint_last.json"
LINT_HISTORY = "lint_history.jsonl"
HISTORY_KEEP = 400
RECORD_SCHEMA = 1

RULES = (
    "out_of_language",
    "meta_leak",
    "tracker_leak",
    "avoid_phrase",
    "repetition",
    "restatement",
    "pc_authoring",
    "secret_leak",
    "negated_description",
    "glossary_variant",
    "calque",
)
# The summary leads with what harms play most; findings keep rule order.
SUMMARY_ORDER = (
    "secret_leak",
    "out_of_language",
    "meta_leak",
    "tracker_leak",
    "avoid_phrase",
    "restatement",
    "pc_authoring",
    "calque",
    "glossary_variant",
    "negated_description",
    "repetition",
)

EVIDENCE_MAX = 3
SNIPPET_CHARS = 80
SUMMARY_MAX = 400
SUMMARY_QUOTE = 40
# Live replies run to about 11,000 characters; anything past this is linted no
# further, which keeps a pathological reply inside the hook's time budget.
REPLY_MAX_CHARS = 60_000
DETECT_CHARS = 5_000

LANGUAGE_CONFIDENCE = 0.15
# The other language must also hold this share of a line's words. A line
# written in a pack language sits well above it; a play-language line with two
# words that happen to be another language's function words (Turkish "el" and
# "para" are Spanish ones) stays below.
FOREIGN_MIN_SHARE = 0.25
SENTENCE_MIN_WORDS = 6
SENTENCE_MIN_HITS = 2
# Tool descriptions are short by nature ("Saving the scene"); one function word
# of the other language decides there.
DESCRIPTION_MIN_WORDS = 3
DESCRIPTION_MIN_HITS = 1
# Whole lines are read too: status lines and list items break into short
# sentences ("Status: day 814, night.") or bury their function words among
# names ("Marcus, Nella, Dunstan and nine men"). A line of LINE_MIN_WORDS words
# with no sign of the play language is in another language when LINE_MIN_HITS
# distinct function words of it appear...
LINE_MIN_WORDS = 5
LINE_MIN_HITS = 2
# ...or one, when the play language writes letters the other never does
# (Turkish ı, ş, ğ against English) and this many ordinary words show none.
LINE_LETTER_WORDS = 8
DETECT_PROMPTS = 5
PROMPT_SAMPLE_CHARS = 300

# Bare digits are reported only when they equal a day or revision of three
# digits or more: "12 men" on day 12 is a coincidence, "412" on revision 412
# hardly ever is. Pack day patterns ("92. gün", "day 92") catch any day.
TRACKER_MIN_VALUE = 100

NGRAM_SIZES = (3, 4, 5)
NGRAM_MIN_CONTENT = 2
CONTENT_MIN_LENGTH = 3
FINGERPRINT_MAX = 300
REPEAT_WINDOW = 8
REPEAT_MIN_REPLIES = 3

# The opening is the first 40 words of the prose, or its whole first sentence
# when that is longer (at most 80 words).
RESTATE_OPENING_WORDS = 40
RESTATE_OPENING_MAX = 80
# An echo is a run of this many consecutive words of the prompt...
RESTATE_RUN = 4
RESTATE_RUN_CONTENT = 2
# ...or a quoted line made of the Player's quoted words.
RESTATE_QUOTE_WORDS = 3
RESTATE_QUOTE_SHARE = 0.8
RESTATE_QUOTE_MAX_WORDS = 200
# A pasted document is not restated; only its start is compared.
RESTATE_PROMPT_CHARS = 20_000
# Words match when equal or when both share their first four letters, so an
# inflected echo still matches (soruyorum/soruyorsun, kendime/kendine,
# frage/fragst, look/looking).
RESTATE_STEM = 4

NEGATED_MIN = 2

# Backend words reported in every play language, besides the pack's own list.
BACKEND_WORDS = ("revision", "commit", "payload", "schema", "helper", "operation id")
# Backend words that are ordinary vocabulary in a play language. English play
# relies on its pack's unambiguous collocations instead of these single words.
NATIVE_BACKEND_WORDS = {"de": frozenset({"revision", "schema"})}
# A campaign avoid entry that is one token this long is a stem: Turkish and
# similar languages attach endings, so "kenetlen" must match "kenetlenmiş".
MIN_STEM_LETTERS = 4
# Same convention as check_player_facing: these statuses mean the PC knows it.
SAFE_STATUSES = ("revealed", "pc-known", "player-known", "confirmed")
PLACEHOLDER_HEADINGS = frozenset({"protected name", "name", "example"})
EMPTY_CELLS = frozenset({"", "-", "—", "–", "none", "n/a", "na"})

# Structural backend traces, matched on the raw reply.
_PATH_RE = re.compile(r"(?<![\w/.-])(?:[\w.-]+/)*[\w-]+\.(?:md|ya?ml|jsonl?|py)(?![\w-])")
_DIR_RE = re.compile(r"(?<![\w/.-])(?:campaign|tools|\.repog-runtime)/")
_CODE_RE = re.compile(r"`{3}[^\n]*|`[^`\n]+`")
_SNAKE_RE = re.compile(r"(?<!\w)[^\W\d_][^\W_]*(?:_[^\W_]+){2,}(?!\w)")
_STRUCTURAL = (_PATH_RE, _DIR_RE, _CODE_RE, _SNAKE_RE)

# Quoted speech within one line: "…", “…”, „…“, «…», 「…」, 『…』 (opener -> closers).
# An opener without a closer later on its line quotes nothing.
_QUOTE_CLOSERS = {'"': '"', "“": "”", "„": "“”", "«": "»", "「": "」", "『": "』"}
_HABIT_QUOTE_RE = re.compile(r'"([^"\n]+)"|“([^”\n]+)”|„([^“”\n]+)[“”]|«([^»\n]+)»')
# Dash dialogue (Turkish, Spanish, French): a line that opens with an em or en
# dash, after indentation, a list marker or emphasis, is speech.
_DASHES = "—–"
_DASH_LINE_RE = re.compile(r"^\s*(?:(?:[-*+]|\d{1,9}[.)])\s+)?[*_]{0,3}\s*(?P<dash>[—–]+)")
# A short letter run after an apostrophe is a clitic or case ending (Halvar'ın,
# it's, l'un), not a word of its own; dropped before language detection so
# "ın"/"in"/"a" do not read as another language's function words, and before
# word matching so "Halvar'a" and "Halvar" are the same word.
_CLITIC_RE = re.compile(r"(?<=[^\W\d_])['’][^\W\d_]{1,3}(?![^\W_])")
_OOC_RE = re.compile(r"^\W*ooc\b", re.IGNORECASE)
# A line opening an out-of-character note: "(OOC) …", "(OOC: …)", "[OOC] …",
# "**OOC:** …", "*(OOC: …)*", "OOC — …".
_OOC_MARK_RE = re.compile(r"^[\s>*_~]*(?P<bracket>[(\[])?\s*ooc\b", re.IGNORECASE)
_RULE_LINE_RE = re.compile(r"^ {0,3}(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})$")
# Markdown structure that is not narration: headings, list items, block quotes, table rows.
_STRUCTURE_RE = re.compile(r"^ {0,3}(?:#{1,6}(?:[ \t]|$)|[-*+][ \t]|>|\|)")
_LINE_ENDS = "\r\n\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029"
# A capital right after one of these opens a sentence or a quote; it says nothing about names.
_OPENING_MARKS = ".!?…:;\n\"“”„«»「『—–"
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_PROTECTED_SECTION_RE = re.compile(r"(?ms)^## Protected Proper Nouns\s*$\n(?P<body>.*?)(?=^##\s|\Z)")
_TABLE_SEPARATOR_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$")


@dataclass(frozen=True)
class _Reply:
    text: str  # everything the Player saw, NFC
    prose: str  # `text` without OOC blocks and Markdown structure; same offsets
    prose_sentences: tuple[str, ...]
    narration: str  # `prose` without speech (quoted or dash dialogue); same offsets


@dataclass(frozen=True)
class _Hit:
    count: int
    evidence: list[str]
    note: str  # one English clause for the summary


# ---------------------------------------------------------------------------
# Small text helpers
# ---------------------------------------------------------------------------


def _clip(text: str, limit: int = SNIPPET_CHARS) -> str:
    flat = " ".join(str(text).split())
    return flat if len(flat) <= limit else flat[: limit - 1].rstrip() + "…"


def _window(text: str, start: int, end: int, limit: int = SNIPPET_CHARS) -> str:
    """About `limit` characters of `text` around `[start, end)`, on one line."""

    inner = limit - 2  # room for the two ellipses
    if end - start >= inner:
        return _clip(text[start:end], limit)
    room = inner - (end - start)
    left = max(0, start - room // 2)
    right = min(len(text), max(end, left + inner))
    left = max(0, min(left, right - inner))
    piece = " ".join(text[left:right].split())
    return _clip(("…" if left > 0 else "") + piece + ("…" if right < len(text) else ""), limit)


def _located(original: str, folded: str, start: int, end: int) -> str:
    """Evidence for a span of the folded text, in the original spelling when it maps."""

    return _window(original if len(original) == len(folded) else folded, start, end)


def _span_text(original: str, folded: str, span: tuple[int, int]) -> str:
    return (original if len(original) == len(folded) else folded)[span[0] : span[1]]


def _has_digit(token: str) -> bool:
    return any(char.isdigit() or char.isnumeric() for char in token)


def _items(value: Any) -> list[Any]:
    """A list value as given; anything else (a lone string, a mapping, None) as no items."""

    return value if isinstance(value, list) else []


def _disjoint(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Keep the earlier, longer span where spans overlap (as `find_patterns` does)."""

    kept: list[tuple[int, int]] = []
    reached = -1
    for start, end in sorted(set(spans), key=lambda span: (span[0], -span[1])):
        if end > start and start >= reached:
            kept.append((start, end))
            reached = end
    return kept


def _blank(text: str, spans: list[tuple[int, int]]) -> str:
    pieces: list[str] = []
    cursor = 0
    for start, end in spans:
        pieces.append(text[cursor:start])
        pieces.append(" " * (end - start))
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)


def _blank_matches(pattern: re.Pattern[str], text: str) -> str:
    """`text` with every match of `pattern` replaced by spaces, keeping offsets."""

    return pattern.sub(lambda match: " " * len(match.group(0)), text)


def _quote_spans(text: str) -> list[tuple[int, int]]:
    """Spans of quoted speech, each within one line, in text order.

    Scans left to right: an opener starts a quote that ends at the first of
    its closers later on the same line; an opener with no closer there quotes
    nothing. Linear in the text (a regex would rescan the line for every
    unclosed opener).
    """

    spans: list[tuple[int, int]] = []
    offset = 0
    for line in text.split("\n"):
        size = len(line)
        following: dict[str, int] = {}  # closer -> its first position after the cursor, or `size` for none
        index = 0
        while index < size:
            closers = _QUOTE_CLOSERS.get(line[index])
            if closers is None:
                index += 1
                continue
            end = size
            for closer in closers:
                position = following.get(closer, -1)
                if position <= index:
                    found = line.find(closer, index + 1)
                    position = following[closer] = found if found >= 0 else size
                end = min(end, position)
            if end >= size:
                index += 1  # no closer later on this line: the opener quotes nothing
                continue
            spans.append((offset + index, offset + end + 1))
            index = end + 1
        offset += size + 1
    return spans


def _quotes_blanked(text: str) -> str:
    """`text` with quoted speech replaced by spaces, keeping offsets."""

    return _blank(text, _quote_spans(text))


def _dash_spans(text: str) -> list[tuple[int, int]]:
    """Spans of dash dialogue, each within one line, in text order.

    A line that opens with an em or en dash is speech. A later dash attached to
    a lower-case word opens the narrator's tag, as Spanish writes it ("—¿Qué?
    —preguntó"), and the next dash after the tag resumes the speech ("—dijo
    él—. Quizá"). Any other dash stays inside the speech: a spaced one is a
    pause as often as a tag, one between letters or digits ("10–12") belongs
    to a word, and Turkish and French tags follow a comma without a dash
    ("— On adam dedin, der."), so there the whole line is speech.
    """

    spans: list[tuple[int, int]] = []
    offset = 0
    for piece in text.splitlines(keepends=True):
        line = piece.rstrip(_LINE_ENDS)
        opened = _DASH_LINE_RE.match(line)
        if opened is not None:
            start = opened.start("dash")
            speaking = True
            index = opened.end()
            size = len(line)
            while index < size:
                if line[index] not in _DASHES:
                    index += 1
                    continue
                end = index
                while end < size and line[end] in _DASHES:
                    end += 1
                after = line[end] if end < size else ""
                if not (line[index - 1].isalnum() and after.isalnum()):
                    if speaking and after.islower():
                        spans.append((offset + start, offset + index))
                        speaking = False
                    elif not speaking:
                        start = index
                        speaking = True
                index = end
            if speaking:
                spans.append((offset + start, offset + size))
        offset += len(piece)
    return spans


def _merged(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """The union of `spans` as sorted spans that do not overlap."""

    merged: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _speech_spans(text: str) -> list[tuple[int, int]]:
    """Spans of speech, quoted or dash dialogue, in text order."""

    return _merged(_quote_spans(text) + _dash_spans(text))


def _pattern_spans(folded: str, pack: dict[str, Any], key: str) -> list[tuple[int, int]]:
    """Spans of the pack's `key` regexes in already folded text.

    Pack regexes are written for folded text; this is `find_patterns` with
    positions, so evidence can show where each match sits.
    """

    spans = [match.span() for pattern in compile_patterns(pack, key) for match in pattern.finditer(folded)]
    return _disjoint(spans)


@lru_cache(maxsize=256)
def _phrase_regex(tokens: tuple[str, ...]) -> re.Pattern[str]:
    body = r"[\W_]+".join(re.escape(token) for token in tokens)
    return re.compile(rf"(?<![^\W_]){body}(?![^\W_])")


def _phrase_evidence(text: str, phrase: str, pack: dict[str, Any] | None, shown: str | None = None) -> str:
    """A snippet around the first occurrence of `phrase` (folded, word-bounded) in `text`.

    `shown` is the text to quote from when `text` is a blanked copy of it
    with the same offsets.
    """

    tokens = tuple(words(phrase, pack))
    folded = fold(text, pack)
    match = _phrase_regex(tokens).search(folded) if tokens else None
    if match is None:
        return _clip(phrase)
    original = shown if shown is not None and len(shown) == len(text) else text
    return _located(original, folded, *match.span())


def _quote(text: str, limit: int = SUMMARY_QUOTE) -> str:
    return '"' + _clip(text, limit) + '"'


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}{'' if count == 1 else 's'}"


def _language_name(code: str) -> str:
    return str(load_pack(code).get("name") or code)


def _ignored_words(pack: dict[str, Any], context: dict[str, Any]) -> frozenset[str]:
    """Folded stopwords plus the player character's name: never content words."""

    ignored = {fold(word, pack) for word in _items(pack.get("stopwords")) if isinstance(word, str)}
    ignored.update(words(str(context.get("player_name") or ""), pack))
    return frozenset(ignored)


def _is_content(token: str, ignored: frozenset[str]) -> bool:
    return len(token) >= CONTENT_MIN_LENGTH and token not in ignored and not _has_digit(token)


def _word_spans(text: str, limit: int | None = None) -> list[tuple[int, int]]:
    """Offsets of the words `lang_pack.tokens` finds in (NFC) `text`, at most `limit`."""

    spans: list[tuple[int, int]] = []
    start = -1
    for index, char in enumerate(text):
        if char.isalnum() or (char > "\x7f" and unicodedata.category(char).startswith("M")):
            if start < 0:
                start = index
            continue
        if start >= 0:
            spans.append((start, index))
            start = -1
            if limit is not None and len(spans) >= limit:
                return spans
    if start >= 0:
        spans.append((start, len(text)))
    return spans


def _without_clitics(text: str) -> str:
    """`text` with apostrophe case endings blanked in place ("Halvar'a" -> "Halvar  ")."""

    return _blank_matches(_CLITIC_RE, text)


def _prose(text: str) -> str:
    """`text` without out-of-character blocks and Markdown structure, same length.

    Hidden lines become spaces (line breaks stay), so a span found in the prose
    is the same span in the reply. An OOC block starts at a line opened with an
    OOC marker. A marker that opens a bracket around its note ("(OOC: …)")
    ends where that bracket closes; any other marker ("(OOC) …", "**OOC:** …")
    covers what follows up to the next horizontal rule or the end, the way a GM
    sets an OOC note apart with `---`. Headings, list items, block quotes,
    table rows and rules are hidden wherever they stand.
    """

    pieces: list[str] = []
    mode = ""  # "" prose, "rule" until a horizontal rule, "bracket" until it closes
    depth = 0
    pair = "()"
    for line in text.splitlines(keepends=True):
        body = line.rstrip(_LINE_ENDS)
        hidden = True
        marker = _OOC_MARK_RE.match(body) if not mode else None
        if _RULE_LINE_RE.match(body):
            mode = ""
        elif mode == "bracket":
            depth += body.count(pair[0]) - body.count(pair[1])
            mode = "bracket" if depth > 0 else ""
        elif mode == "rule":
            pass
        elif marker is not None:
            opener = marker.group("bracket")
            pair = "()" if opener in (None, "(") else "[]"
            if opener and not body[marker.end() :].lstrip().startswith(pair[1]):
                note = body[marker.start("bracket") :]
                depth = note.count(pair[0]) - note.count(pair[1])
                mode = "bracket" if depth > 0 else ""
            else:
                mode = "rule"
        else:
            hidden = bool(_STRUCTURE_RE.match(body))
        pieces.append(" " * len(body) + line[len(body) :] if hidden else line)
    return "".join(pieces)


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


@lru_cache(maxsize=4)
def _stopword_table(directory: str) -> tuple[tuple[str, str, frozenset[str]], ...]:
    """`(code, fold mode, folded stopwords)` for every shipped pack in `directory`."""

    table = []
    for code in available_codes():
        pack = load_pack(code)
        mode = "turkish" if pack.get("casefold") == "turkish" else "default"
        table.append((code, mode, frozenset(fold(word, pack) for word in pack.get("stopwords", []))))
    return tuple(table)


def _word_count(text: str) -> int:
    return sum(1 for token in tokens(text) if not _has_digit(token))


def _foreign(text: str, language: str, *, min_words: int, min_hits: int) -> str | None:
    """The other pack language `text` is written in, or None.

    Stopword evidence as in `lang_pack.detect_language`, made strict for text
    that mixes a few foreign-looking words into the play language: a
    capitalized word after the first is a name or title ("Ser Aldric"), a word
    that is also a function word of the play language is no evidence against
    it (Turkish "her an"), a quoted phrase shorter than a line is skipped, and
    the other language must hold FOREIGN_MIN_SHARE of the words with
    `min_hits` distinct function words.
    """

    table = _stopword_table(str(lang_pack.PACK_DIR))
    own = next((row for row in table if row[0] == language), None)
    if own is None or not own[2]:
        return None  # no pack for the play language: nothing to compare against
    short = [span for span in _quote_spans(text) if _word_count(text[span[0] : span[1]]) < min_words]
    raw = [token for token in tokens(_CLITIC_RE.sub("", _blank(text, short))) if not _has_digit(token)]
    total = len(raw)
    if total < min_words:
        return None
    by_mode = {mode: [fold(token, {"casefold": mode}) for token in raw] for mode in {row[1] for row in table}}
    own_words = by_mode[own[1]]
    own_hits = sum(1 for word in own_words if word in own[2])
    ranked: list[tuple[int, int, str]] = []
    for code, mode, stopwords in table:
        if code == language:
            continue
        hits = [
            word
            for index, word in enumerate(by_mode[mode])
            if word in stopwords and own_words[index] not in own[2] and not (index and raw[index][:1].isupper())
        ]
        ranked.append((len(hits), len(set(hits)), code))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], item[2]))
    best, distinct, code = ranked[0]
    rival = max([own_hits] + [hits for hits, _, _ in ranked[1:2]])
    if distinct < min_hits or best <= own_hits or best / total < FOREIGN_MIN_SHARE:
        return None
    return code if (best - rival) / total >= LANGUAGE_CONFIDENCE else None


@lru_cache(maxsize=4)
def _pack_letters(directory: str) -> dict[str, frozenset[str]]:
    """Letters beyond basic Latin in each shipped pack's folded stopwords.

    A stopword list is a small sample of its language (the English one has no
    "z", the French one no "g"), so only letters a language either writes or
    never writes, those outside basic Latin, tell two languages apart.
    """

    return {
        code: frozenset(char for word in stopwords for char in word if char > "\x7f" and char.isalpha())
        for code, _, stopwords in _stopword_table(directory)
    }


def _line_words(sentences: list[str], min_words: int) -> list[tuple[str, bool]]:
    """`(word, is_name)` for the sentences of one line, each read as `_foreign` reads one.

    Digits, apostrophe case endings and quoted phrases shorter than
    `min_words` are dropped; a capitalized word that does not open its
    sentence is a name or title.
    """

    found: list[tuple[str, bool]] = []
    for sentence in sentences:
        short = [span for span in _quote_spans(sentence) if _word_count(sentence[span[0] : span[1]]) < min_words]
        raw = [token for token in tokens(_CLITIC_RE.sub("", _blank(sentence, short))) if not _has_digit(token)]
        found.extend((token, index > 0 and token[:1].isupper()) for index, token in enumerate(raw))
    return found


def _foreign_line(sentences: list[str], language: str) -> str | None:
    """The other pack language a whole line is written in, or None.

    Catches the status lines and list items `_foreign` misses sentence by
    sentence. The line needs LINE_MIN_WORDS words, not all capitalized, and no
    sign of the play language in its ordinary (non-name) words: none of its
    function words and none of the letters it writes and the other language
    never does. A function word of both languages is evidence for neither
    (Turkish and English "on"). The other language then needs LINE_MIN_HITS
    distinct function words, or one when the play language has such letters
    and LINE_LETTER_WORDS ordinary words show none of them, and it must lead
    every other language.
    """

    table = _stopword_table(str(lang_pack.PACK_DIR))
    own = next((row for row in table if row[0] == language), None)
    if own is None or not own[2]:
        return None
    found = _line_words(sentences, LINE_MIN_WORDS)
    if len(found) < LINE_MIN_WORDS or all(word[:1].isupper() for word, _ in found):
        return None  # too short, or only names and numbers
    plain = [word for word, name in found if not name]
    by_mode = {mode: [fold(word, {"casefold": mode}) for word in plain] for mode in {row[1] for row in table}}
    own_words = by_mode[own[1]]
    # Letters as written: the Turkish fold would turn the "I" of an English word into "ı".
    shapes = [fold(word, None) for word in plain]
    letters = _pack_letters(str(lang_pack.PACK_DIR))
    ranked: list[tuple[int, str, bool]] = []
    for code, mode, stopwords in table:
        if code == language:
            continue
        theirs = by_mode[mode]
        hits = {word for word, mine in zip(theirs, own_words) if word in stopwords and mine not in own[2]}
        own_hits = sum(1 for word, mine in zip(theirs, own_words) if mine in own[2] and word not in stopwords)
        marks = letters.get(language, frozenset()) - letters.get(code, frozenset())
        marked = any(not marks.isdisjoint(shape) for shape in shapes)
        needed = 1 if marks and len(plain) >= LINE_LETTER_WORDS else LINE_MIN_HITS
        ranked.append((len(hits), code, not own_hits and not marked and len(hits) >= needed))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], item[1]))
    hits, code, qualifies = ranked[0]
    runner_up = ranked[1][0] if len(ranked) > 1 else 0
    return code if qualifies and hits > runner_up else None


def _language_note(items: list[tuple[str, str]], noun: str) -> str:
    codes = Counter(code for code, _ in items)
    label = _language_name(next(iter(codes))) if len(codes) == 1 else "other-language"
    return f"{_plural(len(items), f'{label} {noun}')}: {_quote(items[0][1])}"


def _out_of_language(reply: _Reply, descriptions: list[str], language: str) -> _Hit | None:
    if not language:
        return None
    lines: list[tuple[str, str]] = []
    for line in reply.text.splitlines():
        sentences = sentence_split(line)
        found = [
            (code, sentence)
            for sentence in sentences
            if (code := _foreign(sentence, language, min_words=SENTENCE_MIN_WORDS, min_hits=SENTENCE_MIN_HITS))
        ]
        if not found and (code := _foreign_line(sentences, language)):
            found = [(code, line.strip())]
        lines.extend(found)
    tools = [
        (code, description)
        for description in descriptions
        if (code := _foreign(description, language, min_words=DESCRIPTION_MIN_WORDS, min_hits=DESCRIPTION_MIN_HITS))
    ]
    if not lines and not tools:
        return None
    tool_evidence = [_clip(f"[tool] {description}") for _, description in tools]
    line_evidence = [_clip(sentence) for _, sentence in lines]
    evidence = line_evidence[: EVIDENCE_MAX - min(1, len(tool_evidence))] + tool_evidence
    notes = []
    if lines:
        notes.append(_language_note(lines, "line"))
    if tools:
        notes.append(_language_note(tools, "tool description"))
    return _Hit(len(lines) + len(tools), evidence, "; ".join(notes))


def _meta_terms(pack: dict[str, Any]) -> list[tuple[str, dict[str, Any] | None]]:
    """Pack meta words (folded the pack's way) plus the English backend words."""

    terms: dict[str, tuple[str, dict[str, Any] | None]] = {}
    for word in _items(pack.get("meta_words")):
        if isinstance(word, str) and word.strip():
            terms.setdefault(" ".join(words(word, pack)), (word.strip(), pack))
    code = str(pack.get("code", ""))
    if code != "en":
        native = NATIVE_BACKEND_WORDS.get(code, frozenset())
        ordinary = {" ".join(words(word, pack)) for word in _items(pack.get("stopwords")) if isinstance(word, str)}
        for word in BACKEND_WORDS:
            key = " ".join(words(word, None))
            if word not in native and key not in ordinary:
                terms.setdefault(key, (word, None))
    return [value for key, value in terms.items() if key]


def _term_counts(
    text: str, terms: list[tuple[str, dict[str, Any] | None]]
) -> list[tuple[str, dict[str, Any] | None, int]]:
    """Occurrences per term; one inside a longer listed term counts for the longer one."""

    counted = [(phrase, term_pack, count_phrase(text, phrase, term_pack)) for phrase, term_pack in terms]
    result = []
    for index, (phrase, term_pack, count) in enumerate(counted):
        if not count:
            continue
        size = len(words(phrase, term_pack))
        for other_index, (other, other_pack, other_count) in enumerate(counted):
            if other_index != index and other_count and len(words(other, other_pack)) > size:
                count -= other_count * count_phrase(other, phrase, term_pack)
        if count > 0:
            result.append((phrase, term_pack, count))
    return result


def _meta_leak(reply: _Reply, pack: dict[str, Any]) -> _Hit | None:
    spans = _disjoint([match.span() for regex in _STRUCTURAL for match in regex.finditer(reply.text)])
    labels = [reply.text[start:end].strip("`") or "`" for start, end in spans]
    evidence = [_window(reply.text, start, end) for start, end in spans]
    total = len(spans)
    # Vocabulary only counts outside quoted speech: a character may say "commit".
    rest = _quotes_blanked(_blank(reply.text, spans))
    for phrase, term_pack, count in _term_counts(rest, _meta_terms(pack)):
        total += count
        labels.append(phrase)
        evidence.append(_phrase_evidence(rest, phrase, term_pack, reply.text))
    if not total:
        return None
    shown = list(dict.fromkeys(labels))
    note = f"backend {'term' if total == 1 else 'terms'} shown: " + ", ".join(_quote(label, 30) for label in shown[:2])
    return _Hit(total, evidence, note)


def _tracker_values(context: dict[str, Any]) -> list[str]:
    values = []
    for key in ("day", "revision"):
        value = context.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= TRACKER_MIN_VALUE:
            values.append(str(value))
    return list(dict.fromkeys(values))


def _tracker_leak(reply: _Reply, pack: dict[str, Any], context: dict[str, Any]) -> _Hit | None:
    folded = fold(reply.prose, pack)
    spans = _pattern_spans(folded, pack, "day_patterns")
    for value in _tracker_values(context):
        # Not a piece of a longer number such as "1.412" or "412,5".
        spans.extend(match.span() for match in re.finditer(rf"(?<![\d.,]){value}(?![\d]|[.,]\d)", folded))
    spans = _disjoint(spans)
    if not spans:
        return None
    evidence = [_located(reply.text, folded, start, end) for start, end in spans]
    first = _span_text(reply.text, folded, spans[0])
    return _Hit(len(spans), evidence, f"tracker number in prose: {_quote(first)}")


def _avoid_caps(pack: dict[str, Any], context: dict[str, Any]) -> list[tuple[str, int]]:
    """Pack and campaign avoid phrases with their per-reply caps (lowest wins)."""

    caps: dict[str, tuple[str, int]] = {}

    def add(phrase: Any, cap: Any) -> None:
        if not isinstance(phrase, str):
            return
        key = " ".join(words(phrase, pack))
        limit = cap if isinstance(cap, int) and not isinstance(cap, bool) and cap >= 0 else 0
        if key and (key not in caps or limit < caps[key][1]):
            caps[key] = (phrase.strip(), limit)

    for item in _items(pack.get("avoid_phrases")):
        if isinstance(item, dict):
            add(item.get("phrase"), item.get("max_per_reply", 1))
    for item in _items(context.get("avoid_phrases")):
        if isinstance(item, dict):
            add(item.get("phrase"), item.get("max_per_reply", 0))
        else:
            add(item, 0)  # a campaign's own avoid list means "not at all"
    return list(caps.values())


def _stems(context: dict[str, Any], pack: dict[str, Any]) -> set[str]:
    """Campaign avoid entries written as a single stem ("kenetlen", "tıkırd")."""

    stems: set[str] = set()
    for item in _items(context.get("avoid_phrases")):
        phrase = item.get("phrase") if isinstance(item, dict) else item
        if isinstance(phrase, str):
            folded = words(phrase, pack)
            if len(folded) == 1 and len(folded[0]) >= MIN_STEM_LETTERS:
                stems.add(folded[0])
    return stems


def _stem_count(text: str, stem: str, pack: dict[str, Any]) -> int:
    return sum(1 for token in words(text, pack) if token.startswith(stem))


def _avoid_phrases(reply: _Reply, pack: dict[str, Any], context: dict[str, Any]) -> _Hit | None:
    over = []
    stems = _stems(context, pack)
    for phrase, cap in _avoid_caps(pack, context):
        key = " ".join(words(phrase, pack))
        if key in stems:
            count = _stem_count(reply.prose, key, pack)
        else:
            count = count_phrase(reply.prose, phrase, pack)
        if count > cap:
            over.append((phrase, count, cap))
    if not over:
        return None
    over.sort(key=lambda item: -(item[1] - item[2]))
    evidence = [_clip(f'"{phrase}" x{count} (cap {cap})') for phrase, count, cap in over]
    parts = [f"{count}x {_quote(phrase, 30)} (cap {cap})" for phrase, count, cap in over[:2]]
    if len(over) > 2:
        parts.append(f"{len(over) - 2} more stock phrases")
    return _Hit(sum(count for _, count, _ in over), evidence, ", ".join(parts))


def _gram_hash(gram: tuple[str, ...]) -> str:
    return hashlib.blake2b(" ".join(gram).encode("utf-8"), digest_size=4).hexdigest()


def _sentence_words(sentence: str, pack: dict[str, Any]) -> tuple[list[str], list[bool]]:
    """Folded words of a sentence without apostrophe case endings, and which were capitalized."""

    raw = tokens(_CLITIC_RE.sub("", sentence))
    return [fold(token, pack) for token in raw], [token[:1].isupper() for token in raw]


def _grams(
    sentences: list[tuple[list[str], list[bool]]], size: int, ignored: frozenset[str]
) -> dict[tuple[str, ...], int]:
    """Each distinct word n-gram with two or more content words, at its first token index.

    N-grams stay inside one sentence. Content words are tokens of three or more
    letters that are not stopwords, the player character's name, or numbers.
    An n-gram whose content words are all capitalized is a name ("Ilse ile
    Varro", "the Old Harbor Gate"), not a phrase, and is left out.
    """

    found: dict[tuple[str, ...], int] = {}
    offset = 0
    for folded, capital in sentences:
        for index in range(len(folded) - size + 1):
            gram = tuple(folded[index : index + size])
            if gram in found:
                continue
            content = [position for position in range(index, index + size) if _is_content(folded[position], ignored)]
            if len(content) >= NGRAM_MIN_CONTENT and not all(capital[position] for position in content):
                found[gram] = offset + index
        offset += len(folded)
    return found


def _fingerprint(grams: dict[tuple[str, ...], int]) -> list[str]:
    """Sorted hashes, the lowest FINGERPRINT_MAX: the same n-gram keeps its chance in every reply."""

    return sorted({_gram_hash(gram) for gram in grams})[:FINGERPRINT_MAX]


def _hash_set(value: Any) -> frozenset[str]:
    return frozenset(item for item in value if isinstance(item, str)) if isinstance(value, list) else frozenset()


def _repetition(grams: dict[int, dict[tuple[str, ...], int]], history: list[dict[str, Any]]) -> _Hit | None:
    earlier = [record for record in history if isinstance(record, dict)][-(REPEAT_WINDOW - 1) :]
    if len(earlier) < REPEAT_MIN_REPLIES - 1:
        return None
    fours = [_hash_set(record.get("fingerprint")) for record in earlier]
    threes = [_hash_set(record.get("trigrams")) for record in earlier]
    window = len(earlier) + 1
    candidates: list[tuple[int, int, int, tuple[str, ...]]] = []
    for size in sorted(grams, reverse=True):
        for gram, position in grams[size].items():
            if size == 3:
                key = _gram_hash(gram)
                seen = sum(1 for hashes in threes if key in hashes)
            elif size == 4:
                key = _gram_hash(gram)
                seen = sum(1 for hashes in fours if key in hashes)
            else:  # a longer n-gram is present where all of its 4-grams are
                keys = [_gram_hash(gram[index : index + 4]) for index in range(size - 3)]
                seen = sum(1 for hashes in fours if all(key in hashes for key in keys))
            if seen + 1 >= REPEAT_MIN_REPLIES:
                candidates.append((seen + 1, size, position, gram))
    picked: list[tuple[int, int, int, tuple[str, ...]]] = []
    for candidate in sorted(candidates, key=lambda item: (-item[0], -item[1], item[2])):
        _, size, position, _ = candidate
        if all(position >= other[2] + other[1] or other[2] >= position + size for other in picked):
            picked.append(candidate)
    if not picked:
        return None
    evidence = [_clip(f'"{" ".join(gram)}" ({replies} of last {window})') for replies, _, _, gram in picked]
    replies, _, _, gram = picked[0]
    note = f"repeated from earlier replies: {_quote(' '.join(gram))} ({replies} of last {window})"
    return _Hit(len(picked), evidence, note)


def _stem_key(word: str) -> str:
    """Two words match when their keys are equal: the whole word, or its first RESTATE_STEM letters."""

    return word if len(word) < RESTATE_STEM else word[:RESTATE_STEM]


@dataclass(frozen=True)
class _Words:
    spans: list[tuple[int, int]]  # offsets in the text the words came from
    folded: list[str]
    keys: list[str]
    named: list[bool]  # capitalized without opening a sentence or a quote: part of a name


def _matchable(text: str, pack: dict[str, Any], offset: int = 0) -> _Words:
    """The words of `text` (case endings after an apostrophe dropped), ready for echo matching."""

    spans = _word_spans(_without_clitics(text))
    raw = [text[start:end] for start, end in spans]
    folded = [fold(token, pack) for token in raw]
    named = []
    for index, (start, _) in enumerate(spans):
        gap = text[spans[index - 1][1] : start] if index else "."
        named.append(raw[index][:1].isupper() and not any(char in _OPENING_MARKS for char in gap))
    return _Words(
        [(start + offset, end + offset) for start, end in spans],
        folded,
        [_stem_key(word) for word in folded],
        named,
    )


def _opening(reply: _Reply) -> tuple[int, int] | None:
    """Character range of the prose opening: RESTATE_OPENING_WORDS words or the whole first sentence."""

    spans = _word_spans(reply.prose, RESTATE_OPENING_MAX)
    if not spans:
        return None
    end = spans[min(len(spans), RESTATE_OPENING_WORDS) - 1][1]
    if reply.prose_sentences:
        first = reply.prose_sentences[0]
        found = reply.prose.find(first)
        if found >= 0:
            end = max(end, found + len(first))
    return spans[0][0], min(end, spans[-1][1])


def _echoed_run(opening: _Words, prompt: _Words, ignored: frozenset[str]) -> tuple[int, int, int] | None:
    """The longest run of RESTATE_RUN or more consecutive prompt words in the opening.

    Returns `(length, last opening index, last prompt index)`. A run must hold
    RESTATE_RUN_CONTENT content words, not all of them capitalized inside a
    sentence: a shared multi-word name ("the Old Harbor Gate") is not an echo.
    """

    positions: dict[str, list[int]] = {}
    for index, key in enumerate(prompt.keys):
        positions.setdefault(key, []).append(index)

    def qualifies(first: int, last: int) -> bool:
        content = [index for index in range(first, last + 1) if _is_content(opening.folded[index], ignored)]
        return len(content) >= RESTATE_RUN_CONTENT and not all(opening.named[index] for index in content)

    best: tuple[int, int, int] | None = None
    previous: dict[int, int] = {}
    for index, key in enumerate(opening.keys):
        current = {position: previous.get(position - 1, 0) + 1 for position in positions.get(key, ())}
        for position, length in current.items():
            if length >= RESTATE_RUN and (best is None or length > best[0]) and qualifies(index - length + 1, index):
                best = (length, index, position)
        previous = current
    return best


def _common_words(first: list[str], second: list[str]) -> int:
    """Length of the longest common subsequence of two key lists."""

    row = [0] * (len(second) + 1)
    for key in first:
        diagonal = 0
        for index, other in enumerate(second, start=1):
            above = row[index]
            row[index] = diagonal + 1 if key == other else max(row[index - 1], above)
            diagonal = above
    return row[-1]


def _echoed_quote(
    reply: _Reply, start: int, end: int, prompt: str, pack: dict[str, Any]
) -> tuple[tuple[int, int], tuple[int, int]] | None:
    """A spoken line in the opening made of the Player's spoken words: (reply span, prompt span).

    Spoken means quoted or dash dialogue, on either side.
    """

    asked = []
    for span in _speech_spans(prompt):
        keys = _matchable(prompt[span[0] : span[1]], pack).keys[:RESTATE_QUOTE_MAX_WORDS]
        if len(keys) >= RESTATE_QUOTE_WORDS:
            asked.append((span, keys))
    if not asked:
        return None
    for span in _speech_spans(reply.prose):
        if span[1] <= start:
            continue  # the opening starts at its first word, so a leading quote mark lies just before it
        if span[0] >= end:
            break  # a quote that opens inside the opening may close after it
        keys = _matchable(reply.prose[span[0] : span[1]], pack).keys[:RESTATE_QUOTE_MAX_WORDS]
        if len(keys) < RESTATE_QUOTE_WORDS:
            continue
        for source_span, source in asked:
            shared = _common_words(keys, source)
            if shared >= RESTATE_QUOTE_WORDS and shared >= RESTATE_QUOTE_SHARE * len(keys):
                return span, source_span
    return None


def _restatement(prompt: str, reply: _Reply, pack: dict[str, Any], ignored: frozenset[str]) -> _Hit | None:
    """The prose opening echoes the Player's own words.

    Flags a run of RESTATE_RUN consecutive prompt words in the opening (a word
    may change its ending, "soruyorum" -> "soruyorsun"), or a quoted line in
    the opening made of the Player's quoted words. Separate content words
    shared with the prompt are the topic, not an echo, and are fine.
    """

    window = _opening(reply)
    prompt = prompt[:RESTATE_PROMPT_CHARS]
    if window is None or not prompt.strip():
        return None
    start, end = window
    opening = _matchable(reply.prose[start:end], pack, start)
    asked = _matchable(prompt, pack)
    run = _echoed_run(opening, asked, ignored)
    if run is not None:
        length, last, position = run
        echo = (opening.spans[last - length + 1][0], opening.spans[last][1])
        source = (asked.spans[position - length + 1][0], asked.spans[position][1])
    else:
        quoted = _echoed_quote(reply, start, end, prompt, pack)
        if quoted is None:
            return None
        echo, source = quoted
    evidence = [_window(reply.text, *echo), _clip("Player: " + _window(prompt, *source, limit=SNIPPET_CHARS - 8))]
    return _Hit(1, evidence, f"opening restates the Player's words: {_quote(reply.text[echo[0] : echo[1]])}")


def _pc_authoring(reply: _Reply, pack: dict[str, Any]) -> _Hit | None:
    # Speech, quoted or dash dialogue, is skipped: an NPC may well say "you said".
    folded = fold(reply.narration, pack)
    spans = _pattern_spans(folded, pack, "pc_speech_patterns")
    if not spans:
        return None
    evidence = [_located(reply.text, folded, start, end) for start, end in spans]
    first = _span_text(reply.text, folded, spans[0])
    return _Hit(len(spans), evidence, f"narration may author the player character: {_quote(first)}")


def _status_known(status: Any) -> bool:
    text = " ".join(str(status or "").strip().strip("`*_ ").casefold().split())
    return any(re.match(rf"{re.escape(safe)}\b", text) for safe in SAFE_STATUSES)


def _secret_leak(reply: _Reply, descriptions: list[str], pack: dict[str, Any], context: dict[str, Any]) -> _Hit | None:
    found: list[tuple[dict[str, Any], int, str]] = []
    seen: set[str] = set()
    for entry in _items(context.get("protected_names")):
        if not isinstance(entry, dict) or _status_known(entry.get("status")):
            continue
        name = str(entry.get("name") or "").strip()
        key = " ".join(words(name, pack))
        if len(name) < 2 or not key or key in seen:
            continue
        seen.add(key)
        in_reply = count_phrase(reply.text, name, pack)
        # Tool descriptions are visible to the Player as well.
        in_tools = [description for description in descriptions if count_phrase(description, name, pack)]
        if not in_reply and not in_tools:
            continue
        snippet = _phrase_evidence(reply.text, name, pack) if in_reply else _clip(f"[tool] {in_tools[0]}")
        found.append((entry, in_reply + len(in_tools), snippet))
    if not found:
        return None
    # The summary reaches the GM's context, so it names fact ids, not the names.
    labels = []
    for entry, _, _ in found[:2]:
        fact = str(entry.get("fact_id") or "").strip() or "no fact id"
        status = _clip(str(entry.get("status") or "").strip() or "unrevealed", 20)
        labels.append(f"{fact}, {status}")
    note = f"{_plural(len(found), 'protected name')} in the reply ({'; '.join(labels)})"
    return _Hit(sum(count for _, count, _ in found), [snippet for _, _, snippet in found], note)


def _negated_description(reply: _Reply, pack: dict[str, Any]) -> _Hit | None:
    folded = fold(reply.narration, pack)
    spans = _pattern_spans(folded, pack, "negated_description")
    if len(spans) < NEGATED_MIN:
        return None
    evidence = [_located(reply.text, folded, start, end) for start, end in spans]
    return _Hit(len(spans), evidence, _plural(len(spans), "negated description"))


def _glossary_variants(reply: _Reply, pack: dict[str, Any], context: dict[str, Any]) -> _Hit | None:
    found: list[tuple[str, str, int]] = []
    seen: set[str] = set()
    for item in _items(context.get("glossary_variants")):
        if not isinstance(item, dict):
            continue
        variant = str(item.get("variant") or "").strip()
        preferred = str(item.get("preferred") or "").strip()
        key = " ".join(words(variant, pack))
        if not key or key in seen or key == " ".join(words(preferred, pack)):
            continue
        seen.add(key)
        count = count_phrase(reply.prose, variant, pack)
        if count and preferred:
            # "Warden" listed as a variant of "Harbor Warden" is fine inside the preferred form.
            count -= count_phrase(reply.prose, preferred, pack) * count_phrase(preferred, variant, pack)
        if count > 0:
            found.append((variant, preferred, count))
    if not found:
        return None
    evidence = [_clip(f'"{variant}" x{count} (preferred: "{preferred}")') for variant, preferred, count in found]
    variant, preferred, _ = found[0]
    note = f"{_quote(variant, 30)} instead of {_quote(preferred, 30)}"
    if len(found) > 1:
        note += f" and {_plural(len(found) - 1, 'other variant')}"
    return _Hit(sum(count for _, _, count in found), evidence, note)


def _calques(reply: _Reply, pack: dict[str, Any]) -> _Hit | None:
    found = []
    for item in _items(pack.get("calques")):
        if isinstance(item, dict) and isinstance(item.get("bad"), str):
            count = count_phrase(reply.prose, item["bad"], pack)
            if count:
                found.append((item["bad"], str(item.get("better") or ""), count))
    if not found:
        return None
    evidence = [_clip(f'"{bad}" -> "{better}"' if better else f'"{bad}"') for bad, better, _ in found]
    bad, better, _ = found[0]
    note = f"calque {_quote(bad, 30)}" + (f" (try {_quote(better, 30)})" if better else "")
    if len(found) > 1:
        note += f" and {_plural(len(found) - 1, 'other calque')}"
    return _Hit(sum(count for _, _, count in found), evidence, note)


def _summary(notes: list[str]) -> str:
    """`Last reply: a; b; c.` within SUMMARY_MAX characters, or "" when clean."""

    if not notes:
        return ""
    prefix = "Last reply: "
    parts: list[str] = []
    for index, note in enumerate(notes):
        remaining = len(notes) - index - 1
        reserve = len(f"; +{remaining} more") if remaining else 0
        if len(prefix + "; ".join(parts + [note]) + ".") + reserve > SUMMARY_MAX:
            break
        parts.append(note)
    if not parts:
        return _clip(prefix + notes[0] + ".", SUMMARY_MAX)
    dropped = len(notes) - len(parts)
    return prefix + "; ".join(parts) + (f"; +{dropped} more" if dropped else "") + "."


# ---------------------------------------------------------------------------
# Public lint
# ---------------------------------------------------------------------------


def _reply(texts: list[str]) -> _Reply:
    text = "\n\n".join(item for item in texts or [] if isinstance(item, str) and item.strip())
    text = unicodedata.normalize("NFC", text[:REPLY_MAX_CHARS])
    prose = _prose(text)
    return _Reply(
        text,
        prose,
        tuple(sentence_split(prose)),
        _blank(prose, _speech_spans(prose)),
    )


def lint_reply(
    prompt: str,
    texts: list[str],
    descriptions: list[str],
    *,
    pack: dict[str, Any],
    context: dict[str, Any],
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    """Lint one reply. Pure: reads nothing, writes nothing, never calls a model.

    `texts` are the assistant text blocks the Player saw, in order;
    `descriptions` the visible tool-call descriptions. `pack` is the play
    language's pack. `context` may carry `day`, `revision`, `player_name`,
    `protected_names` ([{name, holders, status, fact_id?}]), `avoid_phrases`
    (strings, or {phrase, max_per_reply}), `glossary_variants`
    ([{variant, preferred}]) and `play_language`. `history` holds earlier
    distinct reply records, oldest first, with `fingerprint` and `trigrams`.

    Returns `findings` ([{rule, count, evidence}] in rule order), `counts`,
    `summary` ("" when clean), `fingerprint` (folded word 4-gram hashes of the
    prose, at most 300), `trigrams` (the same for 3-grams), `language` and
    `words`.
    """

    pack = pack if isinstance(pack, dict) else {}
    context = context if isinstance(context, dict) else {}
    history = [record for record in history or [] if isinstance(record, dict)]
    if isinstance(texts, str):
        texts = [texts]
    if isinstance(descriptions, str):
        descriptions = [descriptions]
    language = normalize_code(str(context.get("play_language") or pack.get("code") or ""))
    reply = _reply(texts)
    prompt = unicodedata.normalize("NFC", str(prompt or ""))
    visible = [item.strip() for item in descriptions or [] if isinstance(item, str) and item.strip()]
    ignored = _ignored_words(pack, context)
    sentence_words = [_sentence_words(sentence, pack) for sentence in reply.prose_sentences]
    grams = {size: _grams(sentence_words, size, ignored) for size in NGRAM_SIZES}

    hits: dict[str, _Hit | None] = {
        "out_of_language": _out_of_language(reply, visible, language),
        "meta_leak": _meta_leak(reply, pack),
        "tracker_leak": _tracker_leak(reply, pack, context),
        "avoid_phrase": _avoid_phrases(reply, pack, context),
        # Without the language's stopwords every frequent function-word run would count.
        "repetition": _repetition(grams, history) if pack.get("stopwords") else None,
        "restatement": _restatement(prompt, reply, pack, ignored),
        "pc_authoring": _pc_authoring(reply, pack),
        "secret_leak": _secret_leak(reply, visible, pack, context),
        "negated_description": _negated_description(reply, pack),
        "glossary_variant": _glossary_variants(reply, pack, context),
        "calque": _calques(reply, pack),
    }
    findings = [
        {"rule": rule, "count": hit.count, "evidence": list(dict.fromkeys(hit.evidence))[:EVIDENCE_MAX]}
        for rule in RULES
        if (hit := hits[rule]) is not None and hit.count > 0
    ]
    notes = [hit.note for rule in SUMMARY_ORDER if (hit := hits[rule]) is not None and hit.count > 0]
    return {
        "language": language or None,
        "words": sum(1 for token in tokens(reply.text) if not _has_digit(token)),
        "findings": findings,
        "counts": {finding["rule"]: finding["count"] for finding in findings},
        "summary": _summary(notes),
        "fingerprint": _fingerprint(grams[4]),
        "trigrams": _fingerprint(grams[3]),
    }


# ---------------------------------------------------------------------------
# Campaign context
# ---------------------------------------------------------------------------


def _clean_cell(value: str) -> str:
    return " ".join(str(value).split()).strip("`*_\"'“”‘’ ")


def _split_list(value: str) -> list[str]:
    items = [_clean_cell(part) for part in re.split(r"[,;]", value or "")]
    return [item for item in items if item.casefold() not in EMPTY_CELLS]


def _field(block: str, label: str) -> str:
    match = re.search(rf"(?mi)^\s*[-*]\s*{re.escape(label)}\s*:[ \t]*(.*?)[ \t]*$", block)
    return _clean_cell(match.group(1)) if match else ""


def _heading_names(title: str) -> list[str]:
    title = re.sub(r"\s*\([^)]*\)\s*$", "", title)  # a trailing gloss such as "(F-007)"
    names = [_clean_cell(part) for part in re.split(r"\s+/\s+", title)]
    return [name for name in names if len(name) >= 2]


def protected_names(text: str) -> list[dict[str, Any]]:
    """`### Name` entries under `## Protected Proper Nouns` in knowledge_boundaries.md.

    Each gives `{name, holders, status, fact_id}`; `holders` come from the
    `- NPCs or factions who know:` line. The template's placeholder entry is
    skipped. A heading `A / B` names two forms of one protected name.
    """

    section = _PROTECTED_SECTION_RE.search(_COMMENT_RE.sub("", text or ""))
    if section is None:
        return []
    body = section.group("body")
    headings = list(re.finditer(r"(?m)^###\s+(.+?)\s*$", body))
    entries: list[dict[str, Any]] = []
    for index, heading in enumerate(headings):
        title = _clean_cell(heading.group(1))
        if not title or title.casefold() in PLACEHOLDER_HEADINGS:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        block = body[heading.end() : end]
        status = _field(block, "Status")
        fact_id = _field(block, "Fact id")
        holders = _split_list(_field(block, "NPCs or factions who know"))
        for name in _heading_names(title):
            entries.append({"name": name, "holders": holders, "status": status, "fact_id": fact_id})
    return entries


def _row_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    inner = stripped[1:-1] if len(stripped) > 1 and stripped.endswith("|") else stripped[1:]
    return [_clean_cell(cell) for cell in inner.split("|")]


def _column(names: list[str], prefix: str) -> int | None:
    return next((index for index, name in enumerate(names) if name.startswith(prefix)), None)


def glossary_variants(text: str) -> list[dict[str, str]]:
    """`{variant, preferred}` pairs from any glossary table with Preferred and Variants columns.

    Columns are found by header name; a Variants cell may list several forms
    separated by commas or semicolons. Commented example rows are ignored.
    """

    lines = _COMMENT_RE.sub("", text or "").splitlines()
    pairs: list[dict[str, str]] = []
    index = 0
    while index + 1 < len(lines):
        header = _row_cells(lines[index])
        if header is None or not _TABLE_SEPARATOR_RE.match(lines[index + 1].strip()):
            index += 1
            continue
        names = [cell.casefold() for cell in header]
        preferred_at, variants_at = _column(names, "preferred"), _column(names, "variant")
        index += 2
        if preferred_at is None or variants_at is None:
            continue
        while index < len(lines) and (cells := _row_cells(lines[index])) is not None:
            index += 1
            if cells and cells[0].casefold().startswith("e.g."):
                continue
            preferred = cells[preferred_at] if preferred_at < len(cells) else ""
            variants = cells[variants_at] if variants_at < len(cells) else ""
            if preferred.casefold() in EMPTY_CELLS:
                continue
            for variant in _split_list(variants):
                if variant.casefold() != preferred.casefold():
                    pairs.append({"variant": variant, "preferred": preferred})
    return pairs


def _yaml_scalar(value: str) -> str:
    value = value.strip()
    if value[:1] in {'"', "'"}:
        end = value.find(value[0], 1)
        if end > 0:
            return value[1:end].strip()
    if " #" in value:
        value = value.split(" #", 1)[0]
    return value.strip().strip("'\"")


def _inline_list(value: str) -> list[str]:
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return [_yaml_scalar(part) for part in value.strip().strip("[]").split(",") if _yaml_scalar(part)]
    return [str(item).strip() for item in decoded if str(item).strip()] if isinstance(decoded, list) else []


def _yaml_list(text: str, key: str) -> list[str]:
    """The first `key:` list in a simple YAML file, inline (`[a, b]`) or as `- item` lines."""

    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(rf"^(\s*){re.escape(key)}:[ \t]*(.*?)[ \t]*$", line)
        if not match:
            continue
        indent = len(match.group(1))
        inline = match.group(2)
        if inline and not inline.startswith("#"):
            return _inline_list(inline.split(" #", 1)[0].strip()) if inline.startswith("[") else []
        items: list[str] = []
        for child in lines[index + 1 :]:
            stripped = child.strip()
            if not stripped or stripped.startswith("#"):
                continue
            child_indent = len(child) - len(child.lstrip(" "))
            if child_indent >= indent and (stripped == "-" or stripped.startswith(("- ", "-\t"))):
                items.append(_yaml_scalar(stripped[1:]))
                continue
            if child_indent <= indent:
                break
        return [item for item in items if item]
    return []


def campaign_avoid_phrases(campaign: Path) -> list[str]:
    """`style_state.json` avoid phrases plus the profile's `narrative_signature.avoid_habits`.

    A habit that quotes phrases ('stock beats like "a moment"') contributes
    the quoted phrases; otherwise the whole habit is the phrase.
    """

    phrases: list[str] = []
    style = read_json(campaign / "style_state.json", {})
    values = style.get("avoid_phrases", []) if isinstance(style, dict) else []
    if isinstance(values, list):
        phrases.extend(value.strip() for value in values if isinstance(value, str) and value.strip())
    for habit in _yaml_list(read_text(campaign / "play_profile.yaml"), "avoid_habits"):
        quoted = [next(group for group in match if group).strip() for match in _HABIT_QUOTE_RE.findall(habit)]
        phrases.extend(quoted or [habit])
    return list(dict.fromkeys(phrase for phrase in phrases if phrase))


def campaign_context(campaign: Path, language: str) -> dict[str, Any]:
    """The lint context read from the campaign's owner files."""

    state = state_summary(campaign)
    return {
        "day": state.get("day"),
        "revision": state.get("revision"),
        "player_name": state.get("player_name") or "",
        "protected_names": protected_names(read_text(campaign / "knowledge_boundaries.md")),
        "avoid_phrases": campaign_avoid_phrases(campaign),
        "glossary_variants": glossary_variants(read_text(campaign / "glossary.md")),
        "play_language": language,
    }


# ---------------------------------------------------------------------------
# History, language, hook
# ---------------------------------------------------------------------------


def distinct_history(records: list[dict[str, Any]], *, exclude: str = "") -> list[dict[str, Any]]:
    """One record per reply, oldest first.

    A turn can end more than once (another hook may continue it); the latest
    record for a prompt replaces earlier ones, and `exclude` drops the
    current prompt's records.
    """

    kept: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in reversed(records):
        if not isinstance(record, dict):
            continue
        key = str(record.get("prompt_uuid") or "")
        if key:
            if key == exclude or key in seen:
                continue
            seen.add(key)
        kept.append(record)
    kept.reverse()
    return kept


def resolve_language(
    setting: str, prompt: str, history: list[dict[str, Any]], reply: str
) -> tuple[str, str, float | None]:
    """`(code, source, confidence)`: the configured language, else a detection.

    `auto` detects from this prompt plus up to five earlier stored prompts,
    then from the reply itself; `("", "none", None)` when nothing decides.
    """

    configured = normalize_code(setting) if setting and setting != "auto" else ""
    if configured:
        return configured, "setting", None
    earlier = [str(record.get("prompt_sample") or "") for record in history][-DETECT_PROMPTS:]
    for source, text in (("prompts", "\n".join(earlier + [prompt[:DETECT_CHARS]])), ("reply", reply[:DETECT_CHARS])):
        code, confidence = detect_language(_CLITIC_RE.sub("", text))
        if code:
            return code, source, confidence
    return "", "none", None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_hook(event: dict[str, Any]) -> dict[str, Any] | None:
    """Lint the reply that just ended and store the result.

    Returns the record written to `lint_last.json`, or None when skipped: no
    ready RPG campaign, lint switched off, no transcript or prompt, or an
    out-of-character prompt. Never raises.
    """

    try:
        return _run_hook(event)
    except Exception:
        return None


def _run_hook(event: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(event, dict):
        return None
    cwd = event.get("cwd")
    campaign = find_campaign(cwd if isinstance(cwd, str) and cwd.strip() else None)
    if campaign is None or not is_ready_rpg(campaign):
        return None
    settings = runtime_settings(campaign)
    if settings.get("presentation_lint") != "on":
        return None
    transcript = event.get("transcript_path")
    if not isinstance(transcript, str) or not transcript.strip():
        return None
    turn = last_turn(os.path.expanduser(transcript))
    if not turn:
        return None
    prompt = str(turn.get("prompt") or "")
    if _OOC_RE.match(prompt):
        return None  # an out-of-character exchange is not narration
    texts = [text for text in turn.get("assistant_texts") or [] if isinstance(text, str)]
    final = event.get("last_assistant_message")
    # Stop can fire before the transcript holds the final message.
    if isinstance(final, str) and final.strip() and (not texts or texts[-1].strip() != final.strip()):
        texts.append(final)
    descriptions = [text for text in turn.get("tool_descriptions") or [] if isinstance(text, str)]
    prompt_uuid = str(turn.get("prompt_uuid") or "")

    directory = runtime_dir(campaign)
    history_path = directory / LINT_HISTORY
    history = distinct_history(read_jsonl(history_path), exclude=prompt_uuid)
    language, source, confidence = resolve_language(
        settings.get("language", "auto"), prompt, history, "\n\n".join(texts)
    )
    context = campaign_context(campaign, language)
    result = lint_reply(prompt, texts, descriptions, pack=load_pack(language), context=context, history=history)

    at = _now()
    session_id = str(event.get("session_id") or "")
    record = {
        "schema_version": RECORD_SCHEMA,
        "at": at,
        "session_id": session_id,
        "prompt_uuid": prompt_uuid,
        "language": language or None,
        "language_source": source,
        "language_confidence": confidence,
        "revision": context.get("revision"),
        "day": context.get("day"),
        "words": result["words"],
        "counts": result["counts"],
        "findings": result["findings"],
        "summary": result["summary"],
    }
    write_json_atomic(directory / LINT_LAST, record)
    append_jsonl(
        history_path,
        {
            "at": at,
            "session_id": session_id,
            "prompt_uuid": prompt_uuid,
            "language": language or None,
            "prompt_sample": prompt[:PROMPT_SAMPLE_CHARS],
            "words": result["words"],
            "counts": result["counts"],
            "fingerprint": result["fingerprint"],
            "trigrams": result["trigrams"],
        },
        keep_last=HISTORY_KEEP,
    )
    return record


# ---------------------------------------------------------------------------
# Report and CLI
# ---------------------------------------------------------------------------


def report(campaign: Path, last: int | None = None) -> dict[str, Any]:
    """Aggregate rule counts over the stored history (for the distill review)."""

    folder = campaign / RUNTIME_DIR
    records = distinct_history(read_jsonl(folder / LINT_HISTORY))
    if last:
        records = records[-last:]
    rules = {rule: {"replies": 0, "total": 0} for rule in RULES}
    languages: Counter[str] = Counter()
    clean = 0
    for record in records:
        counts = record.get("counts") if isinstance(record.get("counts"), dict) else {}
        flagged = False
        for rule, value in counts.items():
            if rule in rules and isinstance(value, int) and not isinstance(value, bool) and value > 0:
                rules[rule]["replies"] += 1
                rules[rule]["total"] += value
                flagged = True
        clean += 0 if flagged else 1
        languages[str(record.get("language") or "unknown")] += 1
    latest = read_json(folder / LINT_LAST, {})
    return {
        "ok": True,
        "replies": len(records),
        "clean_replies": clean,
        "since": records[0].get("at") if records else None,
        "until": records[-1].get("at") if records else None,
        "languages": dict(sorted(languages.items())),
        "rules": rules,
        "latest_summary": latest.get("summary", "") if isinstance(latest, dict) else "",
    }


def _campaign_arg(value: str) -> Path:
    base = Path(value)
    nested = base / "campaign"
    if (nested / "current_state.yaml").is_file():
        return nested
    return base


def _hook_main() -> int:
    try:
        raw = sys.stdin.buffer.read()
        event = json.loads(raw.decode("utf-8-sig", errors="replace"))
    except Exception:
        return 0
    if isinstance(event, dict):
        run_hook(event)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("hook", help="Lint the reply that just ended (Stop hook event JSON on stdin)")
    summary = commands.add_parser("report", help="Aggregate counts per rule over the lint history")
    summary.add_argument("campaign", help="Campaign folder (or the project folder that holds campaign/)")
    summary.add_argument("--last", type=int, default=None, help="Only the newest N replies")
    args = parser.parse_args(argv)
    if args.command == "hook":
        return _hook_main()
    campaign = _campaign_arg(args.campaign)
    if not (campaign / "current_state.yaml").is_file():
        print(
            json.dumps(
                {"ok": False, "failure_category": "campaign_missing", "failure_reason": f"No campaign at {campaign}"},
                ensure_ascii=True,
            )
        )
        return 2
    if args.last is not None and args.last < 1:
        print(
            json.dumps(
                {"ok": False, "failure_category": "input_invalid", "failure_reason": "--last must be at least 1"},
                ensure_ascii=True,
            )
        )
        return 2
    print(json.dumps(report(campaign, args.last), indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

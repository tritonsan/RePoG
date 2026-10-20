"""Language packs: per-language word lists and patterns kept as data, not code.

Every language-aware runtime check (presentation lint, scene capsule, name
check) reads what it knows about a language from
`plugin/packs/languages/<code>.json`. This module only loads packs, folds case
the way a language folds it, splits words and sentences in any script, counts
phrases, and guesses a text's language from its function words. It never
decides what a sentence means.

Pack keys (all optional except `code`, `name`, `stopwords`): `casefold`
("turkish" or "default"), `stopwords`, `avoid_phrases`, `negated_description`,
`day_patterns`, `pc_speech_patterns`, `meta_words`, `calques`, `common_words`,
`card`. Pack regexes are written for folded text (see `fold`): lower case,
German sharp s as "ss", Turkish dotted and dotless i kept apart.

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
from functools import lru_cache
from pathlib import Path
from typing import Any


PACK_DIR = Path(__file__).resolve().parents[1] / "packs" / "languages"
MIN_DETECT_WORDS = 8
# A guess resting on a single function word is noise: Turkish "et" (meat; the
# verb in "devam et") is also French "et", Turkish "para" (money) is Spanish
# "para". The winning language needs at least this many stopword hits.
MIN_DETECT_HITS = 2
CARD_LIMIT = 600
LIST_KEYS = ("stopwords", "negated_description", "day_patterns", "pc_speech_patterns", "meta_words", "common_words")
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


def _cap(value: Any) -> int:
    """A per-reply cap: a whole number of zero or more, else the default 1."""

    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 1


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
        values = raw.get(key, [])
        pack[key] = [value for value in values if isinstance(value, str) and value.strip()] if isinstance(values, list) else []
    phrases = raw.get("avoid_phrases", [])
    pack["avoid_phrases"] = [
        {"phrase": item["phrase"], "max_per_reply": _cap(item.get("max_per_reply")), "note": _text(item.get("note"))}
        for item in (phrases if isinstance(phrases, list) else [])
        if isinstance(item, dict) and isinstance(item.get("phrase"), str) and item["phrase"].strip()
    ]
    calques = raw.get("calques", [])
    pack["calques"] = [
        {"bad": item["bad"], "better": _text(item.get("better"))}
        for item in (calques if isinstance(calques, list) else [])
        if isinstance(item, dict) and isinstance(item.get("bad"), str) and item["bad"].strip()
    ]
    pack["card"] = _clip(_text(raw.get("card")).strip(), CARD_LIMIT)
    return pack


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

"""Scene capsule: a compact, deterministic briefing injected before each prompt.

Long sessions lose facts to context compaction, and a GM rarely re-reads the
character notes mid-scene. Before each Player prompt the UserPromptSubmit hook
injects this capsule as hidden context: the scene header, the people in scope
with their stable `## Core` facts, which protected facts each of them does
not hold (by fact id only, never the secret text), the standing directives in
scope, the play-language card, the last reply's presentation-lint summary,
roll receipts not yet committed, and staged curation waiting to be applied.

The capsule is a read of the owners, never an owner. It decides nothing about
meaning, invents nothing, and names the note that holds each fact so the GM can
read it before contradicting it. Long values are cut at a clause or list
boundary outside brackets, so an item never loses its bracketed qualifier, and
a dated legacy state keeps its heading ("Current State (day 737)") instead of
passing for the present.

To stay small it is sent in full on the first prompt of a session, after a
reset (SessionStart on resume, clear, or compaction), when the scene id
changes, and on every 12th prompt. Otherwise the header is followed only by
what changed since it was last shown in this session: changed sections, and
for the cast only the changed lines of each person (with their protected
Status and Kin lines), each line whole; what does not fit waits for the next
prompt instead of being cut. Someone who leaves scope and comes back unchanged
costs one roster line while their briefing is under 12 prompts old, and is
briefed again in full after that. Per-session line hashes, a turn counter, and
the names the last prompt mentioned live in
`campaign/.repog-runtime/capsule_state.json`, which only the prompt hook and a
reset write. Names from the last reply go to `capsule_names.json`, which only
the (asynchronous) Stop hook writes, so the two hooks never overwrite each
other's state. Both files may be deleted at any time.

Names are matched as whole words after the language pack's case folding (so
Turkish dotted and dotless i stay distinct), against character, place, and
faction note titles, file stems, and `- Aliases:` Core lines, plus each
title's given names: a word of a multi-word title that no other note or the
player character uses and that the notes never write in lower case (so
"Maren" finds "Maren Ashwick", while "Lord" or "Old" find nobody). A given
name that is a stopword or common word of the play language is not matched in
free text. Names shorter than three letters are never matched in free text.

CLI (for debugging; the hooks call the functions directly):
    python tools/scene_capsule.py hook < event.json
    python tools/scene_capsule.py reset [--session ID] <campaign>
    python tools/scene_capsule.py show <campaign> [--full] [--prompt TEXT] [--session ID]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

import curation
import lang_pack
import owner_ops
import roll_dice
from repog_runtime import (
    RUNTIME_DEFAULTS,
    RUNTIME_DIR,
    block_scalars,
    find_campaign,
    is_ready_rpg,
    read_json,
    read_text,
    runtime_settings,
    state_summary,
    write_json_atomic,
)


STATE_FILE = "capsule_state.json"
NAMES_FILE = "capsule_names.json"
LINT_FILE = "lint_last.json"
STATE_VERSION = 2
NAMES_VERSION = 1

FULL_EVERY = 12  # every 12th prompt of a session gets a full capsule
FULL_MAX = 6_000
DELTA_MAX = 2_000
MAX_CAST = 8
MAX_DIRECTIVES = 12
MAX_SECRET_IDS = 12
MAX_ROLLS = 8
MAX_STAGED = 10
MAX_RELATIONS = 3
MAX_SESSIONS = 24
MAX_REMEMBERED = 16
MAX_REPLY_BATCHES = 3  # reply-name batches kept per session until a prompt uses them
MAX_NAME_CHARS = 80
MIN_NAME_LETTERS = 3
MIN_CUT = 24  # a line that would be cut shorter than this is dropped instead
MIN_SHARE = 48  # a cast line or knowledge field cut to fit gets at least this much, or waits

HEADER_CHARS = 240
FIELD_CHARS = 160
KIN_CHARS = 600
NOW_CHARS = 300
STATE_LABEL_CHARS = 32
RELATION_CHARS = 160
KNOWLEDGE_CHARS = 400
CARD_CHARS = 600
GLOSSARY_CHARS = 240
LINT_CHARS = 400
ROSTER_CHARS = 300

CHARACTER, PLACE, FACTION = "character", "place", "faction"
NOTE_FOLDERS = ((CHARACTER, "characters"), (PLACE, "places"), (FACTION, "factions"))

CORE_FIELDS = ("Status", "Pronouns and address", "Kin", "Role", "Home", "Speaks")
# Status and Kin survive any size cut: a dead relative treated as alive is the
# failure this capsule exists to prevent. Kin is cut only between relatives,
# never inside one, and only past KIN_CHARS.
PROTECTED_FIELDS = frozenset({"Status", "Kin"})
LEGACY_FIELDS = ("Voice rhythm", "Social tactic", "Hard boundary", "Routine and availability")
GLOSSARY_FIELDS = ("Titles and honorifics", "Address forms")
HOLDER_FIELDS = ("npcs or factions who know", "companions who know")
CONFIRMED_FIELD = "confirmed fact ids"
PC_KNOWN_STATUSES = ("pc-known", "player-known", "confirmed")  # as the presentation lint reads them

SECTION_ORDER = ("cast", "secrets", "directives", "language", "lint", "rolls", "curation")
# Per-section character caps. The cast gets whatever the other sections leave
# under the capsule cap, up to its own cap. A delta shows the language section
# only when it changed (a language detected after the first prompt).
CAPS: dict[bool, dict[str, int]] = {
    True: {
        "header": 400,
        "cast": 4_400,
        "secrets": 600,
        "directives": 1_100,
        "language": 900,
        "lint": 450,
        "rolls": 400,
        "curation": 250,
    },
    False: {
        "header": 400,
        "cast": 1_600,
        "secrets": 250,
        "directives": 380,
        "language": 700,
        "lint": 420,
        "rolls": 250,
        "curation": 120,
    },
}
# What a delta shows for a section that had content and is now empty.
CLEARED = {
    "cast": "[cast] nobody present or named.",
    "secrets": "[secrets] nothing to guard for this cast.",
    "directives": "[directives] none active in scope.",
    "lint": "[lint] last reply clean.",
    "rolls": "[rolls] no open receipts.",
    "curation": "[curation] nothing staged.",
}
DEFER_NOTE = "  (+{count} more in scope, shown on the next prompt)"
WAIT_NOTE = "  (+{count} more lines on the next prompt)"
PARTIAL_NOTE = ": changed lines only"
GONE_NOTE = "(no longer recorded)"

# Same cadence table as the RPG writer: a full distill is required once
# `durable_turns_since_distill` reaches the policy's count.
DISTILL_THRESHOLDS = {
    "every_durable": 1,
    "scene_checkpoint_or_3_durable": 3,
    "scene_checkpoint_or_5_durable": 5,
    "scene_or_3_durable": 3,
    "scene_or_5_durable": 5,
}

FIELD_RE = re.compile(r"^ ?[-*+][ \t]+([^:\n]{1,80}?)[ \t]*:[ \t]*(.*?)[ \t]*$")
BULLET_RE = re.compile(r"^[-*+][ \t]+")
TIER_RE = re.compile(r"(?mi)^[ \t]*(?:[-*+][ \t]+)?Tier[ \t]*:[ \t]*(.*?)[ \t]*$")
TITLE_RE = re.compile(r"(?m)^#[ \t]+(.+?)[ \t]*#*[ \t]*$")
CORE_RE = re.compile(r"(?mis)^##[ \t]+Core[ \t]*#*[ \t]*$(.*?)(?=^#{1,2}[ \t]|\Z)")
LEGACY_STATE_RE = re.compile(r"^(current state|state on day)\b")
NUMBER_RE = re.compile(r"\d+")
EMPTY_FIELD_RE = re.compile(r"^[^:]{1,80}:$")
QUALIFIER_RE = re.compile(r"\s*[(\[,;:]|\s+[-–—]\s+")
FACT_ID_RE = re.compile(r"[^\s,;()`'\"]+")
NAME_WORD_RE = re.compile(r"[^\W\d_]+")
NOT_PROSE_RE = re.compile(r"`[^`\n]*`|\S*[/\\_]\S*")  # code spans and paths: file stems are lower case

_PER_PROMPT = ("cast:", "secrets:")  # records of cast and secret lines, which expire after FULL_EVERY prompts
_OPEN, _CLOSE = "([{", ")]}"
_SENTENCE_END = ".!?…"
_EMPTY_HASH = hashlib.sha256(b"").hexdigest()[:16]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def _read_md(path: Path) -> str:
    """A campaign Markdown file without BOM, CR, or HTML comments; "" when unreadable.

    Bytes that are not UTF-8 are replaced instead of costing the whole note, so
    a note saved in another encoding still shows its readable lines. Comments
    hold examples and notes to the author, never campaign truth. An
    unterminated comment hides the rest of the file, as Markdown renders it.
    """

    try:
        text = path.read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return ""
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?s)<!--.*?-->", "", text)
    return re.sub(r"(?s)<!--.*\Z", "", text)


def _clip(text: str, limit: int) -> str:
    """`text` cut to at most `limit` characters, at a word boundary when one is near, marked "…"."""

    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    space = cut.rfind(" ")
    if space >= (limit - 1) // 2:
        cut = cut[:space]
    return cut.rstrip(" ,;:…") + "…"


def _safe_clip(text: str, limit: int) -> str:
    """`text` cut to `limit` characters at the last clause, list, or word boundary outside brackets.

    A cut never separates an item from its bracketed qualifier, as in "Ilse
    (sister, dead)" or "F-011 (all but the informer)", so whatever is shown
    keeps the meaning the owner gives it; "…" marks the omitted rest.
    """

    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    room = limit - 1
    clause = comma = word = 0
    depth = 0
    for index in range(room + 1):
        char = text[index]
        if char in _OPEN:
            depth += 1
        elif char in _CLOSE:
            depth = max(0, depth - 1)
        elif depth == 0:
            if char == ";" or (char in _SENTENCE_END and text[index + 1 : index + 2] in (" ", "")):
                clause = index
            elif char == ",":
                comma = index
            elif char == " " and text[index + 1 : index + 2] not in tuple(_OPEN):
                word = index  # never between an item and its bracketed qualifier
    for cut, floor in ((clause, room // 2), (comma, room // 2), (word, room // 3)):
        if cut and cut >= floor:
            return text[:cut].rstrip(" ,;:…") + "…"
    return _clip(text, limit)


def _clauses(text: str) -> list[str]:
    """`text` split at semicolons outside brackets."""

    parts: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if char in _OPEN:
            depth += 1
        elif char in _CLOSE:
            depth = max(0, depth - 1)
        elif char == ";" and depth == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    parts.append(text[start:].strip())
    return [part for part in parts if part]


def _head_tail(text: str, limit: int) -> str:
    """A long running cell as its first clause and as many of its last clauses as fit.

    Relationship cells that grow by appending keep their summary in the first
    clause and the newest change in the last ones; the omitted middle is
    marked. Anything else is cut with `_safe_clip`.
    """

    if len(text) <= limit:
        return text
    clauses = _clauses(text)
    if len(clauses) >= 3 and len(clauses[0]) <= limit // 2:
        tail: list[str] = []
        used = len(clauses[0]) + len("; …")
        for clause in reversed(clauses[1:]):
            if used + 2 + len(clause) > limit:
                break
            tail.insert(0, clause)
            used += 2 + len(clause)
        if tail and len(tail) < len(clauses) - 1:
            return f"{clauses[0]}; …; {'; '.join(tail)}"
        if not tail and limit - used - 2 >= 2 * MIN_CUT:
            # The newest clause alone is too long: show how it begins.
            return f"{clauses[0]}; …; {_safe_clip(clauses[-1], limit - used - 2)}"
    return _safe_clip(text, limit)


def _join(items: Iterable[str]) -> str:
    """Items on one line: after a full stop a space, otherwise "; "."""

    text = ""
    for item in items:
        if text:
            text += " " if text.endswith((".", "!", "?")) else "; "
        text += item
    return text


def _flat(text: Any) -> str:
    return " ".join(str(text).split())


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _int(value: Any) -> int:
    return value if type(value) is int and value >= 0 else 0


def _fit_lines(lines: list[str], cap: int) -> list[str]:
    """Keep whole lines while they fit in `cap` characters; mark a cut with `…`."""

    kept: list[str] = []
    used = -1  # the first line has no newline before it
    for line in lines:
        if used + 1 + len(line) <= cap:
            kept.append(line)
            used += 1 + len(line)
            continue
        room = cap - used - 1
        if room >= MIN_CUT or (not kept and room > 0):
            kept.append(_clip(line, room))
        elif kept and not kept[-1].endswith("…"):
            last = kept[-1]
            kept[-1] = last + "…" if used < cap else last[:-1].rstrip() + "…"
        break
    return kept


def _water(lengths: list[int], budget: int) -> list[int]:
    """Shares of `budget`: short wants are met whole, long ones split what is left evenly."""

    shares = [0] * len(lengths)
    left = len(lengths)
    for index in sorted(range(len(lengths)), key=lambda item: (lengths[item], item)):
        give = min(lengths[index], max(0, budget) // left)
        shares[index] = give
        budget -= give
        left -= 1
    return shares


def _share(items: list[str], limit: int) -> str:
    """Items joined (see `_join`) within `limit`, each keeping its head.

    Short items are shown whole and long ones split what is left, so one long
    field (a list of confirmed fact ids) cannot hide the fields after it (the
    explicitly unknown ones). Items that cannot get MIN_SHARE characters each
    are dropped from the end, marked with "…".
    """

    whole = _join(items)
    if len(whole) <= limit:
        return whole
    for count in range(len(items), 0, -1):
        chosen = items[:count]
        dropped = count < len(items)
        budget = limit - 2 * (count - 1) - (2 if dropped else 0)
        shares = _water([len(item) for item in chosen], budget)
        if all(share >= min(len(item), MIN_SHARE) for share, item in zip(shares, chosen)):
            text = _join(_safe_clip(item, share) for item, share in zip(chosen, shares))
            if dropped and not text.endswith("…"):
                text += " …" if text.endswith((".", "!", "?")) else "…"
            return text
    return _safe_clip(items[0], limit) if items else ""


# ---------------------------------------------------------------------------
# Markdown structure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Section:
    level: int
    title: str
    body: str


def _sections(text: str) -> list[_Section]:
    """Every heading outside code fences, with the text up to the next heading of its level or higher."""

    lines = text.splitlines()
    heads: list[tuple[int, int, str]] = []
    fenced = False
    for index, line in enumerate(lines):
        if owner_ops.FENCE_RE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            match = owner_ops.HEADING_RE.match(line)
            if match:
                heads.append((index, len(match.group(1)), match.group(2).strip()))
    sections: list[_Section] = []
    for position, (index, level, title) in enumerate(heads):
        end = next((later for later, later_level, _ in heads[position + 1 :] if later_level <= level), len(lines))
        sections.append(_Section(level, title, "\n".join(lines[index + 1 : end])))
    return sections


def _filled(value: str) -> str:
    """A field value, or "" for a template placeholder such as an enum menu."""

    value = value.strip()
    if "|" in value or value.replace(" ", "").upper() == "T1/T2/T3":
        return ""
    return value


def _fields(body: str) -> dict[str, str]:
    """`- Key: value` bullets keyed by casefolded key; the first occurrence wins.

    Indented lines continue the previous field (a wrapped sentence, or nested
    bullets joined with "; "). A blank line or other text ends the field.
    """

    values: dict[str, str] = {}
    current: str | None = None
    for line in body.splitlines():
        if not line.strip():
            current = None
            continue
        indent = len(line) - len(line.lstrip(" \t"))
        match = FIELD_RE.match(line) if indent <= 1 else None
        if match:
            key = match.group(1).strip().casefold()
            current = None if key in values else key
            if current is not None:
                values[current] = match.group(2).strip()
            continue
        if current is not None and indent >= 2:
            item = line.strip()
            nested = BULLET_RE.match(item)
            item = item[nested.end() :] if nested else item
            joiner = "; " if nested else " "
            values[current] = f"{values[current]}{joiner}{item}" if values[current] else item
            continue
        current = None
    return values


def _items(body: str) -> list[str]:
    """A block's bullets and paragraphs as one-line items, without empty `Key:` fields.

    A wrapped line continues its item; a nested bullet joins it with "; ".
    """

    items: list[str] = []
    joined = False  # whether the next line may continue the last item
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            joined = False
            continue
        indent = len(line) - len(line.lstrip(" \t"))
        bullet = BULLET_RE.match(stripped)
        text = _flat(stripped[bullet.end() :] if bullet else stripped)
        if not text:
            continue
        if (bullet and indent <= 1) or not joined or not items:
            items.append(text)
        else:
            items[-1] += (" " if not bullet or items[-1].endswith(":") else "; ") + text
        joined = True
    return [item for item in items if not EMPTY_FIELD_RE.match(item)]


def _cells(line: str) -> list[str]:
    row = line.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", row)]


def _tables(text: str, required: set[str]) -> list[tuple[list[str], list[str]]]:
    """Rows of every table whose header names all `required` columns: (columns, cells)."""

    rows: list[tuple[list[str], list[str]]] = []
    lines = text.splitlines()
    columns: list[str] | None = None
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            columns = None
            continue
        if columns is None:
            names = [cell.casefold() for cell in _cells(line)]
            following = lines[index + 1].strip() if index + 1 < len(lines) else ""
            if required <= set(names) and owner_ops.TABLE_SEPARATOR_RE.match(following):
                columns = names
            continue
        if owner_ops.TABLE_SEPARATOR_RE.match(line.strip()):
            continue
        rows.append((columns, _cells(line)))
    return rows


# ---------------------------------------------------------------------------
# Notes and name matching
# ---------------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class _Note:
    kind: str
    path: str  # campaign-relative POSIX path
    title: str
    aliases: tuple[str, ...]
    text: str

    @property
    def names(self) -> tuple[str, ...]:
        return (self.title, Path(self.path).stem, *self.aliases)


def _note_aliases(text: str) -> tuple[str, ...]:
    match = CORE_RE.search(text)
    raw = _filled(_fields(match.group(1)).get("aliases", "")) if match else ""
    aliases = (_flat(part).strip("\"'`") for part in re.split(r"[,;]", raw))
    return tuple(alias for alias in aliases if alias)


def _note_paths(directory: Path) -> list[Path]:
    """`*.md` files directly in `directory`, sorted; names starting with "_" are templates."""

    try:
        with os.scandir(directory) as entries:
            names = [
                entry.name
                for entry in entries
                if entry.name.lower().endswith(".md") and not entry.name.startswith("_") and entry.is_file()
            ]
    except OSError:
        return []
    return [directory / name for name in sorted(names)]


def _load_notes(campaign: Path) -> list[_Note]:
    """Character, place, and faction notes, for name matching and the cast."""

    notes: list[_Note] = []
    for kind, folder in NOTE_FOLDERS:
        for path in _note_paths(campaign / folder):
            text = _read_md(path)
            match = TITLE_RE.search(text)
            title = _flat(match.group(1)) if match else path.stem
            notes.append(_Note(kind, f"{folder}/{path.name}", title or path.stem, _note_aliases(text), text))
    return notes


def _letters(tokens: tuple[str, ...]) -> int:
    return sum(1 for token in tokens for char in token if char.isalpha())


def _contains(haystack: tuple[str, ...], needle: tuple[str, ...]) -> bool:
    size = len(needle)
    return bool(size) and any(haystack[index : index + size] == needle for index in range(len(haystack) - size + 1))


def _lowercase_words(texts: Iterable[str], pack: dict[str, Any]) -> set[str]:
    """Folded words the notes write in lower case somewhere in their prose.

    A word written in lower case is an ordinary word or a title ("lord",
    "old"), not a given name. Code spans and paths are skipped, because file
    stems are written in lower case.
    """

    raw: set[str] = set()
    for text in texts:
        prose = NOT_PROSE_RE.sub(" ", unicodedata.normalize("NFC", text))
        raw.update(word for word in NAME_WORD_RE.findall(prose) if word[0].islower())
    return {lang_pack.fold(word, pack) for word in raw}


class _Matcher:
    """Whole-word, folded name lookup over every note's title, stem, aliases, and given names."""

    def __init__(self, notes: list[_Note], pack: dict[str, Any], reserved: Iterable[str] = ()) -> None:
        self.pack = pack
        self.exact: dict[tuple[str, ...], list[_Note]] = {}
        self.first: dict[str, list[tuple[tuple[str, ...], _Note]]] = {}
        for note in notes:
            for name in note.names:
                tokens = self.tokens(name)
                if not tokens:
                    continue
                bucket = self.exact.setdefault(tokens, [])
                if note not in bucket:
                    bucket.append(note)
                if _letters(tokens) >= MIN_NAME_LETTERS:
                    self.first.setdefault(tokens[0], []).append((tokens, note))
        self.blocked = {
            lang_pack.fold(word, pack) for key in ("stopwords", "common_words") for word in pack.get(key) or []
        }
        self.given: dict[str, _Note] = {}
        self.given_of: dict[_Note, tuple[str, ...]] = {}
        self._index_given(notes, reserved)

    def tokens(self, text: str) -> tuple[str, ...]:
        return tuple(lang_pack.words(text, self.pack))

    def _index_given(self, notes: list[_Note], reserved: Iterable[str]) -> None:
        """Given names: a title word no other note (or the player character) uses, never written in lower case."""

        owners: dict[str, set[int]] = {}
        for position, note in enumerate(notes):
            for name in note.names:
                for token in self.tokens(name):
                    owners.setdefault(token, set()).add(position)
        for name in reserved:
            for token in self.tokens(name):
                owners.setdefault(token, set()).add(-1)
        candidates: dict[str, int] = {}
        for position, note in enumerate(notes):
            title = self.tokens(note.title)
            if note.kind != CHARACTER or len(title) < 2:
                continue  # people go by a first name; places and factions by their names
            for token in title:
                if (
                    owners.get(token) == {position}
                    and _letters((token,)) >= MIN_NAME_LETTERS
                    and not any(char.isdigit() for char in token)
                ):
                    candidates[token] = position
        if not candidates:
            return
        lower = _lowercase_words((note.text for note in notes), self.pack)
        for token, position in candidates.items():
            if token in lower:
                continue
            note = notes[position]
            self.given[token] = note
            self.given_of[note] = (*self.given_of.get(note, ()), token)

    def scan(self, text: str, kinds: Iterable[str] | None = None) -> list[_Note]:
        """Notes named in free text, in order of first mention; the longest name wins at each word.

        A given name counts only where no full name starts, and never when it
        is a stopword or common word of the play language.
        """

        wanted = set(kinds) if kinds is not None else None
        words = self.tokens(text)
        found: list[_Note] = []
        index = 0
        while index < len(words):
            best_size = 0
            best: list[_Note] = []
            for name, note in self.first.get(words[index], ()):
                if wanted is not None and note.kind not in wanted:
                    continue
                size = len(name)
                if size >= best_size and words[index : index + size] == name:
                    if size > best_size:
                        best_size, best = size, []
                    if note not in best:
                        best.append(note)
            if not best_size and words[index] not in self.blocked:
                note = self.given.get(words[index])
                if note is not None and (wanted is None or note.kind in wanted):
                    best_size, best = 1, [note]
            for note in best:
                if note not in found:
                    found.append(note)
            index += best_size or 1
        return found

    def named(self, name: str, kinds: Iterable[str]) -> list[_Note]:
        """Notes whose title, stem, alias, or given name equals `name` after folding."""

        wanted = set(kinds)
        tokens = self.tokens(name)
        found = [note for note in self.exact.get(tokens, []) if note.kind in wanted]
        if not found and len(tokens) == 1:
            note = self.given.get(tokens[0])
            if note is not None and note.kind in wanted:
                found = [note]
        return found

    def resolve(self, name: str, kinds: Iterable[str]) -> _Note | None:
        """The note a scene entry or location names, or None.

        An exact title, stem, alias, or given name first; then the entry's head
        before a qualifier ("Witness (wounded)", "Edric, at the gate"); then,
        for an id without spaces ("npc_witness"), the first name inside it. A
        phrase that only mentions someone ("Edric's guard") names nobody.
        """

        kinds = tuple(kinds)
        head = QUALIFIER_RE.split(name.strip(), maxsplit=1)[0]
        found = self.named(name, kinds) or (self.named(head, kinds) if head else [])
        if not found and not any(char.isspace() for char in name.strip()):
            found = self.scan(name, kinds)
        return found[0] if found else None

    def holder_names(self, member: _Member) -> list[tuple[str, ...]]:
        """Folded name forms that identify `member` in a holder list, given names included."""

        names = [self.tokens(name) for name in member.names]
        if member.note is not None:
            names.extend((token,) for token in self.given_of.get(member.note, ()))
        return [name for name in names if name]


# ---------------------------------------------------------------------------
# Scope: who and what this turn is about
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Member:
    name: str
    note: _Note | None
    via: str  # present | mentioned

    @property
    def names(self) -> tuple[str, ...]:
        return self.note.names if self.note is not None else (self.name,)

    @property
    def key(self) -> str:
        if self.note is not None:
            return f"cast:{self.note.path}"
        return f"cast:name:{_flat(self.name).casefold()}"


@dataclass
class _Scope:
    cast: list[_Member]
    entity_names: set[tuple[str, ...]]  # folded names of every entity in scope, for directives
    mentioned: list[str]  # note titles named in the prompt, remembered for the next turn


def _remembered(entry: dict[str, Any]) -> list[str]:
    names = entry.get("names")
    return [name for name in names if isinstance(name, str)] if isinstance(names, list) else []


def _scope(summary: dict[str, Any], prompt: str, remembered: list[str], matcher: _Matcher) -> _Scope:
    cast: list[_Member] = []
    seen: set[str] = set()

    def add(member: _Member) -> None:
        if len(cast) < MAX_CAST and member.key not in seen:
            seen.add(member.key)
            cast.append(member)

    for raw in summary.get("present_npcs") or []:
        name = _flat(raw)
        if name:
            note = matcher.resolve(name, (CHARACTER,)) or matcher.resolve(name, (FACTION,))
            add(_Member(note.title if note else name, note, "present"))
    named = matcher.scan(prompt)
    recent: list[_Note] = []
    for name in remembered:
        for note in matcher.named(name, (CHARACTER, PLACE, FACTION)):
            if note not in recent:
                recent.append(note)
    for note in named + recent:
        if note.kind == CHARACTER:
            add(_Member(note.title, note, "mentioned"))

    entity_names: set[tuple[str, ...]] = set()
    for member in cast:
        entity_names.update(matcher.holder_names(member))
    for note in named + recent:
        if note.kind != CHARACTER:
            entity_names.update(matcher.tokens(name) for name in note.names)
    location = _flat(summary.get("location") or "")
    if location:
        entity_names.add(matcher.tokens(location))
        place = matcher.resolve(location, (PLACE,))
        if place is not None:
            entity_names.update(matcher.tokens(name) for name in place.names)
    entity_names.discard(())
    mentioned = list(dict.fromkeys(note.title for note in named))
    return _Scope(cast, entity_names, mentioned)


# ---------------------------------------------------------------------------
# Language
# ---------------------------------------------------------------------------


def _lint_data(campaign: Path) -> dict[str, Any]:
    data = read_json(campaign / RUNTIME_DIR / LINT_FILE, None)
    return data if isinstance(data, dict) else {}


def _lint_language(lint: dict[str, Any]) -> str:
    """The play language the presentation lint detected, under whichever key it used."""

    candidates: list[Any] = [lint.get(key) for key in ("play_language", "language", "detected_language")]
    detection = lint.get("detection")
    if isinstance(detection, dict):
        candidates.extend(detection.get(key) for key in ("language", "code"))
    for value in candidates:
        if isinstance(value, dict):
            value = value.get("code") or value.get("language")
        code = lang_pack.normalize_code(value) if isinstance(value, str) else ""
        if code:
            return code
    return ""


def _language(
    settings: dict[str, Any], prompt: str, entry: dict[str, Any], lint: dict[str, Any]
) -> tuple[str, str]:
    """(code, source): the configured language, else a detected one, else ("", "auto").

    The lint's detection (over several prompts and the reply) comes first,
    then the one this session already settled on, and only then this prompt
    alone, so one out-of-character line in another language cannot switch the
    pack back and forth.
    """

    configured = str(settings.get("language") or "auto").strip()
    code = lang_pack.normalize_code(configured) if configured.casefold() != "auto" else ""
    if code:
        return code, "configured"
    code = _lint_language(lint)
    if code:
        return code, "detected"
    stored = entry.get("language")
    code = lang_pack.normalize_code(stored) if isinstance(stored, str) else ""
    if code:
        return code, "detected"
    code, confidence = lang_pack.detect_language(prompt)
    if code and confidence >= 0.1:
        return code, "detected"
    return "", "auto"


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


def _header_lines(campaign: Path, summary: dict[str, Any], settings: dict[str, Any]) -> list[str]:
    def shown(value: Any) -> str:
        return "?" if value is None or value == "" else _flat(value)

    order = settings.get("persistence_order") or RUNTIME_DEFAULTS["persistence_order"]
    line = (
        f"RePoG capsule — rev {shown(summary.get('revision'))} · day {shown(summary.get('day'))} "
        f"phase {shown(summary.get('phase'))} · {shown(summary.get('location'))} · "
        f"scene {shown(summary.get('scene_id'))} · persistence: {order}"
    )
    lines = [_clip(line, HEADER_CHARS)]
    policy = block_scalars(read_text(campaign / "play_profile.yaml"), "performance").get("cold_distill_policy", "")
    threshold = DISTILL_THRESHOLDS.get(policy)
    turns = summary.get("durable_turns_since_distill")
    if threshold is not None and isinstance(turns, int) and turns >= threshold - 1:
        lines.append("Full distill is due after this turn's commit.")
    return lines


@dataclass(frozen=True)
class _Line:
    key: str  # stable identity inside its block, for line-level deltas ("" for the block's first line)
    text: str
    protected: bool = False
    gone: bool = False  # marks a line the note no longer has
    note: bool = False  # a remark of the capsule's own, never recorded
    prefix: str = ""  # with `items`: the text before them
    items: tuple[str, ...] = ()  # fields shared out again when the line is cut, so each keeps its head

    def cut(self, limit: int) -> str:
        if len(self.text) <= limit:
            return self.text
        if self.items and limit - len(self.prefix) >= MIN_CUT:
            return self.prefix + _share(list(self.items), limit - len(self.prefix))
        return _safe_clip(self.text, limit)


@dataclass(frozen=True)
class _Block:
    key: str
    lines: tuple[_Line, ...]

    def line_key(self, line: _Line) -> str:
        return f"{self.key}|{line.key}"

    @property
    def natural(self) -> int:
        return sum(len(line.text) + 1 for line in self.lines)

    @property
    def minimum(self) -> int:
        return sum(len(line.text) + 1 for line in self.lines if line.protected)


def _core(sections: list[_Section]) -> dict[str, str]:
    for section in sections:
        if section.title.casefold() == "core":
            return {key: value for key, value in ((k, _filled(v)) for k, v in _fields(section.body).items()) if value}
    return {}


def _legacy_lines(note: _Note, sections: list[_Section]) -> list[_Line]:
    lines: list[_Line] = []
    tier = next((_filled(match.group(1)) for match in TIER_RE.finditer(note.text) if _filled(match.group(1))), "")
    if tier:
        lines.append(_Line("Tier", f"  Tier: {_safe_clip(tier, FIELD_CHARS)}"))
    card = next((section for section in sections if "agency card" in section.title.casefold()), None)
    fields = _fields(card.body if card is not None else note.text)
    for label in LEGACY_FIELDS:
        value = _filled(fields.get(label.casefold(), ""))
        if value:
            lines.append(_Line(label, f"  {label}: {_safe_clip(value, FIELD_CHARS)}"))
    return lines


def _state_label(title: str) -> str:
    """A legacy state heading short enough to label a line, keeping its date."""

    title = _flat(title)
    if len(title) <= STATE_LABEL_CHARS:
        return title
    head = QUALIFIER_RE.split(title, maxsplit=1)[0]
    return head if 8 <= len(head) <= STATE_LABEL_CHARS else _clip(title, STATE_LABEL_CHARS)


def _state_text(sections: list[_Section]) -> tuple[str, list[str]]:
    """(label, items) of the note's current state, or ("", []).

    A filled `## Now` wins. Otherwise the newest filled `Current State` /
    `State On Day N` section: the highest number in its heading when every
    such heading has one, else the last. A legacy state keeps its own heading
    as the label, so its date stays visible.
    """

    current = [section for section in sections if section.title.casefold() == "now" and _items(section.body)]
    if current:
        return "Now", _items(current[-1].body)
    legacy = [
        section
        for section in sections
        if LEGACY_STATE_RE.match(section.title.casefold()) and _items(section.body)
    ]
    if not legacy:
        return "", []
    numbers = [[int(number) for number in NUMBER_RE.findall(section.title)] for section in legacy]
    chosen = legacy[-1]
    if all(numbers):
        chosen = legacy[max(range(len(legacy)), key=lambda index: (max(numbers[index]), index))]
    return _state_label(chosen.title), _items(chosen.body)


def _relation_rows(
    member: _Member, rows: list[tuple[list[str], list[str]]], pcs: list[tuple[str, ...]], matcher: _Matcher
) -> list[tuple[str, str]]:
    """(endpoints, detail) for the member's rows with the player character, at most MAX_RELATIONS."""

    names = [name for name in (matcher.tokens(name) for name in member.names) if name]
    found: list[tuple[str, str]] = []
    for columns, cells in rows:
        def cell(name: str) -> str:
            index = columns.index(name) if name in columns else -1
            return cells[index] if 0 <= index < len(cells) else ""

        ends = (matcher.tokens(cell("from")), matcher.tokens(cell("to")))
        mine = [any(_contains(end, name) for name in names) for end in ends]
        theirs = [any(_contains(end, pc) for pc in pcs) for end in ends]
        if not ((mine[0] and theirs[1]) or (theirs[0] and mine[1])):
            continue
        parts = [_safe_clip(cell("relation"), RELATION_CHARS)]
        if "status" in columns:
            parts.append(_safe_clip(cell("status"), RELATION_CHARS))
            following = columns.index("status") + 1
            if following < len(cells):
                parts.append(_head_tail(cells[following], RELATION_CHARS))
        head = " ".join(part for part in (cell("from"), cell("direction"), cell("to")) if part)
        found.append((head, "; ".join(part for part in parts if part)))
        if len(found) == MAX_RELATIONS:
            break
    return found


def _knowledge_entries(kb_sections: list[_Section]) -> list[_Section]:
    """`### Name` blocks under the NPC (and companion or faction) knowledge headings."""

    entries: list[_Section] = []
    for section in kb_sections:
        title = section.title.casefold()
        if section.level == 2 and "knowledge" in title and any(word in title for word in ("npc", "companion", "faction")):
            entries.extend(sub for sub in _sections(section.body) if sub.level == 3)
    return entries


def _knowledge_entry(member: _Member, entries: list[_Section], matcher: _Matcher) -> _Section | None:
    """The member's knowledge block: a heading equal to one of their names, or to one before a qualifier.

    A heading that merely starts with the name ("Tom Ashwick" for a note
    titled "Tom") belongs to someone else.
    """

    names = {matcher.tokens(name) for name in member.names} - {()}
    for entry in entries:
        if matcher.tokens(entry.title) in names:
            return entry
    for entry in entries:
        head = QUALIFIER_RE.split(entry.title.strip(), maxsplit=1)[0]
        if head and matcher.tokens(head) in names:
            return entry
    return None


def _member_block(
    member: _Member,
    *,
    relation_rows: list[tuple[list[str], list[str]]],
    pcs: list[tuple[str, ...]],
    knowledge: list[_Section],
    matcher: _Matcher,
) -> _Block:
    lines: list[_Line] = []
    if member.note is None:
        lines.append(_Line("", f"- {member.name} (no note)", True))
    else:
        note = member.note
        sections = _sections(note.text)
        lines.append(_Line("", f"- {note.title} ({note.path})", True))
        core = _core(sections)
        shown = [label for label in CORE_FIELDS if core.get(label.casefold())]
        for label in shown:
            value = core[label.casefold()]
            limit = KIN_CHARS if label == "Kin" else FIELD_CHARS
            lines.append(_Line(label, f"  {label}: {_safe_clip(value, limit)}", label in PROTECTED_FIELDS))
        if not shown:
            lines.extend(_legacy_lines(note, sections))
        label, now = _state_text(sections)
        if now:
            # Each bullet of a state keeps its head, so a fact in a later
            # bullet ("Her mother: died ...") is not lost behind the first.
            prefix = f"  {label}: "
            lines.append(_Line("Now", prefix + _share(now, NOW_CHARS), prefix=prefix, items=tuple(now)))
    used = {line.key for line in lines}
    for head, detail in _relation_rows(member, relation_rows, pcs, matcher):
        key = f"Rel {head}"
        while key in used:
            key += "+"
        used.add(key)
        lines.append(_Line(key, f"  Rel: {head}: {detail}" if detail else f"  Rel: {head}"))
    entry = _knowledge_entry(member, knowledge, matcher)
    items = tuple(_items(entry.body)) if entry is not None else ()
    if items:
        prefix = "  Knowledge: "
        text = prefix + _share(list(items), KNOWLEDGE_CHARS)
        lines.append(_Line("Knowledge", text, prefix=prefix, items=items))
    return _Block(member.key, tuple(lines))


def _guarded_block(member: _Member, **context: Any) -> _Block:
    """One member's block; a note that fails to read still names the member."""

    try:
        return _member_block(member, **context)
    except Exception:
        where = f" ({member.note.path})" if member.note is not None else ""
        return _Block(member.key, (_Line("", f"- {member.name}{where}", True), _Line("Now", "  (could not be read this turn)")))


def _roster(cast: list[_Member]) -> list[str]:
    if not cast:
        return []
    names = ", ".join(f"{member.name} ({member.via})" for member in cast)
    return [_clip(f"[cast] in scope: {names}", ROSTER_CHARS)]


def _protected_facts(kb_sections: list[_Section], matcher: _Matcher) -> list[tuple[str, tuple[str, ...]]]:
    """(fact id, folded holder words) for every protected entry not yet revealed.

    Facts the player character does not know yet come first, so a line cut
    for size keeps the ids that matter most.
    """

    hidden: list[tuple[str, tuple[str, ...]]] = []
    known: list[tuple[str, tuple[str, ...]]] = []
    seen: set[str] = set()
    for section in kb_sections:
        if section.level != 2 or "protected" not in section.title.casefold():
            continue
        for entry in _sections(section.body):
            if entry.level != 3:
                continue
            fields = _fields(entry.body)
            match = FACT_ID_RE.search(_filled(fields.get("fact id", "")))
            status = fields.get("status", "").strip().strip("`*_ ").casefold()
            if match is None or status.startswith("revealed") or match.group(0) in seen:
                continue
            seen.add(match.group(0))
            holders = " ".join(fields.get(key, "") for key in HOLDER_FIELDS)
            (known if status.startswith(PC_KNOWN_STATUSES) else hidden).append((match.group(0), matcher.tokens(holders)))
    return hidden + known


def _missing_facts(
    member: _Member, facts: list[tuple[str, tuple[str, ...]]], knowledge: list[_Section], matcher: _Matcher
) -> list[str]:
    """Protected fact ids the member does not hold.

    A member holds a fact when its holder list names them (any name form,
    given names included) or when their own knowledge block lists the fact id
    among their confirmed fact ids.
    """

    if not facts:
        return []
    names = matcher.holder_names(member)
    entry = _knowledge_entry(member, knowledge, matcher)
    confirmed = _fields(entry.body).get(CONFIRMED_FIELD, "") if entry is not None else ""
    missing: list[str] = []
    for fact, holders in facts:
        if any(_contains(holders, name) for name in names):
            continue
        if confirmed and re.search(rf"(?<![\w-]){re.escape(fact)}(?![\w-])", confirmed):
            continue
        missing.append(fact)
    return missing


def _secret_line(name: str, facts: list[str], limit: int) -> str:
    """`- Name: not a holder of F-1, F-2 (+N more)` within `limit`, whole ids only; "" when none fits."""

    if not facts:
        line = f"- {name}: nothing to guard."
        return line if len(line) <= limit else ""
    head = f"- {name}: not a holder of "
    shown = facts[:MAX_SECRET_IDS]
    for count in range(len(shown), 0, -1):
        more = len(facts) - count
        line = head + ", ".join(shown[:count]) + (f" (+{more} more)" if more else "")
        if len(line) <= limit:
            return line
    return ""


def _secrets_piece(items: list[tuple[str, str, list[str]]], cap: int) -> tuple[list[str], list[str]]:
    """The secrets section within `cap` and the keys of the member lines it shows."""

    lines = ["[secrets]"]
    used = len(lines[0])
    shown: list[str] = []
    for key, name, facts in items:
        line = _secret_line(name, facts, cap - used - 1)
        if not line:
            break
        lines.append(line)
        used += len(line) + 1
        shown.append(key)
    return (lines if shown else []), shown


def _directive_applies(scope_text: str, scene: str, scope: _Scope, matcher: _Matcher) -> bool:
    """True for `global`, `scene:<current scene id>`, or `entity:<a name in scope>`."""

    kind, _, value = scope_text.partition(":")
    kind, value = kind.strip().casefold(), _flat(value)
    if not value:
        return kind == "global"
    if kind == "scene":
        return bool(scene) and lang_pack.fold(value, matcher.pack) == scene
    if kind == "entity":
        return matcher.tokens(value) in scope.entity_names
    return False


def _directive_lines(campaign: Path, summary: dict[str, Any], scope: _Scope, matcher: _Matcher) -> list[str]:
    """Active directives in scope, newest first (rows are appended, so the last row is newest)."""

    scene = lang_pack.fold(_flat(summary.get("scene_id") or ""), matcher.pack)
    lines: list[str] = []
    for row in reversed(curation.active_directives(campaign)):
        if not _directive_applies(row["scope"], scene, scope, matcher):
            continue
        lines.append(f"- {row['id']} ({_flat(row['scope'])}): {_flat(row['directive'])}")
        if len(lines) == MAX_DIRECTIVES:
            break
    return ["[directives]", *lines] if lines else []


def _glossary_lines(campaign: Path) -> list[str]:
    fields = _fields(_read_md(campaign / "glossary.md"))
    lines: list[str] = []
    for label in GLOSSARY_FIELDS:
        value = _filled(fields.get(label.casefold(), ""))
        if value:
            lines.append(_clip(f"{label}: {_flat(value)}", GLOSSARY_CHARS))
    return lines


def _language_lines(campaign: Path, code: str, source: str, pack: dict[str, Any]) -> list[str]:
    lines = [f"[language] {code} ({source})" if code else "[language] auto (not detected yet)"]
    card = _flat(pack.get("card", "")) if code else ""
    if card:
        lines.append(_clip(card, CARD_CHARS))
    return lines + _glossary_lines(campaign)


def _lint_lines(lint: dict[str, Any], settings: dict[str, Any]) -> tuple[list[str], str]:
    """The lint section and its change basis: the whole finding record, so a new reply re-shows it."""

    summary = lint.get("summary")
    if settings.get("presentation_lint") == "off" or not isinstance(summary, str) or not summary.strip():
        return [], ""
    return [f"[lint] {_clip(_flat(summary), LINT_CHARS)}"], json.dumps(lint, sort_keys=True, ensure_ascii=False)


def _roll_lines(campaign: Path, revision: Any) -> list[str]:
    if type(revision) is not int:
        return []
    try:
        receipts = roll_dice.open_receipts(campaign, revision)
    except (roll_dice.RollCallError, OSError, ValueError):
        return ["[rolls] the roll receipt store could not be read."]
    lines: list[str] = []
    for receipt in receipts[:MAX_ROLLS]:
        call = receipt.get("call") if isinstance(receipt.get("call"), dict) else {}
        what = " ".join(_flat(call.get(key, "?")) for key in ("actor", "axis"))
        lines.append(
            f"- roll {_flat(receipt.get('roll_id', '?'))} ({what} vs {_flat(call.get('difficulty', '?'))}): "
            f"{_flat(receipt.get('band', '?'))}, not yet committed"
        )
    if len(receipts) > MAX_ROLLS:
        lines.append(f"- +{len(receipts) - MAX_ROLLS} more open receipts")
    return ["[rolls]", *lines] if lines else []


def _curation_lines(campaign: Path) -> list[str]:
    ids = [path.stem for path in curation.list_staged(campaign)]
    if not ids:
        return []
    more = f" (+{len(ids) - MAX_STAGED} more)" if len(ids) > MAX_STAGED else ""
    return [f"[curation] staged, waiting to be applied: {', '.join(ids[:MAX_STAGED])}{more}"]


def _guarded(key: str, render: Callable[[], list[str]]) -> list[str]:
    """One section, isolated: a section that fails to read becomes a one-line notice.

    The capsule runs inside a prompt hook, so one unreadable owner must not
    cost the GM the rest of the briefing.
    """

    try:
        return render()
    except Exception:
        return [f"[{key}] could not be read this turn."]


# ---------------------------------------------------------------------------
# Deltas and the size budget for the cast
# ---------------------------------------------------------------------------


def _delta_blocks(blocks: list[_Block], line_hashes: dict[str, str], previous: dict[str, str]) -> list[_Block]:
    """What each block shows in a delta, or nothing when it is unchanged since last shown.

    A block shown before in this session repeats only its first line, its
    protected lines, its changed lines, and a marker for each line the note no
    longer has; a block not shown before (or renamed) is shown whole.
    """

    shown: list[_Block] = []
    for block in blocks:
        keys = {block.line_key(line) for line in block.lines}
        changed = [line for line in block.lines if previous.get(block.line_key(line)) != line_hashes[block.line_key(line)]]
        prefix = f"{block.key}|"
        gone = [
            _Line(key[len(prefix) :], f"  {key[len(prefix) :] or 'Entry'}: {GONE_NOTE}", gone=True)
            for key in sorted(previous)
            if key.startswith(prefix) and key not in keys
        ]
        if not changed and not gone:
            continue
        first = block.lines[0]
        if first in changed:
            shown.append(_Block(block.key, (*block.lines, *gone)))
            continue
        partial = _Line(first.key, first.text + PARTIAL_NOTE, True)
        rest = [line for line in block.lines[1:] if line.protected or line in changed]
        shown.append(_Block(block.key, (partial, *rest, *gone)))
    return shown


def _fit_block(block: _Block, budget: int, *, cut: bool) -> list[tuple[_Line, str]]:
    """Fit a block into `budget`; protected lines are never cut or dropped.

    With `cut` (a full capsule, which must brief everyone at once) the other
    lines share what is left the way `_share` shares a line's fields: short
    lines whole, long ones cut to an even share of at least MIN_SHARE, so the
    current state, the relation to the player character, and the knowledge
    each keep their head; past that, lines are dropped from the bottom.
    Without `cut` (a delta) a line is shown whole or waits for the next
    prompt, so no qualifier is cut away. A line left out is not recorded as
    shown, and the next delta carries it; a note says how many wait.
    """

    if block.natural <= budget:
        return [(line, line.text) for line in block.lines]
    room = budget - block.minimum
    texts: dict[int, str] = {}
    loose = [index for index, line in enumerate(block.lines) if not line.protected]
    if cut:
        shares: list[int] = []
        while loose:
            shares = _water([len(block.lines[index].text) for index in loose], room - len(loose))
            if all(share >= min(len(block.lines[index].text), MIN_SHARE) for share, index in zip(shares, loose)):
                break
            loose.pop()
        texts = {index: block.lines[index].cut(share) for index, share in zip(loose, shares)}
    else:
        for index in loose:
            size = len(block.lines[index].text) + 1
            if size <= room:
                texts[index] = block.lines[index].text
                room -= size
    kept = [
        (line, line.text if line.protected else texts[index])
        for index, line in enumerate(block.lines)
        if line.protected or index in texts
    ]
    waiting = len(block.lines) - len(kept)
    note = WAIT_NOTE.format(count=waiting)
    if waiting and sum(len(text) + 1 for _, text in kept) + len(note) + 1 <= budget:
        kept.append((_Line("", note, note=True), note))
    return kept


def _allocate(blocks: list[_Block], budget: int, *, cut: bool) -> list[int]:
    """Budgets for the leading blocks whose protected lines fit; the rest wait.

    Every admitted block first gets its protected minimum. With `cut` the
    remaining room is shared out so that small blocks are shown whole and
    large ones split what is left evenly. Without it (a delta, where lines are
    shown whole or wait) the room goes to the blocks in scope order, so the
    first ones are completed and the rest follow on later prompts instead of
    every block waiting at once.
    """

    count, spent = 0, 0
    for block in blocks:
        if spent + block.minimum > budget:
            break
        spent += block.minimum
        count += 1
    wants = [block.natural - block.minimum for block in blocks[:count]]
    extra = budget - spent
    if cut:
        gives = _water(wants, extra)
    else:
        gives = []
        for want in wants:
            gives.append(min(want, max(0, extra)))
            extra -= gives[-1]
    return [block.minimum + give for block, give in zip(blocks[:count], gives)]


def _cast_lines(
    roster: list[str], blocks: list[_Block], budget: int, *, cut: bool
) -> tuple[list[str], list[str], list[str]]:
    """The cast section within `budget`, the line keys it shows, and the gone-line keys it shows.

    A block whose protected lines do not fit waits whole; a line left out is
    not recorded as shown, so a later delta carries it.
    """

    lines = _fit_lines(roster, max(0, min(budget, ROSTER_CHARS)))
    room = budget - sum(len(line) + 1 for line in lines)
    allotted = _allocate(blocks, room, cut=cut)
    if len(allotted) < len(blocks):
        allotted = _allocate(blocks, room - len(DEFER_NOTE) - 1, cut=cut)
    shown: list[str] = []
    gone: list[str] = []
    for block, share in zip(blocks, allotted):
        for line, text in _fit_block(block, share, cut=cut):
            lines.append(text)
            if not line.note:
                (gone if line.gone else shown).append(block.line_key(line))
    deferred = len(blocks) - len(allotted)
    note = DEFER_NOTE.format(count=deferred)
    if deferred and sum(len(line) + 1 for line in lines) + len(note) + 1 <= budget:
        lines.append(note)
    return lines, shown, gone


# ---------------------------------------------------------------------------
# Capsule state and remembered reply names
# ---------------------------------------------------------------------------


def _state_path(campaign: Path) -> Path:
    return campaign / RUNTIME_DIR / STATE_FILE


def _names_path(campaign: Path) -> Path:
    return campaign / RUNTIME_DIR / NAMES_FILE


def _load_sessions(path: Path, version: int) -> dict[str, Any]:
    data = read_json(path, None)
    if not isinstance(data, dict) or data.get("version") != version or not isinstance(data.get("sessions"), dict):
        return {"version": version, "seq": 0, "sessions": {}}
    sessions = {key: value for key, value in data["sessions"].items() if isinstance(key, str) and isinstance(value, dict)}
    return {"version": version, "seq": _int(data.get("seq")), "sessions": sessions}


def _load_state(campaign: Path) -> dict[str, Any]:
    return _load_sessions(_state_path(campaign), STATE_VERSION)


def _touch(state: dict[str, Any], session_id: str) -> dict[str, Any]:
    """The session's entry, created if needed, marked as the most recently used."""

    state["seq"] = _int(state.get("seq")) + 1
    entry = state["sessions"].setdefault(session_id, {})
    entry["seq"] = state["seq"]
    return entry


def _save_sessions(path: Path, state: dict[str, Any]) -> None:
    sessions = state["sessions"]
    if len(sessions) > MAX_SESSIONS:
        newest = sorted(sessions, key=lambda key: _int(sessions[key].get("seq")), reverse=True)[:MAX_SESSIONS]
        state["sessions"] = {key: value for key, value in sessions.items() if key in newest}
    for attempt in range(3):
        try:
            write_json_atomic(path, state)
            return
        except PermissionError:
            # Windows refuses the replace while the other hook is reading the file.
            if attempt == 2:
                raise
            time.sleep(0.05 * (attempt + 1))


def _save_state(campaign: Path, state: dict[str, Any]) -> None:
    _save_sessions(_state_path(campaign), state)


def _clean_names(names: Iterable[Any]) -> list[str]:
    cleaned: dict[str, str] = {}
    for name in names:
        if not isinstance(name, str):
            continue
        text = _flat(name)
        if text and len(text) <= MAX_NAME_CHARS:
            cleaned.setdefault(text.casefold(), text)
    return list(cleaned.values())


def _batches(entry: dict[str, Any]) -> list[tuple[int, list[str]]]:
    raw = entry.get("batches")
    batches: list[tuple[int, list[str]]] = []
    for batch in raw if isinstance(raw, list) else []:
        if isinstance(batch, dict) and _int(batch.get("n")) and isinstance(batch.get("names"), list):
            batches.append((_int(batch["n"]), _clean_names(batch["names"])))
    return batches


def _reply_names(campaign: Path, session_id: str, entry: dict[str, Any]) -> tuple[list[str], int]:
    """Names from replies this session's capsule has not used yet, and the newest reply number."""

    batches = _batches(_load_sessions(_names_path(campaign), NAMES_VERSION)["sessions"].get(session_id, {}))
    newest = max((number for number, _ in batches), default=0)
    seen = _int(entry.get("reply_seen"))
    if newest < seen:
        seen = 0  # the names file was deleted since; its numbering started again
    names = _clean_names(name for number, names in batches if number > seen for name in names)
    return names[-MAX_REMEMBERED:], newest


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------


def _full_reason(entry: dict[str, Any], scene_id: str, full: bool | None) -> str | None:
    """Why this prompt gets a full capsule, or None for a delta."""

    if full is not None:
        return "requested" if full else None
    if not _int(entry.get("prompts")):
        return "first prompt"
    if entry.get("reset"):
        return "reset"
    if str(entry.get("scene_id") or "") != scene_id:
        return "scene change"
    if _int(entry.get("since_full")) + 1 >= FULL_EVERY:
        return "periodic"
    return None


def compose(
    campaign: Path, prompt: str, *, session_id: str, settings: dict[str, Any], full: bool | None = None
) -> tuple[str, dict[str, Any]]:
    """The capsule text and the capsule state that records it, without writing anything."""

    campaign = Path(campaign)
    prompt = prompt if isinstance(prompt, str) else ""
    settings = settings if isinstance(settings, dict) else {}
    session_id = str(session_id or "default")
    state = _load_state(campaign)
    entry = state["sessions"].get(session_id, {})
    reply_names, reply_number = _reply_names(campaign, session_id, entry)
    summary = state_summary(campaign)
    lint = _lint_data(campaign)
    code, source = _language(settings, prompt, entry, lint)
    pack = lang_pack.load_pack(code)
    matcher = _Matcher(_load_notes(campaign), pack, [summary.get("player_name") or ""])
    scope = _scope(summary, prompt, [*_remembered(entry), *reply_names], matcher)

    kb_sections = _sections(_read_md(campaign / "knowledge_boundaries.md"))
    relation_rows = _tables(_read_md(campaign / "relationship_map.md"), {"from", "to", "relation"})
    pcs = [tokens for tokens in (matcher.tokens(name) for name in (summary.get("player_name") or "", "PC")) if tokens]
    knowledge = _knowledge_entries(kb_sections)
    blocks = [
        _guarded_block(member, relation_rows=relation_rows, pcs=pcs, knowledge=knowledge, matcher=matcher)
        for member in scope.cast
    ]
    roster = _roster(scope.cast)
    facts = _protected_facts(kb_sections, matcher)
    secrets = [
        (f"secrets:{member.key[len('cast:') :]}", member.name, _missing_facts(member, facts, knowledge, matcher))
        for member in scope.cast
    ]
    lint_lines, lint_basis = _lint_lines(lint, settings)
    rendered: dict[str, list[str]] = {
        "directives": _guarded("directives", lambda: _directive_lines(campaign, summary, scope, matcher)),
        "language": _language_lines(campaign, code, source, pack),
        "lint": lint_lines,
        "rolls": _guarded("rolls", lambda: _roll_lines(campaign, summary.get("revision"))),
        "curation": _guarded("curation", lambda: _curation_lines(campaign)),
    }
    section_hashes = {key: _digest("\n".join(lines)) for key, lines in rendered.items()}
    section_hashes["lint"] = _digest(lint_basis)
    section_hashes["cast"] = _digest("\n".join(roster))
    secret_hashes = {key: _digest(", ".join(missing)) for key, _, missing in secrets}
    line_hashes = {block.line_key(line): _digest(line.text) for block in blocks for line in block.lines}

    scene_id = _flat(summary.get("scene_id") or "")
    number = _int(entry.get("prompts")) + 1
    is_full = _full_reason(entry, scene_id, full) is not None
    # After a reset (or on a session's first prompt) the context holds no
    # earlier capsule, so nothing counts as shown. Otherwise what an earlier
    # capsule showed stays in context: a full capsule re-shows the scene but
    # keeps those records, and a person who leaves scope and returns
    # unchanged is not shown again while their lines are under FULL_EVERY
    # prompts old. Older records expire, which also bounds the state file.
    fresh = not _int(entry.get("prompts")) or bool(entry.get("reset"))
    old_hashes = entry.get("hashes") if isinstance(entry.get("hashes"), dict) and not fresh else {}
    old_seen = entry.get("seen") if isinstance(entry.get("seen"), dict) and not fresh else {}
    expired = {
        key for key in old_hashes if key.startswith(_PER_PROMPT) and not number - FULL_EVERY < _int(old_seen.get(key)) < number
    }
    # A person whose oldest line has expired is briefed again whole, not as "changed lines".
    stale = {key.split("|", 1)[0] for key in expired if "|" in key}
    expired.update(key for key in old_hashes if key.split("|", 1)[0] in stale)
    recorded: dict[str, Any] = {key: value for key, value in old_hashes.items() if key not in expired}
    seen: dict[str, int] = {key: _int(old_seen[key]) for key in recorded if key in old_seen}
    previous: dict[str, Any] = {} if is_full else dict(recorded)
    if is_full:
        # What this capsule shows of the people in scope replaces their records.
        current = tuple(f"{block.key}|" for block in blocks) + tuple(key for key, _, _ in secrets)
        for key in [key for key in recorded if key.startswith(current)]:
            del recorded[key]
            seen.pop(key, None)
    caps = CAPS[is_full]
    limit = FULL_MAX if is_full else DELTA_MAX

    def shown(keys: Iterable[str], hashes: dict[str, str]) -> None:
        for key in keys:
            recorded[key] = hashes[key]
            seen[key] = number

    pieces: dict[str, list[str]] = {}
    secret_items: list[tuple[str, str, list[str]]] = []
    for key, name, missing in secrets:
        before = previous.get(key)
        if before == secret_hashes[key]:
            continue
        if not missing and before in (None, _EMPTY_HASH):
            shown([key], secret_hashes)  # nothing to guard, and nothing shown that needs clearing
            continue
        secret_items.append((key, name, missing))
    if secret_items:
        if not is_full and not any(missing for _, _, missing in secrets):
            secret_lines, shown_secrets = [CLEARED["secrets"]], [key for key, _, _ in secret_items]
        else:
            secret_lines, shown_secrets = _secrets_piece(secret_items, caps["secrets"])
        if secret_lines:
            pieces["secrets"] = secret_lines
        shown(shown_secrets, secret_hashes)
    for key in ("directives", "language", "lint", "rolls", "curation"):
        lines = rendered[key]
        before = previous.get(key)
        if before == section_hashes[key]:
            continue
        if lines:
            pieces[key] = _fit_lines(lines, caps[key])
        elif before not in (None, _EMPTY_HASH):
            pieces[key] = [CLEARED[key]]
        recorded[key] = section_hashes[key]

    cast_blocks = blocks if is_full else _delta_blocks(blocks, line_hashes, previous)
    roster_changed = previous.get("cast") != section_hashes["cast"]
    show_cast = is_full or bool(cast_blocks) or (roster_changed and (bool(roster) or previous.get("cast") is not None))
    roster_lines = roster or ([CLEARED["cast"]] if show_cast and not is_full else [])

    header = _header_lines(campaign, summary, settings)
    if not is_full:
        emitted = [key for key in SECTION_ORDER if key in pieces or (key == "cast" and show_cast)]
        header.append(
            f"Delta: {', '.join(emitted)} changed; other sections are as last shown."
            if emitted
            else "Delta: nothing changed since the last capsule."
        )
    header = _fit_lines(header, caps["header"])
    used = sum(len(line) + 1 for line in header) + sum(len(line) + 1 for lines in pieces.values() for line in lines)
    cast: list[str] = []
    if show_cast:
        cast, shown_lines, gone_lines = _cast_lines(
            roster_lines, cast_blocks, min(caps["cast"], limit - used), cut=is_full
        )
        if not roster_lines or cast[:1] == roster_lines[:1]:
            recorded["cast"] = section_hashes["cast"]
        shown(shown_lines, line_hashes)
        for key in gone_lines:
            recorded.pop(key, None)
            seen.pop(key, None)
    body = [*header, *cast]
    for key in SECTION_ORDER:
        body.extend(pieces.get(key, []))
    text = _clip("\n".join(line for line in body if line), limit)

    new_state = json.loads(json.dumps(state))
    new_entry = _touch(new_state, session_id)
    new_entry.update(
        {
            "prompts": number,
            "since_full": 0 if is_full else _int(entry.get("since_full")) + 1,
            "scene_id": scene_id,
            "reset": False,
            "hashes": recorded,
            "seen": seen,
            "names": scope.mentioned[:MAX_REMEMBERED],
            "reply_seen": reply_number,
        }
    )
    if code and source == "detected":
        new_entry["language"] = code
    return text, new_state


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_capsule(
    campaign: Path, prompt: str, *, session_id: str, settings: dict[str, Any], full: bool | None = None
) -> str:
    """Build this prompt's capsule and record it for the session's next delta.

    `full=None` chooses full or delta by the session's history; True or False
    forces one. A runtime folder that cannot be written only means the next
    prompt gets a full capsule again.
    """

    text, state = compose(campaign, prompt, session_id=session_id, settings=settings, full=full)
    if Path(campaign).is_dir():
        try:
            _save_state(Path(campaign), state)
        except OSError:
            pass
    return text


def run_hook(event: dict[str, Any]) -> str:
    """The capsule for one UserPromptSubmit event, or "" when skipped. Never raises."""

    try:
        if not isinstance(event, dict):
            return ""
        cwd = event.get("cwd")
        campaign = find_campaign(cwd if isinstance(cwd, str) and cwd else None)
        if campaign is None or not is_ready_rpg(campaign):
            return ""
        settings = runtime_settings(campaign)
        if settings.get("scene_capsule") != "on":
            return ""
        prompt = event.get("prompt")
        session_id = event.get("session_id")
        return build_capsule(
            campaign,
            prompt if isinstance(prompt, str) else "",
            session_id=session_id if isinstance(session_id, str) and session_id else "default",
            settings=settings,
        )
    except Exception:
        return ""


def reset(campaign: Path, session_id: str | None = None) -> None:
    """Mark one session, or every recorded session, for a full capsule on its next prompt.

    A session with no record gets a full capsule on its first prompt anyway,
    so nothing is written for it. Raises OSError only when the runtime folder
    cannot be written.
    """

    campaign = Path(campaign)
    if not campaign.is_dir():
        return
    state = _load_state(campaign)
    sessions = state["sessions"]
    targets = list(sessions) if session_id is None else [key for key in (str(session_id),) if key in sessions]
    if not targets:
        return
    for key in targets:
        sessions[key]["reset"] = True
    _save_state(campaign, state)


def remember_names(campaign: Path, session_id: str, names: Iterable[str]) -> None:
    """Add names (for example those in the last reply) to the session's next scope.

    Remembered names are note titles or aliases; the next capsule resolves them
    to notes, so a name carries over one prompt. They are kept in their own
    file, which only this function writes: the Stop hook that calls it runs
    asynchronously and must never overwrite the capsule state a prompt or a
    reset has just written. Raises OSError only when the runtime folder cannot
    be written.
    """

    campaign = Path(campaign)
    cleaned = _clean_names(names)[:MAX_REMEMBERED]
    if not cleaned or not campaign.is_dir():
        return
    path = _names_path(campaign)
    data = _load_sessions(path, NAMES_VERSION)
    entry = _touch(data, str(session_id or "default"))
    number = _int(entry.get("count")) + 1
    batches = [{"n": n, "names": batch} for n, batch in _batches(entry)][-(MAX_REPLY_BATCHES - 1) :]
    entry.update({"count": number, "batches": [*batches, {"n": number, "names": cleaned}]})
    _save_sessions(path, data)


def names_in_text(campaign: Path, text: str, *, settings: dict[str, Any] | None = None) -> list[str]:
    """Titles of the character, place, and faction notes named in `text` (e.g. a reply)."""

    campaign = Path(campaign)
    settings = runtime_settings(campaign) if settings is None else settings
    code, _ = _language(settings, text, {}, _lint_data(campaign))
    player = state_summary(campaign).get("player_name") or ""
    matcher = _Matcher(_load_notes(campaign), lang_pack.load_pack(code), [player])
    return list(dict.fromkeys(note.title for note in matcher.scan(text)))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _campaign_arg(value: str) -> Path:
    base = Path(value)
    nested = base / "campaign"
    return nested if (nested / "current_state.yaml").is_file() else base


def _write_json(value: dict[str, Any]) -> None:
    sys.stdout.buffer.write((json.dumps(value, ensure_ascii=True) + "\n").encode("ascii"))
    sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("hook", help="read a UserPromptSubmit event on stdin and print {\"text\": ...}")
    reset_parser = commands.add_parser("reset", help="mark a session (default: every session) for a full capsule")
    reset_parser.add_argument("--session", default=None, help="session id; omit to reset every session")
    reset_parser.add_argument("campaign", help="campaign folder (or the project folder that holds campaign/)")
    show = commands.add_parser("show", help="print the next capsule as UTF-8 text without recording it")
    show.add_argument("campaign", help="campaign folder (or the project folder that holds campaign/)")
    show.add_argument("--full", action="store_true", help="force a full capsule")
    show.add_argument("--prompt", default="", help="the Player prompt to match names in")
    show.add_argument("--session", default="show", help="session id whose history decides full or delta")
    args = parser.parse_args(argv)

    if args.command == "hook":
        try:
            event = json.loads(sys.stdin.buffer.read().decode("utf-8-sig") or "{}")
        except Exception:
            event = {}
        _write_json({"text": run_hook(event if isinstance(event, dict) else {})})
        return 0
    campaign = _campaign_arg(args.campaign)
    if not (campaign / "current_state.yaml").is_file():
        _write_json({"ok": False, "failure_reason": f"no RePoG campaign (current_state.yaml) at {campaign}"})
        return 2
    if args.command == "reset":
        try:
            reset(campaign, args.session)
        except OSError as exc:
            _write_json({"ok": False, "failure_reason": f"cannot write the capsule state: {exc}"})
            return 2
        _write_json({"ok": True, "session": args.session})
        return 0
    text, _ = compose(
        campaign, args.prompt, session_id=args.session, settings=runtime_settings(campaign), full=True if args.full else None
    )
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())

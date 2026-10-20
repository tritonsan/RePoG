"""Warn when a new character name will be easy to misread or confuse in play.

Long sessions showed two failure shapes: a name that is also a common word
("Kara" reads as "black" in Turkish prose) and two names one letter apart
(Corran/Corlan, Hilda/Hilde) that the narrator later swaps. This module only
compares spellings, folded with the play language's pack; it never judges
whether a name fits the setting. Every finding is advisory.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from typing import Any

from lang_pack import load_pack, words


WARNING = "warning"
INFO = "info"
# Names are short; these caps keep a runaway title (a pasted paragraph) from
# turning the pairwise edit-distance checks into minutes of work.
MAX_NAME_WORDS = 8
MAX_WORD_LENGTH = 40
MAX_SHOWN = 80


def levenshtein(a: str, b: str) -> int:
    """Edit distance: insertions, deletions and substitutions each cost 1."""

    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for row, left in enumerate(a, start=1):
        current = [row]
        for column, right in enumerate(b, start=1):
            current.append(min(previous[column] + 1, current[column - 1] + 1, previous[column - 1] + (left != right)))
        previous = current
    return previous[-1]


def _max_distance(length: int) -> int:
    if length >= 7:
        return 2
    if length >= 4:
        return 1
    return 0


def _one_letter_apart(a: str, b: str) -> bool:
    """Same opening, same letters but one: Halvar/Harlan, Marlen/Mantel.

    Edit distance misses these (Halvar to Harlan is 3), yet a reader sees the
    same shape. Applies to single words of five or more letters.
    """

    if min(len(a), len(b)) < 5 or abs(len(a) - len(b)) > 1 or a[:2] != b[:2]:
        return False
    left, right = Counter(a), Counter(b)
    return sum((left - right).values()) <= 1 and sum((right - left).values()) <= 1


def _confusable(a: str, b: str) -> str | None:
    """Why two folded spellings are easy to confuse, or None."""

    limit = _max_distance(min(len(a), len(b)))
    if abs(len(a) - len(b)) <= limit:  # otherwise the distance cannot be within the limit
        distance = levenshtein(a, b)
        if 0 < distance <= limit:
            return f"{distance} letter{'s' if distance > 1 else ''} apart"
    if " " not in a and " " not in b and _one_letter_apart(a, b):
        return "the same letters but one"
    return None


def _name_words(name: Any, pack: dict[str, Any]) -> list[str]:
    return [word[:MAX_WORD_LENGTH] for word in words(name if isinstance(name, str) else "", pack)[:MAX_NAME_WORDS]]


def _shown(name: str) -> str:
    return name if len(name) <= MAX_SHOWN else name[: MAX_SHOWN - 1] + "…"


def _names(existing: Any) -> list[str]:
    """`existing` as a list of names: a lone string is one name, junk is none."""

    if isinstance(existing, str):
        return [existing]
    if isinstance(existing, (list, tuple, set, frozenset)):
        return [item for item in existing if isinstance(item, str)]
    return []


def _duplicate_reason(new_words: list[str], other_words: list[str]) -> str | None:
    """Why two names (as folded words) read as the same or nearly the same name.

    Words the names share (a surname, a title) are set aside, so "Jo Ironhand"
    and "Al Ironhand" differ only by "jo"/"al" and pass, while "Sir Corran"
    and "Sir Corlan" are compared as "corran"/"corlan". A name whose every word
    is part of the other ("Edric" and "Edric Vale") may be the same character.
    """

    if new_words == other_words:
        return "same"
    shared = set(new_words) & set(other_words)
    new_rest = [word for word in new_words if word not in shared]
    other_rest = [word for word in other_words if word not in shared]
    if not new_rest and not other_rest:
        return "same words"
    if not new_rest or not other_rest:
        return "part"
    pairs = [(" ".join(new_rest), " ".join(other_rest))]
    pairs.extend(
        (left, right)
        for left in new_rest
        for right in other_rest
        if min(len(left), len(right)) >= 4 and (left, right) != pairs[0]
    )
    return next((found for found in (_confusable(left, right) for left, right in pairs) if found), None)


def _duplicate_message(name: str, other: str, reason: str) -> str:
    shown, other_shown = _shown(name), _shown(other)
    if reason == "same":
        return f'"{shown}" is the same name as "{other_shown}".'
    if reason == "same words":
        return f'"{shown}" uses the same words as "{other_shown}".'
    if reason == "part":
        return f'"{shown}" and "{other_shown}" share a whole name; they may be the same character.'
    return f'"{shown}" is easy to confuse with "{other_shown}" ({reason}).'


def _finding(rule: str, level: str, message: str, match: str) -> dict[str, str]:
    return {"rule": rule, "level": level, "message": message, "match": match}


def check_name(name: str, existing: list[str], pack: dict[str, Any] | None) -> list[dict[str, str]]:
    """Advisory findings for a new name against existing names and the pack.

    Rules: `name_common_word` (a word of the name equals a pack common word),
    `name_near_duplicate` (once shared words such as a surname or title are set
    aside, the rest of the names, or two of their words, are within
    Levenshtein 1 for four or more letters and 2 for seven or more, or share
    all letters but one; also identical names and a name contained in the
    other), and `name_same_initial_sound` (info only: first words share their
    first three letters and differ in length by at most one). Warnings come
    before info; findings follow the order of `existing`.
    """

    pack = pack if isinstance(pack, dict) else {}
    new_words = _name_words(name, pack)
    if not new_words:
        return []
    findings: list[dict[str, str]] = []
    language = str(pack.get("name") or pack.get("code") or "the play language")

    common = {" ".join(words(word, pack)) for word in pack.get("common_words", []) if isinstance(word, str)}
    for word in dict.fromkeys(new_words):
        if word in common:
            findings.append(
                _finding(
                    "name_common_word",
                    WARNING,
                    f'"{_shown(name)}" contains "{word}", a common word in {language}; prose may read it as the word.',
                    word,
                )
            )

    infos: list[dict[str, str]] = []
    seen: set[str] = set()
    for other in _names(existing):
        other_words = _name_words(other, pack)
        key = " ".join(other_words)
        if not other_words or key in seen:
            continue
        seen.add(key)
        reason = _duplicate_reason(new_words, other_words)
        if reason:
            findings.append(_finding("name_near_duplicate", WARNING, _duplicate_message(name, other, reason), other))
            continue
        first, other_first = new_words[0], other_words[0]
        if min(len(first), len(other_first)) >= 3 and first[:3] == other_first[:3] and abs(len(first) - len(other_first)) <= 1:
            infos.append(
                _finding(
                    "name_same_initial_sound",
                    INFO,
                    f'"{_shown(name)}" starts like "{_shown(other)}"; readers may mix them up when both appear.',
                    other,
                )
            )
    return findings + infos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name")
    parser.add_argument("--existing", nargs="*", default=[])
    parser.add_argument("--language", default="en", help="language pack code, e.g. tr, en, de")
    args = parser.parse_args(argv)
    result = {"warnings": check_name(args.name, args.existing, load_pack(args.language))}
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

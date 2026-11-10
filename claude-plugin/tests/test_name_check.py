"""Name check: common-word and near-duplicate warnings for new character names."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import name_check
from lang_pack import load_pack
from name_check import check_name, levenshtein


EN = load_pack("en")
TR = load_pack("tr")


def _rules(findings: list[dict]) -> list[str]:
    return [finding["rule"] for finding in findings]


@pytest.mark.parametrize(
    ("left", "right", "distance"),
    [
        ("", "", 0),
        ("", "abc", 3),
        ("kitten", "sitting", 3),
        ("corran", "corlan", 1),
        ("halvar", "harlan", 3),
        ("hilda", "hilde", 1),
        ("annabelle", "anabella", 2),
        ("ışık", "isik", 3),
    ],
)
def test_levenshtein(left: str, right: str, distance: int) -> None:
    assert levenshtein(left, right) == distance
    assert levenshtein(right, left) == distance


@pytest.mark.parametrize(
    ("name", "other"),
    [
        ("Corran", "Corlan"),
        ("Halvar", "Harlan"),
        ("Hilda", "Hilde"),
        ("HILDA", "hilde"),
        ("Annabelle", "Anabella"),
        ("Rosalind", "Rosamund"),
        ("Sir Corran", "Sir Corlan"),
        ("Harlan Voss", "Halvar Ironhand"),
    ],
)
def test_near_duplicates_are_warned(name: str, other: str) -> None:
    findings = check_name(name, ["Witness", other], EN)
    assert findings == [
        {
            "rule": "name_near_duplicate",
            "level": "warning",
            "message": findings[0]["message"],
            "match": other,
        }
    ]
    assert name in findings[0]["message"] and other in findings[0]["message"]


@pytest.mark.parametrize(
    ("name", "other"),
    [
        ("Mira", "Nora"),  # two letters apart at four letters
        ("Edric", "Garrick"),
        ("Selim", "Siyem"),  # different openings
        ("Edric Vale", "Mara Vale"),  # a shared surname is kin, not a collision
    ],
)
def test_distinct_names_pass(name: str, other: str) -> None:
    assert check_name(name, [other], EN) == []


def test_identical_name_is_reported_once() -> None:
    findings = check_name("Edric", ["Edric", "EDRIC", "Mara"], EN)
    assert _rules(findings) == ["name_near_duplicate"]
    assert "same name" in findings[0]["message"]


def test_common_words_use_the_language_fold() -> None:
    findings = check_name("Kara Ayşe", [], TR)
    assert findings == [
        {
            "rule": "name_common_word",
            "level": "warning",
            "message": findings[0]["message"],
            "match": "kara",
        }
    ]
    assert _rules(check_name("IŞIK", [], TR)) == ["name_common_word"]  # folds to "ışık", not "isik"
    assert check_name("Tamara", [], TR) == []
    assert check_name("Nurhan", [], TR) == []
    assert _rules(check_name("Will Turner", [], EN)) == ["name_common_word"]
    assert check_name("Kara", [], EN) == []  # common in Turkish, not in English


def test_same_initial_sound_is_info_only() -> None:
    findings = check_name("Corwin", ["Cormac", "Mara"], EN)
    assert findings == [
        {
            "rule": "name_same_initial_sound",
            "level": "info",
            "message": findings[0]["message"],
            "match": "Cormac",
        }
    ]
    assert check_name("Corwin", ["Cornelius"], EN) == []  # lengths differ by more than one
    assert _rules(check_name("Ann", ["Anne"], EN)) == ["name_same_initial_sound"]  # too short for a distance warning


def test_warnings_come_before_info() -> None:
    findings = check_name("Kara", ["Karim", "Kare"], TR)
    assert _rules(findings) == ["name_common_word", "name_near_duplicate", "name_same_initial_sound"]
    assert [finding["level"] for finding in findings] == ["warning", "warning", "info"]


def test_degenerate_input_is_harmless() -> None:
    assert check_name("", ["Corlan"], EN) == []
    assert check_name("  -- ", ["Corlan"], EN) == []
    assert check_name("Corran", ["", None, 7, "Corlan"], EN)[0]["match"] == "Corlan"  # type: ignore[list-item]
    assert check_name("Corran", ["Corlan"], load_pack("xx"))[0]["rule"] == "name_near_duplicate"
    assert check_name("Corran", ["Corlan"], None)[0]["rule"] == "name_near_duplicate"


def test_cli() -> None:
    script = str(Path(name_check.__file__))
    result = subprocess.run(
        [sys.executable, script, "Kara", "--existing", "Karim", "--language", "tr"],
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout.decode("utf-8"))
    assert _rules(payload["warnings"]) == ["name_common_word", "name_same_initial_sound"]

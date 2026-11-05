"""Declared roll calls, their receipt store, and the legacy expression CLI."""

from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import odds
import roll_dice


RESOLUTION = """mechanics:
  dice_mode: open_gm_rolls
  resolution:
    die: 1d2
    stat_min: 1
    stat_max: 5
    difficulty_min: 1
    difficulty_max: 5
    auto_success_margin: 2
    bands:
      - {at_least: 0, band: success}
      - {at_least: -1, band: partial_small_cost}
      - {at_least: -2, band: partial_medium_cost}
      - {at_least: -99, band: partial_heavy_cost}
"""

NOW = "2026-10-19T12:00:00Z"


def _append(path: Path, text: str) -> None:
    with open(path, "a", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def _set_revision(campaign: Path, revision: int) -> None:
    state = campaign / "current_state.yaml"
    text = re.sub(r"(?m)^continuity_revision: \d+$", f"continuity_revision: {revision}", state.read_text(encoding="utf-8"))
    state.write_bytes(text.encode("utf-8"))


def _call(**overrides: object) -> dict:
    call = {
        "actor": "Marcus",
        "axis": "street_sense",
        "value": 2,
        "difficulty": 4,
        "factors": [{"label": "prepared ambush", "modifier": 1}],
        "stakes": "the bait is seen through and the men scatter",
    }
    call.update(overrides)
    return call


def _store_lines(campaign: Path) -> list[str]:
    path = roll_dice.receipts_path(campaign)
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


@pytest.fixture()
def scaled(campaign: Path) -> Path:
    _append(campaign / "play_profile.yaml", RESOLUTION)
    return campaign


# ---------------------------------------------------------------------------
# Legacy expression mode
# ---------------------------------------------------------------------------


LEGACY_LOCK = """{
  "ok": true,
  "roll_id": "turn-12-lock",
  "expression": "2d6+1",
  "seed": "turn-12-lock",
  "dice": [
    3,
    5
  ],
  "subtotal": 8,
  "modifier": 1,
  "total": 9,
  "bounds": {
    "minimum": 3,
    "maximum": 13
  }
}
"""

LEGACY_INT_SEED = """{
  "ok": true,
  "roll_id": "84b7f4114f733b145228",
  "expression": "3d8-2",
  "seed": "42",
  "dice": [
    8,
    3,
    3
  ],
  "subtotal": 14,
  "modifier": -2,
  "total": 12,
  "bounds": {
    "minimum": 1,
    "maximum": 22
  }
}
"""


def test_legacy_expression_output_is_byte_identical(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"expression": "2d6+1", "seed": "turn-12-lock", "roll_id": "turn-12-lock"}
    assert roll_dice.main(["--input-json", json.dumps(payload)]) == 0
    assert capsys.readouterr().out == LEGACY_LOCK
    assert roll_dice.main(["--input-json", json.dumps({"expression": "3d8-2", "seed": 42})]) == 0
    assert capsys.readouterr().out == LEGACY_INT_SEED


def test_legacy_errors_keep_their_shape(capsys: pytest.CaptureFixture[str]) -> None:
    assert roll_dice.main(["--input-json", '{"expression": "0d6"}']) == 2
    assert capsys.readouterr().out == '{\n  "ok": false,\n  "error": "dice count must be between 1 and 100"\n}\n'
    assert roll_dice.main(["--input-json", json.dumps({"call": _call(), "roll_id": "x"})]) == 2
    assert json.loads(capsys.readouterr().out) == {"ok": False, "error": "a roll call needs --campaign <campaign folder>"}


def test_legacy_without_seed_still_rolls() -> None:
    result = roll_dice.roll({"expression": "1d20"})
    assert 1 <= result["total"] <= 20 and result["seed"]


def test_cli_runs_under_optimized_python() -> None:
    # `python -OO` (or PYTHONOPTIMIZE=2) strips docstrings; the 0.2.0 CLI worked there.
    payload = {"expression": "2d6+1", "seed": "turn-12-lock", "roll_id": "turn-12-lock"}
    completed = subprocess.run(
        [sys.executable, "-B", "-OO", roll_dice.__file__, "--input-json", json.dumps(payload)],
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert completed.stdout.replace(b"\r\n", b"\n").decode("ascii") == LEGACY_LOCK


def test_json_past_the_parser_limits_is_a_typed_failure(scaled: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Past Python's integer digit limit json.loads raises a plain ValueError (not a
    # JSONDecodeError), and deep nesting a RecursionError; neither may become a traceback.
    digits = "1" * 5000
    assert roll_dice.main(["--input-json", '{"expression": ' + digits + "}"]) == 2
    legacy = json.loads(capsys.readouterr().out)
    assert legacy["ok"] is False and set(legacy) == {"ok", "error"}
    if hasattr(sys, "get_int_max_str_digits"):
        assert legacy["error"] == "input JSON holds a number with too many digits"
    assert roll_dice.main(["--input-json", "[" * 100_000 + "]" * 100_000]) == 2
    assert json.loads(capsys.readouterr().out) == {"ok": False, "error": "input JSON is nested too deeply"}

    call = json.dumps({"roll_id": "big", "call": _call()}).replace('"value": 2', '"value": ' + digits)
    assert roll_dice.main(["--campaign", str(scaled), "--input-json", call]) == 2
    failure = json.loads(capsys.readouterr().out)
    assert failure["ok"] is False and failure["failure_category"] == "input_invalid"
    assert roll_dice.find_receipt(scaled, "big") is None


# ---------------------------------------------------------------------------
# Call mode
# ---------------------------------------------------------------------------


def test_call_writes_one_receipt_and_repeats_idempotently(scaled: Path) -> None:
    # Difficulty 5 leaves both faces of the d2 in play (difficulty 4 is certain).
    first = roll_dice.roll_call(scaled, {"roll_id": "bait-feint", "call": _call(difficulty=5)}, now=NOW)
    assert first["ok"] and first["repeat"] is False
    assert first["revision"] == 0 and first["die"] == "1d2" and first["at"] == NOW
    assert len(first["dice"]) == 1 and first["dice"][0] in (1, 2)
    assert first["total"] == 2 + 1 + first["dice"][0]
    assert first["margin"] == first["total"] - 5
    assert first["band"] == odds.band_for(first["margin"], odds.load_resolution(RESOLUTION)["bands"])
    assert first["auto"] is False and first["certain"] is False
    assert len(_store_lines(scaled)) == 1

    for _ in range(3):
        again = roll_dice.roll_call(
            scaled, {"roll_id": "bait-feint", "call": _call(difficulty=5)}, now="2030-01-01T00:00:00Z"
        )
        assert again["repeat"] is True
        assert {**again, "repeat": False} == first
    # Whitespace and an omitted empty factor list do not make a different call.
    plain = roll_dice.roll_call(scaled, {"roll_id": "plain", "call": _call(factors=[])}, now=NOW)
    same = _call(actor="  Marcus ")
    del same["factors"]
    assert roll_dice.roll_call(scaled, {"roll_id": "plain", "call": same})["repeat"] is True
    assert plain["call"]["factors"] == []
    assert len(_store_lines(scaled)) == 2
    assert b"\r\n" not in roll_dice.receipts_path(scaled).read_bytes()


def test_seed_is_derived_from_campaign_revision_id_and_call(scaled: Path) -> None:
    ids = [f"probe-{index}" for index in range(24)]
    faces = [roll_dice.roll_call(scaled, {"roll_id": roll_id, "call": _call(difficulty=5)})["dice"] for roll_id in ids]
    # A fresh store at the same campaign id and revision reproduces every roll.
    roll_dice.receipts_path(scaled).unlink()
    assert [roll_dice.roll_call(scaled, {"roll_id": r, "call": _call(difficulty=5)})["dice"] for r in ids] == faces
    # Both faces of the d2 occur across ids, so a new id is a genuinely new roll.
    assert {face[0] for face in faces} == {1, 2}


def test_shopping_with_the_same_id_is_refused(scaled: Path) -> None:
    roll_dice.roll_call(scaled, {"roll_id": "bait-feint", "call": _call()}, now=NOW)
    before = _store_lines(scaled)
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(scaled, {"roll_id": "bait-feint", "call": _call(difficulty=3)})
    assert caught.value.category == "roll_id_conflict"
    assert "different call" in str(caught.value)
    with pytest.raises(roll_dice.RollCallError, match="different call"):
        roll_dice.roll_call(scaled, {"roll_id": "bait-feint", "call": _call(stakes="something else")})
    assert _store_lines(scaled) == before


def test_same_id_at_a_later_revision_is_refused(scaled: Path) -> None:
    first = roll_dice.roll_call(scaled, {"roll_id": "bait-feint", "call": _call()}, now=NOW)
    _set_revision(scaled, 1)
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(scaled, {"roll_id": "bait-feint", "call": _call()})
    assert caught.value.category == "roll_id_conflict"
    # A GM re-reading the roll after the commit sees the recorded result, not an
    # invitation to roll again.
    message = str(caught.value)
    assert f"revision 0 with band {first['band']}" in message and "that result stands" in message
    assert len(_store_lines(scaled)) == 1


def test_range_errors_read_clearly_on_a_negative_scale(campaign: Path) -> None:
    _append(
        campaign / "play_profile.yaml",
        "mechanics:\n  resolution:\n    die: 1d6\n    stat_min: -3\n    stat_max: -1\n"
        "    difficulty_min: -2\n    difficulty_max: 2\n",
    )
    with pytest.raises(roll_dice.RollCallError, match="outside the stat scale -3 to -1;"):
        roll_dice.roll_call(campaign, {"roll_id": "low", "call": _call(value=0, difficulty=0)})
    with pytest.raises(roll_dice.RollCallError, match="outside the difficulty scale -2 to 2;"):
        roll_dice.roll_call(campaign, {"roll_id": "low", "call": _call(value=-2, difficulty=3)})
    assert roll_dice.roll_call(campaign, {"roll_id": "low", "call": _call(value=-2, difficulty=-2)})["ok"]


def test_auto_success_rolls_no_die(scaled: Path) -> None:
    result = roll_dice.roll_call(scaled, {"roll_id": "easy", "call": _call(value=5, difficulty=3, factors=[])})
    assert result["auto"] is True and result["dice"] == []
    assert result["band"] == "success" and result["total"] == 5 and result["margin"] == 2
    # Modifiers count toward the auto margin.
    boosted = roll_dice.roll_call(
        scaled,
        {"roll_id": "boosted", "call": _call(value=3, difficulty=3, factors=[{"label": "high ground", "modifier": 2}])},
    )
    assert boosted["auto"] is True and boosted["dice"] == []
    # One short of the margin, but even a 1 on the d2 succeeds: certain, so no die either.
    certain = roll_dice.roll_call(scaled, {"roll_id": "close", "call": _call(value=4, difficulty=3, factors=[])})
    assert certain["auto"] is True and certain["certain"] is True and certain["dice"] == []
    # A call that can still miss rolls.
    rolled = roll_dice.roll_call(scaled, {"roll_id": "risky", "call": _call(value=1, difficulty=3, factors=[])})
    assert rolled["auto"] is False and len(rolled["dice"]) == 1


@pytest.mark.parametrize(
    "value, difficulty, face, band",
    [
        (1, 3, 2, "success"),
        (1, 3, 1, "partial_small_cost"),
        (1, 4, 1, "partial_medium_cost"),
        (1, 5, 1, "partial_heavy_cost"),
    ],
)
def test_band_mapping(value: int, difficulty: int, face: int, band: str) -> None:
    resolution = odds.load_resolution(RESOLUTION)
    call = roll_dice.normalize_call(_call(value=value, difficulty=difficulty, factors=[]))
    outcome = roll_dice.evaluate_call(call, [face], resolution)
    assert outcome["band"] == band
    assert outcome["total"] == value + face and outcome["margin"] == value + face - difficulty
    assert outcome["auto"] is False


def test_a_certain_call_ignores_its_faces() -> None:
    # 3 vs 3 on a d2: the lowest roll already reaches success.
    resolution = odds.load_resolution(RESOLUTION)
    call = roll_dice.normalize_call(_call(value=3, difficulty=3, factors=[]))
    outcome = roll_dice.evaluate_call(call, [1], resolution)
    assert outcome == {"dice": [], "total": 3, "margin": 0, "band": "success", "auto": True}


def test_without_a_scale_the_call_names_its_die_and_bands_are_success_or_failure(campaign: Path) -> None:
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(campaign, {"roll_id": "free", "call": _call()})
    assert caught.value.category == "die_missing"
    result = roll_dice.roll_call(campaign, {"roll_id": "free", "die": "1d6", "call": _call(value=9, difficulty=20)})
    assert result["die"] == "1d6" and result["auto"] is False
    assert result["band"] == ("success" if result["margin"] >= 0 else "failure")
    assert result["band"] == "failure"  # 9 + 1 + d6 never reaches 20
    # Without a scale the die count is the number of faces: one die always adds
    # at least 1, so 1 vs 2 is certain and 1 vs 3 is rolled.
    certain = roll_dice.normalize_call(_call(value=1, difficulty=2, factors=[]))
    assert roll_dice.evaluate_call(certain, [1], None) == {
        "dice": [],
        "total": 1,
        "margin": -1,
        "band": "success",
        "auto": True,
    }
    call = roll_dice.normalize_call(_call(value=1, difficulty=3, factors=[]))
    assert roll_dice.evaluate_call(call, [2], None)["band"] == "success"
    assert roll_dice.evaluate_call(call, [1], None)["band"] == "failure"
    assert roll_dice.evaluate_call(call, [1], None)["auto"] is False


def test_configured_die_cannot_be_swapped(scaled: Path) -> None:
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(scaled, {"roll_id": "swap", "die": "1d6", "call": _call()})
    assert caught.value.category == "die_mismatch"
    assert roll_dice.roll_call(scaled, {"roll_id": "same", "die": "1d2", "call": _call()})["die"] == "1d2"


@pytest.mark.parametrize(
    "overrides, fragment",
    [
        ({"value": 6}, "call.value 6 is outside the stat scale 1-5"),
        ({"value": 0}, "outside the stat scale 1-5"),
        ({"difficulty": 6}, "call.difficulty 6 is outside the difficulty scale 1-5"),
    ],
)
def test_range_errors_name_the_scale(scaled: Path, overrides: dict, fragment: str) -> None:
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(scaled, {"roll_id": "out", "call": _call(**overrides)})
    assert caught.value.category == "out_of_range"
    assert fragment in str(caught.value)
    assert "OOC rules change" in str(caught.value)
    assert _store_lines(scaled) == []


@pytest.mark.parametrize(
    "payload, fragment",
    [
        ({"roll_id": "a", "call": _call(), "seed": 7}, "derives its own seed"),
        ({"roll_id": "a", "call": _call(), "note": "x"}, "unknown keys: note"),
        ({"call": _call()}, "roll_id must be"),
        ({"roll_id": "-bad", "call": _call()}, "roll_id must be"),
        ({"roll_id": "a", "call": _call(stakes=" ")}, "call.stakes must be non-empty"),
        ({"roll_id": "a", "call": _call(value=True)}, "call.value must be an integer"),
        ({"roll_id": "a", "call": _call(difficulty="4")}, "call.difficulty must be an integer"),
        ({"roll_id": "a", "call": _call(factors=[{"label": "x", "modifier": 1.5}])}, "modifier must be an integer"),
        ({"roll_id": "a", "call": _call(factors=[{"label": "x" * 81, "modifier": 1}])}, "at most 80"),
        ({"roll_id": "a", "call": _call(mood="tense")}, "call has unknown keys: mood"),
        ({"roll_id": "a", "call": {**_call(), "actor": None}}, "call.actor must be non-empty"),
        ({"roll_id": "a", "call": _call(actor="A" * 81)}, "call.actor must be at most 80"),
        ({"roll_id": "a", "call": _call(axis="x" * 81)}, "call.axis must be at most 80"),
        ({"roll_id": "a", "call": _call(stakes="s" * 501)}, "call.stakes must be at most 500"),
        ({"roll_id": "a", "call": _call(factors=[{"label": "x", "modifier": 1}] * 13)}, "at most 12 items"),
        ({"roll_id": "a", "call": _call(factors=[{"label": "x", "modifier": 101}])}, "magnitude must be at most 100"),
        ({"roll_id": "a", "call": _call(factors=[{"label": "x", "modifier": 1, "why": "y"}])}, "exactly label and modifier"),
        ({"roll_id": "a", "call": _call(value=1001)}, "call.value magnitude must be at most 1000"),
        ({"roll_id": "a", "call": "Marcus vs 4"}, "call must be an object"),
    ],
)
def test_input_validation(scaled: Path, payload: dict, fragment: str) -> None:
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(scaled, payload)
    assert caught.value.category == "input_invalid"
    assert fragment in str(caught.value)


def test_unicode_roll_ids_and_names_are_accepted(scaled: Path) -> None:
    result = roll_dice.roll_call(
        scaled, {"roll_id": "tuzak-çözme", "call": _call(actor="Işıl", axis="sokak_bilgisi")}
    )
    assert result["call"]["actor"] == "Işıl"
    assert roll_dice.find_receipt(scaled, "tuzak-çözme")["call"]["actor"] == "Işıl"


def test_roll_ids_keep_combining_marks_of_any_script() -> None:
    virama = chr(0x094D)  # Devanagari sign virama (a combining mark)
    damma, kasra = chr(0x064F), chr(0x0650)  # Arabic vowel marks
    devanagari = chr(0x0915) + chr(0x0930) + virama + chr(0x092E) + "-1"
    arabic = chr(0x0644) + damma + chr(0x0639) + kasra + chr(0x0628)
    assert roll_dice.valid_roll_id(devanagari) and roll_dice.valid_roll_id(arabic)
    assert not roll_dice.valid_roll_id(chr(0x0301) + "x")  # a mark cannot open the id
    for bad in ("-bad", ".x", "a b", "a/b", "x" * 81, ""):
        assert not roll_dice.valid_roll_id(bad)
    assert roll_dice.valid_roll_id("x" * 80) and roll_dice.valid_roll_id("_turn-12:lock.2")


@pytest.mark.parametrize("bad", ["a\u2028b", "a\u2029b", "a\x85b", "a\tb", "a\x00b", "a\rb", "a\nb"])
@pytest.mark.parametrize("field", ["actor", "stakes", "factor"])
def test_line_breaking_characters_are_refused(scaled: Path, bad: str, field: str) -> None:
    # A raw U+2028 or U+0085 would split the stored JSON line for str.splitlines readers.
    call = _call(factors=[{"label": bad, "modifier": 1}]) if field == "factor" else _call(**{field: bad})
    with pytest.raises(roll_dice.RollCallError, match="one line") as caught:
        roll_dice.roll_call(scaled, {"roll_id": "sep", "call": call})
    assert caught.value.category == "input_invalid"
    assert _store_lines(scaled) == []


@pytest.mark.parametrize("field", ["actor", "axis", "stakes", "factor"])
def test_a_lone_surrogate_escape_is_input_invalid(scaled: Path, field: str, capsys: pytest.CaptureFixture[str]) -> None:
    # JSON can carry "\ud800" but UTF-8 cannot store it; it used to escape as an
    # untyped UnicodeEncodeError from the library and as "io_error" from the CLI.
    bad = "Mar\ud800cus"
    call = _call(factors=[{"label": bad, "modifier": 1}]) if field == "factor" else _call(**{field: bad})
    with pytest.raises(roll_dice.RollCallError, match="lone surrogate") as caught:
        roll_dice.roll_call(scaled, {"roll_id": "sur", "call": call})
    assert caught.value.category == "input_invalid"
    assert roll_dice.main(["--campaign", str(scaled), "--input-json", json.dumps({"roll_id": "sur", "call": call})]) == 2
    assert json.loads(capsys.readouterr().out)["failure_category"] == "input_invalid"
    assert _store_lines(scaled) == []


def test_text_and_roll_ids_are_nfc_canonical(scaled: Path) -> None:
    decomposed_actor = "C\u0327ag\u0306ri"  # "Çağri" typed with combining marks
    decomposed_id = "tuzak-c\u0327o\u0308zme"
    first = roll_dice.roll_call(scaled, {"roll_id": decomposed_id, "call": _call(actor=decomposed_actor)})
    assert first["roll_id"] == "tuzak-çözme" and first["call"]["actor"] == "Çağri"
    again = roll_dice.roll_call(scaled, {"roll_id": "tuzak-çözme", "call": _call(actor="Çağri")})
    assert again["repeat"] is True and again["dice"] == first["dice"]
    assert roll_dice.find_receipt(scaled, decomposed_id)["roll_id"] == "tuzak-çözme"
    assert roll_dice.find_receipt(scaled, "  tuzak-çözme ")["roll_id"] == "tuzak-çözme"
    assert roll_dice.find_receipt(scaled, None) is None  # type: ignore[arg-type]
    assert len(_store_lines(scaled)) == 1


def test_roll_ids_are_exact_not_casefolded(scaled: Path) -> None:
    # Turkish dotted and dotless I fold differently by locale; ids never fold at all.
    ids = ["IŞIK", "ışık", "İz", "iz"]
    for roll_id in ids:
        assert roll_dice.roll_call(scaled, {"roll_id": roll_id, "call": _call()})["repeat"] is False
    assert [json.loads(line)["roll_id"] for line in _store_lines(scaled)] == ids
    assert roll_dice.find_receipt(scaled, "Işık") is None


def test_seed_depends_on_campaign_id_and_revision(scaled: Path) -> None:
    ids = [f"probe-{index}" for index in range(24)]

    def faces() -> list[list[int]]:
        result = [roll_dice.roll_call(scaled, {"roll_id": r, "call": _call(difficulty=5)})["dice"] for r in ids]
        roll_dice.receipts_path(scaled).unlink()
        return result

    base = faces()
    _set_revision(scaled, 1)
    later = faces()
    state = scaled / "current_state.yaml"
    state.write_bytes(state.read_bytes().replace(b"campaign_id: test_campaign", b"campaign_id: other_campaign"))
    other = faces()
    assert base != later and base != other and later != other


@pytest.fixture()
def windows_copy(scaled: Path, tmp_path: Path) -> Path:
    """A second copy of the scaled campaign, taken before the test rolls anything."""

    copy = tmp_path / "copy" / "campaign"
    shutil.copytree(scaled, copy)
    return copy


def test_bom_and_crlf_state_files_roll_the_same_dice(scaled: Path, windows_copy: Path) -> None:
    plain = roll_dice.roll_call(scaled, {"roll_id": "same", "call": _call()}, now=NOW)
    for path in (windows_copy / "current_state.yaml", windows_copy / "play_profile.yaml"):
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    windows = roll_dice.roll_call(windows_copy, {"roll_id": "same", "call": _call()}, now=NOW)
    assert windows == plain


def test_unreadable_campaign_files_are_typed_errors_not_silent_defaults(scaled: Path) -> None:
    profile = scaled / "play_profile.yaml"
    profile.write_bytes(profile.read_bytes().replace(b"band: success", "band: başarı".encode("cp1254")))
    # Without the strict read the configured scale would vanish and the caller's die would apply.
    with pytest.raises(roll_dice.RollCallError, match="not valid UTF-8") as caught:
        roll_dice.roll_call(scaled, {"roll_id": "x", "die": "1d20", "call": _call()})
    assert caught.value.category == "resolution_invalid"
    assert _store_lines(scaled) == []

    profile.write_bytes(b"schema_version: 2\n")
    state = scaled / "current_state.yaml"
    state.write_bytes(state.read_bytes().replace(b"continuity_revision: 0", b"continuity_revision: soon"))
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(scaled, {"roll_id": "x", "die": "1d6", "call": _call()})
    assert caught.value.category == "state_invalid"


def test_empty_campaign_files_mean_no_store_no_scale_or_a_typed_error(campaign: Path) -> None:
    store = roll_dice.receipts_path(campaign)
    store.parent.mkdir(parents=True)
    store.write_bytes(b"")
    assert roll_dice.find_receipt(campaign, "x") is None and roll_dice.open_receipts(campaign, 0) == []
    (campaign / "play_profile.yaml").write_bytes(b"")
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(campaign, {"roll_id": "x", "call": _call()})
    assert caught.value.category == "die_missing"
    assert roll_dice.roll_call(campaign, {"roll_id": "x", "die": "1d6", "call": _call()})["repeat"] is False
    assert len(_store_lines(campaign)) == 1
    (campaign / "current_state.yaml").write_bytes(b"")
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(campaign, {"roll_id": "y", "die": "1d6", "call": _call()})
    assert caught.value.category == "state_invalid"


def test_non_object_payload_is_input_invalid(scaled: Path) -> None:
    with pytest.raises(roll_dice.RollCallError, match="JSON object") as caught:
        roll_dice.roll_call(scaled, "seedless")  # type: ignore[arg-type]
    assert caught.value.category == "input_invalid"


def test_invalid_scale_config_is_a_typed_error(campaign: Path) -> None:
    _append(campaign / "play_profile.yaml", "mechanics:\n  resolution:\n    die: 1d6\n    stat_mx: 5\n")
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(campaign, {"roll_id": "a", "call": _call()})
    assert caught.value.category == "resolution_invalid"


def test_project_folder_is_accepted(scaled: Path) -> None:
    result = roll_dice.roll_call(scaled.parent, {"roll_id": "from-project", "call": _call()})
    assert roll_dice.find_receipt(scaled, "from-project") is not None
    assert roll_dice.find_receipt(scaled.parent, "from-project")["band"] == result["band"]
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(scaled / "characters", {"roll_id": "nowhere", "call": _call()})
    assert caught.value.category == "campaign_missing"


# ---------------------------------------------------------------------------
# Receipt store API
# ---------------------------------------------------------------------------


def test_open_receipts_and_mark_consumed(scaled: Path) -> None:
    roll_dice.roll_call(scaled, {"roll_id": "one", "call": _call()}, now=NOW)
    roll_dice.roll_call(scaled, {"roll_id": "two", "call": _call(difficulty=5)}, now=NOW)
    assert roll_dice.find_receipt(scaled, "missing") is None
    assert [r["roll_id"] for r in roll_dice.open_receipts(scaled, 0)] == ["one", "two"]
    assert roll_dice.open_receipts(scaled, 1) == []

    # An unreadable line survives the rewrite untouched.
    _append(roll_dice.receipts_path(scaled), "not json\n")
    assert roll_dice.mark_consumed(scaled, ["one", "ghost"], 1) == ["one"]
    assert roll_dice.mark_consumed(scaled, ["one"], 2) == []
    assert [r["roll_id"] for r in roll_dice.open_receipts(scaled, 0)] == ["two"]
    assert roll_dice.find_receipt(scaled, "one")["consumed_revision"] == 1
    lines = _store_lines(scaled)
    assert "not json" in lines and len(lines) == 3
    assert b"\r\n" not in roll_dice.receipts_path(scaled).read_bytes()

    # A repeat of a consumed roll still returns its receipt, consumption included.
    repeat = roll_dice.roll_call(scaled, {"roll_id": "one", "call": _call()})
    assert repeat["repeat"] is True and repeat["consumed_revision"] == 1


def test_store_api_is_quiet_without_a_store(campaign: Path) -> None:
    assert roll_dice.find_receipt(campaign, "x") is None
    assert roll_dice.open_receipts(campaign, 0) == []
    assert roll_dice.mark_consumed(campaign, ["x"], 1) == []
    assert not (campaign / ".repog-runtime").exists()
    with pytest.raises(roll_dice.RollCallError):
        roll_dice.mark_consumed(campaign, ["x"], "1")  # type: ignore[arg-type]


def test_store_keeps_the_newest_receipts(scaled: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(roll_dice, "RECEIPT_KEEP", 3)
    for index in range(5):
        roll_dice.roll_call(scaled, {"roll_id": f"r{index}", "call": _call()}, now=NOW)
    assert [json.loads(line)["roll_id"] for line in _store_lines(scaled)] == ["r2", "r3", "r4"]


def test_stored_receipt_has_exactly_the_documented_fields(scaled: Path) -> None:
    roll_dice.roll_call(scaled, {"roll_id": "fields", "call": _call()}, now=NOW)
    (line,) = _store_lines(scaled)
    assert set(json.loads(line)) == set(roll_dice.RECEIPT_FIELDS)


def test_a_bad_store_line_never_truncates_or_hides_the_store(scaled: Path) -> None:
    roll_dice.roll_call(scaled, {"roll_id": "one", "call": _call()}, now=NOW)
    path = roll_dice.receipts_path(scaled)
    legacy = {"roll_id": "legacy", "revision": 0, "call": {}, "stakes": "a\u2028b"}
    with open(path, "ab") as stream:
        stream.write(b"\xff\xfe not utf-8\r\n")  # undecodable, and CRLF
        stream.write(b"[1, 2]\n")  # JSON, but not a receipt
        stream.write(b'{"roll_id": ["one"], "revision": 0}\n')  # an unhashable id must not crash
        stream.write(json.dumps(legacy, ensure_ascii=False).encode("utf-8") + b"\r\n")  # raw U+2028 inside
    roll_dice.roll_call(scaled, {"roll_id": "two", "call": _call()}, now=NOW)

    assert [r["roll_id"] for r in roll_dice.read_receipts(scaled)] == ["one", ["one"], "legacy", "two"]
    assert roll_dice.find_receipt(scaled, "legacy")["stakes"] == "a\u2028b"
    assert roll_dice.mark_consumed(scaled, ["one", "two"], 1) == ["one", "two"]
    data = path.read_bytes()
    assert b"\r" not in data and data.endswith(b"\n")
    assert b"\xff\xfe not utf-8\n" in data and b"[1, 2]\n" in data
    assert b'{"roll_id": ["one"], "revision": 0}\n' in data
    assert len(data.split(b"\n")) == 7  # six lines, nothing dropped


def test_a_byte_order_mark_never_hides_the_first_receipt(scaled: Path) -> None:
    first = roll_dice.roll_call(scaled, {"roll_id": "one", "call": _call()}, now=NOW)
    path = roll_dice.receipts_path(scaled)
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())  # as some editors save UTF-8
    assert roll_dice.find_receipt(scaled, "one")["dice"] == first["dice"]
    assert [r["roll_id"] for r in roll_dice.open_receipts(scaled, 0)] == ["one"]
    # The id stays taken: a changed call is refused instead of rolled afresh.
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(scaled, {"roll_id": "one", "call": _call(difficulty=5)})
    assert caught.value.category == "roll_id_conflict"
    assert roll_dice.roll_call(scaled, {"roll_id": "one", "call": _call()})["repeat"] is True
    assert roll_dice.mark_consumed(scaled, ["one"], 1) == ["one"]
    data = path.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf") and len(data.splitlines()) == 1


def test_a_store_line_past_the_integer_digit_limit_is_skipped(scaled: Path) -> None:
    # json.loads raises a plain ValueError for it; readers must skip the line, not
    # crash the writer's roll check.
    roll_dice.roll_call(scaled, {"roll_id": "one", "call": _call()}, now=NOW)
    path = roll_dice.receipts_path(scaled)
    huge = b'{"roll_id": "huge", "revision": 0, "n": ' + b"7" * 5000 + b"}\n"
    with open(path, "ab") as stream:
        stream.write(huge)
    roll_dice.roll_call(scaled, {"roll_id": "two", "call": _call()}, now=NOW)
    assert roll_dice.find_receipt(scaled, "two")["roll_id"] == "two"
    assert {"one", "two"} <= {r["roll_id"] for r in roll_dice.read_receipts(scaled)}
    assert {"one", "two"} <= {r["roll_id"] for r in roll_dice.open_receipts(scaled, 0)}
    assert roll_dice.mark_consumed(scaled, ["one", "two"], 1) == ["one", "two"]
    assert huge in path.read_bytes()  # kept verbatim


def test_mark_consumed_takes_a_single_id_as_one_id(scaled: Path) -> None:
    roll_dice.roll_call(scaled, {"roll_id": "a", "call": _call()}, now=NOW)
    roll_dice.roll_call(scaled, {"roll_id": "ab", "call": _call()}, now=NOW)
    # A plain string must not be read as the ids "a" and "b".
    assert roll_dice.mark_consumed(scaled, "ab", 1) == ["ab"]
    assert [r["roll_id"] for r in roll_dice.open_receipts(scaled, 0)] == ["a"]
    assert roll_dice.open_receipts(scaled, None) == []  # type: ignore[arg-type]
    assert roll_dice.open_receipts(scaled, True) == []  # type: ignore[arg-type]


def test_store_io_failures_are_typed(scaled: Path, capsys: pytest.CaptureFixture[str]) -> None:
    roll_dice.receipts_path(scaled).mkdir(parents=True)  # a folder where the store file belongs
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.find_receipt(scaled, "x")
    assert caught.value.category == "io_error"
    request = json.dumps({"roll_id": "x", "call": _call()})
    assert roll_dice.main(["--campaign", str(scaled), "--input-json", request]) == 2
    assert json.loads(capsys.readouterr().out)["failure_category"] == "io_error"


# ---------------------------------------------------------------------------
# Call mode CLI
# ---------------------------------------------------------------------------


def test_call_cli_prints_receipt_and_typed_failures(scaled: Path, capsys: pytest.CaptureFixture[str]) -> None:
    request = json.dumps({"roll_id": "cli", "call": _call()})
    assert roll_dice.main(["--campaign", str(scaled), "--input-json", request]) == 0
    first = capsys.readouterr().out
    assert roll_dice.main(["--campaign", str(scaled), "--input-json", request]) == 0
    second = capsys.readouterr().out
    assert first.replace('"repeat": false', '"repeat": true') == second
    receipt = json.loads(first)
    assert list(receipt)[:5] == ["summary", "ok", "repeat", "roll_id", "revision"]
    assert first.isascii()

    clash = json.dumps({"roll_id": "cli", "call": _call(value=1)})
    assert roll_dice.main(["--campaign", str(scaled), "--input-json", clash]) == 2
    failure = json.loads(capsys.readouterr().out)
    assert failure["ok"] is False and failure["failure_category"] == "roll_id_conflict"

    assert roll_dice.main(["--campaign", str(scaled), "--input-json", "{oops"]) == 2
    assert json.loads(capsys.readouterr().out)["failure_category"] == "input_invalid"
    assert roll_dice.main(["--campaign", str(scaled), "--input-json", '{"expression": "1d6"}']) == 2
    assert json.loads(capsys.readouterr().out)["failure_category"] == "input_invalid"
    assert roll_dice.main(["--campaign", str(scaled), "--input-json", "[" * 100_000 + "]" * 100_000]) == 2
    assert json.loads(capsys.readouterr().out)["failure_category"] == "input_invalid"
    assert roll_dice.main(["--campaign", str(scaled), "--input-json", "[1]"]) == 2
    assert json.loads(capsys.readouterr().out) == {
        "ok": False,
        "failure_category": "input_invalid",
        "failure_reason": "input must be a JSON object",
    }


def test_call_cli_output_stays_ascii_with_turkish_text(scaled: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Windows consoles may not encode Turkish letters; the escaped JSON decodes back exactly.
    request = json.dumps(
        {"roll_id": "tuzak-çözme", "call": _call(actor="Işıl", stakes="İpler kopar ve ışık söner")},
        ensure_ascii=False,
    )
    assert roll_dice.main(["--campaign", str(scaled), "--input-json", request]) == 0
    out = capsys.readouterr().out
    assert out.isascii()
    receipt = json.loads(out)
    assert receipt["roll_id"] == "tuzak-çözme"
    assert receipt["call"]["actor"] == "Işıl" and receipt["call"]["stakes"] == "İpler kopar ve ışık söner"


# ---------------------------------------------------------------------------
# Play-simulation gaps: the difficulty's reason, accepted keys, request files
# ---------------------------------------------------------------------------


REASON = "the bell warned the guards, so they watch the alley"


def test_reason_is_part_of_the_canonical_call_and_the_receipt(scaled: Path) -> None:
    first = roll_dice.roll_call(scaled, {"roll_id": "alley", "call": _call(reason=f"  {REASON} ")}, now=NOW)
    assert first["call"]["reason"] == REASON
    (line,) = _store_lines(scaled)
    assert json.loads(line)["call"]["reason"] == REASON
    assert roll_dice.find_receipt(scaled, "alley")["call"]["reason"] == REASON
    # The same reason repeats the receipt; another reason, or none, is another call.
    assert roll_dice.roll_call(scaled, {"roll_id": "alley", "call": _call(reason=REASON)})["repeat"] is True
    for changed in (_call(reason="the alley is dark"), _call()):
        with pytest.raises(roll_dice.RollCallError, match="different call") as caught:
            roll_dice.roll_call(scaled, {"roll_id": "alley", "call": changed})
        assert caught.value.category == "roll_id_conflict"
    assert len(_store_lines(scaled)) == 1


def test_a_null_reason_is_absent_from_the_canonical_call() -> None:
    plain = roll_dice.normalize_call(_call())
    assert "reason" not in plain
    assert roll_dice.normalize_call(_call(reason=None)) == plain


# Dice the 0.3.0 call mode rolled before a call could carry a reason; a call
# without one must keep exactly these receipts (same campaign id and revision).
PINNED_2D20 = {"pin-0": [12, 20], "pin-1": [12, 17], "pin-2": [15, 5], "pin-3": [12, 2], "pin-4": [17, 3], "pin-5": [12, 2]}


def test_a_call_without_a_reason_rolls_as_before(tmp_path: Path) -> None:
    root = tmp_path / "campaign"
    root.mkdir()
    (root / "current_state.yaml").write_text("campaign_id: test_campaign\ncontinuity_revision: 0\n", encoding="utf-8")

    def dice(call: dict) -> dict[str, list[int]]:
        # 2 + 1 vs 4 is certain on 2d20 since 0.4.0, so the receipt records no
        # dice; the faces its seed derives are what must not change.
        rolled = {}
        for roll_id in PINNED_2D20:
            receipt = roll_dice.roll_call(root, {"roll_id": roll_id, "die": "2d20", "call": call})
            seed = roll_dice._seed("test_campaign", 0, roll_id, "2d20", receipt["call"])
            rolled[roll_id] = roll_dice._faces(seed, 2, 20)
        roll_dice.receipts_path(root).unlink()
        return rolled

    assert dice(_call()) == PINNED_2D20
    assert dice(_call(reason=None)) == PINNED_2D20
    # A reason is part of the call, so it is part of the seed.
    assert dice(_call(reason=REASON)) != PINNED_2D20


@pytest.mark.parametrize(
    "reason, fragment",
    [
        ("r" * 201, "call.reason must be at most 200 characters"),
        ("", "call.reason must be non-empty text"),
        ("  ", "call.reason must be non-empty text"),
        (7, "call.reason must be non-empty text"),
        ("bell\nalley", "call.reason must be one line"),
        ("bell alley", "call.reason must be one line"),
        ("bell\ud800", "call.reason holds a lone surrogate"),
    ],
)
def test_reason_is_one_short_line(scaled: Path, reason: object, fragment: str) -> None:
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(scaled, {"roll_id": "why", "call": _call(reason=reason)})
    assert caught.value.category == "input_invalid"
    assert fragment in str(caught.value)
    assert _store_lines(scaled) == []


def test_a_reason_of_200_characters_is_accepted(scaled: Path) -> None:
    result = roll_dice.roll_call(scaled, {"roll_id": "why", "call": _call(reason="r" * roll_dice.MAX_REASON)})
    assert roll_dice.MAX_REASON == 200 and len(result["call"]["reason"]) == 200


def test_unknown_key_errors_list_the_accepted_keys(scaled: Path) -> None:
    # Regression: a GM declaring "the difficulty with a one-line reason" got a bare refusal.
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(scaled, {"roll_id": "a", "call": _call(difficulty_reason="alert guards")})
    assert caught.value.category == "input_invalid"
    assert str(caught.value) == (
        "call has unknown keys: difficulty_reason; accepted keys: actor, axis, value, difficulty, stakes (required); "
        "factors, reason (optional)"
    )
    assert all(key in str(caught.value) for key in roll_dice.CALL_KEYS)
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.roll_call(scaled, {"roll_id": "a", "call": _call(), "note": "x"})
    assert str(caught.value) == "unknown keys: note; accepted keys: roll_id, call (required); die (optional)"


def test_input_file_matches_input_json_in_both_modes(scaled: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    legacy = tmp_path / "legacy.json"
    legacy.write_bytes(json.dumps({"expression": "2d6+1", "seed": "turn-12-lock", "roll_id": "turn-12-lock"}).encode("utf-8"))
    assert roll_dice.main(["--input-file", str(legacy)]) == 0
    assert capsys.readouterr().out == LEGACY_LOCK

    # Apostrophes and Turkish letters in the prose, a BOM, and CRLF: nothing for a shell to quote.
    request = {
        "roll_id": "alley",
        "call": _call(actor="Işıl", stakes="the guard's dog hears Işıl's step", reason="the watch's bell rang"),
    }
    path = tmp_path / "call.json"
    text = json.dumps(request, ensure_ascii=False, indent=2).replace("\n", "\r\n")
    path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    assert roll_dice.main(["--campaign", str(scaled), "--input-file", str(path)]) == 0
    from_file = capsys.readouterr().out
    assert roll_dice.main(["--campaign", str(scaled), "--input-json", json.dumps(request)]) == 0
    assert capsys.readouterr().out == from_file.replace('"repeat": false', '"repeat": true')
    receipt = json.loads(from_file)
    assert receipt["call"]["stakes"] == "the guard's dog hears Işıl's step"
    assert receipt["call"]["reason"] == "the watch's bell rang"
    assert from_file.isascii()


def test_input_file_dash_reads_standard_input_as_utf8_bytes(
    scaled: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    request = {"roll_id": "stdin", "call": _call(actor="Işıl", stakes="the guard's dog barks")}
    data = b"\xef\xbb\xbf" + json.dumps(request, ensure_ascii=False).encode("utf-8")
    # The text layer's code page must never be used: cp1252 would garble the Turkish letters.
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(data), encoding="cp1252"))
    assert roll_dice.main(["--campaign", str(scaled), "--input-file", "-"]) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["roll_id"] == "stdin" and receipt["call"]["actor"] == "Işıl"


def test_input_file_dash_reads_a_real_pipe(scaled: Path) -> None:
    request = {"roll_id": "pipe", "call": _call(actor="Işıl", stakes="the guard's dog barks", reason="it's dark")}
    completed = subprocess.run(
        [sys.executable, "-B", roll_dice.__file__, "--campaign", str(scaled), "--input-file", "-"],
        input=b"\xef\xbb\xbf" + json.dumps(request, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    receipt = json.loads(completed.stdout)
    assert receipt["call"]["actor"] == "Işıl" and receipt["call"]["reason"] == "it's dark"
    assert roll_dice.find_receipt(scaled, "pipe")["band"] == receipt["band"]


def test_input_file_failures_keep_each_mode_s_shape(
    scaled: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing.json"
    assert roll_dice.main(["--input-file", str(missing)]) == 2
    legacy = json.loads(capsys.readouterr().out)
    assert set(legacy) == {"ok", "error"} and legacy["ok"] is False
    assert legacy["error"].startswith(f"cannot read --input-file {missing}: ")
    assert roll_dice.main(["--campaign", str(scaled), "--input-file", str(missing)]) == 2
    failure = json.loads(capsys.readouterr().out)
    assert set(failure) == {"ok", "failure_category", "failure_reason"}
    assert failure["failure_category"] == "io_error"

    cp1254 = tmp_path / "cp1254.json"
    body = json.dumps({"roll_id": "x", "call": _call(actor="Işıl")}, ensure_ascii=False).encode("cp1254")
    first_bad = body.index("ş".encode("cp1254"))
    cp1254.write_bytes(body)
    assert roll_dice.main(["--campaign", str(scaled), "--input-file", str(cp1254)]) == 2
    failure = json.loads(capsys.readouterr().out)
    assert failure["failure_category"] == "input_invalid"
    assert failure["failure_reason"] == (
        f"--input-file {cp1254} is not valid UTF-8 (byte {first_bad}); save the request as UTF-8 and retry"
    )
    # With a byte order mark the offset still counts from the start of the file.
    cp1254.write_bytes(b"\xef\xbb\xbf" + body)
    assert roll_dice.main(["--input-file", str(cp1254)]) == 2
    assert f"is not valid UTF-8 (byte {first_bad + 3});" in json.loads(capsys.readouterr().out)["error"]

    # A NUL in the path is a ValueError from the OS layer, never a traceback.
    assert roll_dice.main(["--campaign", str(scaled), "--input-file", "bad\0name.json"]) == 2
    failure = json.loads(capsys.readouterr().out)
    assert failure["failure_category"] == "io_error" and failure["failure_reason"].startswith("cannot read --input-file bad")
    assert _store_lines(scaled) == []


def test_cli_takes_exactly_one_input_source(scaled: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "request.json"
    path.write_text(json.dumps({"roll_id": "x", "call": _call()}), encoding="utf-8")
    for argv in (["--campaign", str(scaled)], ["--input-json", "{}", "--input-file", str(path)]):
        with pytest.raises(SystemExit) as exited:
            roll_dice.main(argv)
        assert exited.value.code == 2
    errors = capsys.readouterr().err
    assert "one of the arguments --input-json --input-file is required" in errors
    assert "not allowed with argument" in errors
    assert _store_lines(scaled) == []

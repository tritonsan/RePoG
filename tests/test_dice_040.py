"""0.4.0 roll receipts: exact odds, certainty, stakes checks, the display line, axes and rereads."""

from __future__ import annotations

import io
import json
import re
import sys
from collections import Counter
from itertools import product
from pathlib import Path

import pytest

import odds
import roll_dice


NOW = "2026-11-04T12:00:00Z"

# Five bands in the shape the G2 campaign used, on 2d6.
GRADED = """mechanics:
  dice_mode: open_gm_rolls
  resolution:
    die: 2d6
    stat_min: 1
    stat_max: 10
    difficulty_min: 2
    difficulty_max: 20
    bands:
      - {at_least: 4, band: critical}
      - {at_least: 1, band: clean}
      - {at_least: 0, band: success_with_cost}
      - {at_least: -2, band: partial_or_loss}
      - {at_least: -99, band: failure}
"""

TEMPLATE_BANDS = [
    {"at_least": 0, "band": "success"},
    {"at_least": -2, "band": "partial_small_cost"},
    {"at_least": -4, "band": "partial_heavy_cost"},
    {"at_least": -99, "band": "failure"},
]


def _profile(campaign: Path, text: str) -> None:
    path = campaign / "play_profile.yaml"
    path.write_bytes(path.read_bytes() + text.encode("utf-8"))


def _language(campaign: Path, language: str, records: str | None = None) -> None:
    block = f"narration:\n  language: {language}\n"
    if records is not None:
        block += f"  records_language: {records}\n"
    _profile(campaign, block)


def _narration(values: dict) -> str:
    """A `narration:` block with these keys, "" for none."""

    return "narration:\n" + "".join(f"  {key}: {value}\n" for key, value in values.items()) if values else ""


def _lint_record(campaign: Path, content: str) -> None:
    folder = campaign / ".repog-runtime"
    folder.mkdir(exist_ok=True)
    (folder / "lint_last.json").write_text(content, encoding="utf-8")


def _set_revision(campaign: Path, revision: int) -> None:
    state = campaign / "current_state.yaml"
    text = state.read_text(encoding="utf-8")
    state.write_bytes(text.replace("continuity_revision: 0\n", f"continuity_revision: {revision}\n", 1).encode("utf-8"))


def _call(**overrides: object) -> dict:
    call = {
        "actor": "Mira",
        "axis": "street_sense",
        "value": 5,
        "difficulty": 9,
        "factors": [{"label": "high ground", "modifier": 1}],
        "stakes": "the courier slips into the crowd",
    }
    call.update(overrides)
    return call


def _roll(campaign: Path, roll_id: str, **overrides: object) -> dict:
    return roll_dice.roll_call(campaign, {"roll_id": roll_id, "call": _call(**overrides)}, now=NOW)


def _rules(result: dict) -> list[str]:
    return [warning["rule"] for warning in result["warnings"]]


@pytest.fixture()
def graded(campaign: Path) -> Path:
    _profile(campaign, GRADED)
    return campaign


# ---------------------------------------------------------------------------
# Exact odds
# ---------------------------------------------------------------------------


def _brute(call: dict, count: int, sides: int, bands: list[dict]) -> Counter:
    base = call["value"] + sum(f["modifier"] for f in call["factors"]) - call["difficulty"]
    return Counter(odds.band_for(base + sum(faces), bands) for faces in product(range(1, sides + 1), repeat=count))


@pytest.mark.parametrize("count, sides", [(1, 2), (1, 6), (2, 6), (3, 4)])
@pytest.mark.parametrize("difficulty", [2, 5, 8, 11, 14])
def test_odds_match_brute_force_enumeration(count: int, sides: int, difficulty: int) -> None:
    bands = odds.load_resolution(GRADED)["bands"]
    call = roll_dice.normalize_call(_call(difficulty=difficulty))
    chances = roll_dice.call_odds(call, count, sides, bands)
    ways = _brute(call, count, sides, bands)
    reachable = [band["band"] for band in bands if ways[band["band"]]]
    below = sum(ways[name] for name in ways if name not in {"critical", "clean", "success_with_cost"})
    assert chances["reachable_bands"] == reachable
    assert chances["floor_band"] == reachable[-1] and chances["ceiling_band"] == reachable[0]
    assert chances["p_below_success"] == round(below / sides**count, 4)
    assert chances["certain"] is (reachable[-1] in {"critical", "clean", "success_with_cost"})


@pytest.mark.parametrize(
    "bands, expected",
    [
        ([{"at_least": 0, "band": "only"}], ["only"]),
        ([{"at_least": 1, "band": "only"}], ["only"]),
        (list(odds.DEFAULT_BANDS), ["success"]),
        (TEMPLATE_BANDS, ["success"]),
        (odds.load_resolution(GRADED)["bands"], ["critical", "clean", "success_with_cost"]),
        # The band a margin of 0 lands in is the lowest success, whatever its threshold.
        ([{"at_least": -1, "band": "hit"}, {"at_least": -9, "band": "miss"}], ["hit"]),
        (
            [{"at_least": 1, "band": "clean"}, {"at_least": -1, "band": "cost"}, {"at_least": -9, "band": "failure"}],
            ["clean", "cost"],
        ),
        # The last band also catches every lower margin: when 0 lands there, the band above counts.
        (
            [{"at_least": 2, "band": "hit"}, {"at_least": 1, "band": "graze"}, {"at_least": 0, "band": "miss"}],
            ["hit", "graze"],
        ),
        ([{"at_least": 3, "band": "great"}, {"at_least": 0, "band": "fine"}], ["great"]),
    ],
)
def test_success_bands(bands: list[dict], expected: list[str]) -> None:
    assert roll_dice.success_bands(bands) == expected
    # The full check reads the lowest success band the same way (odds.success_band, package C).
    lowest = getattr(odds, "success_band", None)
    if lowest is not None:
        assert lowest(bands)["band"] == expected[-1]


def test_receipt_carries_the_odds_fields(graded: Path) -> None:
    # 5 + 1 vs 9 on 2d6: margin -1 to 9; only a roll of 2 (1 in 36) lands below success.
    result = _roll(graded, "dock-chase")
    assert result["reachable_bands"] == ["critical", "clean", "success_with_cost", "partial_or_loss"]
    assert result["floor_band"] == "partial_or_loss" and result["ceiling_band"] == "critical"
    assert result["p_below_success"] == round(1 / 36, 4)
    assert result["certain"] is False and result["auto"] is False and len(result["dice"]) == 2
    (line,) = roll_dice.receipts_path(graded).read_text(encoding="utf-8").splitlines()
    assert set(json.loads(line)) == set(roll_dice.RECEIPT_FIELDS)


# ---------------------------------------------------------------------------
# Certainty and auto success
# ---------------------------------------------------------------------------


def test_a_certain_call_is_auto_at_its_floor_band(graded: Path) -> None:
    # 5 + 1 vs 4: the lowest roll (2) gives margin 4, already critical; vs 6 it gives clean.
    critical = _roll(graded, "sure", difficulty=4)
    assert critical["certain"] is True and critical["auto"] is True and critical["dice"] == []
    assert critical["band"] == critical["floor_band"] == "critical"
    clean = _roll(graded, "likely", difficulty=6)
    assert clean["certain"] is True and clean["auto"] is True
    assert clean["band"] == "clean" and clean["ceiling_band"] == "critical"
    assert clean["p_below_success"] == 0.0
    (warning,) = [w for w in clean["warnings"] if w["rule"] == "roll_certain"]
    assert "clean" in warning["message"] and "without rolling" in warning["message"]
    assert clean["summary"] == "ok clean margin 0"


def test_auto_success_margin_records_the_floor_band_not_the_top_band(campaign: Path) -> None:
    # Before 0.4.0 an auto success always took the first band (critical here).
    _profile(campaign, GRADED.replace("    bands:", "    auto_success_margin: 2\n    bands:"))
    result = _roll(campaign, "easy", value=4, difficulty=3, factors=[])
    assert result["auto"] is True and result["band"] == "clean" and result["floor_band"] == "clean"


def test_a_margin_auto_success_below_the_floor_takes_the_lowest_success_band(campaign: Path) -> None:
    _profile(
        campaign,
        "mechanics:\n  resolution:\n    die: 1d6\n    auto_success_margin: 0\n    bands:\n"
        "      - {at_least: 5, band: success}\n      - {at_least: -99, band: failure}\n",
    )
    result = _roll(campaign, "granted", value=3, difficulty=3, factors=[])
    assert result["auto"] is True and result["certain"] is False
    assert result["band"] == "success" and result["floor_band"] == "failure"
    assert "roll_certain" not in _rules(result)


def test_without_a_scale_a_certain_call_still_takes_no_dice(campaign: Path) -> None:
    result = roll_dice.roll_call(campaign, {"roll_id": "free", "die": "1d6", "call": _call(value=3, difficulty=4)})
    assert result["certain"] is True and result["auto"] is True and result["band"] == "success"
    risky = roll_dice.roll_call(campaign, {"roll_id": "free-2", "die": "1d6", "call": _call(value=3, difficulty=6)})
    assert risky["certain"] is False and risky["reachable_bands"] == ["success", "failure"]
    assert risky["p_below_success"] == round(1 / 6, 4)


# ---------------------------------------------------------------------------
# Stakes
# ---------------------------------------------------------------------------


GRADED_BANDS = odds.load_resolution(GRADED)["bands"]


def test_stakes_keys_parse_in_any_pack_language_and_case() -> None:
    stakes = (
        "Kaçış: KRİTİK: gemiyi alır; Temiz: kaçar | bedel: yaralanır; "
        "KISMİ: iz bırakır; basarisiz: yakalanır"
    )
    entries = roll_dice.stakes_entries(stakes, GRADED_BANDS)
    assert [entry["key"] for entry in entries] == ["KRİTİK", "Temiz", "bedel", "KISMİ", "basarisiz"]
    assert [entry["kind"] for entry in entries] == ["critical", "clean", "cost", "partial", "failure"]
    assert [entry["text"] for entry in entries] == ["gemiyi alır", "kaçar", "yaralanır", "iz bırakır", "yakalanır"]
    assert [entry["bands"] for entry in entries] == [
        ["critical"],
        ["clean"],
        ["success_with_cost"],
        ["partial_or_loss"],
        ["failure"],
    ]


def test_stakes_keys_in_german_spanish_and_french() -> None:
    for stakes in (
        "Erfolg: x; Preis: y; Fehlschlag: z",
        "éxito: x; coste: y; fracaso: z",
        "réussite: x; coût: y; échec: z",
    ):
        kinds = [entry["kind"] for entry in roll_dice.stakes_entries(stakes, GRADED_BANDS)]
        assert kinds == ["success", "cost", "failure"], stakes


def test_stakes_keys_may_name_a_band_exactly_or_in_several_words() -> None:
    entries = roll_dice.stakes_entries(
        "success with cost: torn sleeve; partial or loss: the map; kritik başarı: the ship", GRADED_BANDS
    )
    assert [(entry["key"], entry["bands"]) for entry in entries] == [
        ("success with cost", ["success_with_cost"]),
        ("partial or loss", ["partial_or_loss"]),
        ("kritik başarı", ["critical"]),
    ]
    assert entries[0]["kind"] is None and entries[2]["kind"] == "critical"


def test_a_success_key_covers_every_success_band_but_failure_stays_by_name() -> None:
    entries = roll_dice.stakes_entries("Başarılı: kaçar; clean: temiz kaçar; failure: yakalanır", GRADED_BANDS)
    assert [(entry["kind"], entry["bands"]) for entry in entries] == [
        ("success", ["critical", "clean", "success_with_cost"]),
        (None, ["clean"]),  # names the band exactly
        (None, ["failure"]),
    ]
    # The more specific entry wins for its band; the success entry fills the rest.
    assert roll_dice._entry_for("clean", entries)["text"] == "temiz kaçar"
    assert roll_dice._entry_for("critical", entries)["text"] == "kaçar"
    assert roll_dice._entry_for("partial_or_loss", entries) is None
    # A failure kind describes only bands named for it, never the partial bands above it.
    (fail,) = roll_dice.stakes_entries("başarısız: yakalanır", TEMPLATE_BANDS)
    assert fail["kind"] == "failure" and fail["bands"] == ["failure"]


def test_a_key_pairing_a_success_word_with_a_failure_word_describes_the_bad_band() -> None:
    # `critical failure` is a failure: the below-success word is the head noun.
    stakes = "success: she escapes; partial: drops the map; critical failure: falls into the harbour"
    entries = roll_dice.stakes_entries(stakes, GRADED_BANDS)
    assert [(entry["kind"], entry["bands"]) for entry in entries] == [
        ("success", ["critical", "clean", "success_with_cost"]),
        ("partial", ["partial_or_loss"]),
        ("failure", ["failure"]),
    ]
    call = roll_dice.normalize_call(_call(difficulty=13, factors=[], stakes=stakes))
    critical = roll_dice.display_line(call, {"dice": [6, 6], "band": "critical"}, entries, "en")
    failure = roll_dice.display_line(call, {"dice": [1, 1], "band": "failure"}, entries, "en")
    assert critical == "Mira · street sense 5 vs 13 → 6+6 = critical · she escapes"
    assert failure == "Mira · street sense 5 vs 13 → 1+1 = failure · falls into the harbour"
    assert roll_dice.stakes_warnings(entries, roll_dice.call_odds(call, 2, 6, GRADED_BANDS), GRADED_BANDS) == []
    turkish = roll_dice.stakes_entries(
        "başarı: kaçar; kısmi: haritayı düşürür; kritik başarısızlık: limana düşer", GRADED_BANDS
    )
    assert roll_dice.display_line(call, {"dice": [1, 1], "band": "failure"}, turkish, "tr").endswith(
        "= başarısız · limana düşer"
    )


@pytest.mark.parametrize(
    "stakes, kind",
    [
        ("kritik başarısızlık: limana düşer", "failure"),
        ("Crit Fail: caught", "failure"),
        ("échec critique: caught", "failure"),
        ("fracaso crítico: caught", "failure"),
        ("critical loss: the map", "loss"),
        ("kritik başarı: the ship", "critical"),
        ("critical success: the ship", "critical"),
    ],
)
def test_a_compound_key_takes_the_kind_of_its_head_noun(stakes: str, kind: str) -> None:
    (entry,) = roll_dice.stakes_entries(stakes, GRADED_BANDS)
    assert entry["kind"] == kind


def test_a_band_name_pairing_both_sides_counts_as_the_bad_result() -> None:
    bands = [
        {"at_least": 4, "band": "critical_success"},
        {"at_least": 0, "band": "success"},
        {"at_least": -3, "band": "failure"},
        {"at_least": -99, "band": "critical_failure"},
    ]
    (critical,) = roll_dice.stakes_entries("critical: the ship", bands)
    assert critical["bands"] == ["critical_success"]
    (failure,) = roll_dice.stakes_entries("başarısız: caught", bands)
    assert failure["bands"] == ["failure", "critical_failure"]


def test_a_word_inside_prose_is_not_a_key() -> None:
    # A kind word counts only as a whole word directly before a colon.
    assert roll_dice.stakes_entries("the failure of the plan: they scatter", GRADED_BANDS) == []
    assert roll_dice.stakes_entries("the rope, uncleanly: cut, gives way", GRADED_BANDS) == []
    assert roll_dice.stakes_entries("the guards hear the gate", GRADED_BANDS) == []


def test_stakes_describing_an_unreachable_band_warn(graded: Path) -> None:
    # 5 + 1 vs 9 reaches partial_or_loss at worst, never failure.
    result = _roll(graded, "chase", stakes="clean: away; cost: cut; partial: map lost; failure: caught")
    (warning,) = [w for w in result["warnings"] if w["rule"] == "stakes_unreachable_band"]
    assert "failure" in warning["message"] and "cannot reach" in warning["message"]
    assert "stakes_missing_band" not in _rules(result)
    with_crit = _roll(graded, "chase-2", difficulty=4, stakes="kritik: gemi; temiz: kaçar")
    assert _rules(with_crit) == ["roll_certain", "stakes_unreachable_band"]
    assert "temiz" in with_crit["warnings"][1]["message"]


def test_a_key_for_a_band_the_campaign_lacks_is_unreachable(campaign: Path) -> None:
    result = roll_dice.roll_call(
        campaign,
        {"roll_id": "x", "die": "1d6", "call": _call(value=1, difficulty=4, stakes="critical: ship; failure: caught")},
    )
    (warning,) = [w for w in result["warnings"] if w["rule"] == "stakes_unreachable_band"]
    assert warning["message"].startswith("the stakes describe critical (no such band), which this call cannot reach")


def test_reachable_bands_below_success_must_be_described(graded: Path) -> None:
    # 5 + 1 vs 13: margin -5 to 5, so partial_or_loss and failure are both reachable.
    keyed = _roll(graded, "climb", difficulty=13, stakes="clean: up; failure: falls")
    (warning,) = [w for w in keyed["warnings"] if w["rule"] == "stakes_missing_band"]
    assert "partial_or_loss" in warning["message"] and "failure," not in warning["message"]
    unkeyed = _roll(graded, "climb-2", difficulty=13, stakes="Mira falls into the harbour")
    (warning,) = [w for w in unkeyed["warnings"] if w["rule"] == "stakes_missing_band"]
    assert "partial_or_loss, failure" in warning["message"]
    described = _roll(graded, "climb-3", difficulty=13, stakes="partial: slips; failure: falls; critical: flies")
    assert described["warnings"] == []


def test_one_unkeyed_line_covers_a_single_bad_band(campaign: Path) -> None:
    result = roll_dice.roll_call(
        campaign, {"roll_id": "x", "die": "1d6", "call": _call(value=1, difficulty=4, stakes="the guards hear")}
    )
    assert result["reachable_bands"] == ["success", "failure"] and result["warnings"] == []


def test_an_entry_without_text_describes_nothing(graded: Path) -> None:
    result = _roll(graded, "empty", difficulty=13, stakes="partial: slips; failure:")
    (warning,) = [w for w in result["warnings"] if w["rule"] == "stakes_missing_band"]
    assert "failure" in warning["message"]


# ---------------------------------------------------------------------------
# The display line
# ---------------------------------------------------------------------------


def test_display_line_in_english_with_the_unkeyed_stakes(graded: Path) -> None:
    result = _roll(graded, "chase")
    dice = "+".join(str(face) for face in result["dice"])
    label = {"success_with_cost": "success with cost", "partial_or_loss": "partial or loss"}.get(
        result["band"], result["band"]
    )
    expected = f"Mira · street sense 5 + 1 vs 9 → {dice} = {label} · at stake: the courier slips into the crowd"
    assert result["display"] == expected


def test_display_line_in_turkish_shows_the_keyed_clause(graded: Path) -> None:
    _language(graded, "tr")
    stakes = "kritik: gemiyi alır; temiz: kaçar; bedel: yaralanır; kısmi: iz bırakır"
    result = _roll(graded, "kovalama", actor="Işıl", difficulty=4, stakes=stakes)
    assert result["display"] == "Işıl · street sense 5 + 1 karşı 4 → zarsız = kritik · gemiyi alır"
    unkeyed = _roll(graded, "kovalama-2", actor="Işıl", difficulty=6, factors=[], stakes="iz bırakır")
    assert unkeyed["display"] == "Işıl · street sense 5 karşı 6 → zarsız = temiz · risk: iz bırakır"
    # A template band name is written in the play language, whatever key the GM used.
    costly = _roll(graded, "kovalama-3", actor="Işıl", difficulty=7, factors=[], stakes="cost: yaralanır")
    assert costly["display"] == "Işıl · street sense 5 karşı 7 → zarsız = bedelli başarı · yaralanır"


@pytest.mark.parametrize(
    "band, language, expected",
    [
        ("success_with_cost", "tr", "bedelli başarı"),
        ("partial_or_loss", "de", "teilweise oder Verlust"),
        ("Partial Small Cost", "es", "parcial, coste leve"),
        ("partial-heavy-cost", "fr", "partiel, coût lourd"),
        ("partial_medium_cost", "en", "partial medium cost"),
        ("partial_medium_cost", "ja", "partial medium cost"),
        ("FAILURE", "tr", "başarısız"),
        ("crit", "de", "kritisch"),
        ("narrow_escape", "tr", "narrow escape"),
    ],
)
def test_band_labels_follow_the_play_language(band: str, language: str, expected: str) -> None:
    assert roll_dice.band_label(band, language) == expected


def test_every_template_band_phrase_is_in_every_language() -> None:
    names = set(roll_dice.BAND_PHRASES["tr"])
    for code in ("de", "es", "fr"):
        assert set(roll_dice.BAND_PHRASES[code]) == names, code
    profile = (Path(roll_dice.__file__).resolve().parents[1] / "templates" / "campaign" / "play_profile.yaml").read_text(
        encoding="utf-8"
    )
    template_names = set(re.findall(r"band: ([a-z_]+)\}", profile))
    assert template_names and template_names - {"success", "failure"} <= names


def test_display_line_names_the_band_when_its_stakes_are_missing(campaign: Path) -> None:
    _language(campaign, "de")
    request = {"roll_id": "x", "die": "1d6", "call": _call(value=3, difficulty=4, factors=[], stakes="Fehlschlag: weg")}
    result = roll_dice.roll_call(campaign, request)
    assert result["display"] == "Mira · street sense 3 gegen 4 → ohne Wurf = Erfolg"


def test_display_line_shows_a_negative_factor_sum_and_is_clipped(graded: Path) -> None:
    factors = [{"label": "rain", "modifier": -3}, {"label": "rope", "modifier": 1}]
    result = _roll(graded, "long", factors=factors, difficulty=4, stakes="x" * 400)
    assert " 5 - 2 vs 4 → " in result["display"]
    assert len(result["display"]) == roll_dice.DISPLAY_MAX and result["display"].endswith("x…")
    # The stakes clause shortens first, so the band always shows.
    label = roll_dice.band_label(result["band"], "en")
    assert f" = {label} · at stake: xxx" in result["display"]


def test_display_line_drops_the_clause_before_the_numbers(graded: Path) -> None:
    # A 135-character head leaves too little room for any clause.
    result = _roll(graded, "names", actor="A" * 50, axis="b" * 50, difficulty=4, stakes="critical: caught")
    assert len(result["display"]) <= roll_dice.DISPLAY_MAX
    assert "caught" not in result["display"] and " vs 4 → " in result["display"]
    assert result["display"].endswith(f"= {result['band']}")
    longer = _roll(graded, "names-2", actor="A" * 80, axis="b" * 80, difficulty=4, stakes="failure: caught")
    assert len(longer["display"]) == roll_dice.DISPLAY_MAX and longer["display"].endswith("…")


@pytest.mark.parametrize(
    "narration, expected",
    [
        ({"language": "tr"}, "tr"),
        ({"language": "tr-TR"}, "tr"),
        ({"language": "FR"}, "fr"),
        ({"language": "es"}, "es"),
        ({"language": "ja"}, "en"),
        ({"language": "auto", "records_language": "de"}, "de"),
        ({"language": "auto", "records_language": "same"}, "en"),
        ({}, "en"),
    ],
)
def test_play_language(narration: dict, expected: str) -> None:
    assert roll_dice.play_language(_narration(narration)) == expected


@pytest.mark.parametrize(
    "narration, detected, expected",
    [
        ({"language": "auto", "records_language": "same"}, "tr", "tr"),
        ({}, "tr", "tr"),
        # The detected play language comes before a records language, which may differ from it.
        ({"language": "auto", "records_language": "de"}, "fr", "fr"),
        ({"language": "auto", "records_language": "de"}, "", "de"),
        ({"language": "es"}, "tr", "es"),  # a configured language wins
        ({"language": "auto"}, "ja", "en"),
    ],
)
def test_an_auto_play_language_takes_the_detected_one(narration: dict, detected: str, expected: str) -> None:
    assert roll_dice.play_language(_narration(narration), detected) == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        ('{"language": "tr"}', "tr"),
        ('{"language": "TR-tr"}', "tr"),
        ('{"language": null, "play_language": "de"}', "de"),
        ('{"language": "unknown"}', ""),
        ('["tr"]', ""),
        ("{not json", ""),
        (None, ""),
    ],
)
def test_detected_language_reads_the_lint_record(campaign: Path, content: str | None, expected: str) -> None:
    if content is not None:
        _lint_record(campaign, content)
    assert roll_dice.detected_language(campaign) == expected


def test_an_auto_play_language_follows_the_language_the_lint_detected(graded: Path) -> None:
    # Quick, Standard and Companion campaigns keep the template's `language: auto`.
    _language(graded, "auto", "same")
    stakes = "temiz: kaçar; kısmi: iz bırakır"
    before = _roll(graded, "before", difficulty=6, factors=[], stakes=stakes)
    assert before["display"] == "Mira · street sense 5 vs 6 → no roll = clean · kaçar"
    _lint_record(graded, '{"language": "tr"}')
    after = _roll(graded, "after", difficulty=6, factors=[], stakes=stakes)
    assert after["display"] == "Mira · street sense 5 karşı 6 → zarsız = temiz · kaçar"


def test_every_display_table_has_every_word() -> None:
    keys = set(roll_dice.DISPLAY_WORDS["en"])
    assert {"vs", "auto", "stake"} | set(roll_dice.STAKES_KINDS) == keys
    for code in ("tr", "de", "es", "fr"):
        assert set(roll_dice.DISPLAY_WORDS[code]) == keys, code


# ---------------------------------------------------------------------------
# Output shape
# ---------------------------------------------------------------------------


def test_cli_output_starts_with_the_summary(graded: Path, capsys: pytest.CaptureFixture[str]) -> None:
    request = json.dumps({"roll_id": "cli", "call": _call(difficulty=4, stakes="failure: caught")})
    assert roll_dice.main(["--campaign", str(graded), "--input-json", request]) == 0
    out = capsys.readouterr().out
    receipt = json.loads(out)
    assert list(receipt)[:3] == ["summary", "ok", "repeat"]
    assert receipt["summary"] == f"ok critical margin {receipt['margin']}"
    assert [list(warning)[0] for warning in receipt["warnings"]] == ["rule", "rule"]
    assert out.isascii()
    assert roll_dice.main(["--campaign", str(graded), "--input-json", request]) == 0
    assert capsys.readouterr().out == out.replace('"repeat": false', '"repeat": true')


def test_a_receipt_stored_before_0_4_0_repeats_with_a_built_summary(graded: Path) -> None:
    call = roll_dice.normalize_call(_call())
    legacy = {
        "roll_id": "old",
        "revision": 0,
        "call": call,
        "die": "2d6",
        "dice": [3, 4],
        "total": 13,
        "margin": 4,
        "band": "critical",
        "auto": False,
        "at": NOW,
    }
    path = roll_dice.receipts_path(graded)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")
    again = roll_dice.roll_call(graded, {"roll_id": "old", "call": _call()})
    assert again["repeat"] is True and again["summary"] == "ok critical margin 4"
    assert "display" not in again and again["dice"] == [3, 4]


# ---------------------------------------------------------------------------
# axes
# ---------------------------------------------------------------------------


def test_axes_counts_receipts_per_actor_and_axis(graded: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _roll(graded, "a0", axis="Might", difficulty=13)
    _set_revision(graded, 1)
    _roll(graded, "a1", axis="might", difficulty=4)  # certain: auto
    _roll(graded, "a2", axis="Might", difficulty=13)
    _roll(graded, "a3", actor="Branak", axis="wits", difficulty=13)
    roll_dice.reread(graded, {"roll_id": "a2", "reason": "new bands", "new_band": "clean"}, now=NOW)

    everything = roll_dice.axes(graded)
    assert everything["receipts"] == 4
    assert everything["axes"] == [
        {"actor": "Branak", "axis": "wits", "count": 1, "auto": 0},
        {"actor": "Mira", "axis": "Might", "count": 3, "auto": 1},
    ]
    assert roll_dice.main(["--campaign", str(graded), "axes", "--since-revision", "1"]) == 0
    since = json.loads(capsys.readouterr().out)
    assert list(since)[0] == "summary" and since["summary"] == "ok receipts 3 pairs 2"
    assert since["since_revision"] == 1 and since["receipts"] == 3
    assert {(row["actor"], row["axis"]): row["count"] for row in since["axes"]} == {
        ("Branak", "wits"): 1,
        ("Mira", "might"): 2,
    }


def test_axes_cli_arguments_are_checked(graded: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for argv in (
        ["axes"],
        ["--campaign", str(graded), "axes", "--input-json", "{}"],
        ["--campaign", str(graded), "--since-revision", "2", "--input-json", "{}"],
    ):
        with pytest.raises(SystemExit) as exited:
            roll_dice.main(argv)
        assert exited.value.code == 2
    errors = capsys.readouterr().err
    assert "axes needs --campaign" in errors and "takes no request" in errors and "belongs to the axes" in errors
    assert roll_dice.main(["--campaign", str(tmp_path / "nowhere"), "axes"]) == 2
    assert json.loads(capsys.readouterr().out)["failure_category"] == "campaign_missing"
    assert roll_dice.main(["--campaign", str(graded), "axes"]) == 0
    assert json.loads(capsys.readouterr().out)["axes"] == []


# ---------------------------------------------------------------------------
# reread
# ---------------------------------------------------------------------------


def test_reread_appends_a_row_that_is_never_a_receipt(graded: Path) -> None:
    first = _roll(graded, "fight", difficulty=13)
    _set_revision(graded, 2)
    row = roll_dice.reread(graded, {"roll_id": "fight", "reason": "the cost band moved", "new_band": "clean"}, now=NOW)
    assert row == {
        "summary": "ok reread fight as clean",
        "ok": True,
        "repeat": False,
        "kind": "reread",
        "reread_of": "fight",
        "reason": "the cost band moved",
        "new_band": "clean",
        "revision": 2,
        "at": NOW,
    }
    stored = json.loads(roll_dice.receipts_path(graded).read_text(encoding="utf-8").splitlines()[-1])
    assert set(stored) == {"kind", "reread_of", "reason", "new_band", "revision", "at"}

    # The receipt is unchanged and the reread row is invisible to receipt readers.
    assert roll_dice.find_receipt(graded, "fight")["band"] == first["band"]
    assert [r["roll_id"] for r in roll_dice.read_receipts(graded)] == ["fight"]
    assert roll_dice.open_receipts(graded, 2) == [] and roll_dice.open_receipts(graded, 0)[0]["roll_id"] == "fight"
    assert [r["new_band"] for r in roll_dice.read_rereads(graded)] == ["clean"]
    assert roll_dice.mark_consumed(graded, ["fight"], 3) == ["fight"]
    assert roll_dice.read_rereads(graded)[0].get("consumed_revision") is None


def test_reread_repeats_for_the_newest_identical_reading(graded: Path) -> None:
    _roll(graded, "fight", difficulty=13)
    request = {"roll_id": "fight", "reason": "bands changed", "new_band": "clean"}
    assert roll_dice.reread(graded, request, now=NOW)["repeat"] is False
    assert roll_dice.reread(graded, request, now="later")["repeat"] is True
    assert roll_dice.reread(graded, {**request, "new_band": "failure"}, now=NOW)["repeat"] is False
    assert roll_dice.reread(graded, request, now=NOW)["repeat"] is False  # back to clean: a new reading
    assert [row["new_band"] for row in roll_dice.read_rereads(graded)] == ["clean", "failure", "clean"]


@pytest.mark.parametrize(
    "request_, category, fragment",
    [
        ({"roll_id": "ghost", "reason": "r", "new_band": "clean"}, "input_invalid", "names no recorded roll"),
        ({"roll_id": "fight", "reason": "r", "new_band": "great"}, "input_invalid", "is not a band of this campaign"),
        ({"roll_id": "fight", "reason": "", "new_band": "clean"}, "input_invalid", "reason must be non-empty"),
        ({"roll_id": "fight", "new_band": "clean"}, "input_invalid", "reason must be non-empty"),
        ({"roll_id": "player: 2d6", "reason": "r", "new_band": "clean"}, "input_invalid", "roll_id must be"),
        (
            {"roll_id": "fight", "reason": "r", "new_band": "clean", "band": "x"},
            "input_invalid",
            "unknown keys: band; accepted keys: roll_id, reason, new_band (required)",
        ),
    ],
)
def test_reread_refusals(graded: Path, request_: dict, category: str, fragment: str) -> None:
    _roll(graded, "fight", difficulty=13)
    before = roll_dice.receipts_path(graded).read_bytes()
    with pytest.raises(roll_dice.RollCallError) as caught:
        roll_dice.reread(graded, request_)
    assert caught.value.category == category and fragment in str(caught.value)
    assert roll_dice.receipts_path(graded).read_bytes() == before


def test_reread_rows_do_not_block_or_shadow_a_roll_id(graded: Path) -> None:
    first = _roll(graded, "fight", difficulty=13)
    roll_dice.reread(graded, {"roll_id": "fight", "reason": "bands changed", "new_band": "clean"}, now=NOW)
    again = _roll(graded, "fight", difficulty=13)
    assert again["repeat"] is True and again["band"] == first["band"]


def test_reread_cli_reads_standard_input(
    graded: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _roll(graded, "fight", difficulty=13)
    data = json.dumps({"roll_id": "fight", "reason": "bantlar değişti", "new_band": "clean"}, ensure_ascii=False)
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(data.encode("utf-8")), encoding="cp1252"))
    assert roll_dice.main(["--campaign", str(graded), "reread", "--input-file", "-"]) == 0
    out = capsys.readouterr().out
    result = json.loads(out)
    assert list(result)[0] == "summary" and result["reason"] == "bantlar değişti" and out.isascii()
    with pytest.raises(SystemExit):
        roll_dice.main(["reread", "--input-json", data])
    assert roll_dice.main(["--campaign", str(graded), "reread", "--input-json", '{"roll_id": "fight"}']) == 2
    assert json.loads(capsys.readouterr().out)["failure_category"] == "input_invalid"

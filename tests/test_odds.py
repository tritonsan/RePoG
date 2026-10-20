"""Exact odds and scale exhaustion for the declared resolution scale."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import odds


LIVE_SCALE = """schema_version: 2
mechanics:
  modules: []
  resolution_grounding: fictional
  dice_mode: open_gm_rolls
  resolution:
    die: 1d2              # any NdM
    stat_min: 1
    stat_max: 5
    difficulty_min: 1
    difficulty_max: 5
    auto_success_margin: 2     # stat - difficulty >= this succeeds without a roll
    bands:                     # margin = total - difficulty; first match wins
      - {at_least: 0, band: success}
      - {at_least: -1, band: partial_small_cost}
      - {at_least: -2, band: partial_medium_cost}
      - {at_least: -99, band: partial_heavy_cost}

narration:
  language: auto
"""

HEALTHY_SCALE = """mechanics:
  resolution:
    die: 1d6
    stat_min: 1
    stat_max: 5
    difficulty_min: 3
    difficulty_max: 10
    bands:
      - {at_least: 0, band: success}
      - {at_least: -99, band: failure}
"""


def _write(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def test_load_resolution_parses_the_documented_block() -> None:
    resolution = odds.load_resolution(LIVE_SCALE)
    assert resolution == {
        "die": "1d2",
        "dice_count": 1,
        "dice_sides": 2,
        "stat_min": 1,
        "stat_max": 5,
        "difficulty_min": 1,
        "difficulty_max": 5,
        "auto_success_margin": 2,
        "bands": [
            {"at_least": 0, "band": "success"},
            {"at_least": -1, "band": "partial_small_cost"},
            {"at_least": -2, "band": "partial_medium_cost"},
            {"at_least": -99, "band": "partial_heavy_cost"},
        ],
    }


def test_load_resolution_is_none_without_a_block() -> None:
    assert odds.load_resolution("") is None
    assert odds.load_resolution("mechanics:\n  modules: []\n  resolution_grounding: fictional\n") is None
    # A `resolution:` key outside `mechanics:` is not the scale.
    assert odds.load_resolution("narration:\n  resolution:\n    die: 1d6\n") is None


def test_block_flow_and_indentless_band_lists_parse_alike() -> None:
    block = (
        "mechanics:\n  resolution:\n    die: 2d6\n    bands:\n"
        "      - at_least: 0\n        band: success\n      - at_least: -3\n        band: failure\n"
    )
    flow = "mechanics:\n  resolution:\n    die: 2d6\n    bands: [{at_least: 0, band: success}, {at_least: -3, band: failure}]\n"
    indentless = (
        "mechanics:\n  resolution:\n    die: 2d6\n    bands:\n"
        "    - {at_least: 0, band: success}\n    - {at_least: -3, band: \"failure\"}\n"
    )
    parsed = [odds.load_resolution(text) for text in (block, flow, indentless)]
    assert parsed[0] == parsed[1] == parsed[2]
    assert parsed[0]["bands"] == [{"at_least": 0, "band": "success"}, {"at_least": -3, "band": "failure"}]


def test_defaults_fill_scale_and_bands() -> None:
    resolution = odds.load_resolution("mechanics:\n  resolution:\n    die: 1D6\n")
    assert resolution["die"] == "1d6"
    assert (resolution["stat_min"], resolution["stat_max"]) == (1, 5)
    assert (resolution["difficulty_min"], resolution["difficulty_max"]) == (1, 5)
    assert resolution["auto_success_margin"] is None
    assert [band["band"] for band in resolution["bands"]] == ["success", "failure"]


@pytest.mark.parametrize(
    "body, fragment",
    [
        ("    die: d6\n", "NdM"),
        ("    die: 20d6\n", "die count"),
        ("    stat_max: 5\n", "die is required"),
        ("    die: 1d6\n    stat_min: 6\n    stat_max: 5\n", "must not exceed"),
        ("    die: 1d6\n    auto_success_margn: 2\n", "unknown keys"),
        ("    die: 1d6\n    stat_max: high\n", "integer"),
        ("    die: 1d6\n    bands: []\n", "at least one band"),
        ("    die: 1d6\n    bands:\n      - {at_least: 0}\n", "exactly at_least and band"),
        ("    die: 1d6\n    bands:\n      - {at_least: 0, band: a}\n      - {at_least: -1, band: a}\n", "repeats"),
        # A band listed below a lower or equal threshold could never be reached.
        ("    die: 1d6\n    bands:\n      - {at_least: -99, band: failure}\n      - {at_least: 0, band: success}\n",
         "can never be reached"),
        ("    die: 1d6\n    bands:\n      - {at_least: 0, band: success}\n      - {at_least: 0, band: partial}\n",
         "can never be reached"),
        ("    die: 1d6\n    stat_max: 1001\n", "between -1000 and 1000"),
        # Tab indentation would otherwise end the block early and drop keys silently.
        ("    die: 1d6\n\tstat_max: 9\n", "spaces, not tabs"),
    ],
)
def test_invalid_blocks_raise_typed_errors(body: str, fragment: str) -> None:
    with pytest.raises(odds.ResolutionError, match=fragment):
        odds.load_resolution("mechanics:\n  resolution:\n" + body)


def test_bom_and_crlf_profiles_parse_like_plain_ones() -> None:
    plain = odds.load_resolution(LIVE_SCALE)
    assert odds.load_resolution("\ufeff" + LIVE_SCALE.replace("schema_version: 2\n", "", 1)) == plain
    assert odds.load_resolution(LIVE_SCALE.replace("\n", "\r\n")) == plain


def test_inline_or_nested_resolution_is_never_silently_ignored() -> None:
    with pytest.raises(odds.ResolutionError, match="indented block"):
        odds.load_resolution("mechanics:\n  resolution: {die: 1d6, stat_max: 7}\n")
    assert odds.load_resolution("mechanics:\n  resolution: null\n  dice_mode: open_gm_rolls\n") is None
    assert odds.load_resolution("mechanics:\n  resolution: ~  # off for now\n") is None
    # Only a key directly under `mechanics:` is the scale, not one nested in another key.
    nested = "mechanics:\n  modules:\n    combat:\n      resolution:\n        die: 1d20\n  dice_mode: hybrid\n"
    assert odds.load_resolution(nested) is None
    with pytest.raises(odds.ResolutionError, match="spaces, not tabs"):
        odds.load_resolution("mechanics:\n\tresolution:\n\t\tdie: 1d6\n")


@pytest.mark.parametrize("separator", [" ", " ", "\x85", "\x0c", "\x1c"])
def test_only_lf_and_cr_end_a_line(separator: str) -> None:
    # str.splitlines would end the block inside this comment and silently drop stat_max.
    text = f"mechanics:\n  resolution:\n    die: 1d6  # note{separator}more\n    stat_max: 9\n"
    assert odds.load_resolution(text)["stat_max"] == 9
    assert odds.load_resolution(text.replace("\n", "\r"))["stat_max"] == 9  # CR-only files too


@pytest.mark.parametrize("key", ["resolution :", '"resolution":', "'resolution' :"])
def test_a_spaced_or_quoted_resolution_key_is_still_the_scale(key: str) -> None:
    # Valid YAML for the same key; missing it would drop the scale and let a caller pick any die.
    text = f"mechanics:\n  dice_mode: open_gm_rolls\n  {key}\n    die: 1d6\n    stat_max: 9\n"
    assert odds.load_resolution(text)["stat_max"] == 9
    assert odds.load_resolution(f'"mechanics" :  # quoted\n  {key}\n    die: 1d6\n')["die"] == "1d6"
    with pytest.raises(odds.ResolutionError, match="inline value"):
        odds.load_resolution(f"mechanics:\n  {key} 1d6\n")
    with pytest.raises(odds.ResolutionError, match="spaces, not tabs"):
        odds.load_resolution(f"mechanics:\n\t{key}\n\t\tdie: 1d6\n")


def test_a_tab_indented_sibling_does_not_hide_the_block() -> None:
    # The tab line must not set the sibling indent and make `resolution:` look nested.
    text = "mechanics:\n\tmodules: []\n  resolution:\n    die: 1d6\n    stat_max: 9\n"
    assert odds.load_resolution(text)["stat_max"] == 9


def test_hand_built_blocks_are_validated() -> None:
    with pytest.raises(odds.ResolutionError, match="mapping"):
        odds.normalize_resolution(["die", "1d6"])  # type: ignore[arg-type]
    for name in ("hit\u2028miss", "hit\x85miss", "hit\tmiss", "hit\ud800miss"):
        with pytest.raises(odds.ResolutionError, match="one line"):
            odds.normalize_resolution({"die": "1d6", "bands": [{"at_least": 0, "band": name}]})
    edge = odds.normalize_resolution({"die": "1d6", "difficulty_min": 950, "difficulty_max": 1000})
    assert edge["difficulty_max"] == 1000
    named = odds.normalize_resolution({"die": "1d6", "bands": [{"at_least": 0, "band": "  başarı "}]})
    assert named["bands"] == [{"at_least": 0, "band": "başarı"}]


def _brute_force_ways(resolution: dict, stat: int, difficulty: int) -> dict[str, int]:
    bands = resolution["bands"]
    ways = {band["band"]: 0 for band in bands}
    total = resolution["dice_sides"] ** resolution["dice_count"]
    if odds.is_auto(resolution, stat, difficulty):
        ways[bands[0]["band"]] = total
        return ways
    for rolled, number in odds.die_distribution(resolution["dice_count"], resolution["dice_sides"]).items():
        ways[odds.band_for(stat + rolled - difficulty, bands)] += number
    return ways


@pytest.mark.parametrize("die", ["1d2", "1d6", "2d6", "3d4", "1d20"])
@pytest.mark.parametrize("auto", [None, 2])
def test_band_counts_match_brute_force_enumeration(die: str, auto: int | None) -> None:
    resolution = odds.normalize_resolution(
        {
            "die": die,
            "stat_min": -2,
            "stat_max": 6,
            "difficulty_min": 1,
            "difficulty_max": 14,
            "auto_success_margin": auto,
            "bands": [
                {"at_least": 3, "band": "strong"},
                {"at_least": 0, "band": "success"},
                {"at_least": -2, "band": "partial"},
                {"at_least": -5, "band": "failure"},
            ],
        }
    )
    for stat in range(-2, 7):
        for difficulty in range(1, 15):
            ways, total = odds.band_ways(resolution, stat, difficulty)
            assert ways == _brute_force_ways(resolution, stat, difficulty)
            assert sum(ways.values()) == total


def test_unsorted_hand_built_bands_still_count_exactly() -> None:
    # band_ways falls back to enumeration for a resolution that skipped normalization.
    resolution = {
        "die": "1d6", "dice_count": 1, "dice_sides": 6, "stat_min": 1, "stat_max": 3,
        "difficulty_min": 1, "difficulty_max": 6, "auto_success_margin": None,
        "bands": [{"at_least": -9, "band": "floor"}, {"at_least": 0, "band": "success"}],
    }
    for stat in range(1, 4):
        for difficulty in range(1, 7):
            assert odds.band_ways(resolution, stat, difficulty)[0] == _brute_force_ways(resolution, stat, difficulty)


def test_format_table_escapes_pipes_in_band_names() -> None:
    resolution = odds.normalize_resolution(
        {"die": "1d6", "bands": [{"at_least": 0, "band": "yes|but"}, {"at_least": -9, "band": "no"}]}
    )
    output = odds.format_table(resolution)
    assert "| Stat | Difficulty | Roll | yes\\|but | no |" in output


def test_band_for_uses_first_match_and_last_band_as_floor() -> None:
    bands = odds.load_resolution(LIVE_SCALE)["bands"]
    assert odds.band_for(3, bands) == "success"
    assert odds.band_for(0, bands) == "success"
    assert odds.band_for(-1, bands) == "partial_small_cost"
    assert odds.band_for(-2, bands) == "partial_medium_cost"
    assert odds.band_for(-3, bands) == "partial_heavy_cost"
    assert odds.band_for(-500, bands) == "partial_heavy_cost"


def test_die_distribution_is_exact() -> None:
    two_d6 = odds.die_distribution(2, 6)
    assert sum(two_d6.values()) == 36
    assert two_d6[7] == 6 and two_d6[2] == 1 and two_d6[12] == 1


def test_success_table_on_the_live_scale() -> None:
    table = odds.success_table(odds.load_resolution(LIVE_SCALE))
    assert len(table) == 25
    for cell in table.values():
        assert sum(cell.values()) == pytest.approx(1.0)
    # 1 + d2 vs 3 -> margins -1 or 0.
    assert table[(1, 3)] == {
        "success": 0.5,
        "partial_small_cost": 0.5,
        "partial_medium_cost": 0.0,
        "partial_heavy_cost": 0.0,
    }
    # 1 + d2 vs 5 -> margins -3 or -2.
    assert table[(1, 5)]["partial_medium_cost"] == 0.5
    assert table[(1, 5)]["partial_heavy_cost"] == 0.5
    # 5 vs 3 clears the auto margin: certain, no roll.
    assert table[(5, 3)]["success"] == 1.0
    assert odds.is_auto(odds.load_resolution(LIVE_SCALE), 5, 3)


def test_live_scale_is_exhausted_at_stat_five() -> None:
    resolution = odds.load_resolution(LIVE_SCALE)
    findings = odds.exhaustion_findings(resolution)
    rules = {finding["rule"]: finding for finding in findings}
    assert rules["scale_exhausted"]["severity"] == "warning"
    assert "stat 5" in rules["scale_exhausted"]["message"]
    assert "starts at stat 4" in rules["scale_exhausted"]["message"]
    assert rules["first_band_unreachable"]["severity"] == "info"
    assert "stat 1 vs difficulty 4-5" in rules["first_band_unreachable"]["message"]
    warnings = odds.exhaustion(resolution)
    assert warnings[0].startswith("scale_exhausted: ")


def test_one_d6_on_the_same_one_to_five_scale_is_still_exhausted() -> None:
    # The die only adds, so stat 5 vs difficulty 5 never falls below margin +1.
    resolution = odds.load_resolution("mechanics:\n  resolution:\n    die: 1d6\n")
    assert any(line.startswith("scale_exhausted") for line in odds.exhaustion(resolution))


def _exhausted(resolution: dict) -> list[dict[str, str]]:
    return [f for f in odds.exhaustion_findings(resolution) if f["rule"] == "scale_exhausted"]


@pytest.mark.parametrize(
    "block, needed",
    [
        (LIVE_SCALE, 7),  # 5 + 1d2 vs 6 still never drops below margin 0
        ("mechanics:\n  resolution:\n    die: 1d6\n", 7),
        ("mechanics:\n  resolution:\n    die: 3d6\n    difficulty_max: 8\n", 9),
        # The auto-success margin, not the die, sets the bar here.
        ("mechanics:\n  resolution:\n    die: 1d6\n    auto_success_margin: -3\n    difficulty_max: 8\n", 9),
        (
            "mechanics:\n  resolution:\n    die: 1d6\n    stat_min: -3\n    stat_max: -1\n"
            "    difficulty_min: -4\n    difficulty_max: -2\n",
            1,
        ),
    ],
)
def test_scale_exhausted_names_the_difficulty_that_restores_risk(block: str, needed: int) -> None:
    resolution = odds.load_resolution(block)
    (warning,) = _exhausted(resolution)
    message = warning["message"]
    assert f"raise difficulty_max to at least {needed} " in message
    assert "change the die" not in message
    assert odds.risky_difficulty(resolution, resolution["stat_max"]) == needed
    # The named difficulty is exactly the fix: one less stays exhausted ...
    assert _exhausted({**resolution, "difficulty_max": needed - 1, "difficulty_min": min(resolution["difficulty_min"], needed - 1)})
    assert not _exhausted({**resolution, "difficulty_max": needed})
    # ... and a die with more sides alone does not help.
    count = resolution["dice_count"]
    assert _exhausted({**resolution, "die": f"{count}d100", "dice_sides": 100})


def test_normalize_resolution_accepts_its_own_output() -> None:
    # Stage 2 may re-validate a loaded scale or an adjusted copy of it.
    resolution = odds.load_resolution(LIVE_SCALE)
    assert odds.normalize_resolution(resolution) == resolution
    raised = odds.normalize_resolution({**resolution, "difficulty_max": 7})
    assert raised["difficulty_max"] == 7 and not _exhausted(raised)
    with pytest.raises(odds.ResolutionError, match="dice_sides 2 does not match die '1d6'"):
        odds.normalize_resolution({**resolution, "die": "1d6"})


def test_a_single_band_scale_asks_for_a_lower_band() -> None:
    resolution = odds.normalize_resolution(
        {"die": "1d6", "difficulty_max": 60, "bands": [{"at_least": 0, "band": "success"}]}
    )
    assert odds.risky_difficulty(resolution, 5) is None
    (warning,) = _exhausted(resolution)
    assert "add a lower band" in warning["message"]
    assert "difficulty_max to at least" not in warning["message"]


def test_negative_ranges_print_without_double_minus() -> None:
    assert (odds.span(1, 5), odds.span(-3, -1), odds.span(-2, 2), odds.span(0, 0)) == ("1-5", "-3 to -1", "-2 to 2", "0-0")
    resolution = odds.normalize_resolution(
        {"die": "1d2", "stat_min": -3, "stat_max": -1, "difficulty_min": -2, "difficulty_max": 2}
    )
    output = odds.format_table(resolution)
    assert "- Stat -3 to -1; difficulty -2 to 2." in output
    # -3 + 1d2 vs 0..2 never reaches margin 0: the info line groups those difficulties.
    assert "stat -3 vs difficulty 0-2; stat -2 vs difficulty 1-2; stat -1 vs difficulty 2" in output
    assert "scale_exhausted" not in output  # -1 + 1d2 vs 2 can still fail
    exhausted = odds.normalize_resolution(
        {"die": "1d6", "stat_min": -3, "stat_max": -1, "difficulty_min": -4, "difficulty_max": -2}
    )
    assert "every difficulty -4 to -2 gives success" in _exhausted(exhausted)[0]["message"]


def test_healthier_scale_keeps_risk_at_the_top_stat() -> None:
    resolution = odds.load_resolution(HEALTHY_SCALE)
    lines = odds.exhaustion(resolution)
    assert not any(line.startswith("scale_exhausted") for line in lines)
    table = odds.success_table(resolution)
    # 5 + d6 vs 10 -> success on 5 or 6.
    assert table[(5, 10)]["success"] == pytest.approx(2 / 6)
    assert table[(5, 10)]["failure"] == pytest.approx(4 / 6)


def test_format_table_and_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "campaign"
    root.mkdir()
    _write(root / "play_profile.yaml", LIVE_SCALE)
    assert odds.main([str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "| Stat \\ Difficulty | 1 | 2 | 3 | 4 | 5 |" in output
    assert "| 1 | 3 | roll | 50% | 50% | 0% | 0% |" in output
    assert "| 5 | 1 | auto | 100% |" in output
    assert "scale_exhausted (warning)" in output

    _write(root / "play_profile.yaml", "schema_version: 2\n")
    assert odds.main([str(root)]) == 1
    assert "No mechanics.resolution" in capsys.readouterr().out

    _write(root / "play_profile.yaml", "mechanics:\n  resolution:\n    die: 1d1\n")
    assert odds.main([str(root)]) == 2
    assert "die sides" in capsys.readouterr().out


def test_cli_reads_the_profile_strictly_as_utf8(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "campaign"
    root.mkdir()
    profile = root / "play_profile.yaml"
    profile.write_bytes(LIVE_SCALE.replace("band: success", "band: başarı").encode("cp1254"))
    assert odds.main([str(root)]) == 2
    assert "play_profile.yaml is not valid UTF-8" in capsys.readouterr().out

    windows = LIVE_SCALE.replace("band: success", "band: başarı").replace("\n", "\r\n")
    profile.write_bytes(b"\xef\xbb\xbf" + windows.encode("utf-8"))
    assert odds.main([str(root)]) == 0
    assert "## Chance of başarı" in capsys.readouterr().out


def test_percent_formatting_keeps_tiny_odds_visible() -> None:
    assert odds._percent(1, 3) == "33.3%"
    assert odds._percent(1, 3000) == "<0.1%"
    assert odds._percent(2999, 3000) == ">99.9%"
    assert odds._percent(2, 2) == "100%"

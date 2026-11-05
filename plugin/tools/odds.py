"""Exact odds for a campaign's declared resolution scale.

A roll call (`tools/roll_dice.py --campaign`) adds a die to a stat plus
declared modifiers and compares the total with a declared difficulty. Whether
that scale still carries any risk is plain arithmetic, so this module
enumerates the die exactly and reports, for every stat and difficulty on the
scale, the chance of each outcome band. It also flags a scale that progression
has exhausted (the top stat succeeds against every difficulty), so the table
can be raised through an OOC rules change before rolls go hollow.

The resolution block is optional and lives in `play_profile.yaml`:

    mechanics:
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

Bands are listed from the highest `at_least` down (a band listed below a
lower or equal threshold could never be reached, so that is refused). The
first band whose `at_least` the margin reaches wins; a margin below every
threshold falls into the last band. The module never decides what a band
means in the fiction.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any


DIE_RE = re.compile(r"^\s*(\d{1,2})[dD](\d{1,3})\s*$")
MAX_DICE = 10
MAX_SIDES = 100
MAX_SPAN = 100  # values in one stat or difficulty range, so the table stays small
MAX_ABS_SCALE = 1000  # matches the call-mode limit on value and difficulty in roll_dice
MAX_BANDS = 12
MAX_BAND_NAME = 60
SUMMARY_STATS = 3  # stats named in the first_band_unreachable summary
LINE_BREAKING = frozenset({"Cc", "Zl", "Zp"})  # control, line and paragraph separators
# A lone surrogate (only possible in a hand-built block) could not be stored in a receipt.
BAND_NAME_REFUSED = LINE_BREAKING | {"Cs"}

SCALE_DEFAULTS: dict[str, int] = {"stat_min": 1, "stat_max": 5, "difficulty_min": 1, "difficulty_max": 5}
DEFAULT_BANDS: tuple[dict[str, Any], ...] = (
    {"at_least": 0, "band": "success"},
    {"at_least": -999, "band": "failure"},
)
ALLOWED_KEYS = frozenset({"die", "bands", "auto_success_margin", *SCALE_DEFAULTS})
DERIVED_KEYS = frozenset({"dice_count", "dice_sides"})  # added by normalize_resolution
BAND_KEYS = frozenset({"at_least", "band"})

KEY_VALUE_RE = re.compile(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$")
FLOW_MAP_RE = re.compile(r"\{[^{}]*\}")
# YAML allows blanks before the colon and a quoted key; missing either would
# silently drop the whole scale.
MECHANICS_KEY_RE = re.compile(r"""^(["']?)mechanics\1[ \t]*:[ \t]*(#.*)?$""")
RESOLUTION_KEY_RE = re.compile(r"""^(["']?)resolution\1[ \t]*:(.*)$""")


class ResolutionError(ValueError):
    """A `mechanics.resolution` block that cannot be used exactly as written."""

    category = "resolution_invalid"


# ---------------------------------------------------------------------------
# Parsing play_profile.yaml
# ---------------------------------------------------------------------------


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _uncomment(text: str) -> str:
    return re.sub(r"(^|\s)#.*$", "", text).strip()


def _scalar(value: str) -> str:
    value = _uncomment(value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value


def _pair(text: str) -> tuple[str, str]:
    match = KEY_VALUE_RE.match(text.strip())
    if match is None:
        raise ResolutionError(f"mechanics.resolution: expected `key: value`, found {text.strip()!r}")
    return match.group(1), _scalar(match.group(2))


def _flow_mapping(text: str) -> dict[str, str]:
    text = text.strip()
    if not (text.startswith("{") and text.endswith("}")):
        raise ResolutionError(f"mechanics.resolution: expected an inline mapping, found {text!r}")
    mapping: dict[str, str] = {}
    for part in text[1:-1].split(","):
        if not part.strip():
            continue
        key, value = _pair(part)
        if key in mapping:
            raise ResolutionError(f"mechanics.resolution: duplicate key {key!r} in {text!r}")
        mapping[key] = value
    return mapping


def _flow_list(text: str) -> list[dict[str, str]]:
    text = text.strip()
    if not (text.startswith("[") and text.endswith("]")):
        raise ResolutionError(f"mechanics.resolution.bands: expected a list, found {text!r}")
    inner = text[1:-1]
    if FLOW_MAP_RE.sub("", inner).replace(",", "").strip():
        raise ResolutionError("mechanics.resolution.bands: list items must be inline mappings")
    return [_flow_mapping(item) for item in FLOW_MAP_RE.findall(inner)]


def _block_items(lines: list[str], start: int, parent_indent: int) -> tuple[list[dict[str, str]], int]:
    """Parse `- {..}` or `- key: value` list items below `bands:`."""

    items: list[dict[str, str]] = []
    index = start
    while index < len(lines):
        line = lines[index]
        stripped = _uncomment(line)
        is_item = stripped == "-" or stripped.startswith("- ")
        if _indent(line) < parent_indent or (_indent(line) == parent_indent and not is_item):
            break
        if is_item:
            body = stripped[1:].strip()
            if body.startswith("{"):
                items.append(_flow_mapping(body))
            else:
                items.append(dict([_pair(body)]) if body else {})
        else:
            if not items:
                raise ResolutionError(f"mechanics.resolution.bands: unexpected line {stripped!r}")
            key, value = _pair(stripped)
            if key in items[-1]:
                raise ResolutionError(f"mechanics.resolution.bands: duplicate key {key!r}")
            items[-1][key] = value
        index += 1
    return items, index


def _lines(text: str) -> list[str]:
    """Split where YAML splits: at LF, CR LF, or a lone CR, nowhere else.

    `str.splitlines` also breaks at U+2028, U+2029, U+0085, and a few control
    characters; one of those inside a comment would end the block early and
    silently drop every key after it.
    """

    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _resolution_lines(text: str) -> list[str] | None:
    """Content lines nested under `mechanics:` -> `resolution:`, or None.

    Only a `resolution:` key directly under `mechanics:` counts. An explicit
    `resolution: null` (or `~`) is absent; any other inline value, and tab
    indentation inside the block, is refused rather than silently ignored.
    """

    inside_mechanics = False
    child_indent: int | None = None
    resolution_indent: int | None = None
    collected: list[str] = []
    for line in _lines(text):
        if not inside_mechanics:
            inside_mechanics = MECHANICS_KEY_RE.match(line) is not None
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith((" ", "\t")):
            break  # next top-level key
        leading = line[: len(line) - len(line.lstrip(" \t"))]
        inside_block = resolution_indent is not None
        if "\t" in leading:
            if inside_block or RESOLUTION_KEY_RE.match(stripped):
                raise ResolutionError("mechanics.resolution: indent with spaces, not tabs")
            # Another tab-indented key: it must not set the sibling indent, or
            # a correctly indented `resolution:` after it would be skipped.
            continue
        indent = _indent(line)
        if child_indent is None:
            child_indent = indent
        if not inside_block:
            match = RESOLUTION_KEY_RE.match(stripped)
            if match is None or indent != child_indent:
                continue
            inline = _uncomment(match.group(2))
            if inline in {"null", "Null", "NULL", "~"}:
                return None
            if inline:
                raise ResolutionError(
                    "mechanics.resolution must be an indented block of `key: value` lines, "
                    f"not an inline value ({inline!r})"
                )
            resolution_indent = indent
            continue
        if indent <= resolution_indent:
            break
        collected.append(line)
    return None if resolution_indent is None else collected


def _parse_block(lines: list[str]) -> dict[str, Any]:
    raw: dict[str, Any] = {}
    if not lines:
        return raw
    child = _indent(lines[0])
    index = 0
    while index < len(lines):
        line = lines[index]
        if _indent(line) != child:
            raise ResolutionError(f"mechanics.resolution: unexpected indentation at {line.strip()!r}")
        key, value = _pair(_uncomment(line))
        if key in raw:
            raise ResolutionError(f"mechanics.resolution: duplicate key {key!r}")
        if key == "bands":
            if value:
                raw[key] = _flow_list(value)
                index += 1
            else:
                raw[key], index = _block_items(lines, index + 1, child)
            continue
        raw[key] = value
        index += 1
    return raw


def load_resolution(play_profile_text: str) -> dict[str, Any] | None:
    """The normalized `mechanics.resolution` block, or None when absent.

    Raises `ResolutionError` when the block exists but cannot be used.
    """

    if play_profile_text.startswith("\ufeff"):
        play_profile_text = play_profile_text[1:]  # a BOM must not hide a first-line `mechanics:`
    lines = _resolution_lines(play_profile_text)
    if lines is None:
        return None
    return normalize_resolution(_parse_block(lines))


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def parse_die(expression: Any) -> tuple[int, int]:
    """`NdM` -> (count, sides), bounded so the die can be enumerated exactly."""

    if not isinstance(expression, str):
        raise ResolutionError("die must be text in NdM form, such as 1d6")
    match = DIE_RE.match(expression)
    if match is None:
        raise ResolutionError(f"die must use NdM form, such as 1d6; found {expression!r}")
    count, sides = int(match.group(1)), int(match.group(2))
    if not 1 <= count <= MAX_DICE:
        raise ResolutionError(f"die count must be between 1 and {MAX_DICE}")
    if not 2 <= sides <= MAX_SIDES:
        raise ResolutionError(f"die sides must be between 2 and {MAX_SIDES}")
    return count, sides


def _integer(value: Any, label: str) -> int:
    if type(value) is int:
        return value
    if isinstance(value, str) and re.fullmatch(r"[+-]?\d{1,6}", value.strip()):
        return int(value.strip())
    raise ResolutionError(f"{label} must be an integer")


def _bands(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return [dict(band) for band in DEFAULT_BANDS]
    if not isinstance(raw, list) or not raw:
        raise ResolutionError("mechanics.resolution.bands must list at least one band")
    if len(raw) > MAX_BANDS:
        raise ResolutionError(f"mechanics.resolution.bands may list at most {MAX_BANDS} bands")
    bands: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position, item in enumerate(raw):
        label = f"mechanics.resolution.bands[{position}]"
        if not isinstance(item, dict) or set(item) != BAND_KEYS:
            raise ResolutionError(f"{label} needs exactly at_least and band")
        name = item["band"]
        if (
            not isinstance(name, str)
            or not name.strip()
            or len(name.strip()) > MAX_BAND_NAME
            or any(unicodedata.category(char) in BAND_NAME_REFUSED for char in name.strip())
        ):
            raise ResolutionError(f"{label}.band must be one line of at most {MAX_BAND_NAME} valid characters")
        name = unicodedata.normalize("NFC", name.strip())
        if name in seen:
            raise ResolutionError(f"{label}.band repeats {name!r}")
        seen.add(name)
        at_least = _integer(item["at_least"], f"{label}.at_least")
        if bands and at_least >= bands[-1]["at_least"]:
            raise ResolutionError(
                f"{label} ({name}, at_least {at_least}) can never be reached below "
                f"{bands[-1]['band']} (at_least {bands[-1]['at_least']}); list bands from the "
                "highest at_least down, because the first match wins"
            )
        bands.append({"at_least": at_least, "band": name})
    return bands


def _scale(raw: dict[str, Any]) -> dict[str, int]:
    scale: dict[str, int] = {}
    for key, default in SCALE_DEFAULTS.items():
        value = _integer(raw.get(key, default), f"mechanics.resolution.{key}")
        if abs(value) > MAX_ABS_SCALE:
            raise ResolutionError(f"mechanics.resolution.{key} must be between -{MAX_ABS_SCALE} and {MAX_ABS_SCALE}")
        scale[key] = value
    for prefix in ("stat", "difficulty"):
        low, high = scale[f"{prefix}_min"], scale[f"{prefix}_max"]
        if low > high:
            raise ResolutionError(f"mechanics.resolution.{prefix}_min must not exceed {prefix}_max")
        if high - low + 1 > MAX_SPAN:
            raise ResolutionError(f"mechanics.resolution {prefix} range may hold at most {MAX_SPAN} values")
    return scale


def normalize_resolution(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate a parsed or hand-built resolution block and fill defaults.

    Idempotent: a normalized resolution (with its derived `dice_count` and
    `dice_sides`) normalizes to itself, so a caller can re-validate an
    adjusted copy; the derived keys must agree with `die`.
    """

    if not isinstance(raw, dict):
        raise ResolutionError("mechanics.resolution must be a mapping")
    unknown = sorted(set(raw) - ALLOWED_KEYS - DERIVED_KEYS)
    if unknown:
        raise ResolutionError(f"mechanics.resolution has unknown keys: {', '.join(unknown)}")
    if raw.get("die") in (None, ""):
        raise ResolutionError("mechanics.resolution.die is required, such as 1d6")
    count, sides = parse_die(raw["die"])
    for key, derived in (("dice_count", count), ("dice_sides", sides)):
        if key in raw and _integer(raw[key], f"mechanics.resolution.{key}") != derived:
            raise ResolutionError(f"mechanics.resolution.{key} {raw[key]!r} does not match die {raw['die']!r}")
    scale = _scale(raw)
    auto = raw.get("auto_success_margin")
    if isinstance(auto, str) and auto.strip().lower() in {"", "null", "~", "none"}:
        auto = None
    return {
        "die": f"{count}d{sides}",
        "dice_count": count,
        "dice_sides": sides,
        **scale,
        "auto_success_margin": None if auto is None else _integer(auto, "mechanics.resolution.auto_success_margin"),
        "bands": _bands(raw.get("bands")),
    }


# ---------------------------------------------------------------------------
# Outcomes
# ---------------------------------------------------------------------------


def band_for(margin: int, bands: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> str:
    """First band whose threshold the margin reaches; else the last band."""

    for band in bands:
        if margin >= band["at_least"]:
            return band["band"]
    return bands[-1]["band"]


def is_auto(resolution: dict[str, Any] | None, value: int, difficulty: int, modifiers: int = 0) -> bool:
    """True when the call succeeds without a roll under `auto_success_margin`."""

    if not resolution or resolution.get("auto_success_margin") is None:
        return False
    return value + modifiers - difficulty >= resolution["auto_success_margin"]


@lru_cache(maxsize=64)
def _distribution(count: int, sides: int) -> tuple[tuple[int, int], ...]:
    ways: dict[int, int] = {0: 1}
    for _ in range(count):
        following: dict[int, int] = {}
        for subtotal, number in ways.items():
            for face in range(1, sides + 1):
                following[subtotal + face] = following.get(subtotal + face, 0) + number
        ways = following
    return tuple(sorted(ways.items()))


def die_distribution(count: int, sides: int) -> dict[int, int]:
    """Number of ways to roll each sum on NdM (exact, out of sides ** count)."""

    return dict(_distribution(count, sides))


@lru_cache(maxsize=64)
def _at_least_counts(count: int, sides: int) -> tuple[int, tuple[int, ...]]:
    """(lowest sum, ways to roll at least `lowest + i` for each i); sums are contiguous."""

    distribution = _distribution(count, sides)
    running = 0
    suffix: list[int] = []
    for _, number in reversed(distribution):
        running += number
        suffix.append(running)
    return distribution[0][0], tuple(reversed(suffix))


def _ways_at_least(count: int, sides: int, threshold: int) -> int:
    lowest, suffix = _at_least_counts(count, sides)
    index = threshold - lowest
    if index <= 0:
        return suffix[0]
    return suffix[index] if index < len(suffix) else 0


def band_ways(resolution: dict[str, Any], stat: int, difficulty: int) -> tuple[dict[str, int], int]:
    """Exact ways per band out of the returned total, with no modifiers."""

    bands = resolution["bands"]
    count, sides = resolution["dice_count"], resolution["dice_sides"]
    total = sides**count
    ways = {band["band"]: 0 for band in bands}
    if is_auto(resolution, stat, difficulty):
        ways[bands[0]["band"]] = total
        return ways, total
    thresholds = [band["at_least"] for band in bands]
    if any(upper <= lower for upper, lower in zip(thresholds, thresholds[1:])):
        # Not normalized: fall back to enumerating every sum.
        for rolled, number in _distribution(count, sides):
            ways[band_for(stat + rolled - difficulty, bands)] += number
        return ways, total
    # margin >= at_least  <=>  rolled >= at_least - stat + difficulty
    reached_above = 0
    for band in bands[:-1]:
        reached = _ways_at_least(count, sides, band["at_least"] - stat + difficulty)
        ways[band["band"]] = reached - reached_above
        reached_above = reached
    ways[bands[-1]["band"]] = total - reached_above
    return ways, total


def span(low: int, high: int) -> str:
    """A range as `1-5`, or `-3 to -1` when a bound is negative (so `-3--1` never prints)."""

    return f"{low}-{high}" if low >= 0 and high >= 0 else f"{low} to {high}"


def _pairs(resolution: dict[str, Any]) -> list[tuple[int, int]]:
    return [
        (stat, difficulty)
        for stat in range(resolution["stat_min"], resolution["stat_max"] + 1)
        for difficulty in range(resolution["difficulty_min"], resolution["difficulty_max"] + 1)
    ]


def success_table(resolution: dict[str, Any]) -> dict[tuple[int, int], dict[str, float]]:
    """(stat, difficulty) -> {band: probability} for every pair on the scale."""

    table: dict[tuple[int, int], dict[str, float]] = {}
    for stat, difficulty in _pairs(resolution):
        ways, total = band_ways(resolution, stat, difficulty)
        table[(stat, difficulty)] = {band: number / total for band, number in ways.items()}
    return table


def _ranges(numbers: list[int]) -> str:
    groups: list[list[int]] = []
    for number in numbers:
        if groups and number == groups[-1][-1] + 1:
            groups[-1].append(number)
        else:
            groups.append([number])
    return ", ".join(str(group[0]) if len(group) == 1 else span(group[0], group[-1]) for group in groups)


def _certain_at(resolution: dict[str, Any], stat: int) -> bool:
    """True when the first band is certain against every difficulty."""

    first = resolution["bands"][0]["band"]
    for difficulty in range(resolution["difficulty_min"], resolution["difficulty_max"] + 1):
        ways, total = band_ways(resolution, stat, difficulty)
        if ways[first] != total:
            return False
    return True


def risky_difficulty(resolution: dict[str, Any], stat: int) -> int | None:
    """The lowest difficulty at which `stat` (no modifiers) can miss the first band.

    The die only adds to the stat, so the first band is certain whenever even
    the lowest roll (one per die) reaches it, or the auto-success margin
    applies; a die with more sides cannot change that. None when no difficulty
    can (a single band takes every margin).
    """

    first = resolution["bands"][0]
    needed = stat + resolution["dice_count"] - first["at_least"] + 1
    if resolution["auto_success_margin"] is not None:
        needed = max(needed, stat - resolution["auto_success_margin"] + 1)
    ways, total = band_ways(resolution, stat, needed)
    return needed if ways[first["band"]] < total else None


def exhaustion_findings(resolution: dict[str, Any]) -> list[dict[str, str]]:
    """Structured findings: `scale_exhausted` (warning), `first_band_unreachable` (info)."""

    first = resolution["bands"][0]["band"]
    findings: list[dict[str, str]] = []
    top = resolution["stat_max"]
    if _certain_at(resolution, top):
        lowest = top
        while lowest - 1 >= resolution["stat_min"] and _certain_at(resolution, lowest - 1):
            lowest -= 1
        since = f"; certainty already starts at stat {lowest}" if lowest < top else ""
        needed = risky_difficulty(resolution, top)
        if needed is None:
            remedy = f"every margin falls into {first}, so add a lower band through an OOC rules change"
        else:
            # Name the exact fix: a die with more sides leaves the scale exhausted.
            remedy = (
                f"stat {top} can miss {first} only against difficulty {needed} or more (more die sides do "
                f"not change that), so raise difficulty_max to at least {needed} through an OOC rules change"
            )
        findings.append(
            {
                "rule": "scale_exhausted",
                "severity": "warning",
                "message": (
                    f"at stat {top} (the scale maximum) every difficulty "
                    f"{span(resolution['difficulty_min'], resolution['difficulty_max'])} gives {first} with "
                    f"certainty on {resolution['die']}{since}; {remedy}"
                ),
            }
        )
    unreachable: dict[int, list[int]] = {}
    for stat, difficulty in _pairs(resolution):
        if band_ways(resolution, stat, difficulty)[0][first] == 0:
            unreachable.setdefault(stat, []).append(difficulty)
    if unreachable:
        # One summary line: the count, then the first few stats (a wide scale
        # would otherwise list every stat).
        count = sum(len(values) for values in unreachable.values())
        shown = list(unreachable.items())[:SUMMARY_STATS]
        listed = "; ".join(f"stat {stat} vs difficulty {_ranges(values)}" for stat, values in shown)
        more = len(unreachable) - len(shown)
        findings.append(
            {
                "rule": "first_band_unreachable",
                "severity": "info",
                "message": (
                    f"{first} cannot occur in {count} of {len(_pairs(resolution))} stat/difficulty pairs: {listed}"
                    + (f"; and {more} more stats" if more else "")
                ),
            }
        )
    return findings


def success_band(bands: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> dict[str, Any]:
    """The lowest success band: the one a margin of 0 (total meets difficulty) lands in.

    The last band is the floor for every lower margin, so it is a success band
    only on a single-band scale; when 0 lands there, the band above it counts.
    """

    index = next((index for index, band in enumerate(bands) if band["at_least"] <= 0), len(bands) - 1)
    return bands[min(index, max(len(bands) - 2, 0))]


def dead_zone(resolution: dict[str, Any]) -> tuple[int, int] | None:
    """Pre-roll margins (stat + modifiers - difficulty) that roll but cannot miss success.

    The margin rule rolls below `auto_success_margin`, yet the lowest roll (one
    per die) already lifts every margin from `success at_least - dice_count`
    into the success band. Only margins the scale reaches without modifiers
    count. None when no such margin exists.
    """

    auto = resolution.get("auto_success_margin")
    if auto is None:
        return None
    certain_from = success_band(resolution["bands"])["at_least"] - resolution["dice_count"]
    low = max(certain_from, resolution["stat_min"] - resolution["difficulty_max"])
    high = min(auto - 1, resolution["stat_max"] - resolution["difficulty_min"])
    return (low, high) if low <= high else None


def dead_zone_findings(resolution: dict[str, Any]) -> list[dict[str, str]]:
    """`auto_success_dead_zone` (warning) when the margin rule rolls certain calls."""

    zone = dead_zone(resolution)
    if zone is None:
        return []
    band = success_band(resolution["bands"])
    certain_from = band["at_least"] - resolution["dice_count"]
    return [
        {
            "rule": "auto_success_dead_zone",
            "severity": "warning",
            "message": (
                f"auto_success_margin {resolution['auto_success_margin']} sends calls at margins "
                f"{span(*zone)} (stat + modifiers - difficulty) to the dice, but {resolution['die']} adds at least "
                f"{resolution['dice_count']}, so those calls always reach {band['band']} and the dice helper "
                f"records them as certain without rolling; set auto_success_margin to {certain_from} through an "
                "OOC rules change so the margin rule agrees with the dice"
            ),
        }
    ]


def findings(resolution: dict[str, Any]) -> list[dict[str, str]]:
    """Every scale finding: exhaustion, first-band reach, and the auto-success dead zone."""

    return exhaustion_findings(resolution) + dead_zone_findings(resolution)


def worst_band_unreachable(resolution: dict[str, Any]) -> tuple[int, int]:
    """(pairs where the worst band cannot occur, all stat/difficulty pairs), no modifiers."""

    worst = resolution["bands"][-1]["band"]
    pairs = _pairs(resolution)
    return sum(1 for stat, difficulty in pairs if band_ways(resolution, stat, difficulty)[0][worst] == 0), len(pairs)


def exhaustion(resolution: dict[str, Any]) -> list[str]:
    """Findings as `rule: message` lines; `scale_exhausted` is the warning."""

    return [f"{finding['rule']}: {finding['message']}" for finding in exhaustion_findings(resolution)]


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------


def _percent(number: int, total: int) -> str:
    if number * 100 % total == 0:
        return f"{number * 100 // total}%"
    value = number * 100 / total
    text = f"{value:.1f}%"
    if text == "0.0%":
        return "<0.1%"
    if text == "100.0%":
        return ">99.9%"
    return text


def format_table(resolution: dict[str, Any]) -> str:
    """The odds as Markdown: a first-band matrix, every band, then findings."""

    bands = resolution["bands"]
    first = bands[0]["band"]
    thresholds = ", ".join(
        f"{band['band']} (margin >= {band['at_least']})" if index < len(bands) - 1 else f"{band['band']} (otherwise)"
        for index, band in enumerate(bands)
    )
    auto = resolution["auto_success_margin"]
    difficulties = list(range(resolution["difficulty_min"], resolution["difficulty_max"] + 1))
    lines = [
        "# Resolution odds",
        "",
        f"- Die: {resolution['die']}; total = stat + modifiers + die; margin = total - difficulty. "
        "The tables count no modifiers.",
        f"- Stat {span(resolution['stat_min'], resolution['stat_max'])}; "
        f"difficulty {span(resolution['difficulty_min'], resolution['difficulty_max'])}.",
        "- Auto success: "
        + ("none" if auto is None else f"stat + modifiers - difficulty >= {auto} succeeds without a roll")
        + ".",
        f"- Bands, first match wins: {thresholds}.",
        "",
        f"## Chance of {first}",
        "",
        "| Stat \\ Difficulty | " + " | ".join(str(d) for d in difficulties) + " |",
        "| --- | " + " | ".join("---" for _ in difficulties) + " |",
    ]
    for stat in range(resolution["stat_min"], resolution["stat_max"] + 1):
        cells = []
        for difficulty in difficulties:
            ways, total = band_ways(resolution, stat, difficulty)
            cell = _percent(ways[first], total)
            cells.append(f"{cell} auto" if is_auto(resolution, stat, difficulty) else cell)
        lines.append(f"| {stat} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Every band",
        "",
        "| Stat | Difficulty | Roll | " + " | ".join(band["band"].replace("|", "\\|") for band in bands) + " |",
        "| --- | --- | --- | " + " | ".join("---" for _ in bands) + " |",
    ]
    for stat, difficulty in _pairs(resolution):
        ways, total = band_ways(resolution, stat, difficulty)
        roll = "auto" if is_auto(resolution, stat, difficulty) else "roll"
        lines.append(
            f"| {stat} | {difficulty} | {roll} | "
            + " | ".join(_percent(ways[band["band"]], total) for band in bands)
            + " |"
        )
    lines += ["", "## Findings", ""]
    lines += [f"- {f['rule']} ({f['severity']}): {f['message']}" for f in findings(resolution)] or ["- none"]
    return "\n".join(lines) + "\n"


def _profile_path(target: Path) -> Path:
    for folder in (target, target / "campaign"):
        if (folder / "play_profile.yaml").is_file():
            return folder / "play_profile.yaml"
    raise FileNotFoundError(f"no play_profile.yaml under {target}")


def _profile_text(target: Path) -> str:
    """play_profile.yaml as text, read strictly as UTF-8 (a BOM is dropped)."""

    profile = _profile_path(target)
    try:
        return profile.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ResolutionError(
            f"{profile.name} is not valid UTF-8 (byte {exc.start}); save it as UTF-8 and retry"
        ) from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the campaign's resolution odds as Markdown.")
    parser.add_argument("campaign", help="Campaign folder (or the project folder that holds campaign/).")
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    try:
        resolution = load_resolution(_profile_text(Path(args.campaign)))
    except (OSError, ResolutionError) as exc:
        print(f"Cannot read the resolution scale: {exc}")
        return 2
    if resolution is None:
        print("No mechanics.resolution block in play_profile.yaml; nothing to tabulate.")
        return 1
    sys.stdout.write(format_table(resolution))
    return 0


if __name__ == "__main__":
    sys.exit(main())

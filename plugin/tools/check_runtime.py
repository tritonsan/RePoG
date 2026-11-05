"""Full-check rules for the plugin's runtime layer and note shape.

Kept apart from `check_state.py` so that file stays small enough to ship.
Every rule here is structural: it reads settings, the dice scale, roll
receipts, and note headings, and never judges what a note says.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

import lang_pack
import odds
from repog_runtime import RUNTIME_ALLOWED, RUNTIME_DIR, block_scalars, read_jsonl, read_text, runtime_settings


Add = Callable[..., None]

DEFAULT_STAT_RANGE = (1, 5)
IMPORTANT_TIER_RE = re.compile(r"(?im)^(?:-\s*)?Tier:\s*T[23]\b")
CORE_HEADING_RE = re.compile(r"(?m)^##[ \t]+Core[ \t]*$")
STATUS_RE = re.compile(r"(?im)^-[ \t]*Status:[ \t]*(\S.*?)[ \t]*$")
TITLE_RE = re.compile(r"(?m)^#[ \t]+(.+?)[ \t]*$")
NUMERIC_SCALE_RE = re.compile(r"(?im)^\s*[-*]\s+Numeric scale:\s*(-?\d+)\s*(?:-|–|—|to|\.\.)\s*(-?\d+)\b")
# The runtime reader takes `runtime:` as a block of `key: value` lines only; an
# inline mapping (`runtime: {scene_capsule: off}`) would be ignored silently.
INLINE_RUNTIME_RE = re.compile(r"(?m)^runtime:[ \t]*([^\s#].*?)[ \t]*$")

# `failure_unreachable`: the newest receipts decide once there are enough of
# them; with fewer, the scale's own stat/difficulty matchups do.
RECENT_RECEIPTS = 20
MIN_RECEIPTS = 5
UNREACHABLE_SHARE = 0.8
ROLLS_FILE = "rolls.jsonl"
# presentation_lint.LINT_HISTORY: one line per linted reply, the repetition
# memory while `runtime.presentation_lint` is on.
LINT_HISTORY_FILE = "lint_history.jsonl"


def resolution(profile_text: str) -> dict[str, Any] | None:
    """The configured dice scale, or None when absent or unreadable."""

    try:
        return odds.load_resolution(profile_text)
    except Exception:  # an invalid block is reported by check_profile, not here
        return None


def numeric_scale(rules_text: str) -> tuple[int, int] | None:
    """The `- Numeric scale: min-max` line of rules.md, or None."""

    match = NUMERIC_SCALE_RE.search(re.sub(r"<!--.*?-->", "", rules_text, flags=re.DOTALL))
    if match is None:
        return None
    low, high = int(match.group(1)), int(match.group(2))
    return (low, high) if low <= high else None


def stat_range(profile_text: str, rules_text: str = "") -> tuple[int, int]:
    """The stat range the power checks use.

    It is the dice scale's range, widened by a `- Numeric scale:` line in
    rules.md when one is present, so a value valid under either declared scale
    is never out of range. With neither, the 1-5 default applies.
    """

    configured = resolution(profile_text)
    ranges = [] if configured is None else [(int(configured["stat_min"]), int(configured["stat_max"]))]
    declared = numeric_scale(rules_text) if rules_text else None
    if declared is not None:
        ranges.append(declared)
    if not ranges:
        return DEFAULT_STAT_RANGE
    return min(low for low, _ in ranges), max(high for _, high in ranges)


def rescaled(value: float, stat_range: tuple[int, int], count: int = 1) -> float:
    """A figure written for the 1-5 default scale, placed on `stat_range`.

    The level-band ceilings and budgets are written for 1-5; on another range
    each stat keeps the same share of it (linear, and unchanged on 1-5). With
    `count`, `value` is a total over that many stats.
    """

    low, high = stat_range
    default_low, default_high = DEFAULT_STAT_RANGE
    return count * low + (value - count * default_low) * (high - low) / (default_high - default_low)


def check_profile(profile_text: str, path: Path, add: Add) -> None:
    """Runtime switches, play and records language, and the dice scale's odds."""

    inline = INLINE_RUNTIME_RE.search(profile_text)
    if inline is not None and inline.group(1).split(" #", 1)[0].strip() not in {"{}", "null", "Null", "NULL", "~"}:
        add(
            "error",
            "runtime_block_inline",
            f"runtime: holds the inline value '{inline.group(1)[:80]}', which the hooks ignore; "
            "write each setting on its own indented `key: value` line under runtime:.",
            path,
        )
    runtime = block_scalars(profile_text, "runtime")
    for key, value in runtime.items():
        allowed = RUNTIME_ALLOWED.get(key)
        if allowed is None:
            add("warning", "runtime_setting_unknown", f"runtime.{key} is not a known setting; it is ignored.", path)
        elif value not in allowed:
            add(
                "error",
                "runtime_setting_invalid",
                f"runtime.{key} is '{value}'; use one of: {', '.join(sorted(allowed))}.",
                path,
            )
    narration = block_scalars(profile_text, "narration")
    language = narration.get("language", "")
    if language and language != "auto":
        code = lang_pack.normalize_code(language)
        if not code:
            add("error", "narration_language_invalid", f"narration.language '{language}' is not a language code.", path)
        elif code not in lang_pack.available_codes():
            add(
                "warning",
                "language_pack_missing",
                f"No language pack for '{code}'; presentation checks fall back to generic rules.",
                path,
            )
    records = narration.get("records_language", "")
    if records and records != "same" and not lang_pack.normalize_code(records):
        add(
            "error",
            "records_language_invalid",
            f"narration.records_language '{records}' is neither `same` nor a language code.",
            path,
        )
    try:
        configured = odds.load_resolution(profile_text)
    except Exception as exc:
        add("error", "resolution_invalid", f"mechanics.resolution: {exc}", path)
        return
    if configured is None:
        return
    for finding in odds.findings(configured):
        add(finding.get("severity", "warning"), finding.get("rule", "resolution"), finding.get("message", ""), path)


def _calls(campaign: Path) -> list[dict[str, Any]]:
    """The newest roll-call receipts; reread rows and malformed lines are skipped."""

    rows = read_jsonl(campaign / RUNTIME_DIR / ROLLS_FILE)
    calls = [row for row in rows if row.get("kind") != "reread" and isinstance(row.get("call"), dict)]
    return calls[-RECENT_RECEIPTS:]


def _worst_reachable(receipt: dict[str, Any], configured: dict[str, Any] | None) -> bool | None:
    """Whether a receipt's call could land in the worst band; None when unreadable.

    An auto call was never rolled, so it cannot, whatever its dice could have
    made. Otherwise the receipt's own odds decide (`reachable_bands`, then
    `floor_band`), and an older receipt is worked out from its call.
    """

    bands = configured["bands"] if configured else list(odds.DEFAULT_BANDS)
    worst = bands[-1]["band"]
    if receipt.get("auto") is True:
        return False
    reachable = receipt.get("reachable_bands")
    if isinstance(reachable, list):
        return worst in reachable
    if isinstance(receipt.get("floor_band"), str):
        return receipt["floor_band"] == worst
    call = receipt["call"]
    try:
        count, _ = odds.parse_die(receipt.get("die") or (configured or {}).get("die") or "1d6")
        modifiers = sum(int(factor.get("modifier", 0)) for factor in call.get("factors") or [])
        value, difficulty = int(call["value"]), int(call["difficulty"])
    except (KeyError, TypeError, ValueError, AttributeError):
        return None
    if odds.is_auto(configured, value, difficulty, modifiers):
        return False
    return odds.band_for(value + modifiers + count - difficulty, bands) == worst


def check_rolls(campaign: Path, profile_text: str, path: Path, add: Add) -> None:
    """`failure_unreachable`: recent calls (or the scale) almost never reach the worst band."""

    configured = resolution(profile_text)
    outcomes = [_worst_reachable(receipt, configured) for receipt in _calls(campaign)]
    outcomes = [outcome for outcome in outcomes if outcome is not None]
    if len(outcomes) >= MIN_RECEIPTS:
        total, unreachable = len(outcomes), outcomes.count(False)
        scope = f"the last {total} roll calls"
    elif configured is not None:
        unreachable, total = odds.worst_band_unreachable(configured)
        scope = f"the scale's {total} stat/difficulty pairs"
    else:
        return
    if not total or unreachable < UNREACHABLE_SHARE * total:
        return
    worst = (configured["bands"] if configured else odds.DEFAULT_BANDS)[-1]["band"]
    add(
        "warning",
        "failure_unreachable",
        f"{worst} could not occur in {unreachable} of {scope} ({round(unreachable * 100 / total)}%); a call "
        f"that cannot reach {worst} carries no risk. Set difficulties and factors so a bad result stays "
        "possible, or narrate a certain result without rolling.",
        path,
    )


def lint_keeps_style_memory(campaign: Path) -> bool:
    """Whether the presentation lint, not `style_state.json`, tracks repetition.

    True while `runtime.presentation_lint` is on (the default) or once a lint
    history exists; distill then no longer samples a reply into
    `style_state.json`, so an empty one there is expected, not inert.
    """

    if (campaign / RUNTIME_DIR / LINT_HISTORY_FILE).is_file():
        return True
    return runtime_settings(campaign).get("presentation_lint") == "on"


def note_title(text: str, note: Path) -> str:
    match = TITLE_RE.search(text)
    return match.group(1).strip() if match else note.stem.replace("_", " ")


def core_status(text: str) -> str:
    """The `- Status:` value inside the note's `## Core` section, folded."""

    core = CORE_HEADING_RE.search(text)
    if core is None:
        return ""
    body = text[core.end() :]
    following = re.search(r"(?m)^#{1,2}[ \t]+\S", body)
    if following is not None:
        body = body[: following.start()]
    match = STATUS_RE.search(body)
    return match.group(1).strip().casefold() if match else ""


def _add_listing(add: Add, severity: str, rule: str, message: str, path: Path, paths: list[Path]) -> None:
    """Report an aggregated finding with its files; an `add` without `paths` still works."""

    try:
        add(severity, rule, message, path, paths=[str(item) for item in paths])
    except TypeError:
        add(severity, rule, message, path)


def check_notes(campaign: Path, present_npcs: list[str], add: Add) -> None:
    """Core blocks on important notes, and no dead character in the scene."""

    folder = campaign / "characters"
    if not folder.is_dir():
        return
    missing: list[tuple[str, Path]] = []
    present = {name.strip().casefold() for name in present_npcs if name.strip()}
    for note in sorted(folder.glob("*.md")):
        if note.name.startswith("_"):
            continue
        text = read_text(note)
        title = note_title(text, note)
        if IMPORTANT_TIER_RE.search(text) and CORE_HEADING_RE.search(text) is None:
            missing.append((title, note))
        if core_status(text) == "dead" and (title.casefold() in present or note.stem.casefold() in present):
            add(
                "error",
                "dead_present",
                f"{title} is recorded as dead in its ## Core but is listed in current_scene.present_npcs.",
                note,
            )
    if missing:
        # Name them all (within reason): the curator packet needs every target.
        titles = [title for title, _ in missing]
        shown = ", ".join(titles[:40]) + (f", and {len(titles) - 40} more" if len(titles) > 40 else "")
        _add_listing(
            add,
            "warning",
            "note_core_missing",
            f"{len(missing)} T2/T3 note(s) have no ## Core block (status, kin, address): {shown}. "
            "Add them at the next distill or let the curator fold them in.",
            folder,
            [note for _, note in missing],
        )

"""Full-check rules for the plugin's runtime layer and note shape.

Kept apart from `check_state.py` so that file stays small enough to ship.
Every rule here is structural: it reads settings, the dice scale, and note
headings, and never judges what a note says.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

import lang_pack
import odds
from repog_runtime import RUNTIME_ALLOWED, block_scalars, read_text


Add = Callable[[str, str, str, Path], None]

DEFAULT_STAT_RANGE = (1, 5)
IMPORTANT_TIER_RE = re.compile(r"(?im)^(?:-\s*)?Tier:\s*T[23]\b")
CORE_HEADING_RE = re.compile(r"(?m)^##[ \t]+Core[ \t]*$")
STATUS_RE = re.compile(r"(?im)^-[ \t]*Status:[ \t]*(\S.*?)[ \t]*$")
TITLE_RE = re.compile(r"(?m)^#[ \t]+(.+?)[ \t]*$")


def resolution(profile_text: str) -> dict[str, Any] | None:
    """The configured dice scale, or None when absent or unreadable."""

    try:
        return odds.load_resolution(profile_text)
    except Exception:  # an invalid block is reported by check_profile, not here
        return None


def stat_range(profile_text: str) -> tuple[int, int]:
    configured = resolution(profile_text)
    if configured is None:
        return DEFAULT_STAT_RANGE
    return int(configured["stat_min"]), int(configured["stat_max"])


def check_profile(profile_text: str, path: Path, add: Add) -> None:
    """Runtime switches, play language, and the dice scale's odds."""

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
    language = block_scalars(profile_text, "narration").get("language", "")
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
    try:
        configured = odds.load_resolution(profile_text)
    except Exception as exc:
        add("error", "resolution_invalid", f"mechanics.resolution: {exc}", path)
        return
    if configured is None:
        return
    for finding in odds.exhaustion_findings(configured):
        add(finding.get("severity", "warning"), finding.get("rule", "resolution"), finding.get("message", ""), path)


def _title(text: str, note: Path) -> str:
    match = TITLE_RE.search(text)
    return match.group(1).strip() if match else note.stem.replace("_", " ")


def _status(text: str) -> str:
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


def check_notes(campaign: Path, present_npcs: list[str], add: Add) -> None:
    """Core blocks on important notes, and no dead character in the scene."""

    folder = campaign / "characters"
    if not folder.is_dir():
        return
    missing: list[str] = []
    present = {name.strip().casefold() for name in present_npcs if name.strip()}
    for note in sorted(folder.glob("*.md")):
        if note.name.startswith("_"):
            continue
        text = read_text(note)
        title = _title(text, note)
        if IMPORTANT_TIER_RE.search(text) and CORE_HEADING_RE.search(text) is None:
            missing.append(title)
        if _status(text) == "dead" and (title.casefold() in present or note.stem.casefold() in present):
            add(
                "error",
                "dead_present",
                f"{title} is recorded as dead in its ## Core but is listed in current_scene.present_npcs.",
                note,
            )
    if missing:
        shown = ", ".join(missing[:6]) + (f", and {len(missing) - 6} more" if len(missing) > 6 else "")
        add(
            "warning",
            "note_core_missing",
            f"{len(missing)} T2/T3 note(s) have no ## Core block (status, kin, address): {shown}. "
            "Add them at the next distill or let the curator fold them in.",
            folder,
        )

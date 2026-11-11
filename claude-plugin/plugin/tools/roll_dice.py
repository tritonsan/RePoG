"""Roll one bounded, reproducible NdM+/-K expression and emit JSON.

Two modes share this helper:

- Expression mode (no `--campaign`) rolls a free `NdM+/-K` expression
  with an optional caller seed. Its output shape is unchanged since 0.2.0.
- Call mode (`--campaign <path>` with `{"call": ..., "roll_id": ...}`)
  rolls a declared check: actor, axis, stat value, difficulty (with an
  optional one-line `reason`), modifiers, and stakes are fixed before the die
  is seen. The seed is derived from the
  campaign id, the continuity revision, the roll id, and the canonical call,
  so repeating the same call returns the same receipt and a different result
  needs a new roll id, which stays on record. Receipts are appended to
  `campaign/.repog-runtime/rolls.jsonl`, the runtime store the writer checks
  when a commit cites a roll.

Each receipt also carries the call's exact odds (the bands it can reach, the
floor and ceiling band, and the chance of landing below success), a one-line
`summary`, a Player-facing `display` line in the play language, and warnings
about the declared stakes. A call whose lowest roll already lands in a success
band is `certain`: it records no dice and takes that floor band.

Two more call-mode commands read and extend the store:

- `axes --since-revision N` counts receipts per actor and axis.
- `reread` (a request of `roll_id`, `reason` and `new_band`) records that a
  past roll is now read under another band after a retroactive rules change.
  The receipt itself never changes.

The request is one JSON object, given as `--input-json` or read with
`--input-file` from a UTF-8 file (or standard input for `-`), which keeps
apostrophes in prose clear of shell quoting.

A roll supplies numbers and a band name, never the fictional meaning of the
result; that stays with the GM. The display line only moves the GM's own
stakes text next to the numbers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import secrets
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

import odds
from repog_runtime import RUNTIME_DIR, block_scalars, read_json, top_scalar


DICE_RE = re.compile(r"^\s*(\d{1,3})[dD](\d{1,4})(?:\s*([+-])\s*(\d{1,6}))?\s*$")
MAX_DICE = 100
MAX_SIDES = 1000
MAX_ABS_MODIFIER = 100_000

# Call mode limits. A call is a short declaration, not a narration.
MAX_ROLL_ID = 80
ROLL_ID_PUNCTUATION = frozenset("_.:-")
REQUEST_REQUIRED = ("roll_id", "call")
REQUEST_OPTIONAL = ("die",)
REQUEST_KEYS = frozenset(REQUEST_REQUIRED + REQUEST_OPTIONAL)
CALL_REQUIRED = ("actor", "axis", "value", "difficulty", "stakes")
CALL_OPTIONAL = ("factors", "reason")
CALL_KEYS = frozenset(CALL_REQUIRED + CALL_OPTIONAL)
FACTOR_KEYS = frozenset({"label", "modifier"})
MAX_NAME = 80
MAX_REASON = 200
MAX_STAKES = 500
MAX_FACTORS = 12
MAX_ABS_CALL_NUMBER = 1000
RECEIPTS_FILE = "rolls.jsonl"
RECEIPT_KEEP = 2000
# The stored fields in output order; `summary` always prints first.
RECEIPT_FIELDS = (
    "summary",
    "roll_id",
    "revision",
    "call",
    "die",
    "dice",
    "total",
    "margin",
    "band",
    "auto",
    "certain",
    "floor_band",
    "ceiling_band",
    "reachable_bands",
    "p_below_success",
    "display",
    "warnings",
    "at",
)
# A reread row says a past roll is now read under another band. It is never a
# receipt: it carries no `roll_id`, is never open, and cannot be cited.
REREAD_KIND = "reread"
REREAD_KEYS = ("roll_id", "reason", "new_band")
P_DIGITS = 4  # decimals kept in p_below_success
SEED_DOMAIN = "repog-roll-call-v1"
UTF8_BOM = b"\xef\xbb\xbf"
# The writer reads a `roll_reference` starting with this as the Player's own
# physical roll, never as a receipt, so no receipt may carry such an id.
PLAYER_ROLL_PREFIX = "player:"

# Stakes keys by band kind, in every pack language (en, tr, de, es, fr), with
# plain-letter spellings. Matching ignores case; Python's regex case folding
# already treats Turkish dotted and dotless i as one letter. The order is the
# order of specificity: when several stakes entries describe one band (cost
# and success for `success_with_cost`), the earlier kind wins.
STAKES_KINDS: dict[str, tuple[str, ...]] = {
    "critical": ("critical", "crit", "kritik", "kritisch", "crítico", "critico", "critique"),
    "clean": ("clean", "temiz", "sauber", "limpio", "net", "nette"),
    "cost": ("cost", "costly", "bedel", "bedelli", "kosten", "preis", "coste", "costo", "coût", "cout"),
    "partial": ("partial", "kısmi", "teilweise", "parcial", "partiel", "partielle"),
    "loss": ("loss", "kayıp", "verlust", "pérdida", "perdida", "perte"),
    "failure": (
        "failure", "fail", "başarısız", "basarisiz", "başarısızlık", "basarisizlik",
        "fehlschlag", "misserfolg", "fracaso", "échec", "echec",
    ),
    "success": (
        "success", "başarı", "basari", "başarılı", "basarili", "erfolg", "éxito", "exito", "réussite", "reussite",
    ),
}
NAME_SEPARATOR = r"[\s_-]+"
# A name pairing a kind from each side of success (`critical failure`,
# `kritik başarısızlık`, `échec critique`) names the bad result: the
# below-success word is its head noun, whichever side the other word stands.
SUCCESS_SIDE_KINDS = frozenset({"critical", "clean", "success"})
BELOW_SUCCESS_KINDS = frozenset({"failure", "loss"})

# The display line's fixed words per play language; English is the fallback.
# Band kinds use the same keys as STAKES_KINDS.
DISPLAY_WORDS: dict[str, dict[str, str]] = {
    "en": {
        "vs": "vs", "auto": "no roll", "stake": "at stake", "critical": "critical", "clean": "clean",
        "cost": "cost", "partial": "partial", "loss": "loss", "failure": "failure", "success": "success",
    },
    "tr": {
        "vs": "karşı", "auto": "zarsız", "stake": "risk", "critical": "kritik", "clean": "temiz",
        "cost": "bedel", "partial": "kısmi", "loss": "kayıp", "failure": "başarısız", "success": "başarı",
    },
    "de": {
        "vs": "gegen", "auto": "ohne Wurf", "stake": "auf dem Spiel", "critical": "kritisch", "clean": "sauber",
        "cost": "Preis", "partial": "teilweise", "loss": "Verlust", "failure": "Fehlschlag", "success": "Erfolg",
    },
    "es": {
        "vs": "contra", "auto": "sin tirada", "stake": "en juego", "critical": "crítico", "clean": "limpio",
        "cost": "coste", "partial": "parcial", "loss": "pérdida", "failure": "fracaso", "success": "éxito",
    },
    "fr": {
        "vs": "contre", "auto": "sans jet", "stake": "enjeu", "critical": "critique", "clean": "net",
        "cost": "coût", "partial": "partiel", "loss": "perte", "failure": "échec", "success": "réussite",
    },
}
# Band names the plugin's templates and playbooks use, as the display line
# writes them in each play language. English writes every band name with
# spaces for '_', and any other band name shows as written.
BAND_PHRASES: dict[str, dict[str, str]] = {
    "tr": {
        "critical_success": "kritik başarı",
        "clean_success": "temiz başarı",
        "success_with_cost": "bedelli başarı",
        "partial_or_loss": "kısmi ya da kayıp",
        "partial_small_cost": "kısmi, küçük bedel",
        "partial_medium_cost": "kısmi, orta bedel",
        "partial_heavy_cost": "kısmi, ağır bedel",
    },
    "de": {
        "critical_success": "kritischer Erfolg",
        "clean_success": "sauberer Erfolg",
        "success_with_cost": "Erfolg mit Preis",
        "partial_or_loss": "teilweise oder Verlust",
        "partial_small_cost": "teilweise, kleiner Preis",
        "partial_medium_cost": "teilweise, mittlerer Preis",
        "partial_heavy_cost": "teilweise, hoher Preis",
    },
    "es": {
        "critical_success": "éxito crítico",
        "clean_success": "éxito limpio",
        "success_with_cost": "éxito con coste",
        "partial_or_loss": "parcial o pérdida",
        "partial_small_cost": "parcial, coste leve",
        "partial_medium_cost": "parcial, coste medio",
        "partial_heavy_cost": "parcial, coste alto",
    },
    "fr": {
        "critical_success": "réussite critique",
        "clean_success": "réussite nette",
        "success_with_cost": "réussite avec un coût",
        "partial_or_loss": "partiel ou perte",
        "partial_small_cost": "partiel, coût léger",
        "partial_medium_cost": "partiel, coût moyen",
        "partial_heavy_cost": "partiel, coût lourd",
    },
}
DISPLAY_MAX = 140
CLAUSE_SEPARATOR = " · "
MIN_CLAUSE = 12  # a shorter room drops the stakes clause rather than show a stub
LANGUAGE_CODE_RE = re.compile(r"^([a-z]{2,3})(?:[-_][a-z0-9]{1,8})*$")
# The presentation lint's last record names the play language it detected;
# an `auto` profile language resolves to it, as in the writer and the capsule.
LINT_RECORD = "lint_last.json"
LINT_LANGUAGE_KEYS = ("language", "play_language")


class DiceError(ValueError):
    """Raised for malformed or unsafe dice requests."""


class RollCallError(DiceError):
    """A roll call refused before any receipt is written."""

    def __init__(self, category: str, reason: str) -> None:
        super().__init__(reason)
        self.category = category


# ---------------------------------------------------------------------------
# Expression mode (unchanged contract)
# ---------------------------------------------------------------------------


def parse_expression(expression: Any) -> tuple[str, int, int, int]:
    if not isinstance(expression, str):
        raise DiceError("expression must be a string in NdM+/-K form")
    match = DICE_RE.fullmatch(expression)
    if match is None:
        raise DiceError("expression must use NdM, NdM+K, or NdM-K")
    count = int(match.group(1))
    sides = int(match.group(2))
    modifier = int(match.group(4) or 0)
    if match.group(3) == "-":
        modifier = -modifier
    if not 1 <= count <= MAX_DICE:
        raise DiceError(f"dice count must be between 1 and {MAX_DICE}")
    if not 2 <= sides <= MAX_SIDES:
        raise DiceError(f"die sides must be between 2 and {MAX_SIDES}")
    if abs(modifier) > MAX_ABS_MODIFIER:
        raise DiceError(f"modifier magnitude must be at most {MAX_ABS_MODIFIER}")
    canonical = f"{count}d{sides}{modifier:+d}" if modifier else f"{count}d{sides}"
    return canonical, count, sides, modifier


def _seed_value(raw_seed: Any) -> tuple[str, int]:
    if raw_seed is None:
        token = str(secrets.randbits(128))
    elif type(raw_seed) is int:
        token = str(raw_seed)
    elif isinstance(raw_seed, str) and raw_seed.strip():
        token = raw_seed.strip()
    else:
        raise DiceError("seed must be a non-empty string or integer")
    digest = hashlib.sha256(f"repog-dice-v1\0{token}".encode("utf-8")).digest()
    return token, int.from_bytes(digest, "big")


def roll(payload: dict[str, Any]) -> dict[str, Any]:
    canonical, count, sides, modifier = parse_expression(payload.get("expression"))
    seed_token, seed_value = _seed_value(payload.get("seed"))
    requested_roll_id = payload.get("roll_id")
    if requested_roll_id is not None and (not isinstance(requested_roll_id, str) or not requested_roll_id.strip()):
        raise DiceError("roll_id must be a non-empty string when provided")
    roll_id = (
        requested_roll_id.strip()
        if isinstance(requested_roll_id, str)
        else hashlib.sha256(f"{canonical}\0{seed_token}".encode("utf-8")).hexdigest()[:20]
    )
    rng = random.Random(seed_value)
    results = [rng.randint(1, sides) for _ in range(count)]
    subtotal = sum(results)
    return {
        "ok": True,
        "roll_id": roll_id,
        "expression": canonical,
        "seed": seed_token,
        "dice": results,
        "subtotal": subtotal,
        "modifier": modifier,
        "total": subtotal + modifier,
        "bounds": {"minimum": count + modifier, "maximum": count * sides + modifier},
    }


# ---------------------------------------------------------------------------
# Call mode: validation
# ---------------------------------------------------------------------------


def _line(value: Any, label: str, maximum: int) -> str:
    """Trimmed, NFC-normalized, single-line text.

    Control characters and Unicode line/paragraph separators are refused: a
    raw U+2028 or U+0085 in a stored receipt would split its JSON line for any
    reader that uses `str.splitlines`. So is a lone surrogate, which JSON can
    carry as an escape (`\\ud800`) but UTF-8 cannot store.
    """

    if not isinstance(value, str) or not value.strip():
        raise RollCallError("input_invalid", f"{label} must be non-empty text")
    value = unicodedata.normalize("NFC", value.strip())
    if any(unicodedata.category(char) == "Cs" for char in value):
        raise RollCallError("input_invalid", f"{label} holds a lone surrogate escape; send valid Unicode text")
    if any(unicodedata.category(char) in odds.LINE_BREAKING for char in value):
        raise RollCallError("input_invalid", f"{label} must be one line without control characters")
    if len(value) > maximum:
        raise RollCallError("input_invalid", f"{label} must be at most {maximum} characters")
    return value


def _whole(value: Any, label: str, maximum: int = MAX_ABS_CALL_NUMBER) -> int:
    if type(value) is not int:
        raise RollCallError("input_invalid", f"{label} must be an integer")
    if abs(value) > maximum:
        raise RollCallError("input_invalid", f"{label} magnitude must be at most {maximum}")
    return value


def _unknown_keys(prefix: str, unknown: list[str], required: tuple[str, ...], optional: tuple[str, ...]) -> RollCallError:
    """An unknown-key refusal that names every key the object accepts."""

    accepted = f"{', '.join(required)} (required)"
    if optional:
        accepted += f"; {', '.join(optional)} (optional)"
    return RollCallError("input_invalid", f"{prefix}: {', '.join(unknown)}; accepted keys: {accepted}")


def normalize_call(call: Any) -> dict[str, Any]:
    """The canonical call: trimmed text, integer numbers, factors always listed.

    `reason` appears only when given, so a call without one keeps the seed and
    receipt it had before the field existed.
    """

    if not isinstance(call, dict):
        raise RollCallError("input_invalid", "call must be an object")
    unknown = sorted(set(call) - CALL_KEYS)
    if unknown:
        raise _unknown_keys("call has unknown keys", unknown, CALL_REQUIRED, CALL_OPTIONAL)
    raw_factors = call.get("factors")
    if raw_factors is None:
        raw_factors = []
    if not isinstance(raw_factors, list) or len(raw_factors) > MAX_FACTORS:
        raise RollCallError("input_invalid", f"call.factors must be a list of at most {MAX_FACTORS} items")
    factors: list[dict[str, Any]] = []
    for index, factor in enumerate(raw_factors):
        label = f"call.factors[{index}]"
        if not isinstance(factor, dict) or set(factor) != FACTOR_KEYS:
            raise RollCallError("input_invalid", f"{label} needs exactly label and modifier")
        factors.append(
            {
                "label": _line(factor["label"], f"{label}.label", MAX_NAME),
                "modifier": _whole(factor["modifier"], f"{label}.modifier", 100),
            }
        )
    canonical = {
        "actor": _line(call.get("actor"), "call.actor", MAX_NAME),
        "axis": _line(call.get("axis"), "call.axis", MAX_NAME),
        "value": _whole(call.get("value"), "call.value"),
        "difficulty": _whole(call.get("difficulty"), "call.difficulty"),
        "factors": factors,
        "stakes": _line(call.get("stakes"), "call.stakes", MAX_STAKES),
    }
    # The one-line reason for the difficulty; a null value counts as absent.
    if call.get("reason") is not None:
        canonical["reason"] = _line(call["reason"], "call.reason", MAX_REASON)
    return canonical


def _canonical_id(value: str) -> str:
    return unicodedata.normalize("NFC", value.strip())


def valid_roll_id(text: str) -> bool:
    """1-80 letters or digits in any script (with their combining marks), '_', '.', ':' or '-'.

    The first character is a letter, digit, or '_'.
    """

    if not 1 <= len(text) <= MAX_ROLL_ID or not (text[0].isalnum() or text[0] == "_"):
        return False
    return all(
        char.isalnum() or char in ROLL_ID_PUNCTUATION or unicodedata.category(char).startswith("M")
        for char in text[1:]
    )


def _roll_id(value: Any) -> str:
    if not isinstance(value, str) or not valid_roll_id(_canonical_id(value)):
        raise RollCallError(
            "input_invalid",
            f"roll_id must be 1-{MAX_ROLL_ID} letters, digits, '_', '.', ':' or '-', "
            "starting with a letter, digit, or '_'",
        )
    roll_id = _canonical_id(value)
    if roll_id.casefold().startswith(PLAYER_ROLL_PREFIX):
        raise RollCallError(
            "input_invalid",
            f"roll ids starting with '{PLAYER_ROLL_PREFIX}' are reserved for citing the Player's own dice; "
            "choose another roll id",
        )
    return roll_id


def _die(requested: Any, resolution: dict[str, Any] | None) -> tuple[str, int, int]:
    """The die for this call: the configured die, or the request's own when none is configured."""

    if resolution is not None:
        if requested is not None:
            try:
                count, sides = odds.parse_die(requested)
            except odds.ResolutionError as exc:
                raise RollCallError("input_invalid", str(exc)) from exc
            if (count, sides) != (resolution["dice_count"], resolution["dice_sides"]):
                raise RollCallError(
                    "die_mismatch",
                    f"this campaign resolves with {resolution['die']}; {requested} does not match "
                    "(omit die to use the configured one)",
                )
        return resolution["die"], resolution["dice_count"], resolution["dice_sides"]
    if requested is None:
        raise RollCallError(
            "die_missing",
            "play_profile.yaml has no mechanics.resolution die; pass die in NdM form",
        )
    try:
        count, sides = odds.parse_die(requested)
    except odds.ResolutionError as exc:
        raise RollCallError("input_invalid", str(exc)) from exc
    return f"{count}d{sides}", count, sides


def _check_scale(call: dict[str, Any], resolution: dict[str, Any]) -> None:
    for key, prefix, name in (("value", "stat", "stat"), ("difficulty", "difficulty", "difficulty")):
        low, high = resolution[f"{prefix}_min"], resolution[f"{prefix}_max"]
        if not low <= call[key] <= high:
            raise RollCallError(
                "out_of_range",
                f"call.{key} {call[key]} is outside the {name} scale {odds.span(low, high)}; "
                "raise the scale through an OOC rules change first",
            )


# ---------------------------------------------------------------------------
# Call mode: resolution
# ---------------------------------------------------------------------------


def _seed(campaign_id: str, revision: int, roll_id: str, die: str, call: dict[str, Any]) -> bytes:
    canonical = json.dumps(call, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    material = "\0".join((SEED_DOMAIN, campaign_id, str(revision), roll_id, die, canonical))
    return hashlib.sha256(material.encode("utf-8")).digest()


def _faces(seed: bytes, count: int, sides: int) -> list[int]:
    """Unbiased faces from sha256 in counter mode (rejection sampling)."""

    limit = (1 << 64) // sides * sides
    faces: list[int] = []
    counter = 0
    while len(faces) < count:
        block = hashlib.sha256(seed + counter.to_bytes(8, "big")).digest()
        counter += 1
        for offset in range(0, 32, 8):
            value = int.from_bytes(block[offset : offset + 8], "big")
            if value < limit and len(faces) < count:
                faces.append(value % sides + 1)
    return faces


def _modifier_sum(call: dict[str, Any]) -> int:
    return sum(factor["modifier"] for factor in call["factors"])


def _bands(resolution: dict[str, Any] | None) -> list[dict[str, Any]]:
    return list(resolution["bands"] if resolution else odds.DEFAULT_BANDS)


def success_bands(bands: list[dict[str, Any]]) -> list[str]:
    """The bands that count as a success, best first.

    The lowest success band is the one a margin of 0 lands in, where the total
    meets the difficulty; every band above it is a success too. The last band
    also catches every lower margin, so when 0 lands there the band above it
    is the lowest success, unless it is the sole band. This is the reading of
    `odds.success_band`, so the receipts and the full check agree.
    """

    names = [band["band"] for band in bands]
    lowest = min(names.index(odds.band_for(0, bands)), max(len(names) - 2, 0))
    return names[: lowest + 1]


def _floor_band(call: dict[str, Any], count: int, bands: list[dict[str, Any]]) -> str:
    """The band of the lowest possible roll: one on every die."""

    return odds.band_for(call["value"] + _modifier_sum(call) + count - call["difficulty"], bands)


def evaluate_call(call: dict[str, Any], faces: list[int], resolution: dict[str, Any] | None) -> dict[str, Any]:
    """Total, margin, band, and auto flag for a normalized call and rolled faces.

    Pure. A call is auto when its lowest roll already lands in a success band
    (it is certain) or when the auto-success margin applies; an auto call
    ignores `faces`, records no dice, and takes the floor band, raised to the
    lowest success band when the margin rule grants a success the floor does
    not reach. Without a resolution the die count is the number of faces.
    """

    bands = _bands(resolution)
    successes = success_bands(bands)
    modifiers = _modifier_sum(call)
    floor = _floor_band(call, resolution["dice_count"] if resolution else len(faces), bands)
    auto = floor in successes or odds.is_auto(resolution, call["value"], call["difficulty"], modifiers)
    dice = [] if auto else list(faces)
    total = call["value"] + modifiers + sum(dice)
    margin = total - call["difficulty"]
    if auto:
        band = floor if floor in successes else successes[-1]
    else:
        band = odds.band_for(margin, bands)
    return {"dice": dice, "total": total, "margin": margin, "band": band, "auto": auto}


def call_odds(call: dict[str, Any], count: int, sides: int, bands: list[dict[str, Any]]) -> dict[str, Any]:
    """The call's exact odds on `count` dice of `sides` faces.

    Every sum the dice can make is enumerated with its number of ways, so the
    reachable bands (best first) and the chance of landing below the lowest
    success band are exact, not sampled.
    """

    base = call["value"] + _modifier_sum(call) - call["difficulty"]
    ways = {band["band"]: 0 for band in bands}
    for rolled, number in odds.die_distribution(count, sides).items():
        ways[odds.band_for(base + rolled, bands)] += number
    reachable = [band["band"] for band in bands if ways[band["band"]]]
    successes = success_bands(bands)
    below = sum(number for name, number in ways.items() if name not in successes)
    return {
        "certain": reachable[-1] in successes,
        "floor_band": reachable[-1],
        "ceiling_band": reachable[0],
        "reachable_bands": reachable,
        "p_below_success": round(below / sides**count, P_DIGITS),
    }


# ---------------------------------------------------------------------------
# Call mode: stakes and the display line
#
# Stakes may be one line about what a bad result costs, or keyed entries such
# as `clean: ...; cost: ...; failure: ...`. A key is a campaign band name or a
# band kind from STAKES_KINDS; a kind describes every band whose name holds
# that kind (`cost` describes `success_with_cost`), and `success` also
# describes every success band. A key or band name pairing a success-side
# kind with a below-success one holds only the latter (`critical failure`
# is a failure). Text before the first key is a preamble.
# ---------------------------------------------------------------------------


def _name_pattern(name: str) -> str:
    """A band name or alias as a regex whose words may be split by spaces, '_' or '-'.

    Empty for a name made only of separators, which can never be a key.
    """

    return NAME_SEPARATOR.join(re.escape(word) for word in re.split(NAME_SEPARATOR, name.strip()) if word)


def _same_name(text: str, name: str) -> bool:
    """True when `text` spells `name`, ignoring case and the separators between words."""

    pattern = _name_pattern(name)
    return bool(pattern) and re.fullmatch(pattern, text, re.IGNORECASE) is not None


def _kind_of(word: str) -> str | None:
    for kind, aliases in STAKES_KINDS.items():
        if any(_same_name(word, alias) for alias in aliases):
            return kind
    return None


def _kinds_in(name: str) -> list[str]:
    """The band kinds named by the words of a band name or stakes key, most specific first.

    A name that pairs a success-side kind with a below-success one names the
    bad result, so its success-side kinds drop: `critical failure` and
    `kritik başarısızlık` are failures, while `kritik başarı` stays critical.
    """

    found = {_kind_of(word) for word in re.split(NAME_SEPARATOR, name) if word}
    if found & BELOW_SUCCESS_KINDS and found & SUCCESS_SIDE_KINDS:
        found -= SUCCESS_SIDE_KINDS
    return [kind for kind in STAKES_KINDS if kind in found]


def _bands_of_kind(kind: str, bands: list[dict[str, Any]]) -> list[str]:
    """The bands a kind word describes, in band order.

    A band whose name holds the kind; for `success`, every success band too.
    No kind below success widens this way, so a `failure` entry never stands
    in for a partial band.
    """

    covered = set(success_bands(bands)) if kind == "success" else set()
    return [band["band"] for band in bands if band["band"] in covered or kind in _kinds_in(band["band"])]


def _key_regex(bands: list[dict[str, Any]]) -> re.Pattern[str]:
    """`key:` where a key is one or more band names or kind words."""

    names = [band["band"] for band in bands] + [alias for aliases in STAKES_KINDS.values() for alias in aliases]
    units = "|".join(sorted({_name_pattern(name) for name in names} - {""}, key=len, reverse=True))
    return re.compile(rf"(?<!\w)((?:{units})(?:{NAME_SEPARATOR}(?:{units}))*)\s*:", re.IGNORECASE)


def stakes_entries(stakes: str, bands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keyed stakes entries, in order: `{"key", "bands", "kind", "text"}`.

    `bands` lists the campaign bands the entry describes: the one band the key
    names exactly, or else the bands of the key's most specific kind.
    `kind` is None for an exact band name. An entry with no text describes
    nothing. [] means the stakes are one unkeyed line.
    """

    matches = list(_key_regex(bands).finditer(stakes))
    entries: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(stakes)
        key = match.group(1)
        text = stakes[match.end() : end].strip(" \t;|,/")
        exact = [band["band"] for band in bands if _same_name(key, band["band"])]
        kinds = _kinds_in(key)
        kind = None if exact or not kinds else kinds[0]
        described = exact or (_bands_of_kind(kind, bands) if kind is not None else [])
        entries.append({"key": key, "bands": described if text else [], "kind": kind, "text": text})
    return entries


def _entry_for(band: str, entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The stakes entry for one band: an exact name first, then the most specific kind."""

    describing = [entry for entry in entries if band in entry["bands"]]
    if not describing:
        return None
    order = list(STAKES_KINDS)
    return min(describing, key=lambda entry: -1 if entry["kind"] is None else order.index(entry["kind"]))


def stakes_warnings(
    entries: list[dict[str, Any]], chances: dict[str, Any], bands: list[dict[str, Any]]
) -> list[dict[str, str]]:
    """`stakes_unreachable_band` and `stakes_missing_band` findings for one call."""

    reachable = chances["reachable_bands"]
    successes = success_bands(bands)
    warnings: list[dict[str, str]] = []
    unreachable = [
        entry["key"] if entry["bands"] else f"{entry['key']} (no such band)"
        for entry in entries
        if entry["text"] and not set(entry["bands"]) & set(reachable)
    ]
    if unreachable:
        warnings.append(
            {
                "rule": "stakes_unreachable_band",
                "message": f"the stakes describe {', '.join(unreachable)}, which this call cannot reach "
                f"(reachable: {', '.join(reachable)})",
            }
        )
    bad = [band for band in reachable if band not in successes]
    if entries:
        missing = [band for band in bad if _entry_for(band, entries) is None]
    else:
        # One unkeyed line covers a single result below success, not several.
        missing = bad if len(bad) > 1 else []
    if missing:
        warnings.append(
            {
                "rule": "stakes_missing_band",
                "message": f"this call can land in {', '.join(missing)}, which the stakes do not describe; "
                "key each reachable result, such as `cost: ...; failure: ...`",
            }
        )
    return warnings


def _language_code(value: Any) -> str:
    """The primary subtag of a language code in lower case ("tr-TR" -> "tr"), else ""."""

    match = LANGUAGE_CODE_RE.match(value.strip().lower()) if isinstance(value, str) else None
    return match.group(1) if match is not None else ""


def detected_language(campaign: Path) -> str:
    """The play language the presentation lint last detected, "" when none is on record.

    Read from `.repog-runtime/lint_last.json`; a missing or unreadable record
    only leaves the display line to its fallback.
    """

    record = read_json(campaign / RUNTIME_DIR / LINT_RECORD, {})
    if not isinstance(record, dict):
        return ""
    for key in LINT_LANGUAGE_KEYS:
        code = _language_code(record.get(key))
        if code:
            return code
    return ""


def play_language(profile_text: str, detected: str = "") -> str:
    """The display language: `narration.language`, else `detected`, else a records-language code, else English.

    An `auto` (or missing) `narration.language` takes `detected`, the language
    the presentation lint saw in the replies, before the records language,
    which is not the play language unless it is `same`. A code without a
    display table falls back to English.
    """

    narration = block_scalars(profile_text, "narration")
    for value in (narration.get("language"), detected, narration.get("records_language")):
        code = _language_code(value)
        if code:
            return code if code in DISPLAY_WORDS else "en"
    return "en"


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def band_label(band: str, language: str) -> str:
    """A band name in the play language.

    One kind word (`critical`, `failure`) takes the language's word; a band
    name from BAND_PHRASES takes its phrase; any other name shows as written,
    with spaces for '_'.
    """

    kind = _kind_of(band.strip())
    if kind is not None:
        return DISPLAY_WORDS.get(language, DISPLAY_WORDS["en"])[kind]
    key = "_".join(word.casefold() for word in re.split(NAME_SEPARATOR, band.strip()) if word)
    return BAND_PHRASES.get(language, {}).get(key, band.replace("_", " "))


def _stake_clause(band: str, stakes: str, entries: list[dict[str, Any]], words: dict[str, str]) -> str:
    """The GM's stakes text for the rolled band: its keyed entry, or the whole unkeyed line.

    Empty when the stakes are keyed but no entry describes this band.
    """

    if not entries:
        return f"{words['stake']}: {stakes}"
    entry = _entry_for(band, entries)
    return entry["text"] if entry is not None else ""


def _with_clause(head: str, clause: str) -> str:
    """`head · clause` within DISPLAY_MAX; the clause shortens first, so the numbers and band stay."""

    room = DISPLAY_MAX - len(head) - len(CLAUSE_SEPARATOR)
    if clause and room >= MIN_CLAUSE:
        return head + CLAUSE_SEPARATOR + _clip(clause, room)
    return _clip(head, DISPLAY_MAX)


def display_line(
    call: dict[str, Any], outcome: dict[str, Any], entries: list[dict[str, Any]], language: str
) -> str:
    """The Player-facing roll line, at most DISPLAY_MAX characters.

    `<Actor> · <axis> <value> + <factors> vs <difficulty> → <dice> = <band>`,
    then ` · ` and the GM's own stakes text for the rolled band: the matching
    keyed entry's text, or `<at stake>: <stakes>` for an unkeyed stakes line.
    The fixed words and template band names follow the play language.
    """

    words = DISPLAY_WORDS.get(language, DISPLAY_WORDS["en"])
    head = f"{call['actor']} · {call['axis'].replace('_', ' ')} {call['value']}"
    modifiers = _modifier_sum(call)
    if modifiers:
        head += f" {'+' if modifiers > 0 else '-'} {abs(modifiers)}"
    rolled = "+".join(str(face) for face in outcome["dice"]) or words["auto"]
    head += f" {words['vs']} {call['difficulty']} → {rolled} = {band_label(outcome['band'], language)}"
    return _with_clause(head, _stake_clause(outcome["band"], call["stakes"], entries, words))


def _summary(record: dict[str, Any]) -> str:
    return f"ok {record.get('band')} margin {record.get('margin')}"


def _roll_warnings(chances: dict[str, Any], stakes_found: list[dict[str, str]]) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    if chances["certain"]:
        warnings.append(
            {
                "rule": "roll_certain",
                "message": f"even the lowest roll lands in {chances['floor_band']}, a success: narrate that "
                "result without rolling (it is recorded as auto)",
            }
        )
    return warnings + stakes_found


def _campaign_root(path: str | Path) -> Path:
    base = Path(path)
    for folder in (base, base / "campaign"):
        if (folder / "current_state.yaml").is_file():
            return folder
    raise RollCallError("campaign_missing", f"no RePoG campaign (current_state.yaml) at {base}")


def _store_root(path: str | Path) -> Path:
    try:
        return _campaign_root(path)
    except RollCallError:
        return Path(path)


def receipts_path(campaign: str | Path) -> Path:
    return _store_root(campaign) / RUNTIME_DIR / RECEIPTS_FILE


def _campaign_text(path: Path, category: str) -> str | None:
    """A campaign file as text (BOM dropped), None when absent.

    Read strictly: an unreadable or non-UTF-8 file must not pass for an empty
    one, or a configured scale would silently stop applying.
    """

    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise RollCallError("io_error", f"cannot read {path.name}: {exc}") from exc
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RollCallError(
            category, f"{path.name} is not valid UTF-8 (byte {exc.start}); save it as UTF-8 and retry"
        ) from None
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _revision(state_text: str) -> int:
    value = top_scalar(state_text, "continuity_revision")
    if not re.fullmatch(r"-?[0-9]{1,9}", value):
        raise RollCallError("state_invalid", "current_state.yaml has no integer continuity_revision")
    return int(value)


def _profile_text(campaign: Path) -> str:
    """play_profile.yaml as text, "" when absent."""

    return _campaign_text(campaign / "play_profile.yaml", "resolution_invalid") or ""


def _resolution(profile_text: str) -> dict[str, Any] | None:
    try:
        return odds.load_resolution(profile_text)
    except odds.ResolutionError as exc:
        raise RollCallError("resolution_invalid", str(exc)) from exc


def _present(receipt: dict[str, Any], repeat: bool) -> dict[str, Any]:
    """Stable output order, identical for a first roll and its repeats.

    `summary` comes first; a receipt stored before it existed gets one built
    from its band and margin. Each warning names its rule first.
    """

    ordered = json.loads(json.dumps(receipt, sort_keys=True, ensure_ascii=False))
    summary = ordered.pop("summary", None) or _summary(ordered)
    result: dict[str, Any] = {"summary": summary, "ok": True, "repeat": repeat}
    for key in RECEIPT_FIELDS:
        if key in ordered:
            result[key] = ordered.pop(key)
    result.update(ordered)
    if isinstance(result.get("warnings"), list):
        result["warnings"] = [
            {"rule": item.pop("rule"), **item} if isinstance(item, dict) and "rule" in item else item
            for item in result["warnings"]
        ]
    return result


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def roll_call(campaign: str | Path, payload: dict[str, Any], *, now: str | None = None) -> dict[str, Any]:
    """Resolve one declared call and record its receipt (idempotent per roll id)."""

    root = _campaign_root(campaign)
    if not isinstance(payload, dict):
        raise RollCallError("input_invalid", "input must be a JSON object")
    if "seed" in payload or "expression" in payload:
        raise RollCallError(
            "input_invalid",
            "a roll call derives its own seed and die; omit seed and expression (or omit --campaign for a free roll)",
        )
    unknown = sorted(set(payload) - REQUEST_KEYS)
    if unknown:
        raise _unknown_keys("unknown keys", unknown, REQUEST_REQUIRED, REQUEST_OPTIONAL)
    roll_id = _roll_id(payload.get("roll_id"))
    call = normalize_call(payload.get("call"))
    profile_text = _profile_text(root)
    resolution = _resolution(profile_text)
    die, count, sides = _die(payload.get("die"), resolution)
    if resolution is not None:
        _check_scale(call, resolution)
    state_text = _campaign_text(root / "current_state.yaml", "state_invalid") or ""
    revision = _revision(state_text)

    path = receipts_path(root)
    lines = _store_lines(path)
    existing = _newest(lines, roll_id)
    if existing is not None:
        if existing.get("call") != call or existing.get("die") != die:
            raise RollCallError(
                "roll_id_conflict",
                f"roll id {roll_id} was already used for a different call; choose a new roll id "
                "(the earlier roll stays on record)",
            )
        if existing.get("revision") != revision:
            # Name the recorded result: after a commit this is usually a GM
            # re-reading the roll, and a bare "choose a new roll id" invites a re-roll.
            raise RollCallError(
                "roll_id_conflict",
                f"roll id {roll_id} was rolled at revision {existing.get('revision')} with band "
                f"{existing.get('band')}, and that result stands; a new attempt needs a fictional "
                "reason and a new roll id",
            )
        return _present(existing, True)

    campaign_id = top_scalar(state_text, "campaign_id")
    faces = _faces(_seed(campaign_id, revision, roll_id, die, call), count, sides)
    bands = _bands(resolution)
    outcome = evaluate_call(call, faces, resolution)
    chances = call_odds(call, count, sides, bands)
    entries = stakes_entries(call["stakes"], bands)
    receipt = {
        "summary": _summary(outcome),
        "roll_id": roll_id,
        "revision": revision,
        "call": call,
        "die": die,
        **outcome,
        **chances,
        "display": display_line(call, outcome, entries, play_language(profile_text, detected_language(root))),
        "warnings": _roll_warnings(chances, stakes_warnings(entries, chances, bands)),
        "at": now or _now(),
    }
    lines.append(_encode(receipt))
    _write_store(path, lines[-RECEIPT_KEEP:])
    return _present(receipt, False)


# ---------------------------------------------------------------------------
# Call mode: rereads and axis counts
# ---------------------------------------------------------------------------


def reread(campaign: str | Path, payload: dict[str, Any], *, now: str | None = None) -> dict[str, Any]:
    """Record that a past roll is now read under another band (idempotent for the newest reading).

    For a retroactive rules change: the receipt keeps the band it rolled, and
    the appended row names the band the campaign reads it as from now on.
    """

    root = _campaign_root(campaign)
    if not isinstance(payload, dict):
        raise RollCallError("input_invalid", "input must be a JSON object")
    unknown = sorted(set(payload) - set(REREAD_KEYS))
    if unknown:
        raise _unknown_keys("unknown keys", unknown, REREAD_KEYS, ())
    roll_id = _roll_id(payload.get("roll_id"))
    reason = _line(payload.get("reason"), "reason", MAX_REASON)
    new_band = _line(payload.get("new_band"), "new_band", odds.MAX_BAND_NAME)
    names = [band["band"] for band in _bands(_resolution(_profile_text(root)))]
    if new_band not in names:
        raise RollCallError(
            "input_invalid", f"new_band {new_band!r} is not a band of this campaign: {', '.join(names)}"
        )
    state_text = _campaign_text(root / "current_state.yaml", "state_invalid") or ""
    revision = _revision(state_text)

    path = receipts_path(root)
    lines = _store_lines(path)
    if _newest(lines, roll_id) is None:
        raise RollCallError("input_invalid", f"roll id {roll_id} names no recorded roll")
    latest = _newest_reread(lines, roll_id)
    if latest is not None and (latest.get("new_band"), latest.get("reason")) == (new_band, reason):
        return _present_reread(latest, True)
    row = {
        "kind": REREAD_KIND,
        "reread_of": roll_id,
        "reason": reason,
        "new_band": new_band,
        "revision": revision,
        "at": now or _now(),
    }
    lines.append(_encode(row))
    _write_store(path, lines[-RECEIPT_KEEP:])
    return _present_reread(row, False)


def _present_reread(row: dict[str, Any], repeat: bool) -> dict[str, Any]:
    summary = f"ok reread {row.get('reread_of')} as {row.get('new_band')}"
    return {"summary": summary, "ok": True, "repeat": repeat, **row}


def axes(campaign: str | Path, since_revision: int | None = None) -> dict[str, Any]:
    """Receipt counts per actor and axis, at or after `since_revision` (every receipt when None).

    Names group without regard to case and keep the first spelling seen;
    `auto` counts the receipts that took their band without dice.
    """

    if since_revision is not None and type(since_revision) is not int:
        raise RollCallError("input_invalid", "since_revision must be an integer")
    counts: dict[tuple[str, str], dict[str, Any]] = {}
    receipts = 0
    for receipt in read_receipts(_campaign_root(campaign)):
        call, revision = receipt.get("call"), receipt.get("revision")
        if type(revision) is not int or (since_revision is not None and revision < since_revision):
            continue
        if not isinstance(call, dict) or not all(isinstance(call.get(key), str) for key in ("actor", "axis")):
            continue
        row = counts.setdefault(
            (call["actor"].casefold(), call["axis"].casefold()),
            {"actor": call["actor"], "axis": call["axis"], "count": 0, "auto": 0},
        )
        row["count"] += 1
        row["auto"] += receipt.get("auto") is True
        receipts += 1
    rows = sorted(counts.values(), key=lambda row: (row["actor"].casefold(), -row["count"], row["axis"].casefold()))
    return {
        "summary": f"ok receipts {receipts} pairs {len(rows)}",
        "ok": True,
        "since_revision": since_revision,
        "receipts": receipts,
        "axes": rows,
    }


# ---------------------------------------------------------------------------
# Receipt store (library API for the RPG writer and the scene capsule)
#
# The store is handled as raw bytes split on LF only: a line that is not valid
# UTF-8 JSON is skipped by readers and kept verbatim by writers, so one bad
# line can neither hide the other receipts nor get the store truncated.
# ---------------------------------------------------------------------------


def _store_lines(path: Path) -> list[bytes]:
    """The store's non-blank lines (CR dropped), or [] when it does not exist yet.

    A UTF-8 byte order mark, which some editors add on save, is dropped: left
    in place it would make the first receipt unreadable, and its roll id free
    to be rolled again.
    """

    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise RollCallError("io_error", f"cannot read the roll receipts at {path}: {exc}") from exc
    if data.startswith(UTF8_BOM):
        data = data[len(UTF8_BOM) :]
    return [line.rstrip(b"\r") for line in data.split(b"\n") if line.strip()]


def _decode(line: bytes) -> dict[str, Any] | None:
    try:
        value = json.loads(line.decode("utf-8"))
    except (ValueError, RecursionError):
        # Bad UTF-8, bad JSON, or an integer past Python's digit limit (a plain
        # ValueError, not a JSONDecodeError): one bad line is skipped, never fatal.
        return None
    return value if isinstance(value, dict) else None


def _encode(record: dict[str, Any]) -> bytes:
    return json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8")


def is_reread(record: dict[str, Any]) -> bool:
    """True for a reread row, which is never a receipt."""

    return record.get("kind") == REREAD_KIND


def _newest(lines: list[bytes], roll_id: str) -> dict[str, Any] | None:
    """The newest receipt (never a reread row) with this roll id."""

    for line in reversed(lines):
        record = _decode(line)
        if record is not None and not is_reread(record) and record.get("roll_id") == roll_id:
            return record
    return None


def _newest_reread(lines: list[bytes], roll_id: str) -> dict[str, Any] | None:
    for line in reversed(lines):
        record = _decode(line)
        if record is not None and is_reread(record) and record.get("reread_of") == roll_id:
            return record
    return None


def _replace_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
        for attempt in range(3):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                # Windows refuses the replace while another process briefly holds the file.
                if attempt == 2:
                    raise
                time.sleep(0.05 * (attempt + 1))
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _write_store(path: Path, lines: list[bytes]) -> None:
    """Replace the store atomically (temp file, then os.replace), LF only."""

    try:
        _replace_bytes(path, b"".join(line + b"\n" for line in lines))
    except OSError as exc:
        raise RollCallError("io_error", f"cannot write the roll receipts at {path}: {exc}") from exc


def _records(campaign: str | Path) -> list[dict[str, Any]]:
    return [record for record in map(_decode, _store_lines(receipts_path(campaign))) if record is not None]


def read_receipts(campaign: str | Path) -> list[dict[str, Any]]:
    """Every readable receipt, oldest first, without reread rows; [] when the store does not exist."""

    return [record for record in _records(campaign) if not is_reread(record)]


def read_rereads(campaign: str | Path) -> list[dict[str, Any]]:
    """Every reread row, oldest first: `{kind, reread_of, reason, new_band, revision, at}`."""

    return [record for record in _records(campaign) if is_reread(record)]


def find_receipt(campaign: str | Path, roll_id: str) -> dict[str, Any] | None:
    """The newest receipt with this roll id (trimmed, NFC), or None."""

    if not isinstance(roll_id, str) or not roll_id.strip():
        return None
    return _newest(_store_lines(receipts_path(campaign)), _canonical_id(roll_id))


def open_receipts(campaign: str | Path, revision: int) -> list[dict[str, Any]]:
    """Receipts rolled at `revision` that no commit has consumed yet ([] for a non-integer revision)."""

    if type(revision) is not int:
        return []
    return [
        record
        for record in read_receipts(campaign)
        if type(record.get("revision")) is int
        and record["revision"] == revision
        and record.get("consumed_revision") is None
    ]


def mark_consumed(campaign: str | Path, roll_ids: Iterable[str] | str, revision: int) -> list[str]:
    """Stamp `consumed_revision` on unconsumed receipts; returns the ids stamped.

    Rewrites the store atomically and is safe to repeat: already consumed
    receipts are left alone, and unreadable lines are kept verbatim. A single
    id may be passed as a plain string.
    """

    if type(revision) is not int:
        raise RollCallError("input_invalid", "revision must be an integer")
    if isinstance(roll_ids, str):
        roll_ids = [roll_ids]
    wanted = {_canonical_id(roll_id) for roll_id in roll_ids if isinstance(roll_id, str) and roll_id.strip()}
    path = receipts_path(campaign)
    lines = _store_lines(path) if wanted else []
    marked: list[str] = []
    for index, line in enumerate(lines):
        record = _decode(line)
        if (
            record is None
            or is_reread(record)
            or not isinstance(record.get("roll_id"), str)
            or record["roll_id"] not in wanted
            or record.get("consumed_revision") is not None
        ):
            continue
        record["consumed_revision"] = revision
        lines[index] = _encode(record)
        if record["roll_id"] not in marked:
            marked.append(record["roll_id"])
    if marked:
        _write_store(path, lines)
    return marked


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_request(raw: str) -> dict[str, Any]:
    """The request object, or a typed failure the CLI can print.

    Malformed JSON stays a JSONDecodeError, whose message the 0.2.0 output
    carries. `json.loads` also raises a plain ValueError for an integer past
    Python's digit limit and a RecursionError for very deep nesting; both
    become a DiceError so they reach the typed error output, not a traceback.
    """

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise
    except RecursionError:
        raise DiceError("input JSON is nested too deeply") from None
    except ValueError:
        raise DiceError("input JSON holds a number with too many digits") from None
    if not isinstance(payload, dict):
        raise DiceError("input must be a JSON object")
    return payload


def read_input_file(path: str) -> str:
    """The request text from a UTF-8 file, or from standard input when `path` is '-'.

    Read as bytes and decoded strictly as UTF-8 with a leading byte order mark
    dropped, never in the console or locale code page.
    """

    label = "standard input" if path == "-" else f"--input-file {path}"
    if path == "-":
        stream = getattr(sys.stdin, "buffer", None)
        if stream is None:
            raise RollCallError("io_error", "standard input is not available; pass --input-file PATH or --input-json")
        read = stream.read
    else:
        read = Path(path).read_bytes
    try:
        data = read()
    except (OSError, ValueError) as exc:  # ValueError: a NUL in the path, or a closed stream
        raise RollCallError("io_error", f"cannot read {label}: {getattr(exc, 'strerror', None) or exc}") from None
    # Strip the mark here rather than with utf-8-sig, which counts error offsets after it.
    offset = len(UTF8_BOM) if data.startswith(UTF8_BOM) else 0
    try:
        return data[offset:].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RollCallError(
            "input_invalid",
            f"{label} is not valid UTF-8 (byte {offset + exc.start}); save the request as UTF-8 and retry",
        ) from None


def _expression_main(read_request: Callable[[], str]) -> int:
    try:
        payload = _parse_request(read_request())
        if "call" in payload:
            raise DiceError("a roll call needs --campaign <campaign folder>")
        result = roll(payload)
    except (json.JSONDecodeError, DiceError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def _campaign_main(run: Callable[[], dict[str, Any]]) -> int:
    """Run one call-mode command and print its result or typed failure."""

    def failure(category: str, reason: str) -> dict[str, Any]:
        return {"ok": False, "failure_category": category, "failure_reason": reason}

    exit_code = 2
    try:
        result = run()
        exit_code = 0
    except json.JSONDecodeError as exc:
        result = failure("input_invalid", f"invalid JSON: {exc}")
    except RollCallError as exc:
        result = failure(exc.category, str(exc))
    except DiceError as exc:
        result = failure("input_invalid", str(exc))
    except (OSError, UnicodeError) as exc:
        result = failure("io_error", str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return exit_code


def main(argv: list[str] | None = None) -> int:
    # `python -OO` (or PYTHONOPTIMIZE=2) strips docstrings, so __doc__ may be None.
    parser = argparse.ArgumentParser(description=(__doc__ or "").partition("\n")[0] or None)
    parser.add_argument(
        "command",
        nargs="?",
        choices=("axes", "reread"),
        help="With --campaign: 'axes' counts receipts per actor and axis; 'reread' records a past roll's "
        "new band from a request of roll_id, reason and new_band. Omit to roll.",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input-json", help="Dice request as one JSON object.")
    source.add_argument(
        "--input-file",
        metavar="PATH",
        help="Read the request from a UTF-8 file, or from standard input when PATH is -, so prose needs no shell quoting.",
    )
    parser.add_argument(
        "--campaign",
        help="Campaign folder: roll a declared call and record its receipt instead of a free expression.",
    )
    parser.add_argument("--since-revision", type=int, metavar="N", help="axes: count receipts at or after revision N.")
    args = parser.parse_args(argv)
    has_request = args.input_json is not None or args.input_file is not None
    if args.command is not None and args.campaign is None:
        parser.error(f"{args.command} needs --campaign <campaign folder>")
    if args.since_revision is not None and args.command != "axes":
        parser.error("--since-revision belongs to the axes command")
    if args.command == "axes":
        if has_request:
            parser.error("axes reads the receipt store and takes no request")
        return _campaign_main(lambda: axes(args.campaign, args.since_revision))
    if not has_request:
        parser.error("one of the arguments --input-json --input-file is required")

    def read_request() -> str:
        # Read inside each mode's error handling, so a bad file reports in that mode's shape.
        return args.input_json if args.input_file is None else read_input_file(args.input_file)

    if args.command == "reread":
        return _campaign_main(lambda: reread(args.campaign, _parse_request(read_request())))
    if args.campaign is None:
        return _expression_main(read_request)
    return _campaign_main(lambda: roll_call(args.campaign, _parse_request(read_request())))


if __name__ == "__main__":
    sys.exit(main())

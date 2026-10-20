"""Roll one bounded, reproducible NdM+/-K expression and emit JSON.

Two modes share this helper:

- Expression mode (`--input-json` alone) rolls a free `NdM+/-K` expression
  with an optional caller seed. Its output shape is unchanged since 0.2.0.
- Call mode (`--campaign <path> --input-json {"call": ..., "roll_id": ...}`)
  rolls a declared check: actor, axis, stat value, difficulty, modifiers, and
  stakes are fixed before the die is seen. The seed is derived from the
  campaign id, the continuity revision, the roll id, and the canonical call,
  so repeating the same call returns the same receipt and a different result
  needs a new roll id, which stays on record. Receipts are appended to
  `campaign/.repog-runtime/rolls.jsonl`, the runtime store the writer checks
  when a commit cites a roll.

A roll supplies numbers and a band name, never the fictional meaning of the
result; that stays with the GM.
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
from typing import Any, Iterable

import odds
from repog_runtime import RUNTIME_DIR, top_scalar


DICE_RE = re.compile(r"^\s*(\d{1,3})[dD](\d{1,4})(?:\s*([+-])\s*(\d{1,6}))?\s*$")
MAX_DICE = 100
MAX_SIDES = 1000
MAX_ABS_MODIFIER = 100_000

# Call mode limits. A call is a short declaration, not a narration.
MAX_ROLL_ID = 80
ROLL_ID_PUNCTUATION = frozenset("_.:-")
REQUEST_KEYS = frozenset({"call", "roll_id", "die"})
CALL_KEYS = frozenset({"actor", "axis", "value", "difficulty", "factors", "stakes"})
FACTOR_KEYS = frozenset({"label", "modifier"})
MAX_NAME = 80
MAX_STAKES = 500
MAX_FACTORS = 12
MAX_ABS_CALL_NUMBER = 1000
RECEIPTS_FILE = "rolls.jsonl"
RECEIPT_KEEP = 2000
RECEIPT_FIELDS = ("roll_id", "revision", "call", "die", "dice", "total", "margin", "band", "auto", "at")
SEED_DOMAIN = "repog-roll-call-v1"
UTF8_BOM = b"\xef\xbb\xbf"


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


def normalize_call(call: Any) -> dict[str, Any]:
    """The canonical call: trimmed text, integer numbers, factors always listed."""

    if not isinstance(call, dict):
        raise RollCallError("input_invalid", "call must be an object")
    unknown = sorted(set(call) - CALL_KEYS)
    if unknown:
        raise RollCallError("input_invalid", f"call has unknown keys: {', '.join(unknown)}")
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
    return {
        "actor": _line(call.get("actor"), "call.actor", MAX_NAME),
        "axis": _line(call.get("axis"), "call.axis", MAX_NAME),
        "value": _whole(call.get("value"), "call.value"),
        "difficulty": _whole(call.get("difficulty"), "call.difficulty"),
        "factors": factors,
        "stakes": _line(call.get("stakes"), "call.stakes", MAX_STAKES),
    }


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
    return _canonical_id(value)


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


def evaluate_call(call: dict[str, Any], faces: list[int], resolution: dict[str, Any] | None) -> dict[str, Any]:
    """Total, margin, band, and auto flag for a normalized call and rolled faces.

    Pure: an auto success ignores `faces` and records no dice.
    """

    modifiers = sum(factor["modifier"] for factor in call["factors"])
    auto = odds.is_auto(resolution, call["value"], call["difficulty"], modifiers)
    dice = [] if auto else list(faces)
    total = call["value"] + modifiers + sum(dice)
    margin = total - call["difficulty"]
    bands = resolution["bands"] if resolution else odds.DEFAULT_BANDS
    band = bands[0]["band"] if auto else odds.band_for(margin, bands)
    return {"dice": dice, "total": total, "margin": margin, "band": band, "auto": auto}


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


def _resolution(campaign: Path) -> dict[str, Any] | None:
    text = _campaign_text(campaign / "play_profile.yaml", "resolution_invalid")
    if text is None:
        return None
    try:
        return odds.load_resolution(text)
    except odds.ResolutionError as exc:
        raise RollCallError("resolution_invalid", str(exc)) from exc


def _present(receipt: dict[str, Any], repeat: bool) -> dict[str, Any]:
    """Stable output order, identical for a first roll and its repeats."""

    ordered = json.loads(json.dumps(receipt, sort_keys=True, ensure_ascii=False))
    result: dict[str, Any] = {"ok": True, "repeat": repeat}
    for key in RECEIPT_FIELDS:
        if key in ordered:
            result[key] = ordered.pop(key)
    result.update(ordered)
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
        raise RollCallError("input_invalid", f"unknown keys: {', '.join(unknown)}")
    roll_id = _roll_id(payload.get("roll_id"))
    call = normalize_call(payload.get("call"))
    resolution = _resolution(root)
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
    receipt = {
        "roll_id": roll_id,
        "revision": revision,
        "call": call,
        "die": die,
        **evaluate_call(call, faces, resolution),
        "at": now or _now(),
    }
    lines.append(_encode(receipt))
    _write_store(path, lines[-RECEIPT_KEEP:])
    return _present(receipt, False)


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


def _newest(lines: list[bytes], roll_id: str) -> dict[str, Any] | None:
    for line in reversed(lines):
        record = _decode(line)
        if record is not None and record.get("roll_id") == roll_id:
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


def read_receipts(campaign: str | Path) -> list[dict[str, Any]]:
    """Every readable receipt, oldest first; [] when the store does not exist."""

    return [record for record in map(_decode, _store_lines(receipts_path(campaign))) if record is not None]


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


def _expression_main(raw: str) -> int:
    try:
        payload = _parse_request(raw)
        if "call" in payload:
            raise DiceError("a roll call needs --campaign <campaign folder>")
        result = roll(payload)
    except (json.JSONDecodeError, DiceError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def _call_main(campaign: str, raw: str) -> int:
    def failure(category: str, reason: str) -> dict[str, Any]:
        return {"ok": False, "failure_category": category, "failure_reason": reason}

    exit_code = 2
    try:
        payload = _parse_request(raw)
        result = roll_call(campaign, payload)
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
    parser.add_argument("--input-json", required=True, help="Dice request as one JSON object.")
    parser.add_argument(
        "--campaign",
        help="Campaign folder: roll a declared call and record its receipt instead of a free expression.",
    )
    args = parser.parse_args(argv)
    if args.campaign is None:
        return _expression_main(args.input_json)
    return _call_main(args.campaign, args.input_json)


if __name__ == "__main__":
    sys.exit(main())

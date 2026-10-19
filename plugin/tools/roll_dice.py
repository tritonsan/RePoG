"""Roll one bounded, reproducible NdM+/-K expression and emit JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import secrets
import sys
from typing import Any


DICE_RE = re.compile(r"^\s*(\d{1,3})[dD](\d{1,4})(?:\s*([+-])\s*(\d{1,6}))?\s*$")
MAX_DICE = 100
MAX_SIDES = 1000
MAX_ABS_MODIFIER = 100_000


class DiceError(ValueError):
    """Raised for malformed or unsafe dice requests."""


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", required=True, help="Dice request as one JSON object.")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input_json)
        if not isinstance(payload, dict):
            raise DiceError("input must be a JSON object")
        result = roll(payload)
    except (json.JSONDecodeError, DiceError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

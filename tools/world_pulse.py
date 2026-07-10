"""Produce a deterministic uncertainty envelope for an on-demand world update."""

from __future__ import annotations

import argparse
import json
import random
import secrets
import sys
from typing import Any


DIRECTIONS = ("advance", "setback", "opportunity", "complication", "stasis")


def _fail(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message}


def generate_pulse(payload: dict[str, Any]) -> dict[str, Any]:
    domain = payload.get("domain")
    if not isinstance(domain, str) or not domain.strip():
        return _fail("domain must be a non-empty string")

    try:
        elapsed_steps = int(payload.get("elapsed_steps", 0))
        volatility = int(payload.get("volatility", 0))
        pressure = int(payload.get("pressure", 0))
        event_cap = int(payload.get("event_cap", 3))
    except (TypeError, ValueError):
        return _fail("elapsed_steps, volatility, pressure, and event_cap must be integers")

    if elapsed_steps < 0:
        return _fail("elapsed_steps must be at least 0")
    if not 0 <= volatility <= 3:
        return _fail("volatility must be between 0 and 3")
    if not 0 <= pressure <= 4:
        return _fail("pressure must be between 0 and 4")
    if not 1 <= event_cap <= 5:
        return _fail("event_cap must be between 1 and 5")

    raw_seed = payload.get("seed")
    try:
        seed = secrets.randbits(63) if raw_seed is None else int(raw_seed)
    except (TypeError, ValueError):
        return _fail("seed must be an integer when provided")

    rng = random.Random(seed)
    opportunities = min(event_cap, 1 + elapsed_steps // 3 + volatility // 2)
    chance = min(0.95, 0.08 + elapsed_steps * 0.08 + volatility * 0.13 + pressure * 0.09)

    event_count = sum(1 for _ in range(opportunities) if rng.random() < chance)
    if event_count == 0 and pressure >= 4 and elapsed_steps > 0:
        event_count = 1

    weights = {
        "advance": 3 + pressure,
        "setback": 2 + volatility,
        "opportunity": 3,
        "complication": 2 + volatility + pressure // 2,
        "stasis": max(1, 5 - elapsed_steps - volatility),
    }

    events = []
    for index in range(event_count):
        direction = rng.choices(DIRECTIONS, weights=[weights[name] for name in DIRECTIONS], k=1)[0]
        intensity = min(3, 1 + int(rng.random() < (0.25 + volatility * 0.12)) + int(pressure >= 4))
        events.append({"slot": index + 1, "direction": direction, "intensity": intensity})

    return {
        "ok": True,
        "domain": domain.strip(),
        "seed": seed,
        "inputs": {
            "elapsed_steps": elapsed_steps,
            "volatility": volatility,
            "pressure": pressure,
            "event_cap": event_cap,
        },
        "event_count": event_count,
        "events": events,
        "instruction": (
            "Interpret only these uncertainty slots. Use campaign context to decide semantic events, "
            "then record only durable changes and player-perceivable consequences."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", required=True, help="World pulse input as one JSON object.")
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.input_json)
    except json.JSONDecodeError as exc:
        print(json.dumps(_fail(f"invalid JSON: {exc}"), indent=2))
        return 2

    if not isinstance(payload, dict):
        print(json.dumps(_fail("input must be a JSON object"), indent=2))
        return 2

    result = generate_pulse(payload)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())

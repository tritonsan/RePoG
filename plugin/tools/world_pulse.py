"""Produce a deterministic uncertainty envelope for an on-demand world update.

One request names one domain.  A time skip that touches several domains can
send them together as ``{"domains": [<request>, ...]}`` (at most 12); each
result is identical to the matching single-domain call and keeps its order.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from typing import Any


DIRECTIONS = ("advance", "setback", "opportunity", "complication", "stasis")
MAX_BATCH_DOMAINS = 12


def _fail(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message}


def _integer(value: Any, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer")
    return value


def _encodable(text: str) -> bool:
    """False for strings with lone surrogates, which JSON escapes can smuggle in."""
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _stable_seed(evaluation_id: str, domain: str) -> int:
    digest = hashlib.sha256(f"repog-world-pulse-v2\0{evaluation_id}\0{domain}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def generate_pulse(payload: dict[str, Any]) -> dict[str, Any]:
    domain = payload.get("domain")
    if not isinstance(domain, str) or not domain.strip():
        return _fail("domain must be a non-empty string")
    if not _encodable(domain):
        return _fail("domain must be valid Unicode text (it contains a lone surrogate)")

    try:
        elapsed_steps = _integer(payload.get("elapsed_steps", 0), "elapsed_steps")
        volatility = _integer(payload.get("volatility", 0), "volatility")
        pressure = _integer(payload.get("pressure", 0), "pressure")
        event_cap = _integer(payload.get("event_cap", 3), "event_cap")
    except ValueError as exc:
        return _fail(str(exc))

    if elapsed_steps < 0:
        return _fail("elapsed_steps must be at least 0")
    if not 0 <= volatility <= 3:
        return _fail("volatility must be between 0 and 3")
    if not 0 <= pressure <= 4:
        return _fail("pressure must be between 0 and 4")
    if not 1 <= event_cap <= 5:
        return _fail("event_cap must be between 1 and 5")

    evaluation_id = payload.get("evaluation_id")
    raw_seed = payload.get("seed")
    if evaluation_id is not None and (not isinstance(evaluation_id, str) or not evaluation_id.strip()):
        return _fail("evaluation_id must be a non-empty string when provided")
    if evaluation_id is not None and not _encodable(evaluation_id):
        return _fail("evaluation_id must be valid Unicode text (it contains a lone surrogate)")
    if raw_seed is None:
        if not isinstance(evaluation_id, str) or not evaluation_id.strip():
            return _fail("evaluation_id is required unless a legacy seed is provided")
        evaluation_id = evaluation_id.strip()
        seed = _stable_seed(evaluation_id, domain.strip())
        seed_source = "evaluation_id"
    else:
        if type(raw_seed) is not int:
            return _fail("seed must be an integer when provided")
        seed = raw_seed
        seed_source = "explicit_seed"

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
        "evaluation_id": evaluation_id,
        "seed": seed,
        "seed_source": seed_source,
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


def generate_batch(payload: dict[str, Any]) -> dict[str, Any]:
    """Run several single-domain requests; any invalid entry fails the whole batch."""
    extra = sorted(key for key in payload if key != "domains")
    if extra:
        return _fail(
            f"a batch request takes only 'domains'; move {', '.join(extra)} into each domain entry"
        )
    requests = payload.get("domains")
    if not isinstance(requests, list) or not requests:
        return _fail("domains must be a non-empty array")
    if len(requests) > MAX_BATCH_DOMAINS:
        return _fail(f"domains accepts at most {MAX_BATCH_DOMAINS} entries")
    results = []
    for index, request in enumerate(requests):
        if not isinstance(request, dict):
            return _fail(f"domains[{index}] must be an object")
        if "domains" in request:
            return _fail(f"domains[{index}] cannot itself be a batch")
        result = generate_pulse(request)
        if not result["ok"]:
            return _fail(f"domains[{index}]: {result['error']}")
        results.append(result)
    return {"ok": True, "results": results}


def handle_request(payload: Any) -> dict[str, Any]:
    """Dispatch a single-domain request or a ``domains`` batch."""
    if not isinstance(payload, dict):
        return _fail("input must be a JSON object")
    if "domains" in payload:
        return generate_batch(payload)
    return generate_pulse(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", required=True, help="World pulse input as one JSON object.")
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.input_json)
    except RecursionError:
        print(json.dumps(_fail("invalid JSON: it is nested too deeply"), indent=2))
        return 2
    except ValueError as exc:  # JSONDecodeError, or an integer literal too long to convert
        print(json.dumps(_fail(f"invalid JSON: {exc}"), indent=2))
        return 2

    if not isinstance(payload, dict):
        print(json.dumps(_fail("input must be a JSON object"), indent=2))
        return 2

    result = handle_request(payload)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())

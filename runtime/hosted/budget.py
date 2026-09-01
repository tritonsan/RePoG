from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


SESSION_LIMIT_MICRO_USD = 1_000_000
DAILY_LIMIT_MICRO_USD = 10_000_000


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int


def estimate_micro_usd(usage: Usage) -> int:
    """Luna in-region ceiling: $0.22/M input, $0.022/M cached, $1.32/M output."""
    uncached = max(0, usage.input_tokens - usage.cached_input_tokens)
    dollars = Decimal(uncached) * Decimal("0.22") / 1_000_000
    dollars += Decimal(usage.cached_input_tokens) * Decimal("0.022") / 1_000_000
    dollars += Decimal(usage.output_tokens) * Decimal("1.32") / 1_000_000
    return max(1, int(dollars * 1_000_000))


def ensure_within_limits(session_spend: int, daily_spend: int, reservation: int) -> None:
    if session_spend + reservation > SESSION_LIMIT_MICRO_USD:
        raise RuntimeError("session_budget_exhausted")
    if daily_spend + reservation > DAILY_LIMIT_MICRO_USD:
        raise RuntimeError("daily_budget_exhausted")

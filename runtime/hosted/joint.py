from __future__ import annotations

from typing import Any


def compile_joint_context(state: dict[str, Any], intents: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Build the bounded beat without ever inventing a missing participant."""
    return {
        "manifest": state["manifest"],
        "turn": state["turn_brief"],
        "human_intent": intents.get("human"),
        "agent_intent": intents.get("agent"),
        "resolution_contract": {
            "joint_causal_beat": True,
            "agent_intent_is_proposal_only": True,
            "missing_intents_must_remain_null": True,
            "character_autonomy": "The Agent Seat may cooperate, refuse, negotiate, or choose a character-consistent third action.",
        },
    }

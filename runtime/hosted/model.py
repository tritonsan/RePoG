from __future__ import annotations

import json
import os
from typing import Any

from aws_bedrock_token_generator import provide_token
from openai import BedrockOpenAI

MODEL_ID = "openai.gpt-5.6-luna"


def client() -> BedrockOpenAI:
    region = os.environ.get("AWS_REGION", "us-east-1")
    return BedrockOpenAI(aws_region=region, bedrock_token_provider=lambda: provide_token(region=region))


def resolve_turn(context: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
    response = client().responses.create(
        model=MODEL_ID,
        store=False,
        max_output_tokens=2500,
        input=[
            {"role": "developer", "content": "You are RePoG's bounded GM reasoning layer. Resolve only supplied human and agent intents. Never invent a missing seat intent. The character may cooperate, refuse, negotiate, or choose a third action according to its values and decision rules. The next_turn must be a complete Agent Turn Brief v1 for the same session and controlled character, with turn_number and revision incremented exactly once and a fresh turn_id. For this hosted jury run set persistence.mode to none and persistence.request to an empty object; the runtime durably records the validated next turn and public event. Return strict JSON with narration, persistence, agent_outcome, visible_consequences, and next_turn."},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        text={"format": {"type": "json_schema", "name": "repog_joint_turn", "strict": True, "schema": {
            "type": "object", "additionalProperties": False,
            "required": ["narration", "persistence", "agent_outcome", "visible_consequences", "next_turn"],
            "properties": {
                "narration": {"type": "string", "maxLength": 6000},
                "persistence": {"type": "object", "additionalProperties": False, "required": ["mode", "request"], "properties": {"mode": {"type": "string", "enum": ["none", "durable", "checkpoint"]}, "request": {"type": "object", "additionalProperties": True}}},
                "agent_outcome": {"type": "string", "enum": ["accepted", "altered", "rejected", "skipped"]},
                "visible_consequences": {"type": "array", "maxItems": 12, "items": {"type": "string", "maxLength": 600}},
                "next_turn": {"type": "object", "additionalProperties": True},
            },
        }}},
    )
    value = json.loads(response.output_text)
    usage = getattr(response, "usage", None)
    counts = {
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "cached_input_tokens": int(getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
    }
    return value, counts

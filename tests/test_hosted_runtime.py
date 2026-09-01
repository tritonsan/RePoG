import time
from pathlib import Path

import pytest

from runtime.hosted.budget import Usage, ensure_within_limits, estimate_micro_usd
from runtime.hosted.security import AuthenticationError, sign, verify
from runtime.hosted.joint import compile_joint_context
from runtime.hosted.contracts import validate_bootstrap, validate_resolution


ROOT = Path(__file__).parents[1]


def test_signed_request_round_trip_and_tamper_rejection():
    now = int(time.time())
    body = b'{"mode":"prepared"}'
    headers = {"X-RePoG-Timestamp": str(now), "X-RePoG-Nonce": "once", "X-RePoG-Signature": sign("secret", str(now), "once", "POST", "/runtime/v1/sessions", body)}
    assert verify("secret", headers, "POST", "/runtime/v1/sessions", body, now=now) == "once"
    with pytest.raises(AuthenticationError):
        verify("secret", headers, "POST", "/runtime/v1/sessions", b'{}', now=now)


def test_luna_cost_ceiling_and_hard_limits():
    assert estimate_micro_usd(Usage(input_tokens=100_000, cached_input_tokens=0, output_tokens=10_000)) == 35_200
    ensure_within_limits(900_000, 9_000_000, 50_000)
    with pytest.raises(RuntimeError, match="session_budget_exhausted"):
        ensure_within_limits(990_000, 0, 20_000)
    with pytest.raises(RuntimeError, match="daily_budget_exhausted"):
        ensure_within_limits(0, 9_990_000, 20_000)


def test_missing_agent_intent_stays_missing_and_autonomy_is_explicit():
    context = compile_joint_context({"manifest": {"characters": []}, "turn_brief": {"session": {"turn_id": "turn-1"}}}, {"human": {"action": "Open the door"}})
    assert context["human_intent"] == {"action": "Open the door"}
    assert context["agent_intent"] is None
    assert context["resolution_contract"]["agent_intent_is_proposal_only"] is True
    assert "refuse" in context["resolution_contract"]["character_autonomy"]


def test_infrastructure_locks_luna_and_real_coordination_window():
    template = (ROOT / "infra" / "aws" / "template.yaml").read_text(encoding="utf-8")
    model = (ROOT / "runtime" / "hosted" / "model.py").read_text(encoding="utf-8")
    assert '"Seconds":15' in template
    assert "ReservedConcurrentExecutions: 5" in template
    assert 'MODEL_ID = "openai.gpt-5.6-luna"' in model
    assert "terra" not in model.lower()


def test_reviewed_golden_bootstrap_is_contract_valid():
    bootstrap = __import__("json").loads(
        (ROOT / "infra" / "aws" / "golden" / "black-gull" / "bootstrap.json").read_text(encoding="utf-8")
    )
    validate_bootstrap(bootstrap)


def test_next_turn_must_advance_same_session_and_character():
    bootstrap = __import__("json").loads(
        (ROOT / "infra" / "aws" / "golden" / "black-gull" / "bootstrap.json").read_text(encoding="utf-8")
    )
    state = {"turn_brief": bootstrap["initial_turn"]}
    next_turn = __import__("copy").deepcopy(bootstrap["initial_turn"])
    next_turn["session"].update({"turn_id": "black-gull-turn-002", "turn_number": 2, "revision": 13})
    resolution = {"next_turn": next_turn}
    validate_resolution(state, resolution)
    next_turn["session"]["turn_id"] = bootstrap["initial_turn"]["session"]["turn_id"]
    with pytest.raises(RuntimeError, match="next_turn_id_reused"):
        validate_resolution(state, resolution)

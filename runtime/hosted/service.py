from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3

from .budget import Usage, estimate_micro_usd
from . import model, persistence, storage
from .joint import compile_joint_context
from .contracts import validate_bootstrap, validate_resolution

SESSION_SECONDS = 90 * 60
MAX_TURNS = 20
TURN_RESERVATION_MICRO_USD = 250_000


def create_session(payload: dict[str, Any]) -> dict[str, Any]:
    mode = payload.get("mode", "prepared")
    if mode not in {"prepared", "quick_forge"}:
        raise ValueError("mode_invalid")
    if mode == "quick_forge" and payload.get("webmcp_opt_in") is not True:
        raise ValueError("quick_forge_requires_explicit_webmcp_opt_in")
    bootstrap = storage.load_golden_bootstrap()
    validate_bootstrap(bootstrap)
    session_id = f"hosted-{uuid.uuid4()}"
    now = int(time.time())
    state = {
        "pk": f"SESSION#{session_id}", "sk": "STATE", "session_id": session_id,
        "site_session_id": str(payload.get("site_session_id", "")), "mode": mode,
        "runtime_status": "forging" if mode == "quick_forge" else "ready",
        "revision": 0, "turn_number": 1, "turn_id": bootstrap["initial_turn"]["session"]["turn_id"],
        "manifest": bootstrap["manifest"], "turn_brief": bootstrap["initial_turn"],
        "spend_reserved": 0, "spend_settled": 0, "spend_total": 0, "window_execution": "",
        "created_at": now, "updated_at": now, "expires_at": now + SESSION_SECONDS,
    }
    storage.create_session(state)
    persistence.initialize_workspace(os.environ["REPOG_WORKSPACE_BUCKET"], session_id)
    if mode == "quick_forge":
        boto3.client("stepfunctions").start_execution(
            stateMachineArn=os.environ["REPOG_FORGE_STATE_MACHINE_ARN"],
            name=session_id.replace("hosted-", "forge-"),
            input=__import__("json").dumps({"action": "quick_forge", "session_id": session_id, "forge_prompt": str(payload.get("forge_prompt", ""))[:2000]}),
        )
    return {"ok": True, "session_id": session_id, "status": state["runtime_status"], "expires_at": datetime.fromtimestamp(state["expires_at"], timezone.utc).isoformat(), "manifest": state["manifest"], "initial_turn": state["turn_brief"]}


def submit_intent(session_id: str, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    state = storage.get_session(session_id)
    if int(state["expires_at"]) <= int(time.time()) or int(state["turn_number"]) > MAX_TURNS:
        raise RuntimeError("session_limit_reached")
    if kind == "agent" and str(payload.get("expected_turn_id", "")) != state["turn_id"]:
        raise RuntimeError("stale_turn")
    operation_id = str(payload.get("operation_id") or uuid.uuid4())
    created = storage.store_intent(session_id, state["turn_id"], kind, operation_id, payload)
    if created and not state.get("window_execution"):
        execution_name = f"turn-{session_id[-24:]}-{state['turn_number']}"
        step_functions = boto3.client("stepfunctions")
        try:
            response = step_functions.start_execution(
                stateMachineArn=os.environ["REPOG_TURN_STATE_MACHINE_ARN"],
                name=execution_name,
                input=__import__("json").dumps({"action": "resolve_turn", "session_id": session_id, "turn_id": state["turn_id"]}),
            )
            execution_arn = response["executionArn"]
        except step_functions.exceptions.ExecutionAlreadyExists:
            execution_arn = f"{os.environ['REPOG_TURN_STATE_MACHINE_ARN'].replace(':stateMachine:', ':execution:')}:{execution_name}"
        storage.mark_window_started(session_id, state["turn_id"], execution_arn)
    return {"ok": True, "operation_id": operation_id, "status": "pending", "coordination_window_ms": 15_000, "idempotent": not created}


def resolve_joint_turn(session_id: str, turn_id: str) -> dict[str, Any]:
    state = storage.get_session(session_id)
    if state["turn_id"] != turn_id:
        return {"ok": True, "status": "superseded"}
    intents = storage.get_intents(session_id, turn_id)
    # Missing keys stay absent. In particular, no agent intent is synthesized.
    context = compile_joint_context(state, intents)
    day_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    storage.reserve(session_id, TURN_RESERVATION_MICRO_USD, day_key)
    storage.table().update_item(Key={"pk": f"SESSION#{session_id}", "sk": "STATE"}, UpdateExpression="SET runtime_status = :status", ExpressionAttributeValues={":status": "resolving"})
    try:
        resolution, counts = model.resolve_turn(context)
        validate_resolution(state, resolution)
        actual = estimate_micro_usd(Usage(**counts))
        persistence.apply(os.environ["REPOG_WORKSPACE_BUCKET"], session_id, resolution["persistence"])
        storage.commit_resolution(session_id, int(state["revision"]), resolution)
        storage.put_event(session_id, int(state["revision"]) + 1, {"type": "turn_resolved", "narration": resolution["narration"], "agent_intent_present": "agent" in intents, "agent_operation_id": intents.get("agent", {}).get("operation_id"), "agent_outcome": resolution["agent_outcome"], "visible_consequences": resolution["visible_consequences"]})
        storage.settle(session_id, TURN_RESERVATION_MICRO_USD, actual, day_key)
        return {"ok": True, "status": "ready", "revision": int(state["revision"]) + 1}
    except Exception:
        storage.settle(session_id, TURN_RESERVATION_MICRO_USD, 0, day_key)
        storage.table().update_item(Key={"pk": f"SESSION#{session_id}", "sk": "STATE"}, UpdateExpression="SET runtime_status = :status", ExpressionAttributeValues={":status": "resolution_failed"})
        raise

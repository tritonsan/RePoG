from __future__ import annotations

import base64
import json
import logging
import os
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any

from .security import AuthenticationError, verify
from .service import create_session, resolve_joint_turn, submit_intent
from . import storage
from .forge import quick_forge


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def response(status: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {"statusCode": status, "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"}, "body": json.dumps(payload, default=lambda value: int(value) if isinstance(value, Decimal) else str(value))}


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    if event.get("action") == "resolve_turn":
        return resolve_joint_turn(str(event["session_id"]), str(event["turn_id"]))
    if event.get("action") == "quick_forge":
        reservation = 500_000
        day_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        reserved = False
        try:
            storage.reserve(str(event["session_id"]), reservation, day_key)
            reserved = True
            result = quick_forge(os.environ["REPOG_WORKSPACE_BUCKET"], str(event["session_id"]), str(event.get("forge_prompt", "")))
            storage.settle(str(event["session_id"]), reservation, int(result.pop("_actual_micro_usd")), day_key)
            reserved = False
            manifest = result.pop("_manifest")
            initial_turn = result.pop("_initial_turn")
            turn_session = initial_turn["session"]
            storage.table().update_item(Key={"pk": f"SESSION#{event['session_id']}", "sk": "STATE"}, UpdateExpression="SET runtime_status = :status, manifest = :manifest, turn_brief = :turn, turn_id = :turn_id, turn_number = :turn_number", ExpressionAttributeValues={":status": "ready", ":manifest": manifest, ":turn": initial_turn, ":turn_id": turn_session["turn_id"], ":turn_number": int(turn_session["turn_number"])})
            return result
        except Exception:
            LOGGER.exception("hosted_quick_forge_failed", extra={"session_id": str(event.get("session_id", ""))})
            if reserved:
                storage.settle(str(event["session_id"]), reservation, 0, day_key)
            storage.table().update_item(Key={"pk": f"SESSION#{event['session_id']}", "sk": "STATE"}, UpdateExpression="SET runtime_status = :status", ExpressionAttributeValues={":status": "forge_failed"})
            raise
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "/")
    raw = event.get("body") or ""
    body = base64.b64decode(raw) if event.get("isBase64Encoded") else raw.encode()
    try:
        nonce = verify(os.environ["REPOG_SHARED_SECRET"], event.get("headers", {}), method, path, body)
        storage.claim_nonce(nonce)
        payload = json.loads(body or b"{}")
        if method == "POST" and path == "/runtime/v1/sessions":
            return response(201, create_session(payload))
        parts = path.strip("/").split("/")
        if len(parts) == 4 and parts[:3] == ["runtime", "v1", "sessions"] and method == "GET":
            state = storage.get_session(parts[3])
            return response(200, {"ok": True, "session_id": state["session_id"], "status": state["runtime_status"], "revision": int(state["revision"]), "turn_number": int(state["turn_number"]), "manifest": state["manifest"], "turn": state["turn_brief"], "expires_at": int(state["expires_at"])})
        if len(parts) == 5 and parts[:3] == ["runtime", "v1", "sessions"] and parts[4] == "events" and method == "GET":
            return response(200, {"ok": True, "events": storage.list_events(parts[3])})
        if len(parts) == 5 and parts[:3] == ["runtime", "v1", "sessions"] and method == "POST":
            kind = {"human-intents": "human", "agent-intents": "agent"}.get(parts[4])
            if kind:
                return response(202, submit_intent(parts[3], kind, payload))
        return response(404, {"ok": False, "failure_category": "not_found"})
    except AuthenticationError as exc:
        return response(401, {"ok": False, "failure_category": "unauthorized", "failure_reason": str(exc)})
    except (KeyError, ValueError, RuntimeError) as exc:
        return response(409, {"ok": False, "failure_category": str(exc), "failure_reason": str(exc)})
    except Exception:
        LOGGER.exception("hosted_runtime_request_failed", extra={"method": method, "path": path})
        return response(500, {"ok": False, "failure_category": "runtime_failure", "failure_reason": "The hosted runtime could not complete the request."})

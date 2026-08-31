"""Restart-safe transport between bounded RePoG Agent Seats and a hosted relay.

The optional bridge invokes the Agent Seat CLI for every local operation,
reads only a precompiled Agent Pack, and never resolves fictional outcomes.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from compile_agent_brief import BriefError, compile_state_brief


class BridgeError(Exception):
    pass


RequestFn = Callable[..., dict[str, Any]]


def _json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BridgeError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BridgeError(f"{path} must contain a JSON object")
    return value


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _request(url: str, *, method: str = "GET", token: str = "", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            detail = {"failure_reason": str(exc)}
        raise BridgeError(detail.get("failure_reason") or detail.get("failure_category") or str(exc)) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise BridgeError(str(exc)) from exc
    if not isinstance(result, dict) or result.get("ok") is False:
        raise BridgeError(str(result.get("failure_reason") or result.get("failure_category") or "Relay request failed"))
    return result


def _agent_cli(state_path: str, command: str, *, request: dict[str, Any] | None = None, operation_id: str = "") -> dict[str, Any]:
    argv = [sys.executable, str(Path(__file__).with_name("agent_seat.py")), str(Path(state_path).resolve()), command]
    if request is not None:
        argv.extend(["--input-json", json.dumps(request, ensure_ascii=False)])
    if operation_id:
        argv.extend(["--operation-id", operation_id])
    completed = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=30, check=False)
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise BridgeError(f"Agent Seat CLI returned invalid JSON: {completed.stderr.strip()}") from exc
    if completed.returncode != 0 or result.get("ok") is False:
        raise BridgeError(str(result.get("failure_reason") or result.get("failure_category") or "Agent Seat CLI failed"))
    return result


def _save(path: Path, state: dict[str, Any]) -> None:
    state["updated_at_epoch_ms"] = int(time.time() * 1000)
    _atomic_json(path, state)


def create(args: argparse.Namespace, request_fn: RequestFn = _request) -> dict[str, Any]:
    bootstrap = os.environ.get(args.bootstrap_env, "")
    if not bootstrap:
        raise BridgeError(f"Environment variable {args.bootstrap_env} is required")
    manifest_path, turn_path = Path(args.manifest).resolve(), Path(args.turn).resolve()
    initial_turn = _json_file(turn_path)
    result = request_fn(f"{args.relay_url.rstrip('/')}/api/v1/sessions", method="POST", token=bootstrap, payload={"manifest": _json_file(manifest_path), "initial_turn": initial_turn})
    state = {
        "schema_version": "1.1", "relay_url": args.relay_url.rstrip("/"), "session_id": result["session_id"],
        "bridge_token": result["bridge_token"], "invite_url": result["invite_url"], "expires_at": result["expires_at"],
        "manifest_path": str(manifest_path), "agent_state_path": str(Path(args.agent_state).resolve()) if args.agent_state else "",
        "remote_revision": 0, "active_operation_id": "", "awaiting_advance": False,
        "published_turn_id": str(initial_turn.get("session", {}).get("turn_id", "")),
    }
    _save(Path(args.state), state)
    return {"ok": True, "session_id": state["session_id"], "invite_url": state["invite_url"], "expires_at": state["expires_at"], "state_path": str(Path(args.state).resolve())}


def pull(args: argparse.Namespace, request_fn: RequestFn = _request) -> dict[str, Any]:
    state = _json_file(Path(args.state))
    return request_fn(f"{state['relay_url']}/api/v1/sessions/{state['session_id']}/intents", token=str(state["bridge_token"]))


def resolve(args: argparse.Namespace, request_fn: RequestFn = _request) -> dict[str, Any]:
    state = _json_file(Path(args.state))
    envelope = json.loads(args.input_json)
    if not isinstance(envelope, dict):
        raise BridgeError("--input-json must contain an object")
    if args.next_turn:
        envelope["next_turn"] = _json_file(Path(args.next_turn))
    return request_fn(f"{state['relay_url']}/api/v1/sessions/{state['session_id']}/resolve", method="POST", token=str(state["bridge_token"]), payload=envelope)


def _submit_remote_intent(state: dict[str, Any], remote: dict[str, Any], agent_cli: Callable[..., dict[str, Any]]) -> None:
    intent = remote.get("intent")
    if not isinstance(intent, dict):
        raise BridgeError("Relay intent is invalid")
    local = agent_cli(state["agent_state_path"], "next-turn")
    if local.get("status") not in {"ready", "waiting"} or not isinstance(local.get("beat"), dict):
        raise BridgeError("Local Agent Seat is not accepting an intent")
    beat = local["beat"]
    request = {
        "operation_id": intent.get("operation_id"), "expected_scene_id": beat.get("scene_id"),
        "expected_source_revision": beat.get("source_revision"), "actor_id": intent.get("actor_id"),
        "action_type": intent.get("action_type"), "action": intent.get("action"), "approach": intent.get("approach", ""),
        "speech": intent.get("speech", ""), "targets": intent.get("targets", []), "resource_refs": intent.get("resource_refs", []),
        "knowledge_refs": intent.get("knowledge_refs", []), "requested_effect": intent.get("requested_effect", ""),
        "asserted_outcomes": intent.get("asserted_outcomes", []),
    }
    agent_cli(state["agent_state_path"], "submit-turn", request=request)


def pump_once(state_path: Path, request_fn: RequestFn = _request, agent_cli: Callable[..., dict[str, Any]] = _agent_cli) -> dict[str, Any]:
    """Perform at most one durable bridge transition."""
    state_path = state_path.resolve()
    state = _json_file(state_path)
    for required in ("relay_url", "session_id", "bridge_token", "manifest_path", "agent_state_path"):
        if not state.get(required):
            raise BridgeError(f"Bridge state is missing {required}")
    base = f"{state['relay_url']}/api/v1/sessions/{state['session_id']}"
    remote = request_fn(f"{base}/intents", token=str(state["bridge_token"]))
    state["remote_revision"] = remote.get("session_revision", state.get("remote_revision", 0))
    intents = remote.get("intents", [])
    if not isinstance(intents, list):
        raise BridgeError("Relay intent list is invalid")

    active = str(state.get("active_operation_id", ""))
    if not active and intents:
        first = intents[0]
        if not isinstance(first, dict):
            raise BridgeError("Relay intent entry is invalid")
        active = str(first.get("operation_id", ""))
        if agent_cli(state["agent_state_path"], "turn-status", operation_id=active).get("status") == "not_found":
            _submit_remote_intent(state, first, agent_cli)
        state["active_operation_id"] = active
        _save(state_path, state)
        return {"ok": True, "transition": "intent_submitted", "operation_id": active}

    if active:
        local_status = agent_cli(state["agent_state_path"], "turn-status", operation_id=active)
        resolution = local_status.get("resolution")
        remote_pending = any(isinstance(item, dict) and item.get("operation_id") == active for item in intents)
        if isinstance(resolution, dict) and remote_pending:
            response = request_fn(f"{base}/resolve", method="POST", token=str(state["bridge_token"]), payload={
                "operation_id": active, "expected_session_revision": remote["session_revision"], "outcome": resolution["outcome"],
                "summary": resolution["summary"], "visible_consequences": resolution.get("visible_consequences", []), "next_status": "waiting",
            })
            state.update({"remote_revision": response["session_revision"], "active_operation_id": "", "last_resolved_operation_id": active, "awaiting_advance": True})
            _save(state_path, state)
            return {"ok": True, "transition": "resolution_published", "operation_id": active}
        if isinstance(resolution, dict) and not remote_pending:
            state.update({"active_operation_id": "", "awaiting_advance": True})
            _save(state_path, state)
            return {"ok": True, "transition": "resolution_reconciled", "operation_id": active}
        _save(state_path, state)
        return {"ok": True, "transition": "waiting_for_resolution", "operation_id": active}

    if state.get("awaiting_advance"):
        local = agent_cli(state["agent_state_path"], "next-turn")
        next_status = local.get("status") if local.get("status") in {"ready", "paused", "complete"} else ""
        if next_status:
            payload: dict[str, Any] = {"expected_session_revision": remote["session_revision"], "next_status": next_status}
            turn_id = ""
            if next_status == "ready":
                brief = compile_state_brief(_json_file(Path(state["manifest_path"])), local)
                turn_id = str(brief["session"]["turn_id"])
                if turn_id == state.get("published_turn_id"):
                    return {"ok": True, "transition": "waiting_for_next_beat"}
                payload["next_turn"] = brief
            response = request_fn(f"{base}/advance", method="POST", token=str(state["bridge_token"]), payload=payload)
            state.update({"remote_revision": response["session_revision"], "awaiting_advance": False})
            if turn_id:
                state["published_turn_id"] = turn_id
            _save(state_path, state)
            return {"ok": True, "transition": f"session_{next_status}"}
    _save(state_path, state)
    return {"ok": True, "transition": "idle"}


def watch(args: argparse.Namespace) -> dict[str, Any]:
    interval = max(0.25, min(float(args.interval), 30.0))
    if args.once:
        return pump_once(Path(args.state))
    transitions = 0
    try:
        while True:
            result = pump_once(Path(args.state))
            transitions += int(result.get("transition") not in {"idle", "waiting_for_resolution", "waiting_for_next_beat"})
            time.sleep(interval)
    except KeyboardInterrupt:
        return {"ok": True, "transition": "stopped", "durable_transitions": transitions}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create_parser = commands.add_parser("create")
    create_parser.add_argument("--relay-url", required=True); create_parser.add_argument("--manifest", required=True); create_parser.add_argument("--turn", required=True)
    create_parser.add_argument("--agent-state"); create_parser.add_argument("--state", default="campaign/agent_bridge_state.json"); create_parser.add_argument("--bootstrap-env", default="REPOG_RELAY_BOOTSTRAP_KEY")
    pull_parser = commands.add_parser("pull"); pull_parser.add_argument("--state", default="campaign/agent_bridge_state.json")
    resolve_parser = commands.add_parser("resolve"); resolve_parser.add_argument("--state", default="campaign/agent_bridge_state.json"); resolve_parser.add_argument("--input-json", required=True); resolve_parser.add_argument("--next-turn")
    watch_parser = commands.add_parser("watch"); watch_parser.add_argument("--state", default="campaign/agent_bridge_state.json"); watch_parser.add_argument("--interval", type=float, default=1.0); watch_parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = create(args) if args.command == "create" else pull(args) if args.command == "pull" else resolve(args) if args.command == "resolve" else watch(args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (BridgeError, BriefError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"ok": False, "failure_category": "bridge_error", "failure_reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())

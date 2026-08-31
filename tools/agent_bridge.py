"""Transport bounded Agent Seat envelopes between RePoG and a hosted relay.

This optional adapter is not a narrative engine. It reads only explicitly
compiled Agent Pack/Turn Brief files and the bounded Agent Seat operation
store. It never reads campaign truth or resolves fictional outcomes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class BridgeError(Exception):
    pass


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


def create(args: argparse.Namespace) -> dict[str, Any]:
    bootstrap = os.environ.get(args.bootstrap_env, "")
    if not bootstrap:
        raise BridgeError(f"Environment variable {args.bootstrap_env} is required")
    result = _request(
        f"{args.relay_url.rstrip('/')}/api/v1/sessions",
        method="POST",
        token=bootstrap,
        payload={"manifest": _json_file(Path(args.manifest)), "initial_turn": _json_file(Path(args.turn))},
    )
    state = {
        "schema_version": "1.0",
        "relay_url": args.relay_url.rstrip("/"),
        "session_id": result["session_id"],
        "bridge_token": result["bridge_token"],
        "invite_url": result["invite_url"],
        "expires_at": result["expires_at"],
    }
    _atomic_json(Path(args.state), state)
    return {"ok": True, "session_id": state["session_id"], "invite_url": state["invite_url"], "expires_at": state["expires_at"], "state_path": str(Path(args.state).resolve())}


def pull(args: argparse.Namespace) -> dict[str, Any]:
    state = _json_file(Path(args.state))
    return _request(f"{state['relay_url']}/api/v1/sessions/{state['session_id']}/intents", token=str(state["bridge_token"]))


def resolve(args: argparse.Namespace) -> dict[str, Any]:
    state = _json_file(Path(args.state))
    envelope = json.loads(args.input_json)
    if not isinstance(envelope, dict):
        raise BridgeError("--input-json must contain an object")
    if args.next_turn:
        envelope["next_turn"] = _json_file(Path(args.next_turn))
    return _request(f"{state['relay_url']}/api/v1/sessions/{state['session_id']}/resolve", method="POST", token=str(state["bridge_token"]), payload=envelope)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create_parser = commands.add_parser("create")
    create_parser.add_argument("--relay-url", required=True)
    create_parser.add_argument("--manifest", required=True)
    create_parser.add_argument("--turn", required=True)
    create_parser.add_argument("--state", default="campaign/agent_bridge_state.json")
    create_parser.add_argument("--bootstrap-env", default="REPOG_RELAY_BOOTSTRAP_KEY")
    pull_parser = commands.add_parser("pull")
    pull_parser.add_argument("--state", default="campaign/agent_bridge_state.json")
    resolve_parser = commands.add_parser("resolve")
    resolve_parser.add_argument("--state", default="campaign/agent_bridge_state.json")
    resolve_parser.add_argument("--input-json", required=True)
    resolve_parser.add_argument("--next-turn")
    args = parser.parse_args(argv)
    try:
        result = create(args) if args.command == "create" else pull(args) if args.command == "pull" else resolve(args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (BridgeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "failure_category": "bridge_error", "failure_reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())

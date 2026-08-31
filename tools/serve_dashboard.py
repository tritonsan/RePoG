"""Serve a validated RePoG dashboard on loopback with safe HTTP headers."""

from __future__ import annotations

import argparse
import functools
import json
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from agent_seat import AgentSeatError, check_state as check_agent_seat, get_context, get_next_turn, get_turn_status, set_session_status, submit_turn
from check_dashboard import check_dashboard
from check_world_voices import validate_projection_file


SECURITY_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Origin-Agent-Cluster": "?1",
    "Permissions-Policy": "tools=(self)",
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; "
        "base-uri 'none'; frame-ancestors 'none'"
    ),
}


class DashboardHandler(SimpleHTTPRequestHandler):
    server_version = "RePoGTable/1"

    def _json_response(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _host_is_local(self) -> bool:
        host = self.headers.get("Host", "").lower()
        name = host.rsplit(":", 1)[0] if ":" in host else host
        return name in {"127.0.0.1", "localhost"}

    def _seat_state_path(self) -> Path:
        return Path(self.directory).parent / "agent_seat_state.json"

    def _agent_seat_error(self, exc: AgentSeatError) -> None:
        status = HTTPStatus.CONFLICT if exc.exit_code == 3 else HTTPStatus.BAD_REQUEST
        if exc.category == "update_busy":
            status = HTTPStatus.SERVICE_UNAVAILABLE
        self._json_response(status, {"ok": False, "failure_category": exc.category, "failure_reason": str(exc)})

    def end_headers(self) -> None:
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        super().end_headers()

    def list_directory(self, path: str):  # type: ignore[override]
        self.send_error(HTTPStatus.NOT_FOUND, "Directory listing is disabled")
        return None

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if not self._host_is_local():
            self._json_response(HTTPStatus.BAD_REQUEST, {"ok": False, "failure_category": "host_invalid", "failure_reason": "Host is not allowed."})
            return
        request = urlsplit(self.path)
        request_path = request.path
        if request_path == "/api/seat/context":
            try:
                self._json_response(HTTPStatus.OK, get_context(self._seat_state_path()))
            except AgentSeatError as exc:
                self._agent_seat_error(exc)
            return
        if request_path == "/api/seat/next-turn":
            raw_revision = parse_qs(request.query).get("after_revision", [""])[0]
            try:
                after_revision = int(raw_revision) if raw_revision else None
                self._json_response(HTTPStatus.OK, get_next_turn(self._seat_state_path(), after_revision))
            except (AgentSeatError, ValueError) as exc:
                if isinstance(exc, AgentSeatError):
                    self._agent_seat_error(exc)
                else:
                    self._json_response(HTTPStatus.BAD_REQUEST, {"ok": False, "failure_category": "input_invalid", "failure_reason": "after_revision must be an integer."})
            return
        if request_path == "/api/seat/turn-status":
            operation_id = parse_qs(request.query).get("operation_id", [""])[0]
            try:
                self._json_response(HTTPStatus.OK, get_turn_status(self._seat_state_path(), operation_id))
            except AgentSeatError as exc:
                self._agent_seat_error(exc)
            return
        if request_path.endswith("/dashboard_state.json") or request_path == "/dashboard_state.json":
            state_path = Path(self.directory) / "dashboard_state.json"
            result = check_dashboard(state_path, campaign_path=Path(self.directory).parent)
            if not result["ok"]:
                body = json.dumps(
                    {
                        "ok": False,
                        "message": "Dashboard state did not pass validation.",
                        "error_count": result["error_count"],
                    }
                ).encode("utf-8")
                self.send_response(HTTPStatus.SERVICE_UNAVAILABLE)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        if request_path.startswith("/assets/world_voices/") and request_path.endswith(".json"):
            relative = request_path.lstrip("/")
            result = validate_projection_file(Path(self.directory).parent, relative)
            if not result["ok"]:
                body = json.dumps({"ok": False, "message": "Player document projection did not pass validation.", "error_count": result["error_count"]}).encode("utf-8")
                self.send_response(HTTPStatus.SERVICE_UNAVAILABLE)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if not self._host_is_local():
            self._json_response(HTTPStatus.BAD_REQUEST, {"ok": False, "failure_category": "host_invalid", "failure_reason": "Host is not allowed."})
            return
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin", "")
        if origin != f"http://{host}":
            self._json_response(HTTPStatus.FORBIDDEN, {"ok": False, "failure_category": "origin_invalid", "failure_reason": "A same-origin browser request is required."})
            return
        request_path = urlsplit(self.path).path
        if request_path not in {"/api/seat/turn", "/api/seat/pause", "/api/seat/resume", "/api/seat/complete"}:
            self._json_response(HTTPStatus.NOT_FOUND, {"ok": False, "failure_category": "route_missing", "failure_reason": "API route not found."})
            return
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            self._json_response(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"ok": False, "failure_category": "content_type_invalid", "failure_reason": "Content-Type must be application/json."})
            return
        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._json_response(HTTPStatus.LENGTH_REQUIRED, {"ok": False, "failure_category": "length_required", "failure_reason": "A valid Content-Length is required."})
            return
        if content_length < 2 or content_length > 16_384:
            self._json_response(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"ok": False, "failure_category": "body_size_invalid", "failure_reason": "Request body must be between 2 and 16384 bytes."})
            return
        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json_response(HTTPStatus.BAD_REQUEST, {"ok": False, "failure_category": "json_invalid", "failure_reason": "Request body must be valid UTF-8 JSON."})
            return
        try:
            if request_path == "/api/seat/turn":
                result = submit_turn(self._seat_state_path(), payload)
            else:
                target = {"/api/seat/pause": "paused", "/api/seat/resume": "active", "/api/seat/complete": "complete"}[request_path]
                result = set_session_status(self._seat_state_path(), payload, target)
            self._json_response(HTTPStatus.OK, result)
        except AgentSeatError as exc:
            self._agent_seat_error(exc)

    def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib handler API
        self._json_response(HTTPStatus.METHOD_NOT_ALLOWED, {"ok": False, "failure_category": "method_not_allowed", "failure_reason": "Cross-origin requests are not supported."})

    def log_message(self, format: str, *args) -> None:
        sys.stderr.write(f"[dashboard] {self.address_string()} - {format % args}\n")


def validate_directory(directory: Path) -> dict:
    directory = directory.resolve()
    index_path = directory / "index.html"
    state_path = directory / "dashboard_state.json"
    if not index_path.is_file():
        return {"ok": False, "failure_category": "index_missing", "failure_reason": f"Missing {index_path}"}
    result = check_dashboard(state_path, campaign_path=directory.parent)
    if not result["ok"]:
        return {
            "ok": False,
            "failure_category": "dashboard_validation_failed",
            "failure_reason": "Dashboard state has validation errors.",
            "validation": result,
        }
    agent_seat = check_agent_seat(directory.parent / "agent_seat_state.json")
    if not agent_seat["ok"]:
        return {
            "ok": False,
            "failure_category": "agent_seat_validation_failed",
            "failure_reason": agent_seat["failure_reason"],
            "validation": agent_seat,
        }
    return {"ok": True, "directory": str(directory), "validation": result, "agent_seat": agent_seat}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="campaign/dashboard", help="Dashboard directory.")
    parser.add_argument("--port", type=int, default=8787, help="Loopback port (default: 8787).")
    parser.add_argument("--check-only", action="store_true", help="Validate without starting the server.")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        print(json.dumps({"ok": False, "failure_category": "port_invalid", "failure_reason": "Port must be from 1 to 65535."}, indent=2))
        return 2
    directory = Path(args.directory).resolve()
    result = validate_directory(directory)
    if not result["ok"] or args.check_only:
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0 if result["ok"] else 2

    handler = functools.partial(DashboardHandler, directory=str(directory))
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    except OSError as exc:
        print(json.dumps({"ok": False, "failure_category": "bind_failed", "failure_reason": str(exc)}, indent=2))
        return 2
    print(json.dumps({"ok": True, "url": f"http://127.0.0.1:{args.port}/", "directory": str(directory)}, ensure_ascii=True), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

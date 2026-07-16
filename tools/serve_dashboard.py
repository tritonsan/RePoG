"""Serve a validated RePoG dashboard on loopback with safe HTTP headers."""

from __future__ import annotations

import argparse
import functools
import json
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from check_dashboard import check_dashboard


SECURITY_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; "
        "base-uri 'none'; frame-ancestors 'none'"
    ),
}


class DashboardHandler(SimpleHTTPRequestHandler):
    server_version = "RePoGDashboard/3"

    def end_headers(self) -> None:
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        super().end_headers()

    def list_directory(self, path: str):  # type: ignore[override]
        self.send_error(HTTPStatus.NOT_FOUND, "Directory listing is disabled")
        return None

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        request_path = urlsplit(self.path).path
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
        super().do_GET()

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
    return {"ok": True, "directory": str(directory), "validation": result}


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

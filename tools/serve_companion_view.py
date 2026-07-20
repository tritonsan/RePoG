"""Serve the validated Companion View on loopback with a strict allowlist."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from check_companion_view import check_companion_view


SECURITY_HEADERS = {
    "Cache-Control": "no-cache, max-age=0, must-revalidate",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Content-Security-Policy": (
        "default-src 'none'; img-src 'self'; style-src 'self'; script-src 'self'; "
        "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    ),
}
STATIC_ALLOWLIST = {
    "/": "index.html",
    "/index.html": "index.html",
    "/app.js": "app.js",
    "/style.css": "style.css",
    "/companion_view_state.json": "companion_view_state.json",
}


def _stat_key(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return stat.st_mtime_ns, stat.st_size


class ValidationCache:
    """Revalidate only when the projection or protected-name source changes."""

    def __init__(self, view: Path) -> None:
        self.view = view.resolve()
        self.campaign = self.view.parent.resolve()
        self.state = self.view / "companion_view_state.json"
        self.knowledge = self.campaign / "knowledge_boundaries.md"
        self._key: tuple[Any, ...] | None = None
        self._result: dict[str, Any] | None = None
        self._portrait: str | None = None

    def validate(self) -> tuple[dict[str, Any], str | None]:
        portrait_stat = _stat_key(self.view / self._portrait) if self._portrait else None
        static_stats = tuple(_stat_key(self.view / name) for name in ("index.html", "app.js", "style.css"))
        key = (_stat_key(self.state), _stat_key(self.knowledge), self._portrait, portrait_stat, static_stats)
        if key == self._key and self._result is not None:
            return self._result, self._portrait
        result = check_companion_view(self.state, campaign_path=self.campaign, require_assets=True)
        portrait: str | None = None
        if result["ok"]:
            try:
                data = json.loads(self.state.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                result = {
                    "ok": False,
                    "error_count": 1,
                    "warning_count": 0,
                    "findings": [],
                }
            else:
                portrait_data = data.get("portrait")
                if isinstance(portrait_data, dict) and isinstance(portrait_data.get("asset"), str):
                    portrait = portrait_data["asset"].replace("\\", "/")
        self._key = key
        self._result = result
        self._portrait = portrait
        return result, portrait


class CompanionViewHandler(BaseHTTPRequestHandler):
    server_version = "RePoGCompanionView/1"

    @property
    def view(self) -> Path:
        return self.server.view  # type: ignore[attr-defined]

    @property
    def validation_cache(self) -> ValidationCache:
        return self.server.validation_cache  # type: ignore[attr-defined]

    def _security_headers(self) -> None:
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)

    def _error(self, status: HTTPStatus, message: str) -> None:
        body = json.dumps({"ok": False, "message": message}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _request_path(self) -> str | None:
        try:
            path = unquote(urlsplit(self.path).path, errors="strict")
        except (UnicodeError, ValueError):
            return None
        if "\\" in path or "\x00" in path or "//" in path:
            return None
        if any(part in {".", ".."} for part in Path(path).parts):
            return None
        return path

    def _allowed_file(self, request_path: str) -> Path | None:
        relative = STATIC_ALLOWLIST.get(request_path)
        if relative is None:
            result, portrait = self.validation_cache.validate()
            if not result["ok"] or portrait is None or request_path != f"/{portrait}":
                return None
            relative = portrait
        candidate = self.view / Path(relative)
        if candidate.is_symlink() or any(parent.is_symlink() for parent in candidate.parents if parent != self.view.parent):
            return None
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.view)
        except ValueError:
            return None
        return resolved if resolved.is_file() else None

    def _serve(self) -> None:
        request_path = self._request_path()
        if request_path is None:
            self._error(HTTPStatus.BAD_REQUEST, "Invalid request path.")
            return
        if request_path == "/companion_view_state.json" or request_path.startswith("/assets/"):
            result, _ = self.validation_cache.validate()
            if not result["ok"]:
                self._error(HTTPStatus.SERVICE_UNAVAILABLE, "Companion View state did not pass validation.")
                return
        path = self._allowed_file(request_path)
        if path is None:
            self._error(HTTPStatus.NOT_FOUND, "Not found.")
            return
        stat = path.stat()
        tag_source = f"{path.name}:{stat.st_mtime_ns}:{stat.st_size}".encode("utf-8")
        etag = f'"{hashlib.sha256(tag_source).hexdigest()[:24]}"'
        if self.headers.get("If-None-Match", "").strip() == etag:
            self.send_response(HTTPStatus.NOT_MODIFIED)
            self.send_header("ETag", etag)
            self._security_headers()
            self.end_headers()
            return
        try:
            body = path.read_bytes()
        except OSError:
            self._error(HTTPStatus.NOT_FOUND, "Not found.")
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if path.suffix.casefold() == ".json":
            content_type = "application/json"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith(("text/", "application/json", "application/javascript")) else content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("ETag", etag)
        self._security_headers()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        self._serve()

    def do_HEAD(self) -> None:  # noqa: N802 - stdlib handler API
        self._serve()

    def do_POST(self) -> None:  # noqa: N802 - explicit read-only surface
        self._error(HTTPStatus.METHOD_NOT_ALLOWED, "Companion View is read-only.")

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write(f"[companion-view] {self.address_string()} - {format % args}\n")


class CompanionViewServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], view: Path) -> None:
        self.view = view.resolve()
        self.validation_cache = ValidationCache(self.view)
        super().__init__(address, CompanionViewHandler)


def validate_directory(view: Path) -> dict[str, Any]:
    view = view.resolve()
    state = view / "companion_view_state.json"
    result = check_companion_view(state, campaign_path=view.parent, require_assets=True)
    if not result["ok"]:
        return {
            "ok": False,
            "failure_category": "companion_view_validation_failed",
            "failure_reason": "Companion View has validation errors.",
            "validation": result,
        }
    return {"ok": True, "directory": str(view), "validation": result}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="campaign/companion_view")
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        print(json.dumps({"ok": False, "failure_category": "port_invalid", "failure_reason": "Port must be from 1 to 65535."}, indent=2))
        return 2
    view = Path(args.directory).resolve()
    result = validate_directory(view)
    if args.check_only or not result["ok"]:
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0 if result["ok"] else 2
    try:
        server = CompanionViewServer(("127.0.0.1", args.port), view)
    except OSError as exc:
        print(json.dumps({"ok": False, "failure_category": "bind_failed", "failure_reason": str(exc)}, indent=2))
        return 2
    print(json.dumps({"ok": True, "url": f"http://127.0.0.1:{args.port}/", "directory": str(view)}, ensure_ascii=True), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

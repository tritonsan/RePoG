"""Apply a small, revision-guarded, atomic patch to a Dashboard V3 state."""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from check_dashboard import check_dashboard_data


class DashboardUpdateError(Exception):
    def __init__(self, category: str, message: str, *, exit_code: int = 2) -> None:
        super().__init__(message)
        self.category = category
        self.exit_code = exit_code


def _positive_revision(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise DashboardUpdateError("input_invalid", f"{name} must be a non-negative integer.")
    return value


def _atomic_write(path: Path, data: dict) -> None:
    payload = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def apply_dashboard_patch(state_path: Path, request: dict) -> dict:
    state_path = state_path.resolve()
    if not state_path.is_file():
        raise DashboardUpdateError("state_missing", f"Dashboard state does not exist: {state_path}")
    if not isinstance(request, dict):
        raise DashboardUpdateError("input_invalid", "Patch request must be a JSON object.")

    lock_path = state_path.with_name(f".{state_path.name}.lock")
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise DashboardUpdateError("update_busy", "Another dashboard update is in progress.", exit_code=4) from exc

    try:
        try:
            current = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DashboardUpdateError("state_invalid", str(exc)) from exc
        if current.get("dashboard_version") != 3:
            raise DashboardUpdateError("version_unsupported", "Atomic tile patches require Dashboard V3.")
        current_validation = check_dashboard_data(current, state_path, require_assets=True)
        if not current_validation["ok"]:
            raise DashboardUpdateError("state_invalid", json.dumps(current_validation["findings"], ensure_ascii=False))

        actual_revision = _positive_revision(current.get("dashboard_revision"), "current dashboard_revision")
        expected_revision = _positive_revision(request.get("expected_revision"), "expected_revision")
        if actual_revision != expected_revision:
            raise DashboardUpdateError(
                "revision_conflict",
                f"Expected dashboard revision {expected_revision}, found {actual_revision}.",
                exit_code=3,
            )
        source_revision = request.get("source_revision", current.get("source_revision"))
        source_revision = _positive_revision(source_revision, "source_revision")
        if source_revision < current.get("source_revision", 0):
            raise DashboardUpdateError("revision_invalid", "source_revision cannot move backwards.")

        candidate = copy.deepcopy(current)
        for key in ("campaign", "theme", "scene_id", "refresh", "refresh_interval_ms"):
            if key in request:
                candidate[key] = copy.deepcopy(request[key])

        operations = request.get("operations", [])
        if not isinstance(operations, list):
            raise DashboardUpdateError("input_invalid", "operations must be a list.")
        tiles = list(candidate.get("tiles", []))
        by_id = {tile.get("id"): index for index, tile in enumerate(tiles) if isinstance(tile, dict)}
        changed_ids: list[str] = []
        for index, operation in enumerate(operations):
            if not isinstance(operation, dict):
                raise DashboardUpdateError("input_invalid", f"operations[{index}] must be an object.")
            action = operation.get("op")
            if action == "upsert":
                tile = operation.get("tile")
                if not isinstance(tile, dict) or not isinstance(tile.get("id"), str) or not tile["id"].strip():
                    raise DashboardUpdateError("input_invalid", f"operations[{index}].tile needs a non-empty id.")
                tile_id = tile["id"]
                if tile_id in by_id:
                    tiles[by_id[tile_id]] = copy.deepcopy(tile)
                else:
                    by_id[tile_id] = len(tiles)
                    tiles.append(copy.deepcopy(tile))
                changed_ids.append(tile_id)
            elif action == "remove":
                tile_id = operation.get("id")
                if not isinstance(tile_id, str) or not tile_id.strip():
                    raise DashboardUpdateError("input_invalid", f"operations[{index}].id must be non-empty text.")
                tiles = [tile for tile in tiles if not isinstance(tile, dict) or tile.get("id") != tile_id]
                by_id = {tile.get("id"): pos for pos, tile in enumerate(tiles) if isinstance(tile, dict)}
                changed_ids.append(tile_id)
            else:
                raise DashboardUpdateError("input_invalid", f"Unsupported tile operation: {action!r}.")

        candidate["tiles"] = tiles
        candidate["dashboard_revision"] = actual_revision + 1
        candidate["source_revision"] = source_revision
        candidate["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        validation = check_dashboard_data(candidate, state_path, require_assets=True)
        if not validation["ok"]:
            raise DashboardUpdateError("validation_failed", json.dumps(validation["findings"], ensure_ascii=False))
        _atomic_write(state_path, candidate)
        return {
            "ok": True,
            "dashboard_path": str(state_path),
            "previous_revision": actual_revision,
            "dashboard_revision": actual_revision + 1,
            "source_revision": source_revision,
            "changed_tile_ids": changed_ids,
            "warning_count": validation["warning_count"],
            "warnings": [item for item in validation["findings"] if item["severity"] == "warning"],
        }
    finally:
        try:
            os.close(lock_fd)
        finally:
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def _load_request(args: argparse.Namespace) -> dict:
    if args.input_json:
        try:
            value = json.loads(args.input_json)
        except json.JSONDecodeError as exc:
            raise DashboardUpdateError("input_invalid", f"Invalid --input-json: {exc}") from exc
    elif args.input_file:
        try:
            value = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DashboardUpdateError("input_invalid", f"Cannot read --input-file: {exc}") from exc
    else:
        try:
            value = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            raise DashboardUpdateError("input_invalid", f"Invalid JSON on stdin: {exc}") from exc
    if not isinstance(value, dict):
        raise DashboardUpdateError("input_invalid", "Patch request must be a JSON object.")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dashboard_state", help="Path to dashboard_state.json.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input-json", help="Patch request as JSON.")
    source.add_argument("--input-file", help="Path to a JSON patch request.")
    args = parser.parse_args(argv)
    try:
        result = apply_dashboard_patch(Path(args.dashboard_state), _load_request(args))
    except DashboardUpdateError as exc:
        print(json.dumps({"ok": False, "failure_category": exc.category, "failure_reason": str(exc)}, indent=2))
        return exc.exit_code
    except OSError as exc:
        print(json.dumps({"ok": False, "failure_category": "write_failed", "failure_reason": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

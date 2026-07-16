"""Manage one resumable visual draft transaction for a RePoG campaign."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from check_dashboard import check_dashboard_data


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")


class VisualError(Exception):
    def __init__(self, category: str, message: str, *, exit_code: int = 2) -> None:
        super().__init__(message)
        self.category = category
        self.exit_code = exit_code


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualError("state_invalid", f"Cannot read {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualError("state_invalid", f"{path.name} must contain a JSON object.")
    return value


def _validate_state(state: dict) -> None:
    if state.get("schema_version") != 1:
        raise VisualError("state_invalid", "visual_state.json schema_version must be 1.")
    revision = state.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise VisualError("state_invalid", "visual_state.json revision must be a non-negative integer.")
    if state.get("pending") is not None and not isinstance(state.get("pending"), dict):
        raise VisualError("state_invalid", "visual_state.json pending must be an object or null.")
    if not isinstance(state.get("history"), list):
        raise VisualError("state_invalid", "visual_state.json history must be a list.")


def _campaign_file(root: Path, value: str, *, must_exist: bool = False) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise VisualError("input_invalid", "A campaign-relative path is required.")
    candidate = (root / value).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise VisualError("path_forbidden", "Path must stay inside the campaign folder.") from exc
    if must_exist and not candidate.is_file():
        raise VisualError("file_missing", f"File does not exist: {value}")
    return candidate


def _required(payload: dict, name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip():
        raise VisualError("input_invalid", f"{name} must be non-empty text.")
    return value.strip()


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def _json_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _commit_with_rollback(changes: dict[Path, bytes]) -> None:
    snapshots: dict[Path, bytes | None] = {}
    written: list[Path] = []
    try:
        for path, payload in changes.items():
            snapshots[path] = path.read_bytes() if path.exists() else None
            _atomic_bytes(path, payload)
            written.append(path)
    except Exception as exc:
        rollback_errors: list[str] = []
        for path in reversed(written):
            try:
                original = snapshots[path]
                if original is None:
                    path.unlink(missing_ok=True)
                else:
                    _atomic_bytes(path, original)
            except Exception as rollback_exc:  # pragma: no cover - exceptional filesystem failure
                rollback_errors.append(f"{path}: {rollback_exc}")
        detail = f"; rollback errors: {'; '.join(rollback_errors)}" if rollback_errors else ""
        raise VisualError("accept_failed_rolled_back", f"Visual acceptance failed and was rolled back: {exc}{detail}") from exc


def _state_paths(root: Path) -> tuple[Path, Path, Path]:
    state_path = root / "visual_state.json"
    gallery_path = root / "visual_gallery.md"
    dashboard_path = root / "dashboard" / "dashboard_state.json"
    for path in (state_path, gallery_path, dashboard_path):
        if not path.is_file():
            raise VisualError("file_missing", f"Required campaign file is missing: {path.relative_to(root)}")
    return state_path, gallery_path, dashboard_path


def _pending(state: dict, transaction_id: str) -> dict:
    pending = state.get("pending")
    if not isinstance(pending, dict):
        raise VisualError("no_pending_visual", "There is no visual awaiting review.", exit_code=3)
    if pending.get("transaction_id") != transaction_id:
        raise VisualError("transaction_conflict", "The transaction id does not match the pending visual.", exit_code=3)
    return pending


def _write_state(state_path: Path, state: dict) -> None:
    _validate_state(state)
    _atomic_bytes(state_path, _json_bytes(state))


def begin(root: Path, payload: dict) -> dict:
    state_path, _, _ = _state_paths(root)
    state = _load_json(state_path)
    _validate_state(state)
    if state.get("pending") is not None:
        raise VisualError("visual_already_pending", "Finish or cancel the current visual before starting another.", exit_code=3)
    transaction_id = payload.get("transaction_id") or f"visual-{uuid.uuid4().hex[:12]}"
    if not isinstance(transaction_id, str) or not SAFE_ID.fullmatch(transaction_id):
        raise VisualError("input_invalid", "transaction_id must be a short lowercase id.")
    placement_requested = payload.get("dashboard_placement_requested", False)
    if not isinstance(placement_requested, bool):
        raise VisualError("input_invalid", "dashboard_placement_requested must be true or false.")
    pending = {
        "transaction_id": transaction_id,
        "status": "begun",
        "target": _required(payload, "target"),
        "draft_path": "",
        "previous_drafts": [],
        "interrupted_context": _required(payload, "interrupted_context"),
        "last_meaningful_beat": _required(payload, "last_meaningful_beat"),
        "return_anchor": _required(payload, "return_anchor"),
        "next_step": _required(payload, "next_step"),
        "dashboard_placement_requested": placement_requested,
        "dashboard_tile_id": str(payload.get("dashboard_tile_id", "gallery")).strip() or "gallery",
        "appearance_file": str(payload.get("appearance_file", "appearance_guide.md")).strip() or "appearance_guide.md",
        "revision_instructions": "",
        "revision_count": 0,
        "started_at": _utc_now(),
    }
    if not SAFE_ID.fullmatch(pending["dashboard_tile_id"]):
        raise VisualError("input_invalid", "dashboard_tile_id must be a short lowercase id.")
    appearance_path = _campaign_file(root, pending["appearance_file"], must_exist=True)
    if appearance_path.suffix.lower() != ".md":
        raise VisualError("input_invalid", "appearance_file must be a campaign Markdown note.")
    state["pending"] = pending
    state["revision"] += 1
    _write_state(state_path, state)
    return {
        "ok": True,
        "action": "begin",
        "transaction_id": transaction_id,
        "player_instruction": "The next result may contain only the image. Reply with acceptance or the changes you want.",
        "resume_after_review": {"return_anchor": pending["return_anchor"], "next_step": pending["next_step"]},
    }


def attach(root: Path, payload: dict) -> dict:
    state_path, _, _ = _state_paths(root)
    state = _load_json(state_path)
    _validate_state(state)
    transaction_id = _required(payload, "transaction_id")
    pending = _pending(state, transaction_id)
    draft_value = _required(payload, "draft_path").replace("\\", "/")
    draft = _campaign_file(root, draft_value, must_exist=True)
    if draft.suffix.lower() not in IMAGE_SUFFIXES:
        raise VisualError("input_invalid", "Draft must be a PNG, JPEG, WebP, or GIF image.")
    try:
        draft.relative_to((root / "visuals").resolve())
    except ValueError as exc:
        raise VisualError("path_forbidden", "Drafts must be stored under campaign/visuals before attachment.") from exc
    pending["draft_path"] = draft.relative_to(root).as_posix()
    pending["status"] = "attached"
    pending["attached_at"] = _utc_now()
    state["revision"] += 1
    _write_state(state_path, state)
    return {"ok": True, "action": "attach", "transaction_id": transaction_id, "status": "awaiting_player_review"}


def revise(root: Path, payload: dict) -> dict:
    state_path, _, _ = _state_paths(root)
    state = _load_json(state_path)
    _validate_state(state)
    transaction_id = _required(payload, "transaction_id")
    pending = _pending(state, transaction_id)
    if pending.get("status") != "attached" or not pending.get("draft_path"):
        raise VisualError("draft_not_attached", "Attach a draft before requesting a revision.", exit_code=3)
    instructions = _required(payload, "instructions")
    if pending.get("draft_path"):
        pending.setdefault("previous_drafts", []).append(pending["draft_path"])
    pending["draft_path"] = ""
    pending["revision_instructions"] = instructions
    pending["revision_count"] = int(pending.get("revision_count", 0)) + 1
    pending["status"] = "revision_requested"
    state["revision"] += 1
    _write_state(state_path, state)
    return {
        "ok": True,
        "action": "revise",
        "transaction_id": transaction_id,
        "revision_count": pending["revision_count"],
        "resume_after_review": {"return_anchor": pending["return_anchor"], "next_step": pending["next_step"]},
    }


def _clean_table(value: str) -> str:
    return " ".join(value.replace("|", "/").replace("`", "'").split())


def _gallery_text(existing: str, payload: dict, asset_path: str) -> str:
    name = _clean_table(_required(payload, "name"))
    visual_type = _clean_table(str(payload.get("visual_type", "visual")))
    linked = _clean_table(str(payload.get("linked_element", ""))) or "campaign element"
    prompt = _clean_table(str(payload.get("prompt_summary", ""))) or "accepted draft"
    notes = _clean_table(str(payload.get("canon_notes", ""))) or "accepted as shown"
    shown = _clean_table(str(payload.get("last_shown", "accepted now")))
    row = f"- `{name} | {visual_type} | accepted | {asset_path} | {linked} | {prompt} | {notes} | {shown}`"
    marker = "## Accepted Visual Canon"
    if marker in existing:
        before, after = existing.split(marker, 1)
        return before.rstrip() + "\n\n" + row + "\n\n" + marker + after
    return existing.rstrip() + "\n\n" + row + "\n"


def _appearance_text(existing: str, payload: dict, pending: dict, asset_path: str) -> str:
    name = _required(payload, "name")
    notes = str(payload.get("canon_notes", "")).strip() or "Accepted as shown; written campaign facts remain authoritative."
    linked = str(payload.get("linked_element", "")).strip() or pending["target"]
    return (
        existing.rstrip()
        + f"\n\n## Accepted Visual: {name}\n\n"
        + f"- Linked element: {linked}\n"
        + f"- Accepted asset: {asset_path}\n"
        + f"- Canon appearance notes: {notes}\n"
    )


def _dashboard_with_visual(dashboard: dict, pending: dict, payload: dict, asset_path: str) -> dict:
    candidate = copy.deepcopy(dashboard)
    if candidate.get("dashboard_version") != 3:
        raise VisualError("dashboard_version_unsupported", "Visual placement requires Dashboard V3.")
    tile_id = pending["dashboard_tile_id"]
    tiles = candidate.get("tiles")
    if not isinstance(tiles, list):
        raise VisualError("dashboard_invalid", "Dashboard tiles are missing.")
    gallery = next((tile for tile in tiles if isinstance(tile, dict) and tile.get("id") == tile_id), None)
    if gallery is None:
        gallery = {"id": tile_id, "type": "gallery", "title": "Accepted Visuals", "order": 90, "data": {"items": []}}
        tiles.append(gallery)
    if gallery.get("type") != "gallery" or not isinstance(gallery.get("data"), dict):
        raise VisualError("dashboard_invalid", "Requested dashboard placement tile is not a gallery tile.")
    items = gallery["data"].setdefault("items", [])
    if not isinstance(items, list):
        raise VisualError("dashboard_invalid", "Gallery tile items must be a list.")
    items.append(
        {
            "name": _required(payload, "name"),
            "type": str(payload.get("visual_type", "visual")),
            "status": "accepted",
            "image": asset_path,
            "summary": str(payload.get("canon_notes", "")).strip(),
        }
    )
    candidate["dashboard_revision"] = int(candidate.get("dashboard_revision", 0)) + 1
    candidate["updated_at"] = _utc_now()
    candidate["refresh"] = {"status": "current", "reason": "Accepted visual added"}
    return candidate


def accept(root: Path, payload: dict) -> dict:
    state_path, gallery_path, dashboard_path = _state_paths(root)
    state = _load_json(state_path)
    _validate_state(state)
    transaction_id = _required(payload, "transaction_id")
    pending = _pending(state, transaction_id)
    if pending.get("status") != "attached" or not pending.get("draft_path"):
        raise VisualError("draft_not_attached", "Attach a generated draft before accepting it.", exit_code=3)
    draft = _campaign_file(root, pending["draft_path"], must_exist=True)
    destination_value = _required(payload, "destination").replace("\\", "/")
    destination_parts = Path(destination_value).parts
    if not destination_value.startswith("assets/") or ".." in destination_parts or any(part.lower() in {"_drafts", "drafts"} for part in destination_parts):
        raise VisualError("input_invalid", "destination must be a safe assets/... path.")
    destination = _campaign_file(root / "dashboard", destination_value)
    if destination.suffix.lower() not in IMAGE_SUFFIXES:
        raise VisualError("input_invalid", "Accepted visual must be a PNG, JPEG, WebP, or GIF image.")
    if destination.exists():
        raise VisualError("asset_exists", "Destination already exists; choose a versioned asset name.", exit_code=3)

    campaign_destination_value = str(payload.get("campaign_destination", "")).strip().replace("\\", "/")
    if not campaign_destination_value:
        visual_type = str(payload.get("visual_type", "visual")).strip().lower()
        folder = {
            "npc": "characters",
            "character": "characters",
            "companion": "characters",
            "place": "places",
            "location": "places",
            "faction": "factions",
            "item": "items",
            "scene": "scenes",
        }.get(visual_type, "scenes")
        campaign_destination_value = f"visuals/{folder}/{Path(destination_value).name}"
    campaign_parts = Path(campaign_destination_value).parts
    if (
        not campaign_destination_value.startswith("visuals/")
        or ".." in campaign_parts
        or any(part.lower() in {"_drafts", "drafts"} for part in campaign_parts)
    ):
        raise VisualError("input_invalid", "campaign_destination must be a safe accepted visuals/... path.")
    campaign_destination = _campaign_file(root, campaign_destination_value)
    if campaign_destination.suffix.lower() not in IMAGE_SUFFIXES:
        raise VisualError("input_invalid", "Campaign visual must be a PNG, JPEG, WebP, or GIF image.")
    if campaign_destination.exists():
        raise VisualError("asset_exists", "Campaign visual destination already exists; choose a versioned name.", exit_code=3)

    appearance_value = str(payload.get("appearance_file", pending["appearance_file"])).strip()
    appearance_path = _campaign_file(root, appearance_value, must_exist=True)
    if appearance_path.suffix.lower() != ".md":
        raise VisualError("input_invalid", "appearance_file must be a campaign Markdown note.")
    if appearance_path == gallery_path:
        raise VisualError("input_invalid", "appearance_file must be separate from visual_gallery.md.")
    gallery_candidate = _gallery_text(
        gallery_path.read_text(encoding="utf-8"), payload, campaign_destination_value
    )
    appearance_candidate = _appearance_text(
        appearance_path.read_text(encoding="utf-8"), payload, pending, campaign_destination_value
    )

    changes: dict[Path, bytes] = {
        destination: draft.read_bytes(),
        campaign_destination: draft.read_bytes(),
        gallery_path: gallery_candidate.encode("utf-8"),
        appearance_path: appearance_candidate.encode("utf-8"),
    }
    if pending.get("dashboard_placement_requested"):
        dashboard = _load_json(dashboard_path)
        dashboard_candidate = _dashboard_with_visual(dashboard, pending, payload, destination_value)
        dashboard_validation = check_dashboard_data(dashboard_candidate, dashboard_path, require_assets=False)
        if not dashboard_validation["ok"]:
            raise VisualError("dashboard_validation_failed", json.dumps(dashboard_validation["findings"], ensure_ascii=False))
        changes[dashboard_path] = _json_bytes(dashboard_candidate)

    completed_at = _utc_now()
    resume = {"return_anchor": pending["return_anchor"], "next_step": pending["next_step"]}
    history_entry = {
        "transaction_id": transaction_id,
        "status": "accepted",
        "target": pending["target"],
        "asset": campaign_destination_value,
        "dashboard_asset": f"dashboard/{destination_value}",
        "dashboard_placement_completed": bool(pending.get("dashboard_placement_requested")),
        "resume": resume,
        "completed_at": completed_at,
    }
    state["history"].append(history_entry)
    state["pending"] = None
    state["revision"] += 1
    changes[state_path] = _json_bytes(state)
    _commit_with_rollback(changes)
    return {
        "ok": True,
        "action": "accept",
        "transaction_id": transaction_id,
        "asset": campaign_destination_value,
        "dashboard_asset": f"dashboard/{destination_value}",
        "dashboard_placement_completed": history_entry["dashboard_placement_completed"],
        "resume": resume,
        "player_handoff": f"Return to: {resume['return_anchor']} Next: {resume['next_step']}",
    }


def cancel(root: Path, payload: dict) -> dict:
    state_path, _, _ = _state_paths(root)
    state = _load_json(state_path)
    _validate_state(state)
    transaction_id = _required(payload, "transaction_id")
    pending = _pending(state, transaction_id)
    reason = str(payload.get("reason", "Player chose to continue without this draft.")).strip()
    resume = {"return_anchor": pending["return_anchor"], "next_step": pending["next_step"]}
    state["history"].append(
        {
            "transaction_id": transaction_id,
            "status": "cancelled",
            "target": pending["target"],
            "reason": reason,
            "resume": resume,
            "completed_at": _utc_now(),
        }
    )
    state["pending"] = None
    state["revision"] += 1
    _write_state(state_path, state)
    return {"ok": True, "action": "cancel", "transaction_id": transaction_id, "resume": resume}


def _payload(args: argparse.Namespace) -> dict:
    value: dict[str, Any] = {}
    if getattr(args, "input_json", None):
        try:
            loaded = json.loads(args.input_json)
        except json.JSONDecodeError as exc:
            raise VisualError("input_invalid", f"Invalid --input-json: {exc}") from exc
        if not isinstance(loaded, dict):
            raise VisualError("input_invalid", "--input-json must contain an object.")
        value.update(loaded)
    for key, item in vars(args).items():
        if key not in {"campaign", "command", "input_json", "handler"} and item is not None:
            value[key] = item
    return value


def _common(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("--transaction-id")
    subparser.add_argument("--input-json", help="Command fields as a JSON object.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", help="Campaign folder containing visual_state.json.")
    commands = parser.add_subparsers(dest="command", required=True)

    begin_parser = commands.add_parser("begin")
    _common(begin_parser)
    begin_parser.add_argument("--target")
    begin_parser.add_argument("--interrupted-context")
    begin_parser.add_argument("--last-meaningful-beat")
    begin_parser.add_argument("--return-anchor")
    begin_parser.add_argument("--next-step")
    begin_parser.add_argument("--dashboard-placement-requested", action="store_true", default=None)
    begin_parser.add_argument("--dashboard-tile-id")
    begin_parser.add_argument("--appearance-file")
    begin_parser.set_defaults(handler=begin)

    attach_parser = commands.add_parser("attach")
    _common(attach_parser)
    attach_parser.add_argument("--draft-path")
    attach_parser.set_defaults(handler=attach)

    revise_parser = commands.add_parser("revise")
    _common(revise_parser)
    revise_parser.add_argument("--instructions")
    revise_parser.set_defaults(handler=revise)

    accept_parser = commands.add_parser("accept")
    _common(accept_parser)
    accept_parser.add_argument("--destination")
    accept_parser.add_argument("--campaign-destination")
    accept_parser.add_argument("--name")
    accept_parser.add_argument("--visual-type")
    accept_parser.add_argument("--linked-element")
    accept_parser.add_argument("--prompt-summary")
    accept_parser.add_argument("--canon-notes")
    accept_parser.add_argument("--last-shown")
    accept_parser.add_argument("--appearance-file")
    accept_parser.set_defaults(handler=accept)

    cancel_parser = commands.add_parser("cancel")
    _common(cancel_parser)
    cancel_parser.add_argument("--reason")
    cancel_parser.set_defaults(handler=cancel)

    args = parser.parse_args(argv)
    try:
        root = Path(args.campaign).resolve()
        if not root.is_dir():
            raise VisualError("campaign_missing", f"Campaign folder does not exist: {root}")
        result = args.handler(root, _payload(args))
    except VisualError as exc:
        print(json.dumps({"ok": False, "failure_category": exc.category, "failure_reason": str(exc)}, indent=2))
        return exc.exit_code
    except OSError as exc:
        print(json.dumps({"ok": False, "failure_category": "filesystem_error", "failure_reason": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

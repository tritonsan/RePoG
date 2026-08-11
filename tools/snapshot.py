"""Create a reversible snapshot of a RePoG Lite campaign folder."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def _slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "manual"


def _iter_campaign_files(root: Path, snapshots_dir: Path) -> list[Path]:
    transaction_dir = root / ".repog-transactions"
    files: list[Path] = []
    for path in root.rglob("*"):
        if (
            path == snapshots_dir
            or snapshots_dir in path.parents
            or path == transaction_dir
            or transaction_dir in path.parents
        ):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files)


def _yaml_top_values(text: str) -> dict[str, str]:
    """Read the small top-level scalar subset used by snapshot identity."""

    values: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip("'\"`")
    return values


def _integer(value: object, *, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _snapshot_identity(campaign_path: Path) -> dict[str, object]:
    setup_path = campaign_path / "setup_profile.yaml"
    setup = _yaml_top_values(setup_path.read_text(encoding="utf-8")) if setup_path.is_file() else {}
    setup_schema = _integer(setup.get("schema_version"), default=1)
    experience_mode = str(setup.get("experience_mode", "")).strip()
    if setup_schema < 4 and not experience_mode:
        experience_mode = "rpg"

    state_path = campaign_path / "current_state.yaml"
    state = _yaml_top_values(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
    continuity_revision = _integer(state.get("continuity_revision"), default=0)
    if experience_mode == "companion":
        companion_state_path = campaign_path / "companion_state.json"
        if companion_state_path.is_file():
            try:
                companion_state = json.loads(companion_state_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                companion_state = {}
            if isinstance(companion_state, dict):
                continuity_revision = _integer(companion_state.get("continuity_revision"), default=continuity_revision)

    return {
        "manifest_version": 2,
        "campaign_id": str(state.get("campaign_id", "")).strip(),
        "setup_revision": _integer(setup.get("setup_revision"), default=0),
        "continuity_revision": continuity_revision,
        "ready_for_play": str(setup.get("ready_for_play", "false")).lower() in {"true", "yes"},
        "setup_status": str(setup.get("status", "")).strip(),
        "experience_mode": experience_mode,
    }


def _create_snapshot_locked(campaign_path: Path, label: str) -> dict:
    """Copy one snapshot while the shared RPG transaction lock is held."""

    snapshots_dir = campaign_path / "snapshots"
    snapshots_dir.mkdir(exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_name = f"{stamp}_{_slug(label)}"
    snapshot_path = snapshots_dir / snapshot_name

    if snapshot_path.exists():
        return {
            "ok": False,
            "error": "snapshot_already_exists",
            "snapshot_path": str(snapshot_path),
        }

    snapshot_path.mkdir()

    files = _iter_campaign_files(campaign_path, snapshots_dir)
    copied: list[str] = []
    file_records: list[dict[str, object]] = []
    for source in files:
        relative = source.relative_to(campaign_path)
        target = snapshot_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        relative_posix = relative.as_posix()
        payload = target.read_bytes()
        copied.append(relative_posix)
        file_records.append(
            {
                "path": relative_posix,
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    content_digest = hashlib.sha256(
        json.dumps(file_records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    manifest = {
        **_snapshot_identity(campaign_path),
        "created_at": stamp,
        "source": str(campaign_path),
        "label": label,
        "files": copied,
        "file_records": file_records,
        "content_digest": f"sha256:{content_digest}",
    }
    (snapshot_path / "snapshot_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    return {
        "ok": True,
        "campaign_path": str(campaign_path),
        "snapshot_path": str(snapshot_path),
        "files_copied": len(copied),
    }


def create_snapshot(campaign_path: Path, label: str) -> dict:
    campaign_path = campaign_path.resolve()
    if not campaign_path.exists() or not campaign_path.is_dir():
        return {
            "ok": False,
            "error": "campaign_path_not_found",
            "campaign_path": str(campaign_path),
        }

    transaction_dir = campaign_path / ".repog-transactions"
    lock_path = transaction_dir / ".lock"
    try:
        transaction_dir.mkdir(exist_ok=True)
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            entries = sorted(path.name for path in transaction_dir.iterdir())
        except OSError:
            entries = [".lock"]
        return {
            "ok": False,
            "error": "rpg_transaction_pending",
            "transaction_path": str(transaction_dir),
            "entries": entries,
        }
    except OSError as exc:
        return {
            "ok": False,
            "error": "rpg_transaction_unreadable",
            "transaction_path": str(transaction_dir),
            "reason": str(exc),
        }

    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="\n") as stream:
            stream.write(f"{os.getpid()}\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            pending_entries = sorted(
                path.name for path in transaction_dir.iterdir() if path != lock_path
            )
        except OSError as exc:
            return {
                "ok": False,
                "error": "rpg_transaction_unreadable",
                "transaction_path": str(transaction_dir),
                "reason": str(exc),
            }
        if pending_entries:
            return {
                "ok": False,
                "error": "rpg_transaction_pending",
                "transaction_path": str(transaction_dir),
                "entries": pending_entries,
            }
        return _create_snapshot_locked(campaign_path, label)
    finally:
        try:
            lock_path.unlink(missing_ok=True)
        finally:
            try:
                transaction_dir.rmdir()
            except OSError:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_path", help="Path to a Lite campaign folder.")
    parser.add_argument(
        "--label",
        default="manual",
        help="Short label included in the snapshot folder name.",
    )
    args = parser.parse_args(argv)

    result = create_snapshot(Path(args.campaign_path), args.label)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())

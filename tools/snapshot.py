"""Create a reversible snapshot of a RePoG Lite campaign folder."""

from __future__ import annotations

import argparse
import json
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
    files: list[Path] = []
    for path in root.rglob("*"):
        if path == snapshots_dir or snapshots_dir in path.parents:
            continue
        if path.is_file():
            files.append(path)
    return sorted(files)


def create_snapshot(campaign_path: Path, label: str) -> dict:
    campaign_path = campaign_path.resolve()
    if not campaign_path.exists() or not campaign_path.is_dir():
        return {
            "ok": False,
            "error": "campaign_path_not_found",
            "campaign_path": str(campaign_path),
        }

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
    for source in files:
        relative = source.relative_to(campaign_path)
        target = snapshot_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(relative.as_posix())

    manifest = {
        "created_at": stamp,
        "source": str(campaign_path),
        "label": label,
        "files": copied,
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


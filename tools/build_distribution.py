"""Build a clean RePoG release directory and optional deterministic ZIP.

The public Git repository is the canonical source.  Packaging reads the
committed HEAD archive, never the mutable working tree, so ignored caches,
local campaigns, Git metadata, and unstaged files cannot enter the result.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True


class DistributionError(RuntimeError):
    pass


def _git(source: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={source.as_posix()}", "-C", str(source), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise DistributionError(result.stderr.strip() or "Git command failed.")
    return result.stdout.strip()


def _load_verifier(source: Path):
    path = source / "tools" / "verify_workspace.py"
    spec = importlib.util.spec_from_file_location("repog_verify_workspace", path)
    if spec is None or spec.loader is None:
        raise DistributionError("Could not load the workspace verifier.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _manifest(root: Path, commit: str) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        if relative == "DISTRIBUTION_MANIFEST.json":
            continue
        records.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return {
        "schema_version": 1,
        "canonical_source": "public/RePoG",
        "source_commit": commit,
        "file_count": len(records),
        "files": records,
    }


def _write_deterministic_zip(root: Path, archive: Path) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    temporary = archive.with_name(f".{archive.name}.tmp")
    if temporary.exists():
        temporary.unlink()
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
                relative = Path(root.name) / path.relative_to(root)
                info = zipfile.ZipInfo(relative.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                bundle.writestr(info, path.read_bytes())
        temporary.replace(archive)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def build(source: Path, target: Path, *, archive: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    source = source.resolve()
    target = target.resolve()
    archive = archive.resolve() if archive else None
    if target.exists():
        raise DistributionError(f"Target already exists: {target}")
    if archive and archive.exists():
        raise DistributionError(f"Archive already exists: {archive}")
    if not (source / ".git").is_dir():
        raise DistributionError(f"Canonical source is not a Git checkout: {source}")

    commit = _git(source, "rev-parse", "HEAD")
    tracked = [line for line in _git(source, "ls-files").splitlines() if line]
    policy = _load_verifier(source)
    selected = [
        path
        for path in tracked
        if path != "DISTRIBUTION_MANIFEST.json" and policy.distribution_path_allowed(path)
    ]
    excluded = [path for path in tracked if path not in selected]
    if not selected:
        raise DistributionError("The public distribution allowlist selected no files from HEAD.")
    preview = {
        "ok": True,
        "dry_run": dry_run,
        "canonical_source": str(source),
        "source_commit": commit,
        "target": str(target),
        "archive": str(archive) if archive else None,
        "tracked_file_count": len(tracked),
        "selected_file_count": len(selected),
        "excluded_tracked_file_count": len(excluded),
        "excluded_tracked_files": excluded,
    }
    if dry_run:
        return preview

    target.parent.mkdir(parents=True, exist_ok=True)
    staging_parent = target.parent
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.staging-", dir=staging_parent))
    git_archive = staging_parent / f".{target.name}.{commit[:12]}.git-archive.zip"
    try:
        result = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={source.as_posix()}",
                "-C",
                str(source),
                "archive",
                "--format=zip",
                f"--output={git_archive}",
                "HEAD",
                "--",
                *selected,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if result.returncode != 0:
            raise DistributionError(result.stderr.strip() or "Could not archive canonical HEAD.")
        with zipfile.ZipFile(git_archive) as bundle:
            bundle.extractall(staging)

        verifier = _load_verifier(staging)
        verification = verifier.verify_workspace(staging, distribution=True)
        if not verification.get("ok"):
            rules = ", ".join(item.get("rule", "unknown") for item in verification.get("findings", []) if item.get("severity") == "error")
            raise DistributionError(f"Extracted package failed verification: {rules}")

        manifest = _manifest(staging, commit)
        (staging / "DISTRIBUTION_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        manifest_verification = verifier.verify_workspace(staging, distribution=True)
        if not manifest_verification.get("ok"):
            rules = ", ".join(item.get("rule", "unknown") for item in manifest_verification.get("findings", []) if item.get("severity") == "error")
            raise DistributionError(f"Generated manifest failed verification: {rules}")
        staging.replace(target)
        if archive:
            _write_deterministic_zip(target, archive)
        preview.update(
            {
                "manifest_file_count": manifest["file_count"],
                "manifest": str(target / "DISTRIBUTION_MANIFEST.json"),
                "verification": {"errors": 0, "warnings": verification.get("warning_count", 0)},
            }
        )
        return preview
    except Exception:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        raise
    finally:
        git_archive.unlink(missing_ok=True)
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="New directory to create. Existing targets are refused.")
    parser.add_argument("--archive", help="Optional deterministic ZIP path to create.")
    parser.add_argument("--source", default=str(Path(__file__).resolve().parents[1]), help=argparse.SUPPRESS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = build(Path(args.source), Path(args.target), archive=Path(args.archive) if args.archive else None, dry_run=args.dry_run)
    except (DistributionError, OSError, zipfile.BadZipFile) as exc:
        result = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=True))
        else:
            print(f"Distribution build failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        action = "Would build" if result["dry_run"] else "Built"
        print(f"{action} RePoG {result['source_commit'][:12]} -> {result['target']}")
        if result.get("archive"):
            print(f"Archive: {result['archive']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

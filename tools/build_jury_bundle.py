"""Build the reviewed artifacts consumed by the hosted RePoG jury runtime.

The standalone player distribution and the hosted jury adapter share one
canonical Git commit, but they are packaged separately.  The Lambda archive is
rootless because the runtime extracts it directly into its workspace folder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEFAULT_BOOTSTRAP = ROOT / "infra" / "aws" / "golden" / "black-gull" / "bootstrap.json"
DEFAULT_OUTPUT = ROOT / ".site-artifacts" / "hosted-runtime"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rootless_zip(source: Path, archive: Path) -> None:
    temporary = archive.with_suffix(".zip.tmp")
    temporary.unlink(missing_ok=True)
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(item for item in source.rglob("*") if item.is_file()):
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes())
    temporary.replace(archive)


def build(output: Path, bootstrap_path: Path) -> dict[str, object]:
    from build_distribution import build as build_distribution

    from runtime.hosted.contracts import validate_bootstrap

    bootstrap = json.loads(bootstrap_path.read_text(encoding="utf-8"))
    validate_bootstrap(bootstrap)

    output = output.resolve()
    if output.exists():
        raise RuntimeError(f"output_exists:{output}")
    output.mkdir(parents=True)
    workspace = output / "workspace"
    try:
        distribution = build_distribution(ROOT, workspace)
        workspace_zip = output / "workspace.zip"
        _rootless_zip(workspace, workspace_zip)
        bootstrap_output = output / "bootstrap.json"
        shutil.copy2(bootstrap_path, bootstrap_output)
        with zipfile.ZipFile(workspace_zip) as bundle:
            names = set(bundle.namelist())
        required = {"AGENTS.md", "tools/rpg_state.py", "campaign/current_state.yaml"}
        missing = sorted(required - names)
        if missing:
            raise RuntimeError(f"runtime_workspace_missing:{','.join(missing)}")
        manifest = {
            "schema_version": 1,
            "source_commit": distribution["source_commit"],
            "workspace_zip": {
                "path": str(workspace_zip),
                "bytes": workspace_zip.stat().st_size,
                "sha256": _sha256(workspace_zip),
                "rootless": True,
            },
            "bootstrap": {
                "path": str(bootstrap_output),
                "bytes": bootstrap_output.stat().st_size,
                "sha256": _sha256(bootstrap_output),
                "pack_id": bootstrap["manifest"]["pack_id"],
                "character_id": bootstrap["initial_turn"]["seat"]["character_id"],
            },
        }
        (output / "artifact-manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        shutil.rmtree(workspace)
        return {"ok": True, **manifest}
    except Exception:
        shutil.rmtree(output, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--bootstrap", default=str(DEFAULT_BOOTSTRAP))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = build(Path(args.output), Path(args.bootstrap))
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}
        print(json.dumps(result, indent=2) if args.json else f"Jury bundle failed: {exc}")
        return 2
    print(json.dumps(result, indent=2) if args.json else f"Built {result['workspace_zip']['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

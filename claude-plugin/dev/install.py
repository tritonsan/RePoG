"""Sync the plugin into the Claude desktop app's installed copy, with a backup.

    python dev/install.py [--target PATH] [--dry-run]

The desktop app keeps an uploaded plugin under
`~/.claude/plugins/marketplaces/local-desktop-app-uploads/repog`. This script
copies every changed file from `plugin/` there, after backing up the files it
replaces under `dist/install-backups/<stamp>/`. The installed
`.claude-plugin/plugin.json` is left alone, because its version must keep
matching the app's own install registry. New skill text and hooks load in the
next session; helpers are read live.
"""

from __future__ import annotations

import argparse
import datetime as dt
import filecmp
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugin"
DEFAULT_TARGET = Path.home() / ".claude" / "plugins" / "marketplaces" / "local-desktop-app-uploads" / "repog"
KEEP_INSTALLED = {".claude-plugin/plugin.json"}


def plan(target: Path) -> list[Path]:
    changed: list[Path] = []
    for path in sorted(SOURCE.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(SOURCE)
        if relative.as_posix() in KEEP_INSTALLED:
            continue
        installed = target / relative
        if not installed.exists() or not filecmp.cmp(path, installed, shallow=False):
            changed.append(relative)
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not args.target.is_dir():
        print(f"installed plugin not found: {args.target}", file=sys.stderr)
        return 2
    changed = plan(args.target)
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    backup = ROOT / "dist" / "install-backups" / stamp
    for relative in changed:
        installed = args.target / relative
        print(("would copy " if args.dry_run else "copy ") + relative.as_posix())
        if args.dry_run:
            continue
        if installed.exists():
            (backup / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(installed, backup / relative)
        installed.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / relative, installed)
    print(f"{len(changed)} file(s) {'to sync' if args.dry_run else 'synced'}; backup: {backup if changed and not args.dry_run else 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

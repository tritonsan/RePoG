"""Build the uploadable plugin ZIP from `plugin/`.

    python dev/package.py

Writes `dist/repog-plugin-<version>.zip` with the manifest at the ZIP root, the
layout the desktop app's plugin upload expects. Refuses to overwrite an
existing archive so a released version is never silently replaced.
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugin"


def main() -> int:
    manifest = json.loads((SOURCE / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    archive = ROOT / "dist" / f"repog-plugin-{manifest['version']}.zip"
    if archive.exists():
        print(f"refusing to overwrite {archive}", file=sys.stderr)
        return 2
    archive.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(SOURCE.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                bundle.write(path, path.relative_to(SOURCE).as_posix())
                count += 1
    print(f"{archive} ({count} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Sync canonical Agent Seat JSON schemas into the isolated hosted app."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "contracts" / "agent-seat" / "v1"
TARGET = ROOT / "apps" / "webmcp" / "contracts" / "agent-seat" / "v1"
SCHEMAS = (
    "agent-session-pack.schema.json",
    "agent-turn-brief.schema.json",
    "agent-intent-envelope.schema.json",
    "agent-resolution-envelope.schema.json",
)


def digest(path: Path) -> str:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the hosted copies drift from canonical schemas.")
    args = parser.parse_args()
    errors: list[str] = []
    for name in SCHEMAS:
        source = SOURCE / name
        target = TARGET / name
        if args.check:
            if not target.exists() or digest(source) != digest(target):
                errors.append(name)
        else:
            TARGET.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    result = {"ok": not errors, "mode": "check" if args.check else "sync", "schemas": list(SCHEMAS), "drift": errors}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

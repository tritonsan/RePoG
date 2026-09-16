"""Make helper imports work from a standalone source checkout."""

from __future__ import annotations

import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

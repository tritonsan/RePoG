"""Structural instruction checks; semantic behavior belongs to replay evaluation.

These tests follow routed files rather than freezing paragraphs or line wrapping.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from verify_workspace import REQUIRED_FILES, distribution_path_allowed

ROOT = Path(__file__).resolve().parents[1]


def test_routed_runtime_files_are_self_contained_and_distributable() -> None:
    sources = [ROOT / "AGENTS.md", *sorted((ROOT / "workflows").rglob("*.md"))]
    for source in sources:
        text = source.read_text(encoding="utf-8")
        for relative in re.findall(r"`((?:workflows|briefs|evaluation)/[^`\s]+\.(?:md|json))`", text):
            assert (ROOT / relative).is_file(), (source.relative_to(ROOT), relative)
            assert distribution_path_allowed(relative), relative


def test_cold_references_and_approved_replay_protocols_are_required() -> None:
    required = set(REQUIRED_FILES)
    for relative in (
        "workflows/reference/authority-map.md",
        "workflows/reference/setup-contract.md",
        "workflows/reference/creation.md",
        "workflows/reference/optional-surfaces.md",
        "workflows/gm/playbooks/persistence.md",
        "workflows/gm/playbooks/advancement.md",
        "workflows/orchestration/WORKFLOW.md",
        "workflows/worldbuild/playbooks/finalization.md",
        "evaluation/README.md", "evaluation/sustained_rpg.json",
        "evaluation/companion_continuity.json",
    ):
        assert relative in required
        assert (ROOT / relative).is_file()
        assert distribution_path_allowed(relative)


def test_hot_instruction_layer_does_not_reabsorb_cold_catalogs() -> None:
    # These generous regression ceilings protect the deliberately slim routing
    # layer without forcing a specific wording or promising response latency.
    assert len((ROOT / "AGENTS.md").read_bytes()) < 18000
    assert len((ROOT / "workflows/gm/WORKFLOW.md").read_bytes()) < 23000


def test_semantic_protocols_are_parseable_without_claiming_completed_results() -> None:
    for name in ("sustained_rpg.json", "companion_continuity.json"):
        fixture = json.loads((ROOT / "evaluation" / name).read_text(encoding="utf-8"))
        assert isinstance(fixture, dict)
        assert fixture  # Execution and independent scoring are a separate gate.

"""Workspace wiring for the runtime layer ported from the Claude Code plugin.

The helpers and their behavior are covered by the ported tests; these checks
cover what only the standalone workspace adds: the writer's fallback templates,
the language packs, and the player package boundary.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

import lang_pack
import rpg_state
from verify_workspace import REQUIRED_FILES, distribution_path_allowed

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", sorted(rpg_state.TEMPLATE_OWNERS))
def test_writer_fallback_templates_match_the_blank_campaign_owners(name: str) -> None:
    # An older campaign that lacks the owner starts it from this copy, so both
    # must hold the same blank text as the template campaign in this repository.
    fallback = rpg_state.TEMPLATE_DIR / name
    assert fallback.resolve() == (ROOT / "templates" / "campaign" / name).resolve()
    assert fallback.read_bytes() == (ROOT / "campaign" / name).read_bytes()
    for relative in (f"templates/campaign/{name}", f"campaign/{name}"):
        assert relative in REQUIRED_FILES
        assert distribution_path_allowed(relative), relative


TEMPLATE_MIRROR = sorted(
    path.relative_to(ROOT / "templates" / "campaign").as_posix()
    for path in (ROOT / "templates" / "campaign").rglob("*")
    if path.is_file()
)


def test_template_mirror_covers_the_owners_the_helpers_read() -> None:
    # The writer, the full check, the capsule, and Session 0 read the blank
    # template from templates/campaign/, because campaign/ becomes the live
    # campaign once play starts.
    for name in ("characters/_template.md", "active_cast.md", "boundaries.md", "style_state.json",
                 "storytelling.md", "play_profile.yaml", "setup_profile.yaml", "directives.md", "glossary.md"):
        assert name in TEMPLATE_MIRROR, name


@pytest.mark.parametrize("name", TEMPLATE_MIRROR)
def test_template_mirror_matches_the_blank_campaign(name: str) -> None:
    # Git may check either copy out with CRLF; the stored text is what must match.
    mirror = (ROOT / "templates" / "campaign" / name).read_bytes().replace(b"\r\n", b"\n")
    blank = (ROOT / "campaign" / name).read_bytes().replace(b"\r\n", b"\n")
    assert mirror == blank
    for relative in (f"templates/campaign/{name}", f"campaign/{name}"):
        assert distribution_path_allowed(relative), relative
    assert f"templates/campaign/{name}" in REQUIRED_FILES


def _local_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return {name for name in names if (ROOT / "tools" / f"{name}.py").is_file()}


def test_every_helper_the_writer_and_checker_load_is_required_and_shipped() -> None:
    # check_state loads check_content by file path, so it is named here.
    pending = ["rpg_state", "check_state", "check_runtime", "check_content", "presentation_lint", "scene_capsule", "session_zero_state"]
    seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        pending.extend(_local_imports(ROOT / "tools" / f"{name}.py"))
    for name in sorted(seen):
        relative = f"tools/{name}.py"
        assert relative in REQUIRED_FILES, relative
        assert distribution_path_allowed(relative), relative


def test_language_packs_are_required_and_shipped() -> None:
    assert lang_pack.PACK_DIR.resolve() == (ROOT / "packs" / "languages").resolve()
    packs = sorted(path for path in lang_pack.PACK_DIR.iterdir() if path.suffix in {".json", ".md"})
    assert {path.stem for path in packs if path.suffix == ".json"} >= {"de", "en", "es", "fr", "tr"}
    for path in packs:
        relative = path.relative_to(ROOT).as_posix()
        assert relative in REQUIRED_FILES, relative
        assert distribution_path_allowed(relative), relative


def test_runtime_working_files_never_ship() -> None:
    for relative in (
        "campaign/.repog-runtime/rolls.jsonl",
        "campaign/.repog-runtime/lint_history.jsonl",
        "campaign/.repog-runtime/curation/demo.json",
        "campaign/archive/session_log_through_r40.md",
    ):
        assert not distribution_path_allowed(relative), relative

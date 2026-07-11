from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load():
    path = ROOT / "tools" / "create_campaign_workspace.py"
    spec = importlib.util.spec_from_file_location("create_campaign_workspace", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


workspace = _load()


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    target = tmp_path / "Yeni Oyun"
    result = workspace.create(target, "yeni_oyun", "no", dry_run=True)
    assert result["ok"]
    assert not target.exists()
    assert "AGENTS.md" in result["manifest"]


def test_workspace_is_clean_standalone_and_unicode_safe(tmp_path: Path) -> None:
    target = tmp_path / "Şafak Seferi"
    result = workspace.create(target, "safak_seferi", "no")
    assert result["ok"]
    assert (target / "campaign" / "setup_profile.yaml").is_file()
    assert "safak_seferi" in (target / "campaign" / "current_state.yaml").read_text(encoding="utf-8")
    assert (target / "CLAUDE.md").is_file()
    assert (target / "OPEN_CAMPAIGN.md").is_file()
    assert not (target / "campaign" / "character_foundation.md").exists()
    assert not (target / "campaign" / "group.md").exists()
    assert (target / "templates" / "campaign" / "group.md").is_file()
    assert not (target / ".git").exists()
    assert not (target / "tests").exists()
    assert not (target / "examples").exists()
    assert not (target / "campaigns").exists()
    assert not (target / ".github").exists()


def test_nonempty_target_is_rejected_without_changes(tmp_path: Path) -> None:
    target = tmp_path / "occupied"
    target.mkdir()
    marker = target / "keep.txt"
    marker.write_text("mine", encoding="utf-8")
    result = workspace.create(target, "test", "no")
    assert not result["ok"]
    assert marker.read_text(encoding="utf-8") == "mine"


def test_invalid_campaign_id_is_rejected(tmp_path: Path) -> None:
    result = workspace.create(tmp_path / "target", "Bad Id", "no")
    assert not result["ok"]
    assert not (tmp_path / "target").exists()


def test_generated_workspace_has_no_parent_dependency(tmp_path: Path) -> None:
    target = tmp_path / "standalone"
    workspace.create(target, "standalone", "no")
    completed = subprocess.run(
        [sys.executable, "tools/check_state.py", "campaign"],
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_git_no_does_not_initialize_repository(tmp_path: Path) -> None:
    target = tmp_path / "no_git"
    result = workspace.create(target, "no_git", "no")
    assert result["git"]["requested"] is False
    assert not (target / ".git").exists()

from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT

DEEP_V8_STAGE_FILES = tuple(
    f"workflows/worldbuild/deep_v8/{number:02d}_{slug}.md"
    for number, slug in (
        (1, "north_star_authority"),
        (2, "research_canon_grounding"),
        (3, "character_core"),
        (4, "thin_world_kernel"),
        (5, "character_realization_mechanics"),
        (6, "living_world_ecology"),
        (7, "runtime_experience_contract"),
        (8, "reciprocity_campaign_horizon"),
        (9, "first_act_preparation"),
    )
)

REQUIRED_DEEP_V8_FILES = (
    "campaign/character_foundation.md",
    "campaign/session_zero_state.json",
    "tools/README.md",
    "tools/session_zero_state.py",
    "tools/migrate_session_zero_v8.py",
    "workflows/worldbuild/playbooks/finalization.md",
    "workflows/worldbuild/deep_v8/README.md",
    "workflows/worldbuild/deep_v8/manifest.json",
    *DEEP_V8_STAGE_FILES,
    "tools/file_transaction.py",
    "contracts/agent-seat/v1/agent-session-pack.schema.json",
    "contracts/agent-seat/v1/agent-turn-brief.schema.json",
    "contracts/agent-seat/v1/agent-intent-envelope.schema.json",
    "contracts/agent-seat/v1/agent-resolution-envelope.schema.json",
    "workflows/reference/authority-map.md",
    "workflows/gm/playbooks/persistence.md",
    "workflows/gm/playbooks/advancement.md",
    "workflows/worldbuild/playbooks/rpg_quick_v9.md",
    "workflows/worldbuild/playbooks/rpg_standard_v9.md",
    "evaluation/sustained_rpg.json",
    "evaluation/companion_continuity.json",
)

LOCAL_ONLY_ARTIFACTS = (
    "development/private_notes.md",
    "campaigns/private_campaign/current_state.yaml",
    "campaign/local_player_notes.md",
    "tests/private_fixture.py",
    "tools/__pycache__/private_cache.pyc",
    "assets/staged-but-uncommitted.txt",
)

TRACKED_OUT_OF_SCOPE = (
    "development/accidentally_tracked.md",
    "campaigns/accidentally_tracked/current_state.yaml",
    "examples/maintainer_demo.md",
    "campaign/characters/private_player_character.md",
)


def _copy_ignore(_directory: str, names: list[str]) -> set[str]:
    excluded = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".hypothesis",
        ".next",
        "dist",
        "node_modules",
        "tests",
    }
    return set(names).intersection(excluded)


def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
        check=False,
    )


def _git(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            "git",
            "-c",
            f"safe.directory={repo.as_posix()}",
            "-C",
            str(repo),
            *arguments,
        ]
    )


def _assert_ok(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, (
        f"command failed with {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_deep_v8_survives_clean_directory_and_zip_distribution(tmp_path: Path) -> None:
    source = tmp_path / "canonical-source"
    shutil.copytree(PUBLIC, source, ignore=_copy_ignore)

    # A public package is an allowlisted product, not an alias for every path
    # that a maintainer may accidentally commit to the canonical repository.
    for relative in TRACKED_OUT_OF_SCOPE:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"tracked but outside the player distribution boundary\n")

    _assert_ok(_git(source, "init"))
    _assert_ok(_git(source, "config", "user.name", "RePoG Distribution Test"))
    _assert_ok(_git(source, "config", "user.email", "distribution-test@invalid.local"))
    _assert_ok(_git(source, "add", "--all"))
    _assert_ok(_git(source, "commit", "-m", "Create canonical public source"))

    # These represent maintainer notes, user campaigns, tests, and runtime
    # cache created after the canonical commit. The builder must archive HEAD,
    # never copy them from the mutable working tree.
    for relative in LOCAL_ONLY_ARTIFACTS:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"must not enter the distribution\n")
    _assert_ok(_git(source, "add", "assets/staged-but-uncommitted.txt"))
    # Package membership and policy must both come from committed HEAD, even
    # when the index and the working verifier have changed independently.
    (source / "tools/verify_workspace.py").write_text(
        "raise AssertionError('mutable working policy was loaded')\n", encoding="utf-8"
    )

    target = tmp_path / "RePoG-release"
    archive = tmp_path / "RePoG-release.zip"
    build = _run(
        [
            sys.executable,
            "-B",
            str(source / "tools" / "build_distribution.py"),
            "--source",
            str(source),
            "--target",
            str(target),
            "--archive",
            str(archive),
            "--json",
        ]
    )
    _assert_ok(build)
    build_report = json.loads(build.stdout)
    assert build_report["ok"] is True
    assert build_report["dry_run"] is False
    assert set(TRACKED_OUT_OF_SCOPE) <= set(build_report["excluded_tracked_files"])
    assert build_report["selected_file_count"] < build_report["tracked_file_count"]
    assert target.is_dir()
    assert archive.is_file()

    for relative in REQUIRED_DEEP_V8_FILES:
        assert (target / relative).is_file(), relative
    for relative in LOCAL_ONLY_ARTIFACTS:
        assert not (target / relative).exists(), relative
    for relative in TRACKED_OUT_OF_SCOPE:
        assert not (target / relative).exists(), relative
    assert not (target / ".git").exists()

    verification = _run(
        [
            sys.executable,
            "-B",
            str(target / "tools" / "verify_workspace.py"),
            str(target),
            "--distribution",
            "--json",
        ]
    )
    _assert_ok(verification)
    verification_report = json.loads(verification.stdout)
    assert verification_report["ok"] is True, verification_report["findings"]
    assert verification_report["distribution"] is True
    assert verification_report["error_count"] == 0
    distribution_check = next(
        item for item in verification_report["checks"] if item["id"] == "distribution"
    )
    assert distribution_check["ok"] is True

    manifest = json.loads(
        (target / "DISTRIBUTION_MANIFEST.json").read_text(encoding="utf-8")
    )
    manifest_paths = {item["path"] for item in manifest["files"]}
    assert set(REQUIRED_DEEP_V8_FILES).issubset(manifest_paths)
    assert manifest_paths.isdisjoint(LOCAL_ONLY_ARTIFACTS)
    assert manifest_paths.isdisjoint(TRACKED_OUT_OF_SCOPE)

    with zipfile.ZipFile(archive) as bundle:
        names = set(bundle.namelist())
    prefix = f"{target.name}/"
    assert prefix + "DISTRIBUTION_MANIFEST.json" in names
    for relative in REQUIRED_DEEP_V8_FILES:
        assert prefix + relative in names, relative
    for relative in LOCAL_ONLY_ARTIFACTS:
        assert prefix + relative not in names, relative
    for relative in TRACKED_OUT_OF_SCOPE:
        assert prefix + relative not in names, relative
    assert not any(
        forbidden in Path(name).parts
        for name in names
        for forbidden in {".git", "__pycache__", "development", "campaigns", "tests"}
    )

    repeat_archive = tmp_path / "repeat.zip"
    repeat = _run([
        sys.executable, "-B", str(source / "tools/build_distribution.py"),
        "--target", str(tmp_path / "independent" / target.name),
        "--archive", str(repeat_archive), "--json",
    ])
    _assert_ok(repeat)
    assert hashlib.sha256(archive.read_bytes()).digest() == hashlib.sha256(repeat_archive.read_bytes()).digest()

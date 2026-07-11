"""Create a clean, standalone RePoG campaign workspace."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COPY_DIRS = ("workflows", "briefs", "templates", "tools")
COPY_FILES = ("AGENTS.md", "LICENSE")
DOC_FILES = ("dashboard.md", "why-codex.md")
CAMPAIGN_ID = re.compile(r"^[a-z][a-z0-9_]*$")


def manifest() -> list[str]:
    entries = list(COPY_FILES)
    for directory in COPY_DIRS:
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                entries.append(path.relative_to(ROOT).as_posix())
    entries.extend(f"docs/{name}" for name in DOC_FILES if (ROOT / "docs" / name).is_file())
    return sorted(set(entries))


def _replace_campaign_id(root: Path, campaign_id: str) -> None:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".yaml", ".yml", ".json"}:
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("replace_me", campaign_id), encoding="utf-8")


def _write_bridges(root: Path, campaign_id: str) -> None:
    (root / "CLAUDE.md").write_text(
        "# Claude Code Instructions\n\nRead `AGENTS.md`, then follow "
        "`workflows/worldbuild/WORKFLOW.md`. The active campaign is `campaign/`.\n",
        encoding="utf-8",
    )
    (root / "OPEN_CAMPAIGN.md").write_text(
        f"# Open Campaign\n\nCampaign id: `{campaign_id}`\n\n"
        "1. Open this folder in Codex, Claude Code, or another agentic coding tool.\n"
        "2. Start a new conversation in this folder.\n"
        "3. Send: `Start this RePoG campaign and guide me through Session 0.`\n\n"
        "The first Session 0 question must ask only whether you want Quick, Standard, or Deep setup.\n",
        encoding="utf-8",
    )


def _git(root: Path) -> dict:
    result = {"requested": True, "initialized": False, "committed": False, "remaining_command": ""}
    try:
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
        result["initialized"] = True
        name = subprocess.run(["git", "config", "user.name"], cwd=root, capture_output=True, text=True)
        email = subprocess.run(["git", "config", "user.email"], cwd=root, capture_output=True, text=True)
        if not name.stdout.strip() or not email.stdout.strip():
            result["warning"] = "Git identity is not configured; workspace was initialized without a commit."
            result["remaining_command"] = 'git add . && git commit -m "Initialize RePoG campaign workspace"'
            return result
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "commit", "-m", "Initialize RePoG campaign workspace"],
            cwd=root, check=True, capture_output=True, text=True,
        )
        result["committed"] = True
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        result["warning"] = f"Git setup did not complete: {exc}"
        result["remaining_command"] = 'git init && git add . && git commit -m "Initialize RePoG campaign workspace"'
    return result


def create(target: Path, campaign_id: str, git_policy: str, dry_run: bool = False) -> dict:
    target = target.expanduser().resolve()
    files = manifest()
    result = {
        "ok": False,
        "target": str(target),
        "campaign_id": campaign_id,
        "operation": "create standalone RePoG campaign workspace",
        "manifest": files,
        "dry_run": dry_run,
        "blockers": [],
    }
    if not CAMPAIGN_ID.fullmatch(campaign_id):
        result["blockers"].append("campaign-id must match ^[a-z][a-z0-9_]*$")
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        result["blockers"].append("target exists and is not an empty directory")
    if result["blockers"]:
        return result
    if dry_run:
        result["ok"] = True
        return result

    target.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{target.name}-repog-", dir=target.parent))
    try:
        for relative in files:
            source = ROOT / relative
            destination = temp / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        shutil.copytree(temp / "templates" / "campaign", temp / "campaign")
        for optional in ("character_foundation.md", "group.md"):
            (temp / "campaign" / optional).unlink(missing_ok=True)
        _replace_campaign_id(temp / "campaign", campaign_id)
        _write_bridges(temp, campaign_id)
        if target.exists():
            target.rmdir()
        temp.replace(target)
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        if target.exists() and target.is_dir() and not any(target.iterdir()):
            target.rmdir()
        raise

    use_git = git_policy == "yes"
    if git_policy == "ask" and sys.stdin.isatty():
        answer = input("Initialize local Git and create the first commit? [y/N] ").strip().lower()
        use_git = answer in {"y", "yes"}
    result["git"] = _git(target) if use_git else {"requested": False, "initialized": False, "committed": False}
    result["ok"] = True
    result["next_step"] = "Open the target folder in your agentic coding tool and start a new conversation."
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--git", choices=("ask", "yes", "no"), default="ask")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = create(Path(args.target), args.campaign_id, args.git, args.dry_run)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Target: {result['target']}")
        print(f"Operation: {result['operation']}")
        if result["blockers"]:
            print("Blocked: " + "; ".join(result["blockers"]))
        elif args.dry_run:
            print(f"Dry run: {len(result['manifest'])} runtime files would be copied.")
        else:
            print(result["next_step"])
            warning = result.get("git", {}).get("warning")
            if warning:
                print(warning)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

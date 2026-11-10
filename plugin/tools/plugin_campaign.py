"""Create a blank RePoG campaign folder for the Claude Code plugin.

The plugin keeps the engine in its install folder and each campaign in the
player's own project folder.  ``init`` copies the bundled blank campaign
template into ``<project>/campaign`` and, when they are missing, adds the two
small project files that make Claude Code treat the folder as a RePoG
campaign.  It never overwrites an existing file or campaign; a project file
that already exists is reported under ``skipped``.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "campaign"

# Auto memory would keep a second, consent-free memory of the player outside
# campaign/.  The output style is the plugin's, named `<plugin>:<style>`.
PROJECT_SETTINGS = {
    "$schema": "https://json.schemastore.org/claude-code-settings.json",
    "autoMemoryEnabled": False,
    "outputStyle": "repog:RePoG",
}

PROJECT_INSTRUCTIONS = """# RePoG Campaign

This folder holds a RePoG campaign created by the RePoG plugin. Before
replying, load the `repog:play` skill and follow it. If that skill is not
available, tell the user that this campaign needs the RePoG plugin enabled.

`campaign/` is the campaign's only memory. Never record player, companion, or
user facts in this file.
"""


class CampaignError(Exception):
    def __init__(self, category: str, reason: str) -> None:
        super().__init__(reason)
        self.category = category


def _write_new(path: Path, text: str) -> bool:
    """Create `path` with `text`; leave an existing file untouched."""

    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except FileExistsError:
        return False
    return True


def init_campaign(project: Path, *, template: Path = TEMPLATE) -> dict[str, Any]:
    project = Path(project).resolve()
    if not project.is_dir():
        raise CampaignError("project_missing", f"project folder does not exist: {project}")
    if not (template / "setup_profile.yaml").is_file():
        raise CampaignError("template_missing", f"blank campaign template is missing: {template}")
    target = project / "campaign"
    if target.exists() or target.is_symlink():
        raise CampaignError("campaign_exists", "this folder already holds a campaign/ folder")

    # Copy beside the target, then rename, so an interrupted copy never leaves
    # a partial campaign/ behind.
    staging = Path(tempfile.mkdtemp(prefix=".repog-campaign-", dir=project))
    try:
        shutil.copytree(template, staging / "campaign")
        (staging / "campaign").rename(target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    # The campaign is complete at this point; the project files only help
    # Claude Code, so one that exists already or cannot be written is skipped.
    created, skipped = ["campaign/"], []
    project_files = (
        (".claude/settings.json", json.dumps(PROJECT_SETTINGS, indent=2) + "\n"),
        ("CLAUDE.md", PROJECT_INSTRUCTIONS),
    )
    for relative, text in project_files:
        path = project / relative
        try:
            path.parent.mkdir(exist_ok=True)
            written = _write_new(path, text)
        except OSError:
            written = False
        (created if written else skipped).append(relative)
    return {
        "ok": True,
        "project": str(project),
        "campaign": str(target),
        "created": created,
        "skipped": skipped,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init", help="Create campaign/ from the blank template")
    init.add_argument("project", help="Project folder that will hold campaign/")
    args = parser.parse_args(argv)
    try:
        result = init_campaign(Path(args.project))
    except CampaignError as exc:
        result = {"ok": False, "failure_category": exc.category, "failure_reason": str(exc)}
        exit_code = 2
    except OSError as exc:
        result = {"ok": False, "failure_category": "io_error", "failure_reason": str(exc)}
        exit_code = 2
    else:
        exit_code = 0
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

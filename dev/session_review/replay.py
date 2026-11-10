"""Play the same Player messages through the real host, on a copy of a game.

    python replay.py <game folder> <out dir> --prompts prompts.json [--plugin-dir plugin] [--model M] [--effort E]

Unit tests cannot see what the model does with an instruction, only what the
helpers do with its calls. To compare two plugin versions, replay one list of
messages against each: once with the installed plugin, once with `--plugin-dir`
pointing at a working tree, each into its own out dir. Then run extract.py on the
two transcripts and compare the turns.

`prompts.json` is a JSON list of Player messages. It holds real play, so keep it
out of the repository, like every other review input. Each message is one
`claude -p` call, and later messages resume the session. The campaign is copied
into `<out dir>/game` and only the copy is played: nothing is written to the
game folder. The whole campaign is copied: a distill's full check needs it all.

Writes `<out dir>/turnN.jsonl` (the host's stream), `session_id.txt` and
`replay.log`. A run can be continued by running it again with more messages.
The transcript itself is under `~/.claude/projects/`, named after the copy's path.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path


INSTALLED_PLUGIN = "repog@local-desktop-app-uploads"
ALLOWED_TOOLS = ("Bash", "Read", "Grep", "Glob", "Skill", "Write", "Edit")
GAME_FILES = ("AGENTS.md", "CLAUDE.md")
TURN_TIMEOUT_SECONDS = 900


def copy_game(source: Path, target: Path) -> None:
    """Copy what a session reads: the campaign, the project settings, the routing files."""

    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source / "campaign", target / "campaign")
    if (source / ".claude").is_dir():
        shutil.copytree(source / ".claude", target / ".claude")
    for name in GAME_FILES:
        if (source / name).is_file():
            shutil.copyfile(source / name, target / name)


def command(session_id: str, *, first: bool, plugin_dir: str | None, model: str | None, effort: str | None) -> list[str]:
    """One `claude -p` call. A plugin dir replaces the installed copy for this run."""

    call = [shutil.which("claude") or "claude", "-p", "--output-format", "stream-json", "--verbose"]
    call += ["--permission-mode", "acceptEdits", "--allowedTools", *ALLOWED_TOOLS]
    if model:
        call += ["--model", model]
    if effort:
        call += ["--effort", effort]
    call += ["--session-id", session_id] if first else ["--resume", session_id]
    if plugin_dir:
        call += ["--plugin-dir", plugin_dir, "--settings", json.dumps({"enabledPlugins": {INSTALLED_PLUGIN: False}})]
    return call


def host_environment() -> dict[str, str]:
    """This process's environment, without what marks it as running inside another session."""

    return {key: value for key, value in os.environ.items() if not key.startswith("CLAUDE") or key == "CLAUDE_CONFIG_DIR"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("game", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--prompts", type=Path, required=True)
    parser.add_argument("--plugin-dir")
    parser.add_argument("--model")
    parser.add_argument("--effort")
    args = parser.parse_args(argv)

    prompts = json.loads(args.prompts.read_text(encoding="utf-8"))
    if not isinstance(prompts, list) or not all(isinstance(item, str) and item.strip() for item in prompts):
        print("prompts must be a JSON list of non-empty strings", file=sys.stderr)
        return 2
    game = args.out / "game"
    if not game.exists():
        copy_game(args.game, game)
    session_file = args.out / "session_id.txt"
    fresh = not session_file.exists()
    session_id = str(uuid.uuid4()) if fresh else session_file.read_text(encoding="utf-8").strip()
    session_file.write_text(session_id, encoding="utf-8")
    done = sum(1 for _ in args.out.glob("turn*.jsonl"))
    for index, prompt in enumerate(prompts, start=1):
        call = command(session_id, first=fresh and index == 1, plugin_dir=args.plugin_dir, model=args.model, effort=args.effort)
        start = time.time()
        result = subprocess.run(
            call, input=prompt.encode("utf-8"), cwd=game, env=host_environment(), capture_output=True, timeout=TURN_TIMEOUT_SECONDS
        )
        (args.out / f"turn{done + index}.jsonl").write_bytes(result.stdout)
        line = f"turn {done + index} rc={result.returncode} {time.time() - start:.1f}s"
        with (args.out / "replay.log").open("a", encoding="utf-8") as log:
            log.write(f"{line} {result.stderr[:300]!r}\n")
        print(line, flush=True)
        if result.returncode != 0:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

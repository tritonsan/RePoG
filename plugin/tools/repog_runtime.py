"""Shared, semantic-free helpers for the plugin's runtime layer.

The runtime layer is everything that runs around a turn rather than inside the
campaign's authority files: the scene capsule injected before a prompt, the
presentation lint and the reply-order record written after a reply, roll
receipts, and staged curation with the writer's list of notes due for it. It
keeps its working files in `campaign/.repog-runtime/`, which is never an owner
of fictional truth and can be deleted at any time without losing the campaign.

Every function here is defensive: hooks must never break a turn, so callers
treat any exception as "do nothing".
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable


RUNTIME_DIR = ".repog-runtime"
# Runtime records shared between components (spec 0.4.0 §2.1): the writer
# lists notes owed a curation pass, and the Stop hook records the last turn's
# reply order; the scene capsule reads both. `curation packet` records each
# packet it issues, so the capsule can tell a curator still at work from one
# never launched.
CURATION_DUE_FILE = "curation_due.json"
CURATION_ISSUED_FILE = "curation_issued.json"
ORDER_FILE = "order_last.json"
# Windows refuses to replace a file while another process has it open, as a
# hook reading lint_last.json does for a moment; a short retry rides that out.
REPLACE_ATTEMPTS = 4
# The first assistant text at least this long counts as the turn's narration.
NARRATION_MIN_CHARS = 200

# Defaults apply when play_profile.yaml has no `runtime:` block, so an existing
# campaign gets the runtime layer without a migration. Each switch is a locked
# profile preference the Player can change through an OOC request.
RUNTIME_DEFAULTS: dict[str, str] = {
    "persistence_order": "narrate_then_commit",
    "presentation_lint": "on",
    "scene_capsule": "on",
    "boundary_curator": "background",
}
RUNTIME_ALLOWED: dict[str, set[str]] = {
    "persistence_order": {"narrate_then_commit", "commit_then_narrate"},
    "presentation_lint": {"on", "off"},
    "scene_capsule": {"on", "off"},
    "boundary_curator": {"background", "inline", "off"},
}


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------


def read_text(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return default


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return default


def replace_file(source: str | Path, target: Path) -> None:
    """`os.replace`, retried briefly while another process holds the target open (Windows)."""

    for attempt in range(REPLACE_ATTEMPTS):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if attempt == REPLACE_ATTEMPTS - 1:
                raise
            time.sleep(0.05 * (attempt + 1))


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        replace_file(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _jsonl_lines(path: Path) -> list[str]:
    """Existing lines of a JSONL store, keeping every decodable line.

    A read failure raises instead of returning nothing, so an append can never
    silently truncate the store. Undecodable bytes are replaced, which damages
    at most the line they sit in; that line then fails JSON parsing and is
    skipped by readers. Only `\\n` separates records.
    """

    if not path.exists():
        return []
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return [line.rstrip("\r") for line in data.decode("utf-8", errors="replace").split("\n") if line.strip()]


def append_jsonl(path: Path, record: dict[str, Any], *, keep_last: int = 500) -> None:
    """Append one record and keep only the newest `keep_last` lines."""

    path.parent.mkdir(parents=True, exist_ok=True)
    lines = _jsonl_lines(path)
    lines.append(json.dumps(record, ensure_ascii=False, sort_keys=True))
    lines = lines[-keep_last:]
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write("\n".join(lines) + "\n")
        replace_file(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = _jsonl_lines(path)
    except OSError:
        return records
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


# ---------------------------------------------------------------------------
# Campaign discovery and settings
# ---------------------------------------------------------------------------


def find_campaign(start: str | Path | None) -> Path | None:
    """Return `<project>/campaign` when the project holds a RePoG campaign."""

    candidates: list[Path] = []
    for value in (start, os.environ.get("CLAUDE_PROJECT_DIR"), os.getcwd()):
        if value:
            candidates.append(Path(value))
    for base in candidates:
        for folder in (base / "campaign", base):
            if (folder / "setup_profile.yaml").is_file() and (folder / "current_state.yaml").is_file():
                return folder.resolve()
    return None


def runtime_dir(campaign: Path) -> Path:
    path = campaign / RUNTIME_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _strip_scalar(value: str) -> str:
    value = value.strip()
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value


def top_scalar(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:[ \t]*(.*?)[ \t]*$", text)
    return _strip_scalar(match.group(1)) if match else ""


def block_scalars(text: str, parent: str) -> dict[str, str]:
    """Flat `key: value` pairs directly under a top-level `parent:` block."""

    lines = text.splitlines()
    values: dict[str, str] = {}
    inside = False
    child_indent: int | None = None
    for line in lines:
        if re.match(rf"^{re.escape(parent)}:\s*(#.*)?$", line):
            inside = True
            continue
        if not inside:
            continue
        if line.strip() and not line.startswith((" ", "\t")) and not line.lstrip().startswith("#"):
            break
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if child_indent is None:
            child_indent = indent
        if indent != child_indent:
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):[ \t]*(.*)$", stripped)
        if match:
            values[match.group(1)] = _strip_scalar(match.group(2))
    return values


def runtime_settings(campaign: Path) -> dict[str, str]:
    """The runtime switches, with defaults for anything missing or invalid."""

    profile = read_text(campaign / "play_profile.yaml")
    configured = block_scalars(profile, "runtime")
    settings = dict(RUNTIME_DEFAULTS)
    for key, allowed in RUNTIME_ALLOWED.items():
        value = configured.get(key, "")
        if value in allowed:
            settings[key] = value
    narration = block_scalars(profile, "narration")
    settings["language"] = narration.get("language", "") or "auto"
    return settings


def records_language(campaign: Path) -> str:
    """The language campaign records are written in, as configured.

    `narration.records_language` when it names a language; the play language
    (`narration.language`) when it is `same` or missing; "auto" when neither
    is set.
    """

    narration = block_scalars(read_text(campaign / "play_profile.yaml"), "narration")
    value = narration.get("records_language", "").strip()
    if value and value.casefold() != "same":
        return value
    return narration.get("language", "").strip() or "auto"


def is_ready_rpg(campaign: Path) -> bool:
    setup = read_text(campaign / "setup_profile.yaml")
    if top_scalar(setup, "ready_for_play").lower() not in {"true", "yes"}:
        return False
    experience = top_scalar(setup, "experience_mode") or "rpg"
    return experience == "rpg"


# ---------------------------------------------------------------------------
# Current state
# ---------------------------------------------------------------------------


def _block_list(text: str, parent: str, key: str) -> list[str]:
    lines = text.splitlines()
    items: list[str] = []
    in_parent = False
    in_key = False
    key_indent = 0
    for line in lines:
        if re.match(rf"^{re.escape(parent)}:\s*$", line):
            in_parent = True
            continue
        if in_parent and line.strip() and not line.startswith((" ", "\t")) and not line.lstrip().startswith("#"):
            break
        if not in_parent:
            continue
        match = re.match(rf"^(\s+){re.escape(key)}:[ \t]*(.*)$", line)
        if match:
            inline = match.group(2).strip()
            if inline.startswith("["):
                try:
                    decoded = json.loads(inline)
                    return [str(item) for item in decoded] if isinstance(decoded, list) else []
                except json.JSONDecodeError:
                    return [part.strip().strip("'\"") for part in inline.strip("[]").split(",") if part.strip()]
            in_key = True
            key_indent = len(match.group(1))
            continue
        if in_key:
            stripped = line.strip()
            if not stripped:
                continue
            indent = len(line) - len(line.lstrip(" "))
            if stripped.startswith("- ") and indent >= key_indent:
                items.append(_strip_scalar(stripped[2:]))
            elif indent <= key_indent:
                break
    return items


def _nested_scalar(text: str, parent: str, key: str) -> str:
    inside = False
    for line in text.splitlines():
        if re.match(rf"^{re.escape(parent)}:\s*$", line):
            inside = True
            continue
        if inside and line.strip() and not line.startswith((" ", "\t")) and not line.lstrip().startswith("#"):
            break
        if inside:
            match = re.match(rf"^\s+{re.escape(key)}:[ \t]*(.*)$", line)
            if match:
                return _strip_scalar(match.group(1))
    return ""


def state_summary(campaign: Path) -> dict[str, Any]:
    """The compact facts every runtime component needs about the live scene."""

    text = read_text(campaign / "current_state.yaml")

    def number(value: str) -> int | None:
        try:
            return int(value)
        except ValueError:
            return None

    return {
        "revision": number(top_scalar(text, "continuity_revision")),
        "last_distilled_revision": number(_nested_scalar(text, "persistence", "last_distilled_revision")),
        "durable_turns_since_distill": number(_nested_scalar(text, "persistence", "durable_turns_since_distill")),
        "day": number(_nested_scalar(text, "fictional_time", "day")),
        "phase": _nested_scalar(text, "fictional_time", "phase"),
        "location": _nested_scalar(text, "current_scene", "location"),
        "title": _nested_scalar(text, "current_scene", "title"),
        "present_npcs": _block_list(text, "current_scene", "present_npcs"),
        "scene_id": _nested_scalar(text, "scene_frame", "scene_id"),
        "scene_mode": _nested_scalar(text, "scene_frame", "mode"),
        "resume_anchor": _nested_scalar(text, "scene_frame", "resume_anchor"),
        "player_name": _nested_scalar(text, "player", "name"),
    }


# ---------------------------------------------------------------------------
# Transcript reading
# ---------------------------------------------------------------------------


def _tail_rows(path: Path, size: int, window: int) -> list[dict[str, Any]]:
    """Parsed rows from the transcript's last `window` bytes, oldest first."""

    with path.open("rb") as stream:
        stream.seek(size - window)
        data = stream.read(window)
    # Rows end at LF only. JSON keeps U+2028, U+2029, and U+0085 raw inside
    # strings, and `str.splitlines` would cut a row there and lose it.
    lines = [line.rstrip("\r") for line in data.decode("utf-8", errors="replace").split("\n")]
    if window < size:
        lines = lines[1:]  # the first line may be cut in half
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _prompt_text(row: dict[str, Any]) -> str | None:
    if row.get("type") != "user" or row.get("isMeta") or row.get("isCompactSummary"):
        return None
    content = row.get("message", {}).get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        if any(isinstance(item, dict) and item.get("type") == "tool_result" for item in content):
            return None
        text = " ".join(item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text")
    else:
        return None
    if not text.strip() or text.lstrip().startswith(("<command", "<local-command", "<task-notification")):
        return None
    return text


def last_turn(transcript: str | Path) -> dict[str, Any] | None:
    """The newest Player prompt and everything the assistant showed after it.

    Returns the prompt, every assistant text block in order (text written
    between tool calls is visible to the Player too), the visible descriptions
    of tool calls, the raw tool uses, and `blocks`: the text and tool-use
    blocks interleaved in the order they were written.
    """

    # Hook events may name the transcript as `~/.claude/projects/...`.
    path = Path(os.path.expanduser(str(transcript)))
    if not path.is_file():
        return None
    size = path.stat().st_size
    window = min(size, 2_000_000)
    while True:
        # Tool results are user rows too, so widen until a real prompt is in
        # view; one long turn can span several megabytes.
        rows = _tail_rows(path, size, window)
        start = None
        for index in range(len(rows) - 1, -1, -1):
            if _prompt_text(rows[index]) is not None:
                start = index
                break
        if start is not None or window >= size:
            break
        window = min(size, window * 4)
    if start is None:
        return None
    texts: list[str] = []
    descriptions: list[str] = []
    tool_uses: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    for row in rows[start + 1 :]:
        if row.get("type") != "assistant":
            continue
        for block in row.get("message", {}).get("content", []) or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and block.get("text", "").strip():
                texts.append(block["text"])
                blocks.append({"type": "text", "text": block["text"]})
            elif block.get("type") == "tool_use":
                tool_use = {"name": block.get("name", ""), "input": block.get("input", {}) or {}}
                tool_uses.append(tool_use)
                blocks.append({"type": "tool_use", **tool_use})
                description = (block.get("input") or {}).get("description")
                if isinstance(description, str) and description.strip():
                    descriptions.append(description.strip())
    return {
        "prompt": _prompt_text(rows[start]) or "",
        "prompt_uuid": rows[start].get("uuid", ""),
        "prompt_timestamp": rows[start].get("timestamp", ""),
        "assistant_texts": texts,
        "tool_descriptions": descriptions,
        "tool_uses": tool_uses,
        "blocks": blocks,
    }


def _is_commit(block: dict[str, Any]) -> bool:
    """True for a tool call whose shell command runs an `rpg_state ... commit-*` transaction."""

    arguments = block.get("input") if block.get("type") == "tool_use" else None
    command = arguments.get("command") if isinstance(arguments, dict) else None
    return isinstance(command, str) and "rpg_state" in command and "commit-" in command


def turn_order(turn: dict[str, Any] | None, last_message: Any = None) -> dict[str, Any]:
    """How a turn ordered its narration and its commit, and whether it ended with visible text.

    `observed` compares the first assistant text of NARRATION_MIN_CHARS or
    more against the first tool call whose command runs an `rpg_state`
    `commit-*` transaction: "narrate_first", "commit_first" (the commit came
    first, or no such text came at all), or "no_commit". `final_text` is True
    when the turn's last block is visible text. The Stop event's
    `last_assistant_message` stands in for a final text the transcript does
    not hold yet. Counts positions only; reads no meaning.
    """

    blocks = list(turn.get("blocks") or []) if isinstance(turn, dict) else []
    texts = [block.get("text", "") for block in blocks if block.get("type") == "text"]
    if isinstance(last_message, str) and last_message.strip() and (not texts or texts[-1].strip() != last_message.strip()):
        blocks.append({"type": "text", "text": last_message})
    commit = next((index for index, block in enumerate(blocks) if _is_commit(block)), None)
    narration = next(
        (
            index
            for index, block in enumerate(blocks)
            if block.get("type") == "text" and len(block.get("text", "").strip()) >= NARRATION_MIN_CHARS
        ),
        None,
    )
    if commit is None:
        observed = "no_commit"
    elif narration is not None and narration < commit:
        observed = "narrate_first"
    else:
        observed = "commit_first"
    final_text = bool(blocks) and blocks[-1].get("type") == "text" and bool(blocks[-1].get("text", "").strip())
    return {"observed": observed, "final_text": final_text}

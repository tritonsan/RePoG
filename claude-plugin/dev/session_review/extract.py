"""Split a Claude Code RePoG transcript into turns, quantify them, and write
readable segment files for review agents.

    python extract.py TRANSCRIPT OUTDIR [--segment-chars N] [--since WHEN]

Writes OUTDIR/turns.jsonl (one record per real Player prompt), OUTDIR/quant.json
(aggregate numbers) and OUTDIR/segments/seg_NN.md (rendered turns).
Read-only on the transcript.

--since keeps only the turns whose prompt is at or after WHEN, an ISO date or
date and time (UTC unless it carries an offset). Turn numbers stay those of the
whole transcript, so a turn keeps its number in every extraction.

How the transcript is read:
- Every Bash or PowerShell command is scanned whole, heredoc bodies excluded
  (`<<\\EOF` too), and every helper in it counts, however the commands are
  chained: `repog.sh <helper>` (also through a variable holding the launcher
  path, bash `R=...` or PowerShell `$R = ...`) and `python [options]
  .../tools/<helper>.py`, options such as `-X utf8` included. Quoted words
  stay whole, so a campaign path with spaces never hides the subcommand.
  Reading a tool's source is no call.
- Claude Code writes one row per content block, each repeating its message's
  usage, so usage (output tokens, thinking time, effort) counts once per
  message id. A row written twice (the same uuid) counts once.
- A compaction belongs to the turn it interrupted: the prompt that opened the
  running turn (`compactMetadata.runningTurnSends.openerUuid`, which may be
  written just after the boundary), else the latest prompt. One that comes
  before any prompt goes to the next prompt. `compaction` says whether it came
  before the reply or mid-turn.
- A call fails when its result is an error or prints a JSON document with
  `"ok": false` at the top level (`failed_calls`).
- Each commit in a call counts as one commit call and is judged by its own
  result, so a failing check chained after it does not fail it: it succeeded
  when the call printed its `{"ok": true, "operation": "commit-<kind>"}`
  document. Without one, it failed when the call failed; a commit whose output
  was piped away in a call that did not fail counts as done.
- A commit-distill result records the records it changed (state, log and
  archives aside) and the staleness or distill-gate warnings its full check
  still reported outside its curation list; info findings do not count.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import re
import statistics
from pathlib import Path

OOC_RE = re.compile(r"(?i)\b(ooc|occ)\b")
LINT_LINE_RE = re.compile(r"(?m)^\[(lint|curation|distill|names?|roll|directives?|glossary|language|habits|order|state)[^\]]*\].*$")

# A reply text block this long is narration; shorter ones are status lines.
NARRATION_CHARS = 200
COMMIT_PREFIX = "rpg_state commit-"
DISTILL_LABEL = "rpg_state commit-distill"

# A heredoc opener: <<EOF, <<-EOF, <<'EOF', <<"EOF", or <<\EOF.
HEREDOC_RE = re.compile(r"""(?<!<)<<-?(?!<)\s*\\?(["']?)([A-Za-z_]\w*)\1""")
# A variable holding the launcher path: bash `R=...`, `export R=...`, or PowerShell `$R = ...`.
LAUNCHER_VAR_RE = re.compile(
    r"""(?:^|[\s;&|(])(?:export\s+|\$)?([A-Za-z_]\w*)\s*=\s*"""
    r"""(?:"[^"\n]*repog\.sh|'[^'\n]*repog\.sh|[^\s"';&|]*repog\.sh)"""
)
# python, python3, python3.10, or py, with its options (`-B`, `-3`, `-X utf8`, `-W ignore`), then the tool.
PYTHON_TOOL_RE = re.compile(
    r"""\b(?:python(?:3(?:\.\d+)?)?|py)(?:\.exe)?["']?"""
    r"""(?:\s+(?:-[XW]\s*[^\s"';&|-][^\s"';&|]*|-[A-Za-z0-9]+))*\s+"""
    r"""(?:"[^"\n]*?|'[^'\n]*?|[^\s"';&|]*?)tools[/\\]([a-z_]+)\.py["']?"""
)
COMMAND_END = frozenset(";&|()`\n")
HELPER_RE = re.compile(r"[a-z_][a-z0-9_]*")
SUBCOMMAND_RE = re.compile(r"[a-z][a-z0-9_-]*")
JSON_START_RE = re.compile(r"(?m)^[ \t]*\{")

# Findings a distill should have reconciled: the 0.3.0 revision-lag rules and
# the 0.4.0 distill-gate rules.
STALE_RULES = frozenset(
    {
        "active_cast_stale",
        "location_graph_stale",
        "relationship_map_stale",
        "session_brief_stale",
        "cast_dead_listed",
        "cast_present_missing",
        "relationship_dead_active",
        "location_unmapped",
        "stacked_sections",
        "now_overflow",
        "minor_romance_history",
    }
)
BOOKKEEPING_FILES = frozenset({"current_state.yaml", "session_log.md"})
BOOKKEEPING_DIRS = ("archive/", ".repog-runtime/")


def ts(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        stamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=dt.timezone.utc)


def parse_since(value: str) -> dt.datetime:
    text = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        text += "T00:00:00"
    stamp = ts(text)
    if stamp is None:
        raise argparse.ArgumentTypeError(f"not an ISO date or date and time: {value}")
    return stamp


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "tool_result":
                    parts.append(text_of(block.get("content")))
        return "\n".join(parts)
    return ""


def is_real_prompt(row: dict) -> bool:
    if row.get("type") != "user" or row.get("isMeta") or row.get("isCompactSummary"):
        return False
    if row.get("toolUseResult") is not None:
        return False
    content = (row.get("message") or {}).get("content")
    if isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
        return False
    origin = row.get("origin")
    kind = origin.get("kind") if isinstance(origin, dict) else origin
    text = text_of(content).strip()
    if not text:
        return False
    if kind not in (None, "human"):
        return False
    if text.startswith("<task-notification>") or text.startswith("<side-sessions-event>"):
        return False
    return True


# ------------------------------------------------------------------ commands


def strip_heredocs(command: str) -> str:
    """The command without heredoc bodies, which are payloads, not commands."""

    kept: list[str] = []
    closing: list[str] = []
    for line in command.split("\n"):
        if closing:
            if line.strip() == closing[0]:
                closing.pop(0)
            continue
        kept.append(line)
        closing.extend(match.group(2) for match in HEREDOC_RE.finditer(line))
    return "\n".join(kept)


def _launcher_re(body: str) -> re.Pattern:
    names = sorted({match.group(1) for match in LAUNCHER_VAR_RE.finditer(body)})
    parts = [r"""repog\.sh["']?"""]
    parts += [rf"""["']?\$(?:\{{{re.escape(name)}\}}|{re.escape(name)}\b)["']?""" for name in names]
    return re.compile("|".join(parts))


def _arguments(body: str, start: int) -> list[str]:
    """The words of one simple command, from `start` to the next shell operator outside quotes.

    A quoted word stays one word without its quotes, so a campaign path with
    spaces is never read as several; an unclosed quote ends at the line end.
    """

    words: list[str] = []
    word: list[str] = []
    quote = ""
    pending = False  # a word has started, even an empty quoted one
    for char in body[start:]:
        if quote:
            if char == quote:
                quote = ""
            elif char == "\n":
                break
            else:
                word.append(char)
        elif char in "\"'":
            quote, pending = char, True
        elif char in COMMAND_END:
            break
        elif char.isspace():
            if pending:
                words.append("".join(word))
                word, pending = [], False
        else:
            word.append(char)
            pending = True
    if pending:
        words.append("".join(word))
    return words


def _subcommand(words: list[str]) -> str | None:
    """The first bare word that is neither a flag, a flag's value, nor `campaign`."""

    previous = ""
    for word in words:
        after_flag = len(previous) > 1 and previous.startswith("-") and "=" not in previous
        previous = word
        if word.startswith("-") or after_flag or word == "campaign":
            continue
        if SUBCOMMAND_RE.fullmatch(word):
            return word
    return None


def _label(helper: str, words: list[str]) -> str:
    sub = _subcommand(words)
    return f"{helper} {sub}" if sub else helper


def command_helpers(command: str) -> list[str]:
    """Every RePoG helper a shell command runs, in order, as `helper [subcommand]`."""

    body = strip_heredocs(command)
    found: list[tuple[int, str]] = []
    for match in _launcher_re(body).finditer(body):
        words = _arguments(body, match.end())
        if words and HELPER_RE.fullmatch(words[0]):
            found.append((match.start(), _label(words[0], words[1:])))
    for match in PYTHON_TOOL_RE.finditer(body):
        found.append((match.start(), _label(match.group(1), _arguments(body, match.end()))))
    return [label for _, label in sorted(found)]


def json_documents(text: str) -> list[dict]:
    """The JSON objects printed in a tool result, each starting on its own line."""

    decoder = json.JSONDecoder()
    documents: list[dict] = []
    position = 0
    for match in JSON_START_RE.finditer(text):
        start = match.end() - 1
        if start < position:
            continue
        try:
            document, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            continue
        if isinstance(document, dict):
            documents.append(document)
            position = end
    return documents


def _posix(path) -> str:
    return str(path or "").replace("\\", "/")


def _is_bookkeeping(path: str) -> bool:
    path = _posix(path)
    return path in BOOKKEEPING_FILES or path.startswith(BOOKKEEPING_DIRS)


def _deferred_paths(document: dict) -> set[str]:
    due = document.get("curation_due")
    if isinstance(due, dict):
        due = due.get("targets")
    return {_posix(item.get("path")) for item in due or [] if isinstance(item, dict)}


def _is_stale(finding, deferred: set[str]) -> bool:
    """A staleness or distill-gate warning (or error) not handed to the curator.

    0.4.0 keeps the revision-lag rule ids as info, which is no stale record.
    """

    return (
        isinstance(finding, dict)
        and finding.get("rule") in STALE_RULES
        and finding.get("severity", "warning") != "info"
        and _posix(finding.get("path")) not in deferred
    )


def commit_results(helpers: list[str], documents: list[dict], call_failed: bool) -> list[tuple[str, dict | None, bool]]:
    """Each commit a call ran: its label, its own success document, and whether it failed.

    rpg_state prints `"operation": "commit-<kind>"` only in a success result,
    so a commit is matched to the first unclaimed such document of its kind.
    A commit left without one failed when the call did.
    """

    unclaimed = [d for d in documents if d.get("ok") is True and isinstance(d.get("operation"), str)]
    results = []
    for label in helpers:
        if not label.startswith(COMMIT_PREFIX):
            continue
        operation = label.split(" ", 1)[1]
        document = next((d for d in unclaimed if d["operation"] == operation), None)
        if document is not None:
            unclaimed.remove(document)
        results.append((label, document, document is None and call_failed))
    return results


def distill_summary(document: dict | None) -> dict:
    """What one commit-distill did, read from its own success document: the
    records it changed and the stale findings left. Without that document it
    is not ok (it failed, or its output was not printed)."""

    if document is None:
        return {"ok": False, "idempotent": False, "changed_records": 0, "stale_rules": []}
    deferred = _deferred_paths(document)
    findings = (document.get("full_check") or {}).get("findings") or []
    stale = {str(finding.get("rule")) for finding in findings if _is_stale(finding, deferred)}
    changed = [path for path in document.get("changed_files") or [] if not _is_bookkeeping(path)]
    return {
        "ok": True,
        "idempotent": bool(document.get("idempotent")),
        "changed_records": len(changed),
        "stale_rules": sorted(stale),
    }


# --------------------------------------------------------------------- turns


def new_turn(index: int, row: dict, text: str) -> dict:
    return {
        "idx": index,
        "uuid": row.get("uuid"),
        "prompt_ts": row.get("timestamp"),
        "prompt": text,
        "events": [],
        "texts": [],
        "tool_counts": collections.Counter(),
        "helpers": [],
        "errors": [],
        "capsules": [],
        "silent_reminders": 0,
        "notifications": 0,
        "compaction_before": False,
        "compaction": None,
        "assistant_rows": 0,
        "out_tokens": 0,
        "thinking_ms": 0,
        "efforts": collections.Counter(),
        "last_ts": row.get("timestamp"),
        "first_narration_ts": None,
        "stop_hook_errors": 0,
        "agents": [],
        "skills": [],
        "commit_calls": 0,
        "commit_chars": [],
        "commit_failures": 0,
        "failed_calls": [],
        "distills": [],
    }


class TurnSplitter:
    """Feeds transcript rows in order and collects one record per Player prompt."""

    def __init__(self) -> None:
        self.turns: list[dict] = []
        self.current: dict | None = None
        self.by_uuid: dict[str, dict] = {}
        self.seen_uuids: set[str] = set()
        self.pending_compaction: dict | None = None
        self.compactions: list[str] = []
        self.tool_names: dict[str, str] = {}
        self.calls: dict[str, tuple[dict, list[str]]] = {}
        self.usage_seen: dict[str, tuple[int, int]] = {}  # message id: (output tokens, thinking ms)

    def feed(self, row: dict) -> None:
        kind = row.get("type")
        if row.get("uuid"):
            if str(row["uuid"]) in self.seen_uuids:
                return  # a row written twice is one row
            self.seen_uuids.add(str(row["uuid"]))
        if kind == "system" and row.get("subtype") == "compact_boundary":
            self._on_compaction(row)
        elif is_real_prompt(row):
            self._on_prompt(row)
        elif self.current is None:
            return
        elif kind == "user":
            self._on_user(row)
        elif kind == "assistant":
            self._on_assistant(row)
        elif kind == "attachment":
            self._on_attachment(row)
        elif kind == "system" and row.get("subtype") == "stop_hook_summary" and row.get("hookErrors"):
            self.current["stop_hook_errors"] += 1

    def _on_prompt(self, row: dict) -> None:
        text = text_of((row.get("message") or {}).get("content")).strip()
        self.current = new_turn(len(self.turns) + 1, row, text)
        self.turns.append(self.current)
        if row.get("uuid"):
            self.by_uuid[str(row["uuid"])] = self.current
        if self.pending_compaction is not None:
            self._mark_compaction(self.current, self.pending_compaction)
            self.pending_compaction = None

    def _on_compaction(self, row: dict) -> None:
        self.compactions.append(row.get("timestamp"))
        opener = ((row.get("compactMetadata") or {}).get("runningTurnSends") or {}).get("openerUuid")
        if opener and str(opener) in self.by_uuid:
            turn = self.by_uuid[str(opener)]
        elif opener and str(opener) not in self.seen_uuids:
            turn = None  # the prompt that opens the running turn is written after the boundary
        else:
            turn = self.current
        if turn is None:
            self.pending_compaction = row
        else:
            self._mark_compaction(turn, row)

    @staticmethod
    def _mark_compaction(turn: dict, row: dict) -> None:
        turn["compaction_before"] = True
        if turn["compaction"] != "before_reply":
            turn["compaction"] = "mid_turn" if turn["assistant_rows"] else "before_reply"
        trigger = (row.get("compactMetadata") or {}).get("trigger") or "?"
        turn["events"].append(("compaction", trigger))

    def _on_user(self, row: dict) -> None:
        current = self.current
        content = (row.get("message") or {}).get("content")
        if row.get("isMeta") and "no visible output" in text_of(content):
            current["silent_reminders"] += 1
            current["events"].append(("silent_reminder",))
        origin = row.get("origin")
        okind = origin.get("kind") if isinstance(origin, dict) else origin
        if okind == "task-notification" or text_of(content).startswith("<task-notification>"):
            current["notifications"] += 1
            current["events"].append(("notification", text_of(content)[:300]))
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    self._on_tool_result(block)

    def _on_tool_result(self, block: dict) -> None:
        tool_id = str(block.get("tool_use_id"))
        text = text_of(block.get("content"))
        if block.get("is_error"):
            name = self.tool_names.get(tool_id, "?")
            self.current["errors"].append({"tool": name, "head": text[:400]})
            self.current["events"].append(("error", name, text[:400]))
        call = self.calls.pop(tool_id, None)
        if call is None:
            return
        turn, helpers = call
        documents = json_documents(text)
        failed = bool(block.get("is_error")) or any(document.get("ok") is False for document in documents)
        if failed:
            turn["failed_calls"].append(" + ".join(helpers))
        for label, document, commit_failed in commit_results(helpers, documents, failed):
            turn["commit_failures"] += commit_failed
            if label == DISTILL_LABEL:
                turn["distills"].append(distill_summary(document))

    def _count_usage(self, row: dict, message: dict) -> None:
        """Output tokens, thinking time and effort, once per message id.

        Every row of a message repeats its usage; a later row may carry a
        larger count, and only the increase is added.
        """

        current = self.current
        tokens = int((message.get("usage") or {}).get("output_tokens") or 0)
        thinking = int(row.get("thinkingDurationMs") or 0)
        message_id = message.get("id")
        previous = self.usage_seen.get(message_id) if message_id else None
        if previous is None:
            current["efforts"][str(row.get("perTurnEffort") or row.get("effort"))] += 1
        seen_tokens, seen_thinking = previous or (0, 0)
        current["out_tokens"] += max(tokens - seen_tokens, 0)
        current["thinking_ms"] += max(thinking - seen_thinking, 0)
        if message_id:
            self.usage_seen[message_id] = (max(seen_tokens, tokens), max(seen_thinking, thinking))

    def _on_assistant(self, row: dict) -> None:
        current = self.current
        stamp = row.get("timestamp")
        if stamp:
            current["last_ts"] = stamp
        current["assistant_rows"] += 1
        message = row.get("message") or {}
        self._count_usage(row, message)
        for block in message.get("content") or []:
            btype = block.get("type")
            if btype == "text" and block.get("text", "").strip():
                current["texts"].append(block["text"])
                current["events"].append(("text", len(block["text"])))
                if len(block["text"]) >= NARRATION_CHARS and current["first_narration_ts"] is None:
                    current["first_narration_ts"] = stamp
            elif btype == "tool_use":
                self._on_tool_use(block)

    def _on_tool_use(self, block: dict) -> None:
        current = self.current
        name = block.get("name", "?")
        tool_id = str(block.get("id"))
        self.tool_names[tool_id] = name
        current["tool_counts"][name] += 1
        data = block.get("input") or {}
        desc = str(data.get("description") or "")
        helpers: list[str] = []
        if name in ("Bash", "PowerShell"):
            command = str(data.get("command") or "")
            head = command[:300]
            helpers = command_helpers(command)
            current["helpers"].extend(helpers)
            if helpers:
                self.calls[tool_id] = (current, helpers)
            commits = sum(1 for label in helpers if label.startswith(COMMIT_PREFIX))
            current["commit_calls"] += commits
            if commits:
                current["commit_chars"].append(len(command))
        elif name in ("Write", "Edit", "Read"):
            head = str(data.get("file_path") or "")
        elif name == "Agent":
            head = f"{data.get('subagent_type')} bg={data.get('run_in_background')} :: {str(data.get('description') or '')}"
            current["agents"].append(head)
        elif name == "Skill":
            head = str(data.get("skill") or "")
            current["skills"].append(head)
        else:
            head = json.dumps(data, ensure_ascii=False)[:200]
        current["events"].append(("tool", name, desc, head, helpers))

    def _on_attachment(self, row: dict) -> None:
        att = row.get("attachment") or {}
        if att.get("type") == "hook_additional_context":
            content = att.get("content")
            text = "\n".join(content) if isinstance(content, list) else str(content or "")
            self.current["capsules"].append(text)
            self.current["events"].append(("capsule", len(text)))
        elif att.get("type") == "queued_command":
            self.current["events"].append(("queued", str(att.get("prompt") or "")[:200]))


def _seconds(start: str | None, end: str | None) -> float | None:
    first, last = ts(start), ts(end)
    return round((last - first).total_seconds(), 1) if first and last else None


def _order(events: list[tuple]) -> str:
    commits = [j for j, e in enumerate(events) if e[0] == "tool" and any(h.startswith(COMMIT_PREFIX) for h in e[4])]
    texts = [j for j, e in enumerate(events) if e[0] == "text" and e[1] >= NARRATION_CHARS]
    if commits and texts:
        return "narrate_first" if texts[0] < commits[0] else "commit_first"
    return "commit_no_long_text" if commits else "no_commit"


def derive(turns: list[dict]) -> None:
    """Add the per-turn numbers that need the whole turn (or the next one)."""

    for i, turn in enumerate(turns):
        turn["wait_s"] = _seconds(turn["prompt_ts"], turn["last_ts"])
        turn["narration_wait_s"] = _seconds(turn["prompt_ts"], turn["first_narration_ts"])
        nxt = turns[i + 1]["prompt_ts"] if i + 1 < len(turns) else None
        turn["gap_to_next_s"] = _seconds(turn["last_ts"], nxt)
        kinds = [e[0] for e in turn["events"] if e[0] != "compaction"]
        turn["order"] = _order(turn["events"])
        turn["final_text_after_tools"] = bool(kinds) and kinds[-1] == "text"
        turn["ooc"] = bool(OOC_RE.search(turn["prompt"]))
        turn["helper_counts"] = collections.Counter(turn["helpers"])
        turn["capsule_lines"] = [m.group(0) for capsule in turn["capsules"] for m in LINT_LINE_RE.finditer(capsule)]
        turn["capsule_chars"] = sum(len(c) for c in turn["capsules"])
        turn["reply_words"] = len("\n\n".join(turn["texts"]).split())


def split(lines, since: dt.datetime | None = None) -> tuple[list[dict], list[str]]:
    """Turns and compaction times from transcript lines, cut at `since`."""

    splitter = TurnSplitter()
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            splitter.feed(row)
    turns, compactions = splitter.turns, splitter.compactions
    derive(turns)
    if since is not None:
        turns = [t for t in turns if (ts(t["prompt_ts"]) or since) >= since]
        compactions = [c for c in compactions if (ts(c) or since) >= since]
    return turns, compactions


# --------------------------------------------------------------------- outputs


def med(values):
    values = [v for v in values if v is not None]
    return round(statistics.median(values), 1) if values else None


def summarize(turns: list[dict], compactions: list[str], since: dt.datetime | None = None) -> dict:
    helper_total = collections.Counter()
    tool_total = collections.Counter()
    for turn in turns:
        helper_total.update(turn["helper_counts"])
        tool_total.update(turn["tool_counts"])
    return {
        "turns": len(turns),
        "since": since.isoformat() if since else None,
        "first": turns[0]["prompt_ts"] if turns else None,
        "last": turns[-1]["last_ts"] if turns else None,
        "compactions": compactions,
        "compaction_turns": [t["idx"] for t in turns if t["compaction"]],
        "median_wait_s": med([t["wait_s"] for t in turns]),
        "median_narration_wait_s": med([t["narration_wait_s"] for t in turns]),
        "median_gap_s": med([t["gap_to_next_s"] for t in turns]),
        "ooc_turns": sum(t["ooc"] for t in turns),
        "silent_reminders": sum(t["silent_reminders"] for t in turns),
        "turns_with_silent_reminder": sum(1 for t in turns if t["silent_reminders"]),
        "order": dict(collections.Counter(t["order"] for t in turns)),
        "helpers": dict(helper_total.most_common()),
        "tools": dict(tool_total.most_common()),
        "errors": sum(len(t["errors"]) for t in turns),
        "commit_calls": sum(t["commit_calls"] for t in turns),
        "commit_failures": sum(t["commit_failures"] for t in turns),
        "median_commit_chars": med([size for t in turns for size in t["commit_chars"]]),
        "distill_calls": sum(len(t["distills"]) for t in turns),
        "capsule_turns": sum(1 for t in turns if t["capsules"]),
        "median_capsule_chars": med([t["capsule_chars"] for t in turns if t["capsules"]]),
        "stop_hook_error_turns": sum(1 for t in turns if t["stop_hook_errors"]),
        "agents": [a for t in turns for a in t["agents"]],
        "median_reply_words": med([t["reply_words"] for t in turns]),
        "out_tokens": sum(t["out_tokens"] for t in turns),
    }


def render(turn: dict) -> str:
    head = (
        f"### T{turn['idx']} [{(turn['prompt_ts'] or '')[:16].replace('T', ' ')}] wait {turn['wait_s']}s"
        f" | words {turn['reply_words']} | order {turn['order']}"
        + (f" | COMPACTION {turn['compaction'].replace('_', ' ').upper()}" if turn["compaction"] else "")
        + (f" | silent-reminders {turn['silent_reminders']}" if turn["silent_reminders"] else "")
    )
    lines = [head, "", "PLAYER: " + turn["prompt"], ""]
    text_i = 0
    for event in turn["events"]:
        if event[0] == "text":
            lines.append("GM: " + turn["texts"][text_i])
            text_i += 1
        elif event[0] == "tool":
            name, desc, cmd = event[1:4]
            lines.append(f"  [tool {name}] {desc} :: {cmd[:220]!s}".replace("\n", " "))
        elif event[0] == "error":
            lines.append(f"  [ERROR {event[1]}] {event[2][:300]}".replace("\n", " "))
        elif event[0] == "compaction":
            lines.append(f"  [compaction: {event[1]}]")
        elif event[0] == "silent_reminder":
            lines.append("  [host: previous response had no visible output]")
        elif event[0] == "notification":
            lines.append("  [notification] " + event[1][:200].replace("\n", " "))
    if turn["capsule_lines"]:
        lines.append("  [capsule notes] " + " || ".join(turn["capsule_lines"])[:1500])
    lines.append("")
    return "\n".join(lines)


def write_turns(out: Path, turns: list[dict]) -> None:
    with open(out / "turns.jsonl", "w", encoding="utf-8") as handle:
        for turn in turns:
            record = dict(turn)
            record["tool_counts"] = dict(turn["tool_counts"])
            record["efforts"] = dict(turn["efforts"])
            record["helper_counts"] = dict(turn["helper_counts"])
            record["events"] = [list(e) for e in turn["events"]]
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_segments(out: Path, turns: list[dict], segment_chars: int) -> list[str]:
    segment, size, number, index = [], 0, 1, []
    for turn in turns:
        block = render(turn)
        if segment and size + len(block) > segment_chars:
            name = f"seg_{number:02d}.md"
            (out / "segments" / name).write_text("\n".join(segment), encoding="utf-8")
            index.append(name)
            segment, size, number = [], 0, number + 1
        segment.append(block)
        size += len(block)
    if segment:
        name = f"seg_{number:02d}.md"
        (out / "segments" / name).write_text("\n".join(segment), encoding="utf-8")
        index.append(name)
    return index


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("transcript")
    parser.add_argument("outdir")
    parser.add_argument("--segment-chars", type=int, default=110_000)
    parser.add_argument("--since", type=parse_since, help="keep turns from this ISO date or time (UTC by default)")
    args = parser.parse_args(argv)
    out = Path(args.outdir)
    (out / "segments").mkdir(parents=True, exist_ok=True)

    with open(args.transcript, encoding="utf-8") as handle:
        turns, compactions = split(handle, args.since)
    quant = summarize(turns, compactions, args.since)
    write_turns(out, turns)
    (out / "quant.json").write_text(json.dumps(quant, ensure_ascii=False, indent=2), encoding="utf-8")
    index = write_segments(out, turns, args.segment_chars)
    print(json.dumps({k: quant[k] for k in quant if k != "agents"}, ensure_ascii=False, indent=1))
    print("segments", len(index))


if __name__ == "__main__":
    main()

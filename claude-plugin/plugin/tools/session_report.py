"""Summarize turn speed and bookkeeping cost from a Claude Code transcript.

Designer-only measurement. It reads one local session transcript (JSONL) and
prints numbers only: no prose, names, or campaign content leave the file. Use
it to compare play before and after a workflow change.

    python tools/session_report.py <transcript.jsonl> [--from-turn N] [--to-turn M]

A turn starts at a typed Player message. Its model wait runs from that message
to the last assistant output before the next one. A turn is durable when it
calls `rpg_state` commit-durable; payload writes are files written to a
scratch or temp folder during the turn.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any


def _time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def _prompt_text(row: dict[str, Any]) -> str | None:
    if row.get("type") != "user" or row.get("isMeta") or row.get("isCompactSummary"):
        return None
    content = row.get("message", {}).get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        if any(isinstance(item, dict) and item.get("type") == "tool_result" for item in content):
            return None
        text = " ".join(item.get("text", "") for item in content if isinstance(item, dict))
    else:
        return None
    if not text.strip() or text.lstrip().startswith(("<command", "<local-command")):
        return None
    return text


def _turns(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    for row in rows:
        text = _prompt_text(row)
        if text is not None and row.get("timestamp"):
            turns.append({"start": _time(row["timestamp"]), "text": text, "rows": []})
        elif turns:
            turns[-1]["rows"].append(row)
    return turns


def _measure(turn: dict[str, Any]) -> dict[str, Any] | None:
    assistant = [row for row in turn["rows"] if row.get("type") == "assistant" and row.get("timestamp")]
    if not assistant:
        return None
    end = _time(assistant[-1]["timestamp"])
    calls: dict[str, dict[str, Any]] = {}
    tools: list[tuple[str, dict[str, Any]]] = []
    first_text = None
    for row in assistant:
        message = row.get("message", {})
        calls[message.get("id") or row.get("uuid", "")] = message.get("usage", {}) or {}
        for block in message.get("content", []) or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                tools.append((block.get("name", ""), block.get("input", {}) or {}))
            elif block.get("type") == "text" and len(block.get("text", "")) > 200 and first_text is None:
                first_text = (_time(row["timestamp"]) - turn["start"]).total_seconds()
    commands = " ".join(str(item.get("command", "")) for name, item in tools if name == "Bash")
    payload_writes = [
        len(str(item.get("content", "")))
        for name, item in tools
        if name == "Write" and re.search(r"(?i)scratchpad|[\\/]te?mp[\\/]", str(item.get("file_path", "")))
    ]
    errors = sum(
        1
        for row in turn["rows"]
        if row.get("type") == "user"
        and isinstance(row.get("message", {}).get("content"), list)
        and any(isinstance(item, dict) and item.get("is_error") for item in row["message"]["content"])
    )
    input_tokens = sum(
        usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
        for usage in calls.values()
    )
    return {
        "wait": (end - turn["start"]).total_seconds(),
        "first_reply": first_text,
        "durable": "commit-durable" in commands,
        "distill": "commit-distill" in commands or bool(re.search(r"(?i)distill|refresh", commands)),
        "api_calls": len(calls),
        "input_tokens": input_tokens,
        "output_tokens": sum(usage.get("output_tokens", 0) for usage in calls.values()),
        "tool_calls": len(tools),
        "payload_writes": len(payload_writes),
        "payload_bytes": sum(payload_writes),
        "tool_errors": errors,
        "ooc": bool(re.search(r"(?i)\booc\b|out of (character|context)", turn["text"])),
        "compaction": any(row.get("type") == "system" and row.get("subtype") == "compact_boundary" for row in turn["rows"]),
    }


def _summary(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)
    return {
        "median": round(statistics.median(ordered), 1),
        "p90": round(ordered[max(0, int(0.9 * len(ordered)) - 1)], 1),
        "mean": round(statistics.fmean(ordered), 1),
    }


def report(path: Path, *, first: int = 1, last: int | None = None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    turns = _turns(rows)
    selected = turns[first - 1 : last]
    measured = [item for item in (_measure(turn) for turn in selected) if item is not None]
    durable = [item for item in measured if item["durable"]]
    soft = [item for item in measured if not item["durable"]]
    return {
        "transcript": str(path),
        "turns_total": len(turns),
        "turns_measured": len(measured),
        "range": [first, last or len(turns)],
        "durable_turns": len(durable),
        "soft_turns": len(soft),
        "distill_turns": sum(1 for item in measured if item["distill"]),
        "wait_seconds": {
            "all": _summary([item["wait"] for item in measured]),
            "durable": _summary([item["wait"] for item in durable]),
            "soft": _summary([item["wait"] for item in soft]),
        },
        "api_calls_per_turn": _summary([item["api_calls"] for item in measured]),
        "input_tokens_per_turn": _summary([item["input_tokens"] for item in measured]),
        "output_tokens_per_turn": _summary([item["output_tokens"] for item in measured]),
        "tool_calls_per_turn": _summary([item["tool_calls"] for item in measured]),
        "payload_writes": sum(item["payload_writes"] for item in measured),
        "payload_bytes_per_write": _summary(
            [item["payload_bytes"] / item["payload_writes"] for item in measured if item["payload_writes"]]
        ),
        "tool_errors": sum(item["tool_errors"] for item in measured),
        "ooc_share": round(sum(item["ooc"] for item in measured) / len(measured), 3) if measured else None,
        "compactions": sum(item["compaction"] for item in measured),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("transcript", help="Path to a Claude Code session transcript (.jsonl)")
    parser.add_argument("--from-turn", type=int, default=1, help="First Player turn to include (1-based)")
    parser.add_argument("--to-turn", type=int, default=None, help="Last Player turn to include")
    args = parser.parse_args(argv)
    try:
        result = report(Path(args.transcript), first=max(1, args.from_turn), last=args.to_turn)
    except OSError as exc:
        print(json.dumps({"ok": False, "failure_category": "io_error", "failure_reason": str(exc)}))
        return 2
    print(json.dumps({"ok": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

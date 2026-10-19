from __future__ import annotations

import json
from pathlib import Path

import session_report


def _row(kind: str, time: str, content, **extra) -> dict:
    return {"type": kind, "timestamp": time, "message": {"content": content, **extra.pop("message", {})}, **extra}


def test_report_counts_durable_turns_and_payload_writes(tmp_path: Path) -> None:
    rows = [
        _row("user", "2026-10-01T10:00:00Z", "I ask the witness about the courier."),
        _row(
            "assistant",
            "2026-10-01T10:00:20Z",
            [{"type": "tool_use", "name": "Write", "input": {"file_path": "C:/x/scratchpad/p.py", "content": "x" * 400}}],
            message={"id": "m1", "usage": {"input_tokens": 10, "cache_read_input_tokens": 1000, "output_tokens": 50}},
        ),
        _row("user", "2026-10-01T10:00:21Z", [{"type": "tool_result", "content": "ok"}]),
        _row(
            "assistant",
            "2026-10-01T10:00:30Z",
            [{"type": "tool_use", "name": "Bash", "input": {"command": "sh repog.sh rpg_state campaign commit-durable --input-file -"}}],
            message={"id": "m2", "usage": {"input_tokens": 5, "cache_read_input_tokens": 1000, "output_tokens": 30}},
        ),
        _row("user", "2026-10-01T10:00:31Z", [{"type": "tool_result", "content": "ok"}]),
        _row(
            "assistant",
            "2026-10-01T10:00:40Z",
            [{"type": "text", "text": "The witness looks away. " * 20}],
            message={"id": "m3", "usage": {"input_tokens": 5, "cache_read_input_tokens": 1000, "output_tokens": 200}},
        ),
        _row("user", "2026-10-01T10:02:00Z", "OOC: how much silver do I have?"),
        _row(
            "assistant",
            "2026-10-01T10:02:05Z",
            [{"type": "text", "text": "Forty silver."}],
            message={"id": "m4", "usage": {"input_tokens": 5, "cache_read_input_tokens": 900, "output_tokens": 10}},
        ),
    ]
    path = tmp_path / "session.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    result = session_report.report(path)

    assert result["turns_total"] == 2 and result["durable_turns"] == 1 and result["soft_turns"] == 1
    assert result["wait_seconds"]["durable"]["median"] == 40.0
    assert result["payload_writes"] == 1 and result["payload_bytes_per_write"]["median"] == 400.0
    assert result["api_calls_per_turn"]["mean"] == 2.0
    assert result["ooc_share"] == 0.5

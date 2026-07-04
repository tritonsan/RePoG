"""Scan proposed player-facing text for RePoG Lite technical leakage."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


RULES: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "file_path",
        "Looks like a file path.",
        re.compile(r"(?i)(?:[a-z]:\\|(?:^|\s)(?:modes|engine|schemas|tools|worlds|skills)[\\/][^\s]+)"),
    ),
    (
        "code_fence_or_inline_code",
        "Contains code-style backticks or a fenced block marker.",
        re.compile(r"`{1,3}"),
    ),
    (
        "json_yaml_marker",
        "Looks like JSON/YAML or implementation-shaped data.",
        re.compile(r"(?m)^\s*(?:[-\w]+:\s|[{}\[\]]\s*$)"),
    ),
    (
        "technical_term",
        "Contains a technical implementation term.",
        re.compile(
            r"(?i)\b("
            r"resolver|patch|schema|json|yaml|markdown|stdout|stdin|cli|audit|"
            r"validation|validator|failure_category|runtime_config|state file|"
            r"turn log|current_state|session_log|memory file|agents\.md|skill\.md|"
            r"tool|script|prompt|engine mode|lite mode|player mode|designer mode"
            r")\b"
        ),
    ),
    (
        "raw_id",
        "Looks like a raw snake_case identifier.",
        re.compile(r"\b[a-z][a-z0-9]+(?:_[a-z0-9]+)+\b"),
    ),
    (
        "placeholder_name",
        "Contains a known placeholder-like name.",
        re.compile(r"(?i)\b(Starting Hub|Wilds Edge|Guide|Ally|Antagonist|Protagonist)\b"),
    ),
    (
        "mojibake",
        "Contains likely encoding corruption.",
        re.compile("[\\u00c3\\u00c4\\u00c5]"),
    ),
]


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def scan_text(text: str) -> dict:
    findings: list[dict] = []
    for rule_id, message, pattern in RULES:
        for match in pattern.finditer(text):
            findings.append(
                {
                    "rule": rule_id,
                    "message": message,
                    "line": _line_number(text, match.start()),
                    "match": match.group(0).strip(),
                }
            )

    return {
        "ok": not findings,
        "finding_count": len(findings),
        "findings": findings,
    }


def _read_input(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.file is not None:
        return Path(args.file).read_text(encoding="utf-8")
    return sys.stdin.read()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", help="Player-facing text to scan.")
    source.add_argument("--file", help="File containing player-facing text.")
    args = parser.parse_args(argv)

    try:
        result = scan_text(_read_input(args))
    except OSError as exc:
        result = {"ok": False, "error": "input_read_failed", "reason": str(exc)}
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())

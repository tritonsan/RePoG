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
            r"script|prompt|engine mode|lite mode|player mode|designer mode"
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


def _clean_markdown_value(value: str) -> str:
    cleaned = value.strip().strip("`*_ ")
    return re.sub(r"\s+", " ", cleaned)


def load_protected_names(campaign_path: Path) -> list[str]:
    """Read exact unrevealed proper nouns from the campaign knowledge ledger."""
    path = campaign_path
    if path.is_dir():
        path = path / "knowledge_boundaries.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    section = re.search(
        r"(?ms)^## Protected Proper Nouns\s*$\n(?P<body>.*?)(?=^##\s|\Z)",
        text,
    )
    if section is None:
        return []
    body = section.group("body")
    headings = list(re.finditer(r"(?m)^###\s+(.+?)\s*$", body))
    protected: list[str] = []
    placeholders = {"protected name", "name", "example"}
    safe_statuses = {"revealed", "pc-known", "player-known", "confirmed"}
    for index, heading in enumerate(headings):
        name = _clean_markdown_value(heading.group(1))
        if not name or name.casefold() in placeholders:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        entry = body[heading.end() : end]
        status_match = re.search(r"(?mi)^\s*-\s*Status:\s*(.+?)\s*$", entry)
        status = _clean_markdown_value(status_match.group(1)).casefold() if status_match else ""
        is_safe = any(re.match(rf"^{re.escape(safe)}\b", status) for safe in safe_statuses)
        if not is_safe:
            protected.append(name)
    return sorted(set(protected), key=lambda item: (item.casefold(), item))


def _protected_findings(text: str, protected_names: list[str]) -> list[dict]:
    findings: list[dict] = []
    for name in protected_names:
        pattern = re.compile(rf"(?<!\w){re.escape(name)}(?!\w)", re.IGNORECASE)
        for match in pattern.finditer(text):
            findings.append(
                {
                    "rule": "protected_name",
                    "message": "Contains an unrevealed campaign-protected name.",
                    "line": _line_number(text, match.start()),
                    "match": match.group(0),
                }
            )
    return findings


def scan_text(text: str, protected_names: list[str] | None = None) -> dict:
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

    findings.extend(_protected_findings(text, protected_names or []))
    findings.sort(key=lambda item: (item["line"], item["rule"], item["match"].casefold()))

    return {
        "ok": not findings,
        "finding_count": len(findings),
        "protected_name_count": len(protected_names or []),
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
    parser.add_argument(
        "--campaign",
        help="Campaign directory or knowledge_boundaries.md used for exact protected-name checks.",
    )
    args = parser.parse_args(argv)

    try:
        campaign_path = Path(args.campaign).resolve() if args.campaign else Path.cwd() / "campaign"
        protected_names = load_protected_names(campaign_path)
        result = scan_text(_read_input(args), protected_names)
    except OSError as exc:
        result = {"ok": False, "error": "input_read_failed", "reason": str(exc)}
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())

"""Warn about repeated narration shape without judging narrative meaning."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WORD_RE = re.compile(r"\b[\w']+\b", re.UNICODE)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def _words(text: str) -> list[str]:
    return [word.casefold() for word in WORD_RE.findall(text)]


def _bucket(word_count: int) -> str:
    if word_count <= 80:
        return "brief"
    if word_count <= 180:
        return "medium"
    return "long"


def _fingerprint(text: str) -> dict[str, Any]:
    words = _words(text)
    sentences = [part.strip() for part in SENTENCE_RE.split(text) if part.strip()]
    starters = []
    for sentence in sentences:
        sentence_words = _words(sentence)
        if sentence_words:
            starters.append(" ".join(sentence_words[: min(3, len(sentence_words))]))

    ngrams = sorted(
        {
            " ".join(words[index : index + 4])
            for index in range(max(0, len(words) - 3))
            if len(set(words[index : index + 4])) > 1
        }
    )
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "word_count": len(words),
        "length_bucket": _bucket(len(words)),
        "paragraph_count": len([part for part in re.split(r"\n\s*\n", text) if part.strip()]),
        "sentence_count": len(sentences),
        "sentence_starters": starters[:20],
        "four_grams": ngrams[:300],
    }


def _load_state(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("style state must be a JSON object")
    if not isinstance(data.get("history", []), list):
        raise ValueError("style state history must be a list")
    return data


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=True)
            stream.write("\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def check_style(state: dict[str, Any], text: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    current = _fingerprint(text)
    history = [item for item in state.get("history", []) if isinstance(item, dict)]
    findings: list[dict[str, Any]] = []

    folded_text = text.casefold()
    for phrase in state.get("avoid_phrases", []):
        if isinstance(phrase, str) and phrase.strip() and phrase.casefold() in folded_text:
            findings.append({"severity": "warning", "rule": "avoid_phrase", "detail": phrase})

    recent = history[-3:]
    if len(recent) == 3 and all(item.get("length_bucket") == current["length_bucket"] for item in recent):
        counts = [item.get("word_count") for item in recent if isinstance(item.get("word_count"), int)]
        if len(counts) == 3:
            average = sum(counts) / len(counts)
            if average and abs(current["word_count"] - average) / average <= 0.15:
                findings.append(
                    {
                        "severity": "info",
                        "rule": "length_monotony",
                        "detail": f"Four consecutive responses use a similar {current['length_bucket']} length.",
                    }
                )

    prior_starters: dict[str, int] = {}
    prior_ngrams: dict[str, int] = {}
    for item in history[-8:]:
        for starter in set(item.get("sentence_starters", [])):
            prior_starters[starter] = prior_starters.get(starter, 0) + 1
        for ngram in set(item.get("four_grams", [])):
            prior_ngrams[ngram] = prior_ngrams.get(ngram, 0) + 1

    repeated_starters = sorted(
        starter for starter in set(current["sentence_starters"]) if prior_starters.get(starter, 0) >= 2
    )
    if repeated_starters:
        findings.append(
            {
                "severity": "info",
                "rule": "sentence_starter_repetition",
                "detail": repeated_starters[:5],
            }
        )

    repeated_ngrams = sorted(ngram for ngram in current["four_grams"] if prior_ngrams.get(ngram, 0) >= 2)
    if repeated_ngrams:
        findings.append(
            {
                "severity": "info",
                "rule": "phrase_shape_repetition",
                "detail": repeated_ngrams[:5],
            }
        )

    return findings, current


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state_path", help="Path to style_state.json.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Candidate narration.")
    source.add_argument("--text-file", help="Read candidate narration from a UTF-8 file.")
    parser.add_argument("--record", action="store_true", help="Record this accepted narration fingerprint.")
    args = parser.parse_args(argv)

    path = Path(args.state_path).resolve()
    try:
        state = _load_state(path)
        text = args.text if args.text is not None else Path(args.text_file).read_text(encoding="utf-8")
        findings, fingerprint = check_style(state, text)
        if args.record:
            maximum = int(state.get("max_history", 8))
            if maximum < 1:
                raise ValueError("max_history must be at least 1")
            state["history"] = (state.get("history", []) + [fingerprint])[-maximum:]
            _atomic_write(path, state)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2

    print(
        json.dumps(
            {
                "ok": True,
                "finding_count": len(findings),
                "findings": findings,
                "fingerprint": {key: value for key, value in fingerprint.items() if key != "four_grams"},
                "recorded": args.record,
            },
            indent=2,
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

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
SPEAKER_TYPES = {"narrator", "npc", "companion", "mixed", "other"}
CATEGORICAL_FIELDS = (
    "dramatic_beat",
    "gm_move",
    "ending_form",
    "sensory_channel",
    "complication_type",
    "npc_social_tactic",
    "metaphor_family",
)
CATEGORICAL_HISTORY_LIMIT = 8


def _words(text: str) -> list[str]:
    return [word.casefold() for word in WORD_RE.findall(text)]


def _bucket(word_count: int) -> str:
    if word_count <= 80:
        return "brief"
    if word_count <= 180:
        return "medium"
    return "long"


def _fingerprint(
    text: str,
    *,
    beat_id: str | None = None,
    scene_id: str | None = None,
    speaker_type: str = "narrator",
    speaker_id: str | None = None,
    categories: dict[str, str] | None = None,
) -> dict[str, Any]:
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
    fingerprint = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "beat_id": beat_id,
        "scene_id": scene_id,
        "speaker_type": speaker_type,
        "speaker_id": speaker_id,
        "word_count": len(words),
        "length_bucket": _bucket(len(words)),
        "paragraph_count": len([part for part in re.split(r"\n\s*\n", text) if part.strip()]),
        "sentence_count": len(sentences),
        "sentence_starters": starters[:20],
        "four_grams": ngrams[:300],
    }
    if categories:
        fingerprint.update(categories)
    return fingerprint


def _load_state(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("style state must be a JSON object")
    if not isinstance(data.get("history", []), list):
        raise ValueError("style state history must be a list")
    if not isinstance(data.get("categorical_history", []), list):
        raise ValueError("style state categorical_history must be a list")
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


def _same_voice_context(prior: dict[str, Any], current: dict[str, Any]) -> bool:
    prior_type = prior.get("speaker_type", "narrator")
    current_type = current.get("speaker_type", "narrator")
    if prior_type != current_type:
        return False
    if current_type in {"npc", "companion"}:
        current_id = current.get("speaker_id")
        return current_id is not None and prior.get("speaker_id") == current_id
    return True


def check_style(
    state: dict[str, Any],
    text: str,
    *,
    beat_id: str | None = None,
    scene_id: str | None = None,
    speaker_type: str = "narrator",
    speaker_id: str | None = None,
    dramatic_beat: str | None = None,
    gm_move: str | None = None,
    ending_form: str | None = None,
    sensory_channel: str | None = None,
    complication_type: str | None = None,
    npc_social_tactic: str | None = None,
    metaphor_family: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if speaker_type not in SPEAKER_TYPES:
        raise ValueError(f"speaker_type must be one of: {', '.join(sorted(SPEAKER_TYPES))}")
    if speaker_id is not None and (not isinstance(speaker_id, str) or not speaker_id.strip()):
        raise ValueError("speaker_id must be a non-empty string when provided")
    if speaker_type in {"npc", "companion"} and speaker_id is None:
        raise ValueError("speaker_id is required for npc or companion style entries")
    for value, name in ((beat_id, "beat_id"), (scene_id, "scene_id")):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{name} must be a non-empty string when provided")
    raw_categories = {
        "dramatic_beat": dramatic_beat,
        "gm_move": gm_move,
        "ending_form": ending_form,
        "sensory_channel": sensory_channel,
        "complication_type": complication_type,
        "npc_social_tactic": npc_social_tactic,
        "metaphor_family": metaphor_family,
    }
    categories: dict[str, str] = {}
    for name, value in raw_categories.items():
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string when provided")
        categories[name] = value.strip()
    current = _fingerprint(
        text,
        beat_id=beat_id.strip() if isinstance(beat_id, str) else None,
        scene_id=scene_id.strip() if isinstance(scene_id, str) else None,
        speaker_type=speaker_type,
        speaker_id=speaker_id.strip() if isinstance(speaker_id, str) else None,
        categories=categories,
    )
    history = [item for item in state.get("history", []) if isinstance(item, dict)]
    comparable_history = [item for item in history if _same_voice_context(item, current)]
    findings: list[dict[str, Any]] = []

    folded_text = text.casefold()
    for phrase in state.get("avoid_phrases", []):
        if isinstance(phrase, str) and phrase.strip() and phrase.casefold() in folded_text:
            findings.append({"severity": "warning", "rule": "avoid_phrase", "detail": phrase})

    recent = comparable_history[-3:]
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
    for item in comparable_history[-8:]:
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

    # These labels are supplied by the GM at sampled review/distill cadence.
    # They are deliberately treated as compact fingerprints: this checker
    # reports repetition but never decides whether a beat is narratively good
    # and never rewrites prose.
    categorical_limit = state.get("max_categorical_history", CATEGORICAL_HISTORY_LIMIT)
    if type(categorical_limit) is not int or not 1 <= categorical_limit <= CATEGORICAL_HISTORY_LIMIT:
        raise ValueError("max_categorical_history must be an integer from 1 through 8")
    categorical_history = [
        item for item in state.get("categorical_history", []) if isinstance(item, dict)
    ][-categorical_limit:]
    comparable_categories = [
        item for item in categorical_history if _same_voice_context(item, current)
    ]
    for field, value in categories.items():
        prior_count = sum(item.get(field) == value for item in comparable_categories)
        if prior_count >= 2:
            findings.append(
                {
                    "severity": "warning",
                    "rule": "categorical_repetition",
                    "category": field,
                    "detail": value,
                    "prior_occurrences": prior_count,
                }
            )

    if speaker_type in {"npc", "companion"} and findings:
        for finding in findings:
            if finding["rule"] in {"sentence_starter_repetition", "phrase_shape_repetition"}:
                finding["context"] = "character_voice"

    return findings, current


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state_path", help="Path to style_state.json.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Candidate narration.")
    source.add_argument("--text-file", help="Read candidate narration from a UTF-8 file.")
    parser.add_argument("--record", action="store_true", help="Record this accepted narration fingerprint.")
    parser.add_argument("--beat-id", help="Durable beat or turn identifier for this entry.")
    parser.add_argument("--scene-id", help="Scene identifier for this entry.")
    parser.add_argument(
        "--speaker-type",
        choices=sorted(SPEAKER_TYPES),
        default="narrator",
        help="Separate narrator patterns from named character voice patterns.",
    )
    parser.add_argument("--speaker-id", help="Stable character id; required for npc or companion entries.")
    for field in CATEGORICAL_FIELDS:
        parser.add_argument(
            f"--{field.replace('_', '-')}",
            dest=field,
            help=f"Optional sampled category: {field}.",
        )
    args = parser.parse_args(argv)

    path = Path(args.state_path).resolve()
    try:
        state = _load_state(path)
        text = args.text if args.text is not None else Path(args.text_file).read_text(encoding="utf-8")
        findings, fingerprint = check_style(
            state,
            text,
            beat_id=args.beat_id,
            scene_id=args.scene_id,
            speaker_type=args.speaker_type,
            speaker_id=args.speaker_id,
            **{field: getattr(args, field) for field in CATEGORICAL_FIELDS},
        )
        if args.record:
            maximum = int(state.get("max_history", 8))
            if maximum < 1:
                raise ValueError("max_history must be at least 1")
            state["history"] = (state.get("history", []) + [fingerprint])[-maximum:]
            category_record = {
                "recorded_at": fingerprint["recorded_at"],
                "beat_id": fingerprint["beat_id"],
                "scene_id": fingerprint["scene_id"],
                "speaker_type": fingerprint["speaker_type"],
                "speaker_id": fingerprint["speaker_id"],
                **{field: fingerprint[field] for field in CATEGORICAL_FIELDS if field in fingerprint},
            }
            if any(field in category_record for field in CATEGORICAL_FIELDS):
                categorical_limit = int(state.get("max_categorical_history", CATEGORICAL_HISTORY_LIMIT))
                if not 1 <= categorical_limit <= CATEGORICAL_HISTORY_LIMIT:
                    raise ValueError("max_categorical_history must be from 1 through 8")
                state["categorical_history"] = (
                    state.get("categorical_history", []) + [category_record]
                )[-categorical_limit:]
            else:
                state.setdefault("categorical_history", [])
            state["schema_version"] = 3
            state["max_categorical_history"] = int(
                state.get("max_categorical_history", CATEGORICAL_HISTORY_LIMIT)
            )
            state["last_beat_id"] = fingerprint["beat_id"]
            state["last_scene_id"] = fingerprint["scene_id"]
            state["last_speaker"] = {
                "type": fingerprint["speaker_type"],
                "id": fingerprint["speaker_id"],
            }
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

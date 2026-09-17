from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import check_state


SPEC = importlib.util.spec_from_file_location(
    "sampled_style_tests", Path(__file__).resolve().parents[1] / "tools" / "check_style.py"
)
style = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(style)

LINE = "I check the ledger before I sign any delivery."


def record(state: dict, text: str = LINE, **kwargs) -> tuple[dict, list[dict]]:
    findings, fingerprint = style.check_style(state, text, **kwargs)
    return style.record_fingerprint(state, fingerprint), findings


def rules(findings: list[dict]) -> set[str]:
    return {item["rule"] for item in findings}


def test_recurring_npc_samples_survive_eight_intervening_narrator_turns() -> None:
    state = {"schema_version": 3, "history": []}
    for _ in range(3):
        state, _ = record(state, speaker_type="npc", speaker_id="clerk", npc_social_tactic="deflect")
    for number in range(8):
        state, _ = record(state, f"The afternoon light reaches table {number}.")
    assert all(item["speaker_type"] == "narrator" for item in state["history"])
    findings, _ = style.check_style(
        state, LINE, speaker_type="npc", speaker_id="clerk", npc_social_tactic="deflect"
    )
    assert {"length_monotony", "sentence_starter_repetition", "phrase_shape_repetition", "categorical_repetition"} <= rules(findings)


def test_cross_npc_repetition_is_advisory_and_does_not_conflate_speakers() -> None:
    state = {}
    for identity in ("clerk", "guard"):
        state, findings = record(state, speaker_type="npc", speaker_id=identity)
        assert "cross_npc_phrase_repetition" not in rules(findings)
    findings, fingerprint = style.check_style(state, LINE, speaker_type="npc", speaker_id="innkeeper")
    cross = [item for item in findings if item["rule"] == "cross_npc_phrase_repetition"]
    assert len(cross) == 1
    assert cross[0]["severity"] == "warning"
    assert cross[0]["speaker_ids"] == ["clerk", "guard"]
    assert fingerprint["speaker_id"] == "innkeeper"
    assert "sentence_starter_repetition" not in rules(findings)


def test_short_shared_phrase_and_unrelated_dialogue_do_not_warn_cross_npc() -> None:
    state = {}
    for identity in ("clerk", "guard", "innkeeper", "porter"):
        state, findings = record(state, "Good morning to you.", speaker_type="npc", speaker_id=identity)
        assert "cross_npc_phrase_repetition" not in rules(findings)
    state, _ = record(state, LINE, speaker_type="npc", speaker_id="clerk")
    state, _ = record(state, LINE, speaker_type="npc", speaker_id="guard")
    findings, _ = style.check_style(state, "Leave the basket beside the red door.", speaker_type="npc", speaker_id="porter")
    assert "cross_npc_phrase_repetition" not in rules(findings)


def test_narrator_and_companion_do_not_count_as_other_npcs() -> None:
    state = {}
    state, _ = record(state)
    state, _ = record(state, speaker_type="companion", speaker_id="clerk")
    state, _ = record(state, speaker_type="npc", speaker_id="clerk")
    findings, _ = style.check_style(state, LINE, speaker_type="npc", speaker_id="guard")
    assert "cross_npc_phrase_repetition" not in rules(findings)
    assert len(state["speaker_history"]) == 2  # Same id, distinct voice types.


def test_character_samples_are_bounded_and_evict_least_recently_recorded_voice() -> None:
    state = {}
    for number in range(8):
        for _ in range(7):
            state, _ = record(state, speaker_type="npc", speaker_id=f"npc_{number}")
    state, _ = record(state, speaker_type="npc", speaker_id="npc_0")
    state, _ = record(state, speaker_type="npc", speaker_id="newcomer")
    assert len(state["history"]) == 8
    assert len(state["speaker_history"]) == 8
    identities = {bucket["speaker_id"] for bucket in state["speaker_history"]}
    assert "npc_0" in identities
    assert "npc_1" not in identities
    assert state["speaker_history"][-1]["speaker_id"] == "newcomer"
    assert all(len(bucket["history"]) <= 4 for bucket in state["speaker_history"])
    assert all("text" not in sample for bucket in state["speaker_history"] for sample in bucket["history"])


def test_legacy_recent_character_samples_seed_retention_without_mutating_input() -> None:
    legacy = {"schema_version": 3, "history": [], "categorical_history": [], "avoid_phrases": []}
    for _ in range(3):
        _, sample = style.check_style(legacy, LINE, speaker_type="npc", speaker_id="clerk")
        legacy["history"].append(sample)
    before = copy.deepcopy(legacy)
    state, _ = record(legacy, "The shutters close.")
    assert legacy == before
    for number in range(8):
        state, _ = record(state, f"Clouds pass over roof {number}.")
    findings, _ = style.check_style(state, LINE, speaker_type="npc", speaker_id="clerk")
    assert "phrase_shape_repetition" in rules(findings)
    assert len(state["speaker_history"][0]["history"]) == 3


@pytest.mark.parametrize("field,value", [
    ("max_speakers", 9), ("max_speakers", 0), ("max_speakers", True),
    ("max_speaker_history", 5), ("max_speaker_history", -1), ("max_speaker_history", "4"),
])
def test_invalid_retention_limits_fail_without_mutation(field: str, value: object) -> None:
    state = {field: value, "history": []}
    before = copy.deepcopy(state)
    with pytest.raises(ValueError, match=field):
        style.check_style(state, LINE)
    assert state == before


def test_custom_smaller_retention_bounds_are_honored() -> None:
    state = {"max_speakers": 2, "max_speaker_history": 2, "max_history": 3}
    for identity in ("a", "b", "c"):
        for _ in range(4):
            state, _ = record(state, speaker_type="npc", speaker_id=identity)
    assert len(state["history"]) == 3
    assert [bucket["speaker_id"] for bucket in state["speaker_history"]] == ["b", "c"]
    assert all(len(bucket["history"]) == 2 for bucket in state["speaker_history"])


def test_mismatched_retained_voice_is_rejected() -> None:
    _, fingerprint = style.check_style({}, LINE, speaker_type="npc", speaker_id="a")
    state = {"speaker_history": [{"speaker_type": "npc", "speaker_id": "b", "history": [fingerprint]}]}
    with pytest.raises(ValueError, match="match their character voice"):
        style.check_style(state, LINE)


def test_cli_shared_motif_warning_never_rejects_or_rewrites_accepted_sample(tmp_path: Path) -> None:
    state_path = tmp_path / "style_state.json"
    state_path.write_text('{"schema_version": 3, "history": []}\n', encoding="utf-8")
    command = [sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "tools" / "check_style.py"), str(state_path)]
    for identity in ("a", "b", "c"):
        result = subprocess.run(command + ["--text", LINE, "--speaker-type", "npc", "--speaker-id", identity, "--record"], capture_output=True, text=True, check=False)
        response = json.loads(result.stdout)
        assert result.returncode == 0 and response["ok"] and response["recorded"], result.stderr
    assert "cross_npc_phrase_repetition" in rules(response["findings"])
    saved = json.loads(state_path.read_text(encoding="utf-8"))
    assert saved["schema_version"] == 3
    assert saved["last_speaker"] == {"type": "npc", "id": "c"}
    expected = style.check_style({}, LINE, speaker_type="npc", speaker_id="c")[1]
    assert saved["history"][-1]["four_grams"] == expected["four_grams"]
    assert not validator_findings(saved)
    before = state_path.read_bytes()
    result = subprocess.run(command + ["--text", LINE, "--speaker-type", "npc", "--speaker-id", "d"], capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert state_path.read_bytes() == before


def validator_findings(state: dict) -> list[dict]:
    findings = []
    check_state._check_style_state(state, Path("synthetic-style-state.json"), findings)
    return findings


def retained_state() -> dict:
    state, _ = record({"schema_version": 3}, speaker_type="npc", speaker_id="a")
    return state


@pytest.mark.parametrize("version", [1, 2, 3])
def test_validator_accepts_legacy_states_without_optional_retention(version: int) -> None:
    findings = validator_findings({"schema_version": version, "history": []})
    assert not [item for item in findings if item["severity"] == "error"]


def test_legacy_nullable_categories_remain_readable() -> None:
    state = {"schema_version": 3, "categorical_history": [
        {"speaker_type": "narrator", "dramatic_beat": "reveal", "gm_move": None},
        {"speaker_type": "narrator", "dramatic_beat": "reveal", "gm_move": None},
    ]}
    findings, _ = style.check_style(state, LINE, dramatic_beat="reveal")
    assert "categorical_repetition" in rules(findings)
    assert not validator_findings(state)


@pytest.mark.parametrize("field,value", [
    ("max_speakers", True), ("max_speakers", 9), ("max_speakers", 0),
    ("max_speaker_history", True), ("max_speaker_history", 5), ("max_speaker_history", "4"),
])
def test_validator_rejects_invalid_optional_bounds(field: str, value: object) -> None:
    state = retained_state()
    state[field] = value
    assert "style_speaker_limit_invalid" in rules(validator_findings(state))


@pytest.mark.parametrize("buckets", [
    {}, [None], [{"speaker_type": [], "speaker_id": "a", "history": []}],
    [{"speaker_type": "npc", "speaker_id": ["a"], "history": []}],
    [{"speaker_type": "npc", "speaker_id": "a", "history": {}}],
])
def test_validator_reports_malformed_retention_without_throwing(buckets: object) -> None:
    state = retained_state()
    state["speaker_history"] = buckets
    assert "style_speaker_history_invalid" in rules(validator_findings(state))


def test_validator_rejects_duplicate_voice_and_mismatched_samples() -> None:
    state = retained_state()
    state["speaker_history"].append(copy.deepcopy(state["speaker_history"][0]))
    state["speaker_history"][0]["history"][0]["speaker_id"] = "different"
    assert {"style_speaker_duplicate", "style_speaker_context_mismatch"} <= rules(validator_findings(state))


@pytest.mark.parametrize("configured_limit", [1, 4])
def test_validator_rejects_history_above_configured_or_hard_limit(configured_limit: int) -> None:
    state = retained_state()
    state["max_speaker_history"] = configured_limit
    sample = state["speaker_history"][0]["history"][0]
    state["speaker_history"][0]["history"] = [copy.deepcopy(sample) for _ in range(configured_limit + 1)]
    assert "style_speaker_samples_too_long" in rules(validator_findings(state))


@pytest.mark.parametrize("configured_limit", [1, 8])
def test_validator_rejects_speaker_count_above_configured_or_hard_limit(configured_limit: int) -> None:
    state = {"schema_version": 3, "max_speakers": configured_limit, "speaker_history": [
        {"speaker_type": "npc", "speaker_id": f"npc_{number}", "history": []}
        for number in range(configured_limit + 1)
    ]}
    assert "style_speaker_history_too_long" in rules(validator_findings(state))


@pytest.mark.parametrize("field,value", [
    ("four_grams", [{}]), ("sentence_starters", "not a list"),
    ("word_count", True), ("paragraph_count", -1), ("gm_move", {}),
])
def test_validator_reuses_fingerprint_shape_checks_for_retained_samples(field: str, value: object) -> None:
    state = retained_state()
    state["speaker_history"][0]["history"][0][field] = value
    assert "style_fingerprint_invalid" in rules(validator_findings(state))


@pytest.mark.parametrize("field", ["text", "narration", "full_text"])
def test_validator_rejects_full_prose_in_retained_sample(field: str) -> None:
    state = retained_state()
    state["speaker_history"][0]["history"][0][field] = LINE
    assert "style_speaker_full_prose" in rules(validator_findings(state))


@pytest.mark.parametrize("corruption", ["unhashable_type", "malformed_grams", "full_prose", "duplicate_voice", "bad_avoid_list"])
def test_cli_reports_malformed_state_without_writing(tmp_path: Path, capsys, corruption: str) -> None:
    state = retained_state()
    bucket = state["speaker_history"][0]
    if corruption == "unhashable_type":
        bucket["speaker_type"] = []
    elif corruption == "malformed_grams":
        bucket["history"][0]["four_grams"] = [{}]
    elif corruption == "full_prose":
        bucket["history"][0]["text"] = LINE
    elif corruption == "duplicate_voice":
        state["speaker_history"].append(copy.deepcopy(bucket))
    else:
        state["avoid_phrases"] = 42
    path = tmp_path / "style_state.json"
    path.write_text(json.dumps(state), encoding="utf-8")
    before = path.read_bytes()
    assert style.main([str(path), "--text", LINE, "--record"]) == 2
    assert json.loads(capsys.readouterr().out)["ok"] is False
    assert path.read_bytes() == before

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

import hook_entry


PLUGIN = Path(__file__).resolve().parents[1] / "plugin"


@pytest.fixture(autouse=True)
def _no_project_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)


def _run(handler: str, event: dict, capsysbinary: pytest.CaptureFixture[bytes], monkeypatch: pytest.MonkeyPatch) -> bytes:
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(json.dumps(event).encode("utf-8")), encoding="utf-8"))
    assert hook_entry.main([handler]) == 0
    return capsysbinary.readouterr().out


def _transcript(tmp_path: Path, prompt: str, reply: str) -> Path:
    rows = [
        {"type": "user", "uuid": "u-1", "timestamp": "2026-10-20T10:00:00Z", "message": {"role": "user", "content": prompt}},
        {
            "type": "assistant",
            "timestamp": "2026-10-20T10:00:05Z",
            "message": {"id": "m1", "role": "assistant", "content": [{"type": "text", "text": reply}]},
        },
    ]
    path = tmp_path / "session.jsonl"
    path.write_bytes(("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n").encode("utf-8"))
    return path


def test_prompt_hook_injects_a_hidden_capsule(campaign: Path, tmp_path: Path, capsysbinary, monkeypatch) -> None:
    out = _run(
        "prompt",
        {"hook_event_name": "UserPromptSubmit", "cwd": str(tmp_path), "session_id": "s-1", "prompt": "I ask the Witness."},
        capsysbinary,
        monkeypatch,
    )
    envelope = json.loads(out.decode("ascii"))
    context = envelope["hookSpecificOutput"]["additionalContext"]
    assert envelope["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "RePoG capsule" in context and len(context) <= hook_entry.MAX_CONTEXT


def test_prompt_hook_is_silent_outside_a_campaign_or_when_off(campaign: Path, tmp_path: Path, capsysbinary, monkeypatch) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert _run("prompt", {"cwd": str(elsewhere), "prompt": "hi"}, capsysbinary, monkeypatch) == b""
    profile = campaign / "play_profile.yaml"
    profile.write_bytes(profile.read_bytes() + b"runtime:\n  scene_capsule: off\n")
    assert _run("prompt", {"cwd": str(tmp_path), "prompt": "hi"}, capsysbinary, monkeypatch) == b""


def test_prompt_hook_applies_settled_staged_curation(campaign: Path, tmp_path: Path, capsysbinary, monkeypatch) -> None:
    note = campaign / "characters" / "witness.md"
    folder = campaign / ".repog-runtime" / "curation"
    folder.mkdir(parents=True)
    staged = folder / "fold-1.json"
    staged.write_bytes(
        json.dumps(
            {
                "curation_id": "fold-1",
                "base_revision": 0,
                "reason": "tidy the current state",
                "base_hashes": {"characters/witness.md": hashlib.sha256(note.read_bytes()).hexdigest()},
                "mutations": [
                    {
                        "path": "characters/witness.md",
                        "ops": [{"op": "replace_section", "heading": "Current State", "text": "Talking freely."}],
                    }
                ],
            }
        ).encode("utf-8")
    )
    past = time.time() - 60
    os.utime(staged, (past, past))

    _run("prompt", {"cwd": str(tmp_path), "session_id": "s-1", "prompt": "Go on."}, capsysbinary, monkeypatch)

    assert "Talking freely." in note.read_text(encoding="utf-8")
    assert (folder / "applied" / "fold-1.json").exists()


def test_stop_hook_writes_lint_and_remembers_names(campaign: Path, tmp_path: Path, capsysbinary, monkeypatch) -> None:
    transcript = _transcript(tmp_path, "I wait at the dock.", "The Witness looks up. Saving the scene.")
    out = _run(
        "stop",
        {
            "hook_event_name": "Stop",
            "cwd": str(tmp_path),
            "session_id": "s-2",
            "transcript_path": str(transcript),
            "last_assistant_message": "The Witness looks up. Saving the scene.",
        },
        capsysbinary,
        monkeypatch,
    )
    assert out == b""
    assert (campaign / ".repog-runtime" / "lint_last.json").exists()
    # The next prompt's capsule includes the person the reply named, even though
    # the prompt itself does not mention them.
    capsule = json.loads(
        _run("prompt", {"cwd": str(tmp_path), "session_id": "s-2", "prompt": "I wait."}, capsysbinary, monkeypatch)
    )["hookSpecificOutput"]["additionalContext"]
    assert "Witness (mentioned)" in capsule


def test_session_start_marks_a_full_capsule(campaign: Path, tmp_path: Path, capsysbinary, monkeypatch) -> None:
    event = {"cwd": str(tmp_path), "session_id": "s-3", "prompt": "Hello."}
    _run("prompt", event, capsysbinary, monkeypatch)
    _run("prompt", event, capsysbinary, monkeypatch)
    assert _run("session-start", {"cwd": str(tmp_path), "session_id": "s-3", "source": "compact"}, capsysbinary, monkeypatch) == b""
    context = json.loads(_run("prompt", event, capsysbinary, monkeypatch))["hookSpecificOutput"]["additionalContext"]
    assert "[cast]" in context or "[language]" in context


@pytest.mark.parametrize(
    ("tool", "tool_input", "allowed"),
    [
        ("Write", {"file_path": "{campaign}/.repog-runtime/curation/fold-2.json", "content": "{}"}, True),
        ("Write", {"file_path": "{campaign}/characters/witness.md", "content": "x"}, False),
        ("Edit", {"file_path": "{campaign}/.repog-runtime/curation/fold-2.json"}, False),
        ("Bash", {"command": "rm -rf campaign"}, False),
    ],
)
def test_pretool_guard_confines_the_curator(campaign: Path, tmp_path: Path, capsysbinary, monkeypatch, tool, tool_input, allowed) -> None:
    resolved = {key: value.replace("{campaign}", str(campaign)) for key, value in tool_input.items()}
    event = {"cwd": str(tmp_path), "agent_type": "repog:repog-curator", "tool_name": tool, "tool_input": resolved}
    out = _run("pretool", event, capsysbinary, monkeypatch)
    if allowed:
        assert out == b""
    else:
        decision = json.loads(out)["hookSpecificOutput"]
        assert decision["permissionDecision"] == "deny" and "staging file" in decision["permissionDecisionReason"]


def test_pretool_guard_ignores_the_main_session(campaign: Path, tmp_path: Path, capsysbinary, monkeypatch) -> None:
    event = {"cwd": str(tmp_path), "tool_name": "Write", "tool_input": {"file_path": str(campaign / "x.md")}}
    assert _run("pretool", event, capsysbinary, monkeypatch) == b""


def test_unknown_handler_and_garbage_input_stay_silent(capsysbinary, monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(b"\xff not json"), encoding="utf-8"))
    assert hook_entry.main(["prompt"]) == 0
    assert hook_entry.main(["no-such-hook"]) == 0
    assert capsysbinary.readouterr().out == b""


# ---------------------------------------------------------------------------
# The shell wrappers, as Claude Code runs them
# ---------------------------------------------------------------------------

SH = shutil.which("sh")


def _script(name: str, event: dict, project: Path) -> subprocess.CompletedProcess[bytes]:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_PLUGIN_ROOT": str(PLUGIN)}
    return subprocess.run(
        [SH, str(PLUGIN / "scripts" / name)],
        input=json.dumps(event).encode("utf-8"),
        capture_output=True,
        env=env,
        cwd=str(project),
        timeout=60,
    )


@pytest.mark.skipif(SH is None, reason="needs a POSIX sh")
def test_shell_wrappers_end_to_end(campaign: Path, tmp_path: Path) -> None:
    prompt = _script("prompt-hook.sh", {"cwd": str(tmp_path), "session_id": "s-9", "prompt": "Hi."}, tmp_path)
    assert prompt.returncode == 0
    assert "RePoG capsule" in json.loads(prompt.stdout)["hookSpecificOutput"]["additionalContext"]

    guard = _script(
        "pretool-guard.sh",
        {"cwd": str(tmp_path), "agent_type": "repog-curator", "tool_name": "Bash", "tool_input": {"command": "ls"}},
        tmp_path,
    )
    assert guard.returncode == 0 and json.loads(guard.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"

    plain = _script("pretool-guard.sh", {"cwd": str(tmp_path), "tool_name": "Bash"}, tmp_path)
    assert plain.returncode == 0 and plain.stdout == b""

    start = _script("session-start.sh", {"cwd": str(tmp_path), "session_id": "s-9", "source": "startup"}, tmp_path)
    assert start.returncode == 0 and b"repog:play" in start.stdout


@pytest.mark.skipif(SH is None, reason="needs a POSIX sh")
def test_shell_wrappers_are_silent_outside_a_campaign(tmp_path: Path) -> None:
    for name in ("prompt-hook.sh", "stop-hook.sh", "session-start.sh", "pretool-guard.sh"):
        result = _script(name, {"cwd": str(tmp_path), "prompt": "hi"}, tmp_path)
        assert result.returncode == 0 and result.stdout == b"", name


def test_hooks_json_uses_plugin_root_paths_only() -> None:
    config = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    commands = [hook["command"] for event in config["hooks"].values() for group in event for hook in group["hooks"]]
    assert set(config["hooks"]) == {"SessionStart", "UserPromptSubmit", "Stop", "PreToolUse"}
    for command in commands:
        assert command.startswith('sh "${CLAUDE_PLUGIN_ROOT}/scripts/') and command.endswith('.sh"')
    stop = config["hooks"]["Stop"][0]["hooks"][0]
    assert stop.get("async") is True
    for script in (PLUGIN / "scripts").glob("*.sh"):
        assert b"\r" not in script.read_bytes(), script.name


def test_last_turn_reads_a_turn_longer_than_the_first_window(tmp_path: Path) -> None:
    import repog_runtime

    big_result = {"type": "user", "message": {"content": [{"type": "tool_result", "content": "x" * 3_000_000}]}}
    rows = [
        {"type": "user", "uuid": "u-1", "message": {"content": "The long question."}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Thinking aloud."}]}},
        big_result,
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "The answer."}]}},
    ]
    path = tmp_path / "long.jsonl"
    path.write_bytes(("\n".join(json.dumps(row) for row in rows) + "\n").encode("utf-8"))
    turn = repog_runtime.last_turn(path)
    assert turn is not None and turn["prompt"] == "The long question."
    assert turn["assistant_texts"] == ["Thinking aloud.", "The answer."]


def test_last_turn_keeps_rows_holding_raw_line_separators(tmp_path: Path) -> None:
    import repog_runtime

    # Claude Code writes U+2028, U+2029, and U+0085 raw inside JSON strings;
    # a row cut at one of them would hide this turn behind the previous one.
    rows = [
        {"type": "user", "uuid": "u-0", "message": {"content": "The earlier question."}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "The earlier answer."}]}},
        {"type": "user", "uuid": "u-1", "message": {"content": "A pasted line\u2028and its second half."}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "The reply\u2029goes on\u0085here."}]}},
    ]
    path = tmp_path / "separators.jsonl"
    path.write_bytes(("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n").encode("utf-8"))
    turn = repog_runtime.last_turn(path)
    assert turn is not None and turn["prompt_uuid"] == "u-1"
    assert turn["assistant_texts"] == ["The reply\u2029goes on\u0085here."]


def test_runtime_writes_wait_for_a_reader_that_holds_the_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import repog_runtime

    real_replace = os.replace
    refused: list[str] = []

    def busy_once(source, target):  # Windows: the prompt hook is reading the file
        if Path(target).name not in refused:
            refused.append(Path(target).name)
            raise PermissionError(13, "Access is denied", str(target))
        return real_replace(source, target)

    monkeypatch.setattr(os, "replace", busy_once)
    repog_runtime.write_json_atomic(tmp_path / "lint_last.json", {"summary": "clean"})
    repog_runtime.append_jsonl(tmp_path / "lint_history.jsonl", {"words": 3})

    assert refused == ["lint_last.json", "lint_history.jsonl"]
    assert json.loads((tmp_path / "lint_last.json").read_text(encoding="utf-8")) == {"summary": "clean"}
    assert repog_runtime.read_jsonl(tmp_path / "lint_history.jsonl") == [{"words": 3}]
    assert sorted(path.name for path in tmp_path.iterdir()) == ["lint_history.jsonl", "lint_last.json"]


def test_plugin_files_stay_within_the_directory_limits() -> None:
    files = [path for path in PLUGIN.rglob("*") if path.is_file() and "__pycache__" not in path.parts]
    assert len(files) < 512
    oversized = [path.relative_to(PLUGIN).as_posix() for path in files if path.stat().st_size >= 256 * 1024]
    assert oversized == []


@pytest.mark.skipif(SH is None, reason="needs a POSIX sh")
def test_a_cached_interpreter_that_left_path_is_probed_again(tmp_path: Path) -> None:
    data = tmp_path / "plugin-data"
    data.mkdir()
    (data / "python-command").write_bytes(b"repog-no-such-python-3")
    probe = subprocess.run(
        [SH, "-c", '. "$1"; printf "%s" "$PY"', "sh", str(PLUGIN / "scripts" / "hook-python.sh")],
        capture_output=True,
        env={**os.environ, "CLAUDE_PLUGIN_DATA": str(data)},
        timeout=60,
    )
    chosen = probe.stdout.decode("ascii")
    assert chosen and chosen != "repog-no-such-python-3"
    assert (data / "python-command").read_bytes().decode("ascii") == chosen


def test_stop_hook_reads_a_transcript_named_from_the_home_folder(
    campaign: Path, tmp_path: Path, capsysbinary, monkeypatch
) -> None:
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    transcript = _transcript(tmp_path, "I wait at the dock.", "The Witness looks up.")
    transcript.replace(home / ".claude" / "session.jsonl")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    event = {"cwd": str(tmp_path), "session_id": "s-home", "transcript_path": "~/.claude/session.jsonl"}
    _run("stop", event, capsysbinary, monkeypatch)
    # The reply's names reach the next capsule only if the "~" path was read.
    capsule = json.loads(
        _run("prompt", {"cwd": str(tmp_path), "session_id": "s-home", "prompt": "I wait."}, capsysbinary, monkeypatch)
    )["hookSpecificOutput"]["additionalContext"]
    assert "Witness (mentioned)" in capsule


def test_prompt_hook_records_a_rejected_curation(campaign: Path, tmp_path: Path, capsysbinary, monkeypatch) -> None:
    folder = campaign / ".repog-runtime" / "curation"
    folder.mkdir(parents=True)
    staged = folder / "stale-1.json"
    staged.write_bytes(
        json.dumps(
            {
                "curation_id": "stale-1",
                "base_revision": 0,
                "reason": "fold the witness note",
                "base_hashes": {"characters/witness.md": "0" * 64},
                "mutations": [
                    {
                        "path": "characters/witness.md",
                        "ops": [{"op": "replace_section", "heading": "Current State", "text": "Calm."}],
                    }
                ],
            }
        ).encode("utf-8")
    )
    past = time.time() - 60
    os.utime(staged, (past, past))

    _run("prompt", {"cwd": str(tmp_path), "session_id": "s-7", "prompt": "Go on."}, capsysbinary, monkeypatch)

    record = json.loads((folder / "last_result.json").read_text(encoding="utf-8"))
    assert record["rejected"][0]["curation_id"] == "stale-1"
    assert "changed since" in record["rejected"][0]["reasons"][0]


def test_the_run_record_is_never_taken_for_a_proposal(campaign: Path, tmp_path: Path, capsysbinary, monkeypatch) -> None:
    test_prompt_hook_records_a_rejected_curation(campaign, tmp_path, capsysbinary, monkeypatch)
    folder = campaign / ".repog-runtime" / "curation"
    for _ in range(3):
        _run("prompt", {"cwd": str(tmp_path), "session_id": "s-7", "prompt": "Again."}, capsysbinary, monkeypatch)
    record = json.loads((folder / "last_result.json").read_text(encoding="utf-8"))
    assert [item["curation_id"] for item in record["rejected"]] == ["stale-1"]
    assert sorted(path.name for path in (folder / "rejected").iterdir()) == ["stale-1.json"]

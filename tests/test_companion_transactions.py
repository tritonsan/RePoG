"""Companion persistence remains semantic-free, durable and single-writer."""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest

import companion_state as companion
import file_transaction as tx


ROOT = Path(__file__).resolve().parents[1]
NOW = "2026-09-16T12:00:00+03:00"


@pytest.fixture
def campaign(tmp_path):
    state = json.loads((ROOT / "campaign/companion_state.json").read_text(encoding="utf-8"))
    state["configured_utc_offset"] = "+03:00"
    (tmp_path / "companion_state.json").write_text(json.dumps(state), encoding="utf-8")
    (tmp_path / "knowledge_boundaries.md").write_text("# Knowledge\nOriginal.\n", encoding="utf-8")
    (tmp_path / "user_context.md").write_text("# User context\nNo entries.\n", encoding="utf-8")
    (tmp_path / "session_log.md").write_text("# Session Log\n", encoding="utf-8")
    (tmp_path / "characters").mkdir()
    return tmp_path


def read_state(campaign):
    return json.loads((campaign / "companion_state.json").read_text(encoding="utf-8"))


def mutation(campaign, path="knowledge_boundaries.md", text="# Knowledge\nChanged.\n"):
    return {"path": path, "expected_sha256": hashlib.sha256((campaign / path).read_bytes()).hexdigest(), "text": text}


def request(**kwargs):
    return {"operation_id": "semantic-1", "semantic_sequence": 1, "expected_state_revision": 0,
            "expected_continuity_revision": 0, "state_patch": {}, "now_override": NOW, **kwargs}


def enable_view(campaign):
    (campaign / "setup_profile.yaml").write_text("experience_mode: companion\nready_for_play: true\n")
    (campaign / "companion_profile.yaml").write_text("profile_status: locked\ncompanion_view: light\n")
    directory = campaign / "companion_view"
    directory.mkdir()
    view = json.loads((ROOT / "campaign/companion_view/companion_view_state.json").read_text())
    view["enabled"] = True
    view["identity"]["name"] = "Mira"
    (directory / "companion_view_state.json").write_text(json.dumps(view))
    return directory / "companion_view_state.json"


def test_owner_only_change_and_log_marker_share_one_revision_and_replay(campaign):
    original_log = (campaign / "session_log.md").read_bytes()
    marker = {"expected_sha256": hashlib.sha256(original_log).hexdigest(), "text": "### Full review\nKnowledge reconciled."}
    payload = request(owner_mutations=[mutation(campaign)], log_marker=marker)
    result = companion.commit_semantic(campaign, **payload)
    assert result["continuity_revision"] == 1
    assert read_state(campaign)["semantic_operation_sequence"] == 1
    assert (campaign / "knowledge_boundaries.md").read_text() == payload["owner_mutations"][0]["text"]
    assert (campaign / "session_log.md").read_bytes().startswith(original_log)
    log = (campaign / "session_log.md").read_bytes()
    assert companion.commit_semantic(campaign, **payload)["idempotent"]
    assert (campaign / "session_log.md").read_bytes() == log
    payload["owner_mutations"][0]["text"] += "Different."
    with pytest.raises(companion.CompanionStateError, match="different semantic payload"):
        companion.commit_semantic(campaign, **payload)


def test_owner_hash_and_revision_fail_before_any_write(campaign):
    before = {path: path.read_bytes() for path in campaign.iterdir() if path.is_file()}
    payload = request(owner_mutations=[mutation(campaign)])
    payload["owner_mutations"][0]["expected_sha256"] = "0" * 64
    with pytest.raises(companion.CompanionStateError, match="stale owner"):
        companion.commit_semantic(campaign, **payload)
    payload = request(owner_mutations=[mutation(campaign)], expected_state_revision=10)
    with pytest.raises(companion.CompanionStateError, match="stale state"):
        companion.commit_semantic(campaign, **payload)
    assert all(path.read_bytes() == value for path, value in before.items())


@pytest.mark.parametrize("path", ["../outside.md", "play_profile.yaml", "session_log.md", "companion_view/private.md", "snapshots/history.md", "world.md"])
def test_owner_allowlist_refuses_unowned_and_escaping_paths(campaign, path):
    with pytest.raises(companion.CompanionStateError):
        companion.commit_semantic(campaign, **request(owner_mutations=[{"path": path, "expected_sha256": None, "text": "New."}]))
    assert read_state(campaign)["state_revision"] == 0


def test_new_character_note_is_allowed_and_root_creation_is_not(campaign):
    result = companion.commit_semantic(campaign, **request(owner_mutations=[{"path": "characters/mira.md", "expected_sha256": None, "text": "# Mira\nA baker.\n"}]))
    assert result["continuity_revision"] == 1
    assert (campaign / "characters/mira.md").is_file()


def test_marker_alone_does_not_create_fictional_revision(campaign):
    marker = {"expected_sha256": hashlib.sha256((campaign / "session_log.md").read_bytes()).hexdigest(), "text": "Reviewed."}
    with pytest.raises(companion.CompanionStateError, match="requires"):
        companion.commit_semantic(campaign, **request(log_marker=marker))
    assert read_state(campaign)["continuity_revision"] == 0


def test_owner_state_and_view_roll_back_on_filesystem_failure(campaign, monkeypatch):
    view_path = enable_view(campaign)
    before = {path: path.read_bytes() for path in (campaign / "knowledge_boundaries.md", campaign / "companion_state.json", view_path)}
    original = companion._apply_transaction_file
    calls = 0
    def fail_second(path, payload):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected write failure")
        original(path, payload)
    monkeypatch.setattr(companion, "_apply_transaction_file", fail_second)
    with pytest.raises(companion.CompanionStateError, match="rolled back"):
        companion.commit_semantic(campaign, **request(owner_mutations=[mutation(campaign)], public_patch={"identity": {"tagline": "At the bakery"}}, expected_public_surface_revision=0))
    assert all(path.read_bytes() == payload for path, payload in before.items())


def test_private_view_patch_rejected_before_owner_write(campaign):
    view_path = enable_view(campaign)
    before = (campaign / "knowledge_boundaries.md").read_bytes()
    with pytest.raises(companion.CompanionStateError, match="patch rejected"):
        companion.commit_semantic(campaign, **request(owner_mutations=[mutation(campaign)], public_patch={"identity": {"private_memory": "hidden"}}, expected_public_surface_revision=0))
    assert (campaign / "knowledge_boundaries.md").read_bytes() == before
    assert json.loads(view_path.read_text())["public_surface_revision"] == 0


@pytest.mark.parametrize("interrupt_after", [1, 2, 3, 4])
def test_process_exit_mid_semantic_batch_recovers_before_retry(campaign, interrupt_after):
    view_path = enable_view(campaign)
    payload = request(owner_mutations=[mutation(campaign)], public_patch={"identity": {"tagline": "At the bakery"}}, expected_public_surface_revision=0)
    payload["log_marker"] = {"expected_sha256": hashlib.sha256((campaign / "session_log.md").read_bytes()).hexdigest(), "text": "Synthetic atomic semantic marker"}
    script = '''import sys, os, json
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0, sys.argv[1])
import companion_state as companion
original=companion._apply_transaction_file
calls=0
def interrupt(path, payload):
    global calls
    original(path, payload)
    calls+=1
    if calls == int(sys.argv[4]):
        os._exit(75)
companion._apply_transaction_file=interrupt
companion.commit_semantic(Path(sys.argv[2]), **json.loads(sys.argv[3]))
'''
    process = subprocess.run([sys.executable, "-B", "-c", script, str(ROOT / "tools"), str(campaign), json.dumps(payload), str(interrupt_after)], capture_output=True, text=True, timeout=15)
    assert process.returncode == 75, process.stderr
    with pytest.raises(companion.CompanionStateError, match="interrupted transaction"):
        companion.inspect(campaign, now_override=NOW)
    result = companion.commit_semantic(campaign, **payload)
    assert not result["idempotent"]
    assert result["continuity_revision"] == 1
    assert json.loads(view_path.read_text())["public_surface_revision"] == 1
    assert (campaign / "session_log.md").read_text().count("Synthetic atomic semantic marker") == 1


def test_same_revision_overlapping_exchange_cannot_both_succeed(campaign, monkeypatch):
    entered = threading.Event()
    release = threading.Event()
    original = companion._atomic_write
    def delayed_write(path, data):
        entered.set()
        assert release.wait(timeout=5)
        original(path, data)
    monkeypatch.setattr(companion, "_atomic_write", delayed_write)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(companion.begin_exchange, campaign, operation_id="contact-1", expected_state_revision=0, now_override=NOW)
        assert entered.wait(timeout=5)
        second = pool.submit(companion.begin_exchange, campaign, operation_id="contact-2", expected_state_revision=0, now_override=NOW)
        try:
            with pytest.raises(companion.CompanionStateError, match="transaction_busy"):
                second.result(timeout=5)
        finally:
            release.set()
        assert first.result(timeout=5)["ok"]
    state = read_state(campaign)
    assert state["state_revision"] == 1
    assert state["recent_operation_ids"] == ["contact-1"]

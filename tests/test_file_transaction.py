"""Exercise actual interrupted processes and guarded filesystem recovery."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import file_transaction as tx
import agent_seat
import session_zero_state
import snapshot
import world_voices


TOOLS = Path(__file__).resolve().parents[1] / "tools"


def child(root: Path, source: str) -> subprocess.CompletedProcess:
    header = f"import sys, os\nfrom pathlib import Path\nsys.dont_write_bytecode=True\nsys.path.insert(0, {str(TOOLS)!r})\nroot=Path({str(root)!r})\n"
    return subprocess.run([sys.executable, "-B", "-c", header + source], capture_output=True, text=True, timeout=15)


def interrupt_batch(root: Path) -> Path:
    (root / "a.md").write_bytes(b"before a")
    (root / "b.md").write_bytes(b"before b")
    result = child(root, '''import file_transaction as tx
def interrupt(path, payload):
    tx.atomic_bytes(path, payload)
    os._exit(71)
with tx.campaign_lock(root):
    tx.commit_files(root, {"a.md":b"after a", "b.md":b"after b"}, apply_file=interrupt)
''')
    assert result.returncode == 71, result.stderr
    return next((root / tx.TRANSACTION_DIR / tx.JOURNAL_DIR).iterdir())


def test_process_exit_restores_prepared_batch_and_releases_lock(tmp_path):
    interrupt_batch(tmp_path)
    assert (tmp_path / "a.md").read_bytes() == b"after a"
    with tx.campaign_lock(tmp_path):
        assert len(tx.recover(tmp_path)) == 1
    assert (tmp_path / "a.md").read_bytes() == b"before a"
    assert (tmp_path / "b.md").read_bytes() == b"before b"


def test_snapshot_refuses_pending_batch_and_excludes_idle_lock(tmp_path):
    interrupt_batch(tmp_path)
    assert snapshot.create_snapshot(tmp_path, "pending")["error"] == "rpg_transaction_pending"
    with tx.campaign_lock(tmp_path):
        tx.recover(tmp_path)
    result = snapshot.create_snapshot(tmp_path, "recovered")
    assert result["ok"]
    copied = json.loads((Path(result["snapshot_path"]) / "snapshot_manifest.json").read_text())["files"]
    assert not any(path.startswith(tx.TRANSACTION_DIR) for path in copied)


def test_live_lock_is_not_removed_and_reentrant_lock_is_safe(tmp_path):
    with tx.campaign_lock(tmp_path):
        with tx.campaign_lock(tmp_path):
            result = child(tmp_path, '''import file_transaction as tx
try:
    with tx.campaign_lock(root): pass
except tx.FileTransactionError as exc:
    print(exc.category)
''')
            assert result.returncode == 0, result.stderr
            assert result.stdout.strip() == "transaction_busy"
    with tx.campaign_lock(tmp_path):
        pass


def test_recovery_checks_every_target_before_rollback(tmp_path):
    interrupt_batch(tmp_path)
    (tmp_path / "b.md").write_bytes(b"independent later edit")
    with tx.campaign_lock(tmp_path), pytest.raises(tx.FileTransactionError, match="independently"):
        tx.recover(tmp_path)
    assert (tmp_path / "a.md").read_bytes() == b"after a"
    assert (tmp_path / "b.md").read_bytes() == b"independent later edit"


@pytest.mark.parametrize("corruption", ["payload", "hash", "path", "duplicate"])
def test_corrupt_journal_is_refused_without_writing_targets(tmp_path, corruption):
    journal = interrupt_batch(tmp_path)
    manifest_path = journal / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if corruption == "payload":
        (journal / "00000.before").write_bytes(b"corrupt")
    elif corruption == "hash":
        manifest["targets"][0]["before"] = "not a digest"
    elif corruption == "path":
        manifest["targets"][0]["path"] = "../escaped.md"
    else:
        manifest["targets"][1]["path"] = "a.md"
    manifest_path.write_text(json.dumps(manifest))
    with tx.campaign_lock(tmp_path), pytest.raises(tx.FileTransactionError):
        tx.recover(tmp_path)
    assert (tmp_path / "a.md").read_bytes() == b"after a"
    assert not (tmp_path.parent / "escaped.md").exists()


def test_committed_journal_cleanup_keeps_committed_contents(tmp_path, monkeypatch):
    original = tx.shutil.rmtree
    with tx.campaign_lock(tmp_path):
        monkeypatch.setattr(tx.shutil, "rmtree", lambda path: (_ for _ in ()).throw(OSError("cleanup failed")))
        tx.commit_files(tmp_path, {"a.md": b"committed"})
        monkeypatch.setattr(tx.shutil, "rmtree", original)
        assert len(tx.recover(tmp_path)) == 1
        assert (tmp_path / "a.md").read_bytes() == b"committed"


def test_committed_journal_refuses_independent_edit(tmp_path, monkeypatch):
    original = tx.shutil.rmtree
    with tx.campaign_lock(tmp_path):
        monkeypatch.setattr(tx.shutil, "rmtree", lambda path: (_ for _ in ()).throw(OSError("cleanup failed")))
        tx.commit_files(tmp_path, {"a.md": b"committed"})
        monkeypatch.setattr(tx.shutil, "rmtree", original)
        (tmp_path / "a.md").write_bytes(b"later independent edit")
        with pytest.raises(tx.FileTransactionError, match="independently"):
            tx.recover(tmp_path)
        assert (tmp_path / "a.md").read_bytes() == b"later independent edit"


def test_lock_probe_is_read_only(tmp_path):
    assert not tx.is_locked(tmp_path)
    assert not list(tmp_path.iterdir())
    with tx.campaign_lock(tmp_path):
        assert tx.is_locked(tmp_path)
        result = child(tmp_path, "import file_transaction as tx\nprint(tx.is_locked(root))\n")
        assert result.stdout.strip() == "True"
    assert not tx.is_locked(tmp_path)


def test_non_rpg_writer_refuses_pending_legacy_journal(tmp_path):
    with tx.campaign_lock(tmp_path):
        legacy = tmp_path / tx.TRANSACTION_DIR / ("a" * 24)
        legacy.mkdir()
        with pytest.raises(tx.FileTransactionError, match="legacy RPG"):
            tx.recover(tmp_path)
        assert tx.recover(tmp_path, allow_legacy=True) == []


def test_batch_create_delete_and_exception_rollback(tmp_path):
    (tmp_path / "old.md").write_bytes(b"old")
    with tx.campaign_lock(tmp_path):
        tx.commit_files(tmp_path, {"old.md": None, "new.md": b"new"})
        assert not (tmp_path / "old.md").exists()
        def fail_validation():
            raise ValueError("bad candidate")
        with pytest.raises(tx.FileTransactionError, match="rolled back"):
            tx.commit_files(tmp_path, {"new.md": b"wrong", "another.md": b"created"}, validate_applied=fail_validation)
    assert (tmp_path / "new.md").read_bytes() == b"new"
    assert not (tmp_path / "another.md").exists()


@pytest.mark.parametrize("path", ["../escape.md", "a/../escape.md", "/absolute.md", "C:/drive.md", "nested:stream.md", ".repog-transactions/evil", "snapshots/old.md"])
def test_protected_and_escaping_paths_rejected(tmp_path, path):
    with tx.campaign_lock(tmp_path), pytest.raises(tx.FileTransactionError):
        tx.commit_files(tmp_path, {path: b"no"})


def test_symlink_target_rejected(tmp_path):
    (tmp_path / "real.md").write_bytes(b"real")
    try:
        (tmp_path / "alias.md").symlink_to(tmp_path / "real.md")
    except OSError:
        pytest.skip("host does not grant symlink creation")
    with tx.campaign_lock(tmp_path), pytest.raises(tx.FileTransactionError):
        tx.commit_files(tmp_path, {"alias.md": b"changed"})
    assert (tmp_path / "real.md").read_bytes() == b"real"


@pytest.mark.skipif(os.name != "nt", reason="Windows junction guard")
def test_transaction_junction_cannot_redirect_storage(tmp_path):
    root = tmp_path / "campaign"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    link = root / tx.TRANSACTION_DIR
    result = subprocess.run(["cmd", "/d", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True, text=True)
    if result.returncode:
        pytest.skip("host does not allow directory junction creation")
    try:
        with pytest.raises(tx.FileTransactionError, match="links"):
            with tx.campaign_lock(root):
                pass
        assert not list(outside.iterdir())
    finally:
        link.rmdir()  # Removes only the verified test junction, not its target.


def test_read_guard_reports_pending_batch_without_mutation(tmp_path):
    journal = interrupt_batch(tmp_path)
    before = {path: path.read_bytes() for path in journal.iterdir() if path.is_file()}
    with pytest.raises(tx.FileTransactionError, match="interrupted transaction"):
        tx.assert_readable(tmp_path)
    assert all(path.read_bytes() == payload for path, payload in before.items())
    path = tmp_path / "agent_seat_state.json"
    path.write_text(json.dumps(agent_seat.initial_state()))
    with pytest.raises(agent_seat.AgentSeatError, match="interrupted transaction"):
        agent_seat.get_next_turn(path)
    with pytest.raises(session_zero_state.StateError, match="interrupted transaction"):
        session_zero_state._assert_readable_state(tmp_path)


@pytest.mark.parametrize("interrupt_after", [1, 2, 3])
def test_session_zero_bundle_recovers_after_process_exit(tmp_path, interrupt_after):
    for name in ("setup_profile.yaml", "session_zero.md", "session_zero_state.json"):
        (tmp_path / name).write_bytes(b"original")
    result = child(tmp_path, f"interrupt_after={interrupt_after}\n" + '''import session_zero_state as state
original=state._atomic_bytes
calls=0
def interrupt(path, payload):
    global calls
    original(path, payload)
    calls+=1
    if calls == interrupt_after:
        os._exit(72)
state._atomic_bytes=interrupt
with state._mutation_lock(root):
    state._atomic_bundle(root/"session_zero_state.json", {"revision":1}, root/"setup_profile.yaml", "new setup", root/"session_zero.md", "new summary")
''')
    assert result.returncode == 72, result.stderr
    with session_zero_state._mutation_lock(tmp_path):
        assert all((tmp_path / name).read_bytes() == b"original" for name in ("setup_profile.yaml", "session_zero.md", "session_zero_state.json"))


@pytest.mark.parametrize("interrupt_after", [1, 2])
def test_world_voices_bundle_recovers_after_process_exit(tmp_path, interrupt_after):
    directory = tmp_path / "world_voices"
    directory.mkdir()
    (directory / "index.json").write_bytes(b"original index")
    (directory / "note.md").write_bytes(b"original body")
    result = child(tmp_path, f"interrupt_after={interrupt_after}\n" + '''import world_voices as voices
original=voices._atomic_bytes
calls=0
def interrupt(path, payload):
    global calls
    original(path, payload)
    calls+=1
    if calls == interrupt_after:
        os._exit(73)
voices._atomic_bytes=interrupt
voices._commit({root/"world_voices"/"note.md":b"new body",root/"world_voices"/"index.json":b"new index"})
''')
    assert result.returncode == 73, result.stderr
    with tx.campaign_lock(tmp_path):
        tx.recover(tmp_path)
    assert (directory / "index.json").read_bytes() == b"original index"
    assert (directory / "note.md").read_bytes() == b"original body"


def test_agent_seat_interruption_does_not_leave_stale_lock(tmp_path):
    path = tmp_path / "agent_seat_state.json"
    path.write_text(json.dumps(agent_seat.initial_state()), encoding="utf-8")
    result = child(tmp_path, '''import agent_seat
agent_seat._update(root/"agent_seat_state.json",lambda state: os._exit(74))
''')
    assert result.returncode == 74, result.stderr
    assert agent_seat._update(path, lambda state: {"ok": True, "idempotent": True})["ok"]


def test_legacy_sentinel_requires_explicit_inspection(tmp_path):
    (tmp_path / ".session-zero-state.lock").write_text("old process")
    with pytest.raises(session_zero_state.StateError, match=".session-zero-state.lock"):
        with session_zero_state._mutation_lock(tmp_path):
            pass
    path = tmp_path / "agent_seat_state.json"
    path.write_text(json.dumps(agent_seat.initial_state()))
    (tmp_path / ".agent_seat_state.json.lock").write_text("")
    with pytest.raises(agent_seat.AgentSeatError, match=".agent_seat_state.json.lock"):
        agent_seat._update(path, lambda state: {"idempotent": True})

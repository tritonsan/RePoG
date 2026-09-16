"""Small local file transactions; no campaign semantics or external services.

Hold ``campaign_lock`` across recovery, reads, revision checks and commit. The
OS owns the lock, so process exit releases it without PID probes or stale-file
deletion. A prepared journal rolls back after interruption; a committed journal
is verified before cleanup. Recovery never overwrites an unrelated later edit.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import threading
import uuid
from pathlib import Path, PurePosixPath
from typing import Callable, Iterator, Mapping


TRANSACTION_DIR = ".repog-transactions"
JOURNAL_DIR = "files"
LOCK_FILE = ".writer.lock"
MAX_TARGETS = 12_000  # Includes bounded World Voices projection documents.
_HELD = threading.local()
_HASH = re.compile(r"^[0-9a-f]{64}$")


class FileTransactionError(Exception):
    def __init__(self, category: str, reason: str) -> None:
        super().__init__(reason)
        self.category = category


def _root(root: Path) -> Path:
    root = Path(root).resolve()
    if not root.is_dir():
        raise FileTransactionError("path_forbidden", "transaction root must be an existing directory")
    return root


def _regular(path: Path) -> None:
    try:
        reparse = bool(getattr(path.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except FileNotFoundError:
        reparse = False
    if reparse or path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        raise FileTransactionError("path_forbidden", f"transaction paths cannot use links: {path.name}")


def _internal(root: Path, *parts: str) -> Path:
    path = root
    for part in (TRANSACTION_DIR, *parts):
        path = path / part
        _regular(path)
    if path.exists() and not path.is_dir():
        raise FileTransactionError("recovery_required", "transaction storage is not a directory")
    return path


def target_path(root: Path, value: str | Path) -> tuple[str, Path]:
    """Validate a literal campaign-relative target, including every ancestor."""
    root = _root(root)
    if isinstance(value, Path):
        if value.is_absolute():
            try:
                value = value.relative_to(root).as_posix()
            except ValueError as exc:
                raise FileTransactionError("path_forbidden", "target is outside transaction root") from exc
        else:
            value = value.as_posix()
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise FileTransactionError("path_forbidden", "target must be a relative POSIX path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} or ":" in part for part in parts):
        raise FileTransactionError("path_forbidden", "target must remain inside the campaign")
    pure = PurePosixPath(value)
    if pure.is_absolute() or pure.parts[0] in {TRANSACTION_DIR, "snapshots", ".git"}:
        raise FileTransactionError("path_forbidden", "target addresses protected transaction or recovery storage")
    path = root
    for part in parts:
        path = path / part
        _regular(path)
    try:
        path.resolve().relative_to(root)
    except ValueError as exc:
        raise FileTransactionError("path_forbidden", "target escapes the campaign") from exc
    if path.exists() and not path.is_file():
        raise FileTransactionError("path_forbidden", "transaction target must be a regular file")
    return value, path


@contextlib.contextmanager
def campaign_lock(root: Path) -> Iterator[None]:
    root = _root(root)
    key = os.path.normcase(str(root))
    held = getattr(_HELD, "roots", None)
    if held is None:
        held = _HELD.roots = set()
    if key in held:
        yield
        return
    storage = _internal(root)
    storage.mkdir(exist_ok=True)
    lock_path = storage / LOCK_FILE
    _regular(lock_path)
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(lock_path, flags, 0o600)
    locked = False
    try:
        if os.fstat(fd).st_size == 0:
            os.write(fd, b"\0")
        os.lseek(fd, 0, os.SEEK_SET)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise FileTransactionError("transaction_busy", "another campaign operation holds the writer lock") from exc
        locked = True
        held.add(key)
        yield
    finally:
        try:
            if locked:
                held.discard(key)
                os.lseek(fd, 0, os.SEEK_SET)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
        # Never unlink an advisory lock: waiters must keep the same inode.


def _require_lock(root: Path) -> None:
    if os.path.normcase(str(root)) not in getattr(_HELD, "roots", set()):
        raise FileTransactionError("transaction_unlocked", "hold campaign_lock across reads, checks and writes")


def is_locked(root: Path) -> bool:
    """Probe the writer lock without creating or deleting any filesystem entry."""
    root = _root(root)
    if os.path.normcase(str(root)) in getattr(_HELD, "roots", set()):
        return True
    lock_path = _internal(root) / LOCK_FILE
    _regular(lock_path)
    try:
        descriptor = os.open(lock_path, os.O_RDWR | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    except FileNotFoundError:
        return False
    try:
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        except OSError:
            return True
        return False
    finally:
        os.close(descriptor)


def assert_readable(root: Path, *, check_lock: bool = True) -> None:
    """Refuse interrupted batches without changing files or recovering on reads."""
    root = _root(root)
    if os.path.normcase(str(root)) in getattr(_HELD, "roots", set()):
        return  # Mutators have already recovered while holding this lock.
    if check_lock and is_locked(root):
        raise FileTransactionError("transaction_busy", "campaign writer is active; retry the read after it finishes")
    storage = _internal(root)
    if not storage.exists():
        return
    for path in storage.iterdir():
        if path.name == LOCK_FILE:
            continue
        if path.name == JOURNAL_DIR:
            directory = _internal(root, JOURNAL_DIR)
            if directory.exists() and not any(directory.iterdir()):
                continue
        raise FileTransactionError("recovery_required", "campaign has an interrupted transaction; retry the original mutation before reading state")


def _hash(data: bytes | None) -> str | None:
    return hashlib.sha256(data).hexdigest() if data is not None else None


def atomic_bytes(path: Path, payload: bytes | None) -> None:
    if payload is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _json_bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _validated_journal(root: Path, journal: Path) -> tuple[dict, list[tuple[Path, bytes | None, bytes | None]]]:
    _regular(journal)
    manifest_path = journal / "manifest.json"
    _regular(manifest_path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FileTransactionError("recovery_required", f"cannot read transaction {journal.name}") from exc
    if not isinstance(manifest, dict) or manifest.get("version") != 1 or manifest.get("status") not in {"prepared", "committed"}:
        raise FileTransactionError("recovery_required", "transaction manifest is invalid")
    records = manifest.get("targets")
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_TARGETS:
        raise FileTransactionError("recovery_required", "transaction target list is invalid")
    targets = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict) or set(record) != {"path", "before", "after"}:
            raise FileTransactionError("recovery_required", "transaction target record is invalid")
        relative, target = target_path(root, record["path"])
        normalized = os.path.normcase(str(target))
        if normalized in seen:
            raise FileTransactionError("recovery_required", "duplicate transaction target")
        seen.add(normalized)
        payloads = []
        for family in ("before", "after"):
            expected = record[family]
            if expected is None:
                payloads.append(None)
                continue
            if not isinstance(expected, str) or not _HASH.fullmatch(expected):
                raise FileTransactionError("recovery_required", "transaction hash is invalid")
            stored = journal / f"{index:05d}.{family}"
            _regular(stored)
            try:
                data = stored.read_bytes()
            except OSError as exc:
                raise FileTransactionError("recovery_required", "transaction payload is missing") from exc
            if _hash(data) != expected:
                raise FileTransactionError("recovery_required", "transaction payload hash does not match")
            payloads.append(data)
        current = target.read_bytes() if target.exists() else None
        allowed = {record["after"]} if manifest["status"] == "committed" else {record["before"], record["after"]}
        if _hash(current) not in allowed:
            raise FileTransactionError("recovery_required", f"transaction target changed independently: {relative}")
        targets.append((target, payloads[0], payloads[1]))
    return manifest, targets


def recover(root: Path, *, allow_legacy: bool = False) -> list[str]:
    root = _root(root)
    _require_lock(root)
    legacy = [path.name for path in _internal(root).iterdir() if path.name not in {LOCK_FILE, JOURNAL_DIR}]
    if legacy and not allow_legacy:
        raise FileTransactionError("recovery_required", "unfinished legacy RPG transaction requires RPG recovery: " + ", ".join(sorted(legacy)))
    storage = _internal(root, JOURNAL_DIR)
    if not storage.exists():
        return []
    recovered = []
    for journal in sorted(storage.iterdir()):
        _regular(journal)
        if not journal.is_dir() or not re.fullmatch(r"[0-9a-f]{32}", journal.name):
            raise FileTransactionError("recovery_required", "unexpected entry in transaction storage")
        if not (journal / "manifest.json").exists():
            # No target is touched until the prepared manifest is durable.
            shutil.rmtree(journal)
            continue
        manifest, targets = _validated_journal(root, journal)
        if manifest["status"] == "prepared":
            for target, before, _ in targets:
                atomic_bytes(target, before)
        shutil.rmtree(journal)
        recovered.append(journal.name)
    return recovered


def commit_files(
    root: Path,
    changes: Mapping[str | Path, bytes | None],
    *,
    apply_file: Callable[[Path, bytes | None], None] | None = None,
    validate_applied: Callable[[], None] | None = None,
) -> None:
    root = _root(root)
    _require_lock(root)
    if not changes or len(changes) > MAX_TARGETS:
        raise FileTransactionError("input_invalid", "transaction needs a bounded nonempty file batch")
    targets = []
    seen = set()
    for relative, payload in changes.items():
        relative, target = target_path(root, relative)
        key = os.path.normcase(str(target))
        if key in seen or (payload is not None and not isinstance(payload, bytes)):
            raise FileTransactionError("input_invalid", "transaction targets must be unique byte payloads")
        seen.add(key)
        targets.append((relative, target, target.read_bytes() if target.exists() else None, payload))
    storage = _internal(root, JOURNAL_DIR)
    storage.mkdir(parents=True, exist_ok=True)
    if any(storage.iterdir()):
        raise FileTransactionError("recovery_required", "recover pending transactions before writing")
    journal = storage / uuid.uuid4().hex
    journal.mkdir()
    manifest = {"version": 1, "status": "prepared", "targets": []}
    try:
        for index, (relative, _, before, after) in enumerate(targets):
            for family, payload in (("before", before), ("after", after)):
                if payload is not None:
                    atomic_bytes(journal / f"{index:05d}.{family}", payload)
            manifest["targets"].append({"path": relative, "before": _hash(before), "after": _hash(after)})
        atomic_bytes(journal / "manifest.json", _json_bytes(manifest))
    except BaseException:
        shutil.rmtree(journal, ignore_errors=True)
        raise
    try:
        for _, target, _, after in targets:
            (apply_file or atomic_bytes)(target, after)
        if validate_applied is not None:
            validate_applied()
        atomic_bytes(journal / "manifest.json", _json_bytes({**manifest, "status": "committed"}))
    except Exception as exc:
        try:
            # Strict checks avoid overwriting external edits even on rollback.
            _, checked = _validated_journal(root, journal)
            for target, before, _ in checked:
                atomic_bytes(target, before)
            shutil.rmtree(journal)
        except Exception as rollback_exc:
            raise FileTransactionError("recovery_required", f"commit failed; rollback needs recovery: {exc}; {rollback_exc}") from exc
        raise FileTransactionError("commit_rolled_back", f"file transaction failed and rolled back: {exc}") from exc
    try:
        shutil.rmtree(journal)
    except OSError:
        pass  # A committed journal is verified and cleaned on the next entry.

"""Staged boundary curation: the file contract between the curator and the writer.

At a full distill or an act/skip boundary the coordinator may hand a frozen
packet to the `repog-curator` agent. The agent reads the target notes and
writes exactly one staging file, `campaign/.repog-runtime/curation/<id>.json`,
holding typed Markdown edits plus the sha256 of each target as it read it. The
deterministic writer (`rpg_state.py commit-curation`) applies a staged edit
only while its target still has that hash, so a note that changed after the
proposal was written is never overwritten with stale text.

This module is semantic-free. It checks the staging file's shape and paths,
compares hashes, lists and files away processed proposals, and builds the
packet. It never decides what a note should say, and it writes no campaign
owner itself.

CLI:
    python tools/curation.py packet <campaign> --target PATH[=REASON] ... [--id ID]
    python tools/curation.py validate <campaign> [STAGED_FILE ...]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

import owner_ops
from repog_runtime import RUNTIME_DIR, runtime_settings, state_summary


CURATION_DIR = "curation"
OUTCOMES = ("applied", "rejected")
PAYLOAD_KEYS = frozenset({"curation_id", "base_revision", "reason", "base_hashes", "mutations"})
MUTATION_KEYS = frozenset({"path", "ops"})
CURATION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_MUTATIONS = 32  # the writer's per-transaction mutation cap
MAX_BASE_HASHES = 2 * MAX_MUTATIONS
MAX_NOTE_TEXT = 500_000  # the writer's per-file cap (rpg_state.MAX_FILE_TEXT)
MAX_PATH_TEXT = 400  # the writer's cap on one campaign-relative path
MAX_REASON = 300
MAX_STAGED_BYTES = 2_000_000
# A real payload nests about six levels (payload, mutations, mutation, ops,
# op, cells). Anything far deeper is refused before a recursive walk (here or
# in the writer) can hit Python's recursion limit.
MAX_DEPTH = 16
HASH_CHUNK = 1 << 20
# Every active directive constrains the curator, so the packet carries them
# all up to this generous cap and reports any it had to leave out.
MAX_DIRECTIVES = 100
DIRECTIVE_COLUMNS = ("id", "scope", "directive", "status")

# Curation follows the distill path rules: Markdown only, never the writer's
# session log, archived history, recovery snapshots, or any hidden working
# folder (runtime files, transaction journals, version control). Directives
# are the Player's own words and change only through an OOC request.
SYSTEM_MANAGED_FILES = frozenset({"session_log.md"})
PLAYER_OWNED_FILES = frozenset({"directives.md"})
FORBIDDEN_TOP_DIRS = frozenset({"archive", "snapshots"})

# The keys the writer reads for each Markdown op. The writer ignores any other
# key, so a typo such as `parent` for `under` would silently move an edit.
MARKDOWN_OP_KEYS: dict[str, frozenset[str]] = {
    "append": frozenset({"heading", "under", "text"}),
    "replace_section": frozenset({"heading", "under", "text"}),
    "remove_section": frozenset({"heading", "under"}),
    "insert_section": frozenset({"heading", "under", "text"}),
    "upsert_row": frozenset({"heading", "under", "table", "key", "cells"}),
    "delete_row": frozenset({"heading", "under", "table", "key"}),
    "replace": frozenset({"old", "new"}),
}

# The full check reads `As of revision:` stamps case-insensitively and across
# whitespace (check_state._markdown_revision), so proposals are compared under
# that broader reading, not only the writer's exact one.
STAMP_RE = re.compile(r"(?im)^As of revision:\s*(\d+)\s*$")


class CurationError(Exception):
    """A curation request that cannot be carried out as given."""

    def __init__(self, category: str, reason: str) -> None:
        super().__init__(reason)
        self.category = category


# ---------------------------------------------------------------------------
# Hashes and paths
# ---------------------------------------------------------------------------


def file_hash(path: Path) -> str:
    """The sha256 hex digest of a file's exact bytes (read in chunks)."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(HASH_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _current_hash(path: Path) -> str | None:
    try:
        return file_hash(path)
    except (OSError, ValueError):
        return None


def _has_control(text: str) -> bool:
    """True when text holds a control character or a Unicode line break.

    `str.splitlines()` (and so the writer's Markdown parser) also breaks lines
    at \\x0b, \\x0c, \\x1c-\\x1e, \\x85, U+2028, and U+2029, so a "one line" value
    must hold none of them. A tab is allowed.
    """

    return any(
        (unicodedata.category(char) == "Cc" and char != "\t") or char in "\u2028\u2029" for char in text
    )


def _encodable(text: str) -> bool:
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _shape_error(value: Any, label: str = "staged payload") -> str | None:
    """Why `value` cannot be checked or written safely, or None.

    JSON allows nesting deep enough to exhaust Python's recursion limit and
    `\\ud800`-style escapes that decode to lone surrogates, which the writer
    cannot encode as UTF-8. Either would crash the writer instead of getting
    the file rejected, so both are refused here, with an iterative walk.
    """

    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        if depth > MAX_DEPTH:
            return f"{label} nests deeper than {MAX_DEPTH} levels"
        if isinstance(item, str):
            if not _encodable(item):
                return f"{label} holds text with a lone surrogate (an unpaired \\ud800-\\udfff escape)"
        elif isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    return f"{label} has a key that is not text: {key!r}"
                if not _encodable(key):
                    return f"{label} has a key with a lone surrogate"
                stack.append((child, depth + 1))
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
    return None


def _same_file_key(path: str) -> str:
    """One key per file whatever the spelling, where file systems fold case or normalization."""

    return unicodedata.normalize("NFC", path).casefold()


def _normalize_hash(value: Any) -> str | None:
    """Accept a bare hex digest or one prefixed `sha256:`; None when malformed."""

    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if text.startswith("sha256:"):
        text = text[len("sha256:") :]
    return text if HASH_RE.fullmatch(text) else None


def _rule_error(pure: PurePosixPath) -> str | None:
    """The allowed-set rules for one canonical campaign-relative path."""

    if pure.suffix != ".md":
        if pure.suffix.lower() == ".md":
            return "must end in lowercase '.md', the only Markdown suffix the writer edits"
        return "must be a Markdown note; curation never edits YAML, JSON, or other files"
    relative = pure.as_posix().casefold()
    if relative in SYSTEM_MANAGED_FILES:
        return "is written only by the writer"
    if relative in PLAYER_OWNED_FILES:
        return "holds the Player's directives, which change only through an OOC request"
    if pure.parts[0].casefold() in FORBIDDEN_TOP_DIRS:
        return f"is in {pure.parts[0]}/, which holds history, not live notes"
    if any(part.startswith(".") for part in pure.parts):
        return "is in a hidden or runtime folder"
    return None


def path_error(campaign: Path, value: Any) -> str | None:
    """Why `value` is not an allowed curation target, or None when it is.

    The rules are checked on the path as written and again on the file it
    resolves to, so a link, a Windows short name (`SESSIO~1.MD`), or a case
    variant cannot reach a forbidden file. A path that resolves to a different
    spelling must be written the way the file is actually named, so two
    spellings can never address one file.
    """

    if not isinstance(value, str) or not value.strip():
        return "must be a campaign-relative path"
    if value != value.strip():
        return "must not start or end with spaces"
    if len(value) > MAX_PATH_TEXT:
        return f"must be at most {MAX_PATH_TEXT} characters, the writer's limit"
    if "\\" in value or _has_control(value):
        return "must be a one-line campaign-relative POSIX path"
    pure = PurePosixPath(value)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        return "must stay inside the campaign folder"
    if ":" in value:
        return "must not contain ':' (a drive or URI prefix, or a Windows stream name)"
    if pure.as_posix() != value:
        return f"must be written as '{pure.as_posix()}'"
    if any(part != part.rstrip(" .") for part in pure.parts):
        return "must not end a folder or file name with a space or a dot"
    problem = _rule_error(pure)
    if problem:
        return problem
    root = campaign.resolve()
    try:
        resolved = (root / Path(*pure.parts)).resolve().relative_to(root)
    except (OSError, ValueError):
        return "escapes the campaign folder"
    canonical = resolved.as_posix()
    if not resolved.parts:
        return "must name a file inside the campaign folder"
    if canonical != value:
        problem = _rule_error(PurePosixPath(canonical))
        if problem:
            return f"resolves to '{canonical}', which {problem}"
        return f"must be written as '{canonical}', the file's own spelling"
    return None


def _target(campaign: Path, relative: str) -> Path:
    return campaign / Path(*PurePosixPath(relative).parts)


# ---------------------------------------------------------------------------
# Staging files
# ---------------------------------------------------------------------------


def curation_dir(campaign: Path) -> Path:
    return campaign / RUNTIME_DIR / CURATION_DIR


def staging_path(campaign: Path, curation_id: str) -> Path:
    if not isinstance(curation_id, str) or CURATION_ID_RE.fullmatch(curation_id) is None:
        raise CurationError("input_invalid", f"curation id {curation_id!r} must match {CURATION_ID_RE.pattern}")
    return curation_dir(campaign) / f"{curation_id}.json"


def is_staging_path(campaign: Path, path: str | Path, curation_id: str | None = None) -> bool:
    """True only for `<campaign>/.repog-runtime/curation/<valid id>.json`.

    Lets a write guard confine the curator to the one file it may create; pass
    the packet's `curation_id` to allow that one name only.
    """

    try:
        candidate = Path(path).resolve()
        folder = curation_dir(campaign).resolve()
    except (OSError, ValueError):
        return False
    return (
        os.path.normcase(str(candidate.parent)) == os.path.normcase(str(folder))
        and candidate.suffix == ".json"
        and CURATION_ID_RE.fullmatch(candidate.stem) is not None
        and (curation_id is None or candidate.stem == curation_id)
    )


def list_staged(campaign: Path) -> list[Path]:
    """Staged files waiting to be processed, oldest first."""

    folder = curation_dir(campaign)
    try:
        entries = [
            entry
            for entry in folder.iterdir()
            if entry.is_file() and entry.suffix == ".json" and not entry.name.startswith(".")
        ]
    except OSError:
        return []

    def age(entry: Path) -> tuple[int, str]:
        try:
            return entry.stat().st_mtime_ns, entry.name
        except OSError:
            return 0, entry.name

    return sorted(entries, key=age)


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise CurationError("input_invalid", f"staged file repeats the key '{key}'; JSON keys must be unique")
        value[key] = item
    return value


def read_staged(path: Path) -> dict[str, Any]:
    """Read one staging file: UTF-8 JSON (a BOM is tolerated), unique keys, one object.

    Every way a file can fail to load raises `CurationError`, never a bare
    `ValueError` or `RecursionError`, so the writer can file a broken proposal
    under `rejected/` instead of tripping over it on every later run.
    """

    try:
        with Path(path).open("rb") as stream:
            raw = stream.read(MAX_STAGED_BYTES + 1)
    except FileNotFoundError as exc:
        raise CurationError("not_found", f"staged file does not exist: {path}") from exc
    except OSError as exc:
        raise CurationError("io_error", f"cannot read staged file {path}: {exc}") from exc
    if len(raw) > MAX_STAGED_BYTES:
        raise CurationError("input_invalid", f"staged file exceeds {MAX_STAGED_BYTES} bytes: {path}")
    try:
        value = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_unique_keys)
    except RecursionError as exc:
        raise CurationError("input_invalid", "staged file nests too deeply to read") from exc
    except ValueError as exc:
        # Undecodable bytes, broken JSON, or a number too long to convert.
        raise CurationError("input_invalid", f"staged file is not UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise CurationError("input_invalid", "staged file must hold one JSON object")
    return value


def move_processed(path: Path, outcome: str) -> Path:
    """Move a processed staging file into `applied/` or `rejected/` next to it.

    Only a `.json` file directly in `.repog-runtime/curation/` can be moved, so
    a wrong path never files a campaign note away. A name already taken there
    gets a `-2`, `-3`, ... suffix, so no record of an earlier proposal is
    overwritten. Returns the new location. Call it under the writer's lock;
    a failing file system operation raises `OSError` unchanged.
    """

    if outcome not in OUTCOMES:
        raise CurationError("input_invalid", f"outcome must be one of: {', '.join(OUTCOMES)}")
    source = Path(path)
    if source.parent.name in OUTCOMES and source.parent.parent.name == CURATION_DIR:
        raise CurationError("input_invalid", f"staged file was already processed: {source}")
    if source.suffix != ".json" or source.parent.name != CURATION_DIR or source.parent.parent.name != RUNTIME_DIR:
        raise CurationError(
            "path_forbidden",
            f"only a staged .json file directly in {RUNTIME_DIR}/{CURATION_DIR}/ can be moved: {source}",
        )
    if not source.is_file():
        raise CurationError("not_found", f"staged file does not exist: {source}")
    folder = source.parent / outcome
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / source.name
    counter = 2
    while target.exists():
        target = folder / f"{source.stem}-{counter}{source.suffix}"
        counter += 1
    os.replace(source, target)
    return target


# ---------------------------------------------------------------------------
# Validation and freshness
# ---------------------------------------------------------------------------


def _check_header(payload: dict[str, Any], errors: list[str]) -> None:
    curation_id = payload.get("curation_id")
    if "curation_id" in payload and (
        not isinstance(curation_id, str) or CURATION_ID_RE.fullmatch(curation_id) is None
    ):
        errors.append(f"curation_id must match {CURATION_ID_RE.pattern}")
    revision = payload.get("base_revision")
    if "base_revision" in payload and (not isinstance(revision, int) or isinstance(revision, bool) or revision < 0):
        errors.append("base_revision must be a non-negative integer")
    reason = payload.get("reason")
    if "reason" in payload:
        # Same rule as the writer's one-line fields: surrounding whitespace,
        # including a trailing line break, is trimmed before the check. The
        # writer copies the reason into the session log, so it must hold no
        # line break of any kind.
        text = reason.strip() if isinstance(reason, str) else ""
        if not text:
            errors.append("reason must be non-empty text")
        elif len(text) > MAX_REASON or _has_control(text):
            errors.append(f"reason must be one line of at most {MAX_REASON} characters")


def _check_hashes(campaign: Path, payload: dict[str, Any], errors: list[str]) -> dict[str, str] | None:
    """Valid base hashes by path, or None when the table is missing or unusable."""

    raw = payload.get("base_hashes")
    if "base_hashes" not in payload:
        return None
    if not isinstance(raw, dict):
        errors.append("base_hashes must be an object of path -> sha256")
        return None
    if len(raw) > MAX_BASE_HASHES:
        errors.append(f"base_hashes lists {len(raw)} files; at most {MAX_BASE_HASHES}")
        return None
    hashes: dict[str, str] = {}
    for path, value in raw.items():
        problem = path_error(campaign, path)
        if problem:
            errors.append(f"base_hashes['{path}'] {problem}")
            continue
        digest = _normalize_hash(value)
        if digest is None:
            errors.append(f"base_hashes['{path}'] must be a 64-character sha256 hex digest")
            continue
        hashes[path] = digest
    return hashes


def _check_mutation(
    campaign: Path,
    raw: Any,
    label: str,
    *,
    hashes: dict[str, str] | None,
    seen: dict[str, str],
    errors: list[str],
) -> None:
    if not isinstance(raw, dict):
        errors.append(f"{label} must be an object with 'path' and 'ops'")
        return
    if "create_text" in raw:
        errors.append(f"{label}: curation cannot create notes; creation is a durable change")
    unknown = sorted(set(raw) - MUTATION_KEYS - {"create_text"})
    if unknown:
        errors.append(f"{label} has unknown key(s): {', '.join(unknown)}; use only 'path' and 'ops'")
    path = raw.get("path")
    problem = path_error(campaign, path)
    if problem:
        errors.append(f"{label}.path {problem}")
        return
    # Where the file system folds case or Unicode normalization, two spellings
    # name one file, and the writer would apply the second edit to stale text.
    key = _same_file_key(path)
    if key in seen:
        errors.append(f"{label}.path '{path}' repeats '{seen[key]}'; put all edits for one file in one mutation")
    seen.setdefault(key, path)
    if hashes is not None and path not in hashes:
        errors.append(f"{label}.path '{path}' has no valid entry in base_hashes")
    try:
        ops = owner_ops.parse_ops(raw.get("ops"), relative=path, label=label)
    except owner_ops.OwnerOpError as exc:
        errors.append(str(exc))
        return
    for position, op in enumerate(ops):
        allowed = MARKDOWN_OP_KEYS.get(op["op"])
        extra = sorted(set(op) - {"op"} - allowed) if allowed is not None else []
        if extra:
            errors.append(
                f"{label}.ops[{position}] has unknown key(s): {', '.join(extra)}; "
                f"{op['op']} takes {', '.join(sorted(allowed or ()))}"
            )
    # Placeholders allocate fact ids or name a revision: both are new truth.
    # Search every text value exactly as the writer will resolve it; a JSON
    # dump would hide `{{\trevision}}` behind an escaped tab.
    if _has_placeholder(raw.get("ops")):
        errors.append(f"{label} uses a {{{{revision}}}} or {{{{next_id}}}} placeholder; curation allocates no ids or revisions")


def _has_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return owner_ops.PLACEHOLDER_RE.search(value) is not None
    if isinstance(value, list):
        return any(_has_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(_has_placeholder(item) for item in value.values())
    return False


def validate_staged(campaign: Path, payload: Any) -> list[str]:
    """Structural errors in a staged payload; an empty list means well formed.

    Checks keys, the curation id, the base revision, the reason, every base
    hash, and every mutation's path, op names, op keys, and absence of
    placeholders. Op addresses are checked by `dry_run`. An empty `mutations`
    list is valid: it records that the curator found nothing it could safely
    change. A payload nested too deeply or holding text the writer cannot
    encode is refused before anything else is checked.
    """

    if not isinstance(payload, dict):
        return ["staged payload must be a JSON object"]
    shape = _shape_error(payload)
    if shape:
        return [shape]
    errors: list[str] = []
    unknown = sorted(set(payload) - PAYLOAD_KEYS)
    if unknown:
        errors.append(f"unknown key(s): {', '.join(unknown)}")
    missing = sorted(PAYLOAD_KEYS - set(payload))
    if missing:
        errors.append(f"missing key(s): {', '.join(missing)}")
    _check_header(payload, errors)
    hashes = _check_hashes(campaign, payload, errors)
    if "mutations" not in payload:
        return errors
    mutations = payload.get("mutations")
    if not isinstance(mutations, list):
        errors.append("mutations must be an array")
        return errors
    if len(mutations) > MAX_MUTATIONS:
        # The file is refused as a whole; checking thousands of entries would
        # only slow the prompt hook that applies staged files.
        errors.append(f"mutations exceeds the limit of {MAX_MUTATIONS}")
        return errors
    seen: dict[str, str] = {}
    for index, raw in enumerate(mutations):
        _check_mutation(campaign, raw, f"mutations[{index}]", hashes=hashes, seen=seen, errors=errors)
    return errors


def split_by_freshness(campaign: Path, payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Split mutations into those whose target is unchanged and stale paths.

    A mutation is fresh only when its target exists and its current sha256
    equals the staged base hash. A changed, missing, or unhashed target is
    stale: the proposal was written against text that no longer exists.
    Callers validate the payload first, and re-check hashes under the writer's
    lock just before writing. The split is per file; a caller that wants a
    proposal applied whole treats any stale path as rejecting the file.
    """

    if not isinstance(payload, dict):
        return [], []
    raw_hashes = payload.get("base_hashes")
    hashes = raw_hashes if isinstance(raw_hashes, dict) else {}
    fresh: list[dict[str, Any]] = []
    stale: list[str] = []
    mutations = payload.get("mutations")
    for mutation in mutations if isinstance(mutations, list) else []:
        path = mutation.get("path") if isinstance(mutation, dict) else None
        if not isinstance(path, str) or path_error(campaign, path):
            stale.append(str(path))
            continue
        expected = _normalize_hash(hashes.get(path))
        if expected is not None and _current_hash(_target(campaign, path)) == expected:
            fresh.append(mutation)
        else:
            stale.append(path)
    return fresh, stale


def _stamps(text: str) -> Counter[str]:
    """Every revision stamp line as written, read the way the full check reads them."""

    return Counter(match.group(0).strip() for match in STAMP_RE.finditer(text))


def dry_run(campaign: Path, mutations: list[dict[str, Any]], *, revision: int) -> list[str]:
    """Apply mutations in memory only and report every one the writer would refuse.

    Reads each target the way the writer does (UTF-8, universal newlines) and
    reports a missing or undecodable file, a failing address, a result over
    the writer's size cap, and any `As of revision:` stamp the proposal adds,
    changes (even in letter case), or removes: the writer sets stamps, and a
    proposal never names a revision. Writes nothing and never raises.
    """

    errors: list[str] = []
    placeholders = owner_ops.PlaceholderContext(revision)
    for index, mutation in enumerate(mutations if isinstance(mutations, list) else []):
        label = f"mutations[{index}]"
        shape = _shape_error(mutation, label)
        if shape:
            errors.append(shape)
            continue
        path = mutation.get("path") if isinstance(mutation, dict) else None
        problem = path_error(campaign, path)
        if problem:
            errors.append(f"{label}.path {problem}")
            continue
        try:
            text = _target(campaign, path).read_text(encoding="utf-8")
        except FileNotFoundError:
            errors.append(f"{path}: the file does not exist")
            continue
        except UnicodeDecodeError:
            errors.append(f"{path}: the file is not UTF-8 text")
            continue
        except OSError as exc:
            errors.append(f"{path}: cannot read the file: {exc}")
            continue
        try:
            ops = owner_ops.parse_ops(mutation.get("ops"), relative=path, label=label)
            result = owner_ops.apply_ops(text, ops, relative=path, label=label, placeholders=placeholders)
        except owner_ops.OwnerOpError as exc:
            errors.append(f"{path}: {exc}")
            continue
        if len(result) > MAX_NOTE_TEXT:
            errors.append(f"{path}: the result holds {len(result)} characters, over the writer's cap of {MAX_NOTE_TEXT}")
        before, after = _stamps(text), _stamps(result)
        if after - before:
            errors.append(f"{path}: adds or changes an 'As of revision:' stamp; the writer sets stamps")
        elif before and not after:
            errors.append(f"{path}: removes the 'As of revision:' stamp; keep it, the writer updates it")
    return errors


def validate_file(campaign: Path, path: Path) -> list[str]:
    """`validate_staged` plus the file's own location and name."""

    try:
        payload = read_staged(path)
    except CurationError as exc:
        return [str(exc)]
    errors = validate_staged(campaign, payload)
    if not is_staging_path(campaign, path):
        errors.append("staged file must be named <curation_id>.json directly in .repog-runtime/curation/")
    curation_id = payload.get("curation_id")
    if isinstance(curation_id, str) and Path(path).stem != curation_id:
        errors.append(f"file name '{Path(path).name}' does not match curation_id '{curation_id}'")
    return errors


# ---------------------------------------------------------------------------
# The frozen packet for the curator agent
# ---------------------------------------------------------------------------


def _cells(line: str) -> list[str]:
    row = line.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", row)]


def _strip_comments(line: str, in_comment: bool) -> tuple[str, bool, bool]:
    """Drop HTML comment text from one line.

    Returns the visible rest, whether a comment is still open at the line's
    end, and whether the line held any comment text.
    """

    kept: list[str] = []
    touched = in_comment
    cursor = 0
    while True:
        if in_comment:
            end = line.find("-->", cursor)
            if end < 0:
                return "".join(kept), True, touched
            cursor, in_comment = end + 3, False
            continue
        start = line.find("<!--", cursor)
        if start < 0:
            kept.append(line[cursor:])
            return "".join(kept), False, touched
        kept.append(line[cursor:start])
        # `<!-->` and `<!--->` are complete (empty) comments in HTML.
        cursor, in_comment, touched = start + 2, True, True


def _visible_lines(text: str) -> list[str]:
    """The lines a rendered page shows as Markdown text.

    Fenced code is literal, so a table inside a fence is an example, not a
    directive, and comment markers inside it mean nothing. A line that held
    only a comment is dropped whole, so a commented example row does not split
    the table around it. An unterminated comment hides the rest of the file.
    """

    visible: list[str] = []
    in_comment = False
    in_fence = False
    for line in text.split("\n"):
        if not in_comment and owner_ops.FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        rest, in_comment, touched = _strip_comments(line, in_comment)
        if touched and not rest.strip():
            continue
        visible.append(rest)
    return visible


def active_directives(campaign: Path, *, limit: int | None = None, strict: bool = False) -> list[dict[str, str]]:
    """Active rows of `directives.md` (`| Id | Scope | Directive | Source | Status |`).

    Rows inside HTML comments or fenced code are examples, not directives, and
    are skipped. Returns every active row in file order (rows are appended, so
    the last is the newest), or only the newest `limit` rows when a limit is
    given. A missing file has no directives. With `strict`, an unreadable file
    or a row whose cell count differs from its header raises `CurationError`
    instead of being skipped, because a skipped row is a Player directive
    silently dropped (an unescaped '|' shifts the Status column).
    """

    try:
        text = (campaign / "directives.md").read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return []
    except (OSError, UnicodeDecodeError) as exc:
        if strict:
            raise CurationError("campaign_invalid", f"cannot read directives.md as UTF-8 text: {exc}") from exc
        return []
    lines = _visible_lines(text)
    found: list[dict[str, str]] = []
    columns: dict[str, int] | None = None
    width = 0
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            columns = None
            continue
        cells = _cells(line)
        if columns is None:
            names = [cell.casefold() for cell in cells]
            following = lines[index + 1] if index + 1 < len(lines) else ""
            if set(DIRECTIVE_COLUMNS) <= set(names) and owner_ops.TABLE_SEPARATOR_RE.match(following.strip()):
                columns = {name: names.index(name) for name in DIRECTIVE_COLUMNS}
                width = len(cells)
            continue
        if owner_ops.TABLE_SEPARATOR_RE.match(line.strip()):
            continue
        if len(cells) != width:
            if strict:
                raise CurationError(
                    "campaign_invalid",
                    f"directives.md row has {len(cells)} cells but its table has {width}; "
                    f"write a '|' inside a cell as '\\|': {line.strip()[:160]}",
                )
            if len(cells) <= max(columns.values()):
                continue
        if cells[columns["status"]].casefold() != "active" or not cells[columns["directive"]]:
            continue
        found.append(
            {
                "id": cells[columns["id"]],
                "scope": cells[columns["scope"]],
                "directive": cells[columns["directive"]],
            }
        )
    if limit is None:
        return found
    return found[-limit:] if limit > 0 else []


def _packet_target(campaign: Path, item: Any) -> tuple[str, str, str]:
    """Check one (path, reason) target; return path, one-line reason, and hash."""

    if not isinstance(item, (tuple, list)) or len(item) != 2:
        raise CurationError("input_invalid", f"each target must be a (path, reason) pair, not {item!r}")
    path, reason = item
    problem = path_error(campaign, path)
    if problem:
        raise CurationError("path_forbidden", f"target '{path}' {problem}")
    if reason is not None and not isinstance(reason, str):
        raise CurationError("input_invalid", f"the reason for target '{path}' must be text")
    target = _target(campaign, path)
    if not target.is_file():
        if target.exists():
            raise CurationError("campaign_invalid", f"target is not a file: {path}")
        raise CurationError("not_found", f"target does not exist: {path}")
    try:
        raw = target.read_bytes()
    except OSError as exc:
        raise CurationError("io_error", f"cannot read target {path}: {exc}") from exc
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CurationError("campaign_invalid", f"target is not UTF-8 text, so the writer cannot edit it: {path}") from exc
    # One line: whitespace of any kind (line breaks included) becomes a space.
    text = " ".join((reason or "").split())
    text = "".join(char for char in text if not _has_control(char))
    return path, text[:MAX_REASON] or "curation", hashlib.sha256(raw).hexdigest()


def build_packet(
    campaign: Path,
    targets: list[tuple[str, str]],
    *,
    curation_id: str | None = None,
) -> dict[str, Any]:
    """The frozen packet the coordinator hands the curator agent.

    The agent has no shell, so the packet carries the base hash of every
    target; the agent copies them into its staging file unchanged. Without an
    explicit id, the id is derived from the revision and the target hashes, so
    asking again for the same unchanged targets names the same staging file.
    A packet is refused while a staged file with its id is still waiting, so a
    second curator never overwrites a proposal nobody has processed. It holds
    at most `MAX_MUTATIONS` targets, one staged mutation each, and every
    active directive; a directives file it cannot read whole is an error, not
    an empty list, because the curator must obey every directive.
    """

    items = list(targets) if isinstance(targets, (list, tuple)) else []
    if not items:
        raise CurationError("input_invalid", "a curation packet needs at least one target")
    if len(items) > MAX_MUTATIONS:
        raise CurationError(
            "input_invalid",
            f"a curation packet takes at most {MAX_MUTATIONS} targets (one staged mutation each); split the request",
        )
    if not (campaign / "current_state.yaml").is_file():
        raise CurationError("campaign_invalid", f"no current_state.yaml in {campaign}; pass the campaign folder")
    revision = state_summary(campaign).get("revision")
    if revision is None:
        raise CurationError("campaign_invalid", "current_state.yaml has no continuity_revision")
    hashes: dict[str, str] = {}
    listed: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    for item in items:
        path, reason, digest = _packet_target(campaign, item)
        key = _same_file_key(path)
        if key in seen:
            raise CurationError("input_invalid", f"target listed twice: {path} (as {seen[key]})")
        seen[key] = path
        hashes[path] = digest
        listed.append({"path": path, "reason": reason})
    if curation_id is None:
        seed = json.dumps(hashes, sort_keys=True).encode("utf-8")
        curation_id = f"r{revision}-{hashlib.sha256(seed).hexdigest()[:10]}"
    staged = staging_path(campaign, curation_id)
    if staged.exists():
        raise CurationError(
            "already_staged",
            f"staged file {staged.name} is still waiting; apply or reject it before asking for the same curation again",
        )
    directives = active_directives(campaign, strict=True)
    packet: dict[str, Any] = {
        "curation_id": curation_id,
        "campaign": str(campaign.resolve()),
        "staging_path": str(staged.resolve()),
        "base_revision": revision,
        "language": runtime_settings(campaign).get("language", "auto"),
        "targets": listed,
        "base_hashes": hashes,
        "directives": directives[-MAX_DIRECTIVES:],
    }
    if len(directives) > MAX_DIRECTIVES:
        packet["directives_omitted"] = len(directives) - MAX_DIRECTIVES
    return packet


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _campaign_arg(value: str) -> Path:
    base = Path(value)
    nested = base / "campaign"
    if (nested / "current_state.yaml").is_file():
        return nested
    return base


def _parse_target(value: str) -> tuple[str, str]:
    """`PATH[=REASON]`. The path ends at its `.md`, so a file name may hold '='."""

    marker = value.find(".md=")
    if marker >= 0:
        return value[: marker + 3].strip(), value[marker + 4 :].strip()
    if value.rstrip().endswith(".md"):
        return value.strip(), ""
    path, _, reason = value.partition("=")
    return path.strip(), reason.strip()


def _validate_report(campaign: Path, files: list[Path]) -> dict[str, Any]:
    revision = state_summary(campaign).get("revision")
    reports: list[dict[str, Any]] = []
    for path in files:
        errors = validate_file(campaign, path)
        report: dict[str, Any] = {"path": str(path), "errors": errors, "ready": False}
        if not errors:
            try:
                payload = read_staged(path)
            except CurationError as exc:  # rewritten or removed since the check above
                report["errors"] = [str(exc)]
                reports.append(report)
                continue
            fresh, stale = split_by_freshness(campaign, payload)
            report["curation_id"] = payload["curation_id"]
            report["fresh_paths"] = [mutation["path"] for mutation in fresh]
            report["stale_paths"] = stale
            report["dry_run_errors"] = dry_run(
                campaign, fresh, revision=revision if revision is not None else payload["base_revision"]
            )
            # Ready: every mutation still applies to the text it was written against.
            report["ready"] = not stale and not report["dry_run_errors"]
        reports.append(report)
    ok = all(not report["errors"] and not report.get("dry_run_errors") for report in reports)
    return {"ok": ok, "files": reports}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    packet = commands.add_parser("packet", help="Build the frozen packet for the curator agent")
    packet.add_argument("campaign", help="Campaign folder (or the project folder that holds campaign/)")
    packet.add_argument("--target", action="append", required=True, help="PATH[=REASON], campaign-relative")
    packet.add_argument("--id", dest="curation_id", default=None, help="Explicit curation id")
    validate = commands.add_parser("validate", help="Check staged files: shape, freshness, and a dry run")
    validate.add_argument("campaign", help="Campaign folder (or the project folder that holds campaign/)")
    validate.add_argument("files", nargs="*", help="Staged files; default: every waiting file")
    args = parser.parse_args(argv)
    campaign = _campaign_arg(args.campaign)
    try:
        if args.command == "packet":
            result: dict[str, Any] = {
                "ok": True,
                **build_packet(campaign, [_parse_target(value) for value in args.target], curation_id=args.curation_id),
            }
            code = 0
        else:
            files = [Path(value) for value in args.files] or list_staged(campaign)
            result = _validate_report(campaign, files)
            code = 0 if result["ok"] else 1
    except CurationError as exc:
        print(json.dumps({"ok": False, "failure_category": exc.category, "failure_reason": str(exc)}, ensure_ascii=True))
        return 2
    except OSError as exc:
        print(json.dumps({"ok": False, "failure_category": "io_error", "failure_reason": str(exc)}, ensure_ascii=True))
        return 2
    # ASCII JSON: no console code page (cp1252, cp1254) can fail to encode it.
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return code


if __name__ == "__main__":
    sys.exit(main())

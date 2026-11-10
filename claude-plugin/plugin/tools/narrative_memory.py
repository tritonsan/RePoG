"""Optional narrative-memory structure checks; no fictional inference or writes.

The text APIs can validate staged owners. ``check_references`` checks only
cross-file links and does not repeat their local findings. All filesystem reads
are bounded and limited to fixed boundary files or explicitly declared links.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path


MAX_FILE_BYTES = 2_000_000
MAX_READ_BYTES = 8_000_000
MAX_REFERENCES = 128
_ID = re.compile(r"^[\w][\w.-]{0,127}$", re.UNICODE)
_PLACEHOLDERS = {"", "todo", "tbd", "unknown", "replace_me", "none yet", "n/a", "[]", "{}", "..."}
_SCOPE = (
    "Places this act can reach", "People who belong to it",
    "What is already in motion as it opens", "What stays true if the character does nothing",
)
_ACCOUNT_FIELDS = (
    "Account id", "Holder ref", "Fact id", "Account", "Stance", "Source ref",
    "Learned at", "Recorded revision", "Supersedes", "Correction ref",
)
_LOOKUP_FIELDS = ("Lookup id", "Signals", "Owner ref", "Why now", "Verified at revision")


def _finding(rule: str, message: str, path: str | Path, severity: str = "error") -> dict:
    return {"severity": severity, "rule": rule, "message": message, "path": str(path)}


def _clean(value: str) -> str:
    return value.strip().strip("`\"'").strip()


def _meaningful(value: str) -> bool:
    return _clean(value).casefold() not in _PLACEHOLDERS and not re.fullmatch(r"[<\[].*?[>\]]", _clean(value))


def _identifier(value: str) -> bool:
    return _meaningful(value) and value.casefold() != "none" and bool(_ID.fullmatch(value))


def _document(text: str) -> str:
    """Ignore instruction examples in fenced blocks and HTML comments."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    lines: list[str] = []
    fence = ""
    for line in text.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if not fence:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = ""
            continue
        if not fence:
            lines.append(line)
    return "\n".join(lines)


def _section(text: str, title: str, level: int = 2) -> str:
    match = re.search(rf"(?mi)^{'#' * level}\s+{re.escape(title)}\s*$", text)
    if not match:
        return ""
    end = re.search(rf"(?m)^#{{1,{level}}}\s", text[match.end():])
    return text[match.end():match.end() + end.start()] if end else text[match.end():]


def _entries(text: str, level: int = 3) -> list[tuple[str, str]]:
    marks = list(re.finditer(rf"(?m)^{'#' * level}\s+(.+?)\s*$", text))
    return [(mark.group(1), text[mark.end():marks[i + 1].start() if i + 1 < len(marks) else len(text)])
            for i, mark in enumerate(marks)]


def _fields(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    previous = ""
    for line in text.splitlines():
        match = re.match(r"^\s*(?:[-*]\s+)?([\w][\w /()–-]*):[ \t]*(.*)$", line)
        if match:
            previous = match.group(1).strip()
            # Duplicated declared fields are retained as invalid, never silently won.
            result[previous] = (result[previous] + "\n[DUPLICATE] " + _clean(match.group(2))
                                if previous in result else _clean(match.group(2)))
        elif previous and line.startswith(("  ", "\t")) and line.strip() and not line.lstrip().startswith(("-", "#", "|")):
            result[previous] += " " + line.strip()
        else:
            previous = ""
    return result


def _revision(value: str) -> int | None:
    return int(value) if re.fullmatch(r"[0-9]{1,18}", value) else None


def _act_data(text: str) -> tuple[dict[str, str], list[tuple[str, dict[str, str]]], bool]:
    text = _document(text)
    current = _fields(_section(text, "Arc Compass"))
    archive = [(name, _fields(body)) for name, body in _entries(_section(text, "Act Archive"))]
    modern = any(_meaningful(fields.get("Act id", "")) and fields.get("Act id", "").lower() != "none"
                 for fields in [current, *(fields for _, fields in archive)])
    return current, archive, modern


def check_threads(text: str, path: str | Path, *, ready: bool = False) -> list[dict]:
    """Validate opted-in current/archive act identities; legacy remains usable."""
    current, archive, modern = _act_data(text)
    if not modern:
        return ([_finding("act_identity_legacy", "No meaningful Act id; retain legacy behavior until explicit adoption.", path, "warning")]
                if ready and _section(_document(text), "Arc Compass") else [])
    findings: list[dict] = []
    records = [("Arc Compass", current, False), *((name, fields, True) for name, fields in archive)]
    ids: dict[str, dict[str, str]] = {}
    archived_ids = {fields.get("Act id", "") for _, fields in archive}
    for name, fields, archived in records:
        act_id = fields.get("Act id", "")
        if not _identifier(act_id):
            findings.append(_finding("act_id_invalid", f"{name}: Act id must be a non-placeholder identifier without spaces.", path))
        elif act_id in ids:
            findings.append(_finding("act_id_reused", f"Act id {act_id!r} occurs more than once in current/archive owners.", path))
        else:
            ids[act_id] = fields
        if archived and _clean(name) != act_id:
            findings.append(_finding("act_archive_heading_mismatch", f"Archive heading {name!r} must match its Act id {act_id!r}.", path))
        status = fields.get("Act status", "")
        if status not in {"planned", "active", "closed"} or (archived and status != "closed"):
            findings.append(_finding("act_status_invalid", f"{name}: archive entries must be closed; current status must be planned, active, or closed.", path))
        if ready and not archived and status == "planned":
            findings.append(_finding("act_not_playable", "Ready modern campaigns need an active or closed current Compass.", path))
        if status in {"active", "planned"} and any(_meaningful(fields.get(field, "")) for field in (
                "Closing action", "Condition met or foreclosed", "Recorded at revision")):
            findings.append(_finding("act_closure_stale", f"{name}: an unclosed act must not carry a completed Closure Record.", path))
        previous = fields.get("Previous act id", "")
        if not previous or (previous != "none" and previous not in archived_ids) or previous == act_id:
            findings.append(_finding("act_previous_invalid", f"{name}: Previous act id must be none or a different archived act.", path))
        if status in {"active", "closed"} or archived:
            required = ("Dramatic question", "Closure conditions", *_SCOPE)
            missing = [field for field in required if not _meaningful(fields.get(field, ""))]
            if missing:
                findings.append(_finding("act_compass_incomplete", f"{name}: missing {', '.join(missing)}.", path))
            opened = _revision(fields.get("Opened at revision", ""))
            if opened is None:
                findings.append(_finding("act_opened_revision_invalid", f"{name}: Opened at revision must be non-negative.", path))
            if status == "closed" or archived:
                closed = _revision(fields.get("Recorded at revision", ""))
                if not all(_meaningful(fields.get(field, "")) for field in ("Closing action", "Condition met or foreclosed")):
                    findings.append(_finding("act_closure_evidence_missing", f"{name}: a closed act requires its Closing action and Condition met or foreclosed.", path))
                if closed is None or (opened is not None and closed < opened):
                    findings.append(_finding("act_closed_revision_invalid", f"{name}: closure revision must be non-negative and not precede opening.", path))
        duplicated = [key for key, value in fields.items() if "\n[DUPLICATE]" in value]
        if duplicated:
            findings.append(_finding("act_field_duplicate", f"{name}: duplicated fields: {', '.join(duplicated)}.", path))
    for act_id in ids:
        seen: set[str] = set()
        cursor = act_id
        while cursor in ids:
            if cursor in seen:
                findings.append(_finding("act_previous_cycle", f"Previous-act chain from {act_id!r} contains a cycle.", path))
                break
            seen.add(cursor)
            cursor = ids[cursor].get("Previous act id", "none")
    return findings


def check_accounts(text: str, path: str | Path) -> list[dict]:
    """Check optional account declarations, not truth or credibility of evidence."""
    findings: list[dict] = []
    ids: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    for name, body in _entries(_section(_document(text), "Holder Accounts")):
        fields = _fields(body)
        if not any(_meaningful(fields.get(field, "")) for field in _ACCOUNT_FIELDS):
            continue
        missing = [field for field in _ACCOUNT_FIELDS if not fields.get(field, "").strip()]
        if missing:
            findings.append(_finding("holder_account_incomplete", f"{name}: missing {', '.join(missing)}.", path))
        account_id = fields.get("Account id", "")
        if not _identifier(account_id):
            findings.append(_finding("holder_account_id_invalid", f"{name}: Account id must be a stable identifier.", path))
        elif account_id in ids:
            findings.append(_finding("holder_account_id_duplicate", f"Duplicate Account id: {account_id}.", path))
        ids.add(account_id)
        fact_id, holder = fields.get("Fact id", ""), fields.get("Holder ref", "")
        if not _identifier(fact_id):
            findings.append(_finding("holder_fact_id_invalid", f"{name}: Fact id must be a stable identifier.", path))
        pair = (holder, fact_id)
        if holder and fact_id and pair in pairs:
            findings.append(_finding("holder_account_pair_duplicate", f"{name}: holder/fact pair already has a current account.", path))
        pairs.add(pair)
        if fields.get("Stance") not in {"confirmed", "suspected", "refuted", "unknown"}:
            findings.append(_finding("holder_account_stance_invalid", f"{name}: invalid Stance.", path))
        if _revision(fields.get("Recorded revision", "")) is None:
            findings.append(_finding("holder_account_revision_invalid", f"{name}: Recorded revision must be non-negative.", path))
        supersedes = fields.get("Supersedes", "")
        if supersedes and (supersedes == account_id or (supersedes != "none" and not _identifier(supersedes))):
            findings.append(_finding("holder_account_supersedes_invalid", f"{name}: Supersedes must be none or a different account id.", path))
        if supersedes and supersedes != "none" and fields.get("Correction ref", "").casefold() in {"", "none"}:
            findings.append(_finding("holder_account_correction_missing", f"{name}: a replacement account needs its Correction ref.", path))
        if any("\n[DUPLICATE]" in value for value in fields.values()):
            findings.append(_finding("holder_account_field_duplicate", f"{name}: account field declared more than once.", path))
    return findings


def check_thread_transition(before: str, after: str, path: str | Path, *, revision: int | None = None) -> list[dict]:
    """Keep committed act identity/closure history across a staged owner change."""
    old, old_archive, modern = _act_data(before)
    if not modern:
        return []  # Adoption must not pretend to reconstruct unrecorded legacy history.
    new, new_archive, after_modern = _act_data(after)
    findings: list[dict] = []
    if not after_modern:
        return [_finding("act_identity_removed", "An adopted act identity contract cannot disappear from a changed owner.", path)]
    old_ids = {fields.get("Act id", ""): fields for _, fields in old_archive}
    new_ids = {fields.get("Act id", ""): fields for _, fields in new_archive}

    def preserved(fields: dict[str, str], candidate: dict[str, str] | None, label: str) -> None:
        if candidate is None:
            findings.append(_finding("act_archive_removed", f"Committed act {label!r} must remain in Act Archive.", path))
            return
        changed = [key for key, value in fields.items()
                   if " ".join(value.split()) != " ".join(candidate.get(key, "").split())]
        if changed:
            findings.append(_finding("act_archive_changed", f"Committed act {label!r} changed structured history: {', '.join(changed)}.", path))

    for act_id, fields in old_ids.items():
        preserved(fields, new_ids.get(act_id), act_id)
    old_id, new_id = old.get("Act id", ""), new.get("Act id", "")
    if old_id != new_id:
        if old.get("Act status") != "closed":
            findings.append(_finding("act_successor_before_closure", "Close the current act before activating its successor.", path))
        preserved(old, new_ids.get(old_id), old_id)
        if new.get("Previous act id") != old_id or new.get("Act status") != "active" or new_id in old_ids:
            findings.append(_finding("act_successor_invalid", "Successor must be a fresh active act whose Previous act id names the outgoing act.", path))
        if revision is not None and _revision(new.get("Opened at revision", "")) != revision:
            findings.append(_finding("act_activation_revision_mismatch", "Successor Opened at revision must equal the committing continuity revision.", path))
    else:
        if old.get("Act status") == "active" and new.get("Act status") == "planned":
            findings.append(_finding("act_status_reversed", "An active act cannot return to draft preparation.", path))
        if old.get("Act status") == "closed":
            if new.get("Act status") != "closed":
                findings.append(_finding("act_reopened", "A closed Act id cannot become planned or active again.", path))
            preserved(old, new, old_id)
        for field in ("Previous act id", "Opened at revision"):
            if old.get("Act status") != "planned" and old.get(field) != new.get(field):
                findings.append(_finding("act_identity_changed", f"Committed {field} cannot change for the same Act id.", path))
        if revision is not None:
            if old.get("Act status") == "planned" and new.get("Act status") == "active" and _revision(new.get("Opened at revision", "")) != revision:
                findings.append(_finding("act_activation_revision_mismatch", "Opened at revision must equal the activation commit revision.", path))
            if old.get("Act status") != "closed" and new.get("Act status") == "closed" and _revision(new.get("Recorded at revision", "")) != revision:
                findings.append(_finding("act_closure_revision_mismatch", "Closure Recorded at revision must equal the closing commit revision.", path))
    return findings


def _anchor(value: str) -> str:
    value = re.sub(r"[^\w\s-]", "", value.casefold())
    return re.sub(r"\s", "-", value)


def _fragment_exists(text: str, fragment: str) -> bool:
    text = _document(text)
    headings = re.findall(r"(?m)^#{1,6}\s+(.+?)\s*$", text)
    if any(fragment == heading or fragment == _anchor(heading) for heading in headings):
        return True
    return any(_clean(value) == fragment for value in re.findall(
        r"(?mi)^[ \t]*-[ \t]*(?:Fact|Thread|Element|Act|Account|Domain|Expectation|Lookup) id:[ \t]*([^\n]+)$", text))


class _Reader:
    def __init__(self, campaign: Path, findings: list[dict]) -> None:
        self.root = campaign.resolve()
        self.findings = findings
        self.cache: dict[str, str | None] = {}
        self.used = 0

    def read(self, relative: str, *, origin: Path, optional: bool = False) -> str | None:
        if relative in self.cache:
            return self.cache[relative]
        parts = relative.split("/")
        if (not relative or "\\" in relative or any(ord(c) < 32 for c in relative)
                or any(part in {"", ".", ".."} or ":" in part for part in parts)
                or any(part.endswith((" ", ".")) for part in parts)
                or parts[0].casefold() in {".git", ".repog-transactions", "snapshots"}):
            self.findings.append(_finding("memory_reference_unsafe", f"Reference must be a campaign-relative owner path: {relative!r}.", origin))
            return None
        path = self.root
        try:
            for part in parts:
                path /= part
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
                    raise ValueError("links and reparse points are not owner paths")
            path.resolve().relative_to(self.root)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("the reference does not name a regular file")
            if info.st_size > MAX_FILE_BYTES or self.used + info.st_size > MAX_READ_BYTES:
                self.findings.append(_finding("memory_reference_limit", f"Cannot verify {relative}: bounded memory-reference read limit exceeded.", origin, "warning"))
                self.cache[relative] = None
                return None
            # O_NOFOLLOW also closes the final-component link swap on platforms supporting it.
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
            with os.fdopen(descriptor, "rb") as stream:
                payload = stream.read(min(MAX_FILE_BYTES, MAX_READ_BYTES - self.used) + 1)
            if len(payload) > MAX_FILE_BYTES or self.used + len(payload) > MAX_READ_BYTES:
                self.findings.append(_finding("memory_reference_limit", f"Cannot verify {relative}: bounded memory-reference read limit exceeded.", origin, "warning"))
                self.cache[relative] = None
                return None
            self.used += len(payload)
            value = payload.decode("utf-8-sig")
        except FileNotFoundError:
            if not optional:
                self.findings.append(_finding("memory_reference_missing", f"Missing referenced owner: {relative}.", origin))
            # Optional misses must not mask a later explicit reference to the same file.
            return None
        except (OSError, ValueError, UnicodeError) as exc:
            self.findings.append(_finding("memory_reference_unsafe", f"Cannot read owner {relative!r}: {exc}.", origin))
            self.cache[relative] = None
            return None
        self.cache[relative] = value
        return value

    def reference(self, reference: str, *, origin: Path, fragment_required: bool = True) -> None:
        relative, separator, fragment = _clean(reference).partition("#")
        if fragment_required and (not separator or not fragment.strip()):
            self.findings.append(_finding("memory_reference_fragment_missing", f"Owner ref needs an existing heading or id: {reference!r}.", origin))
        text = self.read(relative, origin=origin)
        if text is not None and separator and (not fragment or not _fragment_exists(text, fragment)):
            self.findings.append(_finding("memory_reference_fragment_missing", f"Unknown referenced heading or id: {reference!r}.", origin))


def check_references(campaign_path: str | Path, *, ready: bool = False) -> list[dict]:
    """Validate cross-file act identities and declared lookup links; never scan history."""
    root = Path(campaign_path)
    findings: list[dict] = []
    reader = _Reader(root, findings)
    documents = {name: reader.read(name, origin=root / name, optional=True) or "" for name in (
        "threads.md", "opening_brief.md", "next_act_prep.md", "session_brief.md", "knowledge_boundaries.md", "current_state.yaml",
    )}
    revision_match = re.search(r"(?m)^continuity_revision:\s*([0-9]+)\s*$", documents["current_state.yaml"])
    revision = _revision(revision_match.group(1)) if revision_match else None
    current, archive, modern = _act_data(documents["threads.md"])
    if modern:
        act_id = current.get("Act id", "")
        records = {fields.get("Act id", ""): fields for _, fields in archive}
        records[act_id] = current
        archived_ids = {fields.get("Act id", "") for _, fields in archive}
        if revision is not None:
            for known_id, record in records.items():
                for field in ("Opened at revision", "Recorded at revision"):
                    value = _revision(record.get(field, ""))
                    if value is not None and value > revision:
                        findings.append(_finding("act_revision_future", f"Act {known_id!r} {field} exceeds current continuity revision.", root / "threads.md"))
        opening = _fields(_document(documents["opening_brief.md"]))
        status, opening_id = opening.get("Opening status"), opening.get("Opening act id", "")
        if status == "active" and (opening_id != act_id or current.get("Act status") != "active"):
            findings.append(_finding("opening_act_mismatch", "Active opening must name the current active Compass.", root / "opening_brief.md"))
        elif status == "consumed" and opening_id not in records:
            findings.append(_finding("opening_act_unknown", "Consumed opening must retain a current or archived Act id.", root / "opening_brief.md"))
        elif status == "pending" and _meaningful(opening_id) and not _identifier(opening_id):
            findings.append(_finding("opening_act_id_invalid", "Proposed Opening act id must be a stable identifier.", root / "opening_brief.md"))
        prep = _fields(_section(_document(documents["next_act_prep.md"]), "Prep Status"))
        prep_status = prep.get("Prep status")
        if prep_status in {"ready", "used"}:
            before, after = prep.get("Previous act id", ""), prep.get("Next act id", "")
            successor = records.get(after)
            if (before not in archived_ids or not successor or successor.get("Previous act id") != before
                    or successor.get("Act status") not in {"active", "closed"}
                    or (prep_status == "ready" and after != act_id)):
                findings.append(_finding("prep_act_mismatch", "Ready/used prep must link a committed successor to its archived predecessor; ready targets the current act.", root / "next_act_prep.md"))
    seen: set[str] = set()
    lookups = _entries(_section(_document(documents["session_brief.md"]), "Triggered Lookups"))
    for name, body in lookups[:MAX_REFERENCES]:
        fields = _fields(body)
        if not any(fields.get(field) for field in _LOOKUP_FIELDS):
            continue
        missing = [field for field in _LOOKUP_FIELDS if not fields.get(field)]
        if missing:
            findings.append(_finding("memory_lookup_incomplete", f"{name}: missing {', '.join(missing)}.", root / "session_brief.md"))
        lookup_id = fields.get("Lookup id", "")
        if not _identifier(lookup_id) or lookup_id in seen:
            findings.append(_finding("memory_lookup_id_invalid", f"{name}: Lookup id must be a unique stable identifier.", root / "session_brief.md"))
        seen.add(lookup_id)
        if _revision(fields.get("Verified at revision", "")) is None:
            findings.append(_finding("memory_lookup_revision_invalid", f"{name}: Verified at revision must be non-negative.", root / "session_brief.md"))
        elif revision is not None and int(fields["Verified at revision"]) > revision:
            findings.append(_finding("memory_lookup_revision_future", f"{name}: Verified at revision exceeds current continuity revision.", root / "session_brief.md"))
        if any("\n[DUPLICATE]" in value for value in fields.values()):
            findings.append(_finding("memory_lookup_field_duplicate", f"{name}: lookup field declared more than once.", root / "session_brief.md"))
        if fields.get("Owner ref"):
            reader.reference(fields["Owner ref"], origin=root / "session_brief.md")
    if len(lookups) > MAX_REFERENCES:
        findings.append(_finding("memory_reference_limit", f"More than {MAX_REFERENCES} lookups; remaining links were not checked.", root / "session_brief.md", "warning"))
    if revision is not None:
        for name, body in _entries(_section(_document(documents["knowledge_boundaries.md"]), "Holder Accounts")):
            value = _revision(_fields(body).get("Recorded revision", ""))
            if value is not None and value > revision:
                findings.append(_finding("holder_account_revision_future", f"{name}: Recorded revision exceeds current continuity revision.", root / "knowledge_boundaries.md"))
    return findings

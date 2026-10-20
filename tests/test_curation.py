from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import pytest

import curation
import owner_ops


AGENT_FILE = Path(__file__).resolve().parents[1] / "plugin" / "agents" / "repog-curator.md"

STACKED_NOTE = (
    "# Edric\n\n- Tier: T2\n\n## Agency Card\n\n- Voice rhythm: clipped.\n\n"
    "## Current State (day 22)\n\nGuarding the mill. Only Ilse knows he limps.\n\n"
    "## Current State (day 72)\n\nBack in town; the mill burned.\n"
)


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _payload(campaign: Path, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "curation_id": "r0-witness",
        "base_revision": 0,
        "reason": "stacked_sections in characters/witness.md",
        "base_hashes": {"characters/witness.md": _sha(campaign / "characters" / "witness.md")},
        "mutations": [
            {
                "path": "characters/witness.md",
                "ops": [{"op": "replace_section", "heading": "Current State", "text": "Nervous, waiting."}],
            }
        ],
    }
    payload.update(overrides)
    return payload


def _stage(campaign: Path, payload: dict[str, Any], name: str | None = None) -> Path:
    path = curation.curation_dir(campaign) / f"{name or payload['curation_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return path


def _errors_for_path(campaign: Path, path: str) -> list[str]:
    payload = _payload(
        campaign,
        base_hashes={},
        mutations=[{"path": path, "ops": [{"op": "append", "text": "x"}]}],
    )
    return curation.validate_staged(campaign, payload)


# ---------------------------------------------------------------------------
# Hashes
# ---------------------------------------------------------------------------


def test_file_hash_is_sha256_of_exact_bytes(tmp_path: Path) -> None:
    lf = _write(tmp_path / "lf.md", "a\nb\n")
    crlf = tmp_path / "crlf.md"
    crlf.write_bytes(b"a\r\nb\r\n")
    assert curation.file_hash(lf) == hashlib.sha256(b"a\nb\n").hexdigest()
    assert curation.file_hash(lf) != curation.file_hash(crlf)


def test_file_hash_of_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        curation.file_hash(tmp_path / "missing.md")


# ---------------------------------------------------------------------------
# validate_staged: shape
# ---------------------------------------------------------------------------


def test_valid_payload_has_no_errors(campaign: Path) -> None:
    assert curation.validate_staged(campaign, _payload(campaign)) == []


def test_empty_mutations_are_a_valid_no_op(campaign: Path) -> None:
    payload = _payload(campaign, base_hashes={}, mutations=[], reason="nothing safe to fold")
    assert curation.validate_staged(campaign, payload) == []


def test_non_object_payload(campaign: Path) -> None:
    assert curation.validate_staged(campaign, ["not", "an", "object"]) == ["staged payload must be a JSON object"]


def test_unknown_and_missing_keys(campaign: Path) -> None:
    payload = _payload(campaign, operation_id="x", continuity_revision=3)
    del payload["reason"]
    errors = curation.validate_staged(campaign, payload)
    assert "unknown key(s): continuity_revision, operation_id" in errors
    assert "missing key(s): reason" in errors


def test_missing_mutations_and_hashes_are_reported_once(campaign: Path) -> None:
    payload = _payload(campaign)
    del payload["mutations"]
    del payload["base_hashes"]
    assert curation.validate_staged(campaign, payload) == ["missing key(s): base_hashes, mutations"]


@pytest.mark.parametrize("value", ["", "has space", "../escape", "-leading", "a" * 81, 7, None])
def test_bad_curation_id(campaign: Path, value: Any) -> None:
    errors = curation.validate_staged(campaign, _payload(campaign, curation_id=value))
    assert any(error.startswith("curation_id must match") for error in errors)


@pytest.mark.parametrize("value", [-1, True, "3", 2.0, None])
def test_bad_base_revision(campaign: Path, value: Any) -> None:
    errors = curation.validate_staged(campaign, _payload(campaign, base_revision=value))
    assert errors == ["base_revision must be a non-negative integer"]


@pytest.mark.parametrize("value", ["", "   ", "two\nlines", "x" * 301, 5])
def test_bad_reason(campaign: Path, value: Any) -> None:
    errors = curation.validate_staged(campaign, _payload(campaign, reason=value))
    assert len(errors) == 1 and errors[0].startswith("reason must")


def test_base_hashes_must_be_an_object(campaign: Path) -> None:
    errors = curation.validate_staged(campaign, _payload(campaign, base_hashes=["characters/witness.md"]))
    assert "base_hashes must be an object of path -> sha256" in errors
    # Without a hash table there is nothing to compare, so no per-mutation noise.
    assert len(errors) == 1


@pytest.mark.parametrize("digest", ["abc", "g" * 64, "A" * 63, 12, None])
def test_malformed_hash_is_an_error(campaign: Path, digest: Any) -> None:
    errors = curation.validate_staged(campaign, _payload(campaign, base_hashes={"characters/witness.md": digest}))
    assert "base_hashes['characters/witness.md'] must be a 64-character sha256 hex digest" in errors
    assert "mutations[0].path 'characters/witness.md' has no valid entry in base_hashes" in errors


def test_hash_accepts_uppercase_and_sha256_prefix(campaign: Path) -> None:
    digest = _sha(campaign / "characters" / "witness.md")
    for value in (digest.upper(), f"sha256:{digest}"):
        assert curation.validate_staged(campaign, _payload(campaign, base_hashes={"characters/witness.md": value})) == []


def test_missing_hash_for_a_mutated_path(campaign: Path) -> None:
    payload = _payload(campaign, base_hashes={"threads.md": _sha(campaign / "threads.md")})
    errors = curation.validate_staged(campaign, payload)
    assert errors == ["mutations[0].path 'characters/witness.md' has no valid entry in base_hashes"]


def test_extra_hash_for_an_unmutated_file_is_allowed(campaign: Path) -> None:
    payload = _payload(campaign)
    payload["base_hashes"]["threads.md"] = _sha(campaign / "threads.md")
    assert curation.validate_staged(campaign, payload) == []


def test_duplicate_mutation_path(campaign: Path) -> None:
    payload = _payload(campaign)
    payload["mutations"].append(payload["mutations"][0])
    errors = curation.validate_staged(campaign, payload)
    assert any("repeats 'characters/witness.md'" in error for error in errors)


def test_create_text_is_refused(campaign: Path) -> None:
    payload = _payload(
        campaign,
        base_hashes={},
        mutations=[{"path": "characters/new.md", "create_text": "# New\n"}],
    )
    errors = curation.validate_staged(campaign, payload)
    assert any("cannot create notes" in error for error in errors)


def test_exact_replacements_are_an_unknown_mutation_key(campaign: Path) -> None:
    payload = _payload(campaign)
    payload["mutations"][0]["exact_replacements"] = [{"old": "Nervous.", "new": "Calm."}]
    errors = curation.validate_staged(campaign, payload)
    assert any("unknown key(s): exact_replacements" in error for error in errors)


@pytest.mark.parametrize(
    "ops",
    [
        [],
        "replace_section",
        [{"heading": "Current State"}],
        [{"op": "set", "values": {"a": 1}}],
        [{"op": "rewrite_everything"}],
    ],
)
def test_bad_ops_are_reported(campaign: Path, ops: Any) -> None:
    payload = _payload(campaign)
    payload["mutations"][0]["ops"] = ops
    errors = curation.validate_staged(campaign, payload)
    assert len(errors) == 1 and errors[0].startswith("mutations[0]")


@pytest.mark.parametrize("text", ["- Fact id: {{next_id:PC}}", "- Confirmed at revision {{ revision }}"])
def test_placeholders_are_refused(campaign: Path, text: str) -> None:
    payload = _payload(campaign)
    payload["mutations"][0]["ops"] = [{"op": "append", "heading": "Current State", "text": text}]
    errors = curation.validate_staged(campaign, payload)
    assert errors == [
        "mutations[0] uses a {{revision}} or {{next_id}} placeholder; curation allocates no ids or revisions"
    ]


def test_mutation_must_be_an_object(campaign: Path) -> None:
    errors = curation.validate_staged(campaign, _payload(campaign, mutations=["characters/witness.md"]))
    assert errors == ["mutations[0] must be an object with 'path' and 'ops'"]


def test_mutations_must_be_an_array(campaign: Path) -> None:
    errors = curation.validate_staged(campaign, _payload(campaign, mutations={"path": "x.md"}))
    assert errors == ["mutations must be an array"]


def test_mutation_count_is_capped(campaign: Path) -> None:
    hashes: dict[str, str] = {}
    mutations = []
    for index in range(curation.MAX_MUTATIONS + 1):
        path = f"characters/n{index}.md"
        _write(campaign / path, f"# N{index}\n")
        hashes[path] = _sha(campaign / path)
        mutations.append({"path": path, "ops": [{"op": "append", "text": "x"}]})
    errors = curation.validate_staged(campaign, _payload(campaign, base_hashes=hashes, mutations=mutations))
    assert errors == [f"mutations exceeds the limit of {curation.MAX_MUTATIONS}"]


# ---------------------------------------------------------------------------
# validate_staged: forbidden paths
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "fragment"),
    [
        ("session_log.md", "written only by the writer"),
        ("Session_Log.md", "written only by the writer"),
        ("archive/session_log_through_r4.md", "archive/"),
        ("Archive/old.md", "Archive/"),
        ("snapshots/start/threads.md", "snapshots/"),
        (".repog-runtime/notes.md", "hidden or runtime folder"),
        (".repog-runtime/curation/other.md", "hidden or runtime folder"),
        (".repog-transactions/journal.md", "hidden or runtime folder"),
        ("characters/.hidden/edric.md", "hidden or runtime folder"),
        ("current_state.yaml", "must be a Markdown note"),
        ("mechanics_state.json", "must be a Markdown note"),
        ("play_profile.yaml", "must be a Markdown note"),
        ("characters/witness.txt", "must be a Markdown note"),
        ("../outside.md", "inside the campaign folder"),
        ("characters/../../outside.md", "inside the campaign folder"),
        ("./characters/witness.md", "must be written as 'characters/witness.md'"),
        ("/etc/notes.md", "inside the campaign folder"),
        ("C:/notes.md", "drive or URI prefix"),
        ("characters\\witness.md", "POSIX path"),
        ("characters//witness.md", "must be written as 'characters/witness.md'"),
        ("characters/witness.md/", "must be written as 'characters/witness.md'"),
        (" characters/witness.md", "spaces"),
        ("", "campaign-relative path"),
    ],
)
def test_forbidden_mutation_paths(campaign: Path, path: str, fragment: str) -> None:
    errors = _errors_for_path(campaign, path)
    assert len(errors) == 1, errors
    assert errors[0].startswith("mutations[0].path") and fragment in errors[0]


def test_non_text_path_is_forbidden(campaign: Path) -> None:
    errors = _errors_for_path(campaign, 12)  # type: ignore[arg-type]
    assert errors == ["mutations[0].path must be a campaign-relative path"]


def test_forbidden_path_in_base_hashes(campaign: Path) -> None:
    payload = _payload(campaign)
    payload["base_hashes"]["session_log.md"] = _sha(campaign / "session_log.md")
    errors = curation.validate_staged(campaign, payload)
    assert errors == ["base_hashes['session_log.md'] is written only by the writer"]


@pytest.mark.parametrize(
    "path",
    ["characters/witness.md", "knowledge_boundaries.md", "places/harbor/pier.md", "archive.md", "notes/archive/x.md"],
)
def test_allowed_markdown_paths(campaign: Path, path: str) -> None:
    assert curation.path_error(campaign, path) is None


def test_symlink_escaping_the_campaign_is_forbidden(campaign: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    _write(outside / "secret.md", "# Secret\n")
    link = campaign / "linked"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        try:
            import _winapi  # a directory junction needs no symlink privilege on Windows

            _winapi.CreateJunction(str(outside), str(link))
        except (ImportError, AttributeError, OSError):
            pytest.skip("neither symlinks nor junctions are available here")
    assert curation.path_error(campaign, "linked/secret.md") == "escapes the campaign folder"


# ---------------------------------------------------------------------------
# split_by_freshness
# ---------------------------------------------------------------------------


def _two_file_payload(campaign: Path) -> dict[str, Any]:
    return _payload(
        campaign,
        base_hashes={
            "characters/witness.md": _sha(campaign / "characters" / "witness.md"),
            "threads.md": _sha(campaign / "threads.md"),
        },
        mutations=[
            {"path": "characters/witness.md", "ops": [{"op": "append", "text": "- Calm."}]},
            {"path": "threads.md", "ops": [{"op": "append", "text": "- Another thread"}]},
        ],
    )


def test_unchanged_targets_are_fresh(campaign: Path) -> None:
    payload = _two_file_payload(campaign)
    fresh, stale = curation.split_by_freshness(campaign, payload)
    assert fresh == payload["mutations"]
    assert stale == []


def test_changed_target_is_stale(campaign: Path) -> None:
    payload = _two_file_payload(campaign)
    witness = campaign / "characters" / "witness.md"
    witness.write_bytes(witness.read_bytes() + b"\nA new durable fact.\n")
    fresh, stale = curation.split_by_freshness(campaign, payload)
    assert [mutation["path"] for mutation in fresh] == ["threads.md"]
    assert stale == ["characters/witness.md"]


def test_line_ending_change_makes_a_target_stale(campaign: Path) -> None:
    payload = _two_file_payload(campaign)
    threads = campaign / "threads.md"
    threads.write_bytes(threads.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n") + b"\r\n")
    _, stale = curation.split_by_freshness(campaign, payload)
    assert stale == ["threads.md"]


def test_deleted_target_is_stale(campaign: Path) -> None:
    payload = _two_file_payload(campaign)
    (campaign / "threads.md").unlink()
    fresh, stale = curation.split_by_freshness(campaign, payload)
    assert [mutation["path"] for mutation in fresh] == ["characters/witness.md"]
    assert stale == ["threads.md"]


def test_unhashed_or_malformed_hash_is_stale(campaign: Path) -> None:
    payload = _two_file_payload(campaign)
    del payload["base_hashes"]["threads.md"]
    payload["base_hashes"]["characters/witness.md"] = "not-a-hash"
    fresh, stale = curation.split_by_freshness(campaign, payload)
    assert fresh == []
    assert stale == ["characters/witness.md", "threads.md"]


def test_prefixed_hash_is_fresh(campaign: Path) -> None:
    payload = _payload(campaign)
    digest = payload["base_hashes"]["characters/witness.md"]
    payload["base_hashes"]["characters/witness.md"] = f"sha256:{digest.upper()}"
    fresh, stale = curation.split_by_freshness(campaign, payload)
    assert len(fresh) == 1 and stale == []


def test_forbidden_path_is_never_fresh_even_with_a_matching_hash(campaign: Path) -> None:
    log = campaign / "session_log.md"
    payload = _payload(
        campaign,
        base_hashes={"session_log.md": _sha(log)},
        mutations=[{"path": "session_log.md", "ops": [{"op": "append", "text": "forged"}]}],
    )
    fresh, stale = curation.split_by_freshness(campaign, payload)
    assert fresh == [] and stale == ["session_log.md"]


# ---------------------------------------------------------------------------
# Staging files: listing, locating, moving
# ---------------------------------------------------------------------------


def test_list_staged_without_a_runtime_folder_creates_nothing(campaign: Path) -> None:
    assert curation.list_staged(campaign) == []
    assert not (campaign / ".repog-runtime").exists()


def test_list_staged_returns_waiting_json_files_oldest_first(campaign: Path) -> None:
    folder = curation.curation_dir(campaign)
    newer = _write(folder / "a-newer.json", "{}")
    older = _write(folder / "b-older.json", "{}")
    os.utime(older, ns=(1_000_000_000, 1_000_000_000))
    os.utime(newer, ns=(2_000_000_000, 2_000_000_000))
    _write(folder / "applied" / "done.json", "{}")
    _write(folder / "rejected" / "stale.json", "{}")
    _write(folder / ".b-older.json.123.tmp", "{}")
    _write(folder / ".hidden.json", "{}")
    _write(folder / "notes.txt", "x")
    assert curation.list_staged(campaign) == [older, newer]


def test_staging_path_and_guard(campaign: Path) -> None:
    path = curation.staging_path(campaign, "r4-edric")
    assert path == campaign / ".repog-runtime" / "curation" / "r4-edric.json"
    assert curation.is_staging_path(campaign, path)
    assert curation.is_staging_path(campaign, str(path))
    folder = curation.curation_dir(campaign)
    assert not curation.is_staging_path(campaign, folder / "applied" / "r4-edric.json")
    assert not curation.is_staging_path(campaign, folder / "r4-edric.md")
    assert not curation.is_staging_path(campaign, folder / "bad id.json")
    assert not curation.is_staging_path(campaign, campaign / "characters" / "witness.md")
    assert not curation.is_staging_path(campaign, campaign / ".repog-runtime" / "lint_last.json")
    assert not curation.is_staging_path(campaign, folder / ".." / "capsule_state.json")
    assert not curation.is_staging_path(campaign, folder / curation.RESULT_FILE)


def test_staging_path_rejects_a_bad_id(campaign: Path) -> None:
    with pytest.raises(curation.CurationError) as caught:
        curation.staging_path(campaign, "../../characters/witness")
    assert caught.value.category == "input_invalid"


@pytest.mark.parametrize("outcome", ["applied", "rejected"])
def test_move_processed(campaign: Path, outcome: str) -> None:
    staged = _stage(campaign, _payload(campaign))
    moved = curation.move_processed(staged, outcome)
    assert moved == curation.curation_dir(campaign) / outcome / "r0-witness.json"
    assert moved.is_file() and not staged.exists()
    assert curation.list_staged(campaign) == []


def test_move_processed_never_overwrites(campaign: Path) -> None:
    first = curation.move_processed(_stage(campaign, _payload(campaign)), "rejected")
    second = curation.move_processed(_stage(campaign, _payload(campaign)), "rejected")
    third = curation.move_processed(_stage(campaign, _payload(campaign)), "rejected")
    assert [first.name, second.name, third.name] == ["r0-witness.json", "r0-witness-2.json", "r0-witness-3.json"]


def test_move_processed_errors(campaign: Path) -> None:
    staged = _stage(campaign, _payload(campaign))
    with pytest.raises(curation.CurationError) as caught:
        curation.move_processed(staged, "deleted")
    assert caught.value.category == "input_invalid"
    moved = curation.move_processed(staged, "applied")
    with pytest.raises(curation.CurationError) as caught:
        curation.move_processed(moved, "rejected")
    assert caught.value.category == "input_invalid"
    with pytest.raises(curation.CurationError) as caught:
        curation.move_processed(staged, "applied")
    assert caught.value.category == "not_found"


# ---------------------------------------------------------------------------
# Reading files, filename checks, dry runs
# ---------------------------------------------------------------------------


def test_validate_file_accepts_a_well_formed_staging_file(campaign: Path) -> None:
    assert curation.validate_file(campaign, _stage(campaign, _payload(campaign))) == []


def test_validate_file_checks_name_and_folder(campaign: Path) -> None:
    misnamed = _stage(campaign, _payload(campaign), name="r0-other")
    assert curation.validate_file(campaign, misnamed) == [
        "file name 'r0-other.json' does not match curation_id 'r0-witness'"
    ]
    elsewhere = _write(campaign / "characters" / "r0-witness.json", json.dumps(_payload(campaign)))
    assert curation.validate_file(campaign, elsewhere) == [
        "staged file must be named <curation_id>.json directly in .repog-runtime/curation/"
    ]


@pytest.mark.parametrize(("content", "fragment"), [("{not json", "not UTF-8 JSON"), ("[1, 2]", "one JSON object")])
def test_validate_file_reports_unreadable_content(campaign: Path, content: str, fragment: str) -> None:
    path = _write(curation.curation_dir(campaign) / "broken.json", content)
    errors = curation.validate_file(campaign, path)
    assert len(errors) == 1 and fragment in errors[0]


def test_read_staged_missing_file(campaign: Path) -> None:
    with pytest.raises(curation.CurationError) as caught:
        curation.read_staged(curation.curation_dir(campaign) / "absent.json")
    assert caught.value.category == "not_found"


def test_dry_run_reports_bad_addresses(campaign: Path) -> None:
    good = {"path": "characters/witness.md", "ops": [{"op": "replace_section", "heading": "Current State", "text": "Calm."}]}
    bad = {"path": "threads.md", "ops": [{"op": "remove_section", "heading": "No Such Heading"}]}
    errors = curation.dry_run(campaign, [good, bad], revision=0)
    assert len(errors) == 1 and errors[0].startswith("threads.md:") and "No Such Heading" in errors[0]
    assert curation.dry_run(campaign, [good], revision=0) == []
    # A dry run writes nothing.
    assert "Nervous." in (campaign / "characters" / "witness.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Packet
# ---------------------------------------------------------------------------


DIRECTIVES = (
    "# Directives\n\nPlayer and OOC rules that constrain play.\n\n"
    "| Id | Scope | Directive | Source | Status |\n| --- | --- | --- | --- | --- |\n"
    "<!-- | D-000 | global | Example only. | template | active | -->\n"
    "| D-001 | global | Edric never speaks of the war. | OOC r12 | active |\n"
    "<!--\n| D-900 | global | Multi-line example. | template | active |\n-->\n"
    "| D-002 | entity:Edric | Old rule. | OOC r3 | retired |\n"
    "| D-003 | entity:Edric | Edric calls Mira \"girl\". | OOC r14 | Active |\n"
)


def test_build_packet(campaign: Path) -> None:
    _write(campaign / "directives.md", DIRECTIVES)
    packet = curation.build_packet(
        campaign, [("characters/witness.md", "stacked_sections"), ("threads.md", "")]
    )
    assert packet["base_revision"] == 0
    assert packet["base_hashes"] == {
        "characters/witness.md": _sha(campaign / "characters" / "witness.md"),
        "threads.md": _sha(campaign / "threads.md"),
    }
    assert packet["targets"] == [
        {"path": "characters/witness.md", "reason": "stacked_sections"},
        {"path": "threads.md", "reason": "curation"},
    ]
    assert re.fullmatch(r"r0-[0-9a-f]{10}", packet["curation_id"])
    assert Path(packet["staging_path"]) == curation.staging_path(campaign, packet["curation_id"]).resolve()
    assert packet["campaign"] == str(campaign.resolve())
    assert packet["language"] == "auto"
    assert packet["directives"] == [
        {"id": "D-001", "scope": "global", "directive": "Edric never speaks of the war."},
        {"id": "D-003", "scope": "entity:Edric", "directive": "Edric calls Mira \"girl\"."},
    ]
    # The packet only reads: no runtime folder, no staging file.
    assert not (campaign / ".repog-runtime").exists()


def test_packet_id_is_stable_until_a_target_changes(campaign: Path) -> None:
    targets = [("characters/witness.md", "stacked_sections")]
    first = curation.build_packet(campaign, targets)["curation_id"]
    assert curation.build_packet(campaign, targets)["curation_id"] == first
    _write(campaign / "characters" / "witness.md", "# Witness\n\nChanged.\n")
    assert curation.build_packet(campaign, targets)["curation_id"] != first
    assert curation.build_packet(campaign, targets, curation_id="r0-manual")["curation_id"] == "r0-manual"


def test_packet_reads_the_play_language(campaign: Path) -> None:
    profile = campaign / "play_profile.yaml"
    profile.write_bytes(profile.read_bytes() + b"narration:\n  language: tr\n")
    assert curation.build_packet(campaign, [("threads.md", "x")])["language"] == "tr"


@pytest.mark.parametrize(
    ("targets", "category"),
    [
        ([], "input_invalid"),
        ([("session_log.md", "too long")], "path_forbidden"),
        ([("current_state.yaml", "x")], "path_forbidden"),
        ([("archive/old.md", "x")], "path_forbidden"),
        ([("characters/ghost.md", "x")], "not_found"),
        ([("threads.md", "a"), ("threads.md", "b")], "input_invalid"),
    ],
)
def test_build_packet_refusals(campaign: Path, targets: list[tuple[str, str]], category: str) -> None:
    with pytest.raises(curation.CurationError) as caught:
        curation.build_packet(campaign, targets)
    assert caught.value.category == category


def test_build_packet_rejects_a_bad_explicit_id(campaign: Path) -> None:
    with pytest.raises(curation.CurationError):
        curation.build_packet(campaign, [("threads.md", "x")], curation_id="bad/id")


# ---------------------------------------------------------------------------
# End to end: packet -> staged proposal -> freshness -> typed ops
# ---------------------------------------------------------------------------


def _fold_ops() -> list[dict[str, Any]]:
    """The edits the agent prompt describes for a stacked note."""

    return [
        {"op": "replace", "old": "- Tier: T2\n", "new": "- Tier: T2\n\n## Core\n\n- Status: alive\n"},
        {"op": "replace", "old": "## Current State (day 72)\n", "new": "## Now\n"},
        {"op": "replace_section", "heading": "Now", "text": "Back in town; the mill burned. Only Ilse knows he limps."},
        {"op": "remove_section", "heading": "Current State (day 22)"},
        {"op": "insert_section", "heading": "## History", "text": "- Day 22: guarding the mill."},
    ]


def test_staged_fold_applies_when_fresh_and_is_refused_when_stale(campaign: Path) -> None:
    note = _write(campaign / "characters" / "edric.md", STACKED_NOTE)
    packet = curation.build_packet(campaign, [("characters/edric.md", "stacked_sections")])
    payload = {
        "curation_id": packet["curation_id"],
        "base_revision": packet["base_revision"],
        "reason": "fold stacked current-state layers",
        "base_hashes": {"characters/edric.md": packet["base_hashes"]["characters/edric.md"]},
        "mutations": [{"path": "characters/edric.md", "ops": _fold_ops()}],
    }
    staged = Path(packet["staging_path"])
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    assert curation.list_staged(campaign) == [staged]
    assert curation.validate_file(campaign, staged) == []
    fresh, stale = curation.split_by_freshness(campaign, curation.read_staged(staged))
    assert stale == [] and len(fresh) == 1
    assert curation.dry_run(campaign, fresh, revision=0) == []

    mutation = fresh[0]
    ops = owner_ops.parse_ops(mutation["ops"], relative=mutation["path"], label="m")
    result = owner_ops.apply_ops(
        note.read_text(encoding="utf-8"),
        ops,
        relative=mutation["path"],
        label="m",
        placeholders=owner_ops.PlaceholderContext(0),
    )
    assert owner_ops.stacked_headings(result, minimum=2) == []
    headings = re.findall(r"(?m)^#+ .+$", result)
    assert headings == ["# Edric", "## Core", "## Agency Card", "## Now", "## History"]
    assert "Only Ilse knows he limps." in result

    # A durable commit lands on the note before the writer gets to the proposal.
    note.write_bytes(note.read_bytes() + b"\nEdric left town at dawn.\n")
    fresh, stale = curation.split_by_freshness(campaign, curation.read_staged(staged))
    assert fresh == [] and stale == ["characters/edric.md"]
    rejected = curation.move_processed(staged, "rejected")
    assert rejected.parent.name == "rejected" and curation.list_staged(campaign) == []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_packet(campaign: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = curation.main(["packet", str(campaign.parent), "--target", "characters/witness.md=stacked_sections"])
    output = json.loads(capsys.readouterr().out)
    assert code == 0 and output["ok"] is True
    assert output["targets"] == [{"path": "characters/witness.md", "reason": "stacked_sections"}]


def test_cli_packet_refusal(campaign: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = curation.main(["packet", str(campaign), "--target", "session_log.md=x"])
    output = json.loads(capsys.readouterr().out)
    assert code == 2 and output == {
        "ok": False,
        "failure_category": "path_forbidden",
        "failure_reason": "target 'session_log.md' is written only by the writer",
    }


def test_cli_validate(campaign: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert curation.main(["validate", str(campaign)]) == 0
    assert json.loads(capsys.readouterr().out) == {"ok": True, "files": []}

    _stage(campaign, _payload(campaign))
    assert curation.main(["validate", str(campaign)]) == 0
    report = json.loads(capsys.readouterr().out)["files"][0]
    assert report["fresh_paths"] == ["characters/witness.md"] and report["stale_paths"] == []

    broken = _payload(campaign, curation_id="r0-broken")
    broken["mutations"][0]["ops"] = [{"op": "remove_section", "heading": "Missing"}]
    _stage(campaign, broken)
    assert curation.main(["validate", str(campaign)]) == 1
    reports = {item["curation_id"]: item for item in json.loads(capsys.readouterr().out)["files"]}
    assert reports["r0-broken"]["dry_run_errors"]

    bad = _stage(campaign, _payload(campaign, curation_id="r0-bad", reason=""))
    assert curation.main(["validate", str(campaign), str(bad)]) == 1
    assert json.loads(capsys.readouterr().out)["files"][0]["errors"] == ["reason must be non-empty text"]


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------


def _agent_parts() -> tuple[dict[str, str], str]:
    raw = AGENT_FILE.read_bytes()
    assert b"\r" not in raw
    text = raw.decode("utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    assert match, "agent file needs YAML frontmatter"
    fields = dict(line.split(": ", 1) for line in match.group(1).splitlines())
    return fields, match.group(2)


def test_agent_frontmatter() -> None:
    fields, _ = _agent_parts()
    assert fields["name"] == "repog-curator"
    assert fields["tools"] == "Read, Grep, Glob, Write"
    assert fields["model"] == "inherit"
    for trigger in ("stacked_sections", "owner_size_budget", "Core block", "full distill", "never use it for ordinary turns"):
        assert trigger in fields["description"]


def test_agent_frontmatter_values_survive_a_yaml_parser() -> None:
    """Plain YAML scalars end at ' #' (a comment) and break at ': '.

    The first draft wrote 'missing a ## Core block', so a YAML parser cut the
    description there and dropped the 'never use it for ordinary turns' limit.
    """

    fields, _ = _agent_parts()
    for key, value in fields.items():
        assert " #" not in value, f"{key} would be cut at a YAML comment"
        assert ": " not in value, f"{key} is not a valid plain YAML scalar"
        assert not value.startswith(("'", '"', "#", "&", "*", "!", "|", ">", "%", "@", "`", "[", "{"))
    yaml = pytest.importorskip("yaml")
    raw = AGENT_FILE.read_text(encoding="utf-8")
    parsed = yaml.safe_load(raw.split("---\n")[1])
    assert parsed["description"] == fields["description"]
    assert parsed["description"].endswith("persistence, or narration.")


def test_agent_body_is_compact_and_names_the_contract() -> None:
    _, body = _agent_parts()
    assert len(body.encode("utf-8")) < 4096
    for phrase in (
        ".repog-runtime/curation/<curation_id>.json",
        "Write nothing else",
        "base_hashes",
        "## Now",
        "## History",
        "## Core",
        "verbatim",
        "language",
        "one line",
        # Read pages long files; replace_section spans subsections; a split
        # apply must never lose text moved between files.
        "offset and limit",
        "deeper subsections included",
        "never move text from one file to another",
    ):
        assert phrase in body
    keys = re.search(r"```json\n(.*?)```", body, re.S)
    assert keys is not None
    example = json.loads(keys.group(1).replace("<packet>", "x").replace("<one line>", "y").replace("<packet hash>", "0" * 64))
    assert set(example) == curation.PAYLOAD_KEYS


# ---------------------------------------------------------------------------
# Review regressions
# ---------------------------------------------------------------------------


def _link_dir(link: Path, target: Path) -> None:
    """A directory symlink, or a junction on Windows without symlink rights."""

    try:
        os.symlink(target, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        try:
            import _winapi

            _winapi.CreateJunction(str(target), str(link))
        except (ImportError, AttributeError, OSError):
            pytest.skip("neither symlinks nor junctions are available here")


@pytest.mark.parametrize(
    "text",
    ["- Fact id: {{\tnext_id:F}}", "- Seen at revision {{\nrevision}}", "{{revision\t}}"],
)
def test_placeholders_hidden_by_json_escapes_are_refused(campaign: Path, text: str) -> None:
    # owner_ops resolves `\s*` inside the braces, so a tab or line break must
    # not slip past the check (a JSON dump escapes them to `\t` and `\n`).
    payload = _payload(campaign)
    payload["mutations"][0]["ops"] = [{"op": "append", "heading": "Current State", "text": text}]
    errors = curation.validate_staged(campaign, payload)
    assert errors == [
        "mutations[0] uses a {{revision}} or {{next_id}} placeholder; curation allocates no ids or revisions"
    ]


def test_placeholder_inside_table_cells_is_refused(campaign: Path) -> None:
    payload = _payload(campaign)
    payload["mutations"][0]["ops"] = [
        {"op": "upsert_row", "key": "X", "cells": ["X", "{{next_id:PC}}"]},
    ]
    errors = curation.validate_staged(campaign, payload)
    assert any("placeholder" in error for error in errors)


@pytest.mark.parametrize("value", ["fold stacked layers\r\n", "fold stacked layers\n", "  fold stacked layers  "])
def test_reason_is_trimmed_before_the_one_line_check(campaign: Path, value: str) -> None:
    # The writer's one-line fields trim first; a trailing CRLF used to fail
    # while a trailing LF passed.
    assert curation.validate_staged(campaign, _payload(campaign, reason=value)) == []


@pytest.mark.parametrize(
    ("path", "fragment"),
    [
        ("characters/witness.md:hidden.md", "Windows stream"),
        ("characters /witness.md", "space or a dot"),
        ("characters./witness.md", "space or a dot"),
        ("session_log.md.", "space or a dot"),
    ],
)
def test_windows_path_aliases_are_forbidden(campaign: Path, path: str, fragment: str) -> None:
    errors = _errors_for_path(campaign, path)
    assert len(errors) == 1 and fragment in errors[0], errors


def test_link_inside_the_campaign_cannot_reach_archive(campaign: Path) -> None:
    _write(campaign / "archive" / "old.md", "# Old\n")
    _link_dir(campaign / "characters" / "history", campaign / "archive")
    assert curation.path_error(campaign, "characters/history/old.md") == (
        "resolves to 'archive/old.md', which is in archive/, which holds history, not live notes"
    )


def test_link_inside_the_campaign_cannot_reach_the_runtime_folder(campaign: Path) -> None:
    runtime = campaign / ".repog-runtime"
    _write(runtime / "notes.md", "# Runtime\n")
    _link_dir(campaign / "characters" / "rt", runtime)
    problem = curation.path_error(campaign, "characters/rt/notes.md")
    assert problem == "resolves to '.repog-runtime/notes.md', which is in a hidden or runtime folder"


def test_windows_short_name_cannot_reach_the_session_log(campaign: Path) -> None:
    if os.name != "nt":
        pytest.skip("8.3 short names exist only on Windows")
    import ctypes

    log = campaign / "session_log.md"
    buffer = ctypes.create_unicode_buffer(1024)
    if not ctypes.windll.kernel32.GetShortPathNameW(str(log), buffer, 1024):  # type: ignore[attr-defined]
        pytest.skip("GetShortPathNameW failed")
    short = Path(buffer.value).name
    if short.casefold() == log.name.casefold():
        pytest.skip("8.3 short names are disabled on this volume")
    # Before the fix 'SESSIO~1.MD' passed every check and named the log. Its
    # upper-case suffix is now refused outright; the lower-case spelling still
    # reaches the log and must be caught on the resolved name.
    assert curation.path_error(campaign, short) is not None
    assert curation.path_error(campaign, short.lower()) == (
        "resolves to 'session_log.md', which is written only by the writer"
    )


def test_case_variant_must_use_the_files_own_spelling(campaign: Path) -> None:
    if not (campaign / "Characters" / "Witness.md").exists():
        pytest.skip("case-sensitive file system: the variant names a different, missing file")
    assert curation.path_error(campaign, "Characters/Witness.md") == (
        "must be written as 'characters/witness.md', the file's own spelling"
    )
    # So two spellings of one file can never both carry a mutation.
    payload = _payload(campaign)
    payload["mutations"].append({"path": "Characters/Witness.md", "ops": [{"op": "append", "text": "x"}]})
    assert any("own spelling" in error for error in curation.validate_staged(campaign, payload))


def test_non_ascii_note_names_are_allowed(campaign: Path) -> None:
    _write(campaign / "characters" / "İlse.md", "# İlse\n\n## Now\n\nŞehirde.\n")
    _write(campaign / "characters" / "ılgaz.md", "# Ilgaz\n")
    assert curation.path_error(campaign, "characters/İlse.md") is None
    assert curation.path_error(campaign, "characters/ılgaz.md") is None
    packet = curation.build_packet(campaign, [("characters/İlse.md", "core_missing")])
    assert packet["base_hashes"]["characters/İlse.md"] == _sha(campaign / "characters" / "İlse.md")


def test_move_processed_refuses_anything_but_a_staging_file(campaign: Path) -> None:
    note = campaign / "characters" / "witness.md"
    before = note.read_bytes()
    with pytest.raises(curation.CurationError) as caught:
        curation.move_processed(note, "applied")
    assert caught.value.category == "path_forbidden"
    assert note.read_bytes() == before and not (campaign / "characters" / "applied").exists()
    stray = _write(campaign / ".repog-runtime" / "r0-witness.json", "{}")
    with pytest.raises(curation.CurationError) as caught:
        curation.move_processed(stray, "rejected")
    assert caught.value.category == "path_forbidden" and stray.is_file()


def test_read_staged_tolerates_a_bom(campaign: Path) -> None:
    path = curation.staging_path(campaign, "r0-witness")
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps(_payload(campaign)).encode("utf-8"))
    assert curation.validate_file(campaign, path) == []


def test_read_staged_refuses_repeated_keys(campaign: Path) -> None:
    path = curation.staging_path(campaign, "r0-witness")
    path.parent.mkdir(parents=True)
    # A repeated key would let a later 'mutations' silently replace the first.
    path.write_bytes(b'{"curation_id": "r0-witness", "mutations": [], "mutations": []}')
    with pytest.raises(curation.CurationError) as caught:
        curation.read_staged(path)
    assert caught.value.category == "input_invalid" and "repeats the key 'mutations'" in str(caught.value)
    assert curation.validate_file(campaign, path) == [
        "staged file repeats the key 'mutations'; JSON keys must be unique"
    ]


def test_dry_run_never_raises_on_a_malformed_mutation(campaign: Path) -> None:
    errors = curation.dry_run(campaign, [{"ops": []}, "characters/witness.md"], revision=0)  # type: ignore[list-item]
    assert errors == [
        "mutations[0].path must be a campaign-relative path",
        "mutations[1].path must be a campaign-relative path",
    ]


def test_dry_run_reports_a_missing_target(campaign: Path) -> None:
    # Appending to empty text succeeds, so a missing file used to look fine.
    mutation = {"path": "characters/ghost.md", "ops": [{"op": "append", "text": "- Seen."}]}
    assert curation.dry_run(campaign, [mutation], revision=0) == ["characters/ghost.md: the file does not exist"]


def test_dry_run_reports_a_target_that_is_not_utf8(campaign: Path) -> None:
    (campaign / "characters" / "eski.md").write_bytes("# Eski\n\n## Now\n\nŞimdi çarşıda.\n".encode("cp1254"))
    mutation = {"path": "characters/eski.md", "ops": [{"op": "append", "heading": "Now", "text": "x"}]}
    assert curation.dry_run(campaign, [mutation], revision=0) == ["characters/eski.md: the file is not UTF-8 text"]


def test_dry_run_reads_crlf_targets_like_the_writer(campaign: Path) -> None:
    (campaign / "characters" / "crlf.md").write_bytes(b"# Crlf\r\n\r\n## Now\r\n\r\nWaiting.\r\n")
    mutation = {
        "path": "characters/crlf.md",
        "ops": [{"op": "replace", "old": "## Now\n\nWaiting.", "new": "## Now\n\nGone."}],
    }
    assert curation.dry_run(campaign, [mutation], revision=0) == []


def test_dry_run_refuses_a_new_or_changed_revision_stamp(campaign: Path) -> None:
    _write(campaign / "characters" / "stamped.md", "# Stamped\n\nAs of revision: 4\n\n## Now\n\nIdle.\n")
    changed = {"path": "characters/stamped.md", "ops": [{"op": "replace", "old": "revision: 4", "new": "revision: 9"}]}
    added = {"path": "characters/stamped.md", "ops": [{"op": "append", "heading": "Now", "text": "As of revision: 4"}]}
    kept = {"path": "characters/stamped.md", "ops": [{"op": "replace_section", "heading": "Now", "text": "Resting."}]}
    message = "characters/stamped.md: adds or changes an 'As of revision:' stamp; the writer sets stamps"
    assert curation.dry_run(campaign, [changed], revision=4) == [message]
    assert curation.dry_run(campaign, [added], revision=4) == [message]
    assert curation.dry_run(campaign, [kept], revision=4) == []


def test_dry_run_reports_a_result_over_the_writer_cap(campaign: Path) -> None:
    _write(campaign / "characters" / "huge.md", "# Huge\n\n" + "x" * (curation.MAX_NOTE_TEXT - 20) + "\n")
    mutation = {"path": "characters/huge.md", "ops": [{"op": "append", "text": "y" * 100}]}
    errors = curation.dry_run(campaign, [mutation], revision=0)
    assert len(errors) == 1 and "over the writer's cap" in errors[0]


DIRECTIVE_TABLE = "| Id | Scope | Directive | Source | Status |\n| --- | --- | --- | --- | --- |\n"


def test_directive_comment_followed_by_text_does_not_swallow_rows(campaign: Path) -> None:
    _write(
        campaign / "directives.md",
        DIRECTIVE_TABLE
        + "<!-- moved --> | D-001 | global | First. | OOC | active |\n"
        + "| D-002 | global | Second. | OOC | active |\n"
        + "<!-- example -->\n"
        + "| D-003 | global | Third. | OOC | active |\n",
    )
    assert [row["id"] for row in curation.active_directives(campaign)] == ["D-001", "D-002", "D-003"]


def test_unterminated_directive_comment_hides_the_rest(campaign: Path) -> None:
    _write(
        campaign / "directives.md",
        DIRECTIVE_TABLE
        + "| D-001 | global | Real. | OOC | active | <!-- unterminated\n"
        + "| D-900 | global | Example. | template | active |\n",
    )
    assert [row["id"] for row in curation.active_directives(campaign)] == ["D-001"]


def test_template_directives_have_no_active_rows(campaign: Path) -> None:
    template = Path(__file__).resolve().parents[1] / "plugin" / "templates" / "campaign" / "directives.md"
    if not template.is_file():
        pytest.skip("directives template not present")
    (campaign / "directives.md").write_bytes(template.read_bytes())
    assert curation.active_directives(campaign) == []
    # The packet reads strictly; the shipped template must pass that reading.
    assert curation.active_directives(campaign, strict=True) == []


def test_packet_keeps_every_active_directive_up_to_the_cap(campaign: Path) -> None:
    rows = "".join(f"| D-{n:03d} | global | Rule {n}. | OOC | active |\n" for n in range(1, 31))
    _write(campaign / "directives.md", DIRECTIVE_TABLE + rows)
    packet = curation.build_packet(campaign, [("threads.md", "x")])
    # The first draft kept only the newest 24, silently dropping D-001..D-006.
    assert [row["id"] for row in packet["directives"]][:2] == ["D-001", "D-002"]
    assert len(packet["directives"]) == 30 and "directives_omitted" not in packet

    many = "".join(
        f"| D-{n:03d} | global | Rule {n}. | OOC | active |\n" for n in range(1, curation.MAX_DIRECTIVES + 6)
    )
    _write(campaign / "directives.md", DIRECTIVE_TABLE + many)
    packet = curation.build_packet(campaign, [("threads.md", "x")])
    assert len(packet["directives"]) == curation.MAX_DIRECTIVES
    assert packet["directives_omitted"] == 5
    assert packet["directives"][-1]["id"] == f"D-{curation.MAX_DIRECTIVES + 5:03d}"


def test_packet_is_refused_while_its_staged_file_waits(campaign: Path) -> None:
    targets = [("characters/witness.md", "stacked_sections")]
    packet = curation.build_packet(campaign, targets)
    staged = Path(packet["staging_path"])
    staged.parent.mkdir(parents=True)
    staged.write_bytes(b"{}")
    with pytest.raises(curation.CurationError) as caught:
        curation.build_packet(campaign, targets)
    assert caught.value.category == "already_staged"
    # Once processed, the same unchanged targets may be curated again.
    curation.move_processed(staged, "rejected")
    assert curation.build_packet(campaign, targets)["curation_id"] == packet["curation_id"]


def test_packet_refuses_a_target_that_is_not_utf8(campaign: Path) -> None:
    (campaign / "characters" / "eski.md").write_bytes("# Eski\n\nŞimdi.\n".encode("cp1254"))
    with pytest.raises(curation.CurationError) as caught:
        curation.build_packet(campaign, [("characters/eski.md", "x")])
    assert caught.value.category == "campaign_invalid"


@pytest.mark.parametrize("target", [("threads.md",), "threads.md", ("threads.md", "x", "y")])
def test_packet_refuses_a_malformed_target(campaign: Path, target: Any) -> None:
    with pytest.raises(curation.CurationError) as caught:
        curation.build_packet(campaign, [target])
    assert caught.value.category == "input_invalid"


def test_packet_reason_is_one_line(campaign: Path) -> None:
    packet = curation.build_packet(campaign, [("threads.md", "stacked\n sections\tand size")])
    assert packet["targets"] == [{"path": "threads.md", "reason": "stacked sections and size"}]


def test_staging_guard_can_require_the_packet_id(campaign: Path) -> None:
    own = curation.staging_path(campaign, "r0-own")
    other = curation.staging_path(campaign, "r0-other")
    assert curation.is_staging_path(campaign, own, "r0-own")
    assert not curation.is_staging_path(campaign, other, "r0-own")
    assert curation.is_staging_path(campaign, other)


def test_cli_validate_reports_readiness(campaign: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _stage(campaign, _payload(campaign))
    assert curation.main(["validate", str(campaign)]) == 0
    assert json.loads(capsys.readouterr().out)["files"][0]["ready"] is True
    witness = campaign / "characters" / "witness.md"
    witness.write_bytes(witness.read_bytes() + b"\nLater fact.\n")
    assert curation.main(["validate", str(campaign)]) == 0
    report = json.loads(capsys.readouterr().out)["files"][0]
    assert report["ready"] is False and report["stale_paths"] == ["characters/witness.md"]


def test_cli_output_is_ascii_for_non_ascii_names(campaign: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(campaign / "characters" / "şule.md", "# Şule\n")
    assert curation.main(["packet", str(campaign), "--target", "characters/şule.md=core_missing"]) == 0
    out = capsys.readouterr().out
    assert out.isascii()
    assert json.loads(out)["targets"][0]["path"] == "characters/şule.md"


# ---------------------------------------------------------------------------
# Second review: staged files that used to crash the writer
# ---------------------------------------------------------------------------


LINE_SEPARATOR = "\N{LINE SEPARATOR}"


def _deep_json(depth: int) -> bytes:
    return b"[" * depth + b"]" * depth


def _nested_list(depth: int) -> list[Any]:
    value: list[Any] = []
    for _ in range(depth):
        value = [value]
    return value


def _stage_raw(campaign: Path, name: str, raw: bytes, *, age: float = 120) -> Path:
    path = curation.curation_dir(campaign) / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    stamp = time.time() - age
    os.utime(path, (stamp, stamp))
    return path


def test_read_staged_types_a_file_nested_past_the_recursion_limit(campaign: Path) -> None:
    # json.loads raises RecursionError, not JSONDecodeError, for such a file.
    path = _stage_raw(campaign, "r0-witness", b'{"curation_id": "r0-witness", "mutations": ' + _deep_json(5000) + b"}")
    with pytest.raises(curation.CurationError) as caught:
        curation.read_staged(path)
    assert caught.value.category == "input_invalid" and "nests too deeply" in str(caught.value)
    assert curation.validate_file(campaign, path) == ["staged file nests too deeply to read"]


def test_read_staged_types_a_number_too_long_to_convert(campaign: Path) -> None:
    if not hasattr(sys, "get_int_max_str_digits"):
        pytest.skip("this Python converts integers of any length")
    # Python raises a bare ValueError (not a JSONDecodeError) past 4300 digits.
    path = _stage_raw(campaign, "r0-witness", b'{"curation_id": "r0-witness", "base_revision": ' + b"1" * 5000 + b"}")
    with pytest.raises(curation.CurationError) as caught:
        curation.read_staged(path)
    assert caught.value.category == "input_invalid" and "not UTF-8 JSON" in str(caught.value)
    errors = curation.validate_file(campaign, path)
    assert len(errors) == 1 and "not UTF-8 JSON" in errors[0]


def test_deep_nesting_is_refused_before_any_recursive_walk(campaign: Path) -> None:
    payload = _payload(campaign)
    payload["mutations"][0]["ops"][0]["text"] = _nested_list(5000)
    depth_error = f"nests deeper than {curation.MAX_DEPTH} levels"
    # Both used to raise RecursionError (placeholder search, op resolution).
    assert curation.validate_staged(campaign, payload) == [f"staged payload {depth_error}"]
    assert curation.dry_run(campaign, payload["mutations"], revision=0) == [f"mutations[0] {depth_error}"]


def test_a_staged_file_nested_too_deeply_for_curation_is_refused(campaign: Path) -> None:
    raw = json.dumps(_payload(campaign)).replace('"Nervous, waiting."', '"x", "pad": ' + "[" * 40 + "]" * 40)
    path = _stage_raw(campaign, "r0-witness", raw.encode("ascii"))
    assert curation.validate_file(campaign, path) == [f"staged payload nests deeper than {curation.MAX_DEPTH} levels"]


@pytest.mark.parametrize("where", ["text", "reason", "key", "path"])
def test_lone_surrogates_are_refused(campaign: Path, where: str) -> None:
    payload = _payload(campaign)
    if where == "text":
        payload["mutations"][0]["ops"][0]["text"] = "Calm " + chr(0xD800) + " now."
    elif where == "reason":
        payload["reason"] = "fold " + chr(0xDFFF) + " layers"
    elif where == "key":
        payload["mutations"][0]["ops"][0][chr(0xD83D)] = "x"
    else:
        payload["mutations"][0]["path"] = "characters/" + chr(0xDC80) + ".md"
    errors = curation.validate_staged(campaign, payload)
    assert len(errors) == 1 and "lone surrogate" in errors[0], errors


def test_an_escaped_lone_surrogate_in_a_staged_file_is_refused(campaign: Path) -> None:
    raw = json.dumps(_payload(campaign)).replace("Nervous, waiting.", "Nervous, \\ud800 waiting.")
    path = _stage_raw(campaign, "r0-witness", raw.encode("ascii"))
    errors = curation.validate_file(campaign, path)
    assert len(errors) == 1 and "lone surrogate" in errors[0]


def test_non_text_keys_are_an_error_not_a_crash(campaign: Path) -> None:
    payload = _payload(campaign)
    payload[7] = "x"  # type: ignore[index]
    assert curation.validate_staged(campaign, payload) == ["staged payload has a key that is not text: 7"]


def test_writer_rejects_malformed_staged_files_and_applies_later_ones(campaign: Path) -> None:
    """Each bad file used to raise out of commit_curation and stay staged, so
    every later proposal waited behind it forever."""

    rpg_state = pytest.importorskip("rpg_state")
    if not hasattr(rpg_state, "commit_curation"):
        pytest.skip("commit-curation is not integrated yet")
    bad = {
        "r0-deep": b'{"curation_id": "r0-deep", "mutations": ' + _deep_json(5000) + b"}",
        "r0-surrogate": json.dumps(_payload(campaign, curation_id="r0-surrogate"))
        .replace("Nervous, waiting.", "\\ud800")
        .encode("ascii"),
    }
    if hasattr(sys, "get_int_max_str_digits"):
        bad["r0-digits"] = b'{"curation_id": "r0-digits", "base_revision": ' + b"9" * 5000 + b"}"
    for offset, (name, raw) in enumerate(bad.items()):
        _stage_raw(campaign, name, raw, age=300 - offset)
    _stage_raw(campaign, "r0-good", json.dumps(_payload(campaign, curation_id="r0-good")).encode("ascii"), age=60)

    result = rpg_state.commit_curation(campaign)

    assert sorted(item["curation_id"] for item in result["rejected"]) == sorted(bad)
    assert [item["curation_id"] for item in result["applied"]] == ["r0-good"]
    assert curation.list_staged(campaign) == []
    assert "Nervous, waiting." in (campaign / "characters" / "witness.md").read_text(encoding="utf-8")


def test_cli_validate_reports_an_unreadable_file_instead_of_crashing(
    campaign: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _stage_raw(campaign, "r0-deep", b'{"curation_id": "r0-deep", "mutations": ' + _deep_json(5000) + b"}")
    assert curation.main(["validate", str(campaign)]) == 1
    report = json.loads(capsys.readouterr().out)["files"][0]
    assert report["ready"] is False and report["errors"] == ["staged file nests too deeply to read"]


def test_read_staged_stops_at_the_size_cap(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(curation, "MAX_STAGED_BYTES", 64)
    path = _stage_raw(campaign, "r0-witness", json.dumps(_payload(campaign)).encode("ascii"))
    with pytest.raises(curation.CurationError) as caught:
        curation.read_staged(path)
    assert caught.value.category == "input_invalid" and "exceeds 64 bytes" in str(caught.value)


def test_file_hash_reads_in_chunks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data = bytes(range(256)) * 50
    path = tmp_path / "big.md"
    path.write_bytes(data)
    monkeypatch.setattr(curation, "HASH_CHUNK", 7)
    assert curation.file_hash(path) == hashlib.sha256(data).hexdigest()


def test_split_by_freshness_tolerates_a_non_object(campaign: Path) -> None:
    assert curation.split_by_freshness(campaign, ["x"]) == ([], [])  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Second review: revision stamps as the full check reads them
# ---------------------------------------------------------------------------


STAMPED_MAP = (
    "# Relationship Map\n\nAs of revision: 3\n\n| From | Direction | To | Relation |\n"
    "| --- | --- | --- | --- |\n| Mira | -> | Witness | wary |\n"
)


def _map_mutation(*ops: dict[str, Any]) -> dict[str, Any]:
    return {"path": "relationship_map.md", "ops": list(ops)}


def test_dry_run_catches_a_stamp_in_another_letter_case(campaign: Path) -> None:
    _write(campaign / "relationship_map.md", STAMPED_MAP)
    message = "relationship_map.md: adds or changes an 'As of revision:' stamp; the writer sets stamps"
    # check_state reads the first stamp case-insensitively, so this forged line
    # would hide the map's staleness behind revision 99.
    forged = _map_mutation(
        {"op": "replace", "old": "# Relationship Map\n", "new": "# Relationship Map\n\nas of REVISION: 99\n"}
    )
    recased = _map_mutation({"op": "replace", "old": "As of revision: 3", "new": "As Of Revision: 3"})
    assert curation.dry_run(campaign, [forged], revision=3) == [message]
    assert curation.dry_run(campaign, [recased], revision=3) == [message]


def test_dry_run_catches_a_removed_stamp(campaign: Path) -> None:
    _write(campaign / "relationship_map.md", STAMPED_MAP)
    removed = _map_mutation({"op": "replace", "old": "As of revision: 3\n\n", "new": ""})
    assert curation.dry_run(campaign, [removed], revision=3) == [
        "relationship_map.md: removes the 'As of revision:' stamp; keep it, the writer updates it"
    ]
    row = _map_mutation(
        {"op": "upsert_row", "key": ["Mira", "->", "Witness"], "cells": ["Mira", "->", "Witness", "trusting"]}
    )
    assert curation.dry_run(campaign, [row], revision=3) == []


# ---------------------------------------------------------------------------
# Second review: op keys, paths, reasons, duplicates, caps
# ---------------------------------------------------------------------------


def test_op_key_table_covers_every_markdown_op() -> None:
    assert set(curation.MARKDOWN_OP_KEYS) == set(owner_ops.MARKDOWN_OPS)


def test_unknown_op_keys_are_refused(campaign: Path) -> None:
    # The writer ignores unknown keys: `parent` instead of `under` would put
    # the section at the end of the note without any error.
    payload = _payload(campaign)
    payload["mutations"][0]["ops"] = [
        {"op": "insert_section", "heading": "### Kin", "text": "- Ilse", "parent": "Current State"}
    ]
    assert curation.validate_staged(campaign, payload) == [
        "mutations[0].ops[0] has unknown key(s): parent; insert_section takes heading, text, under"
    ]


def test_every_documented_op_key_is_accepted(campaign: Path) -> None:
    payload = _payload(campaign)
    payload["mutations"][0]["ops"] = [
        {"op": "append", "heading": "Current State", "under": "Witness", "text": "x"},
        {"op": "upsert_row", "heading": "H", "under": "Witness", "table": 0, "key": ["a"], "cells": ["a", "b"]},
        {"op": "delete_row", "heading": "H", "under": "Witness", "table": 0, "key": "a"},
        {"op": "replace", "old": "a", "new": "b"},
        {"op": "remove_section", "heading": "H", "under": "Witness"},
        {"op": "replace_section", "heading": "H", "under": "Witness", "text": "x"},
        {"op": "insert_section", "heading": "## H", "under": "# Witness", "text": "x"},
    ]
    assert curation.validate_staged(campaign, payload) == []


@pytest.mark.parametrize(
    ("path", "fragment"),
    [
        # The writer and owner_ops accept only a lower-case '.md'.
        ("characters/Witness.MD", "lowercase '.md'"),
        # str.splitlines() breaks at these, so they are line breaks too.
        ("characters/wit" + LINE_SEPARATOR + "ness.md", "POSIX path"),
        ("characters/wit\x85ness.md", "POSIX path"),
        ("characters/" + "a" * 400 + ".md", "at most 400 characters"),
        ("directives.md", "Player's directives"),
        ("Directives.md", "Player's directives"),
    ],
)
def test_paths_the_writer_or_the_player_owns_are_refused(campaign: Path, path: str, fragment: str) -> None:
    errors = _errors_for_path(campaign, path)
    assert len(errors) == 1 and fragment in errors[0], errors


def test_directives_file_is_never_a_packet_target(campaign: Path) -> None:
    _write(campaign / "directives.md", DIRECTIVE_TABLE + "| D-001 | global | Keep it short. | OOC | active |\n")
    with pytest.raises(curation.CurationError) as caught:
        curation.build_packet(campaign, [("directives.md", "owner_size_budget")])
    assert caught.value.category == "path_forbidden"


@pytest.mark.parametrize(
    "value", ["fold" + LINE_SEPARATOR + "layers", "fold\x85layers", "fold\x00layers", "fold\x0blayers"]
)
def test_reason_holds_no_line_break_of_any_kind(campaign: Path, value: str) -> None:
    # The writer copies the reason into the session log.
    errors = curation.validate_staged(campaign, _payload(campaign, reason=value))
    assert errors == [f"reason must be one line of at most {curation.MAX_REASON} characters"]


def test_reason_may_hold_a_tab(campaign: Path) -> None:
    assert curation.validate_staged(campaign, _payload(campaign, reason="fold\tlayers")) == []


@pytest.mark.parametrize(
    ("first", "second"),
    [
        # NFC and NFD spellings of one name.
        ("characters/\N{LATIN CAPITAL LETTER I WITH DOT ABOVE}lse.md", "characters/I\N{COMBINING DOT ABOVE}lse.md"),
        # One file where the file system folds case.
        ("characters/ghost.md", "characters/GHOST.md"),
    ],
)
def test_two_spellings_of_one_file_are_one_mutation(campaign: Path, first: str, second: str) -> None:
    payload = _payload(
        campaign,
        base_hashes={},
        mutations=[
            {"path": first, "ops": [{"op": "append", "text": "x"}]},
            {"path": second, "ops": [{"op": "append", "text": "y"}]},
        ],
    )
    errors = curation.validate_staged(campaign, payload)
    assert f"mutations[1].path '{second}' repeats '{first}'; put all edits for one file in one mutation" in errors


def test_base_hash_table_is_capped(campaign: Path) -> None:
    hashes = {f"characters/n{index}.md": "0" * 64 for index in range(curation.MAX_BASE_HASHES + 1)}
    errors = curation.validate_staged(campaign, _payload(campaign, base_hashes=hashes, mutations=[]))
    assert errors == [f"base_hashes lists {curation.MAX_BASE_HASHES + 1} files; at most {curation.MAX_BASE_HASHES}"]


# ---------------------------------------------------------------------------
# Second review: the packet
# ---------------------------------------------------------------------------


def test_packet_caps_targets_at_the_mutation_limit(campaign: Path) -> None:
    targets = []
    for index in range(curation.MAX_MUTATIONS + 1):
        _write(campaign / "characters" / f"n{index}.md", f"# N{index}\n")
        targets.append((f"characters/n{index}.md", "core_missing"))
    # The curator could never stage one mutation per target for this packet.
    with pytest.raises(curation.CurationError) as caught:
        curation.build_packet(campaign, targets)
    assert caught.value.category == "input_invalid"
    assert f"at most {curation.MAX_MUTATIONS} targets" in str(caught.value)
    assert len(curation.build_packet(campaign, targets[:-1])["targets"]) == curation.MAX_MUTATIONS


def test_packet_names_a_missing_campaign(tmp_path: Path) -> None:
    with pytest.raises(curation.CurationError) as caught:
        curation.build_packet(tmp_path / "nowhere", [("threads.md", "x")])
    assert caught.value.category == "campaign_invalid" and "no current_state.yaml" in str(caught.value)


def test_packet_refuses_a_folder_target_and_a_non_text_reason(campaign: Path) -> None:
    (campaign / "characters" / "folder.md").mkdir()
    with pytest.raises(curation.CurationError) as caught:
        curation.build_packet(campaign, [("characters/folder.md", "x")])
    assert caught.value.category == "campaign_invalid" and "not a file" in str(caught.value)
    with pytest.raises(curation.CurationError) as caught:
        curation.build_packet(campaign, [("threads.md", 5)])  # type: ignore[list-item]
    assert caught.value.category == "input_invalid"


def test_packet_reason_drops_control_characters(campaign: Path) -> None:
    packet = curation.build_packet(campaign, [("threads.md", "stacked" + LINE_SEPARATOR + "sections\x00 now")])
    assert packet["targets"][0]["reason"] == "stacked sections now"


def test_directive_tables_in_fenced_code_are_examples(campaign: Path) -> None:
    _write(
        campaign / "directives.md",
        "How a row looks:\n\n```markdown\n"
        + DIRECTIVE_TABLE
        + "| D-900 | global | Fenced example. | doc | active |\n```\n\n"
        + DIRECTIVE_TABLE
        + "| D-001 | global | Real. | OOC | active |\n",
    )
    assert [row["id"] for row in curation.active_directives(campaign)] == ["D-001"]


def test_comment_markers_inside_fenced_code_hide_nothing(campaign: Path) -> None:
    _write(
        campaign / "directives.md",
        "```html\n<!-- shown literally\n```\n\n" + DIRECTIVE_TABLE + "| D-001 | global | Real. | OOC | active |\n",
    )
    assert [row["id"] for row in curation.active_directives(campaign)] == ["D-001"]


def test_an_empty_html_comment_closes_on_its_own_line(campaign: Path) -> None:
    _write(
        campaign / "directives.md",
        DIRECTIVE_TABLE
        + "| D-001 | global | One. | OOC | active | <!-->\n"
        + "| D-002 | global | Two. | OOC | active |\n",
    )
    assert [row["id"] for row in curation.active_directives(campaign)] == ["D-001", "D-002"]


def test_escaped_pipes_in_a_directive_read_as_pipes(campaign: Path) -> None:
    _write(campaign / "directives.md", DIRECTIVE_TABLE + "| D-001 | global | Say \\| never. | OOC | active |\n")
    assert curation.active_directives(campaign, strict=True) == [
        {"id": "D-001", "scope": "global", "directive": "Say | never."}
    ]


def test_directives_with_a_byte_order_mark_before_the_table(campaign: Path) -> None:
    (campaign / "directives.md").write_bytes(
        b"\xef\xbb\xbf" + (DIRECTIVE_TABLE + "| D-001 | global | Real. | OOC | active |\n").encode("utf-8")
    )
    assert [row["id"] for row in curation.active_directives(campaign)] == ["D-001"]


def test_a_row_with_an_unescaped_pipe_blocks_the_packet(campaign: Path) -> None:
    _write(campaign / "directives.md", DIRECTIVE_TABLE + "| D-001 | global | Never say a | b word. | OOC | active |\n")
    # Read leniently, the Status column shifts and the directive vanishes...
    assert curation.active_directives(campaign) == []
    # ...so the packet refuses instead of handing the curator a short list.
    with pytest.raises(curation.CurationError) as caught:
        curation.build_packet(campaign, [("threads.md", "x")])
    assert caught.value.category == "campaign_invalid" and "D-001" in str(caught.value)


def test_packet_refuses_an_unreadable_directives_file(campaign: Path) -> None:
    row = "| D-001 | global | \N{LATIN CAPITAL LETTER S WITH CEDILLA}imdi. | OOC | active |\n"
    (campaign / "directives.md").write_bytes((DIRECTIVE_TABLE + row).encode("cp1254"))
    assert curation.active_directives(campaign) == []
    with pytest.raises(curation.CurationError) as caught:
        curation.build_packet(campaign, [("threads.md", "x")])
    assert caught.value.category == "campaign_invalid" and "directives.md" in str(caught.value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("characters/a=b.md=stacked_sections", ("characters/a=b.md", "stacked_sections")),
        ("characters/a=b.md", ("characters/a=b.md", "")),
        ("threads.md=size=310000", ("threads.md", "size=310000")),
        ("threads.md", ("threads.md", "")),
        ("characters/x.MD=r", ("characters/x.MD", "r")),
    ],
)
def test_cli_target_keeps_an_equals_sign_in_the_file_name(value: str, expected: tuple[str, str]) -> None:
    assert curation._parse_target(value) == expected


def test_agent_prompt_states_the_limits_the_validator_enforces() -> None:
    _, body = _agent_parts()
    # A longer reason, an extra op key, or a Core block that splits the
    # Agency Card used to get a whole proposal rejected or break the note.
    assert f"at most {curation.MAX_REASON} characters" in body
    assert "with no other keys" in body
    assert "never inside another section" in body
    assert "Agency Card field" in body

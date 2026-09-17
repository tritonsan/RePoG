"""Structural boundaries reject lost identity/history without judging story prose."""

from pathlib import Path
from types import SimpleNamespace

import pytest

import narrative_memory as memory


def rules(findings):
    return {finding["rule"] for finding in findings}


def act(act_id="act-two", status="active", previous="act-one", opened=4):
    text = f"""- Act id: {act_id}
- Act status: {status}
- Previous act id: {previous}
- Opened at revision: {opened}
- Dramatic question: Can the workshop reopen on its own terms?
- Closure conditions: Its permit is granted or the workshop abandons the application.
- Places this act can reach: Workshop and permit office.
- People who belong to it: Ada and the clerk.
- What is already in motion as it opens: The clerk reviews the application.
- What stays true if the character does nothing: The workshop continues ordinary repairs.
"""
    if status == "closed":
        text += f"""#### Closure Record
- Closing action: The player declined the offered terms.
- Condition met or foreclosed: The current application was abandoned.
- Recorded at revision: {opened + 3}
"""
    return text


def threads(current, *archive):
    return "# Threads\n\n## Arc Compass\n\n" + current + "\n## Act Archive\n" + "\n".join(
        f"### {next(line.split(':', 1)[1].strip() for line in body.splitlines() if line.startswith('- Act id:'))}\n{body}"
        for body in archive
    )


def first_closed():
    return act("act-one", "closed", "none", 0)


def account(account_id="heard-one", holder="ada", fact="permit-result", **updates):
    fields = {"Account id": account_id, "Holder ref": holder, "Fact id": fact,
              "Account": "The application may be delayed.", "Stance": "suspected",
              "Source ref": "letter-one", "Learned at": "Day 2, morning", "Recorded revision": "4",
              "Supersedes": "none", "Correction ref": "none"}
    fields.update(updates)
    return f"### {account_id}\n" + "\n".join(f"- {key}: {value}" for key, value in fields.items()) + "\n"


def lookup(reference="threads.md#arc-compass", lookup_id="workshop-return", revision=4):
    return f"""### Return to the workshop
- Lookup id: {lookup_id}
- Signals: Ada, the workshop, the old permit
- Owner ref: {reference}
- Why now: The player asks about the application or returns to the workshop.
- Verified at revision: {revision}
"""


@pytest.fixture
def campaign(tmp_path):
    (tmp_path / "threads.md").write_text(threads(act(), first_closed()), encoding="utf-8")
    (tmp_path / "opening_brief.md").write_text("Opening status: active\nOpening act id: act-two\n", encoding="utf-8")
    (tmp_path / "next_act_prep.md").write_text("## Prep Status\n- Prep status: ready\n- Previous act id: act-one\n- Next act id: act-two\n", encoding="utf-8")
    (tmp_path / "session_brief.md").write_text("## Triggered Lookups\n" + lookup(), encoding="utf-8")
    (tmp_path / "knowledge_boundaries.md").write_text("## Holder Accounts\n" + account(), encoding="utf-8")
    (tmp_path / "current_state.yaml").write_text("continuity_revision: 4\n", encoding="utf-8")
    return tmp_path


def test_valid_two_act_memory_and_current_accounts(campaign):
    assert memory.check_threads((campaign / "threads.md").read_text(), campaign / "threads.md", ready=True) == []
    assert memory.check_accounts((campaign / "knowledge_boundaries.md").read_text(), campaign / "knowledge_boundaries.md") == []
    assert memory.check_references(campaign, ready=True) == []


def test_legacy_and_blank_templates_do_not_adopt_contract():
    legacy = "## Arc Compass\n- Dramatic question: A real legacy question.\n- Closure conditions: A valid legacy ending.\n"
    assert memory.check_threads(legacy, "threads.md") == []
    findings = memory.check_threads(legacy, "threads.md", ready=True)
    assert rules(findings) == {"act_identity_legacy"} and findings[0]["severity"] == "warning"
    assert memory.check_threads("## Arc Compass\n- Act id:\n- Act status: planned\n", "threads.md") == []
    assert memory.check_accounts("## Holder Accounts\n### Placeholder\n- Account id:\n", "knowledge.md") == []
    assert memory.check_thread_transition(legacy, threads(act("first", previous="none")), "threads.md") == []


def test_real_distribution_templates_are_optional_and_do_not_become_state():
    source = Path(__file__).resolve().parents[1] / "campaign"
    assert memory.check_threads((source / "threads.md").read_text(encoding="utf-8"), "threads.md") == []
    assert memory.check_accounts((source / "knowledge_boundaries.md").read_text(encoding="utf-8"), "knowledge.md") == []


@pytest.mark.parametrize(("old", "new", "expected"), [
    ("- Act id: act-two", "- Act id: act-one", "act_id_reused"),
    ("- Previous act id: act-one", "- Previous act id: missing", "act_previous_invalid"),
    ("- Act status: active", "- Act status: ready", "act_status_invalid"),
    ("- Opened at revision: 4", "- Opened at revision: -1", "act_opened_revision_invalid"),
    ("- Dramatic question: Can the workshop reopen on its own terms?", "- Dramatic question:", "act_compass_incomplete"),
    ("- Closing action: The player declined the offered terms.", "- Closing action:", "act_closure_evidence_missing"),
    ("- Recorded at revision: 3", "- Recorded at revision: -1", "act_closed_revision_invalid"),
])
def test_declared_modern_act_rejects_structural_drift(old, new, expected):
    text = threads(act(), first_closed()).replace(old, new)
    assert expected in rules(memory.check_threads(text, "threads.md", ready=True))


def test_planned_draft_can_be_partial_but_not_ready():
    draft = "## Arc Compass\n- Act id: proposed\n- Act status: planned\n- Previous act id: none\n"
    assert memory.check_threads(draft, "threads.md") == []
    assert "act_not_playable" in rules(memory.check_threads(draft, "threads.md", ready=True))


def test_duplicate_fields_and_previous_cycles_are_detected():
    text = threads(act() + "- Act id: replaced\n", first_closed())
    assert "act_field_duplicate" in rules(memory.check_threads(text, "threads.md"))
    cycle = threads(act("three", previous="one"), act("one", "closed", "two", 0), act("two", "closed", "one", 4))
    assert "act_previous_cycle" in rules(memory.check_threads(cycle, "threads.md"))


def test_stale_closure_and_misnamed_archive_do_not_fit_the_new_act():
    text = threads(act() + "- Closing action: An old act's final action.\n", first_closed()).replace("### act-one", "### wrong-id")
    assert {"act_closure_stale", "act_archive_heading_mismatch"} <= rules(memory.check_threads(text, "threads.md"))


def test_code_examples_and_comments_do_not_declare_live_acts():
    text = "```md\n" + threads(act()) + "```\n<!--\n" + threads(act()) + "\n-->"
    assert memory.check_threads(text, "threads.md", ready=True) == []


def test_safe_successor_preserves_closed_evidence_but_can_reformat_prose():
    before = threads(first_closed())
    archived = first_closed().replace("#### Closure Record", "#### Completed closure")
    after = threads(act(), archived)
    assert memory.check_thread_transition(before, after, "threads.md", revision=4) == []
    assert "act_activation_revision_mismatch" in rules(memory.check_thread_transition(before, after, "threads.md", revision=5))


@pytest.mark.parametrize("mutation", ["drop", "change", "reset", "erase"])
def test_transition_rejects_loss_or_rewrite_of_committed_history(mutation):
    before = threads(act(), first_closed())
    if mutation == "drop":
        after = threads(act())
        expected = "act_archive_removed"
    elif mutation == "change":
        after = before.replace("The player declined the offered terms.", "The player signed the terms.")
        expected = "act_archive_changed"
    elif mutation == "reset":
        after = threads(act("unrelated", previous="none", opened=5), first_closed())
        expected = "act_successor_before_closure"
    else:
        after = "## Arc Compass\n- Act id:\n"
        expected = "act_identity_removed"
    assert expected in rules(memory.check_thread_transition(before, after, "threads.md"))


def test_closed_act_cannot_reopen_or_rewrite_its_decisive_action():
    before = threads(first_closed())
    after = before.replace("- Act status: closed", "- Act status: active")
    assert "act_reopened" in rules(memory.check_thread_transition(before, after, "threads.md"))
    after = before.replace("The player declined the offered terms.", "The player accepted everything.")
    assert "act_archive_changed" in rules(memory.check_thread_transition(before, after, "threads.md"))


def test_closure_revision_belongs_to_closing_commit():
    before = threads(act("one", previous="none", opened=0))
    after = threads(act("one", "closed", "none", 0))
    assert memory.check_thread_transition(before, after, "threads.md", revision=3) == []
    assert "act_closure_revision_mismatch" in rules(memory.check_thread_transition(before, after, "threads.md", revision=4))


@pytest.mark.parametrize(("updates", "expected"), [
    ({"Source ref": ""}, "holder_account_incomplete"),
    ({"Stance": "omniscient"}, "holder_account_stance_invalid"),
    ({"Recorded revision": "-1"}, "holder_account_revision_invalid"),
    ({"Supersedes": "heard-one"}, "holder_account_supersedes_invalid"),
    ({"Supersedes": "older-account"}, "holder_account_correction_missing"),
])
def test_account_shapes_are_checked_without_assessing_prose(updates, expected):
    assert expected in rules(memory.check_accounts("## Holder Accounts\n" + account(**updates), "knowledge.md"))


def test_accounts_have_unique_ids_and_holder_fact_pairs():
    text = "## Holder Accounts\n" + account() + account("heard-two") + account(holder="ben")
    assert {"holder_account_id_duplicate", "holder_account_pair_duplicate"} <= rules(memory.check_accounts(text, "knowledge.md"))


def test_distinct_holders_may_hold_conflicting_accounts_and_unknown_time():
    text = "## Holder Accounts\n" + account() + account("ben-heard", "ben", **{
        "Account": "The application has already been accepted.", "Stance": "confirmed", "Learned at": "unknown",
    })
    assert memory.check_accounts(text, "knowledge.md") == []  # Meaning/credibility belongs to the agent.


def test_pending_proposal_and_consumed_archived_opening_are_valid(campaign):
    path = campaign / "opening_brief.md"
    path.write_text("Opening status: pending\nOpening act id: proposed-three\n")
    assert memory.check_references(campaign) == []
    path.write_text("Opening status: consumed\nOpening act id: act-one\n")
    assert memory.check_references(campaign) == []
    path.write_text("Opening status: active\nOpening act id: act-one\n")
    assert "opening_act_mismatch" in rules(memory.check_references(campaign))


def test_used_prep_may_reference_historical_pair_while_ready_targets_current(campaign):
    path = campaign / "threads.md"
    path.write_text(threads(act("act-three", previous="act-two", opened=8), first_closed(), act("act-two", "closed", "act-one", 4)))
    (campaign / "current_state.yaml").write_text("continuity_revision: 8\n")
    (campaign / "opening_brief.md").write_text("Opening status: consumed\nOpening act id: act-two\n")
    prep = campaign / "next_act_prep.md"
    assert "prep_act_mismatch" in rules(memory.check_references(campaign))
    prep.write_text(prep.read_text().replace("status: ready", "status: used"))
    assert memory.check_references(campaign) == []


@pytest.mark.parametrize("reference", ["threads.md#Arc Compass", "threads.md#arc-compass", "threads.md#act-one", "knowledge_boundaries.md#permit-result"])
def test_exact_heading_anchors_and_explicit_ids_are_accepted(campaign, reference):
    (campaign / "session_brief.md").write_text("## Triggered Lookups\n" + lookup(reference))
    assert memory.check_references(campaign) == []


@pytest.mark.parametrize(("reference", "expected"), [
    ("threads.md#slightly-similar-compass", "memory_reference_fragment_missing"),
    ("threads.md", "memory_reference_fragment_missing"),
    ("absent.md#absent", "memory_reference_missing"),
    ("../private.md#secret", "memory_reference_unsafe"),
    ("/absolute.md#secret", "memory_reference_unsafe"),
    ("C:/private.md#secret", "memory_reference_unsafe"),
    ("characters\\ada.md#secret", "memory_reference_unsafe"),
    ("snapshots/old.md#secret", "memory_reference_unsafe"),
    ("Snapshots/old.md#secret", "memory_reference_unsafe"),
    (".GIT/HEAD#secret", "memory_reference_unsafe"),
    (".REPOG-TRANSACTIONS/old.md#secret", "memory_reference_unsafe"),
])
def test_invalid_or_escaping_owner_references_are_rejected(campaign, reference, expected):
    (campaign / "session_brief.md").write_text("## Triggered Lookups\n" + lookup(reference))
    assert expected in rules(memory.check_references(campaign))


def test_symlink_owner_is_rejected_without_reading_external_text(campaign, tmp_path):
    target = tmp_path.parent / (tmp_path.name + "-outside.md")
    target.write_text("# External\n")
    link = campaign / "link.md"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("Host cannot create symbolic links")
    (campaign / "session_brief.md").write_text("## Triggered Lookups\n" + lookup("link.md#external"))
    assert "memory_reference_unsafe" in rules(memory.check_references(campaign))


def test_empty_fact_id_does_not_consume_the_following_line(campaign):
    (campaign / "blank.md").write_text("# Blank\n- Fact id:\n- Status: active\n")
    (campaign / "session_brief.md").write_text("## Triggered Lookups\n" + lookup("blank.md#- Status: active"))
    assert "memory_reference_fragment_missing" in rules(memory.check_references(campaign))


def test_windows_reparse_attribute_is_rejected_without_platform_specific_api(campaign, monkeypatch):
    target = campaign / "linked.md"
    target.write_text("# Linked\n")
    original = Path.lstat

    def lstat(path, *args, **kwargs):
        result = original(path, *args, **kwargs)
        return SimpleNamespace(st_mode=result.st_mode, st_file_attributes=1024) if path == target else result

    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(memory.stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024, raising=False)
    (campaign / "session_brief.md").write_text("## Triggered Lookups\n" + lookup("linked.md#linked"))
    assert "memory_reference_unsafe" in rules(memory.check_references(campaign))


def test_future_revisions_are_reported_separately_from_semantics(campaign):
    (campaign / "current_state.yaml").write_text("continuity_revision: 2\n")
    assert {"act_revision_future", "memory_lookup_revision_future", "holder_account_revision_future"} <= rules(memory.check_references(campaign))


def test_legacy_lookup_is_not_parsed_as_new_record(campaign):
    (campaign / "session_brief.md").write_text("## Triggered Lookups\n- Return -> existing freeform owner\n")
    assert memory.check_references(campaign) == []


def test_read_limit_reports_unverified_reference_instead_of_loading_large_source(campaign, monkeypatch):
    (campaign / "large.md").write_text("# Topic\n" + "a" * 5000)
    (campaign / "session_brief.md").write_text("## Triggered Lookups\n" + lookup("large.md#topic"))
    monkeypatch.setattr(memory, "MAX_FILE_BYTES", 3000)
    findings = memory.check_references(campaign)
    assert "memory_reference_limit" in rules(findings)
    assert all(item["severity"] == "warning" for item in findings)

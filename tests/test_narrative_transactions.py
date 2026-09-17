"""Narrative identity guards run before real owner transactions, not after them."""
from pathlib import Path
import json
import subprocess
import sys

import pytest

from test_rpg_state import campaign, rpg_state


ROOT = Path(__file__).resolve().parents[1]


def compass(identity="act_return", status="active", previous="none", revision=0):
    closing = "Returned the plane before dusk." if status == "closed" else ""
    condition = "Timely return fulfilled." if status == "closed" else ""
    return f"""- Act id: {identity}
- Act status: {status}
- Previous act id: {previous}
- Opened at revision: {revision}
- Dramatic question: What becomes of the borrowed tool?
- Closure conditions: The tool is returned or its loss is established.
### Act Scope
- Places this act can reach: Workshop and inn
- People who belong to it: Ece and Mira
- What is already in motion as it opens: The borrowed tool is due back.
- What stays true if the character does nothing: Ece closes the workshop at dusk.
### Closure Record
- Closing action: {closing}
- Condition met or foreclosed: {condition}
- Recorded at revision: {1 if closing else ''}
"""


def threads(current, archived=""):
    return f"# Threads\n\n## Arc Compass\n{current}\n## Act Archive\n{archived}"


def payload(path, before, after, revision=0, operation="continuity-change"):
    return {
        "operation_id": operation,
        "expected_continuity_revision": revision,
        "boundary": "ordinary",
        "cause": "The player returned the borrowed tool; the scoped consequence is recorded.",
        "resume_impact": "The next exchange uses the committed question and limits.",
        "changes": [{"id": "continuity", "kind": "knowledge" if path == "knowledge_boundaries.md" else "act",
                     "established_delta": "The established continuity is recorded.",
                     "owners": [path], "cold_targets": []}],
        "mutations": [{"path": path, "exact_replacements": [{"old": before, "new": after}]}],
    }


def cli_commit(campaign, value, command="commit-durable"):
    process = subprocess.run(
        [sys.executable, "-B", str(ROOT / "tools/rpg_state.py"), str(campaign), command,
         "--input-json", json.dumps(value)], capture_output=True, text=True, encoding="utf-8",
        timeout=30,
    )
    assert process.stdout.strip(), process.stderr
    result = json.loads(process.stdout)
    assert process.returncode == 0, (result, process.stderr)
    return result


def test_two_process_act_turnover_retains_old_evidence_and_resets_current_closure(campaign):
    active = threads(compass())
    closed_body = compass(status="closed")
    closed = threads(closed_body)
    (campaign / "threads.md").write_text(active, encoding="utf-8")
    first = cli_commit(campaign, payload("threads.md", active, closed, operation="close-return"))
    assert first["continuity_revision"] == 1
    successor = compass("act_work", previous="act_return", revision=2).replace(
        "What becomes of the borrowed tool?", "Can the player establish an independent workshop?"
    ).replace("The tool is returned or its loss is established.", "A lease is accepted or the attempt is abandoned.")
    archive = "### act_return\n" + closed_body.replace("### Act Scope", "#### Act Scope").replace(
        "### Closure Record", "#### Closure Record"
    )
    next_text = threads(successor, archive)
    second = cli_commit(campaign, payload("threads.md", closed, next_text, 1, "activate-work"))
    assert second["continuity_revision"] == 2
    reloaded = (campaign / "threads.md").read_text(encoding="utf-8")
    current, history = reloaded.split("## Act Archive", 1)
    assert "Act id: act_work" in current and "Closing action: \n" in current
    assert "Returned the plane before dusk." in history
    assert (campaign / "session_log.md").read_text(encoding="utf-8").count("### Durable Revision") == 2
    assert cli_commit(campaign, payload("threads.md", closed, next_text, 1, "activate-work"))["idempotent"]


@pytest.mark.parametrize("before,after", [
    (threads(compass()), threads(compass("act_work", revision=1))),
    (threads(compass(status="closed")), threads(compass())),
    (threads(compass()), threads(compass(status="planned"))),
    (threads(compass()), "# Threads\n\n## Arc Compass\n- Act id:\n"),
    (threads(compass(status="closed")), threads(compass("act_work", previous="act_return", revision=1))),
], ids=["skipped-closure", "reopened-id", "back-to-draft", "dropped-identity", "lost-archive"])
def test_identity_loss_or_illegal_reopening_is_rejected_atomically(campaign, before, after):
    (campaign / "threads.md").write_text(before, encoding="utf-8")
    frozen = {p: p.read_bytes() for p in campaign.rglob("*") if p.is_file()}
    with pytest.raises(rpg_state.RPGStateError) as error:
        rpg_state.commit_durable(campaign, payload("threads.md", before, after))
    assert error.value.category == "candidate_invalid"
    assert all(p.read_bytes() == old for p, old in frozen.items())


def test_duplicate_holder_account_cannot_commit_or_advance_revision(campaign):
    path = campaign / "knowledge_boundaries.md"
    before = path.read_text(encoding="utf-8")
    account = """### Ece's account
- Account id: returned
- Holder ref: characters/ece.md
- Fact id: plane_return
- Account: Saw the plane returned intact; the old account remains disputed.
- Stance: confirmed
- Source ref: session_log.md#return
- Learned at: day 1 afternoon
- Recorded revision: 1
- Supersedes: none
- Correction ref: none
"""
    after = before + "\n## Holder Accounts\n" + account + account.replace("returned", "second", 1)
    with pytest.raises(rpg_state.RPGStateError) as error:
        rpg_state.commit_durable(campaign, payload(path.name, before, after))
    assert error.value.category == "candidate_invalid"
    assert path.read_text(encoding="utf-8") == before
    assert "continuity_revision: 0" in (campaign / "current_state.yaml").read_text(encoding="utf-8")


def test_valid_thread_change_does_not_scan_lookup_files(campaign, monkeypatch):
    checks = rpg_state._candidate_checker()._narrative_checks()

    def forbidden(*args, **kwargs):
        raise AssertionError("Ordinary owner validation must not run the full reference audit")

    monkeypatch.setattr(checks, "check_references", forbidden)
    before = threads(compass())
    after = before.replace("What becomes of the borrowed tool?", "Will the tool be returned in time?")
    (campaign / "threads.md").write_text(before, encoding="utf-8")
    assert rpg_state.commit_durable(campaign, payload("threads.md", before, after))["ok"]


def test_unfinished_reply_checkpoint_survives_process_restart_without_fictional_revision(campaign):
    anchor = "Ece asks whether Mira wants tea now or later; Mira has not answered."
    value = {
        "operation_id": "reply-handoff", "expected_continuity_revision": 0,
        "checkpoint": {"scene_id": "dock-interview", "scene_mode": "focused",
                       "resume_anchor": anchor, "active_cast_handoff": "none"},
        "mutations": [{"path": "current_state.yaml", "exact_replacements": [{
            "old": "resume_anchor: The witness waits for the next question.", "new": "resume_anchor: " + anchor,
        }]}],
    }
    first = cli_commit(campaign, value, "commit-checkpoint")
    assert first["continuity_revision"] == 0
    assert anchor in (campaign / "current_state.yaml").read_text(encoding="utf-8")
    assert cli_commit(campaign, value, "commit-checkpoint")["idempotent"]

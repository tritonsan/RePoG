"""Reproduce setup/readiness defects using disposable, synthetic campaigns.

Run from any directory with the repository's Python/pytest environment:
    python semantic-review/runs/2026-09-17-session-zero-audit/probe_session_zero.py

The script imports existing test builders (therefore needs pytest), executes
their lifecycle assertions, and calls the production validators and durable
writer. Product sources and campaign/ are read only. Synthetic campaigns are
created beneath a TemporaryDirectory in this artifact folder, then removed.
The only persistent output is probe_session_zero_results.json beside this file.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tests")]

import check_state
import rpg_state
import snapshot
import test_deep_session_zero_v8_integration as fixture


def errors(report):
    return [finding for finding in report["findings"] if finding["severity"] == "error"]


def probe_revision(campaign, operation_id):
    state = fixture.session_zero_state.validate_campaign_state(campaign)["state"]
    decision = next(
        item for item in state["decisions"]
        if item["decision_id"] == "01_player_fantasy_tone_and_non_goals"
    )
    payload = {
        key: value for key, value in decision.items()
        if key not in {"created_revision", "revision"}
    }
    payload.update(
        operation_id=operation_id,
        expected_revision=state["setup_revision"],
        value={"choice": "A revised player fantasy and tone"},
    )
    protected = ("session_zero_state.json", "setup_profile.yaml", "session_zero.md")
    before = {name: hashlib.sha256((campaign / name).read_bytes()).hexdigest() for name in protected}
    try:
        result = fixture.session_zero_state.record_decision(campaign, payload)
    except fixture.session_zero_state.StateError as exc:
        result = {"ok": False, "error_category": exc.category, "error": str(exc)}
    after = {name: hashlib.sha256((campaign / name).read_bytes()).hexdigest() for name in protected}
    return {
        "decision_id": decision["decision_id"],
        "expected_revision": state["setup_revision"],
        "setup_ready": "ready_for_play: true" in (campaign / "setup_profile.yaml").read_text(encoding="utf-8"),
        "result": result,
        "state_unchanged": before == after,
    }


def main():
    output = {
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python": sys.version,
        "fixture": "tests/test_deep_session_zero_v8_integration.py::test_topology_replay_reaches_ready_through_the_full_lifecycle[personal_drama]",
        "notes": [
            "The imported test builds accepted setup and genuine full-preflight runtime owners without an LLM.",
            "This is deterministic integration evidence, not a qualitative live GM playtest.",
            "No product sources or live campaign state are mutated.",
        ],
        "deep": [],
    }
    manifest = json.loads(fixture.MANIFEST_PATH.read_text(encoding="utf-8"))
    original_new = fixture._new_deep_campaign
    original_gate = fixture._record_gate
    for version in (8, 9):
        row = {"setup_schema_version": version}
        with tempfile.TemporaryDirectory(prefix="synthetic_session0_", dir=HERE) as directory:
            def new_campaign(tmp_path, manifest):
                campaign = original_new(tmp_path, manifest)
                fixture._set_setup(campaign, schema_version=version)
                return campaign

            def record_gate(campaign, **kwargs):
                if version == 8 and kwargs.get("gate_id") == "draft_preflight_passed":
                    row["revision_before_ready"] = probe_revision(campaign, "audit-pre-ready-revision")
                return original_gate(campaign, **kwargs)

            fixture._new_deep_campaign = new_campaign
            fixture._record_gate = record_gate
            fixture.test_topology_replay_reaches_ready_through_the_full_lifecycle(
                Path(directory), manifest, "personal_drama"
            )
            campaign = Path(directory) / "campaign"
            baseline = check_state.check_campaign(campaign, scope="full")
            row["lifecycle_test_assertions_passed"] = True
            row["canonical_ready_validator_ok"] = fixture.session_zero_state.validate_campaign_state(
                campaign, require_ready=True
            )["ok"]
            row["baseline_full_check"] = {"error_count": baseline["error_count"], "errors": errors(baseline)}
            if version == 8:
                row["revision_after_ready"] = probe_revision(campaign, "audit-post-ready-revision")
                profile = (campaign / "play_profile.yaml").read_text(encoding="utf-8")
                row["world_voices_profile"] = check_state._nested_values(check_state._block(profile, "world_voices"))
                row["world_voices_index_before"] = json.loads((campaign / "world_voices/index.json").read_text(encoding="utf-8"))
                text = (campaign / "threads.md").read_text(encoding="utf-8")
                payload = {
                    "operation_id": "audit-first-durable",
                    "expected_continuity_revision": 0,
                    "boundary": "ordinary",
                    "cause": "The player accepted a delivery task.",
                    "resume_impact": "The agreed delivery remains open.",
                    "changes": [{
                        "id": "accepted-delivery", "kind": "thread",
                        "established_delta": "The player agreed to deliver a sealed letter.",
                        "owners": ["threads.md"], "cold_targets": [],
                    }],
                    "mutations": [{"path": "threads.md", "exact_replacements": [{
                        "old": text,
                        "new": text + "\n- Agreed delivery: Carry a sealed letter to the harbor office.\n",
                    }]}],
                }
                row["durable_payload"] = payload
                row["durable_commit"] = rpg_state.commit_durable(campaign, payload)
                after = check_state.check_campaign(campaign, scope="full")
                row["post_commit_full_check"] = {"error_count": after["error_count"], "errors": errors(after)}
            output["deep"].append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    fixture._new_deep_campaign = original_new
    fixture._record_gate = original_gate

    with tempfile.TemporaryDirectory(prefix="synthetic_snapshot_", dir=HERE) as directory:
        campaign = Path(directory)
        (campaign / "current_state.yaml").write_text("campaign_id: audit\ncontinuity_revision: 0\n", encoding="utf-8")
        (campaign / "setup_profile.yaml").write_text(
            "schema_version: 9\nsetup_revision: 9\nstatus: complete\nready_for_play: true\nexperience_mode: rpg\nsession_zero_mode: quick\n",
            encoding="utf-8",
        )
        snapshot.create_snapshot(campaign, "session-zero-start")
        setup = check_state._setup_context(campaign, [])
        before, after = [], []
        check_state._check_ready_snapshot(campaign, setup=setup, findings=before)
        (campaign / "current_state.yaml").write_text("campaign_id: audit\ncontinuity_revision: 1\n", encoding="utf-8")
        check_state._check_ready_snapshot(campaign, setup=setup, findings=after)
        output["generic_start_snapshot_check"] = {
            "scope": "Isolated _check_ready_snapshot contract probe, not a full campaign fixture",
            "continuity_0": before, "continuity_1": after,
        }
    target = HERE / "probe_session_zero_results.json"
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(str(target), flush=True)


if __name__ == "__main__":
    main()

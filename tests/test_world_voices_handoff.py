"""A dormant World Voices store can catch up to an established causal event."""

import json
from pathlib import Path

import pytest

import check_world_voices
import world_voices


@pytest.fixture()
def campaign(tmp_path: Path) -> Path:
    (tmp_path / "world_voices").mkdir()
    (tmp_path / "world_voices/index.json").write_text(json.dumps({
        "schema_version": 1, "revision": 0, "continuity_revision": 0,
        "operation_sequence": 0, "completed_operations": {}, "artifacts": {},
    }), encoding="utf-8")
    (tmp_path / "current_state.yaml").write_text("continuity_revision: 5\n", encoding="utf-8")
    (tmp_path / "play_profile.yaml").write_text(
        "world_voices:\n  mode: on_demand\n  approval_policy: review_each\n  dashboard_policy: off\n",
        encoding="utf-8",
    )
    return tmp_path


def proposal(source_revision: int) -> dict:
    return {
        "operation_id": "harbor-notice-proposal", "operation_sequence": 1,
        "expected_revision": 0, "expected_continuity_revision": 5,
        "artifact_id": "harbor-notice", "title": "Harbor notice",
        "body_markdown": "The harbor has reopened.", "family": "public_media",
        "artifact_type": "notice",
        "author": {"kind": "office", "ref": "harbor-office", "label": "Harbor Office"},
        "source_event": {"kind": "durable_revision", "ref": f"rev-{source_revision}"},
        "authored_time": "First day, noon", "authored_time_index": 1,
        "authored_place": "Harbor office", "intended_audience": "Harbor visitors",
        "intent": "announce", "channel": "noticeboard",
        "actual_provenance": "Written by the harbor office.",
        "perceived_provenance": "An official harbor notice.",
        "epistemic_basis": {key: [] for key in world_voices.EPISTEMIC_LAYERS},
    }


@pytest.mark.parametrize("source_revision", [1, 5])
def test_public_propose_catches_up_to_existing_campaign_event(campaign, source_revision):
    current = (campaign / "current_state.yaml").read_bytes()
    result = world_voices.apply(campaign, "propose", proposal(source_revision))
    assert result["ok"] and result["continuity_revision"] == 5
    findings, state = check_world_voices.validate_manifest(campaign)
    assert not findings, findings
    artifact = state["artifacts"]["harbor-notice"]
    assert artifact["created_revision"] == 5
    assert artifact["source_event"]["ref"] == f"rev-{source_revision}"
    assert (campaign / artifact["body_path"]).read_text(encoding="utf-8") == "The harbor has reopened.\n"
    assert (campaign / "current_state.yaml").read_bytes() == current


@pytest.mark.parametrize(("indexed_revision", "result_revision", "source_revision"), [
    (0, 5, 6),
    (0, 6, 6),
    (6, 6, 6),
    (0, 6, 999),
])
def test_public_propose_cannot_use_pending_or_future_campaign_event(
    campaign, indexed_revision, result_revision, source_revision
):
    index = campaign / "world_voices/index.json"
    state = json.loads(index.read_text(encoding="utf-8"))
    state["continuity_revision"] = indexed_revision
    index.write_text(json.dumps(state), encoding="utf-8")
    before = index.read_bytes()
    payload = dict(proposal(source_revision), result_continuity_revision=result_revision)
    with pytest.raises(world_voices.WorldVoicesError) as raised:
        world_voices.apply(campaign, "propose", payload)
    assert raised.value.category == "source_event_missing"
    assert index.read_bytes() == before
    assert not (campaign / "world_voices/artifacts/harbor-notice.md").exists()


def test_public_propose_requires_campaign_evidence_for_durable_source(campaign):
    (campaign / "current_state.yaml").unlink()
    payload = dict(proposal(0), expected_continuity_revision=0)
    with pytest.raises(world_voices.WorldVoicesError) as raised:
        world_voices.apply(campaign, "propose", payload)
    assert raised.value.category == "source_event_missing"

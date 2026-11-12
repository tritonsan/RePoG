"""0.4.0 integration checks: the play skill's budget and embedded contract, the
plugin version, and the Balanced distill preset shared by docs and checks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import check_state

PLUGIN = Path(__file__).resolve().parents[1] / "plugin"
SKILL = PLUGIN / "skills" / "play" / "SKILL.md"
AGENTS = PLUGIN / "AGENTS.md"
SKILL_BUDGET = 19_000


def _embedded_agents(skill: str) -> str:
    start = skill.index("# RePoG Workspace Instructions\n")
    end = skill.index("# Claude Code\n")
    return skill[start:end]


def test_play_skill_stays_within_its_byte_budget() -> None:
    assert len(SKILL.read_bytes()) <= SKILL_BUDGET


def test_play_skill_embeds_agents_md_exactly() -> None:
    agents = AGENTS.read_bytes().decode("utf-8").replace("\r\n", "\n")
    skill = SKILL.read_bytes().decode("utf-8")
    assert _embedded_agents(skill) == agents + "\n"


def test_agents_md_keeps_crlf_and_skill_keeps_lf() -> None:
    agents = AGENTS.read_bytes()
    assert agents.count(b"\r\n") == agents.count(b"\n")
    assert b"\r" not in SKILL.read_bytes()


@pytest.mark.parametrize(
    "rule",
    [
        "then the whole reply as text, the turn's last message",
        "Text before or between tool calls is visible",
        "Record content is in the records language",
        "No romantic or sexual relationship, past or present, begins before 18",
    ],
)
def test_agents_md_states_the_040_rules(rule: str) -> None:
    agents = AGENTS.read_bytes().decode("utf-8").replace("\r\n", "\n")
    assert " ".join(rule.split()) in " ".join(agents.split())


@pytest.mark.parametrize(
    "rule",
    [
        "Age rule: no character's romantic or sexual relationship",
        "Asking again earns no more",
        "If the host says you have been quiet",
        "never through `grep`, `head`, or `tail`",
        "show the receipt's `display` line as is",
        "On a language complaint",
        "Keep no order rule of your own",
        "never resend a delivered reply",
    ],
)
def test_play_skill_states_the_040_rules(rule: str) -> None:
    skill = SKILL.read_bytes().decode("utf-8")
    assert " ".join(rule.split()) in " ".join(skill.split())


def test_plugin_manifest_is_043() -> None:
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "0.4.3"


def _balanced_profile(campaign: Path, cold_policy: str) -> None:
    (campaign / "play_profile.yaml").write_text(
        "schema_version: 2\nprofile_status: locked\nsource_setup_revision: 3\nperformance:\n"
        "  semantic_parallelism: off\n  max_parallel_workers: 1\n  turn_protocol: balanced\n"
        f"  cold_distill_policy: {cold_policy}\n"
        "  validation_policy: full_on_distill\n"
        "  dashboard_refresh_policy: every_visible_change\n"
        "  style_review_policy: every_2_durable_and_distill\n  latency_notice_policy: exceptional_only\n"
        "  estimate_acknowledged: true\n",
        encoding="utf-8",
    )


def _preset_findings(campaign: Path) -> list[dict]:
    findings: list[dict] = []
    check_state._check_play_profile(campaign, findings)
    return [item for item in findings if item["rule"] == "turn_preset_mismatch"]


@pytest.mark.parametrize("cold_policy", ["scene_checkpoint_or_5_durable", "scene_checkpoint_or_3_durable"])
def test_balanced_accepts_five_and_keeps_three(campaign: Path, cold_policy: str) -> None:
    _balanced_profile(campaign, cold_policy)
    assert _preset_findings(campaign) == []


def test_balanced_still_refuses_another_policy(campaign: Path) -> None:
    _balanced_profile(campaign, "every_durable")
    mismatches = _preset_findings(campaign)
    assert [item["message"] for item in mismatches] == [
        "balanced requires cold_distill_policy: scene_checkpoint_or_5_durable."
    ]


def test_balanced_docs_name_five_durable_turns() -> None:
    docs = [
        PLUGIN / "workflows" / "reference" / "setup-contract.md",
        PLUGIN / "workflows" / "worldbuild" / "playbooks" / "full_reference.md",
        PLUGIN / "briefs" / "campaign_creation_interview.md",
    ]
    for doc in docs:
        text = " ".join(doc.read_text(encoding="utf-8").split())
        assert "`balanced`: use `scene_checkpoint_or_3_durable`" not in text
        assert "| `balanced` | `scene_checkpoint_or_3_durable`" not in text
        assert "Balanced: light 1–2 minutes, durable 1.5–3 minutes; use `scene_checkpoint_or_3_durable`" not in text
    assert check_state.TURN_PROTOCOL_PRESETS["balanced"]["cold_distill_policy"] == "scene_checkpoint_or_5_durable"

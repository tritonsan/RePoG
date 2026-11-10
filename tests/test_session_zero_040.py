"""Session 0 (package S) for 0.4.0: setup helpers, contract reporting, gates
checked before writing, and the one-call readiness sequence.

Every campaign here is created from the shipped blank template in a temporary
folder and filled with synthetic text only.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

import pytest

import session_zero_state as sz

# The workspace's blank campaign; the plugin copies the same tree with plugin_campaign.
BLANK_CAMPAIGN = Path(__file__).resolve().parents[1] / "campaign"


def _init_campaign(project: Path) -> None:
    shutil.copytree(BLANK_CAMPAIGN, project / "campaign")


STAGES = sz.STAGE_IDS
VALUES: dict[str, dict[str, Any]] = {
    "01_creation_authority": {"mode": "approval_first"},
    "01_primary_topology_intent": {"primary_topology": "personal_drama"},
    "02_research_need_and_permission": {"status": "not_needed", "permission": "not_needed"},
    "02_current_scale_lock": {
        "risk_accepted": False,
        "current_scale_lock_permitted": True,
        "npc_power_scale": "region_anchored_open",
    },
    "06_topology_activation": {
        "primary_topology": "personal_drama",
        "build_order": ["everyday_places", "institutions", "npc_relationships", "independent_pressures"],
    },
    "07_agent_seats": {"mode": "off"},
}
DEPENDS = {
    "02_current_scale_lock": ["02_research_need_and_permission"],
    "06_topology_activation": ["01_primary_topology_intent"],
}
TAGS = {"06_topology_activation": ["character.deep_personal_integration"]}
# Stage 9 decisions recorded between its design gates, not up front.
APPROVALS = ("09_design_direction_review", "09_preparation_approval")
CLEAN_CHECK = {"ok": True, "error_count": 0, "warning_count": 0, "scope": "full", "findings": []}


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, old
    path.write_text(text.replace(old, new), encoding="utf-8")


def _blank_rpg(project: Path) -> Path:
    """A fresh campaign from the shipped template with the RPG experience chosen."""

    _init_campaign(project)
    campaign = project / "campaign"
    _replace(campaign / "setup_profile.yaml", 'experience_mode: ""', "experience_mode: rpg")
    return campaign


class DeepBuilder:
    """Drive a synthetic Deep v8 setup through the real helper, stage by stage."""

    def __init__(self, campaign: Path) -> None:
        self.campaign = campaign
        self.counter = 0
        self.manifest = sz.load_manifest(campaign, require_full=True)

    def revision(self) -> int:
        return json.loads((self.campaign / sz.STATE_FILE).read_text(encoding="utf-8"))["setup_revision"]

    def gate_output(self, gate_id: str) -> str:
        state = json.loads((self.campaign / sz.STATE_FILE).read_text(encoding="utf-8"))
        return state["gates"][gate_id]["output_digest"]

    def op(self, prefix: str) -> str:
        self.counter += 1
        return f"{prefix}-{self.counter:03d}"

    def record(self, decision_id: str, stage_id: str, **override: Any) -> dict[str, Any]:
        payload = {
            "operation_id": self.op("d"),
            "expected_revision": self.revision(),
            "decision_id": decision_id,
            "stage_id": stage_id,
            "status": "locked",
            "source": "player",
            "value": VALUES.get(decision_id, {"summary": f"synthetic {decision_id}"}),
            "depends_on": DEPENDS.get(decision_id, []),
            "trigger_tags": TAGS.get(decision_id, []),
        }
        payload.update(override)
        return sz.record_decision(self.campaign, payload)

    def record_stage(self, stage_id: str) -> None:
        for definition in sz._stage_definitions(self.manifest)[stage_id]["decisions"]:
            if definition["id"] not in APPROVALS:
                self.record(definition["id"], stage_id)

    def owner_refs(self, owners: list[dict[str, str]]) -> list[str]:
        """Materialize one synthetic line per owner and return the refs."""

        refs = []
        for owner in owners:
            relative = owner["path"]
            if relative.endswith("/"):
                relative += "synthetic_note.md"
                path = self.campaign / relative
                if not path.exists():
                    path.write_text("# Synthetic Note\n\n- Status: alive\n", encoding="utf-8")
            else:
                path = self.campaign / relative
                marker = "# synthetic\n" if relative.endswith(".yaml") else "\n- Synthetic line.\n"
                if relative.endswith(".md") or relative.endswith(".yaml"):
                    with path.open("a", encoding="utf-8") as stream:
                        stream.write(marker)
            if relative not in refs:
                refs.append(relative)
        return refs

    def stage_materials(self, stage_id: str) -> tuple[list[str], dict[str, Any]]:
        owners = sz.stage_owners(self.campaign, stage_id)
        refs = self.owner_refs(owners["evidence_owners"])
        extensions = {}
        for extension_id, entry in owners["extensions"].items():
            if entry["status"] != "active":
                continue
            ext_refs = self.owner_refs(entry["owners"])
            extensions[extension_id] = {
                "status": "complete",
                "depth": entry["depth"],
                "output_refs": ext_refs,
                "output_digest": sz.compute_output_digest(self.campaign, ext_refs),
            }
        return refs, extensions

    def complete(self, stage_id: str, refs: list[str] | None = None, extensions: dict | None = None) -> dict:
        if refs is None:
            refs, extensions = self.stage_materials(stage_id)
        return sz.complete_stage(self.campaign, {
            "operation_id": self.op("s"),
            "expected_revision": self.revision(),
            "stage_id": stage_id,
            "output_refs": refs,
            "output_digest": sz.compute_output_digest(self.campaign, refs),
            "extensions": extensions or {},
        })

    def gate(self, gate_id: str, input_digest: str, output_digest: str = "", decided_by: str = "coordinator") -> dict:
        return sz.record_gate(self.campaign, {
            "operation_id": self.op("g"),
            "expected_revision": self.revision(),
            "gate_id": gate_id,
            "input_digest": input_digest,
            "output_digest": output_digest or input_digest,
            "decided_by": decided_by,
            "evidence": {},
        })

    def stage_digest(self, stage_id: str) -> str:
        state = json.loads((self.campaign / sz.STATE_FILE).read_text(encoding="utf-8"))
        return state["stages"][stage_id]["output_digest"]

    def fill_stage_one_records(self) -> None:
        boundaries = self.campaign / "boundaries.md"
        _replace(boundaries, "| Sexual content | avoid / fade before it starts / implied, no explicit description |",
                 "| Sexual content | fade before it starts |")
        _replace(boundaries, "| Harm to children | mentioned or offscreen / avoid |", "| Harm to children | avoid |")

    def fill_anchor_table(self) -> None:
        with (self.campaign / sz.ANCHOR_FILE).open("a", encoding="utf-8") as stream:
            stream.write(
                "\n### Price And Bounty Anchors\n\n| Anchor | Value | Notes |\n| --- | --- | --- |\n"
                "| A meal | 3 coins | harbor stall |\n| A local strongman's bounty | 900 coins | posted |\n"
            )

    def through(self, last_stage: str) -> "DeepBuilder":
        """Complete every stage up to and including ``last_stage`` (1-8), with gates."""

        for stage_id in STAGES[: STAGES.index(last_stage) + 1]:
            self.record_stage(stage_id)
            if stage_id == STAGES[0]:
                self.fill_stage_one_records()
            if stage_id == "04_thin_world_kernel":
                self.fill_anchor_table()
            self.complete(stage_id)
            if stage_id == "02_research_canon_grounding":
                self.gate("research_scope_locked", self.stage_digest(stage_id))
            if stage_id == "08_reciprocity_campaign_horizon":
                self.gate("stages_1_8_complete", self.gate_output("research_scope_locked"))
        return self

    def prepare_first_act(self) -> "DeepBuilder":
        """Stage 9 through both Player approvals and its completion."""

        stage_id = STAGES[-1]
        self.record_stage(stage_id)
        design = self.gate_output("stages_1_8_complete")
        self.gate("first_act_design_complete", design)
        self.record("09_design_direction_review", stage_id)
        self.gate("design_direction_approved", design, decided_by="player")
        refs, extensions = self.stage_materials(stage_id)
        preparation = sz.compute_output_digest(self.campaign, refs)
        self.gate("preparation_materialized", design, preparation)
        self.gate("cross_read_passed", preparation)
        self.record("09_preparation_approval", stage_id)
        self.gate("preparation_approved", preparation, decided_by="player")
        self.complete(stage_id, refs, extensions)
        return self


def _deep(project: Path, *, language: str = "en") -> DeepBuilder:
    campaign = _blank_rpg(project)
    sz.set_depth(campaign, "deep", language=language)
    return DeepBuilder(campaign)


@pytest.fixture(scope="module")
def prepared_source(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One Deep setup through Stage 9 approval, copied by each finalize test."""

    builder = _deep(tmp_path_factory.mktemp("prepared"))
    builder.through("08_reciprocity_campaign_horizon").prepare_first_act()
    return builder.campaign


@pytest.fixture()
def prepared(prepared_source: Path, tmp_path: Path) -> Path:
    target = tmp_path / "campaign"
    shutil.copytree(prepared_source, target)
    return target


def _state(campaign: Path) -> dict[str, Any]:
    return json.loads((campaign / sz.STATE_FILE).read_text(encoding="utf-8"))


def _bytes(campaign: Path) -> dict[str, bytes]:
    return {name: (campaign / name).read_bytes() for name in (sz.STATE_FILE, sz.SETUP_FILE, sz.SUMMARY_FILE)}


def _cli(capsys: pytest.CaptureFixture[str], campaign: Path, *args: str) -> tuple[int, dict[str, Any]]:
    code = sz.main([str(campaign), *args])
    return code, json.loads(capsys.readouterr().out)


# Template and fresh campaign


def test_template_summary_and_state_match_the_canonical_initial_state() -> None:
    template = Path(sz.__file__).resolve().parents[1] / "templates" / "campaign"
    manifest = sz.load_manifest(template)
    state = json.loads((template / sz.STATE_FILE).read_text(encoding="utf-8"))
    assert state == sz.initial_state(manifest)
    assert sz._summary_matches((template / sz.SUMMARY_FILE).read_text(encoding="utf-8"), state)
    assert "`character_interior`: not_applicable / not_applicable" in (template / sz.SUMMARY_FILE).read_text(
        encoding="utf-8"
    )


def test_power_scale_labels_are_short() -> None:
    # The records-language sample strips a `- Label:` prefix only up to 60
    # characters; a longer English label would count against a non-English file.
    text = (Path(sz.__file__).resolve().parents[1] / "templates" / "campaign" / "boundaries.md").read_text(encoding="utf-8")
    section = text.split("\n## Power Scale\n", 1)[1].split("\n## ", 1)[0]
    labels = [line.split(":", 1)[0] for line in section.splitlines() if line.startswith("- ")]
    assert labels == ["- NPC power scale", "- NPC strength next to the character"]
    assert all(len(label) < 40 for label in labels)


def test_fresh_init_routed_by_hand_validates(tmp_path: Path) -> None:
    # The 0.3.0 template failed here with summary_stale before any decision.
    campaign = _blank_rpg(tmp_path)
    setup = campaign / "setup_profile.yaml"
    _replace(setup, 'session_zero_mode: ""', "session_zero_mode: deep")
    _replace(setup, "status: pending", "status: in_progress")
    assert sz.status(campaign)["ok"] is True


def test_fresh_init_then_first_record_decision_succeeds(tmp_path: Path) -> None:
    builder = _deep(tmp_path)
    result = builder.record("01_campaign_frame_and_reach", STAGES[0])
    assert result["ok"] is True and result["setup_revision"] == 1
    status = sz.status(builder.campaign)
    assert status["decision_count"] == 1 and status["play_language"] == "en"


# set-depth and set-language


def test_set_depth_deep_initializes_and_heals_a_stale_summary(tmp_path: Path) -> None:
    campaign = _blank_rpg(tmp_path)
    summary = campaign / sz.SUMMARY_FILE
    _replace(summary, "`world_fabric`: not_applicable / not_applicable", "`world_fabric`: not_applicable")
    (campaign / sz.STATE_FILE).unlink()

    result = sz.set_depth(campaign, "deep")

    assert result["changed"] == sorted([sz.SUMMARY_FILE, sz.STATE_FILE, sz.SETUP_FILE])
    setup = (campaign / sz.SETUP_FILE).read_text(encoding="utf-8")
    assert "session_zero_mode: deep\n" in setup and "status: in_progress\n" in setup
    assert 'question_target: ""' in setup
    assert sz.status(campaign)["ok"] is True
    again = sz.set_depth(campaign, "deep")
    assert again["changed"] == []


def test_set_depth_quick_leaves_the_ledger_alone(tmp_path: Path) -> None:
    campaign = _blank_rpg(tmp_path)
    before = (campaign / sz.SUMMARY_FILE).read_bytes()

    result = sz.set_depth(campaign, "quick", language="tr-TR")

    assert result["changed"] == ["play_profile.yaml", sz.SETUP_FILE]
    assert result["language"] == "tr" and result["language_pack"] is True
    setup = (campaign / sz.SETUP_FILE).read_text(encoding="utf-8")
    assert "session_zero_mode: quick\n" in setup and "status: in_progress\n" in setup
    assert (campaign / sz.SUMMARY_FILE).read_bytes() == before
    assert "\n  language: tr\n" in (campaign / "play_profile.yaml").read_text(encoding="utf-8")


def test_set_depth_refuses_unsafe_routing(tmp_path: Path) -> None:
    _init_campaign(tmp_path)
    campaign = tmp_path / "campaign"
    with pytest.raises(sz.StateError) as unset:
        sz.set_depth(campaign, "deep")
    assert unset.value.category == "experience_unset"

    _replace(campaign / sz.SETUP_FILE, 'experience_mode: ""', "experience_mode: companion")
    with pytest.raises(sz.StateError) as companion:
        sz.set_depth(campaign, "quick")
    assert companion.value.category == "experience_invalid"

    _replace(campaign / sz.SETUP_FILE, "experience_mode: companion", "experience_mode: rpg")
    sz.set_depth(campaign, "deep", language="en")
    DeepBuilder(campaign).record("01_campaign_frame_and_reach", STAGES[0])
    with pytest.raises(sz.StateError) as locked:
        sz.set_depth(campaign, "quick")
    assert locked.value.category == "depth_locked"

    _replace(campaign / sz.SETUP_FILE, "ready_for_play: false", "ready_for_play: true")
    with pytest.raises(sz.StateError) as ready:
        sz.set_language(campaign, "de")
    assert ready.value.category == "setup_ready"


def test_set_language_validates_and_respects_a_locked_profile(tmp_path: Path) -> None:
    campaign = _blank_rpg(tmp_path)
    with pytest.raises(sz.StateError) as auto:
        sz.set_language(campaign, "auto")
    assert auto.value.category == "input_invalid"

    profile = campaign / "play_profile.yaml"
    before = profile.read_text(encoding="utf-8")
    result = sz.set_language(campaign, "es")
    after = profile.read_text(encoding="utf-8")
    assert result == {"ok": True, "operation": "set-language", "changed": True, "language": "es", "language_pack": True}
    assert after == before.replace("\n  language: auto\n", "\n  language: es\n")
    assert sz.set_language(campaign, "es")["changed"] is False

    _replace(profile, "\nprofile_status: pending\n", "\nprofile_status: locked\n")
    with pytest.raises(sz.StateError) as locked:
        sz.set_language(campaign, "fr")
    assert locked.value.category == "profile_locked"


def _to_crlf(path: Path) -> None:
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))


def _all_crlf(path: Path) -> bool:
    payload = path.read_bytes()
    return payload.count(b"\n") == payload.count(b"\r\n") > 0


def _changed_lines(before: bytes, after: bytes) -> list[tuple[bytes, bytes]]:
    old, new = before.splitlines(keepends=True), after.splitlines(keepends=True)
    assert len(old) == len(new)
    return [(line, other) for line, other in zip(old, new) if line != other]


@pytest.mark.parametrize("endings", ["as shipped", "crlf"])
def test_set_language_changes_one_line_and_keeps_its_ending(tmp_path: Path, endings: str) -> None:
    campaign = _blank_rpg(tmp_path)
    profile = campaign / "play_profile.yaml"
    if endings == "crlf":
        _to_crlf(profile)
    before = profile.read_bytes()

    sz.set_language(campaign, "tr")

    ((old, new),) = _changed_lines(before, profile.read_bytes())
    ending = old[len(old.rstrip(b"\r\n")) :]
    assert (old, new) == (b"  language: auto" + ending, b"  language: tr" + ending)
    assert endings != "crlf" or ending == b"\r\n"


def test_setup_writers_keep_crlf_line_endings(tmp_path: Path) -> None:
    campaign = _blank_rpg(tmp_path)
    for name in (sz.SETUP_FILE, sz.SUMMARY_FILE, "play_profile.yaml"):
        _to_crlf(campaign / name)

    sz.set_depth(campaign, "deep", language="tr")
    DeepBuilder(campaign).record("01_campaign_frame_and_reach", STAGES[0])

    for name in (sz.SETUP_FILE, sz.SUMMARY_FILE, "play_profile.yaml"):
        assert _all_crlf(campaign / name), name
    setup = (campaign / sz.SETUP_FILE).read_bytes()
    assert b"\r\nsession_zero_mode: deep\r\n" in setup and b"\r\nsetup_revision: 1\r\n" in setup
    assert sz.status(campaign)["ok"] is True


def test_set_language_adds_a_language_key_an_older_profile_lacks(tmp_path: Path) -> None:
    campaign = _blank_rpg(tmp_path)
    profile = campaign / "play_profile.yaml"
    # The 0.2.0 narration block had no language key.
    line = next(line for line in profile.read_bytes().splitlines(keepends=True) if line.startswith(b"  language: auto"))
    stripped = profile.read_bytes().replace(line, b"", 1)
    profile.write_bytes(stripped)
    sz.set_depth(campaign, "deep")
    builder = DeepBuilder(campaign)
    with pytest.raises(sz.StateError) as unset:
        builder.record("01_campaign_frame_and_reach", STAGES[0])
    assert unset.value.category == "play_language_unset"

    assert sz.set_language(campaign, "tr")["changed"] is True

    # The key comes back as the block's first line, with the block line's ending.
    header = re.search(rb"(?m)^narration:[ \t]*(\r?\n)", stripped)
    assert header is not None
    expected = stripped[: header.end()] + b"  language: tr" + header.group(1) + stripped[header.end() :]
    assert profile.read_bytes() == expected
    assert builder.record("01_campaign_frame_and_reach", STAGES[0])["ok"] is True
    duplicate = profile.read_bytes().replace(b"  language: tr", b"  language: tr\n  language: de", 1)
    profile.write_bytes(duplicate)
    with pytest.raises(sz.StateError) as twice:
        sz.set_language(campaign, "en")
    assert twice.value.category == "profile_invalid"


@pytest.mark.parametrize("depth", ["quick", "standard"])
def test_set_depth_heals_a_partial_hand_edit_before_the_first_decision(tmp_path: Path, depth: str) -> None:
    campaign = _blank_rpg(tmp_path)
    setup = campaign / sz.SETUP_FILE
    _replace(setup, 'session_zero_mode: ""', f"session_zero_mode: {depth}")
    _replace(setup, 'question_target: ""', "question_target: 9")

    result = sz.set_depth(campaign, depth)

    assert result["changed"] == [sz.SETUP_FILE]
    text = setup.read_text(encoding="utf-8")
    assert "\nstatus: in_progress\n" in text and '\nquestion_target: ""\n' in text
    assert f"\nsession_zero_mode: {depth}\n" in text
    assert sz.set_depth(campaign, depth)["changed"] == []


# record-decision


def test_stage_one_content_waits_for_the_play_language(tmp_path: Path) -> None:
    builder = _deep(tmp_path, language="")
    before = _bytes(builder.campaign)
    with pytest.raises(sz.StateError) as error:
        builder.record("01_campaign_frame_and_reach", STAGES[0])
    assert error.value.category == "play_language_unset"
    assert "set-language" in str(error.value)
    assert _bytes(builder.campaign) == before

    sz.set_language(builder.campaign, "tr")
    assert builder.record("01_campaign_frame_and_reach", STAGES[0])["ok"] is True


def test_record_decision_reports_every_contract_problem_at_once(tmp_path: Path) -> None:
    builder = _deep(tmp_path)
    builder.record("01_campaign_frame_and_reach", STAGES[0])
    before = _bytes(builder.campaign)
    with pytest.raises(sz.StateError) as error:
        builder.record(
            "02_current_scale_lock",
            STAGES[0],
            status="deferred",
            source="nobody",
            value="locked",
            depends_on=["missing_decision"],
            trigger_tags=["not.a.tag"],
        )
    categories = [item["category"] for item in error.value.problems]
    messages = " | ".join(item["message"] for item in error.value.problems)
    assert error.value.category == "input_invalid"
    assert len(error.value.problems) >= 6
    assert {"input_invalid", "decision_blocked", "dependency_missing", "decision_contract"} <= set(categories)
    assert "belongs to stage 02_research_canon_grounding" in messages
    assert "not.a.tag" in messages and "missing_decision" in messages
    assert "must depend on 02_research_need_and_permission" in messages
    assert str(error.value).startswith(f"{len(categories)} problems: 1) ")
    assert _bytes(builder.campaign) == before


def test_cli_lists_problems(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    builder = _deep(tmp_path)
    code, result = _cli(
        capsys,
        builder.campaign,
        "record-decision",
        "--operation-id", "x-1",
        "--expected-revision", "0",
        "--decision-id", "01_creation_authority",
        "--stage-id", STAGES[0],
        "--status", "defaulted",
        "--source", "derived",
        "--value-json", '{"mode": "everything"}',
    )
    assert code == 2 and result["ok"] is False
    assert result["error_category"] == "decision_contract"
    assert [item["message"] for item in result["problems"]] == [
        "01_creation_authority.mode must be one of: approval_first, bounded_inference, broad_world_preparation",
        "01_creation_authority must be a locked Player decision",
    ]


def test_npc_power_scale_is_required_only_when_the_scale_lock_is_recorded() -> None:
    manifest = sz.load_manifest(Path(sz.__file__).resolve().parents[1] / "templates" / "campaign")
    decisions = {
        "02_research_need_and_permission": {
            "value": {"status": "complete", "permission": "approved"},
            "depends_on": [],
        },
        "02_current_scale_lock": {
            "value": {"risk_accepted": False, "current_scale_lock_permitted": True},
            "depends_on": ["02_research_need_and_permission"],
        },
    }
    # An older ledger stays valid; recording the decision again needs the scale.
    assert sz._structured_decision_problems(decisions, manifest) == []
    assert sz._structured_decision_problems(decisions, manifest, recorded_id="02_current_scale_lock") == [
        "02_current_scale_lock.npc_power_scale must be one of: closed, region_anchored_open"
    ]


# complete-stage


def test_stage_one_completion_checks_language_and_content_rows(tmp_path: Path) -> None:
    builder = _deep(tmp_path)
    builder.record_stage(STAGES[0])
    _replace(builder.campaign / "boundaries.md", "| Graphic violence against children on the page | never (fixed) |",
             "| Graphic violence against children on the page | open |")
    _replace(builder.campaign / "boundaries.md", "| Sexual content | avoid / fade before it starts / implied, no explicit description |",
             "| Sexual content | described directly |")
    _replace(builder.campaign / "play_profile.yaml", "\n  language: en\n", "\n  language: auto\n")
    before = _bytes(builder.campaign)

    with pytest.raises(sz.StateError) as error:
        builder.complete(STAGES[0])

    messages = [item["message"] for item in error.value.problems]
    assert error.value.category == "play_language_unset"
    fixed = [message for message in messages if "fixed row" in message]
    assert len(fixed) == 1 and "`Graphic violence against children on the page`" in fixed[0]
    assert any("`sexual content` setting must be one of" in message for message in messages)
    assert any("`harm to children` setting must be one of" in message for message in messages)
    assert _bytes(builder.campaign) == before

    sz.set_language(builder.campaign, "en")
    _replace(builder.campaign / "boundaries.md", "| Graphic violence against children on the page | open |",
             "| Graphic violence against children on the page | never (fixed) |")
    _replace(builder.campaign / "boundaries.md", "| Sexual content | described directly |",
             "| Sexual content | implied, no explicit description |")
    _replace(builder.campaign / "boundaries.md", "| Harm to children | mentioned or offscreen / avoid |",
             "| Harm to children | mentioned or offscreen |")
    assert builder.complete(STAGES[0])["completed_stage"] == STAGES[0]


def test_stage_two_completion_is_refused_before_writing_when_its_gate_would_block(tmp_path: Path) -> None:
    builder = _deep(tmp_path).through(STAGES[0])
    stage_id = STAGES[1]
    builder.record("02_research_need_and_permission", stage_id)
    builder.record("02_source_and_cast_scope", stage_id)
    builder.record("02_canon_divergence_and_native_register", stage_id)
    builder.record(
        "02_current_scale_lock",
        stage_id,
        value={**VALUES["02_current_scale_lock"], "current_scale_lock_permitted": False},
    )
    refs, _ = builder.stage_materials(stage_id)
    before = _bytes(builder.campaign)

    with pytest.raises(sz.StateError) as error:
        builder.complete(stage_id, refs)

    assert error.value.category == "gate_blocked"
    assert "research_scope_locked" in str(error.value) and "nothing was written" in str(error.value)
    assert _bytes(builder.campaign) == before

    builder.record("02_current_scale_lock", stage_id)
    assert builder.complete(stage_id, refs)["completed_stage"] == stage_id
    assert builder.gate("research_scope_locked", builder.stage_digest(stage_id))["ok"] is True


def test_stage_four_needs_the_price_and_bounty_anchor_table(tmp_path: Path) -> None:
    builder = _deep(tmp_path).through("03_character_core")
    stage_id = "04_thin_world_kernel"
    builder.record_stage(stage_id)
    with pytest.raises(sz.StateError) as error:
        builder.complete(stage_id)
    assert error.value.category == "anchor_table_missing"

    builder.fill_anchor_table()
    assert builder.complete(stage_id)["completed_stage"] == stage_id


# Read-only aids


def test_digest_and_stage_owners(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    builder = _deep(tmp_path)
    refs = ["boundaries.md", "world.md"]
    code, result = _cli(capsys, builder.campaign, "digest", "--refs-json", json.dumps(refs))
    assert code == 0 and result["output_digest"] == sz.compute_output_digest(builder.campaign, refs)

    code, result = _cli(
        capsys, builder.campaign, "digest", "--refs-json", '["rules.md"]', "--stage-id", STAGES[0]
    )
    assert code == 2 and result["error_category"] == "output_ref_unowned"

    owners = sz.stage_owners(builder.campaign, STAGES[0])
    assert [item["path"] for item in owners["evidence_owners"]] == [
        "campaign_one_pager.md", "world.md", "boundaries.md", "creation_ledger.md"
    ]
    authority = next(item for item in owners["decisions"] if item["decision_id"] == "01_creation_authority")
    assert authority["value"] == {"mode": ["approval_first", "bounded_inference", "broad_world_preparation"]}
    assert authority["status"] == "locked" and authority["recorded"] is None

    ecology = sz.stage_owners(builder.campaign, "06_living_world_ecology")
    activation = next(item for item in ecology["decisions"] if item["decision_id"] == "06_topology_activation")
    assert activation["depends_on"] == ["01_primary_topology_intent"]
    assert activation["trigger_tags"]["personal_drama"] == "character.deep_personal_integration"
    assert set(ecology["extensions"]) == {"location_network", "faction_information", "group", "character_embedding"}
    assert sz.stage_owners(builder.campaign, "08_reciprocity_campaign_horizon")["next_gate"] == "stages_1_8_complete"


# finalize


def test_finalize_runs_the_readiness_sequence_in_one_call(
    prepared: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sz, "_run_full_check", lambda root: dict(CLEAN_CHECK))
    revision = _state(prepared)["setup_revision"]

    code, result = _cli(capsys, prepared, "finalize", "--operation-id", "ready-1", "--expected-revision", str(revision))

    assert code == 0, result
    assert result["completed_steps"] == list(sz.FINALIZE_STEPS)
    assert result["setup_revision"] == revision + 1
    assert result["snapshot_ref"].endswith("_session-zero-start/snapshot_manifest.json")
    state = _state(prepared)
    assert all(gate["status"] == "complete" for gate in state["gates"].values())
    setup = (prepared / sz.SETUP_FILE).read_text(encoding="utf-8")
    assert "status: complete\n" in setup and "ready_for_play: true\n" in setup
    profile = (prepared / "play_profile.yaml").read_text(encoding="utf-8")
    assert "profile_status: locked\n" in profile and f"source_setup_revision: {revision + 1}\n" in profile
    unused = (prepared / "companion_profile.yaml").read_text(encoding="utf-8")
    assert "profile_status: inactive\n" in unused and f"source_setup_revision: {revision + 1}\n" in unused
    assert sz.validate_campaign_state(prepared, require_ready=True)["ok"] is True

    again = sz.finalize(prepared, operation_id="ready-2", expected_revision=0)
    assert again["idempotent"] is True


def test_finalize_stops_at_a_failing_preflight_without_recording_it(
    prepared: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    failing = {
        "ok": False,
        "error_count": 1,
        "findings": [{"severity": "error", "rule": "opening_missing", "message": "No opening.", "path": "x"}],
    }
    monkeypatch.setattr(sz, "_run_full_check", lambda root: dict(failing))
    revision = _state(prepared)["setup_revision"]

    code, result = _cli(capsys, prepared, "finalize", "--operation-id", "ready-1", "--expected-revision", str(revision))

    assert code == 2
    assert result["error_category"] == "preflight_failed"
    assert result["failed_step"] == "preflight" and result["completed_steps"] == []
    assert result["findings"][0]["rule"] == "opening_missing"
    assert result["setup_revision"] == revision
    assert _state(prepared)["gates"]["draft_preflight_passed"]["status"] == "pending"
    # Both profiles mirror the checked revision; neither is locked yet.
    for name in ("play_profile.yaml", "companion_profile.yaml"):
        text = (prepared / name).read_text(encoding="utf-8")
        assert f"source_setup_revision: {revision}\n" in text and "\nprofile_status: pending\n" in text


@pytest.mark.parametrize(
    ("finding", "blocked"),
    [
        ({"severity": "warning", "rule": "power_band_mismatch"}, True),
        ({"severity": "warning", "rule": "early_stage_power_spike"}, True),
        ({"severity": "warning", "rule": "records_language_mismatch"}, False),
        ({"severity": "info", "rule": "minor_romance_history"}, True),
        ({"severity": "info", "rule": "power_band_mismatch"}, False),
        ({"severity": "warning", "rule": "summary_long"}, False),
    ],
)
def test_finalize_blocks_warnings_that_readiness_does_not_carry(
    prepared: Path, monkeypatch: pytest.MonkeyPatch, finding: dict[str, str], blocked: bool
) -> None:
    check = {**CLEAN_CHECK, "warning_count": 1, "findings": [{**finding, "message": "m", "path": "p"}]}
    monkeypatch.setattr(sz, "_run_full_check", lambda root: dict(check))
    revision = _state(prepared)["setup_revision"]
    if not blocked:
        result = sz.finalize(prepared, operation_id="ready-1", expected_revision=revision, stop_after="draft_preflight_passed")
        assert result["completed_steps"] == ["preflight", "draft_preflight_passed"]
        advisory = finding["rule"] in sz.ADVISORY_RULES and finding["severity"] == "warning"
        assert [item["rule"] for item in result.get("advisories", [])] == ([finding["rule"]] if advisory else [])
        return
    with pytest.raises(sz.StateError) as error:
        sz.finalize(prepared, operation_id="ready-1", expected_revision=revision)
    assert error.value.category == "preflight_blocked"
    assert error.value.details["failed_step"] == "preflight"
    assert _state(prepared)["setup_revision"] == revision


def test_finalize_reports_records_in_another_language_without_blocking(
    prepared: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # The content step keeps boundaries.md's category and setting words in
    # English, so a terse non-English file can read as English: reported only.
    finding = {
        "severity": "warning",
        "rule": "records_language_mismatch",
        "message": "1 record file(s) read as another language than the records language 'tr': boundaries.md (en).",
        "path": str(prepared),
    }
    monkeypatch.setattr(sz, "_run_full_check", lambda root: {**CLEAN_CHECK, "warning_count": 1, "findings": [finding]})
    revision = _state(prepared)["setup_revision"]

    code, result = _cli(capsys, prepared, "finalize", "--operation-id", "ready-1", "--expected-revision", str(revision))

    assert code == 0, result
    assert result["completed_steps"] == list(sz.FINALIZE_STEPS)
    assert result["advisories"] == [{"rule": finding["rule"], "message": finding["message"], "path": finding["path"]}]
    assert _state(prepared)["gates"]["ready_and_snapshotted"]["status"] == "complete"


def test_finalize_stops_after_profile_locks_and_resumes(prepared: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Path] = []

    def check(root: Path) -> dict[str, Any]:
        calls.append(root)
        return dict(CLEAN_CHECK)

    monkeypatch.setattr(sz, "_run_full_check", check)
    revision = _state(prepared)["setup_revision"]

    first = sz.finalize(prepared, operation_id="ready-1", expected_revision=revision, stop_after="lock_profiles")
    assert first["completed_steps"] == ["preflight", "draft_preflight_passed", "lock_profiles"]
    assert "run finalize again" in first["next"]
    assert "profile_status: locked\n" in (prepared / "play_profile.yaml").read_text(encoding="utf-8")
    assert _state(prepared)["gates"]["ready_and_snapshotted"]["status"] == "pending"

    with pytest.raises(sz.StateError) as stale:
        sz.finalize(prepared, operation_id="ready-2", expected_revision=revision)
    assert stale.value.category == "stale_revision"

    second = sz.finalize(prepared, operation_id="ready-2", expected_revision=revision + 1)
    assert second["resumed_after"] == "draft_preflight_passed"
    assert second["completed_steps"] == ["lock_profiles", "snapshot", "ready_evidence", "ready_and_snapshotted"]
    # One preflight run, one aggregate run for the evidence; the gate is never re-run.
    assert len(calls) == 2


def test_finalize_profile_writes_keep_crlf_line_endings(prepared: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sz, "_run_full_check", lambda root: dict(CLEAN_CHECK))
    profiles = [prepared / "play_profile.yaml", prepared / "companion_profile.yaml"]
    for path in profiles:
        _to_crlf(path)
    befores = [path.read_bytes() for path in profiles]
    revision = _state(prepared)["setup_revision"]

    sz.finalize(prepared, operation_id="ready-1", expected_revision=revision, stop_after="lock_profiles")

    for path, before in zip(profiles, befores):
        assert _all_crlf(path), path.name
        # Only the mirrored revision and the profile status change.
        changed = {old.split(b":")[0] for old, _ in _changed_lines(before, path.read_bytes())}
        assert changed <= {b"source_setup_revision", b"profile_status"}
    assert b"\r\nprofile_status: locked\r\n" in profiles[0].read_bytes()
    assert b"\r\nprofile_status: inactive\r\n" in profiles[1].read_bytes()


def test_finalize_preflight_runs_the_real_full_check(prepared: Path) -> None:
    revision = _state(prepared)["setup_revision"]
    with pytest.raises(sz.StateError) as error:
        sz.finalize(prepared, operation_id="ready-1", expected_revision=revision)
    # Synthetic owner files cannot pass the real candidate-ready check.
    assert error.value.category == "preflight_failed"
    assert error.value.details["failed_step"] == "preflight"
    assert error.value.details["findings"]
    assert _state(prepared)["gates"]["draft_preflight_passed"]["status"] == "pending"

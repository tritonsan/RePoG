from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

import pytest

import roll_dice
import rpg_state


def _call(roll_id: str, *, value: int = 3, difficulty: int = 4) -> dict:
    return {
        "roll_id": roll_id,
        "die": "1d6",
        "call": {
            "actor": "Mira",
            "axis": "insight",
            "value": value,
            "difficulty": difficulty,
            "stakes": "the witness clams up",
        },
    }


def _commit(campaign: Path, expected: int, *, roll: str | None = None, outcome: str | None = None, void=None) -> dict:
    change = {
        "id": "read",
        "kind": "knowledge",
        "established_delta": "Mira read the witness.",
        "owners": ["knowledge_boundaries.md"],
    }
    if roll is not None:
        change["roll_reference"] = roll
    if outcome is not None:
        change["outcome"] = outcome
    payload = {
        "operation_id": "turn-" + re.sub(r"[^A-Za-z0-9]+", "-", f"{expected}-{roll}-{outcome}")[:60],
        "expected_continuity_revision": expected,
        "boundary": "ordinary",
        "cause": "Mira studied the witness.",
        "resume_impact": "Keep what Mira read.",
        "changes": [change],
        "mutations": [
            {
                "path": "knowledge_boundaries.md",
                "ops": [{"op": "append", "heading": "Player Knowledge", "text": f"- Fact: read at {expected}."}],
            }
        ],
    }
    if void is not None:
        payload["void_rolls"] = void
    return rpg_state.commit_durable(campaign, payload)


def test_cited_roll_must_match_its_band_and_is_consumed(campaign: Path) -> None:
    receipt = roll_dice.roll_call(campaign, _call("read-1"))
    wrong = "success" if receipt["band"] != "success" else "failure"
    with pytest.raises(rpg_state.RPGStateError, match="does not match"):
        _commit(campaign, 0, roll="read-1", outcome=wrong)
    with pytest.raises(rpg_state.RPGStateError, match="set outcome"):
        _commit(campaign, 0, roll="read-1")

    result = _commit(campaign, 0, roll="read-1", outcome=receipt["band"])

    assert result["continuity_revision"] == 1
    assert roll_dice.find_receipt(campaign, "read-1")["consumed_revision"] == 1
    log = (campaign / "session_log.md").read_text(encoding="utf-8")
    assert f"(roll: read-1 -> {receipt['band']})" in log
    with pytest.raises(rpg_state.RPGStateError, match="rolled at revision 0"):
        _commit(campaign, 1, roll="read-1", outcome=receipt["band"])


def test_an_uncited_roll_blocks_the_commit_until_voided(campaign: Path) -> None:
    roll_dice.roll_call(campaign, _call("peek"))
    with pytest.raises(rpg_state.RPGStateError) as caught:
        _commit(campaign, 0)
    assert caught.value.category == "rolls_unaccounted" and "peek" in str(caught.value)

    result = _commit(campaign, 0, void=[{"roll_id": "peek", "reason": "the Player withdrew the attempt"}])

    assert result["ok"]
    log = (campaign / "session_log.md").read_text(encoding="utf-8")
    assert "- Voided rolls:\n  - peek — the Player withdrew the attempt" in log
    assert roll_dice.find_receipt(campaign, "peek")["consumed_revision"] == 1


def test_legacy_free_text_reference_warns_without_a_store(campaign: Path) -> None:
    result = _commit(campaign, 0, roll="python random gave 2")
    assert result["ok"]
    assert [item["rule"] for item in result["warnings"]] == ["roll_unrecorded"]


def test_unknown_roll_is_refused_once_receipts_exist(campaign: Path) -> None:
    roll_dice.roll_call(campaign, _call("real"))
    with pytest.raises(rpg_state.RPGStateError, match="names no recorded roll"):
        _commit(campaign, 0, roll="imagined", outcome="success")


def test_downtime_is_a_scene_mode(campaign: Path) -> None:
    result = rpg_state.commit_checkpoint(
        campaign,
        {
            "operation_id": "skip-1",
            "expected_continuity_revision": 0,
            "checkpoint": {
                "scene_id": "winter_skip",
                "scene_mode": "downtime",
                "resume_anchor": "Spring arrives; the Player decides what comes next.",
                "active_cast_handoff": "none",
            },
        },
    )
    assert result["ok"] and "  mode: downtime\n" in (campaign / "current_state.yaml").read_text(encoding="utf-8")


def test_new_note_with_a_near_duplicate_name_warns(campaign: Path) -> None:
    payload = {
        "operation_id": "new-npc",
        "expected_continuity_revision": 0,
        "boundary": "ordinary",
        "cause": "A second witness appears.",
        "resume_impact": "Keep the new witness.",
        "changes": [
            {"id": "w2", "kind": "creation", "established_delta": "Witnes arrives.", "owners": ["characters/witnes.md"]}
        ],
        "mutations": [{"path": "characters/witnes.md", "create_text": "# Witnes\n\n- Tier: T1\n"}],
    }
    result = rpg_state.commit_durable(campaign, payload)
    assert any(item["rule"] == "name_near_duplicate" for item in result["warnings"])


# ---------------------------------------------------------------------------
# commit-curation
# ---------------------------------------------------------------------------


def _stage(campaign: Path, curation_id: str, mutations: list[dict], *, hashes: dict | None = None, age: float = 60) -> Path:
    folder = campaign / ".repog-runtime" / "curation"
    folder.mkdir(parents=True, exist_ok=True)
    if hashes is None:
        hashes = {
            item["path"]: hashlib.sha256((campaign / item["path"]).read_bytes()).hexdigest() for item in mutations
        }
    path = folder / f"{curation_id}.json"
    payload = {
        "curation_id": curation_id,
        "base_revision": 0,
        "reason": "fold stacked state sections",
        "base_hashes": hashes,
        "mutations": mutations,
    }
    path.write_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    stamp = time.time() - age
    os.utime(path, (stamp, stamp))
    return path


FOLD = [
    {
        "path": "characters/witness.md",
        "ops": [{"op": "replace_section", "heading": "Current State", "text": "Calm now; talks to Mira."}],
    }
]


def test_fresh_staged_curation_is_applied_and_logged(campaign: Path) -> None:
    staged = _stage(campaign, "cur-1", FOLD)

    result = rpg_state.commit_curation(campaign)

    assert result["applied"] == [{"curation_id": "cur-1", "files": ["characters/witness.md"]}]
    assert "Calm now; talks to Mira." in (campaign / "characters" / "witness.md").read_text(encoding="utf-8")
    assert not staged.exists() and (staged.parent / "applied" / "cur-1.json").exists()
    log = (campaign / "session_log.md").read_text(encoding="utf-8")
    assert "### Curation Applied At Revision 0" in log and "- Curation: cur-1" in log
    assert result["continuity_revision"] == 0


def test_stale_staged_curation_is_rejected_whole(campaign: Path) -> None:
    staged = _stage(campaign, "cur-2", FOLD, hashes={"characters/witness.md": "0" * 64})
    before = (campaign / "characters" / "witness.md").read_bytes()

    result = rpg_state.commit_curation(campaign)

    assert result["applied"] == [] and result["rejected"][0]["curation_id"] == "cur-2"
    assert "changed since" in result["rejected"][0]["reasons"][0]
    assert (campaign / "characters" / "witness.md").read_bytes() == before
    assert (staged.parent / "rejected" / "cur-2.json").exists()


def test_a_freshly_written_staging_file_waits(campaign: Path) -> None:
    staged = _stage(campaign, "cur-3", FOLD, age=0)
    result = rpg_state.commit_curation(campaign)
    assert result["waiting"] == ["cur-3.json"] and staged.exists()


def test_curation_cannot_touch_state_or_log(campaign: Path) -> None:
    staged = _stage(
        campaign,
        "cur-4",
        [{"path": "session_log.md", "ops": [{"op": "append", "text": "forged"}]}],
        hashes={"session_log.md": hashlib.sha256((campaign / "session_log.md").read_bytes()).hexdigest()},
    )
    result = rpg_state.commit_curation(campaign)
    assert result["rejected"] and "forged" not in (campaign / "session_log.md").read_text(encoding="utf-8")
    assert not staged.exists()


def test_curation_cli_prints_utf8(campaign: Path, capsysbinary: pytest.CaptureFixture[bytes]) -> None:
    _stage(campaign, "cur-5", FOLD)
    code = rpg_state.main([str(campaign), "commit-curation", "--apply-staged"])
    out = json.loads(capsysbinary.readouterr().out.decode("utf-8"))
    assert code == 0 and out["applied"][0]["curation_id"] == "cur-5"


# ---------------------------------------------------------------------------
# Player-rolled dice and template-backed owners
# ---------------------------------------------------------------------------


def _set_dice_mode(campaign: Path, mode: str) -> None:
    profile = campaign / "play_profile.yaml"
    profile.write_bytes(profile.read_bytes() + f"mechanics:\n  dice_mode: {mode}\n".encode("utf-8"))


def test_a_players_own_roll_is_cited_by_description(campaign: Path) -> None:
    _set_dice_mode(campaign, "player_rolls")
    roll_dice.roll_call(campaign, _call("gm-side"))
    with pytest.raises(rpg_state.RPGStateError, match="set outcome"):
        _commit(campaign, 0, roll="player: 2d6 for the climb", void=[{"roll_id": "gm-side", "reason": "superseded"}])
    result = _commit(
        campaign,
        0,
        roll="player: 2d6 for the climb",
        outcome="success",
        void=[{"roll_id": "gm-side", "reason": "the Player rolled instead"}],
    )
    assert result["ok"]
    assert "(roll: player: 2d6 for the climb -> success)" in (campaign / "session_log.md").read_text(encoding="utf-8")


def test_a_player_roll_reference_is_refused_when_the_gm_rolls(campaign: Path) -> None:
    _set_dice_mode(campaign, "open_gm_rolls")
    with pytest.raises(rpg_state.RPGStateError, match="does not let the Player roll"):
        _commit(campaign, 0, roll="player: 1d20", outcome="success")


def test_first_directive_in_an_older_campaign_starts_from_the_template(campaign: Path) -> None:
    assert not (campaign / "directives.md").exists()
    payload = {
        "operation_id": "first-directive",
        "expected_continuity_revision": 0,
        "boundary": "ordinary",
        "cause": "The Player asked for shorter replies.",
        "resume_impact": "Keep the table rule.",
        "changes": [
            {"id": "d1", "kind": "directive", "established_delta": "Replies stay short.", "owners": ["directives.md"]}
        ],
        "mutations": [
            {
                "path": "directives.md",
                "ops": [
                    {
                        "op": "append",
                        "heading": "Standing Directives",
                        "text": "| {{next_id:D}} | global | Keep replies short. | OOC request, revision {{revision}} | active |",
                    }
                ],
            }
        ],
    }
    rpg_state.commit_durable(campaign, payload)
    text = (campaign / "directives.md").read_text(encoding="utf-8")
    assert "| D-001 | global | Keep replies short. | OOC request, revision 1 | active |" in text


# ---------------------------------------------------------------------------
# commit-curation: retries, interrupted runs, and the payload it applies
# ---------------------------------------------------------------------------


def test_an_applied_file_that_cannot_move_is_filed_later_and_never_applied_twice(
    campaign: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import curation

    fold = _stage(campaign, "cur-6", FOLD)
    empty = _stage(campaign, "cur-7", [])
    real_move = curation.move_processed

    def refuse_applied(path: Path, outcome: str) -> Path:
        if outcome == "applied":
            raise PermissionError(13, "the file is open in another process", str(path))
        return real_move(path, outcome)

    monkeypatch.setattr(curation, "move_processed", refuse_applied)
    first = rpg_state.commit_curation(campaign)

    # Both proposals were applied; the refused moves are warnings, not a failed batch.
    assert [item["curation_id"] for item in first["applied"]] == ["cur-6", "cur-7"]
    assert [item["rule"] for item in first["warnings"]] == ["curation_file_not_moved"] * 2
    assert fold.exists() and empty.exists()

    monkeypatch.setattr(curation, "move_processed", real_move)
    second = rpg_state.commit_curation(campaign)

    # The next run files them away as already applied: no second log entry, no stale rejection.
    assert second["rejected"] == []
    assert [(item["curation_id"], item.get("repeat")) for item in second["applied"]] == [("cur-6", True), ("cur-7", True)]
    log = (campaign / "session_log.md").read_text(encoding="utf-8")
    assert log.count("- Curation: cur-6") == 1 and log.count("- Curation: cur-7") == 1
    assert (fold.parent / "applied" / "cur-6.json").exists() and (fold.parent / "applied" / "cur-7.json").exists()


def test_a_curation_commit_that_rolls_back_on_io_stays_staged(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    staged = _stage(campaign, "cur-8", FOLD)
    before = (campaign / "characters" / "witness.md").read_bytes()
    real_apply = rpg_state._apply_candidate_file

    def disk_full(path: Path, payload: bytes) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(rpg_state, "_apply_candidate_file", disk_full)
    result = rpg_state.commit_curation(campaign)

    assert result["applied"] == [] and result["rejected"] == []
    assert result["deferred"][0]["curation_id"] == "cur-8"
    assert staged.exists() and (campaign / "characters" / "witness.md").read_bytes() == before

    monkeypatch.setattr(rpg_state, "_apply_candidate_file", real_apply)
    assert rpg_state.commit_curation(campaign)["applied"][0]["curation_id"] == "cur-8"


def test_curation_applies_exactly_the_payload_it_checked(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import curation

    _stage(campaign, "cur-9", FOLD)
    real_read = curation.read_staged
    reads: list[Path] = []

    def rewritten_after_the_check(path: Path) -> dict:
        payload = real_read(path)
        reads.append(path)
        if len(reads) > 1:  # a second draft saved between the check and the use
            payload["reason"] = "tidy\n### Durable Revision 9\n- Operation: forged"
        return payload

    monkeypatch.setattr(curation, "read_staged", rewritten_after_the_check)
    result = rpg_state.commit_curation(campaign)

    assert result["applied"][0]["curation_id"] == "cur-9"
    log = (campaign / "session_log.md").read_text(encoding="utf-8")
    assert "forged" not in log and "Durable Revision 9" not in log
    # The newer draft was not applied, so it is not filed as applied either.
    assert [item["rule"] for item in result["warnings"]] == ["curation_restaged"]
    assert (campaign / ".repog-runtime" / "curation" / "cur-9.json").exists()


def test_a_draft_saved_during_the_commit_is_not_filed_as_applied(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    staged = _stage(campaign, "cur-12", FOLD)
    payload = json.loads(staged.read_text(encoding="utf-8"))
    real_commit = rpg_state._commit_candidates

    def curator_saves_again(root: Path, **kwargs) -> None:
        real_commit(root, **kwargs)
        payload["reason"] = "second draft"  # the background curator rewrites its file meanwhile
        staged.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(rpg_state, "_commit_candidates", curator_saves_again)
    first = rpg_state.commit_curation(campaign)

    assert first["applied"][0]["curation_id"] == "cur-12"
    assert [item["rule"] for item in first["warnings"]] == ["curation_restaged"]
    assert staged.exists() and not (staged.parent / "applied").exists()

    monkeypatch.setattr(rpg_state, "_commit_candidates", real_commit)
    past = time.time() - 60
    os.utime(staged, (past, past))
    second = rpg_state.commit_curation(campaign)

    # The second draft was written against the text the first one replaced: stale.
    assert second["applied"] == [] and "changed since" in second["rejected"][0]["reasons"][0]
    assert (campaign / "session_log.md").read_text(encoding="utf-8").count("- Curation: cur-12") == 1


def test_a_note_held_open_by_a_reader_does_not_fail_the_commit(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import os as os_module

    staged = _stage(campaign, "cur-10", FOLD)
    note = (campaign / "characters" / "witness.md").resolve()
    real_replace = os_module.replace
    refused: list[str] = []

    def busy_once(source, target):  # Windows: another process is reading the note
        if Path(target).resolve() == note and not refused:
            refused.append(str(target))
            raise PermissionError(13, "Access is denied", str(target))
        return real_replace(source, target)

    monkeypatch.setattr(os_module, "replace", busy_once)
    result = rpg_state.commit_curation(campaign)

    assert refused and result["applied"][0]["curation_id"] == "cur-10" and result["deferred"] == []
    assert "Calm now; talks to Mira." in (campaign / "characters" / "witness.md").read_text(encoding="utf-8")
    assert not staged.exists()


@pytest.mark.parametrize("roll_id", ["player:climb", "Player:2d6", "PLAYER:x"])
def test_a_receipt_cannot_take_the_player_roll_prefix(campaign: Path, roll_id: str) -> None:
    # The writer reads "player:..." as the Player's own dice: a receipt under such
    # an id could be cited without its band being checked.
    with pytest.raises(roll_dice.RollCallError, match="reserved") as caught:
        roll_dice.roll_call(campaign, _call(roll_id))
    assert caught.value.category == "input_invalid"
    assert not roll_dice.receipts_path(campaign).exists()


def test_a_staged_path_from_another_campaign_is_refused_and_left_alone(campaign: Path, tmp_path: Path) -> None:
    import shutil

    other = tmp_path / "other" / "campaign"
    shutil.copytree(campaign, other)
    foreign = _stage(other, "cur-11", FOLD)

    result = rpg_state.commit_curation(campaign, staged=[foreign])

    assert result["applied"] == [] and result["rejected"][0]["curation_id"] == "cur-11"
    # The writer only files proposals from its own staging folder.
    assert foreign.exists() and not (foreign.parent / "rejected").exists()
    assert "Calm now" not in (other / "characters" / "witness.md").read_text(encoding="utf-8")


def test_distill_findings_name_the_file_to_curate(campaign: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    note = campaign / "characters" / "witness.md"
    checker = rpg_state._candidate_checker()
    fake = {
        "ok": True,
        "error_count": 0,
        "warning_count": 1,
        "findings": [{"severity": "warning", "rule": "stacked_sections", "message": "3 sections", "path": str(note)}],
    }
    monkeypatch.setattr(checker, "check_campaign", lambda root, scope="full": fake)
    result = rpg_state.commit_distill(
        campaign, {"operation_id": "d-paths", "expected_continuity_revision": 0, "trigger": "manual"}
    )
    assert result["full_check"]["findings"] == [
        {"severity": "warning", "rule": "stacked_sections", "message": "3 sections", "path": "characters/witness.md"}
    ]


def test_name_check_compares_ledger_cast_and_relationship_names(campaign: Path) -> None:
    (campaign / "creation_ledger.md").write_bytes(
        b"# Creation Ledger\n\n## Active Creations\n\n- Corlan | npc | T1 | the ford | A rider. | - | - | - | active\n"
    )
    payload = {
        "operation_id": "new-corran",
        "expected_continuity_revision": 0,
        "boundary": "ordinary",
        "cause": "A ferryman appears.",
        "resume_impact": "Keep the ferryman.",
        "changes": [{"id": "c", "kind": "creation", "established_delta": "Corran arrives.", "owners": ["characters/corran.md"]}],
        "mutations": [{"path": "characters/corran.md", "create_text": "# Corran\n\n- Tier: T1\n"}],
    }
    warnings = rpg_state.commit_durable(campaign, payload)["warnings"]
    assert any(item["rule"] == "name_near_duplicate" and "Corlan" in item["message"] for item in warnings)


def test_name_check_uses_the_play_language(campaign: Path) -> None:
    profile = campaign / "play_profile.yaml"
    profile.write_bytes(profile.read_bytes() + b"narration:\n  language: tr\n")
    payload = {
        "operation_id": "new-tam",
        "expected_continuity_revision": 0,
        "boundary": "ordinary",
        "cause": "A guard appears.",
        "resume_impact": "Keep the guard.",
        "changes": [{"id": "c", "kind": "creation", "established_delta": "Tam arrives.", "owners": ["characters/tam.md"]}],
        "mutations": [{"path": "characters/tam.md", "create_text": "# Tam\n\n- Tier: T1\n\nA guard with six fingers.\n"}],
    }
    warnings = rpg_state.commit_durable(campaign, payload)["warnings"]
    assert any(item["rule"] == "name_common_word" for item in warnings)


def test_an_ooc_directive_can_ride_a_checkpoint(campaign: Path) -> None:
    result = rpg_state.commit_checkpoint(
        campaign,
        {
            "operation_id": "ooc-rule",
            "expected_continuity_revision": 0,
            "checkpoint": {
                "scene_id": "dock-interview",
                "scene_mode": "focused",
                "resume_anchor": "The witness waits for the next question.",
                "active_cast_handoff": "none",
            },
            "mutations": [
                {
                    "path": "directives.md",
                    "ops": [
                        {
                            "op": "append",
                            "heading": "Standing Directives",
                            "text": "| {{next_id:D}} | global | No weather talk. | OOC request, revision {{revision}} | active |",
                        }
                    ],
                }
            ],
        },
    )
    assert result["continuity_revision"] == 0
    assert "| D-001 | global | No weather talk. | OOC request, revision 0 | active |" in (
        campaign / "directives.md"
    ).read_text(encoding="utf-8")

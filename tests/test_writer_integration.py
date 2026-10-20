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

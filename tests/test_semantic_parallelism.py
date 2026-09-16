from __future__ import annotations

import importlib.util
import re
import shutil
from pathlib import Path

import pytest


PRODUCT = Path(__file__).resolve().parents[1]


def _load_check_state():
    path = PRODUCT / "tools" / "check_state.py"
    spec = importlib.util.spec_from_file_location("parallelism_check_state", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


check_state = _load_check_state()


def _load_check_companion():
    path = PRODUCT / "tools" / "check_companion.py"
    spec = importlib.util.spec_from_file_location("parallelism_check_companion", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


check_companion = _load_check_companion()


@pytest.fixture()
def campaign(tmp_path: Path) -> Path:
    target = tmp_path / "campaign"
    shutil.copytree(PRODUCT / "campaign", target)
    return target


def _rules(campaign: Path) -> set[str]:
    return {item["rule"] for item in check_state.check_campaign(campaign)["findings"]}


@pytest.mark.parametrize("filename", ("play_profile.yaml", "companion_profile.yaml"))
def test_new_profiles_default_to_selective_structural_parallelism(filename: str) -> None:
    text = (PRODUCT / "campaign" / filename).read_text(encoding="utf-8")
    assert "  semantic_parallelism: selective_structural\n" in text
    findings = []
    effective = check_state._check_semantic_parallelism(PRODUCT / "campaign" / filename, findings)
    assert findings == []
    assert effective == {"semantic_parallelism": "selective_structural", "max_parallel_workers": 2}


@pytest.mark.parametrize("policy", ("off", "selective_structural", "aggressive_structural"))
def test_semantic_parallelism_accepts_all_policies(campaign: Path, policy: str) -> None:
    path = campaign / "play_profile.yaml"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "semantic_parallelism: selective_structural",
            f"semantic_parallelism: {policy}",
            1,
        ),
        encoding="utf-8",
    )
    rules = _rules(campaign)
    assert "semantic_parallelism_invalid" not in rules
    assert "max_parallel_workers_invalid" not in rules


def test_semantic_parallelism_rejects_unknown_policy(campaign: Path) -> None:
    path = campaign / "play_profile.yaml"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "semantic_parallelism: selective_structural",
            "semantic_parallelism: always_spawn",
            1,
        ),
        encoding="utf-8",
    )
    assert "semantic_parallelism_invalid" in _rules(campaign)


def test_companion_checker_directly_rejects_unknown_policy(campaign: Path) -> None:
    path = campaign / "companion_profile.yaml"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "semantic_parallelism: selective_structural",
            "semantic_parallelism: always_spawn",
            1,
        ),
        encoding="utf-8",
    )
    result = check_companion.check_companion(campaign, scope="hot")
    assert "semantic_parallelism_invalid" in {item["rule"] for item in result["findings"]}


@pytest.mark.parametrize("workers", ("0", "4", "many"))
def test_semantic_parallelism_rejects_invalid_worker_limit(campaign: Path, workers: str) -> None:
    path = campaign / "companion_profile.yaml"
    path.write_text(
        re.sub(r"(?m)^  max_parallel_workers:.*$", f"  max_parallel_workers: {workers}", path.read_text(encoding="utf-8"), count=1),
        encoding="utf-8",
    )
    assert "max_parallel_workers_invalid" in _rules(campaign)


def test_partial_semantic_parallelism_configuration_is_rejected(campaign: Path) -> None:
    path = campaign / "play_profile.yaml"
    path.write_text(
        re.sub(r"(?m)^  max_parallel_workers:.*\n", "", path.read_text(encoding="utf-8"), count=1),
        encoding="utf-8",
    )
    assert "semantic_parallelism_incomplete" in _rules(campaign)


@pytest.mark.parametrize(
    ("replacement", "expected_rule"),
    (
        ("semantic_parallelism: selective_structural", "semantic_parallelism_misplaced"),
        ("    semantic_parallelism: selective_structural", "semantic_parallelism_misplaced"),
    ),
)
def test_semantic_parallelism_rejects_misplaced_reserved_key(
    campaign: Path,
    replacement: str,
    expected_rule: str,
) -> None:
    path = campaign / "play_profile.yaml"
    text = path.read_text(encoding="utf-8")
    text = text.replace("  semantic_parallelism: selective_structural", replacement, 1)
    path.write_text(text, encoding="utf-8")
    assert expected_rule in _rules(campaign)


def test_semantic_parallelism_rejects_duplicate_reserved_key(campaign: Path) -> None:
    path = campaign / "play_profile.yaml"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "  semantic_parallelism: selective_structural",
        "  semantic_parallelism: selective_structural\n  semantic_parallelism: off",
        1,
    )
    path.write_text(text, encoding="utf-8")
    assert "semantic_parallelism_duplicate" in _rules(campaign)


@pytest.mark.parametrize("filename", ("play_profile.yaml", "companion_profile.yaml"))
def test_legacy_profile_without_parallelism_fields_is_effectively_off(campaign: Path, filename: str) -> None:
    path = campaign / filename
    text = path.read_text(encoding="utf-8")
    text = text.replace("  semantic_parallelism: selective_structural\n", "", 1)
    text = re.sub(r"(?m)^  max_parallel_workers:.*\n", "", text, count=1)
    path.write_text(text, encoding="utf-8")

    findings: list[dict] = []
    effective = check_state._check_semantic_parallelism(path, findings)
    assert findings == []
    assert effective == {"semantic_parallelism": "off", "max_parallel_workers": 1}
    contract_rules = {
        item["rule"]
        for item in (
            check_companion.check_companion(campaign, scope="hot")["findings"]
            if filename == "companion_profile.yaml"
            else check_state.check_campaign(campaign, scope="hot")["findings"]
        )
    }
    assert not {
        "semantic_parallelism_incomplete",
        "semantic_parallelism_invalid",
        "max_parallel_workers_invalid",
    } & contract_rules


@pytest.mark.parametrize(
    "misplaced_line",
    (
        "semantic_parallelism: off\n",
        "communication:\n  semantic_parallelism: off\n",
        "max_parallel_workers: 2\n",
        "communication:\n  max_parallel_workers: 2\n",
    ),
)
def test_companion_parallelism_keys_are_rejected_outside_performance(
    campaign: Path,
    misplaced_line: str,
) -> None:
    path = campaign / "companion_profile.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "\n" + misplaced_line, encoding="utf-8")

    result = check_companion.check_companion(campaign, scope="hot")

    assert "semantic_parallelism_misplaced" in {item["rule"] for item in result["findings"]}


@pytest.mark.parametrize("key_value", ("semantic_parallelism: off", "max_parallel_workers: 2"))
def test_companion_parallelism_keys_cannot_be_duplicated(
    campaign: Path,
    key_value: str,
) -> None:
    path = campaign / "companion_profile.yaml"
    text = path.read_text(encoding="utf-8")
    marker = re.search(r"(?m)^  max_parallel_workers:.*\n", text).group(0)
    path.write_text(text.replace(marker, marker + f"  {key_value}\n", 1), encoding="utf-8")

    result = check_companion.check_companion(campaign, scope="hot")

    assert "semantic_parallelism_duplicate" in {item["rule"] for item in result["findings"]}


def test_companion_parallelism_acknowledgement_must_be_boolean(campaign: Path) -> None:
    path = campaign / "companion_profile.yaml"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "parallelism_notice_acknowledged: false",
            "parallelism_notice_acknowledged: later",
            1,
        ),
        encoding="utf-8",
    )

    result = check_companion.check_companion(campaign, scope="hot")

    assert "companion_parallelism_acknowledgement_invalid" in {
        item["rule"] for item in result["findings"]
    }


def test_companion_preflight_checks_ready_content_without_final_lock(campaign: Path) -> None:
    setup = campaign / "setup_profile.yaml"
    setup.write_text(
        setup.read_text(encoding="utf-8").replace('experience_mode: ""', "experience_mode: companion", 1),
        encoding="utf-8",
    )

    ordinary_rules = {
        item["rule"]
        for item in check_companion.check_companion(campaign, scope="hot")["findings"]
    }
    preflight_rules = {
        item["rule"]
        for item in check_companion.check_companion(
            campaign,
            scope="hot",
            preflight_ready=True,
        )["findings"]
    }

    assert "primary_companion_missing" not in ordinary_rules
    assert "primary_companion_missing" in preflight_rules
    assert "companion_parallelism_unacknowledged" in preflight_rules
    assert "companion_parallelism_summary_unacknowledged" in preflight_rules
    assert "companion_profile_not_locked" not in preflight_rules
    assert "companion_profile_revision_stale" not in preflight_rules


def test_companion_preflight_keeps_light_view_disabled_and_skips_current_revision(
    campaign: Path,
) -> None:
    setup = campaign / "setup_profile.yaml"
    setup.write_text(
        setup.read_text(encoding="utf-8").replace('experience_mode: ""', "experience_mode: companion", 1),
        encoding="utf-8",
    )
    profile = campaign / "companion_profile.yaml"
    profile.write_text(
        profile.read_text(encoding="utf-8").replace("companion_view: off", "companion_view: light", 1),
        encoding="utf-8",
    )
    state = campaign / "companion_state.json"
    state.write_text(
        state.read_text(encoding="utf-8").replace('"public_surface_revision": 0', '"public_surface_revision": 9', 1),
        encoding="utf-8",
    )

    result = check_companion.check_companion(
        campaign,
        scope="full",
        preflight_ready=True,
    )
    rules = {item["rule"] for item in result["findings"]}

    assert "companion_view_policy_mismatch" not in rules
    assert "companion_view_revision_stale" not in rules

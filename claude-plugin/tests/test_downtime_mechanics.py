"""Downtime mechanics: ticking clocks, obligations, and batched world pulses."""

from __future__ import annotations

import copy
import io
import json
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any

import pytest

import resolve_mechanic as rm
import world_pulse


def _state(**overrides: Any) -> dict[str, Any]:
    state: dict[str, Any] = {
        "schema_version": 2,
        "enabled": True,
        "revision": 0,
        "continuity_revision": 0,
        "operation_sequence": 0,
        "operation_registry": {},
        "last_operation": None,
        "actors": {
            "player": {
                "resources": {
                    "coin": {"current": 20, "minimum": 0, "maximum": 100},
                    "stamina": {"current": 1, "minimum": 0, "maximum": 5, "regen": {"amount": 1, "unit": "day"}},
                },
                "conditions": {"bruised": {"level": 1, "duration": {"remaining": 3, "unit": "day"}}},
            }
        },
        "clocks": {"siege": {"current": 1, "maximum": 4}},
        "elapsed_time": {},
    }
    state.update(overrides)
    return state


def _apply(state: dict[str, Any], operation: str, operation_id: str | None = None, **fields: Any):
    sequence = state["operation_sequence"] + 1
    payload = {
        "operation_id": operation_id or f"op-{sequence}",
        "operation_sequence": sequence,
        "expected_revision": state["revision"],
        "expected_continuity_revision": state["continuity_revision"],
        "operation": operation,
        **fields,
    }
    return rm.apply_operation(state, payload)


def _downtime_clocks() -> dict[str, Any]:
    return {
        "rent": {
            "current": 1,
            "maximum": 6,
            "owner": "Landlady Vey",
            "tick": {"unit": "day", "amount": 2},
            "on_fill": "The landlady changes the lock.",
        },
        "patrol": {"current": 0, "maximum": 3, "tick": {"unit": "week", "amount": 1}},
        "siege": {"current": 1, "maximum": 4},
    }


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------


def test_old_v2_state_keeps_its_exact_behaviour() -> None:
    state = _state()
    original = copy.deepcopy(state)

    updated, result = _apply(state, "advance_clock", clock_id="siege", amount=1)
    assert result["changes"] == [{"kind": "clock", "clock": "siege", "before": 1, "after": 2}]
    assert state == original
    assert "obligations" not in updated

    updated, result = _apply(updated, "advance_time", unit="day", steps=2)
    assert result["changes"] == [
        {"kind": "time", "unit": "day", "before": 0, "after": 2},
        {"kind": "resource", "resource": "stamina", "before": 1, "after": 3, "actor": "player"},
        {"kind": "condition_duration", "actor": "player", "condition": "bruised", "before": 3, "after": 1},
    ]
    assert updated["clocks"]["siege"] == {"current": 2, "maximum": 4}
    assert "obligations" not in updated


def test_v1_ledger_still_migrates() -> None:
    legacy = {
        "schema_version": 1,
        "enabled": True,
        "revision": 2,
        "applied_operations": ["a", "b"],
        "actors": {"player": {"resources": {"coin": {"current": 5, "minimum": 0, "maximum": 9}}}},
    }
    updated, result = rm.apply_operation(
        legacy, {"operation_id": "c", "operation": "spend", "actor_id": "player", "resource_id": "coin", "amount": 2}
    )
    assert result["migrated_from_schema_v1"] is True
    assert updated["schema_version"] == 2
    assert updated["actors"]["player"]["resources"]["coin"]["current"] == 3


def test_missing_clocks_and_obligations_are_optional() -> None:
    state = _state()
    del state["clocks"]
    updated, result = _apply(state, "advance_time", unit="hour")
    assert result["changes"] == [{"kind": "time", "unit": "hour", "before": 0, "after": 1}]
    assert "clocks" not in updated and "obligations" not in updated


# ---------------------------------------------------------------------------
# Clocks
# ---------------------------------------------------------------------------


def test_advance_time_ticks_matching_clocks_and_reports_filled() -> None:
    state = _state(clocks=_downtime_clocks())

    updated, result = _apply(state, "advance_time", unit="day", steps=2)
    clock_changes = [change for change in result["changes"] if change["kind"] == "clock"]
    assert clock_changes == [
        {"kind": "clock", "clock": "rent", "before": 1, "after": 5, "owner": "Landlady Vey", "reason": "tick"}
    ]
    assert updated["clocks"]["patrol"]["current"] == 0
    assert updated["clocks"]["siege"]["current"] == 1

    # 5 + 2 would be 7: capped at the maximum and reported as filled.
    updated, result = _apply(updated, "advance_time", unit="day")
    clock_changes = [change for change in result["changes"] if change["kind"] == "clock"]
    assert clock_changes == [
        {
            "kind": "clock",
            "clock": "rent",
            "before": 5,
            "after": 6,
            "owner": "Landlady Vey",
            "filled": True,
            "on_fill": "The landlady changes the lock.",
            "reason": "tick",
        }
    ]
    assert updated["clocks"]["rent"]["current"] == 6

    # A full clock does not tick again and is not reported a second time.
    updated, result = _apply(updated, "advance_time", unit="day", steps=3)
    assert not [change for change in result["changes"] if change["kind"] == "clock"]
    assert updated["clocks"]["rent"]["current"] == 6


def test_tick_amount_multiplies_by_steps() -> None:
    state = _state(clocks=_downtime_clocks())
    updated, result = _apply(state, "advance_time", unit="week", steps=2)
    assert updated["clocks"]["patrol"]["current"] == 2
    change = next(change for change in result["changes"] if change["kind"] == "clock")
    assert change == {"kind": "clock", "clock": "patrol", "before": 0, "after": 2, "reason": "tick"}
    assert updated["clocks"]["rent"]["current"] == 1


def test_manual_clock_moves_report_filled_only_at_maximum() -> None:
    state = _state(clocks=_downtime_clocks())
    updated, result = _apply(state, "set_clock", clock_id="rent", value=3)
    assert "filled" not in result["changes"][0]

    updated, result = _apply(updated, "advance_clock", clock_id="rent", amount=10)
    assert result["changes"][0]["filled"] is True
    assert result["changes"][0]["on_fill"] == "The landlady changes the lock."
    assert result["changes"][0]["after"] == 6

    updated, result = _apply(updated, "advance_clock", clock_id="siege", amount=3)
    assert result["changes"] == [{"kind": "clock", "clock": "siege", "before": 1, "after": 4, "filled": True}]


def test_new_clock_fields_accept_null_as_absent() -> None:
    clocks = {"quiet": {"current": 0, "maximum": 2, "owner": None, "tick": None, "on_fill": None}}
    updated, result = _apply(_state(clocks=clocks), "advance_time", unit="day")
    assert updated["clocks"]["quiet"]["current"] == 0
    assert all(change["kind"] != "clock" for change in result["changes"])


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("tick", "daily", "tick must be an object"),
        ("tick", {"amount": 1}, "tick.unit"),
        ("tick", {"unit": "day", "amount": 0}, "tick.amount must be at least 1"),
        ("tick", {"unit": "day", "amount": "1"}, "tick.amount must be an integer"),
        ("tick", {"unit": "day"}, "tick.amount must be an integer"),
        ("owner", "", "owner must be a non-empty string"),
        ("owner", 7, "owner must be a non-empty string"),
        ("on_fill", "first line\nsecond line", "on_fill must be one line"),
    ],
)
def test_invalid_clock_fields_are_rejected(field: str, value: Any, message: str) -> None:
    clocks = {"rent": {"current": 0, "maximum": 3, field: value}}
    with pytest.raises(rm.MechanicError, match=message):
        _apply(_state(clocks=clocks), "advance_time", unit="day")


# ---------------------------------------------------------------------------
# Obligations
# ---------------------------------------------------------------------------


def _with_wages() -> dict[str, Any]:
    state, _ = _apply(
        _state(),
        "add_obligation",
        obligation_id="guard_wages",
        actor_id="player",
        resource_id="coin",
        amount=5,
        period_label="week",
    )
    return state


def test_add_obligation_records_an_unsettled_obligation() -> None:
    state, result = _apply(
        _state(),
        "add_obligation",
        obligation_id="guard_wages",
        actor_id="player",
        resource_id="coin",
        amount=5,
        period_label="week",
    )
    record = {"actor_id": "player", "resource_id": "coin", "amount": 5, "period_label": "week", "settled": []}
    assert state["obligations"] == {"guard_wages": record}
    assert result["changes"] == [
        {"kind": "obligation_added", "obligation": "guard_wages", "actor": "player", "after": record}
    ]
    assert state["actors"]["player"]["resources"]["coin"]["current"] == 20


def test_settle_obligation_spends_once_per_period() -> None:
    state = _with_wages()
    state, result = _apply(state, "settle_obligation", obligation_id="guard_wages", period="week-1")
    assert state["actors"]["player"]["resources"]["coin"]["current"] == 15
    assert state["obligations"]["guard_wages"]["settled"] == ["week-1"]
    assert result["changes"] == [
        {"kind": "resource", "resource": "coin", "before": 20, "after": 15, "actor": "player"},
        {
            "kind": "obligation_settled",
            "obligation": "guard_wages",
            "actor": "player",
            "resource": "coin",
            "period": "week-1",
            "amount": 5,
        },
    ]

    # An amount override applies to this period only.
    state, result = _apply(state, "settle_obligation", obligation_id="guard_wages", period="week-2", amount=3)
    assert state["actors"]["player"]["resources"]["coin"]["current"] == 12
    assert state["obligations"]["guard_wages"]["settled"] == ["week-1", "week-2"]
    assert state["obligations"]["guard_wages"]["amount"] == 5


def test_double_settle_is_an_error_naming_the_period() -> None:
    state = _with_wages()
    state, _ = _apply(state, "settle_obligation", obligation_id="guard_wages", period="week-1")
    before = copy.deepcopy(state)
    with pytest.raises(rm.MechanicError, match="already settled for period 'week-1'"):
        _apply(state, "settle_obligation", operation_id="wages-again", obligation_id="guard_wages", period="week-1")
    assert state == before
    assert state["actors"]["player"]["resources"]["coin"]["current"] == 15


def test_settle_retry_with_same_operation_is_idempotent() -> None:
    state = _with_wages()
    payload = {
        "operation_id": "pay-week-1",
        "operation_sequence": state["operation_sequence"] + 1,
        "expected_revision": state["revision"],
        "expected_continuity_revision": state["continuity_revision"],
        "operation": "settle_obligation",
        "obligation_id": "guard_wages",
        "period": "week-1",
    }
    state, first = rm.apply_operation(state, payload)
    state, retry = rm.apply_operation(state, payload)
    assert first["duplicate"] is False and retry["duplicate"] is True
    assert retry["changes"] == []
    assert state["actors"]["player"]["resources"]["coin"]["current"] == 15


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"actor_id": "ghost"}, "unknown actor: ghost"),
        ({"resource_id": "favor"}, "unknown resource: favor"),
        ({"amount": -1}, "amount must be at least 0"),
        ({"amount": 2.5}, "amount must be an integer"),
        ({"period_label": ""}, "period_label must be a non-empty string"),
        ({"period_label": "week\nmonth"}, "period_label must be one line"),
        ({"obligation_id": " "}, "obligation_id must be a non-empty string"),
    ],
)
def test_add_obligation_rejects_bad_input(fields: dict[str, Any], message: str) -> None:
    request = {
        "obligation_id": "rent",
        "actor_id": "player",
        "resource_id": "coin",
        "amount": 4,
        "period_label": "month",
        **fields,
    }
    with pytest.raises(rm.MechanicError, match=message):
        _apply(_state(), "add_obligation", **request)


def test_add_obligation_rejects_a_duplicate_id() -> None:
    state = _with_wages()
    with pytest.raises(rm.MechanicError, match="obligation already exists: guard_wages"):
        _apply(
            state,
            "add_obligation",
            obligation_id="guard_wages",
            actor_id="player",
            resource_id="coin",
            amount=1,
            period_label="week",
        )


def test_settle_obligation_errors() -> None:
    state = _with_wages()
    with pytest.raises(rm.MechanicError, match="unknown obligation: rent"):
        _apply(state, "settle_obligation", obligation_id="rent", period="week-1")
    with pytest.raises(rm.MechanicError, match="period must be a non-empty string"):
        _apply(state, "settle_obligation", obligation_id="guard_wages")
    with pytest.raises(rm.MechanicError, match="insufficient coin to settle guard_wages for period 'week-1'"):
        _apply(state, "settle_obligation", obligation_id="guard_wages", period="week-1", amount=50)
    assert state["obligations"]["guard_wages"]["settled"] == []


@pytest.mark.parametrize(
    ("record", "message"),
    [
        ({"settled": ["week-1", "week-1"]}, "duplicate periods"),
        ({"settled": "week-1"}, "settled must be a list"),
        ({"amount": -2}, "amount must be at least 0"),
        ({"actor_id": ""}, "actor_id must be a non-empty string"),
    ],
)
def test_malformed_obligations_fail_validation(record: dict[str, Any], message: str) -> None:
    base = {"actor_id": "player", "resource_id": "coin", "amount": 5, "period_label": "week", "settled": []}
    state = _state(obligations={"guard_wages": {**base, **record}})
    with pytest.raises(rm.MechanicError, match=message):
        _apply(state, "advance_time", unit="day")


def test_obligations_must_be_an_object() -> None:
    with pytest.raises(rm.MechanicError, match="obligations must be an object"):
        _apply(_state(obligations=[]), "advance_time", unit="day")


def test_cli_settles_and_persists(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "mechanics_state.json"
    path.write_bytes((json.dumps(_with_wages(), indent=2) + "\n").encode("utf-8"))
    state = json.loads(path.read_text(encoding="utf-8"))
    request = {
        "operation_id": "pay-week-1",
        "operation_sequence": state["operation_sequence"] + 1,
        "expected_revision": state["revision"],
        "expected_continuity_revision": 0,
        "operation": "settle_obligation",
        "obligation_id": "guard_wages",
        "period": "week-1",
    }
    assert rm.main([str(path), "--input-json", json.dumps(request)]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["obligations"]["guard_wages"]["settled"] == ["week-1"]
    assert b"\r\n" not in path.read_bytes()

    request["operation_id"] = "pay-week-1-again"
    request["operation_sequence"] += 1
    request["expected_revision"] += 1
    persisted = path.read_bytes()
    assert rm.main([str(path), "--input-json", json.dumps(request)]) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["ok"] is False and "week-1" in output["error"]
    assert path.read_bytes() == persisted  # the refused double charge never reaches the file


# ---------------------------------------------------------------------------
# World pulse batches
# ---------------------------------------------------------------------------


PULSE_REQUESTS = [
    {"evaluation_id": "skip-d92", "domain": "harbor_trade", "elapsed_steps": 14, "volatility": 2, "pressure": 1},
    {"evaluation_id": "skip-d92", "domain": "guild_politics", "elapsed_steps": 14, "pressure": 4},
    {"domain": "border_watch", "elapsed_steps": 3, "seed": 1234, "event_cap": 5},
    {"evaluation_id": "skip-d92", "domain": "harbor_trade", "elapsed_steps": 0},
]


def test_batch_equals_individual_calls_in_order() -> None:
    batch = world_pulse.handle_request({"domains": copy.deepcopy(PULSE_REQUESTS)})
    assert batch == {"ok": True, "results": [world_pulse.generate_pulse(request) for request in PULSE_REQUESTS]}
    assert [result["domain"] for result in batch["results"]] == [
        "harbor_trade",
        "guild_politics",
        "border_watch",
        "harbor_trade",
    ]


def test_single_request_form_is_unchanged() -> None:
    for request in PULSE_REQUESTS:
        assert world_pulse.handle_request(request) == world_pulse.generate_pulse(request)


def test_batch_cap_is_twelve() -> None:
    requests = [{"evaluation_id": "cap", "domain": f"domain_{index}"} for index in range(13)]
    assert world_pulse.handle_request({"domains": requests[:12]})["ok"] is True
    result = world_pulse.handle_request({"domains": requests})
    assert result == {"ok": False, "error": "domains accepts at most 12 entries"}


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"domains": []}, "domains must be a non-empty array"),
        ({"domains": {"domain": "x"}}, "domains must be a non-empty array"),
        ({"domains": ["harbor"]}, "domains[0] must be an object"),
        ({"domains": [PULSE_REQUESTS[0], {"domain": "x"}]}, "domains[1]: evaluation_id is required"),
        ({"domains": [{"domains": [PULSE_REQUESTS[0]]}]}, "domains[0] cannot itself be a batch"),
        ({"domains": [PULSE_REQUESTS[0]], "elapsed_steps": 3}, "a batch request takes only 'domains'"),
    ],
)
def test_batch_rejects_bad_requests(payload: dict[str, Any], message: str) -> None:
    result = world_pulse.handle_request(payload)
    assert result["ok"] is False
    assert message in result["error"]
    assert "results" not in result


def test_cli_accepts_a_batch(capsys: pytest.CaptureFixture[str]) -> None:
    assert world_pulse.main(["--input-json", json.dumps({"domains": PULSE_REQUESTS})]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed == {"ok": True, "results": [world_pulse.generate_pulse(request) for request in PULSE_REQUESTS]}

    assert world_pulse.main(["--input-json", json.dumps({"domains": []})]) == 2
    assert json.loads(capsys.readouterr().out)["ok"] is False


# ---------------------------------------------------------------------------
# Review regressions: Unicode, line breaks, encodings, and edge inputs
# ---------------------------------------------------------------------------


def test_period_keys_compare_after_nfc_normalisation() -> None:
    composed = "hafta-İ"  # Turkish capital dotted I as one code point.
    decomposed = unicodedata.normalize("NFD", composed)
    assert composed != decomposed
    state, _ = _apply(_with_wages(), "settle_obligation", obligation_id="guard_wages", period=decomposed)
    assert state["obligations"]["guard_wages"]["settled"] == [composed]
    with pytest.raises(rm.MechanicError, match="already settled for period"):
        _apply(state, "settle_obligation", obligation_id="guard_wages", period=composed)
    assert state["actors"]["player"]["resources"]["coin"]["current"] == 15


@pytest.mark.parametrize(
    ("first", "again"),
    [
        ("week-3", "Week-3"),  # English casing
        ("hafta-ı", "HAFTA-I"),  # Turkish: dotless i upper-cases to I
        ("hafta-i", "HAFTA-İ"),  # Turkish: i upper-cases to the dotted capital I
        ("hafta-ı", "hafta-i"),  # every dotted and dotless i is one letter for keys
        ("Straße-2", "STRASSE-2"),  # full case folding, not just lower()
        ("semaine 3", "semaine\N{NO-BREAK SPACE}3"),  # French typography's no-break space
        ("week-3", "ＷＥＥＫ-３"),  # fullwidth forms from an IME
    ],
)
def test_period_keys_match_without_case_in_any_language(first: str, again: str) -> None:
    # Regression: case variants of one period used to be charged twice.
    state, _ = _apply(_with_wages(), "settle_obligation", obligation_id="guard_wages", period=first)
    before = copy.deepcopy(state)
    with pytest.raises(rm.MechanicError, match=r"already settled for period .* \(recorded as "):
        _apply(state, "settle_obligation", operation_id="again", obligation_id="guard_wages", period=again)
    assert state == before
    assert state["obligations"]["guard_wages"]["settled"] == [first]  # stored as given, not folded
    assert state["actors"]["player"]["resources"]["coin"]["current"] == 15


def test_case_insensitive_keys_still_keep_distinct_periods_apart() -> None:
    state, _ = _apply(_with_wages(), "settle_obligation", obligation_id="guard_wages", period="Hafta-1")
    state, _ = _apply(state, "settle_obligation", obligation_id="guard_wages", period="hafta-2")
    state, _ = _apply(state, "settle_obligation", obligation_id="guard_wages", period="kış-1")
    state, _ = _apply(state, "settle_obligation", obligation_id="guard_wages", period="kis-1")
    assert state["obligations"]["guard_wages"]["settled"] == ["Hafta-1", "hafta-2", "kış-1", "kis-1"]
    assert state["actors"]["player"]["resources"]["coin"]["current"] == 0


def test_hand_padded_settled_key_still_blocks_a_double_charge() -> None:
    base = {"actor_id": "player", "resource_id": "coin", "amount": 5, "period_label": "week", "settled": [" week-1 "]}
    state = _state(obligations={"guard_wages": base})
    with pytest.raises(rm.MechanicError, match="already settled for period 'week-1'"):
        _apply(state, "settle_obligation", obligation_id="guard_wages", period="week-1")


def test_stored_settled_keys_that_normalise_equal_are_duplicates() -> None:
    key = "süre-1"
    settled = [key, unicodedata.normalize("NFD", key)]
    base = {"actor_id": "player", "resource_id": "coin", "amount": 5, "period_label": "week", "settled": settled}
    with pytest.raises(rm.MechanicError, match="duplicate periods"):
        _apply(_state(obligations={"guard_wages": base}), "advance_time", unit="day")


@pytest.mark.parametrize(
    "separator",
    ["\N{LINE SEPARATOR}", "\N{PARAGRAPH SEPARATOR}", "\x85", "\x0b", "\x0c", "\x1e", "\r\n"],
    ids=["u2028", "u2029", "nel", "vt", "ff", "rs", "crlf"],
)
def test_one_line_fields_reject_every_line_break(separator: str) -> None:
    clocks = {"rent": {"current": 0, "maximum": 3, "on_fill": f"first{separator}second"}}
    with pytest.raises(rm.MechanicError, match="on_fill must be one line"):
        _apply(_state(clocks=clocks), "advance_time", unit="day")
    with pytest.raises(rm.MechanicError, match="period must be one line"):
        _apply(_with_wages(), "settle_obligation", obligation_id="guard_wages", period=f"w1{separator}w2")
    with pytest.raises(rm.MechanicError, match="period_label must be one line"):
        _apply(
            _state(),
            "add_obligation",
            obligation_id="rent",
            actor_id="player",
            resource_id="coin",
            amount=1,
            period_label=f"week{separator}month",
        )


def test_lone_surrogates_are_rejected_before_they_reach_a_utf8_writer() -> None:
    with pytest.raises(rm.MechanicError, match="period must be valid Unicode text"):
        _apply(_with_wages(), "settle_obligation", obligation_id="guard_wages", period="week-\ud800")
    with pytest.raises(rm.MechanicError, match="obligation_id must be valid Unicode text"):
        _apply(
            _state(),
            "add_obligation",
            obligation_id="rent-\udfff",
            actor_id="player",
            resource_id="coin",
            amount=1,
            period_label="month",
        )
    clocks = {"rent": {"current": 0, "maximum": 3, "owner": "Vey\ud800"}}
    with pytest.raises(rm.MechanicError, match="owner must be valid Unicode text"):
        _apply(_state(clocks=clocks), "advance_time", unit="day")


def test_one_line_fields_have_a_length_cap() -> None:
    long_text = "x" * (rm.MAX_LINE_TEXT + 1)
    with pytest.raises(rm.MechanicError, match=f"period exceeds {rm.MAX_LINE_TEXT} characters"):
        _apply(_with_wages(), "settle_obligation", obligation_id="guard_wages", period=long_text)
    clocks = {"rent": {"current": 0, "maximum": 3, "on_fill": "y" * rm.MAX_LINE_TEXT}}
    updated, _ = _apply(_state(clocks=clocks), "advance_time", unit="day")
    assert len(updated["clocks"]["rent"]["on_fill"]) == rm.MAX_LINE_TEXT


def test_settle_null_amount_means_the_recorded_amount() -> None:
    state, result = _apply(_with_wages(), "settle_obligation", obligation_id="guard_wages", period="week-1", amount=None)
    assert state["actors"]["player"]["resources"]["coin"]["current"] == 15
    assert result["changes"][-1]["amount"] == 5


def test_settle_names_the_obligation_when_its_actor_or_resource_is_gone() -> None:
    base = {"actor_id": "ghost", "resource_id": "coin", "amount": 5, "period_label": "week", "settled": []}
    with pytest.raises(rm.MechanicError, match="obligation guard_wages cannot be settled: unknown actor: ghost"):
        _apply(_state(obligations={"guard_wages": base}), "settle_obligation", obligation_id="guard_wages", period="w1")
    base = {**base, "actor_id": "player", "resource_id": "favor"}
    with pytest.raises(rm.MechanicError, match="obligation guard_wages cannot be settled: unknown resource: favor"):
        _apply(_state(obligations={"guard_wages": base}), "settle_obligation", obligation_id="guard_wages", period="w1")


def test_padded_tick_unit_still_ticks() -> None:
    clocks = {"rent": {"current": 0, "maximum": 3, "tick": {"unit": " day ", "amount": 1}}}
    updated, result = _apply(_state(clocks=clocks), "advance_time", unit="day")
    assert updated["clocks"]["rent"]["current"] == 1
    assert {"kind": "clock", "clock": "rent", "before": 0, "after": 1, "reason": "tick"} in result["changes"]


def test_non_ascii_clock_text_round_trips_through_the_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    clocks = {
        "kira": {
            "current": 2,
            "maximum": 3,
            "owner": "Ev sahibi İlknur",
            "tick": {"unit": "gün", "amount": 1},
            "on_fill": "Kapı kilidi değişir.",
        }
    }
    path = tmp_path / "mechanics_state.json"
    path.write_bytes((json.dumps(_state(clocks=clocks), ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    request = {
        "operation_id": "skip-1",
        "operation_sequence": 1,
        "expected_revision": 0,
        "expected_continuity_revision": 0,
        "operation": "advance_time",
        "unit": "gün",
    }
    assert rm.main([str(path), "--input-json", json.dumps(request)]) == 0
    change = next(change for change in json.loads(capsys.readouterr().out)["changes"] if change["kind"] == "clock")
    assert change["owner"] == "Ev sahibi İlknur"
    assert change["on_fill"] == "Kapı kilidi değişir."
    assert change["filled"] is True
    saved = path.read_bytes()
    saved.decode("ascii")  # written with ASCII escapes, safe for any console or code page
    assert json.loads(saved)["clocks"]["kira"]["current"] == 3


def test_cli_accepts_a_utf8_bom_and_rewrites_without_it(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "mechanics_state.json"
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps(_with_wages(), indent=2).encode("utf-8"))
    state = _with_wages()
    request = {
        "operation_id": "pay-week-1",
        "operation_sequence": state["operation_sequence"] + 1,
        "expected_revision": state["revision"],
        "expected_continuity_revision": 0,
        "operation": "settle_obligation",
        "obligation_id": "guard_wages",
        "period": "week-1",
    }
    assert rm.main([str(path), "--input-json", json.dumps(request)]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert not path.read_bytes().startswith(b"\xef\xbb\xbf")


def test_cli_reports_a_non_utf8_state_file_as_a_typed_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "mechanics_state.json"
    original = '{"schema_version": 2, "note": "çı"}'.encode("cp1254")
    path.write_bytes(original)
    request = {"operation_id": "x", "operation": "advance_time", "unit": "day"}
    assert rm.main([str(path), "--input-json", json.dumps(request)]) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["ok"] is False
    assert "mechanics_state.json is not valid UTF-8" in output["error"]
    assert path.read_bytes() == original


def test_pulse_rejects_lone_surrogates_with_a_typed_error(capsys: pytest.CaptureFixture[str]) -> None:
    result = world_pulse.handle_request({"domain": "harbor", "evaluation_id": "skip-\ud800"})
    assert result == {"ok": False, "error": "evaluation_id must be valid Unicode text (it contains a lone surrogate)"}
    batch = world_pulse.handle_request({"domains": [PULSE_REQUESTS[0], {"domain": "x\udfff", "evaluation_id": "e"}]})
    assert batch == {"ok": False, "error": "domains[1]: domain must be valid Unicode text (it contains a lone surrogate)"}
    raw = '{"domain": "harbor", "evaluation_id": "skip-\\ud800"}'
    assert world_pulse.main(["--input-json", raw]) == 2
    assert json.loads(capsys.readouterr().out)["ok"] is False


def test_pulse_handle_request_rejects_non_objects() -> None:
    for payload in ([PULSE_REQUESTS[0]], "harbor", None):
        assert world_pulse.handle_request(payload) == {"ok": False, "error": "input must be a JSON object"}


def test_pulse_batch_accepts_non_ascii_domains_identically() -> None:
    requests = [
        {"evaluation_id": "atlama-İ", "domain": "İstanbul limanı", "elapsed_steps": 6},
        {"evaluation_id": "atlama-İ", "domain": "Köln", "elapsed_steps": 6, "volatility": 3},
    ]
    batch = world_pulse.handle_request({"domains": requests})
    assert batch == {"ok": True, "results": [world_pulse.generate_pulse(request) for request in requests]}
    assert batch["results"][0]["domain"] == "İstanbul limanı"
    assert batch["results"][0]["seed"] != batch["results"][1]["seed"]


# ---------------------------------------------------------------------------
# Second review: period-key folding and cap, actionable messages, typed CLI
# errors, pinned 0.2.0 pulses, and the commit-durable path end to end
# ---------------------------------------------------------------------------


def test_stored_period_keys_that_differ_only_in_case_are_duplicates() -> None:
    base = {"actor_id": "player", "resource_id": "coin", "amount": 5, "period_label": "week", "settled": ["Week-1", "week-1"]}
    with pytest.raises(rm.MechanicError, match="duplicate periods: 'Week-1' and 'week-1' are the same period"):
        _apply(_state(obligations={"guard_wages": base}), "advance_time", unit="day")


def test_period_cap_applies_to_the_stored_nfc_form() -> None:
    # U+0344 has a two-character NFC form, so this 2,000-character key would store as 3,998.
    expanding = "x" + "\N{COMBINING GREEK DIALYTIKA TONOS}" * (rm.MAX_LINE_TEXT - 1)
    assert len(expanding) == rm.MAX_LINE_TEXT
    assert len(unicodedata.normalize("NFC", expanding)) > rm.MAX_LINE_TEXT
    # Regression: this used to fail later, blaming the stored "guard_wages.settled[0]".
    with pytest.raises(rm.MechanicError, match=f"^period exceeds {rm.MAX_LINE_TEXT} characters$"):
        _apply(_with_wages(), "settle_obligation", obligation_id="guard_wages", period=expanding)


def test_unknown_obligation_error_lists_the_recorded_ids() -> None:
    with pytest.raises(rm.MechanicError, match=r"^unknown obligation: guard_wage \(known: guard_wages\)$"):
        _apply(_with_wages(), "settle_obligation", obligation_id="guard_wage", period="week-1")
    with pytest.raises(rm.MechanicError, match=r"^unknown obligation: rent \(no obligations are recorded\)$"):
        _apply(_state(), "settle_obligation", obligation_id="rent", period="week-1")
    many = {
        f"ob-{index:02d}": {"actor_id": "player", "resource_id": "coin", "amount": 1, "period_label": "week", "settled": []}
        for index in range(12)
    }
    with pytest.raises(rm.MechanicError, match=r"\(known: ob-00, ob-01, .*, ob-09, \.\.\.\)$"):
        _apply(_state(obligations=many), "settle_obligation", obligation_id="rent", period="week-1")


def test_a_malformed_stored_obligation_is_not_reported_as_unknown() -> None:
    # Regression: a non-object record used to fail validation as "unknown obligation".
    with pytest.raises(rm.MechanicError, match=r"^obligation guard_wages must be an object$"):
        _apply(_state(obligations={"guard_wages": "5 coin a week"}), "advance_time", unit="day")


def test_insufficient_funds_error_gives_the_numbers() -> None:
    with pytest.raises(rm.MechanicError, match=r"for period 'week-1': needs 50, has 20 \(minimum 0\), short 30$"):
        _apply(_with_wages(), "settle_obligation", obligation_id="guard_wages", period="week-1", amount=50)


@pytest.mark.parametrize("operation", [None, 7, [], {"name": "spend"}, "settle", "Advance_Time"])
def test_unknown_or_non_string_operations_are_typed_errors(operation: Any) -> None:
    # Regression: a list or object used to escape as TypeError (unhashable type).
    with pytest.raises(rm.MechanicError, match=r"^unsupported operation: .+; use one of add_clock, add_condition, add_item, "):
        _apply(_state(), operation)


def _cli_error(capsys: pytest.CaptureFixture[str], argv: list[str]) -> str:
    assert rm.main(argv) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["ok"] is False
    return output["error"]


def test_cli_names_which_json_input_is_malformed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "mechanics_state.json"
    request = json.dumps({"operation_id": "x", "operation": "advance_time", "unit": "day"})
    for broken in (b"", b'{"schema_version": 2,'):
        path.write_bytes(broken)
        assert _cli_error(capsys, [str(path), "--input-json", request]).startswith("mechanics_state.json is not valid JSON: ")
    path.write_bytes(b"[]")
    assert _cli_error(capsys, [str(path), "--input-json", request]) == "mechanics_state.json must contain a JSON object"

    path.write_bytes(json.dumps(_state()).encode("utf-8"))
    original = path.read_bytes()
    assert _cli_error(capsys, [str(path), "--input-json", "{oops"]).startswith("--input-json is not valid JSON: ")
    assert _cli_error(capsys, [str(path), "--input-json", '["advance_time"]']) == "--input-json must be a JSON object"
    nested = "[" * 100_000 + "]" * 100_000
    assert _cli_error(capsys, [str(path), "--input-json", nested]) == "--input-json is not valid JSON: it is nested too deeply"
    assert path.read_bytes() == original


def test_cli_reports_a_non_string_operation_as_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "mechanics_state.json"
    path.write_bytes(json.dumps(_state()).encode("utf-8"))
    request = {
        "operation_id": "x",
        "operation_sequence": 1,
        "expected_revision": 0,
        "expected_continuity_revision": 0,
        "operation": [],
    }
    assert _cli_error(capsys, [str(path), "--input-json", json.dumps(request)]).startswith("unsupported operation: []; ")


def test_cli_turns_a_recursion_error_into_a_typed_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # A ledger nested deeper than copy.deepcopy can follow raises RecursionError while it is copied.
    path = tmp_path / "mechanics_state.json"
    path.write_bytes(json.dumps(_state()).encode("utf-8"))
    original = path.read_bytes()

    def exhaust_the_stack(state: dict[str, Any], payload: dict[str, Any]) -> Any:
        raise RecursionError("maximum recursion depth exceeded")

    monkeypatch.setattr(rm, "apply_operation", exhaust_the_stack)
    request = json.dumps({"operation_id": "x", "operation": "advance_time", "unit": "day"})
    assert _cli_error(capsys, [str(path), "--input-json", request]) == (
        "mechanics_state.json or --input-json is nested too deeply"
    )
    assert path.read_bytes() == original


@pytest.mark.skipif(
    not hasattr(sys, "get_int_max_str_digits") or sys.get_int_max_str_digits() == 0,
    reason="this Python has no limit on integer string conversion",
)
def test_overlong_integer_literals_are_typed_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    digits = "9" * (sys.get_int_max_str_digits() + 1)
    path = tmp_path / "mechanics_state.json"
    path.write_bytes(json.dumps(_state()).encode("utf-8"))
    request = '{"operation_id": "x", "operation": "advance_time", "unit": "day", "steps": ' + digits + "}"
    assert _cli_error(capsys, [str(path), "--input-json", request]).startswith("--input-json is not valid JSON: ")
    assert world_pulse.main(["--input-json", '{"domain": "harbor", "seed": ' + digits + "}"]) == 2
    assert json.loads(capsys.readouterr().out)["error"].startswith("invalid JSON: ")


def test_pulse_cli_reports_deeply_nested_input_as_a_typed_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert world_pulse.main(["--input-json", "[" * 100_000 + "]" * 100_000]) == 2
    assert json.loads(capsys.readouterr().out) == {"ok": False, "error": "invalid JSON: it is nested too deeply"}


# Envelopes produced by plugin 0.2.0 for these requests: (request, seed, [(direction, intensity), ...]).
PULSES_FROM_0_2_0 = [
    (PULSE_REQUESTS[0], 2997031482751482577, [("setback", 2), ("advance", 2), ("advance", 1)]),
    (PULSE_REQUESTS[1], 1762912006466251030, [("complication", 2), ("advance", 2), ("advance", 2)]),
    (PULSE_REQUESTS[2], 1234, []),
    ({"evaluation_id": "atlama-İ", "domain": "İstanbul limanı", "elapsed_steps": 6}, 8805949642910100022, [("advance", 1)]),
]


def test_pulses_match_the_0_2_0_release_alone_and_in_a_batch() -> None:
    expected = [
        (seed, [{"slot": slot, "direction": direction, "intensity": intensity} for slot, (direction, intensity) in enumerate(events, 1)])
        for _, seed, events in PULSES_FROM_0_2_0
    ]
    requests = [request for request, _, _ in PULSES_FROM_0_2_0]
    singles = [world_pulse.handle_request(copy.deepcopy(request)) for request in requests]
    batch = world_pulse.handle_request({"domains": copy.deepcopy(requests)})
    assert [(result["seed"], result["events"]) for result in singles] == expected
    assert [(result["seed"], result["events"]) for result in batch["results"]] == expected
    assert all(result["event_count"] == len(result["events"]) for result in batch["results"])


def test_batch_leaves_its_requests_untouched() -> None:
    requests = copy.deepcopy(PULSE_REQUESTS)
    world_pulse.handle_request({"domains": requests})
    assert requests == PULSE_REQUESTS


def test_commit_durable_settles_once_and_ticks_clocks_in_one_transaction(campaign: Path) -> None:
    import rpg_state  # The Stage 2 writer; imported here so it cannot break the unit tests above.

    clocks = {
        "kira": {
            "current": 2,
            "maximum": 3,
            "owner": "Ev sahibi İlknur",
            "tick": {"unit": "gün", "amount": 1},
            "on_fill": "Kapı kilidi değişir.",
        }
    }
    (campaign / "mechanics_state.json").write_text(json.dumps(_state(clocks=clocks), indent=2) + "\n", encoding="utf-8")

    def commit(operation_id: str, expected: int, operations: list[dict[str, Any]]) -> dict[str, Any]:
        return rpg_state.commit_durable(
            campaign,
            {
                "operation_id": operation_id,
                "expected_continuity_revision": expected,
                "boundary": "ordinary",
                "cause": "A week passed in the city.",
                "resume_impact": "A restart must keep the paid wages and the rent clock.",
                "changes": [
                    {
                        "id": "upkeep",
                        "kind": "resource",
                        "established_delta": "The guards were paid and the rent came due.",
                        "owners": ["mechanics_state.json"],
                    }
                ],
                "mutations": [],
                "mechanic_operations": operations,
            },
        )

    wages = {"obligation_id": "guard_wages", "actor_id": "player", "resource_id": "coin", "amount": 5, "period_label": "week"}
    result = commit(
        "turn-001",
        0,
        [
            {"operation_id": "wages-add", "operation": "add_obligation", **wages},
            {"operation_id": "wages-w1", "operation": "settle_obligation", "obligation_id": "guard_wages", "period": "week-1"},
            {"operation_id": "skip-1", "operation": "advance_time", "unit": "gün"},
        ],
    )
    assert result["ok"] is True and result["continuity_revision"] == 1
    tick = next(change for change in result["mechanic_results"][2]["changes"] if change["kind"] == "clock")
    assert tick == {
        "kind": "clock",
        "clock": "kira",
        "before": 2,
        "after": 3,
        "owner": "Ev sahibi İlknur",
        "filled": True,
        "on_fill": "Kapı kilidi değişir.",
        "reason": "tick",
    }
    saved = json.loads((campaign / "mechanics_state.json").read_text(encoding="utf-8"))
    assert saved["obligations"]["guard_wages"]["settled"] == ["week-1"]
    assert saved["actors"]["player"]["resources"]["coin"]["current"] == 15
    assert saved["clocks"]["kira"]["current"] == 3

    persisted = (campaign / "mechanics_state.json").read_bytes()
    again = [{"operation_id": "wages-w1-again", "operation": "settle_obligation", "obligation_id": "guard_wages", "period": "Week-1"}]
    with pytest.raises(rpg_state.RPGStateError, match=r"already settled for period 'Week-1' \(recorded as 'week-1'\)") as refused:
        commit("turn-002", 1, again)
    assert refused.value.category == "candidate_invalid"
    assert (campaign / "mechanics_state.json").read_bytes() == persisted


# ---------------------------------------------------------------------------
# Play-simulation gaps: obligations paid from an inventory item, clocks
# started and retired during play, and request files for the world pulse
# ---------------------------------------------------------------------------


def _purse_state(**overrides: Any) -> dict[str, Any]:
    """The player keeps silver as a counted inventory item, not as a resource."""
    state = _state(**overrides)
    state["actors"]["player"]["inventory"] = {"silver": {"quantity": 12}, "rope": {"quantity": 1, "consumable": False}}
    return state


def _silver_wages(**fields: Any) -> dict[str, Any]:
    return {
        "obligation_id": "guard_wages",
        "actor_id": "player",
        "item_id": "silver",
        "amount": 5,
        "period_label": "week",
        **fields,
    }


def _with_silver_wages() -> dict[str, Any]:
    state, _ = _apply(_purse_state(), "add_obligation", **_silver_wages())
    return state


def test_add_obligation_can_name_an_inventory_item() -> None:
    state, result = _apply(_purse_state(), "add_obligation", **_silver_wages())
    record = {"actor_id": "player", "item_id": "silver", "amount": 5, "period_label": "week", "settled": []}
    assert state["obligations"] == {"guard_wages": record}
    assert result["changes"] == [
        {"kind": "obligation_added", "obligation": "guard_wages", "actor": "player", "after": record}
    ]
    assert state["actors"]["player"]["inventory"]["silver"]["quantity"] == 12


def test_item_obligation_spends_its_quantity_once_per_period() -> None:
    state, result = _apply(_with_silver_wages(), "settle_obligation", obligation_id="guard_wages", period="week-1")
    assert state["actors"]["player"]["inventory"]["silver"]["quantity"] == 7
    assert state["actors"]["player"]["resources"]["coin"]["current"] == 20  # the coin resource is untouched
    assert result["changes"] == [
        {"kind": "inventory", "item": "silver", "before": 12, "after": 7, "actor": "player"},
        {
            "kind": "obligation_settled",
            "obligation": "guard_wages",
            "actor": "player",
            "item": "silver",
            "period": "week-1",
            "amount": 5,
        },
    ]
    # Regression: wages paid with remove_item had no period guard and were charged twice.
    before = copy.deepcopy(state)
    with pytest.raises(rm.MechanicError, match=r"already settled for period 'Week-1' \(recorded as 'week-1'\)"):
        _apply(state, "settle_obligation", operation_id="again", obligation_id="guard_wages", period="Week-1")
    assert state == before
    # An item may be spent down to 0.
    state, _ = _apply(state, "settle_obligation", obligation_id="guard_wages", period="week-2", amount=7)
    assert state["actors"]["player"]["inventory"]["silver"]["quantity"] == 0
    assert state["obligations"]["guard_wages"]["settled"] == ["week-1", "week-2"]


def test_item_obligation_never_takes_the_quantity_below_zero() -> None:
    state = _with_silver_wages()
    before = copy.deepcopy(state)
    with pytest.raises(
        rm.MechanicError,
        match=r"^insufficient silver to settle guard_wages for period 'week-1': needs 13, has 12, short 1$",
    ):
        _apply(state, "settle_obligation", obligation_id="guard_wages", period="week-1", amount=13)
    assert state == before


def test_resource_shortfall_counts_from_the_minimum() -> None:
    state = _state()
    state["actors"]["player"]["resources"]["favor"] = {"current": 6, "minimum": 3, "maximum": 9}
    state, _ = _apply(
        state, "add_obligation", obligation_id="tithe", actor_id="player", resource_id="favor", amount=5, period_label="week"
    )
    with pytest.raises(rm.MechanicError, match=r"^insufficient favor to settle tithe for period 'w1': needs 5, has 6 \(minimum 3\), short 2$"):
        _apply(state, "settle_obligation", obligation_id="tithe", period="w1")


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"resource_id": "coin"}, "^add_obligation needs exactly one of resource_id or item_id; both are given$"),
        ({"item_id": None}, "^add_obligation needs exactly one of resource_id or item_id; neither is given$"),
        ({"item_id": " "}, "^item_id must be a non-empty string$"),
        ({"item_id": 7}, "^item_id must be a non-empty string$"),
    ],
)
def test_add_obligation_names_exactly_one_holding(fields: dict[str, Any], message: str) -> None:
    state = _purse_state()
    with pytest.raises(rm.MechanicError, match=message):
        _apply(state, "add_obligation", **_silver_wages(**fields))
    assert "obligations" not in state


def test_a_null_holding_key_counts_as_absent() -> None:
    state, _ = _apply(_purse_state(), "add_obligation", **_silver_wages(resource_id=None))
    assert state["obligations"]["guard_wages"] == {
        "actor_id": "player",
        "item_id": "silver",
        "amount": 5,
        "period_label": "week",
        "settled": [],
    }


def test_an_unknown_holding_names_what_the_actor_holds() -> None:
    # Regression: "unknown resource: silver" gave no hint that the silver was an inventory item.
    holdings = r"\(player has resources: coin, stamina; items: rope, silver\)"
    with pytest.raises(rm.MechanicError, match=rf"^unknown resource: silver {holdings}; silver is an inventory item, so name it with item_id$"):
        _apply(_purse_state(), "add_obligation", **_silver_wages(item_id=None, resource_id="silver"))
    with pytest.raises(rm.MechanicError, match=rf"^unknown item: coin {holdings}; coin is a resource, so name it with resource_id$"):
        _apply(_purse_state(), "add_obligation", **_silver_wages(item_id="coin"))
    with pytest.raises(rm.MechanicError, match=rf"^unknown item: gold {holdings}$"):
        _apply(_purse_state(), "add_obligation", **_silver_wages(item_id="gold"))
    with pytest.raises(rm.MechanicError, match=r"^unknown item: silver \(player has resources: coin, stamina; items: none\)$"):
        _apply(_state(), "add_obligation", **_silver_wages())


def test_settling_names_the_holdings_when_the_stored_item_is_gone() -> None:
    base = {"actor_id": "player", "item_id": "silver", "amount": 5, "period_label": "week", "settled": []}
    with pytest.raises(
        rm.MechanicError,
        match=r"^obligation guard_wages cannot be settled: unknown item: silver \(player has resources: coin, stamina; items: none\)$",
    ):
        _apply(_state(obligations={"guard_wages": base}), "settle_obligation", obligation_id="guard_wages", period="w1")


@pytest.mark.parametrize(
    ("record", "message"),
    [
        ({"item_id": "silver"}, "^obligation guard_wages needs exactly one of resource_id or item_id; both are given$"),
        ({"resource_id": None}, "^obligation guard_wages needs exactly one of resource_id or item_id; neither is given$"),
        ({"resource_id": None, "item_id": ""}, "^guard_wages.item_id must be a non-empty string$"),
    ],
)
def test_stored_obligations_name_exactly_one_holding(record: dict[str, Any], message: str) -> None:
    base = {"actor_id": "player", "resource_id": "coin", "amount": 5, "period_label": "week", "settled": []}
    with pytest.raises(rm.MechanicError, match=message):
        _apply(_purse_state(obligations={"guard_wages": {**base, **record}}), "advance_time", unit="day")


WATCH = {
    "current": 0,
    "maximum": 3,
    "owner": "Captain Ilse's watch",
    "tick": {"unit": "day", "amount": 1},
    "on_fill": "The watch kicks in the warehouse door.",
}


def test_add_clock_starts_a_ticking_clock_during_play() -> None:
    fields = {key: value for key, value in WATCH.items() if key != "current"}
    state, result = _apply(_state(), "add_clock", clock_id="watch_search", **fields)
    assert state["clocks"] == {"siege": {"current": 1, "maximum": 4}, "watch_search": WATCH}
    assert result["changes"] == [{"kind": "clock_added", "clock": "watch_search", "after": WATCH}]

    state, result = _apply(state, "advance_time", unit="day", steps=5)
    assert [change for change in result["changes"] if change["kind"] == "clock"] == [
        {
            "kind": "clock",
            "clock": "watch_search",
            "before": 0,
            "after": 3,
            "owner": "Captain Ilse's watch",
            "filled": True,
            "on_fill": "The watch kicks in the warehouse door.",
            "reason": "tick",
        }
    ]


def test_add_clock_defaults_and_null_fields() -> None:
    state, result = _apply(_state(), "add_clock", clock_id="alarm", maximum=4, current=None, owner=None, tick=None, on_fill=None)
    assert state["clocks"]["alarm"] == {"current": 0, "maximum": 4}
    assert result["changes"] == [{"kind": "clock_added", "clock": "alarm", "after": {"current": 0, "maximum": 4}}]
    state, _ = _apply(state, "add_clock", clock_id=" fuse ", maximum=2, current=2, tick={"unit": " hour ", "amount": 1})
    assert state["clocks"]["fuse"] == {"current": 2, "maximum": 2, "tick": {"unit": "hour", "amount": 1}}
    state, result = _apply(state, "advance_clock", clock_id="alarm")
    assert result["changes"] == [{"kind": "clock", "clock": "alarm", "before": 0, "after": 1}]


def test_add_clock_refuses_an_existing_id_and_retries_idempotently() -> None:
    state = _state()
    before = copy.deepcopy(state)
    with pytest.raises(rm.MechanicError, match=r"^clock already exists: siege$"):
        _apply(state, "add_clock", clock_id="siege", maximum=6)
    assert state == before

    payload = {
        "operation_id": "start-watch",
        "operation_sequence": 1,
        "expected_revision": 0,
        "expected_continuity_revision": 0,
        "operation": "add_clock",
        "clock_id": "watch",
        "maximum": 4,
    }
    state, first = rm.apply_operation(state, payload)
    state, retry = rm.apply_operation(state, payload)
    assert first["duplicate"] is False and retry["duplicate"] is True and retry["changes"] == []
    assert state["clocks"]["watch"] == {"current": 0, "maximum": 4}


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"maximum": 0}, "^maximum must be at least 1$"),
        ({"maximum": "4"}, "^maximum must be an integer$"),
        ({"maximum": None}, "^maximum must be an integer$"),
        ({"current": -1}, "^current must be at least 0$"),
        ({"current": 5}, "^current must be at most 4$"),
        ({"current": True}, "^current must be an integer$"),
        ({"clock_id": " "}, "^clock_id must be a non-empty string$"),
        ({"clock_id": "watch\nsearch"}, "^clock_id must be one line$"),
        ({"owner": ""}, "^owner must be a non-empty string$"),
        ({"owner": "Ilse\ud800"}, "^owner must be valid Unicode text"),
        ({"on_fill": "first second"}, "^on_fill must be one line$"),
        ({"on_fill": "x" * (rm.MAX_LINE_TEXT + 1)}, f"^on_fill exceeds {rm.MAX_LINE_TEXT} characters$"),
        ({"tick": "daily"}, "^tick must be an object with unit and amount$"),
        ({"tick": {"amount": 1}}, r"^tick\.unit must be a non-empty string$"),
        ({"tick": {"unit": "day"}}, r"^tick\.amount must be an integer$"),
        ({"tick": {"unit": "day", "amount": 0}}, r"^tick\.amount must be at least 1$"),
        ({"tick": {"unit": "day", "amount": 1, "every": 2}}, "^tick takes only unit and amount, not every$"),
    ],
)
def test_add_clock_validates_like_a_stored_clock(fields: dict[str, Any], message: str) -> None:
    state = _state()
    before = copy.deepcopy(state)
    with pytest.raises(rm.MechanicError, match=message):
        _apply(state, "add_clock", **{"clock_id": "watch", "maximum": 4, **fields})
    assert state == before


def test_remove_clock_records_the_removed_clock() -> None:
    state, result = _apply(_state(clocks=_downtime_clocks()), "remove_clock", clock_id="rent")
    assert sorted(state["clocks"]) == ["patrol", "siege"]
    assert result["changes"] == [{"kind": "clock_removed", "clock": "rent", "before": _downtime_clocks()["rent"]}]
    # A retired clock no longer ticks, and its id is free for a new one.
    state, result = _apply(state, "advance_time", unit="day", steps=2)
    assert all(change["kind"] != "clock" for change in result["changes"])
    state, _ = _apply(state, "add_clock", clock_id="rent", maximum=2)
    assert state["clocks"]["rent"] == {"current": 0, "maximum": 2}


def test_unknown_clock_errors_list_the_recorded_clocks() -> None:
    with pytest.raises(rm.MechanicError, match=r"^unknown clock: rnt \(known: patrol, rent, siege\)$"):
        _apply(_state(clocks=_downtime_clocks()), "remove_clock", clock_id="rnt")
    with pytest.raises(rm.MechanicError, match=r"^unknown clock: siege \(no clocks are recorded\)$"):
        _apply(_state(clocks={}), "advance_clock", clock_id="siege")
    with pytest.raises(rm.MechanicError, match=r"^clock_id must be a non-empty string$"):
        _apply(_state(), "remove_clock")


def test_a_malformed_stored_clock_is_not_reported_as_unknown() -> None:
    with pytest.raises(rm.MechanicError, match=r"^clock siege must be an object$"):
        _apply(_state(clocks={"siege": 4}), "advance_time", unit="day")


def _commit_mechanics(campaign: Path, operation_id: str, expected: int, operations: list[dict[str, Any]]) -> dict[str, Any]:
    import rpg_state  # The Stage 2 writer, imported late like the commit test above.

    return rpg_state.commit_durable(
        campaign,
        {
            "operation_id": operation_id,
            "expected_continuity_revision": expected,
            "boundary": "ordinary",
            "cause": "The watch began its search and the guards were paid.",
            "resume_impact": "A restart must keep the search clock and the paid wages.",
            "changes": [
                {
                    "id": "upkeep",
                    "kind": "resource",
                    "established_delta": "The guards were paid in silver; the watch is searching.",
                    "owners": ["mechanics_state.json"],
                }
            ],
            "mutations": [],
            "mechanic_operations": operations,
        },
    )


def test_commit_durable_runs_item_wages_and_clocks_started_in_play(campaign: Path) -> None:
    import rpg_state

    (campaign / "mechanics_state.json").write_text(json.dumps(_purse_state(), indent=2) + "\n", encoding="utf-8")
    watch = {"maximum": 2, "owner": "Kaptan İlse'nin muhafızları", "tick": {"unit": "gün", "amount": 1}, "on_fill": "Muhafızlar depoya dalar."}
    result = _commit_mechanics(
        campaign,
        "turn-001",
        0,
        [
            {"operation_id": "watch-start", "operation": "add_clock", "clock_id": "watch_search", **watch},
            {"operation_id": "wages-add", "operation": "add_obligation", **_silver_wages()},
            {"operation_id": "wages-w1", "operation": "settle_obligation", "obligation_id": "guard_wages", "period": "week-1"},
            {"operation_id": "skip-2", "operation": "advance_time", "unit": "gün", "steps": 2},
            {"operation_id": "siege-over", "operation": "remove_clock", "clock_id": "siege"},
        ],
    )
    assert result["ok"] is True and result["continuity_revision"] == 1
    tick = next(change for change in result["mechanic_results"][3]["changes"] if change["kind"] == "clock")
    assert tick["clock"] == "watch_search" and tick["filled"] is True and tick["on_fill"] == "Muhafızlar depoya dalar."
    assert result["mechanic_results"][4]["changes"] == [
        {"kind": "clock_removed", "clock": "siege", "before": {"current": 1, "maximum": 4}}
    ]
    saved = json.loads((campaign / "mechanics_state.json").read_text(encoding="utf-8"))
    assert saved["clocks"] == {"watch_search": {"current": 2, **watch}}
    assert saved["actors"]["player"]["inventory"]["silver"]["quantity"] == 7
    assert saved["obligations"]["guard_wages"]["settled"] == ["week-1"]

    persisted = (campaign / "mechanics_state.json").read_bytes()
    again = [{"operation_id": "wages-w1-again", "operation": "settle_obligation", "obligation_id": "guard_wages", "period": "week-1"}]
    with pytest.raises(rpg_state.RPGStateError, match=r"already settled for period 'week-1'"):
        _commit_mechanics(campaign, "turn-002", 1, again)
    assert (campaign / "mechanics_state.json").read_bytes() == persisted


PULSE_PROSE = {"evaluation_id": "skip-d92", "domain": "the smugglers' guild of Kaçakçı Köyü", "elapsed_steps": 4, "volatility": 1}


def test_pulse_cli_reads_a_request_file_like_input_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    request = {"domains": [*PULSE_REQUESTS, PULSE_PROSE]}
    assert world_pulse.main(["--input-json", json.dumps(request)]) == 0
    from_json = capsys.readouterr().out
    assert json.loads(from_json) == world_pulse.handle_request(copy.deepcopy(request))

    # A BOM and CRLF from a Windows editor, and raw UTF-8 prose with apostrophes.
    path = tmp_path / "pulse.json"
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps(request, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8"))
    assert world_pulse.main(["--input-file", str(path)]) == 0
    assert capsys.readouterr().out == from_json


def test_pulse_cli_reads_standard_input_as_utf8_bytes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    data = b"\xef\xbb\xbf" + json.dumps(PULSE_PROSE, ensure_ascii=False).encode("utf-8")
    # The text layer's code page must never be used: cp1252 would garble the Turkish letters.
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(data), encoding="cp1252"))
    assert world_pulse.main(["--input-file", "-"]) == 0
    assert json.loads(capsys.readouterr().out) == world_pulse.generate_pulse(PULSE_PROSE)


def test_pulse_cli_reads_a_real_pipe() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", world_pulse.__file__, "--input-file", "-"],
        input=json.dumps(PULSE_PROSE, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert json.loads(completed.stdout) == world_pulse.generate_pulse(PULSE_PROSE)


def test_pulse_cli_input_file_failures_keep_the_error_shape(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "missing.json"
    assert world_pulse.main(["--input-file", str(missing)]) == 2
    output = json.loads(capsys.readouterr().out)
    assert set(output) == {"ok", "error"} and output["ok"] is False
    assert output["error"].startswith(f"cannot read --input-file {missing}: ")

    legacy = tmp_path / "cp1254.json"
    legacy.write_bytes('{"domain": "kıyı", "evaluation_id": "e"}'.encode("cp1254"))
    assert world_pulse.main(["--input-file", str(legacy)]) == 2
    assert json.loads(capsys.readouterr().out) == {
        "ok": False,
        "error": f"--input-file {legacy} is not valid UTF-8 (byte 13); save the request as UTF-8 and retry",
    }
    # With a byte order mark the offset still counts from the start of the file.
    legacy.write_bytes(b"\xef\xbb\xbf" + legacy.read_bytes())
    assert world_pulse.main(["--input-file", str(legacy)]) == 2
    assert "is not valid UTF-8 (byte 16);" in json.loads(capsys.readouterr().out)["error"]

    # A NUL in the path is a ValueError from the OS layer, never a traceback.
    assert world_pulse.main(["--input-file", "bad\0name.json"]) == 2
    assert json.loads(capsys.readouterr().out)["error"].startswith("cannot read --input-file bad")

    broken = tmp_path / "broken.json"
    broken.write_text("{oops", encoding="utf-8")
    assert world_pulse.main(["--input-file", str(broken)]) == 2
    assert json.loads(capsys.readouterr().out)["error"].startswith("invalid JSON: ")


def test_pulse_cli_takes_exactly_one_input_source(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "pulse.json"
    path.write_text(json.dumps(PULSE_REQUESTS[0]), encoding="utf-8")
    for argv in ([], ["--input-json", json.dumps(PULSE_REQUESTS[0]), "--input-file", str(path)]):
        with pytest.raises(SystemExit) as exited:
            world_pulse.main(argv)
        assert exited.value.code == 2
    errors = capsys.readouterr().err
    assert "one of the arguments --input-json --input-file is required" in errors
    assert "not allowed with argument" in errors

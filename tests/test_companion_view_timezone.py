"""The dependency-free UTC view also works on Windows without a tz database."""

import json
from pathlib import Path
from zoneinfo import ZoneInfoNotFoundError

import pytest
import check_companion_view as view


@pytest.mark.parametrize(("zone", "valid"), [
    ("UTC", True), ("Etc/UTC", True), ("GMT", True), ("Etc/GMT", True),
    ("Not/AZone", False), ("Europe/Istanbul", False),
])
def test_timezone_validation_without_host_data(tmp_path, monkeypatch, zone, valid):
    def unavailable(name):
        raise ZoneInfoNotFoundError(name)
    monkeypatch.setattr(view, "ZoneInfo", unavailable)
    template = Path(__file__).resolve().parents[1] / "campaign/companion_view/companion_view_state.json"
    data = json.loads(template.read_text(encoding="utf-8"))
    data["local_clock"] = {"label": "Local time", "timezone": zone}
    result = view.check_companion_view_data(data, tmp_path / "companion_view_state.json", require_assets=False)
    rules = {finding["rule"] for finding in result["findings"]}
    assert ("companion_view_timezone_invalid" not in rules) == valid

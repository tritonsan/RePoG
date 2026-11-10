"""Read-only product audit; all mutations are to a disposable template copy.

This isolates profile validation. It does not assert full campaign readiness.
Requires only bundled tools and the standard library.
"""
from pathlib import Path
import json
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import check_state
import resolve_mechanic


def run():
    results = []
    with tempfile.TemporaryDirectory(prefix="repog-session-zero-profile-") as directory:
        root = Path(directory).resolve() / "campaign"
        shutil.copytree(ROOT / "campaign", root)
        setup = root / "setup_profile.yaml"
        setup.write_text(setup.read_text(encoding="utf-8").replace(
            "ready_for_play: false", "ready_for_play: true").replace(
            'experience_mode: ""', "experience_mode: rpg"), encoding="utf-8")
        profile = root / "play_profile.yaml"
        base = profile.read_text(encoding="utf-8")
        for before, after in {
            "profile_status: pending": "profile_status: locked",
            'turn_protocol: ""': "turn_protocol: fast",
            'cold_distill_policy: ""': "cold_distill_policy: scene_checkpoint_or_5_durable",
            'validation_policy: ""': "validation_policy: full_on_distill",
            'style_review_policy: ""': "style_review_policy: sampled_and_distill",
            "estimate_acknowledged: false": "estimate_acknowledged: true",
            'cadence: ""': "cadence: none", 'presentation: ""': "presentation: none",
            "anchors: []": "anchors: [concrete detail, plain dialogue, variable rhythm]",
        }.items():
            base = base.replace(before, after)
        for name, extra in [("system_fit.md", "\n- Profile: fast\n"),
                            ("session_zero.md", "\n- Turn protocol: fast\n")]:
            path = root / name
            path.write_text(path.read_text(encoding="utf-8") + extra, encoding="utf-8")
        for name, before, after in [
            ("baseline", "inventory_tracking: abstract", "inventory_tracking: abstract"),
            ("quantified", "inventory_tracking: abstract", "inventory_tracking: quantified"),
            ("conditions", "wound_tracking: narrative", "wound_tracking: conditions"),
            ("step_time", "time_tracking: coarse", "time_tracking: step"),
            ("route_time", "travel_tracking: abstract", "travel_tracking: route_time"),
        ]:
            profile.write_text(base.replace(before, after), encoding="utf-8")
            findings = []
            check_state._check_play_profile(root, findings)
            results.append({"case": name, "scope": "isolated profile validator",
                            "error_rules": [f["rule"] for f in findings if f["severity"] == "error"],
                            "mechanics_enabled": False, "modules": []})
        ledger = json.loads((root / "mechanics_state.json").read_text(encoding="utf-8"))
        operation = {"operation_id": "audit-time-1", "operation_sequence": 1,
                     "expected_revision": 0, "expected_continuity_revision": 0,
                     "resulting_continuity_revision": 1, "operation": "advance_time",
                     "unit": "step", "steps": 1}
        try:
            resolve_mechanic.apply_operation(ledger, operation)
        except resolve_mechanic.MechanicError as exc:
            results.append({"disabled_operation_error": str(exc)})
        positive = dict(ledger, enabled=True)
        updated, result = resolve_mechanic.apply_operation(positive, operation)
        results.append({"positive_control_enabled": result["ok"], "elapsed_time": updated["elapsed_time"]})
    return {"source_commit": "2ed60778ed22a7e9983da126f2453759900c139b",
            "limitation": "Not an aggregate ready-campaign or narrative replay.", "results": results}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))

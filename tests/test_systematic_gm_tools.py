from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


world_pulse = load_module("repog_world_pulse", "tools/world_pulse.py")
check_style = load_module("repog_check_style", "tools/check_style.py")
resolve_mechanic = load_module("repog_resolve_mechanic", "tools/resolve_mechanic.py")


class WorldPulseTests(unittest.TestCase):
    def test_same_seed_produces_same_pulse(self):
        payload = {
            "domain": "harbor_trade",
            "elapsed_steps": 5,
            "volatility": 2,
            "pressure": 3,
            "seed": 77,
        }
        self.assertEqual(world_pulse.generate_pulse(payload), world_pulse.generate_pulse(payload))

    def test_invalid_range_is_rejected(self):
        result = world_pulse.generate_pulse({"domain": "x", "volatility": 9})
        self.assertFalse(result["ok"])


class StyleTests(unittest.TestCase):
    def test_avoid_phrase_and_length_monotony_warn(self):
        state = {
            "schema_version": 1,
            "max_history": 8,
            "avoid_phrases": ["knuckles went white"],
            "history": [
                {"word_count": 10, "length_bucket": "brief", "sentence_starters": [], "four_grams": []},
                {"word_count": 11, "length_bucket": "brief", "sentence_starters": [], "four_grams": []},
                {"word_count": 10, "length_bucket": "brief", "sentence_starters": [], "four_grams": []},
            ],
        }
        findings, _ = check_style.check_style(
            state,
            "His knuckles went white. The room remains very still tonight.",
        )
        rules = {finding["rule"] for finding in findings}
        self.assertIn("avoid_phrase", rules)
        self.assertIn("length_monotony", rules)


class MechanicTests(unittest.TestCase):
    def setUp(self):
        self.state = {
            "schema_version": 1,
            "enabled": True,
            "revision": 0,
            "actors": {
                "player": {
                    "resources": {
                        "mana": {
                            "current": 10,
                            "minimum": 0,
                            "maximum": 10,
                            "regen": {"amount": 2, "unit": "scene"},
                        }
                    },
                    "abilities": {
                        "fire_spell": {
                            "known": True,
                            "costs": {"mana": 5},
                            "cooldown": {"duration": 2, "remaining": 0, "unit": "scene"},
                        }
                    },
                }
            },
            "applied_operations": [],
        }

    def test_use_spends_resource_and_is_idempotent(self):
        payload = {
            "operation_id": "turn-1-fire",
            "operation": "use",
            "actor_id": "player",
            "action_id": "fire_spell",
        }
        updated, result = resolve_mechanic.apply_operation(self.state, payload)
        self.assertTrue(result["ok"])
        self.assertEqual(updated["actors"]["player"]["resources"]["mana"]["current"], 5)
        self.assertEqual(updated["actors"]["player"]["abilities"]["fire_spell"]["cooldown"]["remaining"], 2)

        duplicate_state, duplicate = resolve_mechanic.apply_operation(updated, payload)
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(duplicate_state["actors"]["player"]["resources"]["mana"]["current"], 5)

    def test_insufficient_resource_is_rejected_without_partial_change(self):
        self.state["actors"]["player"]["resources"]["mana"]["current"] = 4
        with self.assertRaises(resolve_mechanic.MechanicError):
            resolve_mechanic.apply_operation(
                self.state,
                {
                    "operation_id": "turn-2-fire",
                    "operation": "use",
                    "actor_id": "player",
                    "action_id": "fire_spell",
                },
            )
        self.assertEqual(self.state["actors"]["player"]["resources"]["mana"]["current"], 4)

    def test_advance_time_regenerates_and_reduces_cooldown(self):
        used, _ = resolve_mechanic.apply_operation(
            self.state,
            {
                "operation_id": "turn-3-fire",
                "operation": "use",
                "actor_id": "player",
                "action_id": "fire_spell",
            },
        )
        advanced, _ = resolve_mechanic.apply_operation(
            used,
            {
                "operation_id": "scene-advance-1",
                "operation": "advance_time",
                "steps": 1,
                "unit": "scene",
            },
        )
        self.assertEqual(advanced["actors"]["player"]["resources"]["mana"]["current"], 7)
        self.assertEqual(advanced["actors"]["player"]["abilities"]["fire_spell"]["cooldown"]["remaining"], 1)

        with self.assertRaises(resolve_mechanic.MechanicError):
            resolve_mechanic.apply_operation(
                advanced,
                {
                    "operation_id": "turn-4-fire",
                    "operation": "use",
                    "actor_id": "player",
                    "action_id": "fire_spell",
                },
            )

    def test_revision_mismatch_is_rejected(self):
        with self.assertRaises(resolve_mechanic.MechanicError):
            resolve_mechanic.apply_operation(
                self.state,
                {
                    "operation_id": "turn-5-spend",
                    "operation": "spend",
                    "actor_id": "player",
                    "resource_id": "mana",
                    "amount": 1,
                    "expected_revision": 9,
                },
            )

    def test_cli_state_shape_can_round_trip_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mechanics_state.json"
            path.write_text(json.dumps(self.state), encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["revision"], 0)


if __name__ == "__main__":
    unittest.main()

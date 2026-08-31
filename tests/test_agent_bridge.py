from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from agent_bridge import pump_once  # noqa: E402
from compile_agent_brief import compile_pack  # noqa: E402


class BridgePumpTests(unittest.TestCase):
    def test_pump_persists_submit_resolve_and_advance_transitions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pack = compile_pack({
                "pack_id": "demo-pack", "game_contract": {"title": "Demo", "genre": "Fantasy", "tone": "Tense", "reality_rules": [], "table_boundaries": []},
                "characters": [{"character_id": "mira", "display_name": "Mira", "role": "Scout", "identity": "A careful scout.", "prioritized_values": "Safety.", "goals": ["Open route."], "decision_rules": ["Observe."], "contradictions": "Cautious.", "voice_examples": ["Low tide."], "capabilities": ["self.speak", "self.observe"], "forbidden_authority": ["world outcomes"], "knowledge_refs": [], "readiness": "ready"}],
            })
            manifest = root / "pack.json"; manifest.write_text(json.dumps(pack), encoding="utf-8")
            bridge = root / "bridge.json"
            bridge.write_text(json.dumps({"schema_version": "1.1", "relay_url": "https://relay.test", "session_id": "relay-1", "bridge_token": "secret", "manifest_path": str(manifest), "agent_state_path": str(root / "seat.json"), "remote_revision": 2, "active_operation_id": "", "awaiting_advance": False, "published_turn_id": "beat-1"}), encoding="utf-8")
            remote = {"revision": 2, "pending": True}
            phase = {"resolved": False, "next": False}
            intent = {"operation_id": "op-1", "actor_id": "mira", "action_type": "speak", "action": "Test the guard.", "approach": "Quiet", "speech": "Low tide.", "targets": ["guard"], "resource_refs": [], "knowledge_refs": [], "requested_effect": "Observe.", "asserted_outcomes": []}

            def request(url, **kwargs):
                if url.endswith("/intents"):
                    return {"ok": True, "session_revision": remote["revision"], "status": "active", "intents": [{"operation_id": "op-1", "intent": intent}] if remote["pending"] else []}
                if url.endswith("/resolve"):
                    remote.update(revision=3, pending=False); return {"ok": True, "session_revision": 3}
                self.assertTrue(url.endswith("/advance")); self.assertEqual(kwargs["payload"]["next_turn"]["session"]["turn_number"], 2)
                remote["revision"] = 4; return {"ok": True, "session_revision": 4}

            def agent(_state, command, **kwargs):
                if command == "turn-status":
                    return {"ok": True, "status": "resolved", "resolution": {"outcome": "accepted", "summary": "The test lands.", "visible_consequences": ["The guard looks up."]}} if phase["resolved"] else {"ok": True, "status": "not_found"}
                if command == "submit-turn": return {"ok": True, "status": "pending"}
                turn_number = 2 if phase["next"] else 1
                status = "ready" if phase["next"] or not phase["resolved"] else "resolved"
                return {"ok": True, "status": status, "session": {"session_id": "session-demo", "current_turn_number": turn_number}, "seat": {"seat_id": "mira", "character_ref": "characters/mira.md", "role": "Scout", "capabilities": ["self.speak", "self.observe"]}, "beat": {"beat_id": f"beat-{turn_number}", "scene_id": f"scene-{turn_number}", "source_revision": turn_number}, "perspective": {"summary": "A bounded scene.", "pressure": "", "perceivable_facts": [], "known_facts": [], "self_knowledge": [], "party_public_facts": [], "allowed_actions": ["Speak"], "entity_refs": ["guard"], "owned_resource_refs": [], "knowledge_index": []}}

            self.assertEqual(pump_once(bridge, request, agent)["transition"], "intent_submitted")
            phase["resolved"] = True
            self.assertEqual(pump_once(bridge, request, agent)["transition"], "resolution_published")
            phase["next"] = True
            self.assertEqual(pump_once(bridge, request, agent)["transition"], "session_ready")
            self.assertEqual(json.loads(bridge.read_text())["published_turn_id"], "beat-2")


if __name__ == "__main__":
    unittest.main()

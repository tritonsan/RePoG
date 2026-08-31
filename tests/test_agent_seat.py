from __future__ import annotations

import functools
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from agent_seat import (  # noqa: E402
    AgentSeatError,
    get_context,
    get_next_turn,
    get_turn_status,
    initial_state,
    open_beat,
    resolve_turn,
    submit_turn,
)
from compile_agent_brief import compile_brief, compile_pack, validate_pack, validate_roster  # noqa: E402
from serve_dashboard import DashboardHandler  # noqa: E402


def open_request() -> dict:
    return {
        "operation_id": "open-dock-001",
        "expected_seat_revision": 0,
        "seat": {
            "seat_id": "mira",
            "character_ref": "characters/mira.md",
            "display_name": "Mira",
            "role": "Scout",
            "persona": {
                "goals": ["Protect the party."],
                "voice_anchors": ["Concise"],
                "boundaries": ["Do not invent player thoughts."],
            },
            "capabilities": ["self.speak", "self.move", "self.observe", "self.recall"],
        },
        "beat": {"beat_id": "dock-001", "scene_id": "dock-arrival", "source_revision": 12},
        "projection": {
            "summary": "A guard blocks the cellar door.",
            "perceivable_facts": ["The guard hides his left hand."],
            "self_knowledge": ["You are near the rear exit."],
            "known_facts": ["The ring resembles the Black Gull mark."],
            "party_public_facts": ["The party needs cellar access."],
            "allowed_actions": ["Observe", "Question", "Signal", "Act"],
            "entity_refs": ["guard", "arden"],
            "owned_resource_refs": ["black-gull-ring"],
            "knowledge_index": [
                {
                    "fact_id": "black-gull-mark",
                    "text": "The ring resembles the Black Gull mark.",
                    "status": "observed",
                    "source": "mira",
                    "confidence": 0.9,
                    "learned_at_revision": 11,
                    "last_confirmed_revision": 12,
                }
            ],
        },
    }


def turn_request() -> dict:
    return {
        "operation_id": "mira-turn-001",
        "expected_scene_id": "dock-arrival",
        "expected_source_revision": 12,
        "action": "Mention the Black Gull inn and watch the guard's reaction.",
        "approach": "Indirect and quiet.",
        "speech": "Long night at the Black Gull?",
        "actor_id": "mira",
        "action_type": "social_test",
        "targets": ["guard"],
        "resource_refs": [],
        "knowledge_refs": ["black-gull-mark"],
        "requested_effect": "observe the guard reaction",
        "asserted_outcomes": [],
    }


class AgentSeatStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.state_path = self.root / "agent_seat_state.json"
        self.state_path.write_text(json.dumps(initial_state()), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_open_submit_replay_and_resolve(self) -> None:
        opened = open_beat(self.state_path, open_request())
        self.assertEqual(opened["seat_revision"], 1)
        context = get_context(self.state_path)
        self.assertTrue(context["available"])
        self.assertEqual(context["perspective"]["known_facts"], ["The ring resembles the Black Gull mark."])

        submitted = submit_turn(self.state_path, turn_request())
        self.assertEqual(submitted["status"], "pending")
        replayed = submit_turn(self.state_path, turn_request())
        self.assertTrue(replayed["idempotent"])
        self.assertEqual(replayed["seat_revision"], submitted["seat_revision"])

        resolution = resolve_turn(
            self.state_path,
            {
                "operation_id": "resolve-dock-001",
                "expected_seat_revision": 2,
                "intent_operation_id": "mira-turn-001",
                "outcome": "accepted",
                "summary": "The guard reacts to the inn's name.",
                "visible_consequences": ["His attention shifts away from the cellar latch."],
            },
        )
        self.assertEqual(resolution["status"], "resolved")
        status = get_turn_status(self.state_path, "mira-turn-001")
        self.assertEqual(status["resolution"]["outcome"], "accepted")

    def test_same_operation_with_different_payload_is_rejected(self) -> None:
        open_beat(self.state_path, open_request())
        submit_turn(self.state_path, turn_request())
        changed = turn_request()
        changed["speech"] = "Different retry"
        with self.assertRaises(AgentSeatError) as caught:
            submit_turn(self.state_path, changed)
        self.assertEqual(caught.exception.category, "operation_conflict")

    def test_stale_scene_is_rejected_without_state_change(self) -> None:
        open_beat(self.state_path, open_request())
        stale = turn_request()
        stale["expected_source_revision"] = 11
        before = self.state_path.read_bytes()
        with self.assertRaises(AgentSeatError) as caught:
            submit_turn(self.state_path, stale)
        self.assertEqual(caught.exception.category, "stale_turn")
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_structured_authority_rejects_unknown_fact_and_asserted_outcome(self) -> None:
        open_beat(self.state_path, open_request())
        unknown = turn_request()
        unknown["knowledge_refs"] = ["gm-secret"]
        with self.assertRaises(AgentSeatError) as caught:
            submit_turn(self.state_path, unknown)
        self.assertEqual(caught.exception.category, "knowledge_violation")
        outcome = turn_request()
        outcome["operation_id"] = "mira-turn-002"
        outcome["asserted_outcomes"] = ["The guard obeys Mira."]
        with self.assertRaises(AgentSeatError) as caught:
            submit_turn(self.state_path, outcome)
        self.assertEqual(caught.exception.category, "authority_violation")

    def test_projection_is_explicit_and_does_not_read_campaign_files(self) -> None:
        secret = self.root / "secrets_and_clues.md"
        secret.write_text("GM ONLY: the guard is an impostor", encoding="utf-8")
        open_beat(self.state_path, open_request())
        serialized = json.dumps(get_context(self.state_path))
        self.assertNotIn("impostor", serialized)
        self.assertNotIn(str(secret), serialized)

    def test_resolved_beat_can_advance_without_reset(self) -> None:
        open_beat(self.state_path, open_request())
        submit_turn(self.state_path, turn_request())
        resolve_turn(
            self.state_path,
            {
                "operation_id": "resolve-dock-001",
                "expected_seat_revision": 2,
                "intent_operation_id": "mira-turn-001",
                "outcome": "accepted",
                "summary": "The guard reacts.",
                "visible_consequences": ["The cellar opens."],
            },
        )
        second = open_request()
        second["operation_id"] = "open-cellar-002"
        second["expected_seat_revision"] = 3
        second["beat"] = {"beat_id": "cellar-002", "scene_id": "cellar-entry", "source_revision": 13}
        opened = open_beat(self.state_path, second)
        self.assertEqual(opened["turn_number"], 2)
        self.assertEqual(get_next_turn(self.state_path)["status"], "ready")
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertEqual(len(state["turn_history"]), 1)


class AgentBriefTests(unittest.TestCase):
    def test_compiler_enforces_bounded_projection(self) -> None:
        request = {
            "session": {"session_id": "demo", "turn_id": "turn-1", "turn_number": 1, "revision": 1},
            "seat": {"seat_id": "mira", "character_ref": "characters/mira.md", "role": "Scout", "authority": ["Speak"], "forbidden_authority": ["GM truth"]},
            "scene": {"scene_id": "dock", "summary": "A guard blocks the way.", "pressure": "The bell is close.", "perceivable_facts": ["A bell hangs nearby."], "affordances": ["Observe"]},
            "character": {"identity": "Mira, a cautious scout.", "prioritized_values": "Party safety, then initiative.", "short_term_goal": "Open the route.", "long_term_goal": "Expose the Black Gull.", "contradictions": "Cautious but impatient with bullies.", "decision_rules": ["Test before confronting."], "voice_examples": ["Low tide."]},
            "relevant_knowledge": ["The ring resembles the Black Gull mark."],
            "relevant_memories": [],
        }
        brief = compile_brief(request)
        self.assertEqual(brief["session"]["turn_number"], 1)
        self.assertEqual(brief["seat"]["character_id"], "mira")
        self.assertNotIn("gm_truth", json.dumps(brief).lower())

    def test_ready_roster_requires_t3_playability_card(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            campaign = Path(temporary)
            (campaign / "characters").mkdir()
            (campaign / "agent_roster.json").write_text(json.dumps({"schema_version": "1.0", "mode": "on_demand", "max_active_seats": 1, "characters": [{"character_ref": "characters/mira.md", "status": "ready", "role": "party_companion"}]}), encoding="utf-8")
            (campaign / "characters" / "mira.md").write_text("# Mira\n\nTier: T2\n", encoding="utf-8")
            result = validate_roster(campaign)
            self.assertFalse(result["ok"])

    def test_generic_pack_compiles_two_ready_characters(self) -> None:
        request = {
            "pack_id": "cross-genre-demo",
            "game_contract": {
                "title": "Cross Genre Demo",
                "genre": "Fantasy and science fiction",
                "tone": "Consequential intrigue",
                "reality_rules": ["Outcomes follow established positioning."],
                "table_boundaries": ["Agents author only their character."],
            },
            "characters": [
                {
                    "character_id": character_id,
                    "display_name": name,
                    "role": role,
                    "identity": identity,
                    "prioritized_values": values,
                    "goals": [goal],
                    "decision_rules": [rule],
                    "contradictions": contradiction,
                    "voice_examples": [voice],
                    "capabilities": ["self.speak", "self.observe"],
                    "forbidden_authority": ["world outcomes"],
                    "knowledge_refs": [],
                    "readiness": "ready",
                }
                for character_id, name, role, identity, values, goal, rule, contradiction, voice in [
                    ("mira", "Mira", "Scout", "A cautious scout.", "Party safety.", "Open the route.", "Test before confronting.", "Patient but protective.", "Low tide."),
                    ("iko", "Iko", "Envoy", "An evidence-led envoy.", "Verifiable evidence.", "Stop a false alarm.", "Verify before classifying.", "Procedural but adaptive.", "Show me the timestamp."),
                ]
            ],
        }
        pack = compile_pack(request)
        result = validate_pack(pack)
        self.assertTrue(result["ok"])
        self.assertEqual(result["ready_count"], 2)


class AgentSeatHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.campaign = Path(self.temporary.name) / "campaign"
        self.dashboard = self.campaign / "dashboard"
        self.dashboard.mkdir(parents=True)
        (self.dashboard / "index.html").write_text("<!doctype html><title>test</title>", encoding="utf-8")
        self.state_path = self.campaign / "agent_seat_state.json"
        self.state_path.write_text(json.dumps(initial_state()), encoding="utf-8")
        open_beat(self.state_path, open_request())
        handler = functools.partial(DashboardHandler, directory=str(self.dashboard))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def _json(self, request: urllib.request.Request) -> tuple[int, dict]:
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def test_context_and_same_origin_submit(self) -> None:
        status, context = self._json(urllib.request.Request(f"{self.origin}/api/seat/context"))
        self.assertEqual(status, 200)
        self.assertEqual(context["seat"]["display_name"], "Mira")
        payload = json.dumps(turn_request()).encode("utf-8")
        request = urllib.request.Request(
            f"{self.origin}/api/seat/turn",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json", "Origin": self.origin},
        )
        status, result = self._json(request)
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "pending")

    def test_cross_origin_submit_is_rejected(self) -> None:
        payload = json.dumps(turn_request()).encode("utf-8")
        request = urllib.request.Request(
            f"{self.origin}/api/seat/turn",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json", "Origin": "https://attacker.example"},
        )
        status, result = self._json(request)
        self.assertEqual(status, 403)
        self.assertEqual(result["failure_category"], "origin_invalid")


if __name__ == "__main__":
    unittest.main()

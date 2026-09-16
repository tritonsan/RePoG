# RePoG Agent Seat

Agent Seat lets a browser agent control one existing RPG character without
giving that agent GM context or direct campaign write access. The fictional
character and the participant controlling it remain separate concepts.

## Authority Boundary

`campaign/agent_roster.json` owns candidate/readiness policy. Only validated
T3 party-capable characters can become ready, and only one ready character may
be bound at a time. `campaign/agent_seat_state.json` owns only operational
participant state:

- one seat-to-character binding;
- one open beat and its source campaign revision;
- one explicitly curated, character-safe perspective;
- at most one pending intent;
- one character-visible current resolution and bounded prior-turn history;
- bounded idempotency evidence.

It does not own fictional truth. A pending intent cannot change a character,
location, relationship, inventory item, clue, or continuity revision. The GM
must resolve the human and Agent Seat proposals together and persist the
result through the ordinary RPG transaction.

The portable boundary is versioned under `contracts/agent-seat/v1/`:

- `AgentSessionPack` carries only the game contract, ready character cards,
  machine-readable capabilities, knowledge references, and session policy;
- `AgentTurnBrief` is the current character-safe projection;
- `AgentIntentEnvelope` separates actor, action type, targets, owned resources,
  cited knowledge, requested effect, and forbidden asserted outcomes;
- `AgentResolutionEnvelope` carries only the outcome and consequences visible
  to the active character.

Unknown capabilities are denied. Targets, resources, and knowledge references
must exist in the current brief. An agent may request an effect but the
`asserted_outcomes` list must remain empty because RePoG is the sole outcome
authority.

### Portable Envelopes And Local Records

The four portable schemas ship in the player ZIP. Local seat state and HTTP
requests retain their separate storage/transport format; do not validate a raw
local record as a portable envelope.

`tools/compile_agent_brief.py` provides read-only adapters:

- `compile-pack` produces the versioned Session Pack. The Python
  `compile_state_brief(pack, next_turn)` function produces a Turn Brief from
  the ready, bounded `agent_seat.get_next_turn` response.
- `import-intent --input-json ...` accepts an object with `intent` and `brief`
  fields. It checks the portable intent's turn, source revision, actor, and
  character authority, then returns a local `request`. Submit that request
  through the ordinary `agent_seat.submit_turn` entry point; submission checks
  the live beat again. Translation alone writes nothing.
- `export-resolution --input-json ...` accepts the bounded resolved next-turn
  response and returns a portable `resolution`. It exports only visible
  consequences; internal timestamps and local operational fields stay out.

The source test suite validates a real compile → submit → resolve lifecycle
against all four schemas, including stale-turn and unauthorized-reference
rejections. No third-party schema package is required during ordinary play.

## Local Table Flow

1. Session Zero explicitly chooses Agent Seats `off` or `on_demand` inside the
   existing Play/System decision.
2. The GM validates the roster, prepares a safe seat projection, and invokes `open-beat` with the
   current scene and continuity revision.
3. The browser agent opens the Dashboard through `serve_dashboard.py`.
4. The page registers progressive-enhancement WebMCP tools:
   `repog.get_my_perspective`, `repog.recall_my_knowledge`,
   `repog.commit_turn`, and `repog.get_turn_status`.
5. `commit_turn` writes one pending proposal using a stable operation id and
   expected scene revision.
6. The GM reads the pending intent, resolves the causal beat, and commits any
   established world changes through the existing RPG writer.
7. The GM invokes `resolve-turn` with only consequences the controlled
   character may perceive.

After resolution, the GM may open the next beat without resetting the state.
The previous intent and visible resolution move into bounded `turn_history`.
`next-turn` returns `ready`, `waiting`, `resolved`, `paused`, or `complete`;
pause/resume operations preserve the same durable session. WebMCP cannot wake
a closed model session, so a later client resumes rather than restarting.

The Dashboard tiles remain read-only. The Table status strip displays only
seat readiness and never displays the private perspective.

## Open-Beat Request

```json
{
  "operation_id": "open-dock-001",
  "expected_seat_revision": 0,
  "seat": {
    "seat_id": "mira",
    "character_ref": "characters/mira.md",
    "display_name": "Mira",
    "role": "Scout",
    "persona": {
      "goals": ["Keep the party alive without surrendering initiative."],
      "voice_anchors": ["Concise", "Dry humor"],
      "boundaries": ["Do not invent another character's thoughts."]
    }
  },
  "beat": {
    "beat_id": "dock-001",
    "scene_id": "dock-arrival",
    "source_revision": 12
  },
  "projection": {
    "summary": "A nervous guard blocks the cellar door.",
    "perceivable_facts": ["The guard keeps his left hand close to his coat."],
    "self_knowledge": ["You are positioned near the rear exit."],
    "known_facts": ["You recognize the ring from the Black Gull inn."],
    "party_public_facts": ["The party needs access to the cellar."],
    "allowed_actions": ["Observe", "Question", "Signal", "Act"]
  }
}
```

Only material already supported by campaign authorities should enter the
projection. The helper validates shape and bounds, not fictional truth; the GM
remains responsible for epistemic correctness.

## HTTP Boundary

The local server exposes only:

- `GET /api/seat/context`
- `GET /api/seat/next-turn?after_revision=...`
- `GET /api/seat/turn-status?operation_id=...`
- `POST /api/seat/turn`
- `POST /api/seat/pause`
- `POST /api/seat/resume`
- `POST /api/seat/complete`

It binds to loopback, requires a local Host, rejects cross-origin writes,
limits JSON body size, and serves neither the campaign directory nor GM-only
state.

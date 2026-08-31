# WebMCP Challenge build manifest

This manifest separates the pre-challenge RePoG baseline from the WebMCP Agent Seat work prepared for the challenge.

## Baseline

- Public repository: `https://github.com/tritonsan/RePoG`
- Pre-WebMCP baseline commit: `4813bc8` (`Implement Deep Session 0 v8`)
- RePoG remains the sole authority for game state, resolution, visibility, and continuity.

## Challenge implementation

- Canonical, genre-neutral Agent Session Pack, Turn Brief, Intent, and Resolution contracts under `contracts/agent-seat/v1/`.
- Session Zero opt-in and Tier 3 companion readiness integrated into the core campaign workflow.
- Persistent Agent Seat lifecycle: join once, receive successive bounded briefs, submit intent-only turns, pause, resume, and stop on explicit conditions.
- Deterministic local authority checks for actor, targets, owned resources, knowledge provenance, optimistic revision, and idempotency.
- Hosted WebMCP application under `apps/webmcp/`, with D1-backed sessions and two deliberately different fixture worlds.
- Secure relay mode with a server bootstrap secret, short-lived session-specific bridge credentials, separate browser invitation credentials, HttpOnly session cookies, expiry, body limits, and same-origin browser writes.
- Local bridge adapter under `tools/agent_bridge.py`; it transports compiled projections and intents but never resolves narrative outcomes.

## Demo versus product boundary

The Black Gull and Orison scenarios are deterministic judging fixtures. They prove that the same WebMCP contract works across fantasy intrigue and science-fiction crisis play. They are not the product's content model. Real games use a RePoG-compiled Agent Session Pack and successive bounded Turn Briefs through relay mode.

## Verification surface

- Python Agent Seat and bridge tests: `tests/test_agent_seat.py`
- Hosted contract/policy tests: `apps/webmcp/tests/contracts.test.ts`
- Workspace validation: `tools/verify_workspace.py`
- Hosted production build, lint, production dependency audit, local D1 migrations, fixture E2E, and relay E2E.

## Source provenance

The initial hosted prototype history was preserved before integration (`65ad847`, `ed988b8`, `9f95faa`). The complete hosted source now lives in the public RePoG repository rather than a disconnected nested repository.

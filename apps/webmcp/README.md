# RePoG Living Table

The hosted WebMCP relay and deterministic demonstration surface for RePoG
Agent Seat. It registers generic, character-independent WebMCP tools and keeps
durable sessions, turn briefs, structured intents, visible resolutions, and
event traces in D1.

## Modes

- `fixture`: Black Gull and Orison demonstrate the same Agent Session Pack v1
  contract with deterministic, clearly bounded resolutions.
- `bridge`: a local RePoG workspace uploads an explicitly safe pack and turn
  brief, receives the agent's pending intent, resolves it through the ordinary
  RePoG game flow, and returns only character-visible consequences.

The relay never receives campaign files, GM truth, or another participant's
private state. Bridge session creation requires the hosted
`REPOG_RELAY_BOOTSTRAP_KEY`; every created session receives separate bridge and
browser invitation credentials.

## Development

```bash
npm install
npm run db:migrate:local
npm test
npm run eval:webmcp
npm run lint
npm run build
```

The D1 schema is owned by `db/schema.ts`; generated migrations are committed
under `drizzle/`. Testable WebMCP tool definitions live in
`lib/webmcp-tools.ts`; the page only registers them. Hosted contract copies
are checked against the canonical repository schemas with
`python ../../tools/sync_agent_contracts.py --check`.

For a real RePoG session, create the relay with `--agent-state`, then run the
restart-safe worker:

```bash
python tools/agent_bridge.py watch --state campaign/agent_bridge_state.json
```

The worker submits remote intents through `agent_seat.py`, waits for RePoG to
resolve them, publishes only visible consequences, and advances the relay when
the next bounded beat becomes ready. `--once` performs one transition for
schedulers and diagnostics.

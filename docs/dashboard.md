# Local Campaign Dashboard V3

RePoG includes an optional, local-only, player-safe campaign board. It is a
secondary view, never the campaign source of truth. Dashboard V3 shows only the
tiles a campaign actually needs and does not invent a ready character, default
stats, or mechanical resources during Session 0.

## V3 State

`campaign/dashboard/dashboard_state.json` has two revision fields:

- `source_revision`: the campaign continuity revision represented by the board;
- `dashboard_revision`: the board edit revision used for optimistic updates.

It also records `scene_id`, an update timestamp, and refresh status/reason. The
`tiles` list accepts these types:

```text
setup_progress  scene       character   stats
resources       clocks      conditions  companions
people          threads     clues       inventory
map             gallery
```

A minimal active board can contain only a scene and people tile. Mechanics-light
campaigns should omit stats, resources, conditions, clocks, and inventory tiles
unless the Player explicitly chose those systems.

Example:

```json
{
  "schema_version": "3.0",
  "dashboard_version": 3,
  "dashboard_revision": 4,
  "source_revision": 12,
  "scene_id": "old-dock-arrival",
  "updated_at": "2026-07-16T12:00:00Z",
  "refresh_interval_ms": 4000,
  "refresh": {"status": "current", "reason": "Scene changed"},
  "campaign": {"title": "Salt Road", "pitch": "A hard voyage home.", "tone": "Tense wonder"},
  "theme": {"accent": "#7dd3fc", "background": "#0f1115", "mood": "Cold dawn"},
  "tiles": [
    {
      "id": "scene",
      "type": "scene",
      "title": "Current Scene",
      "order": 10,
      "data": {
        "title": "Old Dock",
        "location": "Lantern Quay",
        "summary": "Rain needles the empty landing.",
        "pressure": "The tide turns soon.",
        "image": ""
      }
    }
  ]
}
```

V2 files remain readable in the browser through a compatibility adapter. New
campaigns and all atomic update tooling use V3.

## Validate And Open

From the workspace root:

```bash
python tools/check_dashboard.py campaign/dashboard/dashboard_state.json
python tools/serve_dashboard.py campaign/dashboard
```

Then open `http://127.0.0.1:8787/`. The server binds only to loopback, validates
the state before startup and before serving state updates, disables directory
listing, and adds no-cache and browser security headers. Use `--check-only` to
validate the server target without opening a port.

## Atomic Tile Updates

Use the board revision shown in the current state:

```bash
python tools/update_dashboard.py campaign/dashboard/dashboard_state.json \
  --input-json '{"expected_revision":0,"source_revision":1,"scene_id":"arrival","refresh":{"status":"current","reason":"Opening scene prepared"},"operations":[{"op":"upsert","tile":{"id":"scene","type":"scene","title":"Current Scene","order":10,"data":{"title":"Arrival","location":"Old Dock","summary":"The voyage begins.","pressure":"","image":""}}}]}'
```

`upsert` replaces one tile by id or appends it; `remove` takes an `id`. The tool
refuses a stale `expected_revision`, validates the complete candidate, and uses
an atomic file replacement. It never rewrites campaign memory.

## Map And Accessibility

A map tile uses local Leaflet assets, positive width/height bounds, unique nodes
inside those bounds, valid edges, and an optional current node. Every map also
renders a keyboard-readable text list of locations and routes. Refreshes update
only changed tiles and preserve the map view and open place when possible.

Accepted images open in a keyboard-safe dialog that restores focus. The board
honors reduced-motion preferences. External image URLs, absolute paths, draft
assets, missing assets, hidden fields, invalid theme colors, duplicate ids, and
stale continuity revisions fail validation.

## Visual Acceptance And Return

Generated images are drafts until accepted. Use the transaction tool:

```bash
python tools/visual_handoff.py campaign begin --transaction-id visual-example --input-json '{"target":"Player portrait","interrupted_context":"Session Zero","last_meaningful_beat":"The character concept was confirmed.","return_anchor":"Session Zero: visual choice","next_step":"Ask whether to begin play","dashboard_placement_requested":true}'
python tools/visual_handoff.py campaign attach --transaction-id visual-example --draft-path visuals/_drafts/portrait.png
python tools/visual_handoff.py campaign accept --transaction-id visual-example --name "Ari" --visual-type character --destination assets/characters/ari-v1.png --campaign-destination visuals/characters/ari-v1.png --canon-notes "Short dark hair and a weathered red coat."
```

Use the transaction id returned by `begin`; the fixed id above is illustrative.
`accept` copies the approved asset into campaign visual memory and dashboard
assets, updates the visual gallery, records appearance canon, performs requested
dashboard placement, and clears the pending state as one rollback-protected
chain. `--campaign-destination` is optional; when omitted, the visual type selects
an accepted `visuals/` category. Its `resume` result is the required return to
the interrupted question or fictional beat. `revise` and `cancel` preserve the
same anchor.

## Player-Safe Boundary

Only confirmed, player-known information belongs in dashboard state. Never add
GM-only truth, protected names, secret motives, unrevealed clues, internal ids,
campaign file paths, or workflow notes. Accepted source assets live below
`campaign/visuals/`; their player-board copies live below
`campaign/dashboard/assets/` and are referenced as relative `assets/...` paths.

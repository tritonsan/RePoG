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
map             gallery     documents
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

A map tile uses only bundled Leaflet assets and never requires a remote tile
provider or API key. Legacy `bounds + nodes + edges` maps remain readable.
New maps should use the Atlas V1 contract, which can represent points, routes,
boundaries, water, regions, terrain, structures, and hazards without changing
Dashboard V3 itself.

Atlas V1 uses an explicit top-left Cartesian coordinate space. `schematic`
projection communicates approximate topology; `spatial` is reserved for
approved geography. Four scales are available: `region`, `city`, `interior`,
and `network`. Skins (`auto`, `minimal`, `survey`, `civic`, `field`, and
`systems`) change visual provenance only. They never change knowledge, access,
risk, or route truth.

```json
{
  "atlas_version": 1,
  "coordinate_space": {
    "type": "cartesian",
    "width": 1000,
    "height": 640,
    "origin": "top_left"
  },
  "scale_mode": "region",
  "projection": "schematic",
  "skin": "survey",
  "current_feature_id": "lantern-quay",
  "features": [
    {
      "id": "lantern-quay",
      "label": "Lantern Quay",
      "style_role": "place",
      "knowledge_state": "confirmed",
      "access_state": "open",
      "risk_state": "none",
      "geometry": {"type": "point", "coordinates": [180, 420]}
    },
    {
      "id": "north-gate",
      "label": "North Gate",
      "style_role": "landmark",
      "geometry": {"type": "point", "coordinates": [590, 250]}
    },
    {
      "id": "salt-road",
      "label": "Salt Road",
      "style_role": "route",
      "from": "lantern-quay",
      "to": "north-gate",
      "geometry": {
        "type": "line",
        "coordinates": [[180, 420], [360, 350], [590, 250]]
      }
    }
  ]
}
```

`campaign/map_atlas.json` is the editable cartographic source. Point features
may keep a `location_ref` matching a player-known location-graph endpoint;
generated routes keep an internal `route_ref`. Those provenance fields are
removed from the player-facing tile. Authored areas and line geometry remain
stable across later compiles, while newly known graph endpoints receive a
deterministic schematic position.

Preview or apply the derived tile with:

```powershell
python tools/compile_map_atlas.py campaign --dry-run
python tools/compile_map_atlas.py campaign
```

The compiler runs only when the map tile is enabled. It reads `Player-known`
connections, omits unknown topology, validates the complete candidate board,
and uses the current continuity revision for an atomic Dashboard V3 patch. A
second unchanged run is a no-op. `--emit-request` prints the patch without
writing it when another workflow needs to apply the update.

State axes stay separate:

- knowledge: `confirmed`, `reported`, `inferred`, `stale`;
- access: `open`, `conditional`, `blocked`, `unknown`;
- risk: `none`, `caution`, `danger`, `unknown`.

An unknown feature must be omitted entirely because even its silhouette or
route stub can reveal hidden topology. Generated schematic context may use an
unlabelled `presentation_only: true` neutral area; it is decorative and does
not enter popups, selection, legends, or the text atlas.

Every map provides a synchronized keyboard-readable atlas ordered around the
current location, then known places, areas, and routes. Visual states use line
pattern, shape, and text as well as color. Refreshes update only changed tiles
and preserve the map view, selected feature, open detail, and text-atlas state
when possible.

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

## World Voices Documents

The optional V3 `documents` tile points only to
`assets/world_voices/catalog.json`. The catalog contains bounded page
references; each page holds at most 40 player-safe summaries, and each readable
document is a separate validated JSON file. This keeps the central Dashboard
state and initial load bounded while allowing a large local archive.

Inbox, Public, Archive, Threads, source/type filters, search, local unread
emphasis, a document reader, and Compare Accounts are presentation only. Read
state stays in browser storage. Replies and all campaign-changing annotations
happen through natural-language play.

The controlled personal, newspaper, faction, official, intelligence, and
neutral skins use local HTML/CSS and text-only insertion. Open reader/focus
state survives unrelated tile refreshes. Compare Accounts displays only
player-known statements and never announces objective truth.

Private `campaign/world_voices/` files are never browser-readable. Hidden
documents are absent from catalog files, pages, document filenames, visible
counts, search, and comparisons. The loopback server validates each requested
World Voices JSON file before serving it. See `docs/world-voices.md`.

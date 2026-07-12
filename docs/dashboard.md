# Local Campaign Dashboard

RePoG can include a local, auto-refreshing player board for each campaign.

The dashboard is optional. It is not the campaign's source of truth. It is a
player-facing surface that shows selected, safe information from the campaign:
current scene, character state, visible NPCs, known clues, active threads,
inventory, a pan/zoom local atlas, and accepted visuals.

## How It Works

Each standalone campaign may contain:

```text
campaign/dashboard/
  index.html
  dashboard_state.json
  assets/
  vendor/leaflet/
```

`dashboard_state.json` is curated by the agent. It should contain only
information the player character can know, perceive, or has already confirmed.

`index.html` reads `dashboard_state.json` every few seconds and updates the
view. The V2 template vendors Leaflet locally for the atlas; it does not use a
CDN and should keep working offline once the repository is present.
Leaflet's license is included under `vendor/leaflet/LICENSE`.

## Dashboard V2 Shape

V2 is still read-only and player-safe. Add these optional fields when a
campaign wants the richer local atlas:

```json
{
  "dashboard_version": 2,
  "map": {
    "mode": "leaflet_simple",
    "summary": "Player-known space",
    "background_image": "assets/maps/local-atlas.png",
    "bounds": { "width": 1000, "height": 640 },
    "current_node_id": "dock",
    "nodes": [
      {
        "id": "dock",
        "label": "Old Dock",
        "type": "place",
        "x": 420,
        "y": 280,
        "status": "current",
        "summary": "Where the character is now."
      }
    ],
    "edges": [
      { "from": "dock", "to": "market", "status": "known", "label": "main road" }
    ]
  }
}
```

If no atlas image exists, keep `background_image` blank. The board will render a
neutral abstract map surface with player-known nodes and routes.

## Open It Locally

From the repository root:

```bash
python -m http.server 8787 --directory campaign/dashboard
```

Then open this in Codex's in-app browser or a normal browser:

```text
http://localhost:8787/
```

## Player-Safe Rule

The dashboard must never show:

- GM-only truth;
- protected names before reveal;
- unrevealed clues or secret motives;
- internal ids;
- file paths outside `assets/`;
- prompt, tool, validation, script, YAML, or Markdown language;
- notes about how the agent stores or checks the campaign.

If a fact belongs in `knowledge_boundaries.md` as hidden, it does not belong in
the dashboard.

## Image Assets

Store accepted player-visible images under:

```text
dashboard/assets/
```

Use relative paths in `dashboard_state.json`, such as:

```json
"image": "assets/locations/lantern-quay.png"
```

Do not reference absolute local paths, external URLs, draft images, or secret
GM-only visuals.

For V2, map backgrounds also count as dashboard assets and must use
`assets/...` paths.

## Checks

Validate the dashboard state:

```bash
python tools/check_dashboard.py campaign/dashboard/dashboard_state.json
```

Validate the campaign folder:

```bash
python tools/check_state.py campaign
```

## Visual Acceptance And Return

Generated images are drafts until accepted. When the Player asks to create an
image and add it to the dashboard, the agent previews the draft first, explains
before generation that acceptance will be needed, and completes the asset copy
plus dashboard reference only after acceptance.

Afterward, the agent returns to the interrupted Session 0 step or play scene. A
bare "dashboard updated" message is not a complete player experience.

## Known Limits

- The dashboard is read-only. Player actions still happen in the agent chat.
- The dashboard is local-only.
- The agent must curate `dashboard_state.json`; there is no automatic exporter
  from all campaign notes yet.
- If the local server is not running, the page may not load the JSON in some
  browser contexts.

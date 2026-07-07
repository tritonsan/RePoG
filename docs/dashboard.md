# Local Campaign Dashboard

RePoG can include a local, auto-refreshing player board for each campaign.

The dashboard is optional. It is not the campaign's source of truth. It is a
player-facing surface that shows selected, safe information from the campaign:
current scene, character state, visible NPCs, known clues, active threads,
inventory, simple map links, and accepted visuals.

## How It Works

Each campaign may contain:

```text
campaigns/<campaign_id>/dashboard/
  index.html
  dashboard_state.json
  assets/
```

`dashboard_state.json` is curated by the agent. It should contain only
information the player character can know, perceive, or has already confirmed.

`index.html` reads `dashboard_state.json` every few seconds and updates the
view. It has no external dependencies.

## Open It Locally

From the repository root:

```bash
python -m http.server 8787 --directory campaigns/<campaign_id>/dashboard
```

Then open this in Codex's in-app browser or a normal browser:

```text
http://localhost:8787/
```

For the template dashboard:

```bash
python -m http.server 8787 --directory templates/campaign/dashboard
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

## Checks

Validate the dashboard state:

```bash
python tools/check_dashboard.py campaigns/<campaign_id>/dashboard/dashboard_state.json
```

Validate the campaign folder:

```bash
python tools/check_state.py campaigns/<campaign_id>
```

## Known Limits

- The dashboard is read-only. Player actions still happen in the agent chat.
- The dashboard is local-only in V1.
- The agent must curate `dashboard_state.json`; there is no automatic exporter
  from all campaign notes yet.
- If the local server is not running, the page may not load the JSON in some
  browser contexts.

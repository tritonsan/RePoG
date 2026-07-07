# Demo Script

This is a short script for a future demo video or GIF.

Target length: 60 to 90 seconds.

## Goal

Show that RePoG can start a campaign through Codex, create campaign memory, run
checks, and begin a natural opening scene.

## Flow

1. Open the `RePoG` folder in Codex.
2. Show `README.md` and `START_HERE.md`.
3. Paste the Quick Start prompt.
4. Answer a few Session 0 questions with the recommended original demo
   setting below.
5. Show Codex creating or filling a campaign folder.
6. Show Codex preparing the local dashboard state for the opening scene.
7. Show a quick check command:

   ```bash
   python tools/check_state.py campaigns/<campaign_id>
   python tools/check_dashboard.py campaigns/<campaign_id>/dashboard/dashboard_state.json
   ```

8. Open the dashboard in the Codex in-app browser:

   ```bash
   python -m http.server 8787 --directory campaigns/<campaign_id>/dashboard
   ```

   Then open `http://localhost:8787/`.

9. Show the first opening scene.
10. Enter one player action in natural language.
11. Briefly show that campaign notes and the dashboard changed behind the
    scenes.

## What To Emphasize

- The player speaks naturally.
- Codex handles the campaign notebook.
- Important memory is in readable files.
- The local dashboard shows only player-known information.
- Checks exist, but the game does not feel like a state engine.
- RePoG is a workspace pattern, not a standalone app.

## Recommended Demo Setting

Use this original setting for the public demo unless a better one appears.

### The Saltglass City

Pitch:

```text
A half-sunken city built on glass reefs, where smugglers, saints,
debt-collectors, and storm-divers fight over memories crystallized by the sea.
```

Why it works for a short demo:

- original and safe from franchise/IP confusion;
- visually strong in a GIF or short video;
- easy to understand in one sentence;
- supports hidden knowledge, NPC memory, factions, relationships, arc hooks,
  and optional visual generation;
- strange enough to feel memorable without requiring a lore dump.

Suggested Session 0 answers:

- Genre: weird nautical fantasy noir.
- Tone: atmospheric, grounded, mysterious, not grimdark.
- Player fantasy: ex-diver, investigator, survivor.
- World: The Saltglass City.
- Campaign length: short demo with long-campaign potential.
- Canon policy: original world, no external canon.
- Visuals: yes, one opening location image only.
- Art direction: painterly cinematic concept art; salt, glass, rain, lanterns,
  teal, gold, black; no anime, no neon cyberpunk.

Suggested player character:

```text
Mara Venn, a former storm-diver who can hear fragments of memories trapped
inside saltglass. She returns to the city after receiving a shard containing
her dead brother's voice.
```

Suggested first visual:

```text
Lantern Quay, a rain-slick dock district built over black water and pale glass
reefs, with hanging storm bells, small boats, wet stone stairs, and warm
lanterns reflected in the tide.
```

Suggested opening:

Mara arrives at Lantern Quay at dawn. A courier has left a saltglass shard
wrapped in oilcloth. It whispers her brother's voice, but only when the tide
pulls back. The GM should show the place, the arrival context, the visible
situation, and the neutral action space without explaining the full mystery.

## Avoid

- Showing copyrighted worlds.
- Spending too long on folder internals.
- Making it look like users need to understand every template before playing.
- Presenting RePoG as Codex-only.

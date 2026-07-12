# RePoG Workspace

RePoG turns an agentic coding workspace into a long-form solo tabletop RPG Game
Master. This repository is the ready-to-play workspace: download the ZIP, open
the extracted folder, and start a new conversation.

## Start

1. Select **Code → Download ZIP** on GitHub.
2. Extract the ZIP and optionally rename the folder for your campaign.
3. Open that extracted folder in Codex, Claude Code, or another agentic coding
   tool.
4. Start a new conversation and send:

   ```text
   Start this RePoG campaign and guide me through Session 0.
   ```

5. Choose Quick, Standard, or Deep Session 0 and answer naturally.

The included `campaign/` folder is blank campaign memory. The agent fills and
maintains it while you focus on the character, world, and choices. You do not
need to copy templates, run an installer, clone a development repository, or
understand the file structure before playing.

## Session 0 Depth

- **Quick:** 6–8 decisions, roughly 10–15 minutes.
- **Standard:** 17 core modules, roughly 30–60 minutes.
- **Deep:** adaptive detail packs, normally 30–45 decisions and 60–120 minutes.

All modes use the same continuity model. Quick records visible defaults;
Standard gives a balanced setup; Deep opens only the detail packages relevant
to the chosen campaign.

## What RePoG Keeps Coherent

- current scene, fictional time, character state, inventory, and pressure;
- NPC location, activity, availability, natural presence, and independent next
  move;
- playable routes, access, traffic, and player-known locations;
- current relationships, debts, trust, tension, and information asymmetry;
- factions and offscreen world movement only when fiction triggers them;
- secrets and knowledge boundaries;
- progression, companion development, arc closure, and next-act preparation;
- accepted visuals and the optional player-safe dashboard.

During play, these notes and checks remain behind the curtain. The player
speaks in natural language and receives the living world, not technical state.

## Optional Dashboard

After Session 0, open the local player dashboard with:

```bash
python -m http.server 8787 --directory campaign/dashboard
```

Then visit `http://localhost:8787/`. The dashboard is read-only and contains
only player-known information. See [`docs/dashboard.md`](docs/dashboard.md).

## Optional Checks

```bash
python tools/check_state.py campaign
python tools/check_dashboard.py campaign/dashboard/dashboard_state.json
python tools/snapshot.py campaign --label before_scene
```

These are guardrails, not a second game engine.

## Workspace Contents

- `AGENTS.md`: durable GM and continuity rules.
- `CLAUDE.md`: compatibility bridge for Claude Code.
- `OPEN_CAMPAIGN.md`: first-conversation instructions.
- `workflows/`: worldbuilding, GM, distill, and audit procedures.
- `briefs/`: Session 0 interview guidance.
- `campaign/`: this game's readable memory and player dashboard.
- `tools/`: small local checks, snapshots, mechanics, and style helpers.

RePoG is licensed under the Apache License, Version 2.0. See [`LICENSE`](LICENSE).

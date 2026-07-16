# RePoG Workspace

RePoG turns an agentic coding workspace into a long-form solo tabletop RPG Game
Master. This repository is the ready-to-play workspace: download the ZIP, open
the extracted folder, and start a new conversation.

## Watch the Demo

[![Watch the RePoG demo](https://img.youtube.com/vi/jpXtyfrd5k0/maxresdefault.jpg)](https://youtu.be/jpXtyfrd5k0)

▶ **[Watch the full RePoG demo on YouTube](https://youtu.be/jpXtyfrd5k0)**

## Start

<details>
<summary><strong>Show the four-step installation guide</strong></summary>

The interface language and exact layout may differ from the recordings, but the
four steps are the same.

### 1. Download the workspace

On GitHub, select **Code → Download ZIP**.

![Select Code and Download ZIP on GitHub](assets/getting-started/01-download-zip.gif)

The current repository file list may look simpler than the recording because
the public download has since been reduced to the clean player workspace.

### 2. Extract the ZIP

Extract the archive into a new folder. You may rename that folder for your
campaign.

![Extract the downloaded RePoG ZIP](assets/getting-started/02-extract-workspace.gif)

### 3. Open the folder

In Codex, select **Open Folder** and choose the extracted workspace. The same
folder can also be opened in Claude Code or another agentic coding tool.

![Open the extracted RePoG folder in Codex](assets/getting-started/03-open-in-codex.gif)

### 4. Start Session 0

Start a new conversation in the opened workspace and send:

```text
Start this RePoG campaign and guide me through Session 0.
```

![Start a new conversation in the RePoG workspace](assets/getting-started/04-start-conversation.gif)

Choose Quick, Standard, or Deep Session 0 and answer naturally. After your
pitch, RePoG offers a small Starter Bundle of campaign-specific approaches;
you can accept one, mix them, change them, use the recommended default, or
defer a non-critical choice.

</details>

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

## Lenses And Optional Mechanics

Session 0 can combine setting lenses (`fantasy`, `realistic`, `cyberpunk`) with
the `survival` play lens. Lenses shape questions and coherent defaults; they do
not silently turn on HP, mana, inventory accounting, dice, wounds, or other
rules. RePoG explains the tracking cost first, and only the mechanic modules
you approve become part of the campaign.

The resulting `play_profile.yaml` keeps the accepted lenses, mechanics,
narrative signature, player-authorship boundary, resolution grounding,
breather preference, advancement cadence, dashboard policy, visual policy,
and turn-speed preference in one compact runtime contract. This lets a mixed
fantasy-survival campaign keep both identities without making every fantasy
campaign track rations or spell points.

## Turn Speed And Continuity

Session 0 also asks how much maintenance each turn should perform:

- **Fast (recommended):** saves current truth immediately, uses a small scene
  checkpoint when needed, and reserves full distillation for five durable
  turns or a true structural boundary.
- **Balanced:** reconciles secondary notes at important beats or after three
  durable turns.
- **Maximum Continuity:** updates every affected note and runs full checks on
  every durable turn.
- **Custom:** lets you tune the cadence without disabling core continuity
  safeguards.

The setup interview shows typical wait ranges and separately explains the
extra time for dashboard refreshes and generated images. These are planning
estimates rather than guarantees.

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

## GM Flow And Breathing Room

RePoG resolves each turn from the player's stated intent and method, the
world's real resistance, what involved characters can actually know, and the
nearest causal consequence. The GM does not speak for the player character or
decide their private feelings unless the selected narration contract explicitly
invites shared interiority.

The pacing model also makes room for recovery, ordinary conversation,
maintenance, companion time, small exploration, and quiet personal choices.
A calm scene does not receive a surprise threat merely because the GM wants to
move on. The player may remain there, leave through a natural affordance, or
encounter an already-established world event when its real trigger becomes
due.

If you request a generated visual, RePoG first preserves the interrupted
question or fictional beat. A visual is not treated as campaign canon or added
to the dashboard until you accept it; after acceptance, revision, or
cancellation, play returns to the preserved point.

## Optional Dashboard

After Session 0, open the local player dashboard with:

```bash
python tools/serve_dashboard.py campaign/dashboard
```

Then visit `http://localhost:8787/`. The dashboard is read-only and contains
only player-known information. Dashboard V3 uses campaign-specific tiles, so a
mechanics-light game does not show invented stats or resources. Revision-aware
updates reject stale data instead of silently replacing newer state. See
[`docs/dashboard.md`](docs/dashboard.md).

## Optional Checks

```bash
python tools/verify_workspace.py
python tools/check_state.py campaign --scope hot
python tools/check_state.py campaign --scope full
python tools/check_dashboard.py campaign/dashboard/dashboard_state.json
python tools/snapshot.py campaign --label before_scene
```

`verify_workspace.py` is the dependency-free all-in-one smoke check for the
downloaded workspace. Add `--json` for agent-readable output. The individual
commands remain useful when diagnosing one area. These are guardrails, not a
second game engine.

## Workspace Contents

- `AGENTS.md`: durable GM and continuity rules.
- `CLAUDE.md`: compatibility bridge for Claude Code.
- `OPEN_CAMPAIGN.md`: first-conversation instructions.
- `workflows/`: worldbuilding, GM, distill, and audit procedures.
- `briefs/`: Session 0 interview guidance and composable genre lenses.
- `campaign/`: this game's readable memory and player dashboard.
- `tools/`: small local checks, snapshots, mechanics, and style helpers.

RePoG is licensed under the Apache License, Version 2.0. See [`LICENSE`](LICENSE).

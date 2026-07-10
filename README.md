# RePoG: A GM Workspace For Agentic Coding Tools

RePoG turns an agentic coding workspace into a long-form solo tabletop RPG
Game Master.

You bring the character, the world idea, and the choices. Your agent uses this
folder as its campaign notebook: it builds the world with you, remembers NPCs
and places, tracks secrets and relationships, prepares new arcs, and keeps the
game moving in natural language.

RePoG is designed and tested around OpenAI Codex-style repo workflows, but the
pattern is broader: any agentic coding tool that can read instructions, edit
Markdown files, and run small helper scripts can adapt it.

## Why This Matters

Long AI roleplay sessions often break in familiar ways:

- the model forgets NPCs, locations, debts, clues, and old decisions;
- NPCs accidentally know secrets the player character never revealed;
- every scene starts to feel like the same funnel toward the same clue;
- major arc endings happen without proper rewards, upgrades, or follow-through;
- the next session starts from vibes instead of durable campaign memory.

RePoG treats those problems as workspace problems. The campaign lives in files:
world notes, knowledge boundaries, creation ledgers, relationship maps,
progression reviews, snapshots, and lightweight checks. The GM can still
improvise, but important facts have somewhere to live.

The goal is simple: a campaign that feels like sitting with a GM, while the
agent quietly keeps a very good notebook.

## What You Can Do

- Start a fresh RPG campaign from any genre or universe.
- Build the world through a guided Session 0 interview.
- Play in ordinary natural language instead of commands or menus.
- Keep NPCs, companions, factions, locations, items, secrets, and relationships
  from being forgotten.
- Track why relevant NPCs are present, what they are doing independently, and
  where they plausibly go next.
- Keep gameable location connections, access, traffic, and travel facts in a
  compact graph.
- Separate GM-only truth from what the player, companions, NPCs, and factions
  actually know.
- Track character growth, companion growth, rewards, and major arc closures.
- Carry old NPCs, items, debts, threads, and consequences into the next act.
- Let the GM select only the memory relevant to the current scene instead of
  loading the entire campaign notebook every turn.
- Advance relevant factions, routines, economies, or other world domains on
  demand when the fiction triggers them.
- Optionally enforce resources, ability costs, cooldowns, and regeneration with
  small deterministic tools.
- Detect repeated narration length, sentence openings, stock phrases, and
  campaign-specific cliches.
- Use optional source or web research when canon, history, physics, culture, or
  genre logic matters.
- Open a local auto-refresh campaign board for the current scene, known clues,
  visible NPCs, inventory, a pan/zoom local atlas, and accepted visuals.
- Extend the workspace toward visual references when your agentic tool supports
  image generation or image display.
- Detect stale hot context, duplicate current relationships, broken location
  graph references, and incomplete presence logic with Lite V2 checks.

## Quick Start

1. Clone the repository.

   ```bash
   git clone https://github.com/tritonsan/RePoG.git
   cd RePoG
   ```

2. Open the `RePoG` folder in your agentic coding tool.

3. Start a new thread or session in that folder.

4. Paste this prompt:

   ```text
   Create a new RePoG campaign from scratch.
   Guide me through Session 0 one question at a time.
   Keep the setting open until I choose a universe, genre, and tone.
   If the world needs canon, historical, real-world, scientific, or genre
   research, make a short research dossier before locking the world rules.
   When the campaign is ready, create the campaign folder, check it, take a
   starting snapshot, and begin with a natural opening scene.
   ```

5. Answer the questions naturally. When setup is finished, play by writing what
   your character does.

For a shorter first step, open [`START_HERE.md`](START_HERE.md).

## How It Feels In Play

You write:

```text
I keep my smile, lower my voice, and ask the dock clerk who paid him to delay
the cargo.
```

The agent answers as the GM:

```text
The clerk's pen stops moving. For a moment he keeps his eyes on the ledger, as
if the numbers might protect him. Then he closes the book with two fingers and
says, "If I answer that, I need to know you're not about to make my day worse."
```

Behind the scenes, RePoG helps the agent remember what the clerk knows, what
the player has discovered, what should stay hidden, and what consequences may
return later. The player should not have to see that machinery during normal
play.

## Why Codex Is A Good Fit

RePoG is a strong fit for Codex because Codex already works inside a repo:

- `AGENTS.md` gives durable project instructions.
- `workflows/` tells the agent how to run worldbuilding, play, distill, and
  audit tasks.
- `templates/` gives every new campaign the same memory shape.
- `tools/` provides small checks for campaign state, player-facing leakage, and
  snapshots.
- Markdown memory lets Codex revise the world as play continues instead of
  relying only on chat history.

Read the longer rationale in [`docs/why-codex.md`](docs/why-codex.md).

## Examples

Starter examples are intentionally generic and non-IP:

- [`examples/fantasy-frontier`](examples/fantasy-frontier/)
- [`examples/orbital-noir`](examples/orbital-noir/)
- [`examples/historical-intrigue`](examples/historical-intrigue/)

They are not full campaigns. They show the kind of pitch, Session 0 answers,
world notes, player seed, and first scene brief RePoG expects.

## Project Status

RePoG is early, playable, and actively evolving. The current focus is the Lite
workspace: Markdown memory, natural GM behavior, Session 0 worldbuilding,
continuity, progression, and lightweight checks.

See:

- [`docs/roadmap.md`](docs/roadmap.md)
- [`docs/dashboard.md`](docs/dashboard.md)
- [`CHANGELOG.md`](CHANGELOG.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)

## What RePoG Is Not

RePoG is not a standalone game app, virtual tabletop, Discord bot, dice engine,
ruleset clone, or prewritten campaign.

It is a structured campaign workspace for an AI coding agent acting as GM.

<details>
<summary>What RePoG Tracks</summary>

RePoG gives the agent a campaign memory structure for:

- the campaign promise and tone;
- world rules, canon policy, and source research;
- the player character's stats, abilities, limits, and risks;
- NPCs, companions, factions, and locations;
- who knows what, including hidden facts and protected names;
- secrets and clues that can surface in different ways;
- relationships, debts, promises, reputation, and consequences;
- items, conditions, threats, and active threads;
- rewards, upgrades, companion growth, and arc closure;
- next-act preparation after a major arc ends.

The files are readable Markdown, so you can inspect or edit them when you want.
During play, the agent should keep them out of the narration.

</details>

<details>
<summary>For Agentic Tool Users</summary>

RePoG works best when the agent can:

- read repository instructions;
- edit Markdown and YAML files;
- run small Python helper scripts;
- keep a long-running conversation grounded in the campaign folder.

For OpenAI Codex, the main instruction file is `AGENTS.md`. Other agentic coding
tools can adapt the same files by reading the repository-local instructions and
following the workflows under `workflows/`.

Recommended startup files:

1. `AGENTS.md`
2. `workflows/worldbuild/WORKFLOW.md`
3. `briefs/campaign_creation_interview.md`

</details>

<details>
<summary>Campaign Folder Shape</summary>

A campaign folder is created under `campaigns/<campaign_id>/`.

Important memory files include:

- `campaign_one_pager.md`: the campaign promise.
- `research_dossier.md`: source research, canon, realism, and world logic.
- `world.md`: the compact campaign bible.
- `player.md`: the player character.
- `player_ties.md`: how the character changes the world.
- `storytelling.md`: narration and reveal preferences.
- `appearance_guide.md`: player, NPC, faction, and location appearance detail
  rules for continuity, staging, and future visuals.
- `knowledge_boundaries.md`: who knows what.
- `creation_ledger.md`: named NPCs, places, and factions.
- `relationship_map.md`: compact relationship links.
- `secrets_and_clues.md`: flexible discoveries.
- `progression.md`: rewards and advancement expectations.
- `arc_closure.md`: milestone and upgrade reviews.
- `next_act_prep.md`: what carries forward into the next major act.
- `opening_brief.md`: the next opening scene source.
- `current_state.yaml`: small structured state for checks.
- `world_dynamics.md`: on-demand offscreen domains and notable changes.
- `style_state.json`: bounded narration fingerprints for repetition checks.
- `mechanics_state.json`: optional deterministic resources and cooldowns.
- `dashboard/`: optional local player board.

The full template lives in `templates/campaign/`.

</details>

<details>
<summary>Optional Helper Tools</summary>

The helper tools use Python's standard library.

Check campaign shape:

```bash
python tools/check_state.py campaigns/<campaign_id>
```

Scan player-facing text for technical leakage:

```bash
python tools/check_player_facing.py --text "You step into the rain."
```

Create a reversible snapshot:

```bash
python tools/snapshot.py campaigns/<campaign_id> --label before_scene
```

Check a dashboard state file:

```bash
python tools/check_dashboard.py campaigns/<campaign_id>/dashboard/dashboard_state.json
```

Open a local campaign board:

```bash
python -m http.server 8787 --directory campaigns/<campaign_id>/dashboard
```

The dashboard is read-only, player-safe, and local. Its V2 template uses
vendored Leaflet for a no-CDN local atlas.

These tools are optional guardrails. The main experience is still the agent
reading and writing campaign notes.

</details>

<details>
<summary>Session 0 Modules</summary>

RePoG creates campaigns through a guided Session 0:

1. Campaign Pitch
2. Research Need Gate
3. Group Contract
4. System Fit
5. Canon Policy
6. Palette
7. World Truths
8. Scale
9. Current And Impending Issues
10. Factions
11. Faces And Places
12. Progression And Rewards
13. Player Character
14. PC Integration
15. Starting Situation / Session 0.5
16. Continuity Rules

The agent should ask one question at a time. The world should begin as a
playable core, not a complete encyclopedia.

</details>

## License

RePoG is licensed under the Apache License, Version 2.0. See [`LICENSE`](LICENSE).

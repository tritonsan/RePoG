# RePoG: A GM Workspace For Agentic Coding Tools

RePoG turns an agentic coding workspace into a long-form tabletop RPG Game
Master.

You bring the character, the world idea, and the choices. Your coding agent
uses this repository as its notebook: it builds the campaign with you, remembers
NPCs and places, tracks secrets and relationships, prepares new arcs, and keeps
the game moving in natural language.

RePoG is currently shaped and tested for OpenAI Codex-style repo workflows, but
the idea is broader: any agentic coding tool that can read and edit a folder of
Markdown files can use the same structure.

## What You Can Do With RePoG

- Start a fresh RPG campaign from any genre or universe.
- Build a world through a guided Session 0 interview.
- Play in natural language instead of commands or menus.
- Keep NPCs, companions, factions, locations, items, secrets, and relationships
  from being forgotten.
- Let the GM hide information until the character actually discovers it.
- Track character growth, companion growth, rewards, and major arc closures.
- Prepare the next act from what happened before, instead of starting each arc
  from a blank slate.
- Use web or source research during worldbuilding when canon, history, physics,
  culture, or genre logic matters.

The goal is simple: a campaign that feels like sitting with a GM, while the
agent quietly keeps a very good notebook.

## How It Feels In Play

You write what your character does:

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

## Quick Start

1. Download or clone the repository.

   ```bash
   git clone <repo-url> RePoG
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

5. Answer the questions. When the setup is finished, play by writing your
   character's actions in ordinary language.

## What RePoG Tracks

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

## What RePoG Is Not

RePoG is not a standalone game app.

It is also not a virtual tabletop, Discord bot, dice engine, ruleset clone, or
prewritten campaign. It is a structured campaign workspace for an AI coding
agent acting as GM.

You can play fantasy, sci-fi, crime, horror, political intrigue, anime-inspired
adventure, historical drama, or a completely original setting. The repository
does not ship with a fixed world.

## What's Next For RePoG

The current version focuses on the campaign notebook and GM behavior. The next
useful improvements are:

- better first-run examples for different genres;
- more sample campaigns that do not depend on any specific IP;
- clearer prompts for non-Codex agentic tools;
- image generation and image use for agentic tools that support visual
  workflows, such as character portraits, location moodboards, maps, clues,
  items, and faction symbols;
- optional dice and challenge helpers, only where they improve play;
- stronger audit tools for continuity, hidden knowledge, and arc transitions;
- improved guidance for publishing and sharing campaign templates.

The guiding rule is: add structure only when it helps the game feel more
natural, coherent, and alive.

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
- `knowledge_boundaries.md`: who knows what.
- `creation_ledger.md`: named NPCs, places, and factions.
- `relationship_map.md`: compact relationship links.
- `secrets_and_clues.md`: flexible discoveries.
- `progression.md`: rewards and advancement expectations.
- `arc_closure.md`: milestone and upgrade reviews.
- `next_act_prep.md`: what carries forward into the next major act.
- `opening_brief.md`: the next opening scene source.
- `current_state.yaml`: small structured state for checks.

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

RePoG is licensed under the Apache License, Version 2.0. See `LICENSE`.

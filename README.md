# RePoG

RePoG is a Codex-first tabletop RPG workspace.

It is designed to be opened in OpenAI Codex and used as a natural-language Game
Master system with durable Markdown memory. For now, RePoG is not a standalone
app, web service, Discord bot, VTT plugin, or general RPG engine. The intended
runtime is Codex.

## What RePoG Does

RePoG helps Codex run an RPG campaign by giving it:

- repo-local instructions in `AGENTS.md`;
- GM, worldbuilding, distill, and audit workflows;
- a campaign memory template made of readable Markdown files;
- lightweight Python checks for campaign shape, snapshots, and player-facing
  leakage;
- guardrails for NPC knowledge, hidden information, storytelling pace,
  progression, companion growth, and relationship tracking.

The goal is a table-like RPG flow: the player talks naturally, Codex plays the
world naturally, and the notes stay organized enough for long-running play.

## What Is Included

```text
RePoG/
  AGENTS.md
  README.md
  START_HERE.md
  briefs/
  workflows/
    gm/
    worldbuild/
    distill/
    audit/
  templates/
    campaign/
  campaigns/
  tools/
```

No setting-specific campaign is included. RePoG is universe-neutral by default.

## Requirements

- OpenAI Codex.
- Python 3.10 or newer for the optional local helper tools.

The helper tools use only Python's standard library.

## Use RePoG In Your Codex

1. Download or clone this repository.

   ```bash
   git clone <your-repog-repo-url> RePoG
   ```

2. Open the `RePoG` folder in Codex.

3. Start a new thread in that folder.

4. Ask Codex to create a campaign. Example:

   ```text
   Create a new RePoG campaign from scratch.
   Use the full modular Session 0 interview.
   Ask exactly one question at a time and wait for my answer.
   Keep the campaign setting-neutral until I choose a universe.
   ```

5. Codex should read:

   - `AGENTS.md`
   - `workflows/worldbuild/WORKFLOW.md`
   - `briefs/campaign_creation_interview.md`

6. Codex should ask the Session 0 questions one by one, then create a campaign
   folder under `campaigns/<campaign_id>/`.

7. When campaign files are created, run:

   ```bash
   python tools/check_state.py campaigns/<campaign_id>
   ```

8. Before play starts, ask Codex to draft the opening scene and scan it:

   ```bash
   python tools/check_player_facing.py --text "<opening scene>"
   ```

9. Create a starting snapshot:

   ```bash
   python tools/snapshot.py campaigns/<campaign_id> --label start
   ```

10. Begin play. In normal play, the player can write actions in natural
    language. Codex should use `workflows/gm/WORKFLOW.md`.

## Session 0 Modules

RePoG creates campaigns through a modular Session 0 interview:

1. Campaign Pitch.
2. Group Contract.
3. System Fit.
4. Canon Policy.
5. Palette.
6. World Truths.
7. Scale.
8. Current And Impending Issues.
9. Factions.
10. Faces And Places.
11. Progression And Rewards.
12. Player Character.
13. PC Integration.
14. Starting Situation / Session 0.5.
15. Continuity Rules.

Codex should ask one question at a time. The world should begin as a playable
core, not a complete encyclopedia.

## Campaign Memory

A campaign folder is built from the template in `templates/campaign/`.

Important files include:

- `world.md`: summary campaign bible.
- `campaign_one_pager.md`: player-facing campaign promise.
- `storytelling.md`: narration style, pacing, exposition, and reveal policy.
- `knowledge_boundaries.md`: who knows what; protected names; safe wording.
- `opening_brief.md`: first or post-arc opening source.
- `player.md`: player character.
- `player_ties.md`: character-linked world details.
- `creation_ledger.md`: compact record of named NPCs, places, and factions.
- `relationship_map.md`: compact edge-list relationship map.
- `secrets_and_clues.md`: flexible clues and discoveries.
- `progression.md`: rewards, milestones, companion advancement.
- `arc_closure.md`: closure reviews and upgrade decisions.
- `current_state.yaml`: small structured campaign state.

## Normal Play

When the player writes an action, Codex should:

1. Read the relevant campaign memory.
2. Check what the player character, companions, NPCs, and factions actually
   know.
3. Respond in Player Mode with only living fiction.
4. Update the smallest necessary memory files if the fiction changed.
5. Run helper checks when durable memory changed.

Player-facing narration must not expose file names, YAML, Markdown structure,
tool calls, prompts, internal notes, or implementation language.

## Helper Tools

Check campaign shape:

```bash
python tools/check_state.py campaigns/<campaign_id>
```

Scan player-facing text:

```bash
python tools/check_player_facing.py --text "You step into the rain."
```

Create a reversible snapshot:

```bash
python tools/snapshot.py campaigns/<campaign_id> --label before_scene
```

## Design Philosophy

RePoG is intentionally small.

Use Markdown instructions and campaign memory before adding code. Add new tools
only when repeated play proves that a deterministic check protects immersion,
continuity, or safety.

If a feature makes play feel like operating software instead of sitting with a
GM, challenge it before adding more machinery.

## License

RePoG is licensed under the Apache License, Version 2.0. See `LICENSE`.

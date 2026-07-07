# Start Here

Open this folder in your agentic coding tool and start a new thread or session.

Paste this:

```text
Create a new RePoG campaign from scratch.
Guide me through Session 0 one question at a time.
Keep the setting open until I choose a universe, genre, and tone.
If the world needs canon, historical, real-world, scientific, or genre
research, make a short research dossier before locking the world rules.
Use middle-detail appearance cards for the player, important NPCs, factions,
and locations so visual continuity stays stable without overloading the notes.
When the campaign is ready, create the campaign folder, check it, take a
starting snapshot, and begin with a natural opening scene.
```

Then answer the questions naturally.

You do not need to understand the folder structure before playing. RePoG is
designed so the agent handles the notebook while you focus on the character,
the world, and the choices.

Optional: RePoG campaigns can include a local player board under
`campaigns/<campaign_id>/dashboard/`. After a campaign exists, run:

```bash
python -m http.server 8787 --directory campaigns/<campaign_id>/dashboard
```

Then open `http://localhost:8787/` in Codex's in-app browser or a normal
browser. See `docs/dashboard.md`.

For OpenAI Codex, the agent should read:

1. `AGENTS.md`
2. `workflows/worldbuild/WORKFLOW.md`
3. `briefs/campaign_creation_interview.md`

After setup, play in natural language.

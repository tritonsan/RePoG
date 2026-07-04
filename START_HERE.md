# Start Here

Open this folder in Codex and start a new thread.

Ask Codex to start a campaign with the full modular Session 0 interview.

Example prompt:

```text
Create a new RePoG campaign from scratch.
Use the full modular Session 0 interview.
Ask exactly one question per message and wait for my answer.
Keep the campaign setting-neutral until I choose a universe.
When the campaign is ready, create the campaign folder, run the checks, take a
starting snapshot, and begin from the opening scene.
```

Codex should read:

1. `AGENTS.md`
2. `workflows/worldbuild/WORKFLOW.md`
3. `briefs/campaign_creation_interview.md`

After the campaign folder exists, run:

```bash
python tools/check_state.py campaigns/<campaign_id>
python tools/snapshot.py campaigns/<campaign_id> --label start
```

Before showing the first scene to the player, scan the draft:

```bash
python tools/check_player_facing.py --text "<opening scene>"
```

Then play in natural language.

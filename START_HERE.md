# Start Here

Create a clean folder for each new campaign from this repository:

```powershell
python tools/create_campaign_workspace.py `
  --target "D:\Games\My Campaign" `
  --campaign-id my_campaign `
  --git ask
```

The command never creates a remote or pushes to GitHub. It refuses to
overwrite a non-empty folder. Open the created folder in your agentic coding
tool and start a new thread or session.

Paste this:

```text
Start this RePoG campaign and guide me through Session 0.
```

Then answer the questions naturally.

You do not need to understand the folder structure before playing. RePoG is
designed so the agent handles the notebook while you focus on the character,
the world, and the choices.

The first question lets you choose Quick, Standard, or Deep setup. Optional:
standalone campaigns include a local player board under `campaign/dashboard/`.
After Session 0, run:

```bash
python -m http.server 8787 --directory campaign/dashboard
```

Then open `http://localhost:8787/` in Codex's in-app browser or a normal
browser. See `docs/dashboard.md`.

For OpenAI Codex, the agent should read:

1. `AGENTS.md`
2. `workflows/worldbuild/WORKFLOW.md`
3. `briefs/campaign_creation_interview.md`

After setup, play in natural language.

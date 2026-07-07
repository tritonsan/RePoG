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
4. Answer a few Session 0 questions with a compact original setting:
   - genre: frontier fantasy;
   - tone: grounded adventure;
   - play focus: travel, social pressure, strange ruins;
   - safety/canon: original world, no external canon.
5. Show Codex creating or filling a campaign folder.
6. Show a quick check command:

   ```bash
   python tools/check_state.py campaigns/<campaign_id>
   ```

7. Show the first opening scene.
8. Enter one player action in natural language.
9. Briefly show that campaign notes changed behind the scenes.

## What To Emphasize

- The player speaks naturally.
- Codex handles the campaign notebook.
- Important memory is in readable files.
- Checks exist, but the game does not feel like a state engine.
- RePoG is a workspace pattern, not a standalone app.

## Avoid

- Showing copyrighted worlds.
- Spending too long on folder internals.
- Making it look like users need to understand every template before playing.
- Presenting RePoG as Codex-only.

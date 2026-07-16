# Start Here

This ZIP is already a clean RePoG campaign workspace.

1. Extract it into a new folder.
2. Rename the folder if you want.
3. Open the extracted folder in Codex, Claude Code, or another agentic coding
   tool.
4. Start a new conversation.
5. Send:

```text
Start this RePoG campaign and guide me through Session 0.
```

The first question asks whether you want Quick, Standard, or Deep setup. After
your pitch, the agent presents 2–4 contextual Starter Bundle options. You can
accept one, mix parts, ask for changes, use the recommended default, or defer a
non-critical choice. The agent then maintains `campaign/` privately while you
answer and play.

Session 0 may combine fantasy, realistic, cyberpunk, and survival lenses, but a
lens never activates mechanics by itself. Dice, strict inventory, wounds,
clocks, structured travel, and other tracked rules are used only after you
approve them. During System Fit the agent also asks whether turns should use
Fast (recommended), Balanced, Maximum Continuity, or Custom maintenance and
shows expected wait ranges before you choose.

Do not open the ZIP archive itself; open the extracted folder. No installation,
repository clone, template copy, or campaign-creation command is required.

Optional dashboard after setup:

```bash
python tools/serve_dashboard.py campaign/dashboard
```

Then open `http://localhost:8787/`.

Optional dependency-free workspace check:

```bash
python tools/verify_workspace.py
```

Use `python tools/verify_workspace.py --json` when an agent needs structured
results. Visual generation is also optional: RePoG preserves the current
question or scene, waits for your approval before treating a draft as canon,
then returns to the preserved point.

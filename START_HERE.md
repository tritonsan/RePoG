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

The first question asks whether you want Quick, Standard, or Deep setup. The
agent then maintains `campaign/` privately while you answer and play.
During System Fit it also asks whether turns should use Fast (recommended),
Balanced, Maximum Continuity, or Custom maintenance and shows the expected
wait ranges before you choose.

Do not open the ZIP archive itself; open the extracted folder. No installation,
repository clone, template copy, or campaign-creation command is required.

Optional dashboard after setup:

```bash
python -m http.server 8787 --directory campaign/dashboard
```

Then open `http://localhost:8787/`.

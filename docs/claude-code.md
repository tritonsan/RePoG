# Claude Code

RePoG runs in Claude Code (the desktop app's Code tab, the CLI, or an IDE
extension) from the same workspace that other agentic tools use. `AGENTS.md`
remains the shared contract. `CLAUDE.md` imports it and adds the few rules that
are specific to Claude Code, and `.claude/` holds Claude Code configuration.
Other tools ignore both.

## Start

1. Extract the player ZIP into a new folder.
2. Open that folder in Claude Code. In the desktop app, start a new Code session
   on the folder; in a terminal, run `claude` inside it.
3. If Claude Code asks whether to trust the folder, accept. The bundled
   permission rules apply only to a trusted folder.
4. Send `Start RePoG and guide me through setup.`

Manual, Accept edits, and Auto permission modes all work. Plan mode cannot save
the campaign. Leave the desktop app's worktree option off for a campaign
session: `campaign/` is one live state, and a worktree copy would split it.
Run one session per campaign at a time.

## Bundled Configuration

| File | Purpose |
| --- | --- |
| `CLAUDE.md` | Imports `AGENTS.md`; adds Claude Code rules for presentation, memory, compaction, and delegation |
| `.claude/settings.json` | Selects the RePoG output style, turns off Claude Code auto memory, pre-approves `python tools/...` helpers and edits inside `campaign/`, and blocks `.env` reads and direct edits to the transaction journal |
| `.claude/output-styles/repog.md` | Replaces Claude Code's software-engineering response style with a Game Master and companion style; explicit maintenance requests still get plain technical answers |
| `.claude/agents/` | `repog-proposal-lane` (Read, Grep, Glob) and `repog-research-lane` (adds WebSearch and WebFetch) for eligible structural boundaries; see [Selective Structural Parallelism](semantic-parallelism.md) |
| `.claude/launch.json` | Desktop preview entries for the Dashboard and Companion View, with auto-verify off |

Web searches and page fetches still ask for permission, and so can a very long
helper command, such as a large Session 0 save; approve it to continue. The lane
turn limits are safety bounds; an incomplete lane is finished serially by the
coordinating agent.

## What Stays Visible

Claude Code shows tool activity in the transcript. RePoG keeps its replies in
the fiction and gives tool calls neutral labels, but the collapsed tool lines
remain. Keep the desktop transcript view on Normal: the Thinking and Verbose
views, expanded tool results, and the subagent pane can show GM-only material
and spoil secrets.

To undo a moment, ask out of character for a correction or retcon. Rewind and
checkpoint restore cover conversation and file-tool edits but not changes the
RePoG helpers saved, so they do not undo campaign state.

## Privacy

Auto memory is off in this workspace so that Claude Code keeps no second memory
of the player or companion user outside `campaign/`, where RePoG's consent and
forget rules apply. Claude Code still keeps its own session transcripts on your
computer until its `cleanupPeriodDays` retention period removes them. RePoG's
forget operation removes campaign content; it does not erase those transcripts.

## Images

Claude Code has no built-in image generator. Without a connected image tool,
RePoG reports generated visuals as unavailable and play continues. You can still
add artwork: place a PNG, JPEG, WebP, or GIF file in `campaign/visuals/_drafts/`
and ask for it to be used. It goes through the same draft review and acceptance
as a generated image.

## Dashboard And Companion View

In the desktop app, ask to open the dashboard or the Companion View. The preview
pane starts `repog-dashboard` (port 8787) or `repog-companion-view` (port 8790)
from `.claude/launch.json`. Where Python is installed only as `python3`, change
`runtimeExecutable` in that file. In the CLI, start the server yourself as shown
in the README.

## Plugin Edition

RePoG also ships as a Claude Code plugin, maintained in `claude-plugin/`. One
install serves every campaign, and each campaign folder holds only its own
`campaign/`. Besides the same helpers and workflows, the plugin runs the scene
capsule and the presentation lint from hooks, launches the boundary curator in
the background, and creates campaigns with `repog:new`. See
`claude-plugin/README.md` to install it.

## Maintaining The Source Repository

Personal overrides belong in `.claude/settings.local.json`, which stays out of
Git and out of the player package. For development work with Claude Code's
default engineering style and auto memory, use:

```json
{
  "outputStyle": "default",
  "autoMemoryEnabled": true
}
```

Run `/context` in the CLI to confirm that `CLAUDE.md` and the imported
`AGENTS.md` loaded, and `/status` to see which settings files are active.
`tools/verify_workspace.py` also checks this layer: the selected output style,
auto memory, the preview entries, and that the bundled lanes stay read-only.

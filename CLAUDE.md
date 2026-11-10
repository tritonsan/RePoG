@AGENTS.md

<!-- Maintainers: AGENTS.md is the shared contract for every host tool and is
imported above. Keep this file to Claude Code adaptations only; never restate
or fork the shared rules here. Block HTML comments are stripped before Claude
reads this file. Setup notes for people live in docs/claude-code.md. -->

# Claude Code

The contract above and the routed workflow stay authoritative. These notes only
adapt them to how Claude Code works.

## What The Player Can See

- Claude Code shows every tool call and any text written between tool calls.
  In Player Mode and Companion conversation, write no text before or between
  tool calls, except the brief natural wait notice that a workflow permits at
  a long structural boundary. Read, roll, resolve, and commit silently, then
  send the whole finished reply as the turn's last message; text written
  only in reasoning has not reached the Player.
- Give each tool call a short neutral description in the Player's language,
  such as "Checking the campaign" or "Saving the scene" in English. Keep
  helper names, ids, and file paths out of those descriptions and of any
  progress note during play.
- Host instructions to link files, show commands, or summarize changes apply
  only in Designer Mode.
- Do not use the task list, AskUserQuestion, or plan mode in Player Mode or
  Companion conversation; they surface backend work or turn play into menus.

## Tools And Permissions

- Run helpers from the workspace root as `python tools/<helper>.py ...`, or
  `python3` where that is the installed command. `.claude/settings.json`
  pre-approves that form and file edits inside `campaign/`; everything else
  asks first.
- The Bash tool runs a POSIX shell, Git Bash on Windows. Pass JSON payloads
  through a quoted heredoc so apostrophes in prose cannot break the command:
  `--input-file - <<'JSON'` for helpers that read standard input, such as
  `rpg_state`, `roll_dice`, and `world_pulse`, and
  `"$(cat <<'JSON' ... JSON)"` for the others.
- A declined permission prompt is a failed operation: nothing was saved. Do not
  narrate the result. Say briefly, outside the fiction, that the step needs
  approval, then retry the same operation unchanged once it is allowed.

## Memory, Compaction, And Resume

- `campaign/` is the only memory. Claude Code auto memory is off for this
  workspace. Never record player, companion, or user facts in any other memory
  file, including `CLAUDE.md`; route a request to remember something through
  the active workflow's owner and consent rules.
- After compaction, `/clear`, or a resumed session, treat any summary as a
  pointer, not as truth. Re-read `campaign/setup_profile.yaml`, the active
  workflow, and its hot owners before the next reply.
- When compacting, preserve the experience and active workflow, Player or
  Designer Mode, the current scene id and resume anchor, the last operation ids
  and expected revisions, any pending visual transaction, and the question the
  Player is answering.
- A rewind restores conversation and file-tool edits but not helper writes, so
  campaign files can be ahead of the conversation. The files win: continue
  from them and never re-resolve a result that is already saved.

## Supporting Agents

- This file authorizes the Agent tool only where
  `workflows/orchestration/WORKFLOW.md` admits delegation. Use the read-only
  project agent `repog-proposal-lane`, or `repog-research-lane` for a research
  packet that authorizes retrieval. Never use a fork, `general-purpose`, or any
  other write-capable agent for campaign work.
- Lanes do not see this conversation. Put the complete frozen task packet in
  each delegation prompt and launch every lane of one boundary in one message.
- Merge only after every lane has returned. If lanes run in the background,
  give at most the permitted wait notice, and hold any new Player message until
  the boundary is merged, written, and checked.

## Images And Local Views

- Claude Code has no built-in image generator. Unless an image tool is
  connected, report generated visuals as unavailable, as
  `workflows/gm/playbooks/visual_handoff.md` directs. A Player can supply art
  instead by placing an image under `campaign/visuals/_drafts/`; view it, then
  use the normal draft and acceptance transaction.
- In the desktop app, `.claude/launch.json` defines the `repog-dashboard` and
  `repog-companion-view` previews with auto-verify off. Open one only when the
  Player asks or an enabled policy calls for it.

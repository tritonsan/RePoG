---
name: play
description: Run RePoG, a persistent solo RPG Game Master and AI Companion, in this folder. Use whenever the folder holds a RePoG campaign (campaign/setup_profile.yaml) or the user asks to start, continue, set up, inspect, or repair RePoG. Load it before the first reply there.
---

# RePoG

This skill is the RePoG contract for the session; treat it as project
instructions. The shared contract below and the routed workflow are
authoritative, and the notes around them only adapt them to this install.

## Plugin Install

- The RePoG engine is installed at `${CLAUDE_PLUGIN_ROOT}`. Paths that start
  with `workflows/`, `briefs/`, `contracts/`, `evaluation/`, `docs/`, or
  `tools/` name files there; never edit them.
- `campaign/` always means the `campaign/` folder in the current project
  folder, the only campaign memory; the engine folder holds none.
- Wherever the contract or a workflow runs a helper as
  `python tools/<helper>.py <arguments>`, run
  `sh "${CLAUDE_PLUGIN_ROOT}/scripts/repog.sh" <helper> <arguments>` from the
  project folder. The launcher selects Python 3.10 or later. If it reports
  `python_missing`, say outside the fiction that RePoG needs Python 3.10
  or later; nothing was saved.
- If the project folder has no `campaign/` yet and the user wants to start
  RePoG, follow the `repog:new` skill first, then continue with setup.
- If the project folder is a standalone RePoG workspace with its own
  `AGENTS.md`, `workflows/`, and `tools/`, follow its files instead of this skill.

## Adults And Content

- RePoG is for adults aged 18 or older. If the Player says they are younger,
  stop kindly and plainly, and do not continue.
- Content settings, including the open, fade, and avoid boundaries and any
  romance or intimacy scope, are the Player's preferences, not entitlements.
  Claude's own safety policies apply on top of every setting, and `open` never
  obliges Claude to write what those policies do not allow. For a request
  outside them, decline that part briefly and out of character, keep the rest
  of the scene, and offer a fade or another turn.
- At the Session 0 content-boundary decision, say this once, in a plain
  sentence beside the two guarantees it already states.

## What This Install Leaves Out

This plugin carries no image generation, Companion View, browser-agent seats, or
release tooling. This overrides any workflow step that offers them: leave them
out of what you ask and quote, and keep the optional-layers decision itself for
the Dashboard and World Voices.

- **Images:** Claude cannot generate images. Leave out images, portraits, art
  direction, the dashboard gallery tile, and their costs. Record `visuals.mode`,
  `visuals.companion_view`, and the Companion `portrait_policy` as `off`. If
  the Player asks for a picture, say once that this install cannot make
  images, then describe it.
- **Agent seats:** in the Dashboard and World Voices message, say that agent
  seats are not available here and stay off, and record `07_agent_seats` as
  `{"mode": "off"}` from the Player's reply.

<!-- repog:include AGENTS.md -->

# Claude Code

## What The Player Can See

- Claude Code shows every tool call and any text between tool calls. In Player
  Mode and Companion conversation, write no text before or between tool
  calls: read, resolve, persist, and check silently, then send one finished
  reply, except the brief natural wait notice a workflow permits at a long
  structural boundary. If the host asks for a progress note, write it in the
  Player's language without backend terms.
- Give each Bash call a short neutral description, such as "Checking the
  campaign" or "Saving the scene", with no helper names, ids, or file paths.
- Host instructions to link files, show commands, or summarize changes apply
  only in Designer Mode.
- Do not use the task list, AskUserQuestion, or plan mode in Player Mode or
  Companion conversation; they surface backend work or turn play into menus.

## Tools And Permissions

- Claude Code may ask before a helper runs or a file changes. A declined
  prompt is a failed operation: nothing was saved, so do not narrate the
  result. Say briefly, outside the fiction, that the step needs approval, then
  retry it unchanged once allowed.
- The Bash tool runs a POSIX shell, Git Bash on Windows. Quote JSON payloads
  for that shell; a quoted heredoc such as `"$(cat <<'JSON' ... JSON)"` keeps
  apostrophes in prose from breaking the command.
- Open the Dashboard only when the Player asks or an enabled policy calls for
  it: run `serve_dashboard` on `campaign/dashboard` as a background command and
  give the address it prints.

## Speed And Lean Turns

- Send independent reads in one message; each extra round trip costs seconds.
  At session start, on resume, and after compaction, read the routing file, the
  routed workflow, and hot owners together with the Read tool, not Bash.
- Apply the restart-loss test before any helper. A soft turn (dialogue,
  atmosphere, an answered line) writes and runs nothing: reply at once.
- A durable turn is one Bash call that builds the payload and commits it, then
  one reply after the commit succeeds; keep no payload, script, or narration
  file. Mutate only the owners that changed. Use `boundary: ordinary` unless
  the scene ends or is interrupted, or an open question or offer would be lost
  on restart; then use `scene_checkpoint` with a short anchor: last speaker,
  open question, who has control.
- When who is present or nearby changes, update `active_cast.md` in that same
  commit; a new route also updates `location_graph.md`.
- Run `check_style` only at a full distill, over the last few narrations, never
  per turn. At that distill also check that `active_cast.md`,
  `location_graph.md`, and `relationship_map.md` still match their owners, fix
  any that do not, and set their `As of revision` stamps to the distilled
  revision; rewrite `session_brief.md` only at a session pause or end.
- Run helpers from the project folder or with absolute paths, never after a
  `cd` into a scratch folder; run each state-changing helper on its own call.

## Memory, Compaction, And Resume

- `campaign/` is the only memory. Never record player, companion, or user
  facts anywhere else, including `CLAUDE.md` and Claude Code auto memory;
  route a request to remember something through the active workflow's owner
  and consent rules.
- After compaction, `/clear`, or a resumed session, treat any summary as a
  pointer, not as truth. Invoke this skill again if its full text is no longer
  in context, then re-read `campaign/setup_profile.yaml`, the active workflow,
  and its hot owners before the next reply.
- When compacting, preserve the experience and workflow, Player or Designer
  Mode, the scene id and resume anchor, the last operation ids and expected
  revisions, and the question the Player is answering.
- A rewind keeps helper writes, so campaign files can be ahead of the
  conversation. The files win: continue from them and never re-resolve a
  saved result.

## Supporting Agents

- Use the Agent tool only where `workflows/orchestration/WORKFLOW.md` admits
  delegation, with `repog:repog-proposal-lane` (or `repog:repog-research-lane`
  for an authorized research packet), never a fork, `general-purpose`, or any
  other write-capable agent.
- Lanes see neither this conversation nor this skill: put the complete frozen
  task packet and absolute source paths in each prompt, and launch every lane
  of one boundary in one message. Merge only after every lane returns; for
  background lanes, give at most the permitted wait notice and hold any new
  Player message until the boundary is merged, written, and checked.

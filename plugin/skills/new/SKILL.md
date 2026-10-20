---
name: new
description: Create a new, blank RePoG campaign in the current folder. Use when the user asks to create, start, or set up a new RePoG campaign or companion here and the folder has no campaign/ folder yet.
---

# New RePoG Campaign

Create a campaign only in the current project folder, and only when the user
asked for a new RePoG campaign or companion here.

1. If `campaign/` already exists, create nothing. Tell the user that a
   campaign is already here, then continue it with the `repog:play` skill.
2. If the folder holds other files or folders, name the folder and ask the
   user to confirm before creating anything. One empty folder per campaign
   keeps campaigns apart.
3. Tell the user in two plain sentences that RePoG is for adults aged 18 or
   older, and that its content settings are preferences: Claude's own safety
   policies decide what it will write. If the user says they are younger,
   create nothing and stop.
4. Run `sh "${CLAUDE_PLUGIN_ROOT}/scripts/repog.sh" plugin_campaign init .`
   with a short description in the user's language, such as "Creating the
   campaign".
5. If the result reports `"ok": false`, tell the user plainly what failed,
   using its `failure_reason`, and stop.
6. Otherwise invoke the `repog:play` skill and begin Session 0 as if the user
   had sent `Start RePoG and guide me through setup.` Keep any campaign idea
   or choice the user already gave.

The helper copies the blank campaign template into `campaign/`. When they do
not exist yet, it also writes `.claude/settings.json`, which turns Claude Code
auto memory off and selects the RePoG output style for this folder, and a
short `CLAUDE.md` that points later sessions at RePoG. It never overwrites an
existing file. Both settings take effect when the next session starts here.

# RePoG

RePoG turns Claude into a persistent Game Master for a long-form solo
roleplaying campaign, or into one persistent adult fictional companion with a
life of their own. Claude interprets, portrays, and narrates; small local
helpers validate and save the campaign's state, so the world remembers what
happened across sessions.

## Requirements

- Claude Code (terminal, IDE extension, or the desktop app's Code tab).
- Python 3.10 or later on `PATH` as `python3`, `python`, or `py`. The helpers
  use only the Python standard library.

## Install

Add the marketplace that hosts this plugin, then install it:

```text
/plugin marketplace add <owner>/<repository>
/plugin install repog@repog
```

To try a local build for one session, start Claude Code with
`claude --plugin-dir <path-to-this-folder>`.

## Play

1. Create an empty folder for the campaign and open it in Claude Code.
2. Run `/repog:new`, or send `Start RePoG and guide me through setup.`
3. Choose an RPG Campaign or an AI Companion and follow Session 0.

Keep one campaign per folder and one session per campaign at a time. Keep the
transcript view on Normal during play: expanded tool output can reveal
material the Game Master keeps hidden.

## What The Plugin Runs And Writes

- **Skills:** `repog:play` holds the RePoG contract and routing; `repog:new`
  creates a campaign.
- **Local helpers:** Python scripts in `tools/`, run through
  `scripts/repog.sh`, validate and save state inside the project folder's
  `campaign/`. Claude Code asks before running them unless you allow them.
- **New campaign files:** `repog:new` copies the blank template to
  `campaign/` and, only when they are missing, writes `.claude/settings.json`
  (turns Claude Code auto memory off and selects the RePoG output style for
  that folder) and a short `CLAUDE.md`. Existing files are never overwritten.
- **SessionStart hook:** `scripts/session-start.sh` checks whether the folder
  holds a plugin campaign and, only then, adds a one-line reminder to load
  `repog:play`. It prints nothing in other folders.
- **Supporting agents:** two read-only proposal lanes for large structural
  steps. Only the research lane can search the web, and only for a research
  task you approved.
- **Optional local view:** the Dashboard server binds to `127.0.0.1` and starts
  only when you ask for it.
- **Left out:** Claude cannot generate images, so image generation is not part
  of this plugin. The Companion View, browser-agent seats, and the release and
  packaging tools are left out too.

## Speed

Turn time depends mostly on Claude's effort level. The `CLAUDE_CODE_EFFORT_LEVEL`
environment variable overrides the effort picker, `/effort`, and the
`effortLevel` setting, whether it is set in your shell, in Windows user
environment variables, or in the `env` block of `settings.json`. If it is set
to `max`, every turn thinks at maximum depth whatever the app shows. Remove it
and choose a low or medium effort for play. The skill also keeps turns lean:
dialogue turns save nothing, a saved turn is one helper call, and the style
check runs only at a full distill.

## Adults Only, Content, And Safety

RePoG is for adults aged 18 or older. Session 0 asks which content boundaries
apply, such as sexual content or graphic violence, as open, fade, or avoid. Those
choices are your preferences, not guarantees: Claude applies its own safety
policies to everything it writes, whatever a setting says, and may decline or
soften content that falls outside them. A setting never overrides those
policies, and you can tighten a boundary at any time.

## Privacy

The plugin collects nothing and sends nothing to any service of its own. Its
helpers make no network calls and it has no telemetry or accounts. Web
research happens only when you ask for it, through Claude's own web tools.
Campaign files stay in your project folder, and your conversation is processed
by Claude under your Anthropic account's terms. RePoG's forget operation
removes campaign content; it does not erase Claude Code's own session
transcripts on your computer.

## License

Apache License 2.0. See `LICENSE` and `THIRD_PARTY_NOTICES.md`.

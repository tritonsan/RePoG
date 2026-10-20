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
transcript view on Normal during play: expanded tool output and hook context
can reveal material the Game Master keeps hidden.

## What The Plugin Runs And Writes

- **Skills:** `repog:play` holds the RePoG contract and routing; `repog:new`
  creates a campaign.
- **Local helpers:** Python scripts in `tools/`, run through
  `scripts/repog.sh`, validate and save state inside the project folder's
  `campaign/`, including working files such as dice-roll receipts in
  `campaign/.repog-runtime/`. Claude Code asks before running them unless you
  allow them.
- **New campaign files:** `repog:new` copies the blank template to
  `campaign/` and, only when they are missing, writes `.claude/settings.json`
  (turns Claude Code auto memory off and selects the RePoG output style for
  that folder) and a short `CLAUDE.md`. Existing files are never overwritten.
- **Hooks:** four, each a shell script in `scripts/` whose Python step runs
  `tools/hook_entry.py` and is skipped without Python 3.10 or later; the
  Python command they find is cached in the plugin's data folder. They never
  stop your prompt or Claude's reply, the curation, capsule, and lint steps
  follow their runtime switches below, and nothing they read or write leaves
  your computer. The first three do nothing outside a folder that holds a
  plugin campaign.
  - `SessionStart`: adds a one-line reminder to load `repog:play` and marks
    the scene capsule for a full refresh in `campaign/.repog-runtime/`.
  - `UserPromptSubmit`: in a ready RPG campaign, first applies waiting curator
    edits whose target notes are unchanged (editing those notes, adding an
    entry to `campaign/session_log.md`, moving each processed proposal into
    the `applied/` or `rejected/` folder next to it, and recording the run's
    outcome in `campaign/.repog-runtime/curation/last_result.json`), then
    adds a hidden scene capsule to Claude's context, matching names in your
    prompt against campaign notes: the scene, the cast in it, secret holders by
    id, your standing directives, language guidance, open dice rolls, the last
    reply's presentation findings, and, once, a curator proposal the last run
    rejected or deferred. It keeps its capsule state in
    `campaign/.repog-runtime/`.
  - `Stop` (runs in the background): reads your last message and the reply
    from Claude Code's local transcript, runs the presentation lint over the
    reply, and writes its findings and a short history (rule counts, phrase
    fingerprints, and the first 300 characters of your message) to
    `campaign/.repog-runtime/`; messages starting with `OOC` are skipped. With
    the capsule on, it also records which campaign notes the reply named.
  - `PreToolUse`: runs on each Write tool call in any folder, but only reads
    the call and lets it through unless it comes from the curator agent, which
    may write nothing except its one staging file.
- **Supporting agents:** two read-only proposal lanes for large structural
  steps, and the boundary curator, which reads campaign notes after a full
  distill and writes one proposal file under `campaign/.repog-runtime/curation/`
  that the helpers apply only while those notes are unchanged. Only the
  research lane can search the web, and only for a research task you approved.
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

Since 0.2.0 a saved turn names what changed and where (a state key, a note
heading, a table row) instead of quoting the old text back, so the GM no longer
writes a script for each save. A full distill closes in one call, can move old
session-log history into `campaign/archive/`, and the full check warns when a
record grows too large or a character note stacks dated sections. For
measuring, `tools/session_report.py <transcript.jsonl>` prints turn times and
bookkeeping counts from a local Claude Code transcript, numbers only.

Since 0.3.0 the reply comes first by default and its save follows in the same
turn. A save that fails is fixed and retried in that turn; a narrated fact that
still cannot be saved is corrected in one out-of-character line.

## Runtime Switches

`campaign/play_profile.yaml` has a `runtime:` block with four switches; a
missing switch takes its default. Ask the Game Master out of character to
change one.

- `persistence_order`: `narrate_then_commit` (default) replies, then saves in
  the same turn; `commit_then_narrate` saves before replying.
- `presentation_lint`: `on` (default) or `off`, the Stop hook's check of each
  reply.
- `scene_capsule`: `on` (default) or `off`, the hidden capsule added to each
  prompt.
- `boundary_curator`: `background` (default), `inline`, or `off`: a background
  agent, the Game Master itself, or no one tidies the notes a full distill
  flags.

## Adults Only, Content, And Safety

RePoG is for adults aged 18 or older. Session 0 asks which content boundaries
apply, such as sexual content or graphic violence, as open, fade, or avoid. Those
choices are your preferences, not guarantees: Claude applies its own safety
policies to everything it writes, whatever a setting says, and may decline or
soften content that falls outside them. A setting never overrides those
policies, and you can tighten a boundary at any time.

## Privacy

The plugin collects nothing and sends nothing to any service of its own. Its
helpers and hooks make no network calls and it has no telemetry or accounts.
Web research happens only when you ask for it, through Claude's own web tools.
Campaign files stay in your project folder, and your conversation is processed
by Claude under your Anthropic account's terms. The hooks read campaign files
and Claude Code's local transcript and write only inside `campaign/`, apart
from the cached Python command in the plugin's data folder. RePoG's
forget operation removes campaign content; it does not erase Claude Code's own
session transcripts on your computer.

## License

Apache License 2.0. See `LICENSE` and `THIRD_PARTY_NOTICES.md`.

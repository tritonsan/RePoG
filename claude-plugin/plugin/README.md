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
    the scene capsule for a full refresh in `campaign/.repog-runtime/`. After
    a compaction or a resume it also prints up to 1,500 characters of the
    accepted style samples in `campaign/storytelling.md` and one line naming
    the campaign's locked persistence order.
  - `UserPromptSubmit`: in a ready RPG campaign, first applies waiting curator
    edits whose target notes are unchanged (editing those notes, adding an
    entry to `campaign/session_log.md`, moving each processed proposal into
    the `applied/` or `rejected/` folder next to it, and recording the run's
    outcome in `campaign/.repog-runtime/curation/last_result.json`), then
    adds a hidden scene capsule to Claude's context, matching names in your
    prompt against campaign notes: the scene, the cast in it and what each
    present character does not know, secret holders by id, your standing
    directives, language guidance, open dice rolls, the campaign's revision and
    state keys, the last reply's presentation findings and the habits that
    keep returning, notes due for tidying, a note when the last turn saved
    before replying or ended without text, and, once, a curator proposal the
    last run rejected or deferred. It keeps its capsule state in
    `campaign/.repog-runtime/`.
  - `Stop` (runs in the background): reads the current session's last turn,
    your message and the reply, locally from Claude Code's transcript, and
    runs the presentation lint over the reply; for a message that starts with
    `OOC` it checks only the reply's prose outside the out-of-character part.
    It stores counts and short snippets, never full text: its findings, a
    short history (rule counts, phrase fingerprints, and your message's
    language code), and the last turn's order (whether the reply came before
    the save, and whether the turn ended with text, in `order_last.json`) in
    `campaign/.repog-runtime/`. With the capsule on, it also records which
    campaign notes the reply named.
  - `PreToolUse`: runs on each Write tool call in any folder, but only reads
    the call and lets it through unless it comes from the curator agent, which
    may write nothing except its one staging file.
- **Supporting agents:** two read-only proposal lanes for large structural
  steps, and the boundary curator, which reads campaign notes after a full
  distill and writes one proposal file under `campaign/.repog-runtime/curation/`
  that the helpers apply only while those notes are unchanged. A full distill
  lists the notes due for it in `campaign/.repog-runtime/curation_due.json`
  until they are tidied. Only the research lane can search the web, and only
  for a research task you approved.
- **Optional local view:** the Dashboard server binds to `127.0.0.1` and starts
  only when you ask for it.
- **Left out:** Claude cannot generate images, so image generation is not part
  of this plugin. If you make pictures with your own image tool, the Game
  Master can write prompts for it: adults only, clothed and non-explicit, and
  checked against the campaign's records. Those images follow that tool's rules
  and your account there. The Companion View, browser-agent seats, and the
  release and packaging tools are left out too.

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

A saved turn saves first and then sends the whole reply as its last message;
a due full distill and its check run before that reply. A save that fails is
fixed and retried in that turn. Saves are kept small, because the Player waits
for them: each fact is written once, in its owner.

0.3.0 and 0.4.0 asked for the reply before the save. On this host that never
worked: the text stayed in the model's reasoning, and in 0.4.0 the Player saw
only a closing line, so 0.4.1 went back to one order.

A save can start from a skeleton the helper prints from the live files, and
records are written in the play language unless the campaign sets another
records language.

## Runtime Switches

`campaign/play_profile.yaml` has a `runtime:` block; a missing switch takes
its default. Ask the Game Master out of character to change one. Its
`persistence_order` line is kept for older profiles and changes nothing: every
turn saves first and replies last.

- `presentation_lint`: `on` (default) or `off`, the Stop hook's check of each
  reply.
- `scene_capsule`: `on` (default) or `off`, the hidden capsule added to each
  prompt.
- `boundary_curator`: `background` (default), `inline`, or `off`: a background
  agent, the Game Master itself, or no one tidies the notes a full distill
  flags.

## Adults Only, Content, And Safety

RePoG is for adults aged 18 or older. Session 0 asks which content boundaries
apply. Sexual content can be avoided, faded before it starts, or implied with
no explicit description; harm to children is at most mentioned or kept
offscreen, or avoided. Two rows are fixed and cannot be changed: no one under
18 appears in any sexual or romantic context, backstory included, and no
graphic violence against children appears on the page. Those choices are your
preferences, not guarantees: Claude applies its own safety policies to
everything it writes, whatever a setting says, and may decline or soften
content that falls outside them. A setting never overrides those policies, and
you can tighten a boundary at any time. When a request goes past a limit, the
Game Master says so once, plainly, and does not go further with each repeat.

The notice the Game Master gives before play, in English and Turkish:

> **Before you play.** RePoG is for adults 18+ only and runs on your own Claude
> account. Anthropic's Usage Policy applies to everything in the session,
> including your own requests and OOC notes, not only the GM's replies. The
> content settings in Session 0 are preferences. Choosing "open" does not
> unlock explicit sexual writing: intimate scenes are written by implication
> and cut away at the act itself. Sexual content involving anyone under 18 is
> never written, not even in a backstory. Dark themes (violence, death, crime)
> can be written, with restraint. If a reply is blocked, that alone is not a
> violation; rewind with `/rewind` or start a new session instead of pushing
> the same request. Repeatedly pushing for explicit sexual content can lead to
> warnings, temporarily stricter filters and, eventually, suspension of your
> account. No exact thresholds are published. Images you make with other tools
> such as Codex follow that provider's rules and your account there.

> **Oynamadan önce.** RePoG yalnızca 18 yaş üstü içindir ve senin kendi Claude
> hesabınla çalışır. Anthropic'in Kullanım Politikası oturumdaki her şeye
> uygulanır: yalnızca GM'in yazdıklarına değil, senin isteklerine ve OOC
> notlarına da. Session 0'daki içerik ayarları birer tercihtir. "Açık" seçmek,
> açık cinsel anlatımın serbest olduğu anlamına gelmez. Yakınlık sahneleri ima
> yoluyla yazılır ve eylemin kendisinde sahne kesilir. 18 yaşından küçük
> biriyle ilgili cinsel içerik, geçmiş hikâyede bile olsa, hiçbir koşulda
> yazılmaz. Karanlık temalar (şiddet, ölüm, suç) yazılabilir ama ölçülü
> anlatılır. Bir yanıt engellenirse bu tek başına ihlal sayılmaz. Aynı isteği
> zorlamak yerine `/rewind` ile geri al ya da yeni bir oturum aç. Açık cinsel
> içerik için tekrar tekrar ısrar etmek uyarıya, geçici olarak sıkılaştırılmış
> filtrelere ve sonunda hesabın askıya alınmasına yol açabilir. Kesin eşikler
> yayımlanmış değildir. Codex gibi başka araçlarla ürettiğin görseller o
> sağlayıcının kurallarına ve oradaki hesabına tabidir.

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

# RPG Persistence Contract

Load after resolution when a commit needs more than the capsule's `[formats]`
card: a checkpoint, an act, or a refused payload. An ordinary commit and a soft
turn need no load.

## Order

Every turn has one order. The Player sees any text written before or between
tool calls, so silent work and visible text never interleave:

1. silent reads and rolls;
2. one commit, when anything persists, and any distill that is due;
3. the whole reply, written as text: the turn's last message.

Your reasoning is invisible. A scene worked out there has not been told, and a
reply written before a tool call does not reliably reach the Player. So settle
the facts, commit them, then write the scene once, complete, as the reply:
never draft its prose first, and never shorten it to a closing line because a
commit came before it. A soft turn is the reads, rolls, and reply alone.

Wait for the command result, and never run the commit in the background. On
failure, fix the typed failure and retry in the same turn, keeping the same
operation id; do not narrate the fact as established, and never complete a
partial write manually. If `full_distill_required` is true or
`narration_allowed` is false, current truth is safe but the distill must finish
before the reply. The result's `reply` field restates the next step for the GM
and is never shown. An older profile may still say `narrate_then_commit` in
`runtime.persistence_order`; it means this same order.

## Classify And Commit

Persistence starts with semantic capture; boundary selection does not substitute
for it.

### 3A. Classify The Semantic Result

After Resolve, apply the restart-loss test: if the workspace restarted now,
would any newly established fictional, mechanical, positional, knowledge,
relationship, inventory, condition, creation, promise, clue, pressure, or
other authority fact needed later be lost? Choose `soft` only when the answer
is no. Otherwise choose `durable`. A resumability-only checkpoint may accompany
a soft result; it is a structural boundary, not durable fiction.

For `durable`, author one capture with:

- a stable `operation_id` and the loaded `expected_continuity_revision`;
- `cause` and the final `boundary`, and `resume_impact` only when the resume
  anchor would not already say it;
- one or more `changes`, each with a unique `id`, semantic `kind`, concise
  `established_delta`, non-empty immediate `owners`, and only genuinely
  secondary `cold_targets` with reasons;
- model-authored `mutations` for every owner, written as typed `ops` (3D),
  and any approved `mechanic_operations`;
- for a change a roll decided, `roll_reference` (the receipt's `roll_id`) and
  `outcome` (its band, exactly as rolled);
- `checkpoint` data when the same turn also needs a scene handoff.

Every owner must be mutated immediately. Never defer a changed fact's only
owner; cold targets are duplicate summaries, projections, preparation,
archives, or enrichment. Do not include helper-managed continuity fields or
the matching `session_log.md` receipt as model-authored mutations.

Every roll made since the last durable commit (a receipt at the expected
revision) must be cited by one change or listed in the payload's `void_rolls`
as `{"roll_id": "...", "reason": "..."}`, such as an attempt the Player
withdrew or a soft result that changed nothing durable; otherwise the writer
refuses the commit with `rolls_unaccounted`. A cited roll must be unused and
from this revision, and an `outcome` that differs from its band is refused. One
roll may back several changes of the same commit.
Under `player_rolls` or `hybrid`, a roll the Player made with their own dice
has no receipt: cite it as `"player: <what was rolled>"` with the band the
reported result reached as `outcome`.
While `dice_mode` is not `judgment_only`, a kind with a `contest`, `contested`,
`conflict`, `clash`, `duel`, or `roll` token needs `roll_reference`.

### Authority Map For Declared Kinds

Classify by what actually changed, not by which file feels convenient. A
disclosure is a knowledge change even when it also moves a relationship, so it
needs both owners. These kind tokens require their authority as an immediate
owner, and the durable writer rejects the commit when one is missing:

| Kind contains | Required immediate owner |
| --- | --- |
| `knowledge`, `disclosure`, `secrecy`, `epistemic` | `knowledge_boundaries.md` |
| `clue`, `secret` | `secrets_and_clues.md` |
| `relationship`, `bond` | `relationship_map.md` |
| `presence`, `whereabouts` | `active_cast.md` |
| `route`, `adjacency` | `location_graph.md` |
| `directive` | `directives.md` |

Other kinds stay free-form. Compose kinds when a turn changes more than one
authority, such as `knowledge_relationship` for a confession that also changes
standing. Never rename a kind to avoid an owner: if a character learned,
revealed, or concealed something, the knowledge ledger is the authority even
when a character note also stores stable epistemic habits.

Two recurring drift patterns to check before committing: a scene in a place
that has no note and no `location_graph.md` connection, and a repeated NPC whose
knowledge row was never updated after an earlier reveal. Both produce
contradictions several turns later.

### 3B. Finalize The Boundary

Choose independently:

- `ordinary` when neither a checkpoint nor full propagation is due;
- `scene_checkpoint` for a resumable scene end, interruption, or handoff that
  does not itself require full distill, and also when about five consecutive
  soft turns have left the scene frame unrefreshed—long soft runs write nothing,
  so nothing else detects the drift;
- `full_distill` at the configured durable threshold or another documented
  structural trigger. A durable result alone does not force this boundary.

An unresolved reply can need a checkpoint before five soft turns: if the next
answer would lose its question/choice referent after restart, preserve the last
speaker, referent, and control point in `scene_frame.resume_anchor`. Reference
the existing owner for an offer; never decide it for the Player. A completed
greeting or joke with no reply dependency still writes nothing. When the exchange
also establishes a promise, permission, disclosure, or relationship consequence,
it is durable and carries the anchor in that same commit. See
`workflows/reference/continuity-memory.md` for the bounded handoff contract.

### 3C. Commit Once

- `soft + ordinary`: no write, counter, dashboard refresh, or check.
- `soft + scene_checkpoint`: invoke
  `python tools/rpg_state.py campaign commit-checkpoint --input-file -` once,
  with the JSON on standard input, the checkpoint, and optional active-cast
  ops. The writer copies the scene id, mode, and anchor into `scene_frame`. It
  creates no continuity revision. It may also carry `directives.md` and
  `glossary.md` ops, so a turn whose only change is an OOC table rule commits
  here, with the unchanged scene frame as its checkpoint (OOC adjustment
  playbook).
- `durable + any boundary`: invoke
  `python tools/rpg_state.py campaign commit-durable --input-file -` exactly
  once the same way. When a checkpoint is needed, include it in this payload;
  never issue a second checkpoint command.
- any `full_distill` boundary: after the immediate durable commit, if one was
  needed, load the Distill workflow. If the boundary only propagates already
  committed events, do not invent another durable result or revision.

The durable writer is the single authority for staging immediate candidates,
checking owner/mutation structure, applying approved mechanic operations,
advancing the revision and durable counter once, appending the structured
receipt, and committing or rolling back the set. Do not manually patch a
subset, increment persistence fields, or append the corresponding event.

Do not delegate the semantic capture or authoritative commit. Selective
structural delegation, when eligible, begins only after the primary agent has
frozen the committed revision and pending cold-target set. Workers cannot
increment revision, append the event, clear pending targets, patch a
projection, or narrate the outcome. The Order section above places the commit
in the turn.

### 3D. Mutation Forms

The commit stands between the Player and the reply, so every word of it is
waiting time. State each fact once, in its owner, and restate nothing:

- `cause` is one sentence, and `established_delta` one short clause.
- While the scene holds, `scene_frame.resume_anchor` carries it: one line saying
  what stands and where control rests. A restart reads it first. Set another
  `current_state.yaml` key only when its value changed, such as the time, the
  place, `present_npcs`, or the inventory. `current_scene.summary`,
  `ongoing_process`, and `last_causal_beat` wait for a scene change or a
  checkpoint.
- A note's `## Now` takes one appended dated line, never a retyped section: the
  writer folds the oldest entries into `## History`. Use `replace_section` only
  when an entry stopped being true.
- A table row takes `set_cells` with the columns that changed. A note or a row
  that is still true needs no edit, even when the scene touched it.

Each mutation names one `path`. Prefer `ops`: the writer
finds the place, so old text is never copied back and deleting costs as little
as adding. `exact_replacements` (`old` must occur once) is for an edit no op
can address; `create_text` makes a new note under `characters/`, `places/`, or
`factions/`.

`current_state.yaml`:

- `{"op": "set", "values": {"key.path": "one line", ...}}` sets existing keys;
  never `continuity_revision` or `persistence`;
- `list_add`, `list_remove`, `list_set` take `key` and `items`, for example
  `current_scene.present_npcs`.

Markdown owners and notes (`heading` is the heading text, `#`s optional; add
`under` when two sections share a heading):

- `append` adds `text` at the end of a section, or of the file without a heading;
- `replace_section` swaps a section's body; `remove_section` deletes it;
- `insert_section` adds `heading` (with its `#`s) at the end of the file or of
  `under`, and refuses one that already exists: never add a dated section;
- `upsert_row` / `delete_row` find a table row by `key`, its first cell or
  first cells such as `["Mira", "->", "Ilse"]`; `cells` is the whole row;
- `set_cells` finds a row the same way and changes only the columns `cells`
  names: `{"op": "set_cells", "key": "Mira", "cells": {"Current activity": "at
  the pier"}}`. A `Revision` column is stamped for you;
- `replace` is one exact replacement inside the list.

`{{revision}}` becomes this commit's revision and `{{next_id:PC}}` the next
free `PC-` number in that file. The writer sets a mutated file's
`As of revision:` stamp and copies a checkpoint into `scene_frame`; do not
repeat them. On an `ordinary` boundary a scene-frame refresh still needs a
change that owns `current_state.yaml`, such as kind `scene_progress`.

```sh
python tools/rpg_state.py campaign commit-durable --input-file - <<'JSON'
{"operation_id": "dock-12-01", "expected_continuity_revision": 41,
 "boundary": "ordinary", "cause": "Mira pressed the witness.",
 "changes": [
  {"id": "scene", "kind": "scene_progress", "established_delta": "The talk turned to the courier.", "owners": ["current_state.yaml", "characters/witness.md"]},
  {"id": "name", "kind": "knowledge", "established_delta": "Mira knows the courier is Ilse.", "owners": ["knowledge_boundaries.md"]}],
 "mutations": [
  {"path": "current_state.yaml", "ops": [{"op": "set", "values": {
    "scene_frame.resume_anchor": "The witness named Ilse and waits for Mira's answer."}}]},
  {"path": "characters/witness.md", "ops": [{"op": "append", "heading": "Now", "text": "Day 12: named the courier to Mira."}]},
  {"path": "knowledge_boundaries.md", "ops": [{"op": "append", "heading": "Player And Character Knowledge",
    "text": "- Fact: the courier is Ilse.\n  - Fact id: {{next_id:PC}}\n  - Last confirmed: revision {{revision}}"}]}]}
JSON
```

The example feeds the payload through a POSIX shell's quoted heredoc
(`<<'JSON'`), which keeps apostrophes in prose intact. The writer reads the
same JSON three ways: from standard input with `--input-file -`, from a UTF-8
file with `--input-file PATH`, or inline with `--input-json`. In PowerShell 7
or later, pipe a single-quoted here-string (`@'` ... `'@`) into
`--input-file -`. Windows PowerShell 5.1 pipes text to programs as ASCII,
which turns letters outside English into `?`; there, write the JSON with the
host's file tool to a file under `tmp/` and pass its path to `--input-file`.

Write every record's content in the records language
(`play_profile.yaml.narration.records_language`, or the play language when it
is `same`): descriptions, `## Now` and History lines, Depth, Agency Card
values, summaries, facts, thread text, and names. Keep the structure exactly as
the templates write it: file names, YAML keys, headings, `- Label:` names,
table headers, enum values such as `alive`, `dead`, scene modes, and band
names, ids, and op names.

### 3E. Payload Helpers And Results

Build a payload from the live files, never from memory. `python
tools/rpg_state.py campaign template --kind durable` (or `checkpoint`,
`distill`, `act`) prints a skeleton: the current revision, an `operation_id`
placeholder, the valid `scene_mode` values, the `current_state.yaml` top-level
keys, the `active_cast.md` and `relationship_map.md` columns, and the owner
each change kind requires. It writes nothing.

Every result carries `next_expected_revision`; pass it as the next payload's
`expected_continuity_revision` instead of counting. `commit-distill` alone also
accepts `"current"`: `{"operation_id": "distill-14",
"expected_continuity_revision": "current", "trigger": "session end", ...}`.

Key paths take Unicode names, and a quoted segment when a name has spaces:
`{"op": "set", "values": {"player.stats.Algı": 4,
"player.stats.\"Sokak Zekâsı\"": 3}}`; a number stays a number.
`--input-file` reads UTF-8 with or without a BOM; other bytes are decoded as
cp1254, then latin-1, with an `input_decoded_<codec>` warning: check the saved
text when one appears.

A checkpoint at boundary `scene_checkpoint` carries `open_choices`, one to five
short strings that replace `current_state.yaml` `open_choices`; without them
the writer refuses with `checkpoint_open_choices_missing`. Elsewhere they are
optional. `"checkpoint": {"scene_id": "dock-12", "scene_mode": "aftermath",
"resume_anchor": "Ilse waits for an answer.", "active_cast_handoff": "none",
"open_choices": ["follow the courier", "report to the warden"]}`.

An act transition is one `commit-act` call, not a hand-built Compass edit. The
writer closes the current Compass (keeping a Closure Record an earlier commit
already wrote), archives it under `## Act Archive`, writes the successor's
Compass, and commits it all as one durable transaction at a
`scene_checkpoint` boundary. `close.act_id` is the current Compass's act id,
`close.outcome` says whether the closure condition was met or foreclosed, and
`close.summary` names the decisive action. `open` needs the new act's
`act_id` (never one used before), `title`, `dramatic_question`, `scope`
(`places`, `people`, `in_motion`, `if_ignored`), and `closure_conditions`;
`prepared_expectations` is optional. Optional `changes` and `mutations` carry
the act-close review in the same transaction, in the commit-durable forms.

```sh
python tools/rpg_state.py campaign commit-act --input-file - <<'JSON'
{"operation_id": "act-2-close", "expected_continuity_revision": 88,
 "close": {"act_id": "act-2", "outcome": "met", "summary": "Mira took the ledger from the council at revision 86."},
 "open": {"act_id": "act-3", "title": "The Ledger's Price",
  "dramatic_question": "Who pays for what the ledger proves?",
  "scope": {"places": ["the harbor district", "the river road"], "people": ["Ilse", "the council's creditors"],
   "in_motion": "The creditors are hiring.", "if_ignored": "The ledger's debts come due at the spring fair."},
  "closure_conditions": ["The ledger is sold, burned, or published."],
  "prepared_expectations": ["The creditors come to collect."]},
 "checkpoint": {"scene_id": "act-3-dawn", "scene_mode": "transition", "resume_anchor": "Dawn after the council fell.",
  "active_cast_handoff": "none", "open_choices": ["sell the ledger", "hide the ledger"]}}
JSON
```

Two refusals carry their own repair. A checkpoint handoff without an
`active_cast.md` mutation returns a ready `upsert_row` op built from the
handoff names and the table's columns: add it and retry. A `relationship` or
`bond` change without `relationship_map.md` asks for that file among the
owners: add it, and never rename the kind instead.

Warnings ask for follow-up, not a retry. Each is `{"rule", "path", "message"}`:

- `now_overflow_folded`: a note's `## Now` held more than 800 characters or
  more than three dated entries, so the writer moved the oldest dated entries
  into `## History`. Nothing to do.
- `death_projection`: a note's Core Status became `dead` or `missing` while
  rows naming it in `active_cast.md` or `relationship_map.md` stayed unchanged.
  Fix the listed rows in the next commit. Rows still stale at the next
  `commit-distill` come back as `cast_dead_listed` or
  `relationship_dead_active`, and it is refused with `distill_unreconciled`
  until its mutations fix them or `deferred_reconcile` lists `active_cast.md`
  or `relationship_map.md`.
- `inventory_count_duplicate`: a `current_state.yaml` inventory line carries a
  count `mechanics_state.json` already tracks; name the item only.
- `cost_unrecorded`: a change cites a roll whose band names a cost, a partial
  result, a loss, or a failure (such as `success_with_cost`, `partial_or_loss`,
  or `failure`), yet the payload changed no `player.conditions` or
  `pending_consequences`, no mechanic, and no character note. Record the cost
  in the next commit.
- `glossary_suggest`: a new note's title holds a word outside the play
  language, or the note is in another language; the suggested `glossary.md`
  row `{Term, Preferred, Variants, Notes}` leaves `Preferred` empty. Fill it
  with the play-language form and commit the row when the name recurs.
- `record_language`: text in `create_text`, `replace_section`, or `append` was
  detected in a language other than the records language; rewrite it there in
  the next commit that touches the path.

Durable receipts omit lines whose value is `none` or empty. A
`session_log.md` over 150,000 characters rotates at the next `commit-distill`
on its own; `rotate_log: false` keeps it in place.

A result may list other `warnings`: an owner near the size cap, stacked note
sections, or a long session log. Handle them at the next distill, not mid-scene.
A new note's warnings are the exception: act on `name_common_word` or
`name_near_duplicate` before the name settles in play, and fill the fields a
new character note's `note_incomplete` warnings name in the next commit that
touches it (`workflows/reference/creation.md`).

For interrupted writes, shared locking, and legacy lock recovery, load
`docs/file-transactions.md` in Designer Mode. Never delete a transaction journal
to bypass a recovery refusal.

Fast and Balanced add no separate per-turn `check_state --scope hot` call. The
writer's bounded structural validation is the per-commit gate; the full check
runs at full distill, which Maximum Continuity reaches on every durable result.
Dashboard, visual, and style work runs only when its own policy is triggered.
Style review is warning-only and never rewrites narration. Semantic GM quality
is model judgment applied through this spine and the relevant playbook, not a
Python gate or a second per-turn model call.

When a scene reaches a source question the dossier never settled, follow the
campaign's in-play research policy: `off` means ask the Designer or take a
conservative assumption and leave it open, `ask_first` means offer a lookup when
the answer would change durable truth, and `bounded_auto` means look it up
narrowly when the question blocks durable truth. Search for that one question
only, never for flavor, and append the result as a research pass with references.
Unresolved stays open instead of becoming invented canon. Keep it invisible in
Player Mode beyond a brief natural wait.

World Voices remains dormant on ordinary turns. When triggered, persist only
active/pending communication references in hot context and load artifact bodies
or old threads on demand. A hidden artifact never causes a Dashboard refresh.

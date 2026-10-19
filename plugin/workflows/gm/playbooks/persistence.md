# RPG Persistence Contract

Load after resolution when a durable result, checkpoint, or full-distill trigger
requires work. Soft ordinary turns need no additional load.

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
- `cause`, `resume_impact`, and the final `boundary`;
- one or more `changes`, each with a unique `id`, semantic `kind`, concise
  `established_delta`, non-empty immediate `owners`, and only genuinely
  secondary `cold_targets` with reasons;
- model-authored `mutations` for every owner, written as typed `ops` (3D),
  and any approved `mechanic_operations`;
- `checkpoint` data when the same turn also needs a scene handoff.

Every owner must be mutated immediately. Never defer a changed fact's only
owner; cold targets are duplicate summaries, projections, preparation,
archives, or enrichment. Do not include helper-managed continuity fields or
the matching `session_log.md` receipt as model-authored mutations.

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
  with the JSON in a quoted heredoc, the checkpoint, and optional active-cast
  ops. The writer copies the scene id, mode, and anchor into `scene_frame`. It
  creates no continuity revision.
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
projection, or narrate the outcome.

Wait for the command result. On failure, do not narrate the fact as established
or complete a partial write manually. Keep the same operation id for a valid
retry after the typed failure is addressed. On success, if
`full_distill_required` is true or `narration_allowed` is false, current truth
is safe but Distill must finish before narration.

### 3D. Mutation Forms

Each mutation names one `path` and exactly one form. Prefer `ops`: the writer
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
  `under`, and refuses one that already exists: replace a note's current state
  in place, never add a dated layer;
- `upsert_row` / `delete_row` find a table row by `key`, its first cell or
  first cells such as `["Mira", "->", "Ilse"]`; `cells` is the whole row;
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
 "resume_impact": "A restart must keep the courier's name.",
 "changes": [
  {"id": "scene", "kind": "scene_progress", "established_delta": "The talk turned to the courier.", "owners": ["current_state.yaml"]},
  {"id": "name", "kind": "knowledge", "established_delta": "Mira knows the courier is Ilse.", "owners": ["knowledge_boundaries.md"]}],
 "mutations": [
  {"path": "current_state.yaml", "ops": [{"op": "set", "values": {
    "scene_frame.last_causal_beat.changed_fact": "The courier is Ilse.",
    "scene_frame.last_causal_beat.returned_control_at": "The witness waits."}}]},
  {"path": "knowledge_boundaries.md", "ops": [{"op": "append", "heading": "Player Knowledge",
    "text": "- Fact: the courier is Ilse.\n  - Fact id: {{next_id:PC}}\n  - Last confirmed: revision {{revision}}"}]}]}
JSON
```

A result may list `warnings`: an owner near the size cap, stacked note
sections, or a long session log. Handle them at the next distill, not mid-scene.

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

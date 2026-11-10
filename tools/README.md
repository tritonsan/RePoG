# Lite Tools

These small deterministic helpers guard campaign continuity. They do not create
narration or act as a second game engine.

## Agent Seat

The optional Agent Seat store keeps a browser-agent participant outside
campaign truth. Opening a beat supplies an already-curated, character-safe
projection; submitting a turn creates only a pending proposal. The GM resolves
that proposal with the human turn before using the ordinary RPG writer.

```bash
python tools/agent_seat.py campaign/agent_seat_state.json status
python tools/agent_seat.py campaign/agent_seat_state.json context
python tools/agent_seat.py campaign/agent_seat_state.json next-turn
python tools/agent_seat.py campaign/agent_seat_state.json open-beat --input-file open_beat.json
python tools/agent_seat.py campaign/agent_seat_state.json turn-status --operation-id mira-turn-001
python tools/agent_seat.py campaign/agent_seat_state.json resolve-turn --input-file resolution.json
python tools/compile_agent_brief.py validate-roster campaign
python tools/compile_agent_brief.py compile-pack --input-json '{...}'
python tools/compile_agent_brief.py validate-pack --input-json '{...}'
```

Resolved beats can advance to the next beat without resetting the state.
`pause-session`, `resume-session`, and `complete-session` preserve a durable
session revision; `migrate` atomically upgrades legacy Agent Seat state.

`tools/serve_dashboard.py` exposes the safe context and pending-turn routes to
same-origin WebMCP tools. It never exposes the private campaign directory and
does not expose configuration or resolution writes over HTTP.

## Campaign Checks

```bash
python tools/check_state.py campaign --scope hot
python tools/check_state.py campaign --scope full
python tools/check_dashboard.py campaign/dashboard/dashboard_state.json
```

`hot` is a bounded diagnostic for an explicit check; play adds no per-turn
check because the writer validates every durable commit. `full` is the
default when `--scope` is omitted and is required at full distill,
session stop, closure, advancement, migration, and audit boundaries. A scene
checkpoint alone persists its small handoff contract and does not force a full
distill.

`check_content.py` holds the full check's content rules, kept apart so
`check_state.py` stays under its size budget. Each compares records that
should agree, and each is a warning:

- `cast_dead_listed`: a note's Core status is dead or missing, but
  `active_cast.md` still lists the name as present;
- `cast_present_missing`: `current_scene.present_npcs` names someone with no
  active-cast row;
- `relationship_dead_active`: a relationship row names a dead character and its
  state does not say dead, ended, or past;
- `location_unmapped`: the scene location is not a node of `location_graph.md`;
- `now_overflow`: a `## Now` over 800 characters or three dated entries,
  counted as the writer counts it;
- `knowledge_holder_conflict`: `knowledge_boundaries.md` lists a holder as
  explicitly unknown or must-not-imply for a fact that a holder account, or a
  dated line in that file or in the holder's own note, mentions with them;
- `minor_romance_history`: a romance or sex term whose closest age in the
  window (same phrase, then clause, then distance) is under 18, in a character
  note or `player.md`. Durations and age spans ("from fifteen to twenty-two")
  are read from their first age only as spans; a kiss counts unless a relative
  or a forehead or cheek kiss shares the clause; HTML comments and template
  guidance lines are skipped. It uses `lang_pack.minor_romance`, the same
  helper as the lint, with each pack read on its own;
- `records_language_mismatch`: one finding listing the top-level Markdown
  records (not the log, glossary, or directives) and the `characters/`,
  `places/`, and `factions/` notes whose content reads as another language
  than the records language (`narration.records_language`, or
  `narration.language` when it is `same`); headings, labels, table headers,
  names, one-word table cells, and template text are left out; under `auto`
  the records language is the one the lint last saw in the replies
  (`lang_pack.campaign_records_language`, shared with the writer);
- under numeric grounding, `power_band_mismatch` (a numeric Power Band below
  the note's highest stat) and `tier_cap_exceeded` (a stat above the
  `rules.md` `## Tier Caps` line `- T1: n` for its tier). A `rules.md` line
  `- Numeric scale: min-max` widens the stat range, and a numeric Power Band
  that covers the stats justifies them.

The old revision-lag rules (`active_cast_stale`, `location_graph_stale`,
`relationship_map_stale`, `session_brief_stale`) are info, and only after a lag
over 25 revisions: content rules decide whether an owner is stale.

A `directives.md` row with Scope `check` and Directive `acknowledge <rule_id>`,
optionally followed by `for <path or name>`, turns matching full-check warnings
into info, adds ` (acknowledged by D-00N)` to the message, and sets
`acknowledged_by`. It applies only in a full check; errors and
`minor_romance_history` are never acknowledged. A finding that lists several
files needs a row without a target, or targeted rows that together cover every
listed file. A healthy campaign carries no unacknowledged warning.

## Deep Session 0 v8 State

Schema-v8 RPG Deep keeps its canonical interview ledger separate from the
human-readable `session_zero.md` projection:

```bash
python tools/session_zero_state.py campaign status
python tools/session_zero_state.py campaign record-decision --operation-id s0-001 --expected-revision 0 --decision-id 01_campaign_frame_and_reach --stage-id 01_north_star_authority --status locked --source player --value-json '{"campaign_promise":"A grounded frontier mystery","reach":"contained"}'
python tools/session_zero_state.py campaign complete-stage --operation-id s0-stage-01 --expected-revision 6 --stage-id 01_north_star_authority --output-refs-json '["campaign_one_pager.md","world.md","boundaries.md","creation_ledger.md"]' --output-digest sha256:replace_with_current_digest
python tools/session_zero_state.py campaign record-gate --operation-id s0-gate-research --expected-revision 12 --gate-id research_scope_locked --input-digest sha256:replace_with_input_digest --output-digest sha256:replace_with_output_digest --decided-by coordinator
python tools/session_zero_state.py campaign render-summary
```

The mutation lines are schematic: use `status` to read the current revision and
replace each digest placeholder with the digest of the exact materialized input
or output set. Stage completion evidence is owner-bounded. For example, Stage 1
must cover its non-deferred campaign-promise, world, boundary, and
creation-ledger owners shown above; the helper rejects missing or unrelated
references. The world-independent character core is materialized in Stage 3,
and `player.md` remains a Stage 5 output rather than an early authority artifact.

```bash
python tools/session_zero_state.py campaign set-depth --depth deep --language tr
python tools/session_zero_state.py campaign set-language --language tr
python tools/session_zero_state.py campaign stage-owners --stage-id 01_north_star_authority
python tools/session_zero_state.py campaign digest --refs-json '["campaign_one_pager.md","world.md","boundaries.md","creation_ledger.md"]' --stage-id 01_north_star_authority
python tools/session_zero_state.py campaign finalize --operation-id s0-final-001 --expected-revision REPLACE_WITH_CURRENT_REVISION
```

`set-depth` (`quick`, `standard`, or `deep`, optionally with `--language`)
records the Player's depth for an RPG setup instead of a hand edit of
`session_zero.md`; `deep` also initializes or repairs the ledger and the
managed summary. It refuses an unset or Companion experience, a ready setup,
too old a schema, and a depth change once decisions exist (`depth_locked`).
`set-language` writes `play_profile.yaml` `narration.language` (never `auto`)
and refuses a locked profile; Session 0 settles it before Stage 1 content, and
a new Stage 1 decision is refused while it is unset or `auto`. `status`
reports `play_language`. `stage-owners` lists a stage's evidence owners, its
extensions and their owners, each decision's owners, required value fields,
`depends_on`, trigger tags, and required gate, and the gate that follows.
`digest` prints the output digest of campaign-relative files and, with
`--stage-id`, checks them against that stage's owners. `record-decision`
reports every contract problem at once in `problems`; `complete-stage` checks
its gates before writing anything and reports its problems the same way.

`finalize` runs the readiness sequence in one call: preflight,
`draft_preflight_passed`, profile locks, snapshot, ready evidence, and
`ready_and_snapshotted`. It stops at the first failing step with a typed error
plus `failed_step` and `completed_steps`, and a rerun resumes without repeating
a passed preflight gate. `--stop-after <step>` (`preflight`,
`draft_preflight_passed`, `lock_profiles`, `snapshot`, `ready_evidence`, or
`ready_and_snapshotted`) pauses after a step, for example to build approved
projections. Readiness is also blocked by calibration warnings
(`power_band_mismatch` and the early-stage power rules) and by
`minor_romance_history` at any severity. A `records_language_mismatch` does
not block; the result lists it under `advisories`.

The steps `finalize` runs remain available one by one. After
`draft_preflight_passed`, use its resulting revision for the locked profiles
and both commands below. First create the snapshot with
`python tools/snapshot.py campaign --label session-zero-start`. Append
`snapshot_manifest.json` to its returned `snapshot_path`, convert that file to a
campaign-relative ref, and pass it to the evidence helper:

```bash
python tools/session_zero_state.py campaign prepare-ready-evidence --operation-id s0-ready-evidence-001 --expected-revision REPLACE_WITH_CURRENT_REVISION --snapshot-ref snapshots/REPLACE_session-zero-start/snapshot_manifest.json --aggregate-check-ref snapshots/deep-v8-readiness.json
python tools/session_zero_state.py campaign record-gate --operation-id s0-ready-001 --expected-revision REPLACE_WITH_CURRENT_REVISION --gate-id ready_and_snapshotted --input-digest REPLACE_WITH_DRAFT_PREFLIGHT_OUTPUT_DIGEST --output-digest REPLACE_WITH_EVIDENCE_SNAPSHOT_DIGEST --decided-by coordinator --evidence-json 'REPLACE_WITH_EXACT_EVIDENCE_OBJECT'
```

These readiness lines are schematic only in their `REPLACE_...` values; the
command names and arguments are exact. `prepare-ready-evidence` runs
`check_state.py --scope full --preflight-ready`, writes and validates the
manifest-authorized aggregate report, and returns the complete `evidence`
object. Pass that object unchanged to the final gate. The profiles are already
locked, but `setup_profile.yaml` remains `in_progress` and not ready while the
evidence is produced. `ready_and_snapshotted` is revision-neutral and is the
only operation that atomically projects `complete` / `ready_for_play: true`.

Every mutation requires a stable operation id and the current expected setup
revision. The helper atomically advances the ledger and the three progress
mirrors in `setup_profile.yaml`; retries are idempotent and stale revisions are
rejected. It does not interpret answers, invent world truth, or activate an
extension from free text. The coordinator supplies only trigger tags listed in
the Deep manifest and materializes semantic owner files before closing a stage.

## RPG Durable Transactions

```bash
python tools/rpg_state.py campaign commit-durable --input-file - <<'JSON'
{...}
JSON
python tools/rpg_state.py campaign commit-checkpoint --input-file - <<'JSON'
{...}
JSON
python tools/rpg_state.py campaign commit-distill --input-file - <<'JSON'
{...}
JSON
python tools/rpg_state.py campaign commit-act --input-file - <<'JSON'
{...}
JSON
python tools/rpg_state.py campaign commit-curation --apply-staged
python tools/rpg_state.py campaign template --kind durable
```

`--input-json "{...}"` still works; `--input-file` reads a UTF-8 file (with or
without a BOM), or standard input for `-`, so prose apostrophes never need
shell escaping. Input that is not UTF-8 is decoded as cp1254, then latin-1,
with the warning `input_decoded_cp1254` or `input_decoded_latin1`.
The plugin edition's `scripts/repog.sh` exports `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` before
it starts Python.

`rpg_state.py` is a semantic-free writer, not a narrative checker. The GM
supplies the established durable changes, their immediate owner paths,
model-authored mutations, and any deferred secondary targets. A mutation is
written as typed `ops` from `owner_ops.py` (set a YAML key, edit a list,
append to, replace, remove, or insert a Markdown section, upsert or delete a
table row, or `set_cells` on the named columns of a row, which also stamps a
`Revision` column), as `exact_replacements`, or as `create_text` for a new
entity note. `resume_impact` is optional, and one roll may back several changes
of a commit.
`{{revision}}` and `{{next_id:PREFIX}}` placeholders resolve in new text. Key
paths accept Unicode identifiers (`player.stats.Algı`) and quoted segments
(`player.stats."Sokak Zekâsı"`), and a key keeps the form the file wrote it
in. The writer stamps a mutated owner's `As of revision:` line, copies a
checkpoint into `scene_frame`, and returns advisory `warnings` for owners near
the size cap, stacked dated sections in entity notes, and a long session log.

`commit-distill` closes a full distill without a continuity revision: it
applies secondary edits (never `current_state.yaml`, `session_log.md`,
mechanics, or profiles), appends the summary and distilled-through marker,
resets the persistence counters, can rotate log history before the previous
marker into `archive/`, and returns the full check. One
`commit-durable` call stages all candidates before writing, appends one
structured revision event, advances continuity and the durable counter once,
and either commits every target or restores their byte-exact prior contents.
Operation ids and payload hashes make the latest retry idempotent. An
interrupted write leaves a local `.repog-transactions/` recovery journal; a
subsequent RPG transaction restores an unfinished commit before accepting new
work, while ambiguous recovery blocks further mutation.

`commit-checkpoint` is only for a resumability-only handoff with no new durable
fiction; it updates the scene frame and optional active-cast handoff without a
continuity revision. It may also edit `directives.md` and `glossary.md`, so an
OOC-only table rule needs no fictional revision. A successful durable response
with `full_distill_required: true` has safely stored current truth but sets
`narration_allowed: false` until the routed full distill completes. Neither
command decides whether a turn was soft, what happened in the fiction, which
facts matter, or what the Player should be told.

Every success result (durable, checkpoint, distill, curation, act, and an
idempotent retry) carries `next_expected_revision`, the
`expected_continuity_revision` the next payload needs; a `stale_revision`
failure carries it too. Durable, checkpoint, distill, and act results add
`reply`, a short English note on the next step: send the whole reply as text
now, or first finish the distill when `narration_allowed` is false. The GM
reads it and never shows it. `template --kind durable|checkpoint|distill|act` is
read-only: it prints `{payload, reference}`, a payload skeleton plus the
current revision, scene modes, boundaries, the `current_state.yaml` top-level
keys, the `active_cast.md` and `relationship_map.md` columns, and the owner
each change kind requires (the distill skeleton uses the revision
`"current"`).

A checkpoint at boundary `scene_checkpoint` (in `commit-durable` and
`commit-act`) must carry `open_choices`, one to five one-line strings of at
most 200 characters that replace `current_state.yaml` `open_choices`;
otherwise the commit is refused with `checkpoint_open_choices_missing`. They
are optional on `commit-checkpoint`. A handoff that names presence changes
without an `active_cast.md` mutation is refused with a ready `upsert_row` op
in `suggested_mutation`, prefilled from the current rows, the handoff names,
and the table's columns. A relationship change without its owner is refused
with the advice to add `relationship_map.md` with its mutation.

Durable and checkpoint commits may also return these advisory warnings:

- `now_overflow_folded` (with `count`): after mutations to a `characters/`,
  `places/`, or `factions/` note, a `## Now` over 800 characters or three dated
  entries (a line starting `Day 12`, `Gün 12`, `Tag 12`, `Día 12`, or
  `Jour 12`, or holding `(day N)`) had its oldest dated entries moved to
  `## History`, which is created right after `## Now` when missing. Undated
  lines stay; `now_overflow` means undated text alone is over budget.
- `death_projection` (with `rows`): a mutation set a note's Core status to dead
  or missing while unchanged `active_cast.md` or `relationship_map.md` rows
  still name it.
- `inventory_count_duplicate`: a new `current_state.yaml` inventory line holds
  a number for an item or resource that `mechanics_state.json` tracks; name
  the item only.
- `cost_unrecorded`: a change cites a roll whose band names a cost, partial
  result, loss, or failure, and the commit changes no condition or pending
  consequence, no mechanic, and no character note.
- `glossary_suggest` (with `row`): a new note whose title uses words of another
  pack language, or whose body is written in one, gets a suggested
  `glossary.md` row `{Term, Preferred, Variants, Notes}`.
- `record_language`: `create_text`, `replace_section`, or `append` text
  (headings, `Label:` prefixes, table headers, comments, and fences left out)
  reads as another language than the records language
  (`narration.records_language`, or `narration.language` when it is `same` or
  missing).

Durable receipts in `session_log.md` leave out lines whose value is `none` or
empty, such as `Deferred propagation`; older logs that kept them still parse
and retry idempotently. The `session_log_size` warning (above 400,000
characters) says the next distill rotates the log.

`commit-distill` also accepts `expected_continuity_revision: "current"` and
`deferred_reconcile: [{"path", "reason"}]`. Before applying anything it runs
the full check and gates on `cast_dead_listed`, `cast_present_missing`,
`relationship_dead_active`, `location_unmapped`, `stacked_sections`,
`now_overflow`, and `minor_romance_history`: a gated finding on a file the
payload neither mutates nor defers refuses the distill with
`failure_category: "distill_unreconciled"` and an `unreconciled` list of
`{path, rule, message}`. A deferred path must be an existing Markdown note the
curator may edit; `minor_romance_history` cannot be deferred. Findings on files
no distill can edit (non-Markdown files, `current_state.yaml`, profiles, the
log, `archive/`) and acknowledged findings do not gate, and when the check
itself fails the gate is skipped with the warning `distill_gate_unavailable`.
A `session_log.md` over 150,000 characters rotates as if `rotate_log` were
true, unless the payload sets `rotate_log: false`; an archive name that is
taken gets a `-2`, `-3`, ... suffix. The result adds `curation_due` (Boundary
Curation below; `curation_due_unwritten` warns when the file could not be
written), `lint_report` (`presentation_lint.report_summary` over the last 20
replies, or null), `next_expected_revision`, and `reply`.

`commit-act` is the typed act transition. Its payload is `{operation_id,
expected_continuity_revision, close: {act_id, outcome, summary}, open: {act_id,
title, dramatic_question, scope: {places, people, in_motion, if_ignored},
closure_conditions, prepared_expectations?}, checkpoint: {..., open_choices},
changes?, mutations?}`. It builds the `threads.md` close, the Act Archive entry,
and the successor Arc Compass (`Opened at revision` set to the new revision),
checks them with the act rules the full check uses, and commits them with the
other changes and mutations as one durable revision at a `scene_checkpoint`
boundary. `close.act_id` must equal the Compass act id (a legacy Compass
without one adopts an id first); a `threads.md` mutation in the same payload,
or an `open.act_id` already archived, is refused. A Compass already closed by
its decisive turn keeps its Closure Record.

A change decided by a roll call carries `roll_reference` (the receipt's
`roll_id`) and `outcome` (its band). The writer refuses a cited roll that has no
receipt, was rolled at another revision, was already used, or names a different
band, and refuses the whole commit with `rolls_unaccounted` while a receipt at
the expected revision is neither cited nor listed in the payload's `void_rolls`
(`[{"roll_id": ..., "reason": ...}]`, at most 16). Cited and voided receipts
are marked consumed after the commit. Until a campaign has a receipt store, a
free-text `roll_reference` without `outcome` passes with a `roll_unrecorded`
warning. A checkpoint may use scene mode `downtime`; a kind containing
`directive` requires `directives.md`, and `glossary.md` is an owner as well
(either starts from the shipped template when missing).

`create_text` for a new entity note adds advisory warnings that never block the
commit. `name_common_word` and `name_near_duplicate` (from `name_check.py`)
compare the new title, in the play language, with the other note titles, the
`creation_ledger.md` entries, and the names in `active_cast.md` and
`relationship_map.md`. A new character note also gets a `note_incomplete`
warning for each gap the full check's character-note rules find, such as a
missing Power Band or missing T2/T3 Agency Card fields; a missing `## Core`
block shows up only in the full check, as `note_core_missing`.

`commit-curation` applies staged curator proposals (see Boundary Curation).
Each staged file is one transaction, applied whole only while every target
still has the hash the curator read; otherwise it moves to `rejected/` with its
reasons. An applied file moves to `applied/` and appends `### Curation Applied
At Revision N` to `session_log.md`. Curation creates no revision and leaves the
persistence counters alone. `--apply-staged` processes every waiting file older
than a few seconds; `--staged PATH` (repeatable) names files instead.

For AI Companion workspaces, the shared state checker routes automatically and
does not apply RPG player/opening/arc readiness rules. The focused commands
are:

```bash
python tools/check_companion.py campaign --scope hot
python tools/check_companion.py campaign --scope full
python tools/companion_state.py campaign begin-exchange --operation-id exchange-0001 --expected-state-revision 0 --expected-continuity-revision 0
python tools/companion_state.py campaign validate
python tools/companion_state.py campaign commit-semantic --operation-id semantic-0001 --semantic-sequence 1 --expected-state-revision 1 --expected-continuity-revision 0 --gap-id gap_from_begin_exchange --state-patch-json "{\"current_presence\":{\"place_ref\":\"home\",\"activity\":\"making dinner\",\"availability\":\"limited\"}}"
```

`begin-exchange` is the ordinary-message fast path: one atomic call measures
the previous timezone-aware gap, advances contact state, and returns the stable
gap id, due signals, current condition, bounded attention queue, relational
context, and conservative event ceiling. It never invents a life event and it
does not increment fictional continuity. Run `commit-semantic` only when the
exchange changes durable life, disclosure, relationship, user memory, or the
already-shared public surface. It requires the next monotonic semantic sequence
and both expected revisions, and increments continuity once. Pass the stable
`gap_id` from `begin-exchange` when reconciling elapsed time; stale ids and
backward wall-clock input are rejected. `--now` accepts a fixed aware ISO
timestamp for tests and replay. Legacy `inspect`, `commit-contact`, and
`commit-presence` commands remain compatibility tools, not the normal route.

The hot route reads only the primary note's compact Hot Character Kernel. Full
biography and secondary notes are loaded only for a relevant topic or a
structural review. Relationship state uses contextual evidence and active
tensions, not a trust/closeness meter.

Run the dependency-free distributable smoke check with:

```bash
python tools/verify_workspace.py
python tools/verify_workspace.py --json
```

Maintainers can also enforce the public-package boundary and build a clean
release from the committed canonical source:

```bash
python -B tools/build_distribution.py --target ../RePoG-release --archive ../RePoG-release.zip
python -B ../RePoG-release/tools/verify_workspace.py ../RePoG-release --distribution
```

The builder packages `HEAD`, not the mutable working tree, then writes a
SHA-256 manifest. See `DISTRIBUTION.md` for the canonical-source and vendor
license contract.

The Claude Code plugin edition is maintained in `claude-plugin/`.

## Dashboard, Companion View, And Visual Transactions

```bash
python tools/serve_dashboard.py campaign/dashboard --check-only
python tools/update_dashboard.py campaign/dashboard/dashboard_state.json --input-json "{...}"
python tools/check_companion_view.py campaign/companion_view/companion_view_state.json --campaign campaign
python tools/serve_companion_view.py campaign/companion_view --check-only
python tools/visual_handoff.py campaign --help
```

Dashboard V3 updates are atomic and require the expected source revision.
`serve_dashboard.py` validates first, binds only to `127.0.0.1`, disables
directory listing, and adds no-cache/security headers. The visual handoff tool
allows one pending `begin → attach → accept/revise/cancel` transaction and
preserves its return anchor. Acceptance copies the approved asset into both
campaign visual memory and dashboard assets; gallery, appearance, and
requested dashboard placement roll back together on failure.

Companion mode keeps Dashboard V3 off. Its independent `off | light`
Companion View is a tiny read-only projection that may contain only accepted
art and facts already shared in conversation. It never projects private
presence, relationship evidence, disclosure readiness, user memory, hidden
contacts, or internal ids. The light View refreshes only when a semantic
transaction changes visible truth. Portrait handoff uses the explicit
`companion_view_portrait` placement target; `rpg_dashboard_gallery` is rejected
in Companion mode.

## World Voices

```bash
python tools/check_world_voices.py campaign
python tools/world_voices.py campaign validate --input-json "{\"projection\":\"full\"}"
python tools/world_voices.py campaign propose --input-json "{...}"
python tools/world_voices.py campaign approve --input-json "{...}"
python tools/world_voices.py campaign schedule --input-json "{...}"
python tools/world_voices.py campaign deliver --input-json "{...}"
python tools/world_voices.py campaign archive_distribution --input-json "{...}"
python tools/world_voices.py campaign project --input-json "{...}"
```

The lifecycle helper accepts already-authored semantic content. It does not
choose a source, event, belief, lie, audience, body, or consequence. Mutations
use expected revisions, monotonic operation sequences, permanent operation
ids, atomic replacement, and rollback. Player acquisition requires explicit
confirmation of the matching knowledge revision. Projection emits only
paginated player-safe JSON below `dashboard/assets/world_voices/`; hidden
changes do not project or request a Dashboard refresh. Coarse authored,
scheduled, and completed time indices provide stable timeline ordering without
turning fictional time into a continuous simulator.

## Snapshot

```bash
python tools/snapshot.py campaign --label before_scene
```

## GM Contract Migration

```bash
python tools/migrate_gm_contract.py campaign --dry-run
python tools/snapshot.py campaign --label before_gm_contract_v3
python tools/migrate_gm_contract.py campaign --apply --json
```

Apply is refused until a snapshot manifest already exists. The migration is
idempotent, preserves fiction prose, maps legacy scene-boundary persistence
names to scene-checkpoint policies, and marks uncertain NPC agency/offscreen,
opening-lifecycle, faction-motion, relationship, and knowledge ownership for
review rather than inventing answers.

## Deep Session 0 v7-to-v8 Migration

```bash
python tools/migrate_session_zero_v8.py --campaign campaign --dry-run
python tools/snapshot.py campaign --label before_session_zero_v8
python tools/migrate_session_zero_v8.py --campaign campaign --apply --json
```

Pending or routing-only schema-v7 setups can move to the v8 shell without a
snapshot. Applying a migration to an in-progress RPG Deep setup requires an
existing full campaign snapshot. Reliable legacy decisions are preserved;
cross-stage pack and approval assumptions are reopened as `needs_review`
instead of being claimed as valid v8 evidence. Completed v7 campaigns and
Quick, Standard, or Companion routes remain untouched. Dry-run is read-only and
a second apply is idempotent.

## Companion Contract Migration

```bash
python tools/migrate_companion_contract.py campaign --dry-run
python tools/snapshot.py campaign --label before_companion_contract_v2
python tools/migrate_companion_contract.py campaign --apply --json
```

Apply likewise requires an existing snapshot and rolls all touched files back
if a write fails. It maps profile/state V1 to the single-exchange V2 contract,
adds the compact Hot Character Kernel and disabled lightweight View runtime,
preserves current presence and established evidence, and removes the old
ordered trust/closeness fields. It does not manufacture private facts,
relationship meaning, or disclosure choices: uncertain fields and a legacy
private-knowledge ledger are returned in `needs_review`. A second run is
idempotent.

## Sampled GM Replay Audit

`tools/gm_replay_suite.json` contains 12 reproducible, non-API scenarios for
sampled quality review. Each fixture provides private initial state, ordered
turns, expected observations, critical failures, and a blank scoring record.
Run it only at an explicit audit or scheduled sample using the blind procedure
in `workflows/audit/WORKFLOW.md`; it is not a per-turn checker or a second
narrative engine. A scenario passes at mean score 1.5 or higher with no
critical Player-authorship or knowledge-boundary failure.

## Companion Acceptance Audit

`tools/companion_acceptance_suite.json` indexes 20 Companion cases covering
setup routing, Quick completion, real-city/private-fiction grounding, the
single-call exchange path, permanent semantic retry safety, backward-time and
condition stability, bounded hot context, topic-specific disclosure,
evidence-based non-ladder relationships, disagreement, user authorship,
attention callbacks, anti-chatbot style, direct AI transparency, bounded
deception opt-in, all three memory policies, Companion View privacy/portrait
return, and RPG regression. The dependency-free verifier executes the
deterministic clock/revision/evidence/privacy/routing subset against temporary copies.
Run the semantic cases as sampled conversation replays under
`workflows/audit/WORKFLOW.md`; they are not per-message gates.

## Player-Facing And Style Checks

At a full RPG boundary, `check_state.py` also checks adopted act identities,
archive/opening/prep references, optional holder-account shapes, and explicit
Triggered Lookup references. `narrative_memory.py` supplies those bounded
structural checks; it does not infer facts, judge prose, or compare meanings.
The durable writer checks changed thread/account structure before committing,
without a campaign scan. Legacy campaigns without meaningful act ids remain
valid and receive an adoption warning only at a ready full review. No automatic
campaign migration or schema-version change is required.

```bash
python tools/check_player_facing.py --campaign campaign --text "You step into the rain."
python tools/check_style.py campaign/style_state.json --text "Rain ticks against the glass." --scene-id dock --beat-id turn-12
python tools/check_style.py campaign/style_state.json --text "Rain ticks against the glass." --scene-id dock --beat-id turn-12 --record
python tools/check_style.py campaign/style_state.json --text "The room settles." --dramatic-beat respite --gm-move offer-affordance --ending-form open-moment --record
```

Use `--speaker-type npc --speaker-id <id>` for a character-only excerpt. This
keeps a deliberate character voice separate from narrator-pattern warnings.
Style schema v3 also retains at most eight optional categorical fingerprints
(`dramatic_beat`, `gm_move`, `ending_form`, `sensory_channel`,
`complication_type`, `npc_social_tactic`, and `metaphor_family`). Repetition is
warning-only; the helper does not judge meaning or rewrite narration.
Optional v3 `speaker_history` retains at most eight NPC/Companion buckets and
four sampled fingerprints per speaker, so intervening narrator samples do not
erase a returning voice. Recording initializes old states lazily; raw dialogue
is not stored. Cross-NPC overlap produces an advisory surface-pattern warning
only after matching multiple other NPCs. Shared factions or deliberate motifs
may explain it; the result is not a verdict on personality or literary quality.
The player-facing check reads exact unrevealed names from
`knowledge_boundaries.md`; ordinary words such as "tool" are not banned.

## Optional World And Mechanics Helpers

```bash
python tools/world_pulse.py --input-json "{\"evaluation_id\":\"harbor-trade-rev-12\",\"domain\":\"harbor_trade\",\"elapsed_steps\":3,\"volatility\":2,\"pressure\":1}"
python tools/roll_dice.py --input-json "{\"expression\":\"2d6+1\",\"seed\":\"turn-12-lock\",\"roll_id\":\"turn-12-lock\"}"
python tools/resolve_mechanic.py campaign/mechanics_state.json --input-json "{\"operation_id\":\"turn-12-fire\",\"operation_sequence\":1,\"expected_revision\":0,\"expected_continuity_revision\":0,\"resulting_continuity_revision\":1,\"operation\":\"use_ability\",\"actor_id\":\"player\",\"action_id\":\"fire_spell\"}"
python tools/world_pulse.py --input-file - <<'JSON'
{"domains": [
 {"evaluation_id": "skip-r41-harbor", "domain": "harbor_trade", "elapsed_steps": 3, "volatility": 2, "pressure": 1},
 {"evaluation_id": "skip-r41-guild", "domain": "guild_feud", "elapsed_steps": 3, "volatility": 1, "pressure": 3}]}
JSON
python tools/resolve_mechanic.py campaign/mechanics_state.json --input-json "{\"operation_id\":\"skip-r41-wages-14\",\"operation_sequence\":8,\"expected_revision\":7,\"expected_continuity_revision\":41,\"resulting_continuity_revision\":42,\"operation\":\"settle_obligation\",\"obligation_id\":\"crew_wages\",\"period\":\"week:14\"}"
```

An `evaluation_id` gives the same world-pulse envelope on every retry. A
legacy explicit integer `seed` remains accepted. A `domains` batch (at most 12)
returns `{"ok": true, "results": [...]}` in request order, each result identical
to its single-domain call; one invalid entry fails the batch. `elapsed_steps`
counts the domain's own step: one week unless its `world_dynamics.md` entry
names another unit. Without `--campaign`, `roll_dice.py` rolls one bounded
`NdM+/-K` expression and returns its seed for reproduction; call mode is
described under Roll Calls And Odds. `world_pulse.py` and `roll_dice.py` take
the request as `--input-json`, from a UTF-8 file with `--input-file PATH`, or
from standard input with `--input-file -`, so a quoted heredoc keeps prose
apostrophes clear of shell quoting. `resolve_mechanic.py` takes only
`--input-json`.

`resolve_mechanic.py` handles only mechanics explicitly configured by the
campaign. Schema v2 rejects numeric strings and floats, requires a monotonic
operation sequence, checks both ledger and campaign continuity revisions, and
supports resources, configured abilities, inventory, conditions, clocks,
obligations, and time. Its operation registry does not discard old ids, so an
operation cannot become valid again after an arbitrary history limit. It never
interprets what those changes mean in the fiction. A schema-v1 ledger is
migrated on its next successful operation; after migration, callers must
supply the sequence and expected revisions shown above.

For downtime, a clock may also carry `owner`, `tick: {unit, amount}`, and
`on_fill`. `add_clock` (`clock_id`, `maximum`, optional `current`, `owner`,
`tick`, `on_fill`) starts a clock during play, and `remove_clock` (`clock_id`)
retires a resolved one, reporting the clock it removed. `advance_time` ticks
every clock whose tick unit matches (amount times steps, capped at the maximum)
and marks the change `filled`, with its `on_fill` line, when the clock reaches
its maximum. `add_obligation` (`obligation_id`, `actor_id`, exactly one of
`resource_id` or `item_id`, `amount`, `period_label`) records a recurring cost
such as wages or rent, paid from a resource or from an inventory item counted
by quantity, such as coins kept in a purse. `settle_obligation`
(`obligation_id`, `period`, optional `amount`) spends it from that holding once
per period key, so settling a period again is refused by name; keys compare
without case, so `Week:3` and `week:3` are one period. During play these run as
`mechanic_operations` inside `commit-durable`, which fills in the sequence and
revisions.

## Roll Calls And Odds

```bash
python tools/roll_dice.py --campaign campaign --input-file - <<'JSON'
{"roll_id": "gate-shove", "call": {"actor": "Mira", "axis": "might", "value": 3, "difficulty": 6,
 "reason": "the bar is rusted into its brackets",
 "factors": [{"label": "crowbar", "modifier": 1}], "stakes": "the guards hear the gate give"}}
JSON
python tools/odds.py campaign
```

Call mode rolls a check declared before the die is seen. The call needs
`actor`, `axis`, integer `value` and `difficulty`, and `stakes`; `factors` are
optional labelled integer modifiers, and an optional one-line `reason` says
why the difficulty is set there. The die comes from `play_profile.yaml`
`mechanics.resolution`, or from a `die` key in `NdM` form when the campaign
declares no scale, and a value or difficulty outside the declared ranges is
refused as `out_of_range`. No seed is accepted: it derives from the campaign
id, the continuity revision, the roll id, and the call, so the same roll id and
call at the same revision return the stored receipt (`repeat: true`), and a
used roll id with a different call is refused. The total is value plus
modifiers plus die, the margin is total minus difficulty, and the first band
whose `at_least` the margin reaches is the outcome (`success` at margin 0 or
more, else `failure`, without a configured scale). A call is `certain` when
its worst reachable band (`floor_band`) is a success band: it is recorded with
no dice as `auto: true` at that floor band, never the top band, with the
warning `roll_certain` (narrate the result without rolling). When value plus
modifiers beats the difficulty by `auto_success_margin` or more, the call is
also `auto: true` without dice, at its floor band, or at the lowest success
band when the floor is below success. Receipts append to
`campaign/.repog-runtime/rolls.jsonl`, newest 2,000 kept. `--input-file -`
reads the request from standard input, so the quoted heredoc above keeps
apostrophes in the stakes safe; `--input-file PATH` reads a UTF-8 file, and
`--input-json` takes the request inline.

The output starts with `summary` (`ok <band> margin <m>`). A receipt also
records `reachable_bands` (best first), `floor_band`, `ceiling_band`,
`p_below_success` (the exact chance, to four decimals, of landing below the
lowest success band, counted over every NdM sum with the value, difficulty, and
factor sum), `certain`, and `display`, the Player-facing line
`<Actor> · <axis> <value> ± <factor sum> vs <difficulty> → <faces | no roll> = <band> · <stakes clause>`
in the play language (`narration.language`, else a `records_language` code;
tables for tr, en, de, es, and fr, English otherwise), at most 140 characters
with the stakes clause shortened first. The GM may show it as is where the
dice mode shows rolls. Stakes may be keyed per band, as
`clean: ...; cost: ...; partial: ...; failure: ...` (keys case-insensitive in
en, tr, de, es, and fr, or an exact band name); `success:` covers every success
band and `failure:` only bands named for failure. The warning
`stakes_unreachable_band` names a described band the call cannot reach, and
`stakes_missing_band` a reachable band below success that the stakes leave
out.

```bash
python tools/roll_dice.py --campaign campaign axes --since-revision 40
python tools/roll_dice.py --campaign campaign reread --input-file - <<'JSON'
{"roll_id": "gate-shove", "reason": "difficulty formula corrected by OOC request", "new_band": "partial_small_cost"}
JSON
```

`axes` prints `{summary, ok, since_revision, receipts, axes: [{actor, axis,
count, auto}]}`: receipts per actor and axis at or after the revision, names
grouped without case. The act-close review uses it to limit awards to axes
rolled this act. `reread` takes `{roll_id, reason, new_band}` for a retroactive
OOC change; the roll must exist and `new_band` must be a campaign band. It
appends `{kind: "reread", reread_of, reason, new_band, revision, at}` and never
edits the receipt; repeating the newest identical reading returns
`repeat: true`. Reread rows are never open receipts and are never cited.

`odds.py` prints the exact chance of each band for every stat and difficulty
on the declared scale as Markdown, then its findings: `scale_exhausted` when
the top stat reaches the first band against every difficulty,
`first_band_unreachable` as one summary line of information, and
`auto_success_dead_zone` (warning) when `auto_success_margin` plus the dice
minimum makes the first success band certain where the margin rule says to
roll. The full check reports the same findings, plus `failure_unreachable`
(warning) when the worst band was out of reach in at least 80% of the last 20
receipts (or of the scale's pairs when fewer than 5 receipts are readable,
with auto receipts counted as out of reach); its message gives the numbers.

## Boundary Curation

```bash
python tools/curation.py packet campaign
python tools/curation.py packet campaign --target characters/edric.md=stacked_sections --target active_cast.md=cast_dead_listed
python tools/curation.py validate campaign
```

`packet` builds the frozen packet for a boundary curator, such as the
`repog-curator` agent where a host provides one: curation id,
staging path, base revision, play language, records language, targets with
reasons, the sha256 of each target, and every active directive. The curator
writes folded text in the records language and keeps the structure as is.
`packet` always takes the notes listed as due in
`campaign/.repog-runtime/curation_due.json`, merging several rules on one path
into one reason. Each `--target PATH=REASON` is added beside them, never in
their place: a named target comes first and its reason leads, followed by the
due reason for the same path. The result adds `targets_from`,
`skipped_targets` (paths that cannot be curated), and `targets_omitted`
(targets past the mutation cap).
`commit-distill` writes that file as `{at, revision, targets: [{path, rule,
reason}]}`, one target per file: the `deferred_reconcile` paths and the files
its post-commit check flags as `cast_dead_listed`,
`relationship_dead_active`, `now_overflow`, `records_language_mismatch`,
`stacked_sections`, or `note_core_missing`. The writer drops a target when a
later `commit-distill` or `commit-curation` changes its path, and deletes the
file when none remain. It refuses `session_log.md`,
`directives.md`, `archive/`, `snapshots/`, hidden folders, and non-Markdown
targets, and refuses a packet whose staged file is still waiting. The curator
writes exactly one file, `campaign/.repog-runtime/curation/<curation_id>.json`,
holding `curation_id`, `base_revision`, `reason`, `base_hashes`, and `mutations`
of typed Markdown ops without placeholders or `create_text`. `validate` reports
each staged file's shape, freshness, and a dry run, and
`rpg_state.py commit-curation` applies it: a file whose targets changed is
rejected whole, a commit that rolls back on file I/O leaves the file staged
(`deferred`), and a file whose exact payload the log already records is only
filed away (`"repeat": true`), never applied twice. Each applied file logs a
`### Curation Applied At Revision N` block with its payload hash. Warnings
`curation_file_not_moved` and `curation_restaged` mean the file stays staged
for the next run.

`campaign/.repog-runtime/curation/last_result.json` is kept for the run
record a host hook may write beside the proposals, so `packet` refuses the id
`last_result`.

Roll ids starting with `player:` are reserved for citing the Player's own
dice, and an inline `runtime: {...}` block is a full-check error
(`runtime_block_inline`): write the switches one per line.

## Runtime Layer

```bash
python tools/presentation_lint.py report campaign --last 20
python tools/lang_pack.py codes
python tools/lang_pack.py detect --candidates tr en < reply.txt
python tools/name_check.py Corlan --existing Corran Mira --language en
```

`campaign/.repog-runtime/` holds working files that are never campaign truth;
deleting it loses none: roll receipts (`rolls.jsonl`), the lint record
(`lint_last.json`, `lint_history.jsonl`), the capsule state, staged curation,
`curation_due.json` (paths, rule names, and short reasons, written by the
writer), and `order_last.json` (written by a host's after-reply hook, where one runs). `repog_runtime.py`
reads the `play_profile.yaml` `runtime:` switches, each defaulting when
absent: `presentation_lint` (`on`), `scene_capsule` (`on`), and
`boundary_curator` (`background`). `persistence_order` has one effective value,
`commit_then_narrate`; `narrate_then_commit` stays valid for older profiles and
means the same order. It resolves the records language as
`narration.records_language`, or
`narration.language` when that is `same` or missing. `presentation_lint` and
`scene_capsule` take effect only where a host hook runs them; without one,
`scene_capsule.py show` prints the capsule on demand and the lint history
stays empty.

- The Claude Code plugin adds `hook_entry.py`, the single entry its hook
  scripts call; it is host-specific and ships only with the plugin.
- `scene_capsule.py` builds the hidden capsule a host's prompt hook injects: a
  header with revision, day, location, scene, and the order
  (`order: reads and rolls → commit every changed fact → whole reply last`); the cast in
  scope with Core lines, the
  newest `## Now` lines that fit, relationship rows, and knowledge; which
  protected facts each does not hold, by fact id; a `[knowledge]` section with
  up to three `- <Name> does not know: ...` items per present NPC from
  `knowledge_boundaries.md`; directives in scope; the language card; the last
  lint summary; open roll receipts; staged curation; and, once, what the last
  curation run rejected or deferred. A session's first capsule, and the first
  after a compaction, ends with the `[formats]` card: the call shapes of a
  roll, an ordinary commit, money and items, and a due distill, with this
  install's launcher path, outside the size cap. A full capsule adds
  `[state] rev N · keys: ...` (the `current_state.yaml` top-level keys),
  `[mechanics] <actor>: <resource> n/max, <item> n` from `mechanics_state.json`, and
  `[habits] last 20 replies: label (n), ...` from
  `presentation_lint.top_habits`; a delta shows `[habits]` only when its rules
  change. While `curation_due.json` lists targets, every capsule shows
  `[curation] due: N files (...)` with the next step for the
  `boundary_curator` setting. Each `order_last.json` record is shown once: an
  `[order]` line when a turn ended with no visible text, or saved a result but
  sent fewer than 60 words, because the Player has then not seen that scene.
  A note stamped `As of revision` before the `threads.md` Arc Compass
  `Opened at revision` shows Core, `Agency Card: hidden (...)`, its Depth
  `Voice signature`, and the tail of Now instead of its Agency Card. A new
  or reset session, a changed scene, and every 12th prompt get the full
  capsule. Otherwise the header is followed only by what changed: changed
  sections, and for each person the changed lines plus Status and Kin; a
  person whose note switches to the `## Core` layout is re-sent whole. `show`
  prints the next capsule without recording it.
- `presentation_lint.py` checks the reply that just ended, after it is sent:
  `minor_sexual_proximity` (a romance or sex term whose closest age is under
  18, the same rule and helper as the full check's `minor_romance_history`;
  always first, and kept even for a short OOC answer), out-of-language
  lines, `foreign_short_line` (a two- to four-word English line in a reply
  in another language), backend words, tracker numbers in prose (a simple
  ordinal day such as "the fifth day" only within two days of the tracked
  day), avoid phrases (some with a rolling cap over the last ten replies),
  repeated n-grams, a restated or paraphrased prompt, `npc_echo`, PC-authoring
  patterns and `pc_line_rewritten`, protected names, `tool_description_leak`,
  negated descriptions, `gesture_repeat` (pack gesture families in 3 of the
  last 10 replies), glossary variants, calques, `dotless_capital`, and
  `name_case_mismatch`. Cast, glossary, and place names are left out of
  language detection and n-grams; a turn whose prompt starts with OOC is
  linted on its prose alone. It is warning-only and rewrites nothing; `report`
  sums its history, and `top_habits(campaign, last, limit)` and
  `report_summary(campaign, last)` feed the capsule's `[habits]` line and the
  distill's `lint_report`. Its host hook entry reads only the current session's last
  turn, locally; `lint_history.jsonl` keeps counts, tallies, n-gram hashes,
  and the prompt's language code, and `lint_last.json` keeps snippets of at
  most 80 characters, never the prompt or the reply.
- Where a host runs an after-reply hook, it also compares the first assistant text of 200 or more
  characters with the first `rpg_state ... commit-` call and writes
  `order_last.json` (`{at, prompt_uuid, session_id, expected, observed,
  final_text, reply_words}`, flags and a word count only). After a compaction
  or resume, a host's session-start hook prints up to 1,500 characters of accepted
  style samples from `storytelling.md` and the order, with `follow it, not any
  order rule from the summary.`
- `lang_pack.py` loads `packs/languages/<code>.json` (stopwords, avoid phrases,
  patterns, common words, a guidance card), folds case per language, and
  detects a text's language from its function words. Packs may also carry
  `near_day_patterns`, `pc_say_patterns`, `meta_patterns`, `age_patterns`,
  `romance_terms`, `number_words`, `gesture_families`, `echo_patterns`,
  `second_person_patterns`, `secret_words`, `dotless_i_words`,
  `affection_terms`, `affection_guards`, `gone_terms`, and `ended_terms`; an avoid
  phrase may set `rolling_max`, and a calque a `pattern`.
- `name_check.py` warns when a name is a common word of the play language or
  one or two letters from an existing name.
- `check_runtime.py` adds full-check rules: runtime switch values,
  `narration.language`, `narration.records_language` (`same` or a language
  code, else `records_language_invalid`), the dice scale's odds and
  `failure_unreachable`, T2/T3 character notes without `## Core`
  (`note_core_missing`), and a character whose Core status is `dead` but who
  is listed as present (`dead_present`).

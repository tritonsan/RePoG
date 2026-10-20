# Lite Tools

These small deterministic helpers guard campaign continuity. They do not create
narration or act as a second game engine.

## Campaign Checks

```bash
python tools/check_state.py campaign --scope hot
python tools/check_state.py campaign --scope full
python tools/check_dashboard.py campaign/dashboard/dashboard_state.json
```

`hot` is the bounded per-durable-turn check used by Fast and Balanced. `full`
is the default when `--scope` is omitted and is required at full distill,
session stop, closure, advancement, migration, and audit boundaries. A scene
checkpoint alone persists its small handoff contract and does not force a full
distill.

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

After `draft_preflight_passed`, use its resulting revision for the locked
profiles and both commands below. First create the snapshot with
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
python tools/rpg_state.py campaign commit-curation --apply-staged
```

`--input-json "{...}"` still works; `--input-file` reads a UTF-8 file, or
standard input for `-`, so prose apostrophes never need shell escaping.

`rpg_state.py` is a semantic-free writer, not a narrative checker. The GM
supplies the established durable changes, their immediate owner paths,
model-authored mutations, and any deferred secondary targets. A mutation is
written as typed `ops` from `owner_ops.py` (set a YAML key, edit a list,
append to, replace, remove, or insert a Markdown section, upsert or delete a
table row), as `exact_replacements`, or as `create_text` for a new entity note.
`{{revision}}` and `{{next_id:PREFIX}}` placeholders resolve in new text. The
writer stamps a mutated owner's `As of revision:` line, copies a checkpoint into
`scene_frame`, and returns advisory `warnings` for owners near the size cap,
stacked dated sections in entity notes, and a long session log.

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
continuity revision. A successful durable response with
`full_distill_required: true` has safely stored current truth but sets
`narration_allowed: false` until the routed full distill completes. Neither
command decides whether a turn was soft, what happened in the fiction, which
facts matter, or what the Player should be told.

A change decided by a roll call carries `roll_reference` (the receipt's
`roll_id`) and `outcome` (its band). The writer refuses a cited roll that has no
receipt, was rolled at another revision, was already used, or names a different
band, and refuses the whole commit with `rolls_unaccounted` while a receipt at
the expected revision is neither cited nor listed in the payload's `void_rolls`
(`[{"roll_id": ..., "reason": ...}]`, at most 16). Cited and voided receipts
are marked consumed after the commit. Until a campaign has a receipt store, a
free-text `roll_reference` without `outcome` passes with a `roll_unrecorded`
warning. A checkpoint may use scene mode `downtime`; a kind containing
`directive` requires `directives.md`, and `glossary.md` is an owner as well.
`create_text` for a new entity note adds advisory `name_common_word` and
`name_near_duplicate` warnings from `name_check.py`.

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

## Dashboard

```bash
python tools/serve_dashboard.py campaign/dashboard --check-only
python tools/update_dashboard.py campaign/dashboard/dashboard_state.json --input-json "{...}"
```

Dashboard V3 updates are atomic and require the expected source revision.
`serve_dashboard.py` validates first, binds only to `127.0.0.1`, disables
directory listing, and adds no-cache/security headers.

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
python tools/world_pulse.py --input-json "{\"domains\":[{\"evaluation_id\":\"skip-r41-harbor\",\"domain\":\"harbor_trade\",\"elapsed_steps\":3,\"volatility\":2,\"pressure\":1},{\"evaluation_id\":\"skip-r41-guild\",\"domain\":\"guild_feud\",\"elapsed_steps\":3,\"volatility\":1,\"pressure\":3}]}"
python tools/resolve_mechanic.py campaign/mechanics_state.json --input-json "{\"operation_id\":\"skip-r41-wages-14\",\"operation_sequence\":8,\"expected_revision\":7,\"expected_continuity_revision\":41,\"resulting_continuity_revision\":42,\"operation\":\"settle_obligation\",\"obligation_id\":\"crew_wages\",\"period\":\"week:14\"}"
```

An `evaluation_id` gives the same world-pulse envelope on every retry. A
legacy explicit integer `seed` remains accepted. A `domains` batch (at most 12)
returns `{"ok": true, "results": [...]}` in request order, each result identical
to its single-domain call; one invalid entry fails the batch. Without
`--campaign`, `roll_dice.py` rolls one bounded `NdM+/-K` expression and returns
its seed for reproduction; call mode is described under Roll Calls And Odds.

`resolve_mechanic.py` handles only mechanics explicitly configured by the
campaign. Schema v2 rejects numeric strings and floats, requires a monotonic
operation sequence, checks both ledger and campaign continuity revisions, and
supports resources, configured abilities, inventory, conditions, clocks, and
time. Its operation registry does not discard old ids, so an operation cannot
become valid again after an arbitrary history limit. It never interprets what
those changes mean in the fiction. A schema-v1
ledger is migrated on its next successful operation; after migration, callers
must supply the sequence and expected revisions shown above.

For downtime, a clock may also carry `owner`, `tick: {unit, amount}`, and
`on_fill`. `advance_time` ticks every clock whose tick unit matches (amount
times steps, capped at the maximum) and marks the change `filled`, with its
`on_fill` line, when the clock reaches its maximum. `add_obligation`
(`obligation_id`, `actor_id`, `resource_id`, `amount`, `period_label`) records a
recurring cost such as wages or rent; `settle_obligation` (`obligation_id`,
`period`, optional `amount`) spends it from the actor's resource once per
period key, so settling a period again is refused by name. During play these
run as `mechanic_operations` inside `commit-durable`, which fills in the
sequence and revisions.

## Roll Calls And Odds

```bash
python tools/roll_dice.py --campaign campaign --input-json "{\"roll_id\":\"gate-shove\",\"call\":{\"actor\":\"Mira\",\"axis\":\"might\",\"value\":3,\"difficulty\":6,\"factors\":[{\"label\":\"crowbar\",\"modifier\":1}],\"stakes\":\"the guards hear the gate give\"}}"
python tools/odds.py campaign
```

Call mode rolls a check declared before the die is seen. The call needs
`actor`, `axis`, integer `value` and `difficulty`, and `stakes`; `factors` are
optional labelled integer modifiers. The die comes from `play_profile.yaml`
`mechanics.resolution`, or from a `die` key in `NdM` form when the campaign
declares no scale, and a value or difficulty outside the declared ranges is
refused as `out_of_range`. No seed is accepted: it derives from the campaign
id, the continuity revision, the roll id, and the call, so the same roll id and
call at the same revision return the stored receipt (`repeat: true`), and a
used roll id with a different call is refused. The total is value plus
modifiers plus die, the margin is total minus difficulty, and the first band
whose `at_least` the margin reaches is the outcome (`success` at margin 0 or
more, else `failure`, without a configured scale). When value plus modifiers
beats the difficulty by `auto_success_margin` or more, the call takes the first
band without dice (`auto: true`). Receipts append to
`campaign/.repog-runtime/rolls.jsonl`, newest 2,000 kept.

`odds.py` prints the exact chance of each band for every stat and difficulty
on the declared scale as Markdown, then its findings: `scale_exhausted` when
the top stat reaches the first band against every difficulty, and
`first_band_unreachable` as information. The full check reports the same
findings.

## Boundary Curation

```bash
python tools/curation.py packet campaign --target characters/edric.md=stacked_sections --target active_cast.md=active_cast_stale
python tools/curation.py validate campaign
```

`packet` builds the frozen packet for the `repog-curator` agent: curation id,
staging path, base revision, play language, targets with reasons, the sha256
of each target, and every active directive. It refuses `session_log.md`,
`archive/`, `snapshots/`, hidden folders, and non-Markdown targets, and refuses
a packet whose staged file is still waiting. The agent writes exactly one file,
`campaign/.repog-runtime/curation/<curation_id>.json`, holding `curation_id`,
`base_revision`, `reason`, `base_hashes`, and `mutations` of typed Markdown ops
without placeholders or `create_text`. `validate` reports each staged file's
shape, freshness, and a dry run. `rpg_state.py commit-curation` applies it.

## Runtime Layer And Hooks

```bash
python tools/presentation_lint.py report campaign --last 20
python tools/scene_capsule.py show campaign --full
python tools/lang_pack.py codes
python tools/lang_pack.py detect --candidates tr en < reply.txt
python tools/name_check.py Corlan --existing Corran Mira --language en
```

`campaign/.repog-runtime/` holds working files that are never campaign truth;
deleting it loses none. `repog_runtime.py` reads four `play_profile.yaml`
`runtime:` switches, each defaulting when absent: `persistence_order`
(`narrate_then_commit`), `presentation_lint` (`on`), `scene_capsule` (`on`), and
`boundary_curator` (`background`).

- `hook_entry.py prompt|stop|session-start|pretool` is the single entry the
  hook scripts call. It reads the hook event on standard input, prints only
  the JSON Claude Code expects, and never raises.
- `scene_capsule.py` builds the hidden capsule the prompt hook injects: a
  header with revision, day, location, scene, and persistence order; the cast
  in scope with Core lines, current state, relationship rows, and knowledge;
  which protected facts each does not hold, by fact id; directives in scope;
  the language card; the last lint summary; open roll receipts; and staged
  curation. A new or reset session, a changed scene, and every 12th prompt get
  the full capsule, otherwise only changed sections. `show` prints the next
  capsule without recording it.
- `presentation_lint.py` checks the reply that just ended, after it is sent:
  out-of-language lines, backend words, tracker numbers in prose, avoid
  phrases, repeated n-grams, a restated prompt, PC-authoring patterns,
  protected names, negated descriptions, glossary variants, and calques. It is
  warning-only and rewrites nothing; `report` sums its history for a distill
  review.
- `lang_pack.py` loads `packs/languages/<code>.json` (stopwords, avoid phrases,
  patterns, common words, a guidance card), folds case per language, and
  detects a text's language from its function words.
- `name_check.py` warns when a name is a common word of the play language or
  one or two letters from an existing name.
- `check_runtime.py` adds full-check rules: runtime switch values,
  `narration.language`, the dice scale's odds, T2/T3 character notes without
  `## Core` (`note_core_missing`), and a character whose Core status is `dead`
  but who is listed as present (`dead_present`).

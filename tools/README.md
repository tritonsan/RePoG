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
python tools/rpg_state.py campaign commit-durable --input-json "{...}"
python tools/rpg_state.py campaign commit-checkpoint --input-json "{...}"
```

`rpg_state.py` is a semantic-free writer, not a narrative checker. The GM
supplies the established durable changes, their immediate owner paths, exact
model-authored mutations, and any deferred secondary targets. One
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
The player-facing check reads exact unrevealed names from
`knowledge_boundaries.md`; ordinary words such as "tool" are not banned.

## Optional World And Mechanics Helpers

```bash
python tools/world_pulse.py --input-json "{\"evaluation_id\":\"harbor-trade-rev-12\",\"domain\":\"harbor_trade\",\"elapsed_steps\":3,\"volatility\":2,\"pressure\":1}"
python tools/roll_dice.py --input-json "{\"expression\":\"2d6+1\",\"seed\":\"turn-12-lock\",\"roll_id\":\"turn-12-lock\"}"
python tools/resolve_mechanic.py campaign/mechanics_state.json --input-json "{\"operation_id\":\"turn-12-fire\",\"operation_sequence\":1,\"expected_revision\":0,\"expected_continuity_revision\":0,\"resulting_continuity_revision\":1,\"operation\":\"use_ability\",\"actor_id\":\"player\",\"action_id\":\"fire_spell\"}"
```

An `evaluation_id` gives the same world-pulse envelope on every retry. A
legacy explicit integer `seed` remains accepted. `roll_dice.py` accepts only
bounded `NdM+/-K` expressions and returns its seed for reproduction.

`resolve_mechanic.py` handles only mechanics explicitly configured by the
campaign. Schema v2 rejects numeric strings and floats, requires a monotonic
operation sequence, checks both ledger and campaign continuity revisions, and
supports resources, configured abilities, inventory, conditions, clocks, and
time. Its operation registry does not discard old ids, so an operation cannot
become valid again after an arbitrary history limit. It never interprets what
those changes mean in the fiction. A schema-v1
ledger is migrated on its next successful operation; after migration, callers
must supply the sequence and expected revisions shown above.

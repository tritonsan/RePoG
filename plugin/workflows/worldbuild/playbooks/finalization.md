# Session 0 Finalization And Materialization

Load this playbook at the selected route's final readiness boundary.

Current reciprocity RPG routes—schema-v6–v8 Quick, schema-v7–v8 Standard,
schema-v7 Deep, schema-v9+ Quick/Standard, and the Deep-v8 ledger route—
reach this boundary only after actual materialized preparation was reviewed
player-safe and approved at the current setup revision. Their substantive
world/cast/opening synthesis is already complete.

Legacy schema-v1–v6 Standard/Deep, legacy Quick, and Companion retain their
existing route: accepted interview truth may still be expanded into the
required playable core inside this boundary before draft preflight.

Supporting workers, when eligible, remain read-only proposal workers. The
coordinator is the sole campaign writer and player-facing voice.

Schema-v9+ Quick/Standard reach this boundary through their single combined
actual-preparation acceptance. Do not request a second readiness approval or
legacy slot 10/module 21. Deep continues its existing ledger gates.
Here "Deep ledger" means the `rpg_deep_v8` flow in every supported schema-v8+
workspace, including v10. Schema-v10+ Quick/Standard require complete required
decision rows instead of a numeric question target.

# Route Boundary

For a current reciprocity RPG route, finalization may only:

- verify frozen approvals and reviewed owner files;
- reconcile non-substantive formatting or metadata;
- run draft preflight;
- lock candidate profiles at the applicable approved revision and transition
  readiness only at the route's final gate;
- build approved derived projections;
- snapshot, aggregate-check, and hand off.

It may not first introduce a character tie, independent pressure, intersection,
place, NPC/faction role, capability/limitation response, opening premise, or
player-facing fact.

# Frozen Setup Seed

Before eligible work, keep `ready_for_play: false` and freeze an in-memory seed
containing:

- setup revision, experience/depth, content-decision count, ordinary
  locked/defaulted/deferred decisions, and reviewed-default state;
- applicable design-direction and preparation approval revisions;
- Deep-only activated/completed/defaulted packs, checkpoint, and extension
  permission;
- campaign promise, character seed, boundaries, research, lenses and mechanics;
- runtime/presentation/performance contracts;
- starting scale, stable ids and visibility classifications;
- sources each lane may read and files it may propose;
- coordinator-exclusive fields.

A current reciprocity RPG seed is valid only when design approval precedes the
accepted preparation at the frozen setup revision. Schema-v7 Deep additionally
requires every activated pack resolved. The Deep ledger instead freezes
`session_zero_state.json`: all nine stages and activated stage extensions must
be complete, no output may be stale, and every gate through
`preparation_approved` must carry current revision/digest evidence.

For Companion, preserve its existing final-summary and parallelism/usage
acknowledgement behavior. Do not manufacture consent during final fields.

Do not persist orchestration bookkeeping. Workers may not allocate cross-domain
ids, change setup decisions, write files, run mutation tools, or announce
completion.

# Eligibility And Lanes

Current reciprocity RPG proposal lanes run before the integrated preparation
review, not after final approval:

- Quick: at most two lanes—world ecology; cast/space.
- Standard/Deep: at most three lanes—world ecology; cast/space; and systems/
  presentation only when substantial and independent.

When this playbook loads, those results must already be merged and reviewed.
Do not launch replacement lanes merely because workers were unavailable.

Legacy RPG routes may use their prior lanes during this boundary. Companion
may use at most two persona/life and relationship/privacy lanes. Under `off` or
without harness support, execute serially. A worker failure always falls back
to coordinator-owned serial completion.

The coordinator owns profiles, player truth, knowledge/disclosure, current
state/presence, opening or Companion voice, ids, revision, approvals, readiness,
projections, visual transactions, snapshot, and checks.

# Coordinator Merge For Legacy Routes

For routes that still materialize here, verify `job_id` and `base_revision`,
discard stale proposals, allocate ids centrally, and merge in authority order:

1. runtime profile and boundaries/research truth;
2. knowledge/disclosure truth;
3. durable world/persona, issues/domains, characters, places, factions,
   relationships, routes and threads;
4. current scene/cast or Companion presence;
5. opening/prep or public-surface projections.

Accepted material belongs to the frozen setup revision. Conflicts are resolved
by the coordinator, never majority vote.

For current reciprocity RPG routes, compare current files with the reviewed
frozen revision and reject any unreviewed substantive delta instead of merging
it.

# RPG Materialization

Legacy routes materializing here create only enough content for opening-scale
play: campaign contract, active RPG profile, inactive Companion profile,
player/ties, memory-v3 state/scene frame, cast, location graph, relationship and
knowledge truth, limited dynamics, relevant characters/places/factions,
opening prep, and approved optional mechanics/projections.

Current reciprocity RPG routes already have these authoritative owners. Their
`first_session.md` is `materialized` and `opening_brief.md` is `active` before
preparation approval. Finalization may not alter substantive reviewed content
without invalidating approval.

The coordinator drafts and leakage-checks the player-facing opening; workers
never deliver it. Mark first-session and opening sources `consumed` only after
the opening is actually used.

# Companion Materialization

Retain the existing Companion contract: adult T3 primary note, locked Companion
profile, inactive RPG profile, Companion state, consent-safe user context,
life domain, strict disclosure ledger, versioned boundaries, relationship truth,
and only needed contacts/places. Keep RPG scene/mechanics/Dashboard/World
Voices inactive. The coordinator validates and writes the first established-
voice message.

# Readiness Order

Use this order exactly. On the Deep ledger, steps 2, 3, and 5–7 are one call
after Stage 9 completes:
`tools/session_zero_state.py campaign finalize --operation-id <id>
--expected-revision <current>`. It stops at the first failing step with a typed
error, `failed_step`, and `completed_steps`; fix that step and call it again
with the current revision. It never repeats a passed preflight gate. With
approved projections (step 4), call it with `--stop-after lock_profiles`, build
them, and call it again. Do not run the steps one by one or edit profile fields
by hand.

Before step 1 on every route, calibrate every NPC card to the accepted NPC
power scale: each T2/T3 `Power Band:` inside the scale and its tier cap, and no
stat above its band. A full check must show no calibration warning
(`power_band_mismatch` and the early-stage power rules) and no
`minor_romance_history`; on the Deep ledger `finalize` refuses readiness until
they are resolved. A `records_language_mismatch` does not block: `finalize`
reports it under `advisories`, and the records are translated when convenient.

1. **Approval gate.**
   - Current reciprocity RPG: design approval exists; actual preparation review
     is accepted; preparation approval equals current `setup_revision`; schema-
     v7 Deep has no unresolved pack; the Deep ledger has no incomplete/stale
     stage or extension and its gate chain is current through
     `preparation_approved`.
   - Legacy/Companion: existing final-summary approval applies.
2. **Draft-state preflight.** While setup is `in_progress`, selected profile is
   pending, and `ready_for_play: false`, run:

   ```powershell
   python tools/check_state.py campaign --scope full --preflight-ready
   ```

   It must report zero errors. Preflight never substitutes for an approval.
   On the Deep ledger, record `draft_preflight_passed` now, bound to the current
   preparation approval. That gate advances `setup_revision`; use the resulting
   revision for every profile, snapshot, aggregate-report, and final-gate step
   below.
3. **Candidate profile and route fields.** Set the selected profile `locked`,
   the unused profile `inactive`, and `source_setup_revision` to the applicable
   approved revision (the post-preflight revision for the Deep ledger). Do not
   increment the revision or narrate. Then follow the explicit route split:
   - **Deep ledger:** keep `status: in_progress`, `ready_for_play: false`;
     its atomic final gate alone owns the readiness transition.
   - **Quick/Standard, legacy non-ledger RPG, and Companion:** set
     `status: complete`, `ready_for_play: true` at the same approved revision
     before projections/snapshot, as their snapshot contract requires. This is
     candidate-ready metadata, not permission to narrate before the final check.
4. **Derived ready projections.** Serially compile approved RPG Atlas/Dashboard
   or Companion View at that revision and run their checks. When RPG Agent
   Seats are `on_demand`, validate `agent_roster.json`; every `ready` entry must
   reference a T3 character with a complete Agent Playability Card and bounded
   authority. Zero ready entries are allowed only when the final player-safe
   preparation review explicitly records that no suitable party-capable T3
   character exists yet.
5. **Starting snapshot.** Run `tools/snapshot.py campaign --label
   session-zero-start` after candidate profiles/projections. The command returns
   `snapshot_path`; append `snapshot_manifest.json` and express that file as a
   campaign-relative ref for the next command.
6. **Final aggregate check.** For the Deep ledger, call
   `tools/session_zero_state.py campaign prepare-ready-evidence` with a stable
   operation id, the current expected revision, the returned snapshot-manifest
   ref, and a manifest-authorized `snapshots/*readiness*.json` target. The helper
   runs the real full candidate-ready check, writes the canonical zero-error
   report, validates every digest, and returns the complete `evidence` object;
   do not hand-author that report. Other routes run their existing full state
   check once, including Companion validation when selected.
7. **Deep ledger final gate.** Record `ready_and_snapshotted` only after the
   snapshot manifest exists, `draft_preflight_passed` remains current, and the
   helper has reported zero errors. Use the same expected revision; pass the
   helper's exact `evidence` object through `--evidence-json`, use its
   `snapshot_digest` as `--output-digest`, and use the
   `draft_preflight_passed` output digest as `--input-digest`. This
   revision-neutral gate atomically changes setup to `complete` and
   `ready_for_play: true`. Other routes have already made their candidate
   transition in step 3; they do not call this gate.
8. **Handoff.** Enter the prepared RPG opening or Companion voice only after
   zero errors. On an RPG route, say one short out-of-fiction thing first, in the
   Player's own language, before the opening narration: they can mark any message
   `OOC` to step outside the story, and that channel covers adding or changing a
   limit, stopping or redoing a moment, changing how much the game tracks or how
   dice are used, and saying a thread has run long enough. This is the only place
   it is said—keep it to a few sentences, do not repeat it at later openings, and
   record in `boundaries.md` that it was stated. Run
   `tools/check_player_facing.py` on the opening narration before delivering it:
   the aggregate state check does not cover leakage, and this narration is drafted
   after every other gate has already passed, so nothing else stands between the
   prohibited-terms list in `boundaries.md` and the Player.
   Then send the OOC line and the opening narration as text, in the reply
   itself. Text written before a tool call is visible to the Player. Only after
   that make the opening's one commit (opening and first-session sources
   `consumed`, the OOC line recorded as stated), never in the background, and
   end the turn with the hand-back line. Never commit first and narrate after.

# Failure And Invalidation

If the initial draft preflight fails, correct the draft issue and rerun it.
For the Deep ledger, record `draft_preflight_passed` only after zero errors. If snapshot or
`prepare-ready-evidence` later fails only because of final metadata or a derived
projection, do not record the preflight gate again. Keep its resulting revision,
correct the non-substantive issue, then repeat candidate profile fields ->
projections -> fresh snapshot -> `prepare-ready-evidence` with a new operation id
for changed inputs -> final gate.

For a non-ledger route, any projection/snapshot/final-check failure after its
candidate transition restores setup to `in_progress`, `ready_for_play: false`,
and the selected profile to `pending` before further work. Keep the accepted
revision for metadata-only repair; rerun the applicable preflight and candidate
sequence, never narrate from failed readiness. Deep failures retain the draft
readiness state and follow their existing evidence/gate recovery; do not repeat
an already successful revision-advancing preflight gate for metadata-only repair.

For a current reciprocity RPG route, any substantive authoritative correction
increments `setup_revision`, clears preparation approval, and returns to the
integrated preparation review and approval. If the change affects design inputs
or a Deep pack, clear both approvals and return to reciprocity design review.
Never patch unreviewed substantive truth into readiness.

After successful handoff, the accepted setup snapshot/report is historical
evidence. Opening consumption, the recorded OOC introduction, ordinary play,
and scoped runtime configuration changes update their current owners; they do
not rewrite or renew the historical starting approval. An actual setup redesign
uses the applicable invalidation/review procedure instead.

Legacy and Companion routes retain their existing draft correction loop. Keep
failed candidate snapshots as diagnostic history only.

# Ready Criteria

Every current reciprocity RPG requires:

- schema-v10+ Quick/Standard: every selected required decision row locked;
  earlier numeric routes: their valid decision budget and status block;
- reviewed defaults/deferrals;
- earlier design approval and current preparation approval;
- permitted research and valid current-revision runtime profile;
- no pack lifecycle outside Deep and no unresolved active Deep pack;
- real character with current desire, competence, limitation/counterplay,
  social position, change/authorship boundaries;
- character-originated anchor or explicit isolation;
- independently moving world issue/domain and playable intersection;
- causal place/routine/access/arrival fit;
- independently motivated relationships and natural present cast;
- neutral action space, actionable active opening, resumable scene frame,
  routes and knowledge boundaries;
- optional player-safe projections and successful starting snapshot.

The Deep ledger replaces the numeric budget/status-block/pack requirements in
that list with its canonical stage ledger, named extensions, output digests,
and complete gate chain. Decision count remains a fatigue signal only.

Structural checkers validate route-specific required rows or legacy counts,
revisions, statuses, packs, owner
existence, and existing readiness contracts. The coordinator and player-safe
review judge semantic reciprocity quality.

Legacy RPG readiness retains its existing requirements. Companion readiness
retains its adult persona, independent life, disclosure/privacy, presence,
boundary, optional View, and snapshot requirements.

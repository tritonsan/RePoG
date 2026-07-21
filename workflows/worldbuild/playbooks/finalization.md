# Session 0 Finalization And Materialization

Load only after the user approves the final Session 0 summary. This is a
structural boundary: it may use bounded read-only proposal workers, but the
coordinator remains the sole campaign writer and player-facing voice.

# Frozen Setup Seed

Before any delegation, keep `ready_for_play: false` and freeze an in-memory
seed containing:

- setup revision, experience/depth, locked/defaulted/deferred decisions;
- pitch/premise, boundaries, research status, active lenses, and approved
  mechanics;
- accepted runtime/presentation/performance policies;
- starting scale, stable entity/fact ids, and visibility classifications;
- sources each lane may read and the files it may propose;
- fields and decisions owned exclusively by the coordinator.

For Companion, final user approval also materializes the already-shown
parallelism/usage notice acknowledgement in both `companion_profile.yaml` and
`session_zero.md` while the profile remains pending. The draft preflight must
therefore prove the acknowledgement before final locking; do not manufacture
consent during the final-fields step.

Do not persist orchestration bookkeeping. Use the Frozen Task Packet and
Supporting-Agent Result contracts in `workflows/orchestration/WORKFLOW.md`.
Workers are read-only and may not allocate cross-domain ids, change setup
decisions, write campaign files, run mutation tools, or announce completion.

# Eligibility And Lanes

Under `off`, or without harness support, execute every lane serially.
Under `selective_structural`, delegate only when at least two lanes contain
substantial independent synthesis. Under `aggressive_structural`, the same
safety contract applies but smaller eligible lanes may run in parallel.

RPG Quick uses at most two workers:

1. world ecology proposal: truths, pressures, initial factions, limited world
   domains, and World Operating Model evidence;
2. cast/space proposal: playable NPC/place cards, natural presence,
   relationships, routes, traffic, and first-scale affordances.

RPG Standard/Deep may use a third worker:

3. systems/presentation proposal: accepted mechanics/progression consequences,
   rules prose, storytelling nuance, and approved visual/Dashboard projection
   requirements.

Companion uses at most two workers:

1. persona/life ecology proposal: behavioral core, contradiction, backstory,
   routine, obligations, goals, places, and bounded social ecology;
2. relationship/privacy proposal: starting relational evidence, boundaries,
   disclosure topics, user-memory policy, messaging habits, and light View
   requirements.

The coordinator always owns the final profile, knowledge/disclosure truth,
current state/presence, opening or final Companion voice, entity ids, revision,
readiness, Dashboard/Companion View writes, visual transactions, snapshot, and
checks.

# Coordinator Merge

Wait for every requested result, verify `job_id` and `base_revision`, discard
stale proposals, allocate requested ids centrally, and resolve overlaps from
accepted Session 0 decisions. Merge in authority order:

1. active runtime profile and stable boundaries/research truth;
2. authoritative knowledge or disclosure facts;
3. durable world/persona notes, issues/domains, characters, places, factions,
   relationships, routes, and threads;
4. current RPG scene/cast or Companion presence/attention state;
5. opening/prep or public-surface projections.

All accepted material belongs to the frozen setup revision. A worker failure
falls back to serial completion; conflicts are resolved by the coordinator,
not by majority vote. Never preserve duplicate current truth merely because
two lanes proposed it.

# RPG Materialization

Create only enough content for the opening scale. Fill the shared campaign
contract, active RPG profile, inactive Companion profile, player/ties,
memory-v3 current state and scene frame, active cast, location graph,
relationship and knowledge truth, limited world dynamics, relevant
characters/places/factions, opening prep, and optional approved mechanics,
Dashboard, Atlas, or visual state.

`first_session.md` moves from `drafting` to `materialized` and
`opening_brief.md` from `pending` to `active`. The coordinator drafts and
leakage-checks the player-facing opening; workers never deliver it. Mark both
opening sources `consumed` only after the opening is actually used.

# Companion Materialization

Create the adult T3 primary note, locked schema-v2 Companion profile, inactive
RPG profile, schema-v2 Companion state, consent-safe user context, at least one
life domain, strict disclosure ledger, versioned boundaries, relationship
truth, and only the contacts/places needed for a coherent starting life.
Assign the workspace's permanent `campaign_id` in the shared current-state
identity even though its RPG scene remains inactive. Keep RPG player, scene,
mechanics, Dashboard, and World Voices material inactive. The coordinator
validates and writes the first message in the established character voice.

# Readiness Order

Use this order exactly:

1. **Draft-state preflight:** while setup is `in_progress`, the selected
   profile is pending, and `ready_for_play: false`, run:

   ```powershell
   python tools/check_state.py campaign --scope full --preflight-ready
   ```

   This applies readiness-content checks while exempting only final status,
   the profile lock, ready-only projections, and starting snapshot. It must
   report zero errors before continuing.
2. **Final fields:** set the selected runtime profile `locked`, the unused
   profile `inactive`, setup `status: complete`, and `ready_for_play: true` at
   the same setup revision. Do not narrate yet.
3. **Derived ready projections:** materialize enabled projections at the final
   revision. For RPG, compile the player-known Atlas when its map tile is
   enabled, create/refresh approved Dashboard V3 tiles, and run their existing
   checks. For Companion `light`, create/refresh the player-safe Companion View
   at the matching public-surface revision and validate it; for `off`, preserve
   the disabled projection. These writes remain serial and undelegated.
4. **Starting snapshot:** run `tools/snapshot.py campaign --label
   session-zero-start` after the final fields are present so the snapshot is a
   restorable ready state including finalized projections.
5. **Final aggregate check:** run the full state check once; for Companion also
   run its required Companion validation as part of the same completion
   boundary, not as an ordinary-message follow-up.
6. **Handoff:** only after zero errors may the coordinator enter the prepared
   RPG opening or speak as the Companion.

If the final aggregate check fails, restore the exact pre-final draft fields
and previous derived projections: setup returns to `in_progress` and
`ready_for_play: false`, and the selected profile returns to its pending
state. Correct authoritative content while draft, rerun `--preflight-ready`,
then repeat the complete final-fields -> derived-projections -> new starting
snapshot -> aggregate-check sequence. Do not merely patch a ready campaign and
rerun the last command. Keep prior candidate snapshots as diagnostic history;
only the latest successful sequence proves readiness.

# Ready Criteria

RPG readiness requires locked/defaulted/deferred modules, completed/defaulted
activated packs, permitted research, a real character, starting place,
campaign pressure or valid calm affordance, actionable active opening,
resumable scene frame, natural present cast, routes, knowledge boundaries,
valid performance/profile revision, optional player-safe Dashboard, and a
starting snapshot.

Companion readiness requires a locked current-revision profile; adult T3
behavioral core, independent life, voice, backstory, ecology, and boundaries;
valid current presence and relational evidence; at least one life domain;
strict disclosure and versioned boundary entries; consent-safe empty initial
user memory; sufficient real-city research when selected; no pending portrait;
and a valid optional light Companion View without private leakage.

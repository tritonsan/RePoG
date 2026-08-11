# Workflow

RePoG Lite Distill

# Purpose

Use this workflow only at a full-distill trigger to reconcile pending durable
events into compact campaign memory. A scene checkpoint is defined below but
does not by itself invoke full distillation. Any turn-established durable truth
must already have a successful `tools/rpg_state.py commit-durable` receipt and
current owner mutation before this workflow begins; Distill does not reconstruct
or judge a missing semantic capture from prose.

Distill is not a technical changelog. It is the GM's memory becoming sharper.

This RPG distill workflow does not run for ordinary Companion exchanges.
Companion mode follows `workflows/companion/WORKFLOW.md`: one
`begin-exchange` call owns contact-clock work, while a bounded
`commit-semantic` transaction updates only the authorities affected by a
meaningful life, disclosure, relationship, callback, user-memory, or public
surface change. At a Companion session stop or explicit full review, reconcile
the append-only history and triggered cold notes without creating RPG scene,
arc, advancement, Dashboard, or World Voices state. The separate optional
Companion View is refreshed only when the same semantic transaction changes
already-shared player-safe truth.

# Inputs

Start with `play_profile.yaml`, `current_state.yaml.persistence`, and pending
durable events in `session_log.md`. Then read only authorities and cold targets
named by those events or required by the trigger. Relevant inputs may include:

- `play_profile.yaml`, which owns runtime performance, narration, mechanics,
  advancement, dashboard, and visual policy;
- `session_log.md`;
- `current_state.yaml`;
- `active_cast.md`;
- `location_graph.md` when movement, access, or discovery changed;
- `map_atlas.json` only when stable geometry or atlas presentation changed;
- `world.md`;
- `research_dossier.md`, when source scope, canon, realism, or world logic was
  tested;
- `system_fit.md`, when the play activity mix or mechanics assumptions changed;
- `palette.md`, when a tone/canon boundary was tested;
- `appearance_guide.md`, when appearance detail rules, visual continuity, or
  image-readiness changed;
- `world_truths.md`, when play established or contradicted a durable truth;
- `issues.md`;
- `faces_and_places.md`;
- `progression.md`;
- `arc_closure.md`;
- `next_act_prep.md`, when preparing or carrying forward a scenario, arc, or
  campaign closure;
- `knowledge_boundaries.md`;
- `creation_ledger.md`;
- `relationship_map.md`;
- `secrets_and_clues.md`, when present;
- `session_brief.md`, when present;
- `threads.md`;
- relevant `characters/*.md`;
- relevant `places/*.md`;
- relevant `factions/*.md`;
- `opening_brief.md` when preparing a next-scene or post-arc opening;
- `style_state.json` when a style review is due;
- `visual_state.json` when a visual transaction was completed or interrupted;
- `dashboard/dashboard_state.json` when the campaign uses a local dashboard;
- `rules.md` if rulings changed.

# Distill Outputs

Distill propagates already committed truth and closes a structural boundary; it
does not repair a skipped immediate owner from event prose.

## Immediate-Authority Precondition

When their truth changed, these surfaces must already have been mutated by the
originating `commit-durable` transaction and must not appear only as cold work:

- `current_state.yaml`, including player position, inventory, conditions,
  scene truth, and arc/advancement gates;
- `active_cast.md` for relevant whereabouts, activity, objective,
  availability, presence reason, and next move;
- `knowledge_boundaries.md`, `relationship_map.md`, `mechanics_state.json`,
  `threads.md`, `world_dynamics.md`, `issues.md`, `location_graph.md`,
  `creation_ledger.md`, `world_truths.md`, and `rules.md` when their owned truth
  changed;
- `player.md`, `player_ties.md`, and relevant `characters/*.md`, `places/*.md`,
  or `factions/*.md` for durable facts they uniquely own;
- `arc_closure.md` when a closure, advancement status, reward, or continuation
  gate became established truth.

If a pending event names one of these as an immediate authority but the change
is absent, stop and treat it as failed capture or recovery, not as deferred
propagation. If Distill reasoning itself establishes new truth in one of these
surfaces, first create one semantic capture and commit it atomically with
boundary `full_distill`.

## Eligible Secondary Propagation

Update only the smallest listed deferred targets or boundary records:

- append a concise session/arc summary and one
  `### Distilled Through Revision N` marker to `session_log.md` after every
  event through N has actually been propagated;
- update `faces_and_places.md` when an already committed issue gained or lost a
  useful NPC/place handle;
- update `research_dossier.md`, `system_fit.md`, `palette.md`, or
  `appearance_guide.md` only when the triggering source, fit, explicit boundary,
  or visual-continuity decision requires it;
- update `next_act_prep.md` after scenario, arc, or campaign closure to carry
  forward already authoritative NPC, faction, location, item, condition,
  secret, relationship, resource, and pressure truth;
- update `progression.md` only when the campaign-level cadence or reward
  philosophy changed, not for one character's newly earned result;
- update `secrets_and_clues.md` as an archive or availability plan after the
  corresponding knowledge truth was committed immediately;
- update `session_brief.md` for the next session, scene chain, or arc;
- enrich character, place, or faction notes only with secondary presentation
  supported by their authority truth. Do not duplicate current relationship,
  knowledge, offscreen motion, or event history, and do not invent a new stable
  fact merely to make the note fuller;
- update `opening_brief.md` as `post_arc_opening` with Opening status `pending`
  while drafting and `active` only after the next opening is complete; the
  historical `first_session.md` remains `consumed`;
- update warning-only `style_state.json` when its policy selects the sample;
- patch Dashboard V3 through `tools/update_dashboard.py` only when an approved
  tile has changed player-known information and its refresh policy is due.

Do not touch an unrelated file merely because a distill is running.

# Summary Shape

A good Lite distill captures:

- what the player chose;
- what changed because of that choice;
- which elements the Player treated as important enough to promote;
- which NPCs now care;
- which NPCs clicked at the table;
- which NPC voice, posture, or ordinary speech detail worked;
- which NPCs sounded too similar, too cryptic, or too suspicious by default;
- what danger or opportunity grew;
- what question remains open;
- what should be remembered next time.

Avoid summaries that read like command logs. Prefer dramatic consequence over
mechanical bookkeeping.

# Persistence Boundaries

Read `current_state.yaml.persistence` and every `### Durable Revision N` after
the most recent `### Distilled Through Revision N` marker. Each structured
event is an atomic receipt and recovery index: its `Immediate authorities`
should already contain the established truth, while `Deferred propagation`
names only secondary work. The event is not another truth owner; when receipt
prose and an immediate authority conflict, the authority wins and a correction
is appended rather than rewriting history.

An `ordinary` soft result writes nothing and never enters this workflow. An
ordinary durable result has already been committed once by `rpg_state.py`; do
not replay it, increment it again, or add a separate hot check here.

## Scene Checkpoint

The GM workflow commits a checkpoint at the boundary that created it:

- when the causal result is durable, checkpoint data and exact scene-frame or
  active-cast mutations are included in that same `commit-durable` payload;
- when no durable truth changed, one `commit-checkpoint` call persists only the
  resumability handoff without a continuity revision.

The checkpoint contains:

- `current_state.yaml.scene_frame`, including the last causal beat, no more
  than three pending consequences, and the concrete resume anchor;
- relevant current whereabouts/activity in `active_cast.md`;
- the active-cast handoff needed to resume safely.

Do not make a second checkpoint write after a durable commit. Do not reconcile
queued cold targets, reset the durable counter, append a distilled-through
marker, or run the full check merely because a scene ended. Pure checkpoint
persistence creates no continuity revision.

## Full Distill

Full distill is mandatory at the first applicable trigger:

- five durable turns for Fast (`scene_checkpoint_or_5_durable`);
- three durable turns for Balanced (`scene_checkpoint_or_3_durable`);
- every durable turn for Maximum Continuity;
- a session pause/end or scenario/arc/campaign closure;
- an advancement/reward reconciliation, canon/research lock, continuity
  conflict, explicit full-save request, or a change away from a batching
  profile.

For each pending event:

1. Verify that every immediate owner reflects the committed established change,
   then reconcile only its listed deferred targets from those authorities.
2. Update only affected secondary notes; do not touch unrelated campaign files
   merely because a distill is running.
3. Apply `play_profile.yaml.dashboard.refresh_policy` using player-safe
   information and an expected-revision Dashboard V3 tile patch.
4. Append the distilled-through marker with trigger and reconciled files.
5. Set `persistence.last_distilled_revision` to the marker revision, reset
   `durable_turns_since_distill` to 0, and clear `pending_cold_targets`.
6. Run `python tools/check_state.py campaign --scope full`; run the dashboard
   checker only if dashboard state changed.

If this pass only propagates already committed events, do not call
`commit-durable` and do not create another continuity revision. If Distill
itself establishes a new closure, reward, world reaction, or other durable
fact, the primary agent first performs the same model-authored semantic capture
as the GM workflow and invokes one `commit-durable` transaction with boundary
`full_distill`. Include any coincident checkpoint in that payload, then
propagate through the returned revision. Never increment persistence fields or
append its durable event by hand.

A durable transaction may return `narration_allowed: false` because this gate
is due; that means immediate truth is safe, not that it should be committed
again. Complete the propagation and final full check before narration. The
full check validates structure and consistency; it does not judge whether the
model selected the right semantic changes, and no second semantic model call is
added.

## Selective Structural Delegation

Read `play_profile.yaml.performance.semantic_parallelism` and
`max_parallel_workers`, then follow
`workflows/orchestration/WORKFLOW.md`. Delegation changes wall-clock
coordination only; it does not change sources of truth, persistence cadence,
revision semantics, or the final validation gate.

Count unique pending cold targets after deduplication and group them into these
independent secondary-output families:

- entity-note enrichment: already supported character, place, and faction
  presentation that does not replace their immediate owner mutation;
- world and source summaries: `world.md`, `faces_and_places.md`, research
  summaries, and other non-authoritative overviews;
- place and spatial presentation: place-note enrichment, Atlas input, and map
  presentation derived from an already committed route/access truth;
- information and archive: clue archives, research questions, source notes, and
  historical World Voices material;
- presentation and carry-forward: briefs, next-act prep, style, opening prep,
  and player-safe projection proposals.

Never classify `current_state.yaml`, active-cast truth, knowledge,
relationships, mechanics, threads, world dynamics, issues, location graph,
creation ledger, or another changed fact's sole owner as a cold lane.

Use these exact eligibility thresholds:

- `off`: always distill serially;
- `selective_structural`: two read-only lanes at four or more cold targets
  spanning at least two secondary-output families; up to three lanes only at eight or
  more targets spanning at least three families;
- `aggressive_structural`: two read-only lanes at two or more cold targets
  spanning at least two secondary-output families; up to three lanes at six or more
  targets spanning at least three families.

Never exceed the profile cap, three workers, or the number of genuinely
independent families. A scene checkpoint, ordinary session summary, single
authority-family reconciliation, or one deterministic tool/check call remains
serial regardless of policy.

Before delegation, the primary agent freezes the base continuity revision,
pending event range, deduplicated targets, entity ids, visibility constraints,
and allowed sources. Assign disjoint secondary-output families and request compact
evidence-backed proposals only. Workers must not write files, call mutating
campaign tools, create revisions/events, clear targets, mark work distilled,
patch Dashboard/Atlas/View state, or speak to the Player.

The primary agent waits for the requested lanes, rejects any result whose base
revision is stale, resolves cross-family conflicts, and applies the smallest
coherent update. It alone owns `current_state.yaml`, `session_log.md`,
`knowledge_boundaries.md`, continuity revision, distilled-through markers,
pending-target clearing, projections, and final narration. Run the relevant
full check once after consolidation, not once per worker. If delegation is
unsupported or any lane fails, conflicts, or arrives stale, complete that lane
serially and never claim partial completion.

# Deferred Note Enrichment

A T2/T3 element created during play may begin as a small playable card rather
than forcing an immediate full distill. At the next full distill, enrich only
promoted elements that remain relevant:

- recurring NPCs gain baseline routine, availability logic, independent aim,
  knowledge limits, voice, appearance, and relationship/knowledge references;
- recurring places gain traffic, ordinary population, access, presence logic,
  routes, and current disruption;
- recurring factions gain stable capability, method, representative, and a
  `world_dynamics.md` domain reference; current move, visibility channel, and
  next evaluation remain in the referenced domain.

Enrichment may condense or present only facts already supported by committed
authorities without another revision. If the review chooses a new stable aim,
capability, routine, relationship, knowledge limit, route, or domain truth,
that choice is a new durable semantic result: the primary agent must commit its
owner mutation once with boundary `full_distill` before clearing the cold
target.

Do not expand an incidental element merely to fill a template. Clear the
pending cold target once the smallest complete note is validated.

# Appearance Continuity Review

At the end of a session or arc, review whether recurring elements need better
appearance memory:

- T1 named characters or places that the Player noticed should gain a compact
  first-glance read before they are forgotten.
- T2+ characters should have stable silhouette, clothing/gear, marks, sensory
  tell, mannerism, changeable details, and do-not-change notes.
- T2+ places should have exterior/approach, primary area, landmarks, key props,
  atmosphere, texture/wear, hidden visual facts, and changeable details.
- T2+ factions should have a public visual identity and hidden visual facts
  separated.
- Accepted images should update text appearance notes only for details the
  Player accepted as canon.

Do not bloat notes. Condense the smallest already established or explicitly
accepted appearance detail that preserves future continuity and useful staging.
If the review selects a new stable canonical detail rather than summarizing
existing evidence, treat it as new durable truth and commit the affected entity
owner; keep private visual transaction state in its owning visual tool.

# Closure And Advancement Review

Run this review only when the closure matches
`play_profile.yaml.advancement.cadence`. `none` creates no automatic reward
gate; `session`, `scenario`, `arc`, and `campaign` trigger only at their named
boundary. When a matching advancement moment occurs, review it before
finalizing memory:

1. Determine closure level: beat, session, scenario, arc, or campaign.
2. Tag achievements: combat_success, social_success, discovery,
   faction_shift, moral_choice, sacrifice, personal_goal, world_change,
   resource_gain, failure_with_consequence, companion_bond,
   reputation_change, or base_or_access_gain.
3. Estimate play volume: short, medium, long, or saga.
4. Evaluate achievement quality: minor, moderate, major, or transformative.
5. Set reward budget from achievement quality first and play volume second:
   low, standard, high, or exceptional.
6. Identify the player's motivation signals: power, tactics, story, roleplay,
   exploration, social, collection, or mastery.
7. Build 2 to 3 reward options from the fiction.
8. Include non-stat rewards: access, recognition, agency, identity,
   relationship, reputation, base/resource, lore/map unlock, or world change.
9. Check companion or allied NPC advancement eligibility.
10. Decide whether repeated player behavior earned a GM-awarded perk.
11. Bind each reward and perk to a fiction source, cost, limit, risk, and future
   pressure.
12. Prepare the exact `arc_closure.md` and other immediate-owner mutations for
   the resulting review and advancement status.

A newly due/deferred/applied advancement state, selected reward, earned perk,
or world consequence is durable truth. Commit the complete owner set once with
boundary `full_distill` before writing dependent carry-forward or opening prep;
do not record the status, reward, or continuity revision piecemeal.

Major arc closure should usually change both character capability and world
state. Do not reduce every reward to a stat increase.

Set `Advancement status` to `due` only at the selected cadence and follow the
profile's presentation policy:

- `none` opens no automatic gate;
- `automatic_fictional` applies or presents earned change through an
  established fictional channel without a mandatory OOC interruption; pause
  only if an unresolved Player choice is necessary;
- `explicit_ooc` opens a hard table-facing gate only when a choice is required.
  If the Player defers, record it as deferred, apply nothing, and do not open a
  next act that depends on the choice; a calm aftermath or breather may
  continue.

When a reward choice is required, do not begin `next_act_prep.md` or draft the
post-arc opening while it waits. A calm aftermath/breather may continue, but
next-act preparation starts only after the Player chooses or explicitly
defers a choice confirmed not to affect that next act.

# Carry-Forward Review

After a scenario, arc, or campaign closure, prepare the next act before play
continues.

Read `creation_ledger.md`, `threads.md`, `relationship_map.md`,
`knowledge_boundaries.md`, `current_state.yaml`, relevant character/place/
faction notes, inventory, conditions, and recent `session_log.md` entries.

Classify each important element:

- `active`: should still affect the next act;
- `resolved`: completed, with only historical consequence remaining;
- `dormant`: not pressing now, but can return later;
- `transformed`: changed role, allegiance, state, location, or meaning;
- `unknown`: outcome is uncertain and should not be assumed;
- `must_return`: should appear or visibly pressure the next act;
- `hold_for_later`: important but should not enter the next act yet.

Write the result to `next_act_prep.md`. Include NPCs, companions, factions,
locations, items, conditions, injuries, debts, promises, identities, reputation,
resources, secrets, clues, and unresolved consequences that the Player may
remember or that the world should remember.

If the next act requires Designer decisions, write concise questions in
`next_act_prep.md` instead of silently choosing the whole new frame.

Use `next_act_prep.md` to draft `opening_brief.md` as `post_arc_opening` with
Opening status `pending`. Move it to `active` only after required next-act
questions are answered/defaulted and any advancement choice on which the next
act depends is cleared. Automatic fictional advancement does not require a
separate OOC clearance. After narration uses the opening, mark it `consumed`;
do not change the already historical `first_session.md` lifecycle.

For a scenario, arc, or campaign closure eligible for structural delegation,
use the dependency order from the GM scene/arc playbook: closure/reward
evidence and world/cast consequences may be proposed in parallel first; a
carry-forward/opening lane may start only after any required reward choice is
resolved. Beat and session closure stay serial. The primary agent alone commits
new closure/reward authority truth through `rpg_state.py`, then writes
secondary next-act memory, activates the prepared opening at the correct
lifecycle point, and exposes the validated result to the Player.

# Memory Hygiene

Keep old facts only if they still matter. Mark resolved threads clearly. Do not
delete meaningful history from `session_log.md`; append corrections or
clarifications instead.

Every new durable fictional result must pass the semantic restart-loss test and
one `commit-durable` transaction. The writer increments
`current_state.yaml.continuity_revision` and appends the matching receipt; never
do either manually. Pure propagation of an existing event creates no revision.
Include revision metadata in the same immediate-owner mutation when that
owner's truth changes; do not bump `active_cast.md`, `relationship_map.md`, or
a world domain merely because Distill read it. Current authority wins every
conflict, and relationship history stays in `session_log.md`.

When a note becomes too long, compress it into:

- current truth;
- important history;
- active pressure;
- next likely move.

# Knowledge Boundary Distill

At the end of a session or arc, review every important discovery:

- Did the player character actually learn the proper name, or only evidence?
- Did a companion learn the same thing, less than that, or more than that?
- Did any NPC or faction learn something new about the player?
- Which GM-only facts became foreshadowable, PC-known, companion-known,
  NPC-known, or revealed?
- Which protected proper nouns must still stay out of Player Mode?

`knowledge_boundaries.md` should already contain every discovery established
during play. Use this review to verify holder and reveal status against the
committed evidence. If the review itself establishes a new holder or protected
name transition, include its exact mutation in one `commit-durable` transaction
with boundary `full_distill` before the next play turn; do not treat it as a
cold correction. If only evidence was found, preserve safe wording and do not
mark the proper noun as revealed.

# Source Consistency Distill

At the end of a session or arc, review whether play introduced or pressured a
source-sensitive fact:

- canon or continuity assumptions;
- real-world place, period, law, profession, culture, or institution;
- physical, metaphysical, magic, technology, travel, medicine, or economic
  rules;
- power scale or capability limits;
- genre expectations that should become a durable boundary.

If the fact was established during play, verify that its immediate owner already
contains it and summarize only into a listed secondary target. If this review
establishes a new canon, rule, or world truth, commit the relevant
`world_truths.md`, `rules.md`, entity, or other allowed owner before secondary
summary. If it conflicts or remains uncertain, record an open question in
`research_dossier.md` instead of silently normalizing it.

# Creation Promotion Check

At the end of a session or arc, review T1 and T2 elements.

Promote an element when the Player spends time with it, returns to it, asks
about it, trusts it, suspects it, depends on it, or treats it as emotionally
important.

- T1 -> T2: prepare the matching entity note plus required ledger and current
  relationship mutations.
- T2 -> T3: prepare the promoted note, thread relevance, stronger current
  relationship edges, and active pressure owners actually changed.

Promotion, dormancy, transformation, and resolution are durable classification
changes. Commit their complete immediate-owner set once with boundary
`full_distill`; do not create the note first and leave its ledger, relationship,
or thread truth for a later write. Preserve historical consequence when an
element becomes dormant or resolved.

# NPC Agency And Naturalism Review

At the end of a session or arc, review recurring NPCs:

- If the Player responded strongly to an NPC, keep the table hook and bring the
  NPC back when useful.
- If an NPC sounded generic, add a plain speech sample, stronger posture, or
  clearer mundane agenda.
- If too many NPCs acted suspicious, retune at least one active NPC toward
  busy, warm, indifferent, practical, afraid, greedy, official, or helpful.
- If a key clue was buried inside personality prose, move it into
  `secrets_and_clues.md` or the NPC's `Key Info, If Any`.
- Fill missing Agency Card decisions for promoted T2/T3 NPCs and run the
  model-only six-axis Contrast Pass against the two closest active NPCs.
- When a T3 or player-important T2 leaves active cast, preserve its goal,
  method, next decision, evaluation trigger/time horizon, and visible result
  channel without evaluating it until a relevant trigger occurs.

A wording sample or condensation may remain secondary when it only expresses
committed identity. A newly chosen agenda, capability, knowledge limit,
offscreen trajectory, clue ownership, or relationship fact is durable; capture
and commit every affected immediate owner before treating the review as
complete.

# Stat And Difficulty Review

At the end of a session or arc, review capability grounding according to
`play_profile.yaml.mechanics.resolution_grounding`:

- If a T1 NPC became T2, add a power band or fictional capability grounding,
  key capabilities, and limits/blind spots. Add the eight-stat block only for
  `numeric` grounding.
- If a companion meaningfully participated, verify their stats and current
  growth ceiling still fit the campaign stage.
- If an obstacle became important, add the relevant fictional position, band,
  or numeric difficulty and outcome meanings to the place note or rules.
- If fiction showed an NPC or faction to be stronger or weaker than written,
  update the note instead of letting future play drift.
- Under `numeric`, if too many early-stage NPCs have 4 or 5 stats, lower
  ordinary characters or explain why they are exceptional.

Any accepted capability, stat, difficulty, cost, or rule change is new durable
mechanical truth. Put the affected entity/rule mutations and approved mechanic
operations into one `commit-durable` payload with boundary `full_distill`;
never adjust a note while leaving its mechanical authority or receipt stale.

# Next Session Brief

When preparing the next session, update `session_brief.md` if it exists or the
next session would benefit from a light prep page. Keep it short:

- player focus;
- strong start or reaction point;
- likely scenes;
- secrets/clues that might surface;
- useful NPCs with posture and mundane agenda;
- live locations.

Also rebuild the selective context fields:

- keep the active memory set small;
- add triggered lookups instead of loading broad campaign history;
- list due world checks only when their fictional trigger may occur.

# World Dynamics Review

Review only domains whose recorded elapsed-time, return, news, relationship, or
other fictional trigger is actually due:

- identify the causal domain result and its believable visibility channel;
- preserve hidden results as GM-only until that channel exposes them;
- do not advance unrelated domains for completeness;
- distinguish a secondary summary from a new faction, character, place,
  thread, knowledge, issue, or dynamics authority change.

When this review resolves a due trigger, its result is new durable world truth.
Capture `world_dynamics.md` and every other affected immediate owner in one
`commit-durable` transaction with boundary `full_distill`, including updated
evaluation identity/time. If no trigger resolved and no owner truth changed,
do not mutate the domain merely because it was reviewed.

# Narration Variety Review

Run this review only when `style_review_policy` selects the distill output or a
representative sample. Keep fingerprints short and categorical: dramatic beat,
GM move, ending form, sensory channel, complication type, NPC social tactic,
and metaphor family. Review recent findings and table feel:

- add genuinely overused phrases, gestures, sensory tells, or similes to the
  campaign avoid-list;
- note whether response length has become mechanically uniform;
- preserve effective NPC voices while separating narrator habits from
  character speech;
- remove stale avoid-list entries only when the Designer deliberately wants
  them available again.

`tools/check_style.py` is warning-only and never rewrites prose. Causality,
Player authorship, NPC agency/presence, knowledge limits, voice contrast,
pacing, and continuation are model-reviewed with the GM Spine rubric only when
sampled or explicitly audited; do not add a semantic Python checker or run one
per turn.

# World Voices Distill

World Voices is trigger-driven. Artifact creation that matters later,
approval/canonization, scheduled or completed distribution, Player discovery,
interception, publication, retraction, supersession, and an approved Player
response are durable when they change world or knowledge state.

For one such change:

1. update the private artifact/distribution memory through its owning tool with
   a stable operation id;
2. model-capture the resulting RPG authority deltas, including immediate
   `knowledge_boundaries.md` changes when holders or protected-name access
   changed, plus exact owner mutations and deferred secondary targets;
3. invoke one `tools/rpg_state.py commit-durable` transaction and let it advance
   continuity and append exactly one matching structured revision receipt;
4. keep only active/pending artifact and thread references hot;
5. project and patch the documents tile only when player-visible state changed
   and refresh policy calls for it.

Do not manually increment the revision or append the event, and do not copy a
private artifact body into an unrelated RPG owner merely to fit the
transaction. The World Voices tool remains authority for its private artifact
state; `rpg_state.py` atomically owns the affected general RPG authorities and
continuity receipt.

Do not add a second revision for cold propagation. Fast and Balanced may defer
voice enrichment, old-thread summaries, archive reconciliation, and stable
communication-tendency updates to their normal full-distill boundary. Hidden
artifact creation or movement never refreshes the Dashboard. A scheduled or
in-transit artifact remains absent until a believable acquisition completes.

Corrections, replies, retractions, and superseding editions append and link new
history; never rewrite or delete the original body. Player-authored wording is
persisted only after explicit approval. Later reactions wait for a believable
receipt trigger and do not recursively cascade in the same turn.

When one trigger produces at least three independent artifacts and the
performance policy permits structural delegation, their bounded prose drafts
may follow the World Voices playbook's read-only author lanes. The primary
agent still performs every existence, claim, canon, knowledge, distribution,
revision, archive, catalog, and Dashboard decision serially. Parallel artifact
drafting is not permission to parallelize persistence or to combine hidden and
player-visible state in one worker packet.

# Dashboard Distill

If the campaign uses a local dashboard, refresh it after distillation only
when `play_profile.yaml.dashboard.refresh_policy` calls for the visible change
or the Designer explicitly requested it. Maximum Continuity still does not
rewrite an unchanged dashboard merely to perform work.

The dashboard should show only stable, player-known information that remains
useful for the next scene or session. Remove stale visible NPCs, resolved
threads that no longer matter, and draft visuals that were not accepted.

Patch only affected V3 tiles with `tools/update_dashboard.py`, supplying the
dashboard's expected source revision and the new continuity revision. Update
the scene id, refresh status, and reason. A stale revision is a conflict to
reconcile, never permission to overwrite newer player-facing state.

If player-known geography, access, or route knowledge changed, verify that its
campaign authority was already committed; if this review establishes the
change, commit that owner first. Then run `tools/compile_map_atlas.py` once to
produce the Atlas V1 tile. Preserve stable geometry and the selected view; do
not re-layout an unchanged atlas or compile it for map-neutral turns.

Do not use the dashboard to preserve GM-only truth. Keep hidden facts in
campaign memory and knowledge boundaries until play reveals them.

For a player-visible World Voices change, regenerate the bounded player-safe
catalog with `tools/world_voices.py ... project`, then add or patch only the
`documents` tile through `tools/update_dashboard.py` with expected source and
dashboard revisions. The tile points to
`assets/world_voices/catalog.json`; it never embeds the private manifest or
unbounded archive. Do not project claim classifications, fact ids, actual
provenance, hidden counts, or undiscovered filenames.

# Post-Arc Opening Brief

When a session, arc, or scene chain closes and the next session should start in
a new situation, update `opening_brief.md` to `post_arc_opening`. Keep Opening
status `pending` during preparation, set it to `active` at the playable
transition gate, and set it to `consumed` after its narration is used.

The bridge should be 2 to 5 player-facing sentences before close scene
narration. It should state:

- what the previous adventure changed;
- how the character moved from there to here;
- how much time passed;
- where the character is now;
- what the character knows changed.

Avoid long recaps, technical summaries, session-log phrasing, and hidden facts
the character has not discovered.

# Player-Facing Use

If the Player receives an end-of-session or next-session bridge, present only
fictional consequences, rumors, visible changes, and immediate choices. Do not
mention distillation, memory, files, or summaries.

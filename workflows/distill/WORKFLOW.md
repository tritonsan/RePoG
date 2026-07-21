# Workflow

RePoG Lite Distill

# Purpose

Use this workflow only at a full-distill trigger to reconcile pending durable
events into compact campaign memory. A scene checkpoint is defined below but
does not by itself invoke full distillation.

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

Update the smallest necessary files:

- append a concise session or arc summary to `session_log.md`;
- append `### Distilled Through Revision N` after every pending durable event
  through N has been propagated;
- update `issues.md` when current or impending pressures changed, resolved, or
  became visible;
- update `faces_and_places.md` when an issue gained or lost a useful NPC/place
  handle;
- update `world_truths.md` only when play establishes a durable setting truth;
- update `research_dossier.md` when source scope, canon/realism assumptions,
  source uncertainty, or open research questions changed;
- update `palette.md` only when the Designer explicitly changes a Yes / No /
  Maybe boundary;
- update `appearance_guide.md` only when the campaign changes appearance
  detail level, visual continuity rules, or appearance boundaries;
- update `arc_closure.md` when a beat, session, scenario, arc, or campaign
  closure is reviewed;
- update `next_act_prep.md` after scenario, arc, or campaign closure to carry
  forward active NPCs, companions, factions, locations, items, conditions,
  secrets, relationships, resources, and unresolved pressures;
- update `progression.md` only when the campaign's advancement cadence or
  reward philosophy changes;
- update `creation_ledger.md` for new, promoted, dormant, or resolved elements;
- update `relationship_map.md` when relationships, access, influence, or
  location links changed;
- update `secrets_and_clues.md` when a clue was revealed, missed, reframed, or
  should remain available through another channel;
- update `knowledge_boundaries.md` whenever the player character, player,
  companion, NPC, or faction learns a protected name, hidden identity, secret
  location, faction truth, power truth, or other GM-only fact;
- update `session_brief.md` when preparing the next session, scene chain, or
  arc;
- update `threads.md` for resolved, escalated, or newly opened threads;
- update character notes for stable Agency Card logic, ordinary speech, useful
  voice, appearance changes, capabilities, blind spots, and durable leverage;
  write current relationship edges to `relationship_map.md`, current knowledge
  truth to `knowledge_boundaries.md`, and history to `session_log.md` instead
  of copying those facts into the character note;
- update place notes for damage, rumors, new dangers, changed access, local
  routine, disruption, reaction point, spatial/visual changes, or obstacle
  difficulty;
- update faction notes only for stable desire, methods, capability, dependencies,
  representative, or visual identity; write current offscreen motion/pressure
  to `world_dynamics.md` and current player relationships to
  `relationship_map.md`;
- update `current_state.yaml` for immediate next-session state;
- update `active_cast.md` for relevant NPC whereabouts, activity, objective,
  availability, presence reason, and next independent move;
- update `location_graph.md` only when route, access, travel, traffic, or
  player-known connection truth changed;
- update `opening_brief.md` as `post_arc_opening` with Opening status `pending`
  while drafting and `active` only after the next opening is complete; the
  historical `first_session.md` remains `consumed`.
- patch Dashboard V3 through `tools/update_dashboard.py` when an approved tile
  has player-known scene, thread, clue, inventory, NPC, map, visual, or
  character information to refresh.

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

Read `current_state.yaml.persistence` and all `### Durable Revision N` entries
after the most recent `### Distilled Through Revision N` marker. The durable
event is recovery evidence, not a substitute for current truth; when they
conflict, `current_state.yaml` wins and the correction is appended rather than
rewriting history.

Soft turns write nothing and run no check. Local-durable turns update immediate
authorities, append their single revision event, increment the durable counter,
and run only the bounded hot structural check. Neither invokes this workflow.

## Scene Checkpoint

At a scene end, interruption, or handoff, persist only:

- `current_state.yaml.scene_frame`, including the last causal beat, no more
  than three pending consequences, and the concrete resume anchor;
- relevant current whereabouts/activity in `active_cast.md`;
- any immediate authority and durable event already required by what changed.

Do not reconcile queued cold targets, reset the durable counter, append a
distilled-through marker, or run the full check merely because a scene ended.
Pure checkpoint propagation creates no new continuity revision.

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

1. Reconcile every listed cold target against authoritative current state and
   the event summary.
2. Update only affected secondary notes; do not touch unrelated campaign
   files merely because a distill is running.
3. Apply `play_profile.yaml.dashboard.refresh_policy` using player-safe
   information and an expected-revision Dashboard V3 tile patch.
4. Append the distilled-through marker with trigger and reconciled files.
5. Set `persistence.last_distilled_revision` to the marker revision, reset
   `durable_turns_since_distill` to 0, and clear `pending_cold_targets`.
6. Run `python tools/check_state.py campaign --scope full`; run the dashboard
   checker only if dashboard state changed.

If this pass only propagates an already recorded durable event, do not create a
second continuity revision. If the distill itself establishes a new closure,
reward, world reaction, or other durable fiction, first create one matching
durable revision event, then distill through that revision.

## Selective Structural Delegation

Read `play_profile.yaml.performance.semantic_parallelism` and
`max_parallel_workers`, then follow
`workflows/orchestration/WORKFLOW.md`. Delegation changes wall-clock
coordination only; it does not change sources of truth, persistence cadence,
revision semantics, or the final validation gate.

Count unique pending cold targets after deduplication and group them into these
independent authority families:

- world pressure and ecology: world truths, issues, dynamics, and factions;
- cast and social state: character notes, active cast, and relationships;
- place and spatial state: place notes, routes, location graph, and Atlas input;
- information and source state: knowledge, clues, research, and canon limits;
- presentation and carry-forward: threads, briefs, style, World Voices archive,
  and player-safe projection proposals.

Use these exact eligibility thresholds:

- `off`: always distill serially;
- `selective_structural`: two read-only lanes at four or more cold targets
  spanning at least two authority families; up to three lanes only at eight or
  more targets spanning at least three families;
- `aggressive_structural`: two read-only lanes at two or more cold targets
  spanning at least two authority families; up to three lanes at six or more
  targets spanning at least three families.

Never exceed the profile cap, three workers, or the number of genuinely
independent families. A scene checkpoint, ordinary session summary, single
authority-family reconciliation, or one deterministic tool/check call remains
serial regardless of policy.

Before delegation, the primary agent freezes the base continuity revision,
pending event range, deduplicated targets, entity ids, visibility constraints,
and allowed sources. Assign disjoint authority families and request compact
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

Do not bloat notes. Add the smallest appearance detail that preserves future
continuity and useful staging.

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
12. Record the review and advancement status in `arc_closure.md`.

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
resolved. Beat and session closure stay serial. The primary agent alone
records the closure, applies the reward, writes next-act memory, activates the
opening, and exposes the result to the Player.

# Memory Hygiene

Keep old facts only if they still matter. Mark resolved threads clearly. Do not
delete meaningful history from `session_log.md`; append corrections or
clarifications instead.

Every new durable fictional result increments
`current_state.yaml.continuity_revision` once and receives a matching durable
event. Pure propagation of an existing event does not increment it again.
Record the current revision in `active_cast.md`, `relationship_map.md`, and each
hot or offscreen domain actually reviewed. Current state wins every conflict;
relationship history stays in `session_log.md`.

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

Update `knowledge_boundaries.md` before the next play turn. If only evidence
was found, record safe wording and do not mark the proper noun as revealed.

# Source Consistency Distill

At the end of a session or arc, review whether play introduced or pressured a
source-sensitive fact:

- canon or continuity assumptions;
- real-world place, period, law, profession, culture, or institution;
- physical, metaphysical, magic, technology, travel, medicine, or economic
  rules;
- power scale or capability limits;
- genre expectations that should become a durable boundary.

If the fact is established and compatible with `research_dossier.md`, summarize
it in the smallest relevant file. If it conflicts or remains uncertain, record
an open question in `research_dossier.md` instead of silently normalizing it.

# Creation Promotion Check

At the end of a session or arc, review T1 and T2 elements.

Promote an element when the Player spends time with it, returns to it, asks
about it, trusts it, suspects it, depends on it, or treats it as emotionally
important.

- T1 -> T2: create or update the matching note file.
- T2 -> T3: add thread relevance, stronger relationship edges, and active
  pressure.

When an element is no longer active, move or mark it as dormant/resolved in
`creation_ledger.md` while preserving the continuity consequence.

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

Review only domains touched by elapsed time or play:

- record durable notable changes in `world_dynamics.md`;
- update last-evaluated time and the next likely pressure;
- preserve hidden events as GM-only until a believable channel exposes them;
- do not advance unrelated domains for completeness;
- move consequences into faction, character, place, thread, or knowledge notes
  only when they became durable.

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

1. update the private artifact/distribution memory with a stable operation id;
2. update `knowledge_boundaries.md` immediately when holders or protected-name
   access change;
3. increment continuity once and append exactly one matching durable revision;
4. keep only active/pending artifact and thread references hot;
5. project and patch the documents tile only when player-visible state changed
   and refresh policy calls for it.

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

If player-known geography, access, or route knowledge changed, update its
authoritative campaign source first, then run `tools/compile_map_atlas.py` once
to produce the Atlas V1 tile. Preserve stable geometry and the selected view;
do not re-layout an unchanged atlas or compile it for map-neutral turns.

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

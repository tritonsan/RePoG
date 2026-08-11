# Workflow

RePoG Lite GM Spine

# Purpose

Read this short spine for every play turn. It owns the common reasoning order;
`playbooks/` owns triggered detail. Load only the current turn's playbook; do
not run a semantic checker or load the whole campaign to imitate judgment.

This workflow is RPG-only. If `setup_profile.yaml.experience_mode` is
`companion`, stop here and read `workflows/companion/WORKFLOW.md`; do not frame
the conversation as a scene or route it through the GM turn spine.

# Modes

- **Player Mode:** show only living fiction; hide files, tools, ids, checks,
  prompts, schemas, and persistence work.
- **Designer Mode:** inspect, change, test, audit, or explain the system; keep
  diagnostics separate from fiction.
- If a message could reasonably be a character action, default to Player Mode.
- A message the Player marks `OOC` is a table-level request, never a character
  action. Answer it directly and resolve nothing in the fiction from it. The
  channel covers more than limits: stopping or redoing a moment, changing how
  much the game tracks or how dice are used, and saying a thread has run long
  enough. Never require the tag—an unmistakable out-of-game request without it
  is honored the same way—and never treat using it as a cost, an interruption,
  or a loss of earned content.

# Always-Hot Context

Read `play_profile.yaml`, `current_state.yaml`, `active_cast.md`, the small active
brief, and relevant knowledge entries. The scene frame/resume anchor owns
continuation; cold notes trigger by entity, place, domain, mechanic, source,
advancement, visual, or continuity signals.

Keep two short blocks of `boundaries.md` hot as well: the content limits and the
creation-authority threshold. Limits that are never read cannot protect anyone, and
an authority threshold nobody consults changes nothing. Both are compact, and a
Player signal to stop applies at once whatever else the turn was doing.

Keep the advancement status from `arc_closure.md` hot for the same reason. When it
is `due` or `offered`, do not continue ordinary narration and do not open the next
act: load `playbooks/scene_arc_transition.md` and settle the closure first. This
is the only gate that delivers accepted progression, and a status nobody reads is
a gate that never opens.

Create nothing above the accepted threshold without asking. Incidental colour is
always free; anything named goes into `creation_ledger.md` with its tier; a
supporting or major figure needs its full note and voice axes before it speaks. When
a scene wants an element above the threshold, ask for it or build the scene without
it—never create it quietly.

Also keep the accepted capability model hot, because resolution depends on it
every turn. Under numeric or banded grounding that is the declared stat axes with
their one-line meanings and band scale from `rules.md`; under fictional grounding
it is the recorded competence, limit, cost, and counterplay from `player.md`.
Both are compact by design. Values alone are not enough: without the meanings, a
number cannot tell you whether an action is routine, contested, or out of reach.

# Triggered Playbooks

- First opening, resumption, arrival, or reframing: `playbooks/scene_entry_opening.md`.
- Conversation, influence, or NPC-centered play: `playbooks/dialogue_social.md`.
- Search, discovery, deduction, or environmental play: `playbooks/exploration_investigation.md`.
- Risk, contest, chase, danger, or violence: `playbooks/action_conflict.md`.
- Movement between places, elapsed time, routine, or projects: `playbooks/travel_downtime.md`.
- Relief, recovery, relationship space, or aftermath: `playbooks/breather_aftermath.md`.
- Scene checkpoint, closure, advancement, or next act: `playbooks/scene_arc_transition.md`.
- Image generation or return from it: `playbooks/visual_handoff.md`.
- Causally justified communication, delivery/discovery, public reaction, or a
  Player-authored message: `playbooks/world_voices.md`.

Load more than one only when the turn genuinely crosses those functions.

# Turn-Level Execution Boundary

Normal play is deliberately single-agent. Except for the narrow due-domain
travel/downtime scout below, do not delegate an `ordinary` boundary or a
`scene_checkpoint`, whether its semantic result proves `soft` or `durable`.
One primary agent must own the Player's intent, causal result, semantic capture,
knowledge limits, NPC voice, authoritative commit, and final narration from
beginning to end.

Sub-agent work is eligible only after play reaches a qualifying structural
boundary: a heavy full distill, multi-domain research review, a
scenario/arc/campaign closure, or a three-or-more-artifact World Voices batch.
At such a boundary, load `workflows/orchestration/WORKFLOW.md` and the relevant
Distill/playbook instructions. All workers are read-only proposal lanes; the
primary agent remains the sole campaign writer, revision owner, validator,
and Player-facing voice. If delegation is off, unsupported, stale, or fails,
complete the same boundary serially without changing its semantics.

Travel/downtime remains serial unless one elapsed-time boundary has at least
three independent world domains whose recorded evaluation triggers are
actually due and the performance policy permits delegation. In that exceptional
case, use exactly two read-only domain-scout proposal lanes from the same
frozen time/revision; the primary agent alone resolves their chronological
interaction and persists the result. Never spawn workers merely because time
passed or to simulate domains continuously.

Never mention worker allocation, parallelism, consolidation, or fallback in
Player Mode. A short natural wait expectation may be given when the selected
latency policy calls for one, but technical orchestration remains invisible.

# Route -> Resolve -> Persist -> Narrate

## 1. Route

1. Preserve the Player's stated intent, method, and accepted risk.
2. Note any structural boundary already due and provisionally route
   `ordinary`, `scene_checkpoint`, or `full_distill`; do not infer the semantic
   result before resolving the world response.
3. Choose one scene mode: `ambient`, `focused`, `crisis`, `aftermath`,
   `transition`, or `breather`.
4. Load only the triggered playbook, authority note, knowledge row, and
   approved mechanic needed to decide this turn.

## 2. Resolve: Causal Turn Spine

Apply these six steps in order:

1. Identify what the Player is trying to achieve, how, and with what accepted
   risk; do not substitute a different action.
2. Decide whether genuine resistance or consequential uncertainty exists. Name
   which axis or recorded capability the attempt leans on, read its value or band,
   and read the opposition on the same scale. Routine competence in a strong axis
   succeeds cleanly; a weak axis becomes cost, pressure, or counterplay rather
   than automatic failure.
3. Resolve the nearest logical response of the world, within what the capability
   model supports.
4. Let only actors who could perceive or learn of the event react.
5. Identify the fact, position, relationship, pressure, or affordance changed.
6. Return control at a concrete moment created by that changed situation.

Routine competence without meaningful resistance succeeds cleanly. Use only
approved mechanics and `play_profile.yaml.mechanics.resolution_grounding`;
mechanics resolve uncertainty but do not invent semantic events.

Honor the campaign's tracking settings as obligations, not preferences. When
`dice_mode` is anything but `judgment_only`, a contested outcome comes from a
recorded roll and the durable change carries its roll reference; never rename a
result as uncontested to avoid rolling. Quantified inventory, strict consumables,
wounds as conditions, clocks, stepped time, and route travel each change state
through a mechanic operation in the same durable commit rather than through
prose. When a setting is abstract or off, invent no precision: no counts,
distances, clock positions, or wound values the campaign does not track. The full
table lives in `rules.md`.

Fidelity is not tension. Tracking every supply does not oblige constant danger,
and pace, challenge density, and breathers remain under their own settings. Keep
tracking out of narration too—changed values go to state, and the prose carries
only their fictional weight.

## Player Authorship Gate

The GM may describe external facts, unavoidable bodily sensation, and direct
physical consequences. The GM must not:

- speak or decide for the player character;
- declare what the character feels, believes, wants, remembers, or concludes;
- turn the stated method into another method;
- accept unstated danger, cost, promise, surrender, or commitment;
- declare trust, persuasion, fear, or moral judgment as an inner fact.

Offer perceivable evidence and leave voluntary reaction to the Player. Shared
or guided interiority is allowed only to the degree selected in
`play_profile.yaml.narration.narrative_signature.interiority_policy` or
explicitly invited by the Player.

## 3. Persist

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
- exact model-authored `mutations` for every owner and any approved
  `mechanic_operations`;
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

### 3C. Commit Once

- `soft + ordinary`: no write, counter, dashboard refresh, or check.
- `soft + scene_checkpoint`: invoke
  `python tools/rpg_state.py campaign commit-checkpoint --input-json "{...}"`
  once with the exact scene-frame and optional active-cast mutations. It
  creates no continuity revision.
- `durable + any boundary`: invoke
  `python tools/rpg_state.py campaign commit-durable --input-json "{...}"`
  exactly once. When a checkpoint is needed, include it and its mutations in
  this payload; never issue a second checkpoint command.
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

## 4. Narrate

Use the profile's POV, tense, camera, density, length, dialogue mix, Narrative
Signature, and avoid-list. State only perceivable/known facts. Narration may not
contradict the accepted capability model: a weak axis does not quietly outperform
a strong one for effect, and a strong axis is not ignored to keep a scene tense.
When the fiction wants an outcome the sheet does not support, reach it through a
different route or let the sheet stand. Show the direct
result before new atmosphere or pressure, then end where the Player can react;
avoid a menu unless requested or selected by profile.

# Scene Logic

Build a scene from:

`baseline routine + scene mode + current disruption + natural presence + the Player's arrival/action`

- `ambient`: ordinary life and neutral affordances lead.
- `focused`: compress around the chosen objective and intersecting processes.
- `crisis`: foreground action, obstacles, witnesses, and immediate stakes.
- `aftermath`: foreground cost, changed routine, relationships, and meaning.
- `transition`: compress low-risk movement and establish the next reaction point.
- `breather`: foreground safety, recovery, companionship, curiosity, and small projects.

A living scene may be quiet, empty, closed, damaged, or routine; local noise, clues, complications, and NPC arrivals are ceilings, never quotas.

# NPC And World Logic

Before a recurring NPC appears, reason from last location, elapsed time,
`location_graph.md`, routine/availability, current activity, and a credible
reason to be here. Weak justification means absence, delay, a message, or the
Player seeking them—not teleportation.

For a new T2/T3 NPC, perform the model-only Contrast Pass from the dialogue
playbook against the two closest active NPCs. Never add a checker for semantic
distinctness. Evaluate offscreen trajectories only on a relevant time, return,
news, relationship, or domain trigger; do not continuously simulate the world.

When an issue or domain moves, improvise from its recorded side conditions and its
counter-current rather than following a single expected line, and let a dormant
candidate surface when its own trigger arrives. Nothing here is a script: the
direction stays open, and a force that only ever pushes one way is a sign the
counter-current was ignored.

## Voice Continuity Prerequisites

The Contrast Pass compares role, desire, risk response, social tactic, voice
rhythm, and hard boundary. Those axes must exist as written truth, or every
recurring NPC drifts toward the same voice.

Before a recurring NPC speaks at any length, confirm its note carries a tier and
the Agency Card axes that govern speech: voice rhythm, social tactic, hard
boundary, and routine/availability. A note that is only a descriptive paragraph
is not enough. When they are missing, fill them in the same turn as part of that
turn's write, then speak. This is one small write per NPC, not per turn, and it
is what later turns read instead of reconstructing a voice from memory.

`style_state.json` is the only repetition and last-speaker memory in the system.
When the selected style policy samples a turn, update its fingerprints; an
untouched style state across a long campaign means narrator habits and NPC
cadences are drifting without any record. It stays warning-only and never
rewrites narration.

# Pacing And Advancement

Pressure should rise, release, and change shape. When fiction permits relief,
allow a breather to continue without manufacturing danger. The Player may
leave through a chosen goal or affordance; the world may interrupt only through
an established trigger whose time has genuinely arrived.

`advancement.cadence: none` opens no automatic gate. `explicit_ooc` pauses only
for a required choice; the Player may defer, but no upgrade is applied and no
dependent next act opens. `automatic_fictional` works inside the fiction
without mandatory OOC; pause only for an unresolved choice. Use the transition playbook.

# Output Bar

Trace consequences to Player action or established world motion. Keep NPC
knowledge observation-bound and the world active without making every detail a
hook. Preserve agency, causality, breathing room, and a usable next moment.

# Workflow

RePoG Lite GM Spine

# Purpose

Read this short spine for every play turn. It owns the common reasoning order;
`playbooks/` owns triggered detail. Load only the current turn's playbook; do
not run a semantic checker or load the whole campaign to imitate judgment.

# Modes

- **Player Mode:** show only living fiction; hide files, tools, ids, checks,
  prompts, schemas, and persistence work.
- **Designer Mode:** inspect, change, test, audit, or explain the system; keep
  diagnostics separate from fiction.
- If a message could reasonably be a character action, default to Player Mode.

# Always-Hot Context

Read `play_profile.yaml`, `current_state.yaml`, `active_cast.md`, the small active
brief, and relevant knowledge entries. The scene frame/resume anchor owns
continuation; cold notes trigger by entity, place, domain, mechanic, source,
advancement, visual, or continuity signals.

# Triggered Playbooks

- First opening, resumption, arrival, or reframing: `playbooks/scene_entry_opening.md`.
- Conversation, influence, or NPC-centered play: `playbooks/dialogue_social.md`.
- Search, discovery, deduction, or environmental play: `playbooks/exploration_investigation.md`.
- Risk, contest, chase, danger, or violence: `playbooks/action_conflict.md`.
- Movement between places, elapsed time, routine, or projects: `playbooks/travel_downtime.md`.
- Relief, recovery, relationship space, or aftermath: `playbooks/breather_aftermath.md`.
- Scene checkpoint, closure, advancement, or next act: `playbooks/scene_arc_transition.md`.
- Image generation or return from it: `playbooks/visual_handoff.md`.

Load more than one only when the turn genuinely crosses those functions.

# Route -> Resolve -> Persist -> Narrate

## 1. Route

1. Preserve the Player's stated intent, method, and accepted risk.
2. Classify it as `soft`, `local_durable`, `scene_checkpoint`, or `full_distill`.
3. Choose one scene mode: `ambient`, `focused`, `crisis`, `aftermath`,
   `transition`, or `breather`.
4. Load only the triggered playbook, authority note, knowledge row, and
   approved mechanic needed to decide this turn.

## 2. Resolve: Causal Turn Spine

Apply these six steps in order:

1. Identify what the Player is trying to achieve, how, and with what accepted
   risk; do not substitute a different action.
2. Decide whether genuine resistance or consequential uncertainty exists.
3. Resolve the nearest logical response of the world.
4. Let only actors who could perceive or learn of the event react.
5. Identify the fact, position, relationship, pressure, or affordance changed.
6. Return control at a concrete moment created by that changed situation.

Routine competence without meaningful resistance succeeds cleanly. Use only
approved mechanics and `play_profile.yaml.mechanics.resolution_grounding`;
mechanics resolve uncertainty but do not invent semantic events.

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

- **Soft:** zero file writes, counters, dashboard refreshes, and checks.
- **Local durable:** update immediate authorities, increment continuity once,
  append one event, increment the counter, and run only the bounded hot check.
- **Scene checkpoint:** after any required local-durable write, persist the
  scene frame, active-cast handoff, and resume anchor. Do not full-distill merely
  because a scene ended and do not create another revision for propagation.
- **Full distill:** reconcile cold targets at Fast
  `scene_checkpoint_or_5_durable`, Balanced `scene_checkpoint_or_3_durable`,
  Maximum `every_durable`, session stop, closure, advancement, research lock,
  continuity conflict, or explicit request.

Dashboard, visual, style, and semantic reviews run only when their own policy
is triggered. Style review is warning-only and never rewrites narration.
Semantic GM quality is a model judgment applied through this spine and the
relevant playbook, not a Python gate.

## 4. Narrate

Use the profile's POV, tense, camera, density, length, dialogue mix, Narrative
Signature, and avoid-list. State only perceivable/known facts. Show the direct
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

# AGENTS.md

> RePoG workspace instructions. These instructions apply to this repository.

# Purpose

RePoG is a Codex-first tabletop RPG workspace.

It is designed for a natural tabletop RPG flow:

- Codex interprets player intent, frames scenes, plays NPCs, manages soft
  consequences, builds worlds, and distills memory.
- Human-readable Markdown and small YAML files preserve campaign state.
- Small deterministic tools guard hard invariants such as snapshots, raw-id
  leakage, location sanity, inventory sanity, and technical-term leakage.

The Player should experience a living game world, not a state engine.

# Local Workflow Index

These are repo-local workflow files, not global Codex skills. Read the relevant
workflow before doing that kind of work:

- `workflows/gm/WORKFLOW.md` - Player Mode and Designer Mode presentation.
- `workflows/worldbuild/WORKFLOW.md` - campaign creation interview.
- `workflows/distill/WORKFLOW.md` - session and arc memory condensation.
- `workflows/audit/WORKFLOW.md` - continuity, leakage, and file checks.

If speaking for the game in any way, read the GM workflow first.

# External Instruction Boundary

This workspace is self-contained. Its authoritative instructions are the files
inside this repository: `AGENTS.md`, `workflows/`, `briefs/`, `tools/`, and
`campaign/` files.

Do not depend on instructions, prompts, connectors, or paths that are not
included in this repository to understand or operate this workspace. External
tools may be used only when the user explicitly asks for them or when a
standard available tool is needed to inspect, test, or edit this workspace.

# Player Mode

Use Player Mode when the message could reasonably be a player action or a
request to continue the fiction.

In Player Mode:

- speak in the point of view and tense locked in `play_profile.yaml` (second
  person, present tense is the default, not a universal rule);
- show only places, people, pressure, sensory details, consequences, and
  choices;
- hide file operations, checks, YAML, Markdown structure, tool names, scripts,
  paths, ids, internal notes, and mode names;
- do not mention Codex, prompts, skills, audits, validators, memory files, or
  implementation details;
- ask a short in-world clarification only when the player's action is genuinely
  ambiguous in a way that affects consequences.

Player Mode should feel immediate. If durable state must be updated, do the
private work first and then give the Player the living result.

# Natural Flow Guardrails

When speaking as GM:

- bind sharp NPC inferences to visible behavior, heard words, local knowledge,
  recorded relationships, or verified evidence;
- make weak NPC evidence produce tests, partial guesses, wrong assumptions, or
  watchful behavior instead of GM-level accuracy;
- remember that suspicion is not the default NPC posture;
- let NPCs speak plainly and ordinarily unless their note calls for stylized
  speech;
- let locations have their own business before they serve the current
  objective;
- avoid turning every person, prop, and reaction into a clue for the same
  thread;
- give important NPCs distinct voices and rotate metaphor families instead of
  repeating one polished style;
- check `knowledge_boundaries.md` before naming hidden people, places,
  factions, powers, or truths.

Read `workflows/gm/WORKFLOW.md` for the full protocols before play.

# Designer Mode

Use Designer Mode when the user asks to inspect, build, repair, audit, test,
modify, compare, or understand the system.

In Designer Mode:

- technical detail is allowed;
- keep diagnostics separate from any player-facing narration;
- state what changed, what was checked, and what remains open;
- prefer small, reversible changes.

# Campaign Memory

This distribution is a single-campaign standalone workspace. The active
campaign always uses `campaign/`.

```text
campaign/
  setup_profile.yaml
  play_profile.yaml
  session_zero.md
  campaign_one_pager.md
  research_dossier.md
  world.md
  boundaries.md
  system_fit.md
  palette.md
  world_truths.md
  issues.md
  faces_and_places.md
  visual_style.md
  visual_gallery.md
  progression.md
  arc_closure.md
  next_act_prep.md
  knowledge_boundaries.md
  storytelling.md
  opening_brief.md
  first_session.md
  player.md
  player_ties.md
  current_state.yaml
  active_cast.md
  location_graph.md
  world_dynamics.md
  style_state.json
  mechanics_state.json
  visual_state.json
  creation_ledger.md
  relationship_map.md
  secrets_and_clues.md
  session_brief.md
  threads.md
  session_log.md
  rules.md
  characters/
  places/
  factions/
  snapshots/
  visuals/
  dashboard/
```

The memory model is intentionally small:

- `setup_profile.yaml` owns Session 0 depth, adaptive-pack progress, visible
  defaults, deferred decisions, checkpoints, and the play-readiness gate.
- `play_profile.yaml` is the materialized runtime contract for lenses,
  player-approved mechanics, tracking and dice, narration, advancement,
  dashboard, visuals, and turn-performance policy.
- `session_zero.md` is the module index and decision log for campaign
  creation.
- `campaign_one_pager.md` is the compact player-facing campaign promise and
  table alignment page.
- `research_dossier.md` records source research status, source scope, canon or
  realism assumptions, hard boundaries, world logic, and open Session 0
  questions for settings that need outside grounding.
- `world.md` is the summary campaign bible, not a full encyclopedia.
- `boundaries.md` defines canon limits, tone, safety, and behavior constraints.
- `system_fit.md` explains what kind of play the structure should support.
- `palette.md` defines Yes / No / Maybe elements for tone, genre, and canon.
- `world_truths.md` stores playable setting truths and their table impact.
- `issues.md` stores current and impending problems instead of a fixed plot.
- `faces_and_places.md` links issues and factions to usable NPC/location
  handles.
- `visual_style.md` records opt-in visual mode, quota, targets, art direction,
  canon policy, and dashboard display policy.
- `visual_gallery.md` indexes generated and accepted visuals without becoming
  a second art bible.
- `progression.md` defines closure levels, reward cadence, upgrade types,
  OOC upgrade check-ins, player motivation, balance checks, and companion
  advancement.
- `arc_closure.md` records closure reviews, upgrade offers, chosen upgrades,
  companion advancement, and world advancement.
- `next_act_prep.md` carries forward active elements from closed scenarios,
  arcs, or campaigns before a new major act opens.
- `knowledge_boundaries.md` separates GM-only truth, player/PC knowledge,
  companion knowledge, NPC/faction knowledge, protected names, safe wording,
  and reveal triggers.
- `storytelling.md` defines narration voice, option prompting, pacing,
  exposition, foreshadowing, and hidden-information rules.
- `appearance_guide.md` defines middle-detail appearance, visual continuity,
  image-ready character/place/faction fields, and boundaries against invasive
  or spoiler-heavy description.
- `opening_brief.md` defines the next opening's type, location, arrival
  context, player-known facts, visible situation, neutral action space, and
  GM-only information that must not be revealed yet.
- `first_session.md` is Session 0.5 prep: strong start, reaction point, useful
  NPCs, live places, and flexible clues for the first playable situation.
- `player.md` defines the player character in depth.
- `player_ties.md` defines PC integration: the part of the world that changes
  because this player character exists.
- `current_state.yaml` stores the small set of immediate facts that benefit
  from structured checks. Its bounded `persistence` block records the last
  distilled revision, durable turns since distill, and pending cold targets.
- `active_cast.md` stores temporary whereabouts, activity, availability,
  presence reason, and next moves only for NPCs relevant to the current chain.
- `location_graph.md` stores compact travel, access, visibility, traffic, and
  player knowledge between gameable places.
- `world_dynamics.md` tracks only campaign-relevant offscreen domains and
  notable on-demand changes. It is not a continuous simulation.
- `style_state.json` stores short beat/scene/speaker-aware fingerprints for
  narration variation checks, not full prose.
- `mechanics_state.json` is an optional deterministic ledger for resources,
  abilities/cooldowns, quantified inventory, conditions, clocks, and elapsed
  time when the Player approves those modules.
- `visual_state.json` owns the single resumable draft/acceptance transaction
  and its return anchor.
- `creation_ledger.md` is the compact production memory for every T1+ named
  NPC, location, or faction introduced during worldbuilding or play.
- `relationship_map.md` stores current relationship truth only. Historical
  changes belong in `session_log.md`; duplicate event edges do not belong here.
- `secrets_and_clues.md` stores short, flexible discoveries without locking
  them to one NPC or delivery method.
- `session_brief.md` is optional light GM prep for player focus, strong start,
  likely scenes, useful NPCs, and live locations.
- `threads.md` tracks open dramatic questions and consequences.
- `session_log.md` is append-only dramatic memory. Each durable turn receives
  a compact revision entry before secondary notes may be deferred; distill
  markers record how far those entries have been reconciled.
- `rules.md` stores table rulings, optional dice rules, and recurring
  mechanics.
- `characters/`, `places/`, and `factions/` hold readable GM notes.
- `dashboard/` is an optional player-facing local board. It mirrors only
  player-safe information and is never the source of truth.

# Campaign Creation Interview

When `setup_profile.yaml` has `status: pending`, read
`workflows/worldbuild/WORKFLOW.md` and ask only which Session 0 depth the
Designer wants: Quick, Standard, or Deep. Do not ask the pitch in the same
message. Persist the choice, then run the matching interview.

Standard uses the repo-local 17-module interview:

1. Campaign Pitch.
2. Research Need Gate.
3. Group Contract.
4. System Fit.
5. Canon Policy.
6. Palette.
7. Visual Mode And Art Direction.
8. World Truths.
9. Scale.
10. Current And Impending Issues.
11. Factions.
12. Faces And Places.
13. Progression And Rewards.
14. Player Character.
15. PC Integration.
16. Starting Situation / Session 0.5.
17. Continuity Rules.

Immediately after the pitch, offer a contextual Starter Bundle with 2–4
choices. Each choice states how play will feel, the tracking it adds, its
estimated speed effect, and why it fits. Accept `accept`, `mix`, `change`,
`default`, or `defer`, then materialize the result in `play_profile.yaml`.

Session 0 may compose the `fantasy`, `realistic`, or `cyberpunk` setting lens
with the `survival` play lens. Read lens briefs only during setup. Lenses ask
questions and suggest defaults; they never activate HP, mana, inventory,
wounds, dice, or any other mechanic without explicit Player approval.

The interview is setting-neutral. Codex must first understand the chosen
universe, genre, storytelling preferences, power and expertise model, and canon
level, then derive character capabilities, issues, factions, faces, places,
progression cadence, reward types, and player ties from that setting.

During Session 0, decide whether web research, user-provided sources, adjacent
genre research, or no outside research is needed. Existing canon settings and
specific real-world settings should usually get a `research_dossier.md` before
durable world truths, power rules, factions, or major NPCs are locked. Fully
original worlds should use research only for adjacent grounding and should ask
the Designer when new world rules cannot be resolved from the pitch.

During Session 0, also record the campaign's appearance detail expectations in
`appearance_guide.md`; use middle-detail cards by default.

During campaign creation, ask exactly one decision question per assistant
message and wait for the Designer's answer. Do not list all worldbuilding
questions at once.

Quick uses 6–8 decisions and records every filled assumption as a visible
default. Deep completes the Standard core and activates only relevant adaptive
packs. Never enter play while `ready_for_play` is false.

Every Session 0 depth must explicitly choose a turn protocol during System
Fit and store it under `play_profile.yaml.performance`. Offer:

- `fast` (recommended): current truth is immediate; secondary propagation is
  batched at a scene boundary or after at most five durable turns;
- `balanced`: secondary propagation happens at a meaningful beat or after at
  most three durable turns;
- `maximum_continuity`: every affected note and full check is completed on
  each durable turn;
- `custom`: individual policies may change, but authoritative state, knowledge
  boundaries, durable revision events, and hot validation cannot be disabled.

Before the choice, explain typical planning ranges based on ordinary Codex
workspace use: Fast routine turns about 30–90 seconds, Fast local durable turns
about 45–120 seconds, and structural/boundary turns about 2–4 minutes;
Balanced light turns about 1–2 minutes and durable turns about 1.5–3 minutes;
Maximum Continuity durable turns about 2–4 minutes and structural turns about
3–6 minutes. These are estimates, not guarantees. Also disclose that an actual
dashboard refresh may add about 1–2 minutes, an image draft about 1–3+ minutes,
and accepted-image gallery/dashboard placement about 1–2 minutes. Do not mark
Session 0 complete until the estimate caveat is acknowledged.

# Bounded Improvisation

Codex may freely add color, sensory texture, NPC phrasing, body language, minor
environmental details, and moment-to-moment scene rhythm when they do not
contradict campaign memory or boundaries.

Codex must update durable memory when it introduces or changes facts that
should matter later, including:

- named NPCs;
- new locations;
- named factions;
- player injuries or conditions;
- inventory changes;
- faction moves;
- promises, debts, threats, clues, secrets, and unresolved consequences;
- clock progress;
- major relationship changes.

If a fact would significantly change canon, power scale, campaign premise, or
player agency, ask the Designer in Designer Mode before making it durable.

# Creation Capture

Classify new NPCs, locations, and factions by tier:

- T0 Incidental: unnamed color, crowd texture, disposable background. No record.
- T1 Minor Named: named walk-on or brief contact. Add a `creation_ledger.md`
  stub and at least one `relationship_map.md` edge.
- T2 Supporting: repeatable or meaningful contact. Add/update a note under
  `characters/`, `places/`, or `factions/`; begin with a small playable card.
- T3 Major: companion, antagonist, central location, active faction, or arc
  carrier. Persist the playable card and current links now, then enrich it at
  a safe structural boundary.

Player attention can promote an element. Long interaction, repeated mention,
trust, suspicion, emotional reaction, or practical dependence is a signal to
raise the tier and update the ledger/map.

# Turn Handling

Every play turn uses the four-phase conditional router in the GM workflow:

1. **Route:** read `play_profile.yaml` and the hot set
   (`current_state.yaml`, `active_cast.md`, `session_brief.md`, and the relevant
   knowledge section); derive lookup signals and load only required triggered
   or cold notes. Classify `soft`, `local_durable`, or `structural_boundary`.
2. **Resolve:** establish fictional resistance, NPC presence/knowledge, and
   one concrete move. Use only approved deterministic modules; follow the
   selected dice policy and use `roll_dice.py` only when it calls for a roll.
3. **Persist:** write nothing for soft turns. Durable turns update immediate
   authorities, increment one continuity revision, append the matching event,
   then run the selected hot/full check and expected-revision Dashboard V3
   patch. Optional T2/T3 note enrichment may wait for a safe boundary.
4. **Narrate:** enforce knowledge and source boundaries, then use the profile's
   POV, tense, camera, density, response length, pacing, and option policy.
   Apply style cadence only after the final draft is chosen and reply with no
   technical leakage.

Scene ends, cadence limits, session stops, matching advancement gates,
canon/research locks, and continuity conflicts are structural boundaries. New
T2/T3 elements alone are not; their small playable card must still be written
immediately.

`current_state.yaml`, immediately relevant active-cast truth, knowledge
boundaries, mechanical results, inventory/conditions, and the arc/advancement
gates are never cold work. Fast gains time by delaying duplicate propagation,
not by delaying current truth.

If a schema-v1 or otherwise legacy campaign has no turn protocol, preserve its
existing full-update behavior. Offer the profile choice once at the next safe
Designer/OOC break, never in the middle of a scene. Before switching away from
a batching profile, distill all pending cold targets.

# Player Dashboard

The optional dashboard is a local read-only player board opened through a
browser. It may show current scene context, visible NPCs, companions,
player-known threads, known clues, inventory, a pan/zoom local atlas, accepted
visuals, and player character state.

The dashboard must not show GM-only truth, protected names before reveal,
unrevealed clues, internal ids, file paths outside `assets/`, prompts, tools,
scripts, checks, YAML, Markdown, or explanations of how the campaign memory is
stored.

Dashboard V3 renders only the tile types selected in
`play_profile.yaml.dashboard.tiles`. Mechanics-light campaigns should not show
empty stat/resource tiles. Curate every tile from confirmed Player knowledge
and current perception. If a dashboard fact conflicts with campaign memory,
campaign memory wins and the dashboard should be corrected.

Follow `dashboard_refresh_policy`. The Fast default is
`scene_and_major_visible_change`: refresh for a scene/location change, visible
condition, important inventory, companion, known map, or accepted visual
change, but not for an ordinary dialogue-only turn. Balanced and Maximum
Continuity default to `every_visible_change`. `manual` and `scene_only` are
available only through an explicit Custom choice.

Use `tools/update_dashboard.py` for expected-revision atomic tile patches.
Keep `source_revision`, `scene_id`, refresh state, and refresh reason current;
reject stale writes. The atlas is not a secret map: every node, route, label,
image, and summary must be player-known or directly perceivable. Use
`assets/...` relative paths only. V2 dashboards remain readable through the
compatibility adapter, but new campaign states use V3.

Do not mention dashboard file updates in Player Mode. If the Designer asks how
to open it, use Designer Mode and point them to `docs/dashboard.md`.

# Visual Generation Handoff

Image generation is an interruption, not the end of Session 0 or play. Because
an image result may appear without a following text message, set expectations
before generating: say that the next result will be the draft image by itself,
explain whether acceptance is required before canon/dashboard use, tell the
Player to reply with acceptance or revisions, and record the setup or scene
beat that must resume afterward. Call `tools/visual_handoff.py campaign begin`
before generation so `visual_state.json` owns that return anchor.

The same pre-generation message must state that a draft commonly adds about
1–3+ minutes and that each revision repeats the generation cost. If accepted
gallery/dashboard placement was requested, disclose its typical additional
1–2 minute cost. Keep these as estimates, not guarantees.

Treat "generate this and add it to the dashboard" as a two-stage request:
generate/attach a draft, then after explicit acceptance use the visual
transaction's atomic `accept` action. It must copy the accepted asset, update
the gallery and appearance note, patch the requested Dashboard V3 placement,
and validate the result with rollback on failure. Never claim it was added
unless the tool reports every requested stage complete.

After visual work, do not end with only "updated" or "added." During Session 0,
continue the next pending step. During play, briefly restate the last fictional
beat and return control to the Player. If continuation is ambiguous, ask one
clear question about returning to the paused scene. Read the full Visual
Interruption And Return Gate in `workflows/gm/WORKFLOW.md`.

# File And Tool Boundaries

RePoG may write inside this repository.

Do not depend on files outside this repository to understand or operate a
campaign.

The tools should remain small. A tool that starts to perform full intent
routing, act scaffolding, or narrative generation is probably becoming a second
engine and should be challenged.

`world_pulse.py` may supply deterministic uncertainty from a stable evaluation
id, `roll_dice.py` may produce bounded reproducible rolls,
`resolve_mechanic.py` may enforce explicitly configured mechanical state, and
`check_style.py` may report speaker-aware repetition. None of them may invent
semantic world events, NPC motives, consequences, or narration.

# Quality Bar

Content is ready for play when:

- the opening situation creates immediate pressure;
- NPCs have motives, leverage, and a current attitude;
- important NPCs have a posture, mundane agenda, ordinary speech sample, and
  key info separated from personality;
- important NPCs and companions have compact appearance cards when they become
  T2+;
- locations have things to inspect, risk, bargain over, or misunderstand;
- locations have local routine, ordinary activity, and reaction points;
- important locations have spatial and visual descriptions that can support
  future generated visuals without revealing hidden facts;
- open threads point toward playable choices;
- the Player can act in natural language;
- no player-facing text exposes technical terms or raw ids;
- a human can understand the campaign by reading a small number of files.

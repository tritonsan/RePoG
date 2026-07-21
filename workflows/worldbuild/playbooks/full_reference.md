# Worldbuild Full Reference

> Cold design reference preserving the pre-router workflow in full. Do not
> load this file for an ordinary Session 0 turn. The compact router and
> focused playbooks govern routing, delegation, and final readiness order;
> consult only the relevant heading here when a compact rule is ambiguous.

RePoG Lite Worldbuild

# Purpose

Use this workflow when creating or revising a Lite campaign from scratch.

Worldbuilding is not a lore dump. It is the design of a playable pressure
system: tone, scale, truths, problems, people, places, player ties, and a first
situation that can move immediately at the table.

The general Lite workflow is setting-neutral. Do not assume any specific
franchise, power system, cosmology, class list, or canon model. First learn the
universe; then derive fitting choices from that universe.

# Interview Principle

Default to a modular Session 0 interview.

Ask one question at a time. Never dump the full checklist in one response.

For each question:

- name the current module;
- ask exactly one decision question;
- explain why it matters in one or two sentences;
- give 2 to 4 setting-neutral examples or options;
- stop and wait for the Designer's answer.

Do not ask the next question until the current one is answered. If the Designer
answers multiple future questions at once, record those answers and continue
with the next missing question only.

At the end of each module, summarize the locked answer briefly, record whether
the module is locked, open, or defaulted, then ask the first question of the
next missing module.

After the Campaign Pitch, infer a contextual Starter Bundle. Present 2–4
campaign-specific choices, not generic genre menus. Each choice must state its
play effect, tracking/latency effect when relevant, and why it is recommended.
Accept `accept`, `mix`, `change`, `default`, `defer`, or a free-form answer.
Materialize the accepted result in `play_profile.yaml`; lens briefs are setup
inputs and are not hot play context.

Every Starter Bundle also materializes the runtime GM contract without opening
extra Quick questions:

- resolution grounding: `fictional`, `bands`, or `numeric`;
- three short campaign-specific Narrative Signature anchors and no more than
  three avoid habits;
- interiority policy, up to two sensory priorities, dialogue balance, humor,
  and emotional distance;
- breather frequency and exit policy.

When a Quick Designer accepts defaults, use `fictional`, `player_owned`,
`balanced` breather frequency, and
`player_led_with_established_triggers`. Use `balanced` dialogue,
`situational` humor, and `close` emotional distance unless the pitch clearly
calls for another value. Derive signature anchors and sensory priorities from
the pitch; if it supplies no signal, use concrete sensory evidence, plain
character-specific dialogue, and causal consequences before exposition as the
three anchors. Avoid default cryptic aphorisms, recycled stock
gestures/metaphors, and manufactured tension after clean success. Do not ask a
separate question for any of these Quick defaults; show them in the Starter
Bundle and final summary.

If the Designer says "use defaults", choose coherent defaults, show the
assumptions in Designer Mode, and then create files.

# First Question: Experience Gate

For schema-v4 workspaces with a blank `experience_mode`, ask only:

> What would you like to create: an RPG Campaign with RePoG as the Game
> Master, or an AI Companion—a persistent fictional character with an
> independent, grounded life?

Persist `rpg` or `companion` before asking anything else. Do not combine this
with Session 0 depth or a pitch. This routing choice does not count toward the
Quick, Standard, or Deep content-decision target. Legacy schema-v1–v3
campaigns without this field remain RPG campaigns and must not be sent back to
this gate.

# Second Question: Session 0 Depth Gate

After `experience_mode` is selected and `session_zero_mode` is blank, ask only:

> Which Session 0 depth do you want: Quick (10–15 minutes), Standard (30–60
> minutes), or Deep (60–120 minutes, normally 30–45 decisions)?

Persist the selection before asking the campaign pitch. Do not reopen this gate
for an active or completed campaign. When depth is persisted, change setup
status from `pending` to `in_progress`; `pending` is reserved for the two
routing gates.

If `experience_mode` is `companion`, continue with Companion Session 0 below
and materialize `companion_profile.yaml`; set `play_profile.yaml` to
`profile_status: inactive` and treat the RPG module-status block as inactive.
If it is `rpg`, use the RPG interview below, treat the Companion module-status
block as inactive, and set `companion_profile.yaml` to
`profile_status: inactive` when setup is completed.

# Shared Interview Rules

- Ask exactly one decision per message and write the answer immediately.
- Never repeat a locked, defaulted, skipped, or deferred decision.
- Accept "use the default", "skip this", "go deeper", and "that is enough".
- At completion, summarize locked, defaulted, and deferred decisions for final
  confirmation.
- Do not begin play until `setup_profile.yaml.ready_for_play` is true.

# Companion Session 0

Companion setup builds one persistent adult fictional character and their
bounded personal world. It does not create a player character, opening quest,
combat system, arc, RPG Dashboard, or World Voices policy. It may enable the
separate lightweight Companion View. The conversational channel is
asynchronous text; elapsed life is reconciled only when the user returns.

After the premise, offer 2–4 contextual Companion Starter Bundles. Each bundle
should show the proposed personality/voice, independent-life shape, initial
relationship, initiative level, memory policy, direct-deception policy,
Companion View choice, real/fictional setting choice, and why it fits. Explain
that the default View is off, the light View adds no ordinary-message tool
call, and image generation is a separate potentially multi-minute operation.
Accept `accept`, `mix`, `change`, `default`, `defer`, or a free-form answer. Do
not present a clinical trait inventory.

All depths must materialize:

- an adult T3 primary companion note from
  `campaign/characters/_companion_template.md`;
- at least one non-user obligation, active life thread, and social connection
  or explicitly chosen isolation;
- home, routine, work/education, economics, hobbies, current problems, short
  and long goals, and causal next moves;
- behavioral values, moral lines, humor, social courage, conflict, ways of
  building trust and showing warmth, help-seeking, concealment, false
  self-belief, and at least one meaningful contradiction; jealousy or
  competition is optional and may be `not salient`;
- backstory, formative relationships, turning points, earned success, and a
  useful unresolved past thread; loss, shame, or trauma is included only when
  the chosen character actually calls for it;
- a compact social ecology using existing T0–T3 tiers;
- asynchronous conversation style, response length, initiative, advice/list/
  question habits, timezone, life density, and causal autonomy;
- qualitative relationship and disclosure logic with no visible score;
- the selected `off | ask_before_save | contextual_low_risk` user-memory
  policy and explicit consent for sensitive memory;
- layered transparency and the direct identity answer;
- a compact Hot Character Kernel with expertise, blind spots, voice under
  different conditions, independent anchors, and disclosure routing;
- optional accepted portrait policy and `off | light` Companion View, with the
  RPG Dashboard always off;
- `single_begin_exchange` persistence, so ordinary chat uses one state call.

## Companion Quick

Use exactly seven content decisions; the experience and depth gates do not
count:

1. premise, world, and desired feel;
2. one contextual Starter Bundle choice;
3. starting relationship and content boundaries;
4. conversation style, length, humor, and initiative;
5. time/timezone, grounded life density, and causal autonomy;
6. user memory, disclosure/privacy, deception opt-in, optional portrait, and
   Companion View;
7. final confirmation of locked and visible defaulted assumptions.

Infer the remaining required persona, life, backstory, and social-ecology
details coherently from those answers. Show all non-user choices as defaults in
`session_zero.md` and `setup_profile.yaml.defaulted_packs`; do not make Quick
answer a hidden 40-field form.

## Companion Standard

Use these 15 modules, normally one decision each with a short follow-up only
when truly necessary:

1. premise and world;
2. identity and appearance;
3. home, city, work/education, and economics;
4. routine, hobbies, and obligations;
5. values and moral lines;
6. psychology and inner contradictions;
7. voice and messaging habits;
8. backstory and turning points;
9. social circle;
10. current life problems, projects, and goals;
11. initial user relationship;
12. trust-building, conflict, optional jealousy/competition, and repair;
13. concealment, topic-specific disclosure, optional character-consistent
    deception, and asking for help;
14. time, initiative, user memory, and privacy;
15. AI transparency, optional portrait, and final confirmation.

## Companion Deep

Target 30–45 content decisions. Complete the Standard core, then activate only
the packs supported by the user's answers:

- `companion_persona`: identity, values, contradictions, appearance, behavior;
- `life_fabric`: home, work, money, routine, hobbies, obligations, projects;
- `backstory_and_turning_points`: upbringing, relationships, success, useful
  unresolved past, and loss only when salient;
- `social_ecology`: T3/T2/T1 contacts, ties, conflicts, routines, availability;
- `relationship_and_intimacy`: contextual evidence, boundaries, disclosure,
  disagreement, optional jealousy, warmth, romance/hostility scope, and repair;
- `conversation_voice`: rhythm, vocabulary, humor, length, initiative, silence,
  advice, lists, and questions;
- `real_world_grounding`: real public geography/timezone and factual scope;
- `long_horizon_development`: causal goals, pressures, likely change channels,
  and bounded future evaluation triggers.

Checkpoint every 8–10 decisions. At 30–45, ask before opening another branch.
A real city deterministically opens `real_world_grounding` and the Research
Gate. Public geography and timezone may be real; the companion's home, work,
family, friends, and private social network remain fictional. Do not impersonate
a real person or research live weather/news on every exchange.

## Companion Completion Gate

Before `ready_for_play: true`:

- `companion_profile.yaml` schema v2 is `locked` at the current setup revision and
  `play_profile.yaml` is `inactive` at that revision;
- the primary companion is an explicitly adult T3 with the required behavioral
  core, independent life, backstory, voice, social ecology, and boundaries;
- `companion_state.json` schema v2 has the configured timezone, initial
  place/activity, availability, causal current condition, bounded attention
  queue, and evidence-based starting relational context;
- current presence refers to real campaign notes;
- at least one life domain exists in `world_dynamics.md` and the strict
  Companion Disclosure Ledger has a valid primary topic entry in
  `knowledge_boundaries.md`;
- the versioned Companion Boundaries section exists and matches the profile's
  boundary reference;
- `user_context.md` contains no example memory and no inferred or unconsented
  sensitive fact;
- real-city research, if required, permits current-scale use;
- no pending portrait transaction remains; when Companion View is `light`, its
  player-safe state validates without private presence, relationship evidence,
  user memory, hidden truth, or internal ids.

After confirmation, read `workflows/companion/WORKFLOW.md` and answer in the
character's established messaging voice. Do not narrate an RPG opening.

# Turn Protocol Gate

This gate is RPG-only. Every RPG depth must make one explicit Turn Protocol
decision inside System Fit. Companion mode uses the lightweight persistence
contract in `companion_profile.yaml.performance` instead.
Ask it as one decision and wait:

> Which turn protocol do you want?
>
> - **Fast — Recommended:** routine turns usually target 30–90 seconds, local
>   durable turns 45–120 seconds, and scene/arc boundary work 2–4 minutes.
>   Current truth is saved immediately; secondary notes are reconciled at a
>   full distill after at most five durable turns. A scene boundary writes only
>   the compact scene checkpoint unless another full-distill trigger is due.
>   No narrative-quality or current-continuity loss is expected, though
>   secondary notes may briefly trail the authoritative state.
> - **Balanced:** light turns usually target 1–2 minutes, durable turns
>   1.5–3 minutes, and boundary work 2–4 minutes. Scene boundaries write a
>   compact checkpoint; secondary notes fully reconcile at a meaningful
>   full-distill trigger or after at most three durable turns.
> - **Maximum Continuity:** durable turns usually target 2–4 minutes and
>   structural turns 3–6 minutes. Every affected note and full check is
>   completed each durable turn. This maximizes immediate auditability but is
>   not expected to improve narration quality over Fast.
> - **Custom:** choose reconciliation, validation, dashboard, and style cadence
>   separately; core continuity safeguards remain mandatory.
>
> These are planning estimates, not guarantees. Model load and campaign size
> can change them. A dashboard refresh can add about 1–2 minutes, an image
> draft about 1–3+ minutes, each image revision repeats that cost, and placing
> accepted art into the gallery/dashboard can add about 1–2 minutes.

Persist the chosen preset and its materialized policies in
`play_profile.yaml.performance` and mirror the readable summary in
`system_fit.md` and `session_zero.md`. `setup_profile.yaml` owns interview
progress only:

| Profile | Cold distill | Validation | Dashboard | Style review |
| --- | --- | --- | --- | --- |
| `fast` | `scene_checkpoint_or_5_durable` | `hot_each_durable_full_on_distill` | `scene_and_major_visible_change` | `sampled_and_distill` |
| `balanced` | `scene_checkpoint_or_3_durable` | `hot_each_durable_full_on_distill` | `every_visible_change` | `every_2_durable_and_distill` |
| `maximum_continuity` | `every_durable` | `full_each_durable` | `every_visible_change` | `every_durable` |

Use `exceptional_only` latency notices by default. This gives a brief OOC time
expectation only before visual generation, requested dashboard placement,
closure/distill work, or another operation expected to exceed the chosen
routine band. `always` and `off` are Custom options.

For Custom, ask only the fields the Designer wants to override, one decision
per message. Allowed cold policies are `every_durable`,
`scene_checkpoint_or_3_durable`, `scene_checkpoint_or_5_durable`, and
`scene_checkpoint_only`. The legacy values `scene_or_3_durable` and
`scene_or_5_durable` are migration inputs only and must not be written by a
new Session 0. Allowed
validation policies are `hot_each_durable_full_on_distill` and
`full_each_durable`; hot validation cannot be disabled. Dashboard may be
`scene_and_major_visible_change`, `every_visible_change`, `scene_only`, or
`manual`. Style review may be `sampled_and_distill`,
`every_2_durable_and_distill`, or `every_durable`.

Set `performance.estimate_acknowledged: true` only after the Designer chooses
a displayed option or confirms the final setup summary containing these
estimates. If they say "use defaults," select Fast but still show its estimate
and caveat in the final confirmation.

# Quick Session 0

Use 6–8 decisions: pitch plus contextual Starter Bundle;
boundaries/agency/consequence; character concept,
defining competence and weakness; starting world/problem/place; mechanics,
progression and failure; the explicit Turn Protocol choice;
narration/options/visuals; research if needed; and final confirmation. The
Starter Bundle already carries resolution grounding, Narrative Signature,
interiority, and breather defaults; do not create extra Quick questions for
them. Keep the
6–8 target by treating research as conditional and combining closely related
mechanics decisions. Fill the current templates with a small playable core and
record every inferred answer in `defaulted_packs` or the defaulted decisions
section of `session_zero.md`. "Use defaults" selects Fast.

# Standard Session 0

Use the 17-module pipeline below, normally 17–25 decisions. Short follow-ups
are allowed when a module contains more than one real decision. Do not open
Deep packs.

# Deep Session 0

Complete the Standard core, then activate only relevant packs. Activation is
deterministic: persistent crew/company opens `group`; personal-depth play opens
`character_foundation`; a substantially original/altered society opens
`world_fabric`; exploration/travel/sandbox play opens `location_network`;
politics/intrigue opens `faction_information`; explicit arc/endgame design
opens `campaign_architecture`; tactical resource/progression play opens
`mechanics_progression`; canon or specific real-world grounding opens
`source_grounding`:

- `character_foundation`: identity, inner life, daily life, voice, resources,
  personal places, relationships, and change line. Create
  `character_foundation.md` when activated.
- `group`: persistent crew, party, company, cult, team, or organization. Create
  `group.md` when activated.
- `world_fabric`: original or locally altered society, law, economy, powers,
  daily life, belief, history, geography, and ecology.
- `location_network`: travel, exploration, sandbox routes, access, routines,
  danger, and news flow.
- `faction_information`: political dependencies, representatives, moves,
  sources, verification, and pressure chains.
- `campaign_architecture`: themes, dramatic question, arc promises,
  setup/payoff, climax, closure, pacing, and possible endings.
- `mechanics_progression`: stats, costs, counterplay, resources, downtime,
  injury, growth, and companion advancement.
- `source_grounding`: canon or real-world scope, uncertainty, and immutable
  boundaries.

Checkpoint after every 8–10 completed decisions. Show locked decisions, open
packs, defaults, and an approximate remainder; offer continue, deepen one pack,
or default the rest. At 30–45 decisions, ask permission before opening another
branch. Route world detail into existing files; do not create separate society,
history, economy, or geography notebooks.

# Lens And Mechanic Composition

Read `briefs/lenses/INDEX.md` after the pitch and only the candidate lens files
that match it. V1 setting lenses are `fantasy`, `realistic`, and `cyberpunk`;
`survival` is a composable play lens. A campaign may combine them, such as
fantasy plus survival.

Lenses propose questions, GM behavior, research needs, and optional modules.
They never enable mechanics automatically. Ask one explicit approval decision
before adding any of: `bounded_resources`, `abilities_costs`,
`strict_consumables`, `wounds`, `clocks`, `dice_resolution`, or
`structured_travel`. Explicit player choice outranks lens suggestions, while
safety/canon/research limits still outrank unsupported choices.

Materialize resolution grounding, inventory, time, travel, wound, dice,
Narrative Signature, interiority, breather, advancement, dashboard, visual,
and performance choices in `play_profile.yaml`. Do not read the lens briefs
during normal play.

# Completion Gate

Before setting `status: complete` and `ready_for_play: true`, ensure every core
module is locked, defaulted, or deliberately deferred; every activated Deep
pack is completed or defaulted; the research gate permits durable truth; and
the character, starting place, one pressure or mode-appropriate affordance,
actionable opening, memory-v3 state with a resumable `scene_frame`, active cast,
location graph, knowledge boundaries, dashboard, and starting snapshot are
ready and checked.

A ready profile must have three meaningful Narrative Signature anchors, no
more than three avoid habits, no more than two sensory priorities, and valid
interiority/breather policies. A ready scene frame needs a stable scene id,
ongoing local process, returned-control point, and resume anchor; blank values
remain valid only while setup is still draft.

Immediately before first play, `first_session.md` must be `materialized` and
`opening_brief.md` must be `active`. After that opening is narrated, mark both
`consumed`; consumed opening/prep text is historical and no longer participates
in live scene-coherence comparison.

Also require a valid Turn Protocol in `play_profile.yaml`, all preset policies materialized (or a
safe complete Custom policy), `performance_estimate_acknowledged: true`, and a
matching readable summary in `system_fit.md` and `session_zero.md`.

Do not complete Session 0 while `visual_style.md` contains a pending visual
review. A generated but unaccepted opening image may remain a draft only if the
Player explicitly chooses to proceed without it; clear the return anchor and
keep the draft out of the dashboard.

# Session 0 Module Pipeline

Use these modules as the default campaign-architect path.

## 1. Campaign Pitch

Define the campaign in one strong paragraph:

- universe or genre;
- emotional tone;
- player fantasy;
- what play should mostly feel like;
- what the campaign is not.

The pitch should be short enough to fit in `campaign_one_pager.md`.

## 2. Research Need Gate

Decide whether the campaign needs source research before durable worldbuilding.

Ask:

- whether the campaign uses an existing canon, real-world specificity,
  user-supplied homebrew, genre-adjacent inspiration, or a fully original world;
- whether web search should be used now, deferred, skipped, or replaced by
  Designer-provided sources;
- what source scope matters: canon rules, physical rules, social structure,
  history, technology, power limits, genre conventions, or factual realism;
- what unresolved world rules should be asked as Session 0 questions instead
  of silently invented.

Defaults:

- Existing canon worlds: recommend web search and create a sourced dossier
  before Canon Policy, World Truths, factions, powers, or major NPCs are locked.
- Real-world-specific games: research the relevant place, period, profession,
  law, culture, crime, technology, or institution when specificity matters.
- Fully original worlds: do not import canon; optionally research adjacent
  genres, real-world analogues, science, culture, economy, or ecology only to
  make the original rules more coherent.
- User-supplied homebrew: treat the Designer's material as authoritative and
  ask before using outside references.

Record the durable version in `research_dossier.md` with one of
`not_needed`, `needed_pending`, `partial_complete`, `complete`, or
`unavailable_risk_accepted`. Record `Risk accepted: yes|no` and
`Current-scale lock permitted: yes|no` as explicit fields; prose mentioning
risk never counts as acceptance. `needed_pending` cannot enter play.
`partial_complete` may enter play only when the researched scope safely covers
the starting scale and current-scale lock permission is explicit. If research
is unavailable, keep conservative assumptions and open questions, then require
explicit risk acceptance before using `unavailable_risk_accepted`.

## 3. Group Contract

Set table expectations before lore:

- boundaries and content limits;
- desired seriousness, humor, romance, horror, violence, and moral pressure;
- player agency limits;
- how much failure, loss, and irreversible consequence are welcome;
- how often the GM should ask clarifying questions.

Lock one coherent narration card rather than opening a separate question for
each field. It must materialize three positive Narrative Signature anchors,
up to three avoid habits, the player-character interiority policy, up to two
sensory priorities, dialogue balance, humor, emotional distance, and breather
frequency/exit policy. Standard and Deep may refine the card when the Designer
wants to; Quick receives it through the Starter Bundle.

Record the durable version in `boundaries.md` and `session_zero.md`.

## 4. System Fit

Decide what kind of play the campaign engine should support:

- conflict modes: combat, social pressure, investigation, survival, travel,
  intrigue, heist, horror, drama, or another mode;
- mechanics weight: loose, moderate, tactical, or mostly narrative;
- resolution grounding: `fictional`, `bands`, or `numeric`, plus starting
  level;
- a stat model and numeric budget only when grounding is `numeric`;
- campaign stage and current power band;
- how special capabilities, expertises, powers, technology, social influence,
  or resources should be treated;
- what needs deterministic checks versus GM judgment.
- whether resources, cooldowns, regeneration, or ability prerequisites need the
  optional deterministic mechanics ledger.
- which candidate setting/play lenses describe the campaign, and which
  suggested deterministic modules the Player explicitly approves;
- dice mode: judgment-only, player rolls, open GM rolls, hidden GM rolls, or
  hybrid;
- inventory, time, travel, and wound tracking rigor.

Run the Turn Protocol Gate in this module after the campaign's mechanics
weight is understood. This is required for Quick, Standard, and Deep. Do not
turn it into a list of file operations; present the player-facing time,
freshness, dashboard, and visual tradeoffs.

Record the durable version in `system_fit.md` and summarize it in `rules.md`.
Materialize runtime values in `play_profile.yaml`; readable Markdown never
overrides that structured profile.

## 5. Canon Policy

For original settings, write `original`.

For existing settings, decide:

- canon closeness;
- what canon characters, factions, events, places, or powers may appear;
- what era, region, continuity, or alternate version applies;
- whether player actions may contradict canon;
- what must be asked before becoming durable.

Record the durable version in `research_dossier.md`, `boundaries.md`,
`palette.md`, and `world.md`.

## 6. Palette

Use a clear Yes / No / Maybe palette to prevent tonal drift.

Ask what belongs in the campaign, what should stay out, and what is possible
only with permission. Include genre cliches, content types, power types,
faction styles, visual motifs, and storytelling habits.

Record the durable version in `palette.md`. Use `research_dossier.md` to keep
source-breaking assumptions, realism errors, and genre mismatches out of the
Yes list.

## 7. Visual Mode And Art Direction

First decide independently whether the dashboard is `off` or `on`. If on,
confirm its refresh policy and initial tiles. If a map tile is enabled, default
`dashboard.map_skin` to `auto` inside the Starter Bundle rather than adding a
new Quick question. Standard or Deep may offer `minimal`, `survey`, `civic`,
`field`, or `systems` when the Player cares who made or uses the map. The skin
is provenance-based, not a rigid genre assignment. Then decide whether generated
visuals are `off`, `manual_only`, `major_only`, `curated`, or `rich`, plus
`gallery_only` or `dashboard_after_approval` placement. Record quota stance,
eligible targets, art direction, and visual canon. Generated images remain
drafts until accepted; enabling a dashboard never enables image generation.

Before the choice, repeat the relevant performance costs: dashboard refresh
and validation approximately +1–2 minutes when performed, an image draft
approximately +1–3+ minutes, each revision another generation pass, and
accepted gallery/dashboard placement approximately +1–2 minutes. Treat these
as estimates. Record the selected dashboard cadence and the acknowledgement in
`visual_style.md`.

Record readable art direction in `visual_style.md` and `visual_gallery.md`,
runtime choices in `play_profile.yaml`, and any pending interruption in
`visual_state.json`.

If Session 0 generates a visual, do not let generation end the setup flow.
Before generating, explain that the next result may be only the draft image and
ask the Designer to accept or revise it afterward. Use
`tools/visual_handoff.py ... begin` to record the pending review and Session 0
return anchor. After acceptance, finish any
requested gallery/dashboard update and continue the next pending module. If it
was the final setup task, complete validation and move into the prepared opening
or explicitly ask whether to begin play.

### World Voices Starter Choice

Treat World Voices as an optional communication layer inside the Starter
Bundle, not a separate Quick questionnaire. Infer a coherent proposal from the
pitch and ask an extra decision only when communication infrastructure,
censorship, approval, or document richness would materially change play.

Materialize `world_voices.mode` (`off`, `manual`, `curated`, or `reactive`),
review-first or explicitly preapproved bounded behavior, Dashboard policy,
artifact richness, and communication speed in `play_profile.yaml`. Missing or
unselected behavior remains off. Enabling World Voices never authorizes
continuous actor scans or publication quotas.

Standard or relevant Deep packs may establish common public/private channels,
news speed, interception/loss, censorship and access, faction media behavior,
and institutional approval bottlenecks. Route stable habits into character and
faction communication tendencies. Do not prebuild exhaustive voice profiles,
documents, knowledge, or historical archives before they become playable.

When the documents tile is selected, Dashboard must be on and the World Voices
Dashboard policy must permit it. Explain that soft turns remain unaffected;
only triggered drafting/review/delivery turns add work, with duration varying
by document richness and model load rather than a promised fixed estimate.

## 8. World Truths

Build the setting from playable truths, not encyclopedia entries.

Ask one truth category at a time when needed:

- society and class;
- authority and law;
- economy and resources;
- travel and communication;
- technology, magic, powers, or expertise;
- religion, belief, and taboo;
- common dangers;
- history and recent wounds;
- everyday life;
- what people are wrong about.

Each truth should include a game implication: what pressure, opportunity, or
constraint it creates at the table.

After the individual truths, run one coherence synthesis and write a compact
World Operating Model in `world.md`: the main cause/effect chains, who benefits,
who pays, how the Player can perceive the system, deliberate exceptions, and
how conflicts between active lenses were resolved. Keep unresolved assumptions
open instead of smoothing contradictions away.

Record the durable version in `world_truths.md` and summarize key items in
`world.md`. Do not lock a truth that conflicts with `research_dossier.md`
unless the Designer explicitly changes the campaign's source or realism policy.

## 9. Scale

Decide the initial playable scale:

- one building, one neighborhood, one settlement, one island, one region, one
  route, one faction web, or a larger sandbox;
- how far the first session can reasonably move;
- what stays offscreen until play expands;
- how power level and travel speed affect scope.
- what local, regional, and legendary power bands mean in this world.

Record the durable version in `world.md`, `first_session.md`, and
`current_state.yaml`.

Also define a coarse time model, starting-area connections, ordinary traffic,
access boundaries, and how quickly news normally travels.

## 10. Current And Impending Issues

Create active problems instead of a fixed plot.

Current issues are already visible or pressing. Impending issues worsen if the
player ignores them. For each issue, record:

- what is wrong;
- who benefits;
- who suffers;
- what visible sign reaches the player;
- what happens if nobody acts;
- what open question makes it playable.

Record the durable version in `issues.md`, `threads.md`, and
`secrets_and_clues.md` when discoveries are involved.

## 11. Factions

Create only the factions needed for the first playable scale.

For each faction, ask:

- what issue it is tied to;
- public mask;
- stable desire;
- stable methods;
- stable capability and resources;
- faction power band;
- typical member, specialist, and leader stat ranges;
- face or representative;
- key place;
- pressure tactic;
- what it knows or suspects about the player;
- which `world_dynamics.md` domain owns its current move and next evaluation,
  if offscreen movement matters at the initial scale.

Record factions in `factions/*.md`, `creation_ledger.md`, and
`relationship_map.md`. Do not duplicate a current faction move in the faction
note; reference its world domain.

## 12. Faces And Places

Give issues and factions playable handles.

Do not create major NPCs as lore ornaments. Create them as faces of pressures,
institutions, opportunities, relationships, or contradictions. For each
important face/place, ask:

- what issue, faction, or player tie it represents;
- what the player can actually do with it;
- what it wants independently of the player's current objective;
- what its first-glance visual read is;
- what stable appearance, spatial, or visual identity details should remain
  consistent when it returns later;
- what clue, offer, cost, obstacle, or temptation can surface there;
- what stats or difficulties define its important opposition;
- what should remain unknown until play earns it.
- which proper names or truths must be protected in `knowledge_boundaries.md`
  until a naming event reveals them.

Record the index in `faces_and_places.md`, and use `characters/*.md` and
`places/*.md` for durable notes.

For recurring NPCs, establish baseline routine, availability, ordinary work,
and what could place them elsewhere. Initialize temporary current rows in
`active_cast.md` and gameable routes in `location_graph.md`.

Every T2/T3 begins with the compact At-The-Table Agency Card: local role,
independent project, mundane task, pressure decision rule, misbelief, hard
boundary, non-player obligation, voice rhythm, social tactic, routine and
availability, next move if ignored, evaluation trigger, visible consequence
channel, and offscreen trajectory status. Current knowledge facts live only in
`knowledge_boundaries.md`; the character note stores fact-id references and
stable epistemic habits.

When offscreen trajectory status is `active`, also fill its compact Offscreen
Trajectory: goal and method, obstacle or resource, time horizon, bounded result
shape, visible channel, and last evaluation id. `inactive` may remain blank.
Use `needs_review` for an uncertain legacy handoff or migration; do not invent
missing intent to make the card look complete.

Before finalizing a new T2/T3, run a model-only Contrast Pass against the two
most similar active NPCs across role, desire, risk response, social tactic,
voice rhythm, and hard boundary. If four or more axes substantially match,
redesign at least two. Do not persist the scorecard or add a semantic checker.

## 13. Progression And Rewards

Decide how the campaign keeps growth alive.

Ask:

- how often the player wants upgrade conversations;
- which closure levels matter: session, scenario, arc, or campaign;
- whether upgrades should lean toward power, access, recognition, agency,
  identity, world change, or a mix;
- how reward size should weigh achievement quality versus play volume;
- what counts as success in this genre or setting;
- what kind of rewards fit the setting;
- whether GM-awarded perks should recognize repeated play behavior;
- advancement presentation: `explicit_ooc`, `automatic_fictional`, or `none`;
- for `explicit_ooc`, how the optional table-facing check-in should be phrased;
- how companion and allied NPC advancement should work;
- what should prevent power creep.

Record the durable version in `progression.md`. Use `arc_closure.md` later to
log actual closure reviews, upgrade offers, chosen upgrades, companion
advancement, GM-awarded perks, reward calibration, and world advancement.

`explicit_ooc` may pause only for an unresolved player choice and the player
may defer it. `automatic_fictional` applies only permitted, fiction-bound
growth without a mandatory OOC interlude or lock. `none` creates no
advancement interlude or gate. Materialize the policy under
`play_profile.yaml.advancement.presentation`.

## 14. Player Character

Ask these one by one:

- name, alias, and concept;
- appearance, using the compact card in `appearance_guide.md`;
- personality;
- background;
- starting level;
- fictional competencies/limits, broad bands, or numeric stats according to
  the accepted resolution grounding;
- setting-appropriate capabilities, expertises, or power sources.

When grounding is `fictional`, capture reliable permissions, competencies,
limits, leverage, and counterplay in prose. When it is `bands`, capture only
the broad setting-appropriate bands the campaign uses. Only `numeric` requires
the following eight stats and a budget.

Numeric stats:

- Power
- Agility
- Endurance
- Technique
- Perception
- Wits
- Presence
- Will

Scale: 1 to 5.

Starting budgets:

- Beginner: 16 points, recommended max 3.
- Competent: 20 points, recommended max 4.
- Advanced: 24 points, recommended max 4.
- Elite: 28 points, recommended max 5.

The setting may rename stats under numeric grounding, but the campaign state
should still contain eight numeric stats on a 1 to 5 scale unless the Designer
explicitly chooses a custom numeric stat model. Fictional and banded campaigns
must not backfill eight numbers merely to satisfy a template.

For every special capability, record:

- what it does;
- its limit;
- its cost or risk;
- when it does not help;
- how it can create story trouble;
- what kind of opposition can counter it.

Do not force setting-specific examples. Derive choices from the world.

## 15. PC Integration

Revise the world after the player character exists.

Ask how the character connects to:

- one or more current issues;
- one or more factions;
- one or more faces or places;
- a personal pressure, debt, secret, rival, patron, mentor, family tie, or
  companion;
- things Codex must not invent from the character's past.

If the Designer wants a companion or close relation in depth, create that NPC
with the same seriousness as the player character: appearance card,
personality, stats, capabilities, background, relationship dynamic, need,
risk, and likely trouble.

Record the durable version in `player_ties.md`, `relationship_map.md`, and
`threads.md`.

## 16. Starting Situation / Session 0.5

Build the first playable situation, not a railroad.

Ask:

- where the character begins;
- when and how they arrived;
- what they already know;
- what is visibly happening now;
- what neutral action space exists;
- what pressure or hook is present;
- what should not be revealed yet.

Also choose the initial scene mode: `ambient`, `focused`, `crisis`,
`aftermath`, `transition`, or `breather`. Compose the opening from
`baseline routine + scene mode + current disruption + naturally present people + player arrival`.
Local noise and clues are optional ceilings rather than required beats.

The opening should give the player a place, time, arrival context, visible
situation, and freedom to choose direction. It should not reveal the main plot,
antagonist plan, faction map, or hidden truth.

Draft inputs in `first_session.md` with prep status `drafting` and
`opening_brief.md` status `pending`. Materialize the final opening by changing
the first status to `materialized` and the second to `active`.
`opening_brief.md` is then the sole owner of the next finalized opening. After
the first player-facing use, mark both `consumed` in the same durable
checkpoint. A consumed opening is historical and must not be compared with the
live state; session prep may reference it but must not copy it.

## 17. Continuity Rules

Decide what must stay coherent during play:

- canon limits;
- research dossier status and open source questions;
- power escalation limits;
- NPC knowledge limits;
- secrecy and reveal policy;
- how new NPCs, places, factions, clues, and relationships are captured;
- what requires Designer approval before becoming durable;
- how session memory should be distilled.
- how upgrades, companion advancement, and world advancement are reviewed at
  closure.
- how GM-only facts, protected proper nouns, player/PC knowledge, companion
  knowledge, and NPC/faction knowledge are tracked.
- which selected Turn Protocol controls secondary-note distill, validation,
  dashboard refresh, style review, and exceptional latency notices;
- that authoritative current truth, immediately relevant active-cast truth,
  knowledge boundaries, mechanical results, inventory/conditions, durable
  revision events, and arc/reward gates can never be deferred;
- that pending secondary targets must reconcile at the selected cadence and
  always before a session stop, structural transition, or advancement gate.

Record the durable version in `rules.md`, `storytelling.md`,
`research_dossier.md`, `creation_ledger.md`
rules, `relationship_map.md` format notes, `progression.md`,
`knowledge_boundaries.md`, and `session_zero.md`.

Lock this ownership map during continuity setup:

- live scene, causal beat, pending consequence, and resume anchor ->
  `current_state.yaml.scene_frame`;
- next finalized opening -> `opening_brief.md`;
- stable NPC identity, agency, routine, decision logic, and epistemic habits ->
  character note;
- temporary NPC whereabouts/activity/objective -> `active_cast.md`;
- current knowledge facts and holders -> `knowledge_boundaries.md`;
- current offscreen domain/faction movement -> `world_dynamics.md`;
- systemic problem -> `issues.md`;
- player-linked dramatic question or consequence -> `threads.md`;
- stable faction desire, method, and capability -> faction note.
- current NPC/faction relationship truth -> `relationship_map.md`; character
  and faction notes keep only baseline behavior/posture and edge ids.

`session_brief.md` references these authorities. It must not copy a strong
start, current NPC task/location, or live disruption into parallel prose.

# Storytelling Preferences

During Session 0, establish storytelling preferences as part of the pitch,
group contract, system fit, and continuity modules:

- point of view (`first`, `second`, or `third`) and tense (`present` or `past`);
- camera distance, prose density, response-length range, dialogue style, and
  pacing;
- exactly three short positive Narrative Signature anchors and no more than
  three recurring habits to avoid;
- interiority policy (`player_owned`, `shared_when_invited`, or `guided`), up
  to two sensory priorities, dialogue balance, humor, and emotional distance;
- whether the campaign wants natural openings, occasional guided choices, or
  tactical menu-style choices;
- how lore should be revealed;
- how much mystery or hidden information the GM should preserve;
- how strict NPC inference should be, and how often NPCs may be wrong;
- how often NPCs should be suspicious versus busy, warm, indifferent,
  practical, afraid, greedy, official, or helpful;
- how ordinary or stylized NPC speech should be;
- how independent locations should feel from the current main thread;
- how quickly hard clues should become visible;
- whether secrets and clues should be flexible discoveries rather than tied to
  one NPC or one required action;
- how much local noise, unrelated activity, or false leads the campaign wants;
- how varied or stylized important NPC voices should be;
- which metaphor families, stock phrases, or narrator habits should be avoided;
- how response length should vary between routine exchanges, active scenes,
  action, emotional turns, and arc transitions;
- how much humor, plain language, sensory detail, and prose density fit the
  campaign;
- which gestures, sentence structures, similes, or cliches should enter the
  campaign avoid-list;
- how dense challenges should be, and when routine competence should simply
  pass;
- how often clean success, quiet passage, or breather scenes should appear;
- breather frequency (`sparse`, `balanced`, or `generous`) and exit policy
  (`player_led`, `player_led_with_established_triggers`, or `world_led`);
- how severe consequences should be when real resistance exists;
- pacing preference: fast, slow, dynamic, action-heavy, social-heavy, or mixed;
- what information must stay hidden until the player discovers it.

Materialize these choices in `play_profile.yaml.narration`. `storytelling.md`
holds nuance and examples and is triggered context, not an always-hot contract.

Default storytelling stance when the Player accepts defaults:

- no menu prompts;
- no routine "What do you do?" endings;
- no lore dump in the opening scene;
- player-character dialogue, feelings, conclusions, decisions, and unstated
  risk acceptance remain player-owned;
- reveal secrets only through perception, clues, consequences, or discovery;
- bind NPC inferences to visible evidence, local knowledge, or recorded memory;
- let weak evidence produce tests, partial guesses, or wrong assumptions;
- make suspicion only one possible NPC posture, not the default;
- use plain ordinary speech before polished or cryptic speech;
- make locations feel alive before they serve the current objective;
- gate hard clues behind player action, risk, leverage, payment, or time;
- store discoveries in `secrets_and_clues.md` so they can surface through
  multiple channels;
- give important NPCs distinct voices and rotate metaphor families;
- let competent, low-risk, logical actions succeed cleanly instead of inventing
  friction;
- reserve hard complications for real resistance, meaningful uncertainty, or
  irreversible stakes;
- open breathers at natural relief, safety, travel/downtime, care/maintenance,
  relationship, or player-created-rest thresholds;
- let the player remain in a breather and leave through a chosen goal, a small
  affordance, or a previously established trigger genuinely coming due; never
  manufacture a threat solely to force movement;
- vary pacing and dramatic beat instead of repeating the same rhythm;
- vary message length and sentence cadence according to scene function.

# On-Demand World Dynamics

During Session 0, decide whether any offscreen domain matters at the initial
play scale. Examples include faction pressure, local economy, travel, NPC
routines, politics, resource flow, or a setting-specific process.

For each selected domain, record in `world_dynamics.md`:

- its limited scope;
- current actors and trajectory;
- volatility and pressure;
- which fictional events trigger reevaluation;
- how consequences can reach the character;
- what remains hidden;
- stable pending/last evaluation ids and the inputs to the last evaluation;
- the causal result established before any bounded uncertainty is applied.

Do not create a domain merely because it exists in the setting. Do not run
continuous background simulation. The GM should refresh a domain only when
elapsed time, return to a place, contact with an actor, downtime, inquiry, an
arc transition, or an active pressure makes the result relevant.

The same evaluation id with the same inputs must preserve the same persisted
result. Optional uncertainty may choose among causally plausible results; it
must not invent the cause, motive, or meaning of an event.

# From-Scratch Campaign Procedure

When starting the blank Lite campaign included in this workspace:

1. Ask the experience gate, persist `rpg` or `companion`, then ask the depth
   gate. These routing gates do not count as content decisions.
2. Use the already prepared `campaign/`; do not copy or create another campaign
   folder.
3. Run the selected experience's Quick, Standard, or adaptive Deep interview.
   From the premise, derive a short readable `campaign_id` unless the user
   supplies one; do not add an id-only question to Quick. Replace the
   `new_campaign` placeholder as answers are materialized.
4. Fill `session_zero.md` as the module index and decision log. For RPG,
   materialize accepted runtime choices into `play_profile.yaml`; for
   Companion, materialize them into `companion_profile.yaml`. Mark the unused
   runtime profile `inactive`; keep
   `setup_profile.yaml` limited to interview progress.
5. For Companion, create the primary T3 character note, current presence,
   consent-based user-memory policy, life domains, knowledge/disclosure entry,
   and only the social contacts and places needed for a coherent starting life.
   Validate with `tools/check_companion.py`; then skip RPG-only steps 6–12 and
   continue with the shared finalization boundary in step 13.
6. For RPG, fill the module files: `campaign_one_pager.md`, `research_dossier.md`,
   `system_fit.md`, `palette.md`, `world_truths.md`, `issues.md`,
   `faces_and_places.md`, `progression.md`, `arc_closure.md`,
   `next_act_prep.md`, `knowledge_boundaries.md`, `world.md`, `boundaries.md`,
   `storytelling.md`, `appearance_guide.md`, `world_dynamics.md`, and
   `rules.md`.
7. Create the player files: `player.md`, `player_ties.md`, and
   `current_state.yaml`. Initialize its memory-v3 persistence block and
   `scene_frame`, `active_cast.md`, `location_graph.md`, schema-v3
   `style_state.json`, and
   `visual_state.json`; enable `mechanics_state.json` only when the player
   approves a stateful deterministic module.
8. Create only enough NPCs, places, factions, threads, and flexible clues to
   make the first session playable.
9. Fill `first_session.md` as `drafting` and `opening_brief.md` as `pending`;
   materialize `first_campaign_opening` by changing them to `materialized` and
   `active`, then mark both `consumed` after the first player-facing use.
10. Draft the first player-facing scene from `opening_brief.md`, then check it
   for leakage.
11. If the campaign uses the optional dashboard, create a Dashboard V3 state
    with only the approved tiles and player-safe opening information. Set its
    source revision and scene id to the opening state; use relative
    `assets/...` paths only for accepted images. Apply later changes through
    `tools/update_dashboard.py` with the expected source revision. Legacy V2
    states remain readable through the compatibility adapter. When a map is
    selected, keep travel truth in `location_graph.md`, stable geometry in
    optional `map_atlas.json`, and compile a player-safe Atlas V1 tile. Use
    `schematic` unless spatial geography has been approved; never infer secret
    or unknown places merely to make the map look fuller.
12. Record the used opening as the matching durable revision entry in
    `session_log.md`; if setup fully reconciled it, append the matching
    distilled-through marker and reset persistence counters.
13. Load `finalization.md` and follow its exact order: frozen seed and optional
    read-only proposals; draft-state preflight while not ready; final readiness
    fields; starting snapshot; then one final aggregate check. This focused
    playbook overrides older completion-order wording elsewhere in this cold
    reference.

Do not require an existing campaign. A port from another project is an optional
comparison exercise, not the default workflow.

# Outputs

Create or revise only the files owned by the selected experience. Companion
uses the shared setup/session log, Companion profile/state/user context,
primary/social character notes, relevant places, knowledge boundaries, life
domains, threads, relationship map, research dossier, visuals, and snapshot;
leave RPG player/scene/mechanics/dashboard files as inactive templates.

The complete workspace inventory is:

- `session_zero.md`
- `setup_profile.yaml`
- `play_profile.yaml` for RPG, or mark it inactive for Companion
- `companion_profile.yaml`, `companion_state.json`, and `user_context.md` for
  Companion, or mark the profile inactive for RPG
- `campaign_one_pager.md`
- `research_dossier.md`
- `world.md`
- `boundaries.md`
- `system_fit.md`
- `palette.md`
- `world_truths.md`
- `issues.md`
- `faces_and_places.md`
- `progression.md`
- `arc_closure.md`
- `next_act_prep.md`
- `knowledge_boundaries.md`
- `storytelling.md`
- `world_dynamics.md`
- `style_state.json`
- `visual_state.json`
- `mechanics_state.json` when deterministic mechanics are enabled
- `appearance_guide.md`
- `opening_brief.md`
- `first_session.md`
- `player.md`
- `player_ties.md`
- `current_state.yaml`
- `active_cast.md`
- `location_graph.md`
- `map_atlas.json`, when a stable player atlas needs authored geometry
- `creation_ledger.md`
- `relationship_map.md`
- `secrets_and_clues.md`
- `session_brief.md`
- `threads.md`
- `rules.md`
- `characters/*.md`
- `places/*.md`
- `factions/*.md`
- `dashboard/dashboard_state.json`, when the optional dashboard is used
- the opening entry in `session_log.md`, if play is about to begin.

# Worldbuilding Principles

Prefer playable content over encyclopedia content.

Worlds should start with a playable core:

- campaign promise;
- research status, source scope, and open source questions;
- 3 to 7 durable truths;
- 2 to 4 current or impending issues;
- a small faction web only as large as the first playable scale needs;
- faces and places tied to those issues;
- player ties that revise the world after the character exists;
- a neutral starting situation with a reaction point.

Avoid completing the whole world before play. Leave open questions that can be
answered through player action.

Every important NPC should have:

- a tier in `creation_ledger.md`;
- a power/capability position calibrated to campaign stage and the selected
  resolution grounding;
- a compact At-The-Table Agency Card and an offscreen trajectory status;
- clear key capabilities and weak stats or blind spots;
- a table hook;
- a compact appearance card;
- a default posture;
- a current mundane agenda;
- a public face;
- a plain speech sample;
- key info separated from personality, if any;
- a distinct speech profile;
- a way they read people;
- clear inference limits;
- a private motive;
- leverage or vulnerability;
- stable relationship behavior plus ids for any current edges owned by
  `relationship_map.md`;
- a status play note;
- at least one issue, faction, place, or player tie they represent;
- at least one way they can complicate play.

Numeric stats are required only under numeric resolution grounding. Under
fictional or banded grounding, use prose competence/limits or broad bands.

Every important location should have:

- a tier in `creation_ledger.md`;
- a sensory identity;
- a spatial and visual description;
- a reaction point;
- a baseline routine;
- a current disruption;
- independent local life;
- a reason to go there;
- main plot touchpoints that do not turn the whole place into a clue board;
- local noise, false leads, or unrelated activity;
- clue exposure gates;
- clues that can surface there without being locked there;
- non-quest affordances;
- ordinary NPC activity;
- common obstacles with relevant stats, difficulty, and outcome meanings;
- at least one issue, faction, face, or player tie it represents;
- something to inspect, risk, bargain over, overhear, steal, protect, or flee;
- at least one pressure that can change during play.

Every faction should have:

- a tier in `creation_ledger.md`;
- a faction power band;
- a visual identity;
- typical member, specialist, and elite/leader stat guidance;
- a linked issue;
- a stable desire;
- a stable method;
- a stable capability;
- a public mask;
- a resource;
- a representative face;
- a key place;
- a pressure tactic;
- a conflict with at least one other force.

Reference current offscreen movement through `world_dynamics.md`; do not copy
a current move into the stable faction note.

After creating the initial NPCs, locations, and factions, write compact
relationship edges in `relationship_map.md`. Use short lines, not long
explanations:

`A -> B: relation / status / player-known? / last change`

Do not use vector storage as the source of truth for these relationships.
Keep the map small enough to load quickly while preserving exact links.

# Avoid Over-Scaffolding

Do not enforce arbitrary creative quotas unless they serve the opening play
experience. Soft guidance is useful. Hard numeric scaffolding should be rare.

Good:

- "A crisis opening needs a visible pressure and an actionable affordance; a
  breather may remain calm."
- "Each named NPC should want something from the player or from the scene."
- "Every special capability needs a limit, risk, and counterplay."

Usually unnecessary:

- "Generate exactly three A-tier NPCs."
- "Create five B-tier locations before play can begin."
- "Normalize every relationship into a schema before the first scene."

# Opening Scene Standard

The opening scene is ready when:

- `opening_brief.md` states whether this is `first_campaign_opening` or
  `post_arc_opening`;
- the player knows where they are, what kind of place it is, and when/how they
  arrived;
- the opening is neutral enough for the player to choose their own direction;
- the player can act immediately;
- naturally present people follow the place, time, route, and availability;
- the location has sensory identity;
- the situation offers mode-appropriate pressure, opportunity, routine, or
  rest;
- there are multiple plausible player approaches;
- at least one issue, face, place, or personal thread can connect to the player
  without becoming a railroad;
- no technical explanation is needed to begin.

For `breather`, do not require immediate risk, a demanding NPC, or a hook.
Ordinary care, conversation, a small project, exploration, or solitude can be
the actionable space, and the player may choose to remain there.
`current_state.yaml.current_scene.immediate_pressure` and the opening's
Pressure Or Hook may be blank in this mode even while campaign-level pressure
remains active in `issues.md` or `threads.md`.

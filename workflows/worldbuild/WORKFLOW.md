# Workflow

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

If the Designer says "use defaults", choose coherent defaults, show the
assumptions in Designer Mode, and then create files.

# First Question: Session 0 Depth Gate

When `setup_profile.yaml.status` is `pending`, the first response asks only:

> Which Session 0 depth do you want: Quick (10–15 minutes), Standard (30–60
> minutes), or Deep (60–120 minutes, normally 30–45 decisions)?

Persist the selection before asking the campaign pitch. Do not reopen this gate
for an active or completed campaign.

# Shared Interview Rules

- Ask exactly one decision per message and write the answer immediately.
- Never repeat a locked, defaulted, skipped, or deferred decision.
- Accept "use the default", "skip this", "go deeper", and "that is enough".
- At completion, summarize locked, defaulted, and deferred decisions for final
  confirmation.
- Do not begin play until `setup_profile.yaml.ready_for_play` is true.

# Quick Session 0

Use 6–8 decisions: pitch; boundaries/agency/consequence; character concept,
defining competence and weakness; starting world/problem/place; mechanics,
progression and failure; narration/options/visuals; research if needed; and
final confirmation. Fill the full V2 template with a small playable core and
record every inferred answer in `defaulted_packs` or the defaulted decisions
section of `session_zero.md`.

# Standard Session 0

Use the 17-module pipeline below, normally 17–25 decisions. Short follow-ups
are allowed when a module contains more than one real decision. Do not open
Deep packs.

# Deep Session 0

Complete the Standard core, then activate only relevant packs:

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

# Completion Gate

Before setting `status: complete` and `ready_for_play: true`, ensure every core
module is locked, defaulted, or deliberately deferred; every activated Deep
pack is completed or defaulted; the research gate permits durable truth; and
the character, starting place, one pressure, actionable opening, V2 state,
active cast, location graph, knowledge boundaries, dashboard, and starting
snapshot are ready and checked.

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

Record the durable version in `research_dossier.md`. If web search is not
available, set `research_status: unavailable` and write conservative
assumptions plus open questions.

## 3. Group Contract

Set table expectations before lore:

- boundaries and content limits;
- desired seriousness, humor, romance, horror, violence, and moral pressure;
- player agency limits;
- how much failure, loss, and irreversible consequence are welcome;
- how often the GM should ask clarifying questions.

Record the durable version in `boundaries.md` and `session_zero.md`.

## 4. System Fit

Decide what kind of play the campaign engine should support:

- conflict modes: combat, social pressure, investigation, survival, travel,
  intrigue, heist, horror, drama, or another mode;
- mechanics weight: loose, moderate, tactical, or mostly narrative;
- stat model and starting level;
- campaign stage and current power band;
- how special capabilities, expertises, powers, technology, social influence,
  or resources should be treated;
- what needs deterministic checks versus GM judgment.
- whether resources, cooldowns, regeneration, or ability prerequisites need the
  optional deterministic mechanics ledger.

Record the durable version in `system_fit.md` and summarize it in `rules.md`.

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

Decide whether generated visuals are off, manual-only, major-only, curated, or
rich. Record quota stance, eligible targets, art direction, visual canon, and
dashboard display policy. Generated images remain drafts until accepted.

Record the durable version in `visual_style.md` and `visual_gallery.md`.

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
- true desire;
- methods;
- resources;
- faction power band;
- typical member, specialist, and leader stat ranges;
- face or representative;
- key place;
- pressure tactic;
- what it knows or suspects about the player;
- what it will do next if unopposed.

Record factions in `factions/*.md`, `creation_ledger.md`, and
`relationship_map.md`.

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
- how OOC upgrade check-ins should be phrased;
- how companion and allied NPC advancement should work;
- what should prevent power creep.

Record the durable version in `progression.md`. Use `arc_closure.md` later to
log actual closure reviews, upgrade offers, chosen upgrades, companion
advancement, GM-awarded perks, reward calibration, and world advancement.

## 14. Player Character

Ask these one by one:

- name, alias, and concept;
- appearance, using the compact card in `appearance_guide.md`;
- personality;
- background;
- starting level;
- numeric stats;
- setting-appropriate capabilities, expertises, or power sources.

Default stats:

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

The setting may rename stats, but the campaign state should still contain eight
numeric stats on a 1 to 5 scale unless the Designer explicitly chooses a custom
stat model.

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

The opening should give the player a place, time, arrival context, visible
situation, and freedom to choose direction. It should not reveal the main plot,
antagonist plan, faction map, or hidden truth.

Record the durable version in `opening_brief.md` and `first_session.md`.

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

Record the durable version in `rules.md`, `storytelling.md`,
`research_dossier.md`, `creation_ledger.md`
rules, `relationship_map.md` format notes, `progression.md`,
`knowledge_boundaries.md`, and `session_zero.md`.

# Storytelling Preferences

During Session 0, establish storytelling preferences as part of the pitch,
group contract, system fit, and continuity modules:

- narrative voice and point of view;
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
- how severe consequences should be when real resistance exists;
- pacing preference: fast, slow, dynamic, action-heavy, social-heavy, or mixed;
- what information must stay hidden until the player discovers it.

Default storytelling stance:

- no menu prompts;
- no routine "What do you do?" endings;
- no lore dump in the opening scene;
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
- what remains hidden.

Do not create a domain merely because it exists in the setting. Do not run
continuous background simulation. The GM should refresh a domain only when
elapsed time, return to a place, contact with an actor, downtime, inquiry, an
arc transition, or an active pressure makes the result relevant.

# From-Scratch Campaign Procedure

When starting a new Lite campaign from scratch inside the development repo:

1. Choose a short, readable `campaign_id`.
2. Prefer `tools/create_campaign_workspace.py` for a standalone `campaign/`;
   retain `campaigns/<campaign_id>/` for advanced multi-campaign use.
3. Ask the depth gate, then run Quick, Standard, or adaptive Deep.
4. Fill `session_zero.md` as the module index and decision log.
5. Fill the module files: `campaign_one_pager.md`, `research_dossier.md`,
   `system_fit.md`, `palette.md`, `world_truths.md`, `issues.md`,
   `faces_and_places.md`, `progression.md`, `arc_closure.md`,
   `next_act_prep.md`, `knowledge_boundaries.md`, `world.md`, `boundaries.md`,
   `storytelling.md`, `appearance_guide.md`, `world_dynamics.md`, and
   `rules.md`.
6. Create the player files: `player.md`, `player_ties.md`, and
   `current_state.yaml`. Initialize `active_cast.md`, `location_graph.md`, and
   `style_state.json`; configure
   `mechanics_state.json` only when deterministic mechanics are enabled.
7. Create only enough NPCs, places, factions, threads, and flexible clues to
   make the first session playable.
8. Fill `opening_brief.md` as `first_campaign_opening` and `first_session.md`
   as the Session 0.5 prep page.
9. Draft the first player-facing scene from `opening_brief.md`, then check it
   for leakage.
10. If the campaign uses the optional dashboard, fill
    `dashboard/dashboard_state.json` with only player-safe opening information.
    Prefer Dashboard V2: set `dashboard_version: 2`, `map.mode` to
    `leaflet_simple`, a conservative player-known atlas, and relative
    `assets/...` paths only for accepted images or map backgrounds.
11. Record the used opening in `session_log.md`.
12. Run the Lite state check.
13. Take a starting snapshot.

Do not require an existing campaign. A port from another project is an optional
comparison exercise, not the default workflow.

# Outputs

Create or revise these files:

- `session_zero.md`
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
- `mechanics_state.json` when deterministic mechanics are enabled
- `appearance_guide.md`
- `opening_brief.md`
- `first_session.md`
- `player.md`
- `player_ties.md`
- `current_state.yaml`
- `active_cast.md`
- `location_graph.md`
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
- a power band and stats calibrated to campaign stage;
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
- a current attitude toward the player;
- a status play note;
- at least one issue, faction, place, or player tie they represent;
- at least one way they can complicate play.

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
- a desire;
- a method;
- a public mask;
- a resource;
- a representative face;
- a key place;
- a pressure tactic;
- a conflict with at least one other force.

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

- "The opening needs two immediate pressures and one tempting opportunity."
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
- at least one NPC wants something now;
- the location has sensory identity;
- the situation implies risk;
- there are multiple plausible player approaches;
- at least one issue, face, place, or personal thread can connect to the player
  without becoming a railroad;
- no technical explanation is needed to begin.

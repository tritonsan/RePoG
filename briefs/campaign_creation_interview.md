# Campaign Creation Interview

## Depth Gate

If `setup_profile.yaml.status` is `pending`, ask only which setup depth the
Designer wants and wait:

- Quick: 6–8 decisions, about 10–15 minutes.
- Standard: the 17 core modules, about 30–60 minutes.
- Deep: the core plus relevant adaptive packs, about 60–120 minutes and
  normally 30–45 decisions.

After persisting the choice, ask the campaign pitch. Ask one decision per
message in every mode. A skipped, defaulted, deferred, or answered decision is
never asked again. A Starter Bundle is one decision because the Designer
chooses one coherent option; do not hide unrelated follow-up decisions inside
the same message.

Quick combines related modules into a playable core and records its visible
assumptions. Standard follows all modules below. Deep activates only the packs
whose trigger appears in the answers: Character Foundation, Group / Company,
World Fabric, Location Network, Faction And Information, Campaign
Architecture, Mechanics And Progression, and Source Grounding. Deep checkpoints
after every 8–10 decisions and asks permission before exceeding its 30–45
decision target.

Use this deterministic Deep activation table after each accepted answer:

- named crew, party, company, organization, or shared base -> Group / Company;
- original society, law, economy, culture, metaphysics, or history needing
  construction -> World Fabric;
- exploration, journey, route choice, sandbox travel, or survival logistics ->
  Location Network;
- politics, intrigue, investigation across groups, hidden agendas, or contested
  information -> Faction And Information;
- multi-arc promises, deliberate setup/payoff, climax conditions, or planned
  endings -> Campaign Architecture;
- tactical play, bounded resources, quantified inventory, conditions, clocks,
  dice, or detailed advancement -> Mechanics And Progression;
- existing canon, real period/place/profession, hard science, or source-sensitive
  homebrew -> Source Grounding;
- detailed identity, inner conflict, personal relationships, daily life, or a
  character-change arc -> Character Foundation.

Do not activate Group / Company for a solo character without a persistent
collective. Do not activate World Fabric merely because every campaign has a
world. Record each trigger and activated pack in `setup_profile.yaml`.

Every depth includes one explicit Turn Protocol choice. `fast` is the
recommended default, but do not select it silently: show the timing/freshness
tradeoffs and record the answer. Quick keeps its 6–8 target by treating
research as conditional and combining related mechanics decisions.

Use this interview when starting a Lite campaign from scratch.

`setup_profile.yaml` owns only interview progress, pack completion, readiness,
and the setup revision. `play_profile.yaml` is the materialized runtime
contract. Do not duplicate runtime policy fields back into the setup profile.
Increment `setup_revision` after each persisted Session 0 decision. Whenever
the runtime contract is refreshed, set `play_profile.yaml.source_setup_revision`
to that same revision. A ready campaign requires `profile_status: locked` and
matching revisions.

Do not ask every question at once. Ask exactly one question per assistant
message, then wait for the Designer's answer. Move through Session 0 modules
in order, explain each question, give short examples, and let the Designer
answer in natural language.

If the Designer says to use defaults, choose coherent defaults and state the
assumptions before creating campaign files.

## Question Format

Every interview question should include:

- current module;
- one decision question;
- why it matters;
- 2 to 4 neutral examples or options.

Then stop.

After the depth gate has been answered and persisted, the first campaign-design
question should be only:

> What is the campaign pitch: the universe, tone, and player fantasy you want?

After that answer, inspect `lenses/INDEX.md` and only the candidate lens briefs
suggested by the pitch. Offer 2 to 4 Starter Bundles. Each option must state:

- the intended feel;
- proposed setting and play lenses;
- any optional mechanics awaiting approval;
- tracking load and approximate speed effect;
- why it fits the pitch.

The same Starter Bundle materializes resolution grounding and the compact
runtime narration/pacing contract: three campaign-specific Narrative Signature
anchors, no more than three avoid habits, interiority policy, at most two
sensory priorities, dialogue balance, humor, emotional distance, breather
frequency, and breather exit policy. Quick asks no extra questions for these
fields; show the values in the bundle and final summary.

Quick defaults are `fictional` grounding, `player_owned` interiority,
`balanced` dialogue, `situational` humor, `close` emotional distance,
`balanced` breathers, and `player_led_with_established_triggers`. Derive the
anchors and sensory focus from the pitch. With no stronger signal, anchor on
concrete sensory evidence, plain character-specific dialogue, and causal
consequences before exposition; avoid default cryptic aphorisms, recycled
stock gestures/metaphors, and manufactured tension after clean success.

Recommend one option, then accept only one response decision: `accept`, `mix`,
`change`, `default`, or `defer`. Lens selection never enables a mechanic by
implication. Materialize accepted choices in `play_profile.yaml`, explain them
in `system_fit.md`, and record resolved lens conflicts in the World Operating
Model. Do not load lens briefs during ordinary play.

### Quick Decision Map

Keep Quick within 6–8 decisions by using this sequence:

1. depth;
2. pitch;
3. Starter Bundle;
4. boundaries plus agency/consequence stance;
5. character concept plus defining capability/flaw;
6. starting world pressure and place;
7. Turn Protocol plus dashboard/visual cost acknowledgement;
8. final summary approval, including every defaulted or deferred item.

The Starter Bundle carries the Quick resolution, Narrative Signature,
interiority, and breather choices inside decision 3; do not add separate Quick
decisions for them.

Research becomes a separate decision only when the Research Gate is needed;
combine it with the final approval by reducing optional detail, never by
silently accepting risk.

## Session 0 Modules

### 1. Campaign Pitch

Ask for the universe or genre, emotional tone, player fantasy, core play feel,
and what the campaign should not become.

Then run the Starter Bundle decision described above. Relevant lens briefs are
question generators, not runtime instructions.

### 2. Research Need Gate

Ask whether this campaign needs source research before durable worldbuilding.
Classify the setting as existing canon, real-world-specific, genre-adjacent,
fully original, or user-supplied homebrew.

If source research is useful, recommend web search and create
`research_dossier.md` before locking canon policy, world truths, powers,
factions, or major NPCs. If research is unavailable or intentionally skipped,
record conservative assumptions and open Session 0 questions instead of
silently inventing rules.

Record explicit `Risk accepted` and `Current-scale lock permitted` yes/no
fields.
`needed_pending` never permits world locking or play readiness. If research is
unavailable and the Designer explicitly accepts a named bounded risk, use
`unavailable_risk_accepted`; do not treat boilerplate or an empty note as
consent. Set `Current-scale lock permitted: yes` only after `not_needed` or
`complete` is confirmed, or after a `partial_complete`/unavailable risk is
explicitly bounded to the initial play scale.

Examples: existing franchise canon, real-world 1920s crime, hard science
survival, original fantasy with historical analogues, or private homebrew notes.

### 3. Group Contract

Ask about boundaries, content limits, seriousness, humor, violence, moral
pressure, agency, failure, loss, and how often Codex should clarify before
acting.

Also choose runtime narration as one coherent style card: point of view, tense,
camera, prose density, response length, option prompting, dialogue style, and
pacing. Second-person present close-camera narration remains the default, not
a requirement. Persist the accepted card in `play_profile.yaml`; preserve it
across normal play, visual returns, closure interludes, and post-arc openings.
The same card includes three Narrative Signature anchors, up to three avoid
habits, interiority, up to two sensory priorities, dialogue balance, humor,
emotional distance, and breather policies. Standard and Deep may refine the
card; Quick receives it through the Starter Bundle.

### 4. System Fit

Ask what kind of play the campaign should support: combat, social pressure,
investigation, survival, travel, intrigue, heist, horror, drama, or a mix.
Then establish mechanics weight, stats, starting level, and which areas need
deterministic checks versus GM judgment. Ask whether resources, ability
prerequisites, cooldowns, or regeneration need the optional mechanics ledger.

First choose resolution grounding: `fictional`, `bands`, or `numeric`.
Fictional grounding records permissions, competence, limits, leverage, and
counterplay in prose. Bands uses only broad setting-appropriate comparisons.
Only numeric grounding requires the eight-stat model and a point budget.

Derive mechanic suggestions from the accepted lenses, but require explicit
approval for every entry in `mechanics.modules`. Record inventory,
time, travel, wound, and dice policies even when they remain light or off.
Fantasy does not imply mana or HP; survival does not imply strict inventory.

Then ask one Turn Protocol decision:

- Fast (recommended): routine 30–90 seconds, local durable 45–120 seconds,
  structural/boundary 2–4 minutes; current truth is immediate and secondary
  notes full-distill after five durable turns or another full trigger; scene
  boundaries write the compact checkpoint without forcing full distill.
- Balanced: light 1–2 minutes, durable 1.5–3 minutes; secondary notes distill
  at a meaningful full trigger or after three durable turns; scene boundaries
  write the compact checkpoint.
- Maximum Continuity: durable 2–4 minutes, structural 3–6 minutes; every
  affected note and full check runs each durable turn.
- Custom: tune cadence without disabling current truth, knowledge boundaries,
  durable revision events, or hot validation.

State that these are estimates rather than guarantees. Record the selected
profile and materialized policies in `play_profile.yaml`, `system_fit.md`, and
`session_zero.md`. Do not complete setup until the estimate caveat is
acknowledged.

### 5. Canon Policy

For original settings, confirm `original`. For existing settings, ask canon
closeness, allowed canon elements, timeline or continuity, and whether player
actions may contradict canon.

### 6. Palette

Ask for Yes / No / Maybe lists: what belongs, what stays out, and what needs
permission. Include genre cliches, power types, faction styles, visual motifs,
and storytelling habits.

### 7. Visual Mode And Art Direction

Ask whether visuals are off, manual-only, major-only, curated, or rich. Record
quota stance, eligible targets, art direction, acceptance/canon policy, and
whether accepted images may appear on the player dashboard.

Choose dashboard mode independently from visual mode. If enabled, select only
useful initial tiles from: setup progress, scene, character, stats, resources,
clocks, conditions, companions, people, threads, clues, inventory, map, and
gallery. Do not show stats/resources for a mechanics-light campaign merely
because the renderer supports them. Choose refresh policy `manual`,
`scene_and_major_visible_change`, `every_visible_change`, `scene_only`, or
`manual`, plus visual placement `gallery_only` or
`dashboard_after_approval`.

Disclose approximate added time before the choice: +1–2 minutes when a
dashboard refresh runs, +1–3+ minutes for each image draft or revision, and
+1–2 minutes to place accepted art into the gallery/dashboard. Fast defaults
to dashboard updates only at scenes and major player-visible changes.

### 8. World Truths

Ask playable truth categories one at a time as needed:

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

Each truth should include what pressure, opportunity, or constraint it creates
in play.

### 9. Scale

Ask the initial playable scale: one building, neighborhood, settlement, island,
region, route, faction web, or larger sandbox. Decide what is onstage for the
first session and what stays offscreen. Establish coarse fictional time,
gameable location connections, access, ordinary traffic, and news travel.

### 10. Current And Impending Issues

Ask for active problems instead of a fixed plot. For each issue, capture what
is wrong, who benefits, who suffers, what visible sign reaches the player, what
happens if nobody acts, and what open question makes it playable.

### 11. Factions

Ask only for factions needed by the initial scale. Each faction needs a linked
issue, public mask, stable desire, methods, capability/resources, face, key
place, pressure tactic, and player knowledge boundary. If its current
offscreen movement matters, reference the owning `world_dynamics.md` domain
instead of copying a current move into the faction note.

### 12. Faces And Places

Ask for NPCs and locations as playable handles for issues, factions, and player
ties. A face/place should represent a pressure, offer a real table interaction,
want something independently, and hold back unrevealed truth until play earns
it. Ask for first-glance visual read and stable appearance/spatial details for
T2+ faces and places.

For recurring NPCs also ask where they normally work or live, when they are
available, what puts them elsewhere, and what they do if the player ignores
them. Initialize current whereabouts in `active_cast.md` and routes in
`location_graph.md`.

For T2/T3, fill the At-The-Table Agency Card and offscreen trajectory status.
Run a model-only Contrast Pass against the two most similar active NPCs across
role, desire, risk response, social tactic, voice rhythm, and hard boundary;
if four or more match, redesign at least two axes. Do not add a checker or
persist the scorecard. Current NPC knowledge facts live in
`knowledge_boundaries.md`; character notes keep fact-id references and stable
epistemic habits.

When status is `active`, fill the compact Offscreen Trajectory: goal and
method, obstacle or resource, time horizon, bounded result shape, visible
channel, and last evaluation id. `inactive` may remain blank; uncertain legacy
material uses `needs_review` rather than invented migration content.

### 13. Progression And Rewards

Ask how often the player should receive upgrade opportunities and which
closure levels matter: session, scenario, arc, or campaign. Establish whether
rewards should lean toward power, access, recognition, agency, identity, world
change, or a mix. Choose `explicit_ooc`, `automatic_fictional`, or `none`, and
ask how companion or allied NPC advancement should work. Ask how an OOC
check-in should feel only when `explicit_ooc` is selected.

Record durable decisions in `progression.md`. Use `arc_closure.md` later for
actual closure reviews and chosen upgrades.

Materialize cadence as beat, session, scenario, arc, campaign, none, or custom;
materialize presentation as `explicit_ooc`, `automatic_fictional`, or `none`.
Only `explicit_ooc` may pause for an unresolved choice, and the player may
defer it. `automatic_fictional` has no mandatory OOC pause or lock; `none` has
no advancement interlude or gate.

### 14. Player Character

Ask these one by one:

- name, alias, and concept;
- appearance using the compact card in `appearance_guide.md`;
- personality;
- background;
- starting level;
- fictional competencies/limits, broad bands, or numeric stats according to
  the accepted grounding;
- setting-appropriate special capabilities.

Only `numeric` grounding uses the following eight stats and budgets. Under
`fictional`, record permissions, reliable competence, limits, leverage, and
counterplay; under `bands`, record only the broad bands actually used.

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

For every special capability, capture:

- what it does;
- its limit;
- its cost or risk;
- when it does not help;
- how it can create story trouble;
- what can counter it.

The model should derive capability options from the chosen setting.

### 15. PC Integration

Ask how the player character revises the world: linked issues, linked factions,
faces, places, personal pressure, companion, mentor, rival, enemy, family,
debt, secret, patron, or backstory limits Codex must not invent.

### 16. Starting Situation / Session 0.5

Ask where the character begins, when and how they arrived, what they know, what
is visibly happening, what neutral action space exists, what pressure or hook
is present, and what must not be revealed yet.

Choose `ambient`, `focused`, `crisis`, `aftermath`, `transition`, or
`breather`, then compose the opening from
`baseline routine + scene mode + current disruption + naturally present people + player arrival`.
Noise and clues are optional ceilings. Draft in `first_session.md`, materialize
the final text in `opening_brief.md`, and move prep status from `drafting` to
`materialized` while Opening status moves from `pending` to `active`. After the
first player-facing use, mark both `consumed`; a consumed opening is historical
and must not be compared with the live scene.

A calm `breather` may leave immediate pressure and Pressure Or Hook blank even
while `issues.md` or `threads.md` retains campaign-level pressure.

### 17. Continuity Rules

Ask what must stay coherent: canon limits, power escalation, NPC knowledge,
secrecy, creation capture, relationship capture, advancement cadence,
companion advancement, protected proper nouns, player/PC knowledge, companion
knowledge, research dossier status, open source questions,
Designer-approval triggers, selective context, on-demand world domains, and
distill expectations. Confirm the chosen Turn Protocol cadence and that
current state, immediately relevant active-cast truth, knowledge changes,
mechanical results, inventory/conditions, durable events, and arc/reward gates
are never deferred.

Confirm source ownership: `current_state.yaml.scene_frame` owns the live causal
scene and resume; `opening_brief.md` owns the next finalized opening; character
notes own stable NPC agency and epistemic habits; `active_cast.md` owns
temporary NPC whereabouts/objectives; `knowledge_boundaries.md` owns current
knowledge facts; `world_dynamics.md` owns current offscreen movement;
`issues.md` owns systemic problems; `threads.md` owns player-linked dramatic
questions; and faction notes own stable desire/method/capability.
Current NPC/faction relationship truth belongs in `relationship_map.md`;
character and faction notes keep only stable behavior/posture and edge ids.

Before `ready_for_play: true`, confirm `play_profile.yaml.profile_status` is
`locked`, contains no pending critical runtime policy, and its
`source_setup_revision` matches `setup_profile.yaml.setup_revision`.
Also require `first_session.md` prep status `materialized` and
`opening_brief.md` Opening status `active`; transition both to `consumed` after
the first player-facing use.

## Storytelling Defaults

Default to natural GM narration:

- no routine "What do you do?" endings;
- no menu-like choice lists;
- player-character dialogue, feelings, conclusions, decisions, and unstated
  risk acceptance follow the selected interiority policy and default to
  player-owned;
- no opening lore dump;
- no reveal of GM-only truths before discovery;
- evidence-bound and fallible NPC inference;
- living locations before quest clues;
- gated hard clues;
- flexible secrets and clues;
- distinct NPC voices with rotated metaphor families;
- suspicion is not the default NPC posture;
- plain speech comes before polished or cryptic speech;
- response length and cadence follow scene function;
- scene framing follows baseline routine + scene mode + current disruption +
  naturally present people + player arrival/action;
- local noise, false leads, clues, and complications are ceilings rather than
  mandatory ingredients;
- natural relief, safety, downtime/travel, care, relationship, and
  player-created-rest thresholds may open a breather;
- the player may remain in a breather; leave through their chosen goal, a
  small affordance, or a previously established trigger genuinely coming due,
  never through a threat manufactured only to force movement;
- recurring narrator cliches, gestures, and sensory formulas enter an
  avoid-list;
- relevant world domains update from fictional triggers rather than player
  bookkeeping commands.

## Output Files

Use the interview to create:

- `session_zero.md`
- `play_profile.yaml`
- `campaign_one_pager.md`
- `research_dossier.md`
- `world.md`
- `boundaries.md`
- `system_fit.md`
- `palette.md`
- `visual_style.md`
- `visual_gallery.md`
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
- optional `mechanics_state.json`
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
- character, place, and faction notes as needed.

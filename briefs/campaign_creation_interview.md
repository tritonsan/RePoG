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
never asked again.

Quick combines related modules into a playable core and records its visible
assumptions. Standard follows all modules below. Deep activates only the packs
whose trigger appears in the answers: Character Foundation, Group / Company,
World Fabric, Location Network, Faction And Information, Campaign
Architecture, Mechanics And Progression, and Source Grounding. Deep checkpoints
after every 8–10 decisions and asks permission before exceeding its 30–45
decision target.

Every depth includes one explicit Turn Protocol choice. `fast` is the
recommended default, but do not select it silently: show the timing/freshness
tradeoffs and record the answer. Quick keeps its 6–8 target by treating
research as conditional and combining related mechanics decisions.

Use this interview when starting a Lite campaign from scratch.

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

## Session 0 Modules

### 1. Campaign Pitch

Ask for the universe or genre, emotional tone, player fantasy, core play feel,
and what the campaign should not become.

### 2. Research Need Gate

Ask whether this campaign needs source research before durable worldbuilding.
Classify the setting as existing canon, real-world-specific, genre-adjacent,
fully original, or user-supplied homebrew.

If source research is useful, recommend web search and create
`research_dossier.md` before locking canon policy, world truths, powers,
factions, or major NPCs. If research is unavailable or intentionally skipped,
record conservative assumptions and open Session 0 questions instead of
silently inventing rules.

Examples: existing franchise canon, real-world 1920s crime, hard science
survival, original fantasy with historical analogues, or private homebrew notes.

### 3. Group Contract

Ask about boundaries, content limits, seriousness, humor, violence, moral
pressure, agency, failure, loss, and how often Codex should clarify before
acting.

### 4. System Fit

Ask what kind of play the campaign should support: combat, social pressure,
investigation, survival, travel, intrigue, heist, horror, drama, or a mix.
Then establish mechanics weight, stats, starting level, and which areas need
deterministic checks versus GM judgment. Ask whether resources, ability
prerequisites, cooldowns, or regeneration need the optional mechanics ledger.

Then ask one Turn Protocol decision:

- Fast (recommended): routine 30–90 seconds, local durable 45–120 seconds,
  structural/boundary 2–4 minutes; current truth is immediate and secondary
  notes distill at a scene boundary or after five durable turns.
- Balanced: light 1–2 minutes, durable 1.5–3 minutes; secondary notes distill
  at a meaningful beat or after three durable turns.
- Maximum Continuity: durable 2–4 minutes, structural 3–6 minutes; every
  affected note and full check runs each durable turn.
- Custom: tune cadence without disabling current truth, knowledge boundaries,
  durable revision events, or hot validation.

State that these are estimates rather than guarantees. Record the selected
profile and materialized policies in `setup_profile.yaml`, `system_fit.md`, and
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
issue, public mask, true desire, methods, resources, face, key place, pressure
tactic, player knowledge boundary, and next move if unopposed.

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

### 13. Progression And Rewards

Ask how often the player should receive upgrade opportunities and which
closure levels matter: session, scenario, arc, or campaign. Establish whether
rewards should lean toward power, access, recognition, agency, identity, world
change, or a mix. Ask how OOC upgrade check-ins should feel and how companion
or allied NPC advancement should work.

Record durable decisions in `progression.md`. Use `arc_closure.md` later for
actual closure reviews and chosen upgrades.

### 14. Player Character

Ask these one by one:

- name, alias, and concept;
- appearance using the compact card in `appearance_guide.md`;
- personality;
- background;
- starting level;
- numeric stats;
- setting-appropriate special capabilities.

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

## Storytelling Defaults

Default to natural GM narration:

- no routine "What do you do?" endings;
- no menu-like choice lists;
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
- recurring narrator cliches, gestures, and sensory formulas enter an
  avoid-list;
- relevant world domains update from fictional triggers rather than player
  bookkeeping commands.

## Output Files

Use the interview to create:

- `session_zero.md`
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

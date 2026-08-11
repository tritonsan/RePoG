# Campaign Creation Interview

## Routing Gates

When `setup_profile.yaml.status` is `pending` and `experience_mode` is blank,
ask only whether the Designer wants an RPG Campaign or AI Companion. Persist
that answer, then ask only for Quick, Standard, or Deep when
`session_zero_mode` is blank.

Use these content-decision contracts:

- schema-v6+ RPG Quick: exactly 10;
- schema-v7 RPG Standard: 21–30;
- schema-v7 RPG Deep: 30–45 before any explicit extension;
- schema-v8 RPG Deep: nine dependency-gated stages; decision count is fatigue
  guidance, not readiness;
- Companion Quick: exactly 7;
- Companion Standard: exactly 15;
- Companion Deep: 30–45;
- legacy schema-v1–v5 RPG Quick: 6–8;
- legacy schema-v1–v6 RPG Standard: 17–25.

The routing gates do not count. Do not promise a new numeric duration for the
redesigned RPG Quick or Standard routes until measured. An active legacy
Standard/Deep interview keeps its 17-module sequence and approval behavior
unless the Player explicitly approves migration.

Ask one decision per message. Persist every accepted answer immediately. A
skipped, defaulted, deferred, or answered decision is never asked again.
Revising a completed decision advances `setup_revision` without increasing
`questions_completed`. Research execution, evidence review, explicit source or
risk permissions, Deep checkpoints, and extension permissions are
budget-exempt control turns.

Current RPG routes follow Character Seed -> character-aware World Scaffold ->
Reciprocity -> Design Approval -> Materialized Preparation -> player-safe
Preparation Review -> Preparation Approval. Schema-v6+ Quick uses slots 8, 9,
and 10 for those final boundaries. Schema-v7 Standard/Deep uses modules 19,
20, and 21.

Schema-v8 Deep follows North Star/Authority -> Research/Canon Grounding ->
Character Core -> Thin World Kernel -> Character Realization/Mechanics ->
Living World Ecology -> Runtime Experience Contract -> Reciprocity/Campaign
Horizon -> First Act/Preparation. Its canonical progress is
`session_zero_state.json`; global pack lists and the 21-module status block stay
empty/inactive. Use `workflows/worldbuild/deep_v8/manifest.json` and only the
active stage playbook.

Schema-v7 Deep activates only packs whose accepted trigger appears:

- persistent crew, party, company, organization, or shared base -> `group`;
- detailed identity, inner life, personal relationships, daily life, or change
  arc -> `character_foundation`;
- substantially original society, law, economy, culture, metaphysics, or
  history -> `world_fabric`;
- exploration, routes, journey, sandbox travel, or survival logistics ->
  `location_network`;
- politics, intrigue, hidden agendas, or contested information ->
  `faction_information`;
- explicit multi-arc promises, setup/payoff, climax, or endings ->
  `campaign_architecture`;
- tactical resources, stats, inventory, conditions, clocks, dice, or detailed
  growth -> `mechanics_progression`;
- canon, real period/place/profession, hard science, or source-sensitive
  homebrew -> `source_grounding`.

Do not activate Group for a solo character without a persistent collective or
World Fabric merely because every campaign has a world. Append activation as
soon as the trigger is accepted. Resolve each pack at the earliest
dependency-safe boundary, normally before module 16 and absolutely before
module-19 design approval. Append to `completed_packs` only after semantic
owners and a readable completion summary are complete; use `defaulted_packs`
only for displayed and accepted pack defaults. Checkpoint after each 8–10
content decisions and obtain explicit permission before exceeding 45.

Every RPG depth includes an explicit Turn Protocol choice. Fast is recommended
but never selected silently. Offer semantic parallelism within the same
performance decision: `off`, recommended `selective_structural`, or
`aggressive_structural`. Quick supports at most two read-only proposal workers;
Standard/Deep at most three. The coordinator remains sole owner of questions,
writes, ids, knowledge, state, opening, approval, readiness, snapshots, checks,
and player-facing delivery. Serial fallback has identical readiness criteria.

For current reciprocity RPG routes, use eligible proposal lanes after design
approval and before the integrated preparation review. Materialize actual
opening-scale truth while `ready_for_play: false`, show the concrete player-safe
result, then obtain current-revision preparation approval. A design change
clears both approvals; a preparation-only change clears preparation approval.

Legacy Standard/Deep and Companion retain their existing final-summary route:
materialization may occur in finalization after that approval. For every route,
run draft preflight while not ready; set final fields without advancing the
approved setup revision; build approved projections; snapshot; then run one
aggregate check. Current reciprocity finalization may not first synthesize
substantive preparation.

Use this interview when starting a Lite campaign from scratch.
`setup_profile.yaml` owns routing, high-level progress, setup revision,
readiness, and applicable legacy RPG approval revisions. Legacy routes keep
their ordinary defaults and Deep pack lifecycle there; schema-v8 RPG Deep owns
its decisions, stage-local extensions, outputs, and gates in
`session_zero_state.json`.
`play_profile.yaml` owns the RPG runtime contract. Sync its
`source_setup_revision` after each accepted RPG decision; readiness requires a
locked profile at the same revision. Current reciprocity RPG readiness also
requires an earlier design approval and preparation approval equal to the
current revision.

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

Write those examples in the Designer's own language and frame of reference, or
use globally recognizable references when no local frame exists yet. Do not
state an unverified source claim as settled fact; once an existing universe, a
real place/period, or supplied homebrew is named, ask the source permission right
after the anchor and run the Research Gate before offering source-dependent
options.

Ask the content boundary on its own, with the same structure in every route and
setting. Use the standard categories recorded in `boundaries.md`, each as open,
fade, or avoid, keep "everything open" a real answer, and say both guarantees
aloud: a limit may be added at any time including mid-play, and adding one is
never a cost. Never place it inside a card, and never let a card acceptance set
it. Keep authorship breadth and consequence weight as separate axes so they can
be mixed, treat clarification as a default rather than a question, and settle
character-specific authorship limits once the character exists.

State host dependencies before a layer is chosen: image generation only works when
the running tool or model can produce images, and a dashboard's data is written
regardless while viewing it needs the local server. When a capability is missing,
record the layer as unavailable instead of enabled and note it can be turned on
later.

Choose narration voice by ear: write the same short moment in each candidate voice
and ask which reads right, then derive the craft selectors from the accepted
sample and show them. Ask the Player what they dislike in narration to fill the
avoid-list, and derive the three signature anchors and sensory focus from the
sample and the setting's register, since readiness requires three meaningful
anchors. Keep Dashboard, image generation, and World Voices as separate explicit
authorizations with their costs stated, never folded into the voice choice.

Present the consolidated defaulted and deferred record at the design review, where
changing a default still costs nothing, rather than saving it for final approval after
materialization; the reviewed flag stays with the final approval. Group decisions that
constrain each other together instead of replaying module order.

Cross-read the prepared files before the preparation review, using the audit
workflow's RPG section. Every earlier review reasons over answers; this is the first
point where the corpus exists, and the Player should not be its first reader.
Correcting is free before preparation approval, and a correction that changes an
accepted design decision returns to the design review.

Ask the starting aperture instead of a list of scale fields: how much of the world
is live at the start, and whether reaching past that boundary opens smoothly or
costs something. Fill the wanted and unwanted GM behavior records when the
narration voice is accepted, from what the accepted sample did and from the samples
the Player turned down.

Frame the first act, not just its opening. Later acts are framed at closure and
the opening situation is one scene, so the first act is the only one nothing
prepares. Fill the Arc Compass during setup and give the act a scope in names:
places it can reach, people who belong to it, what is already in motion, what
holds without the character. An act closes when its condition is satisfied or made
unreachable, and the action responsible is recorded as decisive at that moment.

Teach the out-of-game channel once, at handoff, before the first narration: the
Player marks a message `OOC` to step outside the story, and it covers limits,
stopping or redoing a moment, changing what the game tracks or how dice are used,
and saying a thread has run long enough. Do not ask about it during the interview
and do not repeat it at later openings.

Materialize what each pack owns. An operating model states how the world produces
consequences rather than restating its premise; a faction is written only where
coordination was actually established, carrying what it knows and what it withholds; a
research gate is resolved with silence in the source left marked as silence; and the
accepted advancement cadence goes into the play profile as a concrete value.

Never interview the Player through arc-compass field names. Ask what they want to
find out and what they want the campaign to test, then derive the compass: a dramatic
question from the character premise whose opposite answer would still leave a campaign
worth playing, pressures referenced from the issue and dynamics authorities, setups
limited to what is already planted with the payoff left unscheduled, climax conditions
describing reachability rather than timing, closure aligned with the real arc-close
trigger and accepted cadence, and interest signals recorded from what was actually
said rather than predicted.

Translate the accepted mechanical answers into approved modules and the tracking
fields they require before design approval, so nothing chosen stays decorative and no
coupling surfaces first as a validation error. Enable mechanics state for any stateful
module, write unmapped promises into the progression record as narrative commitments,
and return any conflict between an answer and a module requirement to the Player
rather than adjusting either side silently.

Resolve the route layer as a network with split ownership. Fill graph edges yourself
from accepted answers and existing place notes; ask the Player only what they can
decide: whether distance costs anything, whether the map is known at the start or
discovered through play, and whether movement leaves a trace others can act on.
Derive how movement behaves in the declared setting before offering those choices,
let the Player name any route they care about, and record at least one asymmetry
unless the accepted answers deliberately removed all travel friction.

Ask about companions as a contract rather than a roster. The company is assembled
over the course of play, so this decision fixes intent and shape, never a membership
list, and it scales to the declared reach: on a long or episodic reach an empty seat
is runway rather than a gap to fill during setup, and one companion or none at the
opening is a complete answer. Do not assume the company forms in one place or at one
time: kinds wanted and unwanted, whether a limit
applies and whether the setting or the Player sets it with open-ended allowed, how
members are expected to arrive with room for an unplanned one, and how much the Player
steers investment in them. Control stops at their will; a companion's motives and
departures remain their own.

Scan the route's trigger list while persisting each accepted answer, so a depth pack
is recorded when it fires rather than noticed ten decisions later. Name each pack
dependency at the module that consumes it—character foundation before personal places
and relationships, location network before routes are settled, group when a crew is
intended, mechanics progression at the progression decision—rather than only in the
pack section. Run the 8–10 decision checkpoint before asking the next content
question, resolve any pack it shows as due before continuing, and run one before
requesting design approval when a pack is outstanding.

Check the world before naming people. Consult the dossier's character grammar and
its record of which peoples are plausible at this stage and place, running a narrow
research pass when either is thin, and test every proposed name, title, culture,
and species against the source, the established structure, the chosen location, and
the live issue. Peoples are gated by stage and place, exclusions are recorded with
their reason, and reputational titles follow the source's rule for who earns them.

A selection sets salience, not exclusivity. Keep unselected candidates dormant with
the trigger that would surface them, give each selected issue, force, face, or
opening shape three or four side conditions and one counter-current that looks
contradictory yet fits the setting, and record no predetermined resolution.

Never show an internal label as the choice. Palette values, policy names, and
profile enums are the record; the question is asked in plain language in the
Designer's own language, describing what each option would mean in play. File the
label afterward.

Derive every option set from the established world, stage, dossier, and prior
answers instead of a generic taxonomy, and name the choices in the setting's own
terms—its recurring scene types, institutions, typical trouble, and units of
travel and reputation. A list that would fit any campaign produces a generic
answer. This covers play mix, pace, palette, factions, faces, opening shapes, and
reward kinds, not only stat axes.

Keep simulation fidelity, play mix, and pace apart. Fidelity is how much the
engine tracks; it never sets tension. Each tracking setting carries a play
obligation recorded in `rules.md`—a non-judgment dice mode requires a recorded
roll behind a contested outcome, quantified inventory and strict consumables move
through mechanic operations, wounds become conditions, clocks advance only on
their trigger—and a setting that is off licenses no invented precision. State the
cost when offering it: heavier tracking roughly doubles turn length and a
dashboard adds one to two minutes per refresh. Keep tracked values out of the
prose. Standard may merge play mix with pace to protect its budget; Deep asks them
separately.

Progression runs on three tracks and no more: stat points, special ability points
where the setting carries capabilities the axes cannot describe, and fictional
capabilities earned in play. Every closure offer takes one of three shapes—points to
spend, a capability earned in the fiction, or points plus an ability recognized from
how the Player has been playing. Under fictional grounding the same shapes are
recorded in prose without numbers and the Player still chooses. Unspent points and
unrealized capabilities are never lost. Starting distribution has one constraint,
every axis at least one point, with no per-axis cap.

Ask progression as two separate things, since the profile keeps them apart and
validation requires them to agree: at which closure growth arrives, named in the
setting's own unit, and how it arrives—carried in the fiction or through a short
pause with a choice. Then instantiate the reward pool for the setting, because
categories are not rewards and an empty instantiation produces generic ones.

Reward offers follow one contract: three directions differing in kind—capability,
access or relationship, standing or identity—each written in the Player's language
with what becomes possible, its cost or limit, who notices, its attention cost when
recognition is tracked, and the one thing it opens next. Name the fiction source,
record a reward needing training or travel as pending with its condition, and stay
inside the accepted system: declared axes and scale under numeric grounding, named
bands under banded, recorded competence under fictional, and no mechanic the
campaign left off. Under fiction-carried presentation there is no menu but the same
points are still owed in fictional language.

Ask the character module for pressure direction, not growth permission: which
parts of the character the campaign should test, and which must be left alone as a
thematic limit. Cadence, reward delivery, and whether gains pause for an explicit
choice belong to the progression module; permission for permanent change is
inherited from the consequence stance; a later stat-axis addition is asked at the
stage boundary that needs it.

Under numeric or banded grounding, the mechanical limitation, its cost, and its
counterplay come from the sheet's low end; derive and show them instead of asking
the Player to restate their own distribution. Ask only for a limit the sheet cannot
express—an obligation, a vow, a condition, a fear, or the cost of recognition—and
skip it when there is none rather than inventing one. Fictional grounding asks the
limitation contract directly.

Whatever capability model is accepted must matter in play, so write it compactly
enough to stay in hot context and expect resolution to use it every turn. Give
each stat axis a one-line meaning—coverage, exclusions, and what low, middle, and
defining values look like—and show those meanings before the Player distributes
anything. Narration may not contradict the recorded sheet, and fictional grounding
is bound the same way through its recorded competence, limit, cost, and
counterplay.

Settle resolution grounding before asking how competence is expressed, and let the
play/system module inherit it. Under numeric or banded grounding, design the stat
axes for this setting and this starting stage instead of importing a generic list,
offer two to four candidate sets, derive the point total and bands from the
accepted axis count, ask how many points the Player wants to spend, record the
axes with the campaign rules so validation follows that set, and derive competence
from the distribution. A competence that contradicts the distribution is a
legitimate Player choice and is recorded as accepted.

Ask the Player about the character and derive how the world perceives them. Do
not ask who warms to them, who distrusts them, what strangers assume, or how a
specific room treats them; ask open questions about the character—their most
striking quality, their manner, how they express themselves—and derive the public
read from the answers, revising it as the character grows.

Build the character through a short ordered sequence, not one broad question. In
schema-v7 Standard and Deep, ask identity core, character surface—including the
concrete physical basics of gender or presentation, age, height, weight or frame,
body type, and distinguishing features—desire and why-now,
reliable competence, real limit, position, and change appetite as separate counted
decisions; fixed-count Quick keeps its two character slots and infers what is left
open. Every character question must name what it feeds—a world reaction, an
opening affordance, a pressure channel, or a progression gate—so depth never turns
into a long form. Record the public read in `player.md`, since NPC first reactions
come from it. In Deep, a `long_journey` or `episodic` reach activates
`character_foundation` for the deep layer.

Express the ongoing world-side creation authority as a threshold on the creation
tiers the ledger tracks—supporting and above, major only, or nothing with everything
shown at review—and ask it in plain language rather than in tier codes. Incidental
colour stays free, anything named is logged with its tier, and a scene wanting
something above the threshold either asks or is built without it. Keep that threshold
and the content limits readable during play, since a rule nobody reads governs
nothing.

Derive character-side approval triggers from those two axes instead of asking for
a list: fully player-owned authorship makes every GM-authored inner state, past
fact, relationship, or decision about the character an approval trigger, while
permanent loss the Player put in play is pre-authorized. Ask only the world-side
creation authority, once, and let it inherit the character-side set.
Pre-authorization never widens a content boundary.

Research does not end with setup. Settle an in-play policy—`off`, `ask_first`, or
`bounded_auto`—for the moment a scene reaches a source question the dossier never
answered, record it in `research_dossier.md`, and say what a lookup costs that turn.
Under every policy the search stays narrow, the result is appended as a research
pass with references, and an unresolved answer stays open rather than becoming
invented canon.

Research then runs as bounded passes, not one crossing. When a later accepted
answer opens a source-dependent question the dossier does not answer, run a
narrow pass for that one question before locking dependent truth, and append what
was verified and what stays open. A new source domain or a widened scope needs its
own permission turn.

Decide the world at macro scale even when the character is local: era anchor,
who holds large-scale power, a few movements that run without the character, the
visible channels that carry them into the local slice, and named occupants for the
implied macro seats at roster detail so later references stay consistent.

Treat each module or slot as one decision boundary, not a form of storage
fields. Ask the Player only for a consequential preference or permission, and
present it as a coherent card or a few contextual options. After acceptance, the
coordinator materializes the operational and causal detail—profile selectors,
policies, cards, owners, ids, routines, routes, availability, and knowledge
classification—without asking about each field. At the named review boundaries
the Player checks accepted choices, ordinary defaults/deferrals, and the
player-safe effect of actual preparation instead of filling implementation
fields.

An inherited decision from an earlier module is never re-asked or quietly
weakened; a requested change is a revision of its owning module. A follow-up
counts as another content decision only when it can vary independently, changes
Player experience or permission materially, cannot safely be a displayed
default, is explicitly accepted as a separate decision, and the selected route
still has budget. Clarification, an `accept|mix|change` exchange,
implementation-field collection, factual correction, and review acceptance are
not separate decisions. Fixed-count Quick routes never open an extra decision;
any required opt-in stays visible inside its owning card or remains off. See
`workflows/worldbuild/WORKFLOW.md` and the selected compact playbook for the
authoritative wording.

After the depth gate has been answered and persisted, the first campaign-design
question should be only the world anchor:

> Which world will this campaign occupy—an existing universe, a real place and
> period, an original world, or your own homebrew—which slice of it do we start
> in, and how far do you intend the story to reach?

Record that reach as `contained`, `regional`, `long_journey`, or `episodic` in
`world.md`, with the stated destination when there is one. Reach frames every
later question, so the progression module inherits it instead of asking for
campaign length again, and a `long_journey` or `episodic` reach triggers the
`campaign_architecture` pack in Deep. It is an intent, not a guarantee: it sets
preparation depth, never the outcome.

Tone, promised play, and player fantasy follow as the rest of the promise: a
separate counted decision in schema-v7 Standard/Deep, and the same slot in
fixed-count Quick, where unvolunteered parts are inferred and shown at review.
When the anchor names an existing universe, a real place/period, or supplied
homebrew, run the Research Gate before offering source-dependent options, and
record the cast scope stance—`full_canon`, `canon_world_original_cast`, or
`genre_adjacent_original`—since it decides research scope. Canon Policy inherits
that stance.

After the promise, inspect `briefs/lenses/INDEX.md` and only candidate lens
briefs suggested by the promise. For current schema-v7 RPG routes, use the
promise and character seed to prepare contextual options, but accept system
values only in Play/System and presentation values only in
Presentation/Visual. Schema-v6+ Quick uses the same split at slots 5 and 6.
Legacy RPG and Companion retain their existing bundle decision. Each option
should state:

- intended feel and candidate lenses;
- optional mechanics awaiting approval;
- tracking load and approximate speed effect;
- why it fits the campaign promise and character seed.

A displayed option may preview grounding and the compact runtime narration/
pacing contract: three campaign-specific Narrative Signature anchors, no more
than three avoid habits, interiority, up to two sensory priorities, dialogue,
humor, distance, breathers, and exit policy. Previewing linked choices never
combines the two acceptance boundaries.

Quick defaults remain `fictional` grounding, `player_owned` interiority,
`balanced` dialogue, `situational` humor, `close` emotional distance,
`balanced` breathers, and `player_led_with_established_triggers`. Derive the
anchors and sensory focus from the campaign promise and character. With no
stronger signal, anchor on concrete sensory evidence, plain character-specific
dialogue, and causal consequences before exposition; avoid default cryptic
aphorisms, recycled stock gestures/metaphors, and manufactured tension after
clean success.

Recommend one option, then ask only the current route's named decision. Accept
`accept`, `mix`, `change`, `default`, or `defer`. Lens selection never enables
a mechanic by implication. Materialize accepted choices in
`play_profile.yaml`, explain them in `system_fit.md`, and record resolved lens
conflicts in the World Operating Model. Do not load lens briefs during ordinary
play.

### RPG Quick Decision Map (Schema V6+)

Use exactly these 10 unique slots:

1. Campaign Promise And Player Fantasy.
2. Character Identity, Current Desire, And Why Now.
3. Competence, Limitation, And Social Position.
4. Agency, Authorship, And Boundaries.
5. Play And System Contract.
6. Presentation Contract.
7. Character–World Relationship Pattern.
8. Reciprocity Design Review / design direction approval.
9. Integrated Preparation Review of actual player-safe preparation.
10. Preparation Approval.

Slots 1–4 create the Character Seed. Slots 5–7 establish the play contract and
the required world relationship. Slots 5 and 6 accept one coherent card each, so
a stateful mechanic or an optional Dashboard/visual/World Voices layer is enabled
only when the accepted card states it explicitly; otherwise it stays off. Slot 7
asks for the anchor-or-isolation stance and the desired entanglement shape, and
the coordinator then realizes the independent issue, intersection,
place/routine, and independently motivated relationship. The slot-8 display must show how the world
answers this character: a capability affordance, limitation/counterplay,
character-originated anchor or explicit isolation, world-independent process,
intersection, place/routine fit, independently motivated person or faction,
and a causal opening shape with neutral action space. On acceptance, increment
the setup revision and set `design_direction_approved_revision` to that current
revision.

Then keep `ready_for_play: false` and materialize the actual opening-scale
preparation. Slot 9 shows the real player-safe result—not a second proposal—including
the character, known world/place/relationship positions, independent process,
intersection, visible opening, and neutral actions, and asks whether that
prepared truth is accurate, complete at the promised scale, and faithful to the
approved direction. Slot 10 then asks a separate readiness go/no-go on the same
unchanged preparation, shows the final locked/defaulted/deferred record without
introducing new truth, and records `preparation_approved_revision` at the
resulting current revision.

Persist every accepted answer immediately in its semantic owner, then update
`session_zero.md`, increment the setup revision, and sync the active runtime
profile's source revision on the same turn. The first completion of each slot
increments `questions_completed`; later revisions to that slot do not. If a
post-slot-8 change alters design inputs, clear both approvals and repeat the
design review. If only preparation changes, clear preparation approval and
repeat slots 9–10.

Research never consumes a Quick slot. Pause for the Research Gate when needed,
give every unresolved execution/scope/risk permission its own budget-exempt
turn and revision, and resolve it before dependent design approval. Never fold
research consent into slots 8, 9, or 10.

## Schema-V8 RPG Deep Stage Map

Use `workflows/worldbuild/deep_v8/manifest.json` as structural authority and
load only its active stage playbook. Record one consequential decision per
message through `tools/session_zero_state.py`; stage completion, not a minimum
question count, governs readiness.

1. North Star & Authority.
2. Research & Canon Grounding.
3. Character Core.
4. Thin World Kernel.
5. Character Realization & Mechanics Core.
6. Living World Ecology.
7. Runtime Experience Contract.
8. Reciprocity & Campaign Horizon.
9. First Act & Preparation.

Only safety, research permission, and creation authority fan out immediately
to their semantic owners. Materialize other owner files at stage boundaries,
record their digests, and invalidate downstream stages and approvals when an
upstream decision changes. Stage-local extensions replace the global pack
ledger. The two player approvals remain design direction and the unchanged
materialized preparation package.

## Schema-V7 RPG Standard / Deep Decision Map

Use `workflows/worldbuild/playbooks/rpg_standard_deep.md` as the authoritative
procedure. Standard completes this core in 21–30 content decisions. Deep uses
the same core plus triggered packs in 30–45 decisions before any separately
approved extension:

1. Campaign Promise And Player Fantasy.
2. Research Need And Source Boundary.
3. Agency, Authorship, And Content Boundaries.
4. Character Identity, Current Desire, And Why Now.
5. Competence, Limitation, Social Position, And Change Appetite.
6. Play And System Contract.
7. Presentation And Visual Contract.
8. Canon Policy.
9. Palette.
10. World Truths And Operating Model.
11. Scale, Everyday Life, Access, And Routes.
12. Independent Issues And World Dynamics.
13. Factions And Institutions.
14. Faces, Places, And Independent Relationships.
15. Progression And Rewards.
16. Character–World Reciprocity Pass.
17. Starting Situation Design.
18. Continuity, Ownership, And Preparation Contract.
19. Reciprocity Design Review / design direction approval.
20. Integrated Materialized Preparation Review.
21. Preparation Approval.

Modules 1–9 establish Character Seed and contracts before the world scaffold.
Modules 6 and 7 accept one coherent card each and split into counted follow-ups
only for genuinely independent choices. Module 9 inherits the boundaries already
accepted and asks only about unresolved creative palette elements.

Modules 10–15 build world truth around that known seed without making the world
dependent on the character. The Player chooses governing truths, salient forces,
and which faces, places, and relationship roles matter; the coordinator authors
the operating model, faction and NPC/place cards, routines, availability,
routes, and gated knowledge.

Module 16 asks the Player to accept, mix, or change a proposed intersection and
relationship pattern, and the coordinator then revises the scaffold so it
establishes a character-originated anchor or explicit approved isolation, an
independently moving issue/domain, their playable intersection, competence
affordance, limitation/counterplay, place/routine relationship, and
independently motivated people or factions. Module 17 asks the Player to choose
among coherent opening shapes while the coordinator wires routes, presence, and
hidden limits. Module 18 asks one ongoing creation-authority decision—what always
needs renewed approval versus what may be inferred within accepted
boundaries—and the coordinator locks ownership and source precedence without
reopening research, safety, mechanics, canon, or advancement.

Before module 19, Deep resolves every activated pack and both approval fields
remain null. Module-19 acceptance sets design approval to the resulting setup
revision. Materialize actual preparation while not ready, including active
opening owners, then show it player-safe in module 20 and ask whether it is
factually accurate, complete, and faithful to the approved design. Module 21 then
asks a separate readiness go/no-go on that unchanged preparation and sets
preparation approval to the resulting current revision. Display alone is not
acceptance, module 21 introduces no new truth, and finalization may not first
invent substantive truth.

## Legacy 17-Module Semantic Reference

The detailed modules below preserve schema-v1–v6 Standard/Deep semantics and
remain useful subject guidance. They are not the schema-v7 order, budget, or
approval contract. Map their durable topics to the current 21-module owners
when working on schema v7.

### 1. Campaign Pitch

Ask for the universe or genre, emotional tone, player fantasy, core play feel,
and what the campaign should not become.

Then prepare the contextual bundle support described above. Legacy
Standard/Deep and Companion may accept it through their existing bundle
decision. Schema-v6+ RPG Quick carries the relevant options forward to separate
slots 5 and 6. Lens briefs are question generators, not runtime instructions.

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
emotional distance, and breather policies. Legacy Standard/Deep may refine the
card through their module flow; schema-v6+ Quick accepts it in Presentation
Contract slot 6.

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

- Fast (recommended): routine 30–90 seconds, ordinary durable 45–120 seconds,
  structural/boundary 2–4 minutes; use `scene_checkpoint_or_5_durable` with
  `validation_policy: full_on_distill`. Current truth and bounded atomic
  candidate validation are immediate; secondary notes and the aggregate full
  check wait for five durable turns or another full trigger. Scene boundaries
  write the compact checkpoint without forcing full distill.
- Balanced: light 1–2 minutes, durable 1.5–3 minutes; use
  `scene_checkpoint_or_3_durable` with `validation_policy: full_on_distill`.
  Current truth and atomic candidate validation remain immediate; secondary
  notes and the full check reconcile at a meaningful trigger or after three
  durable turns. Scene boundaries write the compact checkpoint.
- Maximum Continuity: durable 2–4 minutes, structural 3–6 minutes; use
  `every_durable` with `validation_policy: full_each_durable`, so every affected
  secondary note and the full check complete on each durable turn.
- Custom: tune cadence without disabling immediate authority writes, durable
  revision evidence, atomic candidate validation, or aggregate full validation
  at the selected boundary.

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

Before `ready_for_play: true`, confirm the selected route's budget and status
block, a locked active profile at the current setup revision, materialized
first-session preparation, active opening brief, reviewed defaults/deferrals,
and every required approval. Schema-v6+ Quick requires exactly 10 slots and
slots 8/9/10 approval flow. Schema-v7 Standard/Deep requires the 21-module
status block, an earlier design approval, actual player-safe preparation review,
and `preparation_approved_revision` equal to current `setup_revision`; Deep
also requires every active pack completed or defaulted. Transition the opening
sources to `consumed` only after first player-facing use.

Schema-v8 Deep instead requires all nine manifest stages complete, every
activated stage extension complete or explicitly accepted as defaulted, no
stale outputs, and its revision/digest-bound gate chain through
`ready_and_snapshotted`. Its legacy pack lists and 21-module status block are
not readiness authorities.

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

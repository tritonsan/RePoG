# Workflow

RePoG Worldbuild Router

# Purpose

Use this compact router while `campaign/setup_profile.yaml` is not ready for
play. Load only the playbook required by the selected experience, depth,
schema generation, and current boundary.

Worldbuilding creates a playable pressure system, not an encyclopedia. Current
RPG routes follow Character–World Reciprocity: establish a real character seed,
build a world that retains independent causality, run a two-way pass,
materialize actual preparation, show it player-safe, and obtain revision-bound
approval before readiness.

# Hot Loading Rule

| Situation | Load |
| --- | --- |
| RPG Quick interview, reciprocity review, or preparation review | `playbooks/rpg_quick.md` |
| RPG Standard or schema-v7-and-earlier Deep | `playbooks/rpg_standard_deep.md` |
| Schema-v8 RPG Deep | `deep_v8/manifest.json`, then only `deep_v8/<active stage>.md` |
| Companion Quick, Standard, or Deep | `playbooks/companion_setup.md` |
| Research Gate or source work | `playbooks/research_gate.md` |
| Final readiness boundary | `playbooks/finalization.md` |
| Eligible semantic parallelism | `workflows/orchestration/WORKFLOW.md` plus the active playbook boundary |

`playbooks/full_reference.md` is a cold design reference. Compact playbooks and
current schemas govern whenever wording differs.

# Routing Gates

If `experience_mode` is blank, ask only:

> What would you like to create: an RPG Campaign with RePoG as the Game
> Master, or an AI Companion—a persistent fictional character with an
> independent, grounded life?

Persist `rpg` or `companion`. This routing choice does not count toward content
decisions. Legacy schema-v1–v3 campaigns without the field remain RPG.

If experience is selected and `session_zero_mode` is blank, ask only:

> Which Session 0 depth do you want: Quick (compact), Standard (expanded core),
> or Deep (a dependency-guided, staged design with only relevant branches)?

Persist `quick`, `standard`, or `deep`; set status `in_progress`. Quick,
Standard, Companion, and legacy Deep set a numeric `question_target`:

- schema-v6+ RPG Quick: exactly 10;
- schema-v7 RPG Standard: 21–30;
- Companion Quick: exactly 7;
- Companion Standard: exactly 15;
- schema-v7 RPG Deep and Companion Deep: initially 30–45;
- legacy schema-v1–v5 RPG Quick: 6–8;
- legacy schema-v1–v6 RPG Standard: 17–25.

Do not combine either routing gate with the pitch. Numeric setup-duration
promises for redesigned RPG Quick and Standard are withheld until measured;
turn-performance estimates remain separate and still apply.

Route to the matching playbook. An already active legacy Standard/Deep
campaign keeps its existing module numbering and approval behavior unless the
Player explicitly approves migration.

Schema-v8 RPG Deep does not use a readiness question quota or the legacy pack
lists. Initialize `session_zero_state.json`, leave `question_target` blank,
derive `questions_completed` from its decision ledger, and follow its nine
stages. Load the manifest plus only the active stage. The manifest owns
prerequisites, controlled trigger tags, stage-local extensions, and the gate
chain; the stage playbook owns semantic interviewing and materialization.

# Shared Interview Contract

For every content decision:

1. name the current module or slot;
2. ask exactly one decision question;
3. explain why it matters in one or two sentences;
4. offer two to four contextual, neutral options when useful;
5. stop and wait.

For schema-v8 Deep, record the decision through `tools/session_zero_state.py`
and render the managed Deep-v8 summary; do not edit a legacy status block. For
all other routes, write into the selected status block only. The legacy route blocks share slot and module
names—both open with the campaign promise—so an edit keyed to a name alone lands in
the inactive block as well, and validation reads only the selected one, so the
contamination is silent. Leave every non-selected block untouched.

After writing, confirm the value is actually present rather than assuming the edit
landed. A write that silently changes nothing is reported later as a missing field,
which points at the wrong problem: the answer was accepted and recorded in the log,
so the field looks forgotten rather than unwritten.

Write accepted answers immediately. Schema-v8 Deep writes once to its atomic
decision ledger; only safety, research permission, and creation authority also
receive an immediate semantic-owner write. Its controlled trigger tags activate
stage-local extensions automatically. Other routes retain their existing pack
scan and immediate persistence behavior.

Never repeat a locked, defaulted, skipped, deferred, or already answered decision. Accept natural language plus `accept`,
`mix`, `change`, `default`, `defer`, “go deeper,” and “that is enough.” Do not
hide unrelated choices inside a bundle.

Treat each named slot or module as one decision boundary, not as a form to
complete.

- **Player Chooses:** ask only for a consequential preference or permission:
  something that materially changes promised play, safety, agency, authorship,
  source or canon scope, an explicit mechanic, presentation behavior, a salient
  world relationship, or opening direction. Present a coherent player-facing
  card or two to four contextual options instead of a list of storage fields.
- **Coordinator Realizes:** after acceptance, materialize the operational and
  causal detail required to honor that choice at the route's existing
  persistence or preparation boundary. This includes profile selectors,
  policies, causal cards, owners, source precedence, ids, routines, routes,
  availability, knowledge classification, and bounded connective detail. A
  field existing in a semantic owner is not by itself a reason to ask another
  question.
- **Player Reviews:** at the route's named review boundaries, show the accepted
  choices, every player-relevant ordinary default or deferral, and the
  player-safe effect of actual preparation. The Player reviews fidelity and
  completeness; they do not fill implementation fields for the coordinator.

Direct normalization or a value mechanically entailed by an accepted answer is
neither a new decision nor an inferred default. When the coordinator chooses
among multiple plausible ordinary alternatives, give that choice a short,
unique, stable label in `defaulted_decisions`, explain its reason and effect in
`session_zero.md`, and expose its player-visible consequence at the applicable
review.

Never infer a hard content boundary, source or risk permission, stateful
mechanic, numeric grounding, protected player-character fact, player-character
action or interiority outside the accepted policy, or truth reserved for
renewed approval. A decision already accepted in an earlier module is inherited,
not re-asked and never quietly weakened; a requested change to it is a revision
of its owning module.

Check the world again before naming people. Consult the dossier's character
grammar and its record of which peoples are plausible at this stage and place, and
run a narrow research pass when either is thin. A name carries culture, a title
carries a claim, and a species carries a history: each must fit the source, the
structure already established, the chosen location, and the live issue. Peoples are
gated by stage and place—a people the world contains somewhere does not therefore
belong in this port at this time—and an excluded one is recorded with its reason.
Follow the source's own rule for who earns a reputational title, so ordinary
working people are not handed grand ones. A cast named ahead of this check belongs
to no world.

A Player's selection narrows attention, never the world's possibility space. When
they pick which issues, forces, faces, or opening shapes matter, keep the
unselected candidates dormant with the trigger that would surface them rather than
discarding them. Give each selected element three or four side conditions—secondary
effects and the kinds of change that would shift its direction—and one
counter-current that appears to contradict it while still fitting the setting.
Prepared latitude is what lets later turns improvise without inventing new truth,
and a world whose every force points the same way leaves nothing to play against.
Record no predetermined resolution for any of it.

Ask about companions as a contract, not a roster. A company is assembled over the
course of play, so the decision fixes intent and shape rather than a membership list,
and it scales to the declared reach: a long or episodic reach leaves the company
incomplete for a long stretch by design, and an empty seat is runway rather than
something to fill during setup. Starting with one companion, or none, is a complete
answer. A company need not form in one place or at one time, and the interview should leave room for a companion the Player
never planned. Cover what kinds they want beside them and what kinds they do not,
whether a limit applies and whether the setting or the Player sets it with
open-ended as a real answer, how members are expected to arrive over the course of
play, and how much the Player steers investment in them. That last one stops at their
will: a companion's motives, refusals, and departures are their own in every setting,
so control is offered over what to spend and offer, never over what they want.

Show the consolidated record of defaulted and deferred decisions as part of the design
review, not only at final approval. Checkpoints surface defaults in fragments as they
accrue, but the design review is the one place the Player weighs the whole set against
a finished design, and the last point where changing one costs nothing because
materialization has not yet built on it. The reviewed flag still belongs to the final
approval. Organize the synthesis so decisions that constrain each other appear
together, since module order records the order questions were asked rather than the
order the answers matter in.

Materialize depth-pack outputs rather than gesturing at them. A world operating model
states how the world produces consequences, not what it contains, and restating the
premise leaves it unmaterialized however long it runs. A faction is only written where
the answers established coordination rather than a single dangerous person or an
uncoordinated condition, and a real faction records what it knows, what it has wrong,
and what it withholds, with reach that has edges. A research gate is resolved rather
than left pending, verified material kept apart from what stays uncertain, and silence
in the source recorded as silence instead of quietly filled. An accepted advancement
cadence is written into the play profile as a concrete value, since cadence is separate
from presentation and an unset cadence leaves progression unenforceable.

Cross-read the prepared files before the preparation review, not after it. Every
earlier review reasons over accepted answers; the preparation review is the first
point where the produced corpus exists, and the Player should not be its first
reader. Run the audit workflow's RPG section against the prepared campaign and check
what only a cross-read catches: that every module marked resolved actually wrote its
mapped owner, that named places exist and are reachable, that the opening's cast and
their routines agree with the scene, that claimed faction reach and knowledge
boundaries agree with the threads, that relationship edges resolve on both sides,
and that the player-facing checker passes on anything about to be shown. Correcting
is free before preparation approval, which is why the pass belongs here; a
correction that changes an accepted design decision returns to the design review
instead of being folded in quietly.

Write the wanted and unwanted GM behavior records when the narration voice is
accepted. They are concrete responses rather than adjectives, drawn from what the
accepted sample did and from the samples the Player turned down, and they stay
empty unless that decision fills them. Show a couple of examples before asking what
the Player dislikes, since the question asked cold returns an adjective.

Ask the starting aperture rather than a list of scale fields. How much world is
live at the start, and whether reaching past that boundary opens smoothly or costs
something, are real decisions that change preparation depth and how a Player who
leaves the opening early is met. Governing truths, independent movement, places and
routines, travel structure, and the opening scene itself all belong to other
modules and are never re-asked as scale fields.

Frame the first act, not only its opening scene. Every act after the first is
framed at closure and the opening situation covers one scene, which leaves the
first act as the only one nothing prepares. Fill the Arc Compass for it during
setup—its question, pressures, planted setups, what makes a climax reachable, what
would close it—and give it a scope in names: the places it can reach, the people
who belong to it, what is already in motion, and what stays true if the character
does nothing. One place and one person is an opening, not an act. Leave the
closure record empty until the act actually closes; the condition being satisfied
or made unreachable is what closes it, and the action that did so is recorded then.

Shape multi-arc architecture without fixing a plot, and never interview the Player
through arc-compass field names any more than through entity schema fields. Ask what
they want to find out and what they want tested, then derive the rest: a dramatic
question drawn from the character premise whose opposite answer would still leave a
campaign worth playing, pressures referenced from the issue and dynamics authorities
rather than restated, setups recorded as what is already planted and available with
the payoff left unscheduled, climax conditions stating what makes a climax reachable
rather than when it lands, closure conditions aligned with the real arc-close trigger
and accepted cadence, and interest signals limited to what the Player actually
expressed and updated from play.

Translate accepted mechanical answers into approved modules and their required
tracking fields before design approval, rather than leaving the coupling to surface as
validation errors or, worse, leaving nothing approved so that stats, supplies, and
injury stay decorative. Counted supplies need quantified or encumbrance inventory
tracking; persistent injury needs conditions wound tracking; travel presented as lived
passage needs route_time travel tracking; any dice at all need a dice mode other than
judgment_only; and any approved module beyond dice resolution alone requires mechanics
state to be enabled. Promises that map to no module are recorded as narrative
commitments so a verbal system stays binding, and a conflict between an answer and a
module requirement goes back to the Player instead of being resolved silently in
either direction.

Keep the route layer a network rather than a remark, and split who decides what.
The location graph records travel cost, access, visibility, traffic, conditions, and
route knowledge per connection; those edges are yours to fill from accepted answers
and existing place notes, while the Player decides only what they can meaningfully
decide: whether distance costs anything, whether the map is known at the start or
discovered through play, and whether movement leaves a trace others can act on.
Derive how movement behaves in the declared setting and period before offering those
choices, and phrase them in that setting's terms. Let the Player name any route they
care about, and record at least one asymmetry—one-way, closed, costly, watched, or
unknown—unless the accepted answers deliberately removed all travel friction.

Bind the ongoing creation authority to the creation tiers the ledger already
tracks, so the answer changes when the coordinator stops to ask. The threshold is
supporting-and-above, major-only, or nothing with everything shown at review. Ask it
in plain language—whether a recurring face needs permission or only a major new
force—and never in tier codes. Incidental colour stays free, anything named is
logged with its tier, a supporting or major figure needs its full note and voice
axes before speaking, and a scene that wants something above the threshold either
asks or is built without it. The accepted threshold and the content limits both stay
hot during play; a rule nobody reads governs nothing.

Never put an internal label in front of the Player as the choice itself. Values
like a palette's yes, no, or maybe, a policy name, or a profile enum are the
record; the question is asked in plain language, in the Player's own language,
describing what each option would mean at the table. Say that something would
appear rarely and stay at the edges rather than offering "maybe"; say that a
lookup happens without asking rather than naming the policy. File the label
afterward, and reserve enum vocabulary for Designer Mode.

Write example options in the Player's own language and frame of reference. When
no local frame is established, use globally recognizable references instead of
ones tied to an unrelated region.

Derive every option set from what the campaign has already established—the world,
the stage, the researched dossier, and the answers so far—rather than from a
generic taxonomy. An option list that could belong to any campaign teaches the
Player nothing and invites a generic answer. Name choices in the setting's own
terms and shapes: its recurring scene types, its institutions, its typical
antagonists, its own units of travel and reputation. A generic frame is a fallback
for the first question only, before anything is established, and even then it is
translated into the setting's language as soon as the world is named. This applies
to every offered set, not only to stat axes: play mix, pace, palette, factions,
faces, opening shapes, and reward kinds all follow it.

Ask the content-boundary decision on its own, in every route and for every
setting, using the same structure so it does not depend on the model or the
campaign. Never place it inside a style, bundle, or profile card, and never let
accepting a card set it. Offer the standard categories recorded in
`boundaries.md`—sexual content, harm to children, torture and graphic violence,
harm to animals, suicide and self-harm, severe humiliation or discrimination,
addiction, illness and dying, captivity and slavery—each as open, fade, or avoid,
with "everything open" available as a real answer. State both guarantees when
asking: a limit may be added at any time including mid-play and takes effect
immediately, and adding one is never framed as a cost or a penalty. A Player
signal to stop applies at once. An open-ended "is there anything?" is not
sufficient, because a blank answer would be recorded as consent.

Build the character through a short ordered sequence rather than one broad
question. The Player discovers the character while answering, and the coordinator
needs enough of them to decide how the world reads them, who reacts and how, what
clean success looks like, and where pressure lands. Depth scales with the route:
fixed-count Quick keeps its two character slots and infers what is left open,
while Standard and Deep ask identity, public read, desire and why-now,
competence, limit, position, and change appetite as separate counted decisions.
Deep adds the character-foundation layer when its trigger fires.

Every character question must name what it feeds—a world reaction, an opening
affordance, a pressure channel, or a progression gate. A question with no such
consumer does not get asked, which is what keeps a deep character build from
turning into a long form.

Settle the resolution grounding before asking how competence is expressed, since
`fictional`, `bands`, and `numeric` produce different questions. The play and
system module inherits that answer rather than asking twice.

State the host dependency when offering a layer that needs a capability outside
this workspace. Image generation only works when the running tool or model can
actually produce images, so say that plainly before the Player chooses. When the
capability is absent, do not record the layer as enabled: mark it unavailable,
explain that the campaign loses nothing else by it, and note that it can be turned
on later if the host gains the capability. The same honesty applies to viewing a
dashboard, whose data is written either way but whose viewer needs a local server.
Never let a Player accept a layer that cannot run.

Let the Player choose narration voice by ear. Write the same short moment from
this campaign in each candidate voice, a few sentences apiece, and ask which reads
right; then derive point of view, tense, camera, density, and length from the
accepted sample and show what was recorded. A list of craft terms asks the Player
to guess at labels. Ask them directly what they dislike in narration, because the
avoid-list is theirs to fill, and derive the signature anchors and sensory focus
from the accepted sample and the setting's native register. Keep the operative
values in the profile, which is read every turn, and let the readable narration
note carry explanation rather than the working contract.

Keep simulation fidelity, play mix, and pace as separate questions. How much the
engine tracks, what the campaign spends time on, and how tense it feels vary
independently, and bundling them produces generic cards and a false link between
tracking and tension. Fidelity never obliges constant pressure.

Every tracking setting names an instrument and a turn obligation, recorded in
`rules.md`: dice modes other than judgment-only require a recorded roll behind a
contested outcome, quantified inventory and strict consumables change state
through mechanic operations, wounds become conditions, clocks advance only on
their trigger, stepped time and route travel consume recorded units. When a
setting is off, invent no precision. State the cost when offering fidelity:
heavier tracking roughly doubles turn length, and a dashboard adds one to two
minutes per refresh while being the only place the Player sees tracked values.
Keep tracking out of narration—values go to state, prose carries their fictional
weight. Fidelity may be changed later at a stage boundary as a revision.

Whatever capability model is accepted must matter in play. Write it compactly
enough for the GM to keep hot, so resolution can name the axis or capability an
action leans on, read the opposition on the same scale, and refuse narration that
contradicts it. A model chosen at setup and ignored afterward is decoration; this
applies to fictional grounding too, where the recorded competence, limit, cost,
and counterplay carry the same weight as numbers would.

Keep character-growth permissions with the system side. The character modules ask
only which parts of the character the campaign should test and which must be left
alone—pressure direction that cannot be derived from tone or from the sheet, and
whose "do not touch here" half is a thematic limit no content category records.
Cadence, reward delivery, and whether capability gains pause for an explicit
choice belong to the progression decision; permission for permanent change is
inherited from the accepted consequence stance; adding a stat axis later is a
stage-boundary revision asked when that stage arrives.

Once a distribution is accepted, do not ask the Player to restate it. The low end
of a numeric or banded sheet already states the mechanical limit, its cost, and
how opposition presses it, so derive and show that. Ask only for a limit the sheet
cannot hold—an obligation or debt, a vow or refusal, a physical or mental
condition, a fear, or the cost of being recognized—and skip the question entirely
when the Player has none, spending no decision and inventing no limitation. Under
fictional grounding the same limitation contract is asked directly, because
nothing else records it.

Stat axes are designed per setting and per starting stage, never imported as a
generic list. Author what each axis means before anything is distributed: what it
covers, what it does not, and what a low, middle, and defining value look like in
this setting. Show those meanings to the Player, since a number chosen against an
unexplained label is a guess. Derive candidate sets from the researched world, leave out
capabilities the campaign's stage has not reached, add setting-specific axes when
it has, and offer two to four sets for the Player to accept, mix, or change.
Derive the point total and the low, middle, and defining bands from the accepted
axis count and starting level instead of a fixed classic total, state them, and
ask how many points the Player wants to spend. Record the accepted axes with the
campaign's rules so validation follows that set instead of a default count. Then
derive competence from the distribution and confirm it. A Player may deliberately
take a competence that contradicts their distribution; record that tension as
accepted rather than correcting it. With fictional grounding, do the same work in
prose and skip stat construction entirely.

Ask the Player about the character; derive how the world perceives them. Never
ask the Player to decide what strangers assume, who warms to them, who distrusts
them, or how a room treats them—those are coordinator derivations from the
described character, and asking for them hands the Player the world's side of the
table. Prefer open questions the Player can answer about their own character,
such as the most striking thing about them or how they carry themselves, over
narrow hypotheticals about a specific room or encounter. Revise the derived read
whenever the Player adds to the character, and never let it contradict them.

Keep authorship breadth and consequence weight as independent axes. Who authors
the character's inner life, past, and decisions is one question; whether
permanent loss is in play is another. Present them separately so they can be
mixed, and settle character-specific authorship limits once the character exists
by applying the accepted stance instead of asking again.

Approval triggers have one home each. Character-side triggers are derived from
those two axes rather than asked as a list: fully player-owned authorship makes
every GM-authored inner state, past fact, relationship, or decision about the
character an approval trigger, while permanent loss the Player put in play is
pre-authorized and is not re-approved scene by scene. World-side triggers—new
persistent named people, places, factions, institutions, world-scale forces, and
revealed major truths—are asked once as the ongoing creation-authority decision
and inherit the character-side set without repeating it. Both are recorded in
`boundaries.md`, whose standing improvisation list is only the fallback default
once those entries exist.

Pre-authorization never widens a content boundary. Accepting permanent loss does
not enable a category the Player set to avoid, and no stance outranks the hard
limits.

Unless the Player changes it, the clarification default is: ask before anything
consequential or irreversible, infer ordinary cosmetic detail, and show the
inference at the next review. This is a default rather than an interview
question, and the Player may change it during play without spending a decision.

Do not present an unverified source claim as settled fact. Once the Player names
an existing universe, a real place/period, or supplied homebrew, run
`playbooks/research_gate.md` before offering options whose content depends on
that source—capability bands, threat scale, travel and communication limits,
institutions, economy, or tonal examples. Until a claim is verified, look it up
or mark it as unverified in the same message.

Ask the source and research permission immediately after the world anchor, as a
budget-exempt permission turn, before the rest of the promise. The research
module still owns the recorded classification, scope, status, and risk fields
and does not ask for them a second time.

Research then continues as bounded passes rather than one crossing. Whenever a
later accepted answer opens a source-dependent question the dossier does not
answer—a chosen profession, an institution, a technology, a legal or medical
limit, a newly named place—run a narrow pass for that one question before the
dependent truth is locked, and append what was verified and what stays open. A
new source domain or a widened scope needs its own permission turn; an already
granted scope does not.

Establish the campaign's reach with the world anchor, as part of the same frame
decision: `contained`, `regional`, `long_journey`, or `episodic`, plus the stated
destination when there is one. Reach decides how later questions are framed, so
it cannot wait for the progression module, which inherits it instead of asking
again. A declared reach is an intent, not a guarantee: it sets preparation depth
and framing, never the outcome, and no scene bends to keep an ambition on
schedule. Extending it later is a revision, not a new campaign. Record it in
`world.md`.

Decide the world at macro scale even when the character is local. Before world
truths are locked, establish a bounded macro frame: the era anchor, who holds
large-scale power and what could upset it, two to four large movements that run
without the character, and the visible channels through which the macro reaches
the local slice—news, prices, patrols, migration, levies, rumor. Keep each to a
few lines; this is a frame, not an encyclopedia. Fill the macro seats the source
or setting implies with named figures at roster detail so later references stay
consistent, and give the local slice at least one legible link to that frame
without making the character matter to it.

Macro depth scales with reach. A contained reach keeps the frame thin; a long
journey deepens it, makes the roster matter, and opens later regions through
staged research passes rather than researching every region up front.

The first accepted completion of a decision increments `questions_completed`.
A genuinely separate follow-up may count within the selected budget. Revising
an already completed decision increments `setup_revision` but never increments
`questions_completed` again.

A follow-up counts as another content decision only when the selected route
permits additional decisions and all of the following are true:

1. it can vary independently of the decision already accepted;
2. it materially changes Player experience or permission;
3. it cannot safely be derived or recorded as an ordinary displayed default;
4. it is asked and explicitly accepted as a separate decision;
5. the selected route's current question target has remaining capacity.

Clarification needed to finish the current card, an `accept|mix|change`
exchange, implementation-field collection, factual correction, or acceptance
of a named review is not a separate follow-up. Explicit research source and
risk permissions retain their existing budget-exempt treatment.

Quick's fixed ten-slot route never opens an eleventh content decision. Any
required explicit opt-in must be visible inside its owning coherent slot card
or remain off. Standard and Deep may use their existing variable budget only
for genuinely independent consequential choices.

Experience/depth gates do not count. Triggered research execution, evidence
review, and each explicit source/risk permission are budget-exempt separate
turns and revisions. Deep checkpoint and extension permissions are control
turns; do not disguise them as content decisions.

Every ordinary inferred choice receives a stable label in
`defaulted_decisions` and readable detail in `session_zero.md`.
`defaulted_packs` is only for an activated Deep pack resolved through displayed
and accepted defaults. Pack lifecycle lists remain empty outside Deep.

# Current RPG Reciprocity Approvals

Schema-v6+ Quick and every schema-v7 RPG depth use two approvals:

- design direction approval after the complete reciprocity design;
- preparation approval after actual materialized preparation is shown
  player-safe.

Quick uses slots 8, 9, and 10. Schema-v7 Standard/Deep uses modules 19, 20, and
21. In both routes:

- design approval sets `design_direction_approved_revision` to the resulting
  current setup revision;
- substantive preparation is materialized while `ready_for_play: false`;
- the next review shows actual prepared truth, not another proposal;
- final preparation approval sets `preparation_approved_revision` to the
  resulting current revision;
- design changes clear both approvals; preparation-only changes clear the
  preparation approval;
- stale preparation approval cannot pass preflight.

The integrated preparation review asks whether the actual player-safe
preparation is factually accurate, complete at the promised opening scale, and
faithful to the approved direction. Its acceptance does not authorize
readiness.

Preparation approval then asks for a separate go/no-go on that unchanged
reviewed preparation together with the complete locked/defaulted/deferred
record and readiness implications. It introduces no new campaign truth.

Legacy Standard/Deep and Companion retain their existing final-summary approval
unless explicitly migrated.

# Starter Bundles

For current schema-v7 RPG routes, use the campaign promise and character seed
to prepare contextual bundle options; accept system values in the Play/System
module and presentation values in the Presentation/Visual module. Do not make
one bundle response silently approve both. Schema-v6 Quick follows the same
split across slots 5 and 6. Legacy RPG and Companion retain their existing
bundle decision.

RPG bundle support may preview feel, lenses, resolution grounding, optional
mechanics, Narrative Signature, interiority, sensory/dialogue stance, breathers,
tracking load, performance effect, Dashboard/visual behavior, and character
fit. No lens enables a mechanic by implication. Accepted runtime values belong
in the active profile at the current setup revision.

Present bundle support as coherent player-facing cards the Player can accept,
mix, or change. Acceptance enables only the stateful mechanics and optional
layers the accepted card states explicitly; Dashboard, image generation, and
World Voices never enable one another by implication, and any optional layer
absent from the accepted card remains off. The coordinator then materializes
the subordinate selectors and policy fields without interviewing the Player
field by field.

# Performance And Semantic Parallelism

Every RPG depth includes the Turn Protocol choice. Explain timing/freshness and
the independent costs of Dashboard and visual work. Fast remains recommended:
routine about 30–90 seconds, ordinary durable 45–120 seconds, structural about
2–4 minutes. Balanced and Maximum Continuity retain their documented bands.
Dashboard refresh may add about 1–2 minutes, image draft/revision about
1–3+ minutes, and accepted placement about 1–2 minutes. These are planning
estimates,
not guarantees.

Offer `off`, recommended `selective_structural`, or
`aggressive_structural` in the same performance decision. Quick and Companion
use at most two supporting workers; Standard/Deep use at most three. Workers
are read-only proposal lanes. The coordinator owns questions, approvals,
authoritative writes, ids, knowledge, validation, snapshots, projections, and
player-facing delivery. Serial fallback is normal.

# Authority And Revision Rules

- `setup_profile.yaml` owns decision counts, ordinary defaults/deferrals,
  Deep-pack lifecycle/extension, setup revision, readiness, and applicable RPG
  approval revisions.
- `play_profile.yaml` owns RPG runtime behavior; `companion_profile.yaml` owns
  Companion behavior. The unused profile is `inactive`.
- Every persisted decision/revision increments `setup_revision`; the active
  profile cites the same `source_setup_revision` before readiness.
- Schema-v7 Deep activates packs immediately on accepted triggers, resolves
  them at dependency-safe boundaries, and completes/defaults all active packs
  before reciprocity design approval.
- Research must permit current-scale locking before dependent truth becomes
  durable.
- Only the coordinator writes campaign truth, allocates ids, classifies
  knowledge, sets approvals/readiness, creates snapshots, and delivers text.

# Completion Route

For current reciprocity RPG routes:

1. finish all design inputs and, for Deep, all active packs;
2. obtain design approval;
3. materialize actual opening-scale preparation while not ready, optionally
   using bounded read-only proposal lanes;
4. show and accept the player-safe integrated preparation review as a factual
   accuracy and completeness check;
5. obtain current-revision preparation approval as a separate go/no-go on that
   unchanged reviewed preparation;
6. load `finalization.md`.

For legacy Standard/Deep and Companion, load finalization after their existing
final-summary approval and materialize there as previously documented.

Shared finalization order:

1. verify the route's approval gate and frozen revision;
2. draft-state preflight while not ready;
3. final status/profile/readiness fields without advancing setup revision;
4. serial approved projections at that revision;
5. starting snapshot;
6. one aggregate check;
7. handoff only after zero errors.

A substantive correction to a current reciprocity RPG returns to preparation
review/approval, or to design review if design or Deep-pack truth changed.
Metadata/projection-only corrections may repeat the final boundary without a
new setup decision. Never introduce unreviewed substantive truth after
preparation approval.

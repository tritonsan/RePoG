# RPG Quick Session 0

Load this playbook only after the router has selected `rpg + quick`. Schema-v6+
RPG Quick uses exactly 10 unique content-decision slots. Set
`question_target: 10`; keep `activated_packs`, `completed_packs`, and
`defaulted_packs` empty. The experience/depth gates and triggered Research Gate
work do not count.

Quick is compact because each slot resolves one coherent design boundary, not
because character or preparation work is omitted. It must follow this causal
order:

`character seed -> world scaffold -> two-way reciprocity pass -> design approval -> materialized preparation -> player-safe preparation review -> preparation approval -> readiness`

# Decision Accounting

The first accepted completion of each numbered slot increments
`questions_completed` once. Persisting that answer also increments
`setup_revision`. Revising a completed slot increments `setup_revision` but
never increments `questions_completed` again. Research execution, evidence
review, and each explicit source/risk permission are separate budget-exempt
turns and revisions.

Do not mark a review slot complete merely because a proposal was displayed.
Slots 8, 9, and 10 complete only when the Player accepts the named review.
Requested changes remain within that slot until the revised material is shown
and accepted.

Each slot is one decision boundary under the router's shared Player Chooses /
Coordinator Realizes / Player Reviews contract, not a form of storage fields.
Because Quick is fixed at ten slots, never open an eleventh content decision:
clarification needed to finish the current card, an `accept|mix|change`
exchange, implementation-field collection, or a factual correction all stay
inside the slot already in progress. Any required explicit opt-in must be
visible inside its owning slot card or remain off.

# Ten Decision Slots

Use this order. Ask exactly one slot decision per message and do not collapse
separate slots into one answer:

1. **Campaign Promise And Player Fantasy** — lead with the frame: which
   universe, real place and period, original world, or supplied homebrew; which
   slice of it the campaign starts in; and the declared reach—`contained`,
   `regional`, `long_journey`, or `episodic`. Tone, promised play, desired player
   fantasy, and what the campaign must not become belong to the same slot; take
   whichever of them the Player volunteers, infer the rest coherently, and show
   every inference at the reciprocity and preparation reviews. The reach is an
   intent rather than a guarantee, and it sets how deep the macro frame goes. Quick has ten
   fixed slots, so this never splits into another decision. When the anchor names
   an existing universe, a real place/period, or supplied homebrew, ask the source
   and research permission right here as a budget-exempt permission turn and run
   `playbooks/research_gate.md` before offering any source-dependent option. Run a
   narrow triggered pass later whenever an accepted answer opens a
   source-dependent question the dossier does not answer, and settle the in-play
   research policy—`off`, `ask_first`, or `bounded_auto`—with its per-turn cost
   stated.
2. **Character Identity, Current Desire, And Why Now** — the playable identity,
   the concrete physical basics (gender or presentation, age, height, weight or
   frame, body type, distinguishing features), the character's striking qualities
   and manner, the current desire, and the reason action matters at the opening
   scale now. Ask about the character rather
   than about how others should react to them. Quick keeps this in one slot: take
   what the Player gives, infer the rest coherently unless authorship is fully
   player-owned, and show every inference at review. Record the described surface
   in `player.md` and derive the public read from it, since NPC first reactions
   come from that derivation.
3. **Competence, Limitation, And Social Position** — ask the resolution grounding
   here, since competence depends on it, and let slot 5 inherit it. With numeric or
   banded grounding, offer two to four stat sets derived from this setting and
   starting stage, give every axis a one-line meaning and show it before any
   distribution, derive the point total and bands from the accepted axis count,
   ask how many points to spend, record the axes in `rules.md`, and derive
   competence from the distribution. Whatever model is accepted stays binding in
   play and is kept in hot context. With fictional grounding, keep it in prose.
   Then settle what clean success looks like and whether the character is central,
   peripheral, embedded, returning, or newly arrived, including who already knows
   them. Under numeric or banded grounding, derive the mechanical
   limitation/cost/counterplay from the distribution instead of asking the Player
   to restate it, and ask only for a limit the sheet cannot express—an obligation,
   a vow, a condition, a fear, or the cost of recognition—skipping it when there is
   none. Under fictional grounding, ask the limitation contract directly. A
   competence that contradicts the distribution is allowed and recorded as
   accepted. If the Player volunteers which parts of the character should be tested
   or left alone, record it here; otherwise infer it from the promise and show the
   inference at review. Growth cadence and presentation stay in slot 5.
4. **Agency, Authorship, And Boundaries** — ask the content boundary first and
   alone, using the same standard category set as every other route, each as
   open, fade, or avoid, with "everything open" as a real answer and both
   guarantees stated: a limit may be added at any time including mid-play, and
   adding one is never a cost. It never sits inside a card. Then, within this
   same fixed slot, settle the authorship and consequence stance as two
   independent parts—who authors the character's inner life, past, and decisions,
   and whether permanent loss is in play. Derive the character-side approval
   triggers from those answers instead of asking for a list, and settle world-side
   creation authority as a threshold on the creation tiers the ledger tracks—
   supporting and above, major only, or nothing with everything shown at review—
   asked in plain language rather than in tier codes. Incidental colour stays free,
   anything named is logged with its tier, and nothing above the threshold is
   created silently. Quick has ten fixed slots, so this never splits into another
   decision; infer what the Player leaves open and show it at review.
   Clarification stays a default, not a question, and character-specific limits
   are applied from this stance when the character takes shape.
Progression in Quick rides the play/system slot: settle at which closure growth
arrives and whether it is carried in the fiction or offered in a short pause, keeping
the two consistent, and instantiate the reward pool for this setting so rewards are
not generic. Progression runs on three tracks—stat points, special ability points
where the setting has a layer outside the axes, and fictional capabilities—so every
offer is points, a capability, or points plus an ability recognized from play.
Starting distribution needs at least one point in every axis and has no per-axis cap,
and unspent points are never lost. Reward offers follow the contract in `progression.md`—three directions
differing in kind, each in the Player's language with what becomes possible, its cost,
who notices, and what it opens next—and stay inside the accepted grounding without
using a disabled mechanic.

5. **Play And System Contract** — present two to four coherent player-facing
   Play/System cards and ask the Player to accept one, mix named parts, or
   request a change. Keep two things apart inside the card: simulation fidelity—
   which mechanics modules, `dice_mode`, inventory, time, travel, and wound
   tracking are on, each with the obligation it carries per `rules.md`—and pace
   and pressure, which stay under their own settings. Fidelity does not set
   tension, and a setting the card omits stays off with no invented precision.
   Each card also states dominant play, resolution grounding inherited from slot 3,
   tracking and failure stance, progression stance, Turn Protocol
   timing/freshness, and the semantic parallelism tradeoff, plus the cost of
   heavier tracking. Acceptance enables only mechanics explicitly listed in
   the accepted card. The coordinator materializes the resulting mechanics,
   resolution, inventory, time, travel, wound, dice, failure, advancement,
   performance, validation, and parallelism fields without asking for each
   selector separately.
6. **Presentation Contract** — let the Player choose the voice by ear: write the
   same short moment two to four times in different voices and ask which reads
   right, then derive point of view, tense, camera, density, and length from the
   accepted sample rather than asking for craft terms. Ask what they dislike in
   narration to fill the avoid-list, and derive the three signature anchors and the
   sensory focus from the sample and the setting's register, since readiness needs
   three meaningful anchors. Within this same fixed slot, state the
   player-visible policy and cost of any Dashboard, visual, or World Voices layer;
   each is explicitly on or off and none enables another. Image generation depends
   on the running tool or model supporting it—say so before the choice, and record
   the layer as unavailable rather than enabled when it does not. Dashboard, image generation, and World Voices never enable one
   another by implication; an optional layer not explicitly enabled by the
   accepted card remains off. The coordinator materializes the exact narration,
   Dashboard, visual, and World Voices implementation fields.
7. **Character–World Relationship Pattern** — ask the Player to choose or
   change the desired relationship shape: a character-originated anchor or
   explicit isolation, plus the kind of entanglement they want with the wider
   world. The Player may supply a specific person, place, obligation, or
   routine, but does not have to design the operational ecology. The
   coordinator realizes the independent issue or domain, playable intersection,
   place/routine/access fit, independently motivated person or faction,
   competence affordance, limitation counterplay, and causal opening shape.
   Those realized details remain subject to the slot-8 design review.
8. **Reciprocity Design Review** — show one coherent two-way design: how the
   character changes the initial world, how the world answers the character's
   competence and limitation, why the opening belongs to this character, and
   what remains independent of them. Approval locks the design direction, not
   yet the finished preparation.
9. **Integrated Preparation Review** — after the approved direction has been
   materialized while not ready, show the actual player-safe character, world,
   place, relationship, pressure, and opening preparation, then ask one factual
   question: is it accurate, complete at the promised scale, and faithful to the
   approved direction; if not, what must be corrected? This is a review of
   prepared campaign truth, not another abstract design pitch, and never a
   display of placeholders, implementation fields, or hidden truth. Acceptance
   records the review while readiness and preparation approval remain unset.
10. **Preparation Approval** — show the unchanged preparation accepted at slot 9
    together with the final locked/defaulted/deferred record and readiness
    implications, then ask only whether the Player approves proceeding to
    readiness preflight or is not yet ready to approve. Introduce no new truth,
    option, or first-time persistence here. Only this approval authorizes
    readiness preflight and finalization.

Research is conditional. If needed, pause before any dependent design is
approved and use `playbooks/research_gate.md`. Never fold research consent into
slots 8, 9, or 10. Resume the next missing Quick slot only after the gate
permits the current scale.

# Revision-Bound Approval Contract

Before slot 8, keep both approval fields null. When slot 8 is accepted, persist
its answer, increment the setup revision, and set
`design_direction_approved_revision` to that resulting current revision.
`preparation_approved_revision` remains null.

After slot 8, materialize the accepted direction while
`ready_for_play: false`. When slot 9 is accepted, persist its review at a newer
setup revision. When slot 10 is accepted, persist the approval, increment the
setup revision, set `preparation_approved_revision` to that resulting current
revision, and set `defaults_reviewed: true` only if the displayed ordinary
defaults and deferrals were part of the approval.

Revision rules are strict:

- changing any design input from slots 1–7 clears both approval fields and
  returns to the reciprocity design review;
- changing only materialized preparation after the design remains accepted
  clears preparation approval and returns to slots 9–10;
- revising an already completed slot never increases `questions_completed`;
- a stale preparation approval cannot pass preflight or readiness;
- final readiness fields and derived projections do not create a new setup
  decision and must not advance `setup_revision` after slot 10.

# Immediate Persistence Map

Do not hold accepted answers only in memory. On the same turn as each accepted
decision, update its semantic owners, the readable decision log in
`session_zero.md`, `setup_revision`, and the active profile's
`source_setup_revision`. Do not run a full check after each answer.

| Slot | Immediate authoritative persistence |
| --- | --- |
| 1. Campaign Promise | `campaign_one_pager.md`; premise/summary in `world.md`; campaign id and Quick slot status in setup/session files |
| 2. Identity, Desire, Why Now | `player.md`; current motivation and desired experience; appearance stance in `appearance_guide.md` when known |
| 3. Competence, Limitation, Position | `player.md`; capability permissions/limits/cost/counterplay; initial social position and world-centrality stance |
| 4. Agency, Authorship, Boundaries | `boundaries.md`, `palette.md`, `player.md` authorship limits, and relevant `knowledge_boundaries.md` constraints |
| 5. Play/System Contract | modules, advancement, failure, and performance in `play_profile.yaml`; readable fit in `system_fit.md`, `rules.md`, and `progression.md`; `mechanics_state.json` only for approved stateful modules |
| 6. Presentation Contract | narration/dashboard/visual/World Voices policies in `play_profile.yaml`; `storytelling.md`, `visual_style.md`, `visual_gallery.md`, and resumable `visual_state.json`; derived projections wait for finalization |
| 7. Relationship Pattern | `player_ties.md`; the required character-originated, world-independent, intersection, place/routine, and independent-relationship design constraints; bounded draft references in `world.md`, `issues.md`, and `threads.md` |
| 8. Design Review | player-safe approved design summary and default/defer record in `session_zero.md`; approval reference in `player_ties.md`; current `design_direction_approved_revision`; preparation approval remains null |
| 9. Preparation Review | materialized semantic owners for the opening scale, including relevant world/issue/thread, place, character/faction, relationship, cast, route, state, `first_session.md`, and `opening_brief.md`; player-safe actual-preparation record in `session_zero.md`; readiness remains false |
| 10. Preparation Approval | current `preparation_approved_revision`, reviewed defaults/deferrals, slot status, and final Player approval in `session_zero.md`; this authorizes finalization but must not invent or first persist earlier content |

Conditional research status, evidence, open questions, risk, and current-scale
permission belong in `research_dossier.md` before dependent truth is locked.

# Starter Bundle Placement

Quick does not spend a separate slot on a Starter Bundle. After slot 1, use the
Player's campaign promise to prepare two to four contextual system/presentation
bundles as support for slots 5 and 6. A bundle may recommend linked choices,
but slot 5 and slot 6 remain separate decisions. Present each bundle as a
coherent card the Player can accept, mix, or change, and make every proposed
stateful mechanic and every optional presentation layer explicit inside it.

Each bundle may show:

- intended play feel and candidate setting/play lenses;
- `fictional`, `bands`, or `numeric` resolution grounding;
- mechanics that remain off unless explicitly accepted;
- three short Narrative Signature anchors and up to three avoid habits;
- interiority, at most two sensory priorities, dialogue balance, humor,
  emotional distance, breather frequency, and exit policy;
- tracking and expected speed effect;
- why one option fits the character and campaign promise.

With no stronger signal, recommend `fictional`, `player_owned`, balanced
dialogue, situational humor, close emotional distance, balanced breathers, and
`player_led_with_established_triggers`. Anchor prose on concrete sensory
evidence, character-specific plain dialogue, and causal consequence before
exposition. Avoid cryptic-default speech, recycled stock gestures/metaphors,
and tension manufactured after clean success.

Read only candidate briefs from `briefs/lenses/INDEX.md`. Fantasy alone does
not imply mana or HP; survival alone does not imply strict consumables. Ask for
explicit approval before enabling a stateful deterministic module.

# Required Reciprocity Core

The approved design and materialized preparation must establish all of the
following at the first playable scale:

- the character's current desire and why it matters now;
- a world affordance that lets the defining competence matter without making
  every scene a showcase;
- a real pressure, cost, blind spot, or counterplay channel for the limitation;
- at least one character-originated person, place, obligation, routine, or an
  explicit Player-approved isolation choice;
- at least one issue/domain/process that would exist and move without the
  character;
- a playable intersection where the character-originated and independent
  elements can affect one another;
- a place and baseline routine that explain belonging, access, or arrival;
- at least one NPC or faction with its own work, desire, obligation, and next
  move—not merely a hook dispenser;
- an opening whose routine, arrival, present people, and visible change are
  causally compatible;
- neutral action space that does not require accepting a quest;
- explicit backstory invention boundaries;
- an actionable opening and resumable scene frame under the accepted runtime
  and presentation contracts.

Infer only enough setting content for this core: a short campaign promise and
World Operating Model, three to seven playable truths, limited first-scale
faces/factions, one starting place, and one independent pressure or valid calm
affordance.

Quick still decides the world at macro scale, compressed to three to five lines:
the era anchor, who holds large-scale power, one or two movements that run
without the character, and the channel that makes them visible locally. Fill the
macro seats the setting implies with about three named figures at roster detail—
name and title, seat, one line of disposition and current movement—so later
mentions stay consistent. A roster figure graduates to a character note with a
filled Agency Card before it appears onstage or speaks. Every ordinary inferred choice receives a stable label in
`defaulted_decisions` and readable detail in `session_zero.md`.

# Preparation Materialization And Review

Immediately after slot 8 approval, freeze the approved direction and prepare
the actual opening scale while `ready_for_play: false`. Quick may use at most
two read-only proposal workers:

1. **world ecology:** truths, independent pressures/domains, factions, and the
   world side of competence/limitation counterplay;
2. **cast and space:** character-originated anchors, NPC/place cards, routines,
   natural presence, relationships, routes, and opening affordances.

The coordinator owns player/profile truth, knowledge classification, ids,
authoritative writes, current state, the final opening, and all approval fields.
If a lane is dependent or small, run it serially. Merge and leakage-check the
actual preparation before presenting slot 9.

The slot-9 review must be player-safe and concrete. Show names and facts the
Player may know, the character's opening context, relevant place/routine,
relationship positions, the independent pressure/process, the intersection,
capability and limitation affordances, naturally present people, visible
opening situation, several neutral action possibilities, and the player-visible
effect of ordinary defaults and deferrals. Do not reveal hidden motives, secret
maps, or unrevealed truths merely to prove preparation.

Ask slot 9 as a factual accuracy and completeness question about that prepared
truth. Slot 10 then asks a separate readiness go/no-go on the same unchanged
preparation together with the complete locked/defaulted/deferred record; it
never displays a default, prepared fact, or persisted answer for the first
time.

If the Player requests changes, revise the authoritative preparation while
not ready, increment `setup_revision` without adding a decision slot, clear any
preparation approval, and show the integrated review again. If the request
changes the approved design direction, clear both approvals and return to slot
8 first.

# Quick Performance Card

Present these as planning estimates, not guarantees:

- Fast: routine 30–90 seconds, ordinary durable 45–120 seconds, structural
  boundaries 2–4 minutes;
- Balanced: light 1–2 minutes, durable 1.5–3 minutes;
- Maximum Continuity: durable 2–4 minutes, structural 3–6 minutes;
- Dashboard refresh: about +1–2 minutes when triggered;
- image draft/revision: about +1–3+ minutes each;
- accepted gallery/Dashboard placement: about +1–2 minutes.

Selective semantic parallelism can shorten eligible preparation/research
boundaries but may increase model allowance use. It does not change normal
turn behavior or continuity requirements.

# Quick Finalization

After slot 10 records preparation approval at the current setup revision, load
`finalization.md`. Quick finalization must not perform first-time world/cast/
opening synthesis: that work was materialized and reviewed before approval.
It runs draft preflight, locks profiles/readiness without advancing the setup
revision, builds approved projections, takes the starting snapshot, and runs
the final aggregate check. If a substantive correction is required, return to
the appropriate review slot and obtain a fresh revision-bound preparation
approval before readiness.

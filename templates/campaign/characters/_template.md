# Character Name

In AI Companion mode, use `_companion_template.md` for the primary character.
Use this template for their social circle; read “player” as the user-facing
counterpart only where relevant, and keep every contact's life independent of
the user.

Write every value in the campaign's records language
(`play_profile.yaml.narration.records_language`, or the play language when it
is `same`). Keep the structure exactly as this template writes it: headings,
`- Label:` names, and enum values such as `alive`, `T2`, or `inactive`.

Tier: T1/T2/T3

First appeared:

Linked elements:

Power Band:

## Core

Stable identity facts that must survive a long session, a context reset, and a
time skip. Fill it for every T2/T3 character, and for any other character whose
status, kin, or form of address has mattered in play. Record only facts already
established in play or in an owner file; leave a line blank rather than invent
it. Keep each value on one line, and change a Core fact in the same commit as
the owner whose change caused it.

- Status: alive | dead | missing | unknown
- Pronouns and address:
- Kin:
- Role:
- Home:
- Speaks:
- Aliases:

`Status` holds exactly one of the four listed words; the cause and date of a
change go in `session_log.md`, not on this line. `Pronouns and address` gives
the pronouns used for this character and how others address them: title,
formal or familiar form. `Kin` names each relative with the relation and that
relative's status, such as `Name (sister, dead)`, separated by semicolons; a
dead or missing relative stays listed with that status. `Speaks` gives the
language, the register, and how this character addresses the player's
character. `Aliases` lists other names, titles, or nicknames people use for
them, separated by commas.

## Now

<!--
One short paragraph, at most 800 characters: the character's own situation as
of the latest revision, such as their condition, circumstances, and what is
pressing on them. Keep it consistent with the Agency Card's current task; it
adds the situation, not a second agenda. Facts another owner holds stay there:
in an RPG, `active_cast.md` owns where a tracked character is and what they are
doing, `knowledge_boundaries.md` what they know, and `relationship_map.md` how
they stand with others. Replace this section in place when it changes and never
add a dated copy beside it. Earlier states stay in `session_log.md`; when
stacked dated sections are consolidated, each superseded state may keep one
short line in a `## History` list.
-->

## At-The-Table Agency Card

Fill every field for T2/T3 characters. T1 characters may begin with only the
fields needed for their scene, then complete the card if player attention
promotes them. This compact card is the hot contract; longer notes below may
explain it but must not establish a competing current agenda or routine.

- Local role:
- Independent project:
- Current mundane task:
- Pressure decision rule:
- Misbelief or recurring mistake:
- Hard boundary:
- Non-player obligation:
- Voice rhythm:
- Social tactic:
- Routine and availability:
- Next move if ignored:
- Evaluation trigger:
- Visible consequence channel:
- Offscreen trajectory status: inactive

`Offscreen trajectory status` must be `inactive`, `active`, or `needs_review`.
Use `active` for a T3 or player-important T2 whose independent movement matters
after leaving the active cast. Evaluate it only when its recorded trigger
occurs; do not continuously simulate the character.

## Offscreen Trajectory

Required only when `Offscreen trajectory status` is `active`. An `inactive`
trajectory may remain blank. When legacy material cannot establish these
fields safely, use `needs_review` rather than inventing them during migration.

- Goal and method:
- Obstacle or resource:
- Time horizon:
- Result shape:
- Visible channel:
- Last evaluation id:
- Domain trajectory ref, if the shared process is owned in `world_dynamics.md`:

`Result shape` describes the bounded kind of change that could follow from the
recorded cause; it is not a predetermined outcome. Reevaluate only when the
Agency Card's Evaluation trigger occurs, and preserve the last evaluation id
for idempotent continuation.

This note owns the character's personal trajectory. A shared process involving
several actors belongs in `world_dynamics.md`. When that same process moves to a
domain, set the personal trajectory to `inactive`, archive its former evaluation,
and keep only the domain reference here; do not advance two current copies.
A separate, unrelated personal trajectory may remain active.

Before finalizing a new T2/T3, perform a model-only Contrast Pass against the
two most similar active NPCs. Compare local role, desire, risk response, social
tactic, voice rhythm, and hard boundary. If four or more axes substantially
match, redesign at least two axes. Persist the differentiated character, not a
scorecard, and do not add a semantic checker for this pass.

Also check whether the important voices would remain distinguishable without
their names: different occupations or goals alone do not establish different
speech. Shared faction language may be intentional; preserve individual choices
and social tactics around it.

## Depth

Fill for T2/T3 characters before their first long scene, from established fact
and the accepted setting; leave a line blank rather than invent it. Depth
explains the Agency Card and never competes with it: the card stays the hot
contract. In a campaign that tells its own story in a source work's world,
build the backstory from this campaign, not from a named canon figure, unless
the Player asks for that link.

- Backstory:
- Contradiction:
- Want and need:
- Fear:
- Dream:
- Joys and habits:
- Voice signature:
- How they could change:
- GM-only secret:

<!-- Age rule: no romantic or sexual relationship in this character's past or present begins before 18, and no age or duration written here may imply one; when the character's age changes, recheck every dated line. -->

`Backstory` is their history before play, with ages and dates where they
matter. `Voice signature` is one line naming what makes their speech theirs:
rhythm, register, a habit of address, a word they reach for. `How they could
change` names a direction play could earn, not a planned arc. `GM-only secret`
stays out of narration until play reveals it; once it matters, its fact belongs
in `knowledge_boundaries.md`.

## Agent Playability Card

Fill this only for an RPG T3 character considered for an Agent Seat. T3 is an
eligibility threshold, not automatic permission. Locations, factions,
GM-controlled antagonists, and characters without an explicit party-capable
role remain ineligible. `agent_roster.json` owns machine-readable readiness
and binding policy; this card owns the character-specific play contract.

- Candidate role: party_companion | party_member | persistent_ally | guest | ineligible
- Prioritized values:
- Short-term goal:
- Long-term goal:
- Decision rules under pressure:
- Contradictions and recurring mistakes:
- Self-authority: speech, movement, owned items, personal commitments, or narrower
- Forbidden authority: other characters, GM truth, world outcomes, or broader
- Knowledge-boundary refs:
- Relationship-map refs:
- Voice calibration examples:
- Stop/replan conditions:
- Readiness status: candidate | preparing | ready | paused | revoked | ineligible
- Prepared at continuity revision:

`bounded_full` autonomy never grants outcome authority. The character may
choose freely inside Self-authority. An out-of-authority proposal is rejected
and replanned; it is never silently converted into established fiction.

## Stats (Numeric Grounding Only)

Fill one entry per declared axis in `rules.md` only when
`play_profile.yaml.mechanics.resolution_grounding` is `numeric`. Under
`fictional`, describe competence, limits, leverage, and counterplay in prose.
Under `bands`, record only setting-appropriate broad bands; do not backfill
numbers merely because this template offers them. The axis names come from the
campaign's declared set, never from a fixed generic list, and numbers are only
needed where this figure's capability is actually contested in play.

- Axis: value

## Key Capabilities

What this character can do better than their raw stats suggest, including
powers, training, tools, social authority, local knowledge, or resources.

## Weak Stats / Blind Spots

Stats, situations, assumptions, or pressures where this character is notably
weak, overconfident, inexperienced, or easy to mislead.

## What They Can Reliably Do

Tasks this character should usually succeed at without the GM inventing extra
friction.

## What They Cannot Do

Things this character should not accomplish without help, leverage, special
conditions, or growth.

## Growth Ceiling For Current Stage

How far this character can reasonably grow before the campaign stage expands.

## Combat / Social / Influence Positioning

How this character performs in direct violence, social pressure, institutional
influence, stealth, investigation, or other conflict modes relevant to the
campaign.

## Represents

- Issues:
- Factions:
- Places:
- Player ties:

## Table Hook

One visible detail and one playable mannerism the GM can use immediately at
the table.

## Distinct Appearance

Five short lines that tell this character apart at a glance, in narration and
in an image prompt. Compare them with the two most similar cast members before
filling, and change at least two lines when they match. Keep them consistent
with the fuller Appearance card below.

- Face:
- Height:
- Build:
- Silhouette:
- Signature detail:

## Appearance

See `appearance_guide.md`. For T1 characters, keep this to 1 or 2 lines. For
T2+ characters, fill the compact card.

- First-glance read:
- Silhouette and build:
- Posture and movement:
- Face, hair, and eyes:
- Clothing and gear:
- Marks and history traces:
- Sensory tell:
- Mannerism:
- Image-generation anchor:
- Changeable details:
- Do not change:

## Default Posture

The character's ordinary social stance toward the player before new evidence
changes it. Choose something specific; suspicion is only one possible posture.

## Distinctive Lexicon

Words, images, class markers, jokes, silences, or habits that make this
character sound unlike other important NPCs.

## Do Not Sound Like

NPCs, factions, narrator habits, or stock voices this character should not
resemble.

## Metaphor Family To Avoid

Metaphor families that are overused in the campaign or belong to another
character.

## Plain Speech Sample

A simple, ordinary line this character might say without sounding cryptic or
polished. Write it directly in the campaign's play language, in the register
recorded under `Speaks`.

## Contextual Voice Examples

Use selectively for a T3 or player-important T2 whose voice needs calibration.
Two or three short examples are enough; leave this section empty for characters
who do not need it. These are examples of phrasing, not lines or gestures to
repeat, and do not establish new events, relationships, or known facts. Write
them directly in the campaign's play language.

- Ordinary request or practical answer:
- Refusal under pressure, with the boundary intact:
- With someone trusted, if that relationship is established:

Vary warmth, formality, openness, or sentence rhythm with the audience and
situation while retaining recognizable priorities. A warmer delivery does not
automatically change the character's decision principle or grant information.

## Earned Disposition Changes

Use only when events support a lasting change to a value, habit, or decision
principle. Temporary mood belongs with the current scene; attitude to a particular
person belongs in `relationship_map.md`. Neither alone rewrites the Agency Card.

- Changed disposition and scope:
- Supporting event references in `session_log.md`:
- What remains stable:

Update the affected stable field here, retaining the evidence reference. Keep the
event history in the log, not a second narrative here. A single betrayal need not
make the character distrust everyone; a justified change may remain specific to
one situation. Do not fill this section just to manufacture character growth.

## Public Face

What the player can perceive or learn easily.

## Visual Reference

- Image file:
- Visual status: none, draft, accepted, deprecated, or needs_regen.
- Prompt seed:
- Accepted visual canon:
- Do not change:

## Key Info, If Any

Important clue, offer, warning, or fact this character can provide. Keep it
separate from personality; not every NPC has key info.

## Knowledge References

`knowledge_boundaries.md` owns current known, suspected, unknown, and protected
facts. This character note owns only stable epistemic habits and references to
that ledger; do not copy the fact text here.

- Knowledge-boundary entry:
- Confirmed fact ids:
- Suspicion fact ids:
- Protected-name or reveal-ledger ids:
- Typical source types they trust:

## How They Read People

The visible cues this character notices, and the kinds of cues they often miss
or misread.

## Inference Limits

What this character cannot accurately conclude without stronger evidence.

## How They Test People

Questions, traps, rituals, social pressure, verification habits, or behavior
checks they use before trusting information.

## Communication Tendencies

Stable habits only; current messages, recipients, and knowledge belong to
World Voices and `knowledge_boundaries.md`.

- Preferred forms and channels:
- Audiences they address directly:
- Audiences they avoid or use intermediaries for:
- Delay, silence, and reply habits:
- Drafting, signing, quoting, or authentication habits:
- How voice changes between private and public communication:

## Dialogue Boundaries

Things this character must not say as fact without new evidence.

## Private Motive

What this character wants and why.

## Leverage And Vulnerability

What they can offer, threaten, hide, lose, or be pressured by.

## Status Play

How this character handles social status: raising their own, lowering someone
else's, protecting dignity, avoiding attention, or refusing the game.

## Relationship Behavior And References

This note owns the character's stable relationship behavior, not their current
attitude toward the player. `relationship_map.md` owns current relationship
truth and `session_log.md` owns historical changes.

- Baseline relationship behavior:
- Relationship-map edge ids:

Load the relevant current edge before an important recurring encounter. Respect
its topic, exceptions, and remaining repair conditions instead of treating one
global trust label as the whole relationship. This note references that truth;
it does not carry a second current relationship summary.

## Secret-Keeping Behavior And References

This note owns stable concealment, disclosure, and reaction habits. Current
secret truth and who knows it belong in `knowledge_boundaries.md`; current
relationship consequences belong in `relationship_map.md`.

- Concealment or disclosure habit:
- Knowledge/reveal fact ids:
- Relationship-map edge ids affected by revelation:

## Last Meaningful Interaction

Reference the most recent interaction that should affect future scenes, rather
than copying its history or current relationship consequences here.

- Event reference in `session_log.md`:
- Current relationship edge reference, when affected:
- When to recall it (person, subject, place, or unresolved condition):

## GM Use

How to make this character active at the table.

## Promotion Notes

Why this character should stay at the current tier or move up/down.

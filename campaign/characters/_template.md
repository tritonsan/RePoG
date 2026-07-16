# Character Name

Tier: T1/T2/T3

First appeared:

Linked elements:

Power Band:

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

`Result shape` describes the bounded kind of change that could follow from the
recorded cause; it is not a predetermined outcome. Reevaluate only when the
Agency Card's Evaluation trigger occurs, and preserve the last evaluation id
for idempotent continuation.

Before finalizing a new T2/T3, perform a model-only Contrast Pass against the
two most similar active NPCs. Compare local role, desire, risk response, social
tactic, voice rhythm, and hard boundary. If four or more axes substantially
match, redesign at least two axes. Persist the differentiated character, not a
scorecard, and do not add a semantic checker for this pass.

## Stats (Numeric Grounding Only)

Fill the eight numeric stats only when
`play_profile.yaml.mechanics.resolution_grounding` is `numeric`. Under
`fictional`, describe competence, limits, leverage, and counterplay in prose.
Under `bands`, record only setting-appropriate broad bands; do not backfill
numbers merely because this template offers them.

- Power:
- Agility:
- Endurance:
- Technique:
- Perception:
- Wits:
- Presence:
- Will:

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
polished.

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

## Secret-Keeping Behavior And References

This note owns stable concealment, disclosure, and reaction habits. Current
secret truth and who knows it belong in `knowledge_boundaries.md`; current
relationship consequences belong in `relationship_map.md`.

- Concealment or disclosure habit:
- Knowledge/reveal fact ids:
- Relationship-map edge ids affected by revelation:

## Last Meaningful Interaction

What happened most recently that should affect future scenes.

## GM Use

How to make this character active at the table.

## Promotion Notes

Why this character should stay at the current tier or move up/down.

# Opening Brief

Campaign id: `new_campaign`

Opening status: `pending`

Allowed values are `pending`, `active`, and `consumed`:

- `pending`: the next opening is still being prepared and may be incomplete;
- `active`: this file owns the next opening and may be checked against the live
  starting state;
- `consumed`: the opening has already been narrated and this file is historical
  evidence, not live scene truth.

This file is the GM's working source for the next player-facing opening. It
defines what the Player must know before acting, what should remain hidden, and
whether the opening is the first campaign scene or a post-arc bridge.

While status is `active`, this file is the sole owner of the next finalized
opening. `first_session.md` may supply drafting inputs until its prep status
becomes `materialized`; `session_brief.md` may reference this file but must not
copy its opening text. After the opening is used, mark both this file and
`first_session.md` consumed in the same durable checkpoint. A consumed opening
must not be compared to `current_state.yaml` for current location, present
NPCs, pressure, scene mode, or resume state.

For current RPG reciprocity routes, this file becomes `active` before the
integrated materialized-preparation review: Quick slot 9 or schema-v7
Standard/Deep module 20. Schema-v8 Deep materializes it in Stage 9 before the
single `fix | lock and start` preparation review. Its player-safe facts are
reviewed before the selected route's current-revision preparation approval.

## Approval References

- Route boundary: Quick slots 8–10 | schema-v7 Standard/Deep modules 19–21 |
  schema-v8 Deep Stage 9 gates | legacy final confirmation
- Setup revision:
- Design direction approved revision:
- Integrated materialized preparation accepted revision:
- Preparation approved revision:
- Opening changed after approval: no

## Opening Type

`first_campaign_opening`

Allowed values:

- `first_campaign_opening`
- `post_arc_opening`

## Scene Mode

`ambient`

Allowed values are `ambient`, `focused`, `crisis`, `aftermath`, `transition`,
and `breather`.

Frame the opening through this causal composition:

`baseline routine + scene mode + current disruption + naturally present people + player arrival`

Do not add local noise, clues, or an interruption merely to fill every term.
They are optional and must follow the place, mode, routes, availability, and
character arrival.

## Character–World Fit

- Character's current desire and why now:
- Why this opening fits this character:
- Character-originated anchor or explicit isolation:
- World-independent process:
- Playable intersection:
- Competence affordance:
- Limitation, cost, or counterplay relevance:
- Place/routine/belonging fit:
- Naturally present relationship and its independent agenda:
- Backstory invention boundaries honored:

## Where

The place where the character starts.

## What Kind Of Place

Describe what this place feels like, how it functions, what people normally do
here, and what the character can immediately understand about it. Preserve
ordinary life that is unrelated to the prepared intersection.

## When And How The Character Arrived

For a first campaign opening, state when the character arrived and the mundane,
personal, or chosen reason they are here. The reason must agree with the
prepared social position, access, route, and baseline routine.

For a post-arc opening, state how the last adventure led here, how much time
passed, and what changed during the transition.

## Player-Known Context

Facts the character and Player may know before choosing an action. Include only
approved character/world relationship facts and no hidden justification.

## Immediate Visible Situation

What is happening in front of the character right now. Show the intersection
only to the degree its signs are actually visible.

## Ongoing Local Process

What was already happening before the character arrived or acted. In a quiet
or empty place, record the routine, absence, recovery, or physical process that
still gives the scene independent logic.

- Independent owner/process:
- Baseline movement:
- Next movement if ignored:
- Visible channel:

## Capability Affordance

A natural feature, person, problem, or opportunity through which the defining
competence could matter. Do not force the Player to use it or turn every
approach into the same showcase.

## Limitation Relevance And Counterplay

A causal way the limitation, cost, blind spot, or opposition could matter. Do
not manufacture automatic failure merely to prove the limitation exists.

## Naturally Present People

For each present person, record why place, time, route, routine, and
availability put them here, plus the work/desire/obligation they have beyond
delivering a hook.

- Person:
- Why present:
- Independent agenda:
- Relationship position:
- What they do if ignored:

## Neutral Action Space

Natural things the character could decide to do without being pushed into one
fixed quest. Include ordinary/routine action, movement or observation, a way to
engage the character's own desire, and freedom to ignore or approach the
intersection. Do not write this as a player-facing menu unless the campaign's
storytelling preferences allow guided choices.

## Pressure Or Hook

A small pressure, opportunity, irregularity, or visible tension that makes the
scene alive without explaining the whole campaign plot. It may emerge from the
independent process, the character-originated side, or their intersection, but
must not erase unrelated local life.

For a `breather` opening, pressure may stay in the background. Offer ordinary
affordances without a menu or manufactured threat. Leave the scene when the
Player chooses a new goal, follows an affordance elsewhere, or a previously
established trigger genuinely comes due under the selected breather exit
policy.

This field may be blank when Scene Mode is `breather`. Campaign-level pressure
may remain active in `issues.md` or `threads.md` without becoming immediate
scene pressure.

## Do Not Reveal Yet

GM-only truths, hidden motives, future twists, faction plans, secret backstory,
or off-screen facts that should not be stated in the opening narration or the
player-safe integrated preparation review.

## Player-Safe Preparation Review Extract

A concise factual extract for the selected route's integrated preparation
review. It must match this active opening and may include only player-known
character, place/routine, relationship, independent process, intersection,
affordance, and neutral-action information.

## Player-Facing Opening Draft

Draft the first player-facing text here before checking it for leakage. It
should give the place, causal arrival context, visible situation, and natural
action space without a lore dump, menu prompt, forced quest acceptance, or
unsupported backstory claim.

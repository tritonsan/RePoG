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
defines what the player must know before acting, what should remain hidden, and
whether the opening is the first campaign scene or a post-arc bridge.

While status is `active`, this file is the sole owner of the next finalized
opening. `first_session.md` may supply drafting inputs until its prep status
becomes `materialized`; `session_brief.md` may reference this file but must not
copy its opening text. After the opening is used, mark both this file and
`first_session.md` consumed in the same durable checkpoint. A consumed opening
must not be compared to `current_state.yaml` for current location, present
NPCs, pressure, scene mode, or resume state.

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
They are optional and must follow the place and mode.

## Where

The place where the character starts.

## What Kind Of Place

Describe what this place feels like, how it functions, what people normally do
here, and what the character can immediately understand about it.

## When And How The Character Arrived

For a first campaign opening, state when the character arrived and the mundane
or chosen reason they are here.

For a post-arc opening, state how the last adventure led here, how much time
passed, and what changed during the transition.

## Player-Known Context

Facts the character and player may know before choosing an action.

## Immediate Visible Situation

What is happening in front of the character right now.

## Ongoing Local Process

What was already happening before the character arrived or acted. In a quiet
or empty place, record the routine, absence, recovery, or physical process that
still gives the scene independent logic.

## Neutral Action Space

Natural things the character could decide to do without being pushed into one
fixed quest. Do not write this as a player-facing menu unless the campaign's
storytelling preferences allow guided choices.

## Pressure Or Hook

A small pressure, opportunity, irregularity, or visible tension that makes the
scene alive without explaining the whole campaign plot.

For a `breather` opening, pressure may stay in the background. Offer ordinary
affordances without a menu or manufactured threat. Leave the scene when the
player chooses a new goal, follows an affordance elsewhere, or a previously
established trigger genuinely comes due under the selected breather exit
policy.

This field may be blank when Scene Mode is `breather`. Campaign-level pressure
may remain active in `issues.md` or `threads.md` without becoming immediate
scene pressure.

## Do Not Reveal Yet

GM-only truths, hidden motives, future twists, faction plans, secret backstory,
or off-screen facts that should not be stated in the opening narration.

## Player-Facing Opening Draft

Draft the first player-facing text here before checking it for leakage. It
should give the place, arrival context, visible situation, and natural action
space without a lore dump or menu prompt.

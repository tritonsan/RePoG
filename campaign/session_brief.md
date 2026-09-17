# Session Brief

Campaign id: `new_campaign`

Prepared from revision: 0

Use this as a light GM prep note before a session, scene chain, or arc. It is
not a plot script.

`current_state.yaml` is authoritative for current place, present NPCs,
conditions, inventory, and time. This file must not copy those facts as if it
were a second state file.

`opening_brief.md` owns the next finalized opening; `active_cast.md` owns
temporary NPC whereabouts and objectives; character/place/faction notes own
stable identity; and `world_dynamics.md` owns current offscreen domain motion.
Use references below rather than parallel summaries of those facts.

## Triggered Lookups

Open these only if the listed fictional signal occurs. Keep the set small and
use references to owners, not copies of their current facts. A name, an
established alias, a topic, a return to a place, or a due event can be a signal.

- Signal -> file or element:

For a consequential old promise, debt, knowledge limit, or dormant element
that would otherwise be hard to rediscover, use an optional named subsection
with these bullet fields:

| Field | Record |
| --- | --- |
| Lookup id | A stable local identifier for this pointer. |
| Signals | The established names, aliases, topics, or causal triggers that should cause a lookup. |
| Owner ref | One campaign-relative path with a heading or explicit id, such as `threads.md#arc-compass`. |
| Why now | A short applicability condition, not the answer or a planned outcome. |
| Verified at revision | The continuity revision when this pointer and condition were checked against the owner. |

An older brief can still lead to the correct owner. Treat its applicability as
unverified until the linked source is read; a changed source invalidates the
old condition, not the owner's truth. Recheck affected pointers on a relevant
return, scene handoff, or act preparation. Refresh or remove only those that no
longer apply. Do not refresh every pointer for an unrelated revision.

Legacy `Signal -> file or element` entries remain usable; add detail only when
needed. `workflows/reference/continuity-memory.md` owns discovery, ambiguous
matches, and missing-reference handling. A lookup miss is not proof that a
remembered event never happened.

## Due World Checks

Domains from `world_dynamics.md` that may need an on-demand refresh:

- Domain -> trigger:

## Player Focus

What the player seems interested in right now:

## Context References

The smallest triggered set likely to matter next:

- Active cast rows:
- Relationship rows:
- Knowledge boundaries:
- Rules or resources:
- Active Act id and Compass owner ref:
- Relevant closure-condition owner refs:

The live Compass remains in `threads.md#arc-compass`. Keep its current id and
references here when the campaign has adopted act ids; do not copy the dramatic
question or closure conditions into a competing authority. An id mismatch means
reload the live Compass and repair the pointer before using it. Older campaigns
without act ids keep their existing Compass until an explicit adoption boundary.

## Opening Or Scene-Entry Reference

- Source: `opening_brief.md` or `current_state.yaml.scene_frame`
- Relevant heading, scene id, or revision:
- Why this reference is likely to matter:

## Potential Scenes

- Scene seed:
- Scene seed:
- Scene seed:

## Secrets And Clues To Surface

Reference `secrets_and_clues.md`; do not bind every clue to one delivery path.

- Secret/clue id:

## Useful NPCs

Reference NPCs likely to matter; do not copy current activity or location from
the active cast.

- NPC:
  - Character note:
  - Active-cast row or presence trigger:
  - Knowledge-boundary entry:

## Live Locations

Reference places that may matter; baseline routine stays in the place note and
live disruption stays in `current_state.yaml.scene_frame` or its owning world
domain.

- Location note:
- Current-state or domain reference:

## GM Reminders

- Use ordinary speech.
- Suspicion is not the default NPC posture.
- Make one concrete fictional move at a time.
- Build on the player's ideas.

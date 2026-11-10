# Place Name

Tier: T1/T2/T3

First appeared:

Linked elements:

## Core

Stable facts about the place that must survive a long session, a context reset,
and a time skip. Record only established facts; leave a line blank rather than
invent it. Keep each value on one line, and change a Core fact in the same
commit as the owner whose change caused it.

- Status: intact | damaged | destroyed | abandoned | unknown
- Kind:
- Region or parent place:
- Held or run by:
- Access:
- Aliases:

`Status` holds exactly one of the five listed words. `Access` says who may
enter and on what terms; routes to and from the place stay in
`location_graph.md`. `Aliases` lists other names or spellings people use for
the place, separated by commas.

## Now

<!--
One short paragraph, at most 800 characters: the place's present condition as
of the latest revision, such as damage, repairs, closures, shortages, or a
changed routine. `## Disruption` names the pressure acting on the place; this
section says how the place stands now. Facts another owner holds stay there:
in an RPG, `active_cast.md` and `current_state.yaml` own who is present, and
`location_graph.md` owns routes and their conditions. Replace this section in
place when it changes and never add a dated copy beside it. Earlier states
stay in `session_log.md`; when stacked dated sections are consolidated, each
superseded state may keep one short line in a `## History` list.
-->

## Companion Grounding

Fill this compact card when the place belongs to an AI Companion's life. A
real-city campaign may use real public geography, but the companion's exact
home, workplace details, and private network remain fictional.

- Geography class: real_public | fictional_private | fictional_world
- City or region:
- Timezone:
- Companion's relationship to the place:
- Ordinary opening hours or availability:
- Regular people or roles:
- Routine activities:
- Travel relation to home/work:
- Privacy boundary:

## Scene Composition

When this place becomes a scene, compose it from:

`baseline routine + scene mode + current disruption + naturally present people + player arrival or action`

Choose the mode that follows the fiction:

- `ambient`: foreground routine, local life, and neutral affordances;
- `focused`: concentrate on the process intersecting the player's goal;
- `crisis`: show environment through immediate action, obstacles, and witnesses;
- `aftermath`: show costs, changed relationships, and disrupted routine;
- `transition`: compress low-risk passage while preserving meaningful change;
- `breather`: let ordinary care, conversation, rest, or small projects breathe.

Local noise, false leads, clues, and complications are optional ceilings, not
content quotas. A quiet, empty, closed, or recovering place can still have
independent life and causal logic.

## Represents

- Issues:
- Factions:
- Faces:
- Player ties:

## Sensory Identity

What the place feels, sounds, smells, and moves like.

## Spatial And Visual Description

See `appearance_guide.md`. Keep this image-ready, but do not turn it into an
architectural encyclopedia.

- First-glance read:
- Exterior or approach:
- Interior or primary area:
- Secondary areas:
- Navigation landmarks:
- Key props and affordances:
- Sound, smell, and motion:
- Texture and wear:
- Image-generation anchor:
- Hidden visual facts:
- Changeable details:

## Visual Reference

- Image file:
- Visual status: none, draft, accepted, deprecated, or needs_regen.
- Prompt seed:
- Accepted visual canon:
- Do not change:

## Reaction Point

The pressure, opportunity, visible change, or NPC action the scene should land
on so the player naturally wants to respond. In `ambient` or `breather` mode,
this may be a low-pressure affordance rather than a threat or hook.

## Baseline Routine

What normally happens here before the player or current pressure disrupts it.

## Disruption

What is currently disturbing, changing, or stressing the place.

## Independent Local Life

What happens here when the player is not pursuing the current main thread.

## Purpose In Play

Why the player would come here.

## Main Plot Touchpoints

How this place can connect to active threads without becoming only a clue board.

## Local Noise And False Leads

Unrelated tensions, ordinary business, misleading details, or side activity
that make the place feel alive. Use only when natural; do not force one into
every visit.

## Clue Exposure Gates

What player actions, risks, payments, questions, leverage, or time make harder
clues visible.

## Clues That Can Surface Here

Secrets or clues that could plausibly surface here, without being locked to
this place as the only route.

## Non-Quest Affordances

Things the player can naturally do here besides follow the main objective.

## Ordinary NPC Activity

What local people are doing that is not primarily about the player's goal.

## People Usually Present

Who belongs here, who visits, and who watches.

## Presence Logic

For recurring people, record why they would be here, what task or desire
occupies them, and which time, event, relationship, or disruption changes their
availability.

## Dangers

What can go wrong here.

## Common Obstacles And Difficulties

Use this for recurring or important obstacles in the place.

### Obstacle Name

- Resolution factor: fictional capability/permission, broad band, or numeric
  stat according to `play_profile.yaml.mechanics.resolution_grounding`.
- Difficulty: trivial, routine, challenging, hard, or extreme. With a declared
  `mechanics.resolution` scale, add the word's number from `rules.md` in
  parentheses, such as `hard (9)`.
- Why this fits the current campaign stage:
- Clean success:
- Partial success:
- Failure:
- Bypass, leverage, or alternate approach:

## Opportunities

What can be found, learned, stolen, protected, negotiated, or misunderstood.

## Connections

Other places that can be reached from here.

## Current Changes

How play has changed this location for good. The present moment belongs in
`## Now`.

## Promotion Notes

Why this place should stay at the current tier or move up/down.

# Active Cast

Campaign id: `new_campaign`

As of revision: 0

This is the hot tracker for NPCs who are present, nearby, travelling with the
player, or likely to act in the current scene chain. Character notes own stable
identity and baseline routine; this file owns temporary whereabouts and intent.

The Agency Card's `Next move if ignored` is the character's baseline
independent behavior. The table's `Next move if ignored` is only the immediate
scene-chain action from the NPC's current location and activity. Do not use
either field as a duplicate faction or domain clock.

| NPC | Tier | Current location | Current activity | Immediate objective | Availability | Reason here | Next move if ignored | Last seen | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| Example NPC | T2 | Example Place | Working | Finish the shift | evenings | employed here | close and leave | setup | 0 |

Remove the example row before play. Do not track the whole world here.

Before placing a recurring NPC in a scene, reconcile their last seen location,
elapsed fictional time, `location_graph.md`, and Agency Card availability. A
weak travel or presence reason produces absence, delay, a message, or another
plausible channel—not teleportation.

When a T3 or player-important T2 leaves this tracker, preserve its baseline
next move, evaluation trigger, visible consequence channel, and offscreen
trajectory status in its character Agency Card. If status is `active`, fill the
character note's Offscreen Trajectory goal/method, obstacle/resource, time
horizon, result shape, visible channel, and last evaluation id. Mark uncertain
handoffs `needs_review` instead of inventing them. Evaluate an active
trajectory only on elapsed-time, return, news, relationship-change, or
linked-domain triggers.

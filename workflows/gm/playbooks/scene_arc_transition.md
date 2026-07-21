# Scene And Arc Transition Playbook

Use this playbook for scene exits, pauses, structural closure, advancement, and
opening the next situation.

## Detect The Boundary

A scene transition occurs when location, time, active purpose, dramatic
question, or scene mode meaningfully changes. Do not declare a scene ended
merely because a conversation pauses or a calm beat lasts.

First resolve the Player's last action and any immediate consequence. Never use
bookkeeping as a reason to skip the causal result.

## Scene Checkpoint

At a scene end or interruption, after any required durable write:

1. keep or assign the stable `scene_id` appropriately;
2. record mode, prior local process, disruption, and the last causal beat;
3. retain at most three pending consequences;
4. update relevant active-cast whereabouts, activity, objective, availability,
   reason-here, and next move;
5. write the resume anchor: last Player action, direct result, last world/NPC
   move, and returned-control moment.

This checkpoint is not a full distill. Pure propagation creates no extra
continuity revision or durable event.

## Full Distill Triggers

Run the Distill workflow when:

- Fast reaches five durable turns;
- Balanced reaches three durable turns;
- Maximum Continuity completes any durable turn;
- the session pauses or ends;
- a scenario, arc, or campaign closes;
- an advancement/reward boundary requires reconciliation;
- a canon/research lock or continuity conflict must be resolved;
- the Designer explicitly requests it.

A scene end alone is not on this list. Before changing away from a batching
profile, reconcile all pending cold targets.

## Structural Parallelism

Scene exits, scene checkpoints, beat-closure reasoning, and session-closure
reasoning stay serial. They are not large enough to justify splitting causal
and voice ownership. A session stop may still leave a heavy cold-target
distill that independently qualifies under the Distill thresholds. A scenario,
arc, or campaign closure may use selective structural delegation only under
`workflows/orchestration/WORKFLOW.md` and the Distill workflow.

At an eligible major closure, the primary agent freezes the closing revision,
closure evidence, known facts, and entity ids. It may request at most these
read-only proposal lanes:

1. **Closure evidence and reward:** achievement tags, quality, budget, and
   fiction-grounded options. This lane cannot select or apply a reward.
2. **World and cast consequences:** only causally supported changes to NPCs,
   factions, relationships, places, knowledge, and pressure.
3. **Carry-forward and opening:** next-act classifications and possible
   reaction points, but only after every required reward choice that can affect
   the next act has been resolved.

The first two independent lanes may run together. The third is dependency
ordered: when a reward choice is required, do not start next-act preparation
or opening work until the Player chooses or the choice is explicitly deferred
as non-blocking. The primary agent alone writes `arc_closure.md`,
`next_act_prep.md`, `opening_brief.md`, current state, knowledge, revisions,
and logs; validates the consolidated result once; and presents it to the
Player. Stale, conflicting, incomplete, or failed proposals are discarded and
completed serially.

## Source Of Current Truth

- live scene and resume: `current_state.yaml.scene_frame`;
- next opening: `opening_brief.md`;
- stable NPC identity and decisions: character note;
- temporary NPC location/activity: `active_cast.md`;
- who knows what: `knowledge_boundaries.md`;
- offscreen domain motion: `world_dynamics.md`;
- systemic problem: `issues.md`;
- Player-facing dramatic question: `threads.md`;
- stable faction purpose/method/capacity: faction note.

Do not copy current truth into every file. Secondary summaries point to or
condense the authority and may wait for full distill.

## Cast Handoff

Remove NPCs no longer relevant to the scene chain instead of keeping the whole
world hot. When a T3 or player-important T2 leaves, preserve its triggered
offscreen trajectory. Do not evaluate that trajectory just because it was
written.

## Advancement

Read both cadence and presentation:

- `cadence: none`: no automatic review or gate.
- `presentation: automatic_fictional`: review and apply/present the earned
  change through consequences, access, capability, training, recognition, or
  another established fictional channel. Do not force an OOC interruption.
  Pause only when a required choice cannot be resolved fictionally.
- `presentation: explicit_ooc`: when a choice is required, open a short
  table-facing gate. If the Player defers, record it as deferred; do not choose
  or apply an upgrade and do not open a next act that depends on it. A calm
  aftermath/breather may continue while the choice waits.

Tie every reward to player action and an established fictional source. Do not
interrupt the middle of live danger to distribute it.

## Next Act

At scenario/arc/campaign closure, carry active truth through
`next_act_prep.md`; resolve required advancement; then prepare
`opening_brief.md`. Do not draft the new opening from stale session memory or
start dependent next-act play while preparation/choice remains unresolved.

Use a short player-facing bridge: what changed, how the character arrived,
elapsed time, present location, and what the character knows. Keep hidden
causes out. Then use the scene-entry playbook and return control at a concrete
reaction point.

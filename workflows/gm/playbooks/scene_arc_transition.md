# Scene And Arc Transition Playbook

Use this playbook for scene exits, pauses, structural closure, advancement, and
opening the next situation.

## Detect The Boundary

A scene transition occurs when location, time, active purpose, dramatic
question, or scene mode meaningfully changes. Do not declare a scene ended
merely because a conversation pauses or a calm beat lasts.

First resolve the Player's last action and any immediate consequence. Never use
bookkeeping as a reason to skip the causal result.

A scene boundary changes the frame; an act boundary answers a question. Read the
identified current Compass when the active brief's closure signals are touched;
do not substitute a past act's condition or wait for an award status to detect it. An act closes when the Arc Compass closure condition
in `threads.md` is either satisfied or made permanently unreachable—by whoever
did it, in whichever direction. The condition asks whether the act's question got
answered, not whether it got the answer someone hoped for, so closing on a
failure, a refusal, or an outcome nobody prepared is a real closure and not a
stalled act.

The action that satisfied or foreclosed the condition is the decisive action.
Record it in that Act id's Compass closure record with the resolved/foreclosed
condition and the revision it happened at. Set `Act status: closed` in the same
`commit-durable` transaction as the decisive outcome and its immediate owners.
Only include advancement changes if the accepted reward cadence actually applies.
Recognize it as it resolves rather than reconstructing it from the log afterwards;
a decisive action identified later usually credits the wrong turn.

Do not close because a scene ended well, a count was reached, or the act merely
feels long. Conversely, a refusal, failed plan, or new solution can answer or
foreclose the real question without delivering a prepared ending. A closed
Compass remains current during its aftermath and cannot close a second time.

## When Direction Seems Stalled

Use the Player's actual words/actions before treating a quiet stretch as drift.
One pause is not evidence of permanent disinterest, and no turn-count quota
requires a push. Choose the applicable response:

| Observed situation | Smallest useful response |
| --- | --- |
| The Player asks for help understanding | Restate already available evidence or the immediate affordance plainly; do not invent knowledge or decide the conclusion. |
| Their method is exhausted but the goal remains chosen | Offer a different causally available approach, price, contact, or angle; fixed evidence and accepted costs stay fixed. |
| They explicitly decline the hook or choose a different goal | Honor the new direction. Record the old thread as declined/deferred/dormant or transformed when its meaning actually changes; do not deliver the same demand through another NPC. |
| They choose quiet time or an unrelated project | Use the breather/downtime policy. Established world motion may proceed on its own due trigger, not as punishment or a pacing deadline. |
| Interest is genuinely ambiguous and affects the next commitment | Ask one short in-world or OOC clarification as appropriate; do not infer a lasting preference or repeatedly ask for reassurance. |

Actual external pressures retain their causes, schedules, and visibility channels.
Do not postpone a real consequence just to keep a path convenient, or accelerate
one to pull the Player back. Replan only unplayed possibilities. If a changed goal
answers/forecloses the act, close it; otherwise revise its open question only from
established choices without erasing costs or secretly replacing the campaign promise.

When a closure occurs, apply `advancement.md` before changing any reward status.
Only a matching accepted cadence creates a new due award. Preserve closure
evidence even when no reward is due; never let an act closure override cadence.

## Scene Checkpoint

At a scene end or interruption, first finish the causal result, then apply the
GM workflow's independent semantic-result and boundary decisions. Prepare one
checkpoint containing:

1. the stable `scene_id`, kept or reassigned appropriately;
2. mode, prior local process, disruption, and the last causal beat;
3. no more than three pending consequences;
4. relevant active-cast whereabouts, activity, objective, availability,
   reason-here, and next move;
5. the resume anchor: last Player action, direct result, last world/NPC move,
   and returned-control moment.

If the result is `durable`, include this checkpoint and its exact
`current_state.yaml` / `active_cast.md` mutations in the same
`commit-durable` payload. Use boundary `scene_checkpoint` unless a full-distill
trigger supersedes it; a `full_distill` payload may carry the same coincident
checkpoint. Never call `commit-checkpoint` after that durable transaction.

If the result is `soft`, invoke one `commit-checkpoint` transaction for this
resumability data only. Wait for either transaction to succeed before the
Player-facing bridge. A pure checkpoint is not a full distill and creates no
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
as non-blocking. The primary agent alone authors exact authoritative mutations
and submits any required `rpg_state.py` transaction, including new
`arc_closure.md` truth. Only after that commit does it apply consolidated
secondary Distill outputs to `next_act_prep.md`, `opening_brief.md`, and other
listed deferred targets, validate once, and present the result to the Player.
Stale, conflicting, incomplete, or failed proposals are discarded and
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

Follow the reward offer contract in `progression.md`. Three directions differ in
kind—capability, access or relationship, standing or identity—and each is written in
the Player's language with what becomes possible, its cost or limit, who notices,
its attention cost when recognition is tracked, and the one thing it opens next.
Name the fiction source. Offer one instead of three when only one is honest.

Stay inside the accepted system: declared axes on their scale under numeric
grounding, named bands under banded, recorded competence under fictional, and never
a mechanic the campaign left off. A new axis waits for a stage boundary.

Under fiction-carried presentation there is no menu, yet the same four points are
still owed in fictional language; a sheet that changes without the Player
understanding why is a failure, not a style. When the upgrade needs training,
downtime, travel, or a scene, record it as pending with its condition and let play
deliver it. Record which direction the Player took as a motivation signal.

Apply the transition matrix in `advancement.md` for cadence, presentation,
deferral, continuation locks, and next-act dependencies. Do not derive a second
gate from the status word alone.

Tie every reward to player action and an established fictional source. Do not
interrupt the middle of live danger to distribute it.

## Next Act

At scenario/arc/campaign closure, carry established truth into `next_act_prep.md`
and consult the advancement matrix before starting any preparation dependent on
an unresolved award. An independent aftermath remains playable.

At this boundary—not every turn—consider the accepted campaign horizon and the few
planted expectations touched by actual play:

- Which longer question could this next act affect, or is there no relevant link?
- How did the Player's expressed choices change that connection?
- What can happen here independently of that question?

Keep possible answers open. A horizon may continue, transform, or be deliberately
retired; a substantial change to the accepted campaign promise needs Designer
agreement. None of this requires a main plot for sandbox/episodic play.

Look up relevant Planted Expectations by source/evidence. Distinguish GM preparation
from material the Player really encountered. Carry, make available, pay off,
transform, or retire only what the actual result supports; never schedule a forced
payoff, treat an unshown plan as a shared memory, or surface every old debt at once.
A `must_return` item still needs its causal trigger and a credible visible channel.

### Activate The Successor

For an identified campaign, perform these steps in order:

1. Finish the current act's closure transaction. Keep its closed Compass/record
   intact while the successor is only draft preparation. Choose a fresh stable
   `Next act id` in `next_act_prep.md`, citing the closed `Previous act id`.
2. Prepare an open dramatic question, reachable scope, conditional climax access,
   and closure conditions from actual consequences and chosen direction. Preserve
   meaningful alternative answers, refusal, and failure. Record any relevant
   horizon/expectation references; do not author required scenes or outcomes.
3. When the new act is ready and any dependent choice is resolved or explicitly
   non-blocking, create one `threads.md` candidate that archives the closed Compass
   under `## Act Archive` / `### <old act id>` (nested headings become `####`)
   and replaces it with the new Compass:
   fresh `Act id`, `Act status: active`, `Previous act id` naming that archive,
   `Opened at revision` matching the resulting continuity revision, and an empty
   new Closure Record. Never reuse an archived id or its completed condition.
4. Commit that candidate and any changed immediate current-state/owner facts in
   one `rpg_state.py commit-durable` transaction with boundary `full_distill`.
   Advancing the act is durable even if no reward is due. Do not split archive
   creation from current-Compass replacement or manually increment continuity.
5. After success, reconcile the secondary `next_act_prep.md` references and prepare
   `opening_brief.md` with the new `Opening act id`. Keep it `pending` until its
   identity matches the committed active Compass and its frame is playable. Then
   set it `active` as the candidate opening and run the required full check before
   narration. If validation fails, return it to pending preparation and repair
   the mismatch; do not narrate or replay the already committed act activation. Prep/opening are
   secondary surfaces, not unsupported mutations in the RPG owner transaction.

An old `consumed` opening can retain its archived id until replaced; do not rewrite
history just to make every file mention the new act. If activation fails, the
previous committed state remains authoritative and no new act is narrated.

For an existing campaign without meaningful act ids, preserve legacy behavior and
raise the missing linkage at a safe Designer review. Do not silently invent ids,
revision provenance, or archive history. Deliberate adoption records the current
act as the first tracked one when past evidence cannot support a full archive.
New Session 0 materialization establishes the first id directly, with predecessor
`none` and opening revision 0 when no fictional turn has yet occurred.

Use a short player-facing bridge: what changed, how the character arrived,
elapsed time, present location, and what the character knows. Keep hidden
causes out. Then use the scene-entry playbook and return control at a concrete
reaction point.

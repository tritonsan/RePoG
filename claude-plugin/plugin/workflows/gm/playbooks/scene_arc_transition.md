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
Recognize it as it resolves rather than reconstructing it from the log
afterwards; a decisive action identified later usually credits the wrong turn.
The durable commit of that turn names it in its `established_delta`, so the
answer survives a restart. Close the act only after the scene that answered it
has ended, never in the middle of an exchange, and close it with one
`commit-act` call (Activate The Successor below), whose `close.summary` names
the decisive action and the revision it happened at. Only include advancement
changes if the accepted reward cadence actually applies.

Do not close because a scene ended well, a count was reached, or the act merely
feels long. Conversely, a refusal, failed plan, or new solution can answer or
foreclose the real question without delivering a prepared ending. An answered
act stays current through any aftermath played before its successor is ready,
and it closes once.

A thread or threat closes the same way: the commit that closes it gives its
owner a `Resolution:` line naming what resolved it, which is a roll id, a
Player decision, or a played scene. Nothing closes silently or off-screen, a
time skip included.

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
   and returned-control moment;
6. `open_choices`: one to five short strings naming what the Player can take up
   next, which the writer requires at a `scene_checkpoint` boundary.

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

- the durable count in `performance.cold_distill_policy` is reached: five
  under `scene_checkpoint_or_5_durable` (Fast and Balanced), three under
  `scene_checkpoint_or_3_durable`;
- Maximum Continuity (`every_durable`) completes any durable turn;
- the session pauses or ends;
- a scenario, arc, or campaign closes;
- an advancement/reward boundary requires reconciliation;
- a canon/research lock or continuity conflict must be resolved;
- the Designer explicitly requests it.

A scene end alone is not on this list. Before changing away from a batching
profile, reconcile all pending cold targets. At an act closure, the distill may
also launch the boundary curator (Distill workflow) to fold flagged notes; it
creates no truth and closes nothing.

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

Stat points from an act go only to axes the character actually rolled in it:
list them with `python tools/roll_dice.py --campaign campaign axes
--since-revision N`, where N is the act's `Opened at revision`; a receipt it
counts as `auto` took its band without dice. No award lifts an axis or a
Mastery level past the region cap in `progression.md` unless the Player
explicitly accepts the overreach, and that acceptance is recorded with the
award.

## Act-Close Review

Once the scene that answered the act has ended, and before the successor opens:

1. Review the Agency Card and Depth of every T2/T3 character seen in the act.
   Replace each field the act made untrue: a task finished, a fear faced, a
   secret out, a want met or abandoned. The capsule hides the Agency Card of a
   note no commit has touched since the act opened, so read such a note before
   giving its character a scene.
2. Review `issues.md`, `world_dynamics.md`, and the Planted Expectations in
   `threads.md`: what the act moved, resolved, transformed, or left waiting.
   Run `python tools/world_pulse.py --input-file -` once for the domains whose
   trigger the act made due, and give each timed threat of the next act an
   `active_clocks` entry in `current_state.yaml` (and, with the `clocks`
   module on, its clock through `add_clock`).
3. Under `explicit_ooc` presentation, offer the act-close menu out of
   character, in the Player's language: a table of the character's stats before
   and after the award, a suggested allocation the Player may change, and the
   time-skip options for the gap before the next act (none, a short montage, or
   skip until something happens; `travel_downtime.md`). Under other
   presentations the same content stays in the fiction, as the Advancement
   section above describes.

Put what the review changed in the `changes` and `mutations` of the
`commit-act` call itself, so the reviewed notes carry the new act's opening
revision; the award, the time skip, and the review share that one transaction.

## Next Act

At scenario/arc/campaign closure, carry established truth into `next_act_prep.md`
and consult the advancement matrix before starting any preparation dependent on
an unresolved award. An independent aftermath remains playable.

At this boundary—not every turn—consider the accepted campaign horizon and the few
planted expectations touched by actual play:

First read `player.md` / Player Experience Contract and Change Appetite, and the
relevant stable premises and limits in `player_ties.md`. Read changing NPC,
relationship, knowledge, and world facts from the owners those ties reference.
Compare the still-accepted experience with the Player's explicit new direction:
which connection remains useful, was deliberately revised, or can lie dormant?
Record only owner references and preparation rationale in `next_act_prep.md`.
New accepted preference or tie truth goes to its owner before dependent prep.
Do not infer a permanent preference from silence, failure, or refusing one offer,
and do not repeat Session 0 merely because an act ended. A changed immediate goal
may change this act's opportunities without changing the whole campaign contract.

Then consider:

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

For an identified campaign, perform these steps in order.

1. Wait until the scene that answered the act has ended. Choose a fresh stable
   `Next act id` in `next_act_prep.md`, citing the closing act as its
   `Previous act id`.
2. Prepare an open dramatic question, reachable scope, conditional climax access,
   and closure conditions from actual consequences and chosen direction. Preserve
   meaningful alternative answers, refusal, and failure. Record any relevant
   horizon/expectation references; do not author required scenes or outcomes.
3. When the new act is ready and any dependent choice is resolved or explicitly
   non-blocking, make one `commit-act` call (persistence playbook 3E). `close`
   gives the act id, whether its condition was met or foreclosed, and a
   summary naming the decisive action and its revision; `open` gives the fresh
   act id, a title, the dramatic question, the reachable scope, the closure
   conditions, and optional prepared expectations; `checkpoint` is the handoff
   into the new act's first scene, with its `open_choices`. The writer archives
   the closed Compass under `## Act Archive`, writes the new active Compass with
   its `Opened at revision` and an empty Closure Record, and commits both as one
   durable transaction at a `scene_checkpoint` boundary. Never hand-build the
   archive or the Compass, reuse an archived id or its completed condition, or
   increment continuity by hand. Advancing the act is durable even if no reward
   is due.
4. Carry the Act-Close Review in that same call: the award, the time skip, and
   every changed immediate current-state or owner fact go in its `changes` and
   `mutations`.
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

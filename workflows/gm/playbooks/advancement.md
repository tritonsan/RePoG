# Advancement Transition Contract

This is the sole procedure for advancement cadence, pending choices, continuation,
and next-act dependencies. Load on a closure or pending reward. Scene detection
and handoff remain in `scene_arc_transition.md`; reward appraisal belongs to the
Distill workflow. `arc_closure.md` is the current-state owner, not a second policy.

## Apply In Order

First finish the player's causal action. Identify the actual closure level from
its fictional condition, including failure, refusal, or permanent foreclosure.
A scene end or a count of turns does not establish an act closure.

Read the locked `advancement.cadence` and `advancement.presentation`, the current
reward status, and whether a new scene actually depends on an unresolved choice.
Use this matrix; an act closure alone never forces a reward.

| Condition | State and review | Permitted continuation |
| --- | --- | --- |
| Cadence `none`, or closure does not match the named cadence | Create no new `due` status or automatic reward review. Preserve any already-earned pending award from an earlier matching boundary. | Continue the causal aftermath or prepared next act. |
| Matching cadence, no award pending | Capture closure evidence and set `due` in the same durable transaction. Run the Distill appraisal once. | Do not skip the last action or interrupt live danger to offer rewards. |
| `due`, with no player choice necessary | Apply/present earned change through its accepted channel; record applied or the established realization condition. | No mandatory OOC pause. Narrate the resulting fiction after persistence. |
| `automatic_fictional`, choice required | Offer the actual choice through fiction if possible; otherwise ask a concise OOC clarification. Keep OOC-interlude metadata `not_applicable`. | Only effects and next-act preparation dependent on that choice wait. Independent aftermath/breather continues. |
| `explicit_ooc`, choice required and offered | Record `offered` and OOC `offered`; ask the bounded choice. Do not select an upgrade for the player. | Resolve the offered choice before a dependent effect. A request for quiet play or deferral is honored. |
| Player defers | Record `deferred`, the precise unspent award/amount and any dependency; apply no unchosen upgrade. Under explicit OOC set OOC `deferred` and clear the global fiction lock. | Aftermath/breather may continue. A dependent next act still waits; an explicitly independent next act may be prepared. |
| Player chooses | Commit the chosen reward and all affected owners/mechanics once. Use `chosen` while an established training/downtime condition remains, or `applied` when delivered. | Continue on the resulting state; do not narrate a pending capability as acquired. |

`session`, `scenario`, `arc`, and `campaign` cadence match their named boundary.
A larger closure does not silently stand in for a smaller one: if both occur,
record both as actual boundaries and appraise the earned award once. Presentation
`none` produces no automatic reward offer or OOC gate; do not manufacture an offer
from an otherwise disabled advancement contract.

## Continuation And Persistence

`due` or `offered` alone is never proof that all narration is blocked. Record the
concrete choice and what depends on it. The legacy `Fiction continuation locked
until advancement` field describes only the offered explicit-OOC interlude;
clear it on deferral. It never forbids an independent aftermath or authorizes a
next act that actually depends on an unresolved award. Automatic-fictional and
none presentation keep that flag `no`.

Advancement status, rewards, unspent amounts, realization conditions, and world
consequences are durable facts. Capture all immediate-owner changes in one
`rpg_state.py commit-durable` transaction with boundary `full_distill`, then finish
required propagation/checks. No manual revision or piecemeal reward write.

Do not start dependent next-act preparation while its required choice waits.
Once selected or explicitly deferred as non-blocking, carry current truth into
`next_act_prep.md` and the pending opening. Do not invent a climax or force a
reward to make the act fit a planned plot.

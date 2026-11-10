# 09 — First Act Preparation

## Purpose

Frame the first act, obtain design approval, materialize the actual opening-scale
campaign, cross-read it, and obtain readiness approval. Keep `ready_for_play`
false until the final gate sequence completes.

## Part A — First-Act Design

Ask one decision per message:

1. `09_first_act_frame` — choose the act's open dramatic question, active
   pressures, reachable scope, planted possibilities, and closure conditions.
   Both meaningful answers must remain playable.
2. `09_opening_shape` — accept, mix, or change a player-safe starting place,
   routine/arrival, visible situation, scene mode, pressure or calm affordance,
   competence/counterplay opportunity, and neutral actions.

Record each with the fields in `decisions.md`; recorded as `derived` or
`defaulted`, they depend on `01_creation_authority`. The two approvals have
their own order: `09_design_direction_review` is recorded only after
`first_act_design_complete`, and `09_preparation_approval` only after
`cross_read_passed`.

Write the accepted frame immediately to its design owners. For a new campaign,
assign its stable `Act id` and `Act status: planned` in `threads.md`, with
`Previous act id: none`. Keep any horizon link conditional and its Closure Record
empty; these are coordinator details, not another Player decision. No event chain,
required route, scheduled climax, predetermined outcome, or mandatory quest is
permitted. Draft a short, explicitly non-play narrative proof from this accepted
opening material. It must demonstrate the Stage 7 POV, tense, prose density,
sensory priority, dialogue balance, and Player-authorship boundary without
advancing fiction. Revise the runtime contract if the proof exposes a mismatch,
then pass `first_act_design_complete`.

If the Stage 9 portion of `campaign_architecture` is `active`, define its
first-act scope, reachable conditions, closure alignment, and carry-forward
references here before `first_act_design_complete`. Do not turn its multi-arc
possibilities into a schedule. Keep the portion structurally `active` until the
approved preparation materializes those owners; record its revision-bound
`complete` or explicitly accepted `defaulted` evidence when Stage 9 closes.

## Part B — First Player Approval

Present one integrated, player-safe synthesis of Stages 1–8, the first-act and
opening design, all active/defaulted extensions, and every visible default or
deferral. Ask only `09_design_direction_review` and wait.

Acceptance is Player approval 1 of 2. Record the design digest and resulting
revision, pass `design_direction_approved`, and freeze it. Any design or
extension change invalidates this and every downstream gate.

## Part C — Materialize And Cross-Read

While not ready, materialize the approved opening scale: player/current state,
world truth, independent issues, cast and place cards, relationships, knowledge,
routes/presence, first-session prep, active opening, and approved runtime state.
Set the first Compass `active` at its initial continuity revision (normally 0),
and set `opening_brief.md` / `Opening act id` to that same id. A preparation proof
is not an in-play discovery: mark an expectation planted only if it was genuinely
shown to the Player, with its actual review/turn evidence and knowledge boundary.
Keep the accepted narrative proof as presentation evidence; the actual opening
must follow it but is not narrated yet.
Use `storytelling.md` / Accepted Voice Evidence for why the selected behavior
fit. A real mismatch in another scene function can be calibrated within the
existing review; do not impose another sample quota or approval boundary.

Before review, internally check engagement, refusal, ordinary activity, and
leaving for causal viability. These are not four authored branches. Never
return a rejected hook through another NPC or accelerate independent events to
steer the Player back. Prepare only the detail the accepted scale needs.
Read-only proposal lanes are optional; the coordinator owns all writes, ids,
classification, and delivery.

Before the cross-read, calibrate every NPC card to the accepted NPC power
scale: each T2/T3 `Power Band:` inside the scale and its tier cap, and no stat
above its band. `finalize` refuses readiness while calibration warnings remain.

Record a materialization digest and pass `preparation_materialized`. Run the RPG
cross-read and player-facing leakage checks. Correct structural or consistency
defects before review; a correction that changes approved design returns to Part
B. Pass `cross_read_passed` only at the unchanged audited digest.

## Part D — Review And Second Player Approval

Show the actual player-safe prepared truth, all visible defaults and deferrals,
and the readiness implications in one integrated review. Show the concrete
affordance of relevant accepted choices, requested pressure and protected themes,
and independent/ordinary activity, using actual owner-backed preparation. Keep
that reasoning in `first_session.md` / Character–World Opening Fit and its
Player-Safe Integrated Preparation Review; never promise success or expose
hidden truth. Ask only
`09_preparation_approval`: the Player may request a correction or choose `lock
and start`. Acceptance is Player approval 2 of 2. At the same unchanged
revision and preparation digest it passes `integrated_review_accepted` and then
`preparation_approved`. Any substantive correction returns to the appropriate
earlier gate and invalidates this acceptance.

## Part E — Readiness

Complete Stage 9 with the approved preparation refs, then run
`session_zero_state.py campaign finalize --operation-id <id> --expected-revision
<current>`. It runs the readiness sequence in one call: draft preflight (zero
errors, and no NPC calibration, records-language, or age-rule warning),
`draft_preflight_passed`, profile locks at the resulting revision, the
`session-zero-start` snapshot, the ready evidence, and `ready_and_snapshotted`,
which atomically marks setup complete and ready. It stops at the first failing
step with a typed error, `failed_step`, and `completed_steps`; fix that step
and run it again with the current revision, and it resumes without repeating a
passed preflight gate. With approved projections (Dashboard, Atlas), run it
with `--stop-after lock_profiles`, build them, then run it again. Deliver the
opening only after the final gate, as `playbooks/finalization.md` step 8 says.

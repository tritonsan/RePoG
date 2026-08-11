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

Write the accepted frame immediately to its design owners. No event chain,
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
Keep the accepted narrative proof as presentation evidence; the actual opening
must follow it but is not narrated yet.
Read-only proposal lanes are optional; the coordinator owns all writes, ids,
classification, and delivery.

Record a materialization digest and pass `preparation_materialized`. Run the RPG
cross-read and player-facing leakage checks. Correct structural or consistency
defects before review; a correction that changes approved design returns to Part
B. Pass `cross_read_passed` only at the unchanged audited digest.

## Part D — Review And Second Player Approval

Show the actual player-safe prepared truth, all visible defaults and deferrals,
and the readiness implications in one integrated review. Ask only
`09_preparation_approval`: the Player may request a correction or choose `lock
and start`. Acceptance is Player approval 2 of 2. At the same unchanged
revision and preparation digest it passes `integrated_review_accepted` and then
`preparation_approved`. Any substantive correction returns to the appropriate
earlier gate and invalidates this acceptance.

## Part E — Readiness

Run draft preflight with setup `in_progress`, selected profile `pending`, and
`ready_for_play: false`. After zero errors, record `draft_preflight_passed`,
then use its resulting revision to lock the selected/unused profiles while setup
remains `in_progress` and not ready. Build approved projections and create a
content-bound `session-zero-start` snapshot. Append `snapshot_manifest.json` to
the returned snapshot path and convert it to a campaign-relative ref. Run
`prepare-ready-evidence` with that ref, the unchanged expected revision, and an
authorized readiness-report target; it performs the final aggregate check and
returns the validated evidence object. Record `ready_and_snapshotted` at the same
revision, passing that object unchanged through `--evidence-json`, its snapshot
digest as the output digest, and the preflight-gate digest as the input digest.
This final gate atomically marks setup complete and ready. Deliver the opening
only after the final gate.

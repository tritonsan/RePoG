# Deep Session 0 v8

This directory is the hot-loadable design corpus for a schema-v8 RPG Deep
Session 0. The main router activates it only for that route; it does not replace
Quick, Standard, Companion, legacy Deep, campaign owners, or validators.

## Load Contract

Load `manifest.json`, then only the playbook for the current stage. Load the
shared research, audit, orchestration, or finalization workflow only when the
active stage names that boundary. Do not keep all nine playbooks hot.

The stage order is fixed:

1. `01_north_star_authority`
2. `02_research_canon_grounding`
3. `03_character_core`
4. `04_thin_world_kernel`
5. `05_character_realization_mechanics`
6. `06_living_world_ecology`
7. `07_runtime_experience_contract`
8. `08_reciprocity_campaign_horizon`
9. `09_first_act_preparation`

Prerequisites and gate order come from the manifest, not from a guessed next
question.

## Interaction Contract

- Ask at most one unresolved consequential decision per message, explain why it
  matters, and stop.
- A clarification, factual correction, or `accept | mix | change` exchange stays
  inside the current decision.
- Never convert owner fields into a questionnaire. The Player chooses direction;
  the coordinator realizes bounded implementation detail.
- A critical decision is accepted only after its critical owner write succeeds
  in the same turn. If the write fails, do not assign a terminal decision status
  and do not advance the stage or revision.
- Complete each stage by materializing its remaining coordinator-owned detail.
  Finalization is not a deferred content dump.

## State And Extensions

Use only the status values in `manifest.json`. Every extension must be evaluated
as `not_applicable` or made `active` from a listed `controlled_trigger_tags`
entry. Unlisted interpretation may not activate an extension. An active
extension has one separately evidenced portion for every stage listed in its
manifest definition. The current stage's portion must become `complete` or
receive explicitly displayed and accepted `defaulted` output before that stage
can complete. A multi-stage extension may therefore remain `active` in its
aggregate view while a later portion is pending; that does not reopen a resolved
earlier portion.

For `mixed` ecology, Stage 1 records the primary topology. Stage 6 completes its
prerequisites before adding at most one secondary topology.

## Plot And Approval Boundaries

Stages 1–8 may create pressures, actors, places, relationships, capabilities,
questions, and possible horizons. They must not prescribe a first-act event
sequence, required quest, climax outcome, or fixed resolution. Stage 9 frames
the first act and opening as causal pressure plus neutral affordances, never as a
script.

There are exactly two Player approvals:

1. `09_design_direction_review` approves the complete design direction.
2. `09_preparation_approval` approves readiness on the unchanged, reviewed
   materialized preparation.

The second approval also accepts the factual integrated review: the Player sees
the real prepared package once and chooses `fix` or `lock and start`. The same
unchanged revision and digest then support `integrated_review_accepted` and
`preparation_approved`; there is no third Player approval. Any substantive
change invalidates the downstream gates named in the manifest.

## Final Boundary

After `preparation_approved`, run draft preflight while setup is still
`in_progress`, the selected profile is `pending`, and `ready_for_play` is false.
Record `draft_preflight_passed` only for a zero-error preflight; that gate
advances the revision. Lock profiles at the resulting revision, build derived
projections, and create a content-bound `session-zero-start` snapshot without
marking setup ready. Append `snapshot_manifest.json` to the returned snapshot
path and pass the campaign-relative ref to `prepare-ready-evidence` together with
the same expected revision and an authorized readiness-report target. The helper
runs the full candidate-ready check and returns the exact evidence object for
`ready_and_snapshotted`. Pass it unchanged to that revision-neutral final gate,
which performs the setup complete/ready transition.

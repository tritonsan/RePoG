# RPG Quick Session 0 — Schema v9

Load for `schema_version >= 9`, `experience_mode: rpg`, and `session_zero_mode:
quick`. Existing Quick setups keep their schema and contract unless the user
explicitly requests migration. Quick v9 has **nine unique decision slots**,
`question_target: 9`, and empty Deep pack lifecycle lists.

## Decision Order

Use the semantic content and immediate-owner mapping of numbered slots 1–8 in
`rpg_quick.md`, reading only the current slot and needed common sections. That
file's legacy ten-slot accounting, slot-9/10 approval split, and finalization
instructions do not apply to v9. This version owns order/counts and approvals.

1. Campaign Promise And Player Fantasy.
2. Character Identity, Current Desire, And Why Now.
3. Competence, Limitation, And Social Position.
4. Agency, Authorship, And Boundaries.
5. Play And System Contract.
6. Presentation Contract.
7. Character–World Relationship Pattern.
8. Reciprocity Design Review.
9. Preparation Review And Approval.

Use only `## RPG Quick v9 Decision Slot Status` in `session_zero.md`; do not
write the inactive legacy block. Slots are coherent design decisions, not a
promise of nine chat messages. Research permissions and clarifications can need
additional turns. Explain the current stage and remaining decisions without
claiming an unmeasured setup duration.

## Interview And Authorship

The router's shared interview contract applies: ask at most one unresolved
consequential decision per response. Accept early answers; never convert owner
fields into a questionnaire. Until slot 4 settles authorship, early character
work uses only volunteered facts and explicitly labeled proposals, not inferred
protected biography, interiority, or commitment. A later authority choice never
retroactively approves an undisclosed invention.

Keep safety permissions separate and explicit even within a slot. A bundle may
count once only when its elements form one meaningful choice; do not bury unrelated
permissions to maintain a number. Clarifications stay inside the pending slot.

Persist accepted semantic owners and the selected status row on the same turn.
The first completion increments the decision count; every accepted change
increments setup revision. No per-answer full check is added.

## Design And Actual Preparation

Slot 8 approves the complete design, including consequential defaults and
character–world reciprocity, setting `design_direction_approved_revision` to the
resulting revision. It does not approve unpublished preparation. Materialize the
approved opening scale while not ready, using the legacy playbook's Required
Reciprocity Core and materialization responsibilities, but not its second
preparation-approval turn.

Load `preparation_review_v9.md` for slot 9. Show and accept the audited actual
preparation once, then use `finalization.md`. A material correction clears the
appropriate approval and returns to review, never silently advances readiness.

Use `../reference` paths relative to the workflow root when reading ownership
references; Starter Bundle, mechanics, narration, performance, research, creation,
and privacy constraints remain unchanged. Optional features stay off unless
explicitly accepted. No numerical capability is overridden by an unrecorded
character concept or desired outcome.

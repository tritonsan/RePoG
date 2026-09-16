# Schema-v9 Materialized Preparation Acceptance

Load only for schema-v9+ RPG Quick or Standard at the preparation boundary.
This contract replaces the old separate factual-review and readiness-approval
turns. Existing schema-v6–v8 Quick and schema-v7–v8 Standard retain their old
contracts until explicitly migrated. Deep keeps its `rpg_deep_v8` ledger flow.

## One Display, One Acceptance

After the earlier design approval, materialize the actual opening scale while
`ready_for_play: false`. Freeze that direction/revision; eligible read-only
proposal lanes remain governed by the route and orchestration workflow.
The coordinator alone owns user truth, ids, knowledge, writes, and approvals.

Cross-read the prepared owners with the Audit workflow before showing them.
Every reviewed statement must already have its owner; do not show placeholders,
implementation fields, uncommitted proposals, or hidden fictional truth.
Show one compact player-safe package:

- the character, reliable competence, limits, and protected authorship;
- the setting and first-scale place/routine/access;
- current relationships and naturally present cast;
- an independent pressure or calm process and its intersection with the player;
- the actual opening and several neutral affordances, without prescribing action;
- the complete consequential locked/defaulted/deferred record, accepted optional
  features, and what starting now means.

Ask one decision: request corrections, or approve this prepared package and
proceed to readiness checks/start. This is both factual acceptance and readiness
permission. Never ask the player to approve the unchanged package a second time.
A request for a correction is not terminal acceptance.

## Persist Acceptance Once

For Quick, the combined decision is slot 9 in
`## RPG Quick v9 Decision Slot Status`. For Standard, it is module 20 in
`## RPG Standard v9 Module Status`. Its label is `Preparation Review And Approval`.

On acceptance, increment `setup_revision` once, increment `questions_completed`
only on the decision's first completion, and set `preparation_approved_revision`
to that same resulting revision. Record the actual-preparation review accepted,
`defaults_reviewed: true` only for defaults actually displayed, and the readable
approval/reference fields at that revision. The existing design approval stays
at its earlier revision. Keep readiness false until finalization succeeds.

Do not synthesize any new player-relevant truth between that acceptance and
preflight. No second acceptance, invented extra decision, copied inactive status
row, or phantom approval is needed. Final profile metadata/projections do not
increment the accepted setup revision.

A preparation-only change increments revision, clears preparation approval, and
returns to the combined review. A design change clears both approvals and returns
to design review first. A previously completed decision is never counted twice.
Use `finalization.md` after current-revision approval; retain its validation,
profile, snapshot, and recovery gates.

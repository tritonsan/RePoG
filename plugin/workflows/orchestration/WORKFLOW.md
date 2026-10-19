# Workflow

RePoG Selective Semantic Orchestration

# Purpose

Read this playbook only at a structural boundary that may qualify for
sub-agent delegation. It reduces wall-clock time by parallelizing independent
semantic reading and proposal work. It does not create a second engine, a
background process, or a new source of campaign truth.

The coordinating agent remains the only player-facing voice, decision maker,
and writer of authoritative campaign state. Supporting agents are read-only
analysts. If the active agentic tool cannot create sub-agents, perform the same
lanes serially; readiness and quality requirements do not change.

# Runtime Policy

Read `performance.semantic_parallelism` and
`performance.max_parallel_workers` from the active runtime profile.

- `off`: never delegate.
- `selective_structural`: use only the eligibility gates in this workflow.
- `aggressive_structural`: use the same safety contract with the lower
  thresholds explicitly documented by the calling workflow.
- A missing field is legacy `off`; do not silently increase an existing
  campaign's model usage.

`max_parallel_workers` must be between `1` and `3`. A calling workflow may set
a lower cap. Quick Session 0 has a hard cap of `2`; no RePoG operation may use
more than `3` supporting agents.

Delegation is a wall-clock preference, not a usage-saving feature. State in
the existing Session 0 performance summary that parallel semantic work may
finish a structural boundary sooner while using more of the host tool's model
allowance. Do not add a separate Quick question for this choice.

# Universal Eligibility Gate

Delegate only when all of the following are true:

1. the policy permits it and the harness exposes sub-agent capability;
2. the authoritative revision and applicable Player decisions are frozen;
3. at least two scopes can be completed independently from the frozen packet;
4. the calling workflow's concrete workload threshold is met;
5. no worker must decide Player intent, final narration, readiness, disclosure,
   reward selection, or knowledge truth;
6. the coordinator can merge every result before any authoritative mutation.

When any condition is false, continue serially without warning or failure.
Do not spawn merely to run a Python tool, validator, snapshot, dashboard patch,
Atlas compile, image transaction, dice roll, or browser smoke test.

# One-Layer Rule

The coordinator may create direct supporting agents. Supporting agents must
not create further agents. Use no more than the smaller of:

- the active profile's `max_parallel_workers`;
- the lane cap declared by the calling workflow;
- the number of genuinely independent lanes.

Prefer two well-bounded lanes to three partially overlapping lanes.

# Frozen Task Packet

Before delegation, the coordinator creates an in-memory task packet. Do not
persist orchestration bookkeeping into campaign memory.

```text
job_id
base_revision
experience_mode
boundary_type
scope
allowed_sources
frozen_facts
entity_ids
authority_owner
visibility_constraints
retrieval_policy
forbidden_actions
```

The packet must assign stable entity/fact ids before workers begin. A worker
that needs a new cross-domain id requests it in its result instead of
inventing one. Give each worker only the sources needed for its lane and mark
GM-only, player-known, companion-private, and public-surface material clearly.
This is a reasoning boundary, not an operating-system security boundary;
player-facing leakage checks remain mandatory where already required.

# Supporting-Agent Contract

Every supporting agent must:

- stay read-only;
- avoid file writes, state-changing tools, external messages, submissions, or
  any other external mutation;
- use read-only web/source retrieval only when an authorized frozen research
  packet names it in both `allowed_sources` and `retrieval_policy`;
- use only the frozen facts and cited campaign evidence;
- make no final readiness, canon, reward, relationship, or disclosure ruling;
- avoid player-facing prose unless the task explicitly requests a non-final
  draft for coordinator review;
- return a compact structured result.

```text
job_id
base_revision
scope
evidence_refs
proposed_deltas
requested_references
conflicts
unresolved_questions
visibility_classification
```

An empty section must be reported as empty rather than omitted. A proposal may
be complete Markdown/YAML content for its assigned target, but it is not truth
until the coordinator accepts and writes it.

# Coordinator Merge Contract

After every requested worker returns:

1. compare each `job_id` and `base_revision` with the frozen packet;
2. discard stale or mismatched results;
3. resolve cross-lane conflicts and allocate requested ids centrally;
4. decide knowledge/disclosure classifications and final semantic truth;
5. write authoritative current state and knowledge first;
6. write durable notes and domains;
7. write opening, closure, or carry-forward material;
8. update derived Dashboard, Atlas, Companion View, or World Voices surfaces
   serially and only when their own policy triggers;
9. run the one aggregate check required by the boundary;
10. create or refresh the snapshot only at the calling workflow's specified
    point.

All accepted changes from one boundary share one continuity revision. Cold
propagation does not create a second fictional event or revision.

# Failure And Fallback

- Worker unavailable or failed: finish that lane serially.
- Stale base revision: discard it; re-read and either rerun serially or issue a
  fresh bounded packet.
- Conflicting proposals: the coordinator resolves from authoritative evidence;
  never choose by majority vote.
- Incomplete result: use supported portions and finish the remainder serially.
- Aggregate validation failure: do not claim readiness, closure, delivery,
  visual placement, or Dashboard completion. Correct authoritative state and
  rerun the boundary check.

Never leave a partially merged setup marked ready or a partially merged
closure marked complete.

# Presentation

Sub-agent activity is invisible in RPG Player Mode and Companion Mode. During
Session 0 or an exceptional structural pause, the coordinator may give the
same brief latency notice already permitted by the active profile, such as
"I am preparing the world from your decisions; this may take a little while."
Do not expose agent counts, task packets, merge steps, file ownership, or
internal timing unless the Designer explicitly asks.

# Explicit Non-Delegation Paths

Keep these single-agent even under `aggressive_structural`:

- ordinary RPG soft and local-durable turns;
- scene checkpoints;
- ordinary Companion exchanges, including their single optional semantic
  commit;
- one image draft, revision, or visual acceptance transaction;
- one Dashboard/Atlas/Companion View update;
- mechanics, dice, snapshots, validators, and player-facing leakage checks;
- final opening narration and the companion's final conversational voice.

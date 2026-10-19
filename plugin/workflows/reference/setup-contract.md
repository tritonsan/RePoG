# Shared Setup Contract

Load during Session 0 only. The routed playbook owns version-specific counts,
review boundaries, and persistence. Never load this for ordinary play.

## Session 0 Invariants

While `setup_profile.yaml.ready_for_play` is false, route ordinary setup
messages through `workflows/worldbuild/WORKFLOW.md`, whether setup status is
`pending` or `in_progress`. Load only the experience- and depth-specific
playbook selected by that workflow.

If `experience_mode` is blank, ask only whether the user wants an RPG Campaign
or an AI Companion and persist the explicit answer. For a new schema-v10+ RPG,
next collect or reuse a short campaign intention, then separately ask the depth
choice in terms of joint design and preparation scope. Keep setup pending and
depth blank during this bounded intake; the premise grants no source retrieval,
world preparation, or protected-character permission. It belongs to the later
campaign-promise area and is not asked twice. Treat this as non-terminal intake:
record the provided answer without changing decision counters, setup revision,
or profile locks. The explicitly selected route then records its decision from
that answer at its normal boundary. Companion and earlier RPG routes
retain depth-before-pitch. Persist an explicit Quick, Standard, or Deep choice;
never infer either routing selector or combine its question with new content.
Record an explicitly supplied early routing answer rather than asking again.
Routing gates do not count toward content-decision totals.

The worldbuild workflow and its selected playbook own order, prompting,
persistence, research/finalization handoffs, and materialization. Schema-v8
Deep additionally uses its manifest as structural authority and loads only the
active stage playbook. This section retains only cross-mode Session 0
invariants.

### Shared Content and Materialization Invariants

Session 0 is setting-neutral. Begin from the user's accepted premise or
universe, canon or realism stance, tone and boundaries, desired experience,
and capability or expertise model. Derive setting-specific characters,
pressures, social structures, abilities, progression, and relationship
behavior only from accepted choices and permitted visible defaults. Do not
assume a franchise system, genre mechanic, power model, or relationship
trajectory.

A coherent Starter Bundle or other setup bundle may count as one content
decision only when its elements belong together. Show how it changes the
experience, what tracking or automation it adds, its performance or usage
trade-offs, and why it fits. Surface consequential defaults and do not hide
unrelated choices inside the bundle. A suggested mechanic never becomes active
without explicit approval; materialize accepted runtime choices in the active
profile.

Setting and play lenses are setup-only question and default aids, not runtime
instructions. They cannot activate a mechanic or override an accepted choice.
Persist their accepted results in the active profile and do not load lens
briefs during ordinary RPG play or Companion conversation.

Before locking source-sensitive world facts, capabilities, institutions, or
major entities, classify the research need and follow the research playbook
when grounding is required. Pending research or unaccepted uncertainty cannot
be promoted to durable truth. All external retrieval remains subject to the
External Instruction Boundary.

Record the accepted appearance-detail policy in `appearance_guide.md`.
Use only established, useful surface detail. Bodily measurements and a complete
appearance card are not a prerequisite for play; ask when the Player cares or
an actual upcoming dependency needs them. Unspecified protected facts remain
unspecified and do not justify an invented advantage, obstacle, or NPC judgment.

### Interaction and Readiness Invariants

During Session 0, the active agent may solicit at most one unresolved content
decision per response, explain why it matters, and wait before making an
unapproved consequential choice. Do not dump the remaining interview as a
questionnaire. Record explicit answers supplied early rather than asking for
them again; a coherent bundle may count as one decision only under the bundle
rule above.

The selected playbook owns the decision contract. Schema-v10+ RPG Quick and
Standard use complete required decision rows and ordered revision-bound
approvals, leave `question_target` blank, and treat `questions_completed` only
as progress/fatigue information. Earlier Quick/Standard, Companion, and legacy
Deep retain their numeric budgets. The Deep-v8 ledger uses stage completion as
readiness and treats its count only as a fatigue signal.
Across every depth, record agent-filled assumptions as visible defaults and
name deliberate deferrals. Schema-v8 Deep uses named stage extensions instead
of the legacy global pack ledger. No route may bypass safety, consent,
research, profile, or readiness requirements.

Explicit answers, unaccepted suggestions, uncertainty, rejection, and deliberate
deferral are distinct. A multi-answer message is recorded in dependency-safe
order; later-stage answers never bypass a prerequisite. Ask only an actual
unresolved consequential choice. "I don't know" is not acceptance; "enough"
stops optional expansion without granting missing consent or changing depth;
"pause" stops new questions and leaves the unresolved decision and next
dependency in the existing session summary. Resume from that position without
replaying the interview. Clarify only genuine contradictions; calm play and
detailed tracking, for example, are compatible.

Retain unselected candidates only inside accepted scope. An explicitly rejected
experience cannot return as a renamed hook; a deferral needs its actual accepted
condition. Do not erase established world truth merely because the Player does
not want that play focus. No row, pack, or preparation gate creates a detail
quota: add actors, routes, side effects, and exceptions for causal need.

The existing design review and actual-preparation acceptance remain the two
approval boundaries. Show the concrete player-safe affordance of relevant
accepted choices, with owner evidence, not guaranteed outcomes. Optional
resolution examples are out-of-play explanations inside the owning choice:
no real roll, resource use, character action, continuity write, or extra approval.
Local wording feedback does not become a persistent preference unless the
Player makes that scope clear. Narrowed boundaries apply immediately and only
affected preparation/approvals are revised.

Keep `ready_for_play: false` throughout drafting. Do not enter RPG play or
ordinary Companion conversation until the user approves the final setup
summary and the finalization workflow completes its documented preflight,
current-revision profile lock, required materialization, enabled projections,
starting snapshot, and aggregate validation with zero errors. If finalization
fails, restore the documented draft state and continue setup or repair; do not
narrate from a partially ready workspace.

Every RPG Session 0 depth must explicitly choose a turn protocol during System
Fit and store it under `play_profile.yaml.performance`. Companion mode instead
uses the fixed lightweight persistence choices in `companion_profile.yaml`.
For RPG, offer:

- `fast` (recommended): use `scene_checkpoint_or_5_durable` with
  `validation_policy: full_on_distill`; current truth is immediate, scene ends
  receive a continuation checkpoint, and secondary propagation plus the full
  check waits for five durable turns or another full-distill trigger;
- `balanced`: use `scene_checkpoint_or_3_durable` with
  `validation_policy: full_on_distill`; checkpoint scene ends and reconcile
  secondary propagation plus the full check after at most three durable turns;
- `maximum_continuity`: use `every_durable` with
  `validation_policy: full_each_durable`; reconcile every affected secondary
  note and complete the full check on each durable turn;
- `custom`: individual policies may change, but immediate authority writes,
  durable revision evidence, atomic candidate validation, and full validation
  at the selected boundary cannot be disabled.

Before the choice, explain typical planning ranges from ordinary agentic-tool
workspace use, which vary with the host tool, model, and reasoning level: Fast
routine turns about 30–90 seconds, Fast ordinary durable turns about 45–120
seconds, and structural/boundary turns about 2–4 minutes;
Balanced light turns about 1–2 minutes and durable turns about 1.5–3 minutes;
Maximum Continuity durable turns about 2–4 minutes and structural turns about
3–6 minutes. These are estimates, not guarantees. Also disclose that an actual
dashboard refresh may add about 1–2 minutes, an image draft about 1–3+ minutes,
and accepted-image gallery/dashboard placement about 1–2 minutes. Do not mark
Session 0 complete until the estimate caveat is acknowledged.

New workspaces default to `performance.semantic_parallelism:
selective_structural`. This may shorten independent structural work while
using more model allowance. It is not per-turn parallelism: ordinary RPG and
Companion messages remain single-agent. Quick shows this in the existing
performance summary without adding another question. When a structural
boundary qualifies, read `workflows/orchestration/WORKFLOW.md`; if the harness
has no sub-agent support, complete the identical lanes serially. The
coordinator remains the only campaign writer and player-facing voice.

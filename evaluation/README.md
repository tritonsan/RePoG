# Sustained Play Evaluation

These are replay fixtures and a recording protocol, not passed tests or a runtime
engine. Run them occasionally before release or after meaningful workflow changes.
Ordinary players do not encounter this machinery and ordinary turns gain no checker.
The structural Python suite and semantic replays answer different questions.

## Bounded Run

1. Use a disposable copy of the workspace, fixed model/reasoning settings, and a
   declared instruction revision. Never mutate a real campaign for evaluation.
2. First run `tools/gm_replay_suite.json` as described by the Audit workflow.
   The existing rubric and critical-failure thresholds remain authoritative.
3. For a sustained run, select `sustained_rpg.json` (36 player turns) or
   `companion_continuity.json` (12 timed exchanges). Give the acting agent only
   `initial_state`, `setup`, and one next `turn_sequence` entry at a time. Keep
   `evaluator_only` and result records out of its context until the run ends.
4. Resolve causally rather than aiming for a scripted answer. If an input becomes
   impossible because of an earlier valid choice, record that and use its declared
   conditional intent; never silently replace history to restore a planned plot.
5. Record each input, exact response, relevant tool result, turn wall-clock time,
   tool count, files read/touched, loaded context bytes when available, and committed
   revision. Distinguish actual usage reported by the host from estimates.
6. Honor the declared context-restoration checkpoints using committed owners only;
   do not pass the full prior transcript to the restarted acting context. Freeze an
   artifact manifest so the evaluator can verify what survived. A fiction-only
   replay without real persistence must say so and cannot pass the persistence lane.
7. After the last turn, send the untouched transcript, committed artifacts, and full
   fixture to a different evaluator. The evaluator cites response/artifact evidence
   for every score and records all critical failures. It may not repair the run.

## What To Record

Store actual results under a run-specific directory with a manifest naming fixture
version, instruction commit/diff digest, model/reasoning, date, execution mode
(`full_workspace` or `fiction_only`), evaluator, and limitations. Keep transcripts
local by default. Use synthetic fixture facts, never private real-user memories.
Do not commit user transcripts or secrets as demonstration data.

Report separately:

- semantic rubric scores and critical failures;
- state-restart agreement and any lost/mutated authority fact;
- routine/durable/structural turn median and p95 wall-clock time;
- tool calls, files touched, surfaced model usage, and context size;
- participant/evaluator comments about agency, voice, repetition, and immersion.

No transcript means no semantic result. Blank scoring fields are `unscored`, not
zero or pass. No instrumented time means latency `not_measured`. A successful
structural check is not evidence of enjoyable or natural play.

## Compare Changes

Run baseline and candidate from the same seed/answers using the same model and
settings, at least twice each when making a performance claim. For structural
parallelism apply `docs/semantic-parallelism.md` and its existing >=20% median
benefit/no-quality-regression criteria. Keep ordinary-turn negative controls.
Report small-sample limitations and the measured distribution, not universal
speed promises. Preserve a candidate only when critical agency/knowledge failures
do not regress; a faster but less faithful run is not an improvement.

Use findings for a small rule/owner correction, then replay the affected case.
Do not add transcript scoring or a second semantic judge to the runtime.

## Targeted Narrative Continuity Run

`narrative_continuity.json` is a bounded 22-turn alternative when testing act
identity, conditional promises, holder knowledge, topic-specific repair, macro
continuity, fixed evidence and calm play. Its player inputs deliberately avoid
reciting the rules under test. It adds no new runtime engine or per-turn judge.

Use the fixture's `runner_contract` in a disposable workspace. Restarts at turns
5, 10 and 17 must be actual new acting contexts. A continued conversation, context
compaction, or agent that already read the transcript does not qualify. Give the
new actor only committed owner files, a source-linked active brief, applicable
workflows and the current user message. Do not provide the preceding transcript,
evaluator expectations, scores, or a newly invented omniscient recap. Previously
spoken facts survive only through their ordinary committed owners.

Keep a per-turn trace of the precise loaded file hashes, source revisions,
context identity/provenance, exact tool request/result, changed owners and durable
receipt, response, and measured time where available. Keep the same operation id
for an identical uncertain retry and retain actual failures. If real persistence
or a new context cannot be demonstrated, mark that lane `not_verified`; a plausible
fiction-only transcript cannot substitute for it. Partial focused probes may report
only the turns/lanes actually run and must not claim the complete fixture passed.

Evaluate after freezing the run with a different reader/agent. The original nine
safety/continuity dimensions and critical breaches remain separate from the added
literary observations: recognizability, subtext and relationship scope, specificity,
macro coherence/transformation, earned payoff and reading momentum. These extra
0–2 evidence-backed dimensions have no automatic overall pass threshold. Do not
average away a critical authorship, knowledge, act-identity or promise-scope failure.
For claims of improvement, use blind paired comparison from the same seed/settings;
a single run provides observations only. No fresh run is bundled by this fixture.

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

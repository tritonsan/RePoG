# OpenAI Build Week — RePoG RPG Core

This file separates the pre-existing RePoG baseline from work completed for
OpenAI Build Week. It is an evidence index, not campaign memory and is never
copied into a running game's state.

## Baseline

- Baseline commit: `7ccfd90`
- Baseline product: the clean, single-campaign RePoG workspace on `main`
- Baseline verification: 249 repository tests passed; the blank campaign and
  Dashboard V2 checks completed with zero errors.

Only commits after this baseline are claimed as Build Week work.

## Build Week Goal

Build a focused RPG-core upgrade that uses GPT-5.6 for semantic work while
keeping hard invariants deterministic:

- contextual Session 0 choices and composable setting/play lenses;
- a compact materialized play profile;
- bounded dice and mechanical helpers;
- a validated visual interruption/return lifecycle;
- an adaptive, revision-aware Dashboard V3.

RePoG remains a local workspace. It does not require API keys and does not
claim API-only capabilities such as Programmatic Tool Calling or persisted
reasoning as product features.

## Evidence Ledger

| Change | GPT-5.6 semantic role | Deterministic enforcement | Verification / demo evidence |
| --- | --- | --- | --- |
| Contextual Session 0 and lenses | Infer useful campaign-specific options, combine lenses, surface conflicts | Profile, research, Deep-pack, and readiness validation | `python tools/verify_workspace.py`; Session 0/profile acceptance suite |
| GM routing and narration profile | Interpret fictional intent, resistance, voice, and consequences | Profile enums, campaign-aware knowledge checks, bounded hot/full validation | Four-phase workflow review; hot-context and POV/tense acceptance cases |
| Mechanics and dice | Decide when an established rule applies and translate results into fiction | Seeded dice, strict state operations, revision/idempotency checks | Seed/bounds/strict-integer tests and a 205-operation old-id replay test |
| Visual handoff | Preserve the interrupted setup/scene context in the conversation | Single pending transaction, dual asset copy, atomic rollback, gallery/dashboard validation | Begin/attach/accept and injected-failure rollback tests |
| Dashboard V3 | Curate player-safe summaries and adaptive widgets | Revision-aware patching, strict schema/assets/map/protected-name validation | Dashboard/server checks plus browser polling, map-state, text-atlas, and focus-restoration smoke tests |

## Public Workspace Verification

The downloaded workspace can verify itself without installing dependencies:

```bash
python tools/verify_workspace.py
python tools/verify_workspace.py --json
```

The command checks the distributable layout, parses bundled Python helpers,
runs the full campaign validator, and validates Dashboard V3. The JSON form is
intended for Codex, Claude Code, and other agentic tools.

Final implementation verification on July 16, 2026:

- development acceptance suite: `265 passed`;
- public dependency-free verifier: 0 errors, 0 warnings, one expected
  fresh-template `location_blank` info;
- dashboard validator and `serve_dashboard.py --check-only`: 0 errors;
- browser smoke: an update arriving after an unchanged polling cycle rendered,
  unrelated tile updates preserved map zoom and the open text atlas, and the
  visual dialog restored keyboard focus after Escape;
- Build Week range: `7ccfd90..HEAD` (baseline excluded by Git range syntax).

The development test harness remains outside the clean player ZIP. The public
workspace carries its own dependency-free verifier and all runtime guardrails.

## Submission Evidence To Record

- Codex task/session id: `019f4afe-8604-74e1-b604-5eace6fb6b9c`.
- `/feedback` submission reference: pending submission from this task.
- Final test counts and exact verification commands.
- Before/after screenshots of the same dashboard states and viewports.
- A public video shorter than three minutes with audio, showing a mixed
  fantasy-survival setup, explicit mechanic approval, a roll, visual approval,
  dashboard placement, and return to the interrupted scene.
- The final commit range beginning after `7ccfd90`.

Private campaigns, demo rehearsal notes, generated drafts, and user game data
must not be added to this repository.

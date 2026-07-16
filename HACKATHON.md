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
| Contextual Session 0 and lenses | Infer useful campaign-specific options, combine lenses, surface conflicts | Profile and readiness validation | Pending implementation |
| GM routing and narration profile | Interpret fictional intent, resistance, voice, and consequences | Profile enums, knowledge checks, bounded state validation | Pending implementation |
| Mechanics and dice | Decide when an established rule applies and translate results into fiction | Seeded dice, strict state operations, revision/idempotency checks | Pending implementation |
| Visual handoff | Preserve the interrupted setup/scene context in the conversation | Single pending transaction, asset/gallery/dashboard validation | Pending implementation |
| Dashboard V3 | Curate player-safe summaries and adaptive widgets | Revision-aware patching, strict schema/assets/map validation | Pending implementation |

## Submission Evidence To Record

- Codex task/session id and the `/feedback` submission reference.
- Final test counts and exact verification commands.
- Before/after screenshots of the same dashboard states and viewports.
- A public video shorter than three minutes with audio, showing a mixed
  fantasy-survival setup, explicit mechanic approval, a roll, visual approval,
  dashboard placement, and return to the interrupted scene.
- The final commit range beginning after `7ccfd90`.

Private campaigns, demo rehearsal notes, generated drafts, and user game data
must not be added to this repository.

# Changelog

All notable changes to RePoG will be documented here.

## Unreleased

### Added

- Standalone campaign workspace creation with an explicit runtime allowlist,
  optional local Git initialization, dry-run inspection, and safe refusal to
  overwrite non-empty targets.
- Quick, Standard, and adaptive Deep Session 0 paths with persistent setup
  progress, visible defaults, checkpoints, and a play-readiness gate.
- Optional Deep Character Foundation and Group / Company notes.
- Lite memory V2 with continuity revisions and coarse fictional time.
- `active_cast.md` for relevant NPC whereabouts, activity, availability,
  presence reason, and independent next moves.
- `location_graph.md` for travel, access, visibility, traffic, and route
  knowledge.
- Current-only relationship graph semantics and semantic continuity checks for
  stale prep, graph references, duplicate relationship pairs, research gates,
  NPC presence, and documented arc-earned stat exceptions.
- Optional visual mode, gallery, and organized campaign visual folders.

- Optional local auto-refresh campaign dashboard template.
- `check_dashboard.py` helper for dashboard state validation.
- Dashboard usage documentation and demo-script notes.
- `appearance_guide.md` and middle-detail appearance cards for player
  characters, NPCs, factions, and locations.
- Appearance continuity guidance for GM, worldbuild, distill, and audit
  workflows.
- Selective hot/triggered/cold context routing for GM turns.
- On-demand `world_dynamics.md` domains and deterministic `world_pulse.py`
  uncertainty envelopes.
- Optional deterministic `mechanics_state.json` with resource, ability,
  cooldown, regeneration, idempotency, and revision checks.
- Narration cadence preferences, bounded style fingerprints, and
  warning-oriented `check_style.py`.
- NPC routine, availability, presence logic, and faction next-move guidance.

## v0.1.0 - Public Starter Release

Initial public release candidate for RePoG as a GM workspace for agentic coding
tools.

### Added

- Codex-first `AGENTS.md` instructions.
- Lite workflows for worldbuilding, GM play, distillation, and audit.
- Markdown campaign template for long-form solo RPG play.
- Campaign memory files for worldbuilding, knowledge boundaries, NPCs,
  relationships, secrets, progression, arc closure, and next-act prep.
- Small Python helper tools for campaign checks, player-facing leakage scans,
  and snapshots.
- Public README, contribution docs, roadmap, issue templates, and generic
  starter examples.

### Notes

- RePoG is not a standalone app.
- RePoG is currently best tested with OpenAI Codex-style repo workflows.
- Example settings are original and generic, not tied to any copyrighted IP.

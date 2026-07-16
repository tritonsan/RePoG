# Session Log

Append-only dramatic memory. Do not rewrite old entries unless the Designer
explicitly asks for cleanup. Add corrections as new notes.

Every durable play result also receives a compact revision entry before the
next Player-facing response. These entries protect continuity while detailed
secondary notes wait for their selected distill boundary.

## Durable Event Format

### Durable Revision N

- Event:
- Immediate files:
- Pending cold targets: none

At a scene end, interruption, or handoff, append the compact continuation
checkpoint below after any durable entry that was actually needed. A scene
checkpoint does not increment continuity by itself and does not imply that
cold notes were reconciled.

### Scene Checkpoint Revision N

- Scene id:
- Scene mode:
- Resume anchor:
- Active-cast handoff:

After the pending cold targets have actually been propagated, append:

### Distilled Through Revision N

- Trigger: cadence limit, session stop, arc/advancement, research lock,
  continuity conflict, or explicit request
- Files reconciled:

Do not full-distill merely because a scene ended. Do not rewrite or delete
earlier durable or checkpoint entries after distillation.

## Opening State

- Date:
- Starting location:
- Present NPCs:
- Immediate pressure:
- Player-facing opening used from `opening_brief.md`:

## Entries

### Session 1

- Player choices:
- Consequences:
- NPC reactions:
- Threads opened:
- Threads resolved:
- Remember next time:

# Session Log

Append-only durable continuity memory. Do not rewrite old entries unless the Designer
explicitly asks for cleanup. Add corrections as new notes.

Every durable play result also receives a compact revision entry before the
next Player-facing response. These entries protect continuity while detailed
secondary notes wait for their selected distill boundary.

In AI Companion mode, a routine contact commit is not a durable fictional
event and does not enter this log. Append one Durable Revision only when a
life fact, presence, disclosure, relationship, promise, boundary, callback, or
consent-based user memory meaningfully changes. Do not store raw conversation
transcripts here.

For Companion entries, use ordinary relational language—life update, shared
plan, disclosure, disagreement, repair, boundary, or memory consent. Do not
invent an arc, climax, or dramatic pressure merely to make the log feel active.

## Durable Event Format

New writer-produced entries use the structured receipt below. `Established
changes` records the semantic capture, while `Immediate authorities` names the
files that own those facts. The log entry is recovery evidence; it is not a
second authority for the changed truth.

Existing entries that use `Event`, `Immediate files`, and `Pending cold
targets` remain valid append-only history. Do not rewrite them merely to match
the current format.

### Durable Revision N

- Operation:
- Cause:
- Established changes:
  - change_id [kind]: established delta
- Immediate authorities:
  - change_id -> `owning/file`
- Deferred propagation: none — no secondary surface affected
- Boundary: `ordinary`, `scene_checkpoint`, or `full_distill`
- Resume impact:
- Payload hash: `sha256:<64 lowercase hex characters>`

When secondary views or summaries may wait, replace the `none` value under
`Deferred propagation` with one line per affected change, target, and reason.
The owner of an established change is always an immediate authority, never a
deferred target.

At a scene end, interruption, or handoff, append the compact continuation
checkpoint below after any durable entry that was actually needed. A scene
checkpoint does not increment continuity by itself and does not imply that
cold notes were reconciled.

A standalone checkpoint records `Operation` and `Payload hash`. When the same
atomic durable commit also emits its checkpoint, replace those two fields with
`Source operation` and `Source payload hash`; this identifies shared evidence
without presenting the checkpoint as a second durable operation.

### Scene Checkpoint Revision N

- Operation:
- Scene id:
- Scene mode:
- Resume anchor:
- Active-cast handoff:
- Payload hash: `sha256:<64 lowercase hex characters>`

For a checkpoint paired with its Durable Revision, use instead:

- Source operation:
- Source payload hash: `sha256:<the paired durable payload hash>`

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

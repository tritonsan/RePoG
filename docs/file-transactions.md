# Local file transactions and recovery

Campaign meaning still belongs to the active agent. The local helpers protect
file ownership, expected revisions, operation identity, and the consistency of
the agent-authored write batch. They do not decide events, disclosure, memories,
or narration.

RPG, Companion, Deep Session 0, World Voices, Agent Seat, and snapshots share an
OS-managed writer lock at `campaign/.repog-transactions/.writer.lock`. Its file
normally remains on disk. Its presence is not a busy state: the operating
system releases the actual lock when the process exits. Do not delete this
file to unlock a running operation.

Companion multi-file updates, Session 0 bundles, and World Voices use prepared
and committed journals under `campaign/.repog-transactions/files/`. RPG also
recognizes its earlier transaction journals. Snapshots omit this entire
runtime directory and refuse to copy an unfinished transaction.

## Interrupted operations

Retry the original mutating command with the same operation id, expected
revisions, and original payload. Before reading state, the helper obtains the
writer lock and checks interrupted journals. A prepared batch is restored to
its original bytes; a committed batch is verified and its journal is cleaned.
The normal operation-id and revision rules then decide whether the retry is
already complete or can proceed. Read-only inspectors refuse pending batches;
they do not silently recover or advertise partial state as valid.

If a target or stored journal payload has been independently changed, recovery
stops with `recovery_required`. Preserve the journal and inspect the named files
in Designer Mode. Do not overwrite them or delete the journal to bypass the
guard. An unresolved earlier RPG journal must be recovered through the RPG
writer before another subsystem may write.

These guarantees cover process interruption and caught filesystem failures.
They do not claim a power-loss-safe multi-file filesystem commit or protection
against hardware failures. Keep explicit campaign snapshots for recovery.

## One-time migration of older sentinel locks

Older releases used `campaign/.session-zero-state.lock` and
`campaign/.agent_seat_state.json.lock`. New writers refuse these obsolete
sentinels with `recovery_required`. Confirm that the older helper process has
stopped, inspect any associated partial state, then remove only the named
obsolete sentinel and retry the original command. Do not remove a sentinel
while an older helper may still be writing. New OS-managed locks do not need
this cleanup after a crash.

## Companion authority batches

`commit-semantic` accepts optional `--owner-mutations-json` and
`--log-marker-json` arguments. The corresponding Python keywords are
`owner_mutations` and `log_marker`.

An owner mutation contains `path`, `expected_sha256`, and the complete proposed
`text`. Hash the current file bytes with SHA-256; the helper refuses stale
content. At most 16 owners may change, each under 500,000 characters and under
2,000,000 characters combined. Allowed root authorities are
`knowledge_boundaries.md`, `user_context.md`, `threads.md`, `world_dynamics.md`,
`boundaries.md`, and `relationship_map.md`. Typed Markdown notes under
`characters/`, `places/`, and `factions/` are also allowed. A new typed note uses
`expected_sha256: null`; its parent directory must already exist.

A log marker contains `expected_sha256` for `session_log.md` and `text` under
8,000 characters. It is appended without altering existing log bytes. It joins
the same transaction as the owner, state, and optional public View changes.
Do not write owners or append the marker before calling the helper. Owner-only
semantic changes advance continuity once; a marker alone is not a fictional
change and is refused. Existing calls without these extensions remain valid.

The agent remains responsible for memory consent, established facts, and
player-safe prose. Structured private fields are rejected from the public View;
the generic file transaction never copies an owner file into a public surface.

# Relationship Map

Campaign id: `new_campaign`

As of revision: 0

Use this file for current relationship truth only. Historical changes belong
in `session_log.md`. Keep at most one current row for the same directed pair;
use a bidirectional row when the relationship is genuinely shared.

Keep trust, debt, and tension specific to the subject when that matters: someone
can trust another's craft while refusing to lend them money. An accepted apology
may settle one incident while a key, promise, or access condition remains withheld.
Record the scope of the actual change, including what did not change; neither
one kindness nor one disagreement resets the entire relationship.

In AI Companion mode, this table maps the companion's family, friends,
coworkers, rivals, and other social contacts. Do not duplicate the primary
companion-to-user relationship here; its current qualitative evidence belongs
only in `companion_state.json`.

| From | Direction | To | Relation | Status | Trust / debt / tension | Knowledge asymmetry | Player-known | Last changed | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| Character A | <-> | Character B | working partners | active | cautious trust | A knows more | yes | setup | 0 |

Remove the example row before play. Location topology belongs in
`location_graph.md`, not here.

## Current Edge Detail (Only When Needed)

A short row is usually enough. For a relationship that needs scoped detail, give
the directed pair a stable edge id here and point its `Trust / debt / tension`
cell to that section. Put the current detail in one place, not both the cell and
the section. Character notes and scene lookup lists reference the edge id.

For that edge, keep only the relevant topic, current expectation or boundary,
cause reference in `session_log.md`, and unresolved repair condition if one is
actually established. Preserve qualifications: an apology accepted for one issue
does not erase another, and a promise may depend on a condition. A repair condition
is the NPC's current stance, not a guaranteed solution or a task imposed on the
Player. Unknown conditions can remain unknown.

Before an important reunion or returning to a disputed subject, read the relevant
edge and follow its decisive event reference when needed. Let the history affect
present behavior without reciting it every time. Archive superseded events in the
log; keep the edge's current scope and source reference. Never infer reciprocal
trust, forgiveness, or emotion for the player character.

# Relationship Map

Campaign id: `new_campaign`

As of revision: 0

Use this file for current relationship truth only. Historical changes belong
in `session_log.md`. Keep at most one current row for the same directed pair;
use a bidirectional row when the relationship is genuinely shared.

In AI Companion mode, this table maps the companion's family, friends,
coworkers, rivals, and other social contacts. Do not duplicate the primary
companion-to-user relationship here; its current qualitative evidence belongs
only in `companion_state.json`.

| From | Direction | To | Relation | Status | Trust / debt / tension | Knowledge asymmetry | Player-known | Last changed | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| Character A | <-> | Character B | working partners | active | cautious trust | A knows more | yes | setup | 0 |

Remove the example row before play. Location topology belongs in
`location_graph.md`, not here.

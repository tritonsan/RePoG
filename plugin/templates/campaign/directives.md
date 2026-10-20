# Directives

Standing instructions the Player gave out of character, kept as short rows
instead of prose rules that pile up and stop being followed. Each row holds one
directive, where it came from, and where it applies. Narration follows every
active directive in scope until the Player changes or retires it. While the
scene capsule is on, the GM sees the active rows in scope before each turn:
every `global` row and those for the current scene and for the characters,
places, and factions in play, at most 12, newest first. Keep that set small by
retiring a row once a newer one replaces it.

Directives are table preferences, not fictional truth. They never create
events, change what a character knows, or override `AGENTS.md`, safety
boundaries, or a locked profile. A request that changes a locked profile
setting goes through that profile's OOC change procedure instead.

- `Id`: `D-` and a three-digit number. Numbers count up in creation order from
  `D-000`, which is never assigned itself. Never reuse an id.
- `Scope`: `global`; `scene:<scene id>`, where the id is `scene_frame.scene_id`
  in `current_state.yaml`; or `entity:<name>`, where the name is the title of
  the character, place, or faction note.
- `Directive`: one imperative line, in the Player's words or a faithful
  paraphrase, specific enough to check a reply against.
- `Source`: where the Player asked for it, such as an OOC request and the
  continuity revision it arrived at.
- `Status`: `active` or `retired`. Retire a directive instead of deleting its
  row. A replacement gets a new id and its `Directive` names the id it
  supersedes.

Keep `|` out of every cell; it would split the row.

## Standing Directives

<!--
Illustrative rows only; they are not campaign truth and are not table rows.
A real directive is a row added at the end of the table below, written without
the "e.g." prefix and with a real id.

e.g. | D-NNN | global | Keep replies under 250 words unless a scene needs more. | OOC request, revision 12 | active |
e.g. | D-NNN | entity:Harbor Warden | The warden addresses the player's character formally. | OOC request, revision 30 | active |
e.g. | D-NNN | scene:night-market | Mention crowd noise only when it changes. | OOC request, revision 41 | retired |
-->

| Id | Scope | Directive | Source | Status |
| --- | --- | --- | --- | --- |

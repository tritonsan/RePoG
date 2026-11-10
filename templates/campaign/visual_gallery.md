# Visual Gallery

Campaign id: `new_campaign`

Use this file as the compact index for generated or accepted campaign visuals.
It is not a full art bible. Link each image to the campaign element it depicts
and keep canon notes short.

Status values:

- `draft`: generated or proposed, not canon yet.
- `accepted`: approved for reuse and visual continuity.
- `deprecated`: no longer current, but kept as history.
- `needs_regen`: useful concept, but should be remade.

Generation alone does not mean acceptance. `visual_state.json` and
`tools/visual_handoff.py` enforce the draft, review, acceptance, placement, and
return chain. A request to generate and add an image remains incomplete until
the accepted asset exists under the appropriate `visuals/` category and
`dashboard/assets/`, the dashboard references it when placement was requested,
and the saved return anchor is resumed.

## Visual Index

`Name | Type | Status | Image File | Linked Element | Prompt Used | Canon Notes | Last Shown`

- `Example | npc | draft | visuals/_drafts/example.png | characters/example.md | short prompt summary | not canon yet | never`

Accepted entries are added by the visual handoff tool. Keep draft rows here
only as a human-readable index; draft files must never be referenced by the
player dashboard.

## Accepted Visual Canon

Short notes for details that are now part of continuity.

- Element:
- Canon visual details:

## Deprecated Or Replaced Visuals

- Visual:
- Replaced by:
- Reason:

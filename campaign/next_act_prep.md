# Next Act Prep

Campaign id: `new_campaign`

Use this file after a scenario, arc, or campaign closure and before opening the
next major act. It is GM-facing prep, not player-facing narration.

## Prep Status

- Closure source:
- Previous act id:
- Next act id:
- Prep status: needed
- Advancement gate cleared: no
- Ready for opening brief: no
- Last reviewed:

Allowed prep statuses:

- `not_needed`
- `needed`
- `drafting`
- `ready`
- `used`

The ids refer to `threads.md`, which alone owns Compass state and history. Keep
this prep `drafting` while the successor is only a proposal. `ready`/`used` must
identify the committed successor and its archived predecessor; never copy the old
question/closure condition into a new act merely because the fields are nonblank.
No meaningful Act id means the legacy contract still applies; do not silently
migrate a live campaign.

## Carry-Forward Elements

List every past element that should shape the next act.

`Name | Type | Status | Why It Carries Forward | Must Affect Next Act? | Source File`

- `Example NPC | npc | active | Owes the player a dangerous favor. | yes | characters/example.md`

Useful statuses:

- `active`
- `resolved`
- `dormant`
- `transformed`
- `unknown`
- `must_return`
- `hold_for_later`

## Must Affect Next Act

Elements whose already-established consequences constrain the next act. Record
the causal trigger and visibility channel before surfacing them. `must_return`
is a continuity obligation, not permission to teleport an NPC, force a hook,
reveal a hidden fact, or make every carry-forward item appear in the opening.

- 

## May Return Later

Elements preserved for continuity but not forced into the next act.

- 

## Do Not Use Yet

Elements that remain GM-only, unresolved, offscreen, or too early to introduce.

- 

## Player And Companion State

- Player condition:
- Companion / ally condition:
- Current resources:
- Important items:
- Reputation:
- Known identities or covers:
- Injuries, debts, promises, or obligations:

## Open Threads To Carry

Reference `threads.md`. Keep this section short.

- Thread:
- Current pressure:
- Likely next move:

## Relationship And Knowledge Changes

Reference `relationship_map.md` and `knowledge_boundaries.md`.

- Relationship changes:
- Newly known facts:
- Still-hidden facts:
- Protected names or truths:

## Next Act Questions

Ask these in Designer Mode before locking the next act if the answer is not
already clear.

- Question:
- Why it matters:

## Next Act Frame

- Compass reference: `threads.md` / Act id
- Horizon reference, or none:
- What actual player choices changed in that connection:
- What this act leaves independent of the campaign-scale question:
- Relevant planted-expectation ids and due reasons, if any:

These are references and short preparation rationale, not second owners of the
question, closing conditions, or expectation statuses. Near possibilities may be
concrete; distant outcomes stay open. Carrying the campaign promise forward can
mean preserving, transforming, or explicitly retiring a question rather than
repeating the same hook. Do not infer a new preference from one quiet or failed turn.

- Scale:
- Starting place:
- Time jump:
- Travel or transition:
- Main pressure:
- Secondary pressure:
- Neutral action space:
- Tone shift:
- Expected play mix:

## Opening Brief Inputs

Use these to draft `opening_brief.md` as `post_arc_opening` with Opening status
`pending`. Its `Opening act id` names the proposed successor. Set it to `active`
only after that id matches the committed `active` Compass, this frame is playable,
and any dependent advancement choice is cleared; set it to `consumed` after the
opening is narrated. `first_session.md` remains historical and consumed.

- Previous consequence:
- How the character got here:
- Time passed:
- What the character knows changed:
- Immediate visible situation:
- Do not reveal yet:

## Prep Links

- `arc_closure.md`:
- `threads.md`:
- `creation_ledger.md`:
- `relationship_map.md`:
- `knowledge_boundaries.md`:
- `opening_brief.md`:
- `session_brief.md`:

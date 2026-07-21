# Visual Handoff Playbook

Use this playbook whenever image generation interrupts Session 0 or play. A
visible draft is not acceptance, persistence, dashboard placement, or the end
of the surrounding task.

## Before Generation

Tell the Player, before calling image generation:

- the next result will be the draft image by itself;
- whether explicit acceptance is required before canon/gallery/dashboard use;
- to reply with acceptance or concrete revisions;
- that a draft commonly adds about 1–3+ minutes, each revision repeats that
  cost, and accepted placement commonly adds about 1–2 minutes (estimates only).

Capture the interrupted context, last meaningful setup/scene beat, concrete
return anchor, next step, target, and requested dashboard placement. Call
`tools/visual_handoff.py campaign begin` before generation. Only one visual
transaction may be pending.

Do not ask for acceptance before the Player has seen the image.

Visual work stays serial. Do not delegate image generation, draft attachment,
acceptance, revision, cancellation, gallery updates, Dashboard placement, or
return-anchor restoration to a sub-agent. The primary agent must retain the
single transaction and interrupted context through every outcome; parallel
semantic proposals cannot shorten the external generation call and must never
race the atomic accept operation.

## Draft And Revision

Generate drafts under `visuals/_drafts/` and register the actual output with
the pending transaction. Treat revision requests as new drafts inside the same
handoff. Keep accepted visual canon and “do not change” appearance constraints
stable unless the Player explicitly revises them.

Do not reveal hidden appearance facts, protected identities, secret locations,
or GM-only visual information before the character could perceive them.

## Compound Requests

“Generate this and add it to the dashboard” has two stages:

1. generate and show the draft;
2. after explicit acceptance, run the transaction's atomic accept action.

Acceptance must copy the accepted asset, update `visual_gallery.md` and the
linked appearance authority, patch requested Dashboard V3 placement, validate,
and roll back on failure. Never claim gallery/dashboard placement unless every
requested stage reports success. A rejected or abandoned draft must not appear
as accepted canon.

## Return To Play

After acceptance, rejection, revision failure, or an explicit choice to stop,
restore the recorded return anchor. Clear the transaction only through its
documented atomic outcome.

- Session 0: briefly confirm the outcome, then continue the next pending setup
  decision.
- During a scene: restate the last meaningful fictional beat in one or two
  sentences and return control without advancing the scene.
- Between scenes: offer the already prepared next step or opening.

If the anchor is genuinely ambiguous, ask one clear continuation question. Do
not end with a bare technical confirmation or make the Player reconstruct where
play stopped.

## Dashboard Independence

Visual policy and dashboard refresh policy remain independent. An accepted
image enters the dashboard only when placement was requested and approved; a
dashboard refresh does not itself authorize visual generation.

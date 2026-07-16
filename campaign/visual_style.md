# Visual Style And Image Generation

Campaign id: `new_campaign`

Use this file only if the campaign wants optional generated visuals. Visual
generation can consume Codex usage limits, so it is off by default and should
be enabled only by an explicit Session 0 choice.

## Expected Time Cost

Present these as typical planning ranges, not guarantees:

- a dashboard refresh and validation can add about 1–2 minutes to an affected
  turn;
- one generated image draft can add about 1–3+ minutes;
- each image revision repeats the generation cost;
- placing an accepted visual into the gallery and dashboard can add about
  1–2 minutes after approval.

The Fast profile should default to dashboard refreshes at scene changes and
major player-visible changes, not ordinary dialogue turns. Before image
generation, state the expected extra wait together with the existing draft,
acceptance, and return instructions.

## Visual Mode

- Mode: off
- Quota stance: conservative
- Last reviewed:

Allowed modes:

- `off`: do not suggest or generate visuals during ordinary play.
- `manual_only`: generate visuals only when the Player asks.
- `major_only`: suggest visuals for major accepted elements only.
- `curated`: generate visuals for selected important elements after approval.
- `rich`: visual-heavy campaign; ask before larger batches or repeated use.

Quota stance:

- `conservative`: rare images; protect Codex usage.
- `normal`: occasional images for major moments.
- `generous`: frequent images are welcome, but still ask before batches.

## Generation Targets

Mark what this campaign wants visuals for.

- Player portrait:
- Companion portraits:
- T3 NPCs:
- T2+ NPCs:
- Major places:
- T2+ places:
- Factions or symbols:
- Important items:
- Vehicles, bases, ships, or homes:
- Arc splash images:
- Scene illustrations:

## Art Direction

- Suggested style:
- Medium:
- Realism / stylization level:
- Color palette:
- Lighting:
- Framing:
- Texture:
- Mood:
- Era or genre references:
- Things to avoid:

Codex should suggest an art direction that fits the campaign's universe, tone,
palette, and source/canon policy, then let the Player accept or revise it.

## Prompting Policy

- Prompt language:
- Default aspect ratio:
- Default image purpose:
- Reference images allowed:
- Batch generation allowed:
- Ask before generating if:

Keep prompts setting-neutral unless the campaign itself has chosen a specific
setting, canon, or art direction. Do not import a franchise art style into an
original world unless the Player explicitly wants that inspiration.

## Visual Canon Policy

Generated images are drafts until accepted.

- Draft details are not canon.
- Accepted details become visual canon only if they are recorded below or in
  the linked character, place, faction, or item note.
- If a generated image contradicts campaign memory, campaign memory wins.
- If the Player likes the image but not a detail, record the corrected canon.

## Visual Interaction State

`visual_state.json` is the authoritative interaction checkpoint. It permits one
pending draft at a time and preserves the interrupted context, last meaningful
beat, return anchor, next step, and requested dashboard placement. Do not copy
that changing state into this file.

Use `tools/visual_handoff.py` for `begin`, `attach`, `revise`, `accept`, and
`cancel`. A visual is not complete until the command returns a `resume` object
and the GM uses it to restore Session 0 or Player control.

## Display Policy

- Dashboard refresh policy:
- Show accepted visuals in Player Mode:
- Show draft visuals in Player Mode:
- Repeat existing visuals when an element returns:
- Keep visuals GM-only when:

Player-facing display should be brief and natural. Do not expose file paths,
tool names, prompts, quota language, or implementation notes in Player Mode.

Before generating a draft, run the begin step and use its player instruction:
the next result may contain only the image and the Player should reply with
acceptance or revisions. After the visual task, use the returned resume anchor
instead of ending with a bare update confirmation.

## Visual Continuity Rules

- Keep character appearance consistent after an accepted portrait.
- Do not regenerate accepted visuals without Player approval.
- If an element changes visibly through play, create a new version instead of
  overwriting the old accepted image.
- Store deprecated images as history unless the Player asks to remove them.

## Open Visual Questions

- Question:
- Why it matters:

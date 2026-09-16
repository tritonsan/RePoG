# Optional Surfaces Contract

Load only when an enabled Dashboard, Agent Seat, Companion View, or visual
handoff is triggered. The mode-specific playbook owns execution.

# Player Dashboard And Companion View

The Dashboard is RPG-only; Companion mode keeps it off. Companion may instead
use the independent `off | light` Companion View, which is updated only by a
semantic transaction containing a genuinely shared public-surface change. It
must never show private presence, relationship evidence, disclosure readiness,
hidden truth, user memory, or internal ids.

In RPG, the optional dashboard is a local player board opened through a
browser. Its campaign tiles remain read-only projections. When the Agent Seat
layer is active, the same-origin Table surface may additionally submit one
revision-guarded operational intent through `tools/agent_seat.py`; that intent
is not campaign truth and cannot write dashboard tiles or campaign owners.
The board may show current scene context, visible NPCs, companions,
player-known threads, known clues, inventory, a pan/zoom local atlas, accepted
visuals, player character state, and legitimately acquired World Voices
documents when that optional policy is enabled.

The dashboard must not show GM-only truth, protected names before reveal,
unrevealed clues, internal ids, file paths outside `assets/`, prompts, tools,
scripts, checks, YAML, Markdown, or explanations of how the campaign memory is
stored.

Dashboard V3 renders only the tile types selected in
`play_profile.yaml.dashboard.tiles`. Mechanics-light campaigns should not show
empty stat/resource tiles. Curate every tile from confirmed Player knowledge
and current perception. If a dashboard fact conflicts with campaign memory,
campaign memory wins and the dashboard should be corrected.

Map tiles may use the backward-compatible Atlas V1 contract. Atlas V1 separates
point, line, and area geometry from semantic campaign truth, and supports
`region`, `city`, `interior`, and `network` scales. Use `schematic` when only
topology is known and make the approximate nature visible; use `spatial` only
for approved geography. `play_profile.yaml.dashboard.map_skin` chooses
`auto`, `minimal`, `survey`, `civic`, `field`, or `systems`; a skin changes
presentation, never knowledge, access, risk, or location truth.

Follow `dashboard_refresh_policy`. The Fast default is
`scene_and_major_visible_change`: refresh for a scene/location change, visible
condition, important inventory, companion, known map, or accepted visual
change, but not for an ordinary dialogue-only turn. Balanced and Maximum
Continuity default to `every_visible_change`. `manual` and `scene_only` are
available only through an explicit Custom choice.

Use `tools/update_dashboard.py` for expected-revision atomic tile patches.
Keep `source_revision`, `scene_id`, refresh state, and refresh reason current;
reject stale writes. When player-known geography changes, use
`tools/compile_map_atlas.py` to derive the map tile from `location_graph.md`
and optional stable atlas geometry. Do not run it for dialogue-only or other
map-neutral turns. The atlas is not a secret map: every feature, route, area,
label, image, and summary must be player-known or directly perceivable.
Unknown features are omitted rather than dimmed because their geometry itself
can leak information. Use `assets/...` relative paths only. V2 dashboards and
legacy V3 node/edge maps remain readable through compatibility adapters.

The optional `documents` tile reads only the paginated player projection below
`dashboard/assets/world_voices/`. Hidden artifacts are omitted entirely from
files, counts, search, and comparisons. The private manifest and bodies never
enter browser paths. Compare Accounts may contrast only player-known claims and
must not announce objective GM truth. Document replies and other campaign
actions remain natural-language play, not Dashboard writes.

Do not mention dashboard file updates in Player Mode. If the Designer asks how
to open it, use Designer Mode and point them to `docs/dashboard.md`.

# Visual Generation Handoff

Image generation is an interruption, not the end of Session 0 or play. Because
an image result may appear without a following text message, set expectations
before generating: say that the next result will be the draft image by itself,
explain whether acceptance is required before canon/dashboard use, tell the
Player to reply with acceptance or revisions, and record the setup or scene
beat that must resume afterward. Call `tools/visual_handoff.py campaign begin`
before generation so `visual_state.json` owns that return anchor.

The same pre-generation message must state that a draft commonly adds about
1–3+ minutes and that each revision repeats the generation cost. If accepted
gallery/dashboard placement was requested, disclose its typical additional
1–2 minute cost. Keep these as estimates, not guarantees.

Treat "generate this and add it to the dashboard" as a two-stage request:
generate/attach a draft, then after explicit acceptance use the visual
transaction's atomic `accept` action. It must copy the accepted asset, update
the gallery and appearance note, patch the requested Dashboard V3 placement,
and validate the result with rollback on failure. Never claim it was added
unless the tool reports every requested stage complete.

After visual work, do not end with only "updated" or "added." During Session 0,
continue the next pending step. During play, briefly restate the last fictional
beat and return control to the Player. If continuation is ambiguous, ask one
clear question about returning to the paused scene. Read
`workflows/gm/playbooks/visual_handoff.md` for the complete transaction and
return protocol.

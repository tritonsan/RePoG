# Optional Surfaces Contract

Load only when an enabled Dashboard is triggered. The mode-specific playbook
owns execution.

# Player Dashboard

The Dashboard is RPG-only; Companion mode keeps it off.

In RPG, the optional dashboard is a local player board opened through a
browser. Its campaign tiles remain read-only projections.
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

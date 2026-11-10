# Deep v8 Decision And Gate Contract

Load when recording a Deep v8 decision, completing a stage, or recording a gate.
`tools/session_zero_state.py campaign stage-owners --stage-id <stage>` prints the
same contract for one stage straight from the manifest, with each decision's
owner files and whether it is already recorded. `record-decision` reports every
contract problem of one call in a single error, and `complete-stage` every
failed stage check: the `problems` list gives each one with its category, so
fix them together and retry once.

## Setup Before Stage 1

1. `set-depth --depth deep` persists the Player's explicit depth, sets status
   `in_progress`, and initializes the ledger mirrors and the managed summary.
   Never edit these fields by hand.
2. `set-language --language <code>` settles the play language in
   `play_profile.yaml` `narration.language`. `set-depth --language <code>` does
   both in one call. A new Stage 1 decision and Stage 1 completion are refused
   while the language is unset or `auto`.

## record-decision Fields

| Field | Rule |
| --- | --- |
| `operation_id` | Short stable id (`A-Z a-z 0-9 . _ -`, at most 128). Retrying the identical payload with the same id is idempotent; reusing it with other input is refused. |
| `expected_revision` | The current setup revision (`status`). |
| `decision_id` | The manifest id. |
| `stage_id` | The decision's own manifest stage. A new decision is accepted only in the current stage while it is `active` or `needs_review`. |
| `status` | `locked`, `defaulted`, or `deferred`; `deferred` only where the manifest sets `defer_allowed`. |
| `source` | `player`, `derived`, `defaulted`, or `deferred`. |
| `value` | A JSON object. The structured decisions below have required fields; any other decision takes a short summary object such as `{"summary": "..."}`. |
| `depends_on` | Ids of recorded, non-deferred decisions from the same or an earlier stage. No self-dependency, no cycle, no duplicates. |
| `trigger_tags` | Only manifest `controlled_trigger_tags`, no duplicates. A tag activates its listed extensions at its listed depth. |

Revising a recorded decision with a new value reopens its stage and stales the
gates after it; recording the same value again is refused as `no_change`.

## Structured Decisions

| Decision | Required value | Other rules |
| --- | --- | --- |
| `01_creation_authority` | `{"mode": "approval_first" \| "bounded_inference" \| "broad_world_preparation"}` | `status: locked`, `source: player`. |
| `01_primary_topology_intent` | `{"primary_topology": "exploration_survival" \| "political_intrigue" \| "personal_drama" \| "mixed"}`; for `mixed` also `"primary_branch"`, one of the three others | |
| `02_research_need_and_permission` | `{"status": "not_needed" \| "needed_pending" \| "partial_complete" \| "complete" \| "unavailable_risk_accepted", "permission": "not_needed" \| "approved" \| "declined"}` | |
| `02_current_scale_lock` | `{"risk_accepted": true \| false, "current_scale_lock_permitted": true \| false, "npc_power_scale": "closed" \| "region_anchored_open"}` | `depends_on` includes `02_research_need_and_permission`. `npc_power_scale` is required whenever this decision is recorded. |
| `06_topology_activation` | `{"primary_topology": <the Stage 1 value>, "build_order": <that topology's manifest order>}`; for `mixed` also the Stage 1 `"primary_branch"` | `depends_on` includes `01_primary_topology_intent`; `trigger_tags` include the topology's activation trigger. |
| `07_agent_seats` (setup schema 10+) | `{"mode": "off" \| "on_demand"}` | `status: locked`, `source: player`; `play_profile.yaml` `agent_seats.mode` must match before Stage 7 completes. |
| `09_design_direction_review` | Player approval 1 | Needs gate `first_act_design_complete`. |
| `09_preparation_approval` | Player approval 2 | Needs gate `cross_read_passed`. |

Topology build orders and activation triggers:

| Topology | `build_order` | Trigger tag |
| --- | --- | --- |
| `exploration_survival` | `["places_and_routes", "independent_pressures", "institutions", "npcs"]` | `play_focus.exploration` |
| `political_intrigue` | `["independent_pressures", "institutions", "reach_and_places", "representatives"]` | `play_focus.political_intrigue` |
| `personal_drama` | `["everyday_places", "institutions", "npc_relationships", "independent_pressures"]` | `character.deep_personal_integration` |
| `mixed` | `["stage_01_primary_topology", "primary_prerequisites_complete", "one_secondary_topology"]` | the primary branch's tag |

World-generative decisions (`04_*`, `06_salient_ecology`,
`06_relationship_pattern`, `08_two_way_reciprocity`, `08_campaign_horizon`,
`09_first_act_frame`, `09_opening_shape`) recorded with source `derived` or
`defaulted` must depend on `01_creation_authority`, and its mode must be
`bounded_inference` or `broad_world_preparation`. Under `approval_first` they
are Player decisions.

## complete-stage

- Every manifest decision of the stage is recorded.
- `output_refs` name at least one file for every owner of the stage's
  non-deferred decisions and nothing outside them (`stage-owners` lists them).
  A folder owner such as `characters/` needs a note other than `_template.md`.
  `setup_profile.yaml` and `session_zero.md` are never output refs.
- `output_digest` is `digest --refs-json '<the same refs>'`. `digest
  --stage-id <stage>` also checks the refs against the stage's owners.
- Each active extension portion of the stage needs evidence:
  `{"<extension>": {"status": "complete" | "defaulted", "depth": <its depth>,
  "output_refs": [...], "output_digest": "...", "acceptance_decision_id":
  <an accepted decision, for defaulted>}}`.
- Stage checks the helper runs before writing:
  - Stage 1: the play language is settled, `boundaries.md` keeps both
    `never (fixed)` content rows, and the Sexual content and Harm to children
    settings are one of their listed options.
  - Stage 2: `research_scope_locked` must be able to pass on the result.
  - Stage 4: `world_truths.md` has at least one row under
    `### Price And Bounty Anchors`.
  - Stage 8: `stages_1_8_complete` must be able to pass on the result.
  - Stage 9: the digest equals the approved preparation digest.

## Gates

Each gate's `input_digest` is the previous gate's `output_digest`, except the
first. Use the input as the output unless the gate certifies a different file
set; then use that set's `digest`.

| Gate | `input_digest` | `output_digest` | `decided_by` |
| --- | --- | --- | --- |
| `research_scope_locked` | Stage 2 `output_digest` | the locked research scope (or the input) | `coordinator` |
| `stages_1_8_complete` | previous output | the input | `coordinator` |
| `first_act_design_complete` | previous output | digest of the first-act design owners | `coordinator` |
| `design_direction_approved` | previous output | the design digest the Player approved | `player` |
| `preparation_materialized` | previous output | the preparation digest: `digest` of exactly the Stage 9 output refs | `coordinator` |
| `cross_read_passed` | the preparation digest | the same digest | `coordinator` |
| `preparation_approved` | the preparation digest | the same digest; also closes `integrated_review_accepted` | `player` |
| `draft_preflight_passed`, `ready_and_snapshotted` | recorded by `finalize` | | |

After `preparation_approved`, complete Stage 9 with the same refs, then run
`finalize --operation-id <id> --expected-revision <current>` (see
`playbooks/finalization.md`).

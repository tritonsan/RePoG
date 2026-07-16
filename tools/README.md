# Lite Tools

These small deterministic helpers guard campaign continuity. They do not create
narration or act as a second game engine.

## Campaign Checks

```bash
python tools/check_state.py campaign --scope hot
python tools/check_state.py campaign --scope full
python tools/check_dashboard.py campaign/dashboard/dashboard_state.json
```

`hot` is the bounded per-durable-turn check used by Fast and Balanced. `full`
is the default when `--scope` is omitted and is required at full distill,
session stop, closure, advancement, migration, and audit boundaries. A scene
checkpoint alone persists its small handoff contract and does not force a full
distill.

Run the dependency-free distributable smoke check with:

```bash
python tools/verify_workspace.py
python tools/verify_workspace.py --json
```

## Dashboard And Visual Transactions

```bash
python tools/serve_dashboard.py campaign/dashboard --check-only
python tools/update_dashboard.py campaign/dashboard/dashboard_state.json --input-json "{...}"
python tools/visual_handoff.py campaign --help
```

Dashboard V3 updates are atomic and require the expected source revision.
`serve_dashboard.py` validates first, binds only to `127.0.0.1`, disables
directory listing, and adds no-cache/security headers. The visual handoff tool
allows one pending `begin → attach → accept/revise/cancel` transaction and
preserves its return anchor. Acceptance copies the approved asset into both
campaign visual memory and dashboard assets; gallery, appearance, and
requested dashboard placement roll back together on failure.

## Snapshot

```bash
python tools/snapshot.py campaign --label before_scene
```

## GM Contract Migration

```bash
python tools/migrate_gm_contract.py campaign --dry-run
python tools/snapshot.py campaign --label before_gm_contract_v3
python tools/migrate_gm_contract.py campaign --apply --json
```

Apply is refused until a snapshot manifest already exists. The migration is
idempotent, preserves fiction prose, maps legacy scene-boundary persistence
names to scene-checkpoint policies, and marks uncertain NPC agency/offscreen,
opening-lifecycle, faction-motion, relationship, and knowledge ownership for
review rather than inventing answers.

## Sampled GM Replay Audit

`tools/gm_replay_suite.json` contains 12 reproducible, non-API scenarios for
sampled quality review. Each fixture provides private initial state, ordered
turns, expected observations, critical failures, and a blank scoring record.
Run it only at an explicit audit or scheduled sample using the blind procedure
in `workflows/audit/WORKFLOW.md`; it is not a per-turn checker or a second
narrative engine. A scenario passes at mean score 1.5 or higher with no
critical Player-authorship or knowledge-boundary failure.

## Player-Facing And Style Checks

```bash
python tools/check_player_facing.py --campaign campaign --text "You step into the rain."
python tools/check_style.py campaign/style_state.json --text "Rain ticks against the glass." --scene-id dock --beat-id turn-12
python tools/check_style.py campaign/style_state.json --text "Rain ticks against the glass." --scene-id dock --beat-id turn-12 --record
python tools/check_style.py campaign/style_state.json --text "The room settles." --dramatic-beat respite --gm-move offer-affordance --ending-form open-moment --record
```

Use `--speaker-type npc --speaker-id <id>` for a character-only excerpt. This
keeps a deliberate character voice separate from narrator-pattern warnings.
Style schema v3 also retains at most eight optional categorical fingerprints
(`dramatic_beat`, `gm_move`, `ending_form`, `sensory_channel`,
`complication_type`, `npc_social_tactic`, and `metaphor_family`). Repetition is
warning-only; the helper does not judge meaning or rewrite narration.
The player-facing check reads exact unrevealed names from
`knowledge_boundaries.md`; ordinary words such as "tool" are not banned.

## Optional World And Mechanics Helpers

```bash
python tools/world_pulse.py --input-json "{\"evaluation_id\":\"harbor-trade-rev-12\",\"domain\":\"harbor_trade\",\"elapsed_steps\":3,\"volatility\":2,\"pressure\":1}"
python tools/roll_dice.py --input-json "{\"expression\":\"2d6+1\",\"seed\":\"turn-12-lock\",\"roll_id\":\"turn-12-lock\"}"
python tools/resolve_mechanic.py campaign/mechanics_state.json --input-json "{\"operation_id\":\"turn-12-fire\",\"operation_sequence\":1,\"expected_revision\":0,\"expected_continuity_revision\":0,\"resulting_continuity_revision\":1,\"operation\":\"use_ability\",\"actor_id\":\"player\",\"action_id\":\"fire_spell\"}"
```

An `evaluation_id` gives the same world-pulse envelope on every retry. A
legacy explicit integer `seed` remains accepted. `roll_dice.py` accepts only
bounded `NdM+/-K` expressions and returns its seed for reproduction.

`resolve_mechanic.py` handles only mechanics explicitly configured by the
campaign. Schema v2 rejects numeric strings and floats, requires a monotonic
operation sequence, checks both ledger and campaign continuity revisions, and
supports resources, configured abilities, inventory, conditions, clocks, and
time. Its operation registry does not discard old ids, so an operation cannot
become valid again after an arbitrary history limit. It never interprets what
those changes mean in the fiction. A schema-v1
ledger is migrated on its next successful operation; after migration, callers
must supply the sequence and expected revisions shown above.

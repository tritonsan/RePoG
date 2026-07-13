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
is the default when `--scope` is omitted and is required at distill, scene,
session, closure, advancement, migration, and audit boundaries.

## Snapshot

```bash
python tools/snapshot.py campaign --label before_scene
```

## Player-Facing And Style Checks

```bash
python tools/check_player_facing.py --text "You step into the rain."
python tools/check_style.py campaign/style_state.json --text "Rain ticks against the glass."
python tools/check_style.py campaign/style_state.json --text "Rain ticks against the glass." --record
```

## Optional World And Mechanics Helpers

```bash
python tools/world_pulse.py --input-json "{\"domain\":\"harbor_trade\",\"elapsed_steps\":3,\"volatility\":2,\"pressure\":1,\"seed\":42}"
python tools/resolve_mechanic.py campaign/mechanics_state.json --input-json "{\"operation_id\":\"turn-12-fire\",\"operation\":\"use\",\"actor_id\":\"player\",\"action_id\":\"fire_spell\"}"
```

`world_pulse.py` never invents semantic events. `resolve_mechanic.py` handles
only mechanics explicitly configured by the campaign.

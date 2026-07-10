# Lite Tools

Phase 3 includes these small deterministic helpers:

- `snapshot.py`
- `check_player_facing.py`
- `check_state.py`
- `check_dashboard.py`
- `check_style.py`
- `world_pulse.py`
- `resolve_mechanic.py`

These tools should remain guardrails. They should not become a narrative
engine.

## Usage

Create a campaign snapshot:

```bash
python tools/snapshot.py campaigns/<campaign_id> --label before_scene
```

Scan proposed player-facing text:

```bash
python tools/check_player_facing.py --text "You step into the alley."
```

Check a campaign folder:

```bash
python tools/check_state.py campaigns/<campaign_id>
```

Check a player dashboard state file:

```bash
python tools/check_dashboard.py campaigns/<campaign_id>/dashboard/dashboard_state.json
```

Check a narration draft and optionally record its accepted fingerprint:

```bash
python tools/check_style.py campaigns/<campaign_id>/style_state.json --text "Rain ticks against the glass."
python tools/check_style.py campaigns/<campaign_id>/style_state.json --text "Rain ticks against the glass." --record
```

Generate a deterministic uncertainty envelope for a due world domain:

```bash
python tools/world_pulse.py --input-json "{\"domain\":\"harbor_trade\",\"elapsed_steps\":3,\"volatility\":2,\"pressure\":1,\"seed\":42}"
```

Apply an enabled deterministic mechanic:

```bash
python tools/resolve_mechanic.py campaigns/<campaign_id>/mechanics_state.json --input-json "{\"operation_id\":\"turn-12-fire\",\"operation\":\"use\",\"actor_id\":\"player\",\"action_id\":\"fire_spell\"}"
```

`world_pulse.py` never invents semantic events. `resolve_mechanic.py` handles
only mechanics explicitly configured by the campaign. `check_style.py` emits
warnings, not prose decisions.

For Lite memory V2, `check_state.py` also validates continuity revisions,
block-list present NPCs, active-cast presence reasons, location graph endpoints,
current relationship uniqueness, research gates, and documented arc-earned
stat exceptions. Pre-V2 campaigns receive migration warnings rather than
automatic rewrites.

## Deferred

- `check_links.py`: only split out if link checking grows beyond the small
  checks in `check_state.py`.
- `roll.py`: only add if a campaign explicitly wants dice procedures.

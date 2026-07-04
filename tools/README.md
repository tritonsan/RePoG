# Lite Tools

Phase 3 includes these small deterministic helpers:

- `snapshot.py`
- `check_player_facing.py`
- `check_state.py`

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

## Deferred

- `check_links.py`: only split out if link checking grows beyond the small
  checks in `check_state.py`.
- `roll.py`: only add if a campaign explicitly wants dice procedures.

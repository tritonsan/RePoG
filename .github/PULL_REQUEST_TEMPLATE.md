# Summary

What changed?

# Why

How does this improve RePoG's play experience, documentation, continuity, or
maintainability?

# Checks

- [ ] `python -m py_compile tools/check_state.py tools/check_player_facing.py tools/snapshot.py tools/check_dashboard.py`
- [ ] `python tools/check_state.py templates/campaign`
- [ ] `python tools/check_dashboard.py templates/campaign/dashboard/dashboard_state.json`
- [ ] `python tools/check_player_facing.py --text "You step into the rain."`

# Notes

Known tradeoffs, follow-ups, or things reviewers should pay attention to.

# Contributing To RePoG

Thanks for helping improve RePoG.

RePoG is early. The most useful contributions are clear examples, better
workflow guidance, bug reports from real play, and small improvements that make
long campaigns more natural and coherent.

## Good First Contributions

- Report a confusing setup step.
- Share a generic starter campaign idea.
- Improve wording in a workflow or template.
- Add a player-facing example that shows better GM behavior.
- Report a continuity, hidden-knowledge, or arc-closure failure.
- Suggest a new lightweight check that would catch a real problem.

## Contribution Rules

- Keep the general framework setting-neutral.
- Do not add copyrighted franchise content to the repository.
- Prefer Markdown/workflow improvements before adding code.
- Keep helper tools small and deterministic.
- Do not turn RePoG into a standalone app or full narrative engine unless the
  project direction changes explicitly.
- Player-facing examples should not expose file paths, raw ids, YAML, tool
  names, prompts, or implementation details.

## Local Checks

Run these before opening a pull request when possible:

```bash
python -m py_compile tools/check_state.py tools/check_player_facing.py tools/snapshot.py
python tools/check_state.py templates/campaign
python tools/check_dashboard.py templates/campaign/dashboard/dashboard_state.json
python tools/check_player_facing.py --text "You step into the rain."
```

## Pull Requests

In your PR, include:

- what changed;
- why it improves play or maintainability;
- what checks you ran;
- any tradeoff or known gap.

Small, focused pull requests are easiest to review.

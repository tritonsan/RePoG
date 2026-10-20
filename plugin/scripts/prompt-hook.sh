#!/bin/sh
# RePoG UserPromptSubmit hook.
#
# In a ready RePoG campaign, apply any staged curation whose base files are
# unchanged, then inject the scene capsule (present cast, secrets by id,
# directives, last reply's presentation findings) as hidden context for the
# next reply. Print nothing anywhere else. Never block the prompt.

project="${CLAUDE_PROJECT_DIR:-$PWD}"
[ -f "$project/campaign/setup_profile.yaml" ] || exit 0
[ -f "$project/AGENTS.md" ] && [ -d "$project/workflows" ] && exit 0
. "$(dirname "$0")/hook-python.sh"
[ -n "$PY" ] || exit 0
$PY -B "$(dirname "$0")/../tools/hook_entry.py" prompt 2>/dev/null
exit 0

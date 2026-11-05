#!/bin/sh
# RePoG Stop hook (runs asynchronously).
#
# In a ready RePoG campaign, record whether the turn that just ended narrated
# before its commit and ended with visible text (order_last.json, flags only),
# run the deterministic presentation lint over the reply, and store both for
# the next scene capsule. It reads only this session's last turn, locally.
# Prints nothing and never affects the conversation.

project="${CLAUDE_PROJECT_DIR:-$PWD}"
[ -f "$project/campaign/setup_profile.yaml" ] || exit 0
[ -f "$project/AGENTS.md" ] && [ -d "$project/workflows" ] && exit 0
. "$(dirname "$0")/hook-python.sh"
[ -n "$PY" ] || exit 0
$PY -B "$(dirname "$0")/../tools/hook_entry.py" stop >/dev/null 2>&1
exit 0

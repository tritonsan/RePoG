#!/bin/sh
# RePoG PreToolUse guard for the boundary curator.
#
# The hook runs only for Write, the curator's one writing tool. Main-session
# writes pass straight through without starting Python. Only a call made
# inside the repog-curator subagent is checked: it may write its one staging
# file under campaign/.repog-runtime/curation/ and nothing else.

input=$(cat)
case "$input" in
  *repog-curator*) ;;
  *) exit 0 ;;
esac
. "$(dirname "$0")/hook-python.sh"
[ -n "$PY" ] || exit 0
printf '%s' "$input" | $PY -B "$(dirname "$0")/../tools/hook_entry.py" pretool 2>/dev/null
exit 0

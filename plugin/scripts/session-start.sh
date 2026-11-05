#!/bin/sh
# RePoG SessionStart hook.
#
# In a folder that holds a campaign created by the RePoG plugin, remind Claude
# to load the RePoG skill, including after compaction or /clear. Print nothing
# anywhere else, so the installed plugin adds no context to other projects or
# to standalone RePoG workspaces, which carry their own instructions.

project="${CLAUDE_PROJECT_DIR:-.}"

[ -f "$project/campaign/setup_profile.yaml" ] || exit 0
if [ -f "$project/AGENTS.md" ] && [ -d "$project/workflows" ]; then
  exit 0
fi

input=$(cat)

cat <<'EOF'
This folder holds a RePoG campaign. Before replying, invoke the repog:play skill unless its full text is already in this conversation, then follow it, re-reading campaign/setup_profile.yaml and the routed workflow first.
EOF

# Mark the scene capsule for a full refresh: a new, resumed, cleared, or
# compacted session no longer holds the previous capsule. After a compaction
# or a resume of a ready RPG campaign, the helper also prints the accepted
# style samples and the locked persistence order after the reminder above.
. "$(dirname "$0")/hook-python.sh"
if [ -n "$PY" ]; then
  printf '%s' "$input" | $PY -B "$(dirname "$0")/../tools/hook_entry.py" session-start 2>/dev/null
fi
exit 0

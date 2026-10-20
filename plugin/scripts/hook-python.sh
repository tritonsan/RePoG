# Sourced by the RePoG hook scripts: set PY to a Python 3.10+ command, or
# leave it empty. Hooks stay silent when no suitable Python exists, so a
# missing interpreter never blocks a prompt or a reply.
#
# The probe starts Python once, which costs a noticeable fraction of a second
# on Windows, so the chosen command is cached in the plugin's data folder.
PY=""
cache=""
if [ -n "${CLAUDE_PLUGIN_DATA:-}" ]; then
  cache="$CLAUDE_PLUGIN_DATA/python-command"
  if [ -f "$cache" ]; then
    PY=$(cat "$cache")
    # An interpreter that has left PATH since it was cached is probed again;
    # otherwise every hook would go silent until the cache was deleted.
    command -v "${PY%% *}" >/dev/null 2>&1 || PY=""
  fi
fi
if [ -z "$PY" ]; then
  check='import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'
  for candidate in python python3; do
    found=$(command -v "$candidate" 2>/dev/null) || continue
    # The Windows Store alias only opens the Store; skip it.
    case "$found" in *WindowsApps*) continue ;; esac
    if "$candidate" -c "$check" >/dev/null 2>&1; then
      PY="$candidate"
      break
    fi
  done
  if [ -z "$PY" ] && command -v py >/dev/null 2>&1 && py -3 -c "$check" >/dev/null 2>&1; then
    PY="py -3"
  fi
  if [ -n "$PY" ] && [ -n "$cache" ]; then
    mkdir -p "$CLAUDE_PLUGIN_DATA" 2>/dev/null && printf '%s' "$PY" > "$cache" 2>/dev/null
  fi
fi

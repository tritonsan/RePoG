#!/bin/sh
# Run one bundled RePoG helper with Python 3.10 or later.
#
#   sh repog.sh <helper> [arguments...]
#
# <helper> names tools/<helper>.py inside this plugin; the arguments pass
# through unchanged. The launcher tries python3, python, and the Windows py
# launcher in that order and skips any that is missing, older than 3.10, or a
# placeholder such as the Microsoft Store alias. Failures print the same typed
# JSON shape that the helpers use.

fail() {
  printf '{"ok": false, "failure_category": "%s", "failure_reason": "%s"}\n' "$1" "$2"
  exit "$3"
}

[ "$#" -ge 1 ] || fail helper_invalid "usage: sh repog.sh <helper> [arguments...]" 2
helper="$1"
shift

case "$helper" in
  '' | *[!A-Za-z0-9_]*) fail helper_invalid "helper names use only letters, digits, and underscores" 2 ;;
esac

root=$(cd "$(dirname "$0")/.." && pwd) || fail helper_invalid "cannot locate the plugin folder" 2
script="$root/tools/$helper.py"
[ -f "$script" ] || fail helper_invalid "unknown helper: $helper" 2

check='import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'
if python3 -c "$check" >/dev/null 2>&1; then
  exec python3 -B "$script" "$@"
elif python -c "$check" >/dev/null 2>&1; then
  exec python -B "$script" "$@"
elif py -3 -c "$check" >/dev/null 2>&1; then
  exec py -3 -B "$script" "$@"
fi

fail python_missing "RePoG needs Python 3.10 or later on PATH as python3, python, or py" 127

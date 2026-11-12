"""Exit 0 when this interpreter is Python 3.10 or later: the launchers probe each candidate with it."""

import sys

sys.exit(0 if sys.version_info >= (3, 10) else 1)

"""Ensures the repo root is importable so `from api.src...` (used throughout the codebase)
resolves correctly regardless of which directory pytest is invoked from.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

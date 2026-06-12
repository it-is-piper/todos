"""Pytest config: locate the real todos.sh for subprocess tests."""

import os
import sys
from pathlib import Path

# Make the project root importable so `from todos import Todos` works.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

REAL_TODOS_SH = PROJECT_ROOT / "todos.sh"
REAL_TODOS_PY = PROJECT_ROOT / "todos.py"


def in_venv() -> bool:
    """True if running under uv/pytest with the venv active."""
    return "VIRTUAL_ENV" in os.environ or sys.prefix != sys.base_prefix

"""Pytest config: locate the real todos.sh for subprocess tests."""

import os
import sys


def in_venv() -> bool:
    """True if running under uv/pytest with the venv active."""
    return "VIRTUAL_ENV" in os.environ or sys.prefix != sys.base_prefix

"""Shared fixtures and stubs for API route tests."""

import sys
from unittest.mock import MagicMock

# Stub optional heavy dependencies that may not be installed in test env.
# These are imported transitively when the FastAPI app loads all route modules.
for _mod_name in ("speech_recognition", "bleach"):
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = MagicMock()

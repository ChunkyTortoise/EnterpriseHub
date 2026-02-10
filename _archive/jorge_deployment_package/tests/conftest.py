import os
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

os.environ.setdefault("TESTING_MODE", "true")
os.environ.setdefault("GHL_ACCESS_TOKEN", "test-ghl-token")
os.environ.setdefault("CLAUDE_API_KEY", "test-claude-key")
os.environ.setdefault("GHL_LOCATION_ID", "test-location")
os.environ.setdefault("GHL_WEBHOOK_SECRET", "test-webhook-secret")

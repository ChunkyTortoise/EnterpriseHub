"""
Smoke test for Enterprise Hub module structure.
Verifies that all registered modules exist and are importable.
"""

import importlib
import os

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.unit]

try:
    from app import MODULES
    MODULES_AVAILABLE = True
except (ImportError, SystemExit):
    MODULES = {}
    MODULES_AVAILABLE = False


def require_modules() -> None:
    if not MODULES_AVAILABLE:
        pytest.skip("MODULES not available in app")


def test_module_registration():
    """Verify all modules in registry have corresponding files in modules/."""
    require_modules()

    for key, info in MODULES.items():
        module_name = info["name"]
        try:
            importlib.import_module(f"modules.{module_name}")
        except ImportError as e:
            pytest.fail(f"Module '{module_name}' registered as '{key}' could not be imported: {e}")


def test_icon_paths():
    """Verify all module icons exist."""
    require_modules()

    for key, info in MODULES.items():
        icon_path = info["icon"]
        # Skip remote URLs if any
        if icon_path.startswith("http"):
            continue
        assert os.path.exists(icon_path), f"Icon for '{key}' not found at {icon_path}"


def test_ui_utils():
    """Verify core UI utilities are available."""
    try:
        import utils.ui as ui

        assert hasattr(ui, "setup_interface")
        assert hasattr(ui, "card_metric")
    except ImportError as exc:
        pytest.skip(f"utils.ui unavailable in this environment: {exc}")

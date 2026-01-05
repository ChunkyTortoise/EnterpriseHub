"""
Smoke test for Enterprise Hub module structure.
Verifies that all registered modules exist and are importable.
"""
import pytest
import importlib
from app import MODULES

def test_module_registration():
    """Verify all modules in registry have corresponding files in modules/."""
    for key, info in MODULES.items():
        module_name = info["name"]
        try:
            importlib.import_module(f"modules.{module_name}")
        except ImportError as e:
            pytest.fail(f"Module '{module_name}' registered as '{key}' could not be imported: {e}")

def test_icon_paths():
    """Verify all module icons exist."""
    import os
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
    except ImportError:
        pytest.fail("Could not import utils.ui")

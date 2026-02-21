import runpy
import sys
from pathlib import Path

# Set up paths to ensure all modules are findable
BASE_DIR = Path(__file__).parent
TARGET_APP = BASE_DIR / "ghl_real_estate_ai" / "streamlit_demo" / "app.py"

# Add project root and ghl_real_estate_ai to sys.path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Add ghl_real_estate_ai directory to sys.path
ghl_root = BASE_DIR / "ghl_real_estate_ai"
if str(ghl_root) not in sys.path:
    sys.path.insert(0, str(ghl_root))

# Add streamlit_demo directory to sys.path
demo_root = ghl_root / "streamlit_demo"
if str(demo_root) not in sys.path:
    sys.path.insert(0, str(demo_root))

if __name__ == "__main__":
    from streamlit.web import cli as stcli

    try:
        from streamlit.runtime import exists
    except ImportError:
        # Fallback for older Streamlit versions
        def exists():
            return False

    if not TARGET_APP.exists():
        print(f"Error: Could not find application at {TARGET_APP}")
        sys.exit(1)

    if not exists():
        # Case 1: Running as "python app.py"
        # Launch the target app directly via Streamlit CLI
        sys.argv = ["streamlit", "run", str(TARGET_APP), "--server.port=8501", "--server.address=0.0.0.0"]
        sys.exit(stcli.main())
    else:
        # Case 2: Running via "streamlit run app.py"
        # Execute the target script in the current process to proxy it
        # Update __file__ so the inner script resolves relative paths correctly
        original_file = sys.modules["__main__"].__file__
        sys.modules["__main__"].__file__ = str(TARGET_APP)

        try:
            runpy.run_path(str(TARGET_APP), run_name="__main__")
        finally:
            sys.modules["__main__"].__file__ = original_file

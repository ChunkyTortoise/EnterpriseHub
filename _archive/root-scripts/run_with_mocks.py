import sys
from unittest.mock import MagicMock

# Mock heavy dependencies
sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.config"] = MagicMock()
sys.modules["chromadb.api"] = MagicMock()
sys.modules["chromadb.api.models"] = MagicMock()
sys.modules["chromadb.api.models.Collection"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["onnxruntime"] = MagicMock()

import streamlit.web.cli as stcli

if __name__ == "__main__":
    try:
        from streamlit.runtime import exists
    except ImportError:
        def exists(): return False

    # Ensure the current directory is in sys.path
    sys.path.insert(0, ".")
    
    if not exists():
        sys.argv = ["streamlit", "run", "ghl_real_estate_ai/streamlit_demo/app.py", "--server.headless=true", "--server.port=8501"]
        sys.exit(stcli.main())
    else:
        # If running via streamlit run run_with_mocks.py, just execute the target
        target = "ghl_real_estate_ai/streamlit_demo/app.py"
        with open(target) as f:
            code = f.read()
        global_vars = {
            "__file__": str(target),
            "__name__": "__main__",
        }
        exec(code, global_vars)

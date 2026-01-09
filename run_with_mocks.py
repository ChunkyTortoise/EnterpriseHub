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
    # Ensure the current directory is in sys.path
    sys.path.insert(0, ".")
    sys.argv = ["streamlit", "run", "ghl_real_estate_ai/streamlit_demo/app.py", "--server.headless=true", "--server.port=8501"]
    sys.exit(stcli.main())

import sys
from unittest.mock import MagicMock

# Mock chromadb
chromadb_mock = MagicMock()
sys.modules["chromadb"] = chromadb_mock
sys.modules["chromadb.config"] = MagicMock()
sys.modules["chromadb.api"] = MagicMock()
sys.modules["chromadb.api.models"] = MagicMock()
sys.modules["chromadb.api.models.Collection"] = MagicMock()

# Mock sentence_transformers
st_mock = MagicMock()
sys.modules["sentence_transformers"] = st_mock
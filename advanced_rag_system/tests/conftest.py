"""Pytest configuration and shared fixtures."""

import pytest
import os
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_openai_api_key():
    """Automatically mock OpenAI API key for all tests."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key-for-testing"}):
        yield


@pytest.fixture
def temp_chroma_dir(tmp_path):
    """Provide temporary directory for ChromaDB tests."""
    chroma_path = tmp_path / "chroma_test"
    chroma_path.mkdir()
    return str(chroma_path)
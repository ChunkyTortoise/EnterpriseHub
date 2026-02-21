"""Shared test fixtures for AI DevOps Suite."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from devops_suite.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def httpx_mock():
    """Mock for httpx requests in scraper tests."""
    try:
        from pytest_httpx import HTTPXMock

        mock = HTTPXMock()
        yield mock
    except ImportError:
        pytest.skip("pytest-httpx not installed")

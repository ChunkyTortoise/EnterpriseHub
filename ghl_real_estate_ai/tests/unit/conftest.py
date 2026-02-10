"""Conftest for unit tests — lightweight fixtures that never touch real services."""

import os

import pytest


@pytest.fixture(autouse=True)
def _unit_test_env(monkeypatch):
    """Ensure unit tests never accidentally reach real services."""
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

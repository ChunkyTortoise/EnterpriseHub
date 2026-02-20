"""
Shared pytest fixtures for compliance platform tests.

Provides centralized test configuration including secure secret management.
"""

import os

import pytest


@pytest.fixture(scope="session")
def test_secret_key():
    """
    Test secret key for JWT/token operations in tests.
    
    Uses environment variable TEST_SECRET_KEY if set, otherwise provides
    a secure default for CI environments.
    """
    return os.environ.get("TEST_SECRET_KEY", "test-secret-key-for-ci-only-min-32-chars")


@pytest.fixture(scope="session")
def test_api_key():
    """
    Test API key for authentication tests.
    
    Uses environment variable TEST_API_KEY if set, otherwise provides
    a secure default for CI environments.
    """
    return os.environ.get("TEST_API_KEY", "test-api-key-for-ci-only-min-32-chars")


@pytest.fixture(scope="session")
def test_webhook_secret():
    """
    Test webhook secret for signature verification tests.
    
    Uses environment variable TEST_WEBHOOK_SECRET if set, otherwise provides
    a secure default for CI environments.
    """
    return os.environ.get("TEST_WEBHOOK_SECRET", "test-webhook-secret-for-ci-only-min-32-chars")

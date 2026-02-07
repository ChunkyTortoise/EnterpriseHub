"""
Unit tests for the Authentication and Persistence module.
"""

import os
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from modules import auth

# Use a temporary database for testing
TEST_DB_PATH = "data/test_users.db"

@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup and teardown a clean test database."""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Remove existing test DB if any
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    # Patch DB_PATH in auth module
    with patch("modules.auth.DB_PATH", TEST_DB_PATH):
        auth.init_db()
        yield
        
    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_init_db():
    """Test database initialization."""
    assert os.path.exists(TEST_DB_PATH)
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    
    # Check users table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    assert cursor.fetchone() is not None
    
    # Check scenarios table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scenarios'")
    assert cursor.fetchone() is not None
    
    conn.close()

def test_hash_password():
    """Test password hashing."""
    pwd = "password123"
    h1 = auth.hash_password(pwd)
    h2 = auth.hash_password(pwd)
    assert h1 == h2
    assert h1 != pwd
    assert len(h1) == 64  # SHA-256

def test_create_and_authenticate_user():
    """Test user creation and authentication."""
    username = "testuser"
    password = "securepass"
    
    # Create user
    assert auth.create_user(username, password) is True
    
    # Duplicate user should fail
    assert auth.create_user(username, password) is False
    
    # Authenticate with correct credentials
    assert auth.authenticate_user(username, password) is True
    
    # Authenticate with wrong password
    assert auth.authenticate_user(username, "wrongpass") is False
    
    # Authenticate with non-existent user
    assert auth.authenticate_user("nonexistent", password) is False

def test_scenario_persistence():
    """Test saving, loading, and deleting scenarios."""
    username = "testuser"
    module = "margin_hunter"
    name = "Q1 Plan"
    data = {"price": 100, "cost": 50}
    
    # Save scenario
    assert auth.save_scenario(username, module, name, data) is True
    
    # Retrieve scenarios
    scenarios = auth.get_user_scenarios(username, module)
    assert len(scenarios) == 1
    assert scenarios[0]["name"] == name
    assert "price" in scenarios[0]["data"] # it's a JSON string in DB but returned as dict or string?
    # Actually get_user_scenarios returns Row objects converted to dict, data is still JSON string.
    import json
    loaded_data = json.loads(scenarios[0]["data"])
    assert loaded_data["price"] == 100
    
    # Delete scenario
    scenario_id = scenarios[0]["id"]
    assert auth.delete_scenario(scenario_id, username) is True
    assert len(auth.get_user_scenarios(username, module)) == 0

def test_auth_error_handling():
    """Test error handling in auth functions."""
    with patch("sqlite3.connect", side_effect=Exception("DB Error")):
        assert auth.create_user("user", "pass") is False
        assert auth.authenticate_user("user", "pass") is False
        assert auth.save_scenario("user", "mod", "name", {}) is False
        assert auth.get_user_scenarios("user", "mod") == []
        assert auth.delete_scenario(1, "user") is False

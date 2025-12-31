"""
Authentication and Persistence Module.
Handles user registration, login, and scenario saving using SQLite.
"""

import hashlib
import json
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = os.getenv("DB_PATH", "data/users.db")

def init_db():
    """Initialize the SQLite database with required tables."""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Scenarios table for persistence
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                module TEXT NOT NULL,
                name TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        """)

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def hash_password(password: str) -> str:
    """Hash a password for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str) -> bool:
    """Create a new user in the database."""
    init_db()
    password_hash = hash_password(password)
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user against stored credentials."""
    init_db()
    password_hash = hash_password(password)
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        user = cursor.fetchone()
        conn.close()
        return user is not None
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return False

def save_scenario(username: str, module: str, name: str, data: Dict[str, Any]) -> bool:
    """Save a scenario for a specific user and module."""
    init_db()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        json_data = json.dumps(data)
        cursor.execute(
            "INSERT INTO scenarios (username, module, name, data) VALUES (?, ?, ?, ?)",
            (username, module, name, json_data)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving scenario: {e}")
        return False

def get_user_scenarios(username: str, module: str) -> List[Dict[str, Any]]:
    """Retrieve all saved scenarios for a user and module."""
    init_db()
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, data, created_at FROM scenarios WHERE username = ? AND module = ? ORDER BY created_at DESC",
            (username, module)
        )
        rows = cursor.fetchall()
        scenarios = [dict(row) for row in rows]
        conn.close()
        return scenarios
    except Exception as e:
        logger.error(f"Error retrieving scenarios: {e}")
        return []

def delete_scenario(scenario_id: int, username: str) -> bool:
    """Delete a saved scenario."""
    init_db()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM scenarios WHERE id = ? AND username = ?",
            (scenario_id, username)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error deleting scenario: {e}")
        return False

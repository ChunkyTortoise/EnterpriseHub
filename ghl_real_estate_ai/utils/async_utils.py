"""
Asynchronous utilities for safe task management.
Provides helpers for spawning background tasks in environments with or without active event loops.
"""
import asyncio
import threading
from typing import Coroutine, Any, Optional
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

def safe_create_task(coro: Coroutine) -> Optional[asyncio.Task]:
    """
    Safely create an asyncio task.
    If no event loop is running, it logs a warning and returns None.
    This prevents RuntimeError in synchronous environments like Streamlit initialization.
    """
    try:
        loop = asyncio.get_running_loop()
        return loop.create_task(coro)
    except RuntimeError:
        # No running event loop
        logger.debug(f"No running event loop found for task {coro.__name__ if hasattr(coro, '__name__') else coro}. Skipping.")
        return None

def run_in_background(coro: Coroutine) -> None:
    """
    Ensure a coroutine runs in the background.
    If a loop is running, it uses safe_create_task.
    Otherwise, it could potentially start a new thread or just skip if appropriate.
    For this project's stability needs, skipping background tasks when no loop is active 
    during initialization is often the safest path to avoid crashes.
    """
    safe_create_task(coro)

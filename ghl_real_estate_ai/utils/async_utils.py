"""
Async Utilities for Streamlit Components

Safe async execution utilities to handle event loop conflicts in Streamlit deployments.
Provides robust alternatives to asyncio.run() that work in various environments.
"""

import asyncio
import functools
import threading
from typing import Any, Awaitable, TypeVar, Optional
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

def safe_run_async(coro: Awaitable[T], timeout: Optional[float] = None) -> T:
    """
    Safely run an async coroutine in Streamlit environment.

    This function handles event loop conflicts that can occur when using asyncio.run()
    in Streamlit deployments, especially in production environments.

    Args:
        coro: The coroutine to execute
        timeout: Optional timeout in seconds

    Returns:
        The result of the coroutine execution

    Raises:
        TimeoutError: If timeout is specified and exceeded
        RuntimeError: If coroutine execution fails
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()

        # If we're already in an event loop, we need to run in a thread
        if loop.is_running():
            logger.debug("Running coroutine in thread (event loop already running)")
            return _run_in_thread(coro, timeout)
        else:
            # Event loop exists but not running, we can use it
            logger.debug("Using existing event loop")
            return loop.run_until_complete(asyncio.wait_for(coro, timeout))

    except RuntimeError as e:
        if "no running event loop" in str(e).lower() or "no current event loop" in str(e).lower():
            # No event loop exists, safe to create one
            logger.debug("Creating new event loop")
            try:
                if timeout:
                    return asyncio.run(asyncio.wait_for(coro, timeout))
                else:
                    return asyncio.run(coro)
            except Exception as run_error:
                logger.error(f"Failed to run coroutine with asyncio.run: {run_error}")
                # Fallback to thread execution
                return _run_in_thread(coro, timeout)
        else:
            # Some other RuntimeError, re-raise it
            raise
    except Exception as e:
        logger.error(f"Unexpected error in safe_run_async: {e}")
        # Last resort: try thread execution
        return _run_in_thread(coro, timeout)

def _run_in_thread(coro: Awaitable[T], timeout: Optional[float] = None) -> T:
    """
    Run coroutine in a separate thread with its own event loop.

    This is used when the main thread already has a running event loop.
    """
    import concurrent.futures

    def run_in_new_loop():
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if timeout:
                return loop.run_until_complete(asyncio.wait_for(coro, timeout))
            else:
                return loop.run_until_complete(coro)
        finally:
            loop.close()

    # Use ThreadPoolExecutor to run the coroutine in a separate thread
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_new_loop)
        try:
            # Apply timeout to the thread execution as well
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Coroutine execution timed out after {timeout} seconds")

def sync_async_function(async_func):
    """
    Decorator to convert async functions to sync functions for Streamlit.

    Usage:
        @sync_async_function
        async def my_async_function():
            return await some_async_operation()

        # Can now be called synchronously in Streamlit
        result = my_async_function()
    """
    @functools.wraps(async_func)
    def wrapper(*args, **kwargs):
        coro = async_func(*args, **kwargs)
        return safe_run_async(coro)

    return wrapper

def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """
    Get the current event loop or create a new one if none exists.

    Returns:
        The current or newly created event loop
    """
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, try to get the event loop for this thread
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            # No event loop at all, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

class StreamlitAsyncManager:
    """
    Context manager for handling async operations in Streamlit.

    Usage:
        async with StreamlitAsyncManager() as manager:
            result = await manager.run(some_async_function())
    """

    def __init__(self):
        self.loop = None
        self._thread_loop = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._thread_loop and not self._thread_loop.is_closed():
            self._thread_loop.close()

    async def run(self, coro: Awaitable[T]) -> T:
        """Run a coroutine safely within this manager."""
        return await coro

def handle_streamlit_async_error(error: Exception, operation_name: str = "async operation"):
    """
    Handle async-related errors in Streamlit with user-friendly messages.

    Args:
        error: The exception that occurred
        operation_name: Name of the operation for error messaging
    """
    import streamlit as st

    error_msg = str(error).lower()

    if "event loop" in error_msg or "asyncio" in error_msg:
        st.error(f"""
        🔄 **Async Operation Error**

        The {operation_name} encountered an event loop conflict. This can happen in certain
        deployment environments.

        **Quick Fix:** Try refreshing the page or restarting the application.

        **Technical Details:** {str(error)}
        """)

        st.info("""
        💡 **For Developers:** This error typically occurs when:
        - Multiple event loops are running simultaneously
        - asyncio.run() is called within an existing event loop
        - The deployment environment has event loop restrictions

        Consider using the `safe_run_async()` utility instead of `asyncio.run()`.
        """)
    else:
        st.error(f"Error in {operation_name}: {str(error)}")

# Backward compatibility aliases
run_async_safe = safe_run_async  # Alternative name for clarity
streamlit_async_run = safe_run_async  # Streamlit-specific alias
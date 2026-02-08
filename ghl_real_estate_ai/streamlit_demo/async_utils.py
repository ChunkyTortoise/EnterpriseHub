import asyncio
import threading
from typing import Any, Coroutine, TypeVar

import streamlit as st

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Safely run a coroutine in a Streamlit environment.
    Handles the case where an event loop is already running.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # If we're inside a running loop (like Streamlit's),
        # we need to run the coroutine in a separate thread
        # or use a different approach.
        # For simplicity and compatibility with most Streamlit versions:
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return loop.run_until_complete(coro)

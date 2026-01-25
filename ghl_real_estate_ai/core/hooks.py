"""
Gemini Workflow Hooks System.

Provides lifecycle hooks for the Agent system, allowing for 
custom logic before/after LLM interactions and Tool execution.
"""
import asyncio
from typing import Callable, List, Optional, Any, Dict, Union, Awaitable
from dataclasses import dataclass
from enum import Enum

class HookEvent(Enum):
    SESSION_START = "session_start"
    PRE_GENERATION = "pre_generation"
    POST_GENERATION = "post_generation"
    PRE_TOOL_EXECUTION = "pre_tool_execution"
    POST_TOOL_EXECUTION = "post_tool_execution"
    ON_ERROR = "on_error"

@dataclass
class HookContext:
    """Context passed to hooks."""
    event: HookEvent
    agent_name: str
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None

class HookManager:
    """Manages lifecycle hooks, supporting both sync and async callbacks."""
    
    def __init__(self):
        self._hooks: Dict[HookEvent, List[Callable[[HookContext], Union[None, Awaitable[None]]]]] = {
            event: [] for event in HookEvent
        }

    def register(self, event: HookEvent, callback: Callable[[HookContext], Union[None, Awaitable[None]]]):
        """Register a hook callback."""
        self._hooks[event].append(callback)

    def trigger(self, event: HookEvent, context: HookContext):
        """Trigger all hooks for an event (synchronous)."""
        for callback in self._hooks[event]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    # For sync trigger of async function, create a task
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(callback(context))
                    except RuntimeError:
                        # Fallback: run in a new thread or just log that it couldn't run
                        # In a sync context where we don't have a loop, we can't easily await
                        print(f"Warning: No running event loop found to execute async hook {event.value}")
                else:
                    callback(context)
            except Exception as e:
                # Hooks should not break the main flow, just log error
                print(f"Error in sync hook {event.value}: {e}")

    async def atrigger(self, event: HookEvent, context: HookContext):
        """Trigger all hooks for an event (asynchronous)."""
        for callback in self._hooks[event]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(context)
                else:
                    callback(context)
            except Exception as e:
                print(f"Error in async hook {event.value}: {e}")

# Global hook manager instance
hooks = HookManager()

# Example built-in hook: Audit Logging
def audit_log_hook(ctx: HookContext):
    if ctx.event == HookEvent.POST_TOOL_EXECUTION:
        print(f"[AUDIT] Agent '{ctx.agent_name}' executed tool. Result size: {len(str(ctx.output_data))} chars")

hooks.register(HookEvent.POST_TOOL_EXECUTION, audit_log_hook)

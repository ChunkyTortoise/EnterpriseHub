"""
Gemini Workflow Hooks System.

Provides lifecycle hooks for the Agent system, allowing for 
custom logic before/after LLM interactions and Tool execution.
"""
from typing import Callable, List, Optional, Any, Dict
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
    """Manages lifecycle hooks."""
    
    def __init__(self):
        self._hooks: Dict[HookEvent, List[Callable[[HookContext], None]]] = {
            event: [] for event in HookEvent
        }

    def register(self, event: HookEvent, callback: Callable[[HookContext], None]):
        """Register a hook callback."""
        self._hooks[event].append(callback)

    def trigger(self, event: HookEvent, context: HookContext):
        """Trigger all hooks for an event."""
        for callback in self._hooks[event]:
            try:
                callback(context)
            except Exception as e:
                # Hooks should not break the main flow, just log error
                print(f"Error in hook {event.value}: {e}")

# Global hook manager instance
hooks = HookManager()

# Example built-in hook: Audit Logging
def audit_log_hook(ctx: HookContext):
    if ctx.event == HookEvent.POST_TOOL_EXECUTION:
        print(f"[AUDIT] Agent '{ctx.agent_name}' executed tool. Result size: {len(str(ctx.output_data))} chars")

hooks.register(HookEvent.POST_TOOL_EXECUTION, audit_log_hook)

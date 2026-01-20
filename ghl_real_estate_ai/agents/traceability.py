"""
Traceability and Observability for Gemini Agents.
Provides decorators and utilities to trace agent execution.
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Setup basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_trace")

@dataclass
class TraceLog:
    trace_id: str
    agent_name: str
    action: str
    start_time: float
    end_time: Optional[float] = None
    input_data: Optional[Dict] = None
    output_data: Optional[Any] = None
    status: str = "started"

class AgentTracer:
    """Manages agent execution traces."""
    def __init__(self):
        self.traces: Dict[str, TraceLog] = {}

    def start_trace(self, agent_name: str, action: str, input_data: Dict) -> str:
        trace_id = str(uuid.uuid4())[:8]
        self.traces[trace_id] = TraceLog(
            trace_id=trace_id,
            agent_name=agent_name,
            action=action,
            start_time=time.time(),
            input_data=input_data
        )
        logger.info(f"[{trace_id}] 🟢 Agent '{agent_name}' starting action: {action}")
        return trace_id

    def end_trace(self, trace_id: str, output_data: Any, status: str = "completed"):
        if trace_id in self.traces:
            log = self.traces[trace_id]
            log.end_time = time.time()
            log.output_data = output_data
            log.status = status
            duration = log.end_time - log.start_time
            logger.info(f"[{trace_id}] 🏁 Agent '{log.agent_name}' finished in {duration:.2f}s. Status: {status}")

def trace_agent_action(action_name: Optional[str] = None):
    """Decorator to automatically trace an agent method."""
    
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to find agent name from 'self' or use function name
            agent_name = "UnknownAgent"
            if args and hasattr(args[0], 'name'):
                agent_name = args[0].name
            elif args and hasattr(args[0], 'role'):
                agent_name = str(args[0].role)
            
            action = action_name or func.__name__
            trace_id = agent_tracer.start_trace(agent_name, action, {"args": str(args[1:]), "kwargs": str(kwargs)})
            
            try:
                result = await func(*args, **kwargs)
                agent_tracer.end_trace(trace_id, result)
                return result
            except Exception as e:
                agent_tracer.end_trace(trace_id, str(e), status="failed")
                raise
        return wrapper
    return decorator

# Global tracer instance
agent_tracer = AgentTracer()

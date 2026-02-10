"""Async tool registry with status callbacks for AgentForge."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional


class ToolStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ToolStatusEvent:
    tool_name: str
    status: ToolStatus
    message: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class BaseTool:
    name: str = "tool"
    description: str = ""

    async def run(self, **kwargs: Any) -> Any:
        raise NotImplementedError


StatusCallback = Callable[[ToolStatusEvent], Awaitable[None]]


class ToolRegistry:
    """Register and execute tools asynchronously with live status updates."""

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    async def execute(
        self,
        tool_name: str,
        status_callback: Optional[StatusCallback] = None,
        **kwargs: Any,
    ) -> ToolResult:
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolResult(tool_name=tool_name, success=False, error="Tool not found")

        async def emit(status: ToolStatus, message: str) -> None:
            if status_callback:
                await status_callback(ToolStatusEvent(tool_name=tool_name, status=status, message=message))

        await emit(ToolStatus.RUNNING, "Executing tool")
        start = datetime.utcnow()
        try:
            result = await tool.run(**kwargs)
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            await emit(ToolStatus.SUCCESS, "Tool completed")
            return ToolResult(tool_name=tool_name, success=True, data=result, execution_time_ms=elapsed)
        except Exception as exc:
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            await emit(ToolStatus.ERROR, f"Tool failed: {exc}")
            return ToolResult(tool_name=tool_name, success=False, error=str(exc), execution_time_ms=elapsed)

    async def execute_parallel(
        self,
        tasks: List[Dict[str, Any]],
        status_callback: Optional[StatusCallback] = None,
    ) -> List[ToolResult]:
        coros = [
            self.execute(task["tool_name"], status_callback=status_callback, **task.get("params", {}))
            for task in tasks
        ]
        return await asyncio.gather(*coros)

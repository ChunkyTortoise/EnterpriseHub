"""Custom exceptions for AgentForge DAG operations.

This module defines exceptions specific to DAG manipulation and validation,
providing clear error messages for common issues like cycles, missing nodes,
and validation failures.
"""


class CycleDetectedError(Exception):
    """Exception raised when a cycle is detected in the DAG.

    DAGs must be acyclic by definition. This exception is raised when
    adding an edge would create a cycle, making topological sorting
    impossible.

    Attributes:
        message: Description of the cycle detection.
        cycle_path: Optional list of node IDs forming the cycle.
    """

    def __init__(
        self,
        message: str = "Cycle detected in DAG",
        cycle_path: list[str] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Description of the cycle detection.
            cycle_path: Optional list of node IDs forming the cycle.
        """
        self.cycle_path = cycle_path
        if cycle_path:
            path_str = " -> ".join(cycle_path)
            message = f"{message}: {path_str}"
        super().__init__(message)


class NodeNotFoundError(Exception):
    """Exception raised when a referenced node does not exist in the DAG.

    This exception is raised when attempting to perform operations on
    nodes that haven't been added to the DAG.

    Attributes:
        node_id: The ID of the node that was not found.
        message: Description of the error.
    """

    def __init__(
        self,
        node_id: str,
        message: str | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            node_id: The ID of the node that was not found.
            message: Optional custom error message.
        """
        self.node_id = node_id
        if message is None:
            message = f"Node '{node_id}' not found in DAG"
        super().__init__(message)


class DAGValidationError(Exception):
    """Exception raised when DAG validation fails.

    This exception is raised when the DAG structure is invalid, such as
    when there are validation errors that prevent proper execution.

    Attributes:
        errors: List of validation error messages.
        message: Combined error message.
    """

    def __init__(
        self,
        errors: list[str],
        message: str | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            errors: List of validation error messages.
            message: Optional custom error message.
        """
        self.errors = errors
        if message is None:
            if errors:
                message = f"DAG validation failed: {'; '.join(errors)}"
            else:
                message = "DAG validation failed"
        super().__init__(message)


class ExecutionError(Exception):
    """Exception raised when DAG execution fails.

    This exception is raised during execution engine operations when
    a node fails, timeout occurs, or other execution-related errors happen.

    Attributes:
        node_id: ID of the node where the error occurred (if applicable).
        message: Description of the execution error.
        cause: Underlying exception that caused the failure.
    """

    def __init__(
        self,
        message: str,
        node_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Description of the execution error.
            node_id: ID of the node where the error occurred (if applicable).
            cause: Underlying exception that caused the failure.
        """
        self.node_id = node_id
        self.cause = cause
        if node_id:
            message = f"[{node_id}] {message}"
        super().__init__(message)


class ToolNotFoundError(Exception):
    """Exception raised when a tool is not found in the registry.

    This exception is raised when attempting to retrieve or execute
    a tool that has not been registered.

    Attributes:
        tool_name: Name of the tool that was not found.
    """

    def __init__(self, tool_name: str) -> None:
        """Initialize the exception.

        Args:
            tool_name: Name of the tool that was not found.
        """
        self.tool_name = tool_name
        super().__init__(f"Tool not found: {tool_name}")


class AgentForgeError(Exception):
    """Base exception for all AgentForge errors.

    All custom exceptions in AgentForge should inherit from this class
    to allow for catch-all exception handling.
    """

    pass


class MCPError(AgentForgeError):
    """MCP-related error.

    This exception is raised when MCP (Model Context Protocol) operations
    fail, such as connection errors, tool discovery failures, or execution
    errors.

    Attributes:
        message: Description of the error.
        server: Optional server identifier where the error occurred.
    """

    def __init__(self, message: str, server: str | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Description of the error.
            server: Optional server identifier where the error occurred.
        """
        self.server = server
        if server:
            message = f"[{server}] {message}"
        super().__init__(message)


__all__ = [
    "CycleDetectedError",
    "NodeNotFoundError",
    "DAGValidationError",
    "ExecutionError",
    "ToolNotFoundError",
    "AgentForgeError",
    "MCPError",
]

"""Directed Acyclic Graph (DAG) implementation for AgentForge.

This module provides the core DAG data structure for defining agent
execution order and dependencies. The DAG ensures acyclic dependencies
and supports topological sorting for execution planning.

Example:
    ```python
    from agentforge.core.dag import DAG, DAGConfig

    # Create a DAG
    dag = DAG(config=DAGConfig(name="my_workflow"))

    # Add agents as nodes
    dag.add_node("input_agent", input_agent)
    dag.add_node("process_agent", process_agent)
    dag.add_node("output_agent", output_agent)

    # Define execution order
    dag.add_edge("input_agent", "process_agent")
    dag.add_edge("process_agent", "output_agent")

    # Get execution order
    execution_order = dag.topological_sort()
    ```
"""

from collections import deque

from pydantic import BaseModel

from agentforge.core.agent import BaseAgent
from agentforge.core.exceptions import (
    CycleDetectedError,
    DAGValidationError,
    NodeNotFoundError,
)


class DAGConfig(BaseModel):
    """Configuration for a DAG instance.

    Attributes:
        name: Human-readable name for the DAG.
        max_retries: Maximum number of retry attempts for failed nodes.
        timeout: Optional timeout in seconds for the entire DAG execution.
        fail_fast: If True, cancel all pending nodes on first failure.
    """
    name: str = "default_dag"
    max_retries: int = 3
    timeout: float | None = None
    fail_fast: bool = False


class DAG:
    """Directed Acyclic Graph for agent workflow definition.

    A DAG defines the execution order and dependencies between agents.
    It ensures that the graph remains acyclic and provides methods
    for topological sorting and execution planning.

    Attributes:
        config: Configuration for this DAG instance.

    Example:
        ```python
        dag = DAG()
        dag.add_node("a", agent_a)
        dag.add_node("b", agent_b)
        dag.add_edge("a", "b")  # a must complete before b

        # Get nodes ready to execute
        ready = dag.get_ready_nodes(completed={"a"})  # Returns ["b"]
        ```
    """

    def __init__(
        self,
        config: DAGConfig | None = None,
        *,
        name: str | None = None,
    ) -> None:
        """Initialize an empty DAG.

        Args:
            config: Optional configuration for the DAG.
            name: Optional DAG name override for ergonomic construction.
        """
        if config is None:
            self.config = DAGConfig(name=name or "default_dag")
        elif name is None:
            self.config = config
        else:
            self.config = config.model_copy(update={"name": name})
        self._nodes: dict[str, BaseAgent | None] = {}
        # Adjacency list: node_id -> set of successor node_ids
        self._adjacency: dict[str, set[str]] = {}
        # Reverse adjacency list: node_id -> set of predecessor node_ids
        self._reverse_adjacency: dict[str, set[str]] = {}

    # ==================== Node Management ====================

    def add_node(self, node_id: str, agent: BaseAgent) -> None:
        """Add an agent node to the DAG.

        Args:
            node_id: Unique identifier for the node.
            agent: The agent instance to associate with this node.

        Raises:
            ValueError: If a node with the same ID already exists.
        """
        if node_id in self._nodes:
            # Allow replacing deserialized placeholder nodes (agent=None)
            if self._nodes[node_id] is None:
                self._nodes[node_id] = agent
                return
            raise ValueError(f"Node '{node_id}' already exists in DAG")

        self._nodes[node_id] = agent
        self._adjacency[node_id] = set()
        self._reverse_adjacency[node_id] = set()

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its edges from the DAG.

        Args:
            node_id: The ID of the node to remove.

        Raises:
            NodeNotFoundError: If the node does not exist.
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)

        # Remove all outgoing edges
        for successor in list(self._adjacency[node_id]):
            self._reverse_adjacency[successor].discard(node_id)

        # Remove all incoming edges
        for predecessor in list(self._reverse_adjacency[node_id]):
            self._adjacency[predecessor].discard(node_id)

        # Remove the node
        del self._nodes[node_id]
        del self._adjacency[node_id]
        del self._reverse_adjacency[node_id]

    def get_node(self, node_id: str) -> BaseAgent | None:
        """Get the agent associated with a node.

        Args:
            node_id: The ID of the node to retrieve.

        Returns:
            The agent instance, or None if the node doesn't exist.
        """
        return self._nodes.get(node_id)

    @property
    def nodes(self) -> list[str]:
        """Return all node IDs in the DAG.

        Returns:
            List of all node IDs.
        """
        return list(self._nodes.keys())

    # ==================== Edge Management ====================

    def add_edge(self, source: str, target: str) -> None:
        """Add a directed edge from source to target.

        The edge indicates that the source node must complete before
        the target node can execute.

        Args:
            source: ID of the source (upstream) node.
            target: ID of the target (downstream) node.

        Raises:
            NodeNotFoundError: If either node does not exist.
            CycleDetectedError: If adding the edge would create a cycle.
        """
        if source not in self._nodes:
            raise NodeNotFoundError(source)
        if target not in self._nodes:
            raise NodeNotFoundError(target)

        # Check if edge already exists
        if target in self._adjacency[source]:
            return  # Edge already exists, no-op

        # Temporarily add the edge
        self._adjacency[source].add(target)
        self._reverse_adjacency[target].add(source)

        # Check for cycle
        if self._has_cycle():
            # Remove the edge if it creates a cycle
            self._adjacency[source].discard(target)
            self._reverse_adjacency[target].discard(source)

            # Find the cycle path for error message
            cycle_path = self._find_cycle_path(source, target)
            raise CycleDetectedError(
                f"Adding edge '{source}' -> '{target}' would create a cycle",
                cycle_path,
            )

    def remove_edge(self, source: str, target: str) -> None:
        """Remove a directed edge from the DAG.

        Args:
            source: ID of the source node.
            target: ID of the target node.

        Raises:
            NodeNotFoundError: If either node does not exist.
        """
        if source not in self._nodes:
            raise NodeNotFoundError(source)
        if target not in self._nodes:
            raise NodeNotFoundError(target)

        self._adjacency[source].discard(target)
        self._reverse_adjacency[target].discard(source)

    @property
    def edges(self) -> list[tuple[str, str]]:
        """Return all edges as a list of (source, target) tuples.

        Returns:
            List of all edges in the DAG.
        """
        result = []
        for source, targets in self._adjacency.items():
            for target in targets:
                result.append((source, target))
        return result

    def successors(self, node_id: str) -> list[str]:
        """Get all downstream nodes (nodes that depend on this node).

        Args:
            node_id: The ID of the node.

        Returns:
            List of successor node IDs.

        Raises:
            NodeNotFoundError: If the node does not exist.
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        return list(self._adjacency[node_id])

    def predecessors(self, node_id: str) -> list[str]:
        """Get all upstream nodes (nodes this node depends on).

        Args:
            node_id: The ID of the node.

        Returns:
            List of predecessor node IDs.

        Raises:
            NodeNotFoundError: If the node does not exist.
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        return list(self._reverse_adjacency[node_id])

    # ==================== Graph Analysis ====================

    def in_degree(self, node_id: str) -> int:
        """Get the number of incoming edges for a node.

        Args:
            node_id: The ID of the node.

        Returns:
            Number of incoming edges.

        Raises:
            NodeNotFoundError: If the node does not exist.
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        return len(self._reverse_adjacency[node_id])

    def out_degree(self, node_id: str) -> int:
        """Get the number of outgoing edges for a node.

        Args:
            node_id: The ID of the node.

        Returns:
            Number of outgoing edges.

        Raises:
            NodeNotFoundError: If the node does not exist.
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        return len(self._adjacency[node_id])

    def topological_sort(self) -> list[str]:
        """Return nodes in topological order using Kahn's algorithm.

        The topological order ensures that every node appears before
        all nodes that depend on it.

        Returns:
            List of node IDs in topological order.

        Raises:
            DAGValidationError: If the graph has a cycle (should not happen
                if edges were added through add_edge).
        """
        if not self._nodes:
            return []

        # Calculate in-degrees
        in_degree = {node: len(self._reverse_adjacency[node]) for node in self._nodes}

        # Initialize queue with nodes that have no dependencies
        queue = deque([node for node, degree in in_degree.items() if degree == 0])

        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            # Reduce in-degree of successors
            for successor in self._adjacency[node]:
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)

        # If we couldn't process all nodes, there's a cycle
        if len(result) != len(self._nodes):
            raise DAGValidationError(
                ["Graph contains a cycle, cannot perform topological sort"]
            )

        return result

    def detect_cycle(self) -> bool:
        """Check if the graph contains any cycles.

        Returns:
            True if a cycle exists, False otherwise.
        """
        return self._has_cycle()

    def validate(self) -> list[str]:
        """Validate the DAG structure and return any errors.

        Performs comprehensive validation including:
        - Checking for cycles
        - Verifying all edge references are valid
        - Checking for isolated nodes (warning only)

        Returns:
            List of validation error messages. Empty if valid.
        """
        errors = []

        # Check for cycles
        if self._has_cycle():
            errors.append("Graph contains a cycle")

        # Check for isolated nodes (nodes with no edges)
        isolated_nodes = []
        for node_id in self._nodes:
            if not self._adjacency[node_id] and not self._reverse_adjacency[node_id]:
                isolated_nodes.append(node_id)

        if isolated_nodes:
            errors.append(f"Isolated nodes detected: {', '.join(isolated_nodes)}")

        return errors

    # ==================== Execution Support ====================

    def get_ready_nodes(self, completed: set[str]) -> list[str]:
        """Get nodes whose dependencies are all satisfied.

        A node is ready when all of its predecessors have been completed.

        Args:
            completed: Set of node IDs that have completed execution.

        Returns:
            List of node IDs that are ready to execute.
        """
        ready = []

        for node_id in self._nodes:
            # Skip already completed nodes
            if node_id in completed:
                continue

            # Check if all predecessors are completed
            predecessors = self._reverse_adjacency[node_id]
            if predecessors.issubset(completed):
                ready.append(node_id)

        return ready

    def get_root_nodes(self) -> list[str]:
        """Get nodes with no predecessors (entry points).

        Returns:
            List of node IDs that have no incoming edges.
        """
        return [
            node_id
            for node_id in self._nodes
            if not self._reverse_adjacency[node_id]
        ]

    def get_leaf_nodes(self) -> list[str]:
        """Get nodes with no successors (exit points).

        Returns:
            List of node IDs that have no outgoing edges.
        """
        return [
            node_id
            for node_id in self._nodes
            if not self._adjacency[node_id]
        ]

    # ==================== Serialization ====================

    def to_dict(self) -> dict:
        """Export the DAG structure as a dictionary.

        Note: Agents are serialized as their class names and IDs,
        as they cannot be fully serialized.

        Returns:
            Dictionary containing:
            - config: DAGConfig as dict
            - nodes: Dict of node_id to agent info
            - edges: List of (source, target) tuples
        """
        return {
            "config": self.config.model_dump(),
            "nodes": {
                node_id: {
                    "agent_class": agent.__class__.__name__ if agent is not None else None,
                    "agent_id": agent.agent_id if agent is not None else None,
                }
                for node_id, agent in self._nodes.items()
            },
            "edges": self.edges,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DAG":
        """Create a DAG from a dictionary representation.

        Note: This creates a DAG structure without agents. You'll need
        to call add_node() with actual agent instances.

        Args:
            data: Dictionary containing DAG structure.

        Returns:
            A new DAG instance with the structure from the dictionary.
        """
        config_data = data.get("config", {})
        config = DAGConfig(**config_data)

        dag = cls(config=config)

        # Add placeholder nodes (without agents)
        # Users must call add_node() with actual agents
        for node_id in data.get("nodes", {}):
            dag._nodes[node_id] = None  # type: ignore
            dag._adjacency[node_id] = set()
            dag._reverse_adjacency[node_id] = set()

        # Add edges
        errors = []
        for source, target in data.get("edges", []):
            if source not in dag._nodes:
                errors.append(f"Edge source '{source}' not found in nodes")
                continue
            if target not in dag._nodes:
                errors.append(f"Edge target '{target}' not found in nodes")
                continue
            dag._adjacency[source].add(target)
            dag._reverse_adjacency[target].add(source)

        if errors:
            raise DAGValidationError(errors)

        return dag

    # ==================== Private Methods ====================

    def _has_cycle(self) -> bool:
        """Check if the graph has a cycle using DFS.

        Returns:
            True if a cycle exists, False otherwise.
        """
        # States: 0 = unvisited, 1 = visiting, 2 = visited
        state: dict[str, int] = dict.fromkeys(self._nodes, 0)

        def dfs(node: str) -> bool:
            """Return True if a cycle is detected from this node."""
            if state[node] == 1:  # Back edge found
                return True
            if state[node] == 2:  # Already fully processed
                return False

            state[node] = 1  # Mark as visiting

            for successor in self._adjacency[node]:
                if dfs(successor):
                    return True

            state[node] = 2  # Mark as visited
            return False

        # Check from all nodes (handles disconnected components)
        return any(state[node] == 0 and dfs(node) for node in self._nodes)

    def _find_cycle_path(
        self, source: str, target: str
    ) -> list[str] | None:
        """Find a cycle path after adding edge source -> target.

        After adding an edge that creates a cycle, find the actual
        cycle path for error reporting.

        Args:
            source: The source of the newly added edge.
            target: The target of the newly added edge.

        Returns:
            List of node IDs forming the cycle, or None if not found.
        """
        # Use BFS to find path from target back to source
        visited = set()
        queue = deque([(target, [target])])

        while queue:
            node, path = queue.popleft()

            if node == source and len(path) > 1:
                # Found cycle: source -> target -> ... -> source
                return path + [source]

            if node in visited:
                continue
            visited.add(node)

            for successor in self._adjacency[node]:
                if successor not in visited or successor == source:
                    queue.append((successor, path + [successor]))

        return None

    def __repr__(self) -> str:
        """String representation of the DAG."""
        return (
            f"DAG(name={self.config.name!r}, "
            f"nodes={len(self._nodes)}, edges={len(self.edges)})"
        )

    def __len__(self) -> int:
        """Return the number of nodes in the DAG."""
        return len(self._nodes)

    def __contains__(self, node_id: str) -> bool:
        """Check if a node exists in the DAG."""
        return node_id in self._nodes


__all__ = [
    "DAG",
    "DAGConfig",
]

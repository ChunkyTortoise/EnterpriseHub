"""Comprehensive tests for the DAG implementation.

This module tests all aspects of the DAG class including:
- Node management (add, remove, get)
- Edge management (add, remove, successors, predecessors)
- Graph analysis (in_degree, out_degree, topological_sort, cycle detection)
- Execution support (ready nodes, root/leaf nodes)
- Serialization (to_dict, from_dict)
- Edge cases (empty DAG, single node, disconnected components)
"""

import pytest

from agentforge.core.agent import AgentInput, AgentOutput, BaseAgent
from agentforge.core.dag import DAG, DAGConfig
from agentforge.core.exceptions import (
    CycleDetectedError,
    DAGValidationError,
    NodeNotFoundError,
)
from agentforge.core.types import AgentConfig


class MockAgent(BaseAgent):
    """Mock agent for testing purposes."""

    async def execute(self, input: AgentInput) -> AgentOutput:
        """Return a simple response."""
        return AgentOutput(content=f"Mock response from {self.config.name}")


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    return MockAgent(config=AgentConfig(name="test_agent"))


@pytest.fixture
def empty_dag():
    """Create an empty DAG for testing."""
    return DAG()


@pytest.fixture
def simple_dag(mock_agent):
    """Create a simple DAG with three nodes in a chain."""
    dag = DAG(config=DAGConfig(name="test_dag"))

    agent_a = MockAgent(config=AgentConfig(name="agent_a"))
    agent_b = MockAgent(config=AgentConfig(name="agent_b"))
    agent_c = MockAgent(config=AgentConfig(name="agent_c"))

    dag.add_node("a", agent_a)
    dag.add_node("b", agent_b)
    dag.add_node("c", agent_c)

    dag.add_edge("a", "b")
    dag.add_edge("b", "c")

    return dag


class TestDAGConfig:
    """Tests for DAGConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DAGConfig()
        assert config.name == "default_dag"
        assert config.max_retries == 3
        assert config.timeout is None
        assert config.fail_fast is False

    def test_custom_config(self):
        """Test custom configuration values."""
        config = DAGConfig(
            name="custom_dag",
            max_retries=5,
            timeout=60.0,
            fail_fast=True,
        )
        assert config.name == "custom_dag"
        assert config.max_retries == 5
        assert config.timeout == 60.0
        assert config.fail_fast is True

    def test_constructor_accepts_name_override(self):
        """Test ergonomic DAG(name=...) constructor form."""
        dag = DAG(name="override")
        assert dag.config.name == "override"


class TestNodeManagement:
    """Tests for node management operations."""

    def test_add_node(self, empty_dag, mock_agent):
        """Test adding a node to the DAG."""
        empty_dag.add_node("test_node", mock_agent)

        assert "test_node" in empty_dag
        assert empty_dag.get_node("test_node") is mock_agent
        assert len(empty_dag) == 1

    def test_add_duplicate_node(self, empty_dag, mock_agent):
        """Test that adding a duplicate node raises an error."""
        empty_dag.add_node("test_node", mock_agent)

        with pytest.raises(ValueError, match="already exists"):
            empty_dag.add_node("test_node", mock_agent)

    def test_remove_node(self, simple_dag):
        """Test removing a node from the DAG."""
        assert "b" in simple_dag
        simple_dag.remove_node("b")
        assert "b" not in simple_dag
        assert simple_dag.get_node("b") is None

    def test_remove_node_removes_edges(self, simple_dag):
        """Test that removing a node also removes its edges."""
        simple_dag.remove_node("b")

        # Check that edges involving 'b' are removed
        edges = simple_dag.edges
        assert ("a", "b") not in edges
        assert ("b", "c") not in edges

        # Check that 'a' has no successors
        assert simple_dag.successors("a") == []

        # Check that 'c' has no predecessors
        assert simple_dag.predecessors("c") == []

    def test_remove_nonexistent_node(self, empty_dag):
        """Test that removing a nonexistent node raises an error."""
        with pytest.raises(NodeNotFoundError, match="nonexistent"):
            empty_dag.remove_node("nonexistent")

    def test_get_node(self, simple_dag):
        """Test getting a node by ID."""
        agent = simple_dag.get_node("a")
        assert agent is not None
        assert agent.config.name == "agent_a"

    def test_get_nonexistent_node(self, simple_dag):
        """Test getting a nonexistent node returns None."""
        assert simple_dag.get_node("nonexistent") is None

    def test_nodes_property(self, simple_dag):
        """Test the nodes property returns all node IDs."""
        nodes = simple_dag.nodes
        assert set(nodes) == {"a", "b", "c"}


class TestEdgeManagement:
    """Tests for edge management operations."""

    def test_add_edge(self, empty_dag, mock_agent):
        """Test adding an edge between nodes."""
        agent_a = MockAgent(config=AgentConfig(name="agent_a"))
        agent_b = MockAgent(config=AgentConfig(name="agent_b"))

        empty_dag.add_node("a", agent_a)
        empty_dag.add_node("b", agent_b)
        empty_dag.add_edge("a", "b")

        assert ("a", "b") in empty_dag.edges
        assert empty_dag.successors("a") == ["b"]
        assert empty_dag.predecessors("b") == ["a"]

    def test_add_edge_nonexistent_source(self, simple_dag):
        """Test that adding an edge with nonexistent source raises an error."""
        with pytest.raises(NodeNotFoundError, match="nonexistent"):
            simple_dag.add_edge("nonexistent", "a")

    def test_add_edge_nonexistent_target(self, simple_dag):
        """Test that adding an edge with nonexistent target raises an error."""
        with pytest.raises(NodeNotFoundError, match="nonexistent"):
            simple_dag.add_edge("a", "nonexistent")

    def test_add_duplicate_edge(self, simple_dag):
        """Test that adding a duplicate edge is a no-op."""
        initial_edges = len(simple_dag.edges)
        simple_dag.add_edge("a", "b")  # Already exists
        assert len(simple_dag.edges) == initial_edges

    def test_remove_edge(self, simple_dag):
        """Test removing an edge."""
        simple_dag.remove_edge("a", "b")

        assert ("a", "b") not in simple_dag.edges
        assert "b" not in simple_dag.successors("a")
        assert "a" not in simple_dag.predecessors("b")

    def test_remove_nonexistent_edge(self, simple_dag):
        """Test that removing a nonexistent edge is a no-op."""
        # Should not raise an error
        simple_dag.remove_edge("a", "c")  # This edge doesn't exist

    def test_edges_property(self, simple_dag):
        """Test the edges property returns all edges."""
        edges = simple_dag.edges
        assert set(edges) == {("a", "b"), ("b", "c")}

    def test_successors(self, simple_dag):
        """Test getting successors of a node."""
        assert simple_dag.successors("a") == ["b"]
        assert simple_dag.successors("b") == ["c"]
        assert simple_dag.successors("c") == []

    def test_predecessors(self, simple_dag):
        """Test getting predecessors of a node."""
        assert simple_dag.predecessors("a") == []
        assert simple_dag.predecessors("b") == ["a"]
        assert simple_dag.predecessors("c") == ["b"]

    def test_successors_nonexistent_node(self, simple_dag):
        """Test that getting successors of nonexistent node raises an error."""
        with pytest.raises(NodeNotFoundError):
            simple_dag.successors("nonexistent")

    def test_predecessors_nonexistent_node(self, simple_dag):
        """Test that getting predecessors of nonexistent node raises an error."""
        with pytest.raises(NodeNotFoundError):
            simple_dag.predecessors("nonexistent")


class TestCycleDetection:
    """Tests for cycle detection."""

    def test_detect_no_cycle(self, simple_dag):
        """Test that a valid DAG has no cycles."""
        assert simple_dag.detect_cycle() is False

    def test_add_edge_creates_cycle(self, simple_dag):
        """Test that adding an edge that creates a cycle raises an error."""
        with pytest.raises(CycleDetectedError) as exc_info:
            simple_dag.add_edge("c", "a")

        assert "cycle" in str(exc_info.value).lower()

    def test_cycle_detection_with_self_loop(self, empty_dag, mock_agent):
        """Test that self-loops are detected as cycles."""
        empty_dag.add_node("a", mock_agent)

        with pytest.raises(CycleDetectedError):
            empty_dag.add_edge("a", "a")

    def test_cycle_detection_complex(self, empty_dag):
        """Test cycle detection in a more complex graph."""
        # Create a diamond shape: a -> b, a -> c, b -> d, c -> d
        for name in ["a", "b", "c", "d"]:
            empty_dag.add_node(name, MockAgent(config=AgentConfig(name=name)))

        empty_dag.add_edge("a", "b")
        empty_dag.add_edge("a", "c")
        empty_dag.add_edge("b", "d")
        empty_dag.add_edge("c", "d")

        assert empty_dag.detect_cycle() is False

        # Adding d -> a would create a cycle
        with pytest.raises(CycleDetectedError):
            empty_dag.add_edge("d", "a")


class TestTopologicalSort:
    """Tests for topological sorting."""

    def test_topological_sort_empty_dag(self, empty_dag):
        """Test topological sort of an empty DAG."""
        assert empty_dag.topological_sort() == []

    def test_topological_sort_single_node(self, empty_dag, mock_agent):
        """Test topological sort of a single-node DAG."""
        empty_dag.add_node("a", mock_agent)
        assert empty_dag.topological_sort() == ["a"]

    def test_topological_sort_chain(self, simple_dag):
        """Test topological sort of a chain DAG."""
        result = simple_dag.topological_sort()
        assert result == ["a", "b", "c"]

    def test_topological_sort_diamond(self, empty_dag):
        """Test topological sort of a diamond-shaped DAG."""
        for name in ["a", "b", "c", "d"]:
            empty_dag.add_node(name, MockAgent(config=AgentConfig(name=name)))

        empty_dag.add_edge("a", "b")
        empty_dag.add_edge("a", "c")
        empty_dag.add_edge("b", "d")
        empty_dag.add_edge("c", "d")

        result = empty_dag.topological_sort()

        # 'a' must come first
        assert result[0] == "a"
        # 'd' must come last
        assert result[-1] == "d"
        # 'b' and 'c' must come after 'a' and before 'd'
        assert result.index("b") > result.index("a")
        assert result.index("c") > result.index("a")
        assert result.index("d") > result.index("b")
        assert result.index("d") > result.index("c")

    def test_topological_sort_disconnected(self, empty_dag):
        """Test topological sort of a disconnected DAG."""
        for name in ["a", "b", "c", "d"]:
            empty_dag.add_node(name, MockAgent(config=AgentConfig(name=name)))

        # Only connect a->b, leave c and d isolated
        empty_dag.add_edge("a", "b")

        result = empty_dag.topological_sort()

        # 'a' must come before 'b'
        assert result.index("a") < result.index("b")
        # All nodes should be present
        assert set(result) == {"a", "b", "c", "d"}


class TestGraphAnalysis:
    """Tests for graph analysis methods."""

    def test_in_degree(self, simple_dag):
        """Test in-degree calculation."""
        assert simple_dag.in_degree("a") == 0
        assert simple_dag.in_degree("b") == 1
        assert simple_dag.in_degree("c") == 1

    def test_out_degree(self, simple_dag):
        """Test out-degree calculation."""
        assert simple_dag.out_degree("a") == 1
        assert simple_dag.out_degree("b") == 1
        assert simple_dag.out_degree("c") == 0

    def test_in_degree_nonexistent_node(self, simple_dag):
        """Test that in-degree of nonexistent node raises an error."""
        with pytest.raises(NodeNotFoundError):
            simple_dag.in_degree("nonexistent")

    def test_out_degree_nonexistent_node(self, simple_dag):
        """Test that out-degree of nonexistent node raises an error."""
        with pytest.raises(NodeNotFoundError):
            simple_dag.out_degree("nonexistent")

    def test_validate_valid_dag(self, simple_dag):
        """Test validation of a valid DAG."""
        errors = simple_dag.validate()
        assert errors == []

    def test_validate_empty_dag(self, empty_dag):
        """Test validation of an empty DAG."""
        errors = empty_dag.validate()
        assert errors == []

    def test_validate_isolated_nodes(self, empty_dag):
        """Test validation detects isolated nodes."""
        for name in ["a", "b"]:
            empty_dag.add_node(name, MockAgent(config=AgentConfig(name=name)))

        errors = empty_dag.validate()
        assert len(errors) == 1
        assert "Isolated nodes" in errors[0]


class TestExecutionSupport:
    """Tests for execution support methods."""

    def test_get_ready_nodes_empty_dag(self, empty_dag):
        """Test getting ready nodes from an empty DAG."""
        assert empty_dag.get_ready_nodes(set()) == []

    def test_get_ready_nodes_no_completed(self, simple_dag):
        """Test getting ready nodes with nothing completed."""
        ready = simple_dag.get_ready_nodes(set())
        assert ready == ["a"]  # Only root node is ready

    def test_get_ready_nodes_partial_completion(self, simple_dag):
        """Test getting ready nodes with partial completion."""
        ready = simple_dag.get_ready_nodes({"a"})
        assert ready == ["b"]

        ready = simple_dag.get_ready_nodes({"a", "b"})
        assert ready == ["c"]

    def test_get_ready_nodes_all_completed(self, simple_dag):
        """Test getting ready nodes when all are completed."""
        ready = simple_dag.get_ready_nodes({"a", "b", "c"})
        assert ready == []

    def test_get_ready_nodes_diamond(self, empty_dag):
        """Test getting ready nodes in a diamond DAG."""
        for name in ["a", "b", "c", "d"]:
            empty_dag.add_node(name, MockAgent(config=AgentConfig(name=name)))

        empty_dag.add_edge("a", "b")
        empty_dag.add_edge("a", "c")
        empty_dag.add_edge("b", "d")
        empty_dag.add_edge("c", "d")

        # Initially only 'a' is ready
        assert empty_dag.get_ready_nodes(set()) == ["a"]

        # After 'a' completes, both 'b' and 'c' are ready
        ready = set(empty_dag.get_ready_nodes({"a"}))
        assert ready == {"b", "c"}

        # After 'a' and 'b' complete, only 'c' is ready (d still waiting for c)
        ready = empty_dag.get_ready_nodes({"a", "b"})
        assert ready == ["c"]

        # After 'a', 'b', 'c' complete, 'd' is ready
        ready = empty_dag.get_ready_nodes({"a", "b", "c"})
        assert ready == ["d"]

    def test_get_root_nodes(self, simple_dag):
        """Test getting root nodes."""
        assert simple_dag.get_root_nodes() == ["a"]

    def test_get_root_nodes_multiple(self, empty_dag):
        """Test getting multiple root nodes."""
        for name in ["a", "b", "c"]:
            empty_dag.add_node(name, MockAgent(config=AgentConfig(name=name)))

        empty_dag.add_edge("a", "c")
        # 'a' and 'b' are both roots

        roots = set(empty_dag.get_root_nodes())
        assert roots == {"a", "b"}

    def test_get_leaf_nodes(self, simple_dag):
        """Test getting leaf nodes."""
        assert simple_dag.get_leaf_nodes() == ["c"]

    def test_get_leaf_nodes_multiple(self, empty_dag):
        """Test getting multiple leaf nodes."""
        for name in ["a", "b", "c"]:
            empty_dag.add_node(name, MockAgent(config=AgentConfig(name=name)))

        empty_dag.add_edge("a", "b")
        # 'b' and 'c' are both leaves

        leaves = set(empty_dag.get_leaf_nodes())
        assert leaves == {"b", "c"}


class TestSerialization:
    """Tests for serialization and deserialization."""

    def test_to_dict(self, simple_dag):
        """Test exporting DAG to dictionary."""
        data = simple_dag.to_dict()

        assert data["config"]["name"] == "test_dag"
        assert set(data["nodes"].keys()) == {"a", "b", "c"}
        assert set(data["edges"]) == {("a", "b"), ("b", "c")}

    def test_to_dict_empty_dag(self, empty_dag):
        """Test exporting empty DAG to dictionary."""
        data = empty_dag.to_dict()

        assert data["config"]["name"] == "default_dag"
        assert data["nodes"] == {}
        assert data["edges"] == []

    def test_from_dict(self, simple_dag):
        """Test creating DAG from dictionary."""
        data = simple_dag.to_dict()
        new_dag = DAG.from_dict(data)

        assert new_dag.config.name == "test_dag"
        assert set(new_dag.nodes) == {"a", "b", "c"}
        assert set(new_dag.edges) == {("a", "b"), ("b", "c")}

    def test_from_dict_preserves_structure(self, empty_dag):
        """Test that from_dict preserves graph structure."""
        for name in ["a", "b", "c", "d"]:
            empty_dag.add_node(name, MockAgent(config=AgentConfig(name=name)))

        empty_dag.add_edge("a", "b")
        empty_dag.add_edge("a", "c")
        empty_dag.add_edge("b", "d")
        empty_dag.add_edge("c", "d")

        data = empty_dag.to_dict()
        new_dag = DAG.from_dict(data)

        # Verify structure is preserved
        assert new_dag.successors("a") == ["b", "c"] or new_dag.successors("a") == ["c", "b"]
        assert set(new_dag.predecessors("d")) == {"b", "c"}

    def test_from_dict_without_agents(self):
        """Test that from_dict creates structure without agents."""
        data = {
            "config": {"name": "test"},
            "nodes": {"a": {}, "b": {}},
            "edges": [("a", "b")],
        }

        dag = DAG.from_dict(data)

        # Nodes exist but agents are None
        assert "a" in dag
        assert "b" in dag
        assert dag.get_node("a") is None
        assert dag.get_node("b") is None

    def test_from_dict_placeholder_nodes_can_be_hydrated(self):
        """Test that placeholder nodes can be replaced with real agents."""
        data = {
            "config": {"name": "test"},
            "nodes": {"a": {}, "b": {}},
            "edges": [("a", "b")],
        }

        dag = DAG.from_dict(data)

        dag.add_node("a", MockAgent(config=AgentConfig(name="agent_a")))
        dag.add_node("b", MockAgent(config=AgentConfig(name="agent_b")))

        assert dag.get_node("a") is not None
        assert dag.get_node("b") is not None
        assert set(dag.edges) == {("a", "b")}

    def test_from_dict_invalid_edge_reference_raises(self):
        """Test that from_dict validates edge references."""
        data = {
            "config": {"name": "test"},
            "nodes": {"a": {}},
            "edges": [("a", "missing")],
        }

        with pytest.raises(DAGValidationError, match="Edge target 'missing'"):
            DAG.from_dict(data)


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_dag(self, empty_dag):
        """Test operations on an empty DAG."""
        assert len(empty_dag) == 0
        assert empty_dag.nodes == []
        assert empty_dag.edges == []
        assert empty_dag.topological_sort() == []
        assert empty_dag.get_root_nodes() == []
        assert empty_dag.get_leaf_nodes() == []
        assert empty_dag.detect_cycle() is False

    def test_single_node(self, empty_dag, mock_agent):
        """Test operations on a single-node DAG."""
        empty_dag.add_node("a", mock_agent)

        assert len(empty_dag) == 1
        assert empty_dag.nodes == ["a"]
        assert empty_dag.edges == []
        assert empty_dag.topological_sort() == ["a"]
        assert empty_dag.get_root_nodes() == ["a"]
        assert empty_dag.get_leaf_nodes() == ["a"]
        assert empty_dag.in_degree("a") == 0
        assert empty_dag.out_degree("a") == 0

    def test_disconnected_components(self, empty_dag):
        """Test a DAG with disconnected components."""
        # Create two separate chains
        for name in ["a1", "a2", "b1", "b2"]:
            empty_dag.add_node(name, MockAgent(config=AgentConfig(name=name)))

        empty_dag.add_edge("a1", "a2")
        empty_dag.add_edge("b1", "b2")

        # Both chains should be independent
        assert set(empty_dag.get_root_nodes()) == {"a1", "b1"}
        assert set(empty_dag.get_leaf_nodes()) == {"a2", "b2"}

        # Topological sort should include all nodes
        result = empty_dag.topological_sort()
        assert set(result) == {"a1", "a2", "b1", "b2"}

        # Verify ordering within each chain
        assert result.index("a1") < result.index("a2")
        assert result.index("b1") < result.index("b2")

    def test_contains_operator(self, simple_dag):
        """Test the __contains__ operator."""
        assert "a" in simple_dag
        assert "b" in simple_dag
        assert "nonexistent" not in simple_dag

    def test_len_operator(self, simple_dag):
        """Test the __len__ operator."""
        assert len(simple_dag) == 3

    def test_repr(self, simple_dag):
        """Test the __repr__ method."""
        repr_str = repr(simple_dag)
        assert "DAG" in repr_str
        assert "test_dag" in repr_str
        assert "nodes=3" in repr_str
        assert "edges=2" in repr_str


class TestDAGValidationErrors:
    """Tests for DAGValidationError scenarios."""

    def test_validation_error_format(self):
        """Test that DAGValidationError formats errors correctly."""
        errors = ["Error 1", "Error 2"]
        exc = DAGValidationError(errors)

        assert "Error 1" in str(exc)
        assert "Error 2" in str(exc)
        assert exc.errors == errors

    def test_validation_error_empty(self):
        """Test DAGValidationError with no errors."""
        exc = DAGValidationError([])
        assert "DAG validation failed" in str(exc)


class TestNodeNotFoundError:
    """Tests for NodeNotFoundError scenarios."""

    def test_error_message(self):
        """Test that NodeNotFoundError has correct message."""
        exc = NodeNotFoundError("test_node")
        assert "test_node" in str(exc)
        assert exc.node_id == "test_node"

    def test_custom_message(self):
        """Test NodeNotFoundError with custom message."""
        exc = NodeNotFoundError("test_node", "Custom error")
        assert str(exc) == "Custom error"


class TestCycleDetectedError:
    """Tests for CycleDetectedError scenarios."""

    def test_error_message(self):
        """Test that CycleDetectedError has correct message."""
        exc = CycleDetectedError("Cycle found")
        assert "Cycle found" in str(exc)

    def test_error_with_path(self):
        """Test CycleDetectedError with cycle path."""
        exc = CycleDetectedError(cycle_path=["a", "b", "c", "a"])
        assert "a -> b -> c -> a" in str(exc)
        assert exc.cycle_path == ["a", "b", "c", "a"]

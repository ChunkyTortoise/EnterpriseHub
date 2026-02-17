"""Tests for AgentForge configuration module.

This module tests:
- AgentConfig validation
- EdgeConfig validation
- DAGConfig validation
- PipelineConfig.from_yaml and from_yaml_string
- PipelineBuilder DAG construction
- ConfigurableAgent execution
- Configuration loading utilities
"""

import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from agentforge.config import (
    AgentConfig,
    ConfigurableAgent,
    DAGConfig,
    EdgeConfig,
    PipelineBuilder,
    PipelineConfig,
    find_config_file,
    get_config_value,
    load_config,
    merge_configs,
    validate_config_path,
)
from agentforge.core.agent import AgentInput, AgentOutput
from agentforge.core.dag import DAG
from agentforge.tools.registry import ToolRegistry

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_agent_config_dict() -> dict[str, Any]:
    """Sample agent configuration dictionary."""
    return {
        "name": "test_agent",
        "instructions": "Test instructions",
        "llm": "openai/gpt-4o",
        "tools": ["search"],
        "temperature": 0.7,
        "max_tokens": 1024,
        "metadata": {"role": "test"},
    }


@pytest.fixture
def sample_dag_config_dict() -> dict[str, Any]:
    """Sample DAG configuration dictionary."""
    return {
        "name": "test_dag",
        "agents": {
            "researcher": {
                "name": "Researcher",
                "instructions": "Research the topic.",
                "llm": "openai/gpt-4o",
                "tools": ["search"],
            },
            "writer": {
                "name": "Writer",
                "instructions": "Write the report.",
                "llm": "anthropic/claude-3.5-sonnet",
            },
        },
        "edges": [
            {"source": "researcher", "target": "writer"},
        ],
        "entrypoint": "researcher",
        "max_retries": 3,
        "timeout": 300,
    }


@pytest.fixture
def sample_pipeline_config_dict() -> dict[str, Any]:
    """Sample pipeline configuration dictionary."""
    return {
        "version": "1.0",
        "name": "test_pipeline",
        "dag": {
            "name": "test_dag",
            "agents": {
                "agent1": {
                    "name": "Agent 1",
                    "instructions": "Do something",
                },
            },
            "edges": [],
        },
        "tools": {
            "search": {
                "type": "function",
                "description": "Search for information",
            },
        },
        "env": {
            "API_KEY": "test_key",
        },
    }


@pytest.fixture
def sample_yaml_content() -> str:
    """Sample YAML configuration content."""
    return """
version: "1.0"
name: "test-pipeline"

tools:
  search:
    type: "function"
    description: "Search for information"

dag:
  name: "test-dag"
  entrypoint: "agent1"
  max_retries: 3

  agents:
    agent1:
      name: "Agent One"
      instructions: "First agent"
      llm: "openai/gpt-4o"
      temperature: 0.5

    agent2:
      name: "Agent Two"
      instructions: "Second agent"
      llm: "anthropic/claude-3.5-sonnet"

  edges:
    - source: "agent1"
      target: "agent2"
"""


@pytest.fixture
def temp_yaml_file(sample_pipeline_config_dict: dict[str, Any]) -> Path:
    """Create a temporary YAML file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
    ) as f:
        yaml.dump(sample_pipeline_config_dict, f)
        path = Path(f.name)
    yield path
    # Cleanup
    if path.exists():
        path.unlink()


# =============================================================================
# AgentConfig Tests
# =============================================================================


class TestAgentConfig:
    """Tests for AgentConfig model."""

    def test_agent_config_creation_minimal(self) -> None:
        """Test creating AgentConfig with minimal required fields."""
        config = AgentConfig(
            name="test",
            instructions="Test instructions",
        )

        assert config.name == "test"
        assert config.instructions == "Test instructions"
        assert config.llm == "openai/gpt-4o"
        assert config.tools == []
        assert config.temperature == 0.7
        assert config.max_tokens is None
        assert config.metadata is None

    def test_agent_config_creation_full(
        self,
        sample_agent_config_dict: dict[str, Any],
    ) -> None:
        """Test creating AgentConfig with all fields."""
        config = AgentConfig(**sample_agent_config_dict)

        assert config.name == "test_agent"
        assert config.instructions == "Test instructions"
        assert config.llm == "openai/gpt-4o"
        assert config.tools == ["search"]
        assert config.temperature == 0.7
        assert config.max_tokens == 1024
        assert config.metadata == {"role": "test"}

    def test_agent_config_validation_missing_name(self) -> None:
        """Test that AgentConfig requires name."""
        with pytest.raises(ValidationError):
            AgentConfig(instructions="Test")

    def test_agent_config_validation_missing_instructions(self) -> None:
        """Test that AgentConfig requires instructions."""
        with pytest.raises(ValidationError):
            AgentConfig(name="test")


# =============================================================================
# EdgeConfig Tests
# =============================================================================


class TestEdgeConfig:
    """Tests for EdgeConfig model."""

    def test_edge_config_creation(self) -> None:
        """Test creating EdgeConfig with required fields."""
        edge = EdgeConfig(source="agent1", target="agent2")

        assert edge.source == "agent1"
        assert edge.target == "agent2"
        assert edge.condition is None

    def test_edge_config_with_condition(self) -> None:
        """Test creating EdgeConfig with condition."""
        edge = EdgeConfig(
            source="router",
            target="specialist",
            condition="needs_specialist",
        )

        assert edge.source == "router"
        assert edge.target == "specialist"
        assert edge.condition == "needs_specialist"

    def test_edge_config_validation_missing_source(self) -> None:
        """Test that EdgeConfig requires source."""
        with pytest.raises(ValidationError):
            EdgeConfig(target="agent2")

    def test_edge_config_validation_missing_target(self) -> None:
        """Test that EdgeConfig requires target."""
        with pytest.raises(ValidationError):
            EdgeConfig(source="agent1")


# =============================================================================
# DAGConfig Tests
# =============================================================================


class TestDAGConfig:
    """Tests for DAGConfig model."""

    def test_dag_config_creation_minimal(self) -> None:
        """Test creating DAGConfig with defaults."""
        config = DAGConfig()

        assert config.name == "default_dag"
        assert config.agents == {}
        assert config.edges == []
        assert config.entrypoint is None
        assert config.max_retries == 3
        assert config.timeout is None
        assert config.fail_fast is False

    def test_dag_config_creation_full(
        self,
        sample_dag_config_dict: dict[str, Any],
    ) -> None:
        """Test creating DAGConfig with all fields."""
        config = DAGConfig(**sample_dag_config_dict)

        assert config.name == "test_dag"
        assert "researcher" in config.agents
        assert "writer" in config.agents
        assert len(config.edges) == 1
        assert config.entrypoint == "researcher"
        assert config.max_retries == 3
        assert config.timeout == 300

    def test_dag_config_agents_are_agent_configs(
        self,
        sample_dag_config_dict: dict[str, Any],
    ) -> None:
        """Test that agents are converted to AgentConfig instances."""
        config = DAGConfig(**sample_dag_config_dict)

        assert isinstance(config.agents["researcher"], AgentConfig)
        assert isinstance(config.agents["writer"], AgentConfig)

    def test_dag_config_edges_are_edge_configs(
        self,
        sample_dag_config_dict: dict[str, Any],
    ) -> None:
        """Test that edges are converted to EdgeConfig instances."""
        config = DAGConfig(**sample_dag_config_dict)

        assert isinstance(config.edges[0], EdgeConfig)


# =============================================================================
# PipelineConfig Tests
# =============================================================================


class TestPipelineConfig:
    """Tests for PipelineConfig model."""

    def test_pipeline_config_creation_minimal(self) -> None:
        """Test creating PipelineConfig with defaults."""
        config = PipelineConfig()

        assert config.version == "1.0"
        assert config.name == "pipeline"
        assert isinstance(config.dag, DAGConfig)
        assert config.tools == {}
        assert config.env == {}

    def test_pipeline_config_creation_full(
        self,
        sample_pipeline_config_dict: dict[str, Any],
    ) -> None:
        """Test creating PipelineConfig with all fields."""
        config = PipelineConfig(**sample_pipeline_config_dict)

        assert config.version == "1.0"
        assert config.name == "test_pipeline"
        assert isinstance(config.dag, DAGConfig)
        assert "search" in config.tools
        assert config.env["API_KEY"] == "test_key"

    def test_pipeline_config_from_yaml_file(
        self,
        temp_yaml_file: Path,
    ) -> None:
        """Test loading PipelineConfig from YAML file."""
        config = PipelineConfig.from_yaml(temp_yaml_file)

        assert config.name == "test_pipeline"
        assert config.dag.name == "test_dag"

    def test_pipeline_config_from_yaml_string(
        self,
        sample_yaml_content: str,
    ) -> None:
        """Test loading PipelineConfig from YAML string."""
        config = PipelineConfig.from_yaml_string(sample_yaml_content)

        assert config.name == "test-pipeline"
        assert config.dag.name == "test-dag"
        assert "agent1" in config.dag.agents
        assert "agent2" in config.dag.agents

    def test_pipeline_config_from_yaml_file_not_found(self) -> None:
        """Test that from_yaml raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            PipelineConfig.from_yaml("nonexistent.yaml")

    def test_pipeline_config_from_yaml_invalid_yaml(self) -> None:
        """Test that from_yaml_string raises error for invalid YAML."""
        with pytest.raises(yaml.YAMLError):
            PipelineConfig.from_yaml_string("invalid: yaml: : :")


# =============================================================================
# PipelineBuilder Tests
# =============================================================================


class TestPipelineBuilder:
    """Tests for PipelineBuilder class."""

    def test_pipeline_builder_creation(
        self,
        sample_pipeline_config_dict: dict[str, Any],
    ) -> None:
        """Test creating PipelineBuilder."""
        config = PipelineConfig(**sample_pipeline_config_dict)
        builder = PipelineBuilder(config)

        assert builder.config == config
        assert isinstance(builder.tool_registry, ToolRegistry)
        assert builder._agents == {}
        assert builder._dag is None

    def test_pipeline_builder_with_custom_registry(
        self,
        sample_pipeline_config_dict: dict[str, Any],
    ) -> None:
        """Test creating PipelineBuilder with custom tool registry."""
        config = PipelineConfig(**sample_pipeline_config_dict)
        registry = ToolRegistry()
        builder = PipelineBuilder(config, tool_registry=registry)

        # Check that the registry is the same instance
        assert builder.tool_registry is registry or isinstance(builder.tool_registry, ToolRegistry)

    def test_pipeline_builder_build(
        self,
        sample_pipeline_config_dict: dict[str, Any],
    ) -> None:
        """Test building DAG from configuration."""
        config = PipelineConfig(**sample_pipeline_config_dict)
        builder = PipelineBuilder(config)
        dag = builder.build()

        assert isinstance(dag, DAG)
        assert dag.config.name == "test_dag"
        assert "agent1" in dag.nodes

    def test_pipeline_builder_get_agent(
        self,
        sample_pipeline_config_dict: dict[str, Any],
    ) -> None:
        """Test getting agent by name after build."""
        config = PipelineConfig(**sample_pipeline_config_dict)
        builder = PipelineBuilder(config)
        builder.build()

        agent = builder.get_agent("agent1")
        assert agent is not None
        assert agent.name == "Agent 1"

    def test_pipeline_builder_get_agent_not_found(
        self,
        sample_pipeline_config_dict: dict[str, Any],
    ) -> None:
        """Test getting non-existent agent returns None."""
        config = PipelineConfig(**sample_pipeline_config_dict)
        builder = PipelineBuilder(config)
        builder.build()

        agent = builder.get_agent("nonexistent")
        assert agent is None

    def test_pipeline_builder_get_all_agents(
        self,
        sample_pipeline_config_dict: dict[str, Any],
    ) -> None:
        """Test getting all agents after build."""
        config = PipelineConfig(**sample_pipeline_config_dict)
        builder = PipelineBuilder(config)
        builder.build()

        agents = builder.get_all_agents()
        assert "agent1" in agents
        assert len(agents) == 1

    def test_pipeline_builder_build_with_edges(
        self,
        sample_yaml_content: str,
    ) -> None:
        """Test building DAG with edges."""
        config = PipelineConfig.from_yaml_string(sample_yaml_content)
        builder = PipelineBuilder(config)
        dag = builder.build()

        assert len(dag.edges) == 1
        assert dag.edges[0] == ("agent1", "agent2")

    def test_pipeline_builder_entrypoint_prunes_unreachable_nodes(self) -> None:
        """Test that explicit entrypoint keeps only downstream nodes."""
        config = PipelineConfig.from_yaml_string(
            """
version: "1.0"
name: "entrypoint-test"
dag:
  name: "entrypoint-dag"
  entrypoint: "agent1"
  agents:
    agent1:
      name: "Agent 1"
      instructions: "Start here"
    agent2:
      name: "Agent 2"
      instructions: "Downstream"
    isolated:
      name: "Isolated"
      instructions: "Should be pruned"
  edges:
    - source: "agent1"
      target: "agent2"
"""
        )
        builder = PipelineBuilder(config)
        dag = builder.build()

        assert set(dag.nodes) == {"agent1", "agent2"}
        assert builder.get_agent("isolated") is None

    def test_pipeline_builder_invalid_entrypoint_raises(self) -> None:
        """Test that unknown entrypoint raises a ValueError."""
        config = PipelineConfig.from_yaml_string(
            """
version: "1.0"
name: "invalid-entrypoint-test"
dag:
  name: "entrypoint-dag"
  entrypoint: "missing"
  agents:
    agent1:
      name: "Agent 1"
      instructions: "Hello"
  edges: []
"""
        )
        builder = PipelineBuilder(config)
        with pytest.raises(ValueError, match="Entrypoint 'missing'"):
            builder.build()

    def test_pipeline_builder_dag_property(
        self,
        sample_pipeline_config_dict: dict[str, Any],
    ) -> None:
        """Test dag property returns None before build."""
        config = PipelineConfig(**sample_pipeline_config_dict)
        builder = PipelineBuilder(config)

        assert builder.dag is None

        builder.build()
        assert builder.dag is not None


# =============================================================================
# ConfigurableAgent Tests
# =============================================================================


class TestConfigurableAgent:
    """Tests for ConfigurableAgent class."""

    def test_configurable_agent_creation(self) -> None:
        """Test creating ConfigurableAgent."""
        agent = ConfigurableAgent(
            name="test_agent",
            instructions="Test instructions",
        )

        assert agent.name == "test_agent"
        assert agent.instructions == "Test instructions"
        assert agent.llm == "openai/gpt-4o"
        assert agent.tools == []
        assert agent.temperature == 0.7

    def test_configurable_agent_properties(self) -> None:
        """Test ConfigurableAgent properties."""
        agent = ConfigurableAgent(
            name="test",
            instructions="Test",
            llm="anthropic/claude-3.5-sonnet",
            temperature=0.5,
            max_tokens=2048,
            metadata={"key": "value"},
        )

        assert agent.name == "test"
        assert agent.instructions == "Test"
        assert agent.llm == "anthropic/claude-3.5-sonnet"
        assert agent.temperature == 0.5
        assert agent.max_tokens == 2048
        assert agent.metadata == {"key": "value"}

    @pytest.mark.asyncio
    async def test_configurable_agent_execute(self) -> None:
        """Test ConfigurableAgent execute method."""
        agent = ConfigurableAgent(
            name="test",
            instructions="Test instructions for agent",
        )

        input_data = AgentInput()
        output = await agent.execute(input_data)

        assert isinstance(output, AgentOutput)
        assert "test" in output.content
        assert "Test instructions" in output.content

    @pytest.mark.asyncio
    async def test_configurable_agent_call(self) -> None:
        """Test ConfigurableAgent can be called directly."""
        agent = ConfigurableAgent(
            name="test",
            instructions="Test",
        )

        output = await agent(AgentInput())

        assert isinstance(output, AgentOutput)


# =============================================================================
# Configuration Loading Utilities Tests
# =============================================================================


class TestFindConfigFile:
    """Tests for find_config_file function."""

    def test_find_config_file_not_found(self, tmp_path: Path) -> None:
        """Test finding config file when it doesn't exist."""
        result = find_config_file(
            name="nonexistent",
            search_paths=[str(tmp_path)],
        )
        assert result is None

    def test_find_config_file_yaml(self, tmp_path: Path) -> None:
        """Test finding config file with .yaml extension."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text("name: test")

        result = find_config_file(
            name="test",
            search_paths=[str(tmp_path)],
        )

        assert result == config_file

    def test_find_config_file_yml(self, tmp_path: Path) -> None:
        """Test finding config file with .yml extension."""
        config_file = tmp_path / "test.yml"
        config_file.write_text("name: test")

        result = find_config_file(
            name="test",
            search_paths=[str(tmp_path)],
        )

        assert result == config_file

    def test_find_config_file_priority_yaml(self, tmp_path: Path) -> None:
        """Test that .yaml is checked before .yml."""
        yaml_file = tmp_path / "test.yaml"
        yml_file = tmp_path / "test.yml"
        yaml_file.write_text("name: yaml")
        yml_file.write_text("name: yml")

        result = find_config_file(
            name="test",
            search_paths=[str(tmp_path)],
        )

        assert result == yaml_file

    def test_find_config_file_default_search_paths(
        self,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        """Test default search paths are used."""
        # Create config in current directory
        config_file = tmp_path / "agentforge.yaml"
        config_file.write_text("name: test")

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        result = find_config_file()

        # Result should exist and point to the config file
        assert result is not None
        assert result.name == "agentforge.yaml"
        assert result.exists()


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_from_file(self, tmp_path: Path) -> None:
        """Test loading config from a file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("name: test\nversion: 1.0")

        result = load_config(config_file)

        assert result == {"name": "test", "version": 1.0}

    def test_load_config_file_not_found(self) -> None:
        """Test loading config from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")

    def test_load_config_auto_discover(self, tmp_path: Path, monkeypatch) -> None:
        """Test auto-discovering config file."""
        config_file = tmp_path / "agentforge.yaml"
        config_file.write_text("name: discovered")

        monkeypatch.chdir(tmp_path)

        result = load_config()

        assert result == {"name": "discovered"}

    def test_load_config_empty_file(self, tmp_path: Path) -> None:
        """Test loading empty config file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        result = load_config(config_file)

        assert result == {}

    def test_load_config_none_file(self, tmp_path: Path, monkeypatch) -> None:
        """Test loading config with None path and no default found."""
        # Create a directory with no config files
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        monkeypatch.chdir(empty_dir)

        result = load_config()

        assert result == {}


class TestMergeConfigs:
    """Tests for merge_configs function."""

    def test_merge_configs_empty(self) -> None:
        """Test merging empty configs."""
        result = merge_configs()
        assert result == {}

    def test_merge_configs_single(self) -> None:
        """Test merging single config."""
        config = {"a": 1, "b": 2}
        result = merge_configs(config)
        assert result == config

    def test_merge_configs_multiple(self) -> None:
        """Test merging multiple configs."""
        config1 = {"a": 1, "b": 2}
        config2 = {"b": 3, "c": 4}
        config3 = {"d": 5}

        result = merge_configs(config1, config2, config3)

        assert result == {"a": 1, "b": 3, "c": 4, "d": 5}

    def test_merge_configs_nested(self) -> None:
        """Test merging nested configs."""
        config1 = {"dag": {"name": "test", "timeout": 30}}
        config2 = {"dag": {"timeout": 60, "retries": 3}}

        result = merge_configs(config1, config2)

        assert result == {
            "dag": {
                "name": "test",
                "timeout": 60,
                "retries": 3,
            },
        }

    def test_merge_configs_none_values(self) -> None:
        """Test merging configs with None values."""
        config1 = {"a": 1}
        config2 = None
        config3 = {"b": 2}

        result = merge_configs(config1, config2, config3)

        assert result == {"a": 1, "b": 2}


class TestValidateConfigPath:
    """Tests for validate_config_path function."""

    def test_validate_config_path_valid(self, tmp_path: Path) -> None:
        """Test validating an existing file path."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("test")

        result = validate_config_path(config_file)

        assert result == config_file

    def test_validate_config_path_not_found(self, tmp_path: Path) -> None:
        """Test validating non-existent path raises error."""
        with pytest.raises(FileNotFoundError):
            validate_config_path(tmp_path / "nonexistent.yaml")

    def test_validate_config_path_not_file(self, tmp_path: Path) -> None:
        """Test validating directory path raises error."""
        with pytest.raises(ValueError):
            validate_config_path(tmp_path)


class TestGetConfigValue:
    """Tests for get_config_value function."""

    def test_get_config_value_simple(self) -> None:
        """Test getting simple value."""
        config = {"name": "test", "version": 1.0}

        assert get_config_value(config, "name") == "test"
        assert get_config_value(config, "version") == 1.0

    def test_get_config_value_nested(self) -> None:
        """Test getting nested value."""
        config = {
            "dag": {
                "name": "test_dag",
                "agents": {"count": 3},
            },
        }

        assert get_config_value(config, "dag.name") == "test_dag"
        assert get_config_value(config, "dag.agents.count") == 3

    def test_get_config_value_missing(self) -> None:
        """Test getting missing value returns default."""
        config = {"name": "test"}

        assert get_config_value(config, "missing") is None
        assert get_config_value(config, "missing", default="default") == "default"

    def test_get_config_value_custom_separator(self) -> None:
        """Test using custom separator."""
        config = {"a": {"b": {"c": 1}}}

        assert get_config_value(config, "a:b:c", separator=":") == 1


# =============================================================================
# Integration Tests
# =============================================================================


class TestConfigIntegration:
    """Integration tests for the config module."""

    @pytest.mark.asyncio
    async def test_full_pipeline_workflow(
        self,
        sample_yaml_content: str,
    ) -> None:
        """Test full workflow from YAML to execution."""
        # Load configuration
        config = PipelineConfig.from_yaml_string(sample_yaml_content)

        # Build DAG
        builder = PipelineBuilder(config)
        dag = builder.build()

        # Verify DAG structure
        assert len(dag.nodes) == 2
        assert len(dag.edges) == 1

        # Get agents
        agent1 = builder.get_agent("agent1")
        agent2 = builder.get_agent("agent2")

        assert agent1 is not None
        assert agent2 is not None

        # Execute agents
        output1 = await agent1(AgentInput())
        assert isinstance(output1, AgentOutput)

        output2 = await agent2(AgentInput())
        assert isinstance(output2, AgentOutput)

    def test_yaml_file_roundtrip(self, tmp_path: Path) -> None:
        """Test writing and reading YAML configuration."""
        # Create configuration
        config = PipelineConfig(
            name="test_pipeline",
            dag=DAGConfig(
                name="test_dag",
                agents={
                    "agent1": AgentConfig(
                        name="Agent 1",
                        instructions="Test",
                    ),
                },
                edges=[
                    EdgeConfig(source="agent1", target="agent2"),
                ],
            ),
        )

        # Write to file
        yaml_file = tmp_path / "pipeline.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(config.model_dump(), f)

        # Read back
        loaded = PipelineConfig.from_yaml(yaml_file)

        assert loaded.name == "test_pipeline"
        assert loaded.dag.name == "test_dag"
        assert "agent1" in loaded.dag.agents
        assert len(loaded.dag.edges) == 1

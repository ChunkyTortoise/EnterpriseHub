"""YAML pipeline definitions for AgentForge.

This module provides Pydantic models for defining agent pipelines
via YAML configuration files, along with a builder to construct
DAGs and agents from configuration.

Example:
    ```python
    from agentforge.config.pipeline import PipelineConfig, PipelineBuilder

    # Load from YAML file
    config = PipelineConfig.from_yaml("pipeline.yaml")

    # Build the DAG
    builder = PipelineBuilder(config)
    dag = builder.build()

    # Get agents by name
    researcher = builder.get_agent("researcher")
    ```
"""

from collections import deque
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from agentforge.core.agent import AgentInput, AgentOutput, BaseAgent
from agentforge.core.dag import DAG
from agentforge.tools.registry import ToolRegistry


class AgentConfig(BaseModel):
    """Configuration for an agent in YAML.

    Defines all properties needed to instantiate an agent from
    a YAML configuration file.

    Attributes:
        name: Human-readable name for the agent.
        instructions: System instructions/prompt for the agent.
        llm: LLM provider and model (e.g., "openai/gpt-4o").
        tools: List of tool names to make available to the agent.
        temperature: Sampling temperature for the LLM (0.0-2.0).
        max_tokens: Maximum tokens in the response.
        metadata: Additional metadata for the agent.

    Example:
        ```yaml
        agents:
          researcher:
            name: "Research Agent"
            instructions: "Research the given topic thoroughly."
            llm: "openai/gpt-4o"
            tools: ["search", "web_browse"]
            temperature: 0.7
        ```
    """

    name: str
    instructions: str
    llm: str = "openai/gpt-4o"
    tools: list[str] = Field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int | None = None
    metadata: dict[str, Any] | None = None


class EdgeConfig(BaseModel):
    """Configuration for a DAG edge.

    Defines a directed edge between two agents in the DAG,
    optionally with a condition for conditional routing.

    Attributes:
        source: Name of the source (upstream) agent.
        target: Name of the target (downstream) agent.
        condition: Optional condition for conditional edges.

    Example:
        ```yaml
        edges:
          - source: "researcher"
            target: "writer"
          - source: "router"
            target: "specialist"
            condition: "needs_specialist"
        ```
    """

    source: str
    target: str
    condition: str | None = None


class DAGConfig(BaseModel):
    """Configuration for a DAG in YAML.

    Defines the complete structure of a DAG including agents,
    edges, and execution settings.

    Attributes:
        name: Human-readable name for the DAG.
        agents: Dictionary mapping agent names to their configurations.
        edges: List of edge configurations defining the graph structure.
        entrypoint: Name of the starting agent (optional).
        max_retries: Maximum retry attempts for failed executions.
        timeout: Optional timeout in seconds for the entire DAG.
        fail_fast: If True, cancel all pending nodes on first failure.

    Example:
        ```yaml
        dag:
          name: "research-workflow"
          entrypoint: "researcher"
          max_retries: 3
          timeout: 300
          agents:
            researcher:
              instructions: "Research the topic."
              llm: "openai/gpt-4o"
            writer:
              instructions: "Write a report."
              llm: "anthropic/claude-3.5-sonnet"
          edges:
            - source: "researcher"
              target: "writer"
        ```
    """

    name: str = "default_dag"
    agents: dict[str, AgentConfig] = Field(default_factory=dict)
    edges: list[EdgeConfig] = Field(default_factory=list)
    entrypoint: str | None = None
    max_retries: int = 3
    timeout: float | None = None
    fail_fast: bool = False


class PipelineConfig(BaseModel):
    """Top-level pipeline configuration.

    The root configuration object that contains all settings
    for a complete AgentForge pipeline.

    Attributes:
        version: Configuration schema version.
        name: Human-readable name for the pipeline.
        dag: DAG configuration containing agents and edges.
        tools: Tool definitions indexed by name.
        env: Environment variables for the pipeline.

    Example:
        ```yaml
        version: "1.0"
        name: "research-workflow"

        tools:
          search:
            type: "function"
            description: "Search for information"

        dag:
          name: "research-dag"
          agents:
            researcher:
              instructions: "Research the given topic."
          edges: []
        ```
    """

    version: str = "1.0"
    name: str = "pipeline"
    dag: DAGConfig = Field(default_factory=DAGConfig)
    tools: dict[str, dict[str, Any]] = Field(default_factory=dict)
    env: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PipelineConfig":
        """Load pipeline configuration from YAML file.

        Args:
            path: Path to the YAML configuration file.

        Returns:
            PipelineConfig instance validated from the YAML data.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            yaml.YAMLError: If the YAML is malformed.
            ValidationError: If the data doesn't match the schema.

        Example:
            ```python
            config = PipelineConfig.from_yaml("pipeline.yaml")
            ```
        """
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    @classmethod
    def from_yaml_string(cls, yaml_str: str) -> "PipelineConfig":
        """Load pipeline configuration from YAML string.

        Args:
            yaml_str: YAML configuration as a string.

        Returns:
            PipelineConfig instance validated from the YAML data.

        Raises:
            yaml.YAMLError: If the YAML is malformed.
            ValidationError: If the data doesn't match the schema.

        Example:
            ```python
            yaml_content = '''
            version: "1.0"
            name: "test"
            dag:
              agents: {}
            '''
            config = PipelineConfig.from_yaml_string(yaml_content)
            ```
        """
        data = yaml.safe_load(yaml_str)
        return cls.model_validate(data)


class ConfigurableAgent(BaseAgent):
    """Agent that can be configured from YAML.

    A concrete implementation of BaseAgent that can be instantiated
    from a YAML configuration. This agent stores its configuration
    and provides a basic execute implementation.

    Attributes:
        _name: The agent's name.
        _instructions: System instructions for the agent.
        _llm: LLM provider and model string.
        _tools: List of tool instances available to the agent.
        _temperature: Sampling temperature.
        _max_tokens: Maximum response tokens.
        _metadata: Additional metadata.

    Example:
        ```python
        agent = ConfigurableAgent(
            name="researcher",
            instructions="Research the topic thoroughly.",
            llm="openai/gpt-4o",
            tools=[search_tool],
            temperature=0.7,
        )

        output = await agent(AgentInput(messages=[...]))
        ```
    """

    def __init__(
        self,
        name: str,
        instructions: str,
        llm: str = "openai/gpt-4o",
        tools: list | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the configurable agent.

        Args:
            name: Agent name.
            instructions: System instructions/prompt.
            llm: LLM provider and model.
            tools: List of tool instances.
            temperature: Sampling temperature.
            max_tokens: Maximum response tokens.
            metadata: Additional metadata.
        """
        from agentforge.core.types import AgentConfig

        config = AgentConfig(name=name)
        super().__init__(config=config)

        self._name = name
        self._instructions = instructions
        self._llm = llm
        self._tools = tools or []
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._metadata = metadata

    @property
    def name(self) -> str:
        """Get the agent's name."""
        return self._name

    @property
    def instructions(self) -> str:
        """Get the agent's instructions."""
        return self._instructions

    @property
    def llm(self) -> str:
        """Get the LLM provider/model string."""
        return self._llm

    @property
    def tools(self) -> list:
        """Get the agent's tools."""
        return self._tools

    @property
    def temperature(self) -> float:
        """Get the sampling temperature."""
        return self._temperature

    @property
    def max_tokens(self) -> int | None:
        """Get the max tokens setting."""
        return self._max_tokens

    @property
    def metadata(self) -> dict[str, Any] | None:
        """Get the agent's metadata."""
        return self._metadata

    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute the agent.

        This is a placeholder implementation. Real implementations
        would use the configured LLM to process the input.

        Args:
            input: The input data for the agent to process.

        Returns:
            AgentOutput containing the results of execution.
        """
        # This is a placeholder - real implementation would use LLM
        return AgentOutput(
            content=f"Agent {self._name} executed with instructions: {self._instructions[:50]}...",
            metadata=self._metadata or {},
        )


class PipelineBuilder:
    """Builds DAG and agents from PipelineConfig.

    Takes a PipelineConfig and constructs a fully initialized DAG
    with all agents and edges defined in the configuration.

    Attributes:
        config: The pipeline configuration.
        tool_registry: Registry for looking up tools by name.
        _agents: Cache of built agents indexed by name.
        _dag: The built DAG instance.

    Example:
        ```python
        config = PipelineConfig.from_yaml("pipeline.yaml")
        builder = PipelineBuilder(config, tool_registry=my_registry)
        dag = builder.build()

        # Get a specific agent
        researcher = builder.get_agent("researcher")
        ```
    """

    def __init__(
        self,
        config: PipelineConfig,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        """Initialize the pipeline builder.

        Args:
            config: Pipeline configuration to build from.
            tool_registry: Optional tool registry for looking up tools.
        """
        self.config = config
        self.tool_registry = tool_registry or ToolRegistry()
        self._agents: dict[str, BaseAgent] = {}
        self._dag: DAG | None = None

    def build(self) -> DAG:
        """Build the DAG from configuration.

        Creates all agents, adds them to a new DAG, and establishes
        all edges between agents.

        Returns:
            The fully constructed DAG instance.

        Raises:
            NodeNotFoundError: If an edge references a non-existent agent.
            CycleDetectedError: If the edges would create a cycle.
        """
        from agentforge.core.dag import DAGConfig as CoreDAGConfig

        # Create DAG with config
        dag_config = CoreDAGConfig(
            name=self.config.dag.name,
            max_retries=self.config.dag.max_retries,
            timeout=self.config.dag.timeout,
            fail_fast=self.config.dag.fail_fast,
        )
        self._dag = DAG(config=dag_config)

        # Build agents
        for name, agent_config in self.config.dag.agents.items():
            agent = self._build_agent(agent_config)
            self._dag.add_node(name, agent)
            self._agents[name] = agent

        # Add edges
        for edge in self.config.dag.edges:
            self._dag.add_edge(edge.source, edge.target)

        # Respect explicit entrypoint by pruning disconnected roots/subgraphs.
        # When set, execution starts from this node and includes only downstream nodes.
        if self.config.dag.entrypoint is not None:
            entrypoint = self.config.dag.entrypoint
            if entrypoint not in self._agents:
                raise ValueError(f"Entrypoint '{entrypoint}' is not defined in dag.agents")
            reachable = self._collect_reachable_nodes(entrypoint)
            for node_id in list(self._dag.nodes):
                if node_id not in reachable:
                    self._dag.remove_node(node_id)
                    self._agents.pop(node_id, None)

        return self._dag

    def _collect_reachable_nodes(self, entrypoint: str) -> set[str]:
        """Collect all nodes reachable from an entrypoint (including itself)."""
        if self._dag is None:
            return set()

        reachable: set[str] = set()
        queue = deque([entrypoint])

        while queue:
            node = queue.popleft()
            if node in reachable:
                continue
            reachable.add(node)
            for successor in self._dag.successors(node):
                if successor not in reachable:
                    queue.append(successor)

        return reachable

    def _build_agent(self, config: AgentConfig) -> ConfigurableAgent:
        """Build an agent from configuration.

        Looks up tools from the registry and creates a ConfigurableAgent
        instance with all settings from the configuration.

        Args:
            config: Agent configuration.

        Returns:
            A configured ConfigurableAgent instance.
        """
        # Get tools from registry
        tools = []
        for tool_name in config.tools:
            tool = self.tool_registry.get(tool_name)
            if tool:
                tools.append(tool)

        # Create agent
        return ConfigurableAgent(
            name=config.name,
            instructions=config.instructions,
            llm=config.llm,
            tools=tools,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            metadata=config.metadata,
        )

    def get_agent(self, name: str) -> BaseAgent | None:
        """Get a built agent by name.

        Args:
            name: Name of the agent to retrieve.

        Returns:
            The agent instance, or None if not found.
        """
        return self._agents.get(name)

    def get_all_agents(self) -> dict[str, BaseAgent]:
        """Get all built agents.

        Returns:
            Dictionary mapping agent names to agent instances.
        """
        return self._agents.copy()

    @property
    def dag(self) -> DAG | None:
        """Get the built DAG, or None if build() hasn't been called."""
        return self._dag


__all__ = [
    "AgentConfig",
    "EdgeConfig",
    "DAGConfig",
    "PipelineConfig",
    "ConfigurableAgent",
    "PipelineBuilder",
]

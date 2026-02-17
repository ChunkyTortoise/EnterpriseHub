"""AgentForge - Lightweight multi-agent LLM orchestration framework.

A production-grade Python framework for building multi-agent LLM applications
with zero required dependencies beyond Pydantic for the base install.

Features:
- BaseAgent ABC for agent implementations
- DAG-based workflow orchestration
- Async-first execution engine
- Pluggable LLM providers (LiteLLM, OpenAI-compatible)
- Tool system with automatic schema generation
- MCP (Model Context Protocol) integration
- Memory systems (working, session, persistent, checkpointing)
- Inter-agent communication (message bus, patterns, A2A)
- Observability (tracing, metrics, dashboard)
- CLI for project scaffolding

Example:
    ```python
    from agentforge import BaseAgent, AgentInput, AgentOutput

    class MyAgent(BaseAgent):
        async def execute(self, input: AgentInput) -> AgentOutput:
            return AgentOutput(content="Hello!")

    agent = MyAgent()
    result = await agent(AgentInput(messages=[...]))
    ```

MCP Example:
    ```python
    from agentforge import MCPToolRegistry, MCPConfig

    registry = MCPToolRegistry()
    tools = await registry.register_mcp_server(
        config=MCPConfig(command="python", args=["-m", "my_mcp_server"]),
        prefix="mcp"
    )
    ```
"""

__version__ = "0.2.0"

# Core
from agentforge.comms.a2a import A2AProtocolSupport, AgentCard

# Communications
from agentforge.comms.message import MessageBus, MessageEnvelope
from agentforge.comms.patterns import (
    CommunicationPattern,
    DelegationPattern,
    PubSubPattern,
    RequestResponsePattern,
)

# Config
from agentforge.config import (
    AgentConfig as ConfigAgentConfig,
)
from agentforge.config import (
    ConfigurableAgent,
    EdgeConfig,
    PipelineBuilder,
    PipelineConfig,
    find_config_file,
    get_config_value,
    load_config,
    merge_configs,
    validate_config_path,
)
from agentforge.config import (
    DAGConfig as PipelineDAGConfig,
)
from agentforge.core.agent import (
    Agent,
    AgentExecutionError,
    AgentInput,
    AgentOutput,
    BaseAgent,
)
from agentforge.core.dag import DAG, DAGConfig
from agentforge.core.engine import (
    Engine,
    ExecutionConfig,
    ExecutionEngine,
    ExecutionResult,
)
from agentforge.core.exceptions import (
    AgentForgeError,
    CycleDetectedError,
    DAGValidationError,
    ExecutionError,
    MCPError,
    NodeNotFoundError,
)
from agentforge.core.registry import Registry, registry
from agentforge.core.types import (
    AgentConfig,
    AgentStatus,
    ExecutionContext,
    Message,
    MessageRole,
    Priority,
    ToolCall,
    ToolResult,
)

# Plugin System
from agentforge.ext import (
    AgentForgeContext,
    AgentForgePlugin,
    LoggingPlugin,
    MetricsPlugin,
    PluginLoadError,
    PluginManager,
    PluginMetadata,
    PluginNotFoundError,
    TimingPlugin,
)

# LLM
from agentforge.llm import (
    LiteLLMProvider,
    LLMConfig,
    LLMError,
    LLMProvider,
    LLMResponse,
    LLMUsage,
    OpenAICompatibleProvider,
    get_provider,
)

# Memory
from agentforge.memory.base import MemoryEntry, MemoryProvider, SearchResult
from agentforge.memory.checkpoint import (
    Checkpoint,
    CheckpointStore,
    InMemoryCheckpointStore,
    SQLiteCheckpointStore,
)
from agentforge.memory.persistent import FileMemory, FileMemoryConfig, InMemoryVectorStore
from agentforge.memory.session import SessionMemory, SessionMemoryConfig
from agentforge.memory.working import WorkingMemory
from agentforge.observe.dashboard import (
    ASCIIDashboard,
    Dashboard,
    DashboardConfig,
    StructuredLogger,
    create_dashboard,
)
from agentforge.observe.metrics import (
    CostRecord,
    LatencyStats,
    MetricsCollector,
    TokenUsage,
    get_metrics,
    reset_metrics,
)

# Observability
from agentforge.observe.tracer import (
    OPENTELEMETRY_AVAILABLE,
    AgentTracer,
    TracerConfig,
    TracerNotAvailableError,
    get_tracer,
    reset_tracer,
)

# Tools
from agentforge.tools.base import (
    BaseTool,
    FunctionTool,
    ToolConfig,
    ToolExecutionError,
    ToolMeta,
    ToolSchema,
    tool,
)
from agentforge.tools.function import (
    create_pydantic_model_from_function,
    generate_tool_schema,
    merge_schemas,
    python_type_to_json_schema,
    validate_tool_input,
)

# MCP Integration
from agentforge.tools.mcp import (
    MCPConfig,
    MCPTool,
    MCPToolAdapter,
    MCPToolRegistry,
    discover_mcp_tools,
    register_mcp_tools,
)
from agentforge.tools.registry import (
    ToolNotFoundError,
    ToolRegistry,
    clear_global_registry,
    get_global_registry,
    get_tool,
    register_tool,
    unregister_tool,
)

__all__ = [
    # Version
    "__version__",
    # Core - Agent
    "Agent",
    "BaseAgent",
    "AgentInput",
    "AgentOutput",
    "AgentExecutionError",
    # Core - Types
    "AgentConfig",
    "AgentStatus",
    "ExecutionContext",
    "Message",
    "MessageRole",
    "Priority",
    "ToolCall",
    "ToolResult",
    # Core - DAG
    "DAG",
    "DAGConfig",
    "CycleDetectedError",
    "DAGValidationError",
    "ExecutionError",
    "NodeNotFoundError",
    "AgentForgeError",
    "MCPError",
    # Core - Engine
    "Engine",
    "ExecutionConfig",
    "ExecutionEngine",
    "ExecutionResult",
    # Core - Registry
    "Registry",
    "registry",
    # Tools
    "BaseTool",
    "FunctionTool",
    "ToolMeta",
    "ToolConfig",
    "ToolSchema",
    "ToolExecutionError",
    "ToolNotFoundError",
    "ToolRegistry",
    "tool",
    "generate_tool_schema",
    "create_pydantic_model_from_function",
    "python_type_to_json_schema",
    "validate_tool_input",
    "merge_schemas",
    "register_tool",
    "unregister_tool",
    "get_tool",
    "get_global_registry",
    "clear_global_registry",
    # MCP Integration
    "MCPConfig",
    "MCPTool",
    "MCPToolAdapter",
    "MCPToolRegistry",
    "discover_mcp_tools",
    "register_mcp_tools",
    # Memory
    "MemoryEntry",
    "MemoryProvider",
    "SearchResult",
    "WorkingMemory",
    "SessionMemory",
    "SessionMemoryConfig",
    "FileMemory",
    "FileMemoryConfig",
    "InMemoryVectorStore",
    "Checkpoint",
    "CheckpointStore",
    "InMemoryCheckpointStore",
    "SQLiteCheckpointStore",
    # Communications
    "MessageBus",
    "MessageEnvelope",
    "CommunicationPattern",
    "RequestResponsePattern",
    "DelegationPattern",
    "PubSubPattern",
    "AgentCard",
    "A2AProtocolSupport",
    # Observability
    "AgentTracer",
    "TracerConfig",
    "TracerNotAvailableError",
    "get_tracer",
    "reset_tracer",
    "OPENTELEMETRY_AVAILABLE",
    "TokenUsage",
    "CostRecord",
    "LatencyStats",
    "MetricsCollector",
    "get_metrics",
    "reset_metrics",
    "Dashboard",
    "DashboardConfig",
    "ASCIIDashboard",
    "StructuredLogger",
    "create_dashboard",
    # LLM
    "LLMProvider",
    "LLMConfig",
    "LLMResponse",
    "LLMUsage",
    "LLMError",
    "LiteLLMProvider",
    "OpenAICompatibleProvider",
    "get_provider",
    # Config
    "ConfigAgentConfig",
    "EdgeConfig",
    "PipelineDAGConfig",
    "PipelineConfig",
    "PipelineBuilder",
    "ConfigurableAgent",
    "find_config_file",
    "load_config",
    "merge_configs",
    "validate_config_path",
    "get_config_value",
    # Plugin System
    "AgentForgePlugin",
    "PluginMetadata",
    "AgentForgeContext",
    "PluginManager",
    "PluginLoadError",
    "PluginNotFoundError",
    "LoggingPlugin",
    "MetricsPlugin",
    "TimingPlugin",
]

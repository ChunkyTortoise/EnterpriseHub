"""Configuration module for AgentForge.

This module provides YAML-based configuration for defining agent
pipelines, including DAG structure, agent configurations, and tools.

Example:
    ```python
    from agentforge.config import PipelineConfig, PipelineBuilder

    # Load from YAML file
    config = PipelineConfig.from_yaml("pipeline.yaml")

    # Build the DAG
    builder = PipelineBuilder(config)
    dag = builder.build()
    ```
"""

from agentforge.config.loader import (
    find_config_file,
    get_config_value,
    load_config,
    merge_configs,
    validate_config_path,
)
from agentforge.config.pipeline import (
    AgentConfig,
    ConfigurableAgent,
    DAGConfig,
    EdgeConfig,
    PipelineBuilder,
    PipelineConfig,
)

__all__ = [
    # Pipeline configuration
    "AgentConfig",
    "EdgeConfig",
    "DAGConfig",
    "PipelineConfig",
    "PipelineBuilder",
    "ConfigurableAgent",
    # Configuration loading
    "find_config_file",
    "load_config",
    "merge_configs",
    "validate_config_path",
    "get_config_value",
]

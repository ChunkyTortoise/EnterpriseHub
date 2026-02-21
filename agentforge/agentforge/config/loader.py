"""Configuration loading utilities for AgentForge.

This module provides utilities for finding, loading, and merging
configuration files for AgentForge pipelines.

Example:
    ```python
    from agentforge.config.loader import find_config_file, load_config, merge_configs

    # Find a config file in common locations
    config_path = find_config_file("agentforge")

    # Load configuration
    config = load_config(config_path)

    # Merge multiple configs
    merged = merge_configs(base_config, override_config)
    ```
"""

from pathlib import Path
from typing import Any

import yaml


def find_config_file(
    name: str = "agentforge",
    search_paths: list[str] | None = None,
) -> Path | None:
    """Find a configuration file by searching common locations.

    Searches for configuration files with the given name in the specified
    search paths, trying both .yaml and .yml extensions.

    Args:
        name: Base name of the configuration file (without extension).
        search_paths: List of directories to search. Defaults to
            [".", "./config", "./configs"].

    Returns:
        Path to the first matching configuration file, or None if not found.

    Example:
        ```python
        # Find agentforge.yaml in current directory or config/ folder
        config_path = find_config_file()

        # Find custom config in specific paths
        config_path = find_config_file(
            name="my_pipeline",
            search_paths=["./pipelines", "./configs"]
        )
        ```
    """
    search_paths = search_paths or [".", "./config", "./configs"]
    extensions = [".yaml", ".yml"]

    for path in search_paths:
        for ext in extensions:
            config_path = Path(path) / f"{name}{ext}"
            if config_path.exists():
                return config_path
    return None


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load configuration from file or search for default.

    If no path is provided, searches for a default configuration file
    named "agentforge" in common locations.

    Args:
        path: Path to the configuration file. If None, searches for
            a default configuration file.

    Returns:
        Dictionary containing the configuration data, or an empty
        dictionary if no configuration file is found.

    Raises:
        FileNotFoundError: If a specific path is provided but the file
            doesn't exist.
        yaml.YAMLError: If the YAML file is malformed.

    Example:
        ```python
        # Load from specific path
        config = load_config("./my_pipeline.yaml")

        # Auto-discover configuration
        config = load_config()
        ```
    """
    if path is None:
        found = find_config_file()
        if found is None:
            return {}
        path = found

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)
        return data if data is not None else {}


def merge_configs(*configs: dict[str, Any]) -> dict[str, Any]:
    """Deep merge multiple configuration dictionaries.

    Merges configurations from left to right, with later configurations
    taking precedence. Nested dictionaries are merged recursively,
    while other values are overwritten.

    Args:
        *configs: Configuration dictionaries to merge.

    Returns:
        A new dictionary containing the merged configuration.

    Example:
        ```python
        base = {"dag": {"name": "default", "timeout": 30}}
        override = {"dag": {"timeout": 60, "retries": 3}}

        merged = merge_configs(base, override)
        # Result: {"dag": {"name": "default", "timeout": 60, "retries": 3}}
        ```
    """
    result: dict[str, Any] = {}

    for config in configs:
        if config is None:
            continue

        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_configs(result[key], value)
            else:
                result[key] = value

    return result


def validate_config_path(path: str | Path) -> Path:
    """Validate that a configuration path exists and is a file.

    Args:
        path: Path to validate.

    Returns:
        The validated Path object.

    Raises:
        FileNotFoundError: If the path doesn't exist.
        ValueError: If the path is not a file.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration path does not exist: {path}")

    if not path.is_file():
        raise ValueError(f"Configuration path is not a file: {path}")

    return path


def get_config_value(
    config: dict[str, Any],
    key: str,
    default: Any = None,
    separator: str = ".",
) -> Any:
    """Get a nested configuration value using dot notation.

    Args:
        config: Configuration dictionary.
        key: Dot-separated key path (e.g., "dag.name").
        default: Default value if key is not found.
        separator: Key separator. Defaults to ".".

    Returns:
        The configuration value or default.

    Example:
        ```python
        config = {"dag": {"name": "my_dag", "agents": {"count": 3}}}

        name = get_config_value(config, "dag.name")  # "my_dag"
        count = get_config_value(config, "dag.agents.count")  # 3
        missing = get_config_value(config, "dag.missing", default=0)  # 0
        ```
    """
    keys = key.split(separator)
    value = config

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default

    return value


__all__ = [
    "find_config_file",
    "load_config",
    "merge_configs",
    "validate_config_path",
    "get_config_value",
]

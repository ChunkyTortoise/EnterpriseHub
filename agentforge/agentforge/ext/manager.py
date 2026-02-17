"""Plugin manager for AgentForge.

This module provides the PluginManager class for discovering, loading, and
managing the lifecycle of AgentForge plugins via Python entry points.

Example:
    ```python
    from agentforge.ext import PluginManager, AgentForgeContext

    # Create manager with context
    context = AgentForgeContext()
    manager = PluginManager(context)

    # Discover and load all plugins
    plugins = manager.load_all()

    # Access registered tools
    tool = context.get_tool("my_tool")
    ```
"""

import logging
from importlib.metadata import entry_points
from typing import Any

from agentforge.ext.base import AgentForgeContext, AgentForgePlugin

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """Raised when a plugin fails to load."""

    def __init__(self, plugin_name: str, reason: str) -> None:
        """Initialize the error.

        Args:
            plugin_name: Name of the plugin that failed to load.
            reason: Reason for the failure.
        """
        self.plugin_name = plugin_name
        self.reason = reason
        super().__init__(f"Failed to load plugin '{plugin_name}': {reason}")


class PluginNotFoundError(Exception):
    """Raised when a plugin is not found."""

    def __init__(self, plugin_name: str) -> None:
        """Initialize the error.

        Args:
            plugin_name: Name of the plugin that was not found.
        """
        self.plugin_name = plugin_name
        super().__init__(f"Plugin '{plugin_name}' not found")


class PluginManager:
    """Manages plugin discovery, loading, and lifecycle.

    The PluginManager discovers plugins via Python entry points, loads them,
    and manages their lifecycle through the AgentForgeContext.

    Attributes:
        ENTRY_POINT_GROUP: The entry point group for AgentForge plugins.
        context: The plugin context for registrations.
        _plugins: Dictionary of loaded plugins by name.
        _loaded: Whether plugins have been loaded.
    """

    ENTRY_POINT_GROUP = "agentforge.plugins"

    def __init__(self, context: AgentForgeContext | None = None) -> None:
        """Initialize the plugin manager.

        Args:
            context: Optional plugin context. If not provided, a new one is created.
        """
        self.context = context or AgentForgeContext()
        self._plugins: dict[str, AgentForgePlugin] = {}
        self._loaded: bool = False

    def discover(self) -> dict[str, type[AgentForgePlugin]]:
        """Discover plugins via entry points.

        Scans the Python entry point group "agentforge.plugins" for registered
        plugin classes.

        Returns:
            Dictionary mapping entry point names to plugin classes.

        Example:
            ```python
            manager = PluginManager()
            discovered = manager.discover()
            for name, plugin_class in discovered.items():
                print(f"Found plugin: {name}")
            ```
        """
        discovered: dict[str, type[AgentForgePlugin]] = {}

        try:
            eps = entry_points(group=self.ENTRY_POINT_GROUP)
            for ep in eps:
                try:
                    plugin_class = ep.load()
                    if isinstance(plugin_class, type) and issubclass(
                        plugin_class, AgentForgePlugin
                    ):
                        discovered[ep.name] = plugin_class
                    else:
                        logger.warning(
                            "Skipping plugin entry point '%s': not an AgentForgePlugin subclass",
                            ep.name,
                        )
                except Exception as e:
                    # Log error but continue discovering other plugins
                    logger.warning(
                        "Failed to load plugin entry point '%s': %s",
                        ep.name,
                        e,
                    )
        except Exception:
            # Entry point group doesn't exist or other error
            logger.exception("Failed to discover plugin entry points")

        return discovered

    def load(
        self,
        plugin_class: type[AgentForgePlugin],
        config: dict[str, Any] | None = None,
    ) -> AgentForgePlugin:
        """Load a plugin class.

        Instantiates the plugin class, applies any configuration, and calls
        the on_load method with the context.

        Args:
            plugin_class: The plugin class to load.
            config: Optional configuration dictionary for the plugin.

        Returns:
            The loaded plugin instance.

        Raises:
            PluginLoadError: If the plugin fails to load.

        Example:
            ```python
            manager = PluginManager()
            plugin = manager.load(MyPlugin, config={"setting": "value"})
            ```
        """
        try:
            plugin = plugin_class()
            if config:
                plugin.on_config_change(config)
            plugin.on_load(self.context)
            self._plugins[plugin.metadata.name] = plugin
            return plugin
        except Exception as e:
            raise PluginLoadError(
                plugin_class.__name__,
                str(e),
            ) from e

    def load_all(self, config: dict[str, Any] | None = None) -> dict[str, AgentForgePlugin]:
        """Discover and load all plugins.

        Discovers all plugins via entry points and loads them. This method
        is idempotent - calling it multiple times will only load plugins once.

        Args:
            config: Optional configuration dictionary passed to all plugins.

        Returns:
            Dictionary of loaded plugins by name.

        Example:
            ```python
            manager = PluginManager()
            plugins = manager.load_all()
            print(f"Loaded {len(plugins)} plugins")
            ```
        """
        if self._loaded:
            return self._plugins

        discovered = self.discover()
        for name, plugin_class in discovered.items():
            try:
                self.load(plugin_class, config)
            except PluginLoadError as e:
                logger.warning("Failed to load plugin '%s': %s", name, e.reason)

        self._loaded = True
        return self._plugins

    def unload(self, name: str) -> bool:
        """Unload a plugin by name.

        Calls the plugin's on_unload method and removes it from the registry.

        Args:
            name: Name of the plugin to unload.

        Returns:
            True if the plugin was unloaded, False if it wasn't found.

        Example:
            ```python
            manager = PluginManager()
            manager.load_all()
            if manager.unload("my_plugin"):
                print("Plugin unloaded successfully")
            ```
        """
        if name in self._plugins:
            plugin = self._plugins.pop(name)
            try:
                plugin.on_unload()
            except Exception as e:
                logger.warning("Error during plugin '%s' unload: %s", name, e)
            return True
        return False

    def unload_all(self) -> None:
        """Unload all plugins.

        Calls on_unload for each plugin and clears the registry.

        Example:
            ```python
            manager = PluginManager()
            manager.load_all()
            manager.unload_all()
            ```
        """
        for name in list(self._plugins.keys()):
            self.unload(name)
        self._loaded = False

    def reload(self, name: str, config: dict[str, Any] | None = None) -> AgentForgePlugin:
        """Reload a plugin by name.

        Unloads the plugin if it's loaded, then discovers and loads it again.

        Args:
            name: Name of the plugin to reload.
            config: Optional configuration for the plugin.

        Returns:
            The reloaded plugin instance.

        Raises:
            PluginNotFoundError: If the plugin is not discovered.
            PluginLoadError: If the plugin fails to load.
        """
        # Unload if exists
        self.unload(name)

        # Discover the plugin
        discovered = self.discover()
        if name not in discovered:
            raise PluginNotFoundError(name)

        # Load it
        return self.load(discovered[name], config)

    def get_plugin(self, name: str) -> AgentForgePlugin | None:
        """Get a loaded plugin by name.

        Args:
            name: Name of the plugin to get.

        Returns:
            Plugin instance or None if not found.
        """
        return self._plugins.get(name)

    def list_plugins(self) -> list[str]:
        """List all loaded plugin names.

        Returns:
            List of plugin names.
        """
        return list(self._plugins.keys())

    def get_plugin_metadata(self, name: str) -> dict[str, Any] | None:
        """Get metadata for a loaded plugin.

        Args:
            name: Name of the plugin.

        Returns:
            Metadata dictionary or None if plugin not found.
        """
        plugin = self.get_plugin(name)
        if plugin:
            return plugin.metadata.model_dump()
        return None

    def is_loaded(self) -> bool:
        """Check if plugins have been loaded.

        Returns:
            True if load_all has been called.
        """
        return self._loaded

    def __len__(self) -> int:
        """Return the number of loaded plugins."""
        return len(self._plugins)

    def __contains__(self, name: str) -> bool:
        """Check if a plugin is loaded."""
        return name in self._plugins

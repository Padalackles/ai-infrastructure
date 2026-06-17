"""Registry — MCP service registration and lifecycle management.

ServerManager is the central registry: register, unregister, discover,
start, stop, query tools, aggregate health.
"""

from src.registry.server_manager import ServerManager

__all__ = ["ServerManager"]

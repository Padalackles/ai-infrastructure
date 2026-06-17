"""MCP Hub — Core modules.

Contains the foundational classes that every MCP service depends on:
  - BaseMCPServer — abstract base for all MCP server implementations
  - ServerManager — lifecycle management for registered servers
  - EventBus — in-memory publish/subscribe event system
  - Discovery — auto-discovery of servers in mcp_servers/
"""

from src.core.base_server import BaseMCPServer
from src.core.discovery import Discovery
from src.core.events import EventBus
from src.core.server_manager import ServerManager

__all__ = [
    "BaseMCPServer",
    "Discovery",
    "EventBus",
    "ServerManager",
]

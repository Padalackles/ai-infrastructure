"""Lifecycle — server lifecycle abstractions.

BaseMCPServer defines the lifecycle contract for every MCP service:
  initialize() → lifecycle_start() → lifecycle_stop()

Running state is managed exclusively by lifecycle wrappers.
"""

from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError

__all__ = ["BaseMCPServer", "ToolNotFoundError"]

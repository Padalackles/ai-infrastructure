"""Ombre Brain — MCP (Model Context Protocol) module.

Contains the client, server base class, and registry that together form the
MCP Hub integration layer.
"""

from app.mcp.client import MCPClient
from app.mcp.registry import MCPRegistry
from app.mcp.server import MCPServer

__all__ = [
    "MCPClient",
    "MCPRegistry",
    "MCPServer",
]

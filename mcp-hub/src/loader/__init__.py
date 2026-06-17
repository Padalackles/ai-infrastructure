"""Loader — pluggable MCP server loading strategies.

Discovery scans mcp_servers/ at startup. Loader (ABC) defines the
loading protocol. PythonLoader is the current implementation.
Future: DockerLoader, RemoteLoader.
"""

from src.loader.discovery import Discovery, DiscoveryError, DiscoveryResult
from src.loader.loader import Loader, PythonLoader

__all__ = [
    "Discovery",
    "DiscoveryError",
    "DiscoveryResult",
    "Loader",
    "PythonLoader",
]

"""Router — request dispatch layer.

The Router maps JSON-RPC methods to handlers through the Runtime layer.
It is completely generic — no server-specific logic.

Architecture:
    transport/server.py  →  router  →  handlers  →  runtime  →  registry

Current implementation: src/transport/router.py (Router class).
This package provides the interface and re-exports.
"""

from src.transport.router import Router

__all__ = ["Router"]

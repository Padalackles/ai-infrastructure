"""MCP Servers — auto-discovery namespace.

Convention (fixed):
    mcp_servers/
        ombre/
            manifest.yaml      ← declarative: name, version, class
            server.py          ← implementation: BaseMCPServer subclass
        ntfy/
            manifest.yaml
            server.py
        ...

Discovery scans */manifest.yaml first.
If no manifest — falls back to scanning server.py for a BaseMCPServer subclass.

No manual registration is required. Just add a subdirectory with
manifest.yaml + server.py — zero Hub Core changes.
"""

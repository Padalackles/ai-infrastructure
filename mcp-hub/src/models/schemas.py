"""Shared data models — dataclasses for Hub state and service metadata.

No business logic. Used by registry, loader, runtime, and API modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ServiceInfo:
    """Metadata for a registered MCP service."""

    name: str
    version: str = "0.1.0"
    running: bool = False
    failed: bool = False
    tools: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "running": self.running,
            "failed": self.failed,
        }


@dataclass
class PluginManifest:
    """Parsed manifest.yaml for an MCP server."""

    name: str
    version: str = "0.1.0"
    class_name: str = ""
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginManifest":
        return cls(
            name=data.get("name", ""),
            version=data.get("version", "0.1.0"),
            class_name=data.get("class", ""),
            enabled=data.get("enabled", True),
        )


@dataclass
class HubState:
    """Snapshot of the Hub's current runtime state."""

    version: str = "0.1.0"
    runtime: str = "MCP Hub"
    total_servers: int = 0
    running_servers: int = 0
    failed_servers: int = 0
    failed_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "runtime": self.runtime,
            "total_servers": self.total_servers,
            "running_servers": self.running_servers,
            "failed_servers": self.failed_servers,
            "failed_names": self.failed_names,
        }


@dataclass
class RuntimeContext:
    """Context passed through the request pipeline.

    Carries references to all core services needed by handlers.
    """

    config: dict[str, Any] = field(default_factory=dict)
    registry: Any = None   # ServerManager (avoid circular import)
    event_bus: Any = None  # EventBus
    router: Any = None     # Router

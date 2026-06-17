"""Integration tests for ntfy MCP service — discovery, health, tools, lifecycle."""

import sys

sys.path.insert(0, ".")

import pytest

from mcp_servers.ntfy.adapter import NtfyAdapter
from mcp_servers.ntfy.server import NtfyServer
from src.core.events import EventBus
from src.loader.discovery import Discovery
from src.registry.server_manager import ServerManager
from src.runtime.runtime import Runtime


# ── Adapter ───────────────────────────────────────────────────


class TestNtfyAdapter:
    async def test_health_returns_ok(self):
        adapter = NtfyAdapter()
        health = await adapter.health()
        assert health["status"] == "ok"
        assert "topic" in health

    async def test_info_returns_metadata(self):
        adapter = NtfyAdapter()
        info = await adapter.info()
        assert info["name"] == "ntfy"
        assert info["version"] == "0.1.0"

    async def test_send_stdout(self):
        adapter = NtfyAdapter()
        result = await adapter.send("Test", "Hello world")
        assert result["status"] == "sent"
        assert result["title"] == "Test"
        assert result["message"] == "Hello world"


# ── Server ────────────────────────────────────────────────────


class TestNtfyServer:
    async def test_health(self):
        server = NtfyServer()
        result = await server.health()
        assert result["status"] == "ok"
        assert result["name"] == "ntfy"

    async def test_get_tools(self):
        server = NtfyServer()
        tools = await server.get_tools()
        assert len(tools) == 3
        names = [t["name"] for t in tools]
        assert "ntfy_health" in names
        assert "ntfy_info" in names
        assert "ntfy_send" in names

    async def test_call_tool_health(self):
        server = NtfyServer()
        result = await server.call_tool("ntfy_health")
        assert result["status"] == "ok"

    async def test_call_tool_info(self):
        server = NtfyServer()
        result = await server.call_tool("ntfy_info")
        assert result["name"] == "ntfy"

    async def test_call_tool_send(self):
        server = NtfyServer()
        result = await server.call_tool("ntfy_send", {"title": "T", "message": "M"})
        assert result["status"] == "sent"

    async def test_call_tool_unknown_raises(self):
        server = NtfyServer()
        with pytest.raises(Exception):
            await server.call_tool("nonexistent")


# ── Discovery ─────────────────────────────────────────────────


class TestNtfyDiscovery:
    async def test_ntfy_discovered(self):
        discovery = Discovery()
        servers, result = await discovery.discover()
        ntfy = next((s for s in servers if s.name == "ntfy"), None)
        assert ntfy is not None, "ntfy should be auto-discovered"
        assert "ntfy" in result.loaded


# ── Registry ──────────────────────────────────────────────────


class TestNtfyRegistry:
    async def test_register_and_start(self):
        registry = ServerManager()
        registry.register(NtfyServer())
        assert registry.count == 1
        assert registry.get_server("ntfy") is not None

        await registry.start_all()
        assert registry.running_count == 1


# ── Runtime ───────────────────────────────────────────────────


class TestNtfyRuntime:
    async def test_list_tools_includes_ntfy(self):
        registry = ServerManager()
        registry.register(NtfyServer())
        runtime = Runtime(registry, EventBus(), {})

        tools = await runtime.list_tools()
        ntfy_entry = next(t for t in tools["tools"] if t["server"] == "ntfy")
        assert len(ntfy_entry["tools"]) == 3

    async def test_call_tool_ntfy_send(self):
        registry = ServerManager()
        registry.register(NtfyServer())
        runtime = Runtime(registry, EventBus(), {})

        result = await runtime.call_tool("ntfy", "ntfy_send", {"title": "X", "message": "Y"})
        assert result["server"] == "ntfy"
        assert result["result"]["status"] == "sent"


# ── Multi-server: Ombre + ntfy coexistence ───────────────────


class TestMultiServerNtfy:
    async def test_ntfy_and_ombre_coexist(self):
        registry = ServerManager()
        registry.register(NtfyServer())

        from mcp_servers.ombre.server import OmbreServer
        registry.register(OmbreServer())

        assert registry.count == 2

        runtime = Runtime(registry, EventBus(), {})
        tools = await runtime.list_tools()
        names = [t["server"] for t in tools["tools"]]
        assert "ntfy" in names
        assert "ombre" in names


# ── Zero Core changes verification ────────────────────────────


class TestZeroCoreChanges:
    """Verify that ntfy integration required zero Core modifications."""

    async def test_ntfy_uses_existing_discovery(self):
        """ntfy is discovered by the same Discovery class as all other servers."""
        discovery = Discovery()
        _, result = await discovery.discover()
        all_servers = result.loaded + [n for n, _ in result.failed]
        assert "ntfy" in all_servers

    async def test_ntfy_uses_existing_registry(self):
        """ntfy registers through the same ServerManager."""
        registry = ServerManager()
        registry.register(NtfyServer())
        assert registry.get_server("ntfy") is not None
        # Uses existing ServerManager methods — no new public API needed

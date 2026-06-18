"""Integration tests for Ombre — discovery, registration, tools via Hub."""

import sys

sys.path.insert(0, ".")

import pytest

from mcp_servers.ombre.adapter import DEFAULT_OMBRE_URL, OmbreMCPClient
from mcp_servers.ombre.server import OmbreServer
from src.core.events import EventBus
from src.loader.discovery import Discovery
from src.registry.server_manager import ServerManager
from src.runtime.runtime import Runtime


# ── RemoteMCPClient integration ─────────────────────────────────


class TestRemoteClientIntegration:
    def test_client_not_connected_by_default(self):
        c = OmbreMCPClient()
        assert c.connected is False
        assert c.state == "DISCONNECTED"

    async def test_health_when_disconnected(self):
        c = OmbreMCPClient()
        h = await c.health()
        assert h["state"] == "DISCONNECTED"
        assert h["endpoint"] == DEFAULT_OMBRE_URL
        assert h["tools_count"] == 0

    async def test_call_tool_when_disconnected(self):
        c = OmbreMCPClient()
        result = await c.call_tool("x", {})
        assert result.get("error") is True

    async def test_disconnect_clears_tools(self):
        c = OmbreMCPClient()
        await c.disconnect()
        assert c.tools == []
        assert c.connected is False


# ── Integration: Discovery → Registration ─────────────────────


class TestOmbreDiscoveryToRegistration:
    async def test_ombre_discovered_and_registered(self):
        registry = ServerManager()
        discovery = Discovery()

        servers, result = await discovery.discover()
        ombre = next((s for s in servers if s.name == "ombre"), None)

        assert ombre is not None, "Ombre should be discovered"
        assert ombre.__class__.__name__ == "OmbreServer"
        assert "ombre" in result.loaded

        registry.register(ombre)
        registered = registry.get_server("ombre")
        assert registered is not None
        assert registered.name == "ombre"


# ── Integration: ServerManager → OmbreServer ──────────────────


class TestOmbreServerManagerIntegration:
    async def test_server_registered(self):
        registry = ServerManager()
        registry.register(OmbreServer())
        assert registry.count == 1
        assert registry.get_server("ombre") is not None


# ── Integration: Runtime → Ombre tools ────────────────────────


class TestOmbreRuntimeIntegration:
    async def test_runtime_list_tools_includes_ombre(self):
        registry = ServerManager()
        registry.register(OmbreServer())
        runtime = Runtime(registry, EventBus(), {})

        tools = await runtime.list_tools()
        ombre_entry = next(
            (t for t in tools["tools"] if t["server"] == "ombre"), None
        )
        assert ombre_entry is not None

    async def test_runtime_server_not_found(self):
        registry = ServerManager()
        runtime = Runtime(registry, EventBus(), {})

        from src.transport.response import JSONRPCError

        with pytest.raises(JSONRPCError) as exc_info:
            await runtime.call_tool("nonexistent", "x", {})
        assert exc_info.value.code == -32001


# ── Integration: DiscoveryResult ───────────────────────────────


class TestOmbreDiscoveryResult:
    async def test_discovery_result_contains_ombre(self):
        discovery = Discovery()
        _, result = await discovery.discover()

        all_entries = result.loaded + [name for name, _ in result.failed]
        assert "ombre" in all_entries, (
            f"Ombre not found. Loaded: {result.loaded}, Failed: {result.failed}"
        )


# ── Integration: Multiple servers with Ombre ──────────────────


class TestMultiServerWithOmbre:
    async def test_ombre_coexists_with_other_servers(self):
        registry = ServerManager()
        registry.register(OmbreServer())

        from mcp_servers.example.server import ExampleServer

        registry.register(ExampleServer(name="example"))
        assert registry.count == 2

        runtime = Runtime(registry, EventBus(), {})
        tools = await runtime.list_tools()
        server_names = [t["server"] for t in tools["tools"]]
        assert "ombre" in server_names
        assert "example" in server_names


# ── Integration: OmbreServer lifecycle ────────────────────────


class TestOmbreLifecycleIntegration:
    async def test_start_stop(self):
        server = OmbreServer()
        await server.start()
        await server.stop()
        assert server._client.connected is False

    async def test_health_when_disconnected(self):
        server = OmbreServer()
        h = await server.health()
        assert h["state"] == "DISCONNECTED"

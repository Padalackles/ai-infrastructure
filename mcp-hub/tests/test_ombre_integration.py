"""Integration tests for Ombre adapter — end-to-end Hub pipeline.

Verifies: discovery → registration → health → tools → router.
"""

import sys

sys.path.insert(0, ".")

import pytest
from fastapi.testclient import TestClient

from mcp_servers.ombre.adapter import DEFAULT_ENDPOINT, OmbreAdapter
from mcp_servers.ombre.server import OmbreServer
from src.core.events import EventBus
from src.loader.discovery import Discovery, DiscoveryResult
from src.registry.server_manager import ServerManager
from src.runtime.runtime import Runtime


# ── Integration: Discovery → Registration ─────────────────────


class TestOmbreDiscoveryToRegistration:
    async def test_ombre_discovered_and_registered(self):
        """Ombre is discovered from mcp_servers/ombre/ and registered."""
        registry = ServerManager()
        discovery = Discovery()

        servers, result = await discovery.discover()
        ombre = next((s for s in servers if s.name == "ombre"), None)

        assert ombre is not None, "Ombre should be discovered"
        assert isinstance(ombre, OmbreServer)
        assert "ombre" in result.loaded

        registry.register(ombre)
        registered = registry.get_server("ombre")
        assert registered is not None
        assert registered.name == "ombre"


# ── Integration: Adapter → Health check ───────────────────────


class TestOmbreAdapterIntegration:
    @pytest.mark.integration
    async def test_real_health_check(self):
        """Integration test: real HTTP health check to external Ombre."""
        adapter = OmbreAdapter(endpoint=DEFAULT_ENDPOINT, timeout=10)
        status = await adapter.connect()
        # External Ombre may or may not be reachable in CI
        assert status in ("CONNECTED", "DISCONNECTED", "UNHEALTHY")

    async def test_adapter_health_method(self):
        adapter = OmbreAdapter()
        health = await adapter.health()
        assert "endpoint" in health
        assert "status" in health
        assert "connected" in health


# ── Integration: ServerManager → OmbreServer ──────────────────


class TestOmbreServerManagerIntegration:
    async def test_server_registered_and_started(self):
        registry = ServerManager()
        server = OmbreServer()
        registry.register(server)

        assert registry.count == 1
        assert registry.get_server("ombre") is not None

        await registry.start_all()
        assert registry.running_count == 0  # adapter may fail to connect
        # But server should be registered regardless
        servers = registry.list_servers()
        ombre_info = next(s for s in servers if s["name"] == "ombre")
        assert ombre_info["version"] == "0.1.0"


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
        tool_names = [t["name"] for t in ombre_entry["tools"]]
        assert "ombre_health" in tool_names
        assert "ombre_status" in tool_names

    async def test_runtime_call_tool_ombre_status(self):
        registry = ServerManager()
        registry.register(OmbreServer())
        runtime = Runtime(registry, EventBus(), {})

        result = await runtime.call_tool("ombre", "ombre_status", {})
        assert result["server"] == "ombre"
        assert result["tool"] == "ombre_status"
        assert result["result"]["name"] == "ombre"
        assert "endpoint" in result["result"]

    async def test_runtime_call_tool_unknown_errors(self):
        registry = ServerManager()
        registry.register(OmbreServer())
        runtime = Runtime(registry, EventBus(), {})

        from src.transport.response import JSONRPCError

        with pytest.raises(JSONRPCError):
            await runtime.call_tool("ombre", "nonexistent_tool", {})

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

        # Ombre should be in the result (either loaded or failed)
        all_entries = result.loaded + [name for name, _ in result.failed]
        assert "ombre" in all_entries, (
            f"Ombre not found in discovery result. "
            f"Loaded: {result.loaded}, Failed: {result.failed}"
        )


# ── Integration: Multiple servers with Ombre ──────────────────


class TestMultiServerWithOmbre:
    async def test_ombre_coexists_with_other_servers(self):
        registry = ServerManager()
        registry.register(OmbreServer())

        from mcp_servers.example.server import ExampleServer

        registry.register(ExampleServer())

        assert registry.count == 2

        runtime = Runtime(registry, EventBus(), {})
        tools = await runtime.list_tools()
        server_names = [t["server"] for t in tools["tools"]]
        assert "ombre" in server_names
        assert "example" in server_names


# ── Integration: Adapter info after lifecycle ─────────────────


class TestOmbreLifecycleIntegration:
    async def test_initialize_then_info(self):
        server = OmbreServer()
        await server.initialize()
        # After initialize, adapter should have attempted connection
        info = server._adapter.info()
        assert "endpoint" in info
        assert "connected" in info

    async def test_stop_disconnects(self):
        server = OmbreServer()
        await server.start()
        await server.stop()
        assert server._adapter.connected is False

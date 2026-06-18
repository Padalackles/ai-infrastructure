"""Tests for Ombre adapter — RemoteMCPClient subclass."""

import pytest

import sys
sys.path.insert(0, ".")  # repo root for mcp_servers imports

from src.core.remote_client import RemoteMCPClient, DISCONNECTED
from mcp_servers.ombre.adapter import (
    DEFAULT_OMBRE_URL,
    OmbreMCPClient,
    CONNECTED,
)
from mcp_servers.ombre.server import OmbreServer


# ── RemoteMCPClient generic tests ───────────────────────────────


class TestRemoteMCPClient:
    def test_init_defaults(self):
        c = RemoteMCPClient("Test", url="http://localhost:8000/mcp")
        assert c.url == "http://localhost:8000/mcp"
        assert c.connected is False
        assert c.state == DISCONNECTED
        assert c.tools == []

    def test_server_info_empty_before_connect(self):
        c = RemoteMCPClient("Test", url="http://localhost:8000/mcp")
        assert c.server_info == {}

    async def test_call_tool_when_disconnected(self):
        c = RemoteMCPClient("Test", url="http://localhost:8000/mcp")
        result = await c.call_tool("x", {})
        assert result.get("error") is True

    async def test_disconnect(self):
        c = RemoteMCPClient("Test", url="http://localhost:8000/mcp")
        await c.disconnect()
        assert c.connected is False
        assert c.tools == []


# ── OmbreMCPClient — Ombre-specific ─────────────────────────────


class TestOmbreMCPClient:
    def test_is_subclass(self):
        assert issubclass(OmbreMCPClient, RemoteMCPClient)

    def test_default_url(self):
        c = OmbreMCPClient()
        assert c.url == DEFAULT_OMBRE_URL
        assert c.connected is False

    def test_custom_url(self):
        c = OmbreMCPClient(url="http://custom:9000/mcp", timeout=5)
        assert c.url == "http://custom:9000/mcp"
        assert c.connected is False

    def test_label_is_ombre(self):
        c = OmbreMCPClient()
        # _label is internal but verified via health()
        assert "Ombre" in str(c.__class__.__name__)


# ── OmbreServer lifecycle ───────────────────────────────────────


class TestOmbreServer:
    def test_name_and_version(self):
        server = OmbreServer(name="custom-ombre", version="2.0")
        assert server.name == "custom-ombre"
        assert server.version == "2.0"

    def test_default_values(self):
        server = OmbreServer()
        assert server.name == "ombre"
        assert server.version == "0.1.0"

    def test_get_tools_empty_before_connect(self):
        server = OmbreServer()
        tools = server._client.tools
        assert tools == []  # not connected yet

    async def test_health_when_disconnected(self):
        server = OmbreServer()
        h = await server.health()
        assert h["state"] == DISCONNECTED
        assert h["tools_count"] == 0

    async def test_call_tool_unknown_raises(self):
        server = OmbreServer()
        result = await server._client.call_tool("nonexistent")
        assert result.get("error") is True

    async def test_start_stop(self):
        server = OmbreServer()
        await server.start()
        await server.stop()
        assert server._client.connected is False

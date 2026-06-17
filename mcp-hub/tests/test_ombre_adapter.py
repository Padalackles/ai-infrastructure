"""Tests for Ombre adapter — initialization, manifest, health, registration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import sys
sys.path.insert(0, ".")  # repo root for mcp_servers imports

from mcp_servers.ombre.adapter import DEFAULT_ENDPOINT, OmbreAdapter  # noqa: E402
from mcp_servers.ombre.server import OmbreServer  # noqa: E402


# ── Adapter initialization ────────────────────────────────────


class TestAdapterInit:
    def test_default_endpoint(self):
        adapter = OmbreAdapter()
        assert adapter.endpoint == DEFAULT_ENDPOINT
        assert adapter.connected is False
        assert adapter.timeout == 5

    def test_custom_endpoint(self):
        adapter = OmbreAdapter(endpoint="http://custom:9000", timeout=10)
        assert adapter.endpoint == "http://custom:9000"
        assert adapter.timeout == 10

    def test_info(self):
        adapter = OmbreAdapter(endpoint="http://x:8000")
        info = adapter.info()
        assert info["endpoint"] == "http://x:8000"
        assert info["connected"] is False


# ── Health check ──────────────────────────────────────────────


class TestHealthCheck:
    @patch("mcp_servers.ombre.adapter.http.client.HTTPConnection")
    async def test_connected(self, mock_conn_class):
        mock_conn = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"status":"ok","buckets":0}'
        mock_conn.getresponse.return_value = mock_resp
        mock_conn_class.return_value = mock_conn

        adapter = OmbreAdapter()
        status = await adapter.connect()
        assert status == "CONNECTED"
        assert adapter.connected is True

    @patch("mcp_servers.ombre.adapter.http.client.HTTPConnection")
    async def test_unhealthy_non_200(self, mock_conn_class):
        mock_conn = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 500
        mock_resp.read.return_value = b"{}"
        mock_conn.getresponse.return_value = mock_resp
        mock_conn_class.return_value = mock_conn

        adapter = OmbreAdapter()
        status = await adapter.connect()
        assert status == "UNHEALTHY"
        assert adapter.connected is False

    @patch("mcp_servers.ombre.adapter.http.client.HTTPConnection")
    async def test_disconnected_network_error(self, mock_conn_class):
        mock_conn_class.side_effect = OSError("Connection refused")

        adapter = OmbreAdapter()
        status = await adapter.connect()
        assert status == "DISCONNECTED"
        assert adapter.connected is False

    async def test_health_method(self):
        adapter = OmbreAdapter()
        adapter.connect = AsyncMock(return_value="CONNECTED")
        adapter._connected = True
        result = await adapter.health()
        assert result["status"] == "CONNECTED"
        assert result["connected"] is True

    async def test_disconnect(self):
        adapter = OmbreAdapter()
        adapter._connected = True
        await adapter.disconnect()
        assert adapter.connected is False


# ── OmbreServer lifecycle ─────────────────────────────────────


class TestOmbreServer:
    @patch("mcp_servers.ombre.adapter.http.client.HTTPConnection")
    async def test_initialize_connected(self, mock_conn_class):
        mock_conn = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"status":"ok"}'
        mock_conn.getresponse.return_value = mock_resp
        mock_conn_class.return_value = mock_conn

        server = OmbreServer()
        await server.initialize()
        assert server._adapter.connected is True

    @patch("mcp_servers.ombre.adapter.http.client.HTTPConnection")
    async def test_initialize_disconnected(self, mock_conn_class):
        mock_conn_class.side_effect = OSError("refused")

        server = OmbreServer()
        await server.initialize()
        assert server._adapter.connected is False

    @patch("mcp_servers.ombre.adapter.http.client.HTTPConnection")
    async def test_health_integration(self, mock_conn_class):
        mock_conn = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"status":"ok"}'
        mock_conn.getresponse.return_value = mock_resp
        mock_conn_class.return_value = mock_conn

        server = OmbreServer()
        await server.initialize()
        result = await server.health()
        assert result["status"] == "CONNECTED"
        assert result["endpoint"] == DEFAULT_ENDPOINT

    async def test_get_tools(self):
        server = OmbreServer()
        tools = await server.get_tools()
        assert len(tools) == 2
        names = [t["name"] for t in tools]
        assert "ombre_health" in names
        assert "ombre_status" in names

    async def test_call_tool_health(self):
        server = OmbreServer()
        server._adapter.connect = AsyncMock(return_value="CONNECTED")
        server._adapter._connected = True
        result = await server.call_tool("ombre_health")
        assert result["status"] == "CONNECTED"

    async def test_call_tool_status(self):
        server = OmbreServer()
        result = await server.call_tool("ombre_status")
        assert result["name"] == "ombre"
        assert "endpoint" in result

    async def test_call_tool_unknown_raises(self):
        server = OmbreServer()
        with pytest.raises(Exception):
            await server.call_tool("nonexistent")

    async def test_start_stop(self):
        server = OmbreServer()
        await server.start()
        await server.stop()
        assert server._adapter.connected is False


# ── Service metadata ──────────────────────────────────────────


class TestServiceMetadata:
    def test_name_and_version(self):
        server = OmbreServer(name="custom-ombre", version="2.0")
        assert server.name == "custom-ombre"
        assert server.version == "2.0"

    def test_default_values(self):
        server = OmbreServer()
        assert server.name == "ombre"
        assert server.version == "0.1.0"

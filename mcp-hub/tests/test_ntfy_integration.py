"""Tests for Notification MCP — notify_send via curl to ntfy.sh."""

import pytest

import sys
sys.path.insert(0, ".")

from mcp_servers.ntfy.adapter import NTFY_SERVER, NTFY_TOPIC, send, health, info
from mcp_servers.ntfy.server import NtfyServer


class TestAdapter:
    async def test_health(self):
        h = await health()
        assert h["status"] == "ok"
        assert "topic" in h
        assert "server" in h

    async def test_info(self):
        i = await info()
        assert i["name"] == "ntfy"
        assert i["server"] == NTFY_SERVER
        assert i["topic"] == NTFY_TOPIC

    async def test_send_empty_message(self):
        result = await send(message="")
        assert result["success"] is False
        assert "error" in result
        assert result["provider"] == "ntfy"

    async def test_send_valid(self):
        result = await send(
            message="Task-012 test from pytest",
            title="Claude Test",
            priority="default",
        )
        # May fail if curl not available, but should have structured response
        assert "success" in result
        assert "timestamp" in result
        assert result["provider"] == "ntfy"


class TestNtfyServer:
    async def test_get_tools(self):
        server = NtfyServer()
        tools = await server.get_tools()
        names = [t["name"] for t in tools]
        assert "notify_send" in names
        assert "ntfy_health" in names
        assert "ntfy_info" in names

    async def test_call_tool_notify_send(self):
        server = NtfyServer()
        result = await server.call_tool("notify_send", {
            "message": "Integration test",
            "title": "Pytest",
        })
        assert "success" in result
        assert result["provider"] == "ntfy"

    async def test_call_tool_health(self):
        server = NtfyServer()
        result = await server.call_tool("ntfy_health")
        assert result["status"] == "ok"

    async def test_call_tool_info(self):
        server = NtfyServer()
        result = await server.call_tool("ntfy_info")
        assert result["name"] == "ntfy"

    async def test_call_tool_unknown_raises(self):
        server = NtfyServer()
        with pytest.raises(Exception):
            await server.call_tool("nonexistent")

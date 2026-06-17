"""Tests for ntfy adapter — health, info, send, error handling."""

import sys
sys.path.insert(0, ".")

from unittest.mock import MagicMock, patch
import pytest
from mcp_servers.ntfy.adapter import NtfyAdapter


class TestAdapterHealth:
    async def test_health_returns_ok(self):
        adapter = NtfyAdapter()
        health = await adapter.health()
        assert health["status"] == "ok"

    async def test_health_includes_topic(self):
        adapter = NtfyAdapter(topic="test-topic")
        health = await adapter.health()
        assert health["topic"] == "test-topic"


class TestAdapterInfo:
    async def test_info_returns_metadata(self):
        adapter = NtfyAdapter()
        info = await adapter.info()
        assert info["name"] == "ntfy"
        assert info["version"] == "0.1.0"

    async def test_info_includes_endpoint(self):
        adapter = NtfyAdapter(base_url="https://custom.example.com")
        info = await adapter.info()
        assert "https://custom.example.com" in info["endpoint"]


class TestAdapterSend:
    async def test_send_stdout(self):
        adapter = NtfyAdapter(base_url="")
        result = await adapter.send("Test Title", "Test Message")
        assert result["status"] == "sent"

    @patch("mcp_servers.ntfy.adapter.urlopen")
    async def test_send_http(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        adapter = NtfyAdapter(base_url="https://ntfy.sh")
        result = await adapter.send("Deploy", "v0.1.0 deployed")
        assert result["status"] == "sent (200)"
        assert result["title"] == "Deploy"

    @patch("mcp_servers.ntfy.adapter.urlopen")
    async def test_send_http_fallback_on_error(self, mock_urlopen):
        mock_urlopen.side_effect = OSError("Connection refused")

        adapter = NtfyAdapter(base_url="https://ntfy.sh")
        result = await adapter.send("Title", "Message")
        assert "sent" in result["status"]

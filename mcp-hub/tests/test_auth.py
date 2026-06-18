"""Tests for Bearer Token authentication on POST /mcp."""

import os
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient


# ── Helpers ────────────────────────────────────────────────────


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Bearer Token Tests ─────────────────────────────────────────


class TestAuthDisabled:
    """When MCP_HUB_AUTH_TOKEN is not set, all requests pass through."""

    def test_health_without_token(self):
        """REST endpoints are always public."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MCP_HUB_AUTH_TOKEN", None)
            from src.main import app
            with TestClient(app) as c:
                resp = c.get("/health")
                assert resp.status_code == 200

    def test_mcp_initialize_without_token(self):
        """POST /mcp works without token when auth is disabled."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MCP_HUB_AUTH_TOKEN", None)
            from src.main import app
            with TestClient(app) as c:
                resp = c.post("/mcp", json={
                    "jsonrpc": "2.0", "id": 1,
                    "method": "initialize", "params": {},
                })
                assert resp.status_code == 200
                assert "result" in resp.json()


class TestAuthEnabled:
    """When MCP_HUB_AUTH_TOKEN is set, token validation is enforced."""

    VALID_TOKEN = "test-secret-token-abc123"

    def _client(self):
        from src.main import app
        return TestClient(app)

    @pytest.fixture(autouse=True)
    def setup_token(self, monkeypatch):
        monkeypatch.setenv("MCP_HUB_AUTH_TOKEN", self.VALID_TOKEN)

    def test_rest_endpoints_always_public(self):
        """GET /health, /status, /tools never require auth."""
        c = self._client()
        assert c.get("/health").status_code == 200
        assert c.get("/status").status_code == 200

    def test_mcp_initialize_with_valid_token(self):
        """Valid Bearer token passes through."""
        c = self._client()
        resp = c.post("/mcp",
                      headers=_auth_header(self.VALID_TOKEN),
                      json={"jsonrpc": "2.0", "id": 1,
                            "method": "initialize", "params": {}})
        assert resp.status_code == 200
        assert "result" in resp.json()

    def test_mcp_missing_auth_header(self):
        """Missing Authorization header returns 401."""
        c = self._client()
        resp = c.post("/mcp",
                      json={"jsonrpc": "2.0", "id": 1,
                            "method": "initialize", "params": {}})
        assert resp.status_code == 401
        assert "Unauthorized" in str(resp.json())

    def test_mcp_malformed_auth_header(self):
        """Wrong prefix (not Bearer) returns 401."""
        c = self._client()
        resp = c.post("/mcp",
                      headers={"Authorization": f"Basic {self.VALID_TOKEN}"},
                      json={"jsonrpc": "2.0", "id": 1,
                            "method": "initialize", "params": {}})
        assert resp.status_code == 401

    def test_mcp_wrong_token(self):
        """Incorrect token returns 401."""
        c = self._client()
        resp = c.post("/mcp",
                      headers=_auth_header("wrong-token"),
                      json={"jsonrpc": "2.0", "id": 1,
                            "method": "initialize", "params": {}})
        assert resp.status_code == 401

    def test_mcp_empty_token(self):
        """Empty Bearer token returns 401."""
        c = self._client()
        resp = c.post("/mcp",
                      headers=_auth_header(""),
                      json={"jsonrpc": "2.0", "id": 1,
                            "method": "initialize", "params": {}})
        assert resp.status_code == 401

    def test_mcp_tools_list_with_valid_token(self):
        """Valid token for tools/list works."""
        c = self._client()
        resp = c.post("/mcp",
                      headers=_auth_header(self.VALID_TOKEN),
                      json={"jsonrpc": "2.0", "id": 2,
                            "method": "tools/list", "params": {}})
        assert resp.status_code == 200
        assert "tools" in resp.json()["result"]

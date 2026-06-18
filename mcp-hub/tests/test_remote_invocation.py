"""Remote MCP invocation tests — verify tool calls via POST /mcp."""

from fastapi.testclient import TestClient

from src.main import app


def _client() -> TestClient:
    return TestClient(app)


def _call_tool(client: TestClient, server: str, tool: str, args: dict | None = None):
    return client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"server": server, "tool": tool, "arguments": args or {}},
    })


class TestOmbreRemoteInvocation:
    def test_ombre_health_succeeds(self):
        with _client() as c:
            resp = _call_tool(c, "ombre", "ombre_health")
            assert resp.status_code == 200
            result = resp.json()["result"]
            assert result["server"] == "ombre"
            assert result["tool"] == "ombre_health"

    def test_ombre_status_succeeds(self):
        with _client() as c:
            resp = _call_tool(c, "ombre", "ombre_status")
            assert resp.status_code == 200
            result = resp.json()["result"]
            assert result["result"]["name"] == "ombre"
            assert "endpoint" in result["result"]


class TestNtfyRemoteInvocation:
    def test_ntfy_health_succeeds(self):
        with _client() as c:
            resp = _call_tool(c, "ntfy", "ntfy_health")
            assert resp.status_code == 200
            result = resp.json()["result"]
            assert result["server"] == "ntfy"
            assert result["result"]["status"] == "ok"

    def test_ntfy_info_succeeds(self):
        with _client() as c:
            resp = _call_tool(c, "ntfy", "ntfy_info")
            assert resp.status_code == 200
            result = resp.json()["result"]
            assert result["result"]["name"] == "ntfy"

    def test_ntfy_send_succeeds(self):
        with _client() as c:
            resp = _call_tool(c, "ntfy", "ntfy_send",
                              {"title": "Remote Test", "message": "Invocation works"})
            assert resp.status_code == 200
            result = resp.json()["result"]
            assert result["result"]["status"].startswith("sent")


class TestErrorHandling:
    def test_unknown_server_returns_error(self):
        with _client() as c:
            resp = _call_tool(c, "nonexistent", "x")
            data = resp.json()
            assert data["error"]["code"] == -32001

    def test_unknown_tool_returns_error(self):
        with _client() as c:
            resp = _call_tool(c, "ntfy", "nonexistent_tool")
            data = resp.json()
            assert data["error"]["code"] == -32002

    def test_missing_params_returns_error(self):
        with _client() as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {},
            })
            data = resp.json()
            assert data["error"]["code"] == -32602


class TestRemoteEndpointAvailability:
    """Verify the /mcp endpoint is reachable and returns valid JSON-RPC."""

    def test_endpoint_accepts_valid_jsonrpc(self):
        with _client() as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["jsonrpc"] == "2.0"

    def test_endpoint_rejects_invalid_jsonrpc(self):
        with _client() as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "1.0", "id": 1, "method": "test"
            })
            data = resp.json()
            assert "error" in data

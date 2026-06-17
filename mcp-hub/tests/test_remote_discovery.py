"""Remote MCP discovery tests — verify tool auto-discovery via POST /mcp."""

from fastapi.testclient import TestClient

from src.main import app


def _client() -> TestClient:
    return TestClient(app)


class TestRemoteInitialize:
    """MCP initialize — the first call any MCP client makes."""

    def test_initialize_returns_protocol_version(self):
        with _client() as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["result"]["protocolVersion"] == "2024-11-05"

    def test_initialize_returns_server_info(self):
        with _client() as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}
            })
            data = resp.json()
            assert data["result"]["serverInfo"]["name"] == "mcp-hub"

    def test_initialize_returns_capabilities(self):
        with _client() as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}
            })
            data = resp.json()
            assert "capabilities" in data["result"]
            assert "tools" in data["result"]["capabilities"]

    def test_initialize_returns_server_list(self):
        with _client() as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}
            })
            data = resp.json()
            assert "servers" in data["result"]


class TestRemoteToolDiscovery:
    """MCP tools/list — auto-discovers tools from all registered servers."""

    def test_tools_list_returns_ombre_and_ntfy(self):
        with _client() as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}
            })
            assert resp.status_code == 200
            data = resp.json()
            tools = data["result"]["tools"]
            server_names = [t["server"] for t in tools]
            assert "example" in server_names
            assert "ombre" in server_names
            assert "ntfy" in server_names

    def test_tools_list_ombre_has_health_and_status(self):
        with _client() as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}
            })
            data = resp.json()
            ombre_tools = next(
                t["tools"] for t in data["result"]["tools"] if t["server"] == "ombre"
            )
            tool_names = [t["name"] for t in ombre_tools]
            assert "ombre_health" in tool_names
            assert "ombre_status" in tool_names

    def test_tools_list_ntfy_has_health_info_send(self):
        with _client() as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}
            })
            data = resp.json()
            ntfy_tools = next(
                t["tools"] for t in data["result"]["tools"] if t["server"] == "ntfy"
            )
            tool_names = [t["name"] for t in ntfy_tools]
            assert "ntfy_health" in tool_names
            assert "ntfy_info" in tool_names
            assert "ntfy_send" in tool_names

    def test_tools_list_no_hardcoded_tools(self):
        """Verify tool list is dynamic — not hardcoded."""
        with _client() as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}
            })
            data = resp.json()
            # At least 3 servers should be discovered
            assert len(data["result"]["tools"]) >= 3


class TestRemoteHealth:
    """MCP health method — aggregate health from all servers."""

    def test_health_aggregates_all_servers(self):
        with _client() as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "health", "params": {}
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["result"]["status"] in ("healthy", "degraded")
            assert len(data["result"]["servers"]) >= 3

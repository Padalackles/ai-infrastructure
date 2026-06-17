"""End-to-end transport tests via HTTP (TestClient)."""

import pytest
from fastapi.testclient import TestClient

from src.core.base_server import BaseMCPServer, ToolNotFoundError
from src.core.server_manager import ServerManager
from src.main import app


# ── Test server ───────────────────────────────────────────────


class _TestServer(BaseMCPServer):
    def __init__(self, name="test-server", version="0.1.0"):
        super().__init__(name=name, version=version)

    async def initialize(self) -> None:
        pass

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def get_tools(self):
        return [
            {"name": "add", "description": "Add two numbers",
             "inputSchema": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}}},
        ]

    async def call_tool(self, tool_name, arguments=None):
        if tool_name == "add":
            a = (arguments or {}).get("a", 0)
            b = (arguments or {}).get("b", 0)
            return {"sum": a + b}
        raise ToolNotFoundError(self.name, tool_name)


# ── Fixture ──────────────────────────────────────────────────


@pytest.fixture
def client():
    """Return a TestClient with a fresh Hub instance."""
    # Store test server on the app so lifespan doesn't try discovery
    app.state._test_server = _TestServer()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_with_server():
    """Return a TestClient with a pre-registered server via app state manipulation."""
    # Register directly on app.state.server_manager before making requests
    with TestClient(app) as c:
        mgr: ServerManager = app.state.server_manager
        mgr.register(_TestServer())
        yield c


# ── JSON-RPC endpoint tests ──────────────────────────────────


class TestJSONRPCEndpoint:
    """End-to-end tests against POST /mcp."""

    def test_initialize(self):
        with TestClient(app) as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 1
            assert data["result"]["protocolVersion"] == "2024-11-05"

    def test_tools_list(self):
        with TestClient(app) as c:
            mgr: ServerManager = app.state.server_manager
            mgr.register(_TestServer())

            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}
            })
            data = resp.json()
            assert "result" in data
            tools = data["result"]["tools"]
            assert len(tools) == 1
            assert tools[0]["server"] == "test-server"
            assert len(tools[0]["tools"]) == 1
            assert tools[0]["tools"][0]["name"] == "add"

    def test_tools_call(self):
        with TestClient(app) as c:
            mgr: ServerManager = app.state.server_manager
            mgr.register(_TestServer())

            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"server": "test-server", "tool": "add", "arguments": {"a": 3, "b": 4}}
            })
            data = resp.json()
            assert data["result"]["result"]["sum"] == 7

    def test_tools_call_unknown_server(self):
        with TestClient(app) as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"server": "ghost", "tool": "x"}
            })
            data = resp.json()
            assert "error" in data
            assert data["error"]["code"] == -32001

    def test_tools_call_unknown_tool(self):
        with TestClient(app) as c:
            mgr: ServerManager = app.state.server_manager
            mgr.register(_TestServer())

            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"server": "test-server", "tool": "nonexistent"}
            })
            data = resp.json()
            assert data["error"]["code"] == -32002

    def test_health(self):
        with TestClient(app) as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "health", "params": {}
            })
            data = resp.json()
            assert data["result"]["status"] in ("healthy", "ok")

    def test_invalid_method(self):
        with TestClient(app) as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "nonexistent_method", "params": {}
            })
            data = resp.json()
            assert data["error"]["code"] == -32601

    def test_malformed_jsonrpc(self):
        with TestClient(app) as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "1.0", "id": 1, "method": "test"
            })
            data = resp.json()
            assert "error" in data

    def test_parse_error(self):
        with TestClient(app) as c:
            resp = c.post("/mcp", content="not json", headers={"Content-Type": "application/json"})
            data = resp.json()
            assert data["error"]["code"] == -32700

    def test_notification_returns_empty(self):
        with TestClient(app) as c:
            resp = c.post("/mcp", json={
                "jsonrpc": "2.0", "method": "health"
            })
            # Notification — no id, no meaningful body
            assert resp.status_code == 200


# ── REST endpoint tests ──────────────────────────────────────


class TestRESTEndpoints:
    """Existing REST endpoints should still work."""

    def test_health(self):
        with TestClient(app) as c:
            resp = c.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] in ("healthy", "degraded")
            assert "servers" in data
            assert "total_servers" in data
            assert "running_servers" in data
            assert "failed_servers" in data

    def test_status(self):
        with TestClient(app) as c:
            resp = c.get("/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["runtime"] == "MCP Hub"
            assert "servers" in data
            assert "total_servers" in data
            assert "running_servers" in data
            assert "failed_servers" in data
            assert "failed_names" in data

    def test_tools(self):
        with TestClient(app) as c:
            mgr: ServerManager = app.state.server_manager
            mgr.register(_TestServer())

            resp = c.get("/tools")
            assert resp.status_code == 200
            data = resp.json()
            assert "tools" in data

"""Tests for the transport Router — method dispatch + error handling."""

import pytest

from src.core.base_server import BaseMCPServer, ToolNotFoundError
from src.core.server_manager import ServerManager
from src.transport.request import JSONRPCRequest
from src.transport.response import ErrorCode, JSONRPCResponse
from src.transport.router import Router


# ── Test server (in-memory, no discovery) ──────────────────────


class _EchoServer(BaseMCPServer):
    """Test server that exposes echo + ping tools."""

    def __init__(self):
        super().__init__(name="echo", version="0.1.0")

    async def initialize(self) -> None:
        pass

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def get_tools(self) -> list[dict]:
        return [
            {"name": "echo", "description": "Echo back input"},
            {"name": "ping", "description": "Return pong"},
        ]

    async def call_tool(self, tool_name, arguments=None):
        if tool_name == "echo":
            return arguments or {}
        if tool_name == "ping":
            return {"response": "pong"}
        raise ToolNotFoundError(self.name, tool_name)


class _FailingServer(BaseMCPServer):
    """Test server that always fails."""

    def __init__(self):
        super().__init__(name="failing", version="0.1.0")

    async def initialize(self) -> None:
        pass

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def get_tools(self) -> list[dict]:
        raise RuntimeError("boom")


# ── Fixtures ──────────────────────────────────────────────────


@pytest.fixture
def manager():
    mgr = ServerManager()
    return mgr


@pytest.fixture
def router(manager):
    return Router(manager)


@pytest.fixture
def router_with_server(manager):
    mgr.register(_EchoServer())
    return Router(manager)


# ── initialize ────────────────────────────────────────────────


class TestInitialize:
    async def test_initialize_returns_capabilities(self, router):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="initialize")
        resp = await router.route(req)
        assert isinstance(resp, JSONRPCResponse)
        assert resp.result["protocolVersion"] == "2024-11-05"
        assert resp.result["serverInfo"]["name"] == "mcp-hub"
        assert "capabilities" in resp.result
        assert "servers" in resp.result

    async def test_initialize_includes_registered_servers(self, router_with_server):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="initialize")
        resp = await router_with_server.route(req)
        assert len(resp.result["servers"]) == 1
        assert resp.result["servers"][0]["name"] == "echo"


# ── tools/list ────────────────────────────────────────────────


class TestToolsList:
    async def test_empty_when_no_servers(self, router):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/list")
        resp = await router.route(req)
        assert resp.result["tools"] == []

    async def test_aggregates_tools(self, router_with_server):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/list")
        resp = await router_with_server.route(req)
        tools = resp.result["tools"]
        assert len(tools) == 1
        assert tools[0]["server"] == "echo"
        assert len(tools[0]["tools"]) == 2

    async def test_failing_server_reports_error(self, manager):
        manager.register(_FailingServer())
        router = Router(manager)
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/list")
        resp = await router.route(req)
        tools = resp.result["tools"]
        assert len(tools) == 1
        assert tools[0]["server"] == "failing"
        assert "error" in tools[0]


# ── tools/call ────────────────────────────────────────────────


class TestToolsCall:
    async def test_echo(self, router_with_server):
        req = JSONRPCRequest(
            jsonrpc="2.0", id=1, method="tools/call",
            params={"server": "echo", "tool": "echo", "arguments": {"msg": "hello"}},
        )
        resp = await router_with_server.route(req)
        assert resp.result["server"] == "echo"
        assert resp.result["tool"] == "echo"
        assert resp.result["result"] == {"msg": "hello"}

    async def test_ping(self, router_with_server):
        req = JSONRPCRequest(
            jsonrpc="2.0", id=2, method="tools/call",
            params={"server": "echo", "tool": "ping"},
        )
        resp = await router_with_server.route(req)
        assert resp.result["result"] == {"response": "pong"}

    async def test_server_not_found(self, router):
        req = JSONRPCRequest(
            jsonrpc="2.0", id=1, method="tools/call",
            params={"server": "nonexistent", "tool": "x"},
        )
        resp = await router.route(req)
        assert resp.error.code == ErrorCode.SERVER_NOT_FOUND

    async def test_tool_not_found(self, router_with_server):
        req = JSONRPCRequest(
            jsonrpc="2.0", id=1, method="tools/call",
            params={"server": "echo", "tool": "unknown_tool"},
        )
        resp = await router_with_server.route(req)
        assert resp.error.code == ErrorCode.TOOL_NOT_FOUND

    async def test_missing_server_param(self, router):
        req = JSONRPCRequest(
            jsonrpc="2.0", id=1, method="tools/call",
            params={"tool": "x"},
        )
        resp = await router.route(req)
        assert resp.error.code == ErrorCode.INVALID_PARAMS

    async def test_missing_tool_param(self, router):
        req = JSONRPCRequest(
            jsonrpc="2.0", id=1, method="tools/call",
            params={"server": "echo"},
        )
        resp = await router.route(req)
        assert resp.error.code == ErrorCode.INVALID_PARAMS


# ── health ────────────────────────────────────────────────────


class TestHealth:
    async def test_empty(self, router):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="health")
        resp = await router.route(req)
        assert resp.result["status"] == "ok"
        assert resp.result["servers"] == []

    async def test_running_server(self, router_with_server):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="health")
        resp = await router_with_server.route(req)
        assert resp.result["status"] == "ok"
        servers = resp.result["servers"]
        assert len(servers) == 1
        assert servers[0]["name"] == "echo"


# ── Error cases ───────────────────────────────────────────────


class TestErrors:
    async def test_unknown_method(self, router):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="nonexistent")
        resp = await router.route(req)
        assert resp.error.code == ErrorCode.METHOD_NOT_FOUND

    async def test_notification_no_response(self, router):
        req = JSONRPCRequest(jsonrpc="2.0", method="health")
        resp = await router.route(req)
        assert resp.id is None


# ── ToolNotFoundError ─────────────────────────────────────────


class TestToolNotFoundError:
    def test_exception(self):
        exc = ToolNotFoundError("myserver", "mytool")
        assert "myserver" in str(exc)
        assert "mytool" in str(exc)
        assert exc.server_name == "myserver"
        assert exc.tool_name == "mytool"


# ── Generic constraint: no server names hardcoded ─────────────


class TestGenericDispatch:
    """Verify the router never hardcodes server names."""

    async def test_any_server_name_works(self, manager):
        """Demonstrate that any server name is routed generically."""
        srv = _EchoServer()
        srv.name = "arbitrary-name-123"
        manager.register(srv)
        router = Router(manager)

        req = JSONRPCRequest(
            jsonrpc="2.0", id=1, method="tools/call",
            params={"server": "arbitrary-name-123", "tool": "ping"},
        )
        resp = await router.route(req)
        assert resp.result["result"] == {"response": "pong"}

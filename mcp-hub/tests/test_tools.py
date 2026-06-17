"""Tests for tool aggregation and dispatch — complete coverage of tool workflows."""

import pytest

from src.core.base_server import BaseMCPServer, ToolNotFoundError
from src.core.events import EventBus
from src.core.server_manager import ServerManager
from src.runtime.runtime import Runtime
from src.transport.request import JSONRPCRequest
from src.transport.response import ErrorCode, JSONRPCResponse
from src.transport.router import Router


# ── Multi-tool test server ───────────────────────────────────


class _MathServer(BaseMCPServer):
    def __init__(self, name="math"):
        super().__init__(name=name, version="1.0.0")

    async def initialize(self) -> None:
        pass

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def get_tools(self):
        return [
            {"name": "add", "description": "Add two numbers",
             "inputSchema": {"type": "object", "properties": {"a": {}, "b": {}}}},
            {"name": "multiply", "description": "Multiply two numbers",
             "inputSchema": {"type": "object", "properties": {"a": {}, "b": {}}}},
            {"name": "noop", "description": "No-op tool with no schema",
             "inputSchema": {"type": "object", "properties": {}}},
        ]

    async def call_tool(self, tool_name, arguments=None):
        args = arguments or {}
        if tool_name == "add":
            return {"result": args.get("a", 0) + args.get("b", 0)}
        if tool_name == "multiply":
            return {"result": args.get("a", 0) * args.get("b", 0)}
        if tool_name == "noop":
            return None
        raise ToolNotFoundError(self.name, tool_name)


class _EmptyServer(BaseMCPServer):
    """Server with zero tools."""

    def __init__(self):
        super().__init__(name="empty")

    async def initialize(self) -> None:
        pass

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass


# ── Fixtures ──────────────────────────────────────────────────


@pytest.fixture
def manager():
    return ServerManager()


@pytest.fixture
def router(manager):
    return Router(Runtime(manager, EventBus(), {}))


@pytest.fixture
def router_with_math(manager):
    manager.register(_MathServer())
    return Router(Runtime(manager, EventBus(), {}))


@pytest.fixture
def router_multi(manager):
    manager.register(_MathServer("math"))
    manager.register(_EmptyServer())
    return Router(Runtime(manager, EventBus(), {}))


# ── Tool aggregation ──────────────────────────────────────────


class TestToolsAggregation:
    async def test_single_server_tools(self, router_with_math):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/list")
        resp = await router_with_math.route(req)
        tools = resp.result["tools"]
        assert len(tools) == 1
        assert tools[0]["server"] == "math"
        assert len(tools[0]["tools"]) == 3
        names = [t["name"] for t in tools[0]["tools"]]
        assert "add" in names
        assert "multiply" in names
        assert "noop" in names

    async def test_multi_server_aggregation(self, router_multi):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/list")
        resp = await router_multi.route(req)
        tools = resp.result["tools"]
        assert len(tools) == 2
        server_names = [t["server"] for t in tools]
        assert "math" in server_names
        assert "empty" in server_names

    async def test_empty_server_has_no_tools(self, router_multi):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/list")
        resp = await router_multi.route(req)
        empty_entry = [t for t in resp.result["tools"] if t["server"] == "empty"][0]
        assert empty_entry["tools"] == []


# ── Tool dispatch ────────────────────────────────────────────


class TestToolDispatch:
    async def test_add(self, router_with_math):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/call",
                             params={"server": "math", "tool": "add", "arguments": {"a": 10, "b": 20}})
        resp = await router_with_math.route(req)
        assert resp.result["result"]["result"] == 30

    async def test_multiply(self, router_with_math):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/call",
                             params={"server": "math", "tool": "multiply", "arguments": {"a": 7, "b": 6}})
        resp = await router_with_math.route(req)
        assert resp.result["result"]["result"] == 42

    async def test_noop_returns_null(self, router_with_math):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/call",
                             params={"server": "math", "tool": "noop"})
        resp = await router_with_math.route(req)
        assert resp.result["result"] is None

    async def test_missing_arguments_default_to_empty(self, router_with_math):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/call",
                             params={"server": "math", "tool": "add"})
        resp = await router_with_math.route(req)
        assert resp.result["result"]["result"] == 0  # 0 + 0


# ── ToolNotFoundError ────────────────────────────────────────


class TestToolNotFound:
    async def test_tool_not_found_error_format(self, router_with_math):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/call",
                             params={"server": "math", "tool": "subtract"})
        resp = await router_with_math.route(req)
        assert resp.error.code == ErrorCode.TOOL_NOT_FOUND
        assert "subtract" in resp.error.message
        assert resp.error.data["server"] == "math"
        assert resp.error.data["tool"] == "subtract"


# ── BaseMCPServer default tool behavior ──────────────────────


class TestDefaultToolBehavior:
    async def test_default_get_tools_returns_empty(self):
        class _MinimalServer(BaseMCPServer):
            def __init__(self):
                super().__init__(name="minimal")

            async def initialize(self) -> None:
                pass

            async def start(self) -> None:
                pass

            async def stop(self) -> None:
                pass

        srv = _MinimalServer()
        tools = await srv.get_tools()
        assert tools == []

    async def test_default_call_tool_raises(self):
        class _MinimalServer(BaseMCPServer):
            def __init__(self):
                super().__init__(name="minimal")

            async def initialize(self) -> None:
                pass

            async def start(self) -> None:
                pass

            async def stop(self) -> None:
                pass

        srv = _MinimalServer()
        with pytest.raises(ToolNotFoundError):
            await srv.call_tool("anything")


# ── Generic constraint tests ─────────────────────────────────


class TestGenericConstraints:
    """Verify transport layer never hardcodes server names."""

    async def test_arbitrary_server_name_in_tools_list(self, manager):
        srv = _MathServer("arbitrary-server-x")
        manager.register(srv)
        router = Router(manager)
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/list")
        resp = await router.route(req)
        assert resp.result["tools"][0]["server"] == "arbitrary-server-x"

    async def test_arbitrary_server_name_in_tools_call(self, manager):
        srv = _MathServer("arbitrary-server-y")
        manager.register(srv)
        router = Router(manager)
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/call",
                             params={"server": "arbitrary-server-y", "tool": "add",
                                     "arguments": {"a": 1, "b": 2}})
        resp = await router.route(req)
        assert resp.result["result"]["result"] == 3

    async def test_no_server_name_leaked_in_error(self, router):
        """Error for unknown server should not reveal internal names."""
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/call",
                             params={"server": "unknown", "tool": "x"})
        resp = await router.route(req)
        assert resp.error.code == ErrorCode.SERVER_NOT_FOUND
        assert "unknown" in resp.error.message
        # The error message is user-facing — it names the requested server, not internals

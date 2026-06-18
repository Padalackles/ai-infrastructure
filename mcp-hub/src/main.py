"""MCP Hub — FastAPI application entry point.

Startup pipeline:
    Load Configuration
        ↓
    Initialize Registry
        ↓
    Load Services (Discovery)
        ↓
    Register Services
        ↓
    Initialize Runtime
        ↓
    Bind Runtime + Start FastMCP Transport
        ↓
    Start Services
        ↓
    Hub Ready

Start with:
    uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.types import ASGIApp, Receive, Scope, Send

from src.config import load_config
from src.core.events import EventBus
from src.core.hub_state import set_state
from src.core.logging import set_request_id
from src.loader.discovery import Discovery
from src.registry.server_manager import ServerManager
from src.runtime.runtime import Runtime
from src.transport.server import _mcp_asgi, set_runtime, start_mcp, stop_mcp

# ── Logging ─────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mcp-hub")
mcp_logger = logging.getLogger("mcp-hub.transport")

# Enable DEBUG logging for MCP SDK protocol tracing
for _name in ("mcp", "mcp.server", "mcp.server.streamable_http",
              "mcp.server.lowlevel", "mcp.server.fastmcp"):
    logging.getLogger(_name).setLevel(logging.DEBUG)


# ── Lifecycle ───────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown pipeline."""

    # ── 1. Load Configuration ────────────────────────────────────
    logger.info("Starting MCP Hub...")
    config = load_config()
    app.state.config = config
    logger.info("Configuration Loaded")

    # ── 2. Initialize Registry ────────────────────────────────────
    registry = ServerManager()
    app.state.server_manager = registry
    logger.info("Registry Initialized")

    # ── 3. Initialize Event Bus ───────────────────────────────────
    event_bus = EventBus()
    app.state.event_bus = event_bus
    logger.info("Event Bus Ready")

    # ── 4. Load Services (Discovery) ───────────────────────────────
    discovery = Discovery()
    discovered, disc_result = await discovery.discover()
    for server in discovered:
        registry.register(server)
    app.state.discovery_result = disc_result
    logger.info("Services Loaded — %d discovered", len(discovered))

    # ── 5. Initialize Runtime ─────────────────────────────────────
    runtime = Runtime(registry, event_bus, config)
    app.state.runtime = runtime
    logger.info("Runtime Initialized")

    # Share state so MCP service plugins can inspect the Hub
    import time
    set_state(registry, runtime, time.time())

    # ── 6. Bind Runtime + Start FastMCP Transport ─────────────────
    set_runtime(runtime)
    await start_mcp(app.state)
    logger.info("Transport Ready (FastMCP Streamable HTTP)")

    # ── 7. Start Services ─────────────────────────────────────────
    await runtime.start_all()
    logger.info("Services Started — total: %d running: %d failed: %d",
                registry.count, registry.running_count, registry.failed_count)

    # ── Store metadata ────────────────────────────────────────────
    hub = config.get("hub", {})
    app.state.version = hub.get("version", "0.1.0")
    app.state.runtime_name = hub.get("name", "MCP Hub")

    logger.info("MCP Hub Ready")
    yield

    # ── Shutdown ──────────────────────────────────────────────────
    logger.info("Stopping Services...")
    await runtime.stop_all()
    await stop_mcp(app.state)
    logger.info("Exit.")


# ── Application ─────────────────────────────────────────────────

app = FastAPI(
    title="MCP Hub",
    description="Central orchestration layer for MCP services. "
                "Routes requests, manages server lifecycles, "
                "and provides discovery — zero business logic.",
    version="0.1.0",
    lifespan=lifespan,
    allowed_hosts=["*"],
)

from src.api.routes import router as api_router  # noqa: E402

app.include_router(api_router)


# ── Bearer Token check (raw ASGI — no FastAPI Depends) ───────────

_AUTH_HEADER = "Authorization"
_BEARER_PREFIX = "Bearer "

def _get_token() -> str | None:
    token = os.getenv("MCP_HUB_AUTH_TOKEN", "").strip()
    return token if token else None

def _check_auth(scope: Scope) -> tuple[int, str] | None:
    """Return (401, message) if auth fails, None if OK."""
    configured = _get_token()
    if configured is None:
        return None  # auth disabled

    # ASGI/Starlette normalizes header names to lowercase bytes
    headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
    auth = headers.get("authorization", "")
    if not auth.startswith(_BEARER_PREFIX):
        return (401, "Missing or malformed Authorization header. Expected: Bearer <token>")
    token = auth[len(_BEARER_PREFIX):].strip()
    if token != configured:
        return (401, "Invalid Bearer token")
    return None


# ── MCP ASGI Proxy (zero-buffer, pure passthrough) ───────────────

class MCPProxy:
    """ASGI middleware that proxies /mcp requests directly to FastMCP.

    No Response wrapping.  No body buffering.  No collect.
    send() is passed straight through to FastMCP so SSE streaming
    works natively.
    """

    def __init__(self, app: ASGIApp, mcp_app: ASGIApp) -> None:
        self.app = app
        self.mcp_app = mcp_app

    @staticmethod
    def _log_request(scope: Scope) -> dict:
        """Log all HTTP request details. Returns a dict for reuse in auth failure logs."""
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        info = {
            "method": scope.get("method", "?"),
            "path": scope.get("path", "?"),
            "query": scope.get("query_string", b"").decode(),
            "has_auth": "authorization" in headers,
            "auth_prefix": "",
            "content_type": headers.get("content-type", "(none)"),
            "accept": headers.get("accept", "(none)"),
            "user_agent": headers.get("user-agent", "(none)"),
            "content_length": headers.get("content-length", "(none)"),
        }
        # Check Authorization without printing token
        auth_val = headers.get("authorization", "")
        if auth_val.startswith("Bearer "):
            info["auth_prefix"] = f"Bearer {auth_val[7:8]}***[{len(auth_val)-7} chars]"
        elif auth_val:
            info["auth_prefix"] = f"{auth_val[:6]}*** (not Bearer)"
        mcp_logger.debug(
            "MCP ← %s %s%s  UA=%s  Accept=%s  Content-Type=%s  Content-Length=%s  Authorization=%s",
            info["method"], info["path"],
            f"?{info['query']}" if info["query"] else "",
            info["user_agent"], info["accept"], info["content_type"],
            info["content_length"],
            info["auth_prefix"] if info["has_auth"] else "(none)",
        )
        return info

    @staticmethod
    def _log_response(status: int) -> None:
        mcp_logger.debug("MCP → %d", status)

    @staticmethod
    def _log_auth_failure(info: dict, status: int, message: str) -> None:
        mcp_logger.warning(
            "AUTH DENIED → %d  method=%s path=%s  has_auth=%s auth=%s  UA=%s  Content-Length=%s  reason=%s",
            status, info["method"], info["path"],
            info["has_auth"], info["auth_prefix"] or "(none)",
            info["user_agent"], info["content_length"],
            message,
        )

    @staticmethod
    def _dump_request(scope: Scope, body_bytes: bytes) -> None:
        """Temporary verbose debug log — full request details."""
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        mcp_headers = {k: v for k, v in headers.items() if k.startswith("mcp-")}

        mcp_logger.info("===== Incoming Request =====")
        mcp_logger.info("Method:  %s", scope.get("method", "?"))
        mcp_logger.info("Path:    %s", scope.get("path", "?"))
        qs = scope.get("query_string", b"").decode()
        if qs:
            mcp_logger.info("Query:   %s", qs)
        mcp_logger.info("Headers:")
        for key in ("authorization", "accept", "content-type", "user-agent",
                     "content-length", "mcp-session-id", "mcp-protocol-version"):
            val = headers.get(key)
            if val:
                if key == "authorization" and val.startswith("Bearer "):
                    val = f"Bearer {val[7:8]}***[{len(val)-7} chars]"
                mcp_logger.info("  %s: %s", key, val)
        for k, v in sorted(mcp_headers.items()):
            mcp_logger.info("  %s: %s", k, v)
        # JSON-RPC body
        try:
            import json
            body_obj = json.loads(body_bytes)
            mcp_logger.info("Body(JSON):")
            mcp_logger.info("  jsonrpc: %s", body_obj.get("jsonrpc", "?"))
            mcp_logger.info("  id:      %s", body_obj.get("id", "?"))
            mcp_logger.info("  method:  %s", body_obj.get("method", "?"))
            params = body_obj.get("params", {})
            if isinstance(params, dict) and params:
                for pk, pv in params.items():
                    if isinstance(pv, dict):
                        mcp_logger.info("  params.%s: {%s keys}", pk, len(pv))
                    elif isinstance(pv, str) and len(str(pv)) > 80:
                        mcp_logger.info("  params.%s: %s...", pk, str(pv)[:80])
                    else:
                        mcp_logger.info("  params.%s: %s", pk, pv)
            else:
                mcp_logger.info("  params:  %s", params)
        except Exception:
            mcp_logger.info("Body(raw): %s", body_bytes[:500])
        mcp_logger.info("============================")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path != "/mcp":
            await self.app(scope, receive, send)
            return

        # Assign a unique request ID for log correlation
        set_request_id()

        # Read body eagerly for debug logging, then replay via wrapper
        body_chunks: list[bytes] = []
        more = True
        while more:
            msg = await receive()
            body_chunks.append(msg.get("body", b""))
            more = msg.get("more_body", False)
        body_bytes = b"".join(body_chunks)

        # Replay receive for downstream
        _replayed = False

        async def _replay_receive() -> dict:
            nonlocal _replayed
            if _replayed:
                return {"type": "http.request", "body": b"", "more_body": False}
            _replayed = True
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        self._dump_request(scope, body_bytes)
        req_info = self._log_request(scope)

        # Auth check before forwarding
        auth_error = _check_auth(scope)
        if auth_error is not None:
            status, message = auth_error
            self._log_auth_failure(req_info, status, message)
            mcp_logger.info("===== Outgoing Response =====")
            mcp_logger.info("Status: %d", status)
            mcp_logger.info("Response Headers:")
            mcp_logger.info("  content-type: application/json")
            mcp_logger.info("  www-authenticate: Bearer")
            mcp_logger.info("============================")
            body = (
                f'{{"jsonrpc":"2.0","id":null,'
                f'"error":{{"code":-32003,"message":"Unauthorized: {message}"}}}}'
            ).encode()
            await send({
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"www-authenticate", b"Bearer"),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": body,
            })
            return

        # Wrap send to capture response status + headers
        _response_status = 0
        _response_headers: list = []

        async def _send(message: dict) -> None:
            nonlocal _response_status, _response_headers
            if message["type"] == "http.response.start":
                _response_status = message["status"]
                _response_headers = message.get("headers", [])
                self._log_response(_response_status)
                mcp_logger.info("===== Outgoing Response =====")
                mcp_logger.info("Status: %d", _response_status)
                mcp_logger.info("Response Headers:")
                for k, v in _response_headers:
                    key = k.decode() if isinstance(k, bytes) else k
                    val = v.decode() if isinstance(v, bytes) else v
                    mcp_logger.info("  %s: %s", key, val)
                mcp_logger.info("============================")
            elif message["type"] == "http.response.body":
                pass  # don't log body chunks
            await send(message)

        # Rewrite path so FastMCP sees "/" (its internal streamable_http_path)
        scope = dict(scope)
        scope["path"] = "/"
        scope["raw_path"] = b"/"

        await self.mcp_app(scope, _replay_receive, _send)


# Wrap FastAPI with the MCP proxy
app.add_middleware(MCPProxy, mcp_app=_mcp_asgi)

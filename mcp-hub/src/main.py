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

    headers = dict(scope.get("headers", []))
    auth = headers.get(_AUTH_HEADER.encode(), b"").decode()
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
    def _log_request(scope: Scope) -> None:
        method = scope.get("method", "?")
        path = scope.get("path", "?")
        headers = dict(scope.get("headers", []))
        # Mask Authorization token
        auth = headers.get(b"authorization", b"").decode()
        if auth.startswith("Bearer "):
            token = auth[7:]
            auth = f"Bearer {token[:8]}..."
        mcp_logger.debug("MCP ← %s %s  Authorization=%s", method, path, auth or "(none)")

    @staticmethod
    def _log_response(status: int) -> None:
        mcp_logger.debug("MCP → %d", status)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path != "/mcp":
            await self.app(scope, receive, send)
            return

        self._log_request(scope)

        # Auth check before forwarding
        auth_error = _check_auth(scope)
        if auth_error is not None:
            status, message = auth_error
            self._log_response(status)
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

        # Wrap send to capture the response status code
        _status = 0

        async def _send(message: dict) -> None:
            nonlocal _status
            if message["type"] == "http.response.start":
                _status = message["status"]
                self._log_response(_status)
            elif message["type"] == "http.response.body":
                pass  # don't log body chunks
            await send(message)

        # Rewrite path so FastMCP sees "/" (its internal streamable_http_path)
        scope = dict(scope)
        scope["path"] = "/"
        scope["raw_path"] = b"/"

        await self.mcp_app(scope, receive, _send)


# Wrap FastAPI with the MCP proxy
app.add_middleware(MCPProxy, mcp_app=_mcp_asgi)

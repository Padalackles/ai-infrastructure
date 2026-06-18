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
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import Response

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
)

from src.api.routes import router as api_router  # noqa: E402
from src.core.auth import verify_bearer_token  # noqa: E402

app.include_router(api_router)


# ── /mcp Route (passthrough to FastMCP Starlette ASGI app) ──────

@app.api_route("/mcp", methods=["GET", "POST", "DELETE", "OPTIONS", "HEAD", "PUT", "PATCH"])
async def mcp_gateway(
    request: Request,
    _auth: None = Depends(verify_bearer_token),
) -> Response:
    """Forward all /mcp traffic to the FastMCP Streamable HTTP app.

    Rewrites the ASGI scope path from /mcp to / so FastMCP's internal
    routing (streamable_http_path="/") matches.
    """
    scope = dict(request.scope)
    scope["path"] = "/"
    scope["raw_path"] = b"/"

    status_code = 200
    response_headers: list[tuple[bytes, bytes]] = []
    body_chunks: list[bytes] = []

    async def receive() -> dict:
        return {
            "type": "http.request",
            "body": await request.body(),
            "more_body": False,
        }

    async def send(message: dict) -> None:
        nonlocal status_code, response_headers
        if message["type"] == "http.response.start":
            status_code = message["status"]
            response_headers = message.get("headers", [])
        elif message["type"] == "http.response.body":
            body_chunks.append(message.get("body", b""))

    await _mcp_asgi(scope, receive, send)

    plain_headers = {}
    for k, v in response_headers:
        key = k.decode() if isinstance(k, bytes) else k
        val = v.decode() if isinstance(v, bytes) else v
        plain_headers[key] = val

    return Response(
        content=b"".join(body_chunks),
        status_code=status_code,
        headers=plain_headers,
    )

"""MCP Hub — FastAPI application entry point.

Startup pipeline:
    Load Configuration
        ↓
    Initialize Registry
        ↓
    Load Plugins (Discovery)
        ↓
    Register Services
        ↓
    Initialize Runtime
        ↓
    Start Transport
        ↓
    Hub Ready

Start with:
    uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import load_config
from src.core.events import EventBus
from src.loader.discovery import Discovery
from src.registry.server_manager import ServerManager
from src.runtime.runtime import Runtime
from src.transport.router import Router

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

    # ── 4. Load Plugins (Discovery) ───────────────────────────────
    discovery = Discovery()
    discovered, disc_result = await discovery.discover()
    for server in discovered:
        registry.register(server)
    app.state.discovery_result = disc_result
    logger.info("Plugins Loaded — %d discovered", len(discovered))

    # ── 5. Initialize Runtime ─────────────────────────────────────
    runtime = Runtime(registry, event_bus, config)
    app.state.runtime = runtime
    logger.info("Runtime Initialized")

    # ── 6. Start Transport ────────────────────────────────────────
    router = Router(runtime)
    app.state.router = router
    logger.info("Transport Ready")

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
from src.transport.server import router as transport_router  # noqa: E402

app.include_router(api_router)
app.include_router(transport_router)

"""MCP Hub — FastAPI application entry point.

Lifecycle:
    Application
        ↓
    Config
        ↓
    Logger
        ↓
    ServerManager
        ↓
    All Servers
        ↓
    Ready

Start with:
    uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI

from src.core.discovery import Discovery
from src.core.events import EventBus
from src.core.server_manager import ServerManager
from src.transport.router import Router

# ── Constants ───────────────────────────────────────────────────

VERSION = "0.1.0"
RUNTIME_NAME = "MCP Hub"
CONFIG_PATH = os.getenv("MCP_HUB_CONFIG", str(Path(__file__).resolve().parent.parent / "config.yaml"))

# ── Logging ─────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mcp-hub")


# ── Config loader ───────────────────────────────────────────────

def _load_config(path: str) -> dict[str, Any]:
    """Load the YAML configuration file."""
    config_path = Path(path)
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    logger.warning("Config file not found: %s — using defaults", path)
    return {}


# ── Lifecycle ───────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the MCP Hub."""

    # ── Startup ──────────────────────────────────────────────────
    logger.info("Starting MCP Hub...")

    # Load config
    config = _load_config(CONFIG_PATH)
    app.state.config = config
    logger.info("Config Loaded")

    # Logger is already configured above
    logger.info("Logger Ready")

    # Create Server Manager
    server_manager = ServerManager()
    app.state.server_manager = server_manager
    logger.info("Server Manager Ready")

    # Create Event Bus
    event_bus = EventBus()
    app.state.event_bus = event_bus
    logger.info("Event Bus Ready")

    # Create Router (transport layer — uses ServerManager for all dispatch)
    router = Router(server_manager)
    app.state.router = router
    logger.info("Router Ready")

    # Auto-discover servers (isolated — one failure won't block others)
    discovery = Discovery()
    discovered, disc_result = await discovery.discover()
    for server in discovered:
        server_manager.register(server)
    app.state.discovery_result = disc_result

    # Start all registered servers (lifecycle_start manages _running state)
    await server_manager.start_all()

    logger.info("Servers — total: %d running: %d failed: %d",
                server_manager.count, server_manager.running_count, server_manager.failed_count)

    logger.info("HTTP API Ready")
    logger.info("MCP Hub Ready")

    # Store version / runtime metadata
    app.state.version = VERSION
    app.state.runtime_name = RUNTIME_NAME

    yield  # ── Application runs here ──

    # ── Shutdown ─────────────────────────────────────────────────
    logger.info("Stopping Servers...")

    await server_manager.stop_all()

    logger.info("Exit.")


# ── Application ─────────────────────────────────────────────────

app = FastAPI(
    title="MCP Hub",
    description="Central orchestration layer for MCP services. "
                "Routes requests, manages server lifecycles, "
                "and provides discovery — zero business logic.",
    version=VERSION,
    lifespan=lifespan,
)

from src.api.routes import router as api_router  # noqa: E402
from src.transport.server import router as transport_router  # noqa: E402

app.include_router(api_router)
app.include_router(transport_router)

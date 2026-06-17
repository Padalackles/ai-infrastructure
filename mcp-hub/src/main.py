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
import signal
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI

from src.core.discovery import Discovery
from src.core.events import EventBus
from src.core.server_manager import ServerManager

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
    print("Starting MCP Hub...")
    logger.info("Starting MCP Hub...")

    # Load config
    config = _load_config(CONFIG_PATH)
    app.state.config = config
    print("Config Loaded")
    logger.info("Config Loaded")

    # Logger is already configured above
    print("Logger Ready")
    logger.info("Logger Ready")

    # Create Server Manager
    server_manager = ServerManager()
    app.state.server_manager = server_manager
    print("Server Manager Ready")
    logger.info("Server Manager Ready")

    # Create Event Bus
    event_bus = EventBus()
    app.state.event_bus = event_bus
    logger.info("Event Bus Ready")

    # Auto-discover servers
    discovery = Discovery()
    discovered = await discovery.discover()
    for server in discovered:
        server_manager.register(server)

    print(f"{server_manager.count} Servers Loaded")
    logger.info("%d Servers Loaded", server_manager.count)

    # Start all registered servers
    await server_manager.start_all()

    print("HTTP API Ready")
    logger.info("HTTP API Ready")

    print("MCP Hub Ready")
    logger.info("MCP Hub Ready")

    # Store version / runtime metadata
    app.state.version = VERSION
    app.state.runtime_name = RUNTIME_NAME

    yield  # ── Application runs here ──

    # ── Shutdown ─────────────────────────────────────────────────
    print("\nStopping Servers...")
    logger.info("Stopping Servers...")

    await server_manager.stop_all()

    print("Exit.")
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

app.include_router(api_router)

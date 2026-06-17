"""Example MCP Server — minimal implementation to verify the Hub pipeline.

This server does nothing useful. It exists solely to prove that:
  1. Discovery finds it via manifest.yaml
  2. ServerManager registers and starts it
  3. /health and /status report it
  4. Graceful shutdown stops it
"""

import logging

from src.core.base_server import BaseMCPServer

logger = logging.getLogger(__name__)


class ExampleServer(BaseMCPServer):
    """A do-nothing MCP server used to validate the Hub runtime."""

    async def initialize(self) -> None:
        logger.info("ExampleServer: initialize() called")

    async def start(self) -> None:
        logger.info("ExampleServer: start() called")

    async def stop(self) -> None:
        logger.info("ExampleServer: stop() called")

"""Ntfy Adapter — push notification service.

Self-contained: health always returns ok, send_notification logs to stdout.
Optional: HTTP forwarding to ntfy.sh if NTFY_BASE_URL is configured.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

DEFAULT_NTFY_URL = os.getenv("NTFY_BASE_URL", "https://ntfy.sh")
DEFAULT_TOPIC = os.getenv("NTFY_TOPIC", "ai-infrastructure")


class NtfyAdapter:
    """Push notification adapter.

    Forwards notifications to ntfy.sh API by default.
    Falls back to stdout logging if HTTP send fails.
    """

    def __init__(
        self,
        base_url: str | None = None,
        topic: str | None = None,
    ) -> None:
        self._base_url: str = base_url or DEFAULT_NTFY_URL
        self._topic: str = topic or DEFAULT_TOPIC

    # ── Properties ──────────────────────────────────────────────

    @property
    def endpoint(self) -> str:
        return self._base_url

    @property
    def topic(self) -> str:
        return self._topic

    # ── Health ──────────────────────────────────────────────────

    async def health(self) -> dict[str, Any]:
        """Ntfy is always healthy — no external dependency."""
        return {"status": "ok", "endpoint": self.endpoint, "topic": self._topic}

    # ── Service info ────────────────────────────────────────────

    async def info(self) -> dict[str, Any]:
        """Return service metadata."""
        return {
            "name": "ntfy",
            "version": "0.1.0",
            "endpoint": self.endpoint,
            "topic": self._topic,
        }

    # ── Send notification ───────────────────────────────────────

    async def send(self, title: str, message: str) -> dict[str, Any]:
        """Send a push notification.

        If NTFY_BASE_URL is configured, forwards via HTTP to ntfy.sh.
        Otherwise, logs to stdout.
        """
        if self._base_url:
            return await self._send_http(title, message)
        return self._send_stdout(title, message)

    def _send_stdout(self, title: str, message: str) -> dict[str, Any]:
        """Log notification to stdout."""
        logger.info("ntfy notification — title: %s, message: %s", title, message)
        return {
            "method": "stdout",
            "title": title,
            "message": message,
            "status": "sent",
        }

    async def _send_http(self, title: str, message: str) -> dict[str, Any]:
        """Forward notification to ntfy.sh via HTTP."""
        url = f"{self._base_url}/{self._topic}"
        data = json.dumps({"title": title, "message": message}).encode()
        req = Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=5) as resp:
                return {
                    "method": "http",
                    "url": url,
                    "status": f"sent ({resp.status})",
                    "title": title,
                    "message": message,
                }
        except Exception as exc:
            logger.error("ntfy HTTP send failed: %s", exc)
            # Fall back to stdout
            self._send_stdout(title, message)
            return {"method": "stdout", "title": title, "message": message, "status": "sent (http failed, fallback to stdout)"}

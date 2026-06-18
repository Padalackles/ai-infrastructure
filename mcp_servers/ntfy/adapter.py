"""Notification MCP Adapter — sends push notifications via curl to ntfy.sh.

Executes curl on the host system to deliver notifications.  All
configuration is environment-driven: NTFY_SERVER, NTFY_TOPIC.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

NTFY_SERVER = os.getenv("NTFY_SERVER", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "ai-infrastructure")
DEFAULT_TIMEOUT = 10  # seconds


def _build_command(
    title: str,
    message: str,
    priority: str = "default",
    tags: str = "",
) -> list[str]:
    """Build the curl command line for ntfy.sh."""
    cmd = ["curl", "-s", "-X", "POST"]
    if title:
        cmd += ["-H", f"Title: {title}"]
    if priority != "default":
        cmd += ["-H", f"Priority: {priority}"]
    if tags:
        cmd += ["-H", f"Tags: {tags}"]
    cmd += ["-d", message]
    cmd.append(f"{NTFY_SERVER}/{NTFY_TOPIC}")
    return cmd


async def send(
    message: str,
    title: str = "Claude",
    priority: str = "default",
    tags: str = "",
) -> dict:
    """Send a push notification via ntfy.sh using curl.

    Args:
        message:  Notification body (required, non-empty).
        title:    Notification title.
        priority: ntfy priority: default, min, low, high, urgent.
        tags:     Comma-separated tags.

    Returns:
        Structured JSON result.
    """
    # Validate
    if not message or not message.strip():
        return {
            "success": False,
            "error": "message is required and must be non-empty",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "ntfy",
        }
    if not NTFY_TOPIC or NTFY_TOPIC == "ai-infrastructure":
        logger.warning("NTFY_TOPIC not configured — using default 'ai-infrastructure'")

    cmd = _build_command(title, message, priority, tags)
    logger.info("ntfy curl: %s", " ".join(f'"{c}"' if " " in c else c for c in cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        logger.error("ntfy curl timed out after %ds", DEFAULT_TIMEOUT)
        return {
            "success": False,
            "error": f"curl timed out after {DEFAULT_TIMEOUT}s",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "ntfy",
        }
    except FileNotFoundError:
        logger.error("curl not found on system PATH")
        return {
            "success": False,
            "error": "curl executable not found on this system",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "ntfy",
        }
    except Exception as exc:
        logger.exception("ntfy curl unexpected error")
        return {
            "success": False,
            "error": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "ntfy",
        }

    if result.returncode != 0:
        logger.error("ntfy curl failed (rc=%d): %s", result.returncode, result.stderr)
        return {
            "success": False,
            "error": f"curl exited {result.returncode}: {result.stderr.strip()}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "ntfy",
        }

    # Parse ntfy response
    response_body = result.stdout.strip()
    try:
        ntfy_data = json.loads(response_body)
    except json.JSONDecodeError:
        ntfy_data = {"raw": response_body}

    logger.info("ntfy sent successfully — id=%s", ntfy_data.get("id", "?"))

    return {
        "success": True,
        "message": message[:100],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": "ntfy",
        "ntfy_response": ntfy_data,
    }


async def health() -> dict:
    """Return service health status."""
    return {
        "status": "ok",
        "server": NTFY_SERVER,
        "topic": NTFY_TOPIC,
    }


async def info() -> dict:
    """Return service metadata."""
    return {
        "name": "ntfy",
        "version": "0.2.0",
        "server": NTFY_SERVER,
        "topic": NTFY_TOPIC,
    }

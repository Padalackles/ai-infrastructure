"""Activity Gateway — HTTP event ingress for the Activity subsystem.

Receives raw device events, validates them against the unified schema,
auto-populates server-side fields (id, timestamp, version), logs them,
and returns a success response.

Source-agnostic: MacroDroid, Tasker, Apple Shortcuts, Home Assistant, etc.
all use the same endpoint without modification.
"""

from .router import router

__all__ = ["router"]

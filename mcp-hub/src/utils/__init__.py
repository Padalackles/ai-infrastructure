"""Utilities — shared helper functions.

Currently: ID generation, future: logging helpers, validation.
"""

import uuid


def generate_id(prefix: str = "") -> str:
    """Generate a short unique ID, optionally with a prefix."""
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}_{uid}" if prefix else uid

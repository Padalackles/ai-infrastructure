"""Utility helpers."""


def generate_id(prefix: str = "") -> str:
    """Generate a simple unique ID."""
    import uuid

    uid = uuid.uuid4().hex[:12]
    return f"{prefix}_{uid}" if prefix else uid

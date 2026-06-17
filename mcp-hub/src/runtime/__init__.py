"""Runtime — middleware layer between Router and ServerManager.

Currently a thin pass-through. Future responsibilities:
  - authentication / authorization
  - rate limiting
  - retries
  - metrics
  - caching
"""

from src.runtime.runtime import Runtime

__all__ = ["Runtime"]

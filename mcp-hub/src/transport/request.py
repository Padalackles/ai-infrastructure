"""JSON-RPC 2.0 request model.

Spec: https://www.jsonrpc.org/specification
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class JSONRPCRequest(BaseModel):
    """A JSON-RPC 2.0 request.

    Example:
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    """

    jsonrpc: str = Field(default="2.0")
    id: int | str | None = Field(default=None)
    method: str
    params: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_jsonrpc_version(self) -> "JSONRPCRequest":
        if self.jsonrpc != "2.0":
            raise ValueError("jsonrpc must be '2.0'")
        if not isinstance(self.method, str) or not self.method.strip():
            raise ValueError("method must be a non-empty string")
        return self

    @property
    def is_notification(self) -> bool:
        """A request without an id is a notification — no response expected."""
        return self.id is None

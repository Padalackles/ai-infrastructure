"""Router — thin dispatch layer. Routes JSON-RPC methods to handlers.

No business logic. No server references. Dispatch only.
"""

from __future__ import annotations

import logging
import time

from src.runtime.runtime import Runtime
from src.transport.handlers import (
    handle_health,
    handle_initialize,
    handle_tools_call,
    handle_tools_list,
)
from src.transport.request import JSONRPCRequest
from src.transport.response import (
    ErrorCode,
    JSONRPCError,
    JSONRPCErrorResponse,
    JSONRPCResponse,
    build_error,
    build_result,
)

logger = logging.getLogger("transport")

HANDLERS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
    "health": handle_health,
}


class Router:
    """Dispatches JSON-RPC requests to handlers via Runtime."""

    def __init__(self, runtime: Runtime) -> None:
        self._runtime: Runtime = runtime

    async def route(self, request: JSONRPCRequest) -> JSONRPCResponse | JSONRPCErrorResponse:
        t0 = time.perf_counter()
        req_id = request.id
        method = request.method

        logger.info("REQUEST  id=%s method=%s", req_id, method)

        if request.is_notification:
            logger.debug("NOTIFICATION method=%s", method)
            return JSONRPCResponse(id=None, result=None)

        handler = HANDLERS.get(method)
        if handler is None:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.info("RESPONSE id=%s status=error code=%d method=%s elapsed=%.1fms",
                        req_id, ErrorCode.METHOD_NOT_FOUND, method, elapsed_ms)
            return build_error(req_id, ErrorCode.METHOD_NOT_FOUND, f"Method not found: {method}")

        try:
            result = await handler(self._runtime, request.params)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.info("RESPONSE id=%s status=success method=%s elapsed=%.1fms",
                        req_id, method, elapsed_ms)
            return build_result(req_id, result)
        except JSONRPCError as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.info("RESPONSE id=%s status=error code=%d method=%s elapsed=%.1fms",
                        req_id, exc.code, method, elapsed_ms)
            return exc.to_response(req_id)
        except Exception:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.exception("RESPONSE id=%s status=error method=%s elapsed=%.1fms",
                             req_id, method, elapsed_ms)
            return build_error(req_id, ErrorCode.INTERNAL_ERROR, "Internal error")

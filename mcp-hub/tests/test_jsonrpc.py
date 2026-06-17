"""Tests for JSON-RPC 2.0 request/response models and parser."""

import pytest

from src.transport.jsonrpc import build_parse_error, parse_request
from src.transport.request import JSONRPCRequest
from src.transport.response import (
    ErrorCode,
    JSONRPCErrorDetail,
    JSONRPCErrorResponse,
    JSONRPCResponse,
    build_error,
    build_result,
)


class TestJSONRPCRequest:
    """JSONRPCRequest model validation."""

    def test_valid_request(self):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="tools/list", params={})
        assert req.jsonrpc == "2.0"
        assert req.id == 1
        assert req.method == "tools/list"
        assert not req.is_notification

    def test_notification_when_id_is_none(self):
        req = JSONRPCRequest(jsonrpc="2.0", method="ping")
        assert req.is_notification

    def test_default_jsonrpc(self):
        req = JSONRPCRequest(method="test")
        assert req.jsonrpc == "2.0"

    def test_default_params(self):
        req = JSONRPCRequest(jsonrpc="2.0", id=1, method="test")
        assert req.params == {}

    def test_rejects_wrong_jsonrpc_version(self):
        with pytest.raises(ValueError, match="2.0"):
            JSONRPCRequest(jsonrpc="1.0", id=1, method="test")

    def test_rejects_empty_method(self):
        with pytest.raises(ValueError, match="method"):
            JSONRPCRequest(jsonrpc="2.0", id=1, method="")

    def test_id_can_be_string(self):
        req = JSONRPCRequest(jsonrpc="2.0", id="abc", method="test")
        assert req.id == "abc"

    def test_id_can_be_int(self):
        req = JSONRPCRequest(jsonrpc="2.0", id=42, method="test")
        assert req.id == 42


class TestJSONRPCResponse:
    """Response model builders."""

    def test_build_result(self):
        resp = build_result(1, {"status": "ok"})
        assert resp.jsonrpc == "2.0"
        assert resp.id == 1
        assert resp.result == {"status": "ok"}

    def test_build_error(self):
        resp = build_error(1, -32600, "Invalid Request")
        assert resp.jsonrpc == "2.0"
        assert resp.id == 1
        assert resp.error.code == -32600
        assert resp.error.message == "Invalid Request"
        assert resp.error.data is None

    def test_build_error_with_data(self):
        resp = build_error(1, -32001, "Server not found", {"server": "x"})
        assert resp.error.data == {"server": "x"}

    def test_response_serialization(self):
        resp = build_result(1, ["a", "b"])
        d = resp.model_dump(exclude_none=True)
        assert d == {"jsonrpc": "2.0", "id": 1, "result": ["a", "b"]}

    def test_error_response_serialization(self):
        resp = build_error(None, -32700, "Parse error")
        d = resp.model_dump(exclude_none=True)
        assert d["jsonrpc"] == "2.0"
        assert d["error"]["code"] == -32700


class TestErrorCodes:
    """Standard JSON-RPC error codes."""

    def test_parse_error(self):
        assert ErrorCode.PARSE_ERROR == -32700

    def test_method_not_found(self):
        assert ErrorCode.METHOD_NOT_FOUND == -32601

    def test_server_not_found(self):
        assert ErrorCode.SERVER_NOT_FOUND == -32001

    def test_tool_not_found(self):
        assert ErrorCode.TOOL_NOT_FOUND == -32002


class TestParseRequest:
    """Parser validation."""

    def test_valid_parse(self):
        data = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        result = parse_request(data)
        assert isinstance(result, JSONRPCRequest)
        assert result.method == "tools/list"

    def test_not_a_dict_returns_error(self):
        result = parse_request("not a dict")
        assert isinstance(result, JSONRPCErrorResponse)
        assert result.error.code == ErrorCode.INVALID_REQUEST

    def test_missing_jsonrpc(self):
        result = parse_request({"id": 1, "method": "test"})
        assert isinstance(result, JSONRPCErrorResponse)

    def test_wrong_jsonrpc(self):
        result = parse_request({"jsonrpc": "1.0", "id": 1, "method": "test"})
        assert isinstance(result, JSONRPCErrorResponse)

    def test_missing_method(self):
        result = parse_request({"jsonrpc": "2.0", "id": 1})
        assert isinstance(result, JSONRPCErrorResponse)

    def test_empty_method(self):
        result = parse_request({"jsonrpc": "2.0", "id": 1, "method": ""})
        assert isinstance(result, JSONRPCErrorResponse)

    def test_invalid_id_type(self):
        result = parse_request({"jsonrpc": "2.0", "id": [], "method": "test"})
        assert isinstance(result, JSONRPCErrorResponse)

    def test_parse_error(self):
        err = build_parse_error("unexpected token")
        assert err.error.code == ErrorCode.PARSE_ERROR


class TestJSONRPCErrorDetail:
    """Error detail model."""

    def test_error_detail(self):
        detail = JSONRPCErrorDetail(code=-32600, message="Invalid Request")
        assert detail.code == -32600
        assert detail.message == "Invalid Request"
        assert detail.data is None

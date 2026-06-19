"""Ombre MCP Server plugin — remote MCP client bridge.

Schema Slimming (Task-022):
  Tools with >3 inputSchema properties are invisible to Claude Mobile/Code.
  This adapter rewrites complex schemas down to <=3 core properties
  + an "extra_params" escape hatch for advanced users.
"""

from __future__ import annotations

import json, logging
from typing import Any

from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError
from mcp_servers.ombre.adapter import CONNECTED, DISCONNECTED, OmbreMCPClient

logger = logging.getLogger(__name__)

SLIM_SCHEMAS = {
    "breath": {
        "description": "breath (呼吸/浮现记忆) - Surface or search memories. 不传query=自动浮现,传query=关键词+向量语义双通道检索",
        "properties": {
            "query": {"type": "string", "description": "query (搜索词) - search keyword; leave empty to auto-surface. 留空=自动浮现", "default": ""},
            "max_results": {"type": "integer", "description": "max_results (返回数量) - max 1-50 (default 20). 返回记忆条数上限", "default": 20},
            "extra_params": {"type": "string", "description": "extra_params (高级筛选JSON) - optional advanced. e.g. {\"valence\":0.8,\"arousal\":0.5,\"domain\":\"work\",\"max_tokens\":5000}. valence/arousal 0~1, -1=ignore", "default": ""},
        },
        "_defaults": {"query": "", "max_tokens": 10000, "domain": "", "valence": -1, "arousal": -1, "max_results": 20, "importance_min": -1},
    },
    "trace": {
        "description": "trace (追踪/修改记忆) - Modify memory metadata. 修改元数据: resolved=1沉底,pinned=1钉选,delete=True删除",
        "properties": {
            "bucket_id": {"type": "string", "description": "bucket_id (记忆桶ID) - memory bucket ID to modify. 要修改的记忆桶ID"},
            "resolved": {"type": "integer", "description": "resolved (解决/沉底) - 1=resolve/sink, 0=reactivate. 1=标记已解决并沉底", "default": -1},
            "extra_params": {"type": "string", "description": "extra_params (高级参数JSON) - optional. e.g. {\"name\":\"new\",\"domain\":\"work\",\"valence\":0.8,\"importance\":7,\"tags\":\"t1,t2\",\"pinned\":1,\"delete\":true}", "default": ""},
        },
        "required": ["bucket_id"],
        "_defaults": {"name": "", "domain": "", "valence": -1, "arousal": -1, "importance": -1, "tags": "", "resolved": -1, "pinned": -1, "digested": -1, "content": "", "delete": False},
    },
    "hold": {
        "description": "hold (保存/存储记忆) - Store memory with auto-tagging & merging. 存储单条记忆,自动打标+合并+生成embedding",
        "properties": {
            "content": {"type": "string", "description": "content (记忆内容) - the memory content to store. 要存储的记忆正文"},
            "tags": {"type": "string", "description": "tags (标签) - comma-separated. 逗号分隔标签", "default": ""},
            "extra_params": {"type": "string", "description": "extra_params (高级JSON) - optional. e.g. {\"importance\":7,\"pinned\":true,\"feel\":true,\"valence\":0.8}", "default": ""},
        },
        "required": ["content"],
        "_defaults": {"tags": "", "importance": 5, "pinned": False, "feel": False, "source_bucket": "", "valence": -1, "arousal": -1},
    },
}

def _apply_slim(tool):
    name = tool.get("name", "")
    if name not in SLIM_SCHEMAS:
        return tool
    s = SLIM_SCHEMAS[name]
    nt = {"name": name, "description": s["description"], "inputSchema": {"type": "object", "properties": s["properties"]}}
    if "required" in s:
        nt["inputSchema"]["required"] = s["required"]
    return nt

def _expand(tool_name, arguments):
    if tool_name not in SLIM_SCHEMAS:
        return arguments
    s = SLIM_SCHEMAS[tool_name]
    merged = dict(s["_defaults"])
    extra = arguments.pop("extra_params", "") or ""
    if extra:
        try:
            extra_dict = json.loads(extra)
            if isinstance(extra_dict, dict):
                merged.update(extra_dict)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Bad extra_params for %s: %s", tool_name, extra)
    merged.update({k: v for k, v in arguments.items() if v is not None})
    merged.pop("extra_params", None)
    return merged

class OmbreServer(BaseMCPServer):
    def __init__(self, name="ombre", version="0.1.0", endpoint=None):
        super().__init__(name=name, version=version)
        self._client = OmbreMCPClient(url=endpoint)

    async def initialize(self):
        logger.info("Ombre init — %s", self._client.url)
        state = await self._client.connect()
        if state == CONNECTED:
            logger.info("Ombre connected: %s v%s (%d tools)", self._client.server_info.get("name","?"), self._client.server_info.get("version","?"), len(self._client.tools))
        else:
            logger.warning("Ombre unavailable: %s", state)

    async def start(self):
        logger.info("Ombre started (%d tools)", len(self._client.tools) if self._client.connected else 0)

    async def stop(self):
        await self._client.disconnect()
        logger.info("Ombre stopped")

    async def health(self):
        return {"name": self.name, **(await self._client.health())}

    async def get_tools(self):
        raw = self._client.tools
        slimmed = [_apply_slim(t) for t in raw]
        logger.info("Ombre get_tools: %d raw -> %d slimmed", len(raw), len(slimmed))
        for t in slimmed:
            n = len(t.get("inputSchema",{}).get("properties",{}))
            logger.info("  - %s (%d props)", t.get("name","?"), n)
        return slimmed

    async def call_tool(self, tool_name, arguments=None):
        args = dict(arguments or {})
        expanded = _expand(tool_name, args)
        logger.info("Ombre call_tool: %s -> keys=%s", tool_name, list(expanded.keys()))
        result = await self._client.call_tool(tool_name, expanded)
        if isinstance(result, dict) and result.get("error"):
            raise ToolNotFoundError(self.name, tool_name)
        return result
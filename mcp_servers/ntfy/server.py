"""Notification MCP Service — sends push notifications via ntfy.sh.

Schema Slimming (Task-022):
  notify_send reduced from 4 to 3 properties (message, title, extra_params).
"""

from __future__ import annotations

import json, logging
from typing import Any

from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError
from mcp_servers.ntfy.adapter import health, info, send

logger = logging.getLogger(__name__)

class NtfyServer(BaseMCPServer):
    def __init__(self, name="ntfy", version="0.2.0"):
        super().__init__(name=name, version=version)

    async def initialize(self):
        h = await health()
        logger.info("ntfy init — %s/%s", h["server"], h["topic"])

    async def start(self):
        logger.info("ntfy started")

    async def stop(self):
        logger.info("ntfy stopped")

    async def health(self):
        return {"name": self.name, **(await health())}

    async def get_tools(self):
        tools = [
            {
                "name": "notify_send",
                "description": "notify_send (推送通知) - Send push notification via ntfy.sh. 发送推送通知到手机",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "message (通知内容) - Notification body text. 通知正文"},
                        "title": {"type": "string", "description": "title (标题) - Notification title (default: Claude). 通知标题", "default": "Claude"},
                        "extra_params": {"type": "string", "description": "extra_params (高级JSON) - optional. e.g. {\"priority\":\"high\",\"tags\":\"warning\"}. priority: min/low/high/urgent", "default": ""},
                    },
                    "required": ["message"],
                },
            },
            {"name": "ntfy_health", "description": "ntfy_health (服务健康检查) - Check ntfy service health. 检查ntfy服务状态", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "ntfy_info", "description": "ntfy_info (服务信息) - Get ntfy service metadata. 获取ntfy服务信息", "inputSchema": {"type": "object", "properties": {}}},
        ]
        logger.info("Ntfy get_tools: %d tools", len(tools))
        return tools

    async def call_tool(self, tool_name, arguments=None):
        args = dict(arguments or {})
        if tool_name == "notify_send":
            extra = args.pop("extra_params", "") or ""
            if extra:
                try:
                    ed = json.loads(extra)
                    if isinstance(ed, dict):
                        for k, v in ed.items():
                            if k not in args or not args.get(k):
                                args[k] = v
                except (json.JSONDecodeError, TypeError):
                    logger.warning("Bad notify extra_params: %s", extra)
            return await send(message=args.get("message",""), title=args.get("title","Claude"), priority=args.get("priority","default"), tags=args.get("tags",""))
        if tool_name == "ntfy_health":
            return await self.health()
        if tool_name == "ntfy_info":
            return await info()
        raise ToolNotFoundError(self.name, tool_name)
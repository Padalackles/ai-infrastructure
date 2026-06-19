# Task-022: Claude 客户端 tool_search 索引丢失问题排查与修复

**日期:** 2026-06-19
**状态:** ✅ 已部署
**影响范围:** Claude Mobile / Claude Code 用户
**VPS:** 45.76.169.98 (raven-victor.click)

---

## 1. 问题现象

用户在 Claude 手机端和 Claude Code 中使用 `breath`、`trace`、`hold` 等 Ombre Brain 记忆工具时，提示：

> "breath 工具目前无法通过搜索加载"
> "only 5 tools: dream, ntfy_health, ntfy_info, grow, pulse"

Claude Desktop 端所有 9 个 Tool 均正常可用。

---

## 2. 排查过程

### 2.1 第一阶段：VPS Hub 层排查

通过 SSH 登录 VPS，逐层验证：

| 检查项 | 命令/方法 | 结果 |
|--------|----------|------|
| Docker 容器状态 | `docker compose ps` | ai-mcp-hub Up (healthy), ai-caddy Up, ombre-brain Up 2 days |
| Hub 健康检查 | `curl localhost:8080/health` | healthy, 4/4 servers running |
| Hub 工具列表 | `curl localhost:8080/tools` | **9 个 Tool 全部返回**（breath, hold, grow, trace, pulse, dream + 3 ntfy） |
| Hub 日志 | `docker logs ai-mcp-hub` | `OmbreServer.get_tools() — remote returned 6 tools`, breath/trace 均在列 |
| Ombre Brain 直连 | MCP initialize + tools/list | Ombre Brain v1.27.0, 6 tools |
| Hub 源码扫描 | `grep -rn "registerTool\|skip\|hidden\|filter"` | **0 个过滤逻辑** |
| 缓存/index 文件 | `find /app -type f \( -name "*.db" -o -name "*cache*" -o -name "*index*" \)` | **不存在任何缓存文件** |

**结论：VPS 全链路零问题。所有 Tool 完整地从 Ombre Brain → Hub → /tools 端点返回。**

### 2.2 第二阶段：客户端排查

通过 Claude Code 思考链分析（用户提供），发现 `tool_search` 只返回 5 个 Tool：

```json
["dream", "ntfy_health", "ntfy_info", "grow", "pulse"]
```

缺失：`breath`, `hold`, `trace`, `notify_send`

### 2.3 第三阶段：根因定位

对比可用/不可用 Tool 的 inputSchema 属性数量：

| Tool | 属性数 | Claude Mobile/Code |
|------|--------|-------------------|
| dream | 0 | ✅ 可加载 |
| ntfy_health | 0 | ✅ 可加载 |
| ntfy_info | 0 | ✅ 可加载 |
| pulse | 1 | ✅ 可加载 |
| grow | 1 | ✅ 可加载 |
| **notify_send** | **4** | **❌ 不加载** |
| **breath** | **7** | **❌ 不加载** |
| **hold** | **8** | **❌ 不加载** |
| **trace** | **12** | **❌ 不加载** |

**规律确认：Claude 客户端 `tool_search` 索引器对 inputSchema 属性数 >3 的 Tool 存在加载 Bug。**

`tool_search` 是 Claude 客户端内部闭源函数，无法直接查看源码。但从 100% 可复现的规律推断：存在基于属性数量的过滤逻辑，阈值约在 3-4 之间。返回的恰好 5 个 Tool 也暗示可能存在 `Array.slice(0, 5)` 或类似的结果截断。

---

## 3. 修复方案

### 设计原则

1. **不修改 Ombre Brain 源码** — Ombre Brain (P0luz/Ombre-Brain) 是独立项目
2. **只在 Hub 网关层做 Schema 瘦身** — 改 `mcp_servers/{ombre,ntfy}/server.py`
3. **保留完整功能** — 通过 `extra_params` JSON 逃逸舱传递高级参数
4. **双语描述** — 所有 Tool 和参数描述同时包含中英文，确保 `tool_search` 语义匹配

### 3.1 Schema 瘦身

```python
# mcp_servers/ombre/server.py 新增 SLIM_SCHEMAS 字典

SLIM_SCHEMAS = {
    "breath": {
        # 原始 7 属性 → 瘦身 3 属性
        "properties": {
            "query":       {...},   # 搜索关键词
            "max_results": {...},   # 返回数量
            "extra_params": {...},  # JSON 逃逸舱
        },
        "_defaults": {  # 其余参数默认值
            "max_tokens": 10000, "domain": "", "valence": -1,
            "arousal": -1, "importance_min": -1,
        },
    },
    # trace, hold 同理...
}
```

### 3.2 逃逸舱机制

瘦身前（7 参数）：
```json
{"query": "memory", "valence": 0.8, "domain": "work", "max_results": 5, ...}
```

瘦身后（3 参数）：
```json
{
  "query": "memory",
  "max_results": 5,
  "extra_params": "{\"valence\":0.8,\"domain\":\"work\"}"
}
```

Hub 收到调用后，解析 `extra_params` JSON，用默认值补全缺失参数，再转发给 Ombre Brain。

### 3.3 修改文件清单

| 文件 | 改动 |
|------|------|
| `mcp_servers/ombre/server.py` | 新增 `SLIM_SCHEMAS`、`_apply_slim()`、`_expand()`；修改 `get_tools()` 和 `call_tool()` |
| `mcp_servers/ntfy/server.py` | 精简 `notify_send` Schema（4→3 属性）；新增 `extra_params` 展开逻辑 |

---

## 4. 部署后验证

```
$ curl https://raven-victor.click/tools

✅ notify_send     props=3  (原4)
✅ ntfy_health     props=0  
✅ ntfy_info       props=0  
✅ breath          props=3  (原7)
✅ hold            props=3  (原8)
✅ grow            props=1  
✅ trace           props=3  (原12)
✅ pulse           props=1  
✅ dream           props=0  

全部 <=3 props: YES
```

Hub 日志确认：
```
Ombre get_tools: 6 raw -> 6 slimmed
  - breath (3 props)
  - hold (3 props)  
  - grow (1 props)
  - trace (3 props)
  - pulse (1 props)
  - dream (0 props)
```

---

## 5. 回滚方案

VPS 上原始文件已备份：

```bash
# 回滚 Ombre adapter
cp /root/ai-infrastructure/mcp_servers/ombre/server.py.bak \
   /root/ai-infrastructure/mcp_servers/ombre/server.py

# 回滚 ntfy adapter  
cp /root/ai-infrastructure/mcp_servers/ntfy/server.py.bak \
   /root/ai-infrastructure/mcp_servers/ntfy/server.py

# 重启 Hub
cd /root/ai-infrastructure && docker compose restart mcp-hub
```

---

## 6. 架构教训

1. **MCP 规范本身不限制 Schema 复杂度**，但不同 Claude 客户端（Desktop/Code/Mobile）的实现成熟度不同
2. **网关层是 Schema 适配的理想位置** — 不需要修改上游服务（Ombre Brain），不需要等待下游客户端（Claude）修复 Bug
3. **逃逸舱模式**（核心参数显式暴露 + JSON 字符串传递高级参数）在 API 设计中是实用的兼容性策略
4. **诊断工具链的重要性** — 本次排查使用了 `curl /health`、`curl /tools`、`docker logs`、`grep` 源码扫描、容器内文件搜索等多种手段

---

## 7. 参考链接

- Ombre Brain: https://github.com/P0luz/Ombre-Brain
- MCP Hub (本仓库): https://github.com/Padalackles/ai-infrastructure
- MCP 协议规范: https://modelcontextprotocol.io

# Ombre Brain MCP Tool 排查记录

## 问题背景

在 Claude Web 中，部分 MCP Tool 无法显示，而其他结构相似的 Tool 可以正常显示。

最初观察到：

* `breath` 不显示
* `trace` 不显示
* `dream` 显示
* `grow` 显示

随后进一步确认：

* **Echo 并不是 Ombre Brain 内的 Tool**，此前属于误判，因此后续分析中已移除该因素。

---

# 第一阶段：Schema 对比

对四个 Tool 的 JSON Schema 进行了逐项比较。

比较内容包括：

* `title`
* `default`
* `required`
* `properties`
* 参数数量
* object 结构

得到结果：

| Tool   | required | default | 是否显示 |
| ------ | -------- | ------- | ---- |
| breath | 无        | 有       | ❌    |
| dream  | 无        | 有       | ✅    |
| trace  | 有        | 有       | ❌    |
| grow   | 有        | 有       | ✅    |

可以看到：

* `breath` 与 `dream` 的 Schema 极其接近；
* `trace` 与 `grow` 的 Schema 极其接近；

因此：

> **JSON Schema 本身无法解释 Tool 消失的原因。**

---

# 第二阶段：排除 Schema 问题

进一步检查：

* object 定义
* properties
* required
* default
* 参数类型
* JSON 合法性

均未发现异常。

因此可以基本排除：

* Schema 非法
* required 导致隐藏
* default 导致隐藏
* 参数结构导致隐藏

---

# 第三阶段：定位 Hub 层问题

继续检查 MCP Hub。

发现：

Tool 名称中存在：

```
notify.send
```

而 MCP 对 Tool Name 有正则限制：

```
^[a-zA-Z0-9_-]{1,64}$
```

其中：

```
.
```

（点号）

**不允许出现在 Tool Name 中。**

因此：

```
notify.send
```

违反命名规则。

---

# 修正

修改 Tool Name：

```
notify.send
```

↓

```
notify_send
```

使其符合 MCP 命名规范。

---

# 其他调整

同时确认：

```
HUB_EXPOSE_INTERNAL_TOOLS=false
```

时：

* Hub 不再向 Claude Web 暴露内部工具；
* 内部 Tool 返回空列表 `[]`；
* 对外仅暴露正式 Tool。

---

# 部署结果

部署完成后：

* `notify.send → notify_send` 已生效；
* Hub Tool 名称全部符合规范；
* Claude Web 获取到的 Tool 列表恢复正常。

最终 Hub 共暴露：

**9 个 Tool**

全部符合：

```
^[a-zA-Z0-9_-]{1,64}$
```

---

# 最终结论

本次问题并非由 JSON Schema 导致，而是由于 **MCP Tool Name 不符合命名规范** 所引起。

主要修复内容：

1. 将 `notify.send` 更名为 `notify_send`；
2. 保持对外暴露的 Tool 名称全部符合 MCP 正则要求；
3. 确认内部 Tool 不再向 Claude Web 暴露。

问题已解决。

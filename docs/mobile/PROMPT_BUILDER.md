# Prompt Builder Protocol

**Version:** 1.0.0
**Status:** ✅ Specification Complete
**Created:** 2026-06-20

---

## 1. Purpose

The Prompt Builder converts a Trigger JSON payload into the exact prompt text
that MacroDroid sends to Claude.  It is a **pure function** — no database, no
API, no side effects.

This protocol lives entirely on the Android side.  The backend never generates
prompts.  Claude never receives raw SQLite rows.

---

## 2. Architecture Position

```
                    ┌──── Backend (never touches prompt) ────┐
                    │                                        │
Activity → Decision → TriggerService → SQLite → REST API     │
                                                    │        │
                                                    ▼        │
                                           GET /trigger/pending
                                                    │        │
└───────────────────────────────────────────────────┼────────┘
                                                    │
                    ┌──── Android (MacroDroid) ─────┼────────┐
                    │                               ▼        │
                    │                        buildPrompt()    │
                    │                               │         │
                    │                               ▼         │
                    │                          Claude App     │
                    │                               │         │
                    │                               ▼         │
                    │                    POST /trigger/{id}/ack
                    │                                        │
                    └────────────────────────────────────────┘
```

**Invariants:**

- Decision never creates prompts.
- TriggerService never creates prompts.
- REST API never returns prompt text.
- `buildPrompt()` is a pure function: `Trigger → String`.

---

## 3. Input Format

`buildPrompt()` receives exactly what `GET /trigger/pending` returns
in the `"trigger"` field:

```json
{
    "id": "trg_01abcd1234567890",
    "type": "procrastination",
    "priority": 1,
    "payload": {
        "app": "Bilibili",
        "duration": 7200
    }
}
```

The function reads `type` and `payload` only.  `id`, `priority`, and `status`
are ignored during prompt generation.

---

## 4. Prompt Builder Interface

```
buildPrompt(trigger: Trigger) → String
```

**Contract:**

| Property | Constraint |
|---|---|
| Input | A single Trigger object (the `"trigger"` field of the pending response) |
| Output | A plain UTF-8 string — the exact text to paste into Claude |
| Pure | No I/O, no network, no database |
| Total | Never throws — unknown types produce a fallback prompt |
| Deterministic | Same input → same output every time |

**Pseudo-implementation (MacroDroid / Tasker / JavaScript):**

```javascript
function buildPrompt(trigger) {
    const templates = {
        procrastination: (p) =>
            `用户已经连续使用 ${p.app} ${formatDuration(p.duration)}。\n\n` +
            `请结合最近 Activity，提醒用户停止当前行为，` +
            `并建议更有价值的替代活动。\n\n` +
            `回复控制在 100 字以内。`,

        battery_low: (p) =>
            `用户设备电量已降至 ${p.level}%。\n\n` +
            `请提醒用户及时充电，并根据当前时间建议` +
            `开启省电模式或寻找充电设备。\n\n` +
            `回复控制在 80 字以内。`,

        late_sleep: (p) =>
            `现在是 ${p.current_time}，用户仍然处于活跃状态。\n\n` +
            `请温和地提醒用户休息，说明熬夜对健康的影响，` +
            `并给出放松入睡的建议。\n\n` +
            `回复控制在 100 字以内。`,
    };

    const fn = templates[trigger.type];
    if (fn) {
        return fn(trigger.payload);
    }

    // Unknown type — fallback
    return fallbackPrompt(trigger);
}
```

---

## 5. Prompt Templates

### 5.1 procrastination

**Trigger type:** `procrastination`

**Expected payload:**

```json
{
    "app": "Bilibili",
    "duration": 7200
}
```

| Payload field | Type | Required | Description |
|---|---|---|---|
| `app` | string | ✅ | App name displayed to user |
| `duration` | integer | ✅ | Total usage time in seconds |

**Template:**

```
用户已经连续使用 {app} {formatted_duration}。

请结合最近 Activity，提醒用户停止当前行为，
并建议更有价值的替代活动。

回复控制在 100 字以内。
```

**Example output:**

```
用户已经连续使用 Bilibili 2 小时。

请结合最近 Activity，提醒用户停止当前行为，
并建议更有价值的替代活动。

回复控制在 100 字以内。
```

---

### 5.2 battery_low

**Trigger type:** `battery_low`

**Expected payload:**

```json
{
    "level": 15
}
```

| Payload field | Type | Required | Description |
|---|---|---|---|
| `level` | integer | ✅ | Battery percentage (0–100) |

**Template:**

```
用户设备电量已降至 {level}%。

请提醒用户及时充电，并根据当前时间建议
开启省电模式或寻找充电设备。

回复控制在 80 字以内。
```

**Example output:**

```
用户设备电量已降至 15%。

请提醒用户及时充电，并根据当前时间建议
开启省电模式或寻找充电设备。

回复控制在 80 字以内。
```

---

### 5.3 late_sleep

**Trigger type:** `late_sleep`

**Expected payload:**

```json
{
    "current_time": "02:30",
    "awake_duration": 10800
}
```

| Payload field | Type | Required | Description |
|---|---|---|---|
| `current_time` | string | ✅ | Current local time (HH:MM, 24h) |
| `awake_duration` | integer | ✅ | Seconds since last sleep/doze event |

**Template:**

```
现在是 {current_time}，用户仍然处于活跃状态。

请温和地提醒用户休息，说明熬夜对健康的影响，
并给出放松入睡的建议。

回复控制在 100 字以内。
```

**Example output:**

```
现在是 02:30，用户仍然处于活跃状态。

请温和地提醒用户休息，说明熬夜对健康的影响，
并给出放松入睡的建议。

回复控制在 100 字以内。
```

---

### 5.4 Unknown / Fallback

**Trigger type:** any unmapped type

**Template:**

```
检测到触发器: {type}。

Payload:
{formatted_payload}

请根据以上信息提供建议。回复控制在 100 字以内。
```

**Behavior:**

- Never throws.
- Always produces a valid string.
- Renders the raw `type` and `payload` so Claude can still make sense of it.
- This ensures new trigger types work immediately — no code changes needed
  on the Android side.

**Fallback implementation:**

```javascript
function fallbackPrompt(trigger) {
    const payloadStr = JSON.stringify(trigger.payload, null, 2);
    return (
        `检测到触发器: ${trigger.type}。\n\n` +
        `Payload:\n${payloadStr}\n\n` +
        `请根据以上信息提供建议。回复控制在 100 字以内。`
    );
}
```

---

## 6. Unknown Trigger Policy

| Guarantee | Detail |
|---|---|
| Never crash | All trigger types produce a valid prompt |
| Informative | Raw `type` and `payload` are shown to Claude |
| Forward-compatible | Future trigger types work on day 1 — no Android update needed |
| No silent failure | The fallback prompt makes the situation explicit to Claude |

**Why this matters:**  When a new Rule is deployed on the backend (e.g. `exercise`,
`meeting`), MacroDroid does NOT need to be updated.  `buildPrompt()` falls back
gracefully, and Claude receives enough context to generate a useful response.

---

## 7. Mobile Protocol — Full Android Flow

### Step-by-step

```
1. MacroDroid wakes (periodic trigger, e.g. every 30s).

2. GET https://raven-victor.click/trigger/pending
   → { "trigger": {...}, "recent_activity": [...] }

3. If trigger is null → nothing to do.  Sleep.

4. Extract trigger from response body.

5. prompt = buildPrompt(trigger)

6. Launch Claude app (Intent / URI scheme).

7. Paste prompt into Claude input field.

8. Press Send.

9. Wait for Claude response (optional — MacroDroid can
   read the notification or poll the conversation).

10. POST https://raven-victor.click/trigger/{id}/ack
    → marks trigger as done on the backend.

11. Sleep until next wake interval.
```

### Flow Diagram

```
MacroDroid Wake
      │
      ▼
GET /trigger/pending
      │
      ├── trigger: null ──→ Sleep
      │
      └── trigger: {...}
              │
              ▼
         buildPrompt()
              │
              ▼
        Launch Claude
              │
              ▼
         Paste + Send
              │
              ▼
    POST /trigger/{id}/ack
              │
              ▼
            Sleep
```

### Error Handling

| Failure | Behavior |
|---|---|
| Network error on GET | Retry 3× with 5s backoff, then skip this wake cycle |
| Claude app not installed | Log warning, skip trigger (do NOT ack — it stays pending) |
| Acknowledge fails | Retry 2×, leave pending — will be retried next wake cycle |
| Unknown trigger type | `buildPrompt()` fallback handles it — Claude still gets context |

---

## 8. Future Extension — Adding a New Rule

Adding a new Rule type (e.g. `exercise`, `meeting`, `todo`) requires **only**
a new template in `buildPrompt()`.

### What changes

| Layer | Change needed? |
|---|---|
| Database schema | ❌ None |
| Decision Engine | ❌ None (already supports any `type` string) |
| TriggerService | ❌ None |
| REST API | ❌ None |
| MacroDroid workflow | ❌ None (same GET → buildPrompt → Claude → ack) |
| `buildPrompt()` | ✅ Add one template entry |

### Example — adding `exercise`

```javascript
// Backend Rule (decision/rules.py) — already supported:
@register
def exercise_reminder_rule(events):
    ...
    return TriggerRequest(
        type="exercise",
        payload={"last_activity": "3h ago", "step_count": 1200},
        priority=1,
    )

// Android side — one new template:
const templates = {
    // ... existing ...
    exercise: (p) =>
        `用户已经 ${p.last_activity} 没有活动，今日步数 ${p.step_count}。\n\n` +
        `请建议用户进行简单的身体活动或短距离散步。\n\n` +
        `回复控制在 80 字以内。`,
};
```

**Total cost of a new rule:** 1 backend rule function + 1 Android template entry.

---

## 9. Example Outputs

### 9.1 procrastination

```
用户已经连续使用 Bilibili 2 小时。

请结合最近 Activity，提醒用户停止当前行为，
并建议更有价值的替代活动。

回复控制在 100 字以内。
```

### 9.2 battery_low

```
用户设备电量已降至 15%。

请提醒用户及时充电，并根据当前时间建议
开启省电模式或寻找充电设备。

回复控制在 80 字以内。
```

### 9.3 late_sleep

```
现在是 02:30，用户仍然处于活跃状态。

请温和地提醒用户休息，说明熬夜对健康的影响，
并给出放松入睡的建议。

回复控制在 100 字以内。
```

### 9.4 unknown (e.g. future `exercise` trigger)

```
检测到触发器: exercise。

Payload:
{
  "last_activity": "3h ago",
  "step_count": 1200
}

请根据以上信息提供建议。回复控制在 100 字以内。
```

---

## 10. Template Reference

| Trigger type | Priority | Payload fields | Prompt length |
|---|---|---|---|
| `procrastination` | 2 | `app` (str), `duration` (int, seconds) | ≤ 100 字 |
| `battery_low` | 0 | `level` (int, 0–100) | ≤ 80 字 |
| `late_sleep` | 1 | `current_time` (str), `awake_duration` (int) | ≤ 100 字 |
| `unknown` / any | — | any (rendered as formatted JSON) | ≤ 100 字 |

---

## 11. Design Principles

1. **Backend is dumb.**  It stores triggers, serves JSON, and acks them.  It
   has no opinion about what text Claude should see.

2. **Android is the sole prompt author.**  `buildPrompt()` encapsulates every
   decision about prompt format, language, length, and tone.

3. **Pure function.**  `buildPrompt()` is testable standalone — no mocks,
   no network, no lifecycle.  `buildPrompt({"type": "battery_low", "payload": {"level": 15}})` always returns the same string.

4. **Forward-compatible.**  New trigger types work immediately via fallback.
   Adding a template is an enhancement, not a requirement.

5. **Protocol, not implementation.**  This document defines the *contract*.
   The actual implementation can be in JavaScript (Tasker), MacroDroid
   variables, Kotlin, or any language — as long as it obeys the contract.

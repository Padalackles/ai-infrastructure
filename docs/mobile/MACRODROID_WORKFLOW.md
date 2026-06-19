# MacroDroid Integration Workflow

**Status:** ✅ Complete
**Version:** 1.0.0
**Created:** 2026-06-20

---

## 1. Overview

### 1.1 Purpose

This document defines every action required to recreate the complete
Trigger → Claude pipeline inside MacroDroid on Android.  No programming
is required — everything is configured through MacroDroid's UI.

### 1.2 Pipeline

```
┌─────────────────── Backend (raven-victor.click) ────────────────────┐
│                                                                     │
│   GET /trigger/pending  ──→  { trigger, recent_activity }           │
│   POST /trigger/{id}/ack                                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
        ▲                                        │
        │  HTTP GET                               │  HTTP POST (ack)
        │                                        ▼
┌─────────────────── Android (MacroDroid) ────────────────────────────┐
│                                                                     │
│   1. HTTP Request (GET /trigger/pending)                             │
│   2. If trigger is null → Sleep                                     │
│   3. Extract JSON into variables                                    │
│   4. buildPrompt() → prompt_text                                    │
│   5. Launch Claude                                                  │
│   6. Wait for app                                                   │
│   7. Paste prompt into input field                                  │
│   8. Click Send                                                     │
│   9. HTTP Request (POST /trigger/{id}/ack)                          │
│  10. Sleep until next cycle                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Design Principles

- **Backend never generates prompts.**  Prompt text is built entirely on Android.
- **Trigger JSON is the contract.**  The backend sends JSON; MacroDroid converts it.
- **No Android programming.**  Pure MacroDroid actions + one JavaScript snippet.
- **Type-safe.**  Every trigger type has a known payload schema.
- **Fails gracefully.**  Network errors, missing apps, UI failures — every
  failure case is handled explicitly.

---

## 2. Variables

Every piece of data flows through MacroDroid variables.  All variables
are **string** type.  Numbers and booleans are converted as needed.

### 2.1 Trigger Variables

| Variable | Source | Example | Description |
|---|---|---|---|
| `trigger_id` | `$.trigger.id` | `trg_0a1b2c3d4e5f6g7h` | Unique trigger ID |
| `trigger_type` | `$.trigger.type` | `procrastination` | Canonical trigger type |
| `trigger_status` | `$.trigger.status` | `pending` | Always `pending` or `acked` |
| `trigger_priority` | `$.trigger.priority` | `1` | 0=highest, 1=normal, 2=low |
| `trigger_created_at` | `$.trigger.created_at` | `2026-06-20T15:30:00.000Z` | ISO 8601 UTC |

### 2.2 Payload Variables (by trigger type)

**procrastination:**

| Variable | Source | Example |
|---|---|---|
| `payload_app` | `$.trigger.payload.app` | `com.ss.android.ugc.aweme` |
| `payload_label` | `$.trigger.payload.label` | `TikTok` |
| `payload_threshold_min` | `$.trigger.payload.threshold_minutes` | `25` |
| `payload_actual_min` | `$.trigger.payload.actual_minutes` | `42.5` |

**battery_low:**

| Variable | Source | Example |
|---|---|---|
| `payload_level` | `$.trigger.payload.level` | `15` |
| `payload_threshold` | `$.trigger.payload.threshold` | `20` |
| `payload_charging` | `$.trigger.payload.is_charging` | `false` |

**late_sleep:**

| Variable | Source | Example |
|---|---|---|
| `payload_hour_utc` | `$.trigger.payload.hour_utc` | `15` |
| `payload_cutoff_hour` | `$.trigger.payload.cutoff_hour_utc` | `15` |
| `payload_threshold_min` | `$.trigger.payload.threshold_minutes` | `10` |
| `payload_actual_min` | `$.trigger.payload.actual_minutes` | `34.2` |

**screen.long_use:**

| Variable | Source | Example |
|---|---|---|
| `payload_threshold_min` | `$.trigger.payload.threshold_minutes` | `40` |
| `payload_actual_min` | `$.trigger.payload.actual_minutes` | `65.3` |

**app.long_use:**

| Variable | Source | Example |
|---|---|---|
| `payload_app` | `$.trigger.payload.app` | `com.ss.android.ugc.aweme` |
| `payload_threshold_min` | `$.trigger.payload.threshold_minutes` | `30` |
| `payload_actual_min` | `$.trigger.payload.actual_minutes` | `55.1` |

### 2.3 Computed Variables

| Variable | Created by | Example | Description |
|---|---|---|---|
| `prompt_text` | JavaScript action | (multi-line) | Final text pasted into Claude |
| `http_status` | HTTP Request action | `200` | Response status code |
| `has_trigger` | If condition | `true` / `false` | Whether `$.trigger` is non-null |

---

## 3. HTTP GET — Poll Pending Triggers

### 3.1 Configuration

| Parameter | Value |
|---|---|
| **Action type** | HTTP Request |
| **Method** | GET |
| **URL** | `https://raven-victor.click/trigger/pending` |
| **Headers** | `Accept: application/json` |
| **Timeout** | 10 seconds |
| **Block next actions until complete** | ✅ Checked |

### 3.2 Expected Response

**HTTP 200 — Trigger available:**

```json
{
    "trigger": {
        "id": "trg_0a1b2c3d4e5f6g7h",
        "type": "procrastination",
        "payload": {
            "app": "com.ss.android.ugc.aweme",
            "label": "TikTok",
            "threshold_minutes": 25,
            "actual_minutes": 42.5
        },
        "status": "pending",
        "priority": 1,
        "created_at": "2026-06-20T15:30:00.000Z",
        "acked_at": null
    },
    "recent_activity": [
        {
            "id": "evt_abc123",
            "type": "app.opened",
            "timestamp": "2026-06-20T15:28:00.000Z",
            "payload": {"package": "com.ss.android.ugc.aweme", "label": "TikTok"},
            "device": "pixel-8-pro"
        }
    ]
}
```

**HTTP 200 — No trigger:**

```json
{
    "trigger": null,
    "recent_activity": []
}
```

### 3.3 JSON Parsing

MacroDroid's HTTP Request action automatically parses the JSON response
into variables when you configure **JSON parsing** in the action.

**JSON Path → Variable mappings:**

| JSON Path | MacroDroid Variable |
|---|---|
| `$.trigger` | (use for null check) |
| `$.trigger.id` | `trigger_id` |
| `$.trigger.type` | `trigger_type` |
| `$.trigger.priority` | `trigger_priority` |
| `$.trigger.status` | `trigger_status` |
| `$.trigger.created_at` | `trigger_created_at` |
| `$.trigger.payload.app` | `payload_app` |
| `$.trigger.payload.label` | `payload_label` |
| `$.trigger.payload.level` | `payload_level` |
| `$.trigger.payload.threshold` | `payload_threshold` |
| `$.trigger.payload.is_charging` | `payload_charging` |
| `$.trigger.payload.hour_utc` | `payload_hour_utc` |
| `$.trigger.payload.cutoff_hour_utc` | `payload_cutoff_hour` |
| `$.trigger.payload.threshold_minutes` | `payload_threshold_min` |
| `$.trigger.payload.actual_minutes` | `payload_actual_min` |

> **Note:**  Not all payload fields are present in every trigger type.
> MacroDroid sets missing variables to empty string.  This is expected —
> the JavaScript Prompt Builder handles it.

### 3.4 Failure Handling

| Scenario | Action |
|---|---|
| HTTP timeout (10s) | Set `has_trigger` = false, skip to end of macro |
| HTTP 4xx / 5xx | Set `has_trigger` = false, skip to end of macro |
| Response body empty | Set `has_trigger` = false, skip to end of macro |
| `$.trigger` is null | Set `has_trigger` = false, skip to end of macro |

**MacroDroid constraint branch:**
```
If [trigger_id] = ""   →   Stop (no trigger available)
```

---

## 4. JavaScript Prompt Builder

### 4.1 Purpose

Converts trigger JSON into the exact text sent to Claude.  This is the
**only** place where prompt text is generated.  The backend never touches
prompts.

### 4.2 Input / Output

| Direction | Variable | Type |
|---|---|---|
| **Input** | `trigger_type` | MacroDroid string variable |
| **Input** | `trigger_priority` | MacroDroid string variable |
| **Input** | `trigger_created_at` | MacroDroid string variable |
| **Input** | `payload_*` (all payload vars) | MacroDroid string variables |
| **Output** | `prompt_text` | MacroDroid string variable |

### 4.3 Complete JavaScript Implementation

Paste the following code into MacroDroid's **JavaScript** action:

```javascript
// ── Prompt Builder ──────────────────────────────────────────────
// Input:  MacroDroid local variables (trigger_*, payload_*)
// Output: prompt_text (global variable)

function formatTimestamp(iso) {
    if (!iso) return "----.--.-- --:--";
    try {
        const d = new Date(iso);
        const pad = n => String(n).padStart(2, '0');
        return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    } catch (e) {
        return "----.--.-- --:--";
    }
}

function formatMinutes(minutes) {
    if (!minutes || isNaN(minutes)) return "? 分钟";
    const m = Number(minutes);
    if (m < 1) return "<1 分钟";
    if (m < 60) return Math.round(m) + " 分钟";
    const h = Math.floor(m / 60);
    const r = Math.round(m % 60);
    if (r === 0) return h + " 小时";
    return h + " 小时 " + r + " 分钟";
}

function formatHourUTC(h) {
    if (h === undefined || h === null || h === "") return "?";
    // Convert UTC hour to readable form
    const hour = Number(h);
    const cst = (hour + 8) % 24; // UTC → CST approximation
    const period = cst >= 6 && cst < 18 ? "凌晨" : 
                   cst >= 18 && cst < 22 ? "晚上" :
                   cst >= 22 || cst < 2 ? "深夜" : "凌晨";
    return String(cst).padStart(2, '0') + ":00 (" + period + ")";
}

// ── Read variables ──────────────────────────────────────────────
var type = local.trigger_type || "";
var priority = local.trigger_priority || "1";
var createdAt = local.trigger_created_at || "";

// Priority mark
var PRIORITY_MARK = {"0": "Ⅰ", "1": "Ⅱ", "2": "Ⅲ"};
var mark = PRIORITY_MARK[priority] || "Ⅱ";

// Header
var ts = formatTimestamp(createdAt);
var header = "🔔自动触发|" + ts + " " + mark;

// ── Templates ───────────────────────────────────────────────────

var prompt = "";

switch (type) {

    case "procrastination":
        var appLabel = local.payload_label || local.payload_app || "未知应用";
        var actualMin = local.payload_actual_min;
        prompt = header + "\n\n" +
            "用户已经连续使用 " + appLabel + " " + formatMinutes(actualMin) + "。\n\n" +
            "请自行决定是否回复。";
        break;

    case "battery_low":
        var level = local.payload_level || "?";
        var isCharging = local.payload_charging === "true" || local.payload_charging === "True";
        prompt = header + "\n\n" +
            "用户设备电量已降至 " + level + "%。" +
            (isCharging ? " 设备正在充电。" : "") + "\n\n" +
            "请自行决定是否回复。";
        break;

    case "late_sleep":
        var hourUtc = local.payload_hour_utc;
        var actualMin = local.payload_actual_min;
        prompt = header + "\n\n" +
            "现在是 " + formatHourUTC(hourUtc) + "，用户仍然处于活跃状态（屏幕已亮屏 " + formatMinutes(actualMin) + "）。\n\n" +
            "请自行决定是否回复。";
        break;

    case "screen.long_use":
        var screenMin = local.payload_actual_min;
        prompt = header + "\n\n" +
            "用户已经连续使用设备 " + formatMinutes(screenMin) + "。\n\n" +
            "请自行决定是否回复。";
        break;

    case "app.long_use":
        var appPkg = local.payload_app || "未知应用";
        var appMin = local.payload_actual_min;
        prompt = header + "\n\n" +
            "用户已经连续使用 " + appPkg + " " + formatMinutes(appMin) + "。\n\n" +
            "请自行决定是否回复。";
        break;

    default:
        // ── Unknown type — fallback ─────────────────────────────
        prompt = header + "\n\n" +
            "检测到触发器: " + type + "。\n\n" +
            "请自行决定是否回复。";
        break;
}

// ── Output ───────────────────────────────────────────────────────
global.prompt_text = prompt;
```

### 4.4 Verify the JavaScript

After pasting, test with MacroDroid's **Test Action** feature:

1. Manually set `trigger_type` = `battery_low`
2. Set `payload_level` = `15`
3. Set `trigger_created_at` = `2026-06-20T15:30:00.000Z`
4. Run the JavaScript action
5. Check `prompt_text` contains:
   ```
   🔔自动触发|2026-06-20 15:30 Ⅱ

   用户设备电量已降至 15%。

   请自行决定是否回复。
   ```

---

## 5. Launch Claude

### 5.1 Primary Method — Launch App

| Parameter | Value |
|---|---|
| **Action type** | Launch Application |
| **Application** | Claude |
| **Launch failed →** | Continue anyway (unchecked — see fallback below) |

### 5.2 Alternative — Launch Activity (if Launch App fails)

| Parameter | Value |
|---|---|
| **Action type** | Launch Activity |
| **Package** | `com.anthropic.claude` |
| **Class** | `com.anthropic.claude.MainActivity` |

### 5.3 Fallback — Open URL

As a last resort, open the Claude Play Store page:

| Parameter | Value |
|---|---|
| **Action type** | Open Website |
| **URL** | `https://play.google.com/store/apps/details?id=com.anthropic.claude` |

### 5.4 App Launch Wait

After launching, MacroDroid must wait for Claude to become ready:

| Parameter | Value |
|---|---|
| **Action type** | Wait Before Next Action |
| **Duration** | 3 seconds |

> **Why:** Android needs time to bring the app to foreground and render
> the UI.  3 seconds is sufficient on modern devices.  Increase to 5
> seconds on older hardware.

---

## 6. UI Automation

Claude accepts text input via a standard Android `EditText` field.
MacroDroid's **UI Interaction** action simulates the user typing.

### 6.1 Action Sequence

```
┌──────────────────────────────────────┐
│ 1. UI Interaction — Click            │
│    Find the text input field         │
│    Target: EditText (focused)        │
├──────────────────────────────────────┤
│ 2. UI Interaction — Paste            │
│    Paste {prompt_text}               │
├──────────────────────────────────────┤
│ 3. UI Interaction — Click            │
│    Find the Send button              │
│    Target: Send (contentDescription) │
└──────────────────────────────────────┘
```

### 6.2 Step 1 — Focus Input Field

| Parameter | Value |
|---|---|
| **Action type** | UI Interaction |
| **Interaction** | Click |
| **Identify by** | Text Content |
| **Text to match** | `Message` |
| **Match type** | Contains |
| **Click action** | Click |
| **Timeout** | 5 seconds |
| **If not found** | Continue (graceful degradation) |

> **Alternative identifiers** (try in order):
> 1. Text Content → `Message` (English Claude UI)
> 2. Text Content → `消息` (Chinese Claude UI)
> 3. Class Name → `android.widget.EditText` (generic — always works)
> 4. Resource ID → `com.anthropic.claude:id/input` (if inspectable)

### 6.3 Step 2 — Paste Prompt Text

| Parameter | Value |
|---|---|
| **Action type** | UI Interaction |
| **Interaction** | Paste |
| **Paste content** | `{prompt_text}` (MacroDroid variable) |
| **Identify by** | Text Content |
| **Text to match** | `Message` or `消息` |
| **Timeout** | 5 seconds |
| **If not found** | Set Clipboard to `{prompt_text}`, then retry with generic EditText |

**Clipboard fallback (if Paste fails):**

| Parameter | Value |
|---|---|
| **Action type** | Set Clipboard |
| **Content** | `{prompt_text}` |
| **Action type** | UI Interaction — Paste (Clipboard) |

### 6.4 Step 3 — Click Send

| Parameter | Value |
|---|---|
| **Action type** | UI Interaction |
| **Interaction** | Click |
| **Identify by** | Content Description |
| **Text to match** | `Send` or `发送` |
| **Timeout** | 3 seconds |
| **If not found** | Try clicking by coordinates (last resort) |

**Coordinate fallback:**

| Parameter | Value |
|---|---|
| **Action type** | UI Interaction |
| **Interaction** | Click |
| **Identify by** | X,Y Location |
| **X %** | 90 |
| **Y %** | 95 |

> **Why coordinates as fallback:**  Claude's Send button is always in the
> bottom-right corner.  90%/95% is a safe approximation.

### 6.5 Timing

| Step | Wait before |
|---|---|
| Focus input | 3s (after app launch) |
| Paste text | 0.5s (after focus) |
| Click Send | 0.5s (after paste) |

---

## 7. HTTP ACK — Acknowledge Trigger

After the prompt is sent to Claude, the trigger must be **acknowledged**
on the backend so it isn't processed again.

### 7.1 Configuration

| Parameter | Value |
|---|---|
| **Action type** | HTTP Request |
| **Method** | POST |
| **URL** | `https://raven-victor.click/trigger/{trigger_id}/ack` |
| **Headers** | `Accept: application/json` |
| **Body** | (empty) |
| **Timeout** | 10 seconds |
| **Block next actions** | ❌ Unchecked (fire-and-forget) |

### 7.2 Expected Response

**HTTP 200 — Success:**

```json
{
    "id": "trg_0a1b2c3d4e5f6g7h",
    "type": "procrastination",
    "payload": {...},
    "status": "acked",
    "priority": 1,
    "created_at": "2026-06-20T15:30:00.000Z",
    "acked_at": "2026-06-20T15:31:00.000Z"
}
```

**HTTP 404 — Trigger not found:**

```json
{
    "status": "not_found",
    "message": "No trigger with id 'trg_0a1b2c3d4e5f6g7h'"
}
```

### 7.3 Retry Policy

| Attempt | Behavior |
|---|---|
| 1st | POST /trigger/{id}/ack |
| 1st fails | Wait 5 seconds, retry |
| 2nd fails | Wait 10 seconds, retry |
| 3rd fails | **Give up.** Trigger stays `pending`, will be re-polled next cycle. |

> **Why give up after 3 tries:**  The trigger remains `pending` in the
> queue.  The next polling cycle picks it up again.  This prevents
> infinite retry loops while ensuring nothing is lost.

---

## 8. Error Recovery

### 8.1 Error Matrix

| Failure | Detection | Recovery | Trigger status |
|---|---|---|---|
| No network (GET fails) | HTTP timeout / error | Skip cycle. Wait for next MacroDroid trigger. | Stays `pending` |
| `$.trigger` is null | `trigger_id` is empty | Skip cycle. Nothing to do. | N/A |
| Claude app not installed | Launch App fails | Skip to Clipboard fallback — user sees notification. Do NOT ack. | Stays `pending` |
| UI input not found | UI Interaction timeout | Set Clipboard + coordinate fallback tap. If still fails, do NOT ack. | Stays `pending` |
| ACK fails (1–3 retries) | HTTP non-200 | Give up after 3 retries. Trigger re-polled next cycle. | Stays `pending` |
| Unknown trigger type | JavaScript fallback | `buildPrompt()` renders type + raw payload. Prompt still valid. | Acked normally |

### 8.2 Global Timeout

The entire macro should not run longer than **45 seconds**.  Configure
MacroDroid's **Macro Run Timeout**:

| Parameter | Value |
|---|---|
| **Timeout** | 45 seconds |
| **On timeout** | Stop macro |

### 8.3 MacroDroid Constraint

| Parameter | Value |
|---|---|
| **Constraint** | Network Connected |
| **Invert** | ❌ (only run when connected) |

> This prevents the macro from running when offline — the HTTP GET will
> always fail anyway.

---

## 9. Complete Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     MacroDroid Periodic Trigger                    │
│                     (every 30–60 seconds)                         │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Constraint Check:     │
         │  Network Connected?    │
         └───────────┬───────────┘
                     │
            ┌────────┴────────┐
            │ No              │ Yes
            ▼                 ▼
       ┌────────┐   ┌─────────────────────┐
       │  Stop   │   │  HTTP GET            │
       └────────┘   │  /trigger/pending     │
                    │  Timeout: 10s         │
                    └──────────┬────────────┘
                               │
                      ┌────────┴────────┐
                      │ Fail            │ 200 OK
                      ▼                 ▼
                 ┌────────┐   ┌─────────────────────┐
                 │  Stop   │   │  trigger_id empty?   │
                 └────────┘   └──────────┬────────────┘
                                         │
                                ┌────────┴────────┐
                                │ Yes             │ No (has trigger)
                                ▼                 ▼
                           ┌────────┐   ┌─────────────────────┐
                           │  Stop   │   │  JavaScript          │
                           └────────┘   │  buildPrompt()       │
                                        │  Output: prompt_text │
                                        └──────────┬──────────┘
                                                   │
                                                   ▼
                                        ┌─────────────────────┐
                                        │  Launch Claude       │
                                        │  Package:            │
                                        │  com.anthropic.claude│
                                        └──────────┬──────────┘
                                                   │
                                                   ▼
                                        ┌─────────────────────┐
                                        │  Wait 3 seconds      │
                                        └──────────┬──────────┘
                                                   │
                                                   ▼
                                        ┌─────────────────────┐
                                        │  UI: Click input     │
                                        │  (EditText)          │
                                        └──────────┬──────────┘
                                                   │
                                          ┌────────┴────────┐
                                          │ Fail            │ OK
                                          ▼                 ▼
                                     ┌────────┐   ┌─────────────────────┐
                                     │ Clipboard│   │  UI: Paste prompt    │
                                     │ Fallback │   │  {prompt_text}       │
                                     └────┬─────┘   └──────────┬──────────┘
                                          │                     │
                                          ▼                     ▼
                                        ┌─────────────────────────────┐
                                        │  UI: Click Send              │
                                        │  ContentDesc: "Send"/"发送"  │
                                        │  Fallback: coords 90%,95%   │
                                        └──────────────┬──────────────┘
                                                       │
                                                       ▼
                                        ┌─────────────────────────────┐
                                        │  HTTP POST                   │
                                        │  /trigger/{trigger_id}/ack  │
                                        │  Timeout: 10s               │
                                        │  Retry: 3× (5s, 10s)       │
                                        └──────────────┬──────────────┘
                                                       │
                                                       ▼
                                                  ┌────────┐
                                                  │  Stop   │
                                                  └────────┘
```

---

## 10. Action List — Exact Order

This is the complete, numbered list of actions to create inside MacroDroid.
Build the macro action-by-action in this exact order.

### Macro: "Claude Trigger Pipeline"

**Trigger:** Regular Interval — every 60 seconds

**Constraint:** Network Connected

| # | Action | Configuration |
|---|---|---|
| 1 | **HTTP Request** | `GET https://raven-victor.click/trigger/pending`<br>Headers: `Accept: application/json`<br>Timeout: 10s |
| 2 | **If Condition** | `[trigger_id]` **is empty** → Go to #12 (End) |
| 3 | **Set Variable** | `has_trigger` = `true` |
| 4 | **JavaScript** | Paste the complete Prompt Builder code from §4.3<br>Output: `prompt_text` |
| 5 | **Launch Application** | Claude (`com.anthropic.claude`) |
| 6 | **Wait** | 3 seconds |
| 7 | **UI Interaction — Click** | Identify by: Text Content → `Message`<br>Timeout: 5s |
| 8 | **UI Interaction — Paste** | Content: `{prompt_text}`<br>Identify by: Text Content → `Message`<br>Timeout: 5s |
| 9 | **UI Interaction — Click** | Identify by: Content Description → `Send`<br>Timeout: 3s |
| 10 | **HTTP Request** | `POST https://raven-victor.click/trigger/{trigger_id}/ack`<br>Headers: `Accept: application/json`<br>Timeout: 10s |
| 11 | **If Condition** | ACK failed? → Wait 5s → Retry POST → Wait 10s → Retry POST |
| 12 | **End If** | (closes #2) |

### 10.1 Fallback Sub-macro (UI failures)

If step 7 or 8 fails, insert:

| # | Action | Configuration |
|---|---|---|
| F1 | **Set Clipboard** | `{prompt_text}` |
| F2 | **UI Interaction — Click** | Identify by: Class Name → `android.widget.EditText`<br>Timeout: 3s |
| F3 | **UI Interaction — Paste (Clipboard)** | Timeout: 3s |
| F4 | **UI Interaction — Click** | Identify by: X,Y Location → X=90%, Y=95%<br>Timeout: 3s |

### 10.2 Testing Checklist

- [ ] Macro trigger fires (check MacroDroid log)
- [ ] GET /trigger/pending returns 200
- [ ] `trigger_id` is populated when a pending trigger exists
- [ ] `prompt_text` is non-empty after JavaScript action
- [ ] Claude app launches successfully
- [ ] UI Interaction finds the message input field
- [ ] Prompt text appears in Claude's input
- [ ] Send button is clicked
- [ ] ACK returns 200 with `"status": "acked"`
- [ ] When no trigger pending, macro stops at step 2 (no Claude launch)
- [ ] When offline, constraint prevents execution

---

## 11. Reference — Trigger Types Summary

| Trigger Type | Trigger | Priority | Payload Keys |
|---|---|---|---|
| `screen.long_use` | Screen time excessive | 1 | `threshold_minutes`, `actual_minutes` |
| `app.long_use` | Specific app usage excessive | 1 | `app`, `threshold_minutes`, `actual_minutes` |
| `battery_low` | Battery below threshold | 2 | `level`, `threshold`, `is_charging` |
| `procrastination` | Entertainment app overuse | 1 | `app`, `label`, `threshold_minutes`, `actual_minutes` |
| `late_sleep` | Screen on past cutoff | 1 | `hour_utc`, `cutoff_hour_utc`, `threshold_minutes`, `actual_minutes` |
| *(any new type)* | (fallback) | 1 | *(rendered as JSON)* |

---

## 12. Maintenance — Adding a New Trigger Type

When a new Rule is added to the backend, update **only** the JavaScript
in step 4:

1. Open MacroDroid
2. Edit the "Claude Trigger Pipeline" macro
3. Edit the JavaScript action (step 4)
4. Add a new `case` to the `switch` statement
5. Save

No other changes needed.  Unknown types already work via the `default`
fallback — adding a `case` just improves the prompt quality.

---

## Appendix A: Scripting the JavaScript

To test the Prompt Builder without MacroDroid:

```javascript
// Node.js test harness
function testPromptBuilder() {
    const local = {
        trigger_type: "battery_low",
        trigger_priority: "2",
        trigger_created_at: "2026-06-20T15:30:00.000Z",
        payload_level: "15",
        payload_charging: "false",
    };
    // ... paste buildPrompt code here ...
    console.log(global.prompt_text);
}
testPromptBuilder();
```

## Appendix B: Known Limitations

1. **UI element identifiers may change.**  If Claude updates its UI in a
   Play Store update, the UI Interaction text identifiers (`Message`,
   `Send`) may need updating.  The coordinate fallback provides resilience.

2. **UTC-only timestamps.**  The prompt header uses UTC time.  Future
   versions may compute CST (UTC+8) inside the JavaScript.

3. **No Claude response detection.**  The current macro sends the prompt
   and acks immediately.  It does not wait for Claude's reply.  This is
   by design — the trigger is fire-and-forget.

4. **In-memory cooldown.**  If the backend restarts, cooldown state is
   lost.  A rule may fire again sooner than the configured cooldown.

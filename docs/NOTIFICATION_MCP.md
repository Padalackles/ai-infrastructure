# Notification MCP — ntfy.sh Integration

Push notifications via ntfy.sh, delivered to the `raven-victor-c503460d` topic.
Notifications are sent by executing `curl` on the VPS host.

## Architecture

```
Claude Web → MCP Hub → Notification MCP → curl → https://ntfy.sh/<topic>
                                                              ↓
                                                     Android ntfy app
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `NTFY_SERVER` | `https://ntfy.sh` | ntfy server URL |
| `NTFY_TOPIC` | `raven-victor-c503460d` | Target topic |

Set in `.env`:

```bash
NTFY_SERVER=https://ntfy.sh
NTFY_TOPIC=raven-victor-c503460d
```

## Tools

### `notify_send`

Send a push notification.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `message` | string | ✅ | — | Notification body |
| `title` | string | no | `Claude` | Notification title |
| `priority` | string | no | `default` | `min`, `low`, `default`, `high`, `urgent` |
| `tags` | string | no | — | Comma-separated tags |

### `ntfy_health`

Check service health. Returns server URL and topic.

### `ntfy_info`

Get service metadata (name, version, server, topic).

## Response Format

```json
{
  "success": true,
  "message": "Task-012 test",
  "timestamp": "2026-06-18T12:00:00Z",
  "provider": "ntfy",
  "ntfy_response": {"id": "...", "time": 1234567890}
}
```

Error responses:

```json
{
  "success": false,
  "error": "message is required and must be non-empty",
  "timestamp": "2026-06-18T12:00:00Z",
  "provider": "ntfy"
}
```

## Error Handling

| Error | Response |
|---|---|
| Empty message | `success: false`, `error: "message is required..."` |
| curl timeout | `success: false`, `error: "curl timed out after 10s"` |
| curl not found | `success: false`, `error: "curl executable not found"` |
| curl non-zero exit | `success: false`, `error: "curl exited N: ..."` |

## Testing

```bash
cd mcp-hub
PYTHONPATH="src:.." pytest tests/test_ntfy_integration.py -v
```

Manual test:

```bash
curl -sk -X POST https://raven-victor.click/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"notify_send","arguments":{"message":"Test from CLI","title":"CLI Test"}}}'
```

# Caddy Reverse Proxy

Auto HTTPS via Let's Encrypt. Proxies all traffic to `mcp-hub:8080`.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DOMAIN` | `raven-victor.click` | Public domain name |
| `CADDY_ACME_EMAIL` | `admin@raven-victor.click` | Email for Let's Encrypt |

## Usage

```bash
export DOMAIN=raven-victor.click
export CADDY_ACME_EMAIL=admin@raven-victor.click
docker compose up -d caddy
```

## Current Status

Current default deployment:

- Domain: `raven-victor.click`
- HTTPS via Let's Encrypt
- Automatic HTTP → HTTPS redirect
- TLS 1.3 enabled

## Routes

| Path | Description | Target |
|------|-------------|--------|
| `/mcp*` | MCP endpoint | mcp-hub:8080 |
| `/health*` | Health check | mcp-hub:8080 |
| `/status*` | Status API | mcp-hub:8080 |
| `/tools*` | Tool listing | mcp-hub:8080 |

Caddy automatically:

1. Obtains Let's Encrypt certificate for `$DOMAIN`
2. Redirects HTTP → HTTPS
3. Routes `/mcp`, `/health`, `/status`, `/tools` → `mcp-hub:8080`

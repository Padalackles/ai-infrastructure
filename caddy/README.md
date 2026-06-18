# Caddy Reverse Proxy

Auto HTTPS via Let's Encrypt. Proxies all traffic to `mcp-hub:8080`.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DOMAIN` | `localhost` | Public domain name |
| `CADDY_ACME_EMAIL` | (required) | Email for Let's Encrypt |

## Usage

```bash
export DOMAIN=raven-victor.click
export CADDY_ACME_EMAIL=admin@raven-victor.click
docker compose up -d caddy
```

Caddy automatically:
1. Obtains Let's Encrypt certificate for `$DOMAIN`
2. Redirects HTTP → HTTPS
3. Proxies `/mcp`, `/health`, `/status`, `/tools` → `mcp-hub:8080`

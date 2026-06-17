# Cloudflare Setup

## Prerequisites

- Domain added to Cloudflare
- Cloudflare API token with DNS edit permissions

## SSL/TLS Configuration

1. Go to Cloudflare Dashboard → SSL/TLS
2. Set encryption mode to **Full** or **Full (strict)**
3. Edge Certificates: ensure **Always Use HTTPS** is ON

## DNS Proxy

1. Go to DNS → Records
2. Ensure the A record has proxy enabled (orange cloud)
3. This hides the VPS IP and enables Cloudflare DDoS protection

## Cloudflare Tunnel (Optional)

For additional security (no open ports on VPS):

```bash
# Install cloudflared on VPS
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create mcp-hub-tunnel

# Configure DNS
cloudflared tunnel route dns mcp-hub-tunnel mcp-hub.example.com

# Run tunnel
cloudflared tunnel run mcp-hub-tunnel
```

## Docker Compose (Tunnel)

```yaml
cloudflared:
  image: cloudflare/cloudflared:latest
  container_name: ai-cloudflared
  restart: unless-stopped
  command: tunnel run
  environment:
    - TUNNEL_TOKEN=${CF_TUNNEL_TOKEN}
  networks:
    - ai-net
```

## Verification

```bash
curl -I https://mcp-hub.example.com/health
# HTTP/2 200
# cf-ray: ... (Cloudflare proxy header)
```

# Cloudflare Setup

## Prerequisites

- Domain added to Cloudflare
- Cloudflare API token with DNS edit permissions

## SSL/TLS Configuration

1. Go to Cloudflare Dashboard → SSL/TLS
2. Set encryption mode to **Full** or **Full (strict)**
   - **Full**: Encrypts end-to-end but tolerates self-signed origin certs
   - **Full (strict)**: Requires a valid CA-signed cert on the origin (Caddy provides this via Let's Encrypt)
3. Edge Certificates: ensure **Always Use HTTPS** is ON
4. Enable **Automatic HTTPS Rewrites** to fix mixed-content URLs

## HTTPS-Only Enforcement

1. Go to Cloudflare Dashboard → SSL/TLS → Edge Certificates
2. Turn ON **Always Use HTTPS** — redirects all HTTP to HTTPS
3. Optionally enable **HTTP Strict Transport Security (HSTS)**:
   - Status: ON
   - Max Age: 6 months (recommended starting point)
   - Include subdomains: ON
   - Preload: OFF (until verified stable)

These settings ensure:
- All HTTP requests are redirected to HTTPS (301)
- Browsers and clients cache the HTTPS redirect
- Mixed content is automatically upgraded

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

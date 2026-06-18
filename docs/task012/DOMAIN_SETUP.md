# Domain Setup

## Requirements

- A registered domain name (e.g., `raven-victor.click`)
- DNS managed by Cloudflare (recommended) or any provider

## DNS Configuration

### Option A: Cloudflare (Recommended)

1. Add domain to Cloudflare
2. Create an A record:
   ```
   Type: A
   Name: mcp-hub (or @ for root)
   Content: <VPS_IP_ADDRESS>
   Proxy: On (orange cloud)
   TTL: Auto
   ```

### Option B: Direct DNS

```
Type: A
Name: mcp-hub
Content: <VPS_IP_ADDRESS>
TTL: 3600
```

## Verification

```bash
# Check DNS resolution
dig raven-victor.click

# Should return your VPS IP
```

## Next Steps

After DNS propagates, proceed to `CLOUDFLARE_SETUP.md` (if using Cloudflare) or go directly to Caddy configuration.

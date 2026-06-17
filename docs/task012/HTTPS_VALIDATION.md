# HTTPS Validation

## Prerequisites

- Domain DNS pointing to VPS
- Caddy running in Docker Compose
- Ports 80 and 443 open on VPS firewall

## Validation Steps

### 1. HTTP → HTTPS Redirect

```bash
curl -I http://mcp-hub.example.com/health
# HTTP/1.1 308 Permanent Redirect
# Location: https://mcp-hub.example.com/health
```

### 2. HTTPS Health Check

```bash
curl https://mcp-hub.example.com/health
# {"status":"healthy","total_servers":3,...}
```

### 3. MCP Endpoint

```bash
curl -X POST https://mcp-hub.example.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
# {"jsonrpc":"2.0","id":1,"result":{...}}
```

### 4. Certificate Validity

```bash
curl -vI https://mcp-hub.example.com/health 2>&1 | grep "expire date"
# * expire date: <future date>
```

### 5. TLS Version

```bash
nmap --script ssl-enum-ciphers -p 443 mcp-hub.example.com
# TLS 1.3, strong ciphers
```

## Automated Script

```bash
./scripts/verify_https.sh
```

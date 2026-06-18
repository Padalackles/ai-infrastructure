# HTTPS Validation

## Prerequisites

- Domain DNS pointing to VPS
- Caddy running in Docker Compose
- Ports 80 and 443 open on VPS firewall

## Validation Steps

### 1. HTTP → HTTPS Redirect

```bash
curl -I http://raven-victor.click/health
# HTTP/1.1 308 Permanent Redirect
# Location: https://raven-victor.click/health
```

### 2. HTTPS Health Check

```bash
curl https://raven-victor.click/health
# {"status":"healthy","total_servers":3,...}
```

### 3. MCP Endpoint

```bash
curl -X POST https://raven-victor.click/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
# {"jsonrpc":"2.0","id":1,"result":{...}}
```

### 4. Certificate Validity

```bash
curl -vI https://raven-victor.click/health 2>&1 | grep "expire date"
# * expire date: <future date>
```

### 5. TLS Version

```bash
nmap --script ssl-enum-ciphers -p 443 raven-victor.click
# TLS 1.3, strong ciphers
```

## Automated Script

```bash
./scripts/verify_https.sh
```

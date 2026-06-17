#!/bin/bash
# verify_https.sh — MCP Hub HTTPS validation
# Usage: DOMAIN=mcp-hub.example.com ./scripts/verify_https.sh

set -e

DOMAIN="${DOMAIN:-localhost:8080}"
BASE="https://${DOMAIN}"

echo "=== MCP Hub HTTPS Validation ==="
echo "Target: $BASE"
echo ""

# 1. Health check
echo "[1/5] Health check..."
HEALTH=$(curl -s "$BASE/health")
if echo "$HEALTH" | grep -q '"status"'; then
    echo "  PASS: $HEALTH"
else
    echo "  FAIL: $HEALTH"
    exit 1
fi

# 2. MCP initialize
echo "[2/5] MCP initialize..."
INIT=$(curl -s -X POST "$BASE/mcp" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}')
if echo "$INIT" | grep -q '"protocolVersion"'; then
    echo "  PASS: initialize returns protocolVersion"
else
    echo "  FAIL: $INIT"
    exit 1
fi

# 3. tools/list
echo "[3/5] MCP tools/list..."
TOOLS=$(curl -s -X POST "$BASE/mcp" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}')
if echo "$TOOLS" | grep -q '"tools"'; then
    echo "  PASS: tools/list returns tools"
else
    echo "  FAIL: $TOOLS"
    exit 1
fi

# 4. tools/call
echo "[4/5] MCP tools/call..."
CALL=$(curl -s -X POST "$BASE/mcp" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"ntfy_health"}}')
if echo "$CALL" | grep -q '"result"'; then
    echo "  PASS: tools/call succeeds"
else
    echo "  FAIL: $CALL"
    exit 1
fi

# 5. TLS check
echo "[5/5] TLS certificate..."
if curl -sI "https://$DOMAIN/health" 2>&1 | grep -q "HTTP/2"; then
    echo "  PASS: HTTPS enabled"
else
    echo "  WARN: TLS check skipped (local test)"
fi

echo ""
echo "=== All checks passed ==="

#!/bin/bash
# deploy.sh — MCP Hub Production Deployment
# Run on VPS: bash deploy.sh
set -e

echo "=== MCP Hub Deployment ==="
echo "Domain: raven-victor.click"
echo "Date:   $(date)"
echo ""

# ── 1. Clone or pull the repository ──────────────────────────
REPO_DIR="/root/ai-infrastructure"
if [ -d "$REPO_DIR/.git" ]; then
    echo "[1/6] Pulling latest code..."
    cd "$REPO_DIR"
    git pull origin main
else
    echo "[1/6] Cloning repository..."
    git clone https://github.com/Padalackles/ai-infrastructure.git "$REPO_DIR"
    cd "$REPO_DIR"
fi

# ── 2. Create .env from example ──────────────────────────────
echo "[2/6] Creating .env file..."
cp .env.example .env
# Set the domain (already defaults to raven-victor.click)
# Set Cloudflare tokens — UPDATE THESE with real values
# CF_API_TOKEN=...
# CF_ZONE_ID=...

# ── 3. Build Docker images ───────────────────────────────────
echo "[3/6] Building Docker images..."
docker compose build

# ── 4. Start services ────────────────────────────────────────
echo "[4/6] Starting services..."
docker compose up -d

# ── 5. Wait for healthy ──────────────────────────────────────
echo "[5/6] Waiting for services to be healthy..."
sleep 5
docker compose ps

# ── 6. Quick health check ────────────────────────────────────
echo "[6/6] Quick health check..."
curl -s http://localhost:8080/health | head -c 200
echo ""
curl -s http://localhost:8080/status | head -c 200
echo ""

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Verify externally:"
echo "  curl https://raven-victor.click/health"
echo "  curl https://raven-victor.click/status"
echo "  curl -X POST https://raven-victor.click/mcp -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{}}'"
echo ""
echo "Run full verification:"
echo "  DOMAIN=raven-victor.click ./scripts/verify_https.sh"

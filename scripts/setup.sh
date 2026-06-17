#!/usr/bin/env bash
# ──────────────────────────────────────────
# ai-infrastructure — Setup Script
# ──────────────────────────────────────────
set -euo pipefail

echo "=== ai-infrastructure setup ==="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed."; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "Docker Compose v2 is required."; exit 1; }

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example — please edit it with your values."
else
    echo ".env already exists, skipping."
fi

# TODO: Cloudflare tunnel setup
# TODO: Caddy certificate bootstrap
# TODO: MCP Hub auth token generation

echo "Setup complete. Run: docker compose up -d"

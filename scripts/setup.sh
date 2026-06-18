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

# TODO: Cloudflare tunnel setup (optional — reserved)
# Caddy auto-obtains Let's Encrypt certs on first run — no manual bootstrap needed.
# Generate a secure auth token if not already present:
if ! grep -q "^MCP_HUB_AUTH_TOKEN=.\{32,\}" .env 2>/dev/null; then
    echo "MCP_HUB_AUTH_TOKEN=$(openssl rand -hex 32)" >> .env
    echo "Generated MCP_HUB_AUTH_TOKEN in .env"
fi

echo "Setup complete. Run: docker compose up -d"

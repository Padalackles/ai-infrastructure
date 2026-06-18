# ── MCP Hub — Runtime Environment ──────────
FROM python:3.12-slim

WORKDIR /app

# Install curl (required by Notification MCP / ntfy adapter)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY config.yaml .

# mcp_servers/ is mounted at runtime (see docker-compose.yml).
# The Hub auto-discovers servers from /app/mcp_servers.

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]

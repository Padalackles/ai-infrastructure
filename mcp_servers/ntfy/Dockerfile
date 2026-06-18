# ── ntfy MCP Server — Environment ──────────
# Reserved — ntfy is an external SaaS service (ntfy.sh).
# The Hub connects via mcp_servers/ntfy/adapter.py (Python HTTP bridge).
# This Dockerfile is reserved for future standalone containerization.
FROM python:3.12-alpine

WORKDIR /app
# Reserved — source code lives in sibling .py files (loaded by Hub discovery).
# COPY requirements.txt ./
# RUN pip install -r requirements.txt
# COPY . .

EXPOSE 8080
CMD ["echo", "ntfy MCP — adapter loaded by Hub, not containerized yet"]

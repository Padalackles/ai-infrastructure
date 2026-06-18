# ── Ombre MCP Server — Environment ─────────
# Reserved — Ombre is an external deployment at 45.76.169.98:8000.
# The Hub connects via mcp_servers/ombre/adapter.py (Python HTTP bridge).
# This Dockerfile is reserved for future standalone containerization.
FROM python:3.12-alpine

WORKDIR /app
# Reserved — source code lives in sibling .py files (loaded by Hub discovery).
# COPY requirements.txt ./
# RUN pip install -r requirements.txt
# COPY . .

EXPOSE 8080
CMD ["echo", "Ombre MCP — adapter loaded by Hub, not containerized yet"]

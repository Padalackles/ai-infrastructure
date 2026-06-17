# Ombre Brain

Personal AI infrastructure — MCP-first architecture.

## Directory Structure

```
project/
├── app/
│   ├── api/          # HTTP routes
│   ├── core/         # Configuration system
│   ├── mcp/          # MCP client, server, registry
│   ├── models/       # Pydantic schemas
│   ├── services/     # Business logic services
│   ├── scheduler/    # Task scheduler
│   ├── storage/      # File-based persistence
│   ├── utils/        # Utility helpers
│   └── main.py       # FastAPI entry point
├── config/           # YAML configuration
├── data/             # Runtime data storage
├── tests/            # Test suite
├── requirements.txt
└── .env.example
```

## Quick Start

```bash
cd project
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Health Check

```
GET http://localhost:8000/health → {"status": "ok"}
```

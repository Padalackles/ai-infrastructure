# Ombre MCP Server

Long-term AI memory and MCP orchestration platform — part of the
[AI Infrastructure](https://github.com/Padalackles/ai-infrastructure) project.

Ombre MCP Server provides persistent memory, conversation tracking, task scheduling,
and MCP Hub integration through a FastAPI application following the
**MCP First** architecture principle.

---

## Directory Structure

```
project/
├── app/
│   ├── api/              # HTTP routes (health, future REST endpoints)
│   ├── core/             # Configuration system (YAML-based singleton)
│   ├── mcp/              # MCP client, server base class, registry
│   ├── models/           # Pydantic domain models
│   ├── services/         # Business-logic service stubs
│   ├── scheduler/        # Task scheduler (deferred / recurring)
│   ├── storage/          # File-based JSON persistence
│   ├── utils/            # Utility helpers
│   └── main.py           # FastAPI application entry point
├── config/
│   ├── config.yaml       # Application configuration
│   └── prompts.yaml      # Prompt templates
├── data/                 # Runtime data (conversations, memories, tasks, cache)
├── tests/                # Test suite
├── requirements.txt
├── README.md
└── .env.example
```

---

## Quick Start

```bash
# 1. Enter the project directory
cd project

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the application
uvicorn app.main:app --reload
```

The server starts on `http://localhost:8000` by default.

---

## Health Check

```bash
curl http://localhost:8000/health
# → {"status":"ok"}
```

---

## Configuration

| File | Purpose |
|---|---|
| `config/config.yaml` | Server host/port, storage paths, MCP Hub URL, logging |
| `config/prompts.yaml` | Reusable prompt templates |
| `.env.example` | Environment variable overrides |

Override the config path at runtime:
```bash
CONFIG_PATH=/path/to/custom.yaml uvicorn app.main:app --reload
```

---

## MCP Integration

Ombre MCP Server integrates with the MCP Hub through three modules:

| Module | Role |
|---|---|
| `app/mcp/client.py` | Communicates with registered MCP servers |
| `app/mcp/server.py` | Base class for MCP service implementations |
| `app/mcp/registry.py` | Service registration, routing, lifecycle, and configuration |

---

## Models

| Model | Purpose |
|---|---|
| `Conversation` | Tracks an AI conversation thread |
| `Memory` | A persistent, keyed memory entry with tags |
| `Task` | A scheduled or tracked task with status |
| `UserConfig` | Per-user configuration and preferences |

---

## Development Status

This project foundation was established in **Task-002**. Business logic will be
implemented in **Task-003** and beyond.

See the repository [ROADMAP.md](../ROADMAP.md) for the overall project plan.

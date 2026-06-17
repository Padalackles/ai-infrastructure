"""
Ombre Brain — FastAPI Application Entry Point.

Ombre Brain is the long-term memory and MCP orchestration platform
for the personal AI infrastructure. It provides:

  - Persistent memory storage and retrieval
  - Conversation lifecycle management
  - Task scheduling and tracking
  - MCP Hub integration via the Model Context Protocol

Start with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.api.routes import router as api_router

app = FastAPI(
    title="Ombre Brain",
    description="Long-term AI memory and MCP orchestration platform.",
    version="0.1.0",
)

app.include_router(api_router)

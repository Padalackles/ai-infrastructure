"""Ombre Brain — FastAPI application entry point."""

from fastapi import FastAPI

from app.api.routes import router as health_router

app = FastAPI(
    title="Ombre Brain",
    description="Personal AI infrastructure — MCP-first architecture.",
    version="0.1.0",
)

app.include_router(health_router)

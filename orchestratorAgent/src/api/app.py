"""FastAPI application factory."""

from fastapi import FastAPI

from src.api.routes import health, invocations


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Orchestrator Agent",
        description="Intelligent routing service using LangGraph for workflow orchestration",
        version="1.0.0",
    )

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(invocations.router, tags=["Invocations"])

    return app

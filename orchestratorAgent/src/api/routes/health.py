"""Health check routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
def ping():
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/health")
def health():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "service": "orchestrator-agent",
    }

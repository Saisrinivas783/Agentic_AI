"""FastAPI dependency injection."""

from functools import lru_cache

from src.graph.orchestrator import OrchestratorAgent


@lru_cache
def get_orchestrator() -> OrchestratorAgent:
    """
    Get singleton OrchestratorAgent instance.

    Uses lru_cache to ensure only one instance is created.
    """
    return OrchestratorAgent(
        registry_path="src/tools/definitions/tools.yaml"
    )

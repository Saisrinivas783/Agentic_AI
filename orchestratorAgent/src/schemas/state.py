"""Orchestrator workflow state - pure data container."""

from typing import Any

from pydantic import BaseModel, Field

from src.schemas.api import InvocationContext
from src.schemas.tools import SelectedTool, ToolResult
from src.schemas.registry import ToolDefinition


class OrchestratorState(BaseModel):
    """
    LangGraph state for the orchestrator workflow.

    This is a pure data container - no business logic.
    State flows through nodes which transform it.
    """

    # Input (from request)
    query: str
    session_id: str
    context: InvocationContext | None = None

    # Tool registry (loaded at startup)
    registry: dict[str, ToolDefinition] = Field(default_factory=dict)

    # Intent analysis result (from analyzer node)
    selected_tool: SelectedTool | None = None
    direct_response: str | None = None  # For conversational queries

    # Tool execution result (from executor node)
    tool_result: ToolResult | None = None

    # Final output
    final_answer: str | None = None

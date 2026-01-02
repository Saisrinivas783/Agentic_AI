"""Tool-related schemas for the orchestrator workflow."""

from typing import Any

from pydantic import BaseModel, Field


class SelectedTool(BaseModel):
    """Result of LLM tool selection."""

    tool_name: str = Field(..., description="Name of the selected tool or 'NO_TOOL'")
    confidence: float = Field(..., ge=0.0, le=10.0, description="Confidence score (0-10)")
    reasoning: str = Field("", description="Explanation for selection")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Parameters for tool execution")


class ToolResult(BaseModel):
    """Result from tool execution."""

    tool_name: str
    success: bool = True
    response: Any = None
    error: str | None = None

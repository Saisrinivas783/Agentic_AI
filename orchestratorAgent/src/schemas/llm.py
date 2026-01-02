"""LLM structured output schemas."""

from pydantic import BaseModel, Field


class ToolSelectionOutput(BaseModel):
    """Structured output format for LLM tool selection."""

    selected_tool: str = Field(
        description="Name of the selected tool (e.g., 'IBTAgent', 'ClaimsAgent'), 'NO_TOOL' if no suitable tool, or 'CONVERSATIONAL' for greetings/small talk"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=10.0,
        description="Confidence score between 0 and 10"
    )
    reasoning: str = Field(
        description="Detailed explanation for selection"
    )
    direct_response: str | None = Field(
        default=None,
        description="For CONVERSATIONAL queries, provide a friendly direct response here"
    )

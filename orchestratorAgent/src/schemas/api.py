"""API request/response schemas matching the Orchestrator Agent Technical Specification."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# Base Models
# =============================================================================

class BaseWorkflowRequest(BaseModel):
    """Base model for all workflow requests."""

    session_id: str = Field(..., alias="sessionId", description="Conversation session ID")

    class Config:
        populate_by_name = True


class BaseWorkflowResponse(BaseModel):
    """Base model for all workflow responses."""

    success: bool = True
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: float = 0.0


# =============================================================================
# Invocation Context (from DXAIService)
# =============================================================================

class InvocationContext(BaseModel):
    """Additional context information passed from DXAIService."""

    userName: str = Field(..., description="User identifier")
    userType: str = Field(..., description="User type (member, provider, etc.)")
    source: str = Field(..., description="Request origin (DXAIService)")
    promptId: str = Field(..., description="Prompt identifier")


# =============================================================================
# Invocation Request/Response (POST /invocations)
# =============================================================================

class InvocationRequest(BaseWorkflowRequest):
    """
    Request body for POST /invocations endpoint.
    Matches DXAIService InvokeAgent Request format.
    """

    user_prompt: str = Field(..., alias="userPrompt", description="User's question or request")
    context: InvocationContext | None = Field(None, description="Additional context information")


class SelectedToolResponse(BaseModel):
    """Selected tool information in response."""

    tool_name: str = Field(..., alias="toolName")
    confidence: float = Field(..., ge=0.0, le=10.0)
    reasoning: str = ""

    class Config:
        populate_by_name = True


class InvocationResponse(BaseWorkflowResponse):
    """
    Response body for POST /invocations endpoint.
    """

    session_id: str = Field(..., alias="sessionId")
    selected_tool: SelectedToolResponse | None = Field(None, alias="selectedTool")
    confidence: float = Field(0.0, ge=0.0, le=10.0)
    response_text: str = Field("", alias="responseText")

    class Config:
        populate_by_name = True


# =============================================================================
# Health Check (GET /ping)
# =============================================================================

class HealthResponse(BaseModel):
    """Response for GET /ping endpoint."""

    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from schemas.api import InvocationContext
from .tools import SelectedTools, ToolResult
from schemas.registry import ToolDefinition

class OrchestratorState(BaseModel):
    query: str
    session_id: str
    context: Optional[InvocationContext] = None

    intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    direct_response: Optional[str] = None
    registry: Dict[str, ToolDefinition] = Field(default_factory=dict)

    selected_tools: List[SelectedTools] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)

    final_answer: Optional[str] = None

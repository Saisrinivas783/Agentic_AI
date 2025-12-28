from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class SelectedTools(BaseModel):
    tool_name: str
    reason: str
    confidence: float
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ToolResult(BaseModel):
    tool_name: str
    ok: bool
    raw_response: Any = None
    error: Optional[str] = None
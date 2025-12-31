from typing import List
from pydantic import BaseModel
from .tools import ToolResult, SelectedTools


class InvocationContext(BaseModel):
    userName: str
    userType: str
    source: str
    promptId: str


class InvocationRequest(BaseModel):
    userPrompt: str
    sessionId: str
    context: InvocationContext


class InvocationResponse(BaseModel):
    sessionId: str
    selectedTool: List[SelectedTools]
    confidence: float
    responseText: str

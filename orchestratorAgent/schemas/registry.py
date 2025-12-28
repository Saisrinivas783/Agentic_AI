from typing import List, Optional
from pydantic import BaseModel, HttpUrl


class ToolExample(BaseModel):
    prompt: str
    reasoning: str


class ToolParameters(BaseModel):
    required: List[str]
    optional: Optional[List[str]] = []


class ToolDefinition(BaseModel):
    name: str
    description: str
    endpoint: HttpUrl
    capabilities: List[str]
    parameters: ToolParameters
    examples: Optional[List[ToolExample]] = []
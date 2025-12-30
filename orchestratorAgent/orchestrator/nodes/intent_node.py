import logging
from schemas.state import OrchestratorState
from pydantic import BaseModel, Field
from typing import Optional
from schemas.tools import SelectedTools
from langchain_core.messages import SystemMessage, HumanMessage

from llm.bedrock_llm_client import get_chat_models

logger = logging.getLogger(__name__)


class ToolSelectionFormat(BaseModel):
    """Structured output format for LLM tool selection"""
    selected_tool: str = Field(
        description="Name of the selected tool (e.g., 'IBTAgent', 'ClaimsAgent'), 'NO_TOOL' if no suitable tool, or 'CONVERSATIONAL' for greetings/small talk"
    )
    confidence_score: float = Field(
        description="Confidence score between 0 and 10",
        ge=0.0,
        le=10.0
    )
    reasoning: str = Field(
        description="Detailed explanation for selection"
    )
    direct_response: Optional[str] = Field(
        default=None,
        description="For CONVERSATIONAL queries, provide a friendly direct response here"
    )


def build_system_prompt(tools_context: str) -> str:
    return f"""You are an intelligent tool selection agent for a healthcare insurance system.

Available tools and their capabilities:
{tools_context}

Your task is to:
1. Analyze the user's query to understand their intent
2. Classify the query type:
   - TOOL REQUIRED: Route to appropriate tool (IBTAgent, ClaimsAgent, etc.)
   - CONVERSATIONAL: Simple greeting, thank you, goodbye, small talk
   - OUT OF SCOPE: Query unrelated to insurance/healthcare

**CONVERSATIONAL QUERIES:**
For greetings (hello, hi, hey), thank you messages, or goodbyes:
- Set selected_tool to "CONVERSATIONAL"
- Set confidence_score to 10.0
- Provide a friendly direct_response

Examples:
- "Hello" → CONVERSATIONAL with response: "Hello! I'm here to help you with your insurance benefits and claims. What can I assist you with today?"
- "Thank you" → CONVERSATIONAL with response: "You're welcome! Let me know if you need anything else."

**TOOL ROUTING:**
- Only route to tools for actual insurance questions
- If confidence < 7.0, select "NO_TOOL"
- If query is out of scope, select "NO_TOOL"

Return:
- selected_tool: Tool name, "CONVERSATIONAL", or "NO_TOOL"
- confidence_score: 0-10
- reasoning: Your decision explanation
- direct_response: (Only for CONVERSATIONAL) Your friendly response
"""


def build_tools_context(registry: dict) -> str:
    """Format registry tools into readable context for LLM"""
    if not registry:
        return "No tools available"
    
    tools_list = []
    for tool_name, tool_def in registry.items():
        tool_info = f"""
Tool: {tool_name}
Description: {tool_def.description}
Endpoint: {tool_def.endpoint}
Capabilities: {', '.join(tool_def.capabilities)}
Parameters (Required): {', '.join(tool_def.parameters.required)}
Parameters (Optional): {', '.join(tool_def.parameters.optional) if tool_def.parameters.optional else 'None'}
"""
        tools_list.append(tool_info)
    
    return "\n".join(tools_list)


def intent_node(state: OrchestratorState) -> OrchestratorState:
    """
    Intent detection node that routes user queries to appropriate tools
    """
    user_query = state.query
    logger.info(f"Processing intent for query: {user_query}")

    chat_models = get_chat_models()
    llm = chat_models.get_model()
    logger.info(f"Using model: {llm.model_id}")

    # Build tools context from registry
    tools_context = build_tools_context(state.registry)
    logger.info(f"Registry contains {len(state.registry)} tools")

    SYSTEM_PROMPT = build_system_prompt(tools_context)

    # Use with_structured_output on the LLM
    structured_llm = llm.with_structured_output(ToolSelectionFormat)
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_query)
    ]

    response = structured_llm.invoke(messages)

    # Response is already parsed as ToolSelectionFormat Pydantic model
    parsed: ToolSelectionFormat = response

    # 🔽 DEBUG LOGGING
    logger.info("========== INTENT NODE DEBUG ==========")
    logger.info(f"User Query: {user_query}")
    logger.info(f"Selected Tool: {parsed.selected_tool}")
    logger.info(f"Confidence Score: {parsed.confidence_score}")
    logger.info(f"Reasoning: {parsed.reasoning}")
    if parsed.direct_response:
        logger.info(f"Direct Response: {parsed.direct_response}")
    logger.info("========================================")

    # Update state with intent results
    state.intent = parsed.reasoning
    state.intent_confidence = float(parsed.confidence_score)
    state.direct_response = parsed.direct_response
    selected_tool_obj = SelectedTools(
            tool_name=parsed.selected_tool,
            reason=parsed.reasoning,
            confidence=float(parsed.confidence_score),
            parameters={}  # Add parameters if needed
        )
    state.selected_tools = [selected_tool_obj]
    logger.info(f"State updated - Intent: {state.intent}, Confidence: {state.intent_confidence}")
    
    return state
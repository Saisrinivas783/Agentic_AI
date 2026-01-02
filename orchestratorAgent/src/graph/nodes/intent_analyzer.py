"""Intent analyzer node - LLM-based tool selection."""

import logging

from langchain_core.messages import SystemMessage, HumanMessage

from src.schemas.state import OrchestratorState
from src.schemas.tools import SelectedTool
from src.schemas.llm import ToolSelectionOutput
from src.llm.client import get_chat_models
from src.llm.prompts.intent_analyzer import build_tool_selection_prompt, build_tools_context

logger = logging.getLogger(__name__)


def intent_node(state: OrchestratorState) -> OrchestratorState:
    """
    Intent detection node that routes user queries to appropriate tools.

    Uses LLM with structured output to analyze query and select tool.
    """
    user_query = state.query
    logger.info(f"Processing intent for query: {user_query}")

    # Get LLM
    chat_models = get_chat_models()
    llm = chat_models.get_model()
    logger.info(f"Using model: {llm.model_id}")

    # Build prompt with tools context
    tools_context = build_tools_context(state.registry)
    system_prompt = build_tool_selection_prompt(tools_context)
    logger.info(f"Registry contains {len(state.registry)} tools")

    # Use structured output
    structured_llm = llm.with_structured_output(ToolSelectionOutput)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_query)
    ]

    parsed: ToolSelectionOutput = structured_llm.invoke(messages)

    logger.info(f"Intent analysis: tool={parsed.selected_tool}, confidence={parsed.confidence_score}, reasoning={parsed.reasoning}")

    # Update state with intent results
    state.selected_tool = SelectedTool(
        tool_name=parsed.selected_tool,
        confidence=parsed.confidence_score,
        reasoning=parsed.reasoning,
    )
    state.direct_response = parsed.direct_response

    logger.info(f"State updated - Tool: {state.selected_tool.tool_name}, Confidence: {state.selected_tool.confidence}")

    return state
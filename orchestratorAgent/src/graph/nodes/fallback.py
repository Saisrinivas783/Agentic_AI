"""Fallback node - handles non-tool responses."""

import logging

from src.schemas.state import OrchestratorState

logger = logging.getLogger(__name__)

# Pre-defined response messages (placeholder text per spec)
FALLBACK_MESSAGES = {
    "no_tool_found": "I'm sorry, I couldn't find the right resource to help with your question. Please try rephrasing your query or contact our support team for assistance.",
    "low_confidence": "I'm not entirely sure I understand your question. Could you please provide more details or rephrase your request?",
    "service_unavailable": "I'm currently experiencing technical difficulties. Please try again in a few moments or contact support if the issue persists.",
}


def fallback_node(state: OrchestratorState) -> OrchestratorState:
    """
    Handles fallback scenarios including conversational queries.

    Routes here when:
    - CONVERSATIONAL query (greetings, thanks)
    - NO_TOOL selected
    - Low confidence score
    """
    if not state.selected_tool:
        logger.info("Fallback: No tool in state")
        state.final_answer = FALLBACK_MESSAGES["service_unavailable"]
        return state

    tool_name = state.selected_tool.tool_name
    confidence = state.selected_tool.confidence

    logger.info(f"Fallback - Tool: {tool_name}, Confidence: {confidence}")

    # Use LLM's direct response for conversational queries
    if tool_name == "CONVERSATIONAL" and state.direct_response:
        state.final_answer = state.direct_response
        logger.info("Fallback: Conversational response")

    # No tool match
    elif tool_name == "NO_TOOL":
        state.final_answer = FALLBACK_MESSAGES["no_tool_found"]
        logger.info("Fallback: No tool match")

    # Low confidence
    elif confidence < 7.0:
        state.final_answer = FALLBACK_MESSAGES["low_confidence"]
        logger.info(f"Fallback: Low confidence ({confidence})")

    # Generic fallback
    else:
        state.final_answer = FALLBACK_MESSAGES["service_unavailable"]
        logger.info("Fallback: Generic")

    return state
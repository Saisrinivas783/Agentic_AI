"""Confidence-based routing node."""

import logging

from src.schemas.state import OrchestratorState

logger = logging.getLogger(__name__)

# Minimum confidence required for tool execution
CONFIDENCE_THRESHOLD = 7.0


def guard_rails_router(state: OrchestratorState) -> str:
    """
    Routes based on tool selection confidence.

    Routes to:
    - "execute_tool": Confidence >= 7.0 and valid tool selected
    - "use_fallback": NO_TOOL, low confidence, or CONVERSATIONAL
    """
    if not state.selected_tool:
        logger.info("Guard Rails: No tool selected → use_fallback")
        return "use_fallback"

    tool_name = state.selected_tool.tool_name
    confidence = state.selected_tool.confidence

    logger.info(f"Guard Rails - Tool: {tool_name}, Confidence: {confidence}")

    # Handle conversational queries (greetings, thanks, goodbye)
    if tool_name == "CONVERSATIONAL":
        logger.info("Guard Rails: Conversational query → use_fallback")
        return "use_fallback"

    # Check if tool was found
    if tool_name == "NO_TOOL":
        logger.info("Guard Rails: No tool match → use_fallback")
        return "use_fallback"

    # Check confidence threshold
    if confidence < CONFIDENCE_THRESHOLD:
        logger.info(f"Guard Rails: Confidence {confidence} < {CONFIDENCE_THRESHOLD} → use_fallback")
        return "use_fallback"

    # Route to tool executor
    logger.info(f"Guard Rails: PASSED → execute_tool ({tool_name})")
    return "execute_tool"
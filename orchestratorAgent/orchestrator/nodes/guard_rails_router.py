from schemas.state import OrchestratorState
import logging

logger = logging.getLogger(__name__)

def guard_rails_router(state: OrchestratorState) -> str:
    """
    Routes based on tool selection from intent_node
    
    Routes to:
    - "execute_tool": For IBTAgent, ClaimsAgent, etc.
    - "use_fallback": For NO_TOOL, low confidence, or CONVERSATIONAL
    """
    confidence = state.intent_confidence or 0.0
    
    # selected_tools is a List, get the first one
    if not state.selected_tools:
        logger.info("Guard Rails: No tools selected")
        return "use_fallback"
    
    selected_tool = state.selected_tools[0].tool_name
    
    logger.info(f"Guard Rails - Tool: {selected_tool}, Confidence: {confidence}")
    
    # Handle conversational queries (greetings, thanks, goodbye)
    if selected_tool == "CONVERSATIONAL":
        logger.info("Guard Rails: Conversational query detected → use_fallback")
        return "use_fallback"
    
    # Check confidence threshold for tool routing
    if confidence < 7.0:
        logger.info(f"Guard Rails: FAILED - Confidence {confidence} below threshold → use_fallback")
        return "use_fallback"
    
    # Check if tool was found
    if selected_tool == "NO_TOOL":
        logger.info("Guard Rails: FAILED - No tool match → use_fallback")
        return "use_fallback"
    
    # Route to tool executor
    logger.info(f"Guard Rails: PASSED - Routing to execute_tool for '{selected_tool}'")
    return "execute_tool"
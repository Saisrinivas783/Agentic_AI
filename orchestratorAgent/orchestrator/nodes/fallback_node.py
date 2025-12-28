from schemas.state import OrchestratorState
import logging

logger = logging.getLogger(__name__)

def fallback_node(state: OrchestratorState) -> OrchestratorState:
    """
    Handles fallback scenarios including conversational queries
    """
    # Get selected tool from selected_tools list
    selected_tool = state.selected_tools[0].tool_name
    confidence = state.intent_confidence or 0.0
    direct_response = state.direct_response
    
    logger.info(f"Fallback Node - Tool: {selected_tool}, Confidence: {confidence}")
    
    # Use LLM's direct response for conversational queries
    if selected_tool == "CONVERSATIONAL" and direct_response:
        message = direct_response
        logger.info(f"Fallback: Conversational response - {message}")
    
    # Low confidence
    elif confidence < 7.0 and confidence > 0:
        message = "I'm not entirely sure I understand your question. Could you please provide more details?"
        logger.info(f"Fallback: Low confidence ({confidence})")
    
    # No tool match
    elif selected_tool == "NO_TOOL":
        message = "I'm sorry, I couldn't find the right resource to help with your question. Please try rephrasing or contact support."
        logger.info(f"Fallback: No tool match")
    
    # Generic fallback
    else:
        message = "I'm currently experiencing technical difficulties. Please try again shortly."
        logger.info(f"Fallback: Generic fallback")
    
    state.final_answer = message
    
    return state
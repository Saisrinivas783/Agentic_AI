import logging
from datetime import datetime

from src.schemas.state import OrchestratorState
from src.schemas.tools import ToolResult

logger = logging.getLogger(__name__)


def tool_executor_node(state: OrchestratorState) -> OrchestratorState:
    """
    Executes the selected tool and captures results
    Mock implementation for testing
    """
    
    if not state.selected_tools:
        logger.error("Tool Executor: No tools selected")
        state.final_answer = "Error: No tool selected for execution"
        return state
    
    selected_tool = state.selected_tools[0].tool_name
    confidence = state.selected_tools[0].confidence
    
    logger.info(f"Tool Executor: Executing tool '{selected_tool}'")
    logger.info(f"  User Query: {state.query}")
    logger.info(f"  Confidence: {confidence}")
    
    # Mock tool responses
    mock_responses = {
        "IBTAgent": {
            "ok": True,
            "response": "✅ IBT Agent Response: Your insurance benefits include coverage for preventive care, hospitalization, and emergency services. Your current deductible is $1,500 with 80/20 coinsurance after deductible."
        },
        "ClaimsAgent": {
            "ok": True,
            "response": "✅ Claims Agent Response: Your recent claim (Claim #CLM-2024-12345) has been processed and approved for $2,500. Payment will be deposited within 5-7 business days."
        },
        "SupportAgent": {
            "ok": True,
            "response": "✅ Support Agent Response: We're here to help! Our support team is available 24/7. You can reach us via phone, email, or live chat."
        },
        "DocumentAgent": {
            "ok": True,
            "response": "✅ Document Agent Response: Your insurance documents have been retrieved. You can download your policy summary, coverage details, and member ID card from your account."
        }
    }
    
    # Get mock response or default
    if selected_tool in mock_responses:
        result = mock_responses[selected_tool]
    else:
        result = {
            "ok": True,
            "response": f"✅ {selected_tool} Response: Tool executed successfully for your query: '{state.query}'"
        }
    
    # Create ToolResult object
    tool_result = ToolResult(
        tool_name=selected_tool,
        ok=result["ok"],
        raw_response=result["response"],
        error=None if result["ok"] else "Tool execution failed"
    )
    
    state.tool_results = [tool_result]
    state.final_answer = result["response"]
    
    logger.info(f"Tool Executor: ✅ Tool '{selected_tool}' executed successfully")
    logger.info(f"  Response: {result['response'][:100]}...")
    
    return state
"""Tool executor node - executes selected tool and captures results."""

import logging

from src.schemas.state import OrchestratorState
from src.schemas.tools import ToolResult

logger = logging.getLogger(__name__)

# Mock responses for testing (will be replaced with real HTTP calls)
MOCK_RESPONSES = {
    "IBTAgent": "Your insurance benefits include coverage for preventive care, hospitalization, and emergency services. Your current deductible is $1,500 with 80/20 coinsurance after deductible.",
    "ClaimsAgent": "Your recent claim (Claim #CLM-2024-12345) has been processed and approved for $2,500. Payment will be deposited within 5-7 business days.",
    "SupportAgent": "We're here to help! Our support team is available 24/7. You can reach us via phone, email, or live chat.",
    "DocumentAgent": "Your insurance documents have been retrieved. You can download your policy summary, coverage details, and member ID card from your account.",
}


def tool_executor_node(state: OrchestratorState) -> OrchestratorState:
    """
    Executes the selected tool and captures results.

    Currently uses mock responses - will be replaced with real HTTP calls.
    """
    if not state.selected_tool:
        logger.error("Tool Executor: No tool selected")
        state.final_answer = "Error: No tool selected for execution"
        return state

    tool_name = state.selected_tool.tool_name

    logger.info(f"Tool Executor: Executing '{tool_name}'")
    logger.info(f"  Query: {state.query}")
    logger.info(f"  Confidence: {state.selected_tool.confidence}")

    # Get mock response or default
    response_text = MOCK_RESPONSES.get(
        tool_name,
        f"Tool '{tool_name}' executed successfully for: {state.query}"
    )

    # Create ToolResult
    state.tool_result = ToolResult(
        tool_name=tool_name,
        success=True,
        response=response_text,
    )
    state.final_answer = response_text

    logger.info(f"Tool Executor: ✓ '{tool_name}' completed")

    return state
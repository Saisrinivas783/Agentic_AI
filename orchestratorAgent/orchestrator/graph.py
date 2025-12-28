from langgraph.graph import StateGraph, START, END
from schemas.state import OrchestratorState
from orchestrator.nodes.intent_node import intent_node
from orchestrator.nodes.tool_exec import tool_executor_node
from orchestrator.nodes.guard_rails_router import guard_rails_router
from orchestrator.nodes.fallback_node import fallback_node
from orchestrator.nodes.response_compose import response_compose_node

def build_graph():
    workflow = StateGraph(OrchestratorState)

    # Add nodes
    workflow.add_node("analyzer", intent_node)  # LLM: intent analysis + tool selection
    workflow.add_node("tool_executor", tool_executor_node)  # Calls selected tool API
    workflow.add_node("fallback", fallback_node)  # Returns generic messages

    # # Set entry point
    workflow.set_entry_point("analyzer")

    # Add conditional routing from analyzer (guard rails logic)
    workflow.add_conditional_edges(
        "analyzer",
        guard_rails_router,  # Function that checks confidence >= 7.0 and tool availability
        {
            "execute_tool": "tool_executor",  # High confidence, tool found
            "use_fallback": "fallback"  # Low confidence or no tool match
        }
    )

    # Both tool_executor and fallback end the workflow
    workflow.add_edge("tool_executor", END)
    workflow.add_edge("fallback", END)

    return workflow.compile()
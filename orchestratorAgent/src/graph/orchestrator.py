"""Orchestrator agent - main entry point for workflow execution."""

import logging
import time
from typing import Any

from src.schemas.api import (
    InvocationRequest,
    InvocationResponse,
    SelectedToolResponse,
)
from src.schemas.state import OrchestratorState
from src.tools.registry import load_tools_from_yaml
from src.graph.workflow import build_graph

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Main orchestrator that runs the LangGraph workflow."""

    def __init__(self, registry_path: str = "src/tools/definitions/tools.yaml"):
        self.registry_path = registry_path
        self.registry = load_tools_from_yaml(registry_path)
        self.graph_app = build_graph()
        logger.info(f"OrchestratorAgent initialized with {len(self.registry)} tools")

    def handle_invocation(self, payload: InvocationRequest) -> InvocationResponse:
        """Execute the workflow and return structured response."""
        start_time = time.time()

        # Build initial state
        state = OrchestratorState(
            query=payload.user_prompt,
            session_id=payload.session_id,
            context=payload.context,
            registry=self.registry,
        )

        # Run the graph
        out_dict: dict[str, Any] = self.graph_app.invoke(state.model_dump())
        out_state = OrchestratorState(**out_dict)

        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000

        # Build response
        selected_tool_response = None
        confidence = 0.0

        if out_state.selected_tool:
            selected_tool_response = SelectedToolResponse(
                toolName=out_state.selected_tool.tool_name,
                confidence=out_state.selected_tool.confidence,
                reasoning=out_state.selected_tool.reasoning,
            )
            confidence = out_state.selected_tool.confidence

        return InvocationResponse(
            sessionId=payload.session_id,
            selectedTool=selected_tool_response,
            confidence=confidence,
            responseText=out_state.final_answer or "",
            success=True,
            execution_time_ms=execution_time_ms,
        )

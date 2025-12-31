from typing import Dict, Any

from src.schemas.api import InvocationRequest, InvocationResponse
from src.schemas.state import OrchestratorState
from src.tools.registry import load_tools_from_yaml
from src.graph.workflow import build_graph


class OrchestratorAgent:
    def __init__(self, registry_path: str = "src/tools/definitions/tools.yaml"):
        self.registry_path = registry_path
        self.registry =load_tools_from_yaml(registry_path)
        self.graph_app = build_graph() 

    def handle_invocation(self, payload: InvocationRequest) -> InvocationResponse:
        state = OrchestratorState(
            query=payload.userPrompt,
            session_id=payload.sessionId,
            context=payload.context, 
            registry=self.registry,
        )

        out_dict: Dict[str, Any] = self.graph_app.invoke(state.model_dump())
        out_state = OrchestratorState(**out_dict)


        
        return InvocationResponse(
            sessionId=payload.sessionId,
            selectedTool=out_state.selected_tools,
            confidence=out_state.intent_confidence,
            responseText=out_state.final_answer,
        )

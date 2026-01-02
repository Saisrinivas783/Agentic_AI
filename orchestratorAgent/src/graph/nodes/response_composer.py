from src.schemas.state import OrchestratorState


def response_compose_node(state: OrchestratorState) -> OrchestratorState:
    state.final_answer = state.intent or state.final_answer or ""
    return state

from typing import Any, Dict

def ibt_stub_execute(payload: Dict[str, Any]) -> Dict[str, Any]:
    user_prompt = payload.get("userPrompt", "")
    return {
        "tool": "IBTAgent",
        "status": "success",
        "answer": f"[IBT STUB] For your question: '{user_prompt}', coverage depends on plan. Please check policy details. (stub)"
    }

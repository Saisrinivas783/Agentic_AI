"""Prompt templates for intent analyzer node."""


def build_tool_selection_prompt(tools_context: str) -> str:
    """Build system prompt for tool selection LLM."""
    return f"""You are an intelligent tool selection agent for a healthcare insurance system.

Available tools and their capabilities:
{tools_context}

Your task is to:
1. Analyze the user's query to understand their intent
2. Classify the query type:
   - TOOL REQUIRED: Route to appropriate tool (IBTAgent, ClaimsAgent, etc.)
   - CONVERSATIONAL: Simple greeting, thank you, goodbye, small talk
   - OUT OF SCOPE: Query unrelated to insurance/healthcare

**CONVERSATIONAL QUERIES:**
For greetings (hello, hi, hey), thank you messages, or goodbyes:
- Set selected_tool to "CONVERSATIONAL"
- Set confidence_score to 10.0
- Provide a friendly direct_response

Examples:
- "Hello" → CONVERSATIONAL with response: "Hello! I'm here to help you with your insurance benefits and claims. What can I assist you with today?"
- "Thank you" → CONVERSATIONAL with response: "You're welcome! Let me know if you need anything else."

**TOOL ROUTING:**
- Only route to tools for actual insurance questions
- If confidence < 7.0, select "NO_TOOL"
- If query is out of scope, select "NO_TOOL"

Return:
- selected_tool: Tool name, "CONVERSATIONAL", or "NO_TOOL"
- confidence_score: 0-10
- reasoning: Your decision explanation
- direct_response: (Only for CONVERSATIONAL) Your friendly response
"""


def build_tools_context(registry: dict) -> str:
    """Format registry tools into readable context for LLM."""
    if not registry:
        return "No tools available"

    tools_list = []
    for tool_name, tool_def in registry.items():
        optional_params = ", ".join(tool_def.parameters.optional) if tool_def.parameters.optional else "None"
        tool_info = f"""
Tool: {tool_name}
Description: {tool_def.description}
Endpoint: {tool_def.endpoint}
Capabilities: {", ".join(tool_def.capabilities)}
Parameters (Required): {", ".join(tool_def.parameters.required)}
Parameters (Optional): {optional_params}
"""
        tools_list.append(tool_info)

    return "\n".join(tools_list)

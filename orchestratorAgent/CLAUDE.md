# CLAUDE.md - Orchestrator Agent Development Guide

## Project Overview

The Orchestrator Agent is a Python-based intelligent routing service using LangGraph for workflow orchestration. It dynamically selects and invokes tools based on user prompts using LLM-powered decision making.

**Current Release:** PI2 (IBTAgent only)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (create .env file)
cp .env.example .env  # Edit with your AWS credentials

# Run the server
uvicorn app:app --reload --port 8000

# Test health check
curl http://localhost:8000/ping

# Test invocation
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{"userPrompt": "What are my dental benefits?", "sessionId": "sess-001", "context": {"userName": "testuser", "userType": "member", "source": "DXAIService", "promptId": "p-123"}}'
```

## Project Structure

```
orchestratorAgent/
├── app.py                      # FastAPI entry point (/ping, /invocations)
├── agent.py                    # OrchestratorAgent class - orchestrates the workflow
├── config.py                   # Environment configuration (Bedrock, AWS)
├── requirements.txt            # Python dependencies
├── requests.http               # HTTP test requests (VS Code REST Client)
│
├── orchestrator/
│   ├── graph.py                # LangGraph workflow definition
│   └── nodes/
│       ├── intent_node.py      # LLM-based intent detection & tool selection
│       ├── guard_rails_router.py # Confidence threshold routing (>= 7.0)
│       ├── tool_exec.py        # Tool execution (currently mock)
│       ├── fallback_node.py    # Generic fallback responses
│       └── response_compose.py # Response formatting (not used in current graph)
│
├── llm/
│   └── bedrock_llm_client.py   # AWS Bedrock LLM wrapper with structured output
│
├── registry/
│   ├── loader.py               # YAML tool config loader
│   └── tools-config.yaml       # Tool definitions (IBTAgent for PI2)
│
├── schemas/
│   ├── api.py                  # Request/Response Pydantic models
│   ├── state.py                # OrchestratorState (LangGraph state)
│   ├── registry.py             # ToolDefinition schema
│   └── tools.py                # SelectedTools, ToolResult schemas
│
└── tools/
    └── ibt_stub.py             # IBT tool stub (not currently used)
```

## Architecture

### LangGraph Workflow

```
START
  │
  ▼
┌─────────────┐
│  analyzer   │  ◄── intent_node.py (LLM tool selection)
│ (intent)    │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ guard_rails      │  ◄── guard_rails_router.py (confidence >= 7.0?)
│ (conditional)    │
└───────┬──────────┘
        │
   ┌────┴────┐
   ▼         ▼
execute   use_fallback
 _tool
   │         │
   ▼         ▼
┌──────┐  ┌──────────┐
│tool_ │  │ fallback │
│exec  │  │  _node   │
└──┬───┘  └────┬─────┘
   │           │
   └─────┬─────┘
         ▼
        END
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **Entry Point** | `app.py` | FastAPI server with `/ping` and `/invocations` |
| **Agent** | `agent.py` | Orchestrates workflow execution |
| **Graph** | `orchestrator/graph.py` | LangGraph state machine definition |
| **Intent Node** | `orchestrator/nodes/intent_node.py` | LLM analyzes query, selects tool |
| **Guard Rails** | `orchestrator/nodes/guard_rails_router.py` | Routes based on confidence |
| **Tool Executor** | `orchestrator/nodes/tool_exec.py` | Executes selected tool (mock) |
| **Fallback** | `orchestrator/nodes/fallback_node.py` | Returns generic messages |
| **LLM Client** | `llm/bedrock_llm_client.py` | AWS Bedrock wrapper |

## Environment Variables

Create a `.env` file in the project root:

```env
# AWS Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_TEMPERATURE=0.0
BEDROCK_MAX_TOKENS=1024

# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
AWS_CREDENTIALS_PROFILE=default  # For local development
```

## API Reference

### POST /invocations

**Request:**
```json
{
  "userPrompt": "What are my dental benefits?",
  "sessionId": "sess-001",
  "context": {
    "userName": "john_doe",
    "userType": "member",
    "source": "DXAIService",
    "promptId": "p-123"
  }
}
```

**Response:**
```json
{
  "sessionId": "sess-001",
  "selectedTool": [
    {
      "tool_name": "IBTAgent",
      "reason": "User asking about specific benefit coverage",
      "confidence": 9.0,
      "parameters": {}
    }
  ],
  "confidence": 9.0,
  "responseText": "Your insurance benefits include coverage for..."
}
```

### GET /ping

**Response:**
```json
{
  "status": "ok"
}
```

## Guard Rails Logic

The `guard_rails_router` determines routing based on:

| Condition | Route | Action |
|-----------|-------|--------|
| `confidence >= 7.0` AND tool found | `execute_tool` | Call tool API |
| `confidence < 7.0` | `use_fallback` | Return low confidence message |
| `selected_tool == "NO_TOOL"` | `use_fallback` | Return no tool found message |
| `selected_tool == "CONVERSATIONAL"` | `use_fallback` | Return direct LLM response |

## Adding New Tools

### Step 1: Update tools-config.yaml

```yaml
tools:
  - name: IBTAgent
    # ... existing config ...

  - name: ClaimsAgent
    description: "Processes claims-related queries"
    endpoint: https://claims-service.internal/api/v1
    capabilities:
      - claim status
      - claim submission
      - claim history
    parameters:
      required:
        - userPrompt
        - userName
      optional:
        - claimNumber
    examples:
      - prompt: "What's my claim status?"
        reasoning: "User requesting claim information"

  - name: NavigationAgent
    description: "Helps users navigate the portal and find resources"
    endpoint: https://navigation-service.internal/api/v1
    capabilities:
      - page navigation
      - resource lookup
      - help documentation
    parameters:
      required:
        - userPrompt
      optional:
        - currentPage
    examples:
      - prompt: "How do I update my profile?"
        reasoning: "User needs navigation help"
```

### Step 2: Add Mock Response (Optional)

In `orchestrator/nodes/tool_exec.py`, add to `mock_responses`:

```python
mock_responses = {
    "IBTAgent": { ... },
    "ClaimsAgent": {
        "ok": True,
        "response": "Claims Agent Response: Your claim status is..."
    },
    "NavigationAgent": {
        "ok": True,
        "response": "Navigation Agent Response: To update your profile..."
    }
}
```

### Step 3: Restart Server

The registry is loaded at startup. Restart the server to pick up changes.

## Current Implementation Status

### Implemented
- [x] FastAPI endpoints (`/ping`, `/invocations`)
- [x] LangGraph workflow with conditional routing
- [x] AWS Bedrock LLM integration with structured output
- [x] Intent detection with tool selection
- [x] Guard rails with 7.0 confidence threshold
- [x] Fallback handling (low confidence, no tool, conversational)
- [x] YAML-based tool configuration
- [x] Pydantic schemas for type safety

### TODO - Not Yet Implemented
- [ ] **Real HTTP Tool Calls**: `tool_exec.py` uses mocks - implement actual HTTP client
- [ ] **Input Validation Node**: Add explicit validation before intent analysis
- [ ] **Retry with Exponential Backoff**: For tool API failures
- [ ] **Correlation ID Logging**: Add request tracing across nodes
- [ ] **Performance Metrics**: Latency, throughput tracking
- [ ] **Health Check Enhancement**: Return ISO-8601 timestamp in `/ping`
- [ ] **Response Compose Node**: Currently unused - integrate into workflow
- [ ] **MCP Integration**: Future dynamic tool discovery

## Common Development Tasks

### Testing the Intent Node

```python
# From project root
python -c "
from orchestrator.nodes.intent_node import intent_node
from schemas.state import OrchestratorState
from registry.loader import load_tools_from_yaml

registry = load_tools_from_yaml('registry/tools-config.yaml')
state = OrchestratorState(
    query='What are my dental benefits?',
    session_id='test-123',
    registry=registry
)
result = intent_node(state)
print(f'Tool: {result.selected_tools[0].tool_name}')
print(f'Confidence: {result.intent_confidence}')
"
```

### Testing State Initialization

```bash
python test_state_init.py
```

### Running with Debug Logging

```bash
LOG_LEVEL=DEBUG uvicorn app:app --reload --port 8000
```

## Debugging Tips

1. **Check intent_node logs**: Look for `========== INTENT NODE DEBUG ==========` in console
2. **Guard rails routing**: Look for `Guard Rails - Tool: X, Confidence: Y`
3. **State inspection**: The `test_state_init.py` script dumps full state

## Error Messages

| Message | Cause | Solution |
|---------|-------|----------|
| "I'm not entirely sure I understand your question..." | Confidence < 7.0 | Rephrase query or lower threshold |
| "I couldn't find the right resource..." | NO_TOOL selected | Query out of scope or add new tool |
| "Technical difficulties..." | Generic fallback | Check logs for errors |

## FEPOC API Guidelines

All API development must follow FEPOC standards:
- Naming conventions
- Security standards
- Authentication protocols
- Response formats

Reference: `BCBSA_Web_Services_API_Guidelines_2022.docx`

## Future Enhancements (Post-PI2)

1. **MCP Integration**: Model Context Protocol for dynamic tool discovery
2. **Multi-tool Orchestration**: Support parallel tool execution
3. **Conversation Memory**: Session-based context retention
4. **AgentCore Deployment**: Migration from EKS to AgentCore

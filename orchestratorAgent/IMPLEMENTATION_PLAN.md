# Orchestrator Agent - Implementation Plan

## Executive Summary

This document outlines the architectural improvements and implementation roadmap for the Orchestrator Agent based on requirements analysis. The current implementation provides a solid foundation but needs enhancements to support sequential multi-tool execution, session-based memory, clarification flows, and robust error handling.

---

## Completed Work (Pre-Phase 1)

### ✅ Centralized Configuration System
**Status:** COMPLETED | **Date:** 2024-12-30

Created `settings.py` with pydantic-settings for type-safe, validated configuration:

| Setting Category | Configuration Options |
|-----------------|----------------------|
| AWS | `aws_region` |
| Bedrock LLM | `bedrock_model_id`, `bedrock_temperature`, `bedrock_max_tokens` |
| Timeouts | `bedrock_read_timeout` (300s), `bedrock_connect_timeout` (10s) |
| Retries | `bedrock_max_retries` (3, adaptive mode) |
| Extended Thinking | `extended_thinking_enabled`, `budget_tokens`, `max_tokens` |
| Guard Rails | `confidence_threshold_high` (7.0), `confidence_threshold_low` (5.0) |
| Tool Execution | `tool_timeout`, `tool_max_retries` |
| Session | `session_ttl_seconds`, `max_conversation_history` |
| Logging | `log_level` |

**Files Created/Modified:**
- ✅ `settings.py` - New centralized configuration module
- ✅ `config.py` - Updated as backwards-compatibility layer (deprecated)
- ✅ `.env.example` - Updated with all configuration options
- ✅ `requirements.txt` - Added `pydantic-settings`

### ✅ LLM Client Refactoring
**Status:** COMPLETED | **Date:** 2024-12-30

Refactored `llm/bedrock_llm_client.py` with `ChatModels` class pattern:

**Key Improvements:**
- boto3 client with explicit timeout configuration via `botocore.Config`
- Adaptive retry mode (3 attempts) built into botocore
- AWS authentication via environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- Extended thinking support for Claude 3.5+ models
- Singleton pattern with `get_chat_models()` for efficient client reuse
- Specialized model getters:
  - `get_model()` - Default model based on settings
  - `get_model_for_tool_selection()` - temperature=0 for deterministic responses
  - `get_model_for_conversation()` - temperature=0.7 for natural responses
  - `bedrock_model_with_extended_thinking()` - For complex reasoning tasks
- `make_llm()` maintained for backwards compatibility

**Usage:**
```python
from llm.bedrock_llm_client import get_chat_models

chat_models = get_chat_models()
llm = chat_models.get_model()  # Standard model
llm = chat_models.get_model_for_tool_selection()  # Deterministic
llm = chat_models.bedrock_model_with_extended_thinking()  # Extended thinking
```

---

## Project Structure Reorganization

**Full Details:** See [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)

### Summary

The project needs reorganization to follow FastAPI best practices:

| Current | Proposed |
|---------|----------|
| Flat root with `app.py`, `agent.py`, `settings.py` | `src/` folder with clear hierarchy |
| No API layer separation | `src/api/` with routes, dependencies |
| `orchestrator/` for LangGraph | `src/graph/` with workflow, state, nodes |
| Scattered config files | `src/config/` centralized |
| No test organization | `tests/unit/`, `tests/integration/` |

### Key Folders in New Structure

```
src/
├── api/          # HTTP layer (routes, middleware)
├── core/         # Business logic (orchestrator)
├── graph/        # LangGraph (workflow, nodes, state)
├── llm/          # LLM integrations (client, prompts)
├── tools/        # Tool registry & executor
├── schemas/      # Pydantic models
├── config/       # Settings, logging
└── utils/        # Shared utilities
```

### Migration Priority

This should be done **before Phase 1** to establish clean foundations.

---

## Current State Analysis

### What's Working Well
- Clean FastAPI entry points (`/ping`, `/invocations`)
- LangGraph workflow structure with conditional routing
- YAML-based tool configuration (extensible)
- Pydantic schemas for type safety
- AWS Bedrock integration with structured output
- Guard rails with confidence threshold

### Gaps Identified

| Gap | Impact | Priority |
|-----|--------|----------|
| No multi-tool execution | Cannot handle complex queries | High |
| No session memory | Context lost between turns | High |
| No clarification flow | Ambiguous queries go to fallback | Medium |
| No retry logic for tool failures | Single point of failure | High |
| Linear graph (no cycles) | Underutilizes LangGraph | Medium |
| Mock tool execution | Not production-ready | High |
| `response_compose.py` unused | Dead code | Low |

---

## Target Architecture

### Proposed LangGraph Workflow

```
                                    ┌─────────────────────────┐
                                    │        START            │
                                    └───────────┬─────────────┘
                                                │
                                                ▼
                                    ┌─────────────────────────┐
                                    │   input_validation      │
                                    │   (validate request)    │
                                    └───────────┬─────────────┘
                                                │
                                                ▼
                                    ┌─────────────────────────┐
                                    │   query_analyzer        │
                                    │   (intent + decompose)  │
                                    └───────────┬─────────────┘
                                                │
                                                ▼
                                    ┌─────────────────────────┐
                                    │   confidence_router     │
                                    │   (conditional)         │
                                    └───────────┬─────────────┘
                                                │
                    ┌───────────────────────────┼───────────────────────────┐
                    │                           │                           │
                    ▼                           ▼                           ▼
        ┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
        │  conf >= 7.0      │       │  5.0 <= conf < 7  │       │  conf < 5.0       │
        │  execute_tools    │       │  ask_clarification│       │  use_fallback     │
        └─────────┬─────────┘       └─────────┬─────────┘       └─────────┬─────────┘
                  │                           │                           │
                  ▼                           │                           │
        ┌───────────────────┐                 │                           │
        │  tool_executor    │◄────────────────┘                           │
        │  (with retry)     │     (after user clarifies)                  │
        └─────────┬─────────┘                                             │
                  │                                                       │
                  ▼                                                       │
        ┌───────────────────┐                                             │
        │  tool_result_     │                                             │
        │  checker          │                                             │
        │  (conditional)    │                                             │
        └─────────┬─────────┘                                             │
                  │                                                       │
        ┌─────────┼─────────┐                                             │
        │         │         │                                             │
        ▼         ▼         ▼                                             │
    success   more_tools  failure                                         │
        │         │         │                                             │
        │         │    ┌────┴────┐                                        │
        │         │    │ retry < │──────► tool_executor                   │
        │         │    │ max?    │        (retry loop)                    │
        │         │    └────┬────┘                                        │
        │         │         │ max retries                                 │
        │         │         ▼                                             │
        │         │    use_fallback ◄─────────────────────────────────────┘
        │         │         │
        │         └────►────┤
        │                   │
        ▼                   ▼
┌───────────────────────────────────┐
│        response_compose           │
│    (format final response)        │
└───────────────────┬───────────────┘
                    │
                    ▼
              ┌───────────┐
              │    END    │
              └───────────┘
```

### Key Architectural Changes

#### 1. Query Decomposition (NEW)
The `query_analyzer` node will now:
- Detect if query requires multiple tools
- Decompose into ordered sub-queries
- Return list of `SelectedTool` objects with execution order

#### 2. Confidence-Based Routing (ENHANCED)
Three routing paths instead of two:
- `>= 7.0`: Execute tools
- `5.0 - 6.9`: Ask clarifying question
- `< 5.0`: Fallback message

#### 3. Sequential Tool Execution (NEW)
The `tool_executor` node will:
- Execute tools in sequence
- Pass previous tool's output to next tool's context
- Track execution progress in state

#### 4. Retry Loop (NEW)
Add cycle in graph for retry logic:
- Max 3 retries with exponential backoff
- Track retry count in state
- Conditional edge back to tool_executor or to fallback

#### 5. Session Memory (NEW)
Implement LangGraph checkpointing:
- Use `MemorySaver` or Redis-backed store
- Key by `sessionId`
- Store conversation history and context

---

## Implementation Phases

### Phase 1: Foundation Fixes (PI2 Hardening)
**Goal:** Production-ready single-tool flow

#### 1.1 Real HTTP Tool Calls
**File:** `orchestrator/nodes/tool_exec.py`

```python
# Replace mock_responses with actual HTTP client
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class ToolExecutor:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def execute(self, tool: ToolDefinition, params: dict) -> ToolResult:
        response = await self.client.post(
            tool.endpoint,
            json=params,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return ToolResult(ok=True, response=response.json())
```

**Tasks:**
- [ ] Add `httpx` and `tenacity` to requirements.txt
- [ ] Create `ToolExecutor` class with retry logic
- [ ] Update `tool_exec.py` to use async HTTP calls
- [ ] Add configurable timeout (from environment)
- [ ] Add request/response logging with correlation ID

#### 1.2 Input Validation Node
**File:** `orchestrator/nodes/input_validation.py` (NEW)

```python
from schemas.api import OrchestratorRequest
from schemas.state import OrchestratorState

def input_validation_node(state: OrchestratorState) -> OrchestratorState:
    """Validate request before processing."""
    errors = []

    if not state.query or len(state.query.strip()) == 0:
        errors.append("userPrompt is required and cannot be empty")

    if len(state.query) > 2000:
        errors.append("userPrompt exceeds maximum length of 2000 characters")

    if not state.session_id:
        errors.append("sessionId is required")

    if errors:
        state.validation_errors = errors
        state.is_valid = False
    else:
        state.is_valid = True

    return state
```

**Tasks:**
- [ ] Create `input_validation.py` node
- [ ] Add `validation_errors` and `is_valid` to `OrchestratorState`
- [ ] Add conditional edge after validation (valid → analyzer, invalid → error_response)
- [ ] Update graph.py to include validation node

#### 1.3 Health Check Enhancement
**File:** `app.py`

```python
from datetime import datetime, timezone

@app.get("/ping")
async def ping():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "tools_loaded": len(registry.tools)
    }
```

**Tasks:**
- [ ] Add ISO-8601 timestamp to `/ping` response
- [ ] Add version info
- [ ] Add tools count for monitoring

#### 1.4 Correlation ID Logging
**File:** `app.py` (middleware)

```python
import uuid
from contextvars import ContextVar

correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')

@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    correlation_id.set(req_id)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = req_id
    return response
```

**Tasks:**
- [ ] Add correlation ID middleware
- [ ] Create structured logger with correlation ID
- [ ] Update all nodes to use structured logging

---

### Phase 2: Session Memory & Clarification
**Goal:** Conversation continuity and smart clarification

#### 2.1 LangGraph Checkpointing
**File:** `orchestrator/graph.py`

```python
from langgraph.checkpoint.memory import MemorySaver

# For development
memory = MemorySaver()

# For production (future)
# from langgraph.checkpoint.redis import RedisSaver
# memory = RedisSaver(redis_url="redis://localhost:6379")

graph = builder.compile(checkpointer=memory)
```

**File:** `agent.py`

```python
async def invoke(self, request: OrchestratorRequest) -> OrchestratorResponse:
    config = {
        "configurable": {
            "thread_id": request.sessionId  # Links to session
        }
    }
    result = await self.graph.ainvoke(initial_state, config)
    return result
```

**Tasks:**
- [ ] Add `MemorySaver` checkpointer to graph compilation
- [ ] Pass `thread_id` config in agent invocation
- [ ] Add `conversation_history` to `OrchestratorState`
- [ ] Update `intent_node` to include history in LLM prompt
- [ ] Test multi-turn conversations

#### 2.2 Clarification Node
**File:** `orchestrator/nodes/clarification_node.py` (NEW)

```python
def clarification_node(state: OrchestratorState) -> OrchestratorState:
    """Generate clarifying question for ambiguous queries."""

    # Use LLM to generate contextual clarifying question
    clarification_prompt = f"""
    The user asked: "{state.query}"

    This query is ambiguous. The possible interpretations are:
    - Tool options: {[t.tool_name for t in state.selected_tools]}

    Generate a brief, helpful clarifying question to understand what the user needs.
    Keep it under 50 words.
    """

    question = llm_client.invoke(clarification_prompt)

    state.needs_clarification = True
    state.clarification_question = question
    state.response_text = question

    return state
```

**Tasks:**
- [ ] Create `clarification_node.py`
- [ ] Add `needs_clarification`, `clarification_question` to state
- [ ] Update `confidence_router` for three-way routing
- [ ] Add logic to detect when user responds to clarification
- [ ] Update graph with clarification path

#### 2.3 Update Confidence Router
**File:** `orchestrator/nodes/guard_rails_router.py`

```python
def confidence_router(state: OrchestratorState) -> str:
    """Route based on confidence score."""
    confidence = state.intent_confidence
    tool_name = state.selected_tools[0].tool_name if state.selected_tools else "NO_TOOL"

    if tool_name in ["NO_TOOL", "CONVERSATIONAL"]:
        return "use_fallback"

    if confidence >= 7.0:
        return "execute_tools"
    elif confidence >= 5.0:
        return "ask_clarification"  # NEW path
    else:
        return "use_fallback"
```

**Tasks:**
- [ ] Update router for three-way routing
- [ ] Add edge from `ask_clarification` to `clarification_node`
- [ ] Handle clarification response routing back to analyzer

---

### Phase 3: Multi-Tool Execution
**Goal:** Sequential tool chaining for complex queries

#### 3.1 Query Decomposition
**File:** `orchestrator/nodes/intent_node.py` (ENHANCED)

```python
# Enhanced LLM prompt for decomposition
DECOMPOSITION_PROMPT = """
Given the user query: "{query}"

Available tools:
{tools_info}

Analyze this query and determine:
1. Can this be answered by a single tool? Or does it need multiple tools?
2. If multiple tools, what is the execution order?
3. What information from Tool A should be passed to Tool B?

Respond in JSON:
{{
  "requires_multiple_tools": boolean,
  "tools": [
    {{
      "tool_name": "string",
      "reason": "string",
      "confidence": number,
      "depends_on": "previous_tool_name or null",
      "context_needed": ["list of fields from previous tool"]
    }}
  ],
  "overall_confidence": number
}}
"""
```

**Tasks:**
- [ ] Update intent_node prompt for decomposition
- [ ] Modify `SelectedTool` schema to include `depends_on` and `context_needed`
- [ ] Return list of tools with execution order
- [ ] Handle single vs multi-tool responses

#### 3.2 Sequential Tool Executor
**File:** `orchestrator/nodes/tool_exec.py` (ENHANCED)

```python
async def sequential_tool_executor(state: OrchestratorState) -> OrchestratorState:
    """Execute tools in sequence, passing context between them."""

    tools_to_execute = state.selected_tools
    execution_context = {}
    results = []

    for i, tool in enumerate(tools_to_execute):
        # Build params with context from previous tools
        params = {
            "userPrompt": state.query,
            "userName": state.context.get("userName"),
            "previousContext": execution_context
        }

        try:
            result = await tool_executor.execute(
                tool_definition=state.registry.get_tool(tool.tool_name),
                params=params
            )
            results.append(result)

            # Extract context for next tool
            if tool.context_needed:
                for field in tool.context_needed:
                    execution_context[field] = result.response.get(field)

        except Exception as e:
            state.tool_error = str(e)
            state.current_tool_index = i
            return state  # Will trigger retry or fallback

    state.tool_results = results
    state.all_tools_completed = True
    return state
```

**Tasks:**
- [ ] Update tool_exec for sequential execution
- [ ] Add `tool_results`, `current_tool_index`, `all_tools_completed` to state
- [ ] Implement context passing between tools
- [ ] Add conditional routing after each tool (success/failure/more_tools)

#### 3.3 Tool Result Checker
**File:** `orchestrator/nodes/tool_result_checker.py` (NEW)

```python
def tool_result_checker(state: OrchestratorState) -> str:
    """Determine next step after tool execution."""

    if state.tool_error:
        if state.retry_count < 3:
            return "retry_tool"
        else:
            return "use_fallback"

    if not state.all_tools_completed:
        return "execute_next_tool"

    return "compose_response"
```

**Tasks:**
- [ ] Create tool_result_checker node
- [ ] Add `retry_count` to state
- [ ] Wire up conditional edges in graph

---

### Phase 4: Production Readiness
**Goal:** Monitoring, observability, and reliability

#### 4.1 Structured Logging

```python
import structlog

logger = structlog.get_logger()

# In each node
logger.info(
    "tool_selected",
    tool_name=selected_tool.tool_name,
    confidence=confidence,
    session_id=state.session_id,
    correlation_id=correlation_id.get()
)
```

**Tasks:**
- [ ] Add `structlog` to requirements
- [ ] Configure JSON logging format
- [ ] Add logging to all nodes
- [ ] Include correlation_id in all log entries

#### 4.2 Metrics Collection

```python
from prometheus_client import Counter, Histogram

tool_selection_counter = Counter(
    'orchestrator_tool_selections_total',
    'Total tool selections',
    ['tool_name', 'outcome']
)

latency_histogram = Histogram(
    'orchestrator_request_latency_seconds',
    'Request latency',
    ['endpoint']
)
```

**Tasks:**
- [ ] Add Prometheus metrics
- [ ] Track tool selection accuracy
- [ ] Track latency per node
- [ ] Track retry rates
- [ ] Add `/metrics` endpoint

#### 4.3 Rate Limiting for Bedrock

```python
from asyncio import Semaphore

bedrock_semaphore = Semaphore(10)  # Max 10 concurrent calls

async def invoke_with_rate_limit(prompt: str):
    async with bedrock_semaphore:
        return await llm_client.ainvoke(prompt)
```

**Tasks:**
- [ ] Add concurrency limiter for Bedrock calls
- [ ] Implement request queuing if limit exceeded
- [ ] Add circuit breaker for Bedrock failures

---

## State Schema Updates

### Updated OrchestratorState

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class OrchestratorState(BaseModel):
    # Existing fields
    query: str
    session_id: str
    context: Dict[str, Any]
    registry: ToolRegistry
    selected_tools: List[SelectedTool] = []
    intent_confidence: float = 0.0
    response_text: str = ""

    # Phase 1 additions
    is_valid: bool = True
    validation_errors: List[str] = []
    correlation_id: str = ""

    # Phase 2 additions
    conversation_history: List[Dict[str, str]] = []
    needs_clarification: bool = False
    clarification_question: Optional[str] = None

    # Phase 3 additions
    requires_multiple_tools: bool = False
    current_tool_index: int = 0
    tool_results: List[ToolResult] = []
    all_tools_completed: bool = False
    execution_context: Dict[str, Any] = {}

    # Error handling
    tool_error: Optional[str] = None
    retry_count: int = 0
    fallback_reason: Optional[str] = None
```

---

## Updated Graph Definition

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

def create_orchestrator_graph():
    builder = StateGraph(OrchestratorState)

    # Add nodes
    builder.add_node("input_validation", input_validation_node)
    builder.add_node("query_analyzer", query_analyzer_node)
    builder.add_node("clarification", clarification_node)
    builder.add_node("tool_executor", sequential_tool_executor)
    builder.add_node("fallback", fallback_node)
    builder.add_node("response_compose", response_compose_node)

    # Set entry point
    builder.set_entry_point("input_validation")

    # Validation routing
    builder.add_conditional_edges(
        "input_validation",
        lambda s: "query_analyzer" if s.is_valid else "fallback"
    )

    # Confidence routing
    builder.add_conditional_edges(
        "query_analyzer",
        confidence_router,
        {
            "execute_tools": "tool_executor",
            "ask_clarification": "clarification",
            "use_fallback": "fallback"
        }
    )

    # Clarification goes back to analyzer (after user responds)
    builder.add_edge("clarification", END)  # Returns question to user

    # Tool execution routing
    builder.add_conditional_edges(
        "tool_executor",
        tool_result_checker,
        {
            "retry_tool": "tool_executor",
            "execute_next_tool": "tool_executor",
            "compose_response": "response_compose",
            "use_fallback": "fallback"
        }
    )

    # Final edges
    builder.add_edge("response_compose", END)
    builder.add_edge("fallback", END)

    # Compile with checkpointing
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)
```

---

## Testing Strategy

### Unit Tests

| Component | Test Cases |
|-----------|------------|
| `input_validation` | Empty query, long query, missing sessionId |
| `query_analyzer` | Single tool, multi-tool, no tool match |
| `confidence_router` | High/medium/low confidence routing |
| `tool_executor` | Success, failure, retry exhausted |
| `clarification` | Question generation quality |

### Integration Tests

| Scenario | Expected Flow |
|----------|---------------|
| Simple benefit query | validation → analyzer → executor → compose |
| Ambiguous query | validation → analyzer → clarification → END |
| Multi-tool query | validation → analyzer → executor (x2) → compose |
| Tool failure | executor → retry → retry → fallback |

### Load Tests

- Target: 100 requests/second
- Latency P99: < 5 seconds
- Error rate: < 1%

---

## Migration Path

### PI2 → Phase 1
1. Deploy Phase 1 changes behind feature flag
2. Run in shadow mode (log decisions, don't change behavior)
3. Compare mock vs real tool responses
4. Gradual rollout: 10% → 50% → 100%

### Phase 1 → Phase 2
1. Enable checkpointing with in-memory store
2. Add clarification flow as optional (confidence threshold configurable)
3. Monitor clarification rate and user satisfaction
4. Tune confidence thresholds based on data

### Phase 2 → Phase 3
1. Start with specific multi-tool scenarios (manually configured)
2. Enable LLM-based decomposition for subset of queries
3. Monitor accuracy and latency impact
4. Full rollout after validation

---

## Dependencies to Add

```txt
# requirements.txt additions

# Already Added ✅
pydantic-settings>=2.0.0  # ✅ Added for centralized configuration

# Phase 1 - HTTP client with retry
httpx>=0.25.0
tenacity>=8.2.0

# Phase 4 - Structured logging
structlog>=23.1.0

# Phase 4 - Metrics
prometheus-client>=0.17.0

# Phase 2 - Redis (for production checkpointing)
redis>=4.5.0
# langgraph[redis]  # When using Redis checkpointer
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Bedrock latency spikes | Medium | High | Circuit breaker, fallback responses |
| Multi-tool complexity | Medium | Medium | Start with 2-tool max, expand gradually |
| Session memory bloat | Low | Medium | TTL on sessions, max history length |
| Clarification loops | Low | Low | Max clarification attempts (2) |

---

## Success Metrics

| Metric | Current | Phase 1 Target | Phase 3 Target |
|--------|---------|----------------|----------------|
| Tool selection accuracy | Unknown | 85% | 92% |
| Avg latency | Unknown | < 3s | < 4s |
| Fallback rate | Unknown | < 15% | < 10% |
| Multi-turn success | N/A | N/A | 80% |

---

## Timeline Recommendation

| Phase | Scope | Recommended Duration |
|-------|-------|---------------------|
| Phase 1 | Foundation fixes | First |
| Phase 2 | Memory & clarification | After Phase 1 stable |
| Phase 3 | Multi-tool | After Phase 2 validated |
| Phase 4 | Production readiness | Parallel with Phase 2-3 |

---

## Open Questions

1. **PII Handling**: Does userPrompt contain PII? Need to determine redaction requirements before logging.

2. **Streaming**: Should responses stream to user? This affects response_compose design.

3. **Tool Timeouts**: What are acceptable timeouts for each tool? (IBT, Claims, etc.)

4. **Session TTL**: How long should session memory persist? (30 min? 24 hours?)

5. **Clarification Limit**: Max number of clarification rounds before forcing fallback?

---

## Appendix: File Change Summary

### Completed (Pre-Phase 1) ✅

| File | Action | Status |
|------|--------|--------|
| `settings.py` | New - Centralized configuration | ✅ Done |
| `config.py` | Updated - Backwards compatibility layer | ✅ Done |
| `llm/bedrock_llm_client.py` | Refactored - ChatModels pattern | ✅ Done |
| `requirements.txt` | Added pydantic-settings | ✅ Done |
| `.env.example` | Updated with all config options | ✅ Done |

### Remaining Work

| File | Action | Phase |
|------|--------|-------|
| `requirements.txt` | Add httpx, tenacity | 1 |
| `orchestrator/graph.py` | Major refactor | 1-3 |
| `orchestrator/nodes/tool_exec.py` | Rewrite with HTTP client | 1, 3 |
| `orchestrator/nodes/input_validation.py` | New | 1 |
| `orchestrator/nodes/guard_rails_router.py` | Update for 3-way routing | 2 |
| `orchestrator/nodes/clarification_node.py` | New | 2 |
| `orchestrator/nodes/tool_result_checker.py` | New | 3 |
| `orchestrator/nodes/response_compose.py` | Activate | 1 |
| `schemas/state.py` | Expand with new fields | 1-3 |
| `schemas/tools.py` | Update for multi-tool | 3 |
| `app.py` | Add middleware | 1 |
| `agent.py` | Add checkpointing | 2 |

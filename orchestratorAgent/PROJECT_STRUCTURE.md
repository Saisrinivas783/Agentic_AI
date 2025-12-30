# Project Structure Proposal

## Overview

This document outlines the proposed project structure reorganization for the Orchestrator Agent. The goal is to follow FastAPI best practices, improve maintainability, and prepare for scale.

---

## Current Structure (Problems)

```
orchestratorAgent/
├── app.py                      # Entry point at root - mixed with config
├── agent.py                    # Business logic at root
├── config.py                   # Deprecated, still at root
├── settings.py                 # New config, also at root
├── test_state_init.py          # Test file mixed with source
├── requirements.txt
│
├── orchestrator/               # LangGraph specific
│   ├── graph.py
│   └── nodes/
│       ├── intent_node.py
│       ├── guard_rails_router.py
│       ├── tool_exec.py
│       ├── fallback_node.py
│       └── response_compose.py
│
├── llm/                        # LLM at same level as orchestrator
│   └── bedrock_llm_client.py
│
├── registry/                   # Tool config separate from tool code
│   ├── loader.py
│   └── tools-config.yaml
│
├── schemas/                    # All schemas in one place
│   ├── api.py
│   ├── state.py
│   ├── registry.py
│   └── tools.py
│
└── tools/                      # Empty except stub
    └── ibt_stub.py
```

### Issues Identified

| Issue | Problem | Impact |
|-------|---------|--------|
| No `src/` folder | Source code mixed with project files | Hard to package, messy imports |
| Flat root | `app.py`, `agent.py`, `settings.py` all at root | No clear hierarchy |
| No API layer | Routes embedded in `app.py` | Hard to add versioning, middleware |
| Scattered config | `config.py`, `settings.py`, `tools-config.yaml` in different places | Confusing |
| No tests folder | `test_state_init.py` at root | No test organization |
| Inconsistent naming | `bedrock_llm_client.py` vs `intent_node.py` | Style inconsistency |

---

## Proposed Structure

```
orchestratorAgent/
│
├── src/                            # All source code here
│   ├── __init__.py
│   │
│   ├── main.py                     # FastAPI app factory
│   │
│   ├── api/                        # API Layer (HTTP concerns only)
│   │   ├── __init__.py
│   │   ├── app.py                  # FastAPI app instance, middleware
│   │   ├── dependencies.py         # Dependency injection
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py           # GET /ping, GET /health
│   │       └── invocations.py      # POST /invocations
│   │
│   ├── core/                       # Core business logic
│   │   ├── __init__.py
│   │   ├── orchestrator.py         # OrchestratorAgent class
│   │   └── exceptions.py           # Custom exceptions
│   │
│   ├── graph/                      # LangGraph workflow
│   │   ├── __init__.py
│   │   ├── workflow.py             # Graph definition & compilation
│   │   ├── state.py                # OrchestratorState
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── input_validation.py # Validate input
│   │       ├── intent_analyzer.py  # Intent detection + tool selection
│   │       ├── confidence_router.py# Guard rails routing logic
│   │       ├── tool_executor.py    # Tool execution with retry
│   │       ├── clarification.py    # Ask clarifying questions
│   │       ├── fallback.py         # Fallback responses
│   │       └── response_composer.py# Format final response
│   │
│   ├── llm/                        # LLM integrations
│   │   ├── __init__.py
│   │   ├── client.py               # ChatModels class
│   │   └── prompts/
│   │       ├── __init__.py
│   │       ├── intent.py           # Intent detection prompts
│   │       └── clarification.py    # Clarification prompts
│   │
│   ├── tools/                      # Tool registry & execution
│   │   ├── __init__.py
│   │   ├── registry.py             # Tool loader & registry
│   │   ├── executor.py             # HTTP tool executor
│   │   └── definitions/
│   │       └── tools.yaml          # Tool configurations
│   │
│   ├── schemas/                    # Pydantic models
│   │   ├── __init__.py
│   │   ├── api.py                  # Request/Response models
│   │   ├── state.py                # Graph state (re-export from graph/)
│   │   └── tools.py                # Tool-related schemas
│   │
│   ├── config/                     # All configuration
│   │   ├── __init__.py
│   │   ├── settings.py             # Pydantic settings
│   │   └── logging.py              # Logging configuration
│   │
│   └── utils/                      # Shared utilities
│       ├── __init__.py
│       ├── correlation.py          # Correlation ID handling
│       └── retry.py                # Retry utilities
│
├── tests/                          # All tests
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_nodes/
│   │   │   ├── test_intent_analyzer.py
│   │   │   └── test_tool_executor.py
│   │   └── test_llm/
│   │       └── test_client.py
│   └── integration/
│       ├── __init__.py
│       └── test_api/
│           └── test_invocations.py
│
├── scripts/                        # Utility scripts
│   └── test_requests.http          # HTTP test requests
│
├── .env.example                    # Environment template
├── .gitignore
├── pyproject.toml                  # Modern Python packaging
├── requirements.txt                # Dependencies
├── README.md
├── CHANGELOG.md
└── CLAUDE.md                       # Development guide
```

---

## Reasoning for Each Folder

### `src/` - Source Code Root

**Why:** Separates source code from project metadata

- Standard Python packaging practice
- Cleaner imports: `from src.graph.nodes import intent_analyzer`
- Easy to exclude non-source files from builds
- Follows [PEP 517](https://peps.python.org/pep-0517/) modern packaging

---

### `src/api/` - API Layer

**Why:** Separation of HTTP concerns from business logic

| Component | Purpose |
|-----------|---------|
| `routes/` | Each route file handles one endpoint group |
| `dependencies.py` | FastAPI dependency injection (get_db, get_agent) |
| `app.py` | App factory pattern, middleware, exception handlers |

**Benefits:**
- Enables API versioning (`routes/v1/`, `routes/v2/`)
- Routes only handle HTTP → delegate to `core/` for logic
- Easy to add middleware, CORS, authentication

```python
# src/api/routes/invocations.py
from fastapi import APIRouter, Depends
from src.core.orchestrator import OrchestratorAgent
from src.api.dependencies import get_orchestrator

router = APIRouter()

@router.post("/invocations")
def invoke(
    request: InvocationRequest,
    agent: OrchestratorAgent = Depends(get_orchestrator)
):
    return agent.handle_invocation(request)
```

---

### `src/core/` - Business Logic

**Why:** Pure Python business logic, no framework dependencies

| Component | Purpose |
|-----------|---------|
| `orchestrator.py` | Main agent class that coordinates everything |
| `exceptions.py` | Custom exceptions (ToolNotFoundError, LowConfidenceError) |

**Benefits:**
- Can be tested without FastAPI
- Can be reused in CLI, background workers, etc.
- Framework-agnostic

---

### `src/graph/` - LangGraph Workflow

**Why:** All LangGraph-specific code in one place

| Component | Purpose |
|-----------|---------|
| `workflow.py` | Graph definition, compilation, checkpointer setup |
| `state.py` | `OrchestratorState` TypedDict with all state fields |
| `nodes/` | Each node is a separate file for clarity |

**Benefits:**
- Easy to visualize the entire workflow
- Nodes are pure functions that transform state
- Graph logic is isolated from API/HTTP concerns

```python
# src/graph/workflow.py
from langgraph.graph import StateGraph
from src.graph.state import OrchestratorState
from src.graph.nodes import intent_analyzer, tool_executor, fallback

def create_workflow() -> StateGraph:
    builder = StateGraph(OrchestratorState)
    builder.add_node("intent", intent_analyzer.run)
    builder.add_node("execute", tool_executor.run)
    # ... edges
    return builder.compile()
```

---

### `src/llm/` - LLM Integrations

**Why:** Isolate LLM-specific code for easy swapping

| Component | Purpose |
|-----------|---------|
| `client.py` | `ChatModels` class (Bedrock, could add OpenAI) |
| `prompts/` | Prompt templates as separate files |

**Benefits:**
- Easy to switch LLM providers without touching graph logic
- Prompts can be version controlled and A/B tested
- Clear separation of LLM concerns

---

### `src/tools/` - Tool Management

**Why:** Tool registry and execution are tightly coupled

| Component | Purpose |
|-----------|---------|
| `registry.py` | Load tools from YAML, provide lookup |
| `executor.py` | HTTP client with retry, timeout, error handling |
| `definitions/tools.yaml` | Tool configurations |

**Benefits:**
- Single responsibility: "How do we call external tools?"
- Tool configs alongside tool code
- Easy to add new tools

---

### `src/schemas/` - Pydantic Models

**Why:** Centralized type definitions

- All request/response models in one place
- Reusable across API, core, and graph layers
- Single source of truth for data structures

---

### `src/config/` - Configuration

**Why:** All configuration in one place

| Component | Purpose |
|-----------|---------|
| `settings.py` | Pydantic settings (env vars) |
| `logging.py` | Structured logging setup |

**Benefits:**
- No more scattered config files
- Single import for all settings

---

### `tests/` - Test Organization

**Why:** Mirror source structure for easy navigation

| Folder | Purpose |
|--------|---------|
| `unit/` | Fast, isolated tests |
| `integration/` | Tests with real HTTP calls |
| `conftest.py` | Shared fixtures |

---

## Import Examples

### Before (messy, inconsistent)

```python
from llm.bedrock_llm_client import make_llm
from orchestrator.nodes.intent_node import intent_node
from schemas.state import OrchestratorState
from registry.loader import load_tools_from_yaml
```

### After (clean, predictable)

```python
from src.llm.client import get_chat_models
from src.graph.nodes.intent_analyzer import run as analyze_intent
from src.graph.state import OrchestratorState
from src.tools.registry import ToolRegistry
from src.config.settings import get_settings
```

---

## Migration Steps

| Step | Action | Files Affected |
|------|--------|----------------|
| 1 | Create `src/` folder structure | New directories |
| 2 | Move `app.py` | → `src/api/app.py` + `src/api/routes/` |
| 3 | Move `agent.py` | → `src/core/orchestrator.py` |
| 4 | Move `settings.py` | → `src/config/settings.py` |
| 5 | Move `llm/` | → `src/llm/` |
| 6 | Move `orchestrator/` | → `src/graph/` |
| 7 | Move `registry/` | → `src/tools/` |
| 8 | Move `schemas/` | → `src/schemas/` |
| 9 | Move test files | → `tests/` |
| 10 | Update all imports | Throughout codebase |
| 11 | Create `src/main.py` | New entry point |
| 12 | Delete `config.py` | Remove deprecated file |

---

## Entry Point After Migration

### `src/main.py`

```python
from src.api.app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
```

### `src/api/app.py`

```python
from fastapi import FastAPI
from src.api.routes import health, invocations
from src.config.settings import get_settings

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Orchestrator Agent",
        version="1.0.0",
    )

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(invocations.router, tags=["Invocations"])

    return app
```

---

## Running After Migration

```bash
# Development
uvicorn src.main:app --reload --port 8000

# Or with uv
uv run uvicorn src.main:app --reload --port 8000

# Production
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| Structure | Flat, random | Hierarchical, organized |
| API Layer | Mixed in `app.py` | Dedicated `src/api/` |
| Config | Scattered | Centralized in `src/config/` |
| Tests | Root level | Organized in `tests/` |
| LangGraph | `orchestrator/` | `src/graph/` |
| Imports | Inconsistent | Clean, predictable |
| Packaging | Difficult | Ready for pyproject.toml |

# Changelog

All notable changes to the Orchestrator Agent project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Project Restructure** - Reorganized to proper FastAPI `src/` layout
  - `src/api/` - FastAPI app, routes, dependencies
  - `src/config/` - Centralized settings
  - `src/graph/` - LangGraph workflow and nodes
  - `src/llm/` - LLM client
  - `src/schemas/` - Pydantic models
  - `src/tools/` - Tool registry and definitions
  - `tests/` - Unit and integration test structure

- **`src/schemas/api.py`** - Clean API request/response schemas
  - `BaseWorkflowRequest` - Base with `session_id`
  - `BaseWorkflowResponse` - Base with `success`, `timestamp`, `execution_time_ms`
  - `InvocationContext` - Context from DXAIService
  - `InvocationRequest` - Matches PDF spec exactly
  - `SelectedToolResponse` - Tool selection info for response
  - `InvocationResponse` - Structured response with timing
  - `HealthResponse` - For `/ping` endpoint

- **`settings.py`** - New centralized configuration module using `pydantic-settings`
  - Type-safe configuration with validation
  - Environment variable loading with `.env` file support
  - Comprehensive settings for:
    - AWS region configuration
    - Bedrock LLM settings (model ID, temperature, max tokens)
    - Timeout configuration (read: 300s, connect: 10s)
    - Retry configuration (max 3 attempts, adaptive mode)
    - Extended thinking support for Claude 3.5+ models
    - Guard rails thresholds (high: 7.0, low: 5.0)
    - Tool execution settings
    - Session management (TTL, conversation history limit)
    - Logging configuration

- **`IMPLEMENTATION_PLAN.md`** - Comprehensive implementation roadmap
  - Architecture analysis and gap identification
  - 4-phase implementation plan:
    - Phase 1: Foundation fixes (HTTP calls, validation, retry logic)
    - Phase 2: Session memory & clarification flow
    - Phase 3: Multi-tool sequential execution
    - Phase 4: Production readiness (logging, metrics)
  - Updated LangGraph workflow diagram with cycles and conditional routing
  - State schema updates for new features
  - Testing strategy and migration path

### Changed

- **`src/schemas/state.py`** - Simplified state as pure data container
  - `selected_tool` (single `SelectedTool`) instead of `selected_tools` (list)
  - `tool_result` (single `ToolResult`) instead of `tool_results` (list)
  - Removed `intent` and `intent_confidence` (now in `selected_tool`)
  - Clear separation: state holds data, nodes hold logic

- **`src/schemas/tools.py`** - Cleaner tool schemas
  - `SelectedTool` with `tool_name`, `confidence`, `reasoning`, `parameters`
  - `ToolResult` with `tool_name`, `success`, `response`, `error`

- **`src/schemas/llm.py`** - New file for LLM structured output schemas
  - `ToolSelectionOutput` - Structured output for tool selection

- **`src/llm/prompts/intent_analyzer.py`** - New file for prompt templates
  - `build_tool_selection_prompt()` - System prompt for tool selection
  - `build_tools_context()` - Format registry for LLM

- **`src/graph/nodes/intent_analyzer.py`** - Refactored for separation of concerns
  - Moved `ToolSelectionOutput` to `src/schemas/llm.py`
  - Moved prompt templates to `src/llm/prompts/intent_analyzer.py`
  - Node now imports models and prompts from dedicated modules

- **`src/graph/nodes/confidence_router.py`** - Cleaner routing logic
  - Reads from `state.selected_tool`
  - Added `CONFIDENCE_THRESHOLD = 7.0` constant
  - Simplified conditional checks

- **`src/graph/nodes/tool_executor.py`** - Simplified executor
  - Reads from `state.selected_tool`
  - Sets `state.tool_result` (singular)
  - `MOCK_RESPONSES` dict for testing

- **`src/graph/nodes/fallback.py`** - Uses spec-defined messages
  - `FALLBACK_MESSAGES` dict with `no_tool_found`, `low_confidence`, `service_unavailable`
  - Reads from `state.selected_tool`

- **`src/graph/orchestrator.py`** - Builds structured API response
  - Creates `SelectedToolResponse` from state
  - Adds `execution_time_ms` tracking
  - Uses proper field names (`user_prompt`, `session_id`)

- **File renames for clarity:**
  - `intent_node.py` → `intent_analyzer.py`
  - `guard_rails_router.py` → `confidence_router.py`
  - `tool_exec.py` → `tool_executor.py`
  - `fallback_node.py` → `fallback.py`
  - `response_compose.py` → `response_composer.py`
  - `bedrock_llm_client.py` → `client.py`

- **`llm/bedrock_llm_client.py`** - Complete refactor with `ChatModels` class
  - Now uses `boto3.client` with explicit timeout and retry configuration via `botocore.Config`
  - Authentication via AWS environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
  - Added `bedrock_model_with_extended_thinking()` for Claude 3.5+ complex reasoning
  - Added specialized model getters:
    - `get_model_for_tool_selection()` - temperature=0 for deterministic responses
    - `get_model_for_conversation()` - temperature=0.7 for natural responses
  - Singleton pattern with `get_chat_models()` for efficient client reuse
  - Maintained `make_llm()` for backwards compatibility

- **`config.py`** - Now a backwards-compatibility layer
  - Re-exports settings from `settings.py`
  - Marked as deprecated with migration guidance

- **`.env.example`** - Updated with all configuration options
  - Removed hardcoded credentials (security fix)
  - Added placeholder values for AWS credentials
  - Added all new configuration options with documentation

- **`requirements.txt`** - Added `pydantic-settings` dependency

### Security

- Removed real AWS credentials from `.env.example`
- AWS authentication now strictly via environment variables

### Deprecated

- `config.py` module - Use `from settings import orchestrator_settings` instead
- `aws_credentials_profile` setting - Authentication now via env vars only

## [0.1.0] - 2024-XX-XX (PI2 Release)

### Added

- Initial Orchestrator Agent implementation
- LangGraph workflow with intent detection and tool routing
- AWS Bedrock LLM integration
- YAML-based tool configuration
- Guard rails with confidence threshold (7.0)
- FastAPI endpoints (`/ping`, `/invocations`)
- IBTAgent tool support (mock implementation)

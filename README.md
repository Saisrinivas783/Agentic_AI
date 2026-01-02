# Orchestrator Agent

A Python-based intelligent routing service that uses LangGraph for workflow orchestration. It dynamically selects and invokes appropriate tools based on user prompts using LLM-powered decision making.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [LangGraph Workflow](#langgraph-workflow)
- [Tool Selection Logic](#tool-selection-logic)
- [Guard Rails & Validation](#guard-rails--validation)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [Future Enhancements](#future-enhancements)

## Overview

The Orchestrator Agent serves as an intelligent routing layer that:

- Receives user prompts from upstream services (DXAIService)
- Analyzes query intent using LLM
- Dynamically selects the most appropriate tool based on capabilities
- Invokes the selected tool and returns processed responses
- Applies guard rails for confidence validation

## Architecture

| Component | Technology |
|-----------|------------|
| **Framework** | Python with LangGraph |
| **Deployment** | Amazon EKS (Kubernetes) / AgentCore (Future) |
| **Web Server** | FastAPI (recommended) |
| **LLM Integration** | For tool selection and routing decisions |
| **Configuration** | YAML-based tool definitions |

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   DXAIService   │────▶│  Orchestrator Agent  │────▶│   Tool Agents   │
│                 │     │    (LangGraph)       │     │  (IBT, Claims)  │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │     LLM      │
                        │  (Decision)  │
                        └──────────────┘
```

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd orchestrator-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Tool Configuration (tools-config.yaml)

Tools are defined in a YAML configuration file. Each tool includes:

- **name**: Unique identifier for the tool
- **description**: What the tool handles
- **endpoint**: Internal API endpoint
- **capabilities**: List of capabilities the tool provides
- **parameters**: Required and optional parameters
- **examples**: Sample prompts and reasoning for tool selection

```yaml
tools:
  - name: "IBTAgent"
    description: "Handles insurance benefit and coverage inquiries"
    endpoint: "https://ibt-service.internal/api/v1"
    capabilities:
      - "benefit inquiries"
      - "coverage questions"
      - "policy information"
    parameters:
      required:
        - "userPrompt"
        - "userName"
      optional:
        - "policyNumber"
        - "memberType"
    examples:
      - prompt: "What are my dental benefits?"
        reasoning: "User asking about specific benefit coverage"
      - prompt: "Is physical therapy covered?"
        reasoning: "Coverage inquiry for specific service"

  - name: "ClaimsAgent"
    description: "Processes claims-related queries"
    endpoint: "https://claims-service.internal/api/v1"
    capabilities:
      - "claim status"
      - "claim submission"
      - "claim history"
    parameters:
      required:
        - "userPrompt"
        - "userName"
      optional:
        - "claimNumber"
    examples:
      - prompt: "What's my claim status?"
        reasoning: "User requesting claim information"
```

## API Endpoints

### 1. Process Query/Prompt Endpoint

**Endpoint:** `POST /invocations`

Receives user prompts, determines appropriate tool, and returns processed response.

**Request Body:**

```json
{
  "userPrompt": "string",
  "sessionId": "string",
  "context": {
    "userName": "string",
    "userType": "string",
    "source": "string",
    "promptId": "string"
  }
}
```

**Response:**

```json
{
  "response": "string",
  "toolUsed": "string",
  "confidence": "number",
  "sessionId": "string"
}
```

### 2. Health Check Endpoint

**Endpoint:** `GET /ping`

Returns service health and availability status.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "ISO-8601 datetime"
}
```

## LangGraph Workflow

The orchestrator follows a 7-step workflow process:

```
┌─────────────────────┐
│  1. Input Validation │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  2. Query Analysis   │  ◄── LLM understands user intent
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  3. Tool Selection   │  ◄── LLM selects best tool
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  4. Guard Rails      │  ◄── Validate confidence & availability
└──────────┬──────────┘
           ▼
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐ ┌──────────────┐
│ 5. Tool │ │ Generic Msg  │
│ Invoke  │ │ (Low Conf)   │
└────┬────┘ └──────┬───────┘
     │             │
     └──────┬──────┘
            ▼
┌─────────────────────┐
│ 6. Response Process  │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  7. Error Handling   │
└─────────────────────┘
```

### Workflow Steps

1. **Input Validation** - Validate request format and required fields
2. **Query Analysis** - Use LLM to understand user intent
3. **Tool Selection** - Determine best tool based on capabilities and query
4. **Guard Rails Check** - Validate confidence score and tool availability
5. **Tool Invocation** - Call selected tool with formatted parameters OR return generic message
6. **Response Processing** - Format and return tool response
7. **Error Handling** - Handle failures and fallback scenarios

## Tool Selection Logic

### LLM Decision Making Process

The LLM analyzes queries through these steps:

1. Parse user query for intent and key topics
2. Map query requirements to available tool capabilities
3. Evaluate parameter availability and completeness
4. Calculate confidence score based on matching accuracy
5. Apply guard rails and validation checks
6. Return tool selection with reasoning and confidence score

### Decision Criteria

- Tool capability alignment with query requirements
- Availability of required parameters for tool execution
- Query complexity and tool expertise match
- Historical success patterns for similar queries

### LLM Prompt Template

```
Given the user query: "{user_query}"

Available tools and their capabilities:
{tools_info}

Analyze the query and select the most appropriate tool. Consider:
1. Query intent and topic
2. Tool capabilities and expertise
3. Required parameters availability

Respond with:
- Selected tool name (or "NO_TOOL" if no suitable tool found)
- Reasoning for selection
- Confidence score (1-10)

If confidence is below 7 or no tool matches, respond with "NO_TOOL".
```

## Guard Rails & Validation

### Confidence Threshold Logic

| Threshold | Action |
|-----------|--------|
| **>= 7.0** | Proceed with tool invocation |
| **< 7.0** | Trigger fallback response |
| **NO_TOOL** | Return generic helpful message |

- Minimum confidence score of **7.0 out of 10.0** required for tool selection
- Confidence calculation based on query-tool capability matching accuracy
- Multiple validation layers ensure appropriate tool routing

## Error Handling

### Error Types

| Error Type | Description |
|------------|-------------|
| **Tool Unavailable** | Selected tool is down or unreachable |
| **LLM Failure** | LLM service unavailable or error |
| **Configuration Error** | Invalid tools configuration |
| **Timeout Error** | Tool response timeout |
| **Validation Error** | Invalid request format |
| **Low Confidence** | Query understanding below threshold |
| **No Tool Match** | No applicable tool found for query |

### Fallback Strategy

1. **Low Confidence/No Tool Match**: Return generic helpful message
2. **Tool Failure**: Retry with exponential backoff
3. **All Tools Down**: Return service unavailable message
4. Log detailed error information for all scenarios

### Generic Response Messages

```json
{
  "no_tool_found": "I'm sorry, I couldn't find the right resource to help with your question. Please try rephrasing your query or contact our support team for assistance.",

  "low_confidence": "I'm not entirely sure I understand your question. Could you please provide more details or rephrase your request?",

  "service_unavailable": "I'm currently experiencing technical difficulties. Please try again in a few moments or contact support if the issue persists."
}
```

> **Note:** All pre-defined response messages are placeholder text and will be updated once business stakeholders provide final approved verbiage.

## Logging

The service implements comprehensive logging:

- **Request/Response Logging** - With correlation IDs for traceability
- **Tool Selection Accuracy Metrics** - Track LLM decision quality
- **Performance Metrics** - Latency and throughput monitoring
- **Error Rate Tracking** - Per-tool error rate monitoring

## Future Enhancements

### MCP Integration (Model Context Protocol)

Future releases will support MCP to enable:

- **Dynamic Tool Discovery** - Automatic detection and registration of available tools
- **Runtime Tool Registration** - Tools can register/unregister without service restart
- **Standardized Tool Interface** - Consistent tool communication protocol
- **Enhanced Scalability** - Simplified addition of new tools and capabilities

### PI2 Release Notes

For the PI2 release, only the **IBTAgent** tool will be available. The LLM-based tool selection architecture is implemented to provide:

- **Future-Proof Foundation** - Framework ready for multiple tools
- **Scalable Architecture** - Easy addition of new tools (ClaimsAgent, NavigationAgent, etc.)
- **Consistent Interface** - Uniform prompt/query processing
- **Testing & Validation** - Validation of LLM decision-making logic

**PI2 Behavior:** All valid queries route to IBTAgent with LLM providing confidence scoring and query understanding validation. Invalid or out-of-scope queries trigger guard rails with generic responses.

---

## Development Guidelines

> **IMPORTANT:** All API development must strictly follow FEPOC API guidelines including naming conventions, security standards, authentication protocols, and response formats.

Refer to: `BCBSA_Web_Services_API_Guidelines_2022.docx`

## License

[Add license information]

## Contributing

[Add contribution guidelines]

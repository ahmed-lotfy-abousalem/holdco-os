# Architecture Overview

## 1. Design goal

HoldCo OS should behave like a federated operating layer for a holding company:

- each subsidiary owns its own data
- each subsidiary exposes a narrow, well-defined API
- the orchestrator decides which subsidiary or subsidiaries should answer a question
- the final response is synthesized from live results, not copied into a central store

## 2. Proposed components

### Subsidiary data layer
Each subsidiary has its own local data folder containing:

- SQLite or CSV transaction data
- plain-text document files that simulate contracts, invoices, and reports
- optional embeddings or vector index stored locally

### Subsidiary service layer
Each subsidiary exposes a FastAPI app with endpoints such as:

- GET /health
- GET /transactions
- GET /financial-summary
- POST /documents/search

This service is the local boundary for that subsidiary.

### Orchestrator layer
A separate FastAPI app acts as the holding-company coordinator.

It should:

- receive the user question
- classify which subsidiary or subsidiaries are relevant
- call the relevant subsidiary services
- combine the results into one answer

### LLM layer
The local model is hosted through Ollama.

The orchestrator and optionally the subsidiary services can use the local LLM for:

- routing decisions
- question understanding
- summarization
- response formatting

## 3. Request flow

1. The user asks a question.
2. The orchestrator decides which subsidiaries should participate.
3. The orchestrator calls the relevant subsidiary FastAPI endpoints.
4. Each subsidiary returns its local result set.
5. The orchestrator synthesizes one coherent answer.

## 4. Repository structure

```text
holdco-os/
  README.md
  docs/
    architecture.md
    implementation-plan.md
    testing-plan.md
  data/
    retail/
    logistics/
    finance/
  app/
    shared/            # subsidiary-agnostic: schemas, data loading, REST/MCP app factories
    subsidiaries/
      retail/           # service.py (REST, for manual testing) + mcp_server.py (MCP, for the LLM)
      logistics/
      finance/
    orchestrator/       # main.py (FastAPI app + agentic tool-calling loop) + mcp_client.py
  tests/
    shared/
    subsidiaries/
    orchestrator/
```

Each subsidiary runs two processes: a REST API (ports 8001-8003, kept for curl/Swagger manual testing)
and an MCP server (ports 9001-9003, what the orchestrator's LLM actually calls). Both are thin
compositions built from the shared factories in `app/shared/`, so adding a fourth subsidiary means
adding a data folder plus two ~10-line entrypoint files, not duplicating logic.

## 5. Why this fits your brief

- It avoids Flask entirely.
- It avoids a federated learning server because this is not a training workflow.
- It keeps the architecture aligned with your local-LLM and MCP-oriented interview story.

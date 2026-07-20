# HoldCo OS

A FastAPI-first prototype of a federated holding-company orchestration system. Each subsidiary
(retail, logistics, finance) owns its own data behind its own service boundary. A local LLM
(via [Ollama](https://ollama.com)) drives an agentic orchestrator that decides which subsidiaries
are relevant to a question, calls their tools over the [Model Context Protocol](https://modelcontextprotocol.io),
and synthesizes one answer — without ever centralizing raw subsidiary data.

See [docs/architecture.md](docs/architecture.md) for the full design and repository layout, and
[docs/implementation-plan.md](docs/implementation-plan.md) for how the project was built phase by phase.

## Core direction

- FastAPI, not Flask.
- Each subsidiary's data stays isolated behind its own service boundary — never copied into a shared store.
- A local LLM through Ollama, not a hosted API.
- Subsidiary capabilities are exposed to the LLM as real MCP tools, not hardcoded routing logic.

## Prerequisites

- Python 3.11
- [Ollama](https://ollama.com) installed and running, with a tool-calling-capable model pulled
  (this project defaults to `qwen2.5:7b`):
  ```
  ollama pull qwen2.5:7b
  ```

## Setup

```powershell
python -m venv .venv311
& ".venv311\Scripts\Activate.ps1"
pip install -r requirements-dev.txt
```

## Running it

Seven processes total: each subsidiary runs a REST API (manual testing) and an MCP server (what
the orchestrator's LLM actually calls), plus the orchestrator itself. Run each in its own terminal
(with the venv activated):

```powershell
uvicorn app.subsidiaries.retail.service:app --port 8001
uvicorn app.subsidiaries.logistics.service:app --port 8002
uvicorn app.subsidiaries.finance.service:app --port 8003
python -m app.subsidiaries.retail.mcp_server
python -m app.subsidiaries.logistics.mcp_server
python -m app.subsidiaries.finance.mcp_server
uvicorn app.orchestrator.main:app --port 8000
```

Then open **http://127.0.0.1:8000** for the chat UI, or use the REST APIs' interactive docs at
`http://127.0.0.1:8001/docs` (and `8002`/`8003`).

| Service | REST port | MCP port |
|---|---|---|
| Retail | 8001 | 9001 |
| Logistics | 8002 | 9002 |
| Finance | 8003 | 9003 |
| Orchestrator | 8000 | — |

## Testing

```powershell
pytest tests/ -v
```

All tests mock external calls (Ollama, MCP) — no running services required. See
[docs/testing-plan.md](docs/testing-plan.md) for the manual test checklist.

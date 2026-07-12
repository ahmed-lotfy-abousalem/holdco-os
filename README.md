# HoldCo OS

This workspace is being structured as a FastAPI-first, markdown-led prototype for a federated holding-company orchestration system.

## Core direction

- Use FastAPI instead of Flask.
- Keep each subsidiary's data isolated behind its own service boundary.
- Use a local LLM through Ollama rather than a training server.
- Keep the implementation plan visible in markdown so it can be reviewed, executed, and improved iteratively.

## Architecture in one sentence

A coordinator service routes each user question to the relevant subsidiary service(s), collects the results, and synthesizes a final answer without centralizing raw subsidiary data.

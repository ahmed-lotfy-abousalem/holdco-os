# Implementation Plan

## Phase 0 — setup and scaffolding

- create the repository structure
- define the initial data format for each subsidiary
- set up a Python environment with FastAPI, Uvicorn, and basic retrieval dependencies
- decide whether to use SQLite, CSV, or both for transactions

## Phase 1 — single subsidiary first

Build one subsidiary end to end before expanding.

Goals:

- load local transactions and documents
- build a retrieval flow over the subsidiary documents
- expose a FastAPI service for transactions and document search
- validate that answers stay scoped to that subsidiary

## Phase 2 — expand to three subsidiaries

Replicate the same pattern for:

- retail
- logistics
- finance

Each subsidiary should have its own isolated data folder and its own service.

## Phase 3 — orchestrator service

Introduce a coordinator service that:

- receives questions
- routes them to one or more subsidiary services
- aggregates the results
- returns a final synthesis

Start with deterministic routing rules, then improve to LLM-based routing if needed.

## Phase 4 — local LLM integration

Connect the orchestrator to Ollama.

Use the local model to:

- classify the relevant subsidiaries
- summarize findings
- improve formatting and answer quality

## Phase 5 — testing and hardening

Add tests for:

- transaction filtering
- document retrieval scope
- routing correctness
- graceful handling when one subsidiary is unavailable

## Phase 6 — demo polish

Prepare a short live demo that shows:

1. single-subsidiary answer
2. degraded answer when one service is down
3. restored answer after recovery

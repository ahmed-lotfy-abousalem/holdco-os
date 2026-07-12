# CLAUDE.md

This file is a project-specific instruction file for AI coding assistants.

## What it is

A CLAUDE file tells an assistant how to behave when working in this repository. It can define:

- the preferred framework and language
- the architecture style
- the folder structure
- the testing and verification workflow
- any project-specific conventions

## Why it matters here

This project is meant to be built iteratively and documented clearly. A CLAUDE file helps keep the assistant aligned with your decisions, such as:

- use FastAPI, not Flask
- keep data local to each subsidiary
- prefer markdown-driven planning
- use local Ollama-based LLM integration
- verify changes before claiming completion

## What this file should guide

When working on this project, the assistant should:

1. preserve the federated architecture
2. avoid centralizing raw subsidiary data
3. prefer small, testable changes
4. verify behavior with actual commands or tests
5. keep documentation updated as the system evolves

## Practical example

If a change would introduce a central database or move data into a shared store, this file should steer the assistant away from that choice.

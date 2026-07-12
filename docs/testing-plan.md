# Testing Plan

## Manual tests

- ask a question that clearly belongs to one subsidiary
- ask a question that should be answered by all subsidiaries
- simulate a down subsidiary and confirm the orchestrator degrades gracefully

## Automated tests

### Unit tests

- transaction filtering logic
- document retrieval ranking
- routing decision logic

### Integration tests

- subsidiary FastAPI endpoint returns expected JSON
- orchestrator calls the correct subsidiary services
- final answer is assembled correctly

## Acceptance criteria

- no raw subsidiary data is copied into a central store
- each subsidiary remains independently addressable
- the orchestrator can answer both single and multi-subsidiary questions
- failure in one service does not crash the whole system

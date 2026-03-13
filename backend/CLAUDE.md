# Backend — Claude Context

## Architecture
- FastAPI app entry: `app/main.py`
- 8 AI agents in `app/agents/` — all inherit `BaseAgent`
- Event-driven workflows via LlamaIndex in `app/workflows/`
- Neo4j graph + vector store via `app/services/neo4j_store.py`
- All LLM calls routed through `app/services/llm_service.py`

## Key Patterns
- Pydantic models for all schemas: `app/models/specs.py`
- Guardrails pipeline: InputValidator → PromptGuard → [LLM] → PIIDetector → OutputFilter
- WebSocket progress streaming via `broadcast_workflow_progress`
- Async everywhere: use `asyncio.gather()` for independent agent tasks

## Testing
- `pytest tests/unit/ -v` for unit tests
- `pytest tests/integration/` for integration tests (requires Neo4j or mocks)
- `pytest tests/contract/` for OpenAPI/Pydantic schema verification
- `ruff check . --quiet` for linting

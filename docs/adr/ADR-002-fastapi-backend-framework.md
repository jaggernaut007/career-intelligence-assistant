# ADR-002: FastAPI as Backend Framework

## Status
Accepted

## Context
The Career Intelligence Assistant requires a backend framework that supports:
- Async I/O for parallel agent execution (7 agents running concurrently via `asyncio.gather()`)
- WebSocket connections for real-time progress streaming to the frontend
- Auto-generated API documentation (Swagger/ReDoc) for the multi-endpoint REST API
- Native Pydantic integration for strict input/output validation on all agent contracts
- High performance comparable to Node.js/Go for handling concurrent LLM API calls

Alternatives considered:
- **Django REST Framework**: Mature, but async support is incomplete; ORM is unnecessary (Neo4j is the data layer)
- **Flask**: Lightweight, but lacks native async, WebSocket, and Pydantic integration
- **Express.js (Node.js)**: Good async, but Python is required for LlamaIndex, sentence-transformers, and Presidio

## Decision
Use FastAPI (>=0.109.2) with Uvicorn as the ASGI server. All agents, services, and API routes use `async/await`. WebSocket endpoints provide real-time progress via `/ws/progress/{session_id}`.

## Consequences
- **Easier**: Automatic OpenAPI docs, native async, Pydantic validation on all routes, WebSocket support built-in, excellent Python ML/AI library ecosystem compatibility
- **Harder**: Requires understanding of async Python patterns; Uvicorn worker management for production; no built-in ORM (not needed with Neo4j)

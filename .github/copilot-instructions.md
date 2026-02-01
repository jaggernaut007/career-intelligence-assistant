# AI Copilot Instructions for Career Intelligence Assistant

## Architecture & Project Structure
- **Core Pattern**: Modular Monolith with intelligent agents orchestrated by **LlamaIndex Workflow**.
- **Backend**: FastAPI (`backend/app/main.py`) serving a multi-agent system found in `backend/app/agents/`.
- **Frontend**: React + Vite + TypeScript (`frontend/`), communicating via REST & WebSockets (`/ws/{analysis_id}`).
- **Data Layer**: **Neo4j** (Graph + Vector Store) handled by `backend/app/services/neo4j_store.py`.
- **Workflow Engine**: Event-driven architecture using `LlamaIndex` workflows in `backend/app/workflows/analysis_workflow.py`.

## Critical Developer Workflows
- **Run Backend**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` (Requires `.env` with keys).
- **Run Frontend**: `cd frontend && npm run dev`.
- **Run Tests**:
  - Unit: `pytest tests/unit/ -v` (Use `@pytest.mark.asyncio` for async tests).
  - Integration: `pytest tests/integration/` (Requires local Neo4j or mocks).
  - Contract: `pytest tests/contract/` (Verifies OpenAPI/Pydantic schemas).
- **Environment**: `.env` variables (OPENAI_API_KEY, NEO4J_URI, etc.) are loaded *first* in `backend/app/main.py`.

## Code Conventions & Patterns

### 1. Agent Implementation (Strict Contract)
All agents **MUST** inherit from `BaseAgent` (`backend/app/agents/base_agent.py`) and implement:
- `input_schema` & `output_schema`: Strict Pydantic models from `backend/app/models/specs.py`.
- `process(input_data)`: Main async logic returning `AgentOutput`.
- `health_check()`: Diagnostic method.
- **Example**: See `backend/app/agents/resume_parser.py`.

### 2. Workflow Orchestration
- Use **LlamaIndex Workflows** (`backend/app/workflows/`), NOT manual orchestration.
- Define events in `events.py` (e.g., `ResumeParseEvent`).
- Use `@step` decorators in `CareerAnalysisWorkflow` for parallel execution (e.g., `asyncio.gather` for parsing resume vs JDs).
- **State Management**: Use `ctx.store.set()` / `ctx.store.get()` within workflow steps.

### 3. Asynchronous & Performance
- **Always** use `async`/`await` for I/O (Database, LLM, API).
- Use `asyncio.gather()` for independent agent tasks.
- **Neo4j**: Use the async driver pattern visible in `backend/app/services/neo4j_store.py`.

### 4. Security & Guardrails
- **Pre-Processing**: Apply `InputValidator` and `PromptGuard` (`backend/app/guardrails/`) before sending data to LLMs.
- **Post-Processing**: Apply `PIIDetector` and `OutputFilter` before returning data/storing in Neo4j.
- **Privacy**: Redact PII *before* specific persistence layers if required by `specs/agent-contracts.md`.

## Integration Points
- **WebSocket**: Use `broadcast_workflow_progress` (in `workflows/analysis_workflow.py`) to stream updates to frontend `StatusReporter`.
- **LLM Service**: Route all LLM calls through `backend/app/services/llm_service.py` (do not instantiate OpenAI client directly).
- **Testing Mocks**: When writing unit tests, **always** mock `Neo4j` and `OpenAI` calls to prevent costs and flakiness.

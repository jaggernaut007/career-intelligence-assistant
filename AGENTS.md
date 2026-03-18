# AGENTS.md

## Project Overview
Career Intelligence Assistant — AI-powered resume analysis and job matching platform using a multi-agent architecture with FastAPI backend and React frontend.

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, LlamaIndex Workflows, Pydantic v2
- **Frontend**: React 18, TypeScript 5.3, Vite 5, Zustand, Tailwind CSS 3.4, React Query 5
- **Database**: Neo4j 5.17 (Graph + Vector Store)
- **LLM**: OpenAI (`gpt-5.4-mini` by default) via `backend/app/services/llm_service.py`
- **Testing**: pytest (backend), Vitest (frontend)
- **Code Intelligence**: Nexus-MCP (hybrid search, call graphs, impact analysis, code quality)
- **Linting**: ruff + black + isort (backend), ESLint + Prettier (frontend)

## Build & Test Commands
```bash
# Backend
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd backend && pytest tests/unit/ -v
cd backend && pytest tests/integration/
cd backend && ruff check .

# Frontend
cd frontend && npm run dev
cd frontend && npm test
cd frontend && npm run lint

# Full stack
docker compose up --build
./scripts/init.sh
```

## Code Standards
- All agents inherit from `BaseAgent` and implement `input_schema`, `output_schema`, `process()`, `health_check()`
- Route all LLM calls through `backend/app/services/llm_service.py`
- Use Pydantic models for all request/response schemas (`backend/app/models/specs.py`)
- Use LlamaIndex Workflows for orchestration, with events in `workflows/events.py`
- Apply guardrails (InputValidator, PromptGuard) before LLM calls, (PIIDetector, OutputFilter) after
- Use `async`/`await` for all I/O; use `asyncio.gather()` for independent tasks
- Use direct imports (e.g., `from app.agents.resume_parser import ResumeParser`)
- Backend line length: 100 chars (black/ruff). Frontend: Prettier defaults

## Testing Requirements
- All new features require tests before marking complete
- Verify tests pass via tool call before marking a task done
- Backend: use `@pytest.mark.asyncio` for async tests; mock Neo4j and OpenAI in unit tests
- Frontend: use Testing Library + MSW for component/API tests

## Definition of Done
1. Tests pass (verified via tool call)
2. Linter passes (`ruff check .` for backend, `npm run lint` for frontend)
3. Docs updated if behaviour changed
4. PROGRESS.md updated with what was done
5. E2E smoke test passes (`./scripts/init.sh`)

## Code Intelligence (Nexus-MCP)
- Before modifying a function: run `find_callers` + `impact` to understand blast radius
- Before implementing new features: run `search` to find existing patterns
- At session start: run `overview` to orient on project structure
- For code understanding: use `explain` on unfamiliar symbols instead of manually reading files
- For refactoring: run `analyze` on the target path to check complexity and quality

## Session Start Protocol
1. Read PROGRESS.md for current project state
2. Run `./scripts/init.sh` to verify the app is in a working state
3. Fix any broken state before starting new work

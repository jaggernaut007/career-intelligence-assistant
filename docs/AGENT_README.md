# Career Intelligence Assistant

A multi-agent AI system that analyzes resumes against job descriptions, providing fit analysis, skill gap detection, and interview preparation.

## Features

- **Resume Analysis** - Upload PDF, DOCX, or plain text resumes
- **Job Matching** - Compare against multiple job descriptions (up to 5)
- **Fit Score** - Percentage-based match score with skill breakdown
- **Skill Gap Detection** - Identify missing required and nice-to-have skills
- **Interview Prep** - Likely questions with STAR-format answer examples
- **Market Insights** - Salary ranges and demand trends
- **Chat Assistant** - Ask questions about your resume-job fit
- **Privacy Protection** - Automatic PII detection and redaction

## Quick Start

```bash
# Clone and configure
git clone <repository-url>
cd career-intelligence-assistant
cp .env.example .env
# Edit .env with your API keys (OpenAI, Neo4j, HuggingFace)

# Run with Docker
docker-compose up --build
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

See [Quick Start Guide](docs/getting-started/quick-start.md) for detailed setup.

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | React 18 + Vite + TypeScript + Tailwind |
| **Backend** | Python 3.11 + FastAPI |
| **AI/LLM** | OpenAI GPT + LlamaIndex |
| **Database** | Neo4j AuraDB (graph + vector) |
| **Embeddings** | nomic-embed-text-v1.5 |

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐
│   Frontend  │────►│   Backend   │────►│       AI Agents             │
│  (React)    │◄────│  (FastAPI)  │◄────│  (LlamaIndex Orchestrator)  │
└─────────────┘     └─────────────┘     └─────────────────────────────┘
                           │                        │
                           ▼                        ▼
                    ┌─────────────┐          ┌─────────────┐
                    │  Neo4j DB   │          │  OpenAI API │
                    │(graph+vector)│          │  (GPT-5.2)  │
                    └─────────────┘          └─────────────┘
```

**7 AI Agents**: Resume Parser, JD Analyzer, Skill Matcher, Recommendation, Interview Prep, Market Insights, Chat Fit

## Documentation

| Topic | Link |
|-------|------|
| **Getting Started** | [Quick Start](docs/getting-started/quick-start.md) |
| **Architecture** | [Overview](docs/architecture/overview.md) |
| **API Reference** | [REST API](docs/backend/api-reference.md) |
| **Agent System** | [Agents](docs/backend/agents.md) |
| **Security** | [Guardrails & Rate Limiting](docs/backend/security.md) |
| **Database Schema** | [Neo4j Schema](docs/architecture/database-schema.md) |
| **Deployment** | [GCP Cloud Run](docs/deployment/gcp-cloud-run.md) |
| **Environment** | [Variables](docs/deployment/environment-variables.md) |
| **Frontend** | [Components](docs/frontend/components.md) \| [State](docs/frontend/state-management.md) |
| **Testing** | [Testing Guide](docs/contributing/testing.md) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/session` | Create session |
| `POST` | `/api/v1/upload/resume` | Upload resume |
| `POST` | `/api/v1/upload/job-description` | Add job |
| `POST` | `/api/v1/analyze` | Run analysis |
| `GET` | `/api/v1/results/{session_id}` | Get results |
| `POST` | `/api/v1/chat` | Chat about job fit |
| `WS` | `/ws/progress/{session_id}` | Real-time progress |

Full API documentation: [API Reference](docs/backend/api-reference.md)

## Running Tests

```bash
# Backend
cd backend
uv run pytest                    # All tests
uv run pytest tests/unit -v      # Unit tests only

# Frontend
cd frontend
npm test                         # All tests
npm run test:coverage            # With coverage
```

## Development

```bash
# Backend (with hot reload)
cd backend
uv run uvicorn app.main:app --reload --port 8000

# Frontend (with hot reload)
cd frontend
npm run dev
```

## Performance

| Scenario | Response Time |
|----------|---------------|
| 1 resume + 1 job | ~70-90 seconds |
| 1 resume + 5 jobs | ~80-120 seconds |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass
5. Submit a Pull Request

## License

MIT License

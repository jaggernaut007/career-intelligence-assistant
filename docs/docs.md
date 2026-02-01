# Career Intelligence Assistant Documentation

Welcome to the Career Intelligence Assistant documentation. This multi-agent AI system analyzes resumes against job descriptions, providing fit analysis, skill gap detection, and interview preparation.

## Quick Links

| Section | Description |
|---------|-------------|
| [Quick Start](getting-started/quick-start.md) | Get running in 5 minutes |
| [Architecture Overview](architecture/overview.md) | System design and data flow |
| [API Reference](backend/api-reference.md) | REST API endpoints |
| [Deployment Guide](deployment/gcp-cloud-run.md) | Production deployment |

## Documentation Structure

```
docs/
├── getting-started/
│   ├── quick-start.md          # 5-minute setup
│   └── environment-setup.md    # Detailed configuration
├── architecture/
│   ├── overview.md             # System architecture
│   └── database-schema.md      # Neo4j graph schema
├── backend/
│   ├── api-reference.md        # REST API docs
│   ├── agents.md               # AI agent documentation
│   └── services.md             # Core services
├── frontend/
│   ├── components.md           # React components
│   └── state-management.md     # Zustand stores
└── deployment/
    ├── local-development.md    # Docker Compose setup
    ├── gcp-cloud-run.md        # GCP deployment
    └── environment-variables.md # All env vars
```

## Tech Stack Overview

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18 + Vite + TypeScript + Tailwind |
| **State** | Zustand + React Query |
| **Backend** | FastAPI (Python 3.11+) |
| **AI/LLM** | OpenAI GPT + LlamaIndex |
| **Database** | Neo4j AuraDB (graph + vector) |
| **Embeddings** | nomic-embed-text-v1.5 |
| **Deployment** | Docker + GCP Cloud Run |

## Agent System

The system uses 7 specialized AI agents orchestrated via LlamaIndex:

1. **Resume Parser** - Extracts skills, experience, education from resumes
2. **JD Analyzer** - Parses job description requirements
3. **Skill Matcher** - Calculates fit scores and identifies gaps
4. **Recommendation** - Generates actionable improvement suggestions
5. **Interview Prep** - Creates interview questions with STAR examples
6. **Market Insights** - Provides salary ranges and career trends
7. **Chat Fit** - Conversational agent for Q&A about resume-job fit

See [Agent Documentation](backend/agents.md) for details.

## Docker Setup

### Prerequisites

- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later (included with Docker Desktop)

Verify installation:
```bash
docker --version
docker compose version
```

### Environment Setup

Ensure your `.env` file exists in the project root with the required variables:
```bash
cp .env.example .env
```

Required environment variables:
| Variable | Description |
|----------|-------------|
| `NEO4J_URI` | Neo4j AuraDB connection URI |
| `NEO4J_USERNAME` | Neo4j username |
| `NEO4J_PASSWORD` | Neo4j password |
| `OPENAI_API_KEY` | OpenAI API key |
| `HF_TOKEN` | HuggingFace token for embeddings |

### Development Mode

Development mode includes hot-reload for both frontend and backend, with source code mounted as volumes.

```bash
# Build and start all services
docker compose up --build

# Run in detached mode (background)
docker compose up -d --build

# View logs
docker compose logs -f

# View logs for specific service
docker compose logs -f backend
docker compose logs -f frontend

# Stop containers
docker compose down

# Stop and remove volumes
docker compose down -v
```

### Production Mode

Production mode uses optimized builds with Nginx for the frontend and multi-worker Uvicorn for the backend.

```bash
# Build and run production containers
docker compose -f docker-compose.prod.yml up --build -d

# Check container health status
docker compose -f docker-compose.prod.yml ps

# View production logs
docker compose -f docker-compose.prod.yml logs -f

# Stop production containers
docker compose -f docker-compose.prod.yml down
```

### Rebuilding Containers

```bash
# Rebuild without cache (useful after dependency changes)
docker compose build --no-cache

# Rebuild specific service
docker compose build --no-cache backend
docker compose build --no-cache frontend
```

### Access Points

| Service | Development | Production |
|---------|-------------|------------|
| Frontend | http://localhost:5173 | http://localhost:80 |
| Backend API | http://localhost:8000 | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs | http://localhost:8000/docs |

### Container Architecture

| Container | Base Image | Purpose |
|-----------|------------|---------|
| `career-assistant-backend` | Python 3.11-slim | FastAPI backend with Uvicorn |
| `career-assistant-frontend` | Node 20 Alpine (dev) / Nginx Alpine (prod) | React frontend |

### Troubleshooting

**Port conflicts:**
```bash
# Check if ports are in use
lsof -i :8000
lsof -i :5173
```

**Container not starting:**
```bash
# Check container logs
docker compose logs backend
docker compose logs frontend

# Inspect container
docker inspect career-assistant-backend
```

**Reset everything:**
```bash
# Remove all containers, networks, and volumes
docker compose down -v --rmi local

# Rebuild from scratch
docker compose up --build
```

**Health check failures:**
```bash
# Check backend health endpoint directly
curl http://localhost:8000/health

# Check container health status
docker inspect --format='{{.State.Health.Status}}' career-assistant-backend
```

## Getting Help

- Check the [Troubleshooting Guide](getting-started/troubleshooting.md)
- Review [Environment Variables](deployment/environment-variables.md)
- Examine the [API Reference](backend/api-reference.md)

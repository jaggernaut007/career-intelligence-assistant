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

## Getting Help

- Check the [Troubleshooting Guide](getting-started/troubleshooting.md)
- Review [Environment Variables](deployment/environment-variables.md)
- Examine the [API Reference](backend/api-reference.md)

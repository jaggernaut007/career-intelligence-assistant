# Quick Start Guide

Get the Career Intelligence Assistant running in 5 minutes.

## Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- [OpenAI API key](https://platform.openai.com/)
- [Neo4j AuraDB](https://neo4j.com/cloud/aura/) account (free tier available)
- [HuggingFace token](https://huggingface.co/settings/tokens)

## 1. Clone and Configure

```bash
git clone <repository-url>
cd career-intelligence-assistant

# Copy environment template
cp .env.example .env
```

## 2. Set Environment Variables

Edit `.env` with your credentials:

```ini
# Required - OpenAI
OPENAI_API_KEY=sk-your-api-key-here

# Required - Neo4j AuraDB
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password-here

# Required - HuggingFace (for embeddings)
HF_TOKEN=hf_your-token-here

# Optional - defaults work for local dev
SESSION_SECRET_KEY=change-this-in-production
```

## 3. Start with Docker Compose

```bash
docker-compose up --build
```

This starts:
- **Backend** at `http://localhost:8000`
- **Frontend** at `http://localhost:5173`

## 4. Verify Installation

1. Open `http://localhost:5173` in your browser
2. Check API health: `curl http://localhost:8000/health`
3. View API docs: `http://localhost:8000/docs`

## 5. Use the Application

1. **Upload Resume** - PDF, DOCX, or plain text
2. **Add Job Descriptions** - Paste job postings (up to 5)
3. **Run Analysis** - Get fit scores, skill gaps, recommendations
4. **Explore Results** - Interview prep, market insights

## Alternative: Run Without Docker

### Backend

```bash
cd backend
uv sync                          # Install dependencies
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Response Times

| Scenario | Expected Time |
|----------|---------------|
| 1 resume + 1 job | ~70-90 seconds |
| 1 resume + 5 jobs | ~80-120 seconds |
| 1 resume + 10 jobs | ~90-140 seconds |

## Next Steps

- [Environment Setup](environment-setup.md) - Detailed configuration
- [API Reference](../backend/api-reference.md) - REST endpoints
- [Architecture Overview](../architecture/overview.md) - System design

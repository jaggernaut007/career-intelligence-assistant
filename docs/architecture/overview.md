# Architecture Overview

The Career Intelligence Assistant is a multi-agent AI system that analyzes resumes against job descriptions.

## System Context

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              External Services                               │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│     OpenAI API      │   Neo4j AuraDB      │       HuggingFace               │
│   (GPT-5.2 LLM)     │ (Graph + Vector)    │   (Embeddings API)              │
└──────────┬──────────┴──────────┬──────────┴──────────────┬──────────────────┘
           │                     │                         │
           └─────────────────────┼─────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────────────┐
│                                │                                             │
│  ┌──────────────────┐    ┌─────┴─────┐    ┌──────────────────┐             │
│  │    Frontend      │    │  Backend  │    │    AI Agents     │             │
│  │  (React/Vite)    │◄──►│ (FastAPI) │◄──►│  (LlamaIndex)    │             │
│  └──────────────────┘    └───────────┘    └──────────────────┘             │
│                                                                             │
│                    Career Intelligence Assistant                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │
                          ┌──────┴──────┐
                          │    User     │
                          │  (Browser)  │
                          └─────────────┘
```

---

## Component Architecture

### Frontend (React)

```
┌─────────────────────────────────────────────────────────────────┐
│                         React Application                        │
├─────────────────────────────────────────────────────────────────┤
│  Components                                                      │
│  ├── Wizard (Upload → Jobs → Analysis → Explore)                │
│  ├── Results (FitScore, SkillGaps, Recommendations)             │
│  └── UI (Button, Card, Progress, Modal)                         │
├─────────────────────────────────────────────────────────────────┤
│  State Management                                                │
│  ├── Zustand (sessionStore, wizardStore, analysisStore)         │
│  └── React Query (server state, caching)                        │
├─────────────────────────────────────────────────────────────────┤
│  API Layer                                                       │
│  ├── Axios Client (HTTP requests)                               │
│  └── WebSocket (real-time progress)                             │
└─────────────────────────────────────────────────────────────────┘
```

### Backend (FastAPI)

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                      │
├─────────────────────────────────────────────────────────────────┤
│  API Layer                                                       │
│  ├── REST Routes (/api/v1/*)                                    │
│  ├── WebSocket (/ws/progress/{session_id})                      │
│  └── Middleware (CORS, Rate Limiting)                           │
├─────────────────────────────────────────────────────────────────┤
│  Guardrails                                                      │
│  ├── PII Detection (Presidio)                                   │
│  ├── Input Validation (file size, content length)               │
│  ├── Prompt Injection Defense                                   │
│  └── Output Filtering                                           │
├─────────────────────────────────────────────────────────────────┤
│  Workflow Orchestration                                          │
│  └── LlamaIndex Workflow (parallel agent execution)             │
├─────────────────────────────────────────────────────────────────┤
│  Agents                                                          │
│  ├── Resume Parser                                              │
│  ├── JD Analyzer                                                │
│  ├── Skill Matcher                                              │
│  ├── Recommendation                                             │
│  ├── Interview Prep                                             │
│  └── Market Insights                                            │
├─────────────────────────────────────────────────────────────────┤
│  Services                                                        │
│  ├── LlamaIndex Service (LLM orchestration)                     │
│  ├── Neo4j Store (graph + vector operations)                    │
│  ├── Embedding Service (HuggingFace)                            │
│  └── Document Parser (PDF/DOCX extraction)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Analysis Request Flow

```
1. User uploads resume (Frontend)
        │
        ▼
2. POST /upload/resume (Backend API)
        │
        ▼
3. Document Parser extracts text
        │
        ▼
4. PII Detector redacts sensitive info
        │
        ▼
5. Resume Parser Agent (LlamaIndex → OpenAI)
        │
        ▼
6. Store in Neo4j (graph + embeddings)
        │
        ▼
7. Return parsed resume to frontend
```

### Analysis Execution Flow

```
┌────────────────────────────────────────────────────────────────┐
│                    POST /analyze                                │
└────────────────────────────────┬───────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────┐
│              PHASE 1: Document Parsing (Parallel)               │
│                                                                 │
│    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│    │   Resume    │    │     JD      │    │     JD      │       │
│    │   Parser    │    │  Analyzer 1 │    │  Analyzer 2 │       │
│    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘       │
│           │                  │                  │               │
│           └──────────────────┼──────────────────┘               │
│                              │                                  │
│                     asyncio.gather()                            │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│              PHASE 2: Skill Matching (Parallel)                 │
│                                                                 │
│    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│    │   Matcher   │    │   Matcher   │    │   Matcher   │       │
│    │   Job 1     │    │   Job 2     │    │   Job N     │       │
│    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘       │
│           │                  │                  │               │
│           └──────────────────┼──────────────────┘               │
│                              │                                  │
│                     asyncio.gather()                            │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│              PHASE 3: Advanced Analysis (Parallel)              │
│                                                                 │
│    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│    │  Recommend  │    │  Interview  │    │   Market    │       │
│    │   Agent     │    │    Prep     │    │  Insights   │       │
│    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘       │
│           │                  │                  │               │
│           └──────────────────┼──────────────────┘               │
│                              │                                  │
│                     asyncio.gather()                            │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                    Return Results                               │
└────────────────────────────────────────────────────────────────┘
```

---

## Technology Choices

### Why FastAPI?

- **Async support** - Essential for parallel agent execution
- **Auto-generated docs** - Swagger UI and ReDoc
- **Pydantic integration** - Type-safe request/response validation
- **WebSocket support** - Real-time progress updates
- **High performance** - Comparable to Node.js and Go

### Why LlamaIndex?

- **Agent orchestration** - Built-in workflow management
- **RAG support** - Document parsing and retrieval
- **OpenAI integration** - Native LLM provider support
- **Extensibility** - Custom agents and tools

### Why Neo4j?

- **Graph relationships** - Natural skill-to-job matching
- **Vector search** - Semantic similarity via embeddings
- **Single database** - No separate vector store needed
- **Cypher queries** - Powerful graph traversal

### Why Zustand?

- **Minimal boilerplate** - Simpler than Redux
- **TypeScript support** - Full type safety
- **Small bundle size** - ~1KB gzipped
- **No providers** - Direct store access

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Layers                             │
├─────────────────────────────────────────────────────────────────┤
│  1. Rate Limiting (slowapi)                                     │
│     ├── 10 requests/minute per session                          │
│     └── 100 requests/hour per IP                                │
├─────────────────────────────────────────────────────────────────┤
│  2. Input Validation                                            │
│     ├── File size limit: 10MB                                   │
│     ├── Content length limit: 50,000 characters                 │
│     ├── File type validation: PDF, DOCX, TXT                    │
│     └── Max jobs per session: 5                                 │
├─────────────────────────────────────────────────────────────────┤
│  3. PII Detection (Microsoft Presidio)                          │
│     ├── SSN patterns                                            │
│     ├── Email addresses                                         │
│     ├── Phone numbers                                           │
│     └── Street addresses                                        │
├─────────────────────────────────────────────────────────────────┤
│  4. Prompt Injection Defense                                    │
│     ├── Input sanitization                                      │
│     ├── Template isolation                                      │
│     └── Output validation                                       │
├─────────────────────────────────────────────────────────────────┤
│  5. Output Filtering                                            │
│     ├── JSON schema validation                                  │
│     └── Content sanitization                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Performance Optimizations

| Optimization | Impact | Location |
|-------------|--------|----------|
| Parallel agent execution | 60-70% faster | `analysis_workflow.py` |
| Neo4j connection pooling | 10-15% faster | `neo4j_store.py` |
| Skills cache (5-min TTL) | Reduced DB queries | `neo4j_store.py` |
| Batched vector search | 20% faster matching | `skill_matcher.py` |
| Graph-aware normalization | Better accuracy | `resume_parser.py` |

---

## Scalability Considerations

### Horizontal Scaling

- **Frontend**: Static files on CDN, stateless
- **Backend**: Stateless, scale via Cloud Run instances
- **Neo4j**: AuraDB auto-scales

### Bottlenecks

1. **OpenAI API** - Rate limits, latency (~30-60s per agent call)
2. **Neo4j writes** - Connection pool limits under heavy load
3. **Memory** - Large documents may exceed container limits

### Mitigation Strategies

- Queue long-running analyses
- Implement request caching
- Use streaming responses for large results
- Consider async job processing (Celery/Cloud Tasks)

---

## Related Documentation

- [Database Schema](database-schema.md)
- [Agent Documentation](../backend/agents.md)
- [API Reference](../backend/api-reference.md)
- [Deployment Guide](../deployment/gcp-cloud-run.md)

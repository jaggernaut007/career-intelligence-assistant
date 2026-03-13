# Research Index

Research notes for external libraries, APIs, and architectural investigations.
Create a new note using the [template](RESEARCH-TEMPLATE.md) before implementing with any external dependency.

## Backend Libraries
- [FastAPI](fastapi.md) — Web framework (>=0.109.2 pinned, 0.135.1 latest). Breaking changes: strict Content-Type, Python >=3.10
- [LlamaIndex](llamaindex.md) — RAG orchestration (>=0.10.13 pinned, 0.14.16 latest). MAJOR breaking changes in 0.11+: Pydantic v2 only, ServiceContext removed, agent classes renamed
- [Neo4j Python Driver](neo4j-python-driver.md) — Graph + vector database driver (>=5.17.0 pinned, 6.1.0 latest). `neo4j-driver` package deprecated
- [OpenAI Python SDK](openai-python-sdk.md) — LLM API client (>=1.12.0 pinned, 2.26.0 latest). MAJOR version 2.x available
- [Presidio](presidio.md) — PII detection (>=2.2.354 pinned, 2.2.361 latest). Microsoft-maintained, minor patch updates only
- [Scrapy](scrapy.md) — Web scraping (>=2.11.0 pinned, 2.14.2 latest). Twisted/asyncio integration gotchas
- [Sentence Transformers + Nomic](sentence-transformers-nomic.md) — Embeddings (nomic-embed-text-v1.5, 768-dim). Nomic v2 MoE model now available
- [PyMuPDF](pymupdf.md) — PDF parsing (>=1.23.22 pinned, 1.27.2 latest). AGPL license — verify compliance

## Frontend Libraries
- [Zustand](zustand.md) — State management (^4.5.0 pinned, 5.0.11 latest). v5 stable with breaking changes (React 18 required, selector behavior)
- [React Query](react-query.md) — Server state (@tanstack/react-query ^5.17.0 pinned, 5.90.21 latest). Stable within v5
- [slowapi](slowapi.md) — Rate limiting (>=0.1.9 pinned, 0.1.9 latest). Alpha quality; single maintainer; evaluate alternatives

## Key Findings Summary
| Library | Pinned | Latest | Risk Level |
|---------|--------|--------|-----------|
| FastAPI | >=0.109.2 | 0.135.1 | Medium — breaking changes in newer versions |
| LlamaIndex | >=0.10.13 | 0.14.16 | **High** — major API changes in 0.11+ |
| Neo4j | >=5.17.0 | 6.1.0 | Medium — major version available |
| OpenAI SDK | >=1.12.0 | 2.26.0 | **High** — major version 2.x |
| Presidio | >=2.2.354 | 2.2.361 | Low — minor patches |
| Scrapy | >=2.11.0 | 2.14.2 | Low — minor updates |
| Nomic/ST | >=2.3.1 | latest | Low — model unchanged |
| PyMuPDF | >=1.23.22 | 1.27.2 | Medium — AGPL license |
| Zustand | ^4.5.0 | 5.0.11 | Medium — v5 breaking changes |
| React Query | ^5.17.0 | 5.90.21 | Low — stable within v5 |
| slowapi | >=0.1.9 | 0.1.9 | Medium — alpha quality, bus factor 1 |

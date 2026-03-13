# ADR-003: LlamaIndex for RAG Orchestration

## Status
Accepted

## Context
The system requires a framework for orchestrating 7 AI agents through a multi-phase workflow with:
- Document ingestion (resume parsing, JD analysis)
- Vector-based semantic search (skill matching via embeddings)
- Graph store integration (Neo4j for skill relationships)
- Structured workflow management with event-driven execution
- Built-in support for OpenAI LLM calls

Alternatives considered:
- **LangChain**: More general-purpose, heavier abstraction, more complex API surface; better for chatbot chains but less focused on document processing
- **Custom orchestration**: Full control, but requires building workflow management, retry logic, and tool integration from scratch
- **Semantic Kernel**: Microsoft-focused, less mature Python support at the time of decision

## Decision
Use LlamaIndex (>=0.10.13) with its workflow engine for agent orchestration. Events defined in `workflows/events.py` trigger agent execution across 3 phases. LlamaIndex's native integrations provide:
- `llama-index-llms-openai` for LLM calls
- `llama-index-embeddings-huggingface` for Nomic embeddings
- `llama-index-graph-stores-neo4j` for graph context
- `llama-index-vector-stores-neo4jvector` for vector similarity search

Workflow phases:
1. Document Parsing (parallel: Resume Parser + JD Analyzer)
2. Skill Matching (parallel per job)
3. Advanced Analysis (parallel: Recommendation + Interview Prep + Market Insights)

## Consequences
- **Easier**: Document-focused API simplifies RAG pipeline; built-in workflow management with `@step` decorators; native Neo4j graph+vector integration; simpler API than LangChain for document use cases
- **Harder**: LlamaIndex API evolves rapidly between versions (pin carefully); less community content than LangChain; workflow engine is newer and less battle-tested

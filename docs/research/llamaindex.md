# Research: LlamaIndex
**Library version:** llama-index>=0.10.13 (with plugin ecosystem)
**Latest available:** 0.14.16
**Status:** Needs update -- significant API changes since 0.10.x

## Sources Consulted
| Source | URL | Date accessed |
|--------|-----|---------------|
| PyPI - llama-index | https://pypi.org/project/llama-index/ | 2026-03-13 |
| GitHub - LlamaIndex | https://github.com/run-llama/llama_index | 2026-03-13 |
| LlamaIndex Documentation | https://docs.llamaindex.ai/ | 2026-03-13 |
| NVD CVE Database | https://nvd.nist.gov/ | 2026-03-13 |
| LlamaIndex Migration Guides | https://docs.llamaindex.ai/en/stable/getting_started/installation.html | 2026-03-13 |

## The Correct Approach
The project uses LlamaIndex for RAG with Neo4j as both a graph store and vector store, with event-driven workflows for AI agent orchestration.

```python
# Workflow engine pattern (app/workflows/)
from llama_index.core.workflow import Workflow, step, Event, StartEvent, StopEvent

class CareerAnalysisWorkflow(Workflow):
    @step
    async def analyze(self, ev: StartEvent) -> StopEvent:
        # Agents orchestrated via events
        result = await self.agent.arun(ev.query)
        return StopEvent(result=result)

# Neo4j graph + vector store (app/services/neo4j_store.py)
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.vector_stores.neo4jvector import Neo4jVectorStore

graph_store = Neo4jGraphStore(
    username="neo4j", password="...",
    url="bolt://localhost:7687", database="neo4j"
)
vector_store = Neo4jVectorStore(
    username="neo4j", password="...",
    url="bolt://localhost:7687",
    embedding_dimension=384,  # HuggingFace model dimension
)

# LLM service routing (app/services/llm_service.py)
from llama_index.llms.openai import OpenAI
llm = OpenAI(model="gpt-4", temperature=0)
```

This approach is correct because:
- LlamaIndex's workflow engine provides event-driven agent orchestration with async support
- Neo4j dual-store (graph + vector) enables hybrid retrieval
- Plugin architecture keeps the dependency tree modular

## What We Ruled Out (and Why)
| Approach | Why Rejected |
|----------|-------------|
| LangChain | Heavier abstraction, less transparent, more opinionated about agent patterns |
| Raw OpenAI SDK + manual RAG | Too much boilerplate for graph+vector hybrid retrieval |
| Haystack | Less mature Neo4j integration; smaller plugin ecosystem |
| Direct Neo4j Cypher queries | Loses the abstraction layer; harder to swap embedding models |
| ChromaDB / Pinecone vector store | Neo4j already provides vector indexing; reduces infrastructure complexity |
| LlamaIndex "legacy" single-package | The 0.10.x+ plugin architecture is the correct modern approach |

## Security Assessment
- [x] CVE check
  - **CVE-2024-23751** (Jan 2024): Prompt injection via `pandas_query_engine` allowing arbitrary code execution. Affects llama-index before 0.10.13. Project pins `>=0.10.13` -- **mitigated** if updated to that exact version.
  - **CVE-2024-45201** (2024): Path traversal vulnerability in file readers. Fixed in later 0.10.x releases. **Update recommended.**
  - **General risk:** LlamaIndex processes user-provided documents and queries through LLMs. Prompt injection is an inherent risk. The project's guardrails pipeline (InputValidator -> PromptGuard -> PIIDetector -> OutputFilter) provides defense-in-depth.
  - LlamaIndex plugins (llms-openai, embeddings-huggingface, etc.) each have their own dependency trees and potential vulnerabilities. Pin all plugin versions.
- [x] Maintenance health
  - **Last release:** 0.14.16 (early 2026) -- very actively maintained
  - **Release cadence:** Extremely frequent -- often multiple releases per week
  - **GitHub stars:** ~40,000+
  - **Maintainers:** Run-llama team (~10-20 active contributors, VC-backed company)
  - **Bus factor:** Lower risk than solo-maintainer projects; backed by LlamaIndex Inc.
  - **Open issues:** Typically 300-500; high churn due to rapid development
  - **Warning:** The rapid release cadence means breaking changes are common
- [x] License compatibility
  - **MIT License** -- fully permissive, compatible with any project license
- [x] Dependency tree risk
  - **Heavy transitive dependency tree**: LlamaIndex core pulls in numerous dependencies
  - Plugin architecture helps isolate dependencies but increases total count
  - `llama-index-embeddings-huggingface` pulls in `transformers`, `torch`, `sentence-transformers` -- very large
  - `llama-index-graph-stores-neo4j` depends on `neo4j` driver -- well-maintained
  - Risk: Rapid version churn means pinned versions can become incompatible quickly

## Known Gotchas / Edge Cases

### 1. Breaking Changes Since 0.10.13 -- MAJOR

LlamaIndex has undergone significant restructuring between 0.10.x and 0.14.x:

| Version Range | Breaking Change |
|--------------|----------------|
| 0.10.x -> 0.11.0 | **Workflow engine overhaul**: `Workflow` class API changed; `@step` decorator syntax updated; event routing redesigned |
| 0.11.0+ | **`ServiceContext` fully removed**: Replace with `Settings` global object. `ServiceContext.from_defaults()` no longer exists |
| 0.11.0+ | **Import paths changed**: `from llama_index` became `from llama_index.core` for all core modules |
| 0.12.0+ | **Agent framework rewrite**: `ReActAgent`, `OpenAIAgent` APIs changed; new `AgentRunner` / `AgentWorker` pattern |
| 0.12.0+ | **Callback system replaced**: `CallbackManager` deprecated in favor of instrumentation/observability API |
| 0.13.0+ | **Index construction API changes**: `VectorStoreIndex.from_documents()` kwargs changed |
| 0.13.0+ | **Embedding model defaults changed**: No longer defaults to OpenAI embeddings; must be explicitly set |
| 0.14.0+ | **Plugin version requirements tightened**: Older plugin versions may not work with core 0.14.x |
| 0.14.0+ | **Async-first patterns**: Many synchronous methods deprecated in favor of async equivalents |

**Migration risk: HIGH.** Upgrading from 0.10.13 to 0.14.x is not a drop-in update. Budget dedicated time for migration and testing.

### 2. Neo4j Graph Store Gotchas
- **Connection pooling**: `Neo4jGraphStore` creates its own connection pool. Do not create multiple instances pointing to the same database -- share a single instance across the application.
- **Schema drift**: LlamaIndex creates its own node labels and relationship types in Neo4j. If you also write custom Cypher queries, be aware of the schema LlamaIndex expects (`__Entity__`, `__Relation__` labels in newer versions).
- **Vector index naming**: `Neo4jVectorStore` creates a vector index with a default name. If you have multiple vector stores in the same Neo4j database, you must provide distinct `index_name` parameters.
- **Embedding dimension mismatch**: If you change your embedding model (e.g., from `all-MiniLM-L6-v2` at 384 dims to a larger model), you must drop and recreate the Neo4j vector index. It cannot be resized in place.

### 3. Neo4j Vector Store Gotchas
```python
# GOTCHA: Default similarity metric is cosine, but the index must be created
# with the matching metric. Changing it later requires index recreation.
vector_store = Neo4jVectorStore(
    embedding_dimension=384,
    distance_strategy="cosine",  # Must match index creation
)

# GOTCHA: Hybrid search (vector + keyword) requires a separate fulltext index
# in Neo4j. LlamaIndex does NOT create this automatically in all versions.
vector_store = Neo4jVectorStore(
    hybrid_search=True,  # Requires manual fulltext index setup
)
```

### 4. Workflow Engine Gotchas
- **Event ordering is not guaranteed** in the workflow engine. If you depend on step execution order, use explicit event dependencies, not implicit ordering.
- **Error propagation**: Exceptions in workflow steps may be swallowed silently in some versions. Always add explicit error handling in `@step` methods.
- **Streaming + workflows**: Combining `StreamingResponse` with workflow events requires careful async coordination. The workflow engine runs steps concurrently; streaming must serialize output.
- **Timeout behavior**: Workflows have a default timeout. Long-running agent tasks (e.g., multi-hop retrieval) can hit this timeout silently. Set `timeout=None` or a generous value for complex workflows.
```python
workflow = CareerAnalysisWorkflow(timeout=120)  # seconds, not ms
```

### 5. Plugin Version Compatibility Matrix
The LlamaIndex plugin ecosystem versions independently from core. This causes frequent compatibility breaks:
```
# BROKEN: Core 0.14.x with old plugins
llama-index==0.14.16
llama-index-llms-openai==0.1.6  # Too old for core 0.14.x

# CORRECT: Match plugin versions to core version era
llama-index==0.14.16
llama-index-llms-openai>=0.3.0  # Updated for 0.14.x compatibility
llama-index-embeddings-huggingface>=0.4.0
llama-index-graph-stores-neo4j>=0.4.0
llama-index-vector-stores-neo4jvector>=0.3.0
```
**Always check plugin compatibility when upgrading `llama-index` core.**

### 6. HuggingFace Embeddings in Async Context
`llama-index-embeddings-huggingface` runs the HuggingFace model synchronously under the hood (PyTorch inference). In an async FastAPI application, this blocks the event loop.
```python
# GOTCHA: This blocks the event loop
embeddings = await index.aquery("...")  # Still blocks during embedding

# WORKAROUND: Use asyncio.to_thread for embedding-heavy operations
# or run embedding service separately
```

### 7. Memory Usage with Torch
The `sentence-transformers` + `torch` dependency pulls in ~2GB+ of libraries. In containerized deployments:
- Use `torch` CPU-only builds if GPU is not available: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
- Set `TOKENIZERS_PARALLELISM=false` to avoid deadlocks with forked processes (uvicorn workers)
- First embedding call loads the model into memory (~100-500MB depending on model); plan for cold-start latency

# Research: Neo4j Python Driver

**Library version:** neo4j>=5.17.0
**Latest available:** neo4j 6.1.0 (January 2026)
**Status:** Needs update — major version 6.x available; `neo4j-driver` package deprecated

## Sources Consulted
| Source | URL | Date accessed |
|--------|-----|---------------|
| PyPI | https://pypi.org/project/neo4j/ | 2026-03-13 |
| GitHub Releases | https://github.com/neo4j/neo4j-python-driver/releases | 2026-03-13 |
| API Docs | https://neo4j.com/docs/api/python-driver/current/ | 2026-03-13 |
| Install Guide | https://neo4j.com/docs/python-manual/current/install/ | 2026-03-13 |

## The Correct Approach
The project uses the async Neo4j driver with connection pooling and vector index queries. This pattern remains valid in 6.x.

```python
# Current usage pattern (still correct in 6.x)
from neo4j import AsyncGraphDatabase

driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
async with driver.session() as session:
    result = await session.run("MATCH (s:Skill) RETURN s.name")
```

## What We Ruled Out (and Why)
| Approach | Why Rejected |
|----------|-------------|
| PostgreSQL + pgvector | No native graph traversal for skill relationships |
| Pinecone / Weaviate | Vector-only; requires second DB for graph queries |
| MongoDB Atlas Vector Search | Graph queries require slow aggregation pipelines |

## Security Assessment
- [x] CVE check — No known critical CVEs for the Python driver
- [x] Maintenance health — Maintained by Neo4j Inc (enterprise company); regular releases; Python >=3.10 required in 6.x
- [x] License compatibility — Apache 2.0 License ✅
- [x] Dependency tree risk — Minimal dependencies (pytz, ssl). Low risk

## Known Gotchas / Edge Cases
1. **`neo4j-driver` package is deprecated** — the package was renamed to just `neo4j`. No further updates to `neo4j-driver` after 5.x. Ensure requirements.txt uses `neo4j` not `neo4j-driver`
2. **Python >=3.10 required** in 6.x — project uses 3.11+ so this is fine
3. **Async driver patterns** — always use `AsyncGraphDatabase.driver()` with FastAPI; synchronous driver blocks the event loop
4. **Connection pooling** — max 50 concurrent connections, 1-hour lifetime, 30s acquisition timeout are project settings. These are reasonable for Cloud Run with 0-10 instances
5. **Vector index queries** — use `db.index.vector.queryNodes()` procedure; ensure `skill_embedding_index` is created before querying
6. **AuraDB free tier limits** — limited connections and storage; monitor for production scaling

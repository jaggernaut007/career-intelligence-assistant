# ADR-004: Neo4j AuraDB as Unified Graph + Vector Store

## Status
Accepted

## Context
The skill matching system requires two capabilities:
1. **Graph relationships**: Skills relate to jobs, resumes, experiences, and education through typed edges (HAS_SKILL, REQUIRES_SKILL, MATCHED_TO). Graph traversal enables multi-hop skill discovery.
2. **Vector similarity**: Semantic skill matching uses 768-dimensional Nomic embeddings with cosine similarity (threshold 0.75) for deduplication and fuzzy matching.

Running separate databases (e.g., PostgreSQL + Pinecone) adds operational complexity, data synchronization overhead, and deployment cost.

Alternatives considered:
- **PostgreSQL + pgvector**: Relational + vector, but no native graph traversal for skill relationships
- **Pinecone / Weaviate**: Excellent vector search, but no graph capabilities; requires a second database
- **MongoDB Atlas Vector Search**: Document + vector, but graph queries require aggregation pipelines (slow for multi-hop)

## Decision
Use Neo4j AuraDB (>=5.17.0) as the single database for both graph and vector storage. Schema:
- **Nodes**: Resume, Skill, JobDescription, Experience, Education, Session
- **Relationships**: HAS_SKILL (with level, years), REQUIRES_SKILL (with type), MATCHED_TO (with score, gaps)
- **Vector index**: `skill_embedding_index` on Skill.embedding (768 dims, cosine similarity)
- **Connection pooling**: Max 50 concurrent, 1-hour lifetime, 30s acquisition timeout
- **Skills cache**: 5-minute TTL to reduce DB queries by ~20% during LLM prompt construction

## Consequences
- **Easier**: Single database for all data; unified queries combining graph traversal + vector similarity; AuraDB is managed (no ops); free tier available for development; natural data model for skill-to-job relationships
- **Harder**: Neo4j's Cypher query language has a learning curve; vector search is newer in Neo4j (less mature than dedicated vector DBs); AuraDB free tier has connection limits; async driver patterns required for FastAPI compatibility

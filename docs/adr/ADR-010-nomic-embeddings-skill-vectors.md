# ADR-010: Nomic Embeddings for Skill Vectors

## Status
Accepted

## Context
Skill matching requires semantic similarity search — "React" should match "ReactJS", "Python programming" should be close to "Python 3". This requires embedding skills as vectors and computing cosine similarity.

Requirements:
- High-quality embeddings for short technical terms (1-5 words)
- 768+ dimensions for sufficient expressiveness
- HuggingFace-hosted for easy integration with sentence-transformers
- 8k+ context window for embedding longer skill descriptions when needed

## Decision
Use Nomic `nomic-ai/nomic-embed-text-v1.5` via `sentence-transformers>=2.3.1` and `llama-index-embeddings-huggingface>=0.1.4`.

Configuration:
- **Dimensions**: 768
- **Similarity function**: Cosine
- **Similarity threshold**: 0.75 for skill deduplication
- **Storage**: Neo4j vector index (`skill_embedding_index`)
- **Access**: HuggingFace token (`HF_TOKEN`)

Alternatives considered:
- **OpenAI text-embedding-3-small**: Good quality, but adds per-call API cost for every skill embedding; 1536 dimensions is overkill for short terms
- **all-MiniLM-L6-v2**: Popular, but only 384 dimensions; lower quality for technical vocabulary
- **Cohere embed-v3**: Good quality, but API dependency and cost; less HuggingFace integration
- **BGE-large**: High quality, but 1024 dimensions and slower inference

## Consequences
- **Easier**: SOTA quality for 2025; 768 dims balances quality vs storage; HuggingFace-hosted (no separate API); integrates natively with LlamaIndex; 8k context window handles longer descriptions
- **Harder**: Requires `torch>=2.2.0` (large dependency); HF token required; initial model download is ~500MB; local inference uses CPU/GPU resources

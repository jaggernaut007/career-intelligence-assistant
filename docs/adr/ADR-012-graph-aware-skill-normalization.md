# ADR-012: Graph-Aware Skill Normalization

## Status
Accepted

## Context
Resumes and job descriptions use inconsistent skill naming: "React", "ReactJS", "React.js", "ReactJS Framework" all refer to the same skill. Without normalization:
- Skill matching produces false negatives (resume says "ReactJS", JD says "React" — no match)
- Neo4j accumulates duplicate Skill nodes
- Embedding similarity alone misses domain-specific equivalences (e.g., "AWS" and "Amazon Web Services")

## Decision
Implement a 3-tier normalization pipeline:

1. **Neo4j context query**: Fetch existing normalized skill names from the graph (with 5-minute TTL cache)
2. **LLM normalization**: Pass the raw skill + existing skill list to `gpt-5.4-mini`; the LLM maps to existing names or creates new canonical forms
3. **Vector similarity fallback**: If LLM is uncertain, compute cosine similarity (threshold 0.75) between the new skill embedding and existing skill embeddings

This pipeline runs in both Resume Parser and JD Analyzer agents before storing skills in Neo4j.

## Consequences
- **Easier**: Eliminates duplicate skills; improves matching accuracy; LLM leverages graph context for better decisions; cache reduces DB queries by ~20%; consistent skill taxonomy across all analyses
- **Harder**: Adds ~200-400ms latency per normalization batch; LLM token cost for normalization; cache invalidation needed when new skills are added; edge cases with ambiguous abbreviations (e.g., "ML" = Machine Learning or Markup Language?)

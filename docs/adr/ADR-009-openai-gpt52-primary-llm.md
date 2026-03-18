# ADR-009: OpenAI GPT-5.4 Mini as Primary LLM

## Status
Accepted

## Context
All 7 agents require an LLM for text understanding and generation:
- Resume parsing requires structured extraction from unstructured text
- JD analysis requires identifying required vs nice-to-have skills
- Skill matching requires reasoning about skill equivalence
- Recommendations, interview prep, and market insights require generation
- Chat requires conversational reasoning with context

The LLM must support structured output (JSON), handle long documents (resumes can be 5+ pages), and provide consistent quality across diverse tasks.

## Decision
Use OpenAI `gpt-5.4-mini` as the default primary LLM. All LLM calls are routed through `backend/app/services/llm_service.py` — no direct OpenAI client instantiation in agents.

Key configuration:
- **Temperature**: 0.1 for parsing/matching (deterministic), 0.7 for recommendations/chat (creative)
- **Structured output**: JSON mode for all agent responses
- **Error handling**: Retry with exponential backoff via the service layer

Alternatives considered:
- **Claude (Anthropic)**: Excellent reasoning, but less mature structured output at decision time; higher latency for batch operations
- **Gemini (Google)**: Good multimodal, but less consistent JSON output; integration complexity
- **Open-source (Llama 3, Mistral)**: Lower cost, but self-hosting adds ops overhead; quality gap for structured extraction
- **GPT-4o**: Previous generation model with a weaker efficiency profile for this workload

## Consequences
- **Easier**: Better quality-per-token than the older defaults used in this repo; mature Python SDK; reliable structured output; sufficient context window for long documents
- **Harder**: API cost (~$0.01-0.05 per analysis); vendor lock-in to OpenAI; rate limits under heavy load; requires API key management; no on-premise option

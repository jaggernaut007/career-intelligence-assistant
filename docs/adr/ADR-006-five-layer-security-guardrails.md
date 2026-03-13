# ADR-006: 5-Layer Security Guardrails Pipeline

## Status
Accepted

## Context
The system processes sensitive personal data (resumes containing PII) and passes user-controlled input to LLMs. Without guardrails:
- PII (SSN, phone, email, addresses) could be stored in Neo4j or leaked in responses
- Prompt injection attacks could extract system prompts or manipulate agent behaviour
- Malicious file uploads could exploit document parsing libraries
- Unconstrained API access could lead to abuse and cost overruns
- LLM outputs could contain hallucinated PII or leaked system context

A single security layer is insufficient — defense in depth is required.

## Decision
Implement a 5-layer guardrails pipeline in `backend/app/guardrails/`:

| Layer | Module | When | What |
|-------|--------|------|------|
| 1 | `pii_detector.py` | Pre-LLM | Detect and redact PII using Microsoft Presidio + spaCy NER + regex fallback |
| 2 | `prompt_guard.py` | Pre-LLM | Detect prompt injection (system prompt extraction, instruction override, delimiter injection, role impersonation) |
| 3 | `input_validator.py` | Upload | Validate file size (10MB), content length (50k chars), file types (PDF/DOCX/TXT), magic bytes |
| 4 | `rate_limiter.py` | API | Per-IP rate limiting (10 req/min) via slowapi on POST endpoints |
| 5 | `output_filter.py` | Post-LLM | JSON schema validation, leaked system prompt detection, markdown sanitization |

Pipeline order: Input Validation → PII Detection → Prompt Guard → [LLM Call] → Output Filter

## Consequences
- **Easier**: Defense in depth covers multiple attack vectors; each layer is independently testable; Presidio is production-grade PII detection; rate limiting prevents cost overruns
- **Harder**: 5 layers add latency (~50-100ms total); Presidio requires spaCy model download; false positives in PII detection may redact valid data; prompt injection detection requires ongoing pattern updates

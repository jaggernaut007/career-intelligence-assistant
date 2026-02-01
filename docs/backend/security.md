# Security & Guardrails

The Career Intelligence Assistant implements a comprehensive 5-layer security architecture to ensure safe and reliable AI interactions.

## Security Layers Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         5-LAYER SECURITY GUARDRAILS                          │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────┐  │
│  │   PII     │ │  Prompt   │ │   Input   │ │   Rate    │ │    Output     │  │
│  │ Detection │→│ Injection │→│Validation │→│ Limiting  │→│   Filtering   │  │
│  │(Presidio) │ │   Guard   │ │(File/Size)│ │ (slowapi) │ │(Sanitization) │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: PII Detection

**Location**: `backend/app/guardrails/pii_detector.py`

Automatically detects and redacts personally identifiable information from resumes before processing.

### Detected PII Types

| Type | Examples | Pattern |
|------|----------|---------|
| SSN | 123-45-6789 | Regex + Presidio |
| Email | john@example.com | Presidio NER |
| Phone | (555) 123-4567 | Regex + Presidio |
| Address | 123 Main St, City, ST 12345 | Presidio NER |

### Implementation

```python
from app.guardrails import get_pii_detector

detector = get_pii_detector()
redacted_text = detector.redact(resume_text)
# "john@email.com" → "[EMAIL_REDACTED]"
```

### Technology

- **Microsoft Presidio**: Primary PII detection engine
- **spaCy NLP**: Named entity recognition for addresses and names
- **Regex Fallback**: Pattern matching for SSN and phone formats

---

## Layer 2: Prompt Injection Guard

**Location**: `backend/app/guardrails/prompt_guard.py`

Detects and blocks prompt injection attempts in user inputs.

### Detection Patterns

- System prompt extraction attempts
- Instruction override patterns
- Role impersonation attempts
- Delimiter injection (e.g., `<|system|>`)

### Usage

```python
from app.guardrails import get_prompt_guard

guard = get_prompt_guard()
is_safe, error = guard.validate(user_input)

if not is_safe:
    raise HTTPException(status_code=400, detail=error)
```

---

## Layer 3: Input Validation

**Location**: `backend/app/guardrails/input_validator.py`

Validates all incoming data for security and compliance.

### File Validation

| Check | Limit |
|-------|-------|
| File Size | 10 MB max |
| Content Length | 50,000 characters max |
| Allowed Types | PDF, DOCX, TXT |
| Blocked Types | EXE, DLL, BAT, SH |
| Magic Bytes | PDF header verification |

### Validation API

```python
from app.guardrails import get_input_validator

validator = get_input_validator()

# Validate content length
is_valid, error = validator.validate_content(text)

# Check file type
if extension not in validator.ALLOWED_EXTENSIONS:
    raise HTTPException(status_code=400, detail="Unsupported file type")
```

---

## Layer 4: Rate Limiting

**Location**: `backend/app/guardrails/rate_limiter.py`

Prevents API abuse through request rate limiting.

### Rate Limits

| Scope | Limit | Window |
|-------|-------|--------|
| Per IP Address | 10 requests | 1 minute |

### Implementation

Rate limiting is implemented using **slowapi** and applied to all mutating endpoints:

```python
from app.guardrails.rate_limiter import slowapi_limiter as limiter

@router.post("/session")
@limiter.limit("10/minute")
async def create_session(request: Request):
    ...
```

### Rate-Limited Endpoints

| Endpoint | Method | Limit |
|----------|--------|-------|
| `/api/v1/session` | POST | 10/minute |
| `/api/v1/upload/resume` | POST | 10/minute |
| `/api/v1/upload/job-description` | POST | 10/minute |
| `/api/v1/analyze` | POST | 10/minute |
| `/api/v1/chat` | POST | 10/minute |

### Response Headers

When rate limited, the API returns:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706745600
```

### Custom Rate Limiter Class

A custom `RateLimiter` class is also available for session-based limiting:

```python
from app.guardrails.rate_limiter import get_rate_limiter

limiter = get_rate_limiter(limit=10, window_seconds=60)

if not limiter.check(session_id):
    retry_after = limiter.get_retry_after(session_id)
    raise HTTPException(
        status_code=429,
        detail=f"Rate limit exceeded. Retry after {retry_after:.0f} seconds"
    )
```

---

## Layer 5: Output Filtering

**Location**: `backend/app/guardrails/output_filter.py`

Sanitizes LLM responses before returning to the frontend.

### Filtering Actions

- Strip leaked system prompts
- Validate JSON structure
- Remove potentially harmful content
- Sanitize markdown output

---

## Security Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_PER_MINUTE` | Requests per minute per IP | 10 |
| `MAX_FILE_SIZE_MB` | Maximum upload file size | 10 |
| `MAX_CONTENT_LENGTH` | Maximum text content length | 50000 |

### Production Hardening

For production deployments:

1. **Change session secret**: Set `SESSION_SECRET_KEY` to a secure random value
2. **Restrict CORS**: Configure `CORS_ORIGINS` to allowed domains only
3. **Enable HTTPS**: Use `neo4j+s://` protocol for database connections
4. **Monitor rate limits**: Track 429 responses in logging/monitoring

---

## Testing

### Unit Tests

```bash
# Run rate limiter unit tests
uv run pytest tests/unit/test_rate_limiter.py -v
```

### Integration Tests

```bash
# Run rate limiting integration tests
uv run pytest tests/integration/test_rate_limiting.py -v
```

### Test Coverage

| Component | Test File | Tests |
|-----------|-----------|-------|
| RateLimiter class | `tests/unit/test_rate_limiter.py` | 15 |
| API rate limiting | `tests/integration/test_rate_limiting.py` | 13 |

---

## Error Handling

### Rate Limit Exceeded

```json
{
  "detail": "Rate limit exceeded: 10 per 1 minute"
}
```

### PII Detection Failure

PII is silently redacted; no error is returned to the user.

### Prompt Injection Blocked

```json
{
  "detail": "Content failed security validation: Potential prompt injection detected"
}
```

### File Validation Error

```json
{
  "detail": "File size exceeds maximum of 10MB"
}
```

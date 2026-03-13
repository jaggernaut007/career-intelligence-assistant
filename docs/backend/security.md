# Security & Guardrails

The Career Intelligence Assistant implements a comprehensive 6-layer security architecture to ensure safe and reliable AI interactions.

## Security Layers Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          6-LAYER SECURITY GUARDRAILS                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │   PII    │ │  Prompt  │ │  Input   │ │   Rate   │ │  Output  │ │  API Key │ │
│  │Detection │→│Injection │→│Validate  │→│ Limiting │→│ Filtering│→│Encryption│ │
│  │(Presidio)│ │  Guard   │ │(File/Sz) │ │ (slowapi)│ │(Sanitize)│ │ (Fernet) │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
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
| `/api/v1/session/api-key` | POST | 10/minute |
| `/api/v1/session/password-login` | POST | **5/minute** |
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

## Layer 6: API Key Encryption & Session Security

**Location**: `backend/app/models/session.py`

Per-session OpenAI API keys are encrypted at rest using Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256).

### Encryption Architecture

```
User submits API key
        │
        ▼
┌──────────────────────┐
│  Format validation   │  Must start with "sk-"
│  (sk-* prefix check) │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  OpenAI API check    │  client.models.list()
│  (live validation)   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  Fernet encryption   │  AES-128-CBC + HMAC-SHA256
│  (unique IV per call)│  Derived from SESSION_SECRET_KEY
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  In-memory storage   │  SessionData._encrypted_api_key
│  (never persisted)   │  Auto-deleted on session expiry
└──────────────────────┘
```

### Key Derivation

The Fernet key is derived from `SESSION_SECRET_KEY` via SHA-256:

```python
key_bytes = hashlib.sha256(secret.encode()).digest()
fernet_key = base64.urlsafe_b64encode(key_bytes)
```

### Security Properties

| Property | Implementation |
|----------|----------------|
| **Encryption algorithm** | Fernet (AES-128-CBC + HMAC-SHA256) |
| **IV uniqueness** | Fernet generates a random IV per encryption call |
| **Key derivation** | SHA-256 of `SESSION_SECRET_KEY` |
| **Storage** | In-memory only; never written to disk or database |
| **Lifetime** | Destroyed on logout (`DELETE /session`) or session expiry (1 hour) |
| **Logging** | API key is **never** logged; only session ID appears in logs |
| **`__repr__` safety** | `SessionData.__repr__` shows `api_key=set` or `api_key=not set` |
| **Frontend exposure** | Frontend stores only `apiKeyValidated: boolean`, never the raw key |

### Password Authentication

The system supports an optional password-based login (`APP_PASSWORD` env var) as an alternative to direct API key entry.

| Property | Implementation |
|----------|----------------|
| **Comparison** | Timing-safe `hmac.compare_digest` (prevents timing side-channel attacks) |
| **Rate limit** | 5 attempts/minute per IP (stricter than other endpoints) |
| **Server key guard** | Verifies `OPENAI_API_KEY` exists and starts with `sk-` before assigning |
| **Input normalization** | Password is `.strip()`-ed before comparison |
| **Failure logging** | Logs session ID only, never the attempted password |
| **Availability detection** | `POST /session` returns `auth_methods` so the frontend only shows password login when configured |

### Per-Session LLM Service Instances

Each unique API key gets its own `LlamaIndexService` instance via a bounded cache:

```python
_session_services: Dict[str, LlamaIndexService] = {}  # SHA-256(key) → service
_MAX_SESSION_SERVICES = 50  # FIFO eviction when full
```

- Cache keys are **SHA-256 hashes** of the API key (raw key never used as dict key)
- Access is protected by `asyncio.Lock` to prevent race conditions
- Context variable (`contextvars.ContextVar`) propagates the session API key through the agent call chain

### HTTP Security Headers

The backend adds security headers to all responses:

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'` | Prevent XSS |
| `Cache-Control` | `no-store, no-cache, must-revalidate, private` | Prevent caching of API responses |
| `Pragma` | `no-cache` | HTTP/1.0 cache prevention |

> `Cache-Control` and `Pragma` are applied only to `/api/` routes.

---

## Security Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_PER_MINUTE` | Requests per minute per IP | 10 |
| `MAX_FILE_SIZE_MB` | Maximum upload file size | 10 |
| `MAX_CONTENT_LENGTH` | Maximum text content length | 50000 |
| `APP_PASSWORD` | Application password for password-based login | *(optional — enables password login)* |
| `SESSION_SECRET_KEY` | Secret used to derive Fernet encryption key | *(required — use a 64+ char random string)* |

### Production Hardening

For production deployments:

1. **Change session secret**: Set `SESSION_SECRET_KEY` to a cryptographically random value (e.g., `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`)

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

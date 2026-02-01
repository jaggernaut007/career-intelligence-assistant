# API Reference

The Career Intelligence Assistant exposes a REST API built with FastAPI.

## Interactive Documentation

FastAPI auto-generates interactive API docs:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

See also: [specs/openapi.yaml](../../specs/openapi.yaml)

---

## Base URL

- **Local Development**: `http://localhost:8000/api/v1`
- **Production**: `https://your-domain.com/api/v1`

---

## Authentication

Currently, the API uses session-based identification (no authentication required). Sessions are created automatically and tracked via session ID.

---

## Rate Limiting

Rate limiting is enforced using **slowapi** to prevent API abuse.

| Limit | Scope | Endpoints |
|-------|-------|-----------|
| 10 requests/minute | Per IP address | All POST endpoints |

### Rate-Limited Endpoints

- `POST /api/v1/session` - Create session
- `POST /api/v1/upload/resume` - Upload resume
- `POST /api/v1/upload/job-description` - Add job description
- `POST /api/v1/analyze` - Start analysis
- `POST /api/v1/chat` - Chat with AI

### Rate Limit Response

When rate limit is exceeded, the API returns `429 Too Many Requests`:

```json
{
  "detail": "Rate limit exceeded: 10 per 1 minute"
}
```

Rate limit headers are included in responses:
```
Retry-After: 45
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706745600
```

See [Security Documentation](security.md) for more details.

---

## Endpoints

### Health Check

```http
GET /health
```

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### Session Management

#### Create Session

```http
POST /api/v1/session
```

**Response** `201 Created`:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-31T12:00:00Z"
}
```

#### Get Session Status

```http
GET /api/v1/session/{session_id}
```

**Response** `200 OK`:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "resume_uploaded": true,
  "job_count": 2,
  "analysis_status": "completed",
  "created_at": "2024-01-31T12:00:00Z"
}
```

#### Delete Session

```http
DELETE /api/v1/session/{session_id}
```

**Response** `204 No Content`

---

### Document Upload

#### Upload Resume

```http
POST /api/v1/upload/resume
Content-Type: multipart/form-data
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file` | file | Yes | PDF, DOCX, or TXT file (max 10MB) |
| `session_id` | string | Yes | Session ID |

**Response** `200 OK`:
```json
{
  "resume_id": "550e8400-e29b-41d4-a716-446655440001",
  "skills_count": 15,
  "experiences_count": 4,
  "education_count": 2,
  "summary": "Senior software engineer with 8 years experience..."
}
```

**Error Responses**:
- `400 Bad Request` - Invalid file type or size
- `413 Payload Too Large` - File exceeds 10MB limit

#### Add Job Description

```http
POST /api/v1/upload/job-description
Content-Type: application/json
```

**Request Body**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_description": "We are looking for a Senior Software Engineer..."
}
```

**Response** `200 OK`:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440002",
  "title": "Senior Software Engineer",
  "company": "TechCorp",
  "required_skills_count": 8,
  "nice_to_have_skills_count": 5
}
```

**Limits**: Maximum 5 job descriptions per session.

---

### Analysis

#### Run Analysis

```http
POST /api/v1/analyze
Content-Type: application/json
```

**Request Body**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response** `202 Accepted`:
```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440003",
  "status": "processing",
  "estimated_duration_seconds": 90
}
```

Use WebSocket or polling to track progress.

#### Get Analysis Results

```http
GET /api/v1/results/{session_id}
```

**Response** `200 OK`:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440002",
      "title": "Senior Software Engineer",
      "company": "TechCorp",
      "fit_score": 85.5,
      "matched_skills": ["Python", "FastAPI", "Docker"],
      "missing_required": ["Kubernetes", "AWS"],
      "missing_nice_to_have": ["Terraform"]
    }
  ],
  "processing_time_ms": 87500
}
```

---

### Detailed Results

#### Get Recommendations

```http
GET /api/v1/recommendations/{session_id}
```

**Response** `200 OK`:
```json
{
  "priority_skills": [
    {
      "skill": "Kubernetes",
      "importance": "required",
      "learning_path": "Start with K8s fundamentals course..."
    }
  ],
  "resume_improvements": [
    "Add specific metrics to your achievements",
    "Highlight cloud experience more prominently"
  ],
  "action_items": [
    {
      "action": "Complete AWS Solutions Architect certification",
      "priority": "high",
      "estimated_time": "2-3 months"
    }
  ]
}
```

#### Get Interview Prep

```http
GET /api/v1/interview-prep/{session_id}
```

**Response** `200 OK`:
```json
{
  "technical_questions": [
    {
      "question": "Explain how you would design a microservices architecture",
      "category": "system_design",
      "suggested_answer": "I would start by..."
    }
  ],
  "behavioral_questions": [
    {
      "question": "Tell me about a time you led a challenging project",
      "category": "leadership",
      "star_example": {
        "situation": "...",
        "task": "...",
        "action": "...",
        "result": "..."
      }
    }
  ],
  "questions_to_ask": [
    "What does a typical day look like for this role?",
    "How is success measured in this position?"
  ]
}
```

#### Get Market Insights

```http
GET /api/v1/market-insights/{session_id}
```

**Response** `200 OK`:
```json
{
  "salary_range": {
    "min": 120000,
    "max": 180000,
    "median": 150000,
    "currency": "USD"
  },
  "demand_trend": "growing",
  "top_companies_hiring": ["Google", "Meta", "Amazon"],
  "related_roles": [
    "Staff Engineer",
    "Engineering Manager",
    "Principal Engineer"
  ],
  "skill_demand": [
    {
      "skill": "Kubernetes",
      "demand": "high",
      "salary_premium": "+15%"
    }
  ]
}
```

---

### Progress Tracking

#### REST Polling

```http
GET /api/v1/progress/{session_id}
```

**Response** `200 OK`:
```json
{
  "status": "processing",
  "overall_progress": 45,
  "current_phase": "skill_matching",
  "agents": [
    {
      "name": "resume_parser",
      "status": "completed",
      "progress": 100
    },
    {
      "name": "skill_matcher",
      "status": "running",
      "progress": 60
    }
  ]
}
```

#### WebSocket (Recommended)

```
WS /ws/progress/{session_id}
```

**Messages Received**:
```json
{
  "type": "agent_progress",
  "agent_name": "resume_parser",
  "status": "running",
  "progress": 70,
  "current_step": "Processing extracted data"
}
```

```json
{
  "type": "analysis_complete",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "success": true
}
```

---

### Chat

#### Ask Question About Fit

```http
POST /api/v1/chat
Content-Type: application/json
```

**Request Body**:
```json
{
  "message": "What skills should I prioritize learning for this role?",
  "job_id": "550e8400-e29b-41d4-a716-446655440002"
}
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message` | string | Yes | User's question (1-2000 characters) |
| `job_id` | string | No | Specific job ID to focus on (uses first job if omitted) |

**Response** `200 OK`:
```json
{
  "response": "Based on your profile, I'd recommend prioritizing **Kubernetes** first...\n\n📋 **Recommendations**\n- Start with K8s fundamentals course on Coursera\n- Consider CKA certification\n\n🎤 **Interview Prep**\n- Be ready to discuss container orchestration experience...",
  "suggested_questions": [
    "Which skill gap should I prioritize learning first?",
    "What interview questions should I prepare for Senior Software Engineer?",
    "What certifications would strengthen my application?",
    "How does my experience compare to typical candidates?"
  ]
}
```

**Prerequisites**:
- Valid session with resume uploaded
- At least one job description added
- Analysis completed (recommended for best results)

**Features**:
- UK/EU market-focused advice (salaries in GBP/EUR)
- Markdown-formatted responses with emoji highlights
- Contextual follow-up question suggestions
- Prompt injection protection

**Error Responses**:
- `400 Bad Request` - No resume or job descriptions in session
- `400 Bad Request` - Message failed security validation

---

## Error Responses

All errors follow this format:

```json
{
  "detail": {
    "code": "VALIDATION_ERROR",
    "message": "File size exceeds maximum limit",
    "field": "file"
  }
}
```

### Error Codes

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | `VALIDATION_ERROR` | Invalid request data |
| 400 | `INVALID_FILE_TYPE` | Unsupported file format |
| 404 | `SESSION_NOT_FOUND` | Session doesn't exist |
| 404 | `RESUME_NOT_FOUND` | Resume not uploaded yet |
| 413 | `FILE_TOO_LARGE` | File exceeds size limit |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |

---

## Content Types

| Endpoint | Request | Response |
|----------|---------|----------|
| Upload resume | `multipart/form-data` | `application/json` |
| All others | `application/json` | `application/json` |

---

## CORS

Allowed origins are configured via `CORS_ORIGINS` environment variable.

Default (development):
- `http://localhost:5173`
- `http://localhost:3000`

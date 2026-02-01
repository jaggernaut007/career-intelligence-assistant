# Testing Guide

This guide covers the testing strategy and how to run tests for the Career Intelligence Assistant.

## Testing Stack

| Layer | Framework | Purpose |
|-------|-----------|---------|
| Backend Unit | pytest | Test individual components in isolation |
| Backend Integration | pytest + TestClient | Test API endpoints and workflows |
| Frontend Unit | Vitest | Test React components and hooks |
| Frontend E2E | Vitest + React Testing Library | Test user interactions |

---

## Backend Tests

### Directory Structure

```
backend/tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_rate_limiter.py
│   ├── test_recommendation_agent.py
│   ├── test_market_insights_agent.py
│   └── test_jd_analyzer_agent.py
├── integration/             # Integration tests
│   └── test_rate_limiting.py
└── evaluation/              # LLM evaluation tests
    └── conftest.py
```

### Running Backend Tests

```bash
cd backend

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/test_rate_limiter.py -v

# Run with coverage report
uv run pytest --cov=app

# Run only unit tests
uv run pytest tests/unit -v

# Run only integration tests
uv run pytest tests/integration -v
```

### Test Markers

```bash
# Skip tests that require live API calls
uv run pytest -m "not live"

# Run only integration tests
uv run pytest -m integration
```

---

## Test Categories

### Unit Tests

Test individual components in isolation with mocked dependencies.

#### Rate Limiter Tests (`tests/unit/test_rate_limiter.py`)

| Test Class | Tests | Description |
|------------|-------|-------------|
| `TestRateLimiterClass` | 10 | Core rate limiter functionality |
| `TestSlowApiLimiter` | 2 | Slowapi integration |
| `TestGetRateLimiter` | 3 | Singleton factory function |

**Key Test Cases:**

```python
def test_rate_limiter_allows_requests_under_limit():
    """Requests under the limit should be allowed."""

def test_rate_limiter_blocks_requests_over_limit():
    """Requests over the limit should be blocked."""

def test_rate_limiter_resets_after_window():
    """Rate limit should reset after the time window expires."""

def test_rate_limiter_tracks_sessions_independently():
    """Each session should have its own rate limit counter."""
```

#### Agent Tests

Each agent has dedicated tests verifying:
- Input/output schema compliance
- Required fields in responses
- Error handling
- Integration with services

---

### Integration Tests

Test API endpoints with real HTTP requests using FastAPI TestClient.

#### Rate Limiting Tests (`tests/integration/test_rate_limiting.py`)

| Test Class | Tests | Description |
|------------|-------|-------------|
| `TestAPIRateLimiting` | 4 | API endpoint rate limit behavior |
| `TestRateLimitConfiguration` | 2 | Configuration verification |
| `TestRateLimitedEndpointsList` | 5 | Verify all endpoints are protected |
| `TestRateLimitExceptionHandler` | 2 | Exception handler registration |

**Key Test Cases:**

```python
def test_session_endpoint_has_rate_limit():
    """POST /api/v1/session should be rate limited."""

def test_rate_limit_returns_429_status():
    """Exceeded rate limit should return 429 Too Many Requests."""

def test_app_has_limiter_in_state():
    """App should have limiter in state for slowapi."""
```

---

## Fixtures

Common fixtures are defined in `tests/conftest.py`:

### Sample Data Fixtures

```python
@pytest.fixture
def sample_resume_text() -> str:
    """Sample resume text for testing."""

@pytest.fixture
def sample_job_description() -> str:
    """Sample job description for testing."""

@pytest.fixture
def sample_resume_with_pii() -> str:
    """Resume text containing PII for guardrail testing."""

@pytest.fixture
def malicious_prompt_injection() -> str:
    """Malicious input for prompt injection testing."""
```

### Mock Fixtures

```python
@pytest.fixture
def mock_openai_client() -> MagicMock:
    """Mock OpenAI client for testing."""

@pytest.fixture
def mock_neo4j_store() -> MagicMock:
    """Mock Neo4j store for testing."""

@pytest.fixture
def mock_llamaindex_service() -> MagicMock:
    """Mock LlamaIndex service for testing agents."""
```

### API Client Fixtures

```python
@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for API testing."""
```

---

## Writing New Tests

### Unit Test Template

```python
"""
Unit tests for [Component Name].
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestComponentName:
    """Test suite for ComponentName."""

    def test_basic_functionality(self):
        """Component should perform basic operation."""
        from app.module import ComponentName

        component = ComponentName()
        result = component.do_something()

        assert result is not None

    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Async operation should complete successfully."""
        from app.module import ComponentName

        component = ComponentName()
        result = await component.async_operation()

        assert result.success is True
```

### Integration Test Template

```python
"""
Integration tests for [Feature Name].
"""

import pytest
from fastapi.testclient import TestClient


class TestFeatureAPI:
    """Test suite for Feature API endpoints."""

    def test_endpoint_returns_success(self, test_client: TestClient):
        """Endpoint should return success response."""
        response = test_client.post("/api/v1/endpoint", json={...})

        assert response.status_code == 200
        assert "expected_field" in response.json()
```

---

## Frontend Tests

### Running Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

### Test Location

```
frontend/src/
├── components/
│   └── __tests__/
│       └── Component.test.tsx
├── stores/
│   └── __tests__/
│       └── store.test.ts
└── hooks/
    └── __tests__/
        └── hook.test.ts
```

---

## Continuous Integration

Tests run automatically on:
- Pull request creation
- Push to main/develop branches

### CI Pipeline

```yaml
# Example GitHub Actions workflow
- name: Run Backend Tests
  run: |
    cd backend
    uv run pytest --cov=app --cov-report=xml

- name: Run Frontend Tests
  run: |
    cd frontend
    npm test -- --coverage
```

---

## Best Practices

### Do

- Write tests before implementation (TDD)
- Use descriptive test names
- Mock external services
- Test edge cases and error conditions
- Keep tests independent and isolated

### Don't

- Test implementation details
- Use hardcoded secrets in tests
- Skip cleanup in fixtures
- Write flaky tests with timing dependencies
- Share state between tests

---

## Troubleshooting

### Common Issues

**ImportError in tests:**
```bash
# Ensure you're in the correct virtual environment
cd backend
uv sync
uv run pytest
```

**Async test failures:**
```python
# Use the asyncio marker for async tests
@pytest.mark.asyncio
async def test_async_function():
    ...
```

**Mock not applied:**
```python
# Use autouse fixtures or explicit monkeypatch
@pytest.fixture(autouse=True)
def mock_service(monkeypatch):
    monkeypatch.setattr("app.module.function", mock_function)
```

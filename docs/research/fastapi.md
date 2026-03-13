# Research: FastAPI
**Library version:** fastapi>=0.109.2, uvicorn[standard]>=0.27.1
**Latest available:** 0.135.1 (FastAPI), 0.41.0 (uvicorn)
**Status:** Needs update

## Sources Consulted
| Source | URL | Date accessed |
|--------|-----|---------------|
| PyPI - FastAPI | https://pypi.org/project/fastapi/ | 2026-03-13 |
| PyPI - uvicorn | https://pypi.org/project/uvicorn/ | 2026-03-13 |
| GitHub - FastAPI | https://github.com/fastapi/fastapi | 2026-03-13 |
| NVD CVE Database | https://nvd.nist.gov/ | 2026-03-13 |
| FastAPI Release Notes | https://fastapi.tiangolo.com/release-notes/ | 2026-03-13 |

## The Correct Approach
The project uses FastAPI with async WebSocket streaming, Pydantic v2 models, and uvicorn as the ASGI server. Key patterns:

```python
# Entry point: app/main.py — standard FastAPI app factory
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel  # v2

app = FastAPI()

# WebSocket streaming for workflow progress
@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    await websocket.accept()
    try:
        async for event in workflow_stream():
            await websocket.send_json(event.model_dump())
    except WebSocketDisconnect:
        pass

# Pydantic v2 models for all request/response schemas
class AgentResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str
    result: dict
```

This approach is correct because:
- FastAPI has native Pydantic v2 support since 0.100.0
- Async WebSocket + `send_json()` is the idiomatic pattern
- uvicorn[standard] includes uvloop and httptools for performance

## What We Ruled Out (and Why)
| Approach | Why Rejected |
|----------|-------------|
| Flask + Socket.IO | No native async; requires gevent/eventlet hacks for WebSockets |
| Django Channels | Heavier stack, slower cold start, less native Pydantic integration |
| Starlette directly | FastAPI adds automatic OpenAPI docs, dependency injection, and validation |
| Pydantic v1 compatibility mode | Project should use native v2; `.model_dump()` over `.dict()` |
| Hypercorn ASGI server | uvicorn is more widely adopted and better tested with FastAPI |

## Security Assessment
- [x] CVE check
  - **CVE-2024-24762** (Feb 2024, CVSS 7.5): DoS via multipart form parsing in `python-multipart` dependency. Fixed in FastAPI 0.109.1+ by bumping `python-multipart>=0.0.7`. Project pins `>=0.109.2` so this is **mitigated**.
  - **CVE-2024-47874** (Oct 2024): Another `python-multipart` content-type header parsing vulnerability. Fixed by upgrading `python-multipart>=0.0.12`. Ensure transitive dep is updated.
  - **No direct FastAPI CVEs** in the core framework code as of March 2026. Vulnerabilities have been in dependencies (python-multipart, Starlette).
  - Starlette (FastAPI's foundation) had **CVE-2024-47874** for multipart parsing. Resolved in Starlette 0.40.0+ / FastAPI 0.115.0+.
- [x] Maintenance health
  - **Last release:** 0.135.1 (early 2026) -- actively maintained
  - **Release cadence:** Frequent releases, typically every 1-3 weeks
  - **GitHub stars:** ~82,000+
  - **Primary maintainer:** Sebastian Ramirez (@tiangolo) plus ~15 active contributors
  - **Bus factor:** Medium risk -- heavily driven by one maintainer, but backed by corporate sponsors and a large contributor community
  - **Open issues:** ~400-600 (typical for a project this popular)
- [x] License compatibility
  - **MIT License** -- fully permissive, compatible with any project license
- [x] Dependency tree risk
  - Direct deps: Starlette, Pydantic, typing-extensions (small, well-maintained)
  - `uvicorn[standard]` pulls in: uvloop, httptools, watchfiles, websockets -- all well-maintained
  - `python-multipart` has been the main vulnerability vector; keep it updated

## Known Gotchas / Edge Cases

### 1. Async WebSocket Connection Lifecycle
WebSocket connections in FastAPI do not automatically benefit from dependency injection cleanup. If you use `Depends()` in a WebSocket route, the dependency teardown (yield-based) may not execute if the client disconnects abruptly.
```python
# GOTCHA: This teardown may not run on abrupt disconnect
@app.websocket("/ws")
async def ws(websocket: WebSocket, db: Session = Depends(get_db)):
    # If client disconnects, __aexit__ may not fire
    ...

# SAFER: Use try/finally explicitly
@app.websocket("/ws")
async def ws(websocket: WebSocket):
    db = get_db_session()
    try:
        await websocket.accept()
        ...
    finally:
        db.close()
```

### 2. Pydantic v2 Migration Pitfalls
- `.dict()` is deprecated; use `.model_dump()`
- `.json()` is deprecated; use `.model_dump_json()`
- `Config` inner class is replaced by `model_config = ConfigDict(...)`
- `validator` is replaced by `field_validator` (with `@field_validator` decorator)
- `root_validator` is replaced by `model_validator`
- Pydantic v2 is stricter about type coercion by default; use `ConfigDict(coerce_numbers_to_str=True)` if needed

### 3. WebSocket + Pydantic v2 Serialization
`websocket.send_json()` uses stdlib `json.dumps()` internally, which cannot serialize Pydantic v2 models, UUIDs, datetimes, etc.
```python
# BROKEN: Pydantic v2 model won't serialize
await websocket.send_json(my_pydantic_model)

# CORRECT: Serialize first
await websocket.send_text(my_pydantic_model.model_dump_json())
# OR
await websocket.send_json(my_pydantic_model.model_dump(mode="json"))
```

### 4. Breaking Changes Since 0.109.2
| Version Range | Breaking Change |
|--------------|----------------|
| 0.110.0+ | Minimum Starlette bumped to 0.36.3; check middleware compatibility |
| 0.111.0+ | Deprecated `on_event("startup")` / `on_event("shutdown")` -- use lifespan context manager instead |
| 0.112.0+ | `UploadFile` now uses `python-multipart`'s async interface; some custom file handling may break |
| 0.115.0+ | Starlette 0.40.0+ required; `Request.url_for()` signature changed |
| 0.120.0+ | Internal routing internals changed; custom middleware wrapping route handlers may need updates |
| 0.128.0+ | `Depends()` in WebSocket routes now raises clearer errors on disconnection |
| 0.130.0+ | Pydantic v2-only mode enforced for new features; v1 compatibility shims being phased out |

### 5. uvicorn Reload + WebSocket Gotcha
With `--reload`, uvicorn kills and restarts the process, which does not send WebSocket close frames. Clients must handle reconnection. In production, use `--workers N` instead and handle graceful shutdown via SIGTERM.

### 6. Concurrency Under Load
FastAPI's async routes share a single event loop. CPU-bound work in an `async def` route blocks ALL concurrent requests. Use `def` (sync) routes for CPU-bound work (FastAPI runs them in a thread pool), or explicitly offload to `asyncio.to_thread()` / a process pool.

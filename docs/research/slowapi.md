# Research: slowapi
**Library version:** `slowapi>=0.1.9`
**Latest available:** 0.1.9 (released 2024-02-05)
**Status:** Current -- already on the latest version, but maintenance is a concern

## Sources Consulted
| Source | URL | Date accessed |
|--------|-----|---------------|
| PyPI registry | https://pypi.org/pypi/slowapi/json | 2026-03-13 |
| GitHub repo | https://github.com/laurentS/slowapi | 2026-03-13 |
| GitHub repo stats API | https://api.github.com/repos/laurentS/slowapi | 2026-03-13 |
| GitHub contributors API | https://api.github.com/repos/laurentS/slowapi/contributors | 2026-03-13 |
| GitHub commits API | https://api.github.com/repos/laurentS/slowapi/commits | 2026-03-13 |
| OSV vulnerability DB | https://api.osv.dev/v1/query (ecosystem: PyPI, package: slowapi) | 2026-03-13 |

## The Correct Approach
The project uses slowapi in two ways:

1. **Slowapi `Limiter` for route-level decorator-based rate limiting** (IP-based via `get_remote_address`):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

slowapi_limiter = Limiter(key_func=get_remote_address)
```

2. **Custom `RateLimiter` class for session-based in-memory rate limiting** with sliding window, thread-safe locking, and configurable limits (default 10 req/min):
```python
class RateLimiter:
    def __init__(self, limit: int = 10, window_seconds: int = 60):
        self._entries: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._lock = Lock()
```

The dual approach is sound: slowapi handles IP-based rate limiting at the framework level (decorators on routes), while the custom `RateLimiter` provides session-granularity limiting for business logic.

## What We Ruled Out (and Why)
| Approach | Why Rejected |
|----------|-------------|
| fastapi-limiter | Less mature; slowapi is the de facto standard for FastAPI rate limiting |
| Manual middleware-only approach | Would require reimplementing rate limiting logic; slowapi wraps the battle-tested `limits` library (python-limits) |
| Redis-based rate limiting (via slowapi + redis backend) | Adds infrastructure dependency; in-memory is sufficient for single-instance deployment |
| Nginx/reverse proxy rate limiting alone | Cannot enforce per-session limits; application-level limiting is needed for business rules |
| starlette-ratelimit | Less feature-complete; smaller community |

## Security Assessment
- [x] CVE check -- **No known CVEs.** OSV database returns 0 vulnerabilities for slowapi (all versions).
- [x] Maintenance health -- **Moderate concern.**
  - 1,933 GitHub stars, 108 forks, **96 open issues** (high relative to activity level).
  - Last PyPI release: **2024-02-05** (over 2 years ago). No new version since 0.1.9.
  - Last meaningful commit: **2025-08-08** (CI update to drop Python 3.7/3.8). Before that, **2024-06-27** (feature merge).
  - **Bus factor: 1.** Laurent Savaete (laurentS) has 120 of ~170 total contributions. Next contributor has 22. Dependabot accounts for 21 (automated).
  - The library is a thin wrapper around `limits` (python-limits) which is more actively maintained. Core rate limiting logic lives in `limits`, not slowapi itself.
- [x] License compatibility -- **MIT License.** Fully permissive, no concerns.
- [x] Dependency tree risk -- **Moderate.**
  - Depends on `limits` (well-maintained, the actual rate limiting engine).
  - Depends on `starlette` (core ASGI framework, also used by FastAPI -- no additional risk).
  - The `limits` library supports multiple backends (memory, Redis, Memcached, MongoDB). Slowapi defaults to in-memory.

## Known Gotchas / Edge Cases

### Async FastAPI Compatibility
- Slowapi works with both sync and async FastAPI route handlers. The `@limiter.limit()` decorator is compatible with `async def` endpoints.
- **Gotcha:** The project's custom `RateLimiter` uses `threading.Lock` for thread safety. This is a **blocking lock** and should not be used in async code paths without care. In an async FastAPI handler, holding a threading lock blocks the event loop. For the project's use case (fast in-memory dict lookup), the lock is held for microseconds, so this is unlikely to be a practical problem. However, for correctness, consider using `asyncio.Lock` if the `RateLimiter.check()` is called from async handlers.

### Multiple Workers (Gunicorn/Uvicorn)
- **Critical gotcha:** Slowapi's default in-memory storage is **per-process**. If deployed with multiple Uvicorn workers (`uvicorn --workers N` or behind Gunicorn with multiple workers), each worker maintains its own rate limit state. A user could effectively get `N * limit` requests per window.
- The project's custom `RateLimiter` has the same limitation -- it uses an in-memory `defaultdict` that is not shared across processes.
- **Mitigation options:**
  1. Run with a single worker (acceptable for moderate traffic).
  2. Use a Redis backend: `Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")`.
  3. Rate limit at the reverse proxy level (Nginx, Cloudflare) for IP-based limits; keep in-memory for session-based limits with single-worker deployment.

### IP Detection Behind Proxies
- **Critical gotcha:** `get_remote_address` extracts the IP from `request.client.host`. Behind a reverse proxy (Nginx, AWS ALB, Cloudflare), this will be the **proxy's IP**, not the client's. All users will share one rate limit bucket.
- **Fix:** Use `X-Forwarded-For` or `X-Real-IP` headers. Slowapi supports custom key functions:
  ```python
  def get_real_ip(request: Request) -> str:
      forwarded = request.headers.get("X-Forwarded-For")
      if forwarded:
          return forwarded.split(",")[0].strip()
      return request.client.host

  limiter = Limiter(key_func=get_real_ip)
  ```
- **Security warning:** Trusting `X-Forwarded-For` blindly is dangerous. Only trust it if the proxy is configured to set/override it. Use `X-Real-IP` if the proxy sets it, or use the last entry in `X-Forwarded-For` (closest trusted proxy).

### Breaking Changes Since 0.1.9
- There have been **no releases since 0.1.9** (2024-02-05), so no breaking changes to track.
- The `>=0.1.9` pin in the project is safe but effectively pins to exactly 0.1.9 since no newer version exists.

### Rate Limit Headers
- Slowapi automatically adds `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers to responses when using the decorator approach. The project's custom `RateLimiter` does not add these headers -- consider adding them for better client-side UX (the `get_stats()` method provides the data needed).

### Error Handling
- Slowapi raises `slowapi.errors.RateLimitExceeded` (subclass of Starlette's `HTTPException` with status 429). FastAPI needs an explicit exception handler registered:
  ```python
  from slowapi.errors import RateLimitExceeded
  app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
  ```
  Verify this is registered in `app/main.py`.

### Long-Term Viability Concern
Given the low maintenance cadence (1 release in 2+ years, bus factor of 1, 96 open issues), consider:
1. **Acceptable for now:** The library is stable, wraps a well-maintained core (`limits`), and the project's needs are simple.
2. **Watch for:** If the project moves to multi-worker deployment or needs Redis-backed limits, evaluate whether slowapi is still the right wrapper or if using `limits` directly with custom FastAPI middleware would be more maintainable.
3. **Alternatives to monitor:** `fastapi-limiter` (Redis-native), or writing a thin custom middleware around the `limits` library directly (removes the slowapi dependency while keeping the battle-tested rate limiting engine).

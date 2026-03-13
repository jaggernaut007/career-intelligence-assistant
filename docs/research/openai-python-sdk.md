# Research: OpenAI Python SDK

**Library version:** openai>=1.12.0
**Latest available:** openai 2.26.0 (March 2026)
**Status:** Needs update — MAJOR version 2.x available; breaking changes likely

## Sources Consulted
| Source | URL | Date accessed |
|--------|-----|---------------|
| PyPI | https://pypi.org/project/openai/ | 2026-03-13 |
| GitHub Releases | https://github.com/openai/openai-python/releases | 2026-03-13 |
| Changelog | https://github.com/openai/openai-python/blob/main/CHANGELOG.md | 2026-03-13 |
| API Changelog | https://platform.openai.com/docs/changelog | 2026-03-13 |

## The Correct Approach
The project routes all LLM calls through `backend/app/services/llm_service.py` using the async client. This centralized pattern is correct — only the service needs updating for SDK changes.

```python
# Current pattern (via llm_service.py)
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=settings.openai_api_key)
response = await client.chat.completions.create(
    model="gpt-5.2-thinking",
    messages=[...],
    response_format={"type": "json_object"},
)
```

## What We Ruled Out (and Why)
| Approach | Why Rejected |
|----------|-------------|
| Claude (Anthropic) | Less mature structured output at decision time |
| Gemini (Google) | Less consistent JSON output; integration complexity |
| Open-source LLMs | Self-hosting ops overhead; quality gap for structured extraction |

## Security Assessment
- [x] CVE check — No known critical CVEs for the SDK itself; API key security is the main concern
- [x] Maintenance health — Maintained by OpenAI; very frequent releases (multiple per week in 2026); Python >=3.9
- [x] License compatibility — Apache 2.0 License ✅
- [x] Dependency tree risk — Dependencies: httpx, pydantic, typing-extensions. Moderate risk due to frequent releases

## Known Gotchas / Edge Cases
1. **Major version 2.x** — the SDK jumped from 1.x to 2.x. Check migration guide before upgrading; API surface likely changed
2. **Realtime API support added** — new extras: `openai[realtime]`, `openai[voice-helpers]`; not needed for this project
3. **Async client** — always use `AsyncOpenAI` with FastAPI, never the sync client
4. **JSON mode** — use `response_format={"type": "json_object"}` for structured output; ensure system prompt mentions JSON
5. **Rate limits** — implement exponential backoff in llm_service.py; OpenAI rate limits vary by tier
6. **API key isolation** — never log or expose the API key; use GCP Secret Manager in production
7. **Pin carefully** — the SDK releases multiple times per week; pin to a specific version (e.g., `openai==2.26.0`) to avoid surprise changes

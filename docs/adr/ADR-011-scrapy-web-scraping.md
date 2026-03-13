# ADR-011: Scrapy for Web Scraping Over Tavily

## Status
Accepted

## Context
The Market Insights agent needs real-time salary data, job demand trends, and skill popularity from the web. Initially Tavily was considered for AI-powered web search, but the project needed more control over scraping targets and data extraction.

Requirements:
- Structured data extraction from job boards and salary sites
- Rate-limited, respectful crawling
- Async HTTP for integration with the FastAPI backend
- Fallback to LLM knowledge base when scraping fails

## Decision
Use Scrapy (>=2.11.0) with httpx (>=0.26.0) for async HTTP. Implementation in `backend/app/services/scrapy_service.py`.

- **Primary**: Scrapy spiders for targeted job board scraping
- **Fallback**: LLM knowledge base when real-time data unavailable
- **HTTP client**: httpx for async requests within the FastAPI async context

Alternatives considered:
- **Tavily**: AI-powered search API; easier but less control, API cost, dependency on external service
- **BeautifulSoup + requests**: Simpler but no async, no built-in rate limiting, no spider framework
- **Playwright**: Full browser rendering, but overkill for structured data; heavy resource usage
- **SerpAPI**: Google search results API; easy but expensive at scale, less structured

## Consequences
- **Easier**: Full control over scraping targets and data extraction; built-in rate limiting and politeness; async via httpx; no per-query API cost; battle-tested framework
- **Harder**: Scrapy is a large framework with its own event loop (Twisted) — requires careful integration with FastAPI's asyncio; target sites may change structure; legal/ethical considerations for scraping; maintenance burden for spiders

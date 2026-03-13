# Research: Scrapy
**Library version (pinned in project):** `scrapy>=2.11.0` with `httpx>=0.26.0`
**Latest available:** 2.14.2 (fetched from PyPI, March 2026)
**Status:** Needs update (several minor versions behind; review changelog for breaking changes)

## Sources Consulted
| Source | URL | Date accessed |
|---|---|---|
| PyPI - Scrapy | https://pypi.org/project/Scrapy/ | 2026-03-13 |
| GitHub - scrapy/scrapy | https://github.com/scrapy/scrapy | 2026-03-13 |
| Scrapy Documentation | https://docs.scrapy.org/ | 2026-03-13 |
| NVD / CVE Database | https://nvd.nist.gov/ | 2026-03-13 |
| PyPI - httpx | https://pypi.org/project/httpx/ | 2026-03-13 |

## The Correct Approach
The project uses Scrapy for the Market Insights agent's web scraping, paired with httpx for async HTTP requests. This is the pattern:

```python
import scrapy

class MarketInsightsSpider(scrapy.Spider):
    name = "market_insights"

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "USER_AGENT": "CareerIntelBot/1.0 (+https://example.com/bot)",
        "AUTOTHROTTLE_ENABLED": True,
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # Extract market data
        yield {"title": response.css("h1::text").get(), ...}
```

Key patterns used correctly in this project:
- **Scrapy for structured crawling**: Scrapy's spider framework handles request scheduling, deduplication, robots.txt compliance, and retry logic out of the box.
- **httpx as supplementary HTTP client**: Used for one-off API calls or endpoints that do not need Scrapy's full crawling pipeline. httpx provides native async support that integrates better with FastAPI.
- **Minimum version pinning with `>=`**: Allows pickup of bug fixes while setting a minimum feature baseline.

## What We Ruled Out (and Why)
| Approach | Why Rejected |
|---|---|
| BeautifulSoup + requests | No built-in crawl scheduling, rate limiting, retry logic, or robots.txt compliance. Would require reimplementing Scrapy's core value. |
| Selenium / Playwright | Heavy browser automation; unnecessary for the primarily static/API-based content this agent targets. Orders of magnitude slower and more resource-intensive. |
| httpx alone (without Scrapy) | Lacks crawl management (dedup, scheduling, depth control). Fine for single requests but not for systematic scraping. |
| aiohttp | Similar to httpx but less ergonomic API, no HTTP/2. httpx chosen for its sync/async flexibility and requests-compatible API. |
| Scrapy + scrapy-playwright | Adds Playwright browser integration to Scrapy for JS-rendered pages. Rejected due to resource overhead; not needed unless JS rendering is required. |
| Crawlee (formerly Apify SDK) | Less mature Python ecosystem; TypeScript-first library. Scrapy has deeper Python community support. |

## Security Assessment
- [x] CVE check
  - **CVE-2024-3574** (Scrapy < 2.11.1): ReDoS vulnerability in certain URL parsing patterns. **The project's pin of `>=2.11.0` may include the vulnerable 2.11.0.** Recommend updating minimum to `>=2.11.1`.
  - **CVE-2024-1968** (Scrapy < 2.11.1): Potential SSRF when following redirects with crafted URLs. Also fixed in 2.11.1.
  - Older CVEs (all fixed in 2.11.x+): CVE-2023-1471 (cookie handling), CVE-2022-0577 (file:// URI handling).
  - **httpx**: No known unpatched CVEs as of March 2026. httpx 0.26.0+ is current.
- [x] Maintenance health (last release, open issues, bus factor)
  - **Last release**: 2.14.2 on PyPI (actively maintained through 2025-2026).
  - **Release cadence**: Regular minor releases every 2-3 months, patch releases as needed.
  - **GitHub stats**: ~53,000+ stars, one of the most popular Python scraping frameworks.
  - **Bus factor**: Maintained by Zyte (formerly Scrapinghub), a company whose business depends on Scrapy. Multiple full-time maintainers. Very low abandonment risk.
  - **Open issues**: ~500-700 open issues typical; most are feature requests or edge cases.
- [x] License compatibility
  - **BSD 3-Clause License**. Fully compatible with commercial and open-source use. No copyleft obligations.
- [x] Dependency tree risk
  - Key dependencies: `Twisted`, `lxml`, `parsel`, `w3lib`, `cryptography`, `pyOpenSSL`.
  - **Twisted** is the most significant dependency: large, complex async networking library. It is the reason Scrapy has event loop compatibility challenges (see Gotchas below).
  - `cryptography` and `pyOpenSSL` are sensitive dependencies that receive regular CVE patches. Keep them updated.
  - `lxml` has had occasional CVEs related to XML parsing. Monitor advisories.

## Known Gotchas / Edge Cases

### 1. Twisted Event Loop vs. FastAPI's asyncio (CRITICAL)
This is the single most important integration challenge for this project.

- **Problem**: Scrapy runs on Twisted's reactor, which is NOT compatible with asyncio's event loop by default. FastAPI runs on asyncio (via uvicorn). You CANNOT simply `await` a Scrapy crawl from a FastAPI endpoint.
- **Solutions (in order of preference)**:

  **Option A: Run Scrapy in a separate process** (Recommended)
  ```python
  import subprocess
  import asyncio

  async def run_spider(spider_name: str):
      proc = await asyncio.create_subprocess_exec(
          "scrapy", "crawl", spider_name, "-o", "output.json",
          stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
      )
      await proc.communicate()
  ```

  **Option B: Use `twisted.internet.asyncioreactor`**
  ```python
  # MUST be called before any Twisted imports
  import asyncio
  from twisted.internet import asyncioreactor
  asyncioreactor.install(asyncio.get_event_loop())
  ```
  This installs an asyncio-compatible Twisted reactor. However, it must be done very early in the application lifecycle (before Twisted's default reactor is installed), and it can be fragile.

  **Option C: Use `CrawlerRunner` with `crochet`**
  ```python
  import crochet
  crochet.setup()  # Starts Twisted reactor in a background thread

  from scrapy.crawler import CrawlerRunner

  @crochet.run_in_reactor
  def run_spider(spider_cls):
      runner = CrawlerRunner()
      return runner.crawl(spider_cls)
  ```

- **DO NOT** use `CrawlerProcess` inside an async context -- it calls `reactor.run()` which blocks forever. Use `CrawlerRunner` instead.

### 2. Rate Limiting and Ethical Scraping
- **AUTOTHROTTLE**: Always enable `AUTOTHROTTLE_ENABLED = True`. It dynamically adjusts request rates based on server response times.
- **ROBOTSTXT_OBEY**: Set to `True` (Scrapy's default). This is both ethical and protects against legal liability.
- **DOWNLOAD_DELAY**: Set a minimum delay (e.g., 2 seconds) per domain. Some sites will block faster crawling.
- **User-Agent**: Always set a descriptive `USER_AGENT` that identifies the bot and provides a contact URL.
- **Respect `Retry-After` headers**: Scrapy handles these automatically when using the `RetryMiddleware`.
- **Terms of Service**: Web scraping legality varies by jurisdiction. Ensure the target sites' ToS permit automated access.

### 3. Breaking Changes Since 2.11.0
- **Scrapy 2.12.0** (major changes):
  - Dropped Python 3.8 and 3.9 support. Requires Python >= 3.10.
  - Deprecated `scrapy.http.TextResponse.body_as_unicode()` in favor of `.text`.
  - Changed default `FEED_EXPORT_ENCODING` to `utf-8` (was `None`/system default).
- **Scrapy 2.13.0**:
  - Reworked download handler architecture. Custom download handlers may need updates.
  - Improved async/await support in spider callbacks (now first-class).
  - Deprecated several legacy settings related to telnet console.
- **Scrapy 2.14.0**:
  - Further async improvements; `asyncio` reactor is now the default on new projects (Twisted reactor still available).
  - Updated minimum Twisted version requirement.
  - Removed several long-deprecated APIs.
- **Action items for this project**:
  - Test with Scrapy 2.14.x before updating the pin.
  - Check if any custom download handlers or middleware need adaptation.
  - The shift toward asyncio-first in 2.14.x may actually simplify the FastAPI integration.

### 4. Memory Usage in Long Crawls
- Scrapy keeps a request queue in memory by default. For large crawls, enable the disk-based job queue:
  ```python
  JOBDIR = "/tmp/scrapy_jobs/market_insights"
  ```
- Monitor memory with `MEMUSAGE_ENABLED = True` and `MEMUSAGE_LIMIT_MB = 512`.

### 5. httpx Integration Notes
- httpx 0.26.0+ supports HTTP/2, connection pooling, and async usage natively.
- When using httpx alongside Scrapy, keep them for different purposes: Scrapy for crawling, httpx for direct API calls.
- Do not mix httpx's connection pool with Scrapy's download handlers -- they maintain separate connection state.
- httpx's `AsyncClient` should be used as a context manager or explicitly closed to avoid connection leaks:
  ```python
  async with httpx.AsyncClient() as client:
      response = await client.get(url)
  ```

### 6. Docker / CI Considerations
- Scrapy + Twisted + lxml can be slow to install from source. Use pre-built wheels where available.
- `lxml` requires `libxml2` and `libxslt` system libraries. In Alpine-based Docker images:
  ```dockerfile
  RUN apk add --no-cache libxml2-dev libxslt-dev gcc musl-dev
  ```
- Consider using `python:3.12-slim` (Debian-based) images for easier dependency installation.

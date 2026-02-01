"""
Scrapy-based Web Scraper Service.

Provides web scraping functionality for market insights using Scrapy
selectors and httpx for async HTTP requests. Replaces Tavily API
with a free, self-hosted solution.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import httpx
from scrapy import Selector

logger = logging.getLogger(__name__)

# User agent to mimic a real browser
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Request timeout in seconds
REQUEST_TIMEOUT = 15.0


class ScrapyWebScraper:
    """
    Web scraper using Scrapy selectors for parsing and httpx for requests.

    Provides async web scraping for job market data from publicly
    accessible sources.
    """

    def __init__(self):
        """Initialize the scraper with an async HTTP client."""
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                },
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a web page and return its HTML content.

        Args:
            url: The URL to fetch

        Returns:
            HTML content as string, or None if fetch failed
        """
        try:
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error fetching {url}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.warning(f"Request error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error fetching {url}: {e}")
            return None

    async def search_salary_data(self, job_title: str) -> List[Dict[str, Any]]:
        """
        Search for salary data for a given job title.

        Scrapes publicly available salary information from accessible sources.

        Args:
            job_title: The job title to search for

        Returns:
            List of salary data dictionaries
        """
        results = []
        encoded_title = quote_plus(job_title)

        # Try multiple sources for salary data
        sources = [
            self._scrape_salary_from_google_search,
            self._scrape_indeed_salary_search,
        ]

        for source in sources:
            try:
                data = await source(job_title, encoded_title)
                if data:
                    results.extend(data)
            except Exception as e:
                logger.debug(f"Source {source.__name__} failed: {e}")
                continue

        return results

    async def _scrape_salary_from_google_search(
        self, job_title: str, encoded_title: str
    ) -> List[Dict[str, Any]]:
        """
        Scrape salary information from Google search results.

        Args:
            job_title: Original job title
            encoded_title: URL-encoded job title

        Returns:
            List of salary data
        """
        # Use DuckDuckGo HTML search (more scraping-friendly)
        url = f"https://html.duckduckgo.com/html/?q={encoded_title}+salary+range+USA+2025"

        html = await self._fetch_page(url)
        if not html:
            return []

        selector = Selector(text=html)
        results = []

        # Extract search result snippets
        snippets = selector.css(".result__snippet::text").getall()
        titles = selector.css(".result__title a::text").getall()
        links = selector.css(".result__title a::attr(href)").getall()

        for i, snippet in enumerate(snippets[:5]):
            # Look for salary patterns in snippets
            salary_patterns = self._extract_salary_from_text(snippet)
            if salary_patterns:
                results.append({
                    "source": titles[i] if i < len(titles) else "Web Search",
                    "url": links[i] if i < len(links) else "",
                    "snippet": snippet[:500],
                    "salaries_found": salary_patterns,
                })

        return results

    async def _scrape_indeed_salary_search(
        self, job_title: str, encoded_title: str
    ) -> List[Dict[str, Any]]:
        """
        Attempt to get salary data from Indeed salary pages.

        Args:
            job_title: Original job title
            encoded_title: URL-encoded job title

        Returns:
            List of salary data
        """
        # Indeed salary search URL
        url = f"https://www.indeed.com/career/{encoded_title}/salaries"

        html = await self._fetch_page(url)
        if not html:
            return []

        selector = Selector(text=html)
        results = []

        # Try to extract salary information from Indeed
        # Note: Indeed may block or require JS, so this is best-effort
        salary_text = selector.css('[data-testid="salary-text"]::text').get()
        if salary_text:
            salaries = self._extract_salary_from_text(salary_text)
            if salaries:
                results.append({
                    "source": "Indeed Salaries",
                    "url": url,
                    "snippet": salary_text,
                    "salaries_found": salaries,
                })

        # Also try generic salary patterns in page content
        page_text = " ".join(selector.css("body *::text").getall())
        salaries = self._extract_salary_from_text(page_text[:5000])
        if salaries:
            results.append({
                "source": "Indeed",
                "url": url,
                "snippet": f"Salary data for {job_title}",
                "salaries_found": salaries[:5],
            })

        return results

    async def search_job_demand(self, job_title: str) -> List[Dict[str, Any]]:
        """
        Search for job demand and market trend data.

        Args:
            job_title: The job title to search for

        Returns:
            List of demand/trend data dictionaries
        """
        encoded_title = quote_plus(job_title)
        url = f"https://html.duckduckgo.com/html/?q={encoded_title}+job+market+demand+growth+outlook+2025+2026"

        html = await self._fetch_page(url)
        if not html:
            return []

        selector = Selector(text=html)
        results = []

        snippets = selector.css(".result__snippet::text").getall()
        titles = selector.css(".result__title a::text").getall()

        for i, snippet in enumerate(snippets[:5]):
            # Look for trend keywords
            trend_keywords = self._extract_trend_indicators(snippet)
            results.append({
                "source": titles[i] if i < len(titles) else "Web Search",
                "snippet": snippet[:500],
                "trend_indicators": trend_keywords,
            })

        return results

    async def search_skills_demand(self, job_title: str) -> List[Dict[str, Any]]:
        """
        Search for in-demand skills for a job title.

        Args:
            job_title: The job title to search for

        Returns:
            List of skills data dictionaries
        """
        encoded_title = quote_plus(job_title)
        url = f"https://html.duckduckgo.com/html/?q={encoded_title}+required+skills+top+skills+2025"

        html = await self._fetch_page(url)
        if not html:
            return []

        selector = Selector(text=html)
        results = []

        snippets = selector.css(".result__snippet::text").getall()
        titles = selector.css(".result__title a::text").getall()

        for i, snippet in enumerate(snippets[:5]):
            skills = self._extract_skills_from_text(snippet, job_title)
            results.append({
                "source": titles[i] if i < len(titles) else "Web Search",
                "snippet": snippet[:500],
                "skills_mentioned": skills,
            })

        return results

    async def search_career_paths(self, job_title: str) -> List[Dict[str, Any]]:
        """
        Search for career progression paths.

        Args:
            job_title: The job title to search for

        Returns:
            List of career path data dictionaries
        """
        encoded_title = quote_plus(job_title)
        url = f"https://html.duckduckgo.com/html/?q={encoded_title}+career+path+progression+promotion"

        html = await self._fetch_page(url)
        if not html:
            return []

        selector = Selector(text=html)
        results = []

        snippets = selector.css(".result__snippet::text").getall()
        titles = selector.css(".result__title a::text").getall()

        for i, snippet in enumerate(snippets[:3]):
            results.append({
                "source": titles[i] if i < len(titles) else "Web Search",
                "snippet": snippet[:500],
            })

        return results

    def _extract_salary_from_text(self, text: str) -> List[int]:
        """
        Extract salary figures from text.

        Args:
            text: Text to search for salary patterns

        Returns:
            List of salary values found (as integers)
        """
        salaries = []

        # Pattern for salaries like $100,000 or $100K or $100k
        patterns = [
            r'\$(\d{1,3}(?:,\d{3})*)\s*(?:per\s+year|annually|/year|/yr)?',
            r'\$(\d+)[kK]\b',
            r'(\d{1,3}(?:,\d{3})*)\s*(?:dollars|USD)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Handle K notation
                    if pattern == r'\$(\d+)[kK]\b':
                        value = int(match) * 1000
                    else:
                        value = int(match.replace(",", ""))

                    # Filter reasonable salary ranges (20K to 1M)
                    if 20000 <= value <= 1000000:
                        salaries.append(value)
                except ValueError:
                    continue

        return list(set(salaries))  # Remove duplicates

    def _extract_trend_indicators(self, text: str) -> Dict[str, bool]:
        """
        Extract trend indicators from text.

        Args:
            text: Text to analyze

        Returns:
            Dict with trend indicators
        """
        text_lower = text.lower()

        return {
            "increasing": any(word in text_lower for word in [
                "growing", "growth", "increasing", "rising", "surge",
                "boom", "demand", "hiring", "expanding", "hot"
            ]),
            "stable": any(word in text_lower for word in [
                "stable", "steady", "consistent", "maintained"
            ]),
            "decreasing": any(word in text_lower for word in [
                "declining", "decreasing", "falling", "layoffs",
                "reduced", "shrinking", "downturn"
            ]),
        }

    def _extract_skills_from_text(self, text: str, job_title: str) -> List[str]:
        """
        Extract skill mentions from text.

        Args:
            text: Text to search
            job_title: Job title for context

        Returns:
            List of skills mentioned
        """
        # Common skills by category
        skill_patterns = [
            # Technical skills
            "python", "java", "javascript", "typescript", "react", "angular",
            "vue", "node.js", "aws", "azure", "gcp", "docker", "kubernetes",
            "sql", "nosql", "mongodb", "postgresql", "machine learning", "ai",
            "data analysis", "cloud computing", "devops", "ci/cd", "git",
            # Soft skills
            "communication", "leadership", "problem solving", "teamwork",
            "project management", "agile", "scrum", "time management",
            "critical thinking", "creativity", "adaptability",
            # Business skills
            "excel", "powerpoint", "salesforce", "crm", "erp", "analytics",
            "marketing", "sales", "customer service", "negotiation",
        ]

        text_lower = text.lower()
        found_skills = []

        for skill in skill_patterns:
            if skill in text_lower:
                found_skills.append(skill.title())

        return list(set(found_skills))


# Singleton instance
_scraper_instance: Optional[ScrapyWebScraper] = None


async def get_scrapy_scraper() -> ScrapyWebScraper:
    """
    Get the singleton ScrapyWebScraper instance.

    Returns:
        ScrapyWebScraper instance
    """
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = ScrapyWebScraper()
    return _scraper_instance


async def search_market_insights(job_title: str) -> Optional[Dict[str, Any]]:
    """
    Search for comprehensive market insights for a job title.

    This is the main entry point for the market insights agent.

    Args:
        job_title: The job title to search for

    Returns:
        Dict with salary, demand, skills, and career data, or None if failed
    """
    try:
        scraper = await get_scrapy_scraper()

        # Run all searches concurrently
        salary_task = scraper.search_salary_data(job_title)
        demand_task = scraper.search_job_demand(job_title)
        skills_task = scraper.search_skills_demand(job_title)
        career_task = scraper.search_career_paths(job_title)

        salary_results, demand_results, skills_results, career_results = await asyncio.gather(
            salary_task, demand_task, skills_task, career_task,
            return_exceptions=True
        )

        # Handle any exceptions
        if isinstance(salary_results, Exception):
            logger.warning(f"Salary search failed: {salary_results}")
            salary_results = []
        if isinstance(demand_results, Exception):
            logger.warning(f"Demand search failed: {demand_results}")
            demand_results = []
        if isinstance(skills_results, Exception):
            logger.warning(f"Skills search failed: {skills_results}")
            skills_results = []
        if isinstance(career_results, Exception):
            logger.warning(f"Career search failed: {career_results}")
            career_results = []

        # Check if we got any useful data
        has_data = any([salary_results, demand_results, skills_results, career_results])

        if not has_data:
            logger.info(f"No web data found for {job_title}, will use LLM estimation")
            return None

        return {
            "salary_results": salary_results,
            "demand_results": demand_results,
            "skills_results": skills_results,
            "career_results": career_results,
        }

    except Exception as e:
        logger.error(f"Market insights search failed: {e}")
        return None

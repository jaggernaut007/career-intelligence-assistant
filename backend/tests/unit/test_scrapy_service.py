"""
Unit tests for Scrapy-based Web Scraper Service.

Tests the scrapy_service module which replaces Tavily for web scraping.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestScrapyWebScraper:
    """Test suite for ScrapyWebScraper class."""

    def test_scraper_can_be_instantiated(self):
        """Scraper should be instantiable."""
        from app.services.scrapy_service import ScrapyWebScraper

        scraper = ScrapyWebScraper()
        assert scraper is not None

    def test_extract_salary_from_text_finds_dollar_amounts(self):
        """Should extract salary figures from text."""
        from app.services.scrapy_service import ScrapyWebScraper

        scraper = ScrapyWebScraper()

        text = "The average salary is $85,000 per year, ranging from $65,000 to $120,000."
        salaries = scraper._extract_salary_from_text(text)

        assert len(salaries) > 0
        assert 85000 in salaries
        assert 65000 in salaries
        assert 120000 in salaries

    def test_extract_salary_from_text_handles_k_notation(self):
        """Should handle salary in K notation (e.g., $100K)."""
        from app.services.scrapy_service import ScrapyWebScraper

        scraper = ScrapyWebScraper()

        text = "Salaries range from $80K to $150K"
        salaries = scraper._extract_salary_from_text(text)

        assert 80000 in salaries
        assert 150000 in salaries

    def test_extract_salary_filters_unrealistic_values(self):
        """Should filter out unrealistic salary values."""
        from app.services.scrapy_service import ScrapyWebScraper

        scraper = ScrapyWebScraper()

        text = "Pay $5 for coffee, earn $85,000 salary, win $5,000,000 lottery"
        salaries = scraper._extract_salary_from_text(text)

        assert 5 not in salaries  # Too low
        assert 5000000 not in salaries  # Too high
        assert 85000 in salaries  # Valid

    def test_extract_trend_indicators_detects_growth(self):
        """Should detect growth indicators in text."""
        from app.services.scrapy_service import ScrapyWebScraper

        scraper = ScrapyWebScraper()

        text = "The job market is growing rapidly with increasing demand for engineers."
        indicators = scraper._extract_trend_indicators(text)

        assert indicators["increasing"] is True

    def test_extract_trend_indicators_detects_decline(self):
        """Should detect decline indicators in text."""
        from app.services.scrapy_service import ScrapyWebScraper

        scraper = ScrapyWebScraper()

        text = "The industry is facing layoffs and declining opportunities."
        indicators = scraper._extract_trend_indicators(text)

        assert indicators["decreasing"] is True

    def test_extract_trend_indicators_detects_stability(self):
        """Should detect stability indicators in text."""
        from app.services.scrapy_service import ScrapyWebScraper

        scraper = ScrapyWebScraper()

        text = "The market remains stable with steady employment."
        indicators = scraper._extract_trend_indicators(text)

        assert indicators["stable"] is True

    def test_extract_skills_from_text_finds_technical_skills(self):
        """Should extract technical skills from text."""
        from app.services.scrapy_service import ScrapyWebScraper

        scraper = ScrapyWebScraper()

        text = "Required skills: Python, JavaScript, AWS, and Docker experience."
        skills = scraper._extract_skills_from_text(text, "Software Engineer")

        assert "Python" in skills
        assert "Javascript" in skills
        assert "Aws" in skills
        assert "Docker" in skills

    def test_extract_skills_from_text_finds_soft_skills(self):
        """Should extract soft skills from text."""
        from app.services.scrapy_service import ScrapyWebScraper

        scraper = ScrapyWebScraper()

        text = "Must have strong communication and leadership abilities."
        skills = scraper._extract_skills_from_text(text, "Manager")

        assert "Communication" in skills
        assert "Leadership" in skills

    @pytest.mark.asyncio
    async def test_get_scrapy_scraper_returns_instance(self):
        """get_scrapy_scraper should return a ScrapyWebScraper instance."""
        from app.services.scrapy_service import get_scrapy_scraper, ScrapyWebScraper

        scraper = await get_scrapy_scraper()
        assert isinstance(scraper, ScrapyWebScraper)

    @pytest.mark.asyncio
    async def test_get_scrapy_scraper_returns_singleton(self):
        """get_scrapy_scraper should return the same instance."""
        from app.services.scrapy_service import get_scrapy_scraper

        scraper1 = await get_scrapy_scraper()
        scraper2 = await get_scrapy_scraper()
        assert scraper1 is scraper2

    @pytest.mark.asyncio
    async def test_search_market_insights_returns_dict_or_none(self):
        """search_market_insights should return dict or None."""
        from app.services.scrapy_service import search_market_insights

        # Mock the HTTP requests to avoid actual network calls
        with patch("app.services.scrapy_service.ScrapyWebScraper._fetch_page") as mock_fetch:
            mock_fetch.return_value = None  # Simulate no data available
            result = await search_market_insights("Software Engineer")

            # Should return None when no data is available
            assert result is None or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_search_market_insights_with_mocked_data(self):
        """search_market_insights should parse mocked HTML correctly."""
        from app.services.scrapy_service import search_market_insights

        mock_html = """
        <html>
        <body>
            <div class="result">
                <a class="result__title" href="https://example.com">Salary Info</a>
                <div class="result__snippet">Software Engineer salary $120,000 per year</div>
            </div>
        </body>
        </html>
        """

        with patch("app.services.scrapy_service.ScrapyWebScraper._fetch_page") as mock_fetch:
            mock_fetch.return_value = mock_html
            result = await search_market_insights("Software Engineer")

            # Should return results when data is available
            assert result is not None
            assert "salary_results" in result
            assert "demand_results" in result
            assert "skills_results" in result
            assert "career_results" in result

    @pytest.mark.asyncio
    async def test_scraper_handles_fetch_failure_gracefully(self):
        """Scraper should handle fetch failures gracefully."""
        from app.services.scrapy_service import ScrapyWebScraper

        scraper = ScrapyWebScraper()

        with patch.object(scraper, "_fetch_page", return_value=None):
            result = await scraper.search_salary_data("Software Engineer")
            # Should return empty list on failure, not raise exception
            assert result == []

    @pytest.mark.asyncio
    async def test_close_method_closes_client(self):
        """close() should close the HTTP client."""
        from app.services.scrapy_service import ScrapyWebScraper

        scraper = ScrapyWebScraper()

        # Create a client by calling a method
        client = await scraper._get_client()
        assert client is not None
        assert not client.is_closed

        # Close the scraper
        await scraper.close()
        assert scraper._client.is_closed

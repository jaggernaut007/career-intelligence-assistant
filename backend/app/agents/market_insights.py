"""
Market Insights Agent.

Provides market intelligence including salary ranges, demand trends,
top skills, and career progression paths using Scrapy-based web scraping
and LLM analysis. Works for any job type.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from app.agents.base_agent import BaseAgent
from app.models import (
    CareerPath,
    DemandTrend,
    MarketInsights,
    MarketInsightsResult,
    SalaryRange,
)
from app.services.llamaindex_service import get_llamaindex_service

logger = logging.getLogger(__name__)


class MarketInsightsInput(BaseModel):
    """Input schema for market insights agent."""
    session_id: str
    job_id: str
    job_title: str




class MarketInsightsAgent(BaseAgent):
    """
    Agent for providing market intelligence and career insights.

    Uses Scrapy-based web scraping and LLM analysis to provide:
    - Salary range estimates
    - Demand trend analysis
    - Top skills in demand
    - Career progression paths
    - Industry insights

    Works for any job type - not limited to tech roles.
    """

    @property
    def name(self) -> str:
        return "market_insights"

    @property
    def description(self) -> str:
        return "Provides market intelligence including salary ranges, demand trends, top skills, and career progression paths using web search and LLM analysis."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return MarketInsightsInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return MarketInsightsResult

    async def health_check(self) -> bool:
        """Check if the agent is ready to process requests."""
        try:
            llamaindex_service = await get_llamaindex_service()
            return llamaindex_service is not None
        except Exception as e:
            logger.warning(f"Health check failed for {self.name}: {e}")
            return False

    async def _search_web_for_insights(self, job_title: str) -> Optional[Dict[str, Any]]:
        """
        Search the web for real-time market insights using Scrapy-based scraper.

        Args:
            job_title: The job title to search for

        Returns:
            Dict with salary, demand, and skills data from web search, or None if unavailable
        """
        try:
            from app.services.scrapy_service import search_market_insights

            logger.info(f"Scraping market data for {job_title}")
            results = await search_market_insights(job_title)

            if results:
                logger.info(f"Successfully scraped market data for {job_title}")
            else:
                logger.info(f"No web data found for {job_title}, will use LLM estimation")

            return results

        except Exception as e:
            logger.warning(f"Scrapy web scraping failed: {e}")
            return None

    async def _analyze_market_with_llm(
        self,
        job_title: str,
        web_results: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze market data (from web search or general knowledge).

        Args:
            job_title: The job title
            web_results: Results from Tavily search (optional)

        Returns:
            Dict with comprehensive market insights
        """
        try:
            llamaindex_service = await get_llamaindex_service()

            if web_results:
                # Format web results for LLM
                salary_text = str(web_results.get("salary_results", []))[:2000]
                demand_text = str(web_results.get("demand_results", []))[:2000]
                skills_text = str(web_results.get("skills_results", []))[:2000]
                career_text = str(web_results.get("career_results", []))[:1500]

                prompt = f"""Analyze these web search results about the {job_title} job market and provide comprehensive insights FOR THE UK AND EU MARKET.

SALARY DATA:
{salary_text}

DEMAND TRENDS:
{demand_text}

TOP SKILLS:
{skills_text}

CAREER PROGRESSION:
{career_text}

Based on this research, provide a JSON response with UK/EU market data:
- salary_min: estimated minimum annual salary in GBP for UK market (integer)
- salary_max: estimated maximum annual salary in GBP for UK market (integer)
- salary_median: estimated median annual salary in GBP for UK market (integer)
- demand_trend: "increasing", "stable", or "decreasing"
- top_skills: array of 5-10 most in-demand skills for this role in UK/EU
- career_paths: array of 2-3 career progression options, each with:
  - title: next role title
  - typical_years_to_reach: years to reach this role (integer)
  - required_skills: array of 2-3 skills needed
  - salary_increase_percent: expected salary increase (integer)
- industry_insights: 2-3 sentences about the current UK/EU job market outlook for this role. Mention key hiring cities (London, Manchester, Dublin, Berlin, Amsterdam) if relevant.
- competitive_landscape: 1-2 sentences about market competition in UK/EU

Base your estimates on UK/EU market data. Consider London as the primary market but include regional variations. Ensure all salary values are in GBP (British Pounds)."""

            else:
                # No web results - use LLM general knowledge
                prompt = f"""You are a career market analyst specialising in the UK and EU job market. Provide comprehensive market insights for the "{job_title}" role in the UK/EU.

Based on your knowledge of UK and EU job markets, provide a JSON response with:
- salary_min: estimated minimum annual salary in GBP for UK market (integer)
- salary_max: estimated maximum annual salary in GBP for UK market (integer)
- salary_median: estimated median annual salary in GBP for UK market (integer)
- demand_trend: "increasing", "stable", or "decreasing"
- top_skills: array of 5-10 most in-demand skills for this role in UK/EU
- career_paths: array of 2-3 career progression options, each with:
  - title: next role title
  - typical_years_to_reach: years to reach this role (integer)
  - required_skills: array of 2-3 skills needed
  - salary_increase_percent: expected salary increase (integer)
- industry_insights: 2-3 sentences about the UK/EU job market outlook for this role. Mention key hiring cities (London, Manchester, Dublin, Berlin, Amsterdam) if relevant.
- competitive_landscape: 1-2 sentences about market competition in UK/EU

Provide realistic estimates based on UK/EU market data. Use GBP for all salary figures. Consider London rates as baseline with regional adjustments."""

            result = await llamaindex_service.complete_json(prompt)
            return result

        except Exception as e:
            logger.warning(f"LLM market analysis failed: {e}")
            return {}

    async def _execute(self, input_data: Any) -> Dict[str, Any]:
        """
        Execute market insights generation using web search and LLM.

        Args:
            input_data: Dict with session_id, job_id, job_title

        Returns:
            Dict conforming to MarketInsightsResult schema
        """
        if not isinstance(input_data, dict):
            raise ValueError("Input must be a dictionary")

        session_id = input_data.get("session_id", "")
        job_id = input_data.get("job_id")
        job_title = input_data.get("job_title", "")

        if not job_title or not job_title.strip():
            raise ValueError("Job title is required")

        await self.report_progress(10, "Searching for real-time market data")

        # Try to get real-time data from web search
        web_results = await self._search_web_for_insights(job_title)

        await self.report_progress(40, "Analyzing market data with LLM")

        # Use LLM to analyze (with or without web results)
        analysis = await self._analyze_market_with_llm(job_title, web_results)

        await self.report_progress(70, "Building market insights")

        # Build salary range from LLM analysis (UK/EU market - GBP)
        salary_range = SalaryRange(
            min=analysis.get("salary_min", 35000),
            max=analysis.get("salary_max", 85000),
            median=analysis.get("salary_median", 55000),
            currency="GBP",
            location_adjusted=False
        )

        # Determine demand trend
        demand_str = analysis.get("demand_trend", "stable").lower()
        if "increas" in demand_str:
            demand_trend = DemandTrend.INCREASING
        elif "decreas" in demand_str:
            demand_trend = DemandTrend.DECREASING
        else:
            demand_trend = DemandTrend.STABLE

        # Get top skills
        top_skills = analysis.get("top_skills", [])
        if not isinstance(top_skills, list) or not top_skills:
            top_skills = ["Communication", "Problem Solving", "Technical Skills"]

        # Build career paths from LLM analysis
        career_paths = []
        for path_data in analysis.get("career_paths", []):
            if isinstance(path_data, dict) and path_data.get("title"):
                career_paths.append(CareerPath(
                    title=path_data.get("title", ""),
                    typical_years_to_reach=path_data.get("typical_years_to_reach", 3),
                    required_skills=path_data.get("required_skills", []),
                    salary_increase_percent=path_data.get("salary_increase_percent", 30)
                ))

        # Get industry insights
        industry_insights = analysis.get(
            "industry_insights",
            f"The {job_title} role is in demand with opportunities for growth."
        )

        competitive_landscape = analysis.get(
            "competitive_landscape",
            f"The market for {job_title} positions is competitive."
        )

        # Set data freshness based on whether we used web scraping
        if web_results:
            data_freshness = "Based on real-time UK/EU market data (Jan 2026)"
        else:
            data_freshness = "Based on UK/EU market analysis"

        await self.report_progress(100, "Complete")

        # Build insights object
        insights = MarketInsights(
            salary_range=salary_range,
            demand_trend=demand_trend,
            top_skills_in_demand=top_skills[:10],
            career_paths=career_paths,
            industry_insights=industry_insights,
            competitive_landscape=competitive_landscape,
            data_freshness=data_freshness
        )

        return {
            "session_id": session_id,
            "job_id": job_id,
            "insights": insights.model_dump(mode='json')
        }

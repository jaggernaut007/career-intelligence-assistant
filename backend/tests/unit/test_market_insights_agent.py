"""
Unit tests for Market Insights Agent.

TDD: These tests are written BEFORE implementation.
Tests should FAIL until market_insights.py is implemented.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestMarketInsightsAgent:
    """Test suite for Market Insights Agent."""

    # ========================================================================
    # Agent Interface Compliance Tests
    # ========================================================================

    def test_agent_has_required_name_property(self):
        """Agent must have 'name' property per spec."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()

        assert hasattr(agent, "name")
        assert agent.name == "market_insights"

    def test_agent_has_process_method(self):
        """Agent must have async process method per spec."""
        from app.agents.market_insights import MarketInsightsAgent
        import asyncio

        agent = MarketInsightsAgent()

        assert hasattr(agent, "process")
        assert asyncio.iscoroutinefunction(agent.process)

    # ========================================================================
    # Output Schema Compliance Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_output_conforms_to_market_insights_result_schema(self, sample_session_id):
        """Output must match MarketInsightsResult specification."""
        from app.agents.market_insights import MarketInsightsAgent
        from app.models import MarketInsightsResult

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Senior Software Engineer"
        })

        if result.success:
            insights_result = MarketInsightsResult.model_validate(result.data)
            assert insights_result is not None

    @pytest.mark.asyncio
    async def test_output_includes_insights_object(self, sample_session_id):
        """Output must include insights object."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Software Engineer"
        })

        assert "insights" in result.data

    # ========================================================================
    # Salary Range Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_returns_salary_range(self, sample_session_id):
        """Should return salary range information."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Software Engineer"
        })

        insights = result.data.get("insights", {})
        assert "salary_range" in insights

    @pytest.mark.asyncio
    async def test_salary_range_has_required_fields(self, sample_session_id):
        """Salary range must have min, max, median, currency."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Software Engineer"
        })

        salary = result.data.get("insights", {}).get("salary_range", {})
        assert "min" in salary
        assert "max" in salary
        assert "median" in salary
        assert "currency" in salary

    @pytest.mark.asyncio
    async def test_salary_values_are_integers(self, sample_session_id):
        """Salary values should be integers."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Software Engineer"
        })

        salary = result.data.get("insights", {}).get("salary_range", {})
        if salary:
            assert isinstance(salary.get("min"), int)
            assert isinstance(salary.get("max"), int)
            assert isinstance(salary.get("median"), int)

    @pytest.mark.asyncio
    async def test_salary_min_less_than_max(self, sample_session_id):
        """Salary min should be less than or equal to max."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Software Engineer"
        })

        salary = result.data.get("insights", {}).get("salary_range", {})
        if salary:
            assert salary["min"] <= salary["max"]
            assert salary["min"] <= salary["median"] <= salary["max"]

    # ========================================================================
    # Demand Trend Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_returns_demand_trend(self, sample_session_id):
        """Should return job market demand trend."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Software Engineer"
        })

        insights = result.data.get("insights", {})
        assert "demand_trend" in insights

    @pytest.mark.asyncio
    async def test_demand_trend_is_valid_enum(self, sample_session_id):
        """Demand trend must be increasing/stable/decreasing."""
        from app.agents.market_insights import MarketInsightsAgent
        from app.models import DemandTrend

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Software Engineer"
        })

        trend = result.data.get("insights", {}).get("demand_trend")
        valid_trends = [t.value for t in DemandTrend]
        assert trend in valid_trends

    # ========================================================================
    # Top Skills Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_returns_top_skills_in_demand(self, sample_session_id):
        """Should return list of top skills in demand."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Software Engineer"
        })

        insights = result.data.get("insights", {})
        assert "top_skills_in_demand" in insights
        assert isinstance(insights["top_skills_in_demand"], list)

    @pytest.mark.asyncio
    async def test_top_skills_are_strings(self, sample_session_id):
        """Top skills should be a list of strings."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Software Engineer"
        })

        skills = result.data.get("insights", {}).get("top_skills_in_demand", [])
        assert all(isinstance(s, str) for s in skills)

    # ========================================================================
    # Career Paths Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_returns_career_paths(self, sample_session_id):
        """Should return potential career progression paths."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Software Engineer"
        })

        insights = result.data.get("insights", {})
        assert "career_paths" in insights
        assert isinstance(insights["career_paths"], list)

    @pytest.mark.asyncio
    async def test_career_paths_have_required_fields(self, sample_session_id):
        """Career paths must have title and typical_years_to_reach."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Software Engineer"
        })

        paths = result.data.get("insights", {}).get("career_paths", [])
        for path in paths:
            assert "title" in path
            assert "typical_years_to_reach" in path

    # ========================================================================
    # Industry Insights Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_returns_industry_insights(self, sample_session_id):
        """Should return industry insights text."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Software Engineer"
        })

        insights = result.data.get("insights", {})
        assert "industry_insights" in insights
        assert isinstance(insights["industry_insights"], str)
        assert len(insights["industry_insights"]) > 0

    # ========================================================================
    # Data Freshness Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_returns_data_freshness(self, sample_session_id):
        """Should indicate data freshness."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "job_id": "job-456",
            "job_title": "Software Engineer"
        })

        insights = result.data.get("insights", {})
        assert "data_freshness" in insights

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_handles_unknown_job_title(self):
        """Should handle unknown/unusual job titles gracefully."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": "test-session",
            "job_id": "job-999",
            "job_title": "Chief Unicorn Wrangler"
        })

        # Should still return some insights or gracefully handle
        assert result is not None

    @pytest.mark.asyncio
    async def test_handles_empty_job_title(self):
        """Should return error for empty job title."""
        from app.agents.market_insights import MarketInsightsAgent

        agent = MarketInsightsAgent()
        result = await agent.process({
            "session_id": "test-session",
            "job_id": "job-456",
            "job_title": ""
        })

        assert result.success is False or result.data.get("insights") is None

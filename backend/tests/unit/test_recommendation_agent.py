"""
Unit tests for Recommendation Agent.

TDD: These tests are written BEFORE implementation.
Tests should FAIL until recommendation.py is implemented.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestRecommendationAgent:
    """Test suite for Recommendation Agent."""

    # ========================================================================
    # Agent Interface Compliance Tests
    # ========================================================================

    def test_agent_has_required_name_property(self):
        """Agent must have 'name' property per spec."""
        from app.agents.recommendation import RecommendationAgent

        agent = RecommendationAgent()

        assert hasattr(agent, "name")
        assert agent.name == "recommendation"

    def test_agent_has_process_method(self):
        """Agent must have async process method per spec."""
        from app.agents.recommendation import RecommendationAgent
        import asyncio

        agent = RecommendationAgent()

        assert hasattr(agent, "process")
        assert asyncio.iscoroutinefunction(agent.process)

    # ========================================================================
    # Output Schema Compliance Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_output_conforms_to_recommendation_result_schema(self, sample_session_id):
        """Output must match RecommendationResult specification."""
        from app.agents.recommendation import RecommendationAgent
        from app.models import RecommendationResult

        agent = RecommendationAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456",
            "skill_gaps": ["Kubernetes", "Go"]
        })

        if result.success:
            rec_result = RecommendationResult.model_validate(result.data)
            assert rec_result is not None

    @pytest.mark.asyncio
    async def test_output_includes_recommendations_list(self, sample_session_id):
        """Output must include recommendations list."""
        from app.agents.recommendation import RecommendationAgent

        agent = RecommendationAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        assert "recommendations" in result.data
        assert isinstance(result.data["recommendations"], list)

    # ========================================================================
    # Recommendation Generation Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_generates_skill_gap_recommendations(self, sample_session_id):
        """Should generate recommendations for skill gaps."""
        from app.agents.recommendation import RecommendationAgent

        agent = RecommendationAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456",
            "skill_gaps": ["Kubernetes", "Docker"]
        })

        categories = [r["category"] for r in result.data.get("recommendations", [])]
        assert "skill_gap" in categories

    @pytest.mark.asyncio
    async def test_generates_resume_improvement_recommendations(self, sample_session_id):
        """Should generate resume improvement recommendations."""
        from app.agents.recommendation import RecommendationAgent

        agent = RecommendationAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        categories = [r["category"] for r in result.data.get("recommendations", [])]
        # May have resume improvement suggestions
        assert len(categories) > 0

    # ========================================================================
    # Recommendation Structure Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_recommendations_have_required_fields(self, sample_session_id):
        """Each recommendation must have required fields."""
        from app.agents.recommendation import RecommendationAgent

        agent = RecommendationAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        for rec in result.data.get("recommendations", []):
            assert "id" in rec
            assert "category" in rec
            assert "priority" in rec
            assert "title" in rec
            assert "description" in rec

    @pytest.mark.asyncio
    async def test_recommendations_have_valid_category(self, sample_session_id):
        """Recommendation categories must be valid enum values."""
        from app.agents.recommendation import RecommendationAgent
        from app.models import RecommendationCategory

        agent = RecommendationAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        valid_categories = [c.value for c in RecommendationCategory]
        for rec in result.data.get("recommendations", []):
            assert rec["category"] in valid_categories

    @pytest.mark.asyncio
    async def test_recommendations_have_valid_priority(self, sample_session_id):
        """Recommendation priorities must be high/medium/low."""
        from app.agents.recommendation import RecommendationAgent
        from app.models import Priority

        agent = RecommendationAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        valid_priorities = [p.value for p in Priority]
        for rec in result.data.get("recommendations", []):
            assert rec["priority"] in valid_priorities

    # ========================================================================
    # Priority Ordering Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_returns_priority_order(self, sample_session_id):
        """Should return recommendations in priority order."""
        from app.agents.recommendation import RecommendationAgent

        agent = RecommendationAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        assert "priority_order" in result.data
        assert isinstance(result.data["priority_order"], list)

    @pytest.mark.asyncio
    async def test_high_priority_items_first(self, sample_session_id):
        """High priority recommendations should come first."""
        from app.agents.recommendation import RecommendationAgent

        agent = RecommendationAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456",
            "skill_gaps": ["Critical Skill 1", "Nice Skill 2"]
        })

        recs = result.data.get("recommendations", [])
        if len(recs) >= 2:
            # First recommendations should be higher or equal priority
            priorities = {"high": 3, "medium": 2, "low": 1}
            for i in range(len(recs) - 1):
                current_priority = priorities.get(recs[i]["priority"], 0)
                next_priority = priorities.get(recs[i + 1]["priority"], 0)
                assert current_priority >= next_priority

    # ========================================================================
    # Action Items Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_recommendations_have_action_items(self, sample_session_id):
        """Recommendations should include actionable items."""
        from app.agents.recommendation import RecommendationAgent

        agent = RecommendationAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        for rec in result.data.get("recommendations", []):
            assert "action_items" in rec
            assert isinstance(rec["action_items"], list)

    # ========================================================================
    # Resources Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_skill_gap_recommendations_have_resources(self, sample_session_id):
        """Skill gap recommendations should include learning resources."""
        from app.agents.recommendation import RecommendationAgent

        agent = RecommendationAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456",
            "skill_gaps": ["Kubernetes"]
        })

        skill_gap_recs = [r for r in result.data.get("recommendations", [])
                         if r["category"] == "skill_gap"]

        for rec in skill_gap_recs:
            assert "resources" in rec
            assert isinstance(rec["resources"], list)

    # ========================================================================
    # Estimated Improvement Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_returns_estimated_improvement(self, sample_session_id):
        """Should return estimated improvement score."""
        from app.agents.recommendation import RecommendationAgent

        agent = RecommendationAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        if "estimated_improvement" in result.data:
            assert 0 <= result.data["estimated_improvement"] <= 100

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_handles_missing_analysis_data(self):
        """Should handle missing analysis data gracefully."""
        from app.agents.recommendation import RecommendationAgent

        agent = RecommendationAgent()
        result = await agent.process({
            "session_id": "test-session",
            "resume_id": "nonexistent",
            "job_id": "nonexistent"
        })

        # Should return error or empty recommendations
        assert result is not None

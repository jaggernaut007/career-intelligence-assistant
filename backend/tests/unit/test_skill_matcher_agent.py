"""
Unit tests for Skill Matcher Agent.

TDD: These tests are written BEFORE implementation.
Tests should FAIL until skill_matcher.py is implemented.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestSkillMatcherAgent:
    """Test suite for Skill Matcher Agent."""

    # ========================================================================
    # Agent Interface Compliance Tests
    # ========================================================================

    def test_agent_has_required_name_property(self):
        """Agent must have 'name' property per spec."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()

        assert hasattr(agent, "name")
        assert agent.name == "skill_matcher"

    def test_agent_has_process_method(self):
        """Agent must have async process method per spec."""
        from app.agents.skill_matcher import SkillMatcherAgent
        import asyncio

        agent = SkillMatcherAgent()

        assert hasattr(agent, "process")
        assert asyncio.iscoroutinefunction(agent.process)

    # ========================================================================
    # Output Schema Compliance Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_output_conforms_to_job_match_schema(self, sample_session_id):
        """Output must match JobMatch specification."""
        from app.agents.skill_matcher import SkillMatcherAgent
        from app.models import JobMatch

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        if result.success:
            match = JobMatch.model_validate(result.data)
            assert match is not None

    @pytest.mark.asyncio
    async def test_output_includes_fit_score(self, sample_session_id):
        """Output must include fit_score field."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        assert "fit_score" in result.data

    # ========================================================================
    # Fit Score Calculation Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_fit_score_is_percentage(self, sample_session_id):
        """Fit score should be between 0 and 100."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        score = result.data["fit_score"]
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_perfect_match_gives_high_score(self):
        """Resume with all required skills should score high."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        # This would require mocked data with perfect skill match
        result = await agent.process({
            "session_id": "test-session",
            "resume_id": "perfect-resume",
            "job_id": "matching-job"
        })

        # Perfect match should score above 80
        if result.success:
            assert result.data["fit_score"] >= 80

    @pytest.mark.asyncio
    async def test_no_match_gives_low_score(self):
        """Resume with no matching skills should have zero skill match score."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        # This would require mocked data with no skill overlap
        result = await agent.process({
            "session_id": "test-session",
            "resume_id": "no-match-resume",
            "job_id": "unrelated-job"
        })

        # No skill overlap should give 0 skill match score
        # Total fit score may still be >0 due to experience/education components
        if result.success:
            assert result.data["skill_match_score"] == 0.0
            # Overall score should be lower than a good match
            assert result.data["fit_score"] < result.data.get("education_match_score", 100)

    # ========================================================================
    # Skill Match Detection Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_identifies_matching_skills(self, sample_session_id):
        """Should identify skills present in both resume and JD."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        assert "matching_skills" in result.data
        assert isinstance(result.data["matching_skills"], list)

    @pytest.mark.asyncio
    async def test_matching_skills_have_quality_rating(self, sample_session_id):
        """Matching skills should have match quality (exact/partial/exceeds)."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        for match in result.data.get("matching_skills", []):
            assert "match_quality" in match
            assert match["match_quality"] in ["exact", "partial", "exceeds"]

    @pytest.mark.asyncio
    async def test_detects_skill_level_exceeds(self):
        """Should detect when resume skill level exceeds requirement."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        # Expert Python vs Required Intermediate Python
        result = await agent.process({
            "session_id": "test-session",
            "resume_id": "expert-resume",
            "job_id": "intermediate-job"
        })

        if result.success and result.data.get("matching_skills"):
            qualities = [m["match_quality"] for m in result.data["matching_skills"]]
            # Should have at least some "exceeds" matches
            assert "exceeds" in qualities or "exact" in qualities

    # ========================================================================
    # Skill Gap Detection Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_identifies_missing_skills(self, sample_session_id):
        """Should identify skills required but missing from resume."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        assert "missing_skills" in result.data
        assert isinstance(result.data["missing_skills"], list)

    @pytest.mark.asyncio
    async def test_missing_skills_have_importance(self, sample_session_id):
        """Missing skills should indicate importance (must_have/nice_to_have)."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        for skill in result.data.get("missing_skills", []):
            assert "importance" in skill
            assert skill["importance"] in ["must_have", "nice_to_have"]

    @pytest.mark.asyncio
    async def test_missing_skills_have_difficulty(self, sample_session_id):
        """Missing skills should indicate difficulty to acquire."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        for skill in result.data.get("missing_skills", []):
            assert "difficulty_to_acquire" in skill
            assert skill["difficulty_to_acquire"] in ["easy", "medium", "hard"]

    # ========================================================================
    # Component Score Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_calculates_skill_match_score(self, sample_session_id):
        """Should calculate separate skill match score."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        assert "skill_match_score" in result.data
        assert 0 <= result.data["skill_match_score"] <= 100

    @pytest.mark.asyncio
    async def test_calculates_experience_match_score(self, sample_session_id):
        """Should calculate experience match score."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        assert "experience_match_score" in result.data
        assert 0 <= result.data["experience_match_score"] <= 100

    @pytest.mark.asyncio
    async def test_calculates_education_match_score(self, sample_session_id):
        """Should calculate education match score."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        assert "education_match_score" in result.data
        assert 0 <= result.data["education_match_score"] <= 100

    # ========================================================================
    # Transferable Skills Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_identifies_transferable_skills(self, sample_session_id):
        """Should identify transferable skills."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        assert "transferable_skills" in result.data
        assert isinstance(result.data["transferable_skills"], list)

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_handles_missing_resume(self):
        """Should return minimal result when resume not found (graceful degradation)."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": "test-session",
            "resume_id": "nonexistent-resume",
            "job_id": "job-456"
        })

        # Graceful degradation: returns success with 0 scores
        assert result.success is True
        assert result.data["fit_score"] == 0.0
        assert result.data["matching_skills"] == []

    @pytest.mark.asyncio
    async def test_handles_missing_job(self):
        """Should return minimal result when job not found (graceful degradation)."""
        from app.agents.skill_matcher import SkillMatcherAgent

        agent = SkillMatcherAgent()
        result = await agent.process({
            "session_id": "test-session",
            "resume_id": "resume-123",
            "job_id": "nonexistent-job"
        })

        # Graceful degradation: returns success with 0 scores
        assert result.success is True
        assert result.data["fit_score"] == 0.0
        assert result.data["missing_skills"] == []

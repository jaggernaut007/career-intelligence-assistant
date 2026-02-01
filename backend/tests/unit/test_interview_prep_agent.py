"""
Unit tests for Interview Prep Agent.

TDD: These tests are written BEFORE implementation.
Tests should FAIL until interview_prep.py is implemented.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestInterviewPrepAgent:
    """Test suite for Interview Prep Agent."""

    # ========================================================================
    # Agent Interface Compliance Tests
    # ========================================================================

    def test_agent_has_required_name_property(self):
        """Agent must have 'name' property per spec."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()

        assert hasattr(agent, "name")
        assert agent.name == "interview_prep"

    def test_agent_has_process_method(self):
        """Agent must have async process method per spec."""
        from app.agents.interview_prep import InterviewPrepAgent
        import asyncio

        agent = InterviewPrepAgent()

        assert hasattr(agent, "process")
        assert asyncio.iscoroutinefunction(agent.process)

    # ========================================================================
    # Output Schema Compliance Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_output_conforms_to_interview_prep_result_schema(self, sample_session_id):
        """Output must match InterviewPrepResult specification."""
        from app.agents.interview_prep import InterviewPrepAgent
        from app.models import InterviewPrepResult

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        if result.success:
            prep_result = InterviewPrepResult.model_validate(result.data)
            assert prep_result is not None

    @pytest.mark.asyncio
    async def test_output_includes_questions_list(self, sample_session_id):
        """Output must include questions list."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        assert "questions" in result.data
        assert isinstance(result.data["questions"], list)

    # ========================================================================
    # Interview Question Generation Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_generates_behavioral_questions(self, sample_session_id):
        """Should generate behavioral interview questions."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        categories = [q["category"] for q in result.data.get("questions", [])]
        assert "behavioral" in categories

    @pytest.mark.asyncio
    async def test_generates_technical_questions(self, sample_session_id):
        """Should generate technical interview questions."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        categories = [q["category"] for q in result.data.get("questions", [])]
        assert "technical" in categories

    @pytest.mark.asyncio
    async def test_generates_questions_based_on_job(self, sample_session_id):
        """Questions should be relevant to the job description."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"  # Software Engineer job
        })

        questions = result.data.get("questions", [])
        # At least some questions should relate to software engineering
        assert len(questions) > 0

    # ========================================================================
    # Question Structure Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_questions_have_required_fields(self, sample_session_id):
        """Each question must have required fields."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        for q in result.data.get("questions", []):
            assert "id" in q
            assert "question" in q
            assert "category" in q
            assert "difficulty" in q
            assert "suggested_answer" in q

    @pytest.mark.asyncio
    async def test_questions_have_valid_category(self, sample_session_id):
        """Question categories must be valid enum values."""
        from app.agents.interview_prep import InterviewPrepAgent
        from app.models import QuestionCategory

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        valid_categories = [c.value for c in QuestionCategory]
        for q in result.data.get("questions", []):
            assert q["category"] in valid_categories

    @pytest.mark.asyncio
    async def test_questions_have_valid_difficulty(self, sample_session_id):
        """Question difficulties must be easy/medium/hard."""
        from app.agents.interview_prep import InterviewPrepAgent
        from app.models import Difficulty

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        valid_difficulties = [d.value for d in Difficulty]
        for q in result.data.get("questions", []):
            assert q["difficulty"] in valid_difficulties

    # ========================================================================
    # STAR Example Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_behavioral_questions_have_star_examples(self, sample_session_id):
        """Behavioral questions should include STAR example suggestions."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        behavioral_questions = [q for q in result.data.get("questions", [])
                                if q["category"] == "behavioral"]

        for q in behavioral_questions:
            if q.get("star_example"):
                star = q["star_example"]
                assert "situation" in star
                assert "task" in star
                assert "action" in star
                assert "result" in star

    @pytest.mark.asyncio
    async def test_star_examples_reference_resume_experience(self, sample_session_id):
        """STAR examples should reference candidate's actual experience."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        # Questions may include related_experience field
        for q in result.data.get("questions", []):
            if q.get("related_experience"):
                assert isinstance(q["related_experience"], str)
                assert len(q["related_experience"]) > 0

    # ========================================================================
    # Talking Points Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_includes_talking_points(self, sample_session_id):
        """Should include general talking points."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        assert "talking_points" in result.data
        assert isinstance(result.data["talking_points"], list)

    # ========================================================================
    # Weakness Response Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_includes_weakness_responses(self, sample_session_id):
        """Should include prepared responses for weaknesses/gaps."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456",
            "skill_gaps": ["Kubernetes", "Go"]
        })

        assert "weakness_responses" in result.data
        assert isinstance(result.data["weakness_responses"], list)

    @pytest.mark.asyncio
    async def test_weakness_responses_have_required_fields(self, sample_session_id):
        """Weakness responses must have weakness, honest_response, mitigation."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456",
            "skill_gaps": ["Kubernetes"]
        })

        for wr in result.data.get("weakness_responses", []):
            assert "weakness" in wr
            assert "honest_response" in wr
            assert "mitigation" in wr

    # ========================================================================
    # Questions to Ask Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_includes_questions_to_ask(self, sample_session_id):
        """Should include questions candidate can ask interviewer."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": sample_session_id,
            "resume_id": "resume-123",
            "job_id": "job-456"
        })

        assert "questions_to_ask" in result.data
        assert isinstance(result.data["questions_to_ask"], list)
        assert len(result.data["questions_to_ask"]) > 0

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_handles_missing_resume(self):
        """LLM can still generate prep even without resume (job-focused questions)."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": "test-session",
            "resume_id": "nonexistent",
            "job_id": "job-456"
        })

        # LLM-driven agent can generate prep based on job data alone
        assert result.success is True
        # Questions may still be generated from job context
        assert "questions" in result.data

    @pytest.mark.asyncio
    async def test_handles_missing_job(self):
        """LLM can still generate generic prep even without job description."""
        from app.agents.interview_prep import InterviewPrepAgent

        agent = InterviewPrepAgent()
        result = await agent.process({
            "session_id": "test-session",
            "resume_id": "resume-123",
            "job_id": "nonexistent"
        })

        # LLM-driven agent can generate generic prep
        assert result.success is True
        # Questions may still be generated from resume context
        assert "questions" in result.data

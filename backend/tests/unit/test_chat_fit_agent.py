"""
Unit tests for Chat Fit Agent.

Tests the ChatFitAgent that handles conversational questions about resume-job fit.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestChatFitAgent:
    """Test suite for Chat Fit Agent."""

    # ========================================================================
    # Agent Interface Compliance Tests
    # ========================================================================

    def test_agent_has_required_name_property(self):
        """Agent must have 'name' property per spec."""
        from app.agents.chat_fit import ChatFitAgent

        agent = ChatFitAgent()

        assert hasattr(agent, "name")
        assert agent.name == "chat_fit"

    def test_agent_has_process_method(self):
        """Agent must have async process method per spec."""
        from app.agents.chat_fit import ChatFitAgent
        import asyncio

        agent = ChatFitAgent()

        assert hasattr(agent, "process")
        assert asyncio.iscoroutinefunction(agent.process)

    def test_agent_has_description_property(self):
        """Agent must have description property."""
        from app.agents.chat_fit import ChatFitAgent

        agent = ChatFitAgent()

        assert hasattr(agent, "description")
        assert "resume-job fit" in agent.description.lower()

    def test_agent_has_input_schema(self):
        """Agent must have input schema property."""
        from app.agents.chat_fit import ChatFitAgent, ChatFitInput

        agent = ChatFitAgent()

        assert hasattr(agent, "input_schema")
        assert agent.input_schema == ChatFitInput

    def test_agent_has_output_schema(self):
        """Agent must have output schema property."""
        from app.agents.chat_fit import ChatFitAgent, ChatFitOutput

        agent = ChatFitAgent()

        assert hasattr(agent, "output_schema")
        assert agent.output_schema == ChatFitOutput

    # ========================================================================
    # Input Schema Tests
    # ========================================================================

    def test_input_schema_requires_session_id(self):
        """Input schema must require session_id."""
        from app.agents.chat_fit import ChatFitInput
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ChatFitInput(message="test")

    def test_input_schema_requires_message(self):
        """Input schema must require message."""
        from app.agents.chat_fit import ChatFitInput
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ChatFitInput(session_id="test-session")

    def test_input_schema_accepts_optional_job_id(self):
        """Input schema should accept optional job_id."""
        from app.agents.chat_fit import ChatFitInput

        input_with_job = ChatFitInput(
            session_id="test-session",
            message="What skills am I missing?",
            job_id="job-123"
        )
        assert input_with_job.job_id == "job-123"

        input_without_job = ChatFitInput(
            session_id="test-session",
            message="What skills am I missing?"
        )
        assert input_without_job.job_id is None

    # ========================================================================
    # Output Schema Tests
    # ========================================================================

    def test_output_schema_has_response_field(self):
        """Output schema must have response field."""
        from app.agents.chat_fit import ChatFitOutput

        output = ChatFitOutput(
            response="You have strong Python skills",
            suggested_questions=[]
        )
        assert output.response == "You have strong Python skills"

    def test_output_schema_has_suggested_questions_field(self):
        """Output schema must have suggested_questions field."""
        from app.agents.chat_fit import ChatFitOutput

        output = ChatFitOutput(
            response="Test response",
            suggested_questions=["Question 1?", "Question 2?"]
        )
        assert len(output.suggested_questions) == 2

    def test_output_schema_defaults_empty_suggestions(self):
        """Output schema should default to empty suggestions."""
        from app.agents.chat_fit import ChatFitOutput

        output = ChatFitOutput(response="Test")
        assert output.suggested_questions == []

    # ========================================================================
    # Context Building Tests
    # ========================================================================

    def test_build_context_includes_resume_data(self):
        """Context should include resume summary and skills."""
        from app.agents.chat_fit import ChatFitAgent

        agent = ChatFitAgent()
        resume_data = {
            "summary": "Experienced Python developer",
            "skills": [
                {"name": "Python", "level": "expert"},
                {"name": "JavaScript", "level": "intermediate"}
            ],
            "experiences": [],
            "education": []
        }
        job_data = {
            "title": "Software Engineer",
            "company": "TechCorp",
            "required_skills": [],
            "nice_to_have_skills": []
        }

        context = agent._build_context(resume_data, job_data)

        assert "Experienced Python developer" in context
        assert "Python" in context
        assert "JavaScript" in context

    def test_build_context_includes_job_data(self):
        """Context should include job title and requirements."""
        from app.agents.chat_fit import ChatFitAgent

        agent = ChatFitAgent()
        resume_data = {
            "summary": "Test summary",
            "skills": [],
            "experiences": [],
            "education": []
        }
        job_data = {
            "title": "Senior Developer",
            "company": "MegaCorp",
            "required_skills": [
                {"name": "Python"},
                {"name": "AWS"}
            ],
            "nice_to_have_skills": []
        }

        context = agent._build_context(resume_data, job_data)

        assert "Senior Developer" in context
        assert "MegaCorp" in context
        assert "Python" in context
        assert "AWS" in context

    def test_build_context_includes_match_data(self):
        """Context should include match analysis when provided."""
        from app.agents.chat_fit import ChatFitAgent

        agent = ChatFitAgent()
        resume_data = {
            "summary": "Test",
            "skills": [],
            "experiences": [],
            "education": []
        }
        job_data = {
            "title": "Developer",
            "required_skills": [],
            "nice_to_have_skills": []
        }
        match_data = {
            "fit_score": 75,
            "skill_match_score": 80,
            "experience_match_score": 70,
            "education_match_score": 75,
            "matching_skills": [{"skill_name": "Python"}],
            "missing_skills": [{"skill_name": "Kubernetes", "importance": "must_have", "difficulty_to_acquire": "medium"}],
            "transferable_skills": ["Docker"]
        }

        context = agent._build_context(resume_data, job_data, match_data)

        assert "75%" in context  # fit_score
        assert "80%" in context  # skill_match_score
        assert "Python" in context  # matching skill
        assert "Kubernetes" in context  # missing skill
        assert "Docker" in context  # transferable skill

    def test_build_context_handles_camelcase_fields(self):
        """Context builder should handle both snake_case and camelCase."""
        from app.agents.chat_fit import ChatFitAgent

        agent = ChatFitAgent()
        resume_data = {
            "summary": "Test",
            "skills": [],
            "experiences": [],
            "education": []
        }
        job_data = {
            "title": "Developer",
            "required_skills": [],
            "nice_to_have_skills": []
        }
        # Using camelCase (as might come from frontend)
        match_data = {
            "fitScore": 85,
            "skillMatchScore": 90,
            "experienceMatchScore": 80,
            "educationMatchScore": 75,
            "matchingSkills": [{"skillName": "Python"}],
            "missingSkills": [{"skillName": "Go", "importance": "nice_to_have", "difficultyToAcquire": "easy"}],
            "transferableSkills": ["Node.js"]
        }

        context = agent._build_context(resume_data, job_data, match_data)

        assert "85%" in context  # fitScore
        assert "90%" in context  # skillMatchScore
        assert "Python" in context
        assert "Go" in context

    # ========================================================================
    # Suggested Questions Tests
    # ========================================================================

    def test_suggested_questions_with_gaps(self):
        """Should suggest gap-related questions when gaps exist."""
        from app.agents.chat_fit import ChatFitAgent

        agent = ChatFitAgent()
        questions = agent._get_suggested_questions("Software Engineer", has_gaps=True)

        assert len(questions) <= 4
        # Should include gap-related questions
        gap_keywords = ["gap", "missing", "learn", "prioritize"]
        has_gap_question = any(
            any(kw in q.lower() for kw in gap_keywords)
            for q in questions
        )
        assert has_gap_question

    def test_suggested_questions_without_gaps(self):
        """Should suggest strength-related questions when no gaps."""
        from app.agents.chat_fit import ChatFitAgent

        agent = ChatFitAgent()
        questions = agent._get_suggested_questions("Software Engineer", has_gaps=False)

        assert len(questions) <= 4
        # Should include strength-related questions
        strength_keywords = ["stand out", "strengths", "highlight"]
        has_strength_question = any(
            any(kw in q.lower() for kw in strength_keywords)
            for q in questions
        )
        assert has_strength_question

    def test_suggested_questions_includes_job_title(self):
        """Suggested questions should reference the job title."""
        from app.agents.chat_fit import ChatFitAgent

        agent = ChatFitAgent()
        questions = agent._get_suggested_questions("Data Scientist", has_gaps=True)

        # At least one question should mention the role
        has_role_reference = any("Data Scientist" in q for q in questions)
        assert has_role_reference

    # ========================================================================
    # Execution Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_execute_returns_response_and_suggestions(self, mock_llamaindex_service):
        """Execute should return response and suggested questions."""
        from app.agents.chat_fit import ChatFitAgent, ChatFitInput
        from app.models.session import SessionData, get_session_manager

        # Setup mock session
        session_manager = get_session_manager()
        session_id = "test-chat-session"
        session = SessionData(session_id=session_id)
        session.parsed_resume = {
            "summary": "Python developer",
            "skills": [{"name": "Python", "level": "expert"}],
            "experiences": [],
            "education": []
        }
        session.job_descriptions = {
            "job-1": {
                "title": "Software Engineer",
                "company": "TechCorp",
                "required_skills": [{"name": "Python"}],
                "nice_to_have_skills": []
            }
        }
        session.job_matches = [
            {
                "job_id": "job-1",
                "fit_score": 85,
                "matching_skills": [{"skill_name": "Python"}],
                "missing_skills": []
            }
        ]
        session_manager._sessions[session_id] = session

        # Mock LLM response
        mock_llamaindex_service.complete = AsyncMock(return_value="Based on your profile, you're a strong match!")

        agent = ChatFitAgent()
        input_data = ChatFitInput(
            session_id=session_id,
            message="Am I a good fit for this role?"
        )

        with patch("app.agents.chat_fit.get_llamaindex_service", AsyncMock(return_value=mock_llamaindex_service)):
            result = await agent._execute(input_data)

        assert "response" in result
        assert "suggested_questions" in result
        assert isinstance(result["suggested_questions"], list)

        # Cleanup
        del session_manager._sessions[session_id]

    @pytest.mark.asyncio
    async def test_execute_raises_for_missing_session(self):
        """Execute should raise error for invalid session."""
        from app.agents.chat_fit import ChatFitAgent, ChatFitInput

        agent = ChatFitAgent()
        input_data = ChatFitInput(
            session_id="nonexistent-session",
            message="Test message"
        )

        with pytest.raises(ValueError, match="Session not found"):
            await agent._execute(input_data)

    @pytest.mark.asyncio
    async def test_execute_raises_for_missing_resume(self):
        """Execute should raise error if no resume uploaded."""
        from app.agents.chat_fit import ChatFitAgent, ChatFitInput
        from app.models.session import SessionData, get_session_manager

        session_manager = get_session_manager()
        session_id = "no-resume-session"
        session = SessionData(session_id=session_id)
        session.parsed_resume = None  # No resume
        session_manager._sessions[session_id] = session

        agent = ChatFitAgent()
        input_data = ChatFitInput(
            session_id=session_id,
            message="Test message"
        )

        with pytest.raises(ValueError, match="No resume found"):
            await agent._execute(input_data)

        # Cleanup
        del session_manager._sessions[session_id]

    @pytest.mark.asyncio
    async def test_execute_raises_for_missing_jobs(self):
        """Execute should raise error if no job descriptions."""
        from app.agents.chat_fit import ChatFitAgent, ChatFitInput
        from app.models.session import SessionData, get_session_manager

        session_manager = get_session_manager()
        session_id = "no-jobs-session"
        session = SessionData(session_id=session_id)
        session.parsed_resume = {"summary": "Test", "skills": []}
        session.job_descriptions = {}  # No jobs
        session_manager._sessions[session_id] = session

        agent = ChatFitAgent()
        input_data = ChatFitInput(
            session_id=session_id,
            message="Test message"
        )

        with pytest.raises(ValueError, match="No job descriptions"):
            await agent._execute(input_data)

        # Cleanup
        del session_manager._sessions[session_id]

    @pytest.mark.asyncio
    async def test_execute_uses_specific_job_when_provided(self, mock_llamaindex_service):
        """Execute should focus on specific job when job_id provided."""
        from app.agents.chat_fit import ChatFitAgent, ChatFitInput
        from app.models.session import SessionData, get_session_manager

        session_manager = get_session_manager()
        session_id = "multi-job-session"
        session = SessionData(session_id=session_id)
        session.parsed_resume = {
            "summary": "Developer",
            "skills": [{"name": "Python"}],
            "experiences": [],
            "education": []
        }
        session.job_descriptions = {
            "job-1": {
                "title": "Frontend Developer",
                "company": "Company A",
                "required_skills": [],
                "nice_to_have_skills": []
            },
            "job-2": {
                "title": "Backend Developer",
                "company": "Company B",
                "required_skills": [],
                "nice_to_have_skills": []
            }
        }
        session_manager._sessions[session_id] = session

        mock_llamaindex_service.complete = AsyncMock(return_value="Test response")

        agent = ChatFitAgent()
        input_data = ChatFitInput(
            session_id=session_id,
            message="Tell me about the role",
            job_id="job-2"  # Specifically request job-2
        )

        with patch("app.agents.chat_fit.get_llamaindex_service", AsyncMock(return_value=mock_llamaindex_service)):
            # The agent should use job-2's data
            result = await agent._execute(input_data)

        # Verify the complete call was made
        mock_llamaindex_service.complete.assert_called_once()
        call_args = mock_llamaindex_service.complete.call_args
        prompt = call_args.kwargs.get("prompt", call_args[1].get("prompt", ""))

        # The prompt should contain the second job's details
        assert "Backend Developer" in prompt or "Company B" in prompt

        # Cleanup
        del session_manager._sessions[session_id]

    # ========================================================================
    # Health Check Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_health_check_returns_boolean(self):
        """Health check should return a boolean."""
        from app.agents.chat_fit import ChatFitAgent

        agent = ChatFitAgent()

        with patch("app.agents.chat_fit.get_neo4j_store") as mock_neo4j, \
             patch("app.agents.chat_fit.get_llamaindex_service", new_callable=AsyncMock) as mock_llama:
            mock_neo4j.return_value = MagicMock()
            mock_llama.return_value = MagicMock()

            result = await agent.health_check()

        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_health_check_returns_false_on_error(self):
        """Health check should return False when services unavailable."""
        from app.agents.chat_fit import ChatFitAgent

        agent = ChatFitAgent()

        with patch("app.agents.chat_fit.get_neo4j_store", side_effect=Exception("Connection failed")):
            result = await agent.health_check()

        assert result is False

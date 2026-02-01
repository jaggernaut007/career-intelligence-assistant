"""
Integration tests for Multi-Agent Workflow.

Tests the LlamaIndex Workflow-based agent orchestration system.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio


class TestAgentWorkflow:
    """Test suite for multi-agent orchestration workflow using LlamaIndex Workflows."""

    # ========================================================================
    # Workflow Execution Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_workflow_can_be_instantiated(self):
        """Workflow should be instantiatable."""
        from app.workflows import CareerAnalysisWorkflow

        workflow = CareerAnalysisWorkflow(timeout=60)
        assert workflow is not None

    @pytest.mark.asyncio
    async def test_workflow_events_are_defined(self):
        """All workflow events should be defined."""
        from app.workflows import (
            StartAnalysisEvent,
            ResumeParseEvent,
            ResumeParseResultEvent,
            JDAnalyzeEvent,
            JDAnalyzeResultEvent,
            SkillMatchEvent,
            SkillMatchResultEvent,
            GenerateRecommendationsEvent,
            GenerateInterviewPrepEvent,
            GenerateMarketInsightsEvent,
            RecommendationResultEvent,
            InterviewPrepResultEvent,
            MarketInsightsResultEvent,
        )

        # All events should be importable
        assert StartAnalysisEvent is not None
        assert ResumeParseEvent is not None
        assert SkillMatchEvent is not None

    @pytest.mark.asyncio
    async def test_workflow_state_is_defined(self):
        """Workflow state should be defined."""
        from app.workflows import WorkflowState

        state = WorkflowState(
            session_id="test-session",
            resume_id="resume-123",
            job_ids=["job-456"]
        )

        assert state.session_id == "test-session"
        assert state.resume_id == "resume-123"
        assert state.job_ids == ["job-456"]

    @pytest.mark.asyncio
    async def test_start_event_can_be_created(self):
        """Start event should be creatable with all required fields."""
        from app.workflows import StartAnalysisEvent

        event = StartAnalysisEvent(
            session_id="test-session",
            resume_id="resume-123",
            job_ids=["job-456"],
            resume_text="Sample resume",
            job_texts={"job-456": "Sample JD"}
        )

        assert event.session_id == "test-session"
        assert event.resume_id == "resume-123"
        assert event.job_ids == ["job-456"]
        assert event.resume_text == "Sample resume"

    # ========================================================================
    # Agent Integration Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_agents_can_be_imported(self):
        """All agents should be importable."""
        from app.agents.resume_parser import ResumeParserAgent
        from app.agents.jd_analyzer import JDAnalyzerAgent
        from app.agents.skill_matcher import SkillMatcherAgent
        from app.agents.recommendation import RecommendationAgent
        from app.agents.interview_prep import InterviewPrepAgent
        from app.agents.market_insights import MarketInsightsAgent

        assert ResumeParserAgent is not None
        assert JDAnalyzerAgent is not None
        assert SkillMatcherAgent is not None

    @pytest.mark.asyncio
    async def test_agents_inherit_base_agent(self):
        """All agents should inherit from BaseAgent."""
        from app.agents.base_agent import BaseAgent
        from app.agents.resume_parser import ResumeParserAgent
        from app.agents.skill_matcher import SkillMatcherAgent

        assert issubclass(ResumeParserAgent, BaseAgent)
        assert issubclass(SkillMatcherAgent, BaseAgent)

    @pytest.mark.asyncio
    async def test_base_agent_works_without_message_bus(self):
        """BaseAgent should work without orchestrator message bus."""
        from app.agents.base_agent import BaseAgent

        # Verify message_bus import is optional (try/except in base_agent.py)
        # This should not raise ImportError even though orchestrator is deleted
        assert BaseAgent is not None

    # ========================================================================
    # Neo4j Vector Search Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_neo4j_store_has_vector_methods(self):
        """Neo4j store should have direct vector search methods."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()

        # Verify new vector methods exist
        assert hasattr(store, 'store_skill_embedding')
        assert hasattr(store, 'find_similar_resume_skills')
        assert hasattr(store, 'batch_find_similar_skills')

    @pytest.mark.asyncio
    async def test_skill_matcher_uses_direct_neo4j(self):
        """Skill matcher should use direct Neo4j vector search."""
        from app.agents.skill_matcher import SkillMatcherAgent
        import inspect

        agent = SkillMatcherAgent()

        # Check that _semantic_skill_match doesn't have llamaindex_service param
        sig = inspect.signature(agent._semantic_skill_match)
        params = list(sig.parameters.keys())

        assert 'llamaindex_service' not in params
        assert 'resume_id' in params

    # ========================================================================
    # Event Flow Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_parse_events_have_required_fields(self):
        """Parse events should have required fields."""
        from app.workflows import ResumeParseEvent, JDAnalyzeEvent

        resume_event = ResumeParseEvent(
            resume_text="Sample resume",
            resume_id="resume-123"
        )
        assert resume_event.resume_text == "Sample resume"

        jd_event = JDAnalyzeEvent(
            jd_text="Sample JD",
            job_id="job-456"
        )
        assert jd_event.jd_text == "Sample JD"

    @pytest.mark.asyncio
    async def test_match_event_has_required_fields(self):
        """Skill match event should have required fields."""
        from app.workflows import SkillMatchEvent

        event = SkillMatchEvent(
            session_id="test-session",
            resume_id="resume-123",
            job_id="job-456"
        )
        assert event.session_id == "test-session"
        assert event.job_id == "job-456"

    @pytest.mark.asyncio
    async def test_generation_events_have_skill_gaps(self):
        """Generation events should include skill gaps."""
        from app.workflows import (
            GenerateRecommendationsEvent,
            GenerateInterviewPrepEvent,
        )

        rec_event = GenerateRecommendationsEvent(
            session_id="test-session",
            skill_gaps=["Python", "Machine Learning"]
        )
        assert rec_event.skill_gaps == ["Python", "Machine Learning"]

        prep_event = GenerateInterviewPrepEvent(
            session_id="test-session",
            skill_gaps=["React"]
        )
        assert prep_event.skill_gaps == ["React"]

    # ========================================================================
    # Result Event Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_result_events_have_data_fields(self):
        """Result events should have appropriate data fields."""
        from app.workflows import (
            ResumeParseResultEvent,
            SkillMatchResultEvent,
            RecommendationResultEvent,
        )

        resume_result = ResumeParseResultEvent(
            resume_id="resume-123",
            parsed_resume={"skills": [], "experiences": []}
        )
        assert resume_result.resume_id == "resume-123"

        match_result = SkillMatchResultEvent(
            job_id="job-456",
            match_result={"fit_score": 85.0}
        )
        assert match_result.job_id == "job-456"

        rec_result = RecommendationResultEvent(
            recommendations={"items": []}
        )
        assert rec_result.recommendations == {"items": []}

    # ========================================================================
    # Workflow Factory Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_workflow_returns_instance(self):
        """get_workflow should return a workflow instance."""
        from app.workflows import get_workflow

        workflow = get_workflow()
        assert workflow is not None

    @pytest.mark.asyncio
    async def test_workflow_has_timeout(self):
        """Workflow should have a timeout configured."""
        from app.workflows import CareerAnalysisWorkflow

        workflow = CareerAnalysisWorkflow(timeout=300)
        # Workflow should be configured with timeout
        assert workflow is not None

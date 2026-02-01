"""
Unit tests for Resume Parser Agent.

TDD: These tests are written BEFORE implementation.
Tests should FAIL until resume_parser.py is implemented.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestResumeParserAgent:
    """Test suite for Resume Parser Agent."""

    # ========================================================================
    # Agent Interface Compliance Tests
    # ========================================================================

    def test_agent_has_required_name_property(self):
        """Agent must have 'name' property per spec."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()

        assert hasattr(agent, "name")
        assert agent.name == "resume_parser"

    def test_agent_has_input_schema(self):
        """Agent must define input schema per spec."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()

        assert hasattr(agent, "input_schema")
        assert agent.input_schema is not None

    def test_agent_has_output_schema(self):
        """Agent must define output schema per spec."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()

        assert hasattr(agent, "output_schema")
        assert agent.output_schema is not None

    def test_agent_has_process_method(self):
        """Agent must have async process method per spec."""
        from app.agents.resume_parser import ResumeParserAgent
        import asyncio

        agent = ResumeParserAgent()

        assert hasattr(agent, "process")
        assert asyncio.iscoroutinefunction(agent.process)

    # ========================================================================
    # Output Schema Compliance Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_output_conforms_to_parsed_resume_schema(self, sample_resume_text):
        """Output must match ParsedResume specification."""
        from app.agents.resume_parser import ResumeParserAgent
        from app.models import ParsedResume

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_text)

        # Should be valid ParsedResume
        parsed = ParsedResume.model_validate(result.data)
        assert parsed is not None

    @pytest.mark.asyncio
    async def test_output_includes_required_fields(self, sample_resume_text):
        """Output must include all required fields."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_text)

        assert "id" in result.data
        assert "skills" in result.data
        assert "experiences" in result.data
        assert "education" in result.data
        assert "contact_redacted" in result.data

    # ========================================================================
    # Skill Extraction Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_extracts_skills_from_resume(self, sample_resume_text):
        """Should extract skills mentioned in resume."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_text)

        skills = result.data["skills"]
        assert len(skills) > 0

    @pytest.mark.asyncio
    async def test_skills_have_required_fields(self, sample_resume_text):
        """Each skill must have name, category, and level per spec."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_text)

        for skill in result.data["skills"]:
            assert "name" in skill
            assert "category" in skill
            assert "level" in skill

    @pytest.mark.asyncio
    async def test_extracts_python_skill(self, sample_resume_text):
        """Should extract Python as a skill from sample resume."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_text)

        skill_names = [s["name"].lower() for s in result.data["skills"]]
        assert "python" in skill_names

    @pytest.mark.asyncio
    async def test_assigns_correct_skill_categories(self, sample_resume_text):
        """Skills should be assigned correct categories."""
        from app.agents.resume_parser import ResumeParserAgent
        from app.models import SkillCategory

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_text)

        valid_categories = [c.value for c in SkillCategory]
        for skill in result.data["skills"]:
            assert skill["category"] in valid_categories

    @pytest.mark.asyncio
    async def test_assigns_correct_skill_levels(self, sample_resume_text):
        """Skills should be assigned valid proficiency levels."""
        from app.agents.resume_parser import ResumeParserAgent
        from app.models import SkillLevel

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_text)

        valid_levels = [l.value for l in SkillLevel]
        for skill in result.data["skills"]:
            assert skill["level"] in valid_levels

    # ========================================================================
    # Experience Extraction Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_extracts_work_experiences(self, sample_resume_text):
        """Should extract work experience entries."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_text)

        experiences = result.data["experiences"]
        assert len(experiences) > 0

    @pytest.mark.asyncio
    async def test_experiences_have_required_fields(self, sample_resume_text):
        """Each experience must have title, company, and duration."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_text)

        for exp in result.data["experiences"]:
            assert "title" in exp
            assert "company" in exp
            assert "duration" in exp

    @pytest.mark.asyncio
    async def test_extracts_company_names(self, sample_resume_text):
        """Should extract company names from experience."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_text)

        companies = [e["company"].lower() for e in result.data["experiences"]]
        # Sample resume mentions Google and Microsoft
        assert any("google" in c for c in companies) or any("microsoft" in c for c in companies)

    # ========================================================================
    # Education Extraction Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_extracts_education(self, sample_resume_text):
        """Should extract education entries."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_text)

        education = result.data["education"]
        assert len(education) > 0

    @pytest.mark.asyncio
    async def test_education_has_required_fields(self, sample_resume_text):
        """Each education entry must have degree and institution."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_text)

        for edu in result.data["education"]:
            assert "degree" in edu
            assert "institution" in edu

    # ========================================================================
    # PII Handling Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_pii_is_redacted(self, sample_resume_with_pii):
        """PII should be redacted from output."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_with_pii)

        # Check SSN is not in output
        result_str = str(result.data)
        assert "123-45-6789" not in result_str

    @pytest.mark.asyncio
    async def test_contact_redacted_flag_is_set(self, sample_resume_with_pii):
        """contact_redacted flag should be True when PII detected."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_with_pii)

        assert result.data["contact_redacted"] is True

    @pytest.mark.asyncio
    async def test_email_is_redacted(self, sample_resume_with_pii):
        """Email addresses should be redacted."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_with_pii)

        result_str = str(result.data)
        assert "john.doe@email.com" not in result_str

    @pytest.mark.asyncio
    async def test_phone_is_redacted(self, sample_resume_with_pii):
        """Phone numbers should be redacted."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_with_pii)

        result_str = str(result.data)
        assert "(555) 123-4567" not in result_str

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_handles_empty_resume(self):
        """Should return error for empty resume."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()

        result = await agent.process("")

        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_handles_non_resume_document(self):
        """Should handle documents that aren't resumes gracefully."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        non_resume = "This is a recipe for chocolate cake. Mix flour, sugar, and cocoa..."

        result = await agent.process(non_resume)

        # Should return result but possibly with minimal extracted data
        assert result is not None

    @pytest.mark.asyncio
    async def test_handles_malformed_input(self):
        """Should handle malformed input without crashing."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        malformed = "\x00\x01\x02 garbage data \xff\xfe"

        result = await agent.process(malformed)

        # Should not raise, should return error result
        assert result is not None

    # ========================================================================
    # Non-English Resume Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_handles_non_english_resume(self):
        """Should gracefully handle non-English resumes."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        japanese_resume = "履歴書: スキル Python, JavaScript"

        result = await agent.process(japanese_resume)

        # Should return result (even if partial)
        assert result.success is True or len(result.errors) > 0

    # ========================================================================
    # Performance Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_processing_time_under_limit(self, sample_resume_text):
        """Processing should complete within time limit."""
        from app.agents.resume_parser import ResumeParserAgent
        import time

        agent = ResumeParserAgent()
        start = time.time()

        await agent.process(sample_resume_text)

        elapsed = time.time() - start
        # Should complete within 30 seconds per spec
        assert elapsed < 30

    @pytest.mark.asyncio
    async def test_reports_processing_time(self, sample_resume_text):
        """Agent should report processing time in output."""
        from app.agents.resume_parser import ResumeParserAgent

        agent = ResumeParserAgent()
        result = await agent.process(sample_resume_text)

        assert result.processing_time_ms is not None
        # Mocked execution may complete in 0ms, so we accept >= 0
        assert result.processing_time_ms >= 0

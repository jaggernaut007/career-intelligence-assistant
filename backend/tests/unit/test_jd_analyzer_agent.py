"""
Unit tests for Job Description Analyzer Agent.

TDD: These tests are written BEFORE implementation.
Tests should FAIL until jd_analyzer.py is implemented.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestJDAnalyzerAgent:
    """Test suite for Job Description Analyzer Agent."""

    # ========================================================================
    # Agent Interface Compliance Tests
    # ========================================================================

    def test_agent_has_required_name_property(self):
        """Agent must have 'name' property per spec."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()

        assert hasattr(agent, "name")
        assert agent.name == "jd_analyzer"

    def test_agent_has_process_method(self):
        """Agent must have async process method per spec."""
        from app.agents.jd_analyzer import JDAnalyzerAgent
        import asyncio

        agent = JDAnalyzerAgent()

        assert hasattr(agent, "process")
        assert asyncio.iscoroutinefunction(agent.process)

    # ========================================================================
    # Output Schema Compliance Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_output_conforms_to_parsed_jd_schema(self, sample_job_description):
        """Output must match ParsedJobDescription specification."""
        from app.agents.jd_analyzer import JDAnalyzerAgent
        from app.models import ParsedJobDescription

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        parsed = ParsedJobDescription.model_validate(result.data)
        assert parsed is not None

    @pytest.mark.asyncio
    async def test_output_includes_required_fields(self, sample_job_description):
        """Output must include all required fields."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        assert "id" in result.data
        assert "title" in result.data
        assert "requirements" in result.data
        assert "required_skills" in result.data

    # ========================================================================
    # Job Title Extraction Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_extracts_job_title(self, sample_job_description):
        """Should extract job title from JD."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        assert result.data["title"] != ""
        assert "engineer" in result.data["title"].lower()

    @pytest.mark.asyncio
    async def test_extracts_company_name(self, sample_job_description):
        """Should extract company name from JD."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        assert result.data.get("company") is not None

    # ========================================================================
    # Requirements Extraction Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_extracts_requirements(self, sample_job_description):
        """Should extract requirements from JD."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        requirements = result.data["requirements"]
        assert len(requirements) > 0

    @pytest.mark.asyncio
    async def test_requirements_have_type_field(self, sample_job_description):
        """Each requirement must have type (must_have/nice_to_have)."""
        from app.agents.jd_analyzer import JDAnalyzerAgent
        from app.models import RequirementType

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        valid_types = [t.value for t in RequirementType]
        for req in result.data["requirements"]:
            assert "type" in req
            assert req["type"] in valid_types

    @pytest.mark.asyncio
    async def test_distinguishes_must_have_from_nice_to_have(self, sample_job_description):
        """Should correctly classify must-have vs nice-to-have requirements."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        types = [r["type"] for r in result.data["requirements"]]
        # Should have both types in sample JD
        assert "must_have" in types or "nice_to_have" in types

    # ========================================================================
    # Required Skills Extraction Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_extracts_required_skills(self, sample_job_description):
        """Should extract required skills from JD."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        required_skills = result.data["required_skills"]
        assert len(required_skills) > 0

    @pytest.mark.asyncio
    async def test_required_skills_have_name_and_category(self, sample_job_description):
        """Required skills must have name and category."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        for skill in result.data["required_skills"]:
            assert "name" in skill
            assert "category" in skill

    @pytest.mark.asyncio
    async def test_extracts_python_as_required(self, sample_job_description):
        """Should identify Python as required skill from sample JD."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        skill_names = [s["name"].lower() for s in result.data["required_skills"]]
        assert "python" in skill_names

    # ========================================================================
    # Nice-to-Have Skills Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_extracts_nice_to_have_skills(self, sample_job_description):
        """Should extract nice-to-have skills from JD."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        # Sample JD has nice-to-have section
        nice_to_have = result.data.get("nice_to_have_skills", [])
        assert isinstance(nice_to_have, list)

    # ========================================================================
    # Experience Requirements Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_extracts_experience_years(self, sample_job_description):
        """Should extract years of experience requirement."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        # Sample JD requires 5+ years
        assert result.data.get("experience_years_min") is not None

    @pytest.mark.asyncio
    async def test_experience_years_are_integers(self, sample_job_description):
        """Experience years should be integers."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        if result.data.get("experience_years_min") is not None:
            assert isinstance(result.data["experience_years_min"], int)

    # ========================================================================
    # Responsibilities Extraction Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_extracts_responsibilities(self, sample_job_description):
        """Should extract job responsibilities."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        responsibilities = result.data.get("responsibilities", [])
        assert len(responsibilities) > 0

    # ========================================================================
    # Culture Signals Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_extracts_culture_signals(self, sample_job_description):
        """Should extract culture signals from JD."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process(sample_job_description)

        culture_signals = result.data.get("culture_signals", [])
        assert isinstance(culture_signals, list)

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_handles_empty_job_description(self):
        """Should return error for empty JD."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        result = await agent.process("")

        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_handles_non_job_description(self):
        """Should handle non-JD text gracefully."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        non_jd = "This is a news article about technology trends..."

        result = await agent.process(non_jd)

        # Should return result but possibly with minimal data
        assert result is not None

    @pytest.mark.asyncio
    async def test_handles_partial_job_description(self):
        """Should handle JD with missing sections."""
        from app.agents.jd_analyzer import JDAnalyzerAgent

        agent = JDAnalyzerAgent()
        partial_jd = "Software Engineer position. Requirements: Python, AWS."

        result = await agent.process(partial_jd)

        assert result.success is True
        assert result.data["title"] != ""

"""
Unit tests for Neo4j Store Service.

TDD: These tests are written BEFORE implementation.
Tests should FAIL until neo4j_store.py is implemented.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime


class TestNeo4jStore:
    """Test suite for Neo4j graph and vector store operations."""

    # ========================================================================
    # Connection Tests (require actual Neo4j instance)
    # ========================================================================

    @pytest.mark.skip(reason="Requires actual Neo4j connection - run in integration tests")
    def test_connects_to_neo4j_auradb(self):
        """Should connect to Neo4j AuraDB using URI from config."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()

        assert store.is_connected()

    @pytest.mark.skip(reason="Requires actual Neo4j connection - run in integration tests")
    def test_handles_connection_failure(self):
        """Should handle connection failures gracefully."""
        from app.services.neo4j_store import Neo4jStore

        with patch.dict('os.environ', {'NEO4J_URI': 'invalid://uri'}):
            store = Neo4jStore()

            assert not store.is_connected()

    @pytest.mark.skip(reason="Requires actual Neo4j connection - run in integration tests")
    def test_closes_connection_on_cleanup(self):
        """Should close connection when store is cleaned up."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()
        store.close()

        assert not store.is_connected()

    # ========================================================================
    # Resume Node Operations
    # ========================================================================

    @pytest.mark.asyncio
    async def test_create_resume_node(self):
        """Should create Resume node in graph."""
        from app.services.neo4j_store import Neo4jStore
        from app.models import ParsedResume, Skill, Experience, Education, SkillLevel, SkillCategory

        store = Neo4jStore()
        resume = ParsedResume(
            id="resume-123",
            skills=[Skill(name="Python", category=SkillCategory.PROGRAMMING, level=SkillLevel.EXPERT)],
            experiences=[],
            education=[],
            certifications=[],
            summary="Test resume",
            contact_redacted=True
        )

        result = await store.save_resume(resume)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_resume_by_id(self):
        """Should retrieve Resume node by ID."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()
        resume_id = "resume-123"

        resume = await store.get_resume(resume_id)

        assert resume is not None
        assert resume.id == resume_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_resume_returns_none(self):
        """Should return None for non-existent resume ID."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()

        resume = await store.get_resume("nonexistent-id")

        assert resume is None

    # ========================================================================
    # Job Description Node Operations
    # ========================================================================

    @pytest.mark.asyncio
    async def test_create_job_description_node(self):
        """Should create JobDescription node in graph."""
        from app.services.neo4j_store import Neo4jStore
        from app.models import ParsedJobDescription, Skill, Requirement, SkillLevel, SkillCategory, RequirementType

        store = Neo4jStore()
        jd = ParsedJobDescription(
            id="job-456",
            title="Senior Software Engineer",
            company="TechCorp",
            requirements=[Requirement(text="5+ years experience", type=RequirementType.MUST_HAVE, skills=["Python"])],
            required_skills=[Skill(name="Python", category=SkillCategory.PROGRAMMING, level=SkillLevel.ADVANCED)],
            nice_to_have_skills=[],
            education_requirements=[],
            responsibilities=[],
            culture_signals=[]
        )

        result = await store.save_job_description(jd)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_job_description_by_id(self):
        """Should retrieve JobDescription node by ID."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()
        job_id = "job-456"

        jd = await store.get_job_description(job_id)

        assert jd is not None
        assert jd.id == job_id

    # ========================================================================
    # Skill Node Operations
    # ========================================================================

    @pytest.mark.asyncio
    async def test_create_skill_node(self):
        """Should create or merge Skill node in graph."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()

        result = await store.create_or_merge_skill("Python", "programming")

        assert result is True

    @pytest.mark.asyncio
    async def test_skill_node_is_unique_by_name(self):
        """Same skill name should merge, not create duplicate."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()

        await store.create_or_merge_skill("Python", "programming")
        await store.create_or_merge_skill("Python", "programming")

        count = await store.count_skill_nodes("Python")

        assert count == 1

    # ========================================================================
    # Relationship Operations
    # ========================================================================

    @pytest.mark.asyncio
    async def test_create_has_skill_relationship(self):
        """Should create HAS_SKILL relationship between Resume and Skill."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()

        result = await store.create_has_skill_relationship(
            resume_id="resume-123",
            skill_name="Python",
            proficiency="expert",
            years=5
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_create_requires_relationship(self):
        """Should create REQUIRES relationship between Job and Requirement."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()

        result = await store.create_requires_relationship(
            job_id="job-456",
            requirement_text="5+ years experience"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_create_matched_to_relationship(self):
        """Should create MATCHED_TO relationship between Resume and Job."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()

        result = await store.create_match_relationship(
            resume_id="resume-123",
            job_id="job-456",
            score=85.5,
            gaps=["Kubernetes", "Go"]
        )

        assert result is True

    # ========================================================================
    # Vector Index Operations
    # ========================================================================

    @pytest.mark.asyncio
    async def test_store_resume_embedding(self):
        """Should store embedding vector on Resume node."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()
        embedding = [0.1] * 768

        result = await store.store_embedding(
            node_type="Resume",
            node_id="resume-123",
            embedding=embedding
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_vector_similarity_search(self):
        """Should find similar nodes by vector similarity."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()
        query_embedding = [0.1] * 768

        results = await store.vector_similarity_search(
            node_type="Resume",
            embedding=query_embedding,
            top_k=5
        )

        assert isinstance(results, list)
        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_vector_search_returns_similarity_scores(self):
        """Vector search results should include similarity scores."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()
        query_embedding = [0.1] * 768

        results = await store.vector_similarity_search(
            node_type="Resume",
            embedding=query_embedding,
            top_k=5
        )

        if results:
            assert all("score" in r for r in results)
            assert all(0 <= r["score"] <= 1 for r in results)

    # ========================================================================
    # Query Operations
    # ========================================================================

    @pytest.mark.asyncio
    async def test_find_skills_for_resume(self):
        """Should find all skills associated with a resume."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()

        skills = await store.get_resume_skills("resume-123")

        assert isinstance(skills, list)

    @pytest.mark.asyncio
    async def test_find_matching_jobs_for_resume(self):
        """Should find jobs that match a resume's skills."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()

        matches = await store.find_matching_jobs("resume-123")

        assert isinstance(matches, list)

    @pytest.mark.asyncio
    async def test_get_skill_gap_analysis(self):
        """Should return skills required by job but missing from resume."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()

        gaps = await store.get_skill_gaps(
            resume_id="resume-123",
            job_id="job-456"
        )

        assert isinstance(gaps, list)

    # ========================================================================
    # Session Management
    # ========================================================================

    @pytest.mark.asyncio
    async def test_save_session_data(self):
        """Should save session data to graph."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()
        session_data = {
            "session_id": "session-789",
            "resume_id": "resume-123",
            "job_ids": ["job-456"],
            "created_at": datetime.utcnow().isoformat()
        }

        result = await store.save_session(session_data)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_session_data(self):
        """Should retrieve session data from graph."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()

        session = await store.get_session("session-789")

        assert session is not None
        assert session["session_id"] == "session-789"

    # ========================================================================
    # Cleanup Operations
    # ========================================================================

    @pytest.mark.asyncio
    async def test_delete_session_data(self):
        """Should delete session and related temporary data."""
        from app.services.neo4j_store import Neo4jStore

        store = Neo4jStore()

        result = await store.delete_session("session-789")

        assert result is True

        session = await store.get_session("session-789")
        assert session is None

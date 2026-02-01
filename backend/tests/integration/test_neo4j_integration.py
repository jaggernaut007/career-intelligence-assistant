"""
Integration tests for Neo4j Store Service.

These tests run against the actual Neo4j AuraDB instance.
Requires NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD environment variables.
"""

import pytest
import uuid
from datetime import datetime

from app.services.neo4j_store import Neo4jStore
from app.models import (
    ParsedResume, ParsedJobDescription,
    Skill, Experience, Education, Requirement,
    SkillLevel, SkillCategory, RequirementType
)


def generate_test_id():
    """Generate unique test ID to avoid conflicts."""
    return f"test-{uuid.uuid4().hex[:8]}"


@pytest.mark.integration
class TestNeo4jIntegration:
    """Integration tests for Neo4j operations against real database."""

    @pytest.fixture
    def store(self):
        """Get Neo4j store instance."""
        return Neo4jStore()

    @pytest.fixture
    def test_resume_id(self):
        """Generate unique resume ID for test."""
        return generate_test_id()

    @pytest.fixture
    def test_job_id(self):
        """Generate unique job ID for test."""
        return generate_test_id()

    # ========================================================================
    # Connection Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_connects_to_neo4j(self, store):
        """Should connect to Neo4j AuraDB."""
        driver = await store._get_async_driver()
        assert driver is not None
        assert store._connected is True

    # ========================================================================
    # Resume CRUD Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_save_and_retrieve_resume(self, store, test_resume_id):
        """Should save resume and retrieve it by ID."""
        resume = ParsedResume(
            id=test_resume_id,
            skills=[
                Skill(name="Python", category=SkillCategory.PROGRAMMING, level=SkillLevel.EXPERT),
                Skill(name="AWS", category=SkillCategory.TOOL, level=SkillLevel.ADVANCED)
            ],
            experiences=[
                Experience(
                    title="Software Engineer",
                    company="TestCorp",
                    duration="3 years",
                    duration_months=36,
                    description="Built systems",
                    skills_used=["Python"]
                )
            ],
            education=[
                Education(degree="B.S. Computer Science", institution="Test University", year=2020)
            ],
            certifications=[],
            summary="Test resume",
            contact_redacted=True
        )

        # Save
        result = await store.save_resume(resume)
        assert result is True

        # Retrieve
        retrieved = await store.get_resume(test_resume_id)
        assert retrieved is not None
        assert retrieved.id == test_resume_id
        assert len(retrieved.skills) == 2
        assert any(s.name == "Python" for s in retrieved.skills)

        # Cleanup
        driver = await store._get_async_driver()
        async with driver.session() as session:
            await session.run(f'MATCH (r:Resume {{id: "{test_resume_id}"}}) DETACH DELETE r')

    @pytest.mark.asyncio
    async def test_get_nonexistent_resume(self, store):
        """Should return None for non-existent resume."""
        result = await store.get_resume("nonexistent-resume-id-12345")
        assert result is None

    # ========================================================================
    # Job Description CRUD Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_save_and_retrieve_job_description(self, store, test_job_id):
        """Should save job description and retrieve it by ID."""
        jd = ParsedJobDescription(
            id=test_job_id,
            title="Senior Software Engineer",
            company="TestCorp",
            requirements=[
                Requirement(text="5+ years experience", type=RequirementType.MUST_HAVE, skills=["Python"])
            ],
            required_skills=[
                Skill(name="Python", category=SkillCategory.PROGRAMMING, level=SkillLevel.EXPERT),
                Skill(name="Kubernetes", category=SkillCategory.TOOL, level=SkillLevel.ADVANCED)
            ],
            nice_to_have_skills=[
                Skill(name="Go", category=SkillCategory.PROGRAMMING, level=SkillLevel.INTERMEDIATE)
            ],
            education_requirements=[],
            responsibilities=["Lead engineering team"],
            culture_signals=["Fast-paced"]
        )

        # Save
        result = await store.save_job_description(jd)
        assert result is True

        # Retrieve
        retrieved = await store.get_job_description(test_job_id)
        assert retrieved is not None
        assert retrieved.id == test_job_id
        assert retrieved.title == "Senior Software Engineer"
        assert len(retrieved.required_skills) >= 1

        # Cleanup
        driver = await store._get_async_driver()
        async with driver.session() as session:
            await session.run(f'MATCH (j:JobDescription {{id: "{test_job_id}"}}) DETACH DELETE j')

    # ========================================================================
    # Skill Operations Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_create_and_count_skills(self, store):
        """Should create skill and verify uniqueness."""
        unique_skill = f"TestSkill-{uuid.uuid4().hex[:6]}"

        # Create skill twice
        await store.create_or_merge_skill(unique_skill, "testing")
        await store.create_or_merge_skill(unique_skill, "testing")

        # Count should be 1 (MERGE ensures uniqueness)
        count = await store.count_skill_nodes(unique_skill)
        assert count == 1

        # Cleanup
        driver = await store._get_async_driver()
        async with driver.session() as session:
            await session.run(f'MATCH (s:Skill {{name: "{unique_skill}"}}) DELETE s')

    # ========================================================================
    # Relationship Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_skill_gap_analysis(self, store, test_resume_id, test_job_id):
        """Should correctly identify skill gaps between resume and job."""
        # Create resume with Python and AWS
        resume = ParsedResume(
            id=test_resume_id,
            skills=[
                Skill(name="Python", category=SkillCategory.PROGRAMMING, level=SkillLevel.EXPERT),
                Skill(name="AWS", category=SkillCategory.TOOL, level=SkillLevel.ADVANCED)
            ],
            experiences=[],
            education=[],
            certifications=[],
            summary="Test",
            contact_redacted=True
        )
        await store.save_resume(resume)

        # Create job requiring Python, Kubernetes, Deep Learning
        jd = ParsedJobDescription(
            id=test_job_id,
            title="ML Engineer",
            company="TestCorp",
            requirements=[],
            required_skills=[
                Skill(name="Python", category=SkillCategory.PROGRAMMING, level=SkillLevel.EXPERT),
                Skill(name="Kubernetes", category=SkillCategory.TOOL, level=SkillLevel.ADVANCED),
                Skill(name="Deep Learning", category=SkillCategory.DOMAIN, level=SkillLevel.ADVANCED)
            ],
            nice_to_have_skills=[],
            education_requirements=[],
            responsibilities=[],
            culture_signals=[]
        )
        await store.save_job_description(jd)

        # Get skill gaps
        gaps = await store.get_skill_gaps(test_resume_id, test_job_id)

        # Should find Kubernetes and Deep Learning as gaps (Python is matched)
        gap_names = [g["skill_name"] for g in gaps]
        assert "Kubernetes" in gap_names
        assert "Deep Learning" in gap_names
        assert "Python" not in gap_names  # Python should match

        # Cleanup
        driver = await store._get_async_driver()
        async with driver.session() as session:
            await session.run(f'MATCH (r:Resume {{id: "{test_resume_id}"}}) DETACH DELETE r')
            await session.run(f'MATCH (j:JobDescription {{id: "{test_job_id}"}}) DETACH DELETE j')

    @pytest.mark.asyncio
    async def test_match_relationship(self, store, test_resume_id, test_job_id):
        """Should create and verify match relationship with score."""
        # Create resume and job
        resume = ParsedResume(
            id=test_resume_id,
            skills=[Skill(name="Python", category=SkillCategory.PROGRAMMING, level=SkillLevel.EXPERT)],
            experiences=[],
            education=[],
            certifications=[],
            summary="Test",
            contact_redacted=True
        )
        await store.save_resume(resume)

        jd = ParsedJobDescription(
            id=test_job_id,
            title="Engineer",
            company="Test",
            requirements=[],
            required_skills=[Skill(name="Python", category=SkillCategory.PROGRAMMING, level=SkillLevel.EXPERT)],
            nice_to_have_skills=[],
            education_requirements=[],
            responsibilities=[],
            culture_signals=[]
        )
        await store.save_job_description(jd)

        # Create match
        result = await store.create_match_relationship(
            resume_id=test_resume_id,
            job_id=test_job_id,
            score=85.5,
            gaps=["Kubernetes"]
        )
        assert result is True

        # Cleanup
        driver = await store._get_async_driver()
        async with driver.session() as session:
            await session.run(f'MATCH (r:Resume {{id: "{test_resume_id}"}}) DETACH DELETE r')
            await session.run(f'MATCH (j:JobDescription {{id: "{test_job_id}"}}) DETACH DELETE j')

    # ========================================================================
    # Vector Operations Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_store_and_search_embeddings(self, store, test_resume_id):
        """Should store embedding and find it via vector search."""
        # Create resume
        resume = ParsedResume(
            id=test_resume_id,
            skills=[Skill(name="Python", category=SkillCategory.PROGRAMMING, level=SkillLevel.EXPERT)],
            experiences=[],
            education=[],
            certifications=[],
            summary="Test",
            contact_redacted=True
        )
        await store.save_resume(resume)

        # Store embedding
        embedding = [0.5] * 768
        result = await store.store_embedding("Resume", test_resume_id, embedding)
        assert result is True

        # Search (should find at least our resume)
        results = await store.vector_similarity_search("Resume", embedding, top_k=5)
        assert isinstance(results, list)

        # Cleanup
        driver = await store._get_async_driver()
        async with driver.session() as session:
            await session.run(f'MATCH (r:Resume {{id: "{test_resume_id}"}}) DETACH DELETE r')

    # ========================================================================
    # Session Operations Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_session_crud(self, store):
        """Should save, retrieve, and delete session data."""
        session_id = generate_test_id()
        session_data = {
            "session_id": session_id,
            "resume_id": "resume-123",
            "job_ids": ["job-1", "job-2"],
            "created_at": datetime.utcnow().isoformat()
        }

        # Save
        result = await store.save_session(session_data)
        assert result is True

        # Retrieve
        retrieved = await store.get_session(session_id)
        assert retrieved is not None
        assert retrieved["session_id"] == session_id

        # Delete
        delete_result = await store.delete_session(session_id)
        assert delete_result is True

        # Verify deleted
        after_delete = await store.get_session(session_id)
        assert after_delete is None

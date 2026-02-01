import pytest
from unittest.mock import AsyncMock, patch
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Load .env file BEFORE any fixtures run
from dotenv import load_dotenv

# Find the backend .env file
backend_dir = Path(__file__).parent.parent.parent
env_file = backend_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)

class MockNeo4jStore:
    def __init__(self):
        self.resumes: Dict[str, Any] = {}
        self.jobs: Dict[str, Any] = {}
        
        # Async methods to mock
        self.save_resume = AsyncMock()
        self.store_skill_embedding = AsyncMock()
        self.find_similar_resume_skills = AsyncMock(return_value=[])

    async def get_resume(self, resume_id: str):
        return self.resumes.get(resume_id)

    async def get_job_description(self, job_id: str):
        return self.jobs.get(job_id)
        
    def reset(self):
        self.resumes = {}
        self.jobs = {}
        self.save_resume.reset_mock()
        self.store_skill_embedding.reset_mock()
        self.find_similar_resume_skills.reset_mock()

@pytest.fixture(scope="session", autouse=True)
def mock_env():
    """Ensure environment variables are set for testing."""
    # Only set dummy key if no real key is available (for CI environments)
    if not os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY") == "sk-dummy-key":
        pytest.skip("OPENAI_API_KEY not set - evaluation tests require a real API key")

@pytest.fixture(autouse=True)
def mock_store():
    """
    Mock Neo4j store.
    Yields the MockNeo4jStore instance so tests can seed data.
    """
    store_instance = MockNeo4jStore()
    
    # Patch where get_neo4j_store is defined, and also where it might be imported directly
    # Using patch.dict to patch specific modules if needed, but simple patching is usually spread per test.
    # Here we blanket patch widely used accessors.
    
    with patch("app.services.neo4j_store.get_neo4j_store", return_value=store_instance), \
         patch("app.agents.resume_parser.get_neo4j_store", return_value=store_instance), \
         patch("app.agents.jd_analyzer.get_neo4j_store", return_value=store_instance), \
         patch("app.agents.skill_matcher.get_neo4j_store", return_value=store_instance), \
         patch("app.agents.recommendation.get_neo4j_store", return_value=store_instance), \
         patch("app.agents.interview_prep.get_neo4j_store", return_value=store_instance):
         
        yield store_instance

@pytest.fixture(autouse=True)
def mock_embedding():
    """Mock embedding to avoid API calls."""
    mock_embed = AsyncMock()
    mock_embed.embed = AsyncMock(return_value=[0.1] * 1536)
    
    # Patch where get_embedding_service is defined.
    # Since agents do local imports (inside methods), patching the source is sufficient.
    with patch("app.services.embedding.get_embedding_service", return_value=mock_embed):
         
        yield mock_embed

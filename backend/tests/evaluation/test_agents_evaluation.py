import pytest
import asyncio
import logging
from typing import Dict, Any, Type
from unittest.mock import AsyncMock

from app.agents.resume_parser import ResumeParserAgent
from app.agents.jd_analyzer import JDAnalyzerAgent
from app.agents.skill_matcher import SkillMatcherAgent
from app.agents.interview_prep import InterviewPrepAgent
from app.agents.recommendation import RecommendationAgent
from app.agents.market_insights import MarketInsightsAgent
from app.services.llamaindex_service import LlamaIndexService

from tests.evaluation.llm_judge import LLMJudge
from tests.evaluation.test_cases import get_test_cases_for_agent, AgentTestCase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Map agent names to classes
AGENT_CLASSES: Dict[str, Type] = {
    "resume_parser": ResumeParserAgent,
    "jd_analyzer": JDAnalyzerAgent,
    "skill_matcher": SkillMatcherAgent,
    "interview_prep": InterviewPrepAgent,
    "recommendation": RecommendationAgent,
    "market_insights": MarketInsightsAgent,
}

@pytest.fixture
async def real_llamaindex_service():
    """Create a real LlamaIndexService instance but mock vector store interactions."""
    service = LlamaIndexService()
    
    # Initialize normally - this connects to OpenAI
    # We rely on settings being present in env
    try:
        await service.initialize()
    except Exception as e:
        logger.warning(f"Failed to initialize real LlamaIndexService (check API keys): {e}")
        service._initialized = True
        service._llm = AsyncMock()
    
    # Mock the vector store and store_* methods preventing Neo4j calls
    service._vector_store = AsyncMock() 
    service.store_resume_nodes = AsyncMock()
    service.store_job_nodes = AsyncMock()
    service.semantic_skill_search = AsyncMock(return_value=[])
    service.find_similar_skills = AsyncMock(return_value=[])
    service.embed_text = AsyncMock(return_value=[0.1] * 768)
    service.embed_texts = AsyncMock(return_value=[[0.1] * 768])
    
    return service

@pytest.mark.asyncio
async def test_agent_evaluation(mock_store, real_llamaindex_service, mock_embedding_service, monkeypatch):
    """
    Run LLM-based evaluation for all defined test cases.
    """
    judge = LLMJudge()
    
    # Override get_llamaindex_service to return the REAL service
    async def get_real_service():
        return real_llamaindex_service
        
    # Override get_embedding_service to return MOCK to avoid large model download
    def get_mock_embedding():
        return mock_embedding_service

    # Patch ALL modules that use these services
    agent_modules = [
        "app.agents.base_agent", 
        "app.agents.resume_parser",
        "app.agents.jd_analyzer", 
        "app.agents.skill_matcher",
        "app.agents.recommendation",
        "app.agents.interview_prep",
        "app.agents.market_insights",
        "app.services.llamaindex_service", # Patch the service itself as well
    ]
    
    # Patch get_llamaindex_service (async getter)
    monkeypatch.setattr("app.services.llamaindex_service.get_llamaindex_service", get_real_service)
    
    # Patch get_embedding_service (sync getter)
    monkeypatch.setattr("app.services.embedding.get_embedding_service", get_mock_embedding)

    for module in agent_modules:
        try:
            monkeypatch.setattr(f"{module}.get_llamaindex_service", get_real_service)
        except (AttributeError, ImportError):
             pass
        try:
             monkeypatch.setattr(f"{module}.get_embedding_service", get_mock_embedding)
        except (AttributeError, ImportError):
             pass

    # Iterate over all known agents and their test cases
    for agent_name, AgentClass in AGENT_CLASSES.items():
        test_cases = get_test_cases_for_agent(agent_name)
        
        if not test_cases:
            logger.info(f"No test cases found for agent: {agent_name}")
            continue
            
        logger.info(f"Running evaluation for agent: {agent_name} with {len(test_cases)} test cases")
        
        agent = AgentClass()
        
        for test_case in test_cases:
            logger.info(f"  Running Test Case: {test_case.id} - {test_case.description}")
            
            # Setup mock data if present
            mock_store.reset()
            if test_case.mock_data:
                logger.info("  Seeding mock data for test case")
                if "resumes" in test_case.mock_data:
                    mock_store.resumes.update(test_case.mock_data["resumes"])
                if "jobs" in test_case.mock_data:
                    mock_store.jobs.update(test_case.mock_data["jobs"])
            
            try:
                # Execute Agent
                result = await agent.process(test_case.input_data)
                
                if not result.success:
                    pytest.fail(f"Agent execution failed for {test_case.id}: {result.errors}")
                
                actual_output = result.data
                
                # Evaluate with LLM Judge
                evaluation = await judge.evaluate(
                    agent_name=agent_name,
                    input_data=test_case.input_data,
                    actual_output=actual_output,
                    criteria=test_case.criteria,
                    context=test_case.context
                )
                
                logger.info(f"  Score: {evaluation.score}/10")
                logger.info(f"  Reasoning: {evaluation.reasoning}")
                
                # Assertions
                errors = []
                if not evaluation.is_passing:
                    errors.append(f"Test case {test_case.id} FAILED evaluation. Reason: {evaluation.reasoning}")
                
                if evaluation.score < 6.0: # Threshold for passing
                    errors.append(f"Test case {test_case.id} score too low ({evaluation.score}).")
                
                if errors:
                    pytest.fail("\n".join(errors))
                    
            except Exception as e:
                logger.error(f"  Error running test case {test_case.id}: {e}")
                raise e

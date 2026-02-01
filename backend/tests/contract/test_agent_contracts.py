import pytest
import inspect
from app.agents.base_agent import BaseAgent
from app.agents.resume_parser import ResumeParserAgent
from app.agents.jd_analyzer import JDAnalyzerAgent
from app.agents.skill_matcher import SkillMatcherAgent
# Import other agents as needed

@pytest.mark.contract
def test_agents_inherit_base_agent():
    """Verify all agents inherit from BaseAgent."""
    agents = [
        ResumeParserAgent,
        JDAnalyzerAgent,
        SkillMatcherAgent,
        # Add others
    ]
    for agent_class in agents:
        assert issubclass(agent_class, BaseAgent), f"{agent_class.__name__} must inherit from BaseAgent"

@pytest.mark.contract
def test_agents_implement_process_method():
    """Verify all agents implement the process method with correct signature."""
    agents = [
        ResumeParserAgent,
        JDAnalyzerAgent,
        SkillMatcherAgent,
    ]
    for agent_class in agents:
        process_method = getattr(agent_class, "process", None)
        assert process_method is not None, f"{agent_class.__name__} must implement process()"
        assert inspect.iscoroutinefunction(process_method), f"{agent_class.__name__}.process must be async"
        
        # Check signature (input: AgentInput) -> AgentOutput
        sig = inspect.signature(process_method)
        # First param should be 'input' (excluding self)
        params = list(sig.parameters.values())
        assert len(params) >= 1, f"{agent_class.__name__}.process must take input argument"

@pytest.mark.contract
def test_agent_names_are_unique():
    """Verify all agents have unique names."""
    agents = [
        ResumeParserAgent(),
        JDAnalyzerAgent(),
        SkillMatcherAgent(),
    ]
    names = [agent.name for agent in agents]
    assert len(names) == len(set(names)), "Agent names must be unique"

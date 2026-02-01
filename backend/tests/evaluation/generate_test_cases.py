"""
Script to generate synthetic test cases for agents using LLM.
"""

import sys
import os
import asyncio
import inspect
from typing import Type

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.services.llm_service import LLMService
from app.agents.base_agent import BaseAgent
from app.agents.resume_parser import ResumeParserAgent
from app.agents.jd_analyzer import JDAnalyzerAgent
from app.agents.skill_matcher import SkillMatcherAgent
from app.agents.interview_prep import InterviewPrepAgent
from app.agents.recommendation import RecommendationAgent
from app.agents.market_insights import MarketInsightsAgent

# Registry of agents
AGENTS = {
    "resume_parser": ResumeParserAgent,
    "jd_analyzer": JDAnalyzerAgent,
    "skill_matcher": SkillMatcherAgent,
    "interview_prep": InterviewPrepAgent,
    "recommendation": RecommendationAgent,
    "market_insights": MarketInsightsAgent
}

async def generate_cases(agent_name: str, count: int = 3):
    if agent_name not in AGENTS:
        print(f"Unknown agent: {agent_name}")
        return

    agent_cls: Type[BaseAgent] = AGENTS[agent_name]
    # Instantiate to access properties if they are instance properties (they are abstract properties in BaseAgent)
    # But in implementations they might be class level or require instantiation. 
    # BaseAgent defines them as @property @abstractmethod, so we usually need an instance.
    try:
        agent = agent_cls()
    except Exception as e:
        # Some agents might need init args, but BaseAgent defaults session_id to None
        print(f"Failed to instantiate agent {agent_name}: {e}")
        return

    name = agent.name
    description = agent.description
    input_schema = agent.input_schema.model_json_schema()
    output_schema = agent.output_schema.model_json_schema()

    prompt = f"""
You are a Test Data Generator. 
I need you to generate {count} test cases for the AI Agent: "{name}".

Agent Description: {description}

Input Schema (JSON Schema):
{input_schema}

Output Schema (JSON Schema):
{output_schema}

Please generate {count} Python `AgentTestCase` instantiation blocks.
Each test case should have:
1. `id`: unique string id (e.g. "{name}_gen_001")
2. `agent_name`: "{name}"
3. `input_data`: A valid dictionary matching Input Schema. Make the content realistic.
4. `criteria`: A numbered list of textual expectations that the output must satisfy.
5. `description`: Short title of the test case.
6. `mock_data`: (Optional) If the agent requires data from Neo4j (e.g. `resume_parser` stores data that others read, or `skill_matcher` reads resumes and jobs), provide realistic mock data.
   - For agents like `skill_matcher`, `interview_prep`, `recommendation`: They likely need `resumes` and `jobs` in the database.
   - Generate `mock_data` dictionary with keys "resumes" and/or "jobs".
   - "resumes": Dict[resume_id, {{ "id": ..., "skills": [...], "experiences": [...], "education": [...] }}]
   - "jobs": Dict[job_id, {{ "id": ..., "title": ..., "required_skills": [...], "experience_years_min": ... }}]
   - Ensure the identifiers in `input_data` match the keys in `mock_data`.

Format the output as valid Python code that I can copy-paste into my `test_cases.py` file.
Do not include imports, just the `AgentTestCase(...)` objects in a list named `NEW_CASES`.
"""

    llm = LLMService()
    print(f"Generating {count} test cases for {agent_name}...")
    
    code = await llm.complete(prompt, temperature=0.7)
    
    # Strip markdown code blocks if present
    code = code.replace("```python", "").replace("```", "").strip()

    print("\n" + "="*80)
    print("GENERATED TEST CASES CODE")
    print("="*80 + "\n")
    print(code)
    print("\n" + "="*80)
    
    # Optional: Save to file
    output_file = os.path.join(os.path.dirname(__file__), "generated_test_data.py")
    with open(output_file, "a") as f:
        f.write(f"\n# Generated for {agent_name}\n")
        f.write(code + "\n")
    print(f"Appended code to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_test_cases.py <agent_name> [count]")
        print(f"Available agents: {', '.join(AGENTS.keys())}")
        sys.exit(1)
        
    agent_arg = sys.argv[1]
    count_arg = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    asyncio.run(generate_cases(agent_arg, count_arg))

"""
Test cases definitions for LLM evaluation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class AgentTestCase(BaseModel):
    id: str
    agent_name: str
    input_data: Dict[str, Any]
    criteria: List[str]  # Changed to List[str] to match generated output format
    description: str
    context: Optional[str] = None
    mock_data: Optional[Dict[str, Any]] = None  # Key: "resumes" or "jobs" -> Dict[id, data]

# Sample Resume Text
SAMPLE_RESUME_TEXT = """
John Doe
Software Engineer
Email: john.doe@example.com
Phone: (555) 123-4567

Summary:
Experienced Python developer with 5 years of experience in backend development using FastAPI and Django.
Skilled in cloud architecture (AWS) and database management (PostgreSQL).

Experience:
Senior Software Engineer - TechCorp (2020 - Present)
- Led a team of 5 developers to build a scalable microservices architecture.
- Improved API response time by 40%.

Software Developer - StartupInc (2018 - 2020)
- Developed RESTful APIs using Flask.
- Managed deployment pipelines using Docker and Jenkins.

Education:
B.S. Computer Science - University of Tech (2014 - 2018)

Skills:
Python, Docker, Kubernetes, AWS, SQL, Git
"""

SAMPLE_JD_TEXT = """
Job Title: Senior Python Engineer

Requirements:
- 5+ years of experience with Python.
- Strong knowledge of FastAPI or Django.
- Experience with cloud platforms, preferably AWS.
- Familiarity with containerization (Docker, Kubernetes).
- Bachelor's degree in Computer Science or related field.
"""

# Define Test Cases
TEST_CASES = [
    AgentTestCase(
        id="resume_parser_001",
        agent_name="resume_parser",
        input_data={"resume_text": SAMPLE_RESUME_TEXT},
        criteria=[
            "1. Must confirm that contact information was redacted (contact_redacted=True).",
            "2. Must list at least 5 technical skills including Python, Docker, AWS.",
            "3. Must identify 2 work experiences with correct companies (TechCorp, StartupInc).",
            "4. Must identify 1 education entry (University of Tech).",
            "5. Must extract a professional summary."
        ],
        description="Basic Resume Parsing Test"
    ),
    AgentTestCase(
        id="jd_analyzer_001",
        agent_name="jd_analyzer",
        input_data={"jd_text": SAMPLE_JD_TEXT},
        criteria=[
            "1. Must identify the job title as 'Senior Python Engineer'. ",
            "2. Must extract required years of experience (5+). ",
            "3. Must list key required skills (Python, FastAPI, Django, AWS, Docker, Kubernetes). ",
            "4. Must identify the education requirement."
        ],
        description="Basic Job Description Analysis Test"
    ),
    AgentTestCase(
        id="skill_matcher_001",
        agent_name="skill_matcher",
        input_data={
            "session_id": "test_session",
            "resume_id": "res_fake_1",
            "job_id": "job_fake_1"
        },
        criteria=[
            "1. Must calculate a fit_score between 0 and 100. ",
            "2. Must identify 'Python' and 'FastAPI' as matching skills. ",
            "3. Must identify 'AWS' as a missing skill. ",
            "4. The match quality for Python should be 'exact' or 'exceeds'. "
        ],
        description="Skill Matcher Basic Test with Mock Data",
        mock_data={
            "resumes": {
                "res_fake_1": {
                    "id": "res_fake_1",
                    "skills": [
                        {"name": "Python", "level": "expert"}, 
                        {"name": "FastAPI", "level": "advanced"},
                        {"name": "Docker", "level": "intermediate"}
                    ],
                    "experiences": [{"duration_months": 60}], 
                    "education": [{"degree": "Bachelor"}]
                }
            },
            "jobs": {
                "job_fake_1": {
                    "id": "job_fake_1",
                    "title": "Senior Backend Engineer",
                    "required_skills": [
                        {"name": "Python", "level": "advanced"},
                        {"name": "FastAPI", "level": "intermediate"},
                        {"name": "AWS", "level": "intermediate"}
                    ],
                    "nice_to_have_skills": [],
                    "experience_years_min": 5,
                    "education_requirements": ["Bachelor"]
                }
            }
        }
    )
]

def get_test_cases_for_agent(agent_name: str) -> List[AgentTestCase]:
    # Try to import generated cases
    generated_cases = []
    try:
        from tests.evaluation.generated_test_data import NEW_CASES
        generated_cases = NEW_CASES
    except ImportError:
        pass
    except Exception as e:
        print(f"Warning: Could not load generated test cases: {e}")

    all_cases = TEST_CASES + generated_cases
    return [tc for tc in all_cases if tc.agent_name == agent_name]

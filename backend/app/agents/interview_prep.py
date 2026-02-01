"""
Interview Prep Agent.

Generates likely interview questions and suggested answers based on
resume and job description analysis using LLM.
"""

import logging
from typing import Any, Dict, List, Optional, Type
from uuid import uuid4

from pydantic import BaseModel

from app.agents.base_agent import BaseAgent
from app.models import (
    Difficulty,
    InterviewPrepResult,
    InterviewQuestion,
    QuestionCategory,
    STARExample,
    WeaknessResponse,
)
from app.services.llamaindex_service import get_llamaindex_service
from app.services.neo4j_store import get_neo4j_store

logger = logging.getLogger(__name__)


class InterviewPrepInput(BaseModel):
    """Input schema for interview prep agent."""
    session_id: str
    resume_id: str
    job_id: str
    skill_gaps: Optional[List[str]] = None




class InterviewPrepAgent(BaseAgent):
    """
    Agent for generating interview preparation materials using LLM.

    Uses LlamaIndex LLM to generate:
    - Behavioral questions with STAR examples
    - Technical questions based on required skills
    - Culture fit questions
    - Weakness responses for skill gaps
    - Questions for the candidate to ask
    - Key talking points

    Works for any job type - not limited to tech roles.
    """

    @property
    def name(self) -> str:
        return "interview_prep"

    @property
    def description(self) -> str:
        return "Generates likely interview questions and suggested answers based on resume and job description analysis using LLM."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return InterviewPrepInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return InterviewPrepResult

    async def health_check(self) -> bool:
        """Check if the agent is ready to process requests."""
        try:
            llamaindex_service = await get_llamaindex_service()
            return llamaindex_service is not None
        except Exception as e:
            logger.warning(f"Health check failed for {self.name}: {e}")
            return False

    def _map_difficulty(self, difficulty_str: str) -> Difficulty:
        """Map string difficulty to Difficulty enum."""
        difficulty_lower = difficulty_str.lower() if difficulty_str else "medium"
        if "easy" in difficulty_lower:
            return Difficulty.EASY
        elif "hard" in difficulty_lower:
            return Difficulty.HARD
        return Difficulty.MEDIUM

    def _map_category(self, category_str: str) -> QuestionCategory:
        """Map string category to QuestionCategory enum."""
        category_lower = category_str.lower() if category_str else "technical"
        if "behavior" in category_lower:
            return QuestionCategory.BEHAVIORAL
        elif "culture" in category_lower or "fit" in category_lower:
            return QuestionCategory.CULTURE_FIT
        elif "situation" in category_lower:
            return QuestionCategory.SITUATIONAL
        return QuestionCategory.TECHNICAL

    async def _execute(self, input_data: Any) -> Dict[str, Any]:
        """
        Execute interview preparation generation using LLM.

        Args:
            input_data: Dict with session_id, resume_id, job_id, skill_gaps

        Returns:
            Dict conforming to InterviewPrepResult schema
        """
        if not isinstance(input_data, dict):
            raise ValueError("Input must be a dictionary")

        session_id = input_data.get("session_id", "")
        resume_id = input_data.get("resume_id", "")
        job_id = input_data.get("job_id")
        skill_gaps_input = input_data.get("skill_gaps", [])

        await self.report_progress(10, "Fetching data from Neo4j")

        # Fetch data from Neo4j
        store = get_neo4j_store()

        try:
            resume_data = await store.get_resume(resume_id)
            if hasattr(resume_data, "model_dump"):
                resume_dict = resume_data.model_dump()
            elif isinstance(resume_data, dict):
                resume_dict = resume_data
            else:
                 resume_dict = {}
        except Exception as e:
            logger.warning(f"Could not fetch resume: {e}")
            resume_dict = {"experiences": [], "skills": []}

        try:
            job_data = await store.get_job_description(job_id) if job_id else None
            if hasattr(job_data, "model_dump"):
                 job_dict = job_data.model_dump()
            elif isinstance(job_data, dict):
                 job_dict = job_data
            else:
                 job_dict = {}
        except Exception as e:
            logger.warning(f"Could not fetch job: {e}")
            job_dict = {"required_skills": [], "culture_signals": [], "responsibilities": []}

        await self.report_progress(30, "Processing skill gaps")

        # Normalize skill gaps to list of strings
        skill_gaps = []
        if isinstance(skill_gaps_input, list):
            for gap in skill_gaps_input:
                if isinstance(gap, str):
                    skill_gaps.append(gap)
                elif isinstance(gap, dict):
                    skill_gaps.append(gap.get("skill_name", ""))
        skill_gaps = [g for g in skill_gaps if g]

        await self.report_progress(50, "Generating interview prep with LLM")

        # Use LlamaIndex LLM to generate comprehensive interview prep
        try:
            llamaindex_service = await get_llamaindex_service()

            llm_result = await llamaindex_service.generate_full_interview_prep(
                resume_data=resume_dict,
                job_data=job_dict,
                skill_gaps=skill_gaps,
            )
        except Exception as e:
            logger.warning(f"LLM interview prep generation failed: {e}")
            job_title = job_dict.get("title", "this role")
            # Generate fallback interview prep content (UK/EU focused)
            llm_result = {
                "behavioral_questions": [
                    {
                        "question": "Tell me about a challenging project you worked on and how you handled it.",
                        "why_asked": "Competency-based question assessing problem-solving and resilience (common in UK interviews)",
                        "suggested_answer": "Use the STAR method: describe the Situation, Task, Action, and Result. UK interviewers specifically look for this structure.",
                        "star_example": {
                            "situation": "Describe a specific challenging project",
                            "task": "Explain your responsibilities",
                            "action": "Detail the steps you took",
                            "result": "Share the positive outcome with metrics if possible (e.g., £X saved, Y% improvement)"
                        }
                    },
                    {
                        "question": "Describe a time when you had to work with a difficult team member.",
                        "why_asked": "Evaluates teamwork and conflict resolution skills - highly valued by UK employers",
                        "suggested_answer": "Focus on how you maintained professionalism and found common ground. UK employers value collaborative approaches."
                    }
                ],
                "technical_questions": [
                    {
                        "question": f"What relevant experience do you have for {job_title}?",
                        "why_asked": "Assesses role fit and technical background",
                        "suggested_answer": "Highlight your most relevant skills and experiences, quantifying achievements where possible."
                    }
                ],
                "culture_fit_questions": [
                    {
                        "question": "Why are you interested in this role and our organisation?",
                        "why_asked": "Gauges motivation and cultural alignment - UK employers value research into the company",
                        "suggested_answer": "Connect your career goals with the company's mission, values, and the role's responsibilities. Show you've researched the organisation."
                    }
                ],
                "weakness_responses": [
                    {
                        "weakness": "Area for improvement",
                        "framing": "Frame as an opportunity for growth",
                        "improvement_plan": "Describe concrete steps you're taking to improve, such as courses or certifications"
                    }
                ],
                "questions_to_ask": [
                    "What does success look like in this role after the first 90 days?",
                    "What are the team's current priorities and challenges?",
                    "What learning and development opportunities are available?",
                    "What's the approach to hybrid or flexible working?"
                ],
                "talking_points": [
                    "Emphasize your relevant experience and skills with quantified achievements",
                    "Show enthusiasm for the company and role",
                    "Demonstrate your problem-solving approach using specific examples"
                ]
            }

        await self.report_progress(75, "Building interview question objects")

        all_questions = []

        # Process behavioral questions
        for q_data in llm_result.get("behavioral_questions", []):
            if not q_data.get("question"):
                continue

            star_example = None
            star_data = q_data.get("star_example")
            if star_data and isinstance(star_data, dict):
                star_example = STARExample(
                    situation=star_data.get("situation", ""),
                    task=star_data.get("task", ""),
                    action=star_data.get("action", ""),
                    result=star_data.get("result", "")
                )

            all_questions.append(InterviewQuestion(
                id=str(uuid4()),
                question=q_data.get("question", ""),
                category=QuestionCategory.BEHAVIORAL,
                difficulty=Difficulty.MEDIUM,
                why_asked=q_data.get("why_asked", "Assesses behavioral competencies"),
                suggested_answer=q_data.get("suggested_answer", ""),
                star_example=star_example,
                related_experience=None
            ))

        # Process technical questions
        for q_data in llm_result.get("technical_questions", []):
            if not q_data.get("question"):
                continue

            difficulty = self._map_difficulty(q_data.get("difficulty", "medium"))

            all_questions.append(InterviewQuestion(
                id=str(uuid4()),
                question=q_data.get("question", ""),
                category=QuestionCategory.TECHNICAL,
                difficulty=difficulty,
                why_asked=q_data.get("why_asked", "Tests technical knowledge"),
                suggested_answer=q_data.get("suggested_answer", ""),
                star_example=None,
                related_experience=None
            ))

        # Process culture fit questions
        for q_data in llm_result.get("culture_fit_questions", []):
            if not q_data.get("question"):
                continue

            all_questions.append(InterviewQuestion(
                id=str(uuid4()),
                question=q_data.get("question", ""),
                category=QuestionCategory.CULTURE_FIT,
                difficulty=Difficulty.EASY,
                why_asked=q_data.get("why_asked", "Assesses cultural fit"),
                suggested_answer=q_data.get("suggested_answer", ""),
                star_example=None,
                related_experience=None
            ))

        await self.report_progress(85, "Building weakness responses")

        # Process weakness responses
        weakness_responses = []
        for w_data in llm_result.get("weakness_responses", []):
            if not w_data.get("weakness"):
                continue

            weakness_responses.append(WeaknessResponse(
                weakness=w_data.get("weakness", ""),
                honest_response=w_data.get("honest_response", ""),
                mitigation=w_data.get("mitigation", "")
            ))

        # If no weakness responses from LLM but we have skill gaps, generate basic ones
        if not weakness_responses and skill_gaps:
            for skill in skill_gaps[:3]:
                weakness_responses.append(WeaknessResponse(
                    weakness=f"Limited experience with {skill}",
                    honest_response=f"I acknowledge that {skill} is an area where I'm still developing expertise.",
                    mitigation=f"I'm actively working to improve my {skill} skills through learning and practice."
                ))

        await self.report_progress(95, "Finalizing interview prep")

        # Get questions to ask and talking points
        questions_to_ask = llm_result.get("questions_to_ask", [])
        if not isinstance(questions_to_ask, list):
            questions_to_ask = []

        talking_points = llm_result.get("talking_points", [])
        if not isinstance(talking_points, list):
            talking_points = []

        await self.report_progress(100, "Complete")

        return {
            "session_id": session_id,
            "job_id": job_id,
            "questions": [q.model_dump(mode='json') for q in all_questions],
            "talking_points": talking_points,
            "weakness_responses": [w.model_dump(mode='json') for w in weakness_responses],
            "questions_to_ask": questions_to_ask
        }

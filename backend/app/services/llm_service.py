"""
LLM Service.

Wrapper for OpenAI GPT-5.2 Thinking model with structured output support.
"""

import json
import logging
from typing import Any, Dict, Optional, Type, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMService:
    """OpenAI GPT-5.2 Thinking wrapper with structured output support."""

    def __init__(self):
        """Initialize LLM service."""
        self._client: Optional[AsyncOpenAI] = None

    def _get_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            settings = get_settings()
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        Generate completion from prompt.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Generated text
        """
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            settings = get_settings()
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"LLM completion error: {e}")
            raise

    async def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Generate JSON completion.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature (lower for JSON)
            max_tokens: Maximum tokens

        Returns:
            Parsed JSON dict
        """
        json_system = (system_prompt or "") + "\n\nRespond only with valid JSON."

        response = await self.complete(
            prompt=prompt,
            system_prompt=json_system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Extract JSON from response (handle markdown code blocks)
        json_str = response.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]

        try:
            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Response was: {response}")
            raise ValueError(f"Invalid JSON in LLM response: {e}")

    async def complete_structured(
        self,
        prompt: str,
        output_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> T:
        """
        Generate structured output matching Pydantic schema.

        Args:
            prompt: User prompt
            output_schema: Pydantic model class for output
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Validated Pydantic model instance
        """
        # Build schema-aware system prompt
        schema_json = json.dumps(output_schema.model_json_schema(), indent=2)

        full_system = f"""
{system_prompt or "You are a helpful assistant."}

You must respond with valid JSON that matches this schema:
```json
{schema_json}
```

Respond only with the JSON object, no additional text.
"""

        json_response = await self.complete_json(
            prompt=prompt,
            system_prompt=full_system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Validate against schema
        return output_schema.model_validate(json_response)

    async def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse resume text into structured data.

        Args:
            resume_text: Raw resume text

        Returns:
            Structured resume data
        """
        system_prompt = """
You are an expert resume parser. Extract structured information from resumes.
Focus on:
- Skills (with proficiency levels: beginner, intermediate, advanced, expert)
- Work experience (title, company, duration, key achievements)
- Education (degree, institution, year)
- Certifications

Categorize skills into: programming, framework, tool, soft_skill, domain, certification, language
"""

        prompt = f"""
Parse the following resume and extract structured information:

<resume>
{resume_text}
</resume>

Return a JSON object with:
- skills: array of {{name, category, level, years_experience}}
- experiences: array of {{title, company, duration, description, skills_used}}
- education: array of {{degree, institution, year, field_of_study}}
- certifications: array of strings
- summary: brief professional summary
"""

        return await self.complete_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,  # Low temperature for accuracy
        )

    async def parse_job_description(self, jd_text: str) -> Dict[str, Any]:
        """
        Parse job description into structured data.

        Args:
            jd_text: Raw job description text

        Returns:
            Structured job description data
        """
        system_prompt = """
You are an expert job description analyzer. Extract structured information from job postings.
Focus on:
- Job title and company
- Required skills (must-have)
- Nice-to-have skills
- Experience requirements
- Education requirements
- Key responsibilities
- Culture signals
"""

        prompt = f"""
Parse the following job description and extract structured information:

<job_description>
{jd_text}
</job_description>

Return a JSON object with:
- title: job title
- company: company name (if mentioned)
- required_skills: array of {{name, category, level}}
- nice_to_have_skills: array of {{name, category, level}}
- experience_years_min: minimum years required (integer or null)
- experience_years_max: maximum years (integer or null)
- education_requirements: array of strings
- responsibilities: array of strings
- culture_signals: array of strings indicating company culture
"""

        return await self.complete_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
        )

    async def generate_recommendations(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
        skill_gaps: list,
    ) -> Dict[str, Any]:
        """
        Generate recommendations for improving job fit.

        Args:
            resume_data: Parsed resume
            job_data: Parsed job description
            skill_gaps: List of missing skills

        Returns:
            Recommendations
        """
        system_prompt = """
You are a career advisor. Provide actionable recommendations to help candidates
improve their fit for specific jobs. Be specific and practical.
"""

        prompt = f"""
Based on the following analysis, provide recommendations:

Resume Summary:
{json.dumps(resume_data, indent=2)}

Target Job:
{json.dumps(job_data, indent=2)}

Skill Gaps:
{json.dumps(skill_gaps, indent=2)}

Provide recommendations as JSON with:
- recommendations: array of {{
    id: unique id,
    category: "skill_gap" | "resume_improvement" | "experience_highlight" | "certification" | "networking",
    priority: "high" | "medium" | "low",
    title: short title,
    description: detailed description,
    action_items: array of specific actions,
    estimated_time: time to implement (e.g., "2-4 weeks"),
    resources: array of helpful resources
  }}
- priority_order: array of recommendation IDs in priority order
- estimated_improvement: estimated fit score improvement (0-100)
"""

        return await self.complete_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
        )

    async def generate_interview_questions(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
        skill_gaps: list,
    ) -> Dict[str, Any]:
        """
        Generate likely interview questions and suggested answers.

        Args:
            resume_data: Parsed resume
            job_data: Parsed job description
            skill_gaps: List of missing skills

        Returns:
            Interview preparation content
        """
        system_prompt = """
You are an expert interview coach. Generate likely interview questions based on
the job requirements and candidate's background. Provide suggested answers that
leverage the candidate's actual experience.
"""

        prompt = f"""
Generate interview preparation content based on:

Candidate Background:
{json.dumps(resume_data, indent=2)}

Target Job:
{json.dumps(job_data, indent=2)}

Known Gaps to Address:
{json.dumps(skill_gaps, indent=2)}

Provide as JSON:
- questions: array of {{
    id: unique id,
    question: the question,
    category: "behavioral" | "technical" | "situational" | "culture_fit",
    difficulty: "easy" | "medium" | "hard",
    why_asked: why interviewer asks this,
    suggested_answer: tailored answer using candidate's experience,
    star_example: {{situation, task, action, result}} if behavioral,
    related_experience: which experience to reference
  }}
- talking_points: array of key points to emphasize
- weakness_responses: array of {{weakness, honest_response, mitigation}}
- questions_to_ask: array of good questions for candidate to ask
"""

        return await self.complete_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
        )


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get singleton LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

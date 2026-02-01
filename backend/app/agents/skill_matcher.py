"""
Skill Matcher Agent.

Matches resume skills against job requirements to calculate fit scores,
identify skill gaps, and determine transferable skills using LLM.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from app.agents.base_agent import BaseAgent
from app.config import get_settings
from app.models import (
    Difficulty,
    JobMatch,
    MissingSkill,
    SkillLevel,
    SkillMatch,
)
from app.services.llamaindex_service import get_llamaindex_service
from app.services.neo4j_store import get_neo4j_store

logger = logging.getLogger(__name__)


class SkillMatcherInput(BaseModel):
    """Input schema for skill matcher."""
    session_id: str
    resume_id: str
    job_id: str


class SkillMatcherOutput(BaseModel):
    """Output schema for skill matcher."""
    job_match: JobMatch


# Skill level numeric mapping for comparison
SKILL_LEVEL_VALUES = {
    SkillLevel.BEGINNER: 1,
    SkillLevel.INTERMEDIATE: 2,
    SkillLevel.ADVANCED: 3,
    SkillLevel.EXPERT: 4,
}


class SkillMatcherAgent(BaseAgent):
    """
    Agent for matching resume skills against job requirements.

    Uses LLM to:
    - Calculate overall fit score
    - Identify skill gaps with difficulty assessment
    - Find transferable skills
    - Perform semantic skill matching

    Works for any job type - not limited to tech roles.
    """

    @property
    def name(self) -> str:
        return "skill_matcher"

    @property
    def description(self) -> str:
        return "Matches resume skills against job requirements to calculate fit scores, identify skill gaps, and determine transferable skills using LLM-based semantic analysis."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return SkillMatcherInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return SkillMatcherOutput

    async def health_check(self) -> bool:
        """Check if the agent is ready to process requests."""
        try:
            store = get_neo4j_store()
            llamaindex_service = await get_llamaindex_service()
            return store is not None and llamaindex_service is not None
        except Exception as e:
            logger.warning(f"Health check failed for {self.name}: {e}")
            return False

    def _compare_skill_levels(
        self,
        resume_level: SkillLevel,
        required_level: Optional[SkillLevel]
    ) -> str:
        """
        Compare resume skill level to required level.

        Returns:
            "exact", "partial", or "exceeds"
        """
        if required_level is None:
            return "exact"

        resume_value = SKILL_LEVEL_VALUES[resume_level]
        required_value = SKILL_LEVEL_VALUES[required_level]

        if resume_value > required_value:
            return "exceeds"
        elif resume_value == required_value:
            return "exact"
        else:
            return "partial"

    async def _semantic_skill_match(
        self,
        resume_skills: Dict[str, Any],
        job_skill_name: str,
        resume_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Find semantically similar skills using DIRECT Neo4j vector search.

        No longer uses LlamaIndex - queries Neo4j directly for graph-aware matching.
        This is more efficient because it combines vector similarity with graph
        traversal in a single Cypher query.

        Args:
            resume_skills: Dict of resume skills (name.lower() -> skill dict)
            job_skill_name: Name of required job skill
            resume_id: Resume ID to search within

        Returns:
            Matching resume skill dict or None
        """
        try:
            from app.services.embedding import get_embedding_service

            settings = get_settings()
            embedding_service = get_embedding_service()
            neo4j_store = get_neo4j_store()

            # Generate embedding for job skill
            job_skill_embedding = await embedding_service.embed(f"Skill: {job_skill_name}")

            # Direct Neo4j vector search (graph-aware)
            similar_skills = await neo4j_store.find_similar_resume_skills(
                job_skill_embedding=job_skill_embedding,
                resume_id=resume_id,
                threshold=settings.vector_similarity_threshold,
                limit=1
            )

            if similar_skills:
                best_match = similar_skills[0]
                matched_skill_name = best_match.get("skill_name", "")

                logger.info(
                    f"Neo4j semantic match: '{job_skill_name}' → '{matched_skill_name}' "
                    f"(score: {best_match.get('score', 0):.2f})"
                )

                # Return the resume skill data from our dict
                if matched_skill_name.lower() in resume_skills:
                    return resume_skills[matched_skill_name.lower()]

                # Return from Neo4j result if not in dict
                return {
                    "name": matched_skill_name,
                    "level": best_match.get("level", "intermediate"),
                    "category": best_match.get("category"),
                }

            return None

        except Exception as e:
            logger.warning(f"Neo4j semantic skill matching failed: {e}")
            return None

    async def _get_skill_analysis(
        self,
        missing_skills: List[str],
        resume_skills: List[str],
        job_title: str,
        llamaindex_service,
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze skill gaps and transferable skills.

        Args:
            missing_skills: List of missing skill names
            resume_skills: List of resume skill names
            job_title: Target job title
            llamaindex_service: LlamaIndex service instance

        Returns:
            Dict with difficulty assessments and transferable skills
        """
        try:
            prompt = f"""Analyze these skills for a candidate applying to a {job_title} position.

MISSING SKILLS (skills the candidate needs to learn):
{', '.join(missing_skills) if missing_skills else 'None'}

CANDIDATE'S CURRENT SKILLS:
{', '.join(resume_skills) if resume_skills else 'None'}

Provide a JSON response with:
1. "skill_difficulties": object mapping each missing skill to difficulty ("easy", "medium", "hard")
   - Consider how long it typically takes to learn each skill
   - Consider prerequisites and complexity
2. "transferable_skills": array of general skills the candidate has that would help in this role
   - Based on their current skills, what broader competencies do they have?
   - Examples: "problem-solving", "data analysis", "system design", "communication"

Response format:
{{
  "skill_difficulties": {{"skill_name": "easy|medium|hard", ...}},
  "transferable_skills": ["skill1", "skill2", ...]
}}"""

            result = await llamaindex_service.complete_json(prompt)
            return result

        except Exception as e:
            logger.warning(f"LLM skill analysis failed: {e}")
            return {"skill_difficulties": {}, "transferable_skills": []}

    def _calculate_experience_match(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> float:
        """Calculate experience match score."""
        experiences = resume_data.get("experiences", [])
        total_months = 0

        for exp in experiences:
            months = exp.get("duration_months")
            if months:
                total_months += months
            else:
                duration = exp.get("duration", "")
                if "present" in duration.lower():
                    total_months += 24
                else:
                    total_months += 12

        total_years = total_months / 12
        required_years = job_data.get("experience_years_min", 0) or 0

        if required_years == 0:
            return 100.0

        if total_years >= required_years:
            return 100.0
        elif total_years >= required_years * 0.8:
            return 90.0
        elif total_years >= required_years * 0.6:
            return 75.0
        elif total_years >= required_years * 0.4:
            return 50.0
        else:
            return max(25.0, (total_years / required_years) * 100)

    def _calculate_education_match(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> float:
        """Calculate education match score."""
        education_reqs = job_data.get("education_requirements", [])

        if not education_reqs:
            return 100.0

        resume_education = resume_data.get("education", [])

        if not resume_education:
            return 50.0

        degree_levels = {
            "phd": 5, "doctorate": 5,
            "master": 4, "mba": 4,
            "bachelor": 3,
            "associate": 2,
            "diploma": 1,
        }

        max_resume_level = 0
        for edu in resume_education:
            degree = edu.get("degree", "").lower()
            for level_name, level_value in degree_levels.items():
                if level_name in degree:
                    max_resume_level = max(max_resume_level, level_value)
                    break

        required_level = 0
        for req in education_reqs:
            req_lower = str(req).lower()
            for level_name, level_value in degree_levels.items():
                if level_name in req_lower:
                    required_level = max(required_level, level_value)
                    break

        if required_level == 0:
            return 100.0

        if max_resume_level >= required_level:
            return 100.0
        elif max_resume_level >= required_level - 1:
            return 80.0
        else:
            return 50.0

    async def _execute(self, input_data: Any) -> Dict[str, Any]:
        """
        Execute skill matching analysis using LLM.

        Args:
            input_data: Dict with session_id, resume_id, job_id

        Returns:
            Dict conforming to JobMatch schema
        """
        if not isinstance(input_data, dict):
            raise ValueError("Input must be a dictionary")

        session_id = input_data.get("session_id")
        resume_id = input_data.get("resume_id")
        job_id = input_data.get("job_id")

        if not all([session_id, resume_id, job_id]):
            raise ValueError("Missing required fields: session_id, resume_id, job_id")

        await self.report_progress(10, "Fetching resume data")

        store = get_neo4j_store()

        try:
            resume_data = await store.get_resume(resume_id)
            if not resume_data:
                raise ValueError(f"Resume not found: {resume_id}")
            resume_dict = resume_data.model_dump() if hasattr(resume_data, 'model_dump') else dict(resume_data)
        except Exception as e:
            logger.error(f"Error fetching resume: {e}")
            return self._create_minimal_result(resume_id, job_id)

        await self.report_progress(30, "Fetching job data")

        try:
            job_data = await store.get_job_description(job_id)
            if not job_data:
                raise ValueError(f"Job description not found: {job_id}")
            job_dict = job_data.model_dump() if hasattr(job_data, 'model_dump') else dict(job_data)
        except Exception as e:
            logger.error(f"Error fetching job: {e}")
            return self._create_minimal_result(resume_id, job_id)

        await self.report_progress(50, "Matching skills")

        # Get resume skills
        resume_skills = {}
        for skill in resume_dict.get("skills", []):
            name = skill.get("name", "").lower()
            if name:
                resume_skills[name] = skill

        # Get required and nice-to-have skills
        required_skills = {}
        for skill in job_dict.get("required_skills", []):
            name = skill.get("name", "").lower()
            if name:
                required_skills[name] = {**skill, "importance": "must_have"}

        nice_to_have_skills = {}
        for skill in job_dict.get("nice_to_have_skills", []):
            name = skill.get("name", "").lower()
            if name:
                nice_to_have_skills[name] = {**skill, "importance": "nice_to_have"}

        # Find matching skills
        # Process required skills first to ensure they take priority over nice-to-have
        matching_skills = []
        matched_names = set()

        # Combine skills with required taking priority (required skills won't be overwritten)
        all_job_skills = {**nice_to_have_skills, **required_skills}

        for skill_name, job_skill in all_job_skills.items():
            if skill_name in resume_skills:
                resume_skill = resume_skills[skill_name]

                resume_level = resume_skill.get("level", "intermediate")
                try:
                    resume_level = SkillLevel(resume_level)
                except ValueError:
                    resume_level = SkillLevel.INTERMEDIATE

                required_level = job_skill.get("level")
                if required_level:
                    try:
                        required_level = SkillLevel(required_level)
                    except ValueError:
                        required_level = None

                match_quality = self._compare_skill_levels(resume_level, required_level)

                matching_skills.append(SkillMatch(
                    skill_name=skill_name.title(),
                    resume_level=resume_level,
                    required_level=required_level,
                    match_quality=match_quality
                ))

                matched_names.add(skill_name)

        await self.report_progress(60, "Performing semantic skill matching")

        # Try semantic matching for unmatched skills (PARALLELIZED)
        # Now uses direct Neo4j vector search instead of LlamaIndex
        try:
            # Collect unmatched skills for parallel processing
            unmatched_skills = [
                skill_name for skill_name in all_job_skills.keys()
                if skill_name not in matched_names
            ]

            if unmatched_skills:
                # Create parallel tasks for all semantic matches (direct Neo4j)
                semantic_tasks = [
                    self._semantic_skill_match(
                        resume_skills, skill_name, resume_id
                    )
                    for skill_name in unmatched_skills
                ]

                # Execute all semantic matching in parallel
                semantic_results = await asyncio.gather(*semantic_tasks, return_exceptions=True)

                # Process results
                for skill_name, semantic_match in zip(unmatched_skills, semantic_results):
                    if isinstance(semantic_match, Exception):
                        logger.debug(f"Semantic match failed for {skill_name}: {semantic_match}")
                        continue

                    if semantic_match:
                        resume_level = semantic_match.get("level", "intermediate")
                        try:
                            resume_level = SkillLevel(resume_level)
                        except ValueError:
                            resume_level = SkillLevel.INTERMEDIATE

                        matching_skills.append(SkillMatch(
                            skill_name=skill_name.title(),
                            resume_level=resume_level,
                            required_level=None,
                            match_quality="partial",
                        ))
                        matched_names.add(skill_name)

        except Exception as e:
            logger.warning(f"Semantic matching phase failed: {e}")

        await self.report_progress(70, "Analyzing skill gaps with LLM")

        # Get missing skill names
        missing_skill_names = []
        for skill_name in required_skills:
            if skill_name not in matched_names:
                missing_skill_names.append(skill_name.title())
        for skill_name in nice_to_have_skills:
            if skill_name not in matched_names:
                missing_skill_names.append(skill_name.title())

        # Use LLM to analyze skill difficulties and transferable skills
        resume_skill_names = [s.get("name", "") for s in resume_dict.get("skills", [])]
        job_title = job_dict.get("title", "the target role")

        try:
            llamaindex_service = await get_llamaindex_service()
            skill_analysis = await self._get_skill_analysis(
                missing_skill_names, resume_skill_names, job_title, llamaindex_service
            )
        except Exception as e:
            logger.warning(f"Skill analysis failed: {e}")
            skill_analysis = {"skill_difficulties": {}, "transferable_skills": []}

        skill_difficulties = skill_analysis.get("skill_difficulties", {})
        transferable_skills = skill_analysis.get("transferable_skills", [])

        # Build missing skills with LLM-determined difficulty
        missing_skills = []
        for skill_name in required_skills:
            if skill_name not in matched_names:
                difficulty_str = skill_difficulties.get(skill_name.title(), "medium")
                try:
                    difficulty = Difficulty(difficulty_str.lower())
                except ValueError:
                    difficulty = Difficulty.MEDIUM

                missing_skills.append(MissingSkill(
                    skill_name=skill_name.title(),
                    importance="must_have",
                    difficulty_to_acquire=difficulty
                ))

        for skill_name in nice_to_have_skills:
            if skill_name not in matched_names:
                difficulty_str = skill_difficulties.get(skill_name.title(), "medium")
                try:
                    difficulty = Difficulty(difficulty_str.lower())
                except ValueError:
                    difficulty = Difficulty.MEDIUM

                missing_skills.append(MissingSkill(
                    skill_name=skill_name.title(),
                    importance="nice_to_have",
                    difficulty_to_acquire=difficulty
                ))

        await self.report_progress(80, "Calculating scores")

        # Calculate scores
        total_required = len(required_skills)
        matched_required = len([m for m in matching_skills if m.skill_name.lower() in required_skills])

        if total_required > 0:
            skill_match_score = (matched_required / total_required) * 100
        else:
            skill_match_score = 100.0 if matching_skills else 50.0

        exceeds_count = len([m for m in matching_skills if m.match_quality == "exceeds"])
        partial_count = len([m for m in matching_skills if m.match_quality == "partial"])

        if matching_skills:
            quality_bonus = (exceeds_count * 5 - partial_count * 5) / len(matching_skills)
            skill_match_score = min(100, max(0, skill_match_score + quality_bonus))

        experience_match_score = self._calculate_experience_match(resume_dict, job_dict)
        education_match_score = self._calculate_education_match(resume_dict, job_dict)

        fit_score = (
            skill_match_score * 0.50 +
            experience_match_score * 0.35 +
            education_match_score * 0.15
        )

        await self.report_progress(100, "Complete")

        return {
            "job_id": job_id,
            "resume_id": resume_id,
            "job_title": job_dict.get("title", ""),
            "company": job_dict.get("company"),
            "fit_score": round(fit_score, 1),
            "skill_match_score": round(skill_match_score, 1),
            "experience_match_score": round(experience_match_score, 1),
            "education_match_score": round(education_match_score, 1),
            "matching_skills": [m.model_dump() for m in matching_skills],
            "missing_skills": [m.model_dump() for m in missing_skills],
            "transferable_skills": transferable_skills
        }

    def _create_minimal_result(self, resume_id: str, job_id: str) -> Dict[str, Any]:
        """Create a minimal result when data is not available."""
        return {
            "job_id": job_id,
            "resume_id": resume_id,
            "job_title": "",
            "company": None,
            "fit_score": 0.0,
            "skill_match_score": 0.0,
            "experience_match_score": 0.0,
            "education_match_score": 0.0,
            "matching_skills": [],
            "missing_skills": [],
            "transferable_skills": []
        }

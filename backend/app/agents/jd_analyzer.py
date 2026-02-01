"""
Job Description Analyzer Agent.

Extracts structured data from job descriptions including requirements,
skills, responsibilities, and culture signals using LLM-based parsing.
"""

import asyncio
import logging
from typing import Any, Dict, List, Type
from uuid import uuid4

from pydantic import BaseModel

from app.agents.base_agent import BaseAgent
from app.models import (
    ParsedJobDescription,
    Requirement,
    RequirementType,
    Skill,
    SkillCategory,
    SkillLevel,
)
from app.services.llamaindex_service import get_llamaindex_service
from app.services.neo4j_store import get_neo4j_store

logger = logging.getLogger(__name__)


class JDAnalyzerInput(BaseModel):
    """Input schema for JD analyzer."""
    jd_text: str


class JDAnalyzerOutput(BaseModel):
    """Output schema for JD analyzer."""
    job_description: ParsedJobDescription


class JDAnalyzerAgent(BaseAgent):
    """
    Agent for analyzing job descriptions and extracting structured requirements.

    Uses LLM to extract:
    - Job title and company
    - Required skills (must-have)
    - Nice-to-have skills
    - Experience requirements
    - Education requirements
    - Responsibilities
    - Culture signals

    Works for any job type - not limited to tech roles.
    """

    @property
    def name(self) -> str:
        return "jd_analyzer"

    @property
    def description(self) -> str:
        return "Extracts structured data from job descriptions including requirements, skills, responsibilities, and culture signals using LLM-based parsing."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return JDAnalyzerInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return JDAnalyzerOutput

    async def health_check(self) -> bool:
        """Check if the agent is ready to process requests."""
        try:
            llamaindex_service = await get_llamaindex_service()
            return llamaindex_service is not None
        except Exception as e:
            logger.warning(f"Health check failed for {self.name}: {e}")
            return False

    async def _deduplicate_skills_with_embeddings(
        self,
        skills: List[Skill],
        threshold: float = 0.92
    ) -> List[Skill]:
        """
        Deduplicate JD skills using embedding similarity as fallback.

        Ensures JD skills are normalized to match existing skills in the graph,
        which improves matching accuracy with resume skills.

        Args:
            skills: List of extracted skills
            threshold: Minimum similarity score for deduplication (0-1)

        Returns:
            List of deduplicated skills with normalized names
        """
        if not skills:
            return skills

        try:
            from app.services.embedding import get_embedding_service
            embedding_service = get_embedding_service()
            neo4j_store = get_neo4j_store()

            async def process_skill(skill: Skill) -> Skill:
                """Check if skill matches an existing one via embedding similarity."""
                try:
                    embedding = await embedding_service.embed(f"Skill: {skill.name}")
                    similar = await neo4j_store.find_similar_skills_by_embedding(
                        embedding=embedding,
                        threshold=threshold,
                        limit=1
                    )

                    if similar and similar[0]["score"] > threshold:
                        existing = similar[0]
                        logger.debug(
                            f"JD skill normalized: '{skill.name}' -> '{existing['name']}' "
                            f"(similarity: {existing['score']:.3f})"
                        )
                        return Skill(
                            name=existing["name"],
                            category=SkillCategory(existing["category"]) if existing.get("category") else skill.category,
                            level=skill.level,
                            years_experience=skill.years_experience
                        )
                    return skill
                except Exception as e:
                    logger.warning(f"Error normalizing JD skill '{skill.name}': {e}")
                    return skill

            # Process all skills in parallel
            deduplicated = await asyncio.gather(*[process_skill(s) for s in skills])

            # Remove duplicates created by normalization
            seen_names = set()
            unique_skills = []
            for skill in deduplicated:
                name_lower = skill.name.lower()
                if name_lower not in seen_names:
                    seen_names.add(name_lower)
                    unique_skills.append(skill)

            logger.info(
                f"JD skill deduplication: {len(skills)} -> {len(unique_skills)} skills"
            )
            return unique_skills

        except Exception as e:
            logger.warning(f"JD embedding deduplication failed: {e}")
            return skills

    async def _execute(self, input_data: Any) -> Dict[str, Any]:
        """
        Execute job description analysis using LLM.

        Args:
            input_data: JD text string or dict with jd_text

        Returns:
            Dict conforming to ParsedJobDescription schema
        """
        # Handle both string and dict input
        if isinstance(input_data, str):
            jd_text = input_data
        elif isinstance(input_data, dict):
            jd_text = input_data.get("jd_text", input_data.get("text", ""))
        else:
            jd_text = str(input_data)

        # Validate input
        if not jd_text or not jd_text.strip():
            raise ValueError("Job description text is empty")

        jd_text = jd_text.strip()

        if len(jd_text) < 20:
            raise ValueError("Job description text is too short")

        await self.report_progress(10, "Analyzing job description with LlamaIndex LLM")

        # Use LlamaIndex LLM to extract structured data
        llamaindex_service = await get_llamaindex_service()

        try:
            llm_result = await llamaindex_service.parse_job_description(jd_text)
        except Exception as e:
            logger.warning(f"LLM parsing failed: {e}")
            # Return minimal result on failure
            llm_result = {
                "title": "",
                "company": None,
                "required_skills": [],
                "nice_to_have_skills": [],
                "experience_years_min": None,
                "experience_years_max": None,
                "education_requirements": [],
                "responsibilities": [],
                "culture_signals": []
            }

        await self.report_progress(50, "Processing requirements")

        # Extract job title from LLM output
        title = llm_result.get("title", "").strip()
        if not title:
            # Use first line as fallback
            first_line = jd_text.split("\n")[0].strip()
            title = first_line if len(first_line) < 100 else "Position"

        # Extract company from LLM output
        company = llm_result.get("company")

        await self.report_progress(60, "Processing skills")

        # Process required skills from LLM output
        required_skills = []
        for skill_data in llm_result.get("required_skills", []):
            skill_name = skill_data.get("name", "").strip()
            if not skill_name:
                continue

            # Use LLM-provided category or default
            category_str = skill_data.get("category", "domain")
            try:
                category = SkillCategory(category_str.lower())
            except ValueError:
                category = SkillCategory.DOMAIN

            # Use LLM-provided level or default
            level_str = skill_data.get("level", "intermediate")
            try:
                level = SkillLevel(level_str.lower())
            except ValueError:
                level = SkillLevel.INTERMEDIATE

            required_skills.append(Skill(
                name=skill_name,
                category=category,
                level=level,
                years_experience=None
            ))

        # Process nice-to-have skills from LLM output
        nice_to_have_skills = []
        for skill_data in llm_result.get("nice_to_have_skills", []):
            skill_name = skill_data.get("name", "").strip()
            if not skill_name:
                continue

            category_str = skill_data.get("category", "domain")
            try:
                category = SkillCategory(category_str.lower())
            except ValueError:
                category = SkillCategory.DOMAIN

            level_str = skill_data.get("level", "intermediate")
            try:
                level = SkillLevel(level_str.lower())
            except ValueError:
                level = SkillLevel.INTERMEDIATE

            nice_to_have_skills.append(Skill(
                name=skill_name,
                category=category,
                level=level,
                years_experience=None
            ))

        await self.report_progress(68, "Normalizing skills with embeddings")

        # Deduplicate skills using embedding similarity as fallback
        # This ensures JD skills match resume skills for accurate matching
        required_skills = await self._deduplicate_skills_with_embeddings(required_skills)
        nice_to_have_skills = await self._deduplicate_skills_with_embeddings(nice_to_have_skills)

        await self.report_progress(70, "Processing requirements")

        # Build requirements list from LLM output
        requirements = []

        # Add required skills as requirements
        for skill in required_skills:
            requirements.append(Requirement(
                text=f"Experience with {skill.name}",
                type=RequirementType.MUST_HAVE,
                skills=[skill.name]
            ))

        # Add nice-to-have skills as requirements
        for skill in nice_to_have_skills:
            requirements.append(Requirement(
                text=f"Knowledge of {skill.name}",
                type=RequirementType.NICE_TO_HAVE,
                skills=[skill.name]
            ))

        # Get experience requirements from LLM
        exp_years_min = llm_result.get("experience_years_min")
        exp_years_max = llm_result.get("experience_years_max")

        if exp_years_min is not None:
            requirements.append(Requirement(
                text=f"{exp_years_min}+ years of experience",
                type=RequirementType.MUST_HAVE,
                skills=[]
            ))

        await self.report_progress(80, "Processing responsibilities")

        # Process responsibilities from LLM output
        responsibilities = llm_result.get("responsibilities", [])
        if not isinstance(responsibilities, list):
            responsibilities = []
        responsibilities = [str(r) for r in responsibilities if r]

        # Add responsibilities as requirements
        for resp in responsibilities:
            requirements.append(Requirement(
                text=resp,
                type=RequirementType.RESPONSIBILITY,
                skills=[]
            ))

        await self.report_progress(90, "Processing culture signals")

        # Process education requirements from LLM output
        education_requirements = llm_result.get("education_requirements", [])
        if not isinstance(education_requirements, list):
            education_requirements = []
        education_requirements = [str(e) for e in education_requirements if e]

        # Process culture signals from LLM output
        culture_signals = llm_result.get("culture_signals", [])
        if not isinstance(culture_signals, list):
            culture_signals = []
        culture_signals = [str(s) for s in culture_signals if s]

        # Build result
        job_id = str(uuid4())

        result = {
            "id": job_id,
            "title": title,
            "company": company,
            "requirements": [r.model_dump() for r in requirements],
            "required_skills": [s.model_dump() for s in required_skills],
            "nice_to_have_skills": [s.model_dump() for s in nice_to_have_skills],
            "experience_years_min": exp_years_min,
            "experience_years_max": exp_years_max,
            "education_requirements": education_requirements,
            "responsibilities": responsibilities,
            "culture_signals": culture_signals
        }

        await self.report_progress(95, "Storing to Neo4j")

        # Store parsed job description to Neo4j graph database
        try:
            neo4j_store = get_neo4j_store()
            parsed_jd = ParsedJobDescription(
                id=job_id,
                title=title,
                company=company,
                requirements=requirements,
                required_skills=required_skills,
                nice_to_have_skills=nice_to_have_skills,
                experience_years_min=exp_years_min,
                experience_years_max=exp_years_max,
                education_requirements=education_requirements,
                responsibilities=responsibilities,
                culture_signals=culture_signals
            )
            await neo4j_store.save_job_description(parsed_jd)
            logger.info(f"Stored job description {job_id} to Neo4j")
        except Exception as e:
            logger.warning(f"Failed to store job description to Neo4j: {e}")

        # Store job skill embeddings directly in Neo4j for vector search
        # This replaces LlamaIndex vector store with direct Neo4j embedding storage
        try:
            from app.services.embedding import get_embedding_service
            embedding_service = get_embedding_service()

            skills_stored = 0
            all_skills = result.get("required_skills", []) + result.get("nice_to_have_skills", [])
            for skill in all_skills:
                skill_name = skill.get("name", "")
                if skill_name:
                    # Generate embedding for the skill
                    embedding = await embedding_service.embed(f"Skill: {skill_name}")
                    # Store directly in Neo4j on the Skill node
                    await neo4j_store.store_skill_embedding(
                        skill_name=skill_name,
                        embedding=embedding,
                        category=skill.get("category")
                    )
                    skills_stored += 1

            logger.info(f"Stored {skills_stored} skill embeddings in Neo4j for job {job_id}")
        except Exception as e:
            logger.warning(f"Failed to store skill embeddings: {e}")

        await self.report_progress(100, "Complete")

        return result

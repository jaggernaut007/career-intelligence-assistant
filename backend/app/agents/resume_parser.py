"""
Resume Parser Agent.

Extracts structured data from resume text including skills, experience,
education, and certifications using LLM-based parsing.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Type
from uuid import uuid4

from pydantic import BaseModel

from app.agents.base_agent import BaseAgent
from app.models import (
    AgentOutput,
    Education,
    Experience,
    ParsedResume,
    Skill,
    SkillCategory,
    SkillLevel,
)
from app.services.llamaindex_service import get_llamaindex_service
from app.services.neo4j_store import get_neo4j_store

logger = logging.getLogger(__name__)


class ResumeParserInput(BaseModel):
    """Input schema for resume parser."""
    resume_text: str


class ResumeParserOutput(BaseModel):
    """Output schema for resume parser."""
    resume: ParsedResume


class ResumeParserAgent(BaseAgent):
    """
    Agent for parsing resumes and extracting structured information.

    Uses LLM to extract:
    - Skills with proficiency levels
    - Work experience
    - Education history
    - Certifications

    Works for any job type - not limited to tech roles.
    """

    # PII patterns for redaction (security requirement - keep these)
    PII_PATTERNS = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        "address": r"\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)[,.]?\s*(?:[A-Za-z\s]+,?\s*)?\d{5}(?:-\d{4})?",
    }

    @property
    def name(self) -> str:
        return "resume_parser"

    @property
    def description(self) -> str:
        return "Extracts structured data from resume documents including skills, experience, education, and certifications using LLM-based parsing."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return ResumeParserInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return ResumeParserOutput

    async def health_check(self) -> bool:
        """Check if the agent is ready to process requests."""
        try:
            # Verify LlamaIndex service is available
            llamaindex_service = await get_llamaindex_service()
            return llamaindex_service is not None
        except Exception as e:
            logger.warning(f"Health check failed for {self.name}: {e}")
            return False

    def _redact_pii(self, text: str) -> tuple[str, bool]:
        """
        Redact PII from text.

        Args:
            text: Raw text potentially containing PII

        Returns:
            Tuple of (redacted_text, pii_was_found)
        """
        redacted = text
        pii_found = False

        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, redacted, re.IGNORECASE)
            if matches:
                pii_found = True
                for match in matches:
                    redacted = redacted.replace(match, f"[REDACTED_{pii_type.upper()}]")

        return redacted, pii_found

    async def _deduplicate_with_embeddings(
        self,
        skills: List[Skill],
        threshold: float = 0.92
    ) -> List[Skill]:
        """
        Deduplicate skills using embedding similarity as fallback.

        After LLM extraction, this catches any remaining duplicates that the
        LLM missed (e.g., "PostgreSQL" vs "Postgres DB") by checking embedding
        similarity against existing skills in the graph.

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
                        # Map to existing skill name and category
                        existing = similar[0]
                        logger.debug(
                            f"Normalized '{skill.name}' -> '{existing['name']}' "
                            f"(similarity: {existing['score']:.3f})"
                        )
                        return Skill(
                            name=existing["name"],
                            category=SkillCategory(existing["category"]) if existing.get("category") else skill.category,
                            level=skill.level,
                            years_experience=skill.years_experience,
                            source=skill.source
                        )
                    return skill
                except Exception as e:
                    logger.warning(f"Error normalizing skill '{skill.name}': {e}")
                    return skill

            # Process all skills in parallel for performance
            deduplicated = await asyncio.gather(*[process_skill(s) for s in skills])

            # Remove duplicates that may have been created by normalization
            seen_names = set()
            unique_skills = []
            for skill in deduplicated:
                name_lower = skill.name.lower()
                if name_lower not in seen_names:
                    seen_names.add(name_lower)
                    unique_skills.append(skill)

            logger.info(
                f"Skill deduplication: {len(skills)} -> {len(unique_skills)} skills"
            )
            return unique_skills

        except Exception as e:
            logger.warning(f"Embedding deduplication failed, returning original: {e}")
            return skills

    async def _execute(self, input_data: Any) -> Dict[str, Any]:
        """
        Execute resume parsing using LLM.

        Args:
            input_data: Resume text string or dict with resume_text

        Returns:
            Dict conforming to ParsedResume schema
        """
        # Handle both string and dict input
        if isinstance(input_data, str):
            resume_text = input_data
        elif isinstance(input_data, dict):
            resume_text = input_data.get("resume_text", "")
        else:
            resume_text = str(input_data)

        # Validate input
        if not resume_text or not resume_text.strip():
            raise ValueError("Resume text is empty")

        # Clean up malformed input
        try:
            resume_text = resume_text.encode('utf-8', errors='ignore').decode('utf-8')
        except Exception:
            pass

        resume_text = resume_text.strip()

        if len(resume_text) < 50:
            raise ValueError("Resume text is too short to parse")

        await self.report_progress(10, "Redacting PII")

        # Redact PII before processing
        redacted_text, pii_found = self._redact_pii(resume_text)

        await self.report_progress(20, "Analyzing with LlamaIndex LLM")

        # Use LlamaIndex LLM to extract structured data
        llamaindex_service = await get_llamaindex_service()

        try:
            llm_result = await llamaindex_service.parse_resume(redacted_text)
        except Exception as e:
            logger.warning(f"LLM parsing failed: {e}")
            # Return minimal result on failure
            llm_result = {"skills": [], "experiences": [], "education": [], "certifications": [], "summary": ""}

        await self.report_progress(70, "Processing extracted data")

        # Process skills from LLM output
        skills = []
        for skill_data in llm_result.get("skills", []):
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

            # Get source (explicit/implicit) - default to explicit for backwards compatibility
            source = skill_data.get("source", "explicit")
            if source not in ("explicit", "implicit"):
                source = "explicit"

            skills.append(Skill(
                name=skill_name,
                category=category,
                level=level,
                years_experience=skill_data.get("years_experience"),
                source=source
            ))

        await self.report_progress(80, "Processing experience")

        # Process experiences from LLM output
        experiences = []
        for exp_data in llm_result.get("experiences", []):
            title = exp_data.get("title", "").strip()
            company = exp_data.get("company", "").strip()

            if not title or not company:
                continue

            experiences.append(Experience(
                title=title,
                company=company,
                duration=exp_data.get("duration", "Not specified"),
                duration_months=exp_data.get("duration_months"),
                description=exp_data.get("description", ""),
                skills_used=exp_data.get("skills_used", [])
            ))

        await self.report_progress(90, "Processing education")

        # Process education from LLM output
        education = []
        for edu_data in llm_result.get("education", []):
            degree = edu_data.get("degree", "").strip()
            institution = edu_data.get("institution", "").strip()

            if not degree or not institution:
                continue

            year = edu_data.get("year")
            if isinstance(year, str):
                match = re.search(r"(\d{4})", year)
                year = int(match.group(1)) if match else None

            education.append(Education(
                degree=degree,
                institution=institution,
                year=year,
                gpa=edu_data.get("gpa"),
                field_of_study=edu_data.get("field_of_study")
            ))

        # Process certifications from LLM output
        certifications = llm_result.get("certifications", [])
        if not isinstance(certifications, list):
            certifications = []
        certifications = [str(c) for c in certifications if c]

        await self.report_progress(92, "Normalizing skills with embeddings")

        # Deduplicate skills using embedding similarity as fallback
        # This catches variations the LLM may have missed (e.g., "Postgres DB" -> "PostgreSQL")
        skills = await self._deduplicate_with_embeddings(skills)

        # Get summary from LLM
        summary = llm_result.get("summary", "")
        if len(summary) > 2000:
            summary = summary[:2000]

        # Build result
        resume_id = str(uuid4())

        result = {
            "id": resume_id,
            "skills": [s.model_dump() for s in skills],
            "experiences": [e.model_dump() for e in experiences],
            "education": [e.model_dump() for e in education],
            "certifications": certifications,
            "summary": summary,
            "contact_redacted": pii_found
        }

        await self.report_progress(95, "Storing to Neo4j")

        # Store parsed resume to Neo4j graph database
        try:
            neo4j_store = get_neo4j_store()
            parsed_resume = ParsedResume(
                id=resume_id,
                skills=skills,
                experiences=experiences,
                education=education,
                certifications=certifications,
                summary=summary,
                contact_redacted=pii_found
            )
            await neo4j_store.save_resume(parsed_resume)
            logger.info(f"Stored resume {resume_id} to Neo4j")
        except Exception as e:
            logger.warning(f"Failed to store resume to Neo4j: {e}")

        # Store skill embeddings directly in Neo4j for vector search
        # This replaces LlamaIndex vector store with direct Neo4j embedding storage
        try:
            from app.services.embedding import get_embedding_service
            embedding_service = get_embedding_service()

            skills_stored = 0
            for skill in result.get("skills", []):
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

            logger.info(f"Stored {skills_stored} skill embeddings in Neo4j for resume {resume_id}")
        except Exception as e:
            logger.warning(f"Failed to store skill embeddings: {e}")

        await self.report_progress(100, "Complete")

        return result

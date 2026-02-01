"""
Recommendation Agent.

Generates actionable recommendations for improving job fit based on
skill gaps, experience, and resume analysis using LLM.
"""

import logging
from typing import Any, Dict, List, Optional, Type
from uuid import uuid4

from pydantic import BaseModel

from app.agents.base_agent import BaseAgent
from app.models import (
    Priority,
    Recommendation,
    RecommendationCategory,
    RecommendationResult,
)
from app.services.llamaindex_service import get_llamaindex_service
from app.services.neo4j_store import get_neo4j_store

logger = logging.getLogger(__name__)


class RecommendationInput(BaseModel):
    """Input schema for recommendation agent."""
    session_id: str
    resume_id: str
    job_id: str
    skill_gaps: Optional[List[str]] = None




class RecommendationAgent(BaseAgent):
    """
    Agent for generating actionable recommendations using LLM.

    Uses LlamaIndex LLM to generate:
    - Skill gap closure strategies
    - Resume improvements
    - Experience highlighting tips
    - Certification suggestions
    - Learning resources

    Works for any job type - not limited to tech roles.
    """

    @property
    def name(self) -> str:
        return "recommendation"

    @property
    def description(self) -> str:
        return "Generates actionable recommendations for improving job fit based on skill gaps, experience, and resume analysis using LLM."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return RecommendationInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return RecommendationResult

    async def health_check(self) -> bool:
        """Check if the agent is ready to process requests."""
        try:
            llamaindex_service = await get_llamaindex_service()
            return llamaindex_service is not None
        except Exception as e:
            logger.warning(f"Health check failed for {self.name}: {e}")
            return False

    def _map_priority(self, priority_str: str) -> Priority:
        """Map string priority to Priority enum."""
        priority_lower = priority_str.lower() if priority_str else "medium"
        if "high" in priority_lower:
            return Priority.HIGH
        elif "low" in priority_lower:
            return Priority.LOW
        return Priority.MEDIUM

    def _map_category(self, title: str, skill_name: str = None) -> RecommendationCategory:
        """Map recommendation to category based on content."""
        title_lower = title.lower()
        if "resume" in title_lower or "cv" in title_lower:
            return RecommendationCategory.RESUME_IMPROVEMENT
        elif "certif" in title_lower:
            return RecommendationCategory.CERTIFICATION
        elif "experience" in title_lower or "highlight" in title_lower:
            return RecommendationCategory.EXPERIENCE_HIGHLIGHT
        elif skill_name:
            return RecommendationCategory.SKILL_GAP
        return RecommendationCategory.SKILL_GAP

    async def _execute(self, input_data: Any) -> Dict[str, Any]:
        """
        Execute recommendation generation using LLM.

        Args:
            input_data: Dict with session_id, resume_id, job_id, skill_gaps

        Returns:
            Dict conforming to RecommendationResult schema
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
            resume_dict = {"skills": [], "experiences": [], "education": [], "summary": ""}

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
             job_dict = {"required_skills": [], "responsibilities": [], "title": ""}

        await self.report_progress(30, "Preparing skill gaps data")

        # Normalize skill gaps to list of dicts
        skill_gaps = []
        if isinstance(skill_gaps_input, list):
            for gap in skill_gaps_input:
                if isinstance(gap, str):
                    skill_gaps.append({
                        "skill_name": gap,
                        "importance": "must_have",
                        "difficulty_to_acquire": "medium"
                    })
                elif isinstance(gap, dict):
                    skill_gaps.append(gap)

        await self.report_progress(50, "Generating recommendations with LLM")

        # Use LlamaIndex LLM to generate comprehensive recommendations
        try:
            llamaindex_service = await get_llamaindex_service()

            llm_result = await llamaindex_service.generate_full_recommendations(
                resume_data=resume_dict,
                job_data=job_dict,
                skill_gaps=skill_gaps,
            )
        except Exception as e:
            logger.warning(f"LLM recommendation generation failed: {e}")
            llm_result = []

        await self.report_progress(80, "Building recommendation objects")

        all_recommendations = []

        if isinstance(llm_result, list) and len(llm_result) > 0:
            for rec_data in llm_result:
                if not isinstance(rec_data, dict): continue
                
                title = rec_data.get("title", "Recommendation")
                
                # Determine category
                category_str = str(rec_data.get("category", "")).lower().replace(" ", "_")
                if "skill" in category_str: category = RecommendationCategory.SKILL_GAP
                elif "resume" in category_str: category = RecommendationCategory.RESUME_IMPROVEMENT
                elif "experience" in category_str: category = RecommendationCategory.EXPERIENCE_HIGHLIGHT
                elif "certif" in category_str: category = RecommendationCategory.CERTIFICATION
                elif "network" in category_str: category = RecommendationCategory.NETWORKING
                else: 
                     # Fallback logic based on content keywords
                     category = self._map_category(title)
                
                priority = self._map_priority(rec_data.get("priority", "medium"))

                action_items = rec_data.get("action_items", [])
                if not isinstance(action_items, list):
                    action_items = []

                # Ensure minimum 3 action items
                if len(action_items) < 3:
                     defaults = ["Research industry best practices", "Apply concept in a personal project", "Share knowledge with peers"]
                     if category == RecommendationCategory.SKILL_GAP:
                          defaults = ["Take a relevant online course", "Build a small proof-of-concept project", "Read official documentation"]
                     elif category == RecommendationCategory.RESUME_IMPROVEMENT:
                           defaults = ["Quantify achievements with metrics", "Use strong action verbs", "Tailor content to job description"]
                     
                     for item in defaults:
                         if len(action_items) >= 3: break
                         if item not in action_items:
                             action_items.append(item)
                
                rec = Recommendation(
                    id=str(uuid4()),
                    category=category,
                    priority=priority,
                    title=title,
                    description=rec_data.get("description", ""),
                    action_items=action_items,
                    estimated_time=rec_data.get("estimated_time", "2-4 weeks"),
                    resources=rec_data.get("resources", [])
                )
                all_recommendations.append(rec)
        else:
             # Fallback logic if LLM failed or returned empty (UK/EU focused)
             logger.warning("LLM returned empty list, using fallback recommendations")
             for gap in skill_gaps[:3]:
                skill_name = gap.get("skill_name", "Unknown skill")
                all_recommendations.append(Recommendation(
                    id=str(uuid4()),
                    category=RecommendationCategory.SKILL_GAP,
                    priority=Priority.HIGH,
                    title=f"Develop {skill_name} skills",
                    description=f"Focus on building practical experience with {skill_name}. UK/EU employers value demonstrable skills.",
                    action_items=[f"Take a FutureLearn or Coursera course on {skill_name}", "Build a portfolio project demonstrating this skill", "Consider relevant UK certifications"],
                    estimated_time="2-4 weeks",
                    resources=["FutureLearn", "LinkedIn Learning", "Open University"]
                ))

        await self.report_progress(90, "Finalizing recommendations")

        # Sort by priority
        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        all_recommendations.sort(key=lambda r: priority_order.get(r.priority, 1))

        # Limit to top 7 recommendations to meet constraints
        all_recommendations = all_recommendations[:7]

        # Create priority order list
        priority_order_list = [r.id for r in all_recommendations]

        # Calculate estimated improvement based on recommendations
        high_priority_count = len([r for r in all_recommendations if r.priority == Priority.HIGH])
        estimated_improvement = min(100, high_priority_count * 15 + len(all_recommendations) * 3)

        await self.report_progress(100, "Complete")

        return {
            "session_id": session_id,
            "job_id": job_id,
            "recommendations": [r.model_dump(mode='json') for r in all_recommendations],
            "priority_order": priority_order_list,
            "estimated_improvement": estimated_improvement
        }

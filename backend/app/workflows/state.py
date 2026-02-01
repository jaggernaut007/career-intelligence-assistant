"""
Workflow State for Career Analysis.

Defines shared state accessible by all workflow steps via Context.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class WorkflowState(BaseModel):
    """
    Shared state accessible by all workflow steps.

    This state is stored in-memory via LlamaIndex Context and can be
    accessed/modified by any step in the workflow. It provides efficient
    state sharing without Neo4j round-trips for intermediate data.
    """

    # Session info
    session_id: str = ""
    resume_id: str = ""
    job_ids: List[str] = Field(default_factory=list)

    # Phase 1 results (parsed documents)
    parsed_resume: Optional[Dict[str, Any]] = None
    parsed_jobs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Phase 2 results (skill matching)
    skill_matches: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    all_skill_gaps: List[str] = Field(default_factory=list)

    # Phase 3 results (analysis)
    recommendations: Optional[Dict[str, Any]] = None
    interview_prep: Optional[Dict[str, Any]] = None
    market_insights: Optional[Dict[str, Any]] = None

    # Tracking
    completed_steps: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True

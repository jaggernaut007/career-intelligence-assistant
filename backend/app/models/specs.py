"""
Pydantic Model Specifications for Career Intelligence Assistant.

This file defines all data models/contracts BEFORE implementation.
These specs are the source of truth for API contracts.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================

class SkillLevel(str, Enum):
    """Proficiency level for a skill."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SkillCategory(str, Enum):
    """Category of skill."""
    PROGRAMMING = "programming"
    FRAMEWORK = "framework"
    TOOL = "tool"
    SOFT_SKILL = "soft_skill"
    DOMAIN = "domain"
    CERTIFICATION = "certification"
    LANGUAGE = "language"


class RequirementType(str, Enum):
    """Type of job requirement."""
    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"
    RESPONSIBILITY = "responsibility"


class AgentStatus(str, Enum):
    """Status of an agent during processing."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RecommendationCategory(str, Enum):
    """Category of recommendation."""
    SKILL_GAP = "skill_gap"
    RESUME_IMPROVEMENT = "resume_improvement"
    EXPERIENCE_HIGHLIGHT = "experience_highlight"
    CERTIFICATION = "certification"
    NETWORKING = "networking"


class Priority(str, Enum):
    """Priority level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QuestionCategory(str, Enum):
    """Category of interview question."""
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    SITUATIONAL = "situational"
    CULTURE_FIT = "culture_fit"


class Difficulty(str, Enum):
    """Difficulty level."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class DemandTrend(str, Enum):
    """Job market demand trend."""
    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"


# ============================================================================
# Core Data Models
# ============================================================================

class Skill(BaseModel):
    """A parsed skill from resume or job description."""
    name: str = Field(..., min_length=1, max_length=100)
    category: SkillCategory
    level: SkillLevel
    years_experience: Optional[float] = Field(None, ge=0, le=50)
    source: Literal["explicit", "implicit"] = Field(
        "explicit",
        description="explicit = listed in skills section, implicit = extracted from experience/context"
    )

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return v.strip()


class Experience(BaseModel):
    """Work experience entry."""
    title: str = Field(..., max_length=200)
    company: str = Field(..., max_length=200)
    duration: str = Field(..., description="e.g., '2020-2023' or 'Jan 2020 - Present'")
    duration_months: Optional[int] = Field(None, ge=0, description="Duration in months")
    description: Optional[str] = Field(None, max_length=5000)
    skills_used: List[str] = Field(default_factory=list)


class Education(BaseModel):
    """Education entry."""
    degree: str = Field(..., max_length=200)
    institution: str = Field(..., max_length=200)
    year: Optional[int] = Field(None, ge=1950, le=2030)
    gpa: Optional[float] = Field(None, ge=0, le=4.0)
    field_of_study: Optional[str] = Field(None, max_length=200)


class Requirement(BaseModel):
    """A job requirement."""
    text: str = Field(..., max_length=1000)
    type: RequirementType
    skills: List[str] = Field(default_factory=list)


# ============================================================================
# Parsed Documents
# ============================================================================

class ParsedResume(BaseModel):
    """Complete parsed resume output."""
    id: str = Field(..., description="UUID")
    skills: List[Skill]
    experiences: List[Experience]
    education: List[Education]
    certifications: List[str] = Field(default_factory=list)
    summary: Optional[str] = Field(None, max_length=2000)
    contact_redacted: bool = Field(True, description="Whether PII was redacted")
    embedding: Optional[List[float]] = Field(
        None,
        min_length=768,
        max_length=768,
        description="768-dim embedding vector"
    )


class ParsedJobDescription(BaseModel):
    """Complete parsed job description."""
    id: str = Field(..., description="UUID")
    title: str = Field(..., max_length=200)
    company: Optional[str] = Field(None, max_length=200)
    requirements: List[Requirement]
    required_skills: List[Skill]
    nice_to_have_skills: List[Skill] = Field(default_factory=list)
    experience_years_min: Optional[int] = Field(None, ge=0, le=50)
    experience_years_max: Optional[int] = Field(None, ge=0, le=50)
    education_requirements: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    culture_signals: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = Field(
        None,
        min_length=768,
        max_length=768,
        description="768-dim embedding vector"
    )


# ============================================================================
# Analysis Results
# ============================================================================

class SkillMatch(BaseModel):
    """A matched skill between resume and job."""
    skill_name: str
    resume_level: SkillLevel
    required_level: Optional[SkillLevel] = None
    match_quality: Literal["exact", "partial", "exceeds"]


class MissingSkill(BaseModel):
    """A skill required by job but missing from resume."""
    skill_name: str
    importance: Literal["must_have", "nice_to_have"]
    difficulty_to_acquire: Difficulty


class JobMatch(BaseModel):
    """Complete match analysis for a job."""
    job_id: str
    resume_id: str
    job_title: str
    company: Optional[str] = None
    fit_score: float = Field(..., ge=0, le=100)
    skill_match_score: float = Field(..., ge=0, le=100)
    experience_match_score: float = Field(..., ge=0, le=100)
    education_match_score: float = Field(..., ge=0, le=100)
    matching_skills: List[SkillMatch]
    missing_skills: List[MissingSkill]
    transferable_skills: List[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Complete analysis results for a session."""
    session_id: str
    status: Literal["completed", "in_progress", "failed"]
    job_matches: List[JobMatch]
    completed_at: Optional[datetime] = None


# ============================================================================
# Recommendations
# ============================================================================

class Recommendation(BaseModel):
    """A single recommendation."""
    id: str
    category: RecommendationCategory
    priority: Priority
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    action_items: List[str] = Field(default_factory=list)
    estimated_time: Optional[str] = Field(None, description="e.g., '2-4 weeks'")
    resources: List[str] = Field(default_factory=list)


class RecommendationResult(BaseModel):
    """All recommendations for a job match."""
    session_id: str
    job_id: Optional[str] = None
    recommendations: List[Recommendation]
    priority_order: List[str] = Field(default_factory=list, description="IDs in priority order")
    estimated_improvement: Optional[float] = Field(None, ge=0, le=100)


# ============================================================================
# Interview Prep
# ============================================================================

class STARExample(BaseModel):
    """STAR format interview answer example."""
    situation: str = Field(..., max_length=500)
    task: str = Field(..., max_length=500)
    action: str = Field(..., max_length=1000)
    result: str = Field(..., max_length=500)


class InterviewQuestion(BaseModel):
    """An interview question with suggested answer."""
    id: str
    question: str = Field(..., max_length=1000)
    category: QuestionCategory
    difficulty: Difficulty
    why_asked: Optional[str] = Field(None, max_length=500)
    suggested_answer: str = Field(..., max_length=3000)
    star_example: Optional[STARExample] = None
    related_experience: Optional[str] = Field(None, max_length=500)


class WeaknessResponse(BaseModel):
    """Prepared response for a weakness/skill gap."""
    weakness: str = Field(..., max_length=200)
    honest_response: str = Field(..., max_length=1000)
    mitigation: str = Field(..., max_length=1000)


class InterviewPrepResult(BaseModel):
    """Complete interview preparation package."""
    session_id: str
    job_id: Optional[str] = None
    questions: List[InterviewQuestion]
    talking_points: List[str] = Field(default_factory=list)
    weakness_responses: List[WeaknessResponse] = Field(default_factory=list)
    questions_to_ask: List[str] = Field(default_factory=list)


# ============================================================================
# Market Insights
# ============================================================================

class SalaryRange(BaseModel):
    """Salary range information."""
    min: int = Field(..., ge=0)
    max: int = Field(..., ge=0)
    median: int = Field(..., ge=0)
    currency: str = Field("USD", max_length=3)
    location_adjusted: bool = False


class CareerPath(BaseModel):
    """A potential career progression path."""
    title: str = Field(..., max_length=200)
    typical_years_to_reach: int = Field(..., ge=0, le=30)
    required_skills: List[str] = Field(default_factory=list)
    salary_increase_percent: Optional[int] = Field(None, ge=0, le=200)


class MarketInsights(BaseModel):
    """Market insights for a role."""
    salary_range: SalaryRange
    demand_trend: DemandTrend
    top_skills_in_demand: List[str] = Field(default_factory=list)
    career_paths: List[CareerPath] = Field(default_factory=list)
    industry_insights: str = Field(..., max_length=2000)
    competitive_landscape: Optional[str] = Field(None, max_length=1000)
    data_freshness: str = Field("Based on Aug 2025 data")


class MarketInsightsResult(BaseModel):
    """Complete market insights response."""
    session_id: str
    job_id: Optional[str] = None
    insights: MarketInsights


# ============================================================================
# Session
# ============================================================================

class Session(BaseModel):
    """Session state."""
    session_id: str
    created_at: datetime
    expires_at: datetime
    resume: Optional[ParsedResume] = None
    job_descriptions: List[ParsedJobDescription] = Field(default_factory=list)
    analysis_results: Optional[AnalysisResult] = None


class SessionResponse(BaseModel):
    """Response when creating a session."""
    session_id: str
    created_at: datetime
    expires_at: datetime


# ============================================================================
# Agent Messages
# ============================================================================

class AgentInput(BaseModel):
    """Base input for all agents."""
    session_id: str
    request_id: str


class AgentOutput(BaseModel):
    """Base output for all agents."""
    success: bool
    data: Dict[str, Any]
    errors: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[int] = None


class AgentStatusUpdate(BaseModel):
    """Status update from an agent."""
    agent_name: str
    status: AgentStatus
    progress: int = Field(..., ge=0, le=100)
    current_step: Optional[str] = None
    error: Optional[str] = None


class AgentMessage(BaseModel):
    """Message passed between agents via message bus."""
    message_id: str
    timestamp: datetime
    source_agent: str
    target_agent: Optional[str] = None  # None = broadcast
    message_type: Literal["request", "response", "error", "status"]
    payload: Dict[str, Any]
    correlation_id: str


# ============================================================================
# API Request/Response Models
# ============================================================================

class ResumeUploadResponse(BaseModel):
    """Response after uploading resume."""
    resume_id: str
    status: Literal["parsed", "error"]
    skills: List[Skill]
    experiences: List[Experience]
    education: List[Education]
    summary: Optional[str] = None
    pii_redacted: bool = True


class JobDescriptionUploadResponse(BaseModel):
    """Response after uploading job description."""
    job_id: str
    status: Literal["parsed", "error"]
    title: str
    company: Optional[str] = None
    requirements: List[Requirement]
    required_skills: List[Skill]
    nice_to_have_skills: List[Skill] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    """Request to run analysis."""
    session_id: str


class AnalysisStartedResponse(BaseModel):
    """Response when analysis is started."""
    analysis_id: str
    status: Literal["started", "queued"]
    websocket_url: str
    estimated_duration_seconds: Optional[int] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    version: str = "1.0.0"
    dependencies: Dict[str, Literal["connected", "disconnected", "available", "unavailable"]] = Field(
        default_factory=dict
    )


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

"""Pydantic models and schemas."""

from .specs import (
    # Enums
    SkillLevel,
    SkillCategory,
    RequirementType,
    AgentStatus,
    RecommendationCategory,
    Priority,
    QuestionCategory,
    Difficulty,
    DemandTrend,
    # Core Models
    Skill,
    Experience,
    Education,
    Requirement,
    # Parsed Documents
    ParsedResume,
    ParsedJobDescription,
    # Analysis
    SkillMatch,
    MissingSkill,
    JobMatch,
    AnalysisResult,
    # Recommendations
    Recommendation,
    RecommendationResult,
    # Interview
    STARExample,
    InterviewQuestion,
    WeaknessResponse,
    InterviewPrepResult,
    # Market
    SalaryRange,
    CareerPath,
    MarketInsights,
    MarketInsightsResult,
    # Session
    Session,
    SessionResponse,
    # Agent
    AgentInput,
    AgentOutput,
    AgentStatusUpdate,
    AgentMessage,
    # API
    ResumeUploadResponse,
    JobDescriptionUploadResponse,
    AnalyzeRequest,
    AnalysisStartedResponse,
    HealthResponse,
    ErrorResponse,
)

__all__ = [
    # Enums
    "SkillLevel",
    "SkillCategory",
    "RequirementType",
    "AgentStatus",
    "RecommendationCategory",
    "Priority",
    "QuestionCategory",
    "Difficulty",
    "DemandTrend",
    # Core Models
    "Skill",
    "Experience",
    "Education",
    "Requirement",
    # Parsed Documents
    "ParsedResume",
    "ParsedJobDescription",
    # Analysis
    "SkillMatch",
    "MissingSkill",
    "JobMatch",
    "AnalysisResult",
    # Recommendations
    "Recommendation",
    "RecommendationResult",
    # Interview
    "STARExample",
    "InterviewQuestion",
    "WeaknessResponse",
    "InterviewPrepResult",
    # Market
    "SalaryRange",
    "CareerPath",
    "MarketInsights",
    "MarketInsightsResult",
    # Session
    "Session",
    "SessionResponse",
    # Agent
    "AgentInput",
    "AgentOutput",
    "AgentStatusUpdate",
    "AgentMessage",
    # API
    "ResumeUploadResponse",
    "JobDescriptionUploadResponse",
    "AnalyzeRequest",
    "AnalysisStartedResponse",
    "HealthResponse",
    "ErrorResponse",
]

"""Workflow engine using LlamaIndex Workflows."""

from app.workflows.events import (
    StartAnalysisEvent,
    ResumeParseEvent,
    ResumeParseResultEvent,
    JDAnalyzeEvent,
    JDAnalyzeResultEvent,
    SkillMatchEvent,
    SkillMatchResultEvent,
    GenerateRecommendationsEvent,
    GenerateInterviewPrepEvent,
    GenerateMarketInsightsEvent,
    RecommendationResultEvent,
    InterviewPrepResultEvent,
    MarketInsightsResultEvent,
)
from app.workflows.state import WorkflowState
from app.workflows.analysis_workflow import CareerAnalysisWorkflow, get_workflow

__all__ = [
    # Events
    "StartAnalysisEvent",
    "ResumeParseEvent",
    "ResumeParseResultEvent",
    "JDAnalyzeEvent",
    "JDAnalyzeResultEvent",
    "SkillMatchEvent",
    "SkillMatchResultEvent",
    "GenerateRecommendationsEvent",
    "GenerateInterviewPrepEvent",
    "GenerateMarketInsightsEvent",
    "RecommendationResultEvent",
    "InterviewPrepResultEvent",
    "MarketInsightsResultEvent",
    # State
    "WorkflowState",
    # Workflow
    "CareerAnalysisWorkflow",
    "get_workflow",
]

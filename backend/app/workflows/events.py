"""
Workflow Events for Career Analysis.

Defines typed events for communication between workflow steps.
Uses LlamaIndex Event class for workflow compatibility.
"""

from typing import List, Dict, Optional, Any

from llama_index.core.workflow import Event, StartEvent


# ============================================================================
# Input Events
# ============================================================================

class StartAnalysisEvent(StartEvent):
    """Event to start the career analysis workflow.

    Extends StartEvent to satisfy LlamaIndex Workflow's requirement
    that at least one step accepts StartEvent.
    """
    session_id: str
    resume_id: str
    job_ids: List[str]
    resume_text: Optional[str] = None
    job_texts: Optional[Dict[str, str]] = None


# ============================================================================
# Phase 1 Events: Document Parsing
# ============================================================================

class ResumeParseEvent(Event):
    """Event to trigger resume parsing."""
    resume_text: str
    resume_id: str


class ResumeParseResultEvent(Event):
    """Result event from resume parsing."""
    resume_id: str
    parsed_resume: Dict[str, Any]


class JDAnalyzeEvent(Event):
    """Event to trigger job description analysis."""
    job_id: str
    jd_text: str


class JDAnalyzeResultEvent(Event):
    """Result event from job description analysis."""
    job_id: str
    parsed_jd: Dict[str, Any]


# ============================================================================
# Phase 2 Events: Skill Matching
# ============================================================================

class SkillMatchEvent(Event):
    """Event to trigger skill matching."""
    session_id: str
    resume_id: str
    job_id: str


class SkillMatchResultEvent(Event):
    """Result event from skill matching."""
    job_id: str
    match_result: Dict[str, Any]


# ============================================================================
# Phase 3 Events: Analysis Generation
# ============================================================================

class GenerateRecommendationsEvent(Event):
    """Event to trigger recommendation generation."""
    session_id: str
    skill_gaps: List[str] = []


class GenerateInterviewPrepEvent(Event):
    """Event to trigger interview prep generation."""
    session_id: str
    skill_gaps: List[str] = []


class GenerateMarketInsightsEvent(Event):
    """Event to trigger market insights generation."""
    session_id: str
    job_title: str


# ============================================================================
# Result Events
# ============================================================================

class RecommendationResultEvent(Event):
    """Result event from recommendation generation."""
    recommendations: Dict[str, Any]


class InterviewPrepResultEvent(Event):
    """Result event from interview prep generation."""
    interview_prep: Dict[str, Any]


class MarketInsightsResultEvent(Event):
    """Result event from market insights generation."""
    market_insights: Dict[str, Any]

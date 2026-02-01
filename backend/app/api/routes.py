"""
API Routes.

REST API endpoints for the Career Intelligence Assistant.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from io import BytesIO

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models.session import get_session_manager, SessionData, SessionManager
from app.guardrails import (
    get_input_validator,
    get_pii_detector,
    get_output_filter,
    get_prompt_guard,
)
from app.guardrails.rate_limiter import slowapi_limiter as limiter

logger = logging.getLogger(__name__)
settings = get_settings()


import re

def extract_year_from_education(year_value: Any) -> Optional[int]:
    """
    Extract a valid year from various formats.

    Handles:
    - Integer: returns as-is
    - Date range string like "Sep 2023 — Sep 2024": extracts the last year
    - Single year string like "2024": converts to int
    - None or invalid: returns None
    """
    if year_value is None:
        return None

    if isinstance(year_value, int):
        if 1950 <= year_value <= 2030:
            return year_value
        return None

    if isinstance(year_value, str):
        # Try to find all 4-digit years in the string
        years = re.findall(r'\b(19|20)\d{2}\b', year_value)
        if years:
            # Return the last (most recent) year found
            last_year = int(years[-1])
            if 1950 <= last_year <= 2030:
                return last_year
        # Try direct conversion
        try:
            year_int = int(year_value)
            if 1950 <= year_int <= 2030:
                return year_int
        except ValueError:
            pass

    return None


def sanitize_education_list(education_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sanitize education list to ensure year fields are valid integers."""
    sanitized = []
    for edu in education_list:
        sanitized_edu = edu.copy()
        if "year" in sanitized_edu:
            sanitized_edu["year"] = extract_year_from_education(sanitized_edu["year"])
        sanitized.append(sanitized_edu)
    return sanitized


# Create router
router = APIRouter(prefix="/api/v1", tags=["API"])


# ============================================================================
# Request/Response Models (imported from specs.py for contract compliance)
# ============================================================================

from app.models.specs import (
    SessionResponse as SpecSessionResponse,
    ResumeUploadResponse as SpecResumeUploadResponse,
    JobDescriptionUploadResponse as SpecJobDescriptionUploadResponse,
    AnalyzeRequest,
    AnalysisStartedResponse as SpecAnalysisStartedResponse,
    ErrorResponse as SpecErrorResponse,
    Skill,
    Experience,
    Education,
    Requirement,
)


class SessionResponse(BaseModel):
    """Response for session creation."""
    session_id: str
    created_at: str
    expires_at: str


class ResumeUploadResponse(BaseModel):
    """Response for resume upload."""
    resume_id: str
    status: str = "parsed"
    skills: List[Skill]
    experiences: List[Experience]
    education: List[Education]
    summary: Optional[str] = None
    pii_redacted: bool = True


class JobDescriptionRequest(BaseModel):
    """Request for job description upload (text-based)."""
    text: str = Field(..., min_length=10, max_length=50000)


class JobDescriptionUploadResponse(BaseModel):
    """Response for job description upload."""
    job_id: str
    status: str = "parsed"
    title: str
    company: Optional[str] = None
    required_skills: List[Skill]
    nice_to_have_skills: List[Skill]
    requirements: List[Requirement]


class AnalysisStartedResponse(BaseModel):
    """Response when analysis starts."""
    analysis_id: str
    status: str = "started"  # Literal["started", "queued"]
    websocket_url: str
    estimated_duration_seconds: Optional[int] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# Dependencies
# ============================================================================

async def get_session(
    x_session_id: str = Header(..., alias="X-Session-ID"),
    session_manager: SessionManager = Depends(get_session_manager),
) -> SessionData:
    """Dependency to get and validate session."""
    session = session_manager.get_session(x_session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    return session


async def get_optional_session(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_manager: SessionManager = Depends(get_session_manager),
) -> Optional[SessionData]:
    """Dependency to optionally get session."""
    if x_session_id is None:
        return None
    return session_manager.get_session(x_session_id)


# ============================================================================
# Session Endpoints
# ============================================================================

@router.post(
    "/session",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new session",
    description="Create a new analysis session. Sessions expire after 1 hour.",
)
@limiter.limit("10/minute")
async def create_session(
    request: Request,
    session_manager: SessionManager = Depends(get_session_manager),
) -> SessionResponse:
    """Create a new analysis session."""
    session = session_manager.create_session()

    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at.isoformat(),
        expires_at=session.expires_at.isoformat(),
    )


@router.get(
    "/session/{session_id}",
    summary="Get session status",
    description="Get the current status of a session.",
)
async def get_session_status(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
) -> Dict[str, Any]:
    """Get session status."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return session.to_dict()


@router.delete(
    "/session/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete session",
    description="Delete a session and all associated data.",
)
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
):
    """Delete a session."""
    deleted = session_manager.delete_session(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


# ============================================================================
# Upload Endpoints
# ============================================================================

@router.post(
    "/upload/resume",
    response_model=ResumeUploadResponse,
    summary="Upload resume",
    description="Upload and parse a resume file (PDF, DOCX, or TXT). Max 10MB.",
)
@limiter.limit("10/minute")
async def upload_resume(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: SessionData = Depends(get_session),
    session_manager: SessionManager = Depends(get_session_manager),
) -> ResumeUploadResponse:
    """Upload and parse a resume."""
    # Validate file
    input_validator = get_input_validator()

    # Check file size
    content = await file.read()
    if len(content) > input_validator.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum of {input_validator.max_file_size // (1024*1024)}MB",
        )

    # Check file extension
    filename = file.filename or "unknown"
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in input_validator.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {extension}. Allowed: {', '.join(input_validator.ALLOWED_EXTENSIONS)}",
        )

    # Check file type by magic bytes
    if extension == ".pdf" and not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match PDF format",
        )

    if extension in {".exe", ".dll", ".bat", ".sh"} or content.startswith(b"MZ") or content.startswith(b"\x7fELF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Executable files are not allowed",
        )

    # Parse document
    try:
        from app.services.document_parser import get_document_parser
        parser = get_document_parser()
        resume_text = parser.parse(BytesIO(content), filename)
    except Exception as e:
        logger.error(f"Failed to parse resume: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse document: {str(e)}",
        )

    # Validate content length
    is_valid, error = input_validator.validate_content(resume_text)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    # Check for prompt injection
    prompt_guard = get_prompt_guard()
    is_safe, injection_error = prompt_guard.validate(resume_text)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content failed security validation: {injection_error}",
        )

    # Detect and redact PII
    pii_detector = get_pii_detector()
    redacted_text = pii_detector.redact(resume_text)

    # Parse resume with LLM
    try:
        from app.services.llamaindex_service import get_llamaindex_service
        llamaindex_service = await get_llamaindex_service()
        parsed_resume = await llamaindex_service.parse_resume(redacted_text)
    except Exception as e:
        logger.error(f"Failed to parse resume with LLM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze resume",
        )

    # Generate resume ID
    resume_id = f"resume-{uuid.uuid4().hex[:8]}"

    # Store in session
    session_manager.set_resume(
        session_id=session.session_id,
        resume_id=resume_id,
        resume_text=resume_text,
        parsed_resume=parsed_resume,
    )

    # Store in Neo4j synchronously to prevent race condition with analysis
    # Sanitize education data early for both Neo4j storage and response
    sanitized_education = sanitize_education_list(parsed_resume.get("education", []))

    try:
        from app.services.neo4j_store import get_neo4j_store
        from app.services.embedding import get_embedding_service
        from app.models import ParsedResume as ParsedResumeModel

        neo4j_store = get_neo4j_store()
        embedding_service = get_embedding_service()

        # Construct ParsedResume object for Neo4j storage
        resume_obj = ParsedResumeModel(
            id=resume_id,
            summary=parsed_resume.get("summary"),
            skills=parsed_resume.get("skills", []),
            experiences=parsed_resume.get("experiences", []),
            education=sanitized_education,
            certifications=parsed_resume.get("certifications", []),
            contact_redacted=True
        )
        await neo4j_store.save_resume(resume_obj)
        logger.info(f"Stored resume {resume_id} in Neo4j")

        # Store skill embeddings directly in Neo4j (replaces LlamaIndex)
        skills_stored = 0
        for skill in parsed_resume.get("skills", []):
            skill_name = skill.get("name", "")
            if skill_name:
                embedding = await embedding_service.embed(f"Skill: {skill_name}")
                await neo4j_store.store_skill_embedding(
                    skill_name=skill_name,
                    embedding=embedding,
                    category=skill.get("category")
                )
                skills_stored += 1
        logger.info(f"Stored {skills_stored} skill embeddings for resume {resume_id}")
    except Exception as e:
        logger.error(f"Failed to store resume in Neo4j: {e}")

    return ResumeUploadResponse(
        resume_id=resume_id,
        status="parsed",
        skills=parsed_resume.get("skills", []),
        experiences=parsed_resume.get("experiences", []),
        education=sanitized_education,
        summary=parsed_resume.get("summary"),
        pii_redacted=True,
    )


@router.post(
    "/upload/job-description",
    response_model=JobDescriptionUploadResponse,
    summary="Upload job description",
    description="Upload a job description (as file or text). Max 5 per session.",
)
@limiter.limit("10/minute")
async def upload_job_description(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    session: SessionData = Depends(get_session),
    session_manager: SessionManager = Depends(get_session_manager),
) -> JobDescriptionUploadResponse:
    """Upload and parse a job description."""
    # Check JD limit
    if len(session.job_descriptions) >= session_manager.MAX_JDS_PER_SESSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {session_manager.MAX_JDS_PER_SESSION} job descriptions per session",
        )

    # Get JD text from file or text input
    jd_text = ""
    filename = "text_input.txt"

    if file is not None:
        content = await file.read()
        filename = file.filename or "unknown"

        # Validate file
        input_validator = get_input_validator()
        extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if extension not in input_validator.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {extension}",
            )

        # Parse document
        try:
            from app.services.document_parser import get_document_parser
            parser = get_document_parser()
            jd_text = parser.parse(BytesIO(content), filename)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse document: {str(e)}",
            )
    elif text is not None:
        jd_text = text
    else:
        # Try to parse JSON body
        try:
            body = await request.json()
            jd_text = body.get("text", "")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either file or text must be provided",
            )

    # Validate text
    if not jd_text or len(jd_text.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text is too short",
        )

    input_validator = get_input_validator()
    is_valid, error = input_validator.validate_content(jd_text)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    # Check for prompt injection
    prompt_guard = get_prompt_guard()
    is_safe, injection_error = prompt_guard.validate(jd_text)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content failed security validation: {injection_error}",
        )

    # Parse JD with LLM
    try:
        from app.services.llamaindex_service import get_llamaindex_service
        llamaindex_service = await get_llamaindex_service()
        parsed_jd = await llamaindex_service.parse_job_description(jd_text)
    except Exception as e:
        logger.error(f"Failed to parse JD with LLM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze job description",
        )

    # Generate job ID
    job_id = f"job-{uuid.uuid4().hex[:8]}"

    # Store in session
    success = session_manager.add_job_description(
        session_id=session.session_id,
        job_id=job_id,
        parsed_jd=parsed_jd,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add job description to session",
        )

    # Store in Neo4j synchronously to prevent race condition with analysis
    try:
        from app.services.neo4j_store import get_neo4j_store
        from app.services.embedding import get_embedding_service
        from app.models import ParsedJobDescription as ParsedJDModel

        neo4j_store = get_neo4j_store()
        embedding_service = get_embedding_service()

        # Construct ParsedJobDescription object for Neo4j storage
        jd_obj = ParsedJDModel(
            id=job_id,
            title=parsed_jd.get("title", "Unknown"),
            company=parsed_jd.get("company"),
            required_skills=parsed_jd.get("required_skills", []),
            nice_to_have_skills=parsed_jd.get("nice_to_have_skills", []),
            requirements=parsed_jd.get("requirements", []),
            experience_years_min=parsed_jd.get("experience_years_min"),
            experience_years_max=parsed_jd.get("experience_years_max"),
            education_requirements=parsed_jd.get("education_requirements", []),
            responsibilities=parsed_jd.get("responsibilities", []),
            culture_signals=parsed_jd.get("culture_signals", [])
        )
        await neo4j_store.save_job_description(jd_obj)
        logger.info(f"Stored job description {job_id} in Neo4j")

        # Store skill embeddings directly in Neo4j (replaces LlamaIndex)
        skills_stored = 0
        all_skills = parsed_jd.get("required_skills", []) + parsed_jd.get("nice_to_have_skills", [])
        for skill in all_skills:
            skill_name = skill.get("name", "")
            if skill_name:
                embedding = await embedding_service.embed(f"Skill: {skill_name}")
                await neo4j_store.store_skill_embedding(
                    skill_name=skill_name,
                    embedding=embedding,
                    category=skill.get("category")
                )
                skills_stored += 1
        logger.info(f"Stored {skills_stored} skill embeddings for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to store JD in Neo4j: {e}")

    return JobDescriptionUploadResponse(
        job_id=job_id,
        status="parsed",
        title=parsed_jd.get("title", "Unknown"),
        company=parsed_jd.get("company"),
        required_skills=parsed_jd.get("required_skills", []),
        nice_to_have_skills=parsed_jd.get("nice_to_have_skills", []),
        requirements=parsed_jd.get("requirements", []),
    )


# ============================================================================
# Analysis Endpoints
# ============================================================================

@router.post(
    "/analyze",
    response_model=AnalysisStartedResponse,
    summary="Start analysis",
    description="Run full analysis on resume against job descriptions.",
)
@limiter.limit("10/minute")
async def analyze(
    request: Request,
    background_tasks: BackgroundTasks,
    body: AnalyzeRequest,
    session_manager: SessionManager = Depends(get_session_manager),
) -> AnalysisStartedResponse:
    """Start the analysis workflow."""
    session = session_manager.get_session(body.session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Validate session has required data
    if session.resume_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No resume uploaded. Please upload a resume first.",
        )

    if len(session.job_descriptions) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No job descriptions uploaded. Please add at least one job description.",
        )

    # Check if analysis already running
    if session.analysis_status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Analysis already in progress",
        )

    # Generate analysis ID
    analysis_id = f"analysis-{uuid.uuid4().hex[:8]}"

    # Update session
    session.analysis_id = analysis_id
    session.analysis_status = "running"
    session.analysis_started_at = datetime.utcnow()
    session_manager.update_session(session)

    # Run analysis in background using LlamaIndex Workflow
    async def run_analysis():
        try:
            from app.workflows import CareerAnalysisWorkflow, StartAnalysisEvent

            workflow = CareerAnalysisWorkflow(timeout=600)  # 10 minute timeout

            # Create start event with session data
            # Documents are already parsed during upload, so skip parsing phase
            # by not passing resume_text or job_texts
            start_event = StartAnalysisEvent(
                session_id=session.session_id,
                resume_id=session.resume_id,
                job_ids=list(session.job_descriptions.keys()),
                resume_text=None,  # Already parsed during upload
                job_texts=None,  # Already parsed during upload
            )

            # Run the workflow
            result = await workflow.run(start_event=start_event)

            # Store results (result is a dict from StopEvent)
            if result.get("success"):
                session_manager.set_analysis_results(
                    session_id=session.session_id,
                    job_matches=result.get("job_matches", []),
                    recommendations=result.get("recommendations"),
                    interview_prep=result.get("interview_prep"),
                    market_insights=result.get("market_insights"),
                )

            # Broadcast completion via WebSocket
            try:
                from app.api.websocket import broadcast_analysis_complete
                await broadcast_analysis_complete(session.session_id, success=True)
            except Exception:
                pass  # WebSocket broadcast is optional

        except Exception as e:
            logger.exception(f"Analysis failed: {e}")
            failed_session = session_manager.get_session(body.session_id)
            if failed_session:
                failed_session.analysis_status = "failed"
                session_manager.update_session(failed_session)

            # Broadcast failure via WebSocket
            try:
                from app.api.websocket import broadcast_analysis_complete
                # Use body.session_id as fallback if failed_session invalid
                sid = failed_session.session_id if failed_session else body.session_id
                await broadcast_analysis_complete(sid, success=False, error=str(e))
            except Exception:
                pass  # WebSocket broadcast is optional

    background_tasks.add_task(run_analysis)

    # Construct WebSocket URL (use request host for proper URL)
    ws_scheme = "wss" if settings.is_production else "ws"
    ws_url = f"{ws_scheme}://localhost:{settings.port}/ws/progress/{session.session_id}"

    return AnalysisStartedResponse(
        analysis_id=analysis_id,
        status="started",
        websocket_url=ws_url,
        estimated_duration_seconds=30,
    )


# ============================================================================
# Results Endpoints
# ============================================================================

@router.get(
    "/results/{session_id}",
    summary="Get analysis results",
    description="Get the full analysis results for a session.",
)
async def get_results(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
) -> Dict[str, Any]:
    """Get analysis results."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.analysis_status == "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis has not been started",
        )

    # Filter output
    output_filter = get_output_filter()

    return {
        "session_id": session_id,
        "analysis_id": session.analysis_id,
        "status": session.analysis_status,
        "started_at": session.analysis_started_at.isoformat() if session.analysis_started_at else None,
        "completed_at": session.analysis_completed_at.isoformat() if session.analysis_completed_at else None,
        "job_matches": session.job_matches or [],
        "agent_progress": session.agent_progress,
    }


@router.get(
    "/recommendations/{session_id}",
    summary="Get recommendations",
    description="Get recommendations for improving job fit.",
)
async def get_recommendations(
    session_id: str,
    job_id: Optional[str] = None,
    session_manager: SessionManager = Depends(get_session_manager),
) -> Dict[str, Any]:
    """Get recommendations."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.analysis_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis not completed",
        )

    recommendations_data = session.recommendations or {}

    # Extract the recommendations array from the nested structure
    # The agent returns: {session_id, job_id, recommendations: [...], priority_order, estimated_improvement}
    recommendations_list = recommendations_data.get("recommendations", [])

    # Ensure it's a list (handle case where it might be nested differently)
    if not isinstance(recommendations_list, list):
        recommendations_list = []

    # Filter by job_id if provided
    if job_id is not None:
        # Filter recommendations specific to this job
        pass  # TODO: Implement job-specific filtering

    return {
        "session_id": session_id,
        "recommendations": recommendations_list,
        "priority_order": recommendations_data.get("priority_order", []),
        "estimated_improvement": recommendations_data.get("estimated_improvement", 0),
    }


@router.get(
    "/interview-prep/{session_id}",
    summary="Get interview preparation",
    description="Get interview questions and preparation materials.",
)
async def get_interview_prep(
    session_id: str,
    job_id: Optional[str] = None,
    session_manager: SessionManager = Depends(get_session_manager),
) -> Dict[str, Any]:
    """Get interview preparation."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.analysis_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis not completed",
        )

    interview_data = session.interview_prep or {}

    # Extract the interview prep data from the nested structure
    # The agent returns: {session_id, job_id, questions: [...], talking_points, weakness_responses, questions_to_ask}
    questions = interview_data.get("questions", [])
    if not isinstance(questions, list):
        questions = []

    return {
        "session_id": session_id,
        "questions": questions,
        "talkingPoints": interview_data.get("talking_points", []),
        "weaknessResponses": interview_data.get("weakness_responses", []),
        "questionsToAsk": interview_data.get("questions_to_ask", []),
    }


@router.get(
    "/market-insights/{session_id}",
    summary="Get market insights",
    description="Get salary ranges, job demand, and market trends.",
)
async def get_market_insights(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
) -> Dict[str, Any]:
    """Get market insights."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.analysis_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis not completed",
        )

    market_data = session.market_insights or {}

    # Extract the insights from the nested structure
    # The agent returns: {session_id, job_id, insights: {...}}
    insights = market_data.get("insights", {})

    return {
        "session_id": session_id,
        "insights": insights,
    }


# ============================================================================
# Progress Endpoint (REST alternative to WebSocket)
# ============================================================================

@router.get(
    "/progress/{session_id}",
    summary="Get analysis progress",
    description="Get current progress of running analysis (REST alternative to WebSocket).",
)
async def get_progress(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
) -> Dict[str, Any]:
    """Get analysis progress."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return {
        "session_id": session_id,
        "analysis_id": session.analysis_id,
        "status": session.analysis_status,
        "agent_progress": session.agent_progress,
    }


# ============================================================================
# Chat Endpoint
# ============================================================================

class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000, description="User's question")
    job_id: Optional[str] = Field(None, description="Specific job ID to focus on (optional)")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    response: str = Field(..., description="AI response to the question")
    suggested_questions: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with AI about job fit",
    description="Ask questions about your resume-job fit analysis.",
)
@limiter.limit("10/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    session: SessionData = Depends(get_session),
) -> ChatResponse:
    """
    Chat with AI about resume-job fit.

    Requires a valid session with resume and job descriptions uploaded.
    Analysis should be completed for best results, but basic questions
    can be answered before analysis.
    """
    # Check for prompt injection
    prompt_guard = get_prompt_guard()
    is_safe, injection_error = prompt_guard.validate(body.message)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Message failed security validation: {injection_error}",
        )

    # Run chat agent
    try:
        from app.agents.chat_fit import ChatFitAgent, ChatFitInput

        agent = ChatFitAgent(session_id=session.session_id)
        result = await agent.process(
            ChatFitInput(
                session_id=session.session_id,
                message=body.message,
                job_id=body.job_id,
            )
        )

        if not result.success:
            error_msg = result.errors[0] if result.errors else "Chat processing failed"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg,
            )

        return ChatResponse(
            response=result.data.get("response", ""),
            suggested_questions=result.data.get("suggested_questions", []),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request",
        )

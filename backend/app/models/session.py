"""
Session Management.

In-memory session storage for demo/portfolio purposes.
Can be upgraded to Redis for production.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Data stored for each session."""
    session_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))

    # Uploaded data
    resume_id: Optional[str] = None
    resume_text: Optional[str] = None
    parsed_resume: Optional[Dict[str, Any]] = None

    job_descriptions: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # job_id -> parsed JD

    # Analysis results
    analysis_id: Optional[str] = None
    analysis_started_at: Optional[datetime] = None
    analysis_completed_at: Optional[datetime] = None
    analysis_status: str = "pending"  # pending, running, completed, failed

    # Results
    job_matches: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[Dict[str, Any]] = None
    interview_prep: Optional[Dict[str, Any]] = None
    market_insights: Optional[Dict[str, Any]] = None

    # Agent progress tracking
    agent_progress: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # agent_name -> status

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "has_resume": self.resume_id is not None,
            "resume_id": self.resume_id,
            "job_count": len(self.job_descriptions),
            "job_ids": list(self.job_descriptions.keys()),
            "analysis_status": self.analysis_status,
            "analysis_id": self.analysis_id,
        }


class SessionManager:
    """
    In-memory session manager.

    Thread-safe storage for session data.
    Sessions expire after 1 hour by default.
    """

    # Configurable limits
    MAX_SESSIONS = 1000
    MAX_JDS_PER_SESSION = 5
    SESSION_EXPIRY_HOURS = 1

    def __init__(self):
        """Initialize session manager."""
        self._sessions: Dict[str, SessionData] = {}
        self._lock = Lock()

    def create_session(self) -> SessionData:
        """
        Create a new session.

        Returns:
            New SessionData instance
        """
        with self._lock:
            # Clean up expired sessions if approaching limit
            if len(self._sessions) >= self.MAX_SESSIONS:
                self._cleanup_expired()

            # Generate unique session ID
            session_id = str(uuid.uuid4())
            while session_id in self._sessions:
                session_id = str(uuid.uuid4())

            # Create session
            session = SessionData(
                session_id=session_id,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=self.SESSION_EXPIRY_HOURS),
            )
            self._sessions[session_id] = session

            logger.info(f"Created session: {session_id}")
            return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            SessionData if found and not expired, None otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)

            if session is None:
                return None

            if session.is_expired():
                logger.info(f"Session expired: {session_id}")
                del self._sessions[session_id]
                return None

            return session

    def update_session(self, session: SessionData) -> None:
        """
        Update session data.

        Args:
            session: SessionData to update
        """
        with self._lock:
            if session.session_id in self._sessions:
                self._sessions[session.session_id] = session

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session to delete

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Deleted session: {session_id}")
                return True
            return False

    def set_resume(
        self,
        session_id: str,
        resume_id: str,
        resume_text: str,
        parsed_resume: Dict[str, Any],
    ) -> bool:
        """
        Set resume data for a session.

        Args:
            session_id: Session identifier
            resume_id: Resume identifier
            resume_text: Original resume text
            parsed_resume: Parsed resume data

        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            return False

        session.resume_id = resume_id
        session.resume_text = resume_text
        session.parsed_resume = parsed_resume
        self.update_session(session)
        return True

    def add_job_description(
        self,
        session_id: str,
        job_id: str,
        parsed_jd: Dict[str, Any],
    ) -> bool:
        """
        Add a job description to session.

        Args:
            session_id: Session identifier
            job_id: Job description identifier
            parsed_jd: Parsed job description data

        Returns:
            True if successful, False if session not found or limit reached
        """
        session = self.get_session(session_id)
        if session is None:
            return False

        if len(session.job_descriptions) >= self.MAX_JDS_PER_SESSION:
            logger.warning(f"Session {session_id} reached JD limit")
            return False

        session.job_descriptions[job_id] = parsed_jd
        self.update_session(session)
        return True

    def set_analysis_results(
        self,
        session_id: str,
        job_matches: List[Dict[str, Any]],
        recommendations: Optional[Dict[str, Any]] = None,
        interview_prep: Optional[Dict[str, Any]] = None,
        market_insights: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Set analysis results for a session.

        Args:
            session_id: Session identifier
            job_matches: Job match results
            recommendations: Recommendation results
            interview_prep: Interview prep results
            market_insights: Market insights results

        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            return False

        session.job_matches = job_matches
        session.recommendations = recommendations
        session.interview_prep = interview_prep
        session.market_insights = market_insights
        session.analysis_status = "completed"
        session.analysis_completed_at = datetime.utcnow()
        self.update_session(session)
        return True

    def update_agent_progress(
        self,
        session_id: str,
        agent_name: str,
        status: str,
        progress: int = 0,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """
        Update agent progress for a session.

        Args:
            session_id: Session identifier
            agent_name: Name of the agent
            status: Current status (pending, running, completed, failed)
            progress: Progress percentage (0-100)
            result: Agent result data
            error: Error message if failed

        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            return False

        session.agent_progress[agent_name] = {
            "status": status,
            "progress": progress,
            "result": result,
            "error": error,
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.update_session(session)
        return True

    def _cleanup_expired(self) -> int:
        """
        Remove expired sessions.

        Returns:
            Number of sessions removed
        """
        now = datetime.utcnow()
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]

        for sid in expired:
            del self._sessions[sid]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

        return len(expired)

    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics."""
        with self._lock:
            return {
                "total_sessions": len(self._sessions),
                "max_sessions": self.MAX_SESSIONS,
                "max_jds_per_session": self.MAX_JDS_PER_SESSION,
            }


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get the singleton session manager instance.

    Returns:
        SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

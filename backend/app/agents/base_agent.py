"""
Base Agent Abstract Class.

Defines the interface that all agents must implement.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from uuid import uuid4

from pydantic import BaseModel

from app.models import AgentOutput, AgentStatus

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.

    All agents must implement:
    - name: Unique identifier for the agent
    - input_schema: Pydantic model for input validation
    - output_schema: Pydantic model for output validation
    - process(): Main processing method
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize base agent.

        Args:
            session_id: Optional session ID for WebSocket progress updates
        """
        self._session_id = session_id
        self._status = AgentStatus.PENDING

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique name identifier for the agent.

        Returns:
            Agent name string (e.g., "resume_parser", "skill_matcher")
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of agent purpose.

        Returns:
            Description string explaining what this agent does
        """
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Type[BaseModel]:
        """
        Pydantic model class for input validation.

        Returns:
            Pydantic BaseModel subclass
        """
        pass

    @property
    @abstractmethod
    def output_schema(self) -> Type[BaseModel]:
        """
        Pydantic model class for output validation.

        Returns:
            Pydantic BaseModel subclass
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the agent is ready to process requests.

        Returns:
            True if agent is healthy and ready, False otherwise
        """
        pass

    @abstractmethod
    async def _execute(self, input_data: Any) -> Dict[str, Any]:
        """
        Internal execution method to be implemented by subclasses.

        Args:
            input_data: Validated input data

        Returns:
            Dict containing the agent's output data
        """
        pass

    def set_session_id(self, session_id: str) -> None:
        """
        Set the session ID for WebSocket progress updates.

        Args:
            session_id: Session ID string
        """
        self._session_id = session_id

    async def process(self, input_data: Any) -> AgentOutput:
        """
        Main processing method that wraps _execute with error handling and timing.

        Args:
            input_data: Input data (dict or string depending on agent)

        Returns:
            AgentOutput with success status, data, and any errors
        """
        start_time = time.time()
        self._status = AgentStatus.RUNNING

        try:
            # Broadcast start status via WebSocket
            await self.report_progress(0, f"Starting {self.name}")

            # Execute the agent's main logic
            result_data = await self._execute(input_data)

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            self._status = AgentStatus.COMPLETED

            # Broadcast completion
            await self._broadcast_status("completed", 100, "Complete")

            return AgentOutput(
                success=True,
                data=result_data,
                errors=[],
                processing_time_ms=processing_time_ms
            )

        except ValueError as e:
            # Validation or business logic errors
            self._status = AgentStatus.FAILED
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Broadcast failure
            await self._broadcast_status("failed", 0, error=str(e))

            logger.warning(f"Agent {self.name} validation error: {e}")

            return AgentOutput(
                success=False,
                data={},
                errors=[str(e)],
                processing_time_ms=processing_time_ms
            )

        except Exception as e:
            # Unexpected errors
            self._status = AgentStatus.FAILED
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Broadcast failure
            await self._broadcast_status("failed", 0, error=str(e))

            logger.error(f"Agent {self.name} error: {e}", exc_info=True)

            return AgentOutput(
                success=False,
                data={},
                errors=[f"Agent error: {str(e)}"],
                processing_time_ms=processing_time_ms
            )

    async def _broadcast_status(
        self,
        status: str,
        progress: int,
        current_step: str = None,
        error: str = None
    ) -> None:
        """
        Broadcast status update via WebSocket.

        Args:
            status: Current status (pending, running, completed, failed)
            progress: Progress percentage (0-100)
            current_step: Description of current processing step
            error: Optional error message
        """
        if not self._session_id:
            return

        try:
            from app.api.websocket import broadcast_agent_progress
            await broadcast_agent_progress(
                session_id=self._session_id,
                agent_name=self.name,
                status=status,
                progress=progress,
                current_step=current_step,
                error=error,
            )
        except Exception as e:
            # Don't let WebSocket errors break agent execution
            logger.debug(f"Failed to broadcast progress: {e}")

    async def report_progress(self, progress: int, step: str) -> None:
        """
        Report progress update via WebSocket.

        Args:
            progress: Progress percentage (0-100)
            step: Description of current step
        """
        await self._broadcast_status("running", progress, step)

    @property
    def status(self) -> AgentStatus:
        """Get current agent status."""
        return self._status

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, status={self._status.value})>"

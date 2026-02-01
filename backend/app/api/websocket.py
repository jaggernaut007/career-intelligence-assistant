"""
WebSocket Handlers.

Real-time progress updates for analysis workflow.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.session import get_session_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """
    WebSocket connection manager.

    Manages active connections and message broadcasting.
    """

    def __init__(self):
        """Initialize connection manager."""
        # session_id -> set of connections
        self._active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> bool:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            session_id: Session to subscribe to

        Returns:
            True if connection accepted, False otherwise
        """
        # Verify session exists
        session_manager = get_session_manager()
        session = session_manager.get_session(session_id)

        if session is None:
            await websocket.close(code=4001, reason="Session not found")
            return False

        await websocket.accept()

        if session_id not in self._active_connections:
            self._active_connections[session_id] = set()

        self._active_connections[session_id].add(websocket)
        logger.info(f"WebSocket connected for session: {session_id}")
        return True

    def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
            session_id: Session the connection was subscribed to
        """
        if session_id in self._active_connections:
            self._active_connections[session_id].discard(websocket)

            # Clean up empty session entries
            if not self._active_connections[session_id]:
                del self._active_connections[session_id]

        logger.info(f"WebSocket disconnected for session: {session_id}")

    async def broadcast_to_session(
        self,
        session_id: str,
        message: Dict[str, Any],
    ) -> None:
        """
        Broadcast a message to all connections for a session.

        Args:
            session_id: Session to broadcast to
            message: Message dict to send
        """
        if session_id not in self._active_connections:
            return

        # Add timestamp
        message["timestamp"] = datetime.utcnow().isoformat()

        disconnected = set()
        for connection in self._active_connections[session_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.add(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self._active_connections[session_id].discard(connection)

    async def send_agent_update(
        self,
        session_id: str,
        agent_name: str,
        status: str,
        progress: int = 0,
        current_step: str = None,
        result: Any = None,
        error: str = None,
    ) -> None:
        """
        Send agent progress update.

        Args:
            session_id: Session to update
            agent_name: Name of the agent
            status: Current status (pending, running, completed, failed)
            progress: Progress percentage (0-100)
            current_step: Description of current processing step
            result: Optional result data
            error: Optional error message
        """
        message = {
            "type": "agent_update",
            "agent_name": agent_name,
            "status": status,
            "progress": progress,
        }

        if current_step is not None:
            message["current_step"] = current_step
        if result is not None:
            message["result"] = result
        if error is not None:
            message["error"] = error

        await self.broadcast_to_session(session_id, message)

    async def send_analysis_complete(
        self,
        session_id: str,
        success: bool,
        error: str = None,
    ) -> None:
        """
        Send analysis completion notification.

        Args:
            session_id: Session that completed
            success: Whether analysis was successful
            error: Optional error message if failed
        """
        message = {
            "type": "analysis_complete",
            "success": success,
        }
        if error:
            message["error"] = error

        await self.broadcast_to_session(session_id, message)

    def get_connection_count(self, session_id: str) -> int:
        """Get number of active connections for a session."""
        return len(self._active_connections.get(session_id, set()))


# Singleton connection manager
_connection_manager: ConnectionManager = None


def get_connection_manager() -> ConnectionManager:
    """Get the singleton connection manager."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@router.websocket("/ws/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for analysis progress updates.

    Clients connect here to receive real-time updates about:
    - Agent progress (pending, running, completed, failed)
    - Analysis completion

    Message format:
    {
        "type": "agent_update" | "analysis_complete",
        "agent_name": "resume_parser",  // for agent_update
        "status": "running",
        "progress": 50,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    """
    manager = get_connection_manager()
    connected = await manager.connect(websocket, session_id)

    if not connected:
        return

    # Send initial status
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)

    if session:
        # Send current agent progress
        for agent_name, progress_data in session.agent_progress.items():
            await websocket.send_json({
                "type": "agent_update",
                "agent_name": agent_name,
                "status": progress_data.get("status", "pending"),
                "progress": progress_data.get("progress", 0),
                "timestamp": progress_data.get("updated_at", datetime.utcnow().isoformat()),
            })

    try:
        while True:
            # Keep connection alive, handle client messages
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,  # Ping every 30 seconds
                )

                # Handle client messages (e.g., ping)
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, session_id)


# ============================================================================
# Helper function for agents to send updates
# ============================================================================

async def broadcast_agent_progress(
    session_id: str,
    agent_name: str,
    status: str,
    progress: int = 0,
    current_step: str = None,
    result: Any = None,
    error: str = None,
) -> None:
    """
    Broadcast agent progress to WebSocket clients.

    This function should be called by agents during execution.

    Args:
        session_id: Session to update
        agent_name: Name of the agent
        status: Current status
        progress: Progress percentage
        current_step: Description of current processing step
        result: Optional result data
        error: Optional error message
    """
    manager = get_connection_manager()
    await manager.send_agent_update(
        session_id=session_id,
        agent_name=agent_name,
        status=status,
        progress=progress,
        current_step=current_step,
        result=result,
        error=error,
    )

    # Also update session storage
    session_manager = get_session_manager()
    session_manager.update_agent_progress(
        session_id=session_id,
        agent_name=agent_name,
        status=status,
        progress=progress,
        result=result,
        error=error,
    )


async def broadcast_analysis_complete(
    session_id: str,
    success: bool,
    error: str = None,
) -> None:
    """
    Broadcast analysis completion to WebSocket clients.

    Args:
        session_id: Session that completed
        success: Whether analysis was successful
        error: Optional error message
    """
    manager = get_connection_manager()
    await manager.send_analysis_complete(session_id, success, error)

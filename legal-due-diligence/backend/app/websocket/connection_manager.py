"""
WebSocket Connection Manager

Manages real-time connections between the backend and frontend for:
- Approval requests
- Agent status updates
- Workflow progress
"""
from fastapi import WebSocket
from typing import Dict, Any
import logging
import json

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time agent communication."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")

    async def disconnect_all(self):
        """Disconnect all active connections."""
        for session_id in list(self.active_connections.keys()):
            ws = self.active_connections[session_id]
            await ws.close()
            self.disconnect(session_id)

    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """
        Send a message to a specific session.

        Args:
            session_id: Session to send to
            message: Message data (will be JSON serialized)
        """
        if session_id in self.active_connections:
            ws = self.active_connections[session_id]
            try:
                await ws.send_json(message)
                logger.debug(f"Sent message to {session_id}: {message.get('type')}")
            except Exception as e:
                logger.error(f"Failed to send message to {session_id}: {e}")
                self.disconnect(session_id)

    async def send_approval_request(self, session_id: str, approval_context: Any):
        """
        Send an approval request to the frontend.

        Args:
            session_id: Session to send to
            approval_context: ApprovalContext object
        """
        message = {
            "type": "approval_request",
            "data": approval_context.to_dict()
        }
        await self.send_message(session_id, message)

    async def send_agent_status(self, session_id: str, status: str, details: str = ""):
        """
        Send agent status update.

        Args:
            session_id: Session to send to
            status: Status (running, paused, completed, failed)
            details: Additional details
        """
        message = {
            "type": "agent_status",
            "data": {
                "status": status,
                "details": details
            }
        }
        await self.send_message(session_id, message)

    async def send_todos_update(self, session_id: str, todos: list):
        """
        Send todos list update.

        Args:
            session_id: Session to send to
            todos: List of todo items
        """
        message = {
            "type": "todos_update",
            "data": {
                "todos": todos
            }
        }
        await self.send_message(session_id, message)

    async def send_workflow_event(self, session_id: str, event_type: str, data: Dict[str, Any]):
        """
        Send workflow event (tool call, result, etc.)

        Args:
            session_id: Session to send to
            event_type: Type of event
            data: Event data
        """
        message = {
            "type": "workflow_event",
            "data": {
                "event_type": event_type,
                "data": data
            }
        }
        await self.send_message(session_id, message)


# Global connection manager instance
manager = ConnectionManager()

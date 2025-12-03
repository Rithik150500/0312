"""
Legal Due Diligence Web Application - Backend

FastAPI application providing:
- Document upload and management
- Session management
- Agent execution with WebSocket communication
- Human approval workflow
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any
from uuid import uuid4
import logging
import asyncio

from .config import settings
from .database import init_db, get_db
from .models import Session, Document, DocumentPage, SessionStatus
from .websocket.connection_manager import manager
from .services.agent_service import LegalDueDiligenceAgent
from .middleware.approval import ApprovalContextBuilder, APPROVAL_REQUIRED_TOOLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Legal Due Diligence API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()
    logger.info("Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await manager.disconnect_all()


# ============================================================================
# Document Routes
# ============================================================================

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a legal document to the data room.

    This would:
    1. Save to S3/MinIO
    2. Extract text from PDF
    3. Generate page summaries
    4. Identify legally significant pages
    5. Create database records
    """
    logger.info(f"Uploading document: {file.filename}")

    # For now, return mock data
    # In production, this would process the PDF
    doc_id = str(uuid4())[:8]

    return {
        "id": doc_id,
        "filename": file.filename,
        "summary": "Sample legal document (processing required)",
        "pages": 10,
        "uploaded_at": "2024-01-01T00:00:00"
    }


@app.get("/api/documents")
async def list_documents():
    """List all documents in the data room."""
    async with get_db() as db:
        result = await db.execute(
            select(Document).order_by(Document.uploaded_at.desc())
        )
        documents = result.scalars().all()

    return {
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "summary": doc.summary,
                "pages": doc.page_count,
                "uploaded_at": doc.uploaded_at.isoformat()
            }
            for doc in documents
        ]
    }


@app.get("/api/documents/{document_id}")
async def get_document(document_id: str):
    """Get detailed information about a document."""
    async with get_db() as db:
        result = await db.execute(
            select(Document)
            .options(selectinload(Document.pages))
            .where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": doc.id,
        "filename": doc.filename,
        "summary": doc.summary,
        "page_count": doc.page_count,
        "pages": [
            {
                "num": page.page_num,
                "summary": page.summary,
                "legally_significant": page.legally_significant
            }
            for page in sorted(doc.pages, key=lambda p: p.page_num)
        ]
    }


@app.get("/api/documents/{document_id}/pdf")
async def get_document_pdf(document_id: str):
    """Get PDF file for a document."""
    # In production, this would fetch from S3
    raise HTTPException(status_code=501, detail="PDF retrieval not implemented")


# ============================================================================
# Session Routes
# ============================================================================

@app.post("/api/sessions/start")
async def start_session(data: Dict[str, Any]):
    """
    Start a new legal due diligence session.

    Args:
        project_name: Name of the project
        document_ids: List of document IDs to analyze
    """
    project_name = data.get("project_name")
    document_ids = data.get("document_ids", [])

    session_id = str(uuid4())[:8]

    # Create session in database
    async with get_db() as db:
        session = Session(
            id=session_id,
            project_name=project_name,
            document_ids=document_ids,
            status=SessionStatus.CREATED
        )
        db.add(session)
        await db.commit()

    logger.info(f"Created session: {session_id}")

    return {
        "session_id": session_id,
        "status": "created",
        "documents": len(document_ids)
    }


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details."""
    async with get_db() as db:
        result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": session.id,
        "project_name": session.project_name,
        "status": session.status,
        "document_ids": session.document_ids,
        "created_at": session.created_at.isoformat()
    }


# ============================================================================
# WebSocket Route
# ============================================================================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time agent communication.

    Handles:
    - Agent status updates
    - Approval requests
    - Approval decisions
    - Workflow events
    """
    await manager.connect(session_id, websocket)

    try:
        # Send initial status
        await manager.send_agent_status(session_id, "connected")

        # Start agent in background
        asyncio.create_task(run_agent(session_id))

        # Listen for approval decisions
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "approval_decision":
                await handle_approval_decision(session_id, data)

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
        manager.disconnect(session_id)


async def run_agent(session_id: str):
    """
    Run the legal due diligence agent.

    This executes the agent and handles approval workflow.
    """
    try:
        # Update session status
        async with get_db() as db:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()

            if not session:
                logger.error(f"Session not found: {session_id}")
                return

            session.status = SessionStatus.RUNNING
            await db.commit()

        await manager.send_agent_status(session_id, "running", "Starting legal due diligence analysis")

        # Build initial user message with document summaries
        async with get_db() as db:
            result = await db.execute(
                select(Document).where(Document.id.in_(session.document_ids))
            )
            documents = result.scalars().all()

        user_message = "Please perform legal due diligence on the following documents:\n\n"
        for doc in documents:
            user_message += f"- {doc.filename}: {doc.summary}\n"

        # Create and execute agent
        agent = LegalDueDiligenceAgent(session_id)

        # Execute with approval workflow
        # This is simplified - in production would integrate with LangGraph's interrupt system
        result = await agent.execute(user_message)

        # Mark as completed
        async with get_db() as db:
            result_db = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result_db.scalar_one_or_none()
            if session:
                session.status = SessionStatus.COMPLETED
                await db.commit()

        await manager.send_agent_status(session_id, "completed", "Due diligence completed")

    except Exception as e:
        logger.error(f"Agent execution error for {session_id}: {e}")

        async with get_db() as db:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                session.status = SessionStatus.FAILED
                session.error_message = str(e)
                await db.commit()

        await manager.send_agent_status(session_id, "failed", str(e))


async def handle_approval_decision(session_id: str, data: Dict[str, Any]):
    """
    Handle approval decision from frontend.

    Args:
        session_id: Session ID
        data: Decision data with type (approve/edit/reject) and details
    """
    request_id = data.get("request_id")
    decision = data.get("decision")

    logger.info(f"[{session_id}] Approval decision: {decision} for {request_id}")

    # In production, this would:
    # 1. Look up the pending approval by request_id
    # 2. Apply the decision (approve, modify args, or reject)
    # 3. Resume agent execution
    # 4. Send confirmation to frontend

    await manager.send_agent_status(session_id, "running", "Resuming after approval")


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

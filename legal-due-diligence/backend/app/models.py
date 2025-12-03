from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .database import Base


class SessionStatus(str, enum.Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class Session(Base):
    """Legal due diligence session."""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    project_name = Column(String, nullable=False)
    status = Column(String, default=SessionStatus.CREATED)
    document_ids = Column(JSON, default=list)
    thread_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)


class Document(Base):
    """Legal document in the data room."""
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    file_hash = Column(String, unique=True, index=True)
    file_path = Column(String, nullable=False)  # S3 path
    summary = Column(Text)
    page_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationship to pages
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    """Individual page of a document."""
    __tablename__ = "document_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_num = Column(Integer, nullable=False)
    text = Column(Text)
    summary = Column(Text)
    legally_significant = Column(Boolean, default=False)
    image_path = Column(String)  # S3 path to page image
    confidence_score = Column(Float, default=0.0)  # OCR confidence

    # Relationship to document
    document = relationship("Document", back_populates="pages")

    class Config:
        # Unique constraint on document_id + page_num
        indexes = [
            {"fields": ["document_id", "page_num"], "unique": True}
        ]


class AgentFile(Base):
    """Files created by the agent during analysis."""
    __tablename__ = "agent_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

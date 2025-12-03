"""
Approval Workflow Middleware

This module handles human-in-the-loop approval for agent actions.
It builds rich context from tool calls to provide visual feedback in the UI.
"""
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import logging

from ..models import Document, DocumentPage
from ..database import get_db

logger = logging.getLogger(__name__)


@dataclass
class DocumentHighlight:
    """Highlight information for a document."""
    doc_id: str
    reason: str
    legally_significant_pages: List[int]
    all_pages_summary: Dict[int, str]


@dataclass
class PageHighlight:
    """Highlight information for specific pages."""
    doc_id: str
    page_nums: List[int]
    context: str


@dataclass
class FileHighlight:
    """Highlight information for file operations."""
    file_path: str
    operation: str  # 'write' or 'edit'
    content_preview: str


@dataclass
class ApprovalContext:
    """Complete context for an approval request."""
    request_id: str
    tool_name: str
    tool_args: Dict[str, Any]
    allowed_decisions: List[str]  # ['approve', 'edit', 'reject']
    document_highlights: List[DocumentHighlight]
    page_highlights: List[PageHighlight]
    file_highlights: List[FileHighlight]
    agent_reasoning: str
    related_todos: List[str]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "request_id": self.request_id,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "allowed_decisions": self.allowed_decisions,
            "document_highlights": [
                {
                    "doc_id": dh.doc_id,
                    "reason": dh.reason,
                    "legally_significant_pages": dh.legally_significant_pages,
                    "all_pages_summary": dh.all_pages_summary
                }
                for dh in self.document_highlights
            ],
            "page_highlights": [
                {
                    "doc_id": ph.doc_id,
                    "page_nums": ph.page_nums,
                    "context": ph.context
                }
                for ph in self.page_highlights
            ],
            "file_highlights": [
                {
                    "file_path": fh.file_path,
                    "operation": fh.operation,
                    "content_preview": fh.content_preview
                }
                for fh in self.file_highlights
            ],
            "agent_reasoning": self.agent_reasoning,
            "related_todos": self.related_todos,
            "timestamp": self.timestamp
        }


class ApprovalContextBuilder:
    """
    Builds rich approval contexts from agent tool calls.

    This extracts relevant information to provide visual feedback
    in the UI (highlighting documents, pages, files, etc.)
    """

    def __init__(self, session_id: str):
        self.session_id = session_id

    async def build_context(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        conversation_history: List[Any]
    ) -> ApprovalContext:
        """
        Build approval context based on tool type.

        Args:
            tool_name: Name of the tool being called
            tool_args: Arguments passed to the tool
            conversation_history: Recent conversation messages

        Returns:
            Complete approval context
        """
        logger.info(f"[{self.session_id}] Building approval context for: {tool_name}")

        # Route to appropriate builder based on tool
        if tool_name == "get_documents":
            return await self._build_get_documents_context(tool_args, conversation_history)
        elif tool_name == "get_page_text":
            return await self._build_get_page_text_context(tool_args, conversation_history)
        elif tool_name == "get_page_image":
            return await self._build_get_page_image_context(tool_args, conversation_history)
        elif tool_name in ["write_file", "edit_file"]:
            return await self._build_file_context(tool_name, tool_args, conversation_history)
        elif tool_name in ["web_search", "web_fetch"]:
            return await self._build_web_context(tool_name, tool_args, conversation_history)
        elif tool_name in ["analyze_documents", "create_report"]:
            return await self._build_subagent_context(tool_name, tool_args, conversation_history)
        else:
            return await self._build_generic_context(tool_name, tool_args, conversation_history)

    async def _build_get_documents_context(
        self,
        tool_args: Dict[str, Any],
        conversation_history: List[Any]
    ) -> ApprovalContext:
        """Build context for get_documents approval."""

        doc_ids = tool_args.get("doc_ids", [])

        # Fetch document details
        async with get_db() as db:
            result = await db.execute(
                select(Document)
                .options(selectinload(Document.pages))
                .where(Document.id.in_(doc_ids))
            )
            documents = result.scalars().all()

        # Build document highlights
        document_highlights = []
        for doc in documents:
            significant_pages = [p.page_num for p in doc.pages if p.legally_significant]
            page_summaries = {p.page_num: p.summary for p in doc.pages}

            document_highlights.append(DocumentHighlight(
                doc_id=doc.id,
                reason=self._extract_reason(doc.id, conversation_history),
                legally_significant_pages=significant_pages,
                all_pages_summary=page_summaries
            ))

        return ApprovalContext(
            request_id=str(uuid4()),
            tool_name="get_documents",
            tool_args=tool_args,
            allowed_decisions=["approve", "edit", "reject"],
            document_highlights=document_highlights,
            page_highlights=[],
            file_highlights=[],
            agent_reasoning=self._extract_reasoning(conversation_history),
            related_todos=self._extract_todos(conversation_history),
            timestamp=datetime.utcnow().isoformat()
        )

    async def _build_get_page_text_context(
        self,
        tool_args: Dict[str, Any],
        conversation_history: List[Any]
    ) -> ApprovalContext:
        """Build context for get_page_text approval."""

        doc_id = tool_args.get("doc_id")
        page_nums = tool_args.get("page_nums", [])

        # Fetch document
        async with get_db() as db:
            result = await db.execute(
                select(Document)
                .options(selectinload(Document.pages))
                .where(Document.id == doc_id)
            )
            doc = result.scalar_one_or_none()

        document_highlights = []
        if doc:
            significant_pages = [p.page_num for p in doc.pages if p.legally_significant]
            page_summaries = {p.page_num: p.summary for p in doc.pages}

            document_highlights.append(DocumentHighlight(
                doc_id=doc.id,
                reason="Pages requested for detailed review",
                legally_significant_pages=significant_pages,
                all_pages_summary=page_summaries
            ))

        page_highlights = [PageHighlight(
            doc_id=doc_id,
            page_nums=page_nums,
            context=self._extract_reasoning(conversation_history)
        )]

        return ApprovalContext(
            request_id=str(uuid4()),
            tool_name="get_page_text",
            tool_args=tool_args,
            allowed_decisions=["approve", "edit", "reject"],
            document_highlights=document_highlights,
            page_highlights=page_highlights,
            file_highlights=[],
            agent_reasoning=self._extract_reasoning(conversation_history),
            related_todos=self._extract_todos(conversation_history),
            timestamp=datetime.utcnow().isoformat()
        )

    async def _build_get_page_image_context(
        self,
        tool_args: Dict[str, Any],
        conversation_history: List[Any]
    ) -> ApprovalContext:
        """Build context for get_page_image approval."""

        # Similar to get_page_text but with image-specific context
        return await self._build_get_page_text_context(tool_args, conversation_history)

    async def _build_file_context(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        conversation_history: List[Any]
    ) -> ApprovalContext:
        """Build context for file write/edit approval."""

        file_path = tool_args.get("file_path", "")
        content = tool_args.get("content", "") or tool_args.get("new_string", "")

        # Preview content (first 200 chars)
        content_preview = content[:200] + "..." if len(content) > 200 else content

        file_highlights = [FileHighlight(
            file_path=file_path,
            operation="write" if tool_name == "write_file" else "edit",
            content_preview=content_preview
        )]

        return ApprovalContext(
            request_id=str(uuid4()),
            tool_name=tool_name,
            tool_args=tool_args,
            allowed_decisions=["approve", "edit", "reject"],
            document_highlights=[],
            page_highlights=[],
            file_highlights=file_highlights,
            agent_reasoning=self._extract_reasoning(conversation_history),
            related_todos=self._extract_todos(conversation_history),
            timestamp=datetime.utcnow().isoformat()
        )

    async def _build_web_context(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        conversation_history: List[Any]
    ) -> ApprovalContext:
        """Build context for web search/fetch approval."""

        return ApprovalContext(
            request_id=str(uuid4()),
            tool_name=tool_name,
            tool_args=tool_args,
            allowed_decisions=["approve", "edit", "reject"],
            document_highlights=[],
            page_highlights=[],
            file_highlights=[],
            agent_reasoning=self._extract_reasoning(conversation_history),
            related_todos=self._extract_todos(conversation_history),
            timestamp=datetime.utcnow().isoformat()
        )

    async def _build_subagent_context(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        conversation_history: List[Any]
    ) -> ApprovalContext:
        """Build context for subagent task approval."""

        return ApprovalContext(
            request_id=str(uuid4()),
            tool_name=tool_name,
            tool_args=tool_args,
            allowed_decisions=["approve", "edit", "reject"],
            document_highlights=[],
            page_highlights=[],
            file_highlights=[],
            agent_reasoning=self._extract_reasoning(conversation_history),
            related_todos=self._extract_todos(conversation_history),
            timestamp=datetime.utcnow().isoformat()
        )

    async def _build_generic_context(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        conversation_history: List[Any]
    ) -> ApprovalContext:
        """Build generic context for unknown tools."""

        return ApprovalContext(
            request_id=str(uuid4()),
            tool_name=tool_name,
            tool_args=tool_args,
            allowed_decisions=["approve", "reject"],
            document_highlights=[],
            page_highlights=[],
            file_highlights=[],
            agent_reasoning=self._extract_reasoning(conversation_history),
            related_todos=self._extract_todos(conversation_history),
            timestamp=datetime.utcnow().isoformat()
        )

    def _extract_reasoning(self, conversation_history: List[Any]) -> str:
        """Extract agent's most recent reasoning from conversation."""

        for msg in reversed(conversation_history[-5:]):
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                if len(msg.content) > 50:  # Skip very short messages
                    return msg.content[:500]

        return "Continuing with analysis task"

    def _extract_reason(self, doc_id: str, conversation_history: List[Any]) -> str:
        """Extract why agent wants this specific document."""

        for msg in reversed(conversation_history[-10:]):
            if hasattr(msg, 'content') and doc_id in str(msg.content):
                content = str(msg.content)
                sentences = content.split('.')
                for sentence in sentences:
                    if doc_id in sentence:
                        return sentence.strip()[:200]

        return "Document requested for review"

    def _extract_todos(self, conversation_history: List[Any]) -> List[str]:
        """Extract current in-progress todos from conversation."""

        todos = []
        for msg in reversed(conversation_history[-20:]):
            if hasattr(msg, 'tool_calls'):
                for tool_call in msg.tool_calls:
                    if tool_call.get('name') == 'write_todos':
                        args = tool_call.get('args', {})
                        task_list = args.get('todos', [])
                        todos = [
                            task.get('content', '')
                            for task in task_list
                            if task.get('status') == 'in_progress'
                        ]
                        if todos:
                            return todos[:3]  # Return up to 3 current tasks

        return []


# Tools that require approval
APPROVAL_REQUIRED_TOOLS = {
    "get_documents",
    "get_page_text",
    "get_page_image",
    "write_file",
    "edit_file",
    "web_search",
    "web_fetch",
    "analyze_documents",
    "create_report"
}

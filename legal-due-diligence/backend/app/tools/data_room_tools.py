"""
Data Room Tools for Legal Due Diligence Agent

These tools allow the agent to interact with documents in the data room.
"""
from typing import List, Dict, Any
from langchain.tools import tool
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import logging

from ..models import Document, DocumentPage
from ..database import get_db

logger = logging.getLogger(__name__)


def create_data_room_tools(session_id: str):
    """
    Create data room tools with closure over session_id.

    Tools created:
    - list_data_room_documents: List all documents with summaries
    - get_documents: Get detailed info for specific documents
    - get_page_text: Get full text of specific pages
    - get_page_image: Get images of specific pages
    """

    @tool
    async def list_data_room_documents() -> str:
        """
        List all documents in the data room.

        Returns:
            String with all documents showing:
            - Document ID
            - Summary description
            - Number of pages

        Use this first to understand what documents are available.
        """
        logger.info(f"[{session_id}] Listing data room documents")

        async with get_db() as db:
            result = await db.execute(
                select(Document).order_by(Document.uploaded_at.desc())
            )
            documents = result.scalars().all()

        if not documents:
            return "No documents found in the data room."

        output = []
        for doc in documents:
            output.append(
                f"Document ID: {doc.id}\n"
                f"Summary: {doc.summary}\n"
                f"Pages: {doc.page_count}"
            )

        return "\n\n---\n\n".join(output)

    @tool
    async def get_documents(doc_ids: List[str]) -> str:
        """
        Get detailed information about specific documents.

        Args:
            doc_ids: List of document IDs to retrieve

        Returns:
            For each document:
            - Combined summary descriptions of all pages (page num, summary)
            - Full page text of legally significant pages

        Use this to get comprehensive information about documents you want to analyze.
        """
        logger.info(f"[{session_id}] Getting documents: {doc_ids}")

        async with get_db() as db:
            result = await db.execute(
                select(Document)
                .options(selectinload(Document.pages))
                .where(Document.id.in_(doc_ids))
            )
            documents = result.scalars().all()

        if not documents:
            return f"Error: No documents found with IDs: {doc_ids}"

        output = []
        for doc in documents:
            # All pages with summaries
            pages_info = []
            for page in sorted(doc.pages, key=lambda p: p.page_num):
                pages_info.append(f"Page {page.page_num}: {page.summary}")

            pages_summary = "\n".join(pages_info)

            # Full text of legally significant pages
            significant_pages = [p for p in doc.pages if p.legally_significant]
            significant_text = []

            for page in sorted(significant_pages, key=lambda p: p.page_num):
                significant_text.append(
                    f"=== Page {page.page_num} (Legally Significant) ===\n"
                    f"{page.text}"
                )

            significant_section = "\n\n".join(significant_text) if significant_text else "No legally significant pages."

            output.append(
                f"DOCUMENT: {doc.filename} (ID: {doc.id})\n"
                f"Overall Summary: {doc.summary}\n\n"
                f"ALL PAGES:\n{pages_summary}\n\n"
                f"LEGALLY SIGNIFICANT PAGES (FULL TEXT):\n{significant_section}"
            )

        return "\n\n" + "="*80 + "\n\n".join(output)

    @tool
    async def get_page_text(doc_id: str, page_nums: List[int]) -> str:
        """
        Get full text of specific pages from a document.

        Args:
            doc_id: Document ID
            page_nums: List of page numbers to retrieve

        Returns:
            Full text content of the requested pages

        Use this when you need to read specific pages in detail.
        """
        logger.info(f"[{session_id}] Getting page text: doc={doc_id}, pages={page_nums}")

        async with get_db() as db:
            result = await db.execute(
                select(Document)
                .options(selectinload(Document.pages))
                .where(Document.id == doc_id)
            )
            doc = result.scalar_one_or_none()

        if not doc:
            return f"Error: Document '{doc_id}' not found"

        output = []
        for page_num in page_nums:
            page = next((p for p in doc.pages if p.page_num == page_num), None)
            if page:
                output.append(
                    f"=== {doc.filename} - Page {page_num} ===\n"
                    f"{page.text}"
                )
            else:
                output.append(f"Page {page_num}: NOT FOUND")

        return "\n\n".join(output)

    @tool
    async def get_page_image(doc_id: str, page_nums: List[int]) -> str:
        """
        Get images of specific pages.

        Args:
            doc_id: Document ID
            page_nums: List of page numbers to retrieve images for

        Returns:
            Image paths for the requested pages

        **USE SPARINGLY** - Only use for visual elements like signatures, stamps,
        diagrams, or complex layouts not captured in text. Prefer get_page_text
        when possible.
        """
        logger.info(f"[{session_id}] Getting page images: doc={doc_id}, pages={page_nums}")

        async with get_db() as db:
            result = await db.execute(
                select(Document)
                .options(selectinload(Document.pages))
                .where(Document.id == doc_id)
            )
            doc = result.scalar_one_or_none()

        if not doc:
            return f"Error: Document '{doc_id}' not found"

        image_paths = []
        for page_num in page_nums:
            page = next((p for p in doc.pages if p.page_num == page_num), None)
            if page and page.image_path:
                image_paths.append(f"Page {page_num}: {page.image_path}")
            else:
                image_paths.append(f"Page {page_num}: No image available")

        return "\n".join(image_paths)

    return [
        list_data_room_documents,
        get_documents,
        get_page_text,
        get_page_image
    ]


def create_web_research_tools(session_id: str):
    """
    Create web research tools for the analysis agent.

    Tools created:
    - web_search: Search the web for information
    - web_fetch: Fetch content from a specific URL
    """

    @tool
    async def web_search(query: str) -> str:
        """
        Search the web for information related to legal due diligence.

        Args:
            query: Search query

        Returns:
            Search results with titles, URLs, and snippets
        """
        logger.info(f"[{session_id}] Web search: {query}")
        # This would integrate with a search API (Google, Bing, etc.)
        # For now, return a placeholder
        return f"Web search results for: {query}\n\n[Search API integration needed]"

    @tool
    async def web_fetch(url: str) -> str:
        """
        Fetch content from a specific URL.

        Args:
            url: URL to fetch

        Returns:
            Text content from the URL

        **LIMITED USE** - Use sparingly, only when you need specific information
        from a known source.
        """
        logger.info(f"[{session_id}] Web fetch: {url}")
        # This would fetch and parse web content
        # For now, return a placeholder
        return f"Content from {url}\n\n[Web fetch integration needed]"

    return [web_search, web_fetch]

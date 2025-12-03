"""
Document Processing Service

Processes legal documents using Claude Haiku for analysis:
1. Extract pages as images and text
2. Analyze each page with Claude Haiku (image + text)
3. Combine page summaries and get document summary
4. Identify legally significant pages
5. Store in database
"""
from typing import List, Dict, Any, Tuple
from anthropic import Anthropic
from PIL import Image
import base64
import io
import os
import hashlib
import logging
from uuid import uuid4
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models import Document, DocumentPage
from ..config import settings
from .pdf_processor import PDFProcessor
from .storage_client import S3Client

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for processing and analyzing legal documents."""

    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.s3_client = S3Client()
        self.anthropic = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def summarize_page(
        self,
        page_image: Image.Image,
        page_text: str,
        page_num: int
    ) -> str:
        """
        Summarize a single page using Claude Haiku.

        Args:
            page_image: PIL Image of the page
            page_text: Extracted text from the page
            page_num: Page number

        Returns:
            Summary of the page
        """
        logger.info(f"Summarizing page {page_num} with Claude Haiku")

        # Convert image to base64
        image_base64 = self._image_to_base64(page_image)

        # Call Claude Haiku with vision
        try:
            message = self.anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": f"""Analyze this legal document page (page {page_num}).

Extracted text from the page:
{page_text[:2000]}  # Limit text to avoid token limits

Please provide a concise summary (2-3 sentences) covering:
- Main topic or purpose of this page
- Key terms, obligations, or provisions
- Any notable legal clauses or conditions

Summary:"""
                            }
                        ],
                    }
                ],
            )

            summary = message.content[0].text.strip()
            logger.info(f"Page {page_num} summarized: {summary[:100]}...")

            return summary

        except Exception as e:
            logger.error(f"Failed to summarize page {page_num}: {e}")
            # Fallback to text-only summary
            return f"Page {page_num}: {page_text[:200]}"

    async def analyze_document(
        self,
        page_summaries: List[str],
        total_pages: int
    ) -> Tuple[str, List[int]]:
        """
        Analyze the entire document to get summary and legally significant pages.

        Args:
            page_summaries: List of page summaries
            total_pages: Total number of pages

        Returns:
            Tuple of (document_summary, legally_significant_page_numbers)
        """
        logger.info(f"Analyzing document with {total_pages} pages using Claude Haiku")

        # Combine all page summaries
        combined_summaries = "\n\n".join([
            f"Page {i+1}: {summary}"
            for i, summary in enumerate(page_summaries)
        ])

        try:
            message = self.anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""You are analyzing a legal document with {total_pages} pages. Below are summaries of each page.

Page Summaries:
{combined_summaries}

Please provide:

1. DOCUMENT SUMMARY (3-5 sentences):
A high-level summary of the entire document, its purpose, and key points.

2. LEGALLY SIGNIFICANT PAGES (comma-separated page numbers):
List the page numbers that contain legally significant content such as:
- Key contractual obligations or commitments
- Liability or indemnification clauses
- Termination or renewal provisions
- Intellectual property rights
- Financial obligations or payment terms
- Regulatory compliance requirements
- Dispute resolution mechanisms
- Warranties or representations
- Material definitions or terms

Format your response as:

SUMMARY:
[Your document summary here]

SIGNIFICANT_PAGES:
[Comma-separated page numbers, e.g., 1,3,5,7]
"""
                    }
                ],
            )

            response_text = message.content[0].text.strip()

            # Parse response
            summary = ""
            significant_pages = []

            if "SUMMARY:" in response_text and "SIGNIFICANT_PAGES:" in response_text:
                parts = response_text.split("SIGNIFICANT_PAGES:")
                summary = parts[0].replace("SUMMARY:", "").strip()

                pages_text = parts[1].strip()
                if pages_text and pages_text != "None" and pages_text != "N/A":
                    try:
                        significant_pages = [
                            int(p.strip())
                            for p in pages_text.split(",")
                            if p.strip().isdigit()
                        ]
                    except ValueError:
                        logger.warning(f"Failed to parse significant pages: {pages_text}")

            logger.info(f"Document analysis complete. Significant pages: {significant_pages}")

            return summary, significant_pages

        except Exception as e:
            logger.error(f"Failed to analyze document: {e}")
            # Fallback
            return "Legal document (analysis failed)", []

    async def process_document(
        self,
        file_path: str,
        filename: str,
        db_session
    ) -> Document:
        """
        Process a PDF document completely.

        Args:
            file_path: Path to the PDF file
            filename: Original filename
            db_session: Database session

        Returns:
            Document model instance
        """
        logger.info(f"Processing document: {filename}")

        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)

        # Check if already processed
        result = await db_session.execute(
            select(Document).where(Document.file_hash == file_hash)
        )
        existing_doc = result.scalar_one_or_none()

        if existing_doc:
            logger.info(f"Document already processed: {filename}")
            return existing_doc

        # Generate document ID
        doc_id = str(uuid4())[:8]

        # Step 1: Extract pages as images and text
        logger.info("Step 1: Extracting pages as images and text")
        page_images, page_texts = self.pdf_processor.process_pdf(file_path)

        if len(page_images) != len(page_texts):
            logger.warning(
                f"Page count mismatch: {len(page_images)} images vs {len(page_texts)} texts. "
                f"Using minimum count."
            )

        num_pages = min(len(page_images), len(page_texts))

        # Step 2: Upload original PDF to S3
        logger.info("Step 2: Uploading PDF to S3")
        pdf_s3_path = f"documents/{doc_id}/{filename}"
        self.s3_client.upload_file(file_path, pdf_s3_path)

        # Step 3: Process each page
        logger.info(f"Step 3: Processing {num_pages} pages with Claude Haiku")
        page_summaries = []
        pages_data = []

        for i in range(num_pages):
            page_num = i + 1
            page_image = page_images[i]
            page_text = page_texts[i]

            # Summarize page with Claude Haiku
            page_summary = await self.summarize_page(page_image, page_text, page_num)
            page_summaries.append(page_summary)

            # Upload page image to S3
            image_s3_path = f"documents/{doc_id}/pages/page_{page_num}.png"
            self.s3_client.upload_image(page_image, image_s3_path)

            # Store page data
            pages_data.append({
                'page_num': page_num,
                'text': page_text,
                'summary': page_summary,
                'image_path': image_s3_path
            })

            logger.info(f"Processed page {page_num}/{num_pages}")

        # Step 4: Analyze entire document
        logger.info("Step 4: Analyzing entire document with Claude Haiku")
        doc_summary, significant_pages = await self.analyze_document(
            page_summaries,
            num_pages
        )

        # Step 5: Create database records
        logger.info("Step 5: Storing in database")

        # Create document record
        document = Document(
            id=doc_id,
            filename=filename,
            file_hash=file_hash,
            file_path=pdf_s3_path,
            summary=doc_summary,
            page_count=num_pages,
            uploaded_at=datetime.utcnow(),
            processed_at=datetime.utcnow()
        )

        db_session.add(document)

        # Create page records
        for page_data in pages_data:
            page = DocumentPage(
                document_id=doc_id,
                page_num=page_data['page_num'],
                text=page_data['text'],
                summary=page_data['summary'],
                image_path=page_data['image_path'],
                legally_significant=page_data['page_num'] in significant_pages
            )
            db_session.add(page)

        await db_session.commit()

        logger.info(f"Document processing complete: {doc_id}")

        return document

    async def get_by_id(self, doc_id: str, db_session) -> Document:
        """Get a document by ID with pages."""
        result = await db_session.execute(
            select(Document)
            .options(selectinload(Document.pages))
            .where(Document.id == doc_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, doc_ids: List[str], db_session) -> List[Document]:
        """Get multiple documents by IDs with pages."""
        result = await db_session.execute(
            select(Document)
            .options(selectinload(Document.pages))
            .where(Document.id.in_(doc_ids))
        )
        return result.scalars().all()

    async def list_all(self, db_session) -> List[Document]:
        """List all documents."""
        result = await db_session.execute(
            select(Document).order_by(Document.uploaded_at.desc())
        )
        return result.scalars().all()

    async def delete_document(self, doc_id: str, db_session):
        """Delete a document and all its pages."""
        result = await db_session.execute(
            select(Document).where(Document.id == doc_id)
        )
        document = result.scalar_one_or_none()

        if document:
            # Delete from S3
            try:
                self.s3_client.delete_file(document.file_path)
                # Delete page images
                for page in document.pages:
                    if page.image_path:
                        self.s3_client.delete_file(page.image_path)
            except Exception as e:
                logger.warning(f"Failed to delete S3 files: {e}")

            # Delete from database (cascade will handle pages)
            await db_session.delete(document)
            await db_session.commit()

            logger.info(f"Deleted document: {doc_id}")

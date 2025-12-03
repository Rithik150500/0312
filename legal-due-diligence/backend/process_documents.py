#!/usr/bin/env python3
"""
Document Processing CLI Utility

Process PDF documents from a folder and add them to the data room.

Usage:
    python process_documents.py /path/to/pdf/folder
"""
import sys
import os
import asyncio
import logging
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import init_db, AsyncSessionLocal
from app.services.document_service import DocumentService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_folder(folder_path: str):
    """
    Process all PDF files in a folder.

    Args:
        folder_path: Path to folder containing PDF files
    """
    folder = Path(folder_path)

    if not folder.exists() or not folder.is_dir():
        logger.error(f"Invalid folder path: {folder_path}")
        return

    # Get all PDF files
    pdf_files = list(folder.glob("*.pdf"))

    if not pdf_files:
        logger.warning(f"No PDF files found in {folder_path}")
        return

    logger.info(f"Found {len(pdf_files)} PDF files to process")

    # Initialize database
    await init_db()

    # Create document service
    doc_service = DocumentService()

    # Process each document
    processed_count = 0
    failed_count = 0

    for pdf_path in pdf_files:
        filename = pdf_path.name
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {filename}")
        logger.info(f"{'='*60}")

        try:
            async with AsyncSessionLocal() as db:
                document = await doc_service.process_document(
                    file_path=str(pdf_path),
                    filename=filename,
                    db_session=db
                )

            logger.info(f"✓ Successfully processed: {filename}")
            logger.info(f"  Document ID: {document.id}")
            logger.info(f"  Pages: {document.page_count}")
            logger.info(f"  Summary: {document.summary[:100]}...")

            processed_count += 1

        except Exception as e:
            logger.error(f"✗ Failed to process {filename}: {e}", exc_info=True)
            failed_count += 1

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("Processing Complete")
    logger.info(f"{'='*60}")
    logger.info(f"Total files: {len(pdf_files)}")
    logger.info(f"Successfully processed: {processed_count}")
    logger.info(f"Failed: {failed_count}")


async def process_single_document(pdf_path: str):
    """
    Process a single PDF document.

    Args:
        pdf_path: Path to PDF file
    """
    pdf_file = Path(pdf_path)

    if not pdf_file.exists() or not pdf_file.is_file():
        logger.error(f"Invalid file path: {pdf_path}")
        return

    if pdf_file.suffix.lower() != '.pdf':
        logger.error(f"Not a PDF file: {pdf_path}")
        return

    logger.info(f"Processing document: {pdf_file.name}")

    # Initialize database
    await init_db()

    # Create document service
    doc_service = DocumentService()

    try:
        async with AsyncSessionLocal() as db:
            document = await doc_service.process_document(
                file_path=str(pdf_file),
                filename=pdf_file.name,
                db_session=db
            )

        logger.info(f"✓ Successfully processed: {pdf_file.name}")
        logger.info(f"  Document ID: {document.id}")
        logger.info(f"  Pages: {document.page_count}")
        logger.info(f"  Summary: {document.summary}")
        logger.info(f"  Legally significant pages: {[p.page_num for p in document.pages if p.legally_significant]}")

    except Exception as e:
        logger.error(f"✗ Failed to process {pdf_file.name}: {e}", exc_info=True)


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python process_documents.py <folder_or_file_path>")
        print("\nExamples:")
        print("  python process_documents.py /path/to/pdf/folder")
        print("  python process_documents.py /path/to/document.pdf")
        sys.exit(1)

    path = sys.argv[1]

    if os.path.isdir(path):
        await process_folder(path)
    elif os.path.isfile(path):
        await process_single_document(path)
    else:
        logger.error(f"Invalid path: {path}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

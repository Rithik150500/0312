"""
PDF Processing Utilities

Handles PDF to image conversion and text extraction.
"""
from typing import List, Tuple
from pdf2image import convert_from_path
from PIL import Image
import PyPDF2
import io
import logging
import tempfile
import os

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Process PDF files to extract images and text."""

    def __init__(self):
        pass

    def extract_pages_as_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Extract all pages from a PDF as images.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of PIL Images, one per page
        """
        try:
            logger.info(f"Extracting images from PDF: {pdf_path}")

            # Convert PDF to images (one per page)
            images = convert_from_path(
                pdf_path,
                dpi=200,  # Good quality for OCR and viewing
                fmt='png'
            )

            logger.info(f"Extracted {len(images)} pages as images")
            return images

        except Exception as e:
            logger.error(f"Failed to extract images from PDF: {e}")
            raise

    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """
        Extract text from all pages of a PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of text strings, one per page
        """
        try:
            logger.info(f"Extracting text from PDF: {pdf_path}")

            page_texts = []

            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)

                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    page_texts.append(text)

            logger.info(f"Extracted text from {len(page_texts)} pages")
            return page_texts

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise

    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Number of pages
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except Exception as e:
            logger.error(f"Failed to get page count: {e}")
            raise

    def process_pdf(self, pdf_path: str) -> Tuple[List[Image.Image], List[str]]:
        """
        Process a PDF to extract both images and text for all pages.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Tuple of (page_images, page_texts)
        """
        logger.info(f"Processing PDF: {pdf_path}")

        # Extract images and text in parallel would be ideal,
        # but for simplicity we'll do it sequentially
        page_images = self.extract_pages_as_images(pdf_path)
        page_texts = self.extract_text_from_pdf(pdf_path)

        # Verify counts match
        if len(page_images) != len(page_texts):
            logger.warning(
                f"Page count mismatch: {len(page_images)} images vs {len(page_texts)} text pages"
            )

        return page_images, page_texts

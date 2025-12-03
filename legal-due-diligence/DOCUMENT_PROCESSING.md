# Document Processing Guide

This guide explains how the document processing system works and how to use it.

## Overview

The document processing pipeline analyzes PDF documents using Claude Haiku to extract structured information:

```
PDF Document
    ↓
Extract Pages (Images + Text)
    ↓
For Each Page: Claude Haiku Analysis (Image + Text → Summary)
    ↓
Combine Page Summaries
    ↓
Document Analysis: Claude Haiku (Summaries → Document Summary + Legally Significant Pages)
    ↓
Store in Database + S3
```

## Data Structure

### Document
- `doc_id`: Unique identifier
- `summdesc`: AI-generated document summary
- `doc_path`: S3 path to original PDF
- `pages[]`: Array of page objects

### Page
- `page_num`: Page number (1-indexed)
- `summdesc`: AI-generated page summary
- `page_text`: Extracted text content
- `page_image_path`: S3 path to page image
- `legally_significant`: Boolean flag

## Processing Steps

### 1. PDF Extraction

**Tools**: `pdf2image`, `PyPDF2`

- Convert each page to PNG image (200 DPI)
- Extract text from each page using PyPDF2

### 2. Page Analysis

**Model**: Claude Haiku (`claude-3-haiku-20240307`)

For each page:
1. Send page image (base64) + extracted text to Claude Haiku
2. Request:
   - Main topic/purpose of page
   - Key terms, obligations, provisions
   - Notable legal clauses
3. Receive 2-3 sentence summary
4. Store page summary

### 3. Document Analysis

**Model**: Claude Haiku (`claude-3-haiku-20240307`)

After processing all pages:
1. Combine all page summaries
2. Send combined summaries to Claude Haiku
3. Request:
   - Overall document summary (3-5 sentences)
   - List of legally significant pages
4. Parse response for:
   - Document summary
   - Page numbers of legally significant content

### 4. Storage

**S3/MinIO**:
- Original PDF: `documents/{doc_id}/{filename}`
- Page images: `documents/{doc_id}/pages/page_{num}.png`

**PostgreSQL**:
- Document record with metadata
- Page records with summaries and text
- Relationships maintained via foreign keys

## Legally Significant Pages

Claude Haiku identifies pages containing:

- Contractual obligations or commitments
- Liability or indemnification clauses
- Termination or renewal provisions
- Intellectual property rights
- Financial obligations or payment terms
- Regulatory compliance requirements
- Dispute resolution mechanisms
- Warranties or representations
- Material definitions or terms

## Usage

### Method 1: Web Upload

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@contract.pdf"
```

Response:
```json
{
  "id": "abc123",
  "filename": "contract.pdf",
  "summary": "Commercial lease agreement for office space...",
  "pages": 15,
  "uploaded_at": "2024-01-01T12:00:00"
}
```

### Method 2: Process Folder (API)

```bash
curl -X POST http://localhost:8000/api/documents/process-folder \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "/path/to/pdfs"}'
```

Response:
```json
{
  "message": "Processed 5 documents",
  "processed": [
    {
      "id": "abc123",
      "filename": "contract1.pdf",
      "summary": "...",
      "pages": 10
    },
    ...
  ]
}
```

### Method 3: CLI Utility

Process a folder:
```bash
cd backend
python process_documents.py /path/to/pdf/folder
```

Process a single file:
```bash
python process_documents.py /path/to/document.pdf
```

Output:
```
============================================================
Processing: contract.pdf
============================================================
INFO - Extracting images from PDF: contract.pdf
INFO - Extracted 15 pages as images
INFO - Extracting text from PDF: contract.pdf
INFO - Extracted text from 15 pages
INFO - Summarizing page 1 with Claude Haiku
INFO - Page 1 summarized: This page contains the title and parties...
...
INFO - Analyzing document with 15 pages using Claude Haiku
INFO - Document analysis complete. Significant pages: [1, 3, 7, 12]
✓ Successfully processed: contract.pdf
  Document ID: abc123
  Pages: 15
  Summary: Commercial lease agreement for office space...
```

## Performance

### Processing Time

Approximate times per document:

- **PDF Extraction**: 1-2 seconds per page
- **Claude Haiku (page)**: 2-3 seconds per page
- **Claude Haiku (document)**: 3-5 seconds
- **S3 Upload**: 1-2 seconds per page
- **Database Storage**: < 1 second

**Example**: 20-page document ≈ 90-120 seconds

### Cost Estimation

Claude Haiku pricing (as of 2024):
- Input: $0.25 per million tokens
- Output: $1.25 per million tokens

Typical document:
- 20 pages × ~1000 tokens/page = 20,000 input tokens
- 20 pages × ~100 tokens/summary = 2,000 output tokens
- Document analysis: ~2000 input + ~200 output tokens
- **Total cost**: ~$0.006 per 20-page document

## Error Handling

### PDF Processing Errors

If PDF extraction fails:
- Check PDF is not encrypted
- Verify PDF is not corrupted
- Ensure poppler-utils is installed (for pdf2image)

### Claude API Errors

If summarization fails:
- Fallback to text-only summary (first 200 chars)
- Continue processing remaining pages
- Log error for review

### Storage Errors

If S3 upload fails:
- Processing continues
- Database stores local paths as fallback
- Retry can be triggered manually

## Configuration

### Environment Variables

```bash
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxx

# S3/MinIO
S3_ENDPOINT=http://localhost:9000
S3_BUCKET=legal-documents
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/legaldd
```

### Model Configuration

To use a different model, edit `app/services/document_service.py`:

```python
# Change from claude-3-haiku-20240307 to:
model="claude-3-5-sonnet-20241022"  # More powerful but slower/costlier
```

## Querying Processed Documents

### Get All Documents

```python
from app.services.document_service import DocumentService

doc_service = DocumentService()
async with get_db() as db:
    documents = await doc_service.list_all(db)
```

### Get Document with Pages

```python
doc = await doc_service.get_by_id("abc123", db)

print(f"Document: {doc.filename}")
print(f"Summary: {doc.summary}")
print(f"Pages: {doc.page_count}")

for page in doc.pages:
    if page.legally_significant:
        print(f"  Page {page.page_num}: {page.summary}")
```

### Get Legally Significant Pages Only

```python
significant = [p for p in doc.pages if p.legally_significant]
for page in significant:
    print(f"Page {page.page_num}: {page.summary}")
    print(f"Text preview: {page.text[:200]}...")
```

## Troubleshooting

### "No module named 'pdf2image'"

Install dependencies:
```bash
pip install pdf2image PyPDF2 Pillow
apt-get install poppler-utils  # Linux
brew install poppler  # macOS
```

### "Failed to extract images from PDF"

Check if PDF is encrypted:
```bash
pdfinfo document.pdf
```

If encrypted, decrypt first:
```bash
qpdf --decrypt input.pdf output.pdf
```

### "Rate limit exceeded" from Anthropic

Add delay between requests:
```python
import asyncio
await asyncio.sleep(1)  # 1 second delay
```

Or process in smaller batches.

## Best Practices

1. **Batch Processing**: Process documents in batches of 10-20 at a time
2. **Monitoring**: Check logs for failed summaries
3. **Validation**: Spot-check summaries for accuracy
4. **Deduplication**: System automatically skips duplicate files (by hash)
5. **Backup**: Keep original PDFs as source of truth

## Future Enhancements

- [ ] Parallel page processing for faster throughput
- [ ] Support for scanned PDFs (OCR integration)
- [ ] Multi-language document support
- [ ] Custom prompt templates for different document types
- [ ] Confidence scores for legal significance detection
- [ ] Export processed data to JSON/CSV
- [ ] Web UI for monitoring processing status

---

For questions or issues, please file a GitHub issue.

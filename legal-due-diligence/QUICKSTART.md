# Quick Start Guide

Get the Legal Due Diligence application running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Anthropic API key ([Get one here](https://console.anthropic.com/))

## Step 1: Clone and Configure (2 minutes)

```bash
# Clone the repository
git clone <your-repo-url>
cd legal-due-diligence

# Create environment file
cp backend/.env.example backend/.env

# Edit .env and add your API key
nano backend/.env  # or use your preferred editor
```

**Required in `.env`:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Step 2: Start the Application (1 minute)

```bash
# Start all services (PostgreSQL, Redis, MinIO, Backend, Frontend)
docker-compose up -d

# Wait 30 seconds for services to initialize
sleep 30

# Check status
docker-compose ps
```

All services should show "Up" status.

## Step 3: Access the Application (10 seconds)

Open your browser:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (admin/minioadmin)

## Step 4: Upload Your First Document (1 minute)

### Option A: Via Web Interface

1. Go to http://localhost:3000
2. Click "Upload Document"
3. Select a PDF file
4. Wait for processing (~2 minutes per page)
5. View the processed document with AI-generated summaries

### Option B: Via Command Line

```bash
# Upload a single PDF
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/your/contract.pdf"

# Or process an entire folder
docker-compose exec backend python process_documents.py /path/to/pdf/folder
```

## Step 5: Start Due Diligence Session (30 seconds)

1. In the web interface, select processed documents
2. Click "Start Analysis"
3. Watch the agent work in real-time
4. Approve/reject agent actions as needed

## What Happens When You Upload a Document?

```
Your PDF → Extract pages as images + text
         ↓
         Claude Haiku analyzes each page (image + text)
         ↓
         Combined analysis identifies legally significant pages
         ↓
         Document stored with structured metadata
         ↓
         Ready for agent analysis!
```

**Processing time**: ~2-3 seconds per page
**Cost**: ~$0.006 per 20-page document

## Next Steps

### Explore the Features

- **View Documents**: See AI-generated summaries
- **Check Significant Pages**: Review flagged legal content
- **Start Agent Analysis**: Let the AI agent analyze your documents
- **Approve Actions**: Human-in-the-loop workflow
- **Generate Reports**: Create due diligence reports

### Upload More Documents

```bash
# Process multiple PDFs at once
docker-compose exec backend python process_documents.py /path/to/contracts

# Or use the API
curl -X POST http://localhost:8000/api/documents/process-folder \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "/path/to/pdfs"}'
```

### Monitor Processing

```bash
# View backend logs
docker-compose logs -f backend

# View database
docker-compose exec postgres psql -U postgres -d legaldd
```

## Common Issues

### "Connection refused" when accessing frontend

**Solution**: Wait 30-60 seconds for services to fully start
```bash
docker-compose ps
docker-compose logs frontend
```

### Document processing fails

**Solution**: Check your Anthropic API key is valid
```bash
docker-compose exec backend python -c "from app.config import settings; print(settings.ANTHROPIC_API_KEY)"
```

### "No module named..." errors

**Solution**: Rebuild containers
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Quick Reference

### Useful Commands

```bash
# View logs
docker-compose logs -f [service]

# Restart a service
docker-compose restart [service]

# Stop everything
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Access database
docker-compose exec postgres psql -U postgres -d legaldd

# Access backend shell
docker-compose exec backend bash

# Run migrations
docker-compose exec backend alembic upgrade head
```

### API Endpoints

- `GET /api/documents` - List all documents
- `POST /api/documents/upload` - Upload single PDF
- `POST /api/documents/process-folder` - Batch process
- `GET /api/documents/{id}` - Get document details
- `POST /api/sessions/start` - Start analysis session
- `GET /health` - Health check

### Default Credentials

- **MinIO**: `minioadmin` / `minioadmin`
- **PostgreSQL**: `postgres` / `postgres`

## Architecture Overview

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Browser   │─────▶│   Frontend   │◀─────│  WebSocket  │
│ :3000       │      │   (React)    │      │             │
└─────────────┘      └──────────────┘      └─────────────┘
                             │                      │
                             ▼                      │
                     ┌──────────────┐              │
                     │   FastAPI    │◀─────────────┘
                     │   Backend    │
                     │   :8000      │
                     └──────────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
     ┌───────────┐   ┌────────────┐   ┌──────────┐
     │PostgreSQL │   │   Redis    │   │  MinIO   │
     │  :5432    │   │   :6379    │   │  :9000   │
     └───────────┘   └────────────┘   └──────────┘
```

## Performance Tips

### For Large Documents (50+ pages)

Process in background:
```bash
docker-compose exec -d backend python process_documents.py /path/to/large.pdf
docker-compose logs -f backend  # Monitor progress
```

### For Many Documents (100+)

Process in batches of 10-20:
```bash
# Process first batch
ls /path/to/pdfs | head -20 | xargs -I {} docker-compose exec backend python process_documents.py /path/to/pdfs/{}

# Monitor and continue with next batch
```

## Ready to Go! 🚀

Your legal due diligence application is now running. Try uploading a contract PDF and watch the AI analyze it automatically!

### Need Help?

- Full documentation: [README.md](./README.md)
- Document processing details: [DOCUMENT_PROCESSING.md](./DOCUMENT_PROCESSING.md)
- API reference: http://localhost:8000/docs
- Issues: [GitHub Issues](https://github.com/your-repo/issues)

---

**Estimated time to first analysis**: 5 minutes setup + 2 minutes per document

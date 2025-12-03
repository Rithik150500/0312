# Legal Due Diligence Web Application

A comprehensive web application for AI-powered legal due diligence using deep agents architecture. This application enables legal teams to analyze documents in a data room with intelligent agent assistance and human-in-the-loop approval workflows.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Document Processing](#document-processing)
- [Project Structure](#project-structure)
- [Agent System](#agent-system)
- [Data Room Tools](#data-room-tools)
- [Approval Workflow](#approval-workflow)
- [UI Layout](#ui-layout)
- [Development](#development)
- [API Documentation](#api-documentation)

## 🎯 Overview

This application implements a deep agents framework for legal due diligence with the following capabilities:

- **Document Analysis**: Upload and analyze legal documents with AI-powered insights
- **Agent Hierarchy**: Main agent with specialized subagents for analysis and reporting
- **Human Approval**: Interactive approval workflow for critical agent actions
- **Visual Feedback**: Real-time highlights of documents, pages, and files being accessed
- **Context-Aware**: Rich approval context showing why the agent needs access

## 🏗️ Architecture

### Agent Hierarchy

```
Legal Due Diligence Agent (Main)
├── Analysis Subagent (unlimited use)
│   ├── Data Room Tools
│   ├── Web Research Tools
│   └── General Purpose Subagent
└── Create Report Subagent (single use)
    └── File System Tools
```

### System Components

1. **Backend** (FastAPI + Python)
   - Document management and processing
   - Agent orchestration with LangChain/LangGraph
   - WebSocket for real-time communication
   - PostgreSQL for data persistence

2. **Frontend** (React + TypeScript)
   - Responsive UI with dynamic layout
   - Real-time agent workflow visualization
   - PDF viewer with highlighting
   - File editor for agent-created documents

3. **Data Room**
   - Document storage (S3/MinIO)
   - PDF processing and OCR
   - Page-level summaries
   - Legally significant page detection

## ✨ Features

### Document Processing (Claude Haiku)

- **Automatic PDF Processing**: Upload PDFs and get AI-generated summaries
- **Page-Level Analysis**: Each page analyzed with vision AI (image + text)
- **Document Summaries**: Claude Haiku generates comprehensive document summaries
- **Legal Significance Detection**: Automatically identifies critical pages
- **Batch Processing**: Process entire folders of documents at once
- **Deduplication**: Smart file hash checking prevents duplicate processing

### Agent Capabilities

- **Legal Due Diligence Agent**: Orchestrates the overall analysis process
- **Analysis Subagent**: Performs deep analysis of documents and legal issues
- **Report Subagent**: Generates comprehensive due diligence reports
- **Task Management**: Built-in todo list for tracking analysis progress

### Data Room Tools

- `list_data_room_documents`: List all documents with summaries
- `get_documents`: Get detailed document info with page summaries and legally significant pages
- `get_page_text`: Retrieve full text of specific pages
- `get_page_image`: Get page images (limited use for visual elements)

### Web Research Tools

- `web_search`: Search for legal information
- `web_fetch`: Fetch content from specific URLs (limited use)

### Approval Workflow

Human approval required for:
- Document access (`get_documents`, `get_page_text`, `get_page_image`)
- File operations (`write_file`, `edit_file`)
- Web research (`web_search`, `web_fetch`)
- Subagent tasks (`analyze_documents`, `create_report`)

### UI Features

- **Dynamic Layout**: Left panel (20%/40%), Center (60%/20%), Right panel (20%/40%)
- **Document Highlights**: Visual indicators when agent requests documents
- **Page Highlights**: Highlighting of legally significant and requested pages
- **File Highlights**: Shows files being created or edited by agent
- **Real-time Workflow**: Live view of agent actions and reasoning
- **Todo Tracking**: Current tasks and progress

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Async web framework
- **LangChain**: LLM framework
- **LangGraph**: Agent orchestration
- **Anthropic Claude**: LLM provider
- **SQLAlchemy**: ORM
- **PostgreSQL**: Database
- **Redis**: State management
- **MinIO**: Object storage
- **PyPDF2**: PDF processing

### Frontend
- **React 18**: UI library
- **TypeScript**: Type safety
- **Zustand**: State management
- **Vite**: Build tool
- **PDF.js**: PDF rendering
- **Monaco Editor**: Code editor

## 🚀 Getting Started

### ⚡ Quick Start (5 Minutes)

```bash
# 1. Clone and configure
git clone <repository-url>
cd legal-due-diligence
cp backend/.env.example backend/.env
# Add your ANTHROPIC_API_KEY to backend/.env

# 2. Start everything
docker-compose up -d

# 3. Open browser
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

**First upload:**
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@contract.pdf"
```

👉 **See [QUICKSTART.md](./QUICKSTART.md) for detailed 5-minute setup guide**

### Prerequisites

- Docker and Docker Compose
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- Node.js 20+ (optional, for local frontend development)
- Python 3.11+ (optional, for local backend development)

### Full Setup with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd legal-due-diligence
```

2. Create environment file:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env and add your ANTHROPIC_API_KEY
```

3. Start all services:
```bash
docker-compose up -d
```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - MinIO Console: http://localhost:9001

### Local Development

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Set up database
alembic upgrade head

# Run server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📄 Document Processing

The application includes an advanced document processing system powered by Claude Haiku that automatically analyzes legal PDFs.

### Processing Pipeline

```
PDF Upload
    ↓
Extract Pages (Images + Text)
    ↓
For Each Page: Claude Haiku Vision Analysis
    ├─ Input: Page Image + Extracted Text
    └─ Output: Page Summary
    ↓
Combine Page Summaries
    ↓
Document Analysis: Claude Haiku
    ├─ Input: All Page Summaries
    └─ Output: Document Summary + Legally Significant Pages
    ↓
Store in PostgreSQL + S3
```

### Upload Documents

**Via Web API:**
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@contract.pdf"
```

**Response:**
```json
{
  "id": "abc123",
  "filename": "contract.pdf",
  "summary": "Commercial lease agreement for office space with 5-year term...",
  "pages": 15,
  "uploaded_at": "2024-01-01T12:00:00"
}
```

### Batch Processing

**Process entire folder:**
```bash
python backend/process_documents.py /path/to/pdf/folder
```

**Via API:**
```bash
curl -X POST http://localhost:8000/api/documents/process-folder \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "/path/to/pdfs"}'
```

### What Gets Extracted

For each document:
- **Document ID**: Unique identifier
- **Document Summary**: AI-generated overview (3-5 sentences)
- **Page Count**: Total number of pages
- **Pages**: Array of page objects with:
  - Page number
  - Page summary (AI-generated)
  - Extracted text
  - Page image path (S3)
  - Legally significant flag

### Legally Significant Pages

Claude Haiku automatically identifies pages containing:
- Contractual obligations or commitments
- Liability or indemnification clauses
- Termination or renewal provisions
- Intellectual property rights
- Financial obligations or payment terms
- Regulatory compliance requirements
- Dispute resolution mechanisms
- Warranties or representations
- Material definitions or terms

### Performance & Cost

**Processing Time** (20-page document):
- ~90-120 seconds total
- ~2-3 seconds per page for analysis

**Cost** (Claude Haiku):
- ~$0.006 per 20-page document
- Extremely cost-effective for bulk processing

### Detailed Documentation

See [DOCUMENT_PROCESSING.md](./DOCUMENT_PROCESSING.md) for comprehensive documentation including:
- Detailed architecture
- Error handling
- Configuration options
- Troubleshooting guide
- API examples

## 📁 Project Structure

```
legal-due-diligence/
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI application
│   │   ├── config.py                    # Configuration
│   │   ├── database.py                  # Database setup
│   │   ├── models.py                    # SQLAlchemy models
│   │   ├── services/
│   │   │   ├── agent_service.py         # Agent implementation
│   │   │   ├── document_service.py      # Document processing with Claude Haiku
│   │   │   ├── pdf_processor.py         # PDF extraction utilities
│   │   │   └── storage_client.py        # S3/MinIO client
│   │   ├── tools/
│   │   │   └── data_room_tools.py       # Data room tools
│   │   ├── middleware/
│   │   │   └── approval.py              # Approval workflow
│   │   └── websocket/
│   │       └── connection_manager.py
│   ├── process_documents.py             # CLI for batch processing
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/                  # React components
│   │   ├── stores/                      # Zustand stores
│   │   ├── api/                         # API client
│   │   ├── types/                       # TypeScript types
│   │   ├── styles/                      # CSS files
│   │   ├── App.tsx                      # Main app
│   │   └── main.tsx                     # Entry point
│   ├── package.json
│   └── Dockerfile
├── DOCUMENT_PROCESSING.md               # Processing guide
├── README.md
└── docker-compose.yml
```

## 🤖 Agent System

### Main Agent: Legal Due Diligence

**Purpose**: Orchestrate the overall legal due diligence process

**System Prompt**: Specialized for legal document review, risk identification, and coordination

**Tools**:
- Subagent delegation (Analysis, Create Report)
- File system operations

**Workflow**:
1. Review all documents in data room
2. Identify priority documents
3. Delegate analysis to Analysis subagent
4. Organize findings
5. Generate final report via Create Report subagent

### Analysis Subagent

**Purpose**: Detailed legal analysis of documents and issues

**System Prompt**: Specialized for identifying key terms, obligations, risks, and unusual clauses

**Tools**:
- Data room tools
- Web research tools
- General purpose subagent
- File system operations

**Analysis Areas**:
- Contractual obligations
- Liability and indemnification
- Termination provisions
- IP rights
- Regulatory compliance
- Financial obligations
- Dispute resolution
- Change of control

### Create Report Subagent

**Purpose**: Generate comprehensive due diligence reports

**System Prompt**: Specialized for report structuring and formatting

**Tools**:
- File system operations

**Report Structure**:
1. Executive Summary
2. Documents Reviewed
3. Key Findings (High/Medium/Low Risk)
4. Detailed Analysis by Document
5. Recommendations
6. Appendices

## 📊 Data Room Tools

### list_data_room_documents

```python
Returns: All documents with:
- Document ID
- Summary
- Page count
```

### get_documents

```python
Args: doc_ids (List[str])

Returns: For each document:
- All pages with summaries (page num, summary)
- Full text of legally significant pages
```

### get_page_text

```python
Args:
- doc_id (str)
- page_nums (List[int])

Returns: Full text of requested pages
```

### get_page_image

```python
Args:
- doc_id (str)
- page_nums (List[int])

Returns: Image paths for pages

Note: Use sparingly for visual elements only
```

## ✅ Approval Workflow

### Approval Context

When the agent requests approval, the UI provides rich context:

**Document Highlights**:
- Document ID and reason for access
- Legally significant pages
- Page summaries

**Page Highlights**:
- Specific pages requested
- Context/reasoning

**File Highlights**:
- File path
- Operation (write/edit)
- Content preview

**Agent Reasoning**:
- What the agent is trying to accomplish
- Recent thoughts/analysis

**Related Todos**:
- Current in-progress tasks
- Context of where this fits in the workflow

### Approval Decisions

- **Approve**: Allow the action as requested
- **Edit**: Modify the tool arguments before execution
- **Reject**: Deny the action

## 🎨 UI Layout

### Layout Modes

**Default (no selections)**:
- Left: 20% - Data Room Documents
- Center: 60% - Todos (25%) + Workflow (75%)
- Right: 20% - File List

**Document Selected**:
- Left: 40% - PDF Viewer
- Center: 40% - Todos + Workflow
- Right: 20% - File List

**File Selected**:
- Left: 20% - Data Room Documents
- Center: 40% - Todos + Workflow
- Right: 40% - File Editor

**Both Selected**:
- Left: 40% - PDF Viewer
- Center: 20% - Todos + Workflow
- Right: 40% - File Editor

### Component Features

**PDF Viewer**:
- Page navigation
- Collapsible sidebar with page summaries
- Highlights for:
  - Legally significant pages (red border)
  - Agent-requested pages (orange border)

**File Editor**:
- File list with highlights
- Content editor
- Real-time updates from agent

**Approval Panel**:
- Modal overlay
- Full approval context
- Approve/Edit/Reject actions
- JSON editor for tool arguments

## 🔧 Development

### Adding Custom Tools

```python
# backend/app/tools/custom_tools.py
from langchain.tools import tool

@tool
async def my_custom_tool(arg: str) -> str:
    """Tool description for the agent."""
    # Implementation
    return result
```

### Adding Approval for Tools

```python
# backend/app/middleware/approval.py
APPROVAL_REQUIRED_TOOLS = {
    "my_custom_tool",  # Add your tool here
    # ...
}
```

### Extending Approval Context

```python
# In ApprovalContextBuilder
async def _build_custom_context(self, ...):
    # Build custom approval context
    return ApprovalContext(...)
```

## 📚 API Documentation

### REST Endpoints

**Documents**:
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List all documents
- `GET /api/documents/{id}` - Get document details
- `GET /api/documents/{id}/pdf` - Get PDF file

**Sessions**:
- `POST /api/sessions/start` - Start new session
- `GET /api/sessions/{id}` - Get session details

**Health**:
- `GET /health` - Health check

### WebSocket

**Connection**: `ws://localhost:8000/ws/{session_id}`

**Message Types**:

From Server:
- `approval_request` - Request user approval
- `agent_status` - Agent status update
- `todos_update` - Todo list update
- `workflow_event` - Workflow event

To Server:
- `approval_decision` - User's approval decision

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/) and [LangGraph](https://langchain.com/langgraph)
- Powered by [Anthropic Claude](https://anthropic.com/)
- UI inspired by modern legal tech platforms

---

For questions or support, please open an issue on GitHub.

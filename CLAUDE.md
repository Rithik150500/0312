# Deep Agents Framework - Legal Due Diligence

## Project Overview

This repository contains documentation and implementation guides for a deep agents framework designed for legal due diligence workflows. The system leverages LangGraph and the DeepAgents harness to create an AI-powered application that can analyze legal documents, interact with data rooms, and provide intelligent assistance with human-in-the-loop approval workflows.

## Architecture

The project is built on the **DeepAgents** agent harness, which provides:

- **File System Tools**: Read, write, edit, glob, grep operations
- **Task Delegation**: Subagents for isolated multi-step tasks
- **Storage Backends**: State, Filesystem, Store, and Composite backends
- **Human-in-the-Loop**: Approval workflows for critical operations
- **Long-term Memory**: Persistent storage across conversations
- **Tool Result Eviction**: Automatic handling of large tool outputs

## Key Components

### 1. Agent Harness Capabilities
The core agent loop with built-in tools and middleware for file operations, task delegation, and context management.

**File**: `# Agent harness capabilities`

### 2. Storage Backends
Multiple storage strategies for different use cases:
- **StateBackend**: Ephemeral in-memory storage
- **FilesystemBackend**: Real filesystem access with sandboxing
- **StoreBackend**: Persistent cross-conversation storage
- **CompositeBackend**: Route paths to different backends

**File**: `# Backends`

### 3. Subagents
Task delegation system allowing the main agent to create specialized subagents for isolated work.

**File**: `# Subagents`

### 4. Human-in-the-Loop
Approval workflows that pause agent execution for human verification before critical operations.

**File**: `# Human-in-the-loop`

### 5. Long-term Memory
Persistent memory system using LangGraph's Store for cross-conversation knowledge retention.

**File**: `# Long-term memory`

### 6. Deep Agents Middleware
LangGraph middleware components for:
- Approval workflows
- Tool result eviction
- Memory integration
- Prompt caching

**File**: `# Deep Agents Middleware`

### 7. Web Application
Full-stack implementation with FastAPI backend and React frontend for legal document analysis.

**File**: `# Web Application Implementation`

## Technology Stack

### Backend
- **FastAPI**: Web framework with async support
- **LangGraph**: Agent orchestration
- **SQLAlchemy**: Database ORM
- **PostgreSQL**: Primary database
- **Redis**: State management
- **Anthropic Claude**: LLM provider

### Frontend
- **React**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Zustand**: State management
- **WebSocket**: Real-time communication
- **PDF.js**: Document viewing

## Use Case: Legal Due Diligence

The reference implementation demonstrates:

1. **Document Upload**: Upload legal PDFs to a virtual data room
2. **Agent Analysis**: AI agent analyzes documents using specialized tools
3. **Approval Workflow**: Human reviews and approves agent actions
4. **Context Awareness**: Agent maintains context with document highlights, page references, and file operations
5. **Visual Feedback**: UI highlights documents, pages, and files as the agent requests them

## Data Room Tools

The agent has access to specialized tools for legal document analysis:

- `list_data_room_documents`: List all available documents
- `get_documents`: Get detailed document info including page summaries
- `get_page_text`: Retrieve full text of specific pages
- `get_page_image`: Get page images for visual elements

## Approval Context

When the agent requests access to documents or files, the system builds rich approval context including:

- **Document Highlights**: Which documents and why
- **Page Highlights**: Specific pages and their relevance
- **File Highlights**: File operations with content previews
- **Agent Reasoning**: What the agent is trying to accomplish
- **Related Todos**: Current tasks in progress

## Development Guidelines

### Working with this Repository

1. **Reading Documentation**: All documentation files use markdown format with "#" prefix
2. **Code Examples**: Implementation examples are embedded in documentation files
3. **Architecture Patterns**: Follow the patterns established in the Web Application Implementation

### Adding New Features

When extending this framework:

1. **Custom Tools**: Add domain-specific tools following the data room tools pattern
2. **Storage Strategy**: Choose appropriate backend(s) for your use case
3. **Approval Points**: Define which operations require human approval
4. **Subagents**: Create specialized subagents for complex subtasks

### Testing Approach

- Unit tests for individual tools and middleware
- Integration tests for agent workflows
- End-to-end tests for web application flows

## Git Workflow

Current branch: `claude/create-claude-md-01RtyZvdQo9okNdaQzFBj9DS`

All development should occur on Claude-prefixed branches following the naming convention:
`claude/<description>-<session-id>`

## Repository Structure

```
/home/user/0312/
├── # Agent harness capabilities    - Core harness documentation
├── # Backends                       - Storage backend implementations
├── # Deep Agents Middleware         - LangGraph middleware components
├── # Human-in-the-loop             - Approval workflow system
├── # Long-term memory              - Persistent memory implementation
├── # Subagents                     - Task delegation system
├── # Web Application Implementation - Full-stack reference app
└── CLAUDE.md                       - This file
```

## Quick Start

To understand the system:

1. Start with `# Agent harness capabilities` for core concepts
2. Review `# Backends` to understand storage options
3. Read `# Human-in-the-loop` for approval workflows
4. Explore `# Web Application Implementation` for a complete example

## References

- [LangGraph Documentation](https://docs.langchain.com/)
- [DeepAgents Framework](https://docs.langchain.com/oss/deepagents/)
- [Anthropic Claude API](https://docs.anthropic.com/)

## Contact & Contribution

This is a documentation and reference implementation repository. When working with this codebase:

- Follow the established architecture patterns
- Maintain clear separation between agent logic and UI
- Document new tools and middleware components
- Test approval workflows thoroughly

---

**Note**: This framework is designed for legal due diligence but can be adapted for any domain requiring document analysis, human oversight, and intelligent agent assistance.

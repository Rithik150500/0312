/**
 * Main App Component
 *
 * Implements the layout structure:
 * - Left 20%: Data Room Documents
 * - Center Top 25%: Todos Plan
 * - Center 75%: Agent Workflow
 * - Right 20%: Files
 * - Left 40%: PDF Viewer (dynamic)
 * - Right 40%: File Editor (dynamic)
 * - Center: Dynamic width based on selections
 */
import React, { useEffect } from 'react';
import { useAppStore } from './stores/appStore';
import { api } from './api/client';

// Components
import { DocumentList } from './components/DocumentList';
import { TodoPanel } from './components/TodoPanel';
import { WorkflowPanel } from './components/WorkflowPanel';
import { PDFViewer } from './components/PDFViewer';
import { FileEditor } from './components/FileEditor';
import { ApprovalPanel } from './components/ApprovalPanel';

// Styles
import './styles/App.css';

function App() {
  const sessionId = useAppStore(state => state.sessionId);
  const selectedDocumentId = useAppStore(state => state.selectedDocumentId);
  const selectedFilePath = useAppStore(state => state.selectedFilePath);
  const setDocuments = useAppStore(state => state.setDocuments);
  const connect = useAppStore(state => state.connect);

  // Load documents on mount
  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await api.listDocuments();
      setDocuments(response.documents);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleStartSession = async () => {
    try {
      const documents = useAppStore.getState().documents;
      const session = await api.startSession(
        'Legal Due Diligence',
        documents.map(d => d.id)
      );

      connect(session.session_id);
    } catch (error) {
      console.error('Failed to start session:', error);
    }
  };

  // Calculate dynamic widths
  const hasDocumentSelected = !!selectedDocumentId;
  const hasFileSelected = !!selectedFilePath;

  let leftWidth = 20;
  let centerWidth = 60;
  let rightWidth = 20;

  if (hasDocumentSelected && hasFileSelected) {
    leftWidth = 40;
    centerWidth = 20;
    rightWidth = 40;
  } else if (hasDocumentSelected) {
    leftWidth = 40;
    centerWidth = 40;
    rightWidth = 20;
  } else if (hasFileSelected) {
    leftWidth = 20;
    centerWidth = 40;
    rightWidth = 40;
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <h1>⚖️ Legal Due Diligence</h1>
        <div className="header-actions">
          {!sessionId ? (
            <button className="btn btn-primary" onClick={handleStartSession}>
              Start Analysis
            </button>
          ) : (
            <span className="session-badge">Session: {sessionId}</span>
          )}
        </div>
      </header>

      {/* Main Layout */}
      <div className="app-layout">
        {/* Left Panel */}
        <div className="panel panel-left" style={{ width: `${leftWidth}%` }}>
          {hasDocumentSelected ? (
            <PDFViewer />
          ) : (
            <DocumentList />
          )}
        </div>

        {/* Center Panel */}
        <div className="panel panel-center" style={{ width: `${centerWidth}%` }}>
          <div className="center-top" style={{ height: '25%' }}>
            <TodoPanel />
          </div>
          <div className="center-bottom" style={{ height: '75%' }}>
            <WorkflowPanel />
          </div>
        </div>

        {/* Right Panel */}
        <div className="panel panel-right" style={{ width: `${rightWidth}%` }}>
          {hasFileSelected ? (
            <FileEditor />
          ) : (
            <div className="file-list-placeholder">
              <DocumentList />
            </div>
          )}
        </div>
      </div>

      {/* Approval Panel (Overlay) */}
      <ApprovalPanel />
    </div>
  );
}

export default App;

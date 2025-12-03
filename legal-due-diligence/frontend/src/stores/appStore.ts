/**
 * Zustand store for application state management
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type {
  Document,
  DocumentDetail,
  ApprovalRequest,
  UIState,
  Todo,
  WorkflowEvent,
  AgentFile
} from '../types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

interface AppState {
  // Session
  sessionId: string | null;
  ws: WebSocket | null;
  uiState: UIState;

  // Documents
  documents: Document[];
  selectedDocumentId: string | null;
  selectedDocumentDetail: DocumentDetail | null;
  highlightedDocumentIds: Set<string>;
  highlightedPages: Map<string, Set<number>>;

  // Files
  files: Map<string, AgentFile>;
  selectedFilePath: string | null;
  highlightedFilePaths: Set<string>;

  // PDF Viewer
  currentPdfPage: number;

  // Todos
  todos: Todo[];

  // Workflow
  workflowEvents: WorkflowEvent[];

  // Layout
  leftPanelWidth: number;
  rightPanelWidth: number;
  centerTopHeight: number;

  // Actions
  connect: (sessionId: string) => void;
  disconnect: () => void;
  submitDecision: (decision: any) => void;
  selectDocument: (docId: string) => Promise<void>;
  selectFile: (filePath: string) => void;
  setDocuments: (docs: Document[]) => void;
  setCurrentPdfPage: (page: number) => void;
  updateFile: (path: string, content: string) => void;
  setLayoutWidth: (panel: 'left' | 'right', width: number) => void;
  setLayoutHeight: (section: 'centerTop', height: number) => void;
}

export const useAppStore = create<AppState>()(
  devtools((set, get) => ({
    // Initial state
    sessionId: null,
    ws: null,
    uiState: { type: 'idle' },
    documents: [],
    selectedDocumentId: null,
    selectedDocumentDetail: null,
    highlightedDocumentIds: new Set(),
    highlightedPages: new Map(),
    files: new Map(),
    selectedFilePath: null,
    highlightedFilePaths: new Set(),
    currentPdfPage: 1,
    todos: [],
    workflowEvents: [],
    leftPanelWidth: 20,
    rightPanelWidth: 20,
    centerTopHeight: 25,

    // Connect to WebSocket
    connect: (sessionId: string) => {
      const ws = new WebSocket(`${WS_URL}/ws/${sessionId}`);

      ws.onopen = () => {
        console.log('WebSocket connected');
        set({ sessionId, ws, uiState: { type: 'agent_running' } });
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log('WebSocket message:', message);

        switch (message.type) {
          case 'approval_request':
            handleApprovalRequest(message.data, set, get);
            break;

          case 'agent_status':
            handleAgentStatus(message.data, set);
            break;

          case 'todos_update':
            handleTodosUpdate(message.data, set);
            break;

          case 'workflow_event':
            handleWorkflowEvent(message.data, set, get);
            break;

          default:
            console.warn('Unknown message type:', message.type);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        set({ uiState: { type: 'error', message: 'Connection error' } });
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        set({ ws: null });
      };

      set({ sessionId, ws });
    },

    // Disconnect WebSocket
    disconnect: () => {
      const { ws } = get();
      if (ws) {
        ws.close();
        set({ ws: null, sessionId: null });
      }
    },

    // Submit approval decision
    submitDecision: (decision: any) => {
      const { ws, uiState } = get();

      if (!ws || uiState.type !== 'awaiting_approval') {
        console.error('Cannot submit decision: not awaiting approval');
        return;
      }

      ws.send(JSON.stringify({
        type: 'approval_decision',
        request_id: uiState.request.request_id,
        decision
      }));

      // Clear highlights and return to running state
      set({
        uiState: { type: 'agent_running' },
        highlightedDocumentIds: new Set(),
        highlightedPages: new Map(),
        highlightedFilePaths: new Set()
      });
    },

    // Select a document
    selectDocument: async (docId: string) => {
      set({ selectedDocumentId: docId, currentPdfPage: 1 });

      // Fetch detailed document info
      try {
        const response = await fetch(`http://localhost:8000/api/documents/${docId}`);
        const detail = await response.json();
        set({ selectedDocumentDetail: detail });
      } catch (error) {
        console.error('Failed to fetch document detail:', error);
      }
    },

    // Select a file
    selectFile: (filePath: string) => {
      set({ selectedFilePath: filePath });
    },

    // Set documents list
    setDocuments: (docs: Document[]) => {
      set({ documents: docs });
    },

    // Set current PDF page
    setCurrentPdfPage: (page: number) => {
      set({ currentPdfPage: page });
    },

    // Update file content
    updateFile: (path: string, content: string) => {
      const files = new Map(get().files);
      files.set(path, {
        path,
        content,
        updated_at: new Date().toISOString()
      });
      set({ files });
    },

    // Set layout dimensions
    setLayoutWidth: (panel: 'left' | 'right', width: number) => {
      if (panel === 'left') {
        set({ leftPanelWidth: width });
      } else {
        set({ rightPanelWidth: width });
      }
    },

    setLayoutHeight: (section: 'centerTop', height: number) => {
      set({ centerTopHeight: height });
    }
  }))
);

// Helper functions for message handling

function handleApprovalRequest(data: ApprovalRequest, set: any, get: any) {
  const request = data as ApprovalRequest;

  // Extract highlights
  const docIds = new Set(request.document_highlights.map(dh => dh.doc_id));
  const pageHighlights = new Map<string, Set<number>>();

  request.document_highlights.forEach(dh => {
    pageHighlights.set(dh.doc_id, new Set(dh.legally_significant_pages));
  });

  request.page_highlights.forEach(ph => {
    const existing = pageHighlights.get(ph.doc_id) || new Set();
    ph.page_nums.forEach(num => existing.add(num));
    pageHighlights.set(ph.doc_id, existing);
  });

  const fileHighlights = new Set(request.file_highlights.map(fh => fh.file_path));

  // Auto-select first highlighted document if none selected
  const currentSelected = get().selectedDocumentId;
  const newSelected = docIds.size > 0 && !currentSelected
    ? Array.from(docIds)[0]
    : currentSelected;

  set({
    uiState: { type: 'awaiting_approval', request },
    highlightedDocumentIds: docIds,
    highlightedPages: pageHighlights,
    highlightedFilePaths: fileHighlights,
    selectedDocumentId: newSelected
  });
}

function handleAgentStatus(data: any, set: any) {
  const { status, details } = data;

  if (status === 'completed') {
    set({ uiState: { type: 'completed' } });
  } else if (status === 'failed') {
    set({ uiState: { type: 'error', message: details } });
  } else if (status === 'running') {
    set({ uiState: { type: 'agent_running' } });
  }
}

function handleTodosUpdate(data: any, set: any) {
  const { todos } = data;
  set({ todos });
}

function handleWorkflowEvent(data: any, set: any, get: any) {
  const event = {
    event_type: data.event_type,
    data: data.data,
    timestamp: new Date().toISOString()
  };

  const events = [...get().workflowEvents, event];
  set({ workflowEvents: events });
}

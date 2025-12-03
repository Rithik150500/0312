/**
 * API client for backend communication
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Document {
  id: string;
  filename: string;
  summary: string;
  pages: number;
  uploaded_at: string;
}

export interface DocumentDetail extends Document {
  page_count: number;
  pages: Array<{
    num: number;
    summary: string;
    legally_significant: boolean;
  }>;
}

export interface Session {
  session_id: string;
  status: string;
  documents: number;
}

export const api = {
  /**
   * Start a new due diligence session
   */
  async startSession(projectName: string, documentIds: string[]): Promise<Session> {
    const response = await fetch(`${API_BASE}/api/sessions/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_name: projectName,
        document_ids: documentIds
      })
    });

    if (!response.ok) {
      throw new Error('Failed to start session');
    }

    return response.json();
  },

  /**
   * Get session details
   */
  async getSession(sessionId: string): Promise<Session> {
    const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`);

    if (!response.ok) {
      throw new Error('Failed to get session');
    }

    return response.json();
  },

  /**
   * Upload a document
   */
  async uploadDocument(file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/documents/upload`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error('Failed to upload document');
    }

    return response.json();
  },

  /**
   * List all documents
   */
  async listDocuments(): Promise<{ documents: Document[] }> {
    const response = await fetch(`${API_BASE}/api/documents`);

    if (!response.ok) {
      throw new Error('Failed to list documents');
    }

    return response.json();
  },

  /**
   * Get document details
   */
  async getDocument(documentId: string): Promise<DocumentDetail> {
    const response = await fetch(`${API_BASE}/api/documents/${documentId}`);

    if (!response.ok) {
      throw new Error('Failed to get document');
    }

    return response.json();
  }
};

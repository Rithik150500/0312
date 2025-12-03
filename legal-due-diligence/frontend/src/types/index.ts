/**
 * TypeScript type definitions for the Legal Due Diligence application
 */

export interface Document {
  id: string;
  filename: string;
  summary: string;
  pages: number;
  uploaded_at: string;
}

export interface DocumentPage {
  num: number;
  summary: string;
  legally_significant: boolean;
}

export interface DocumentDetail extends Document {
  page_count: number;
  pages: DocumentPage[];
}

export interface Session {
  session_id: string;
  status: string;
  documents: number;
}

export interface ApprovalRequest {
  request_id: string;
  tool_name: string;
  tool_args: Record<string, any>;
  allowed_decisions: string[];
  document_highlights: DocumentHighlight[];
  page_highlights: PageHighlight[];
  file_highlights: FileHighlight[];
  agent_reasoning: string;
  related_todos: string[];
  timestamp: string;
}

export interface DocumentHighlight {
  doc_id: string;
  reason: string;
  legally_significant_pages: number[];
  all_pages_summary: Record<number, string>;
}

export interface PageHighlight {
  doc_id: string;
  page_nums: number[];
  context: string;
}

export interface FileHighlight {
  file_path: string;
  operation: 'write' | 'edit';
  content_preview: string;
}

export interface Todo {
  content: string;
  status: 'pending' | 'in_progress' | 'completed';
  activeForm: string;
}

export interface WorkflowEvent {
  event_type: string;
  data: any;
  timestamp: string;
}

export interface AgentFile {
  path: string;
  content: string;
  updated_at: string;
}

export type UIState =
  | { type: 'idle' }
  | { type: 'agent_running' }
  | { type: 'awaiting_approval'; request: ApprovalRequest }
  | { type: 'completed' }
  | { type: 'error'; message: string };

/**
 * Approval Panel Component
 *
 * Displays approval requests from the agent with rich context:
 * - Agent's reasoning
 * - Related todos
 * - Document/page/file highlights
 * - Approve/Edit/Reject actions
 */
import React, { useState } from 'react';
import { useAppStore } from '../stores/appStore';
import '../styles/ApprovalPanel.css';

export const ApprovalPanel: React.FC = () => {
  const uiState = useAppStore(state => state.uiState);
  const submitDecision = useAppStore(state => state.submitDecision);

  const [isEditing, setIsEditing] = useState(false);
  const [editedArgs, setEditedArgs] = useState<string>('');

  if (uiState.type !== 'awaiting_approval') {
    return null;
  }

  const { request } = uiState;
  const canEdit = request.allowed_decisions.includes('edit');
  const canReject = request.allowed_decisions.includes('reject');

  const handleApprove = () => {
    submitDecision({ type: 'approve' });
    setIsEditing(false);
  };

  const handleEdit = () => {
    if (isEditing) {
      try {
        const parsed = JSON.parse(editedArgs);
        submitDecision({
          type: 'edit',
          edited_action: {
            name: request.tool_name,
            args: parsed
          }
        });
        setIsEditing(false);
      } catch (e) {
        alert('Invalid JSON. Please check your edits.');
      }
    } else {
      setEditedArgs(JSON.stringify(request.tool_args, null, 2));
      setIsEditing(true);
    }
  };

  const handleReject = () => {
    submitDecision({ type: 'reject', reason: 'User rejected' });
    setIsEditing(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  return (
    <div className="approval-panel-overlay">
      <div className="approval-panel">
        {/* Header */}
        <div className="approval-header">
          <div>
            <h2>🔔 Approval Required</h2>
            <span className="tool-badge">{request.tool_name}</span>
          </div>
          <div className="approval-timestamp">
            {new Date(request.timestamp).toLocaleTimeString()}
          </div>
        </div>

        {/* Content */}
        <div className="approval-content">
          {/* Agent's Intent */}
          <div className="approval-section">
            <h3>Agent's Intent</h3>
            <p className="agent-reasoning">{request.agent_reasoning}</p>
          </div>

          {/* Related Tasks */}
          {request.related_todos.length > 0 && (
            <div className="approval-section">
              <h3>Related Tasks</h3>
              <ul className="related-todos">
                {request.related_todos.map((todo, i) => (
                  <li key={i}>{todo}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Requested Action */}
          <div className="approval-section">
            <h3>Requested Action</h3>
            {isEditing ? (
              <div className="editing-section">
                <textarea
                  className="args-editor"
                  value={editedArgs}
                  onChange={(e) => setEditedArgs(e.target.value)}
                  rows={10}
                  spellCheck={false}
                />
                <div className="editing-hint">
                  Edit the JSON above to modify the tool arguments
                </div>
              </div>
            ) : (
              <pre className="args-display">
                {JSON.stringify(request.tool_args, null, 2)}
              </pre>
            )}
          </div>

          {/* Document Highlights */}
          {request.document_highlights.length > 0 && (
            <div className="approval-section">
              <h3>Documents ({request.document_highlights.length})</h3>
              <div className="highlights-list">
                {request.document_highlights.map((dh, i) => (
                  <div key={i} className="highlight-item document-highlight">
                    <div className="highlight-header">
                      <strong>📄 {dh.doc_id}</strong>
                      <span className="page-count-badge">
                        {dh.legally_significant_pages.length} significant pages
                      </span>
                    </div>
                    <p className="highlight-reason">{dh.reason}</p>
                    {dh.legally_significant_pages.length > 0 && (
                      <div className="page-numbers">
                        Pages: {dh.legally_significant_pages.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Page Highlights */}
          {request.page_highlights.length > 0 && (
            <div className="approval-section">
              <h3>Specific Pages</h3>
              <div className="highlights-list">
                {request.page_highlights.map((ph, i) => (
                  <div key={i} className="highlight-item page-highlight">
                    <div className="highlight-header">
                      <strong>📑 {ph.doc_id}</strong>
                    </div>
                    <div className="page-numbers">
                      Pages: {ph.page_nums.join(', ')}
                    </div>
                    <p className="highlight-context">{ph.context}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* File Highlights */}
          {request.file_highlights.length > 0 && (
            <div className="approval-section">
              <h3>Files</h3>
              <div className="highlights-list">
                {request.file_highlights.map((fh, i) => (
                  <div key={i} className="highlight-item file-highlight">
                    <div className="highlight-header">
                      <strong>📝 {fh.file_path}</strong>
                      <span className="operation-badge">{fh.operation}</span>
                    </div>
                    <pre className="file-preview">{fh.content_preview}</pre>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="approval-actions">
          {isEditing && (
            <button
              className="btn btn-cancel"
              onClick={handleCancel}
            >
              Cancel Edit
            </button>
          )}

          <button
            className="btn btn-approve"
            onClick={handleApprove}
            disabled={isEditing}
          >
            ✓ Approve
          </button>

          {canEdit && (
            <button
              className="btn btn-edit"
              onClick={handleEdit}
            >
              {isEditing ? '✓ Confirm Edit' : '✎ Edit'}
            </button>
          )}

          {canReject && (
            <button
              className="btn btn-reject"
              onClick={handleReject}
              disabled={isEditing}
            >
              ✗ Reject
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

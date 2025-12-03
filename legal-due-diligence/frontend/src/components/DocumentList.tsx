/**
 * Document List Component
 *
 * Displays all documents in the data room with highlighting for agent-requested documents.
 */
import React from 'react';
import { useAppStore } from '../stores/appStore';
import '../styles/DocumentList.css';

export const DocumentList: React.FC = () => {
  const documents = useAppStore(state => state.documents);
  const selectedId = useAppStore(state => state.selectedDocumentId);
  const highlightedIds = useAppStore(state => state.highlightedDocumentIds);
  const selectDocument = useAppStore(state => state.selectDocument);

  return (
    <div className="document-list">
      <div className="panel-header">
        <h3>Data Room Documents</h3>
        <span className="document-count">{documents.length} documents</span>
      </div>

      <div className="document-items">
        {documents.length === 0 ? (
          <div className="empty-state">
            <p>No documents in data room</p>
          </div>
        ) : (
          documents.map(doc => {
            const isHighlighted = highlightedIds.has(doc.id);
            const isSelected = selectedId === doc.id;

            return (
              <div
                key={doc.id}
                className={`
                  document-item
                  ${isHighlighted ? 'highlighted' : ''}
                  ${isSelected ? 'selected' : ''}
                `}
                onClick={() => selectDocument(doc.id)}
              >
                {isHighlighted && (
                  <div className="highlight-indicator">
                    <span className="highlight-badge">Agent Requested</span>
                  </div>
                )}

                <div className="document-icon">📄</div>

                <div className="document-info">
                  <div className="document-title">{doc.filename}</div>
                  <div className="document-summary">{doc.summary}</div>
                  <div className="document-meta">
                    {doc.pages} pages · {new Date(doc.uploaded_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

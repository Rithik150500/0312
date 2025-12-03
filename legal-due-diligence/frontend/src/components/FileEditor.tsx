/**
 * File Editor Component
 *
 * Displays and allows editing of files created by the agent.
 * Highlights files when they are being written or edited by the agent.
 */
import React from 'react';
import { useAppStore } from '../stores/appStore';
import '../styles/FileEditor.css';

export const FileEditor: React.FC = () => {
  const files = useAppStore(state => state.files);
  const selectedFilePath = useAppStore(state => state.selectedFilePath);
  const highlightedFilePaths = useAppStore(state => state.highlightedFilePaths);
  const selectFile = useAppStore(state => state.selectFile);
  const updateFile = useAppStore(state => state.updateFile);

  const filesArray = Array.from(files.values());
  const selectedFile = selectedFilePath ? files.get(selectedFilePath) : null;

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (selectedFilePath) {
      updateFile(selectedFilePath, e.target.value);
    }
  };

  return (
    <div className="file-editor">
      {/* File List */}
      <div className="file-list">
        <div className="panel-header">
          <h3>Agent Files</h3>
          <span className="file-count">{filesArray.length} files</span>
        </div>

        <div className="file-items">
          {filesArray.length === 0 ? (
            <div className="empty-state">
              <p>No files yet</p>
            </div>
          ) : (
            filesArray.map(file => {
              const isHighlighted = highlightedFilePaths.has(file.path);
              const isSelected = selectedFilePath === file.path;

              return (
                <div
                  key={file.path}
                  className={`
                    file-item
                    ${isHighlighted ? 'highlighted' : ''}
                    ${isSelected ? 'selected' : ''}
                  `}
                  onClick={() => selectFile(file.path)}
                >
                  {isHighlighted && (
                    <div className="highlight-indicator">
                      <span className="highlight-badge">Agent Writing</span>
                    </div>
                  )}

                  <div className="file-icon">📝</div>

                  <div className="file-info">
                    <div className="file-name">{file.path}</div>
                    <div className="file-meta">
                      Updated: {new Date(file.updated_at).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* File Content */}
      <div className="file-content">
        {selectedFile ? (
          <>
            <div className="content-header">
              <h4>{selectedFile.path}</h4>
              {highlightedFilePaths.has(selectedFile.path) && (
                <span className="header-badge">Currently being modified by agent</span>
              )}
            </div>

            <textarea
              className="content-editor"
              value={selectedFile.content}
              onChange={handleContentChange}
              spellCheck={false}
            />
          </>
        ) : (
          <div className="content-empty">
            <p>Select a file to view its contents</p>
          </div>
        )}
      </div>
    </div>
  );
};

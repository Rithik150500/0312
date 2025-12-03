/**
 * PDF Viewer Component
 *
 * Displays PDF documents with:
 * - Page navigation
 * - Collapsible sidebar with page summaries
 * - Highlighting for legally significant pages and agent-requested pages
 */
import React, { useState, useEffect } from 'react';
import { useAppStore } from '../stores/appStore';
import '../styles/PDFViewer.css';

export const PDFViewer: React.FC = () => {
  const selectedDocId = useAppStore(state => state.selectedDocumentId);
  const selectedDocDetail = useAppStore(state => state.selectedDocumentDetail);
  const highlightedPages = useAppStore(state => state.highlightedPages);
  const currentPage = useAppStore(state => state.currentPdfPage);
  const setCurrentPage = useAppStore(state => state.setCurrentPdfPage);

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const currentDocHighlights = selectedDocId
    ? highlightedPages.get(selectedDocId)
    : undefined;

  const isPageHighlighted = (pageNum: number) => {
    return currentDocHighlights?.has(pageNum) || false;
  };

  const isPageLegallySignificant = (pageNum: number) => {
    if (!selectedDocDetail) return false;
    const page = selectedDocDetail.pages.find(p => p.num === pageNum);
    return page?.legally_significant || false;
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (selectedDocDetail && currentPage < selectedDocDetail.page_count) {
      setCurrentPage(currentPage + 1);
    }
  };

  if (!selectedDocId) {
    return (
      <div className="pdf-viewer">
        <div className="pdf-empty-state">
          <div className="empty-icon">📄</div>
          <p>Select a document to view</p>
        </div>
      </div>
    );
  }

  return (
    <div className="pdf-viewer">
      {/* Toolbar */}
      <div className="pdf-toolbar">
        <button
          className="toolbar-btn"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        >
          {sidebarCollapsed ? '☰ Show Pages' : '✕ Hide Pages'}
        </button>

        <div className="page-controls">
          <button
            className="toolbar-btn"
            onClick={handlePrevPage}
            disabled={currentPage === 1}
          >
            ← Previous
          </button>

          <span className="page-indicator">
            Page {currentPage} of {selectedDocDetail?.page_count || 0}
          </span>

          <button
            className="toolbar-btn"
            onClick={handleNextPage}
            disabled={currentPage === (selectedDocDetail?.page_count || 0)}
          >
            Next →
          </button>
        </div>

        {isPageHighlighted(currentPage) && (
          <span className="page-badge highlighted">Agent Requested</span>
        )}

        {isPageLegallySignificant(currentPage) && (
          <span className="page-badge significant">Legally Significant</span>
        )}
      </div>

      {/* Content Area */}
      <div className="pdf-content">
        {/* Collapsible Sidebar */}
        {!sidebarCollapsed && selectedDocDetail && (
          <div className="pdf-sidebar">
            <div className="sidebar-header">
              <h4>Page Summaries</h4>
            </div>
            <div className="page-list">
              {selectedDocDetail.pages.map(page => (
                <div
                  key={page.num}
                  className={`
                    page-item
                    ${page.num === currentPage ? 'active' : ''}
                    ${isPageHighlighted(page.num) ? 'highlighted' : ''}
                    ${page.legally_significant ? 'significant' : ''}
                  `}
                  onClick={() => setCurrentPage(page.num)}
                >
                  <div className="page-item-header">
                    <span className="page-num">Page {page.num}</span>
                    {page.legally_significant && (
                      <span className="mini-badge">⚖️</span>
                    )}
                    {isPageHighlighted(page.num) && (
                      <span className="mini-badge">👁️</span>
                    )}
                  </div>
                  <div className="page-summary">{page.summary}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* PDF Display */}
        <div className="pdf-display">
          {selectedDocDetail ? (
            <div className={`
              pdf-page
              ${isPageHighlighted(currentPage) ? 'page-highlighted' : ''}
              ${isPageLegallySignificant(currentPage) ? 'page-significant' : ''}
            `}>
              <div className="pdf-placeholder">
                <p>PDF Page {currentPage}</p>
                <p className="pdf-note">
                  (PDF rendering requires pdf.js integration)
                </p>
                {selectedDocDetail.pages.find(p => p.num === currentPage)?.summary}
              </div>
            </div>
          ) : (
            <div className="pdf-loading">Loading document...</div>
          )}
        </div>
      </div>
    </div>
  );
};

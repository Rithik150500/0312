/**
 * Workflow Panel Component
 *
 * Displays the agent's workflow events and tool calls in real-time.
 */
import React, { useEffect, useRef } from 'react';
import { useAppStore } from '../stores/appStore';
import '../styles/WorkflowPanel.css';

export const WorkflowPanel: React.FC = () => {
  const workflowEvents = useAppStore(state => state.workflowEvents);
  const uiState = useAppStore(state => state.uiState);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [workflowEvents]);

  const formatEventType = (type: string) => {
    return type.split('_').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const getEventIcon = (type: string) => {
    if (type.includes('tool_call')) return '🔧';
    if (type.includes('tool_result')) return '✓';
    if (type.includes('thinking')) return '💭';
    if (type.includes('error')) return '❌';
    return '📝';
  };

  return (
    <div className="workflow-panel">
      <div className="panel-header">
        <h3>Agent Workflow</h3>
        <div className="workflow-status">
          {uiState.type === 'agent_running' && (
            <span className="status-badge running">Running</span>
          )}
          {uiState.type === 'awaiting_approval' && (
            <span className="status-badge paused">Paused</span>
          )}
          {uiState.type === 'completed' && (
            <span className="status-badge completed">Completed</span>
          )}
        </div>
      </div>

      <div className="workflow-events" ref={scrollRef}>
        {workflowEvents.length === 0 ? (
          <div className="empty-state">
            <p>Waiting for agent to start...</p>
          </div>
        ) : (
          workflowEvents.map((event, index) => (
            <div key={index} className="workflow-event">
              <div className="event-header">
                <span className="event-icon">{getEventIcon(event.event_type)}</span>
                <span className="event-type">{formatEventType(event.event_type)}</span>
                <span className="event-time">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="event-data">
                <pre>{JSON.stringify(event.data, null, 2)}</pre>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

/**
 * Todo Panel Component
 *
 * Displays the agent's current task list and progress.
 */
import React from 'react';
import { useAppStore } from '../stores/appStore';
import '../styles/TodoPanel.css';

export const TodoPanel: React.FC = () => {
  const todos = useAppStore(state => state.todos);
  const uiState = useAppStore(state => state.uiState);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✓';
      case 'in_progress':
        return '◷';
      case 'pending':
        return '○';
      default:
        return '○';
    }
  };

  const getStatusClass = (status: string) => {
    return `todo-item-${status}`;
  };

  return (
    <div className="todo-panel">
      <div className="panel-header">
        <h3>Task Progress</h3>
        {uiState.type === 'awaiting_approval' && (
          <span className="approval-badge">Awaiting Approval</span>
        )}
      </div>

      <div className="todo-items">
        {todos.length === 0 ? (
          <div className="empty-state">
            <p>No tasks yet</p>
          </div>
        ) : (
          todos.map((todo, index) => (
            <div key={index} className={`todo-item ${getStatusClass(todo.status)}`}>
              <span className="todo-status-icon">{getStatusIcon(todo.status)}</span>
              <div className="todo-content">
                <div className="todo-text">
                  {todo.status === 'in_progress' ? todo.activeForm : todo.content}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

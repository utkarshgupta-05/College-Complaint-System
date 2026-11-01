import React from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

/**
 * Robust React Error Boundary.
 * Catches JavaScript errors anywhere in the child component tree,
 * logs them, and displays an inline recovery interface instead of
 * crashing the whole page into a blank screen.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error(`ErrorBoundary caught error in [${this.props.name || 'Component'}]:`, error, errorInfo);
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      const componentName = this.props.name || 'This section';
      return (
        <div style={{
          padding: '24px',
          margin: '16px auto',
          maxWidth: '800px',
          backgroundColor: '#fff1f2',
          border: '1px solid #fecdd3',
          borderRadius: '12px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <div style={{
              backgroundColor: '#ffe4e6',
              color: '#e11d48',
              padding: '8px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <AlertOctagon size={24} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#9f1239', margin: 0 }}>
                {componentName} encountered an unexpected error
              </h3>
              <p style={{ fontSize: '0.8125rem', color: '#be123c', margin: '2px 0 0 0' }}>
                The rest of the system remains operational. You can attempt to retry this view.
              </p>
            </div>
          </div>

          <div style={{
            backgroundColor: '#ffffff',
            border: '1px solid #f43f5e',
            borderRadius: '6px',
            padding: '10px 14px',
            fontSize: '0.8125rem',
            color: '#881337',
            fontFamily: 'monospace',
            marginBottom: '16px',
            maxHeight: '120px',
            overflowY: 'auto',
            whiteSpace: 'pre-wrap',
          }}>
            {this.state.error?.toString() || 'Unknown runtime error'}
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={this.handleReset}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                backgroundColor: '#e11d48',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={14} /> Try Again
            </button>

            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '8px 16px',
                backgroundColor: '#ffffff',
                color: '#475569',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}


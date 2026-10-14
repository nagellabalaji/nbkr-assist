import React from 'react';
import { ShieldAlert } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an exception:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary-fallback glass-card" style={{ padding: '2rem', textAlign: 'center', margin: '1.5rem auto', maxWidth: '500px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
          <ShieldAlert size={48} style={{ color: 'var(--red-text)' }} />
          <h3 style={{ color: 'var(--text-bright)', margin: 0 }}>Component Failed to Render</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>
            {this.props.message || "An unexpected error occurred while loading this section of the portal."}
          </p>
          <button 
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{ padding: '0.5rem 1rem', background: 'rgba(255, 255, 255, 0.1)', color: 'var(--text-bright)', border: '1px solid rgba(255, 255, 255, 0.2)', borderRadius: '4px', cursor: 'pointer', transition: 'all 0.2s' }}
            onMouseOver={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.2)'}
            onMouseOut={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.1)'}
          >
            Retry Section
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
export default ErrorBoundary;

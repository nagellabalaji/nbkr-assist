import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Clock, CheckCircle, ArrowRight, ShieldAlert } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import './HODGrievances.css';

export const HODGrievances = () => {
  const [grievances, setGrievances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchGrievances = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/hod/grievances', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const json = await res.json();
        if (json.success) {
          setGrievances(json.data);
        } else {
          setError(json.message || 'Failed to fetch grievances');
        }
      } catch (err) {
        setError('Network communication failed');
      } finally {
        setLoading(false);
      }
    };

    fetchGrievances();
  }, []);

  const getPriorityBadgeClass = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'critical':
      case 'high':
        return 'priority-high';
      case 'medium':
        return 'priority-medium';
      default:
        return 'priority-low';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'resolved':
      case 'closed':
        return <CheckCircle className="status-icon resolved" size={18} />;
      case 'in progress':
      case 'assigned':
        return <Clock className="status-icon active" size={18} />;
      default:
        return <AlertCircle className="status-icon pending" size={18} />;
    }
  };

  if (loading) return <Loader message="Accessing department grievances inbox..." />;

  return (
    <div className="hod-grievances-container animate-fade-in">
      <div className="grievances-header">
        <h1>Department Grievance Desk</h1>
        <p>Monitor status, assign active workloads, and audit response SLAs for your department tickets.</p>
      </div>

      {error ? (
        <div className="error-panel glass-card">{error}</div>
      ) : grievances.length === 0 ? (
        <div className="empty-state glass-card">
          <ShieldAlert size={48} />
          <h3>No grievances raised</h3>
          <p>There are no open complaints under your department branch.</p>
        </div>
      ) : (
        <div className="grievance-cards-list">
          {grievances.map((g) => (
            <div key={g.id} className="grievance-row-card glass-card" onClick={() => navigate(`/complaint/${g.id}`)}>
              <div className="card-top-header">
                <span className="ticket-id">{g.id}</span>
                <span className={`priority-badge ${getPriorityBadgeClass(g.priority || g.ai_priority)}`}>
                  {g.priority || g.ai_priority || 'Medium'}
                </span>
              </div>

              <div className="card-mid-body">
                <h3 className="ticket-title">{g.title}</h3>
                <p className="ticket-desc">{g.description}</p>
                <div className="meta-footer">
                  <span>Category: <strong>{g.category_name || 'General'} ({g.subcategory || 'General'})</strong></span>
                  <span>Location: <strong>{g.location}</strong></span>
                  {g.sla_deadline && (
                    <span className="deadline-text">
                      SLA: {new Date(g.sla_deadline).toLocaleString()}
                    </span>
                  )}
                </div>
              </div>

              <div className="card-action-bar">
                <div className="status-block">
                  {getStatusIcon(g.status)}
                  <span className="status-label">{g.status}</span>
                </div>
                <button className="resolve-btn">
                  <span>Open Assignment Desk</span>
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
export default HODGrievances;

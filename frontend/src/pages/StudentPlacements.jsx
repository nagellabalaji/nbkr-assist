import React, { useEffect, useState } from 'react';
import { Briefcase, AlertCircle, CheckCircle, Search, Clock, Calendar, CheckSquare, ShieldAlert } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './StudentPlacements.css';

export const StudentPlacements = () => {
  const [drives, setDrives] = useState([]);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });
  const [search, setSearch] = useState('');

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');

      // Fetch Drives
      const drivesRes = await fetch('/api/placements/drives', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const drivesJson = await drivesRes.json();
      if (drivesJson.success) {
        setDrives(drivesJson.data);
      }

      // Fetch Applications
      const appsRes = await fetch('/api/placements/applications', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const appsJson = await appsRes.json();
      if (appsJson.success) {
        setApplications(appsJson.data);
      }
    } catch (err) {
      setToast({ show: true, message: 'Failed to access recruitment portals.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApply = async (driveId) => {
    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/placements/applications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ drive_id: driveId })
      });
      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: 'Application submitted successfully! Your files are queued for review.', type: 'success' });
        fetchData();
      } else {
        setToast({ show: true, message: json.message || 'Application rejected.', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server communication error.', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusClass = (status) => {
    switch (status?.toLowerCase()) {
      case 'selected': return 'status-selected';
      case 'shortlisted': return 'status-shortlisted';
      case 'rejected': return 'status-rejected';
      default: return 'status-applied';
    }
  };

  const filteredDrives = drives.filter(d => {
    return d.company_name.toLowerCase().includes(search.toLowerCase()) || 
           d.job_role.toLowerCase().includes(search.toLowerCase());
  });

  if (loading) return <Loader message="Accessing placement desks..." />;

  return (
    <div className="student-placements-container animate-fade-in">
      <div className="placements-header">
        <h1>Placement & Career Desk</h1>
        <p>Monitor active college recruitment drives, verify eligibility criteria, and track your applications.</p>
      </div>

      <div className="placements-layout-grid">
        {/* Left: Active drives roster */}
        <div className="drives-section">
          <div className="search-box-wrapper glass-card">
            <Search size={18} className="search-icon" />
            <input 
              type="text" 
              placeholder="Search drives by company or job role..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="search-input"
            />
          </div>

          <div className="drives-grid">
            {filteredDrives.length === 0 ? (
              <div className="empty-drives glass-card">
                <Briefcase size={36} />
                <p>No active placement drives found matching search filters.</p>
              </div>
            ) : (
              filteredDrives.map(d => {
                const hasApplied = applications.some(a => a.drive_id === d.id);
                const appRecord = applications.find(a => a.drive_id === d.id);
                const isCompleted = d.status === 'Completed';

                return (
                  <div key={d.id} className="drive-card glass-card">
                    <div className="drive-card-header">
                      <Briefcase size={22} className="drive-icon" />
                      <span className={`drive-status-badge ${d.status.toLowerCase()}`}>{d.status}</span>
                    </div>

                    <div className="drive-details">
                      <h3 className="company-name">{d.company_name}</h3>
                      <h4 className="job-role">{d.job_role}</h4>
                      <p className="criteria"><strong>Eligibility:</strong> {d.eligibility_criteria || 'B.Tech CSE/ECE/IT'}</p>
                      <p className="package"><strong>Salary:</strong> {d.salary_package || 'Package N/A'}</p>
                    </div>

                    <div className="drive-dates-row">
                      <Calendar size={14} />
                      <span>Date: {new Date(d.drive_date).toLocaleDateString()}</span>
                    </div>

                    <div className="drive-card-actions">
                      {hasApplied ? (
                        <div className={`applied-status-indicator ${getStatusClass(appRecord.status)}`}>
                          Applied — Status: <strong>{appRecord.status.toUpperCase()}</strong>
                        </div>
                      ) : (
                        <button 
                          className="btn btn-primary apply-btn" 
                          onClick={() => handleApply(d.id)}
                          disabled={submitting || isCompleted}
                        >
                          {isCompleted ? 'Drive Closed' : 'Apply Now'}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Applications tracking desk */}
        <div className="applications-tracking-section glass-card">
          <h3>Your Applications Log</h3>
          {applications.length === 0 ? (
            <div className="empty-applications">
              <AlertCircle size={36} />
              <p>No placement drive registrations logged yet.</p>
            </div>
          ) : (
            <div className="applications-timeline">
              {applications.map(a => (
                <div key={a.id} className="app-timeline-card glass-card">
                  <div className="app-item-header">
                    <span className="app-company">{a.company_name}</span>
                    <span className={`status-pill ${getStatusClass(a.status)}`}>
                      {a.status.toUpperCase()}
                    </span>
                  </div>
                  <h4 className="app-role">{a.job_role}</h4>
                  <span className="app-date">Registered on: {new Date(a.applied_at).toLocaleDateString()}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {toast.show && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={() => setToast({ ...toast, show: false })} 
        />
      )}
    </div>
  );
};
export default StudentPlacements;

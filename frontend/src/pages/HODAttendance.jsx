import React, { useEffect, useState } from 'react';
import { Activity, ShieldAlert, CheckCircle2, UserMinus } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import './HODAttendance.css';

export const HODAttendance = () => {
  const [shortages, setShortages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchShortages = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/hod/attendance', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const json = await res.json();
        if (json.success) {
          setShortages(json.data.shortages);
        } else {
          setError(json.message || 'Failed to query attendance registers');
        }
      } catch (err) {
        setError('Network communication failed');
      } finally {
        setLoading(false);
      }
    };

    fetchShortages();
  }, []);

  if (loading) return <Loader message="Analyzing attendance records..." />;

  return (
    <div className="hod-attendance-container animate-fade-in">
      <div className="attendance-header">
        <h1>Attendance Shortage Analyzer</h1>
        <p>View department-wide student attendance shortages and calculate additional classes required to reach 75% eligibility.</p>
      </div>

      <div className="shortage-summary-box glass-card">
        <Activity size={24} className="summary-icon" />
        <div className="summary-text">
          <h3>Active Attendance Audits</h3>
          <p>Currently tracking <strong>{shortages.length}</strong> subject-shortage records in the department.</p>
        </div>
      </div>

      {error ? (
        <div className="error-panel glass-card">{error}</div>
      ) : shortages.length === 0 ? (
        <div className="empty-shortage-state glass-card">
          <CheckCircle2 size={48} className="success-icon" />
          <h3>All Students Eligible!</h3>
          <p>There are no students with attendance shortage in your department. Outstanding performance!</p>
        </div>
      ) : (
        <div className="table-responsive glass-card animate-slide-up">
          <table className="shortage-table">
            <thead>
              <tr>
                <th>Roll Number</th>
                <th>Student Name</th>
                <th>Subject Taught</th>
                <th className="center-text">Total Classes</th>
                <th className="center-text">Present</th>
                <th className="center-text">Absent</th>
                <th>Percentage</th>
                <th className="action-col">Classes Required (for 75%)</th>
              </tr>
            </thead>
            <tbody>
              {shortages.map((item, idx) => (
                <tr key={idx}>
                  <td className="roll-cell">{item.roll_no}</td>
                  <td className="name-cell">{item.student_name}</td>
                  <td>{item.subject}</td>
                  <td className="center-text">{item.total_classes}</td>
                  <td className="center-text present-count">{item.present}</td>
                  <td className="center-text absent-count">{item.absent}</td>
                  <td className="pct-cell">
                    <div className="shortage-pct-bar">
                      <div 
                        className="pct-fill-red" 
                        style={{ width: `${Math.min(item.percentage, 100)}%` }}
                      ></div>
                      <span className="pct-label-text">{item.percentage}%</span>
                    </div>
                  </td>
                  <td className="clearance-col">
                    <span className="clearance-badge">
                      +{item.classes_required_to_clear} classes
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
export default HODAttendance;

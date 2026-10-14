import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, Activity, Wrench, ShieldAlert, AlertTriangle, CheckCircle, BookOpen, Clock, ArrowRight 
} from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import './HODDashboard.css';

export const HODDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchHODDashboard = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/hod/dashboard', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const json = await res.json();
        if (json.success) {
          setStats(json.data);
        } else {
          setError(json.message || 'Failed to load dashboard metrics');
        }
      } catch (err) {
        setError('Network communication failed');
      } finally {
        setLoading(false);
      }
    };

    fetchHODDashboard();
  }, []);

  if (loading) return <Loader message="Analyzing department operations..." />;
  if (error) return <div className="error-panel glass-card">{error}</div>;

  const cardData = [
    { title: "Total Students", value: stats?.totalStudents ?? 0, icon: Users, color: "var(--color-primary)", path: "/hod-students" },
    { title: "Faculty Count", value: stats?.facultyCount ?? 0, icon: Users, color: "var(--color-primary)", path: "/hod-faculty" },
    { title: "Open Grievances", value: stats?.openGrievances ?? 0, icon: AlertTriangle, color: "var(--color-pending)", path: "/hod-grievances" },
    { title: "Critical Grievances", value: stats?.criticalGrievances ?? 0, icon: ShieldAlert, color: "var(--color-error)", path: "/hod-grievances" },
    { title: "SLA Breaches", value: stats?.slaBreaches ?? 0, icon: Clock, color: "var(--color-error)", path: "/hod-grievances" },
    { title: "Average Attendance", value: stats?.averageAttendance ?? "No data available", icon: Activity, color: "var(--color-resolved)", path: "/hod-attendance" },
    { title: "Attendance Shortage", value: stats?.attendanceShortage ?? 0, icon: AlertTriangle, color: "var(--color-error)", path: "/hod-attendance" },
    { title: "Resolved Grievances", value: stats?.resolvedGrievances ?? 0, icon: CheckCircle, color: "var(--color-resolved)", path: "/hod-grievances" }
  ];

  return (
    <div className="hod-dashboard-container animate-fade-in">
      <div className="dashboard-header">
        <h1>NBKR HOD Portal</h1>
        <p>Monitor departmental academic performance rosters, faculty workloads, and grievance operations.</p>
      </div>

      <div className="dashboard-grid">
        {cardData.map((card, idx) => (
          <div key={idx} className="metric-card glass-card" onClick={() => navigate(card.path)}>
            <div className="card-icon-wrapper" style={{ backgroundColor: `${card.color}15`, color: card.color }}>
              <card.icon size={24} />
            </div>
            <div className="card-info">
              <span className="card-title">{card.title}</span>
              <span className="card-value">{card.value}</span>
            </div>
            <div className="card-hover-arrow">
              <ArrowRight size={16} />
            </div>
          </div>
        ))}
      </div>

      {/* Action Hub */}
      <div className="quick-actions-panel glass-card">
        <h3>Departmental Workspaces</h3>
        <div className="actions-grid">
          <button onClick={() => navigate('/hod-overview')} className="action-btn">
            <BookOpen size={18} />
            <span>Department Overview</span>
          </button>
          <button onClick={() => navigate('/hod-students')} className="action-btn">
            <Users size={18} />
            <span>Manage Department Students</span>
          </button>
          <button onClick={() => navigate('/hod-faculty')} className="action-btn">
            <Users size={18} />
            <span>Faculty Workloads & Schedules</span>
          </button>
          <button onClick={() => navigate('/hod-attendance')} className="action-btn">
            <Activity size={18} />
            <span>Attendance Shortage Analyzer</span>
          </button>
          <button onClick={() => navigate('/hod-grievances')} className="action-btn">
            <Wrench size={18} />
            <span>Grievance Assign Desk</span>
          </button>
          <button onClick={() => navigate('/hod-reports')} className="action-btn">
            <BookOpen size={18} />
            <span>Export Department Reports</span>
          </button>
        </div>
      </div>
    </div>
  );
};
export default HODDashboard;

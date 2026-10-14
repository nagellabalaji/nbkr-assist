import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, Activity, Wrench, CheckCircle, BookOpen, AlertCircle, Calendar, ArrowRight 
} from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import './FacultyDashboard.css';

export const FacultyDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardStats = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/faculty/dashboard', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const json = await res.json();
        if (json.success) {
          setStats(json.data);
        } else {
          setError(json.message || 'Failed to load dashboard metrics');
        }
      } catch (err) {
        setError('Network error loading metrics');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardStats();
  }, []);

  if (loading) return <Loader message="Compiling faculty metrics..." />;
  if (error) return <div className="error-panel glass-card">{error}</div>;

  const cardData = [
    { title: "Assigned Grievances", value: stats?.assignedGrievances ?? 0, icon: Wrench, color: "var(--color-primary)", path: "/faculty-grievances" },
    { title: "Open Grievances", value: stats?.openGrievances ?? 0, icon: AlertCircle, color: "var(--color-pending)", path: "/faculty-grievances" },
    { title: "In Progress", value: stats?.inProgressGrievances ?? 0, icon: Activity, color: "var(--color-in-progress)", path: "/faculty-grievances" },
    { title: "Resolved", value: stats?.resolvedGrievances ?? 0, icon: CheckCircle, color: "var(--color-resolved)", path: "/faculty-grievances" },
    { title: "Today's Classes", value: stats?.todayClasses ?? 0, icon: Calendar, color: "var(--color-primary)", path: "/faculty-attendance" },
    { title: "Total Students", value: stats?.totalStudents ?? 0, icon: Users, color: "var(--color-primary)", path: "/faculty-students" },
    { title: "Average Attendance", value: stats?.averageAttendance ?? "No data available", icon: Activity, color: "var(--color-resolved)", path: "/faculty-attendance" }
  ];

  return (
    <div className="faculty-dashboard-container animate-fade-in">
      <div className="dashboard-header">
        <h1>NBKR Faculty Portal</h1>
        <p>Monitor assigned student sections, mark attendance sessions, and resolve academic grievances.</p>
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

      {/* Quick Action Boards */}
      <div className="quick-actions-panel glass-card">
        <h3>Quick Action Workspaces</h3>
        <div className="actions-grid">
          <button onClick={() => navigate('/faculty-attendance')} className="action-btn">
            <Activity size={18} />
            <span>Mark Daily Attendance</span>
          </button>
          <button onClick={() => navigate('/faculty-students')} className="action-btn">
            <Users size={18} />
            <span>Search Enrolled Students</span>
          </button>
          <button onClick={() => navigate('/faculty-grievances')} className="action-btn">
            <Wrench size={18} />
            <span>Resolve Open Grievances</span>
          </button>
        </div>
      </div>
    </div>
  );
};
export default FacultyDashboard;

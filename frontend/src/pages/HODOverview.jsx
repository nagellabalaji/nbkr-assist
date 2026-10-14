import React, { useEffect, useState } from 'react';
import { BookOpen, User, Users, GraduationCap, Star } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import './HODOverview.css';

export const HODOverview = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchOverview = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/hod/overview', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const json = await res.json();
        if (json.success) {
          setData(json.data);
        } else {
          setError(json.message || 'Failed to fetch overview');
        }
      } catch (err) {
        setError('Network communication failed');
      } finally {
        setLoading(false);
      }
    };

    fetchOverview();
  }, []);

  if (loading) return <Loader message="Accessing department records..." />;
  if (error) return <div className="error-panel glass-card">{error}</div>;

  return (
    <div className="hod-overview-container animate-fade-in">
      <div className="overview-header">
        <h1>Department Overview Workspace</h1>
        <p>View basic parameters and counts configured for your academic branch.</p>
      </div>

      <div className="overview-card glass-card">
        <div className="overview-brand-banner">
          <GraduationCap size={48} className="banner-logo" />
          <div className="banner-titles">
            <h2>{data?.department_name}</h2>
            <span className="banner-badge">Code: {data?.department_code}</span>
          </div>
        </div>

        <div className="overview-details-grid">
          <div className="detail-item">
            <User className="detail-icon" />
            <div className="detail-text">
              <span className="detail-label">Head of Department</span>
              <span className="detail-value">{data?.hod_name}</span>
            </div>
          </div>

          <div className="detail-item">
            <Users className="detail-icon" />
            <div className="detail-text">
              <span className="detail-label">Active Faculty Members</span>
              <span className="detail-value">{data?.number_of_faculty}</span>
            </div>
          </div>

          <div className="detail-item">
            <Users className="detail-icon" />
            <div className="detail-text">
              <span className="detail-label">Enrolled Students</span>
              <span className="detail-value">{data?.number_of_students}</span>
            </div>
          </div>

          <div className="detail-item">
            <BookOpen className="detail-icon" />
            <div className="detail-text">
              <span className="detail-label">Academic Subjects</span>
              <span className="detail-value">{data?.number_of_subjects}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default HODOverview;

import React, { useEffect, useState } from 'react';
import { Search, Calendar, Clock, MapPin, ExternalLink, ShieldAlert, CheckCircle } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import './StudentExams.css';

export const StudentExams = () => {
  const [exams, setExams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter states
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('upcoming'); // 'all' | 'upcoming' | 'today' | 'completed'
  const [dateStart, setDateStart] = useState('');
  const [dateEnd, setDateEnd] = useState('');

  const fetchExams = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (dateStart) params.append('date_start', dateStart);
      if (dateEnd) params.append('date_end', dateEnd);

      const res = await fetch(`/api/exams?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        setExams(json.data);
      } else {
        setError(json.message || 'Failed to fetch exam schedules');
      }
    } catch (err) {
      setError('Network communication failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      fetchExams();
    }, 300);
    return () => clearTimeout(delayDebounce);
  }, [search, dateStart, dateEnd]);

  // Calculate dynamic status and filter list
  const getExamStatus = (examDateStr, durationMins) => {
    const now = new Date();
    const examDate = new Date(examDateStr);
    const endDate = new Date(examDate.getTime() + durationMins * 60 * 1000);

    if (now >= examDate && now <= endDate) {
      return 'Today';
    } else if (now > endDate) {
      return 'Completed';
    } else {
      return 'Upcoming';
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'Today': return 'status-today';
      case 'Completed': return 'status-completed';
      default: return 'status-upcoming';
    }
  };

  const filteredExams = exams.filter(e => {
    const status = getExamStatus(e.exam_date, e.duration_mins);
    if (statusFilter === 'all') return true;
    return status.toLowerCase() === statusFilter.toLowerCase();
  });

  const getGoogleCalendarUrl = (exam) => {
    const startDate = new Date(exam.exam_date);
    const endDate = new Date(startDate.getTime() + exam.duration_mins * 60 * 1000);
    
    const formatGCalDate = (date) => {
      return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    };
    
    const startStr = formatGCalDate(startDate);
    const endStr = formatGCalDate(endDate);
    
    const text = encodeURIComponent(exam.title || `${exam.subject} Examination`);
    const details = encodeURIComponent(`Subject: ${exam.subject}\nDuration: ${exam.duration_mins} minutes\nDepartment Scope: ${exam.department_code}`);
    const location = encodeURIComponent(exam.location);
    
    return `https://www.google.com/calendar/render?action=TEMPLATE&text=${text}&dates=${startStr}/${endStr}&details=${details}&location=${location}`;
  };

  return (
    <div className="student-exams-container animate-fade-in">
      <div className="exams-header">
        <h1>Academic Exam Calendar</h1>
        <p>Monitor your department exam schedules, midterms, and test locations.</p>
      </div>

      {/* Filter panel */}
      <div className="filters-board glass-card">
        <div className="search-box-wrapper">
          <Search size={18} className="search-icon" />
          <input 
            type="text" 
            placeholder="Search by subject name or code..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filters-row">
          <div className="filter-item">
            <label>Filter Status</label>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="all">All Exams</option>
              <option value="upcoming">Upcoming</option>
              <option value="today">Ongoing / Today</option>
              <option value="completed">Completed</option>
            </select>
          </div>

          <div className="filter-item">
            <label>Start Date</label>
            <input type="date" value={dateStart} onChange={(e) => setDateStart(e.target.value)} />
          </div>

          <div className="filter-item">
            <label>End Date</label>
            <input type="date" value={dateEnd} onChange={(e) => setDateEnd(e.target.value)} />
          </div>
        </div>
      </div>

      {/* List content */}
      {loading ? (
        <Loader message="Loading exam rosters..." />
      ) : error ? (
        <div className="error-panel glass-card">{error}</div>
      ) : filteredExams.length === 0 ? (
        <div className="empty-exams-state glass-card">
          <Calendar size={48} />
          <p>No exams match your filters or department scope.</p>
        </div>
      ) : (
        <div className="exams-grid">
          {filteredExams.map((exam) => {
            const status = getExamStatus(exam.exam_date, exam.duration_mins);
            const formattedDate = new Date(exam.exam_date).toLocaleDateString(undefined, {
              weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
            });
            const formattedTime = new Date(exam.exam_date).toLocaleTimeString(undefined, {
              hour: '2-digit', minute: '2-digit'
            });

            return (
              <div key={exam.id} className="exam-card glass-card">
                <div className="card-top-row">
                  <span className={`status-badge ${getStatusBadgeClass(status)}`}>
                    {status}
                  </span>
                  <span className="dept-badge">{exam.department_code}</span>
                </div>

                <div className="exam-details">
                  <h3 className="exam-title">{exam.title}</h3>
                  <span className="subject-text">Subject: <strong>{exam.subject}</strong></span>

                  <div className="details-list">
                    <div className="detail-item">
                      <Calendar size={16} />
                      <span>{formattedDate}</span>
                    </div>
                    <div className="detail-item">
                      <Clock size={16} />
                      <span>{formattedTime} ({exam.duration_mins} mins)</span>
                    </div>
                    <div className="detail-item">
                      <MapPin size={16} />
                      <span>Room: {exam.location}</span>
                    </div>
                  </div>
                </div>

                <div className="card-footer">
                  <a 
                    href={getGoogleCalendarUrl(exam)} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="btn btn-outline calendar-sync-btn"
                  >
                    <span>Sync to Google Calendar</span>
                    <ExternalLink size={14} />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
export default StudentExams;

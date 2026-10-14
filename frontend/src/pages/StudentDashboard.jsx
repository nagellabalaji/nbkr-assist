import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { studentService } from '../services/student';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import { ErrorBoundary } from '../components/Common/ErrorBoundary';
import { 
  FileText, CheckCircle2, Clock, AlertTriangle, 
  Search, ArrowRight, Calendar, Tag, MapPin, 
  User, GraduationCap, Award, BookOpen, Bell, 
  ArrowUpRight, HelpCircle, ShieldAlert
} from 'lucide-react';
import './StudentDashboard.css';

export const StudentDashboard = () => {
  const [profile, setProfile] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [grievances, setGrievances] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [attendanceDetails, setAttendanceDetails] = useState([]);
  const [exams, setExams] = useState([]);
  const [placements, setPlacements] = useState([]);
  const [notifications, setNotifications] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });
  const [activeTab, setActiveTab] = useState('grievances'); // grievances, attendance, exams, placements, notifications

  // Filter & Search states for Grievances
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortField, setSortField] = useState('created_at');

  const navigate = useNavigate();

  const loadDashboardData = async () => {
    setLoading(true);
    
    // 1. Fetch summary/profile
    try {
      const summaryRes = await studentService.getSummary();
      if (summaryRes && summaryRes.success) {
        setProfile(summaryRes.data.profile);
        setMetrics(summaryRes.data.metrics);
      }
    } catch (err) {
      console.error("Failed to load dashboard summary profile:", err);
      setToast({ show: true, message: 'Failed to load profile summary details.', type: 'error' });
    }

    // Helper wrapper to catch errors individually
    const fetchSafe = async (apiPromise, setter, label) => {
      try {
        const res = await apiPromise;
        if (res && res.success) {
          setter(res.data);
        } else {
          console.warn(`API returned failure for ${label}:`, res);
        }
      } catch (err) {
        console.error(`Exception loading telemetry for ${label}:`, err);
      }
    };

    // 2. Load other sections concurrently with individual catch fallbacks
    try {
      await Promise.all([
        fetchSafe(studentService.getGrievances(), setGrievances, "Grievances"),
        fetchSafe(studentService.getAttendance(), setAttendance, "Attendance"),
        fetchSafe(studentService.getAttendanceDetails(), setAttendanceDetails, "Attendance Details"),
        fetchSafe(studentService.getExams(), setExams, "Exams"),
        fetchSafe(studentService.getPlacements(), setPlacements, "Placements"),
        fetchSafe(studentService.getNotifications(), setNotifications, "Notifications")
      ]);
    } catch (err) {
      console.error("General error running dashboard telemetry fetches:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const getStatusClass = (status) => {
    return `badge-${status.toLowerCase().replace(' ', '')}`;
  };

  const getPriorityClass = (priority) => {
    return `badge-${priority.toLowerCase()}`;
  };

  // Filter grievances list client-side
  const filteredGrievances = grievances.filter((g) => {
    const matchesSearch = 
      g.title.toLowerCase().includes(search.toLowerCase()) || 
      g.id.toLowerCase().includes(search.toLowerCase()) ||
      g.description.toLowerCase().includes(search.toLowerCase()) ||
      g.location.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter ? g.status === statusFilter : true;
    return matchesSearch && matchesStatus;
  }).sort((a, b) => {
    if (sortField === 'created_at') {
      return new Date(b.created_at) - new Date(a.created_at);
    }
    const priorityWeight = { 'Urgent': 4, 'High': 3, 'Medium': 2, 'Low': 1 };
    return priorityWeight[b.ai_priority] - priorityWeight[a.ai_priority];
  });

  if (loading) {
    return <Loader message="Connecting to NBKR Assist student portal..." />;
  }

  return (
    <div className="student-dashboard-container animate-fade-in">
      
      {/* Toast Alert Notification */}
      {toast.show && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={() => setToast({ ...toast, show: false })} 
        />
      )}

      {/* Header Profile Section */}
      <div className="portal-profile-header glass-card">
        <div className="profile-main-info">
          <div className="avatar-placeholder">
            {profile?.username ? profile.username[0].toUpperCase() : 'S'}
          </div>
          <div className="profile-name-section">
            <span className="welcome-tag">NBKR Student Portal</span>
            <h1>Welcome, {profile?.username || 'Student'}</h1>
            <p className="student-dept">{profile?.department || 'Academic Division'}</p>
          </div>
        </div>

        <div className="profile-details-grid">
          <div className="detail-item">
            <span className="detail-label">Roll Number</span>
            <span className="detail-val">{profile?.roll_no || 'Not Assigned'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Program</span>
            <span className="detail-val">{profile?.program || 'B.Tech'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Academic Year</span>
            <span className="detail-val">{profile?.year || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Semester</span>
            <span className="detail-val">{profile?.semester || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Section</span>
            <span className="detail-val">{profile?.section || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Admission Batch</span>
            <span className="detail-val">{profile?.batch || 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Dashboard Metrics Widgets */}
      <div className="dashboard-grid">
        <div className="metric-card glass-card border-blue" onClick={() => setActiveTab('attendance')}>
          <div className="metric-header">
            <span className="metric-title">Attendance</span>
            <GraduationCap className="metric-icon blue" size={20} />
          </div>
          <div className="metric-number">
            {metrics?.average_attendance !== undefined ? `${metrics.average_attendance}%` : 'No data available'}
          </div>
          <p className="metric-subtext">Overall academic presence</p>
        </div>

        <div className="metric-card glass-card border-orange" onClick={() => setActiveTab('grievances')}>
          <div className="metric-header">
            <span className="metric-title">Open Grievances</span>
            <Clock className="metric-icon orange" size={20} />
          </div>
          <div className="metric-number">{metrics?.open_grievances ?? 0}</div>
          <p className="metric-subtext">Tickets actively under review</p>
        </div>

        <div className="metric-card glass-card border-green" onClick={() => setActiveTab('grievances')}>
          <div className="metric-header">
            <span className="metric-title">Resolved Grievances</span>
            <CheckCircle2 className="metric-icon green" size={20} />
          </div>
          <div className="metric-number">{metrics?.resolved_grievances ?? 0}</div>
          <p className="metric-subtext">Issues resolved & completed</p>
        </div>

        <div className="metric-card glass-card border-purple" onClick={() => setActiveTab('exams')}>
          <div className="metric-header">
            <span className="metric-title">Upcoming Exams</span>
            <BookOpen className="metric-icon purple" size={20} />
          </div>
          <div className="metric-number">{metrics?.upcoming_exams ?? 0}</div>
          <p className="metric-subtext">Scheduled evaluations</p>
        </div>

        <div className="metric-card glass-card border-cyan" onClick={() => setActiveTab('placements')}>
          <div className="metric-header">
            <span className="metric-title">Placements</span>
            <Award className="metric-icon cyan" size={20} />
          </div>
          <div className="metric-number">{metrics?.upcoming_placements ?? 0}</div>
          <p className="metric-subtext">Active drives recruitment cell</p>
        </div>

        <div className="metric-card glass-card border-red" onClick={() => setActiveTab('notifications')}>
          <div className="metric-header">
            <span className="metric-title">Notifications</span>
            <Bell className="metric-icon red" size={20} />
          </div>
          <div className="metric-number">{metrics?.unread_notifications ?? 0}</div>
          <p className="metric-subtext">New broadcast announcements</p>
        </div>
      </div>

      {/* Main Section layout: Quick Actions & Tabbed List Content */}
      <div className="main-portal-content">
        
        {/* Left Side: Quick Actions Panel */}
        <div className="portal-left-panel">
          <div className="quick-actions-card glass-card">
            <h3>Quick Action Hub</h3>
            <p>Direct routes to student support and administrative portals.</p>
            
            <div className="quick-actions-list">
              <Link to="/lodge-complaint" className="q-action-btn primary">
                <FileText size={18} />
                <span>Raise Grievance</span>
                <ArrowUpRight size={14} className="q-arrow" />
              </Link>
              
              <button onClick={() => setActiveTab('grievances')} className={`q-action-btn ${activeTab === 'grievances' ? 'active' : ''}`}>
                <FileText size={18} />
                <span>View My Grievances</span>
              </button>
              
              <button onClick={() => setActiveTab('attendance')} className={`q-action-btn ${activeTab === 'attendance' ? 'active' : ''}`}>
                <GraduationCap size={18} />
                <span>Check Attendance</span>
              </button>

              <button onClick={() => setActiveTab('exams')} className={`q-action-btn ${activeTab === 'exams' ? 'active' : ''}`}>
                <BookOpen size={18} />
                <span>Exam Cell Panel</span>
              </button>

              <button onClick={() => setActiveTab('placements')} className={`q-action-btn ${activeTab === 'placements' ? 'active' : ''}`}>
                <Award size={18} />
                <span>Placement Board</span>
              </button>

              <Link to="/chatbot" className="q-action-btn ai-btn">
                <HelpCircle size={18} />
                <span>NBKR Assist Chat</span>
                <ArrowUpRight size={14} className="q-arrow" />
              </Link>
            </div>
          </div>
        </div>

        {/* Right Side: Interactive Tabs content area */}
        <div className="portal-right-panel">
          
          {/* Navigation Tab list */}
          <div className="portal-tabs-row glass-card">
            <button 
              onClick={() => setActiveTab('grievances')} 
              className={`portal-tab-btn ${activeTab === 'grievances' ? 'active' : ''}`}
            >
              My Grievances ({grievances.length})
            </button>
            <button 
              onClick={() => setActiveTab('attendance')} 
              className={`portal-tab-btn ${activeTab === 'attendance' ? 'active' : ''}`}
            >
              My Attendance
            </button>
            <button 
              onClick={() => setActiveTab('exams')} 
              className={`portal-tab-btn ${activeTab === 'exams' ? 'active' : ''}`}
            >
              Exam Schedule
            </button>
            <button 
              onClick={() => setActiveTab('placements')} 
              className={`portal-tab-btn ${activeTab === 'placements' ? 'active' : ''}`}
            >
              Placement Cell
            </button>
            <button 
              onClick={() => setActiveTab('notifications')} 
              className={`portal-tab-btn ${activeTab === 'notifications' ? 'active' : ''}`}
            >
              Notifications ({notifications.length})
            </button>
          </div>
          
          <ErrorBoundary message="An error occurred while loading this dashboard view.">
          {/* TAB 1: GRIEVANCES */}
          {activeTab === 'grievances' && (
            <div className="tab-pane-container animate-fade-in">
              <div className="filters-card glass-card">
                <div className="search-bar-wrapper">
                  <Search size={18} className="search-icon" />
                  <input 
                    type="text" 
                    placeholder="Search grievances by ID, subject, details..." 
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="form-input search-input"
                  />
                </div>
                <div className="filters-dropdowns-row">
                  <select 
                    value={statusFilter} 
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="form-input filter-dropdown"
                  >
                    <option value="">All Statuses</option>
                    <option value="Submitted">Submitted</option>
                    <option value="Under Review">Under Review</option>
                    <option value="Assigned">Assigned</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Resolved">Resolved</option>
                    <option value="Closed">Closed</option>
                    <option value="Reopened">Reopened</option>
                    <option value="Rejected">Rejected</option>
                  </select>
                  <select 
                    value={sortField} 
                    onChange={(e) => setSortField(e.target.value)}
                    className="form-input filter-dropdown"
                  >
                    <option value="created_at">Sort by: Date</option>
                    <option value="priority">Sort by: Priority</option>
                  </select>
                </div>
              </div>

              {filteredGrievances.length === 0 ? (
                <div className="empty-state-card glass-card">
                  <AlertTriangle className="empty-icon" size={36} />
                  <h3>No grievances registered</h3>
                  <p>You have not logged any grievances matching current filters.</p>
                  <Link to="/lodge-complaint" className="btn btn-primary" style={{ marginTop: '12px' }}>
                    Raise Grievance Ticket
                  </Link>
                </div>
              ) : (
                <div className="table-responsive glass-card">
                  <table className="portal-table">
                    <thead>
                      <tr>
                        <th>Ticket ID</th>
                        <th>Category / Subcategory</th>
                        <th>Subject</th>
                        <th>Priority</th>
                        <th>Status</th>
                        <th>SLA Status</th>
                        <th>Created Date</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredGrievances.map((g) => (
                        <tr key={g.id} onClick={() => navigate(`/complaint/${g.id}`)} className="clickable-row">
                          <td className="ticket-id-cell">{g.id}</td>
                          <td>
                            <div className="dept-code-label">
                              <strong>{g.category_name}</strong>
                              <span className="subtext" style={{ fontSize: '0.72rem', display: 'block', color: 'var(--text-muted)' }}>
                                {g.subcategory || 'General'}
                              </span>
                            </div>
                          </td>
                          <td>
                            <div className="subject-cell-text">
                              <strong>{g.title}</strong>
                              <span className="subtext">{g.location}</span>
                            </div>
                          </td>
                          <td><span className={`badge ${getPriorityClass(g.ai_priority)}`}>{g.ai_priority}</span></td>
                          <td><span className={`badge ${getStatusClass(g.status)}`}>{g.status}</span></td>
                          <td>
                            {g.sla_status === 'Breached' ? (
                              <span className="badge badge-rejected" style={{ fontWeight: '700' }}>Breached</span>
                            ) : (
                              <span className="badge badge-resolved">Normal</span>
                            )}
                          </td>
                          <td>{new Date(g.created_at).toLocaleDateString()}</td>
                          <td>
                            <div className="row-action-link">
                              <span>Details</span>
                              <ArrowRight size={14} />
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: ATTENDANCE */}
          {activeTab === 'attendance' && (
            <div className="tab-pane-container animate-fade-in">
              {attendance.length === 0 ? (
                <div className="empty-state-card glass-card">
                  <GraduationCap className="empty-icon" size={36} />
                  <h3>No attendance logs available</h3>
                  <p>Your academic course attendance statistics have not been published by your HOD / faculty advisors.</p>
                </div>
              ) : (
                <div>
                  <div className="table-responsive glass-card">
                    <table className="portal-table">
                      <thead>
                        <tr>
                          <th>Subject</th>
                          <th>Total Classes</th>
                          <th>Present Classes</th>
                          <th>Absent Classes</th>
                          <th>Attendance Percentage</th>
                          <th>Status / Classes Needed</th>
                        </tr>
                      </thead>
                      <tbody>
                        {attendance.map((a) => (
                          <tr key={a.id}>
                            <td className="subject-name-cell"><strong>{a.subject}</strong></td>
                            <td>{a.total_classes}</td>
                            <td style={{ color: 'var(--green-text)', fontWeight: '600' }}>{a.present}</td>
                            <td style={{ color: 'var(--red-text)', fontWeight: '600' }}>{a.absent}</td>
                            <td>
                              <div className="progress-cell-wrapper">
                                <strong>{a.percentage}%</strong>
                                <div className="progress-bar-bg">
                                  <div 
                                    className={`progress-bar-fill ${a.percentage < 75 ? 'danger' : 'success'}`} 
                                    style={{ width: `${a.percentage}%` }}
                                  ></div>
                                </div>
                              </div>
                            </td>
                            <td>
                              {a.percentage >= 75 ? (
                                <span className="badge badge-resolved">Eligible</span>
                              ) : (
                                <div>
                                  <span className="badge badge-rejected" style={{ marginBottom: '4px', display: 'inline-block' }}>Shortage</span>
                                  <span className="classes-needed-alert" style={{ display: 'block', fontSize: '0.72rem', color: 'var(--red-text)', fontWeight: '700' }}>
                                    Need {Math.max(0, 3 * a.total_classes - 4 * a.present)} classes consecutively
                                  </span>
                                </div>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Detailed Day-by-Day Session Logs */}
                  <div className="detailed-logs-section" style={{ marginTop: '2rem' }}>
                    <h3 style={{ marginBottom: '1rem', color: 'var(--text-bright)' }}>Daily Session History Logs</h3>
                    {attendanceDetails.length === 0 ? (
                      <div className="empty-state-card glass-card" style={{ padding: '20px' }}>
                        <p>No individual session markings logged for this student.</p>
                      </div>
                    ) : (
                      <div className="table-responsive glass-card">
                        <table className="portal-table">
                          <thead>
                            <tr>
                              <th>Date</th>
                              <th>Subject</th>
                              <th>Session</th>
                              <th>Section</th>
                              <th>Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {attendanceDetails.map((det) => (
                              <tr key={det.id}>
                                <td>{det.date}</td>
                                <td><strong>{det.subject_name}</strong></td>
                                <td>{det.session}</td>
                                <td>Section {det.section}</td>
                                <td>
                                  {det.status === 'Present' ? (
                                    <span className="badge badge-resolved">Present</span>
                                  ) : (
                                    <span className="badge badge-rejected">Absent</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: EXAMS */}
          {activeTab === 'exams' && (
            <div className="tab-pane-container animate-fade-in">
              {exams.length === 0 ? (
                <div className="empty-state-card glass-card">
                  <BookOpen className="empty-icon" size={36} />
                  <h3>No upcoming examinations</h3>
                  <p>There are no exam schedules active or announced for your academic department.</p>
                </div>
              ) : (
                <div className="exams-grid">
                  {exams.map((e) => (
                    <div key={e.id} className="exam-schedule-card glass-card">
                      <div className="exam-card-header">
                        <span className="exam-tag">Academic Eval</span>
                        <span className="exam-duration">{e.duration_mins} Mins</span>
                      </div>
                      <h3>{e.title}</h3>
                      <div className="exam-meta">
                        <div className="meta-line">
                          <Tag size={14} />
                          <span>Course: <strong>{e.subject}</strong></span>
                        </div>
                        <div className="meta-line">
                          <Calendar size={14} />
                          <span>Date: <strong>{new Date(e.exam_date).toLocaleString()}</strong></span>
                        </div>
                        <div className="meta-line">
                          <MapPin size={14} />
                          <span>Hall: <strong>{e.location}</strong></span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: PLACEMENT CELL */}
          {activeTab === 'placements' && (
            <div className="tab-pane-container animate-fade-in">
              {placements.length === 0 ? (
                <div className="empty-state-card glass-card">
                  <Award className="empty-icon" size={36} />
                  <h3>No active placement campaigns</h3>
                  <p>There are no recruitment placement campaigns currently accepting registrations.</p>
                </div>
              ) : (
                <div className="table-responsive glass-card">
                  <table className="portal-table">
                    <thead>
                      <tr>
                        <th>Company Name</th>
                        <th>Job Role Offered</th>
                        <th>Eligibility Criteria</th>
                        <th>Salary Package</th>
                        <th>Recruitment Date</th>
                        <th>Drive Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {placements.map((p) => (
                        <tr key={p.id}>
                          <td><strong>{p.company_name}</strong></td>
                          <td>{p.job_role}</td>
                          <td><span className="eligibility-desc-text">{p.eligibility_criteria || 'N/A'}</span></td>
                          <td style={{ color: 'var(--blue-active)', fontWeight: '600' }}>{p.salary_package || 'Not Stated'}</td>
                          <td>{new Date(p.drive_date).toLocaleDateString()}</td>
                          <td>
                            <span className={`badge ${p.status === 'Upcoming' ? 'badge-inprogress' : p.status === 'Ongoing' ? 'badge-reopened' : 'badge-closed'}`}>
                              {p.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 5: NOTIFICATIONS */}
          {activeTab === 'notifications' && (
            <div className="tab-pane-container animate-fade-in">
              {notifications.length === 0 ? (
                <div className="empty-state-card glass-card">
                  <Bell className="empty-icon" size={36} />
                  <h3>Your alerts inbox is empty</h3>
                  <p>You do not have any notices or system alerts in your student inbox.</p>
                </div>
              ) : (
                <div className="notifications-list-wrapper">
                  {notifications.map((n) => (
                    <div key={n.id} className="portal-notification-item glass-card">
                      <div className="notif-badge-wrapper">
                        <span className="notif-icon-circle">
                          <Bell size={16} />
                        </span>
                      </div>
                      <div className="notif-content-wrapper">
                        <div className="notif-title-row">
                          <h4>{n.title}</h4>
                          <span className="notif-time">{new Date(n.created_at).toLocaleString()}</span>
                        </div>
                        <p>{n.message}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          </ErrorBoundary>

        </div>
      </div>
    </div>
  );
};

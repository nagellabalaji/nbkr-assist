import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { adminService } from '../services/admin';
import { complaintService } from '../services/complaints';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import { Modal } from '../components/Common/Modal';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell 
} from 'recharts';
import { 
  FileText, Clock, AlertTriangle, CheckCircle, Trash2, 
  Search, ShieldAlert, Award, Star, Wrench, User, GraduationCap, RefreshCw
} from 'lucide-react';
import './AdminDashboard.css';

export const AdminDashboard = ({ defaultTab }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const [metrics, setMetrics] = useState(null);
  const [chartsData, setChartsData] = useState(null);
  const [complaints, setComplaints] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshingComplaints, setRefreshingComplaints] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // New Analytics states - prioritize defaultTab prop or route
  const [activeTab, setActiveTab] = useState(
    defaultTab || (location.pathname === '/admin-complaints' ? 'grievances' : 'overview')
  );
  const [overviewData, setOverviewData] = useState(null);
  const [attendanceData, setAttendanceData] = useState(null);
  const [modulesData, setModulesData] = useState(null);
  const [error, setError] = useState(null);

  // Search/Filters states
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  // Faculty Assignment
  const FALLBACK_FACULTY = [
    { id: 6, username: 'BALAJI', department: 'Computer Science & Engineering' },
    { id: 7, username: 'PAVAN', department: 'Electronics & Communication Engineering' },
    { id: 8, username: 'SAINADH', department: 'Electrical & Electronics Engineering' },
    { id: 9, username: 'SRINU', department: 'Mechanical Engineering' },
    { id: 10, username: 'AKHILA', department: 'Civil Engineering' },
    { id: 11, username: 'VARALAKSHMI', department: 'Information Technology' },
    { id: 12, username: 'BALAJI', department: 'Artificial Intelligence & Data Science' }
  ];
  const [facultyList, setFacultyList] = useState([]);
  const effectiveFacultyList = facultyList && facultyList.length > 0 ? facultyList : FALLBACK_FACULTY;
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [selectedFacultyId, setSelectedFacultyId] = useState('');
  const [selectedBranch, setSelectedBranch] = useState('');
  const [validationError, setValidationError] = useState('');
  const [activeComplaintId, setActiveComplaintId] = useState('');
  const [assigning, setAssigning] = useState(false);
  const [assignmentSuccessData, setAssignmentSuccessData] = useState(null);

  const formatDateFull = (isoString) => {
    if (!isoString) return 'N/A';
    try {
      const d = new Date(isoString);
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const day = d.getDate();
      const month = months[d.getMonth()];
      const year = d.getFullYear();
      let hours = d.getHours();
      const minutes = d.getMinutes().toString().padStart(2, '0');
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12;
      hours = hours ? hours : 12;
      return `${day} ${month} ${year}, ${hours}:${minutes} ${ampm}`;
    } catch (e) {
      return isoString;
    }
  };

  const formatDateShort = (isoString) => {
    if (!isoString) return 'N/A';
    try {
      const d = new Date(isoString);
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const day = d.getDate();
      const month = months[d.getMonth()];
      const year = d.getFullYear();
      return `${day} ${month} ${year}`;
    } catch (e) {
      return isoString;
    }
  };

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch each API call concurrently but with catch handlers to prevent one crash from blocking others
      const [analyticsRes, overviewRes, attendanceRes, modulesRes, compRes, catRes, facultyRes] = await Promise.all([
        adminService.getAnalytics().catch((err) => { console.error("getAnalytics failed:", err); return null; }),
        adminService.getAnalyticsOverview().catch((err) => { console.error("getAnalyticsOverview failed:", err); return null; }),
        adminService.getAnalyticsAttendance().catch((err) => { console.error("getAnalyticsAttendance failed:", err); return null; }),
        adminService.getAnalyticsModules().catch((err) => { console.error("getAnalyticsModules failed:", err); return null; }),
        complaintService.getComplaints({ per_page: 200 }).catch((err) => { console.error("getComplaints failed:", err); return null; }),
        complaintService.getCategories().catch((err) => { console.error("getCategories failed:", err); return null; }),
        adminService.getFacultyList().catch((err) => { console.error("getFacultyList failed:", err); return null; })
      ]);

      if (analyticsRes && analyticsRes.success && analyticsRes.data) {
        setMetrics(analyticsRes.data.metrics || null);
        setChartsData(analyticsRes.data.charts || null);
      }

      if (overviewRes && overviewRes.success) {
        setOverviewData(overviewRes.data);
      }

      if (attendanceRes && attendanceRes.success) {
        setAttendanceData(attendanceRes.data);
      }

      if (modulesRes && modulesRes.success) {
        setModulesData(modulesRes.data);
      }
      
      if (compRes && compRes.success && Array.isArray(compRes.data)) {
        setComplaints(compRes.data);
      }
      if (catRes && catRes.success && Array.isArray(catRes.data)) {
        setCategories(catRes.data);
      }
      
      if (facultyRes && facultyRes.success && Array.isArray(facultyRes.data)) {
        setFacultyList(facultyRes.data);
      }

      // Only trigger fatal error if BOTH analytics AND complaints failed entirely
      if ((!analyticsRes || !analyticsRes.success) && (!compRes || !compRes.success)) {
        setError("Failed to fetch essential telemetry datasets. Please ensure that all API services are active.");
      }
    } catch (e) {
      console.error("Critical AdminDashboard loader error:", e);
      setError("An unexpected error occurred while compiling institutional analytics.");
      setToast({ show: true, message: 'Failed to retrieve analytics dashboard data.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const fetchComplaints = async (retryCount = 0) => {
    setRefreshingComplaints(true);
    try {
      const compRes = await complaintService.getComplaints({ per_page: 200 });
      if (compRes && compRes.success && Array.isArray(compRes.data)) {
        setComplaints(compRes.data);
      } else if (retryCount < 2) {
        setTimeout(() => fetchComplaints(retryCount + 1), 2000);
      }
    } catch (err) {
      console.error("fetchComplaints failed:", err);
      if (retryCount < 2) {
        setTimeout(() => fetchComplaints(retryCount + 1), 2000);
      }
    } finally {
      setRefreshingComplaints(false);
    }
  };

  const refreshDashboardData = async () => {
    try {
      const [analyticsRes, overviewRes, attendanceRes, modulesRes, compRes, catRes, facultyRes] = await Promise.all([
        adminService.getAnalytics().catch(() => null),
        adminService.getAnalyticsOverview().catch(() => null),
        adminService.getAnalyticsAttendance().catch(() => null),
        adminService.getAnalyticsModules().catch(() => null),
        complaintService.getComplaints({ per_page: 200 }).catch(() => null),
        complaintService.getCategories().catch(() => null),
        adminService.getFacultyList().catch(() => null)
      ]);

      if (analyticsRes && analyticsRes.success) {
        setMetrics(analyticsRes.data.metrics);
        setChartsData(analyticsRes.data.charts);
      }
      if (overviewRes && overviewRes.success) setOverviewData(overviewRes.data);
      if (attendanceRes && attendanceRes.success) setAttendanceData(attendanceRes.data);
      if (modulesRes && modulesRes.success) setModulesData(modulesRes.data);
      if (compRes && compRes.success && Array.isArray(compRes.data)) setComplaints(compRes.data);
      if (catRes && catRes.success && Array.isArray(catRes.data)) setCategories(catRes.data);
      if (facultyRes && facultyRes.success && Array.isArray(facultyRes.data)) setFacultyList(facultyRes.data);
    } catch (e) {
      console.error("Background refresh failed:", e);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  useEffect(() => {
    if (location.pathname === '/admin-complaints') {
      setActiveTab('grievances');
    }
  }, [location.pathname]);

  // Safety trigger: ensure complaints are fetched if empty anywhere on the dashboard
  useEffect(() => {
    if (complaints.length === 0 && !loading && !refreshingComplaints) {
      fetchComplaints();
    }
  }, [complaints.length, loading]);

  const handleDelete = async (e, id) => {
    e.stopPropagation(); // Stop card click navigation
    if (!window.confirm(`Are you sure you want to permanently delete grievance ${id}?`)) return;

    try {
      const res = await complaintService.deleteComplaint(id);
      if (res.success) {
        setToast({ show: true, message: 'Grievance ticket deleted successfully', type: 'success' });
        refreshDashboardData();
      }
    } catch (e) {
      setToast({ show: true, message: 'Failed to delete grievance', type: 'error' });
    }
  };

  const isBranchMatch = (department, branchCode) => {
    if (!department || !branchCode) return false;
    const dept = department.toLowerCase();
    const br = branchCode.toLowerCase();
    
    if (dept === br) return true;
    if (br === 'cse' && (dept.includes('computer science') || dept === 'cse')) return true;
    if (br === 'ece' && (dept.includes('electronics') || dept === 'ece')) return true;
    if (br === 'eee' && (dept.includes('electrical') || dept === 'eee')) return true;
    if (br === 'me' && (dept.includes('mechanical') || dept === 'me')) return true;
    if ((br === 'civil' || br === 'ce') && (dept.includes('civil') || dept === 'ce')) return true;
    if (br === 'it' && (dept.includes('information technology') || dept === 'it')) return true;
    if ((br === 'ai & ds' || br === 'ai' || br === 'ds' || br.includes('ai')) && (dept.includes('artificial intelligence') || dept.includes('data science') || dept.includes('ai'))) return true;
    
    return dept.includes(br);
  };

  useEffect(() => {
    if (selectedFacultyId && selectedBranch) {
      const fac = effectiveFacultyList.find(f => f.id.toString() === selectedFacultyId);
      if (fac && !isBranchMatch(fac.department, selectedBranch)) {
        setValidationError('Selected faculty does not belong to this branch.');
      } else {
        setValidationError('');
      }
    } else {
      setValidationError('');
    }
  }, [selectedFacultyId, selectedBranch, effectiveFacultyList]);

  useEffect(() => {
    if (selectedBranch && selectedFacultyId) {
      const fac = effectiveFacultyList.find(f => f.id.toString() === selectedFacultyId);
      if (fac && !isBranchMatch(fac.department, selectedBranch)) {
        setSelectedFacultyId('');
      }
    }
  }, [selectedBranch, effectiveFacultyList]);

  const openAssignModal = (e, id) => {
    e.stopPropagation();
    setActiveComplaintId(id);
    setSelectedFacultyId('');
    setSelectedBranch('');
    setValidationError('');
    setAssignmentSuccessData(null);
    setIsAssignModalOpen(true);
  };

  const handleCloseSuccessModal = () => {
    setIsAssignModalOpen(false);
    setAssignmentSuccessData(null);
    refreshDashboardData();
  };

  const handleCloseModal = () => {
    setIsAssignModalOpen(false);
    setAssignmentSuccessData(null);
  };

  const handleAssignStaff = async () => {
    if (!selectedFacultyId) {
      setValidationError('Please select a faculty member.');
      return;
    }
    if (!selectedBranch) {
      setValidationError('Please select a branch.');
      return;
    }
    if (!activeComplaintId) return;

    const selectedFaculty = effectiveFacultyList.find(f => f.id.toString() === selectedFacultyId);
    if (!selectedFaculty) {
      setValidationError('Faculty member not found.');
      return;
    }
    if (!isBranchMatch(selectedFaculty.department, selectedBranch)) {
      setValidationError('Selected faculty does not belong to this branch.');
      return;
    }

    setValidationError('');
    setAssigning(true);
    try {
      const res = await complaintService.assignComplaint(activeComplaintId, selectedFacultyId, selectedBranch);
      if (res.success) {
        setToast({ show: true, message: `Grievance assigned successfully to ${selectedFaculty.username}.`, type: 'success' });
        setAssignmentSuccessData({
          facultyName: selectedFaculty.username,
          branchName: selectedBranch,
          assignedAt: res.data?.assigned_at || new Date().toISOString(),
          deadline: res.data?.sla_deadline || res.data?.resolution_deadline || new Date(Date.now() + 2 * 24 * 3600000).toISOString()
        });
      } else {
        setToast({ show: true, message: res.message || 'Unable to assign grievance. Please try again.', type: 'error' });
      }
    } catch (e) {
      const errMsg = e.response?.data?.message || 'Unable to assign grievance. Please try again.';
      setToast({ show: true, message: errMsg, type: 'error' });
    } finally {
      setAssigning(false);
    }
  };

  const filteredComplaints = complaints.filter((comp) => {
    const s = search.toLowerCase();
    const matchesSearch = 
      String(comp.title || '').toLowerCase().includes(s) ||
      String(comp.id || '').toLowerCase().includes(s) ||
      String(comp.student_name || '').toLowerCase().includes(s) ||
      String(comp.roll_no || '').toLowerCase().includes(s) ||
      String(comp.location || '').toLowerCase().includes(s);

    const matchesStatus = statusFilter ? comp.status === statusFilter : true;
    const matchesPriority = priorityFilter ? comp.ai_priority === priorityFilter : true;
    const matchesCategory = categoryFilter ? (comp.category_id && comp.category_id.toString() === categoryFilter) : true;

    return matchesSearch && matchesStatus && matchesPriority && matchesCategory;
  });

  const renderGrievanceQueueTable = () => (
    <div className="admin-queue-card glass-card">
      <div className="queue-header">
        <div>
          <h3>Grievance Administration Queue</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: '4px 0 0 0' }}>
            Showing {filteredComplaints.length} of {complaints.length} registered grievances
          </p>
        </div>
        <div className="queue-actions" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button 
            type="button" 
            onClick={fetchComplaints} 
            className="btn btn-secondary btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap', padding: '7px 12px', fontSize: '0.85rem' }}
            title="Refresh Grievances Queue"
            disabled={refreshingComplaints}
          >
            <RefreshCw size={14} className={refreshingComplaints ? 'spin-anim' : ''} />
            <span>{refreshingComplaints ? 'Refreshing...' : 'Refresh Queue'}</span>
          </button>
          <div className="search-bar-wrapper">
            <Search size={16} className="search-icon" />
            <input 
              type="text" 
              placeholder="Search by ID, roll, student, location..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="form-input search-input"
            />
          </div>
        </div>
      </div>

      <div className="queue-filter-row">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="form-input">
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

        <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)} className="form-input">
          <option value="">All Priorities</option>
          <option value="Low">Low</option>
          <option value="Medium">Medium</option>
          <option value="High">High</option>
          <option value="Urgent">Urgent</option>
        </select>

        <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} className="form-input">
          <option value="">All Categories</option>
          {categories.map(cat => (
            <option key={cat.id} value={cat.id}>{cat.name}</option>
          ))}
        </select>
      </div>

      <div className="table-container" style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
        {complaints.length === 0 ? (
          <div className="empty-table-state" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
            {refreshingComplaints ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                <RefreshCw size={24} className="spin-anim" style={{ color: 'var(--color-primary)' }} />
                <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', margin: 0 }}>
                  Synchronizing grievance records from database...
                </p>
              </div>
            ) : (
              <>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '1.2rem', fontSize: '1rem' }}>
                  No grievances currently loaded into memory.
                </p>
                <button 
                  onClick={() => fetchComplaints(0)} 
                  className="btn btn-primary btn-sm"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '10px 18px', cursor: 'pointer' }}
                >
                  <RefreshCw size={16} />
                  <span>Fetch Grievances Now</span>
                </button>
              </>
            )}
          </div>
        ) : filteredComplaints.length === 0 ? (
          <div className="empty-table-state" style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No complaints registered matching filter criteria.
          </div>
        ) : (
          <table className="custom-table" style={{ width: '100%', minWidth: '700px' }}>
            <thead>
              <tr>
                <th>Ticket ID</th>
                <th>Student / Roll</th>
                <th>Summary</th>
                <th>Location</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Engineer Assigned</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredComplaints.map((comp) => (
                <tr key={comp.id} onClick={() => navigate(`/complaint/${comp.id}`)} style={{ cursor: 'pointer' }}>
                  <td><strong className="queue-id">{comp.id}</strong></td>
                  <td>
                    <div className="student-cell">
                      <span className="s-name">{comp.student_name}</span>
                      <span className="s-roll">{comp.roll_no}</span>
                    </div>
                  </td>
                  <td><span className="queue-title">{comp.title}</span></td>
                  <td><span className="queue-loc">{comp.location}</span></td>
                  <td>{comp.category_name}</td>
                  <td><span className={`badge badge-${(comp.ai_priority || 'medium').toLowerCase()}`}>{comp.ai_priority}</span></td>
                  <td><span className={`badge badge-${(comp.status || 'submitted').toLowerCase().replace(' ', '')}`}>{comp.status}</span></td>
                  <td>
                    {comp.assigned_staff_name ? (
                      <span className="engineer-assigned" style={{ display: 'flex', flexDirection: 'column' }}>
                        <span>{comp.assigned_staff_name}</span>
                        {comp.assigned_branch && (
                          <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>({comp.assigned_branch})</span>
                        )}
                      </span>
                    ) : (
                      <span className="engineer-unassigned">Unassigned</span>
                    )}
                  </td>
                  <td style={{ textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                    <div className="row-actions-group">
                      <button 
                        onClick={(e) => openAssignModal(e, comp.id)} 
                        className="btn btn-secondary btn-icon-only"
                        title="Assign Faculty"
                        disabled={comp.status === 'Closed' || comp.status === 'Rejected'}
                      >
                        <Wrench size={14} />
                      </button>
                      <button 
                        onClick={(e) => handleDelete(e, comp.id)} 
                        className="btn btn-danger btn-icon-only"
                        title="Delete Ticket"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );

  // Recharts color palettes
  const CHART_COLORS = ['#4f46e5', '#14b8a6', '#06b6d4', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'];

  if (error) {
    return (
      <div className="error-boundary-fallback glass-card" style={{ padding: '3rem', textAlign: 'center', margin: '3rem auto', maxWidth: '600px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
        <ShieldAlert size={64} style={{ color: 'var(--red-text)' }} />
        <h2 style={{ color: 'var(--text-bright)', margin: 0 }}>Dashboard Compilation Failed</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '1rem', margin: 0 }}>
          {error}
        </p>
        <button 
          onClick={loadDashboardData}
          style={{ padding: '0.75rem 1.5rem', background: 'rgba(255, 255, 255, 0.1)', color: 'var(--text-bright)', border: '1px solid rgba(255, 255, 255, 0.2)', borderRadius: '4px', cursor: 'pointer', transition: 'all 0.2s', fontSize: '1rem' }}
          onMouseOver={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.2)'}
          onMouseOut={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.1)'}
        >
          Retry Compilation
        </button>
      </div>
    );
  }

  if (loading || !metrics || !chartsData || !overviewData || !attendanceData || !modulesData) {
    return <Loader message="Compiling institution analytics dashboard..." />;
  }

  return (
    <div className="admin-dashboard-container animate-fade-in">
      <div className="admin-header-section">
        <h1>NBKRIST Administration Dashboard</h1>
        <p>Centralized institutional management, analytics telemetry, campus services audits, and automated routing logs.</p>
      </div>

      {/* Navigation Tab list */}
      <div className="portal-tabs-row glass-card">
        <button onClick={() => setActiveTab('overview')} className={`portal-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}>Overview</button>
        <button onClick={() => setActiveTab('attendance')} className={`portal-tab-btn ${activeTab === 'attendance' ? 'active' : ''}`}>Attendance</button>
        <button onClick={() => setActiveTab('grievances')} className={`portal-tab-btn ${activeTab === 'grievances' ? 'active' : ''}`}>Grievances Queue</button>
        <button onClick={() => setActiveTab('hostel')} className={`portal-tab-btn ${activeTab === 'hostel' ? 'active' : ''}`}>Hostel</button>
        <button onClick={() => setActiveTab('transport')} className={`portal-tab-btn ${activeTab === 'transport' ? 'active' : ''}`}>Transport</button>
        <button onClick={() => setActiveTab('library')} className={`portal-tab-btn ${activeTab === 'library' ? 'active' : ''}`}>Library</button>
        <button onClick={() => setActiveTab('placements')} className={`portal-tab-btn ${activeTab === 'placements' ? 'active' : ''}`}>Placements</button>
        <button onClick={() => setActiveTab('exams')} className={`portal-tab-btn ${activeTab === 'exams' ? 'active' : ''}`}>Exams</button>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="tab-pane-container animate-fade-in">
          <div className="dashboard-grid">
            <div className="metric-card glass-card border-blue">
              <div className="metric-header">
                <span className="metric-title">Total Students</span>
                <GraduationCap className="metric-icon blue" size={20} />
              </div>
              <div className="metric-number">{overviewData.total_students}</div>
              <p className="metric-subtext">Active enrollment: {overviewData.active_students}</p>
            </div>

            <div className="metric-card glass-card border-cyan">
              <div className="metric-header">
                <span className="metric-title">Total Staff</span>
                <User className="metric-icon cyan" size={20} />
              </div>
              <div className="metric-number">{overviewData.total_staff}</div>
              <p className="metric-subtext">Faculty & support engineers</p>
            </div>

            <div 
              className="metric-card glass-card border-orange"
              onClick={() => setActiveTab('grievances')}
              style={{ cursor: 'pointer', transition: 'all 0.2s' }}
              title="Click to view Grievances Queue"
            >
              <div className="metric-header">
                <span className="metric-title">Open Tickets</span>
                <AlertTriangle className="metric-icon orange" size={20} />
              </div>
              <div className="metric-number">{overviewData.open_grievances}</div>
              <p className="metric-subtext" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Resolved: {overviewData.resolved_grievances}</span>
                <span style={{ color: '#f59e0b', fontWeight: 'bold' }}>View Queue &rarr;</span>
              </p>
            </div>

            <div className="metric-card glass-card border-green">
              <div className="metric-header">
                <span className="metric-title">Active Placement Drives</span>
                <Award className="metric-icon green" size={20} />
              </div>
              <div className="metric-number">{overviewData.active_placements}</div>
              <p className="metric-subtext">Placement applications: {overviewData.placement_applications}</p>
            </div>
          </div>

          <div className="dashboard-grid" style={{ marginTop: '20px', marginBottom: '30px' }}>
            <div className="metric-card glass-card">
              <h3>Hostel Requests</h3>
              <div className="metric-number" style={{ fontSize: '1.8rem', marginTop: '10px' }}>{overviewData.total_hostel}</div>
            </div>
            <div className="metric-card glass-card">
              <h3>Transport Bookings</h3>
              <div className="metric-number" style={{ fontSize: '1.8rem', marginTop: '10px' }}>{overviewData.total_transport}</div>
            </div>
            <div className="metric-card glass-card">
              <h3>Library Transactions</h3>
              <div className="metric-number" style={{ fontSize: '1.8rem', marginTop: '10px' }}>{overviewData.total_library}</div>
            </div>
            <div className="metric-card glass-card">
              <h3>Total Examinations</h3>
              <div className="metric-number" style={{ fontSize: '1.8rem', marginTop: '10px' }}>{overviewData.total_exams}</div>
            </div>
          </div>

          {/* Grievance Administration Queue directly visible on Overview tab */}
          <div style={{ marginTop: '20px' }}>
            {renderGrievanceQueueTable()}
          </div>
        </div>
      )}

      {/* TAB 2: ATTENDANCE */}
      {activeTab === 'attendance' && (
        <div className="tab-pane-container animate-fade-in">
          <div className="dashboard-grid" style={{ marginBottom: '30px' }}>
            <div className="metric-card glass-card border-blue">
              <div className="metric-header"><span className="metric-title">Average Attendance</span></div>
              <div className="metric-number">{attendanceData.average_attendance}%</div>
            </div>
            <div className="metric-card glass-card border-orange">
              <div className="metric-header"><span className="metric-title">Students in Shortage</span></div>
              <div className="metric-number" style={{ color: 'var(--red-text)' }}>{attendanceData.students_shortage}</div>
              <p className="metric-subtext">Attendance &lt; 75.0%</p>
            </div>
            <div className="metric-card glass-card border-green">
              <div className="metric-header"><span className="metric-title">Eligible Students</span></div>
              <div className="metric-number" style={{ color: 'var(--green-text)' }}>{attendanceData.students_eligible}</div>
              <p className="metric-subtext">Attendance &ge; 75.0%</p>
            </div>
          </div>

          <div className="charts-row-grid" style={{ gridTemplateColumns: '1.5fr 1fr' }}>
            <div className="chart-card glass-card">
              <h3>Attendance by Department</h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={attendanceData.by_department}>
                  <XAxis dataKey="department" stroke="#6b7280" fontSize={10} tickLine={false} />
                  <YAxis stroke="#6b7280" fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', color: '#0f172a' }} />
                  <Bar dataKey="average" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card glass-card">
              <h3>Attendance Distribution</h3>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={attendanceData.distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={70}
                    dataKey="count"
                    nameKey="range"
                  >
                    {attendanceData.distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#0b1120', borderColor: 'rgba(255,255,255,0.08)' }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="pie-legend">
                {attendanceData.distribution.map((entry, idx) => (
                  <div key={entry.range} className="legend-item">
                    <span className="legend-dot" style={{ backgroundColor: CHART_COLORS[idx % CHART_COLORS.length] }}></span>
                    <span className="legend-label">{entry.range} ({entry.count})</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: GRIEVANCES */}
      {activeTab === 'grievances' && (
        <div className="tab-pane-container animate-fade-in">
          {/* Metrics Row */}
          <div className="dashboard-grid">
            <div className="metric-card glass-card border-blue">
              <div className="metric-header">
                <span className="metric-title">Total Grievances</span>
                <FileText className="metric-icon blue" size={20} />
              </div>
              <div className="metric-number">{metrics.totalComplaints}</div>
              <p className="metric-subtext">Total grievances filed</p>
            </div>

            <div className="metric-card glass-card border-orange">
              <div className="metric-header">
                <span className="metric-title">Pending Action</span>
                <Clock className="metric-icon orange" size={20} />
              </div>
              <div className="metric-number">{metrics.pendingComplaints}</div>
              <p className="metric-subtext">Awaiting resolution loops</p>
            </div>

            <div className="metric-card glass-card border-cyan">
              <div className="metric-header">
                <span className="metric-title">Avg Repair Time</span>
                <Clock className="metric-icon cyan" size={20} />
              </div>
              <div className="metric-number">{metrics.avgResolutionTimeHours}h</div>
              <p className="metric-subtext">From submission to fix</p>
            </div>

            <div className="metric-card glass-card border-green">
              <div className="metric-header">
                <span className="metric-title">Satisfaction</span>
                <div className="rating-row" style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#f59e0b' }}>
                  <Star size={16} fill="#f59e0b" />
                  <span>{metrics.averageRating}</span>
                </div>
              </div>
              <div className="metric-number">{metrics.averageRating}/5</div>
              <p className="metric-subtext">Student rating index</p>
            </div>
          </div>

          {/* Recharts Analytics Section */}
          <div className="charts-row-grid">
            <div className="chart-card glass-card">
              <h3>Grievances by Category</h3>
              <div className="chart-container-inner">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={chartsData.byCategory}>
                    <XAxis dataKey="category" stroke="#6b7280" fontSize={10} tickLine={false} />
                    <YAxis stroke="#6b7280" fontSize={10} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', color: '#0f172a' }} />
                    <Bar dataKey="count" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="chart-card glass-card">
              <h3>Daily Grievances Trend (Last 7 Days)</h3>
              <div className="chart-container-inner">
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={chartsData.trend}>
                    <XAxis dataKey="date" stroke="#6b7280" fontSize={10} tickLine={false} />
                    <YAxis stroke="#6b7280" fontSize={10} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', color: '#0f172a' }} />
                    <Line type="monotone" dataKey="count" stroke="var(--secondary)" strokeWidth={3} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="chart-card glass-card">
              <h3>Priority Distribution</h3>
              <div className="chart-container-inner flex-center">
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie
                      data={chartsData.byPriority}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="count"
                      nameKey="priority"
                    >
                      {chartsData.byPriority.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#0b1120', borderColor: 'rgba(255,255,255,0.08)' }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="pie-legend">
                  {chartsData.byPriority.map((entry, idx) => (
                    <div key={entry.priority} className="legend-item">
                      <span className="legend-dot" style={{ backgroundColor: CHART_COLORS[idx % CHART_COLORS.length] }}></span>
                      <span className="legend-label">{entry.priority} ({entry.count})</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Complaints Administration Log Table */}
          {renderGrievanceQueueTable()}
        </div>
      )}

      {/* TAB 4: HOSTEL */}
      {activeTab === 'hostel' && (
        <div className="tab-pane-container animate-fade-in">
          <div className="charts-row-grid" style={{ gridTemplateColumns: '1fr' }}>
            <div className="chart-card glass-card">
              <h3>Hostel Maintenance Requests Status</h3>
              {modulesData.hostel.status_distribution.length === 0 ? (
                <div className="empty-table-state">No hostel maintenance requests registered.</div>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={modulesData.hostel.status_distribution}>
                    <XAxis dataKey="status" stroke="#6b7280" fontSize={10} tickLine={false} />
                    <YAxis stroke="#6b7280" fontSize={10} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', color: '#0f172a' }} />
                    <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: TRANSPORT */}
      {activeTab === 'transport' && (
        <div className="tab-pane-container animate-fade-in">
          <div className="charts-row-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
            <div className="chart-card glass-card">
              <h3>Pass Requests status distribution</h3>
              {modulesData.transport.status_distribution.length === 0 ? (
                <div className="empty-table-state">No transport requests registered.</div>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={modulesData.transport.status_distribution}>
                    <XAxis dataKey="status" stroke="#6b7280" fontSize={10} tickLine={false} />
                    <YAxis stroke="#6b7280" fontSize={10} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', color: '#0f172a' }} />
                    <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="chart-card glass-card">
              <h3>Route Passenger Loads (Approved passes)</h3>
              {modulesData.transport.route_passengers.length === 0 ? (
                <div className="empty-table-state">No approved passengers on bus routes.</div>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={modulesData.transport.route_passengers}>
                    <XAxis dataKey="route" stroke="#6b7280" fontSize={10} tickLine={false} />
                    <YAxis stroke="#6b7280" fontSize={10} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', color: '#0f172a' }} />
                    <Bar dataKey="passengers" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 6: LIBRARY */}
      {activeTab === 'library' && (
        <div className="tab-pane-container animate-fade-in">
          <div className="dashboard-grid">
            <div className="metric-card glass-card border-blue">
              <div className="metric-header"><span className="metric-title">Active Book Loans</span></div>
              <div className="metric-number">{modulesData.library.active_loans}</div>
            </div>
            <div className="metric-card glass-card border-green">
              <div className="metric-header"><span className="metric-title">Total Returns</span></div>
              <div className="metric-number">{modulesData.library.total_returns}</div>
            </div>
            <div className="metric-card glass-card border-orange">
              <div className="metric-header"><span className="metric-title">Overdue Books</span></div>
              <div className="metric-number" style={{ color: 'var(--red-text)' }}>{modulesData.library.overdue_loans}</div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 7: PLACEMENTS */}
      {activeTab === 'placements' && (
        <div className="tab-pane-container animate-fade-in">
          <div className="charts-row-grid" style={{ gridTemplateColumns: '1fr' }}>
            <div className="chart-card glass-card">
              <h3>Applications Status Roster</h3>
              {modulesData.placements.status_distribution.length === 0 ? (
                <div className="empty-table-state">No student applications submitted yet.</div>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={modulesData.placements.status_distribution}>
                    <XAxis dataKey="status" stroke="#6b7280" fontSize={10} tickLine={false} />
                    <YAxis stroke="#6b7280" fontSize={10} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', color: '#0f172a' }} />
                    <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 8: EXAMS */}
      {activeTab === 'exams' && (
        <div className="tab-pane-container animate-fade-in">
          <div className="charts-row-grid" style={{ gridTemplateColumns: '1fr' }}>
            <div className="chart-card glass-card">
              <h3>Department-wise Upcoming Examinations</h3>
              {modulesData.exams.department_distribution.length === 0 ? (
                <div className="empty-table-state">No scheduled examinations registered.</div>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={modulesData.exams.department_distribution}>
                    <XAxis dataKey="department" stroke="#6b7280" fontSize={10} tickLine={false} />
                    <YAxis stroke="#6b7280" fontSize={10} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', color: '#0f172a' }} />
                    <Bar dataKey="exams" fill="#ec4899" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Admin Assign Staff Modal Dialog */}
      <Modal 
        isOpen={isAssignModalOpen} 
        title="Assign Grievance" 
        onClose={handleCloseModal}
      >
        {assignmentSuccessData ? (
          <div className="success-assignment-screen" style={{ padding: '10px 10px 20px 10px', textAlign: 'center' }}>
            <div style={{ fontSize: '3rem', marginBottom: '16px' }}>✅</div>
            <h3 style={{ color: 'var(--color-resolved)', fontSize: '1.4rem', fontWeight: 'bold', margin: '0 0 16px 0' }}>
              Successfully assigned to {assignmentSuccessData.facultyName}
            </h3>
            <p style={{ color: 'var(--text-primary)', fontSize: '1rem', margin: '0 0 8px 0', lineHeight: '1.5' }}>
              Your grievance has been assigned to <strong>{assignmentSuccessData.facultyName}</strong>.
            </p>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', margin: '0 0 24px 0', fontWeight: '500' }}>
              The issue will be resolved within <strong>2 working days</strong>.
            </p>
            
            <div style={{ backgroundColor: 'var(--bg-app)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '16px', textAlign: 'left', marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', fontSize: '0.9rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Faculty:</span>
                <strong style={{ color: 'var(--text-primary)' }}>{assignmentSuccessData.facultyName}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', fontSize: '0.9rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Branch:</span>
                <strong style={{ color: 'var(--text-primary)' }}>{assignmentSuccessData.branchName}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', fontSize: '0.9rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Assigned:</span>
                <strong style={{ color: 'var(--text-primary)' }}>{formatDateFull(assignmentSuccessData.assignedAt)}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Deadline:</span>
                <strong style={{ color: 'var(--text-primary)' }}>{formatDateShort(assignmentSuccessData.deadline)}</strong>
              </div>
            </div>

            <button 
              onClick={handleCloseSuccessModal} 
              className="btn btn-primary" 
              style={{ width: '100%', padding: '12px' }}
            >
              Done
            </button>
          </div>
        ) : (
          <div className="assign-modal-body">
            <div className="form-group" style={{ marginBottom: '1.25rem' }}>
              <label htmlFor="branchSelect">Branch</label>
              <select
                id="branchSelect"
                className="form-input"
                value={selectedBranch}
                onChange={(e) => setSelectedBranch(e.target.value)}
              >
                <option value="" style={{ color: 'var(--text-primary)', backgroundColor: 'var(--bg-card)' }}>Select Branch</option>
                {['CSE', 'IT', 'ECE', 'EEE', 'ME', 'CIVIL', 'AI & DS'].map((br) => (
                  <option key={br} value={br} style={{ color: 'var(--text-primary)', backgroundColor: 'var(--bg-card)' }}>
                    {br}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: '1.25rem' }}>
              <label htmlFor="facultySelect">Faculty Name</label>
              <select
                id="facultySelect"
                className="form-input"
                value={selectedFacultyId}
                onChange={(e) => setSelectedFacultyId(e.target.value)}
                disabled={!selectedBranch}
              >
                {!selectedBranch ? (
                  <option value="" style={{ color: 'var(--text-primary)', backgroundColor: 'var(--bg-card)' }}>Select a branch first</option>
                ) : (
                  <>
                    <option value="" style={{ color: 'var(--text-primary)', backgroundColor: 'var(--bg-card)' }}>Select Faculty</option>
                    {effectiveFacultyList
                      .filter(fac => isBranchMatch(fac.department, selectedBranch))
                      .map((fac) => (
                        <option key={fac.id} value={fac.id} style={{ color: 'var(--text-primary)', backgroundColor: 'var(--bg-card)' }}>
                          {fac.username} — {fac.department}
                        </option>
                      ))}
                    {effectiveFacultyList.filter(fac => isBranchMatch(fac.department, selectedBranch)).length === 0 && (
                      <option value="" disabled style={{ color: 'var(--text-muted)', backgroundColor: 'var(--bg-card)' }}>No faculty members found.</option>
                    )}
                  </>
                )}
              </select>
            </div>

            {validationError && (
              <div className="error-message" style={{ color: 'var(--red-text)', fontSize: '0.875rem', marginBottom: '1rem', fontWeight: '500' }}>
                {validationError}
              </div>
            )}

            <div className="modal-buttons">
              <button onClick={handleCloseModal} className="btn btn-secondary">
                Cancel
              </button>
              <button 
                onClick={handleAssignStaff} 
                className="btn btn-primary" 
                disabled={assigning || !selectedFacultyId || !selectedBranch || !!validationError}
              >
                {assigning ? 'Assigning...' : 'Assign Faculty'}
              </button>
            </div>
          </div>
        )}
      </Modal>

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
export default AdminDashboard;

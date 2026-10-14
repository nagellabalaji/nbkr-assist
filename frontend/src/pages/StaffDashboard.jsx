import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { complaintService } from '../services/complaints';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import { useAuth } from '../context/AuthContext';
import { 
  Wrench, CheckCircle, Clock, MapPin, Tag, 
  Calendar, ArrowRight, AlertTriangle, Search, Filter, ShieldAlert
} from 'lucide-react';
import './StaffDashboard.css';

export const StaffDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [complaints, setComplaints] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // Filtering, Search, and Pagination States
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [slaStatus, setSlaStatus] = useState('');
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(10);

  // Metrics state (separately fetched or calculated from total loaded)
  const [metrics, setMetrics] = useState({
    total: 0,
    open: 0,
    underReview: 0,
    assigned: 0,
    inProgress: 0,
    resolved: 0,
    critical: 0,
    breached: 0
  });

  const loadStaffTickets = async () => {
    setLoading(true);
    try {
      const params = {
        search: search.trim() || undefined,
        status: status || undefined,
        priority: priority || undefined,
        category_id: categoryId || undefined,
        sla_status: slaStatus || undefined,
        page,
        per_page: perPage
      };
      
      const res = await complaintService.getComplaints(params);
      if (res.success) {
        setComplaints(res.data);
        setTotalCount(res.total_count || res.data.length);
      }
    } catch (e) {
      setToast({ show: true, message: 'Failed to retrieve assigned tickets.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // Fetch full tickets once to calculate dashboard metrics independently of pagination
  const loadMetrics = async () => {
    try {
      const res = await complaintService.getComplaints({ per_page: 1000 });
      if (res.success) {
        const list = res.data;
        setMetrics({
          total: list.length,
          open: list.filter(c => ['Submitted', 'Reopened'].includes(c.status)).length,
          underReview: list.filter(c => c.status === 'Under Review').length,
          assigned: list.filter(c => c.status === 'Assigned').length,
          inProgress: list.filter(c => c.status === 'In Progress').length,
          resolved: list.filter(c => ['Resolved', 'Closed'].includes(c.status)).length,
          critical: list.filter(c => ['Critical', 'Urgent', 'High'].includes(c.ai_priority)).length,
          breached: list.filter(c => c.sla_status === 'Breached').length
        });
      }
    } catch (e) {
      console.error("Failed to load operations metrics:", e);
    }
  };

  useEffect(() => {
    loadStaffTickets();
  }, [search, status, priority, categoryId, slaStatus, page, perPage]);

  useEffect(() => {
    loadMetrics();
  }, []);

  const totalPages = Math.ceil(totalCount / perPage);

  if (loading && complaints.length === 0) {
    return <Loader message="Opening operations desk..." />;
  }

  return (
    <div className="staff-dashboard-container animate-fade-in">
      <div className="staff-header-banner">
        <h1>NBKR Grievance Operations Desk</h1>
        <p>Manage, allocate, and track resolution timelines of grievances filed by students.</p>
      </div>

      {/* Grid of 8 Metrics Cards */}
      <div className="metrics-summary-grid">
        <div className="metric-card-small border-blue" onClick={() => { setStatus(''); setSlaStatus(''); setPriority(''); }}>
          <span className="m-lbl">Total</span>
          <span className="m-num">{metrics.total}</span>
        </div>
        <div className="metric-card-small border-purple" onClick={() => { setStatus('Submitted'); setSlaStatus(''); setPriority(''); }}>
          <span className="m-lbl">Open</span>
          <span className="m-num">{metrics.open}</span>
        </div>
        <div className="metric-card-small border-orange" onClick={() => { setStatus('Under Review'); setSlaStatus(''); setPriority(''); }}>
          <span className="m-lbl">Review</span>
          <span className="m-num">{metrics.underReview}</span>
        </div>
        <div className="metric-card-small border-yellow" onClick={() => { setStatus('Assigned'); setSlaStatus(''); setPriority(''); }}>
          <span className="m-lbl">Assigned</span>
          <span className="m-num">{metrics.assigned}</span>
        </div>
        <div className="metric-card-small border-cyan" onClick={() => { setStatus('In Progress'); setSlaStatus(''); setPriority(''); }}>
          <span className="m-lbl">In Progress</span>
          <span className="m-num">{metrics.inProgress}</span>
        </div>
        <div className="metric-card-small border-green" onClick={() => { setStatus('Resolved'); setSlaStatus(''); setPriority(''); }}>
          <span className="m-lbl">Resolved</span>
          <span className="m-num">{metrics.resolved}</span>
        </div>
        <div className="metric-card-small border-red" onClick={() => { setPriority('High'); setStatus(''); setSlaStatus(''); }}>
          <span className="m-lbl">Critical</span>
          <span className="m-num">{metrics.critical}</span>
        </div>
        <div className="metric-card-small border-dark-red" onClick={() => { setSlaStatus('Breached'); setStatus(''); setPriority(''); }}>
          <span className="m-lbl">SLA Breached</span>
          <span className="m-num">{metrics.breached}</span>
        </div>
      </div>

      {/* Search and Filters Hub */}
      <div className="filters-hub-card glass-card">
        <div className="search-box-row">
          <Search className="search-icon" size={16} />
          <input 
            type="text"
            className="form-input search-input"
            placeholder="Search by Grievance ID, Subject, or Roll Number..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>

        <div className="filters-select-row">
          <div className="filter-group">
            <label>Status</label>
            <select className="form-input" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
              <option value="">All Statuses</option>
              <option value="Submitted">Submitted</option>
              <option value="Under Review">Under Review</option>
              <option value="Assigned">Assigned</option>
              <option value="In Progress">In Progress</option>
              <option value="Resolved">Resolved</option>
              <option value="Closed">Closed</option>
              <option value="Reopened">Reopened</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Priority</label>
            <select className="form-input" value={priority} onChange={(e) => { setPriority(e.target.value); setPage(1); }}>
              <option value="">All Priorities</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>

          <div className="filter-group">
            <label>SLA Status</label>
            <select className="form-input" value={slaStatus} onChange={(e) => { setSlaStatus(e.target.value); setPage(1); }}>
              <option value="">All Tickets</option>
              <option value="Normal">Normal</option>
              <option value="Breached">SLA Breached</option>
            </select>
          </div>
        </div>
      </div>

      {/* Queue List Table */}
      <div className="queue-table-section glass-card">
        <div className="section-header-row">
          <h3>Grievance Queue ({totalCount} found)</h3>
        </div>

        {complaints.length === 0 ? (
          <div className="empty-state-queue">
            <CheckCircle size={40} className="check-done-icon" />
            <h4>No grievances match your filter criteria</h4>
            <p>Check search keywords or verify filter values.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="ops-table">
              <thead>
                <tr>
                  <th>Ticket ID</th>
                  <th>Student Info</th>
                  <th>Subject</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>SLA Status</th>
                  <th>Lodged On</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {complaints.map((comp) => (
                  <tr 
                    key={comp.id} 
                    onClick={() => navigate(`/complaint/${comp.id}`)}
                    className={`ops-row-clickable ${comp.sla_status === 'Breached' ? 'row-breached' : ''}`}
                  >
                    <td className="ticket-id-td">{comp.id}</td>
                    <td>
                      <div className="stu-info-td">
                        <strong>{comp.student_name}</strong>
                        <span>{comp.roll_no}</span>
                      </div>
                    </td>
                    <td className="subject-td">
                      <div className="subj-info">
                        <strong>{comp.title}</strong>
                        <span>{comp.location}</span>
                      </div>
                    </td>
                    <td>{comp.category_name}</td>
                    <td>
                      <span className={`p-badge p-${comp.ai_priority.toLowerCase()}`}>
                        {comp.ai_priority}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge ${comp.status.toLowerCase().replace(" ", "-")}`}>
                        {comp.status}
                      </span>
                    </td>
                    <td>
                      {comp.sla_status === 'Breached' ? (
                        <span className="sla-badge breached">
                          <ShieldAlert size={12} /> Breached
                        </span>
                      ) : (
                        <span className="sla-badge normal">Normal</span>
                      )}
                    </td>
                    <td>{new Date(comp.created_at).toLocaleDateString()}</td>
                    <td>
                      <button className="view-detail-link">
                        Manage <ArrowRight size={12} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="pagination-wrapper">
            <button 
              className="btn btn-secondary pagination-btn"
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
            >
              Previous
            </button>
            <span className="pagination-text">
              Page <strong>{page}</strong> of {totalPages}
            </span>
            <button 
              className="btn btn-secondary pagination-btn"
              disabled={page === totalPages}
              onClick={() => setPage(p => p + 1)}
            >
              Next
            </button>
          </div>
        )}
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
export default StaffDashboard;

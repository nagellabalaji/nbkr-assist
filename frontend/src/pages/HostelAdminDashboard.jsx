import React, { useEffect, useState } from 'react';
import { Search, Info, CheckCircle, Clock, XCircle, AlertCircle, Wrench, ShieldAlert } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './HostelAdminDashboard.css';

export const HostelAdminDashboard = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // Filter states
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Edit states
  const [editingReqId, setEditingReqId] = useState(null);
  const [editStatus, setEditStatus] = useState('');
  const [editNotes, setEditNotes] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchRequests = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/hostel/requests', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        setRequests(json.data);
      }
    } catch (err) {
      setToast({ show: true, message: 'Failed to access maintenance registers.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleOpenEdit = (req) => {
    setEditingReqId(req.id);
    setEditStatus(req.status);
    setEditNotes(req.admin_notes || '');
  };

  const handleSaveUpdate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/hostel/requests/${editingReqId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          status: editStatus,
          admin_notes: editNotes
        })
      });
      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: 'Maintenance request updated successfully!', type: 'success' });
        setEditingReqId(null);
        fetchRequests();
      } else {
        setToast({ show: true, message: json.message || 'Update failed.', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server communication error.', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  // Metrics
  const getCount = (st) => requests.filter(r => r.status === st).length;

  const filteredRequests = requests.filter(r => {
    const matchSearch = r.student_name.toLowerCase().includes(search.toLowerCase()) || 
                        r.roll_no.toLowerCase().includes(search.toLowerCase()) ||
                        r.description.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'all' || r.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const getStatusBadgeClass = (status) => {
    switch (status?.toLowerCase()) {
      case 'resolved': return 'status-resolved';
      case 'in_progress': return 'status-progress';
      case 'rejected': return 'status-rejected';
      default: return 'status-submitted';
    }
  };

  if (loading) return <Loader message="Accessing Hostel registers..." />;

  return (
    <div className="hostel-admin-container animate-fade-in">
      <div className="admin-header">
        <h1>Hostel Maintenance Workspace</h1>
        <p>Monitor room complaints, allocate technicians, and log resolved audits.</p>
      </div>

      {/* Metrics Board */}
      <div className="admin-metrics-row">
        <div className="metric-card glass-card">
          <Wrench className="m-icon" />
          <div className="m-val">{requests.length}</div>
          <div className="m-lbl">Total Requests</div>
        </div>
        <div className="metric-card glass-card warning">
          <AlertCircle className="m-icon" />
          <div className="m-val">{getCount('submitted')}</div>
          <div className="m-lbl">Submitted / Unassigned</div>
        </div>
        <div className="metric-card glass-card progress">
          <Clock className="m-icon" />
          <div className="m-val">{getCount('in_progress')}</div>
          <div className="m-lbl">In Progress</div>
        </div>
        <div className="metric-card glass-card success">
          <CheckCircle className="m-icon" />
          <div className="m-val">{getCount('resolved')}</div>
          <div className="m-lbl">Resolved</div>
        </div>
      </div>

      {/* Roster Controls */}
      <div className="roster-controls-card glass-card">
        <div className="search-box-wrapper">
          <Search size={18} className="search-icon" />
          <input 
            type="text" 
            placeholder="Search by student name, roll number, or description..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-item">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="status-select-filter">
            <option value="all">All Request Statuses</option>
            <option value="submitted">Submitted</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>

      {/* Roster Table */}
      <div className="table-responsive glass-card">
        {filteredRequests.length === 0 ? (
          <div className="empty-roster">No maintenance requests found mapping your search filters.</div>
        ) : (
          <table className="roster-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Student & Room</th>
                <th>Category</th>
                <th>Description</th>
                <th>Status</th>
                <th>Last Update</th>
                <th className="center-text">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRequests.map(r => (
                <tr key={r.id}>
                  <td className="monospace-cell">HST-{String(r.id).padStart(4, '0')}</td>
                  <td>
                    <div className="student-room-meta">
                      <strong>{r.student_name} ({r.roll_no})</strong>
                      <span>Block: {r.hostel_no} | Room: {r.room_no}</span>
                    </div>
                  </td>
                  <td><span className="category-badge">{r.request_type.toUpperCase()}</span></td>
                  <td><p className="description-cell">{r.description}</p></td>
                  <td>
                    <span className={`status-pill ${getStatusBadgeClass(r.status)}`}>
                      {r.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td>{new Date(r.updated_at).toLocaleDateString()}</td>
                  <td className="actions-cell">
                    <button className="btn btn-outline edit-action-btn" onClick={() => handleOpenEdit(r)}>
                      Manage
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Edit Form Modal */}
      {editingReqId && (
        <div className="modal-backdrop">
          <div className="modal-content glass-card animate-zoom-in">
            <h3>Manage Maintenance Request HST-{String(editingReqId).padStart(4, '0')}</h3>
            <hr />
            <form onSubmit={handleSaveUpdate} className="admin-update-form">
              <div className="form-group">
                <label>Update Status</label>
                <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>
                  <option value="submitted">Submitted</option>
                  <option value="in_progress">In Progress / Assigned</option>
                  <option value="resolved">Resolved / Fixed</option>
                  <option value="rejected">Rejected / Cancelled</option>
                </select>
              </div>

              <div className="form-group">
                <label>Admin notes / Dispatch details</label>
                <textarea 
                  value={editNotes}
                  onChange={(e) => setEditNotes(e.target.value)}
                  placeholder="Specify details, technician name, or closure remarks..."
                  rows={4}
                />
              </div>

              <div className="modal-actions-footer">
                <button type="button" className="btn btn-outline" onClick={() => setEditingReqId(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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
export default HostelAdminDashboard;

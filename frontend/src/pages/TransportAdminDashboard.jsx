import React, { useEffect, useState } from 'react';
import { Search, Bus, Clock, MapPin, CheckCircle, AlertCircle, XCircle } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './TransportAdminDashboard.css';

export const TransportAdminDashboard = () => {
  const [requests, setRequests] = useState([]);
  const [routes, setRoutes] = useState([]);
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

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch routes
      const routesRes = await fetch('/api/transport/routes', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const routesJson = await routesRes.json();
      if (routesJson.success) {
        setRoutes(routesJson.data);
      }

      // Fetch requests
      const reqRes = await fetch('/api/transport/requests', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const reqJson = await reqRes.json();
      if (reqJson.success) {
        setRequests(reqJson.data);
      }
    } catch (err) {
      setToast({ show: true, message: 'Failed to access transit registers.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
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
      const res = await fetch(`/api/transport/requests/${editingReqId}`, {
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
        setToast({ show: true, message: 'Transport request processed successfully!', type: 'success' });
        setEditingReqId(null);
        fetchData();
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
      case 'approved': return 'status-approved';
      case 'rejected': return 'status-rejected';
      default: return 'status-submitted';
    }
  };

  if (loading) return <Loader message="Accessing transit portal..." />;

  return (
    <div className="transport-admin-container animate-fade-in">
      <div className="admin-header">
        <h1>Transport Roster Desk</h1>
        <p>Monitor bus routing schedules, approve boarding passes, and update timings.</p>
      </div>

      <div className="admin-layout-grid">
        {/* Left: Requests list table */}
        <div className="requests-table-section">
          {/* Metrics Row */}
          <div className="admin-metrics-row">
            <div className="metric-card glass-card">
              <Bus className="m-icon" />
              <div className="m-val">{requests.length}</div>
              <div className="m-lbl">Total Requests</div>
            </div>
            <div className="metric-card glass-card warning">
              <AlertCircle className="m-icon" />
              <div className="m-val">{getCount('submitted')}</div>
              <div className="m-lbl">Pending Review</div>
            </div>
            <div className="metric-card glass-card success">
              <CheckCircle className="m-icon" />
              <div className="m-val">{getCount('approved')}</div>
              <div className="m-lbl">Approved passes</div>
            </div>
          </div>

          {/* Roster Controls */}
          <div className="roster-controls-card glass-card">
            <div className="search-box-wrapper">
              <Search size={18} className="search-icon" />
              <input 
                type="text" 
                placeholder="Search requests by student or details..." 
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="search-input"
              />
            </div>

            <div className="filter-item">
              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="status-select-filter">
                <option value="all">All Request Statuses</option>
                <option value="submitted">Submitted</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </div>

          {/* Roster Table */}
          <div className="table-responsive glass-card">
            {filteredRequests.length === 0 ? (
              <div className="empty-roster">No transport requests found mapping your search.</div>
            ) : (
              <table className="roster-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Student Details</th>
                    <th>Type</th>
                    <th>Selected Route</th>
                    <th>Status</th>
                    <th className="center-text">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRequests.map(r => (
                    <tr key={r.id}>
                      <td className="monospace-cell">TRN-{String(r.id).padStart(4, '0')}</td>
                      <td>
                        <div className="student-details-meta">
                          <strong>{r.student_name}</strong>
                          <span>Roll: {r.roll_no}</span>
                        </div>
                      </td>
                      <td><span className="type-badge">{r.request_type.replace('_', ' ').toUpperCase()}</span></td>
                      <td>{r.route_name !== 'None' ? `${r.route_name} (${r.bus_number})` : 'None'}</td>
                      <td>
                        <span className={`status-pill ${getStatusBadgeClass(r.status)}`}>
                          {r.status}
                        </span>
                      </td>
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
        </div>

        {/* Right: Active bus routes list */}
        <div className="active-routes-section glass-card">
          <h3>Active Bus Routes</h3>
          <div className="routes-list">
            {routes.map(r => (
              <div key={r.id} className="route-card glass-card">
                <div className="route-card-title">
                  <Bus size={18} className="bus-icon" />
                  <strong>{r.route_name}</strong>
                </div>
                <div className="route-card-sub">
                  <span>Bus: <strong>{r.bus_number}</strong></span>
                  <span>Time: <strong>{r.timings}</strong></span>
                </div>
                <div className="route-card-stops">
                  <strong>Stops:</strong>
                  <div className="stops-row">
                    {r.stops.map((stop, idx) => (
                      <span key={idx} className="stop-tag"><MapPin size={10} /> {stop}</span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Edit Form Modal */}
      {editingReqId && (
        <div className="modal-backdrop">
          <div className="modal-content glass-card animate-zoom-in">
            <h3>Manage Transit Request TRN-{String(editingReqId).padStart(4, '0')}</h3>
            <hr />
            <form onSubmit={handleSaveUpdate} className="admin-update-form">
              <div className="form-group">
                <label>Update Status</label>
                <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>
                  <option value="submitted">Submitted</option>
                  <option value="approved">Approved (Issue Pass)</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>

              <div className="form-group">
                <label>Admin Remarks / Route notes</label>
                <textarea 
                  value={editNotes}
                  onChange={(e) => setEditNotes(e.target.value)}
                  placeholder="Specify boarding details, pass validity dates, or rejection reason..."
                  rows={4}
                />
              </div>

              <div className="modal-actions-footer">
                <button type="button" className="btn btn-outline" onClick={() => setEditingReqId(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Processing...' : 'Save Changes'}
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
export default TransportAdminDashboard;

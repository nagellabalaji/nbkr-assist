import React, { useEffect, useState } from 'react';
import { Truck, PlusCircle, AlertCircle, MapPin, Bus, Clock } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './StudentTransport.css';

export const StudentTransport = () => {
  const [routes, setRoutes] = useState([]);
  const [requests, setRequests] = useState([]);
  const [transportStatus, setTransportStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });
  const [showModal, setShowModal] = useState(false);

  // Form fields
  const [requestType, setRequestType] = useState('new_pass');
  const [routeId, setRouteId] = useState('');
  const [description, setDescription] = useState('');

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch status
      const statusRes = await fetch('/api/transport/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const statusJson = await statusRes.json();
      if (statusJson.success) {
        setTransportStatus(statusJson.data.transport_status);
      }

      // Fetch routes
      const routesRes = await fetch('/api/transport/routes', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const routesJson = await routesRes.json();
      if (routesJson.success) {
        setRoutes(routesJson.data);
        if (routesJson.data.length > 0) {
          setRouteId(routesJson.data[0].id);
        }
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
      setToast({ show: true, message: 'Failed to access transport register.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!description.strip()) {
      setToast({ show: true, message: 'Please input a request description.', type: 'error' });
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/transport/requests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          request_type: requestType,
          route_id: requestType === 'grievance' ? null : parseInt(routeId),
          description
        })
      });
      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: 'Transport request registered successfully!', type: 'success' });
        setShowModal(false);
        setDescription('');
        fetchData();
      } else {
        setToast({ show: true, message: json.message || 'Request failed.', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server communication error.', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status?.toLowerCase()) {
      case 'approved': return 'status-approved';
      case 'rejected': return 'status-rejected';
      default: return 'status-submitted';
    }
  };

  if (loading) return <Loader message="Accessing transit registers..." />;

  return (
    <div className="student-transport-container animate-fade-in">
      <div className="transport-header">
        <h1>Transport & Transit Desk</h1>
        <p>Apply for bus passes, verify active route locations, stops, and schedules.</p>
      </div>

      <div className="transport-layout-grid">
        {/* Left column: Status card and Routes display */}
        <div className="routes-and-status-column">
          {/* Status info */}
          <div className="transit-status-card glass-card">
            <div className="status-row-info">
              <Truck size={22} className="trans-icon" />
              <div>
                <h3>Transit configuration</h3>
                <p>Status: <strong className="green">{transportStatus}</strong></p>
              </div>
            </div>
            <button className="btn btn-primary pass-req-btn" onClick={() => setShowModal(true)}>
              <PlusCircle size={18} />
              <span>Request Bus Pass / Route Change</span>
            </button>
          </div>

          {/* Active routes roster */}
          <div className="routes-list-card glass-card">
            <h3>Active College Bus Routes</h3>
            <div className="bus-routes-list">
              {routes.map(r => (
                <div key={r.id} className="route-detail-item glass-card">
                  <div className="route-item-title">
                    <Bus size={18} className="bus-icon" />
                    <strong>{r.route_name}</strong>
                  </div>
                  <div className="route-item-sub">
                    <span>Bus No: <strong>{r.bus_number}</strong></span>
                    <span>Timing: <strong className="timing-clock"><Clock size={12} /> {r.timings}</strong></span>
                  </div>
                  <div className="route-item-stops">
                    <strong>Stops:</strong>
                    <div className="stops-row">
                      {r.stops.map((stop, i) => (
                        <span key={i} className="stop-tag"><MapPin size={10} /> {stop}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right column: Requests list history */}
        <div className="requests-history-card glass-card">
          <h3>Transit Requests history</h3>
          {requests.length === 0 ? (
            <div className="empty-requests">
              <AlertCircle size={36} />
              <p>No transit pass or routing requests raised yet.</p>
            </div>
          ) : (
            <div className="requests-timeline">
              {requests.map(r => (
                <div key={r.id} className="request-timeline-item glass-card">
                  <div className="item-header">
                    <span className="item-type">{r.request_type.replace('_', ' ').toUpperCase()}</span>
                    <span className={`status-pill ${getStatusBadgeClass(r.status)}`}>
                      {r.status}
                    </span>
                  </div>
                  <p className="item-desc">{r.description}</p>
                  {r.route_name !== 'None' && (
                    <div className="route-meta-box">
                      Route: <strong>{r.route_name}</strong> ({r.bus_number})
                    </div>
                  )}
                  {r.admin_notes && (
                    <div className="admin-notes-box">
                      <strong>Admin Notes:</strong> {r.admin_notes}
                    </div>
                  )}
                  <span className="item-date">Created on: {new Date(r.created_at).toLocaleDateString()}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal pass request form */}
      {showModal && (
        <div className="modal-backdrop">
          <div className="modal-content glass-card animate-zoom-in">
            <h3>Request Transit Pass</h3>
            <hr />
            <form onSubmit={handleFormSubmit} className="transport-form">
              <div className="form-group">
                <label>Request Type</label>
                <select value={requestType} onChange={(e) => setRequestType(e.target.value)}>
                  <option value="new_pass">New Bus Pass request</option>
                  <option value="renew_pass">Renew existing Bus Pass</option>
                  <option value="route_change">Change Bus Route</option>
                  <option value="grievance">Transit grievance / complaint</option>
                </select>
              </div>

              {requestType !== 'grievance' && (
                <div className="form-group">
                  <label>Select Target Bus Route</label>
                  <select value={routeId} onChange={(e) => setRouteId(e.target.value)}>
                    {routes.map(r => (
                      <option key={r.id} value={r.id}>{r.route_name} ({r.bus_number})</option>
                    ))}
                  </select>
                </div>
              )}

              <div className="form-group">
                <label>Request description / remarks</label>
                <textarea 
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Specify boarding point and other details..."
                  required
                  rows={4}
                />
              </div>

              <div className="modal-actions-footer">
                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Registering...' : 'Submit Request'}
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
export default StudentTransport;

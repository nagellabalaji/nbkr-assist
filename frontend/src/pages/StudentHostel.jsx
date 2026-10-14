import React, { useEffect, useState } from 'react';
import { ShieldAlert, PlusCircle, Wrench, Home, Info, Clock, CheckCircle } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './StudentHostel.css';

export const StudentHostel = () => {
  const [requests, setRequests] = useState([]);
  const [roomInfo, setRoomInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });
  const [showModal, setShowModal] = useState(false);

  // Form fields
  const [requestType, setRequestType] = useState('electrical');
  const [description, setDescription] = useState('');

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch Room Info
      const roomRes = await fetch('/api/hostel/room-info', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const roomJson = await roomRes.json();
      if (roomJson.success) {
        setRoomInfo(roomJson.data);
      }

      // Fetch Requests List
      const reqRes = await fetch('/api/hostel/requests', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const reqJson = await reqRes.json();
      if (reqJson.success) {
        setRequests(reqJson.data);
      }
    } catch (err) {
      setToast({ show: true, message: 'Failed to fetch hostel details.', type: 'error' });
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
      const res = await fetch('/api/hostel/requests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          request_type: requestType,
          description
        })
      });
      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: 'Maintenance request registered successfully!', type: 'success' });
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
      case 'resolved': return 'status-resolved';
      case 'in_progress': return 'status-progress';
      case 'rejected': return 'status-rejected';
      default: return 'status-submitted';
    }
  };

  if (loading) return <Loader message="Accessing hostel portals..." />;

  const isHosteller = roomInfo?.hostel_status === 'Hosteller';

  return (
    <div className="student-hostel-container animate-fade-in">
      <div className="hostel-header">
        <h1>Hostel Services Workspace</h1>
        <p>Lodge room maintenance complaints, track repairs, and manage room registers.</p>
      </div>

      {!isHosteller ? (
        <div className="dayscholar-lock glass-card">
          <ShieldAlert size={48} className="lock-icon" />
          <h3>Hostel Portal Locked</h3>
          <p>Your academic profile is registered as a **Dayscholar**. Room maintenance logs are restricted to students residing in campus blocks.</p>
        </div>
      ) : (
        <div className="hosteller-layout">
          {/* Room info card */}
          <div className="room-info-card glass-card">
            <div className="card-title-row">
              <Home size={20} className="info-icon" />
              <h3>Hostel Occupancy Details</h3>
            </div>
            <div className="room-details-grid">
              <div className="detail-box">
                <span className="lbl">Hostel Block</span>
                <span className="val">{roomInfo.hostel_no || 'Block A'}</span>
              </div>
              <div className="detail-box">
                <span className="lbl">Room Number</span>
                <span className="val">{roomInfo.room_no || 'Room 102'}</span>
              </div>
              <div className="detail-box">
                <span className="lbl">Status</span>
                <span className="val green">Active Resident</span>
              </div>
            </div>
            <button className="btn btn-primary raise-req-btn" onClick={() => setShowModal(true)}>
              <PlusCircle size={18} />
              <span>Raise Room Maintenance request</span>
            </button>
          </div>

          {/* Requests list */}
          <div className="requests-history glass-card">
            <h3>Maintenance Logs History</h3>
            {requests.length === 0 ? (
              <div className="empty-requests">
                <Clock size={36} />
                <p>No maintenance requests raised yet.</p>
              </div>
            ) : (
              <div className="requests-timeline">
                {requests.map(r => (
                  <div key={r.id} className="request-timeline-item glass-card">
                    <div className="item-header">
                      <span className="item-type">{r.request_type.toUpperCase()}</span>
                      <span className={`status-pill ${getStatusBadgeClass(r.status)}`}>
                        {r.status.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="item-desc">{r.description}</p>
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
      )}

      {/* Raise Request Modal */}
      {showModal && (
        <div className="modal-backdrop">
          <div className="modal-content glass-card animate-zoom-in">
            <h3>Lodge Room Maintenance Request</h3>
            <hr />
            <form onSubmit={handleFormSubmit} className="hostel-form">
              <div className="form-group">
                <label>Request Category</label>
                <select value={requestType} onChange={(e) => setRequestType(e.target.value)}>
                  <option value="electrical">Electrical (Fan, Light, Switch)</option>
                  <option value="plumbing">Plumbing (Tap leakage, Washroom pipes)</option>
                  <option value="room_repair">Room Repair (Lock, Door, Cupboard)</option>
                  <option value="dining">Dining / Mess complaints</option>
                  <option value="other">Other general maintenance</option>
                </select>
              </div>

              <div className="form-group">
                <label>Complaint Description</label>
                <textarea 
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe your room repair issue in detail..."
                  required
                  rows={4}
                />
              </div>

              <div className="modal-actions-footer">
                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Registering...' : 'Raise Request'}
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
export default StudentHostel;

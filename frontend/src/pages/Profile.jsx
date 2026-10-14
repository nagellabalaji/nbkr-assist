import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import { User, Mail, Shield, BookOpen, Home, Phone, Wrench } from 'lucide-react';
import './Profile.css';

export const Profile = () => {
  const { user, updateProfile } = useAuth();
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // Student specific form states
  const [hostelNo, setHostelNo] = useState(user?.profile?.hostel_no || '');
  const [roomNo, setRoomNo] = useState(user?.profile?.room_no || '');
  const [contactNo, setContactNo] = useState(user?.profile?.contact_no || '');

  // Staff specific form states
  const [specialization, setSpecialization] = useState(user?.profile?.specialization || 'Electrical');
  const [isAvailable, setIsAvailable] = useState(user?.profile?.is_available ?? true);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    let payload = {};
    if (user?.role === 'student') {
      payload = {
        hostel_no: hostelNo.trim(),
        room_no: roomNo.trim(),
        contact_no: contactNo.trim()
      };
    } else if (user?.role === 'staff') {
      payload = {
        specialization,
        is_available: isAvailable
      };
    }

    const res = await updateProfile(payload);
    setLoading(false);

    if (res.success) {
      setToast({ show: true, message: 'Profile updated successfully!', type: 'success' });
    } else {
      setToast({ show: true, message: res.message || 'Failed to update profile.', type: 'error' });
    }
  };

  return (
    <div className="profile-page-container animate-fade-in">
      <div className="profile-header-section">
        <h1>My Account Profile</h1>
        <p>Manage your institutional contact details and academic preferences.</p>
      </div>

      <div className="profile-grid">
        {/* Left Side: Static User Profile Summary Card */}
        <div className="profile-summary-card glass-card">
          <div className="profile-avatar-large">
            {user?.username?.[0]?.toUpperCase()}
          </div>
          <h3>{user?.username}</h3>
          <span className="profile-role-badge">{user?.role?.toUpperCase()}</span>
          
          <div className="profile-quick-details">
            <div className="quick-detail-item">
              <Mail size={16} />
              <span>{user?.email}</span>
            </div>
            
            <div className="quick-detail-item">
              <Shield size={16} />
              <span>Status: <strong style={{ color: 'var(--color-resolved)' }}>Active</strong></span>
            </div>

            {user?.role === 'student' && (
              <>
                <div className="quick-detail-item">
                  <BookOpen size={16} />
                  <span>Roll No: <strong>{user?.profile?.roll_no}</strong></span>
                </div>
                <div className="quick-detail-item">
                  <BookOpen size={16} />
                  <span>Dept: {user?.profile?.department}</span>
                </div>
              </>
            )}

            {(user?.role === 'staff' || user?.role === 'faculty' || user?.role === 'hod') && (
              <>
                <div className="quick-detail-item">
                  <Wrench size={16} />
                  <span>Dept: {user?.profile?.department}</span>
                </div>
                {user?.profile?.employee_id && (
                  <div className="quick-detail-item">
                    <User size={16} />
                    <span>Emp ID: <strong>{user?.profile?.employee_id}</strong></span>
                  </div>
                )}
                {user?.profile?.designation && (
                  <div className="quick-detail-item">
                    <User size={16} />
                    <span>Designation: {user?.profile?.designation}</span>
                  </div>
                )}
                {user?.profile?.phone && (
                  <div className="quick-detail-item">
                    <Phone size={16} />
                    <span>Phone: {user?.profile?.phone}</span>
                  </div>
                )}
                {user?.profile?.academic_year && (
                  <div className="quick-detail-item">
                    <BookOpen size={16} />
                    <span>Academic Year: {user?.profile?.academic_year}</span>
                  </div>
                )}
                {user?.role === 'staff' && (
                  <div className="quick-detail-item">
                    <Wrench size={16} />
                    <span>Spec: {user?.profile?.specialization}</span>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Right Side: Profile Edit Form */}
        {user?.role !== 'admin' && (
          <div className="profile-edit-card glass-card">
            <h3>Update Profile Settings</h3>
            
            <form onSubmit={handleSubmit} className="profile-form">
              {user?.role === 'student' && (
                <>
                  <div className="form-group">
                    <label htmlFor="hostelName">Hostel Block / Name</label>
                    <div className="profile-input-wrapper">
                      <Home className="input-icon" size={16} />
                      <input 
                        id="hostelName"
                        type="text" 
                        className="form-input has-icon"
                        placeholder="e.g. Hostel Block B"
                        value={hostelNo}
                        onChange={(e) => setHostelNo(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="roomNum">Room Number</label>
                    <div className="profile-input-wrapper">
                      <Home className="input-icon" size={16} />
                      <input 
                        id="roomNum"
                        type="text" 
                        className="form-input has-icon"
                        placeholder="e.g. 204"
                        value={roomNo}
                        onChange={(e) => setRoomNo(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="form-group full-width">
                    <label htmlFor="contactNum">Mobile Number</label>
                    <div className="profile-input-wrapper">
                      <Phone className="input-icon" size={16} />
                      <input 
                        id="contactNum"
                        type="text" 
                        className="form-input has-icon"
                        placeholder="e.g. 9876543210"
                        value={contactNo}
                        onChange={(e) => setContactNo(e.target.value)}
                      />
                    </div>
                  </div>
                </>
              )}

              {user?.role === 'staff' && (
                <>
                  <div className="form-group">
                    <label htmlFor="specializationSelect">Service Specialization</label>
                    <select
                      id="specializationSelect"
                      className="form-input"
                      value={specialization}
                      onChange={(e) => setSpecialization(e.target.value)}
                      required
                    >
                      <option value="Electrical">Electrical Repairs</option>
                      <option value="Plumbing">Plumbing Maintenance</option>
                      <option value="IT/Internet">IT & Wi-Fi Networks</option>
                      <option value="Cleaning">Housekeeping Services</option>
                      <option value="Furniture">Carpentry & Furniture</option>
                      <option value="Laboratory">Laboratory Apparatus</option>
                      <option value="Transport">College Transport</option>
                      <option value="Other">General Maintenance</option>
                    </select>
                  </div>

                  <div className="form-group flex-row-align">
                    <label className="checkbox-label" htmlFor="availabilityToggle">
                      <input 
                        id="availabilityToggle"
                        type="checkbox" 
                        checked={isAvailable}
                        onChange={(e) => setIsAvailable(e.target.checked)}
                      />
                      <span>Available for work assignments</span>
                    </label>
                  </div>
                </>
              )}

              <button type="submit" className="btn btn-primary profile-submit-btn" disabled={loading}>
                {loading ? <Loader size="small" /> : 'Save Changes'}
              </button>
            </form>
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
export default Profile;

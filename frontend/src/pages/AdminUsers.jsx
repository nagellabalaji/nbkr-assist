import React, { useState, useEffect } from 'react';
import { adminService } from '../services/admin';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import { Search, UserCheck, UserX, ShieldAlert, ShieldCheck } from 'lucide-react';
import './AdminUsers.css';

export const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  const loadUsers = async () => {
    try {
      const res = await adminService.getUsersList();
      if (res.success) {
        setUsers(res.data);
      }
    } catch (e) {
      setToast({ show: true, message: 'Failed to load user list.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleToggleStatus = async (userId, currentStatus) => {
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    const actionText = newStatus === 'active' ? 'unfreeze' : 'freeze';
    
    if (!window.confirm(`Are you sure you want to ${actionText} this user's account login access?`)) return;

    try {
      const res = await adminService.updateUserStatus(userId, newStatus);
      if (res.success) {
        setToast({ show: true, message: `Account access ${newStatus}d successfully.`, type: 'success' });
        loadUsers();
      }
    } catch (e) {
      setToast({ show: true, message: 'Failed to modify account state.', type: 'error' });
    }
  };

  const filteredUsers = users.filter((u) => {
    const matchesSearch = 
      u.username.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      (u.profile?.roll_no && u.profile.roll_no.toLowerCase().includes(search.toLowerCase())) ||
      (u.profile?.department && u.profile.department.toLowerCase().includes(search.toLowerCase()));

    const matchesRole = roleFilter ? u.role === roleFilter : true;

    return matchesSearch && matchesRole;
  });

  if (loading) {
    return <Loader message="Accessing student and staff registry..." />;
  }

  return (
    <div className="admin-users-container animate-fade-in">
      <div className="users-header-section">
        <h1>User Directory Management</h1>
        <p>Monitor user registration logs, review specialization routing fields, and freeze/unfreeze account login tokens.</p>
      </div>

      <div className="users-controls-card glass-card">
        {/* Search */}
        <div className="search-bar-wrapper">
          <Search size={18} className="search-icon" />
          <input 
            type="text" 
            placeholder="Search by name, email, roll number, or department..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="form-input search-input"
          />
        </div>

        {/* Filter Role */}
        <select 
          value={roleFilter} 
          onChange={(e) => setRoleFilter(e.target.value)}
          className="form-input role-filter-dropdown"
        >
          <option value="">All Roles</option>
          <option value="student">Students</option>
          <option value="staff">Estates Staff</option>
        </select>
      </div>

      <div className="users-grid-list">
        {filteredUsers.length === 0 ? (
          <div className="empty-users glass-card">No user accounts found matching your search.</div>
        ) : (
          <div className="users-grid">
            {filteredUsers.map((u) => (
              <div key={u.id} className="user-profile-card glass-card">
                <div className="card-top">
                  <div className="avatar-small">{u.username[0].toUpperCase()}</div>
                  <div className="role-status-row">
                    <span className="role-tag">{u.role.toUpperCase()}</span>
                    <span className={`status-dot ${u.status}`}></span>
                  </div>
                </div>

                <div className="card-body-details">
                  <h4>{u.username}</h4>
                  <p className="email-text">{u.email}</p>

                  <div className="profile-attributes">
                    {u.role === 'student' ? (
                      <>
                        <div className="attribute-row">
                          <span className="attr-lbl">Roll No:</span>
                          <span className="attr-val">{u.profile?.roll_no || 'N/A'}</span>
                        </div>
                        <div className="attribute-row">
                          <span className="attr-lbl">Dept:</span>
                          <span className="attr-val">{u.profile?.department || 'N/A'}</span>
                        </div>
                        <div className="attribute-row">
                          <span className="attr-lbl">Hostel/Room:</span>
                          <span className="attr-val">
                            {u.profile?.hostel_no ? `${u.profile.hostel_no} - R.${u.profile.room_no || '?'}` : 'Day Scholar'}
                          </span>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="attribute-row">
                          <span className="attr-lbl">Dept:</span>
                          <span className="attr-val">{u.profile?.department || 'N/A'}</span>
                        </div>
                        <div className="attribute-row">
                          <span className="attr-lbl">Speciality:</span>
                          <span className="attr-val">{u.profile?.specialization || 'N/A'}</span>
                        </div>
                        <div className="attribute-row">
                          <span className="attr-lbl">Availability:</span>
                          <span className="attr-val">
                            {u.profile?.is_available ? (
                              <strong style={{ color: 'var(--color-resolved)' }}>Available</strong>
                            ) : (
                              <strong style={{ color: 'var(--color-review)' }}>Busy</strong>
                            )}
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                <div className="card-action-footer">
                  <span className="status-label">Account Access: <strong>{u.status.toUpperCase()}</strong></span>
                  <button 
                    onClick={() => handleToggleStatus(u.id, u.status)}
                    className={`btn btn-sm ${u.status === 'active' ? 'btn-danger' : 'btn-accent'}`}
                    title={u.status === 'active' ? 'Freeze Access' : 'Unfreeze Access'}
                  >
                    {u.status === 'active' ? (
                      <>
                        <UserX size={14} />
                        <span>Freeze</span>
                      </>
                    ) : (
                      <>
                        <UserCheck size={14} />
                        <span>Unfreeze</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))}
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
export default AdminUsers;

import React, { useEffect, useState } from 'react';
import { Search, PlusCircle, Briefcase, FileText, CheckCircle, Clock, Trash2, Edit2, AlertCircle } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './PlacementOfficerDashboard.css';

export const PlacementOfficerDashboard = () => {
  const [drives, setDrives] = useState([]);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // View state: 'applications' or 'drives'
  const [viewMode, setViewMode] = useState('applications');

  // Search states
  const [searchApps, setSearchApps] = useState('');
  const [searchDrives, setSearchDrives] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Drive Modal state
  const [showDriveModal, setShowDriveModal] = useState(false);
  const [editingDriveId, setEditingDriveId] = useState(null);
  const [companyName, setCompanyName] = useState('');
  const [jobRole, setJobRole] = useState('');
  const [salaryPackage, setSalaryPackage] = useState('');
  const [criteria, setCriteria] = useState('');
  const [driveDate, setDriveDate] = useState('');

  // Application update state
  const [editingAppId, setEditingAppId] = useState(null);
  const [editStatus, setEditStatus] = useState('');
  const [savingApp, setSavingApp] = useState(false);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');

      // Fetch Drives
      const drivesRes = await fetch('/api/placements/drives', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const drivesJson = await drivesRes.json();
      if (drivesJson.success) {
        setDrives(drivesJson.data);
      }

      // Fetch Applications
      const appsRes = await fetch('/api/placements/applications', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const appsJson = await appsRes.json();
      if (appsJson.success) {
        setApplications(appsJson.data);
      }
    } catch (err) {
      setToast({ show: true, message: 'Failed to access recruitment databases.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenDriveModal = (drive = null) => {
    if (drive) {
      setEditingDriveId(drive.id);
      setCompanyName(drive.company_name);
      setJobRole(drive.job_role);
      setSalaryPackage(drive.salary_package || '');
      setCriteria(drive.eligibility_criteria || '');
      setDriveDate(drive.drive_date ? drive.drive_date.split('T')[0] : '');
    } else {
      setEditingDriveId(null);
      setCompanyName('');
      setJobRole('');
      setSalaryPackage('');
      setCriteria('');
      setDriveDate('');
    }
    setShowDriveModal(true);
  };

  const handleDriveSubmit = async (e) => {
    e.preventDefault();
    if (!companyName || !jobRole || !driveDate) {
      setToast({ show: true, message: 'Please input all required drive fields.', type: 'error' });
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const payload = {
        company_name: companyName,
        job_role: jobRole,
        salary_package: salaryPackage,
        eligibility_criteria: criteria,
        drive_date: driveDate
      };

      const method = editingDriveId ? 'PUT' : 'POST';
      const endpoint = editingDriveId ? `/api/placements/drives/${editingDriveId}` : '/api/placements/drives';

      const res = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: editingDriveId ? 'Drive parameters updated successfully!' : 'Placement drive published successfully!', type: 'success' });
        setShowDriveModal(false);
        fetchData();
      } else {
        setToast({ show: true, message: json.message || 'Operation failed.', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server communication error.', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteDrive = async (driveId) => {
    if (!window.confirm("Are you sure you want to permanently cancel this placement drive circular?")) return;

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/placements/drives/${driveId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: 'Drive deleted from registry.', type: 'success' });
        fetchData();
      } else {
        setToast({ show: true, message: json.message || 'Deletion failed.', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server error.', type: 'error' });
    }
  };

  const handleOpenEditApp = (app) => {
    setEditingAppId(app.id);
    setEditStatus(app.status);
  };

  const handleSaveAppUpdate = async (e) => {
    e.preventDefault();
    setSavingApp(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/placements/applications/${editingAppId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: editStatus })
      });
      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: 'Applicant status updated successfully!', type: 'success' });
        setEditingAppId(null);
        fetchData();
      } else {
        setToast({ show: true, message: json.message || 'Update failed.', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server communication error.', type: 'error' });
    } finally {
      setSavingApp(false);
    }
  };

  // Metrics
  const getSelectedCount = () => applications.filter(a => a.status === 'selected').length;
  const getActiveDrivesCount = () => drives.filter(d => d.status !== 'Completed').length;

  const filteredApplications = applications.filter(a => {
    const matchSearch = a.student_name.toLowerCase().includes(searchApps.toLowerCase()) ||
                        a.roll_no.toLowerCase().includes(searchApps.toLowerCase()) ||
                        a.company_name.toLowerCase().includes(searchApps.toLowerCase());
    const matchStatus = statusFilter === 'all' || a.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const filteredDrives = drives.filter(d => {
    return d.company_name.toLowerCase().includes(searchDrives.toLowerCase()) ||
           d.job_role.toLowerCase().includes(searchDrives.toLowerCase());
  });

  const getStatusBadgeClass = (status) => {
    switch (status?.toLowerCase()) {
      case 'selected': return 'status-selected';
      case 'shortlisted': return 'status-shortlisted';
      case 'rejected': return 'status-rejected';
      default: return 'status-applied';
    }
  };

  if (loading) return <Loader message="Accessing placement console..." />;

  return (
    <div className="placement-officer-container animate-fade-in">
      <div className="dashboard-header">
        <div>
          <h1>Placement Workspace</h1>
          <p>Organize recruitment campaigns, shortlist candidates, and audit selections.</p>
        </div>

        <div className="header-actions">
          <button 
            className={`btn btn-outline ${viewMode === 'applications' ? 'active' : ''}`}
            onClick={() => setViewMode('applications')}
          >
            Review Candidates
          </button>
          <button 
            className={`btn btn-outline ${viewMode === 'drives' ? 'active' : ''}`}
            onClick={() => setViewMode('drives')}
          >
            Review Drives
          </button>
          {viewMode === 'drives' && (
            <button className="btn btn-primary publish-drive-btn" onClick={() => handleOpenDriveModal()}>
              <PlusCircle size={18} />
              <span>Publish Drive</span>
            </button>
          )}
        </div>
      </div>

      {/* Metrics board */}
      <div className="admin-metrics-row">
        <div className="metric-card glass-card">
          <Briefcase className="m-icon" />
          <div className="m-val">{drives.length}</div>
          <div className="m-lbl">Total Job Drives</div>
        </div>
        <div className="metric-card glass-card warning">
          <Clock className="m-icon" />
          <div className="m-val">{getActiveDrivesCount()}</div>
          <div className="m-lbl">Active Campaigns</div>
        </div>
        <div className="metric-card glass-card success">
          <CheckCircle className="m-icon" />
          <div className="m-val">{getSelectedCount()}</div>
          <div className="m-lbl">Placed Candidates</div>
        </div>
      </div>

      {viewMode === 'applications' ? (
        /* Candidates List */
        <div className="applications-workspace">
          <div className="roster-controls-card glass-card">
            <div className="search-box-wrapper">
              <Search size={18} className="search-icon" />
              <input 
                type="text" 
                placeholder="Search candidates by student name, roll number, or company..." 
                value={searchApps}
                onChange={(e) => setSearchApps(e.target.value)}
                className="search-input"
              />
            </div>

            <div className="filter-item">
              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="status-select-filter">
                <option value="all">All Application Statuses</option>
                <option value="applied">Applied</option>
                <option value="shortlisted">Shortlisted</option>
                <option value="selected">Selected</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </div>

          <div className="table-responsive glass-card">
            {filteredApplications.length === 0 ? (
              <div className="empty-roster">No candidates applications found mapping your search filters.</div>
            ) : (
              <table className="roster-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Candidate Details</th>
                    <th>Job Targets</th>
                    <th>Status</th>
                    <th>Applied Date</th>
                    <th className="center-text">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredApplications.map(a => (
                    <tr key={a.id}>
                      <td className="monospace-cell">APP-{String(a.id).padStart(4, '0')}</td>
                      <td>
                        <div className="candidate-meta">
                          <strong>{a.student_name}</strong>
                          <span>Roll: {a.roll_no} | Dept: {a.department}</span>
                        </div>
                      </td>
                      <td>
                        <div className="job-meta">
                          <strong>{a.company_name}</strong>
                          <span>{a.job_role}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`status-pill ${getStatusBadgeClass(a.status)}`}>
                          {a.status}
                        </span>
                      </td>
                      <td>{new Date(a.applied_at).toLocaleDateString()}</td>
                      <td className="actions-cell">
                        <button className="btn btn-outline edit-action-btn" onClick={() => handleOpenEditApp(a)}>
                          Shortlist
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      ) : (
        /* Drives List */
        <div className="drives-workspace">
          <div className="roster-controls-card glass-card">
            <div className="search-box-wrapper">
              <Search size={18} className="search-icon" />
              <input 
                type="text" 
                placeholder="Search drives by company or job role..." 
                value={searchDrives}
                onChange={(e) => setSearchDrives(e.target.value)}
                className="search-input"
              />
            </div>
          </div>

          <div className="table-responsive glass-card">
            {filteredDrives.length === 0 ? (
              <div className="empty-roster">No recruitment drives found mapping your search.</div>
            ) : (
              <table className="roster-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Company Name</th>
                    <th>Job Role</th>
                    <th>Salary Package</th>
                    <th>Target Date</th>
                    <th>Campaign Status</th>
                    <th className="center-text">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredDrives.map(d => (
                    <tr key={d.id}>
                      <td className="monospace-cell">DRV-{String(d.id).padStart(4, '0')}</td>
                      <td><strong>{d.company_name}</strong></td>
                      <td>{d.job_role}</td>
                      <td>{d.salary_package || 'Package N/A'}</td>
                      <td>{new Date(d.drive_date).toLocaleDateString()}</td>
                      <td>
                        <span className={`drive-status-badge ${d.status.toLowerCase()}`}>
                          {d.status}
                        </span>
                      </td>
                      <td className="actions-cell-icons">
                        <button className="icon-btn edit-btn" onClick={() => handleOpenDriveModal(d)}>
                          <Edit2 size={16} />
                        </button>
                        <button className="icon-btn delete-btn" onClick={() => handleDeleteDrive(d.id)}>
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* Drive Form Modal */}
      {showDriveModal && (
        <div className="modal-backdrop">
          <div className="modal-content glass-card animate-zoom-in">
            <h3>{editingDriveId ? 'Edit Recruitment Drive' : 'Publish Recruitment Drive'}</h3>
            <hr />
            <form onSubmit={handleDriveSubmit} className="drive-form">
              <div className="form-group">
                <label>Company Name</label>
                <input 
                  type="text" 
                  value={companyName} 
                  onChange={(e) => setCompanyName(e.target.value)} 
                  placeholder="e.g. Google India" 
                  required
                />
              </div>

              <div className="form-group">
                <label>Job Role</label>
                <input 
                  type="text" 
                  value={jobRole} 
                  onChange={(e) => setJobRole(e.target.value)} 
                  placeholder="e.g. Software Development Engineer" 
                  required
                />
              </div>

              <div className="form-row-grid">
                <div className="form-group">
                  <label>Salary Package</label>
                  <input 
                    type="text" 
                    value={salaryPackage} 
                    onChange={(e) => setSalaryPackage(e.target.value)} 
                    placeholder="e.g. 12 LPA" 
                  />
                </div>

                <div className="form-group">
                  <label>Scheduled Drive Date</label>
                  <input 
                    type="date" 
                    value={driveDate} 
                    onChange={(e) => setDriveDate(e.target.value)} 
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Eligibility Criteria</label>
                <textarea 
                  value={criteria} 
                  onChange={(e) => setCriteria(e.target.value)} 
                  placeholder="e.g. B.Tech (CSE/ECE), Minimum 75% Attendance, No active backlogs..."
                  rows={3}
                />
              </div>

              <div className="modal-actions-footer">
                <button type="button" className="btn btn-outline" onClick={() => setShowDriveModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Publishing...' : editingDriveId ? 'Save Changes' : 'Publish Drive'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Candidate Status Modal */}
      {editingAppId && (
        <div className="modal-backdrop">
          <div className="modal-content glass-card animate-zoom-in">
            <h3>Manage Candidate Application APP-{String(editingAppId).padStart(4, '0')}</h3>
            <hr />
            <form onSubmit={handleSaveAppUpdate} className="status-update-form">
              <div className="form-group">
                <label>Update Candidate Status</label>
                <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>
                  <option value="applied">Applied (Under Review)</option>
                  <option value="shortlisted">Shortlisted</option>
                  <option value="selected">Selected (Placed)</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>

              <div className="modal-actions-footer">
                <button type="button" className="btn btn-outline" onClick={() => setEditingAppId(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={savingApp}>
                  {savingApp ? 'Updating...' : 'Save Changes'}
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
export default PlacementOfficerDashboard;

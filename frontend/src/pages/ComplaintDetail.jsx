import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { complaintService } from '../services/complaints';
import { adminService } from '../services/admin';
import { useAuth } from '../context/AuthContext';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import { Modal } from '../components/Common/Modal';
import { 
  ArrowLeft, Calendar, Tag, MapPin, User, Wrench, 
  History, Star, CheckCircle, MessageSquare, AlertTriangle, Clock,
  Phone, ShieldAlert
} from 'lucide-react';
import './ComplaintDetail.css';

export const ComplaintDetail = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [complaint, setComplaint] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // Admin / HOD Assignment state
  const [facultyList, setFacultyList] = useState([]);
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [selectedFacultyId, setSelectedFacultyId] = useState('');
  const [selectedBranch, setSelectedBranch] = useState('');
  const [validationError, setValidationError] = useState('');
  const [assigning, setAssigning] = useState(false);
  const [assignmentSuccessData, setAssignmentSuccessData] = useState(null);

  // Student Feedback state
  const [feedbackRating, setFeedbackRating] = useState(5);
  const [feedbackComments, setFeedbackComments] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  // Staff Work Action states
  const [workNotesInput, setWorkNotesInput] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);

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

  const getTimeRemaining = (deadlineIso) => {
    if (!deadlineIso) return 'N/A';
    const deadline = new Date(deadlineIso);
    const now = new Date();
    const diffMs = deadline - now;
    if (diffMs < 0) return 'Overdue';
    
    const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
    const days = Math.floor(diffHrs / 24);
    const hours = diffHrs % 24;
    
    if (days > 0) {
      return `${days} Day${days > 1 ? 's' : ''} ${hours} Hour${hours > 1 ? 's' : ''}`;
    }
    return `${hours} Hour${hours > 1 ? 's' : ''}`;
  };

  const fetchComplaintDetails = async () => {
    try {
      const res = await complaintService.getComplaintById(id);
      if (res.success) {
        setComplaint(res.data);
      }
    } catch (e) {
      setToast({ show: true, message: 'Grievance ticket not found', type: 'error' });
      setTimeout(() => navigate(-1), 1500);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaintDetails();
  }, [id]);

  const loadFacultyList = async () => {
    if (!['super_admin', 'hod'].includes(user?.role)) return;
    try {
      const res = await adminService.getFacultyList();
      if (res.success) {
        setFacultyList(res.data);
      }
    } catch (e) {
      console.error('Failed to retrieve faculty list:', e);
    }
  };

  useEffect(() => {
    if (['super_admin', 'hod'].includes(user?.role)) {
      loadFacultyList();
    }
  }, [user]);

  const isBranchMatch = (department, branchCode) => {
    if (!department || !branchCode) return false;
    const dept = department.toLowerCase();
    const br = branchCode.toLowerCase();
    
    if (dept === br) return true;
    if (br === 'cse' && dept.includes('computer science')) return true;
    if (br === 'ece' && dept.includes('electronics') && dept.includes('communication')) return true;
    if (br === 'eee' && dept.includes('electrical') && dept.includes('electronics')) return true;
    if (br === 'me' && dept.includes('mechanical')) return true;
    if ((br === 'civil' || br === 'ce') && dept.includes('civil')) return true;
    if (br === 'it' && dept.includes('information technology')) return true;
    if ((br === 'ai & ds' || br === 'ai' || br === 'ds') && (dept.includes('artificial intelligence') || dept.includes('data science'))) return true;
    
    return dept.includes(br);
  };

  useEffect(() => {
    if (selectedFacultyId && selectedBranch) {
      const fac = facultyList.find(f => f.id.toString() === selectedFacultyId);
      if (fac && !isBranchMatch(fac.department, selectedBranch)) {
        setValidationError('Selected faculty does not belong to this branch.');
      } else {
        setValidationError('');
      }
    } else {
      setValidationError('');
    }
  }, [selectedFacultyId, selectedBranch, facultyList]);

  useEffect(() => {
    if (selectedBranch && selectedFacultyId) {
      const fac = facultyList.find(f => f.id.toString() === selectedFacultyId);
      if (fac && !isBranchMatch(fac.department, selectedBranch)) {
        setSelectedFacultyId('');
      }
    }
  }, [selectedBranch, facultyList]);

  const openAssignModal = () => {
    setSelectedFacultyId('');
    setSelectedBranch('');
    setValidationError('');
    setAssignmentSuccessData(null);
    setIsAssignModalOpen(true);
  };

  const handleCloseSuccessModal = () => {
    setIsAssignModalOpen(false);
    setAssignmentSuccessData(null);
    fetchComplaintDetails();
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

    const selectedFaculty = facultyList.find(f => f.id.toString() === selectedFacultyId);
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
      const res = await complaintService.assignComplaint(id, selectedFacultyId, selectedBranch);
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

  const handleStatusTransition = async (newStatus, comments) => {
    setUpdatingStatus(true);
    try {
      const res = await complaintService.updateStatus(id, newStatus, comments);
      if (res.success) {
        setToast({ show: true, message: `Status updated to ${newStatus}`, type: 'success' });
        setWorkNotesInput('');
        fetchComplaintDetails();
      }
    } catch (e) {
      setToast({ show: true, message: 'Failed to change status', type: 'error' });
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleFeedbackSubmit = async (e) => {
    e.preventDefault();
    setSubmittingFeedback(true);
    try {
      const res = await complaintService.submitFeedback(id, feedbackRating, feedbackComments);
      if (res.success) {
        setToast({ show: true, message: 'Feedback submitted. Ticket closed.', type: 'success' });
        setFeedbackComments('');
        fetchComplaintDetails();
      }
    } catch (e) {
      setToast({ show: true, message: 'Failed to submit feedback', type: 'error' });
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const getStatusStepClass = (stepName) => {
    const steps = ['Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Closed'];
    const currentStepIndex = steps.indexOf(complaint.status);
    const targetStepIndex = steps.indexOf(stepName);

    if (complaint.status === 'Rejected') {
      return stepName === 'Submitted' ? 'completed' : (stepName === 'Under Review' ? 'rejected' : 'disabled');
    }

    if (complaint.status === 'Reopened') {
      return ['Submitted', 'Under Review', 'Assigned', 'In Progress', 'Reopened'].includes(stepName) ? 'completed reopened' : 'disabled';
    }

    if (targetStepIndex === -1) return 'disabled';
    if (targetStepIndex < currentStepIndex) return 'completed';
    if (targetStepIndex === currentStepIndex) return 'active';
    return 'disabled';
  };

  const getProgressPercentage = () => {
    const steps = ['Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Closed'];
    const index = steps.indexOf(complaint.status);
    if (index === -1) return 0;
    return (index / (steps.length - 1)) * 100;
  };

  if (loading) {
    return <Loader message="Opening grievance logs..." />;
  }

  if (!complaint) return null;

  // Render fully secure authenticated URL for serving uploads
  const token = localStorage.getItem('token');
  const backendImageUrl = complaint.image_path 
    ? `http://localhost:5000/api/complaints/uploads/${complaint.image_path.replace('uploads/', '')}?token=${token}`
    : null;

  const isStaff = ['hod', 'faculty', 'maintenance_staff', 'librarian', 'exam_cell', 'placement_officer', 'hostel_admin', 'transport_admin'].includes(user?.role);
  const isAssignedStaff = isStaff && complaint.assigned_staff_id === user.profile?.id;
  const canAssign = ['super_admin', 'hod'].includes(user?.role);
  const canResolveOrUpdate = canAssign || isAssignedStaff;

  return (
    <div className="detail-page-container animate-fade-in">
      {/* Back button */}
      <button onClick={() => navigate(-1)} className="btn btn-secondary back-btn">
        <ArrowLeft size={16} />
        <span>Go Back</span>
      </button>

      {/* Ticket Identity Banner */}
      <div className="ticket-banner glass-card">
        <div className="banner-left">
          <span className="banner-id">{complaint.id}</span>
          <h1>{complaint.title}</h1>
          <div className="banner-meta">
            <span className={`badge badge-${complaint.status.toLowerCase().replace(' ', '')}`}>{complaint.status}</span>
            <span className={`badge badge-${complaint.ai_priority.toLowerCase()}`}>Priority: {complaint.ai_priority}</span>
            {complaint.sla_status === 'Breached' && (
              <span className="badge badge-rejected sla-breached-badge">
                <AlertTriangle size={12} className="inline-icon" /> SLA Breached
              </span>
            )}
          </div>
        </div>
        
        {/* Assign Modal Button for HOD / Admin */}
        {canAssign && (
          <button 
            onClick={() => setIsAssignModalOpen(true)} 
            className="btn btn-primary"
            disabled={complaint.status === 'Closed' || complaint.status === 'Rejected'}
          >
            <Wrench size={16} />
            <span>{complaint.assigned_staff_id ? 'Reassign Staff' : 'Assign Staff'}</span>
          </button>
        )}

        {/* Staff Quick Actions */}
        {isAssignedStaff && (
          <div className="staff-actions-row">
            {complaint.status === 'Assigned' && (
              <button 
                onClick={() => handleStatusTransition('In Progress', 'Staff accepted job and is starting work.')} 
                className="btn btn-primary"
                disabled={updatingStatus}
              >
                Accept Assignment
              </button>
            )}
          </div>
        )}
      </div>

      {/* Status Progress Timeline */}
      <div className="status-progress-card glass-card">
        <h3>Resolution Timeline</h3>
        
        <div className="progress-timeline-wrapper">
          <div className="progress-line">
            <div className="progress-fill-line" style={{ width: `${getProgressPercentage()}%` }}></div>
          </div>

          <div className="timeline-steps">
            <div className={`step-node ${getStatusStepClass('Submitted')}`}>
              <div className="node-dot">1</div>
              <span className="node-label">Submitted</span>
            </div>
            <div className={`step-node ${getStatusStepClass('Under Review')}`}>
              <div className="node-dot">2</div>
              <span className="node-label">Under Review</span>
            </div>
            <div className={`step-node ${getStatusStepClass('Assigned')}`}>
              <div className="node-dot">3</div>
              <span className="node-label">Assigned</span>
            </div>
            <div className={`step-node ${getStatusStepClass('In Progress')}`}>
              <div className="node-dot">4</div>
              <span className="node-label">In Progress</span>
            </div>
            <div className={`step-node ${getStatusStepClass('Resolved')}`}>
              <div className="node-dot">5</div>
              <span className="node-label">Resolved</span>
            </div>
            <div className={`step-node ${getStatusStepClass('Closed')}`}>
              <div className="node-dot">6</div>
              <span className="node-label">Closed</span>
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Info vs Log History */}
      <div className="details-grid">
        {/* Left Side: Ticket Details and Attachments */}
        <div className="info-column-left">
          <div className="glass-card detail-card">
            <h3>Grievance Details</h3>
            
            <p className="description-text">{complaint.description}</p>

            <div className="metadata-grid">
              <div className="meta-block">
                <Tag size={16} />
                <div>
                  <span className="meta-label">Category / Subcategory</span>
                  <span className="meta-value">{complaint.category_name} ({complaint.subcategory || 'General'})</span>
                </div>
              </div>

              <div className="meta-block">
                <MapPin size={16} />
                <div>
                  <span className="meta-label">Location</span>
                  <span className="meta-value">{complaint.location}</span>
                </div>
              </div>

              <div className="meta-block">
                <Calendar size={16} />
                <div>
                  <span className="meta-label">Lodged Date</span>
                  <span className="meta-value">{new Date(complaint.created_at).toLocaleString()}</span>
                </div>
              </div>

              <div className="meta-block">
                <Clock size={16} />
                <div>
                  <span className="meta-label">SLA Deadline / Status</span>
                  <span className="meta-value">
                    {complaint.sla_deadline ? new Date(complaint.sla_deadline).toLocaleString() : 'N/A'}{' '}
                    ({complaint.sla_status})
                  </span>
                </div>
              </div>

              <div className="meta-block">
                <User size={16} />
                <div>
                  <span className="meta-label">Logged By</span>
                  <span className="meta-value">{complaint.student_name} ({complaint.roll_no})</span>
                </div>
              </div>

              {complaint.assigned_staff_name && (
                <div className="meta-block">
                  <Wrench size={16} />
                  <div>
                    <span className="meta-label">Assigned Faculty</span>
                    <span className="meta-value">{complaint.assigned_staff_name}</span>
                    {complaint.assigned_branch && (
                      <span className="meta-value" style={{ fontSize: '0.8rem', opacity: 0.8, marginTop: '0.1rem' }}>
                        Branch: {complaint.assigned_branch}
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Uploaded Image proof */}
            {backendImageUrl && (
              <div className="image-attachment-container">
                <h4>Attachment Proof</h4>
                <div className="attached-image-wrapper">
                  <img src={backendImageUrl} alt="Attachment Proof" />
                </div>
              </div>
            )}
          </div>

          {/* Faculty Assignment Details Card */}
          {complaint.assigned_staff_name && (
            <div className="glass-card detail-card" style={{ marginTop: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
                <User size={18} style={{ color: 'var(--primary)' }} />
                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Faculty Assignment Details</h3>
              </div>
              <div className="metadata-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                
                <div className="meta-block">
                  <User size={16} />
                  <div>
                    <span className="meta-label">Faculty</span>
                    <span className="meta-value">{complaint.assigned_faculty_name || complaint.assigned_staff_name}</span>
                  </div>
                </div>

                {/* Show phone to Admin, HOD, and Faculty, but NOT student */}
                {user?.role !== 'student' && (
                  <div className="meta-block">
                    <Phone size={16} />
                    <div>
                      <span className="meta-label">Phone</span>
                      <span className="meta-value">{complaint.assigned_faculty_phone || 'Not available'}</span>
                    </div>
                  </div>
                )}

                <div className="meta-block">
                  <Tag size={16} />
                  <div>
                    <span className="meta-label">Branch</span>
                    <span className="meta-value">{complaint.assigned_branch || 'N/A'}</span>
                  </div>
                </div>

                <div className="meta-block">
                  <Calendar size={16} />
                  <div>
                    <span className="meta-label">Assigned On</span>
                    <span className="meta-value">
                      {complaint.assigned_at ? formatDateFull(complaint.assigned_at) : 'N/A'}
                    </span>
                  </div>
                </div>

                <div className="meta-block">
                  <Clock size={16} />
                  <div>
                    <span className="meta-label">Expected Resolution</span>
                    <span className="meta-value">Within 2 Working Days</span>
                  </div>
                </div>

                <div className="meta-block">
                  <Calendar size={16} />
                  <div>
                    <span className="meta-label">Resolution Deadline</span>
                    <span className="meta-value">
                      {complaint.resolution_deadline ? formatDateShort(complaint.resolution_deadline) : 'N/A'}
                    </span>
                  </div>
                </div>

                {/* Display time remaining if Faculty is assigned */}
                {isAssignedStaff && complaint.status !== 'Resolved' && complaint.status !== 'Closed' && (
                  <div className="meta-block">
                    <Clock size={16} style={{ color: complaint.assignment_status === 'OVERDUE' ? 'var(--color-rejected)' : 'var(--color-progress)' }} />
                    <div>
                      <span className="meta-label">Time Remaining</span>
                      <span className="meta-value" style={{ fontWeight: 'bold', color: complaint.assignment_status === 'OVERDUE' ? 'var(--color-rejected)' : 'var(--color-progress)' }}>
                        {getTimeRemaining(complaint.resolution_deadline)}
                      </span>
                    </div>
                  </div>
                )}

                <div className="meta-block">
                  <ShieldAlert size={16} />
                  <div>
                    <span className="meta-label">Status</span>
                    <span 
                      className={`badge badge-${(complaint.assignment_status || 'ASSIGNED').toLowerCase().replace('_', '')}`}
                      style={{ marginTop: '4px' }}
                    >
                      {complaint.assignment_status === 'OVERDUE' ? '🔴 OVERDUE' : (complaint.assignment_status === 'ON_TIME' ? '🟢 ON TIME' : complaint.assignment_status)}
                    </span>
                  </div>
                </div>

              </div>
            </div>
          )}

          {/* System Insights Summary Card */}
          <div className="glass-card detail-card ai-insights-summary">
            <div className="ai-insights-header">
              <Star size={18} className="ai-icon-gold" />
              <h3>System Audit Findings</h3>
            </div>
            <div className="ai-metrics-grid">
              <div className="ai-metric-item">
                <span className="ai-lbl">Confidence Score</span>
                <span className="ai-val">{(complaint.ai_confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="ai-metric-item">
                <span className="ai-lbl">Predicted Department</span>
                <span className="ai-val">{complaint.suggested_department}</span>
              </div>
            </div>
          </div>

          {/* Conditional Input forms depending on Roles */}
          
          {/* 1. Student Actions (Reopen & Feedback) */}
          {user?.role === 'student' && (complaint.status === 'Resolved' || complaint.status === 'Closed') && (
            <div className="glass-card detail-card actions-panel">
              {complaint.status === 'Resolved' && !complaint.has_feedback && (
                <form onSubmit={handleFeedbackSubmit} className="feedback-form">
                  <h3>Submit Resolution Feedback</h3>
                  <p className="subtitle">Rate the resolution quality to close this ticket.</p>
                  
                  <div className="stars-rating-container">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setFeedbackRating(star)}
                        className={`star-btn ${feedbackRating >= star ? 'filled' : ''}`}
                      >
                        <Star size={24} />
                      </button>
                    ))}
                  </div>

                  <div className="form-group">
                    <label htmlFor="feedbackCommentsInput">Comments (Optional)</label>
                    <textarea 
                      id="feedbackCommentsInput"
                      className="form-input"
                      rows={3}
                      placeholder="Was the work done properly? Let us know."
                      value={feedbackComments}
                      onChange={(e) => setFeedbackComments(e.target.value)}
                    />
                  </div>

                  <button type="submit" className="btn btn-primary" disabled={submittingFeedback}>
                    {submittingFeedback ? <Loader size="small" /> : 'Submit Feedback & Close Ticket'}
                  </button>
                </form>
              )}

              {complaint.status === 'Resolved' && (
                <div className="reopen-ticket-section">
                  <div className="divider">OR</div>
                  <h4>Problem not solved?</h4>
                  <p className="subtitle">If the representative marked the ticket as resolved but the issue is not fixed, you can reopen it.</p>
                  <button 
                    onClick={() => handleStatusTransition('Reopened', 'Student reopened the ticket. Issue still persists.')} 
                    className="btn btn-danger"
                    disabled={updatingStatus}
                  >
                    Reopen Grievance Ticket
                  </button>
                </div>
              )}
            </div>
          )}

          {/* 2. HOD / Admin Actions (Resolve / Close) */}
          {['super_admin', 'hod'].includes(user?.role) && (
            <div className="glass-card detail-card actions-panel">
              <h3>Administrative / Desk Control</h3>
              <p className="subtitle">Update the status of this grievance officially.</p>
              
              <div className="form-group">
                <label htmlFor="adminNotesInput">Action Log Notes</label>
                <textarea 
                  id="adminNotesInput"
                  className="form-input"
                  rows={3}
                  placeholder="Enter comments about this status change..."
                  value={workNotesInput}
                  onChange={(e) => setWorkNotesInput(e.target.value)}
                  disabled={updatingStatus}
                />
              </div>

              <div className="admin-action-buttons">
                {complaint.status === 'Submitted' && (
                  <button 
                    onClick={() => handleStatusTransition('Under Review', workNotesInput || 'Ticket reviewed.')} 
                    className="btn btn-secondary"
                    disabled={updatingStatus}
                  >
                    Mark Under Review
                  </button>
                )}
                {complaint.status !== 'Resolved' && complaint.status !== 'Closed' && complaint.status !== 'Rejected' && (
                  <button 
                    onClick={() => handleStatusTransition('Resolved', workNotesInput || 'Estates admin resolved the issue.')} 
                    className="btn btn-accent"
                    disabled={updatingStatus}
                  >
                    Resolve Grievance
                  </button>
                )}
              </div>
            </div>
          )}

          {/* 3. Staff Actions (Notes & Resolve) */}
          {user?.role !== 'student' && isAssignedStaff && (
            <div className="glass-card detail-card actions-panel">
              <h3>Maintenance / Faculty Update</h3>
              
              <div className="form-group">
                <label htmlFor="notesInput">Work Progress Notes / Resolution Proof details</label>
                <textarea 
                  id="notesInput"
                  className="form-input"
                  rows={4}
                  placeholder="Describe details of the repair. E.g. Cleared leakage blockage in sink and replaced old pipes."
                  value={workNotesInput}
                  onChange={(e) => setWorkNotesInput(e.target.value)}
                  disabled={updatingStatus}
                />
              </div>

              <div className="staff-action-buttons">
                <button 
                  onClick={() => handleStatusTransition(complaint.status, workNotesInput)} 
                  className="btn btn-secondary"
                  disabled={!workNotesInput.trim() || updatingStatus}
                >
                  Add Work Log Note
                </button>

                {complaint.status === 'In Progress' && (
                  <button 
                    onClick={() => handleStatusTransition('Resolved', workNotesInput || 'Estates engineer resolved the issue.')} 
                    className="btn btn-accent"
                    disabled={updatingStatus}
                  >
                    Mark as Resolved
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Side: Timeline History Audit Logs */}
        <div className="info-column-right">
          <div className="glass-card detail-card history-log-card">
            <div className="history-header">
              <History size={18} />
              <h3>Grievance Activity Log</h3>
            </div>

            <div className="history-timeline">
              {complaint.history && complaint.history.length === 0 ? (
                <p className="empty-history">No logged activity</p>
              ) : (
                complaint.history.map((log) => (
                  <div key={log.id} className="history-item">
                    <div className="history-dot"></div>
                    <div className="history-item-content">
                      <div className="history-item-top">
                        <span className="history-action">{log.action}</span>
                        <span className="history-date">
                          {new Date(log.created_at).toLocaleString()}
                        </span>
                      </div>
                      
                      <div className="history-actor">
                        By: <strong>{log.username}</strong> ({log.role.toUpperCase()})
                      </div>

                      {log.comments && (
                        <p className="history-comments">{log.comments}</p>
                      )}

                      {(log.previous_value || log.new_value) && (
                        <div className="history-values">
                          {log.previous_value && (
                            <span className="history-val-old">From: {log.previous_value}</span>
                          )}
                          {log.new_value && (
                            <span className="history-val-new">To: {log.new_value}</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

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
                    {facultyList
                      .filter(fac => isBranchMatch(fac.department, selectedBranch))
                      .map((fac) => (
                        <option key={fac.id} value={fac.id} style={{ color: 'var(--text-primary)', backgroundColor: 'var(--bg-card)' }}>
                          {fac.username} — {fac.department}
                        </option>
                      ))}
                    {facultyList.filter(fac => isBranchMatch(fac.department, selectedBranch)).length === 0 && (
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
export default ComplaintDetail;

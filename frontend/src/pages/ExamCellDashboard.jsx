import React, { useEffect, useState } from 'react';
import { PlusCircle, Search, Calendar, Edit2, Trash2, ShieldAlert, Award, FileText, CheckCircle } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './ExamCellDashboard.css';

export const ExamCellDashboard = () => {
  const [exams, setExams] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // Filter and Search states
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('all');

  // Modal / Form state
  const [showModal, setShowModal] = useState(false);
  const [editingExamId, setEditingExamId] = useState(null);
  
  // Form fields
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [duration, setDuration] = useState(180);
  const [location, setLocation] = useState('');
  const [departmentId, setDepartmentId] = useState('all'); // 'all' or id

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch departments list
      const deptRes = await fetch('/api/departments');
      const deptJson = await deptRes.json();
      if (deptJson.success) {
        setDepartments(deptJson.data);
      }

      // Fetch exams list
      const examRes = await fetch('/api/exams', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const examJson = await examRes.json();
      if (examJson.success) {
        setExams(examJson.data);
      }
    } catch (err) {
      setToast({ show: true, message: 'Failed to access dashboards', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenPublish = (exam = null) => {
    if (exam) {
      // Editing Mode
      setEditingExamId(exam.id);
      setTitle(exam.title || '');
      setSubject(exam.subject || '');
      
      // Split ISO date to Date & Time inputs
      const d = new Date(exam.exam_date);
      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const hours = String(d.getHours()).padStart(2, '0');
      const minutes = String(d.getMinutes()).padStart(2, '0');
      
      setDate(`${year}-${month}-${day}`);
      setTime(`${hours}:${minutes}`);
      setDuration(exam.duration_mins || 180);
      setLocation(exam.location || '');
      setDepartmentId(exam.department_id ? String(exam.department_id) : 'all');
    } else {
      // Creation Mode
      setEditingExamId(null);
      setTitle('');
      setSubject('');
      setDate('');
      setTime('');
      setDuration(180);
      setLocation('');
      setDepartmentId('all');
    }
    setShowModal(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!title || !subject || !date || !time || !location) {
      setToast({ show: true, message: 'Please fill in all required scheduling inputs.', type: 'error' });
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const examDateTime = `${date}T${time}:00`;
      
      const payload = {
        title,
        subject,
        exam_date: examDateTime,
        duration_mins: parseInt(duration),
        location,
        department_id: departmentId === 'all' ? null : parseInt(departmentId)
      };

      const method = editingExamId ? 'PUT' : 'POST';
      const endpoint = editingExamId ? `/api/exams/${editingExamId}` : '/api/exams';

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
        setToast({ 
          show: true, 
          message: editingExamId ? 'Exam details updated successfully!' : 'New exam notification published successfully!', 
          type: 'success' 
        });
        setShowModal(false);
        fetchData();
      } else {
        setToast({ show: true, message: json.message || 'Saving failed', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server communication error', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (examId) => {
    if (!window.confirm("Are you sure you want to permanently cancel and delete this examination record?")) return;

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/exams/${examId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: 'Exam notification removed successfully.', type: 'success' });
        fetchData();
      } else {
        setToast({ show: true, message: json.message || 'Deletion failed', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server connection error', type: 'error' });
    }
  };

  // Metrics calculators
  const getTotalExams = () => exams.length;
  const getDeptCount = (code) => exams.filter(e => e.department_code === code).length;
  const getExamsThisWeek = () => {
    const now = new Date();
    const oneWeekLater = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
    return exams.filter(e => {
      const d = new Date(e.exam_date);
      return d >= now && d <= oneWeekLater;
    }).length;
  };

  const getExamStatus = (examDateStr, durationMins) => {
    const now = new Date();
    const examDate = new Date(examDateStr);
    const endDate = new Date(examDate.getTime() + durationMins * 60 * 1000);

    if (now >= examDate && now <= endDate) return 'Today';
    if (now > endDate) return 'Completed';
    return 'Upcoming';
  };

  const filteredExams = exams.filter(e => {
    const matchSearch = e.subject.toLowerCase().includes(search.toLowerCase()) || 
                        e.title.toLowerCase().includes(search.toLowerCase());
    const matchDept = deptFilter === 'all' || 
                      (deptFilter === 'general' && !e.department_id) || 
                      String(e.department_id) === deptFilter;
    return matchSearch && matchDept;
  });

  if (loading) return <Loader message="Accessing Exam Cell registers..." />;

  return (
    <div className="examcell-dashboard-container animate-fade-in">
      <div className="dashboard-header">
        <div>
          <h1>Exam Cell Command Portal</h1>
          <p>Schedule tests, publish circular notifications, and edit campus-wide examination halls registers.</p>
        </div>
        <button className="btn btn-primary publish-btn" onClick={() => handleOpenPublish()}>
          <PlusCircle size={18} />
          <span>Publish Exam notification</span>
        </button>
      </div>

      {/* Metrics Board */}
      <div className="metrics-grid">
        <div className="metric-card glass-card">
          <Award className="m-icon" />
          <div className="m-val">{getTotalExams()}</div>
          <div className="m-lbl">Total Exams Scheduled</div>
        </div>
        <div className="metric-card glass-card">
          <FileText className="m-icon" />
          <div className="m-val">{getDeptCount('CSE')}</div>
          <div className="m-lbl">CSE Department Exams</div>
        </div>
        <div className="metric-card glass-card">
          <FileText className="m-icon" />
          <div className="m-val">{getDeptCount('ECE')}</div>
          <div className="m-lbl">ECE Department Exams</div>
        </div>
        <div className="metric-card glass-card">
          <FileText className="m-icon" />
          <div className="m-val">{getDeptCount('IT')}</div>
          <div className="m-lbl">IT Department Exams</div>
        </div>
        <div className="metric-card glass-card">
          <FileText className="m-icon" />
          <div className="m-val">{getDeptCount('EEE')}</div>
          <div className="m-lbl">EEE Department Exams</div>
        </div>
        <div className="metric-card glass-card warning-metric">
          <Calendar className="m-icon" />
          <div className="m-val">{getExamsThisWeek()}</div>
          <div className="m-lbl">Exams This Week</div>
        </div>
      </div>

      {/* Roster Controls Board */}
      <div className="roster-workspace-header glass-card">
        <div className="search-box-wrapper">
          <Search size={18} className="search-icon" />
          <input 
            type="text" 
            placeholder="Search exams by subject or title..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-item">
          <select value={deptFilter} onChange={(e) => setDeptFilter(e.target.value)} className="dept-select-filter">
            <option value="all">All Departments Scope</option>
            <option value="general">General (All Depts)</option>
            {departments.map(d => (
              <option key={d.id} value={d.id}>{d.code} Department</option>
            ))}
          </select>
        </div>
      </div>

      {/* Roster list table */}
      <div className="table-responsive glass-card">
        {filteredExams.length === 0 ? (
          <div className="empty-roster">No exam schedules matched your filter options.</div>
        ) : (
          <table className="roster-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Exam Title & Subject</th>
                <th>Date & Time</th>
                <th>Duration</th>
                <th>Department</th>
                <th>Location</th>
                <th>Status</th>
                <th className="center-text">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredExams.map((exam) => {
                const status = getExamStatus(exam.exam_date, exam.duration_mins);
                const d = new Date(exam.exam_date);
                const dateStr = d.toLocaleDateString();
                const timeStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                return (
                  <tr key={exam.id}>
                    <td className="monospace-cell">EX-{String(exam.id).padStart(4, '0')}</td>
                    <td>
                      <div className="subject-title-cell">
                        <strong>{exam.title}</strong>
                        <span>{exam.subject}</span>
                      </div>
                    </td>
                    <td>{dateStr} - {timeStr}</td>
                    <td>{exam.duration_mins} mins</td>
                    <td><span className="badge-dept">{exam.department_code}</span></td>
                    <td>{exam.location}</td>
                    <td>
                      <span className={`status-pill ${status.toLowerCase()}`}>
                        {status}
                      </span>
                    </td>
                    <td className="actions-cell">
                      <button className="icon-btn edit-btn" onClick={() => handleOpenPublish(exam)}>
                        <Edit2 size={16} />
                      </button>
                      <button className="icon-btn delete-btn" onClick={() => handleDelete(exam.id)}>
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Publish Form Modal */}
      {showModal && (
        <div className="modal-backdrop">
          <div className="modal-content glass-card animate-zoom-in">
            <h3>{editingExamId ? 'Update Exam Notification' : 'Publish Exam Notification'}</h3>
            <hr />
            <form onSubmit={handleFormSubmit} className="publish-form">
              <div className="form-group">
                <label>Title</label>
                <input 
                  type="text" 
                  value={title} 
                  onChange={(e) => setTitle(e.target.value)} 
                  placeholder="e.g. Midterm-I Theory Schedule" 
                  required
                />
              </div>

              <div className="form-group">
                <label>Subject</label>
                <input 
                  type="text" 
                  value={subject} 
                  onChange={(e) => setSubject(e.target.value)} 
                  placeholder="e.g. Machine Learning" 
                  required
                />
              </div>

              <div className="form-row-grid">
                <div className="form-group">
                  <label>Date</label>
                  <input 
                    type="date" 
                    value={date} 
                    onChange={(e) => setDate(e.target.value)} 
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Time</label>
                  <input 
                    type="time" 
                    value={time} 
                    onChange={(e) => setTime(e.target.value)} 
                    required
                  />
                </div>
              </div>

              <div className="form-row-grid">
                <div className="form-group">
                  <label>Duration (Minutes)</label>
                  <input 
                    type="number" 
                    value={duration} 
                    onChange={(e) => setDuration(e.target.value)} 
                    min="1" 
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Location / Hall</label>
                  <input 
                    type="text" 
                    value={location} 
                    onChange={(e) => setLocation(e.target.value)} 
                    placeholder="e.g. LHC-101" 
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Target Department Scope</label>
                <select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
                  <option value="all">All Departments Scope</option>
                  {departments.map(d => (
                    <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
                  ))}
                </select>
              </div>

              <div className="modal-actions-footer">
                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Processing...' : editingExamId ? 'Update Exam' : 'Publish Exam'}
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
export default ExamCellDashboard;

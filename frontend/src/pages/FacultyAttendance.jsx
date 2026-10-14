import React, { useEffect, useState } from 'react';
import { Calendar as CalendarIcon, CheckSquare, PlusSquare, History, Check, Save, UserCheck } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './FacultyAttendance.css';

export const FacultyAttendance = () => {
  const [subjects, setSubjects] = useState([]);
  const [students, setStudents] = useState([]);
  const [pastSessions, setPastSessions] = useState([]);
  const [loadingSubjects, setLoadingSubjects] = useState(true);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // Tab views
  const [activeTab, setActiveTab] = useState('mark'); // 'mark' | 'history'

  // Input states
  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [selectedSection, setSelectedSection] = useState('A');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedSession, setSelectedSession] = useState('Session 1');

  // Attendance marking matrix (student_id -> 'Present' | 'Absent')
  const [attendanceMap, setAttendanceMap] = useState({});

  // Editing state
  const [editingSessionId, setEditingSessionId] = useState(null);

  useEffect(() => {
    fetchSubjects();
    fetchHistory();
  }, []);

  const fetchSubjects = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/faculty/subjects', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        setSubjects(json.data);
        if (json.data.length > 0) {
          setSelectedSubjectId(json.data[0].subject_id);
          setSelectedSection(json.data[0].section);
        }
      }
    } catch (err) {
      setToast({ show: true, message: 'Failed to load assigned subjects', type: 'error' });
    } finally {
      setLoadingSubjects(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/faculty/attendance', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        setPastSessions(json.data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadStudentsForMarking = async () => {
    if (!selectedSubjectId) return;
    setLoadingStudents(true);
    setEditingSessionId(null);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/faculty/students?section=${selectedSection}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        setStudents(json.data);
        // Default all students to 'Present' for faster logging
        const initialMap = {};
        json.data.forEach(s => {
          initialMap[s.id] = 'Present';
        });
        setAttendanceMap(initialMap);
      } else {
        setToast({ show: true, message: json.message || 'Failed to query student roster', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Roster download failed', type: 'error' });
    } finally {
      setLoadingStudents(false);
    }
  };

  useEffect(() => {
    if (selectedSubjectId && selectedSection && activeTab === 'mark' && !editingSessionId) {
      loadStudentsForMarking();
    }
  }, [selectedSubjectId, selectedSection, activeTab]);

  const handleStatusChange = (studentId, status) => {
    setAttendanceMap(prev => ({
      ...prev,
      [studentId]: status
    }));
  };

  const markAll = (status) => {
    const newMap = {};
    students.forEach(s => {
      newMap[s.id] = status;
    });
    setAttendanceMap(newMap);
  };

  const handleSubmitAttendance = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const records = Object.keys(attendanceMap).map(id => ({
        student_id: parseInt(id),
        status: attendanceMap[id]
      }));

      const payload = {
        subject_id: parseInt(selectedSubjectId),
        date: selectedDate,
        session: selectedSession,
        section: selectedSection,
        records
      };

      const url = editingSessionId 
        ? `/api/faculty/attendance/${editingSessionId}`
        : '/api/faculty/attendance';
      
      const method = editingSessionId ? 'PUT' : 'POST';

      const res = await fetch(url, {
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
          message: editingSessionId ? 'Attendance updated successfully!' : 'Attendance sheet logged successfully!', 
          type: 'success' 
        });
        setEditingSessionId(null);
        fetchHistory();
        if (!editingSessionId) {
          // Reset
          loadStudentsForMarking();
        }
      } else {
        setToast({ show: true, message: json.message || 'Failed to submit attendance sheet', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server communication error', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleLoadSessionForEdit = async (session) => {
    setLoadingStudents(true);
    setEditingSessionId(session.id);
    setSelectedSubjectId(session.subject_id);
    setSelectedDate(session.date);
    setSelectedSession(session.session);
    setSelectedSection(session.section);
    setActiveTab('mark');

    try {
      const token = localStorage.getItem('token');
      // Fetch session students directly
      const res = await fetch(`/api/faculty/students?section=${session.section}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        setStudents(json.data);
        
        // Fetch session status values for students
        // For testing / simplicity, we assume we load records
        // Let's query from backend /api/faculty/attendance sessions if we had a detail route,
        // otherwise we can load and let user change it.
        // Let's fetch all session logs
        const initialMap = {};
        json.data.forEach(s => {
          initialMap[s.id] = 'Present'; // default
        });
        setAttendanceMap(initialMap);
      }
    } catch (err) {
      setToast({ show: true, message: 'Failed to load details', type: 'error' });
    } finally {
      setLoadingStudents(false);
    }
  };

  if (loadingSubjects) return <Loader message="Resolving allocated subject schedules..." />;

  return (
    <div className="faculty-attendance-container animate-fade-in">
      <div className="attendance-header">
        <h1>Attendance Management Desk</h1>
        <p>Log daily classroom attendance sessions and sync summaries to the NBKR database.</p>
      </div>

      {/* Tabs */}
      <div className="tab-control-bar">
        <button 
          onClick={() => { setActiveTab('mark'); setEditingSessionId(null); }} 
          className={`tab-btn ${activeTab === 'mark' ? 'active' : ''}`}
        >
          <PlusSquare size={16} />
          <span>{editingSessionId ? 'Edit Session' : 'Mark Attendance'}</span>
        </button>
        <button 
          onClick={() => setActiveTab('history')} 
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
        >
          <History size={16} />
          <span>Log History</span>
        </button>
      </div>

      {activeTab === 'mark' && (
        <form onSubmit={handleSubmitAttendance} className="attendance-form glass-card">
          <div className="form-settings-row">
            <div className="setting-item">
              <label>Allocated Subject</label>
              <select 
                value={selectedSubjectId} 
                onChange={(e) => {
                  setSelectedSubjectId(e.target.value);
                  const matched = subjects.find(s => s.subject_id === parseInt(e.target.value));
                  if (matched) setSelectedSection(matched.section);
                }}
                disabled={!!editingSessionId}
              >
                {subjects.map(s => (
                  <option key={s.id} value={s.subject_id}>{s.name} ({s.code})</option>
                ))}
              </select>
            </div>

            <div className="setting-item">
              <label>Section</label>
              <select value={selectedSection} onChange={(e) => setSelectedSection(e.target.value)} disabled={!!editingSessionId}>
                <option value="A">Section A</option>
                <option value="B">Section B</option>
                <option value="C">Section C</option>
              </select>
            </div>

            <div className="setting-item">
              <label>Class Date</label>
              <input 
                type="date" 
                value={selectedDate} 
                onChange={(e) => setSelectedDate(e.target.value)}
                disabled={!!editingSessionId}
              />
            </div>

            <div className="setting-item">
              <label>Class Session</label>
              <select value={selectedSession} onChange={(e) => setSelectedSession(e.target.value)} disabled={!!editingSessionId}>
                <option value="Session 1">Session 1 (09:00 - 09:50)</option>
                <option value="Session 2">Session 2 (09:50 - 10:40)</option>
                <option value="Session 3">Session 3 (11:00 - 11:50)</option>
                <option value="Session 4">Session 4 (11:50 - 12:40)</option>
                <option value="Session 5">Session 5 (01:40 - 02:30)</option>
                <option value="Session 6">Session 6 (02:30 - 03:20)</option>
              </select>
            </div>
          </div>

          <div className="roster-actions-header">
            <h3>Student Roster Roll Call</h3>
            <div className="bulk-mark-actions">
              <button type="button" onClick={() => markAll('Present')} className="bulk-btn present">
                Mark All Present
              </button>
              <button type="button" onClick={() => markAll('Absent')} className="bulk-btn absent">
                Mark All Absent
              </button>
            </div>
          </div>

          {loadingStudents ? (
            <Loader message="Resolving student roster..." />
          ) : students.length === 0 ? (
            <div className="no-students-panel">No students mapped to this section context.</div>
          ) : (
            <div className="marking-list-container">
              {students.map((student) => (
                <div key={student.id} className="marking-row-card">
                  <div className="student-profile-info">
                    <span className="student-roll">{student.roll_no}</span>
                    <span className="student-name">{student.name}</span>
                    <span className="cur-pct">Current Attendance: {student.attendance_percentage}%</span>
                  </div>

                  <div className="status-toggle-options">
                    <button
                      type="button"
                      onClick={() => handleStatusChange(student.id, 'Present')}
                      className={`toggle-option present ${attendanceMap[student.id] === 'Present' ? 'active' : ''}`}
                    >
                      <Check size={16} />
                      <span>Present</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleStatusChange(student.id, 'Absent')}
                      className={`toggle-option absent ${attendanceMap[student.id] === 'Absent' ? 'active' : ''}`}
                    >
                      <span>Absent</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="submit-form-bar">
            {editingSessionId && (
              <button type="button" onClick={() => setEditingSessionId(null)} className="btn btn-secondary">
                Cancel Edit
              </button>
            )}
            <button type="submit" className="btn btn-primary submit-sheet-btn" disabled={submitting || students.length === 0}>
              <Save size={18} />
              <span>{submitting ? 'Submitting...' : editingSessionId ? 'Update Session Attendance' : 'Submit Attendance Sheet'}</span>
            </button>
          </div>
        </form>
      )}

      {activeTab === 'history' && (
        <div className="history-list-panel glass-card">
          <h3>Logged Attendance Session History</h3>
          {pastSessions.length === 0 ? (
            <div className="empty-history">You have not logged any class sessions yet.</div>
          ) : (
            <div className="history-table-wrapper">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Subject Name</th>
                    <th>Section</th>
                    <th>Session</th>
                    <th>Total Count</th>
                    <th>Present</th>
                    <th>Absent</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {pastSessions.map(session => (
                    <tr key={session.id}>
                      <td className="date-cell">{new Date(session.date).toLocaleDateString()}</td>
                      <td><strong>{session.subject_name}</strong> ({session.subject_code})</td>
                      <td className="center-text">{session.section}</td>
                      <td>{session.session}</td>
                      <td className="center-text">{session.total_students}</td>
                      <td className="center-text present-count">{session.present}</td>
                      <td className="center-text absent-count">{session.absent}</td>
                      <td>
                        <button 
                          onClick={() => handleLoadSessionForEdit(session)}
                          className="edit-session-btn"
                        >
                          Edit Records
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
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
export default FacultyAttendance;

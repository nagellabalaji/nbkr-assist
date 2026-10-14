import React, { useEffect, useState } from 'react';
import { Users, PlusCircle, Book, Award, Save, CheckCircle } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './HODFaculty.css';

export const HODFaculty = () => {
  const [faculty, setFaculty] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // Assignment states
  const [selectedFacultyId, setSelectedFacultyId] = useState('');
  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [section, setSection] = useState('A');

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch faculty list
      const facRes = await fetch('/api/hod/faculty', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const facJson = await facRes.json();
      
      // Fetch subjects list
      const subRes = await fetch('/api/hod/subjects', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const subJson = await subRes.json();

      if (facJson.success) {
        setFaculty(facJson.data);
        if (facJson.data.length > 0) {
          setSelectedFacultyId(facJson.data[0].id);
        }
      }
      
      if (subJson.success) {
        setSubjects(subJson.data);
        if (subJson.data.length > 0) {
          setSelectedSubjectId(subJson.data[0].id);
        }
      }
    } catch (err) {
      setToast({ show: true, message: 'Failed to retrieve department metrics', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAssignSubject = async (e) => {
    e.preventDefault();
    if (!selectedFacultyId || !selectedSubjectId) return;

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/hod/faculty/assign-subject', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          faculty_id: parseInt(selectedFacultyId),
          subject_id: parseInt(selectedSubjectId),
          section
        })
      });

      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: 'Subject workload successfully mapped to faculty member!', type: 'success' });
        // Refresh workload list
        fetchData();
      } else {
        setToast({ show: true, message: json.message || 'Mapping failed', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server communication error', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <Loader message="Accessing faculty registers..." />;

  return (
    <div className="hod-faculty-container animate-fade-in">
      <div className="faculty-header">
        <h1>Faculty Management & Workloads</h1>
        <p>Monitor workloads, specialization streams, and map subject-section schedules to faculty.</p>
      </div>

      <div className="hod-faculty-layout-grid">
        {/* Left: Workloads assignment form */}
        <div className="assign-form-panel glass-card">
          <h3>Map Subject Workload</h3>
          <form onSubmit={handleAssignSubject} className="assign-form">
            <div className="form-group">
              <label>Select Faculty Member</label>
              <select value={selectedFacultyId} onChange={(e) => setSelectedFacultyId(e.target.value)}>
                {faculty.map(f => (
                  <option key={f.id} value={f.id}>{f.name} ({f.designation})</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Select Subject</label>
              <select value={selectedSubjectId} onChange={(e) => setSelectedSubjectId(e.target.value)}>
                {subjects.map(s => (
                  <option key={s.id} value={s.id}>{s.name} ({s.code})</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Target Section</label>
              <select value={section} onChange={(e) => setSection(e.target.value)}>
                <option value="A">Section A</option>
                <option value="B">Section B</option>
                <option value="C">Section C</option>
              </select>
            </div>

            <button type="submit" className="btn btn-primary submit-assign-btn" disabled={submitting || faculty.length === 0 || subjects.length === 0}>
              <PlusCircle size={18} />
              <span>{submitting ? 'Assigning...' : 'Assign Subject workload'}</span>
            </button>
          </form>
        </div>

        {/* Right: Faculty lists */}
        <div className="faculty-list-panel glass-card">
          <h3>Faculty Directory & Active Workloads</h3>
          <div className="faculty-cards-list">
            {faculty.length === 0 ? (
              <div className="empty-faculty-state">No faculty members mapped to your department.</div>
            ) : (
              faculty.map(f => (
                <div key={f.id} className="faculty-card glass-card">
                  <div className="card-top-row">
                    <div className="fac-avatar">
                      {f.name?.[0]?.toUpperCase()}
                    </div>
                    <div className="fac-meta-title">
                      <h4>{f.name}</h4>
                      <span className="designation-text">{f.designation}</span>
                    </div>
                    <span className={`status-pill ${f.is_available ? 'available' : 'unavailable'}`}>
                      {f.is_available ? 'Available' : 'On Leave'}
                    </span>
                  </div>

                  <div className="card-info-details">
                    <span>Emp ID: <strong>{f.employee_id}</strong></span>
                    <span>Spec: {f.specialization}</span>
                    <span>Email: <strong className="email-link">{f.email}</strong></span>
                    <span>Phone: {f.phone}</span>
                  </div>

                  <div className="card-workload-subjects">
                    <h5>Mapped Subject workload</h5>
                    {f.subjects.length === 0 ? (
                      <span className="no-workload">No subjects assigned yet</span>
                    ) : (
                      <div className="subjects-badges-row">
                        {f.subjects.map((subName, i) => (
                          <span key={i} className="sub-badge">{subName}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
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
export default HODFaculty;

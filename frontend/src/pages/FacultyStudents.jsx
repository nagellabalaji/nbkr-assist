import React, { useEffect, useState } from 'react';
import { Search, Filter, ShieldAlert, CheckCircle, AlertTriangle } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import './FacultyStudents.css';

export const FacultyStudents = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters state
  const [search, setSearch] = useState('');
  const [year, setYear] = useState('');
  const [semester, setSemester] = useState('');
  const [section, setSection] = useState('');
  const [status, setStatus] = useState('');

  const fetchStudents = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (year) params.append('year', year);
      if (semester) params.append('semester', semester);
      if (section) params.append('section', section);
      if (status) params.append('attendance_status', status);
      if (search) params.append('search', search);

      const res = await fetch(`/api/faculty/students?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        setStudents(json.data);
      } else {
        setError(json.message || 'Failed to query student rosters');
      }
    } catch (err) {
      setError('Network communication failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Debounce search input changes
    const delayDebounce = setTimeout(() => {
      fetchStudents();
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [search, year, semester, section, status]);

  return (
    <div className="faculty-students-container animate-fade-in">
      <div className="students-header">
        <h1>My Students Directory</h1>
        <p>Inspect academic rosters for your allocated sections and monitor attendance status compliance.</p>
      </div>

      {/* Filters Board */}
      <div className="filters-board glass-card">
        <div className="search-box-wrapper">
          <Search size={18} className="search-icon" />
          <input 
            type="text" 
            placeholder="Search by Name or Roll Number..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filters-row">
          <div className="filter-item">
            <label>Year</label>
            <select value={year} onChange={(e) => setYear(e.target.value)}>
              <option value="">All Years</option>
              <option value="I Year">I Year</option>
              <option value="II Year">II Year</option>
              <option value="III Year">III Year</option>
              <option value="IV Year">IV Year</option>
            </select>
          </div>

          <div className="filter-item">
            <label>Semester</label>
            <select value={semester} onChange={(e) => setSemester(e.target.value)}>
              <option value="">All Semesters</option>
              <option value="I Semester">I Semester</option>
              <option value="II Semester">II Semester</option>
              <option value="III Semester">III Semester</option>
              <option value="IV Semester">IV Semester</option>
              <option value="V Semester">V Semester</option>
              <option value="VI Semester">VI Semester</option>
              <option value="VII Semester">VII Semester</option>
              <option value="VIII Semester">VIII Semester</option>
            </select>
          </div>

          <div className="filter-item">
            <label>Section</label>
            <select value={section} onChange={(e) => setSection(e.target.value)}>
              <option value="">All Sections</option>
              <option value="A">Section A</option>
              <option value="B">Section B</option>
              <option value="C">Section C</option>
            </select>
          </div>

          <div className="filter-item">
            <label>Attendance Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">All Statuses</option>
              <option value="Eligible">Eligible (&gt;= 75%)</option>
              <option value="Shortage">Shortage (&lt; 75%)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Roster Table */}
      <div className="table-responsive glass-card">
        {loading ? (
          <Loader message="Querying students..." />
        ) : error ? (
          <div className="error-panel">{error}</div>
        ) : students.length === 0 ? (
          <div className="empty-table-state">
            <ShieldAlert size={48} />
            <p>No student records matched your filters/scope</p>
          </div>
        ) : (
          <table className="roster-table">
            <thead>
              <tr>
                <th>Roll Number</th>
                <th>Student Name</th>
                <th>Department</th>
                <th>Program</th>
                <th>Year & Sem</th>
                <th>Section</th>
                <th>Attendance</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {students.map((stu) => (
                <tr key={stu.id}>
                  <td className="roll-cell">{stu.roll_no}</td>
                  <td className="name-cell">{stu.name}</td>
                  <td>{stu.department}</td>
                  <td>{stu.program}</td>
                  <td>{stu.year} - {stu.semester}</td>
                  <td className="center-text">{stu.section}</td>
                  <td className="pct-cell">
                    <div className="pct-bar-wrapper">
                      <div 
                        className={`pct-fill ${stu.status.toLowerCase()}`}
                        style={{ width: `${Math.min(stu.attendance_percentage, 100)}%` }}
                      ></div>
                      <span className="pct-text">{stu.attendance_percentage}%</span>
                    </div>
                  </td>
                  <td>
                    <span className={`status-badge ${stu.status.toLowerCase()}`}>
                      {stu.status === 'Eligible' ? (
                        <>
                          <CheckCircle size={14} />
                          <span>Eligible</span>
                        </>
                      ) : (
                        <>
                          <AlertTriangle size={14} />
                          <span>Shortage</span>
                        </>
                      )}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
export default FacultyStudents;

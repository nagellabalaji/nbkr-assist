import React, { useEffect, useState } from 'react';
import { Search, Filter, ShieldAlert, CheckCircle, AlertTriangle } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import './HODStudents.css';

export const HODStudents = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters state
  const [search, setSearch] = useState('');
  const [year, setYear] = useState('');
  const [semester, setSemester] = useState('');
  const [section, setSection] = useState('');
  const [shortage, setShortage] = useState(false);

  const fetchStudents = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (year) params.append('year', year);
      if (semester) params.append('semester', semester);
      if (section) params.append('section', section);
      if (shortage) params.append('attendance_shortage', 'true');
      if (search) params.append('search', search);

      const res = await fetch(`/api/hod/students?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        setStudents(json.data);
      } else {
        setError(json.message || 'Failed to query student directory');
      }
    } catch (err) {
      setError('Network communication failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      fetchStudents();
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [search, year, semester, section, shortage]);

  return (
    <div className="hod-students-container animate-fade-in">
      <div className="students-header">
        <h1>Students Directory Workspace</h1>
        <p>Monitor profiles, sections, and overall attendance statistics for your department students.</p>
      </div>

      {/* Filters board */}
      <div className="filters-board glass-card">
        <div className="search-box-wrapper">
          <Search size={18} className="search-icon" />
          <input 
            type="text" 
            placeholder="Search student by Name or Roll Number..." 
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

          <div className="filter-item flex-row-align">
            <label className="checkbox-label">
              <input 
                type="checkbox" 
                checked={shortage}
                onChange={(e) => setShortage(e.target.checked)}
              />
              <span>Attendance Shortage (&lt; 75%) Only</span>
            </label>
          </div>
        </div>
      </div>

      {/* Directory list table */}
      <div className="table-responsive glass-card">
        {loading ? (
          <Loader message="Accessing students..." />
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
                <th>Year & Sem</th>
                <th>Section</th>
                <th>Attendance</th>
                <th>Hostel Status</th>
                <th>Transport</th>
              </tr>
            </thead>
            <tbody>
              {students.map((stu) => {
                const status = stu.attendance_percentage >= 75.0 ? 'Eligible' : 'Shortage';
                return (
                  <tr key={stu.id}>
                    <td className="roll-cell">{stu.roll_no}</td>
                    <td className="name-cell">{stu.name}</td>
                    <td>{stu.year} - {stu.semester}</td>
                    <td className="center-text">{stu.section}</td>
                    <td className="pct-cell">
                      <div className="pct-bar-wrapper">
                        <div 
                          className={`pct-fill ${status.toLowerCase()}`}
                          style={{ width: `${Math.min(stu.attendance_percentage, 100)}%` }}
                        ></div>
                        <span className="pct-text">{stu.attendance_percentage}%</span>
                      </div>
                    </td>
                    <td>{stu.hostel_status}</td>
                    <td>{stu.transport_status}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
export default HODStudents;

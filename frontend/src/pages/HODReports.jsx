import React, { useEffect, useState } from 'react';
import { BookOpen, FileText, Printer, Download, Users, AlertTriangle } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import './HODReports.css';

export const HODReports = () => {
  const [reportType, setReportType] = useState('attendance_shortage'); // 'attendance_shortage' | 'grievances' | 'workload'
  const [reportData, setReportData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      let endpoint = '';
      if (reportType === 'attendance_shortage') {
        endpoint = '/api/hod/attendance';
      } else if (reportType === 'grievances') {
        endpoint = '/api/hod/grievances';
      } else if (reportType === 'workload') {
        endpoint = '/api/hod/faculty';
      }

      const res = await fetch(endpoint, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        if (reportType === 'attendance_shortage') {
          setReportData(json.data.shortages);
        } else {
          setReportData(json.data);
        }
      } else {
        setError(json.message || 'Failed to fetch report datasets');
      }
    } catch (err) {
      setError('Network failure generating report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [reportType]);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="hod-reports-container animate-fade-in">
      <div className="reports-header no-print">
        <h1>Department Reports Desk</h1>
        <p>Access, filter, and export administrative audits, faculty workload summaries, and student attendance logs.</p>
      </div>

      {/* Select Report Panel */}
      <div className="report-select-panel glass-card no-print">
        <div className="report-selectors">
          <button 
            onClick={() => setReportType('attendance_shortage')} 
            className={`selector-btn ${reportType === 'attendance_shortage' ? 'active' : ''}`}
          >
            <AlertTriangle size={18} />
            <span>Attendance Shortage Report</span>
          </button>
          <button 
            onClick={() => setReportType('grievances')} 
            className={`selector-btn ${reportType === 'grievances' ? 'active' : ''}`}
          >
            <FileText size={18} />
            <span>Department Grievance Report</span>
          </button>
          <button 
            onClick={() => setReportType('workload')} 
            className={`selector-btn ${reportType === 'workload' ? 'active' : ''}`}
          >
            <Users size={18} />
            <span>Faculty Workload Report</span>
          </button>
        </div>

        <button onClick={handlePrint} className="print-btn">
          <Printer size={18} />
          <span>Print / Export PDF</span>
        </button>
      </div>

      {/* Report Workspace */}
      <div className="report-workspace glass-card">
        <div className="report-print-header">
          <h2>NBKRIST - Department Administration Report</h2>
          <p>Generated on: {new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}</p>
          <hr className="print-divider" />
        </div>

        {loading ? (
          <Loader message="Compiling report dataset..." />
        ) : error ? (
          <div className="error-panel">{error}</div>
        ) : reportData.length === 0 ? (
          <div className="empty-report">No records available for the selected report parameters.</div>
        ) : (
          <div className="report-table-wrapper">
            {reportType === 'attendance_shortage' && (
              <table className="report-data-table">
                <thead>
                  <tr>
                    <th>Roll Number</th>
                    <th>Student Name</th>
                    <th>Subject Taught</th>
                    <th>Total Classes</th>
                    <th>Present</th>
                    <th>Percentage</th>
                    <th>Add'l Classes Needed</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData.map((row, idx) => (
                    <tr key={idx}>
                      <td className="monospace-cell">{row.roll_no}</td>
                      <td><strong>{row.student_name}</strong></td>
                      <td>{row.subject}</td>
                      <td>{row.total_classes}</td>
                      <td>{row.present}</td>
                      <td>{row.percentage}%</td>
                      <td className="clearance-text">+{row.classes_required_to_clear} classes</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {reportType === 'grievances' && (
              <table className="report-data-table">
                <thead>
                  <tr>
                    <th>Grievance ID</th>
                    <th>Grievance Title</th>
                    <th>Location</th>
                    <th>Category</th>
                    <th>Priority</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData.map((row, idx) => (
                    <tr key={idx}>
                      <td className="monospace-cell">{row.id}</td>
                      <td><strong>{row.title}</strong></td>
                      <td>{row.location}</td>
                      <td>{row.category_name} ({row.subcategory})</td>
                      <td>{row.priority || row.ai_priority}</td>
                      <td>{row.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {reportType === 'workload' && (
              <table className="report-data-table">
                <thead>
                  <tr>
                    <th>Emp ID</th>
                    <th>Faculty Name</th>
                    <th>Designation</th>
                    <th>Specialization</th>
                    <th>Assigned Subjects / Workloads</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData.map((row, idx) => (
                    <tr key={idx}>
                      <td className="monospace-cell">{row.employee_id}</td>
                      <td><strong>{row.name}</strong></td>
                      <td>{row.designation}</td>
                      <td>{row.specialization}</td>
                      <td>
                        {row.subjects.length === 0 ? (
                          <em>No subjects assigned</em>
                        ) : (
                          row.subjects.join(', ')
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
export default HODReports;

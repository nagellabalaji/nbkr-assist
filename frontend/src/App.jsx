import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { StudentDashboard } from './pages/StudentDashboard';
import { LodgeComplaint } from './pages/LodgeComplaint';
import { Chatbot } from './pages/Chatbot';
import { Profile } from './pages/Profile';
import { ComplaintDetail } from './pages/ComplaintDetail';
import { StaffDashboard } from './pages/StaffDashboard';
import { AdminDashboard } from './pages/AdminDashboard';
import { AdminUsers } from './pages/AdminUsers';
import { ForgotPassword } from './pages/ForgotPassword';
import { FacultyDashboard } from './pages/FacultyDashboard';
import { FacultyStudents } from './pages/FacultyStudents';
import { FacultyAttendance } from './pages/FacultyAttendance';
import { FacultyGrievances } from './pages/FacultyGrievances';
import { HODDashboard } from './pages/HODDashboard';
import { HODOverview } from './pages/HODOverview';
import { HODStudents } from './pages/HODStudents';
import { HODFaculty } from './pages/HODFaculty';
import { HODAttendance } from './pages/HODAttendance';
import { HODGrievances } from './pages/HODGrievances';
import { HODReports } from './pages/HODReports';
import { StudentExams } from './pages/StudentExams';
import { ExamCellDashboard } from './pages/ExamCellDashboard';
import { StudentHostel } from './pages/StudentHostel';
import { StudentTransport } from './pages/StudentTransport';
import { StudentLibrary } from './pages/StudentLibrary';
import { HostelAdminDashboard } from './pages/HostelAdminDashboard';
import { TransportAdminDashboard } from './pages/TransportAdminDashboard';
import { LibrarianDashboard } from './pages/LibrarianDashboard';
import { StudentPlacements } from './pages/StudentPlacements';
import { PlacementOfficerDashboard } from './pages/PlacementOfficerDashboard';
import Loader from './components/Common/Loader';

// Protected Route Wrapper Component
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { isAuthenticated, loading, user } = useAuth();

  if (loading) {
    return <Loader message="Verifying security credentials..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Redirect unauthorized roles to their fallback dashboard
    if (user.role === 'admin' || user.role === 'super_admin') return <Navigate to="/admin-dashboard" replace />;
    if (user.role === 'staff') return <Navigate to="/staff-dashboard" replace />;
    if (user.role === 'faculty') return <Navigate to="/faculty-dashboard" replace />;
    if (user.role === 'hod') return <Navigate to="/hod-dashboard" replace />;
    if (user.role === 'exam_cell') return <Navigate to="/examcell-dashboard" replace />;
    if (user.role === 'hostel_admin') return <Navigate to="/hostel-admin" replace />;
    if (user.role === 'transport_admin') return <Navigate to="/transport-admin" replace />;
    if (user.role === 'librarian') return <Navigate to="/library-admin" replace />;
    if (user.role === 'placement_officer') return <Navigate to="/placement-admin" replace />;
    return <Navigate to="/student-dashboard" replace />;
  }

  // Wrap standard dashboards and sub-pages in DashboardLayout frame
  return <DashboardLayout>{children}</DashboardLayout>;
};

// Root Router Dispatches
const AppRoutes = () => {
  const { isAuthenticated, user } = useAuth();

  return (
    <Routes>
      {/* Public Pages */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />

      {/* Student Pages */}
      <Route 
        path="/student-dashboard" 
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <StudentDashboard />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/lodge-complaint" 
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <LodgeComplaint />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/chatbot" 
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <Chatbot />
          </ProtectedRoute>
        } 
      />

      {/* Maintenance Staff Pages */}
      <Route 
        path="/staff-dashboard" 
        element={
          <ProtectedRoute allowedRoles={['staff']}>
            <StaffDashboard />
          </ProtectedRoute>
        } 
      />

      {/* Admin Pages */}
      <Route 
        path="/admin-dashboard" 
        element={
          <ProtectedRoute allowedRoles={['admin', 'super_admin']}>
            <AdminDashboard />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/admin-complaints" 
        element={
          <ProtectedRoute allowedRoles={['admin', 'super_admin']}>
            <AdminDashboard /> {/* Re-uses dashboard queue filters */}
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/admin-users" 
        element={
          <ProtectedRoute allowedRoles={['admin', 'super_admin']}>
            <AdminUsers />
          </ProtectedRoute>
        } 
      />

      {/* Faculty Pages */}
      <Route 
        path="/faculty-dashboard" 
        element={
          <ProtectedRoute allowedRoles={['faculty']}>
            <FacultyDashboard />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/faculty-students" 
        element={
          <ProtectedRoute allowedRoles={['faculty']}>
            <FacultyStudents />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/faculty-attendance" 
        element={
          <ProtectedRoute allowedRoles={['faculty']}>
            <FacultyAttendance />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/faculty-grievances" 
        element={
          <ProtectedRoute allowedRoles={['faculty']}>
            <FacultyGrievances />
          </ProtectedRoute>
        } 
      />

      {/* HOD Pages */}
      <Route 
        path="/hod-dashboard" 
        element={
          <ProtectedRoute allowedRoles={['hod']}>
            <HODDashboard />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/hod-overview" 
        element={
          <ProtectedRoute allowedRoles={['hod']}>
            <HODOverview />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/hod-students" 
        element={
          <ProtectedRoute allowedRoles={['hod']}>
            <HODStudents />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/hod-faculty" 
        element={
          <ProtectedRoute allowedRoles={['hod']}>
            <HODFaculty />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/hod-attendance" 
        element={
          <ProtectedRoute allowedRoles={['hod']}>
            <HODAttendance />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/hod-grievances" 
        element={
          <ProtectedRoute allowedRoles={['hod']}>
            <HODGrievances />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/hod-reports" 
        element={
          <ProtectedRoute allowedRoles={['hod']}>
            <HODReports />
          </ProtectedRoute>
        } 
      />

      {/* Exam Routes */}
      <Route 
        path="/exams" 
        element={
          <ProtectedRoute allowedRoles={['student', 'faculty', 'hod']}>
            <StudentExams />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/examcell-dashboard" 
        element={
          <ProtectedRoute allowedRoles={['exam_cell']}>
            <ExamCellDashboard />
          </ProtectedRoute>
        } 
      />

      {/* Hostel Routes */}
      <Route 
        path="/hostel" 
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <StudentHostel />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/hostel-admin" 
        element={
          <ProtectedRoute allowedRoles={['hostel_admin']}>
            <HostelAdminDashboard />
          </ProtectedRoute>
        } 
      />

      {/* Transport Routes */}
      <Route 
        path="/transport" 
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <StudentTransport />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/transport-admin" 
        element={
          <ProtectedRoute allowedRoles={['transport_admin']}>
            <TransportAdminDashboard />
          </ProtectedRoute>
        } 
      />

      {/* Library Routes */}
      <Route 
        path="/library" 
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <StudentLibrary />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/library-admin" 
        element={
          <ProtectedRoute allowedRoles={['librarian']}>
            <LibrarianDashboard />
          </ProtectedRoute>
        } 
      />

      {/* Placement Routes */}
      <Route 
        path="/placements" 
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <StudentPlacements />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/placement-admin" 
        element={
          <ProtectedRoute allowedRoles={['placement_officer']}>
            <PlacementOfficerDashboard />
          </ProtectedRoute>
        } 
      />

      {/* Shared Protected Pages */}
      <Route 
        path="/profile" 
        element={
          <ProtectedRoute allowedRoles={['student', 'staff', 'admin', 'super_admin', 'faculty', 'hod', 'exam_cell']}>
            <Profile />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/complaint/:id" 
        element={
          <ProtectedRoute allowedRoles={['student', 'staff', 'admin', 'super_admin', 'faculty', 'hod', 'exam_cell']}>
            <ComplaintDetail />
          </ProtectedRoute>
        } 
      />

      {/* Catch-all Routing */}
      <Route 
        path="*" 
        element={
          isAuthenticated && user ? (
            (user.role === 'admin' || user.role === 'super_admin') ? (
              <Navigate to="/admin-dashboard" replace />
            ) : user.role === 'staff' ? (
              <Navigate to="/staff-dashboard" replace />
            ) : user.role === 'faculty' ? (
              <Navigate to="/faculty-dashboard" replace />
            ) : user.role === 'hod' ? (
              <Navigate to="/hod-dashboard" replace />
            ) : user.role === 'exam_cell' ? (
              <Navigate to="/examcell-dashboard" replace />
            ) : (
              <Navigate to="/student-dashboard" replace />
            )
          ) : (
            <Navigate to="/login" replace />
          )
        } 
      />
    </Routes>
  );
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

export default App;

import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../hooks/useNotification';
import { 
  Home, PlusCircle, MessageSquare, User, LogOut, Bell, 
  Users, Wrench, Menu, X, Check, ArrowRight, Book, Calendar, Award, Shield, Key, Truck, BookOpen, Activity, Briefcase
} from 'lucide-react';
import './DashboardLayout.css';

export const DashboardLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotification();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const getNavLinks = () => {
    if (!user) return [];
    
    switch (user.role) {
      case 'student':
        return [
          { path: '/student-dashboard', label: 'Dashboard', icon: Home },
          { path: '/lodge-complaint', label: 'File Grievance', icon: PlusCircle },
          { path: '/chatbot', label: 'NBKR Assist Chat', icon: MessageSquare },
          { path: '/profile', label: 'My Profile', icon: User }
        ];
      case 'staff':
        return [
          { path: '/staff-dashboard', label: 'Assigned Tasks', icon: Wrench },
          { path: '/profile', label: 'My Profile', icon: User }
        ];
      case 'admin':
      case 'super_admin':
        return [
          { path: '/admin-dashboard', label: 'Analytics Dashboard', icon: Home },
          { path: '/admin-complaints', label: 'All Grievances', icon: Wrench },
          { path: '/admin-users', label: 'Manage Users', icon: Users },
          { path: '/profile', label: 'Admin Profile', icon: User }
        ];
      default:
        return [];
    }
  };

  const navLinks = getNavLinks();

  return (
    <div className="layout-container">
      {/* Mobile Header */}
      <header className="mobile-header">
        <button onClick={() => setIsSidebarOpen(true)} className="mobile-menu-btn" aria-label="Open menu">
          <Menu size={24} />
        </button>
        <span className="logo-text">NBKR Assist</span>
        <div className="mobile-notif-area">
          <button onClick={() => setIsNotifOpen(!isNotifOpen)} className="notif-btn" aria-label="Notifications">
            <Bell size={20} />
            {unreadCount > 0 && <span className="notif-badge">{unreadCount}</span>}
          </button>
        </div>
      </header>

      {/* Sidebar Overlay (Mobile) */}
      {isSidebarOpen && <div className="sidebar-overlay" onClick={() => setIsSidebarOpen(false)}></div>}

      {/* Navigation Sidebar */}
      <aside className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <span className="logo-icon">🎓</span>
          <span className="logo-text">NBKR Assist</span>
          <button onClick={() => setIsSidebarOpen(false)} className="mobile-close-btn" aria-label="Close menu">
            <X size={20} />
          </button>
        </div>

        <div className="user-profile-widget">
          <div className="user-avatar">{user?.username?.[0]?.toUpperCase() || 'U'}</div>
          <div className="user-info">
            <div className="username">{user?.username}</div>
            <div className="user-role">{user?.role?.toUpperCase()}</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-title">Core</div>
          <Link 
            to={
              (user?.role === 'admin' || user?.role === 'super_admin') ? '/admin-dashboard' : 
              user?.role === 'staff' ? '/staff-dashboard' : 
              user?.role === 'faculty' ? '/faculty-dashboard' : 
              user?.role === 'hod' ? '/hod-dashboard' : 
              '/student-dashboard'
            } 
            className={`nav-link ${location.pathname.includes('dashboard') ? 'active' : ''}`}
            onClick={() => setIsSidebarOpen(false)}
          >
            <Home size={18} />
            <span>Dashboard</span>
          </Link>

          {/* Student Specific Links */}
          {user?.role === 'student' && (
            <>
              <div className="nav-section-title">
                <span>Academics</span>
                <span className="coming-soon-tag">Soon</span>
              </div>
              <div className="nav-link disabled"><Activity size={18} /> <span>Attendance</span></div>
              <Link 
                to="/exams" 
                className={`nav-link ${location.pathname === '/exams' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Calendar size={18} />
                <span>Exam Calendar</span>
              </Link>
              <div className="nav-link disabled"><BookOpen size={18} /> <span>Learning Resources</span></div>

              <div className="nav-section-title">Grievance Desk</div>
              <Link 
                to="/lodge-complaint" 
                className={`nav-link ${location.pathname === '/lodge-complaint' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <PlusCircle size={18} />
                <span>File Grievance</span>
              </Link>

              <div className="nav-section-title">Campus Services</div>
              <Link 
                to="/hostel" 
                className={`nav-link ${location.pathname === '/hostel' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Shield size={18} />
                <span>Hostel Support</span>
              </Link>
              <Link 
                to="/transport" 
                className={`nav-link ${location.pathname === '/transport' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Truck size={18} />
                <span>Transport Support</span>
              </Link>
              <Link 
                to="/library" 
                className={`nav-link ${location.pathname === '/library' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Book size={18} />
                <span>Library Support</span>
              </Link>
              <Link 
                to="/placements" 
                className={`nav-link ${location.pathname === '/placements' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Briefcase size={18} />
                <span>Placement Desk</span>
              </Link>

              <div className="nav-section-title">Support & Profile</div>
              <Link 
                to="/chatbot" 
                className={`nav-link ${location.pathname === '/chatbot' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <MessageSquare size={18} />
                <span>NBKR Assist Chat</span>
              </Link>
            </>
          )}

          {/* Faculty Specific Links */}
          {user?.role === 'faculty' && (
            <>
              <div className="nav-section-title">Academics</div>
              <Link 
                to="/faculty-students" 
                className={`nav-link ${location.pathname === '/faculty-students' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Users size={18} />
                <span>My Students</span>
              </Link>
              <Link 
                to="/faculty-attendance" 
                className={`nav-link ${location.pathname === '/faculty-attendance' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Activity size={18} />
                <span>Attendance Manager</span>
              </Link>
              <Link 
                to="/exams" 
                className={`nav-link ${location.pathname === '/exams' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Calendar size={18} />
                <span>Exam Schedules</span>
              </Link>

              <div className="nav-section-title">Grievance Desk</div>
              <Link 
                to="/faculty-grievances" 
                className={`nav-link ${location.pathname === '/faculty-grievances' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Wrench size={18} />
                <span>My Grievances</span>
              </Link>
            </>
          )}

          {/* HOD Specific Links */}
          {user?.role === 'hod' && (
            <>
              <div className="nav-section-title">Department</div>
              <Link 
                to="/hod-overview" 
                className={`nav-link ${location.pathname === '/hod-overview' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <BookOpen size={18} />
                <span>Dept Overview</span>
              </Link>
              <Link 
                to="/hod-students" 
                className={`nav-link ${location.pathname === '/hod-students' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Users size={18} />
                <span>Students Directory</span>
              </Link>
              <Link 
                to="/hod-faculty" 
                className={`nav-link ${location.pathname === '/hod-faculty' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Users size={18} />
                <span>Faculty workloads</span>
              </Link>

              <div className="nav-section-title">Academics & Operations</div>
              <Link 
                to="/hod-attendance" 
                className={`nav-link ${location.pathname === '/hod-attendance' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Activity size={18} />
                <span>Attendance Analytics</span>
              </Link>
              <Link 
                to="/hod-grievances" 
                className={`nav-link ${location.pathname === '/hod-grievances' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Wrench size={18} />
                <span>Grievance Desk</span>
              </Link>
              <Link 
                to="/hod-reports" 
                className={`nav-link ${location.pathname === '/hod-reports' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Book size={18} />
                <span>Reports</span>
              </Link>
              <Link 
                to="/exams" 
                className={`nav-link ${location.pathname === '/exams' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Calendar size={18} />
                <span>Exam Schedules</span>
              </Link>
            </>
          )}

          {/* Legacy staff specific links */}
          {user?.role === 'staff' && (
            <>
              <div className="nav-section-title">Grievance Desk</div>
              <Link 
                to="/staff-dashboard" 
                className={`nav-link ${location.pathname === '/staff-dashboard' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Wrench size={18} />
                <span>Assigned Tasks</span>
              </Link>
            </>
          )}

          {/* Admin Specific Links */}
          {(user?.role === 'admin' || user?.role === 'super_admin') && (
            <>
              <div className="nav-section-title">Grievance Desk</div>
              <Link 
                to="/admin-complaints" 
                className={`nav-link ${location.pathname === '/admin-complaints' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Wrench size={18} />
                <span>All Grievances</span>
              </Link>
              <Link 
                to="/admin-users" 
                className={`nav-link ${location.pathname === '/admin-users' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Users size={18} />
                <span>Manage Users</span>
              </Link>
            </>
          )}
          {/* Exam Cell Specific Links */}
          {user?.role === 'exam_cell' && (
            <>
              <div className="nav-section-title">Exam Operations</div>
              <Link 
                to="/examcell-dashboard" 
                className={`nav-link ${location.pathname === '/examcell-dashboard' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Calendar size={18} />
                <span>Exam Cell Portal</span>
              </Link>
            </>
          )}
          {/* Hostel Admin Specific Links */}
          {user?.role === 'hostel_admin' && (
            <>
              <div className="nav-section-title">Hostel Operations</div>
              <Link 
                to="/hostel-admin" 
                className={`nav-link ${location.pathname === '/hostel-admin' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Home size={18} />
                <span>Hostel Portal</span>
              </Link>
            </>
          )}
          {/* Transport Admin Specific Links */}
          {user?.role === 'transport_admin' && (
            <>
              <div className="nav-section-title">Transport Operations</div>
              <Link 
                to="/transport-admin" 
                className={`nav-link ${location.pathname === '/transport-admin' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Truck size={18} />
                <span>Transport Portal</span>
              </Link>
            </>
          )}
          {/* Librarian Specific Links */}
          {user?.role === 'librarian' && (
            <>
              <div className="nav-section-title">Library Operations</div>
              <Link 
                to="/library-admin" 
                className={`nav-link ${location.pathname === '/library-admin' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Book size={18} />
                <span>Library Portal</span>
              </Link>
            </>
          )}
          {/* Placement Officer Specific Links */}
          {user?.role === 'placement_officer' && (
            <>
              <div className="nav-section-title">Placement Operations</div>
              <Link 
                to="/placement-admin" 
                className={`nav-link ${location.pathname === '/placement-admin' ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Briefcase size={18} />
                <span>Placement Portal</span>
              </Link>
            </>
          )}
          <div className="nav-section-title">Support & Profile</div>
          <Link 
            to="/profile" 
            className={`nav-link ${location.pathname === '/profile' ? 'active' : ''}`}
            onClick={() => setIsSidebarOpen(false)}
          >
            <User size={18} />
            <span>My Profile</span>
          </Link>
        </nav>

        <div className="sidebar-footer">
          <div style={{ padding: '0 8px 10px', fontSize: '0.78rem', color: 'var(--text-muted)', textAlign: 'center', fontWeight: '500' }}>
            Made by <strong style={{ color: 'var(--color-primary)' }}>BALAJI NAGELLA</strong>
          </div>
          <button onClick={handleLogout} className="logout-btn">
            <LogOut size={18} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {/* Desktop Top Navbar */}
        <div className="top-navbar">
          <div className="page-context-title">
            <h2>Welcome Back, {user?.username}</h2>
            <p>NBKR Assist - Student Support & Grievance Portal</p>
          </div>
          
          <div className="top-nav-actions">
            {/* Notifications Dropdown Container */}
            <div className="notif-container">
              <button onClick={() => setIsNotifOpen(!isNotifOpen)} className="notif-btn" aria-label="Notifications">
                <Bell size={20} />
                {unreadCount > 0 && <span className="notif-badge">{unreadCount}</span>}
              </button>

              {isNotifOpen && (
                <>
                  <div className="dropdown-overlay" onClick={() => setIsNotifOpen(false)}></div>
                  <div className="notif-dropdown glass-card">
                    <div className="notif-dropdown-header">
                      <h3>Notifications</h3>
                      {unreadCount > 0 && (
                        <button onClick={markAllAsRead} className="read-all-btn">
                          Mark all read
                        </button>
                      )}
                    </div>

                    <div className="notif-dropdown-list">
                      {notifications.length === 0 ? (
                        <div className="empty-notif">No new notifications</div>
                      ) : (
                        notifications.map((notif) => (
                          <div 
                            key={notif.id} 
                            className={`notif-item ${notif.is_read ? 'read' : 'unread'}`}
                            onClick={() => {
                              markAsRead(notif.id);
                              setIsNotifOpen(false);
                              if (notif.complaint_id) {
                                navigate(`/complaint/${notif.complaint_id}`);
                              }
                            }}
                          >
                            <div className="notif-item-header">
                              <span className="notif-title">{notif.title}</span>
                              {!notif.is_read && <span className="unread-dot"></span>}
                            </div>
                            <p className="notif-msg">{notif.message}</p>
                            <span className="notif-time">
                              {new Date(notif.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
            
            <div className="vertical-divider"></div>

            <div className="top-user-avatar">
              {user?.username?.[0]?.toUpperCase()}
            </div>
          </div>
        </div>

        {/* Dynamic Inner Page */}
        <div className="page-body-container">
          {children}
        </div>

        <footer style={{ textAlign: 'center', padding: '18px 12px 24px', fontSize: '0.85rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-color)', marginTop: '32px' }}>
          <span>NBKR Assist &bull; Student Support & Grievance Portal &bull; Made with dedication by <strong style={{ color: 'var(--text-primary)' }}>BALAJI NAGELLA</strong></span>
        </footer>
      </main>
    </div>
  );
};
export default DashboardLayout;

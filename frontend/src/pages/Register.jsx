import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/auth';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './AuthPages.css';

export const Register = () => {
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();

  // Redirect if already logged in
  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.role === 'admin') navigate('/admin-dashboard');
      else if (user.role === 'staff') navigate('/staff-dashboard');
      else navigate('/student-dashboard');
    }
  }, [isAuthenticated, user, navigate]);

  // Form Fields
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const role = 'student'; // Restricted strictly to student publicly
  
  // Student Specific
  const [rollNo, setRollNo] = useState('');
  const [departmentsList, setDepartmentsList] = useState([]);
  const [departmentId, setDepartmentId] = useState('');
  const [hostelNo, setHostelNo] = useState('');
  const [roomNo, setRoomNo] = useState('');
  const [contactNo, setContactNo] = useState('');

  // OTP Verification States
  const [step, setStep] = useState(1); // 1 = Registration details, 2 = OTP check
  const [otpVal, setOtpVal] = useState(['', '', '', '', '', '']);
  const [timer, setTimer] = useState(60);
  const [canResend, setCanResend] = useState(false);
  const otpInputsRef = useRef([]);

  const [loadingLocal, setLoadingLocal] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // Handle countdown timer for Resend
  useEffect(() => {
    let interval = null;
    if (step === 2 && timer > 0) {
      interval = setInterval(() => {
        setTimer((prev) => prev - 1);
      }, 1000);
    } else if (timer === 0) {
      setCanResend(true);
    }
    return () => clearInterval(interval);
  }, [step, timer]);

  // Load departments list from DB
  useEffect(() => {
    const loadDepts = async () => {
      try {
        const res = await authService.getDepartments();
        if (res.success && res.data.length > 0) {
          setDepartmentsList(res.data);
          setDepartmentId(res.data[0].id.toString());
        }
      } catch (err) {
        console.error('Failed to load departments list:', err);
      }
    };
    loadDepts();
  }, []);

  // Focus transition refs helper
  const handleOtpChange = (e, index) => {
    const val = e.target.value;
    if (isNaN(val)) return; // Allow numbers only

    const newOtp = [...otpVal];
    newOtp[index] = val.substring(val.length - 1); // Get last typed digit
    setOtpVal(newOtp);

    // Auto-focus next input
    if (val && index < 5) {
      otpInputsRef.current[index + 1].focus();
    }
  };

  const handleOtpKeyDown = (e, index) => {
    // Move to previous box on Backspace
    if (e.key === 'Backspace' && !otpVal[index] && index > 0) {
      otpInputsRef.current[index - 1].focus();
    }
  };

  const handleOtpPaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').trim();
    if (pastedData.length !== 6 || isNaN(pastedData)) return;

    const newOtp = pastedData.split('');
    setOtpVal(newOtp);
    otpInputsRef.current[5].focus(); // Focus last box
  };

  const getPayload = () => {
    return {
      username: username.trim(),
      email: email.trim(),
      password: password.trim(),
      role: role,
      roll_no: rollNo.trim().toUpperCase(),
      department_id: parseInt(departmentId),
      hostel_no: hostelNo.trim() || null,
      room_no: roomNo.trim() || null,
      contact_no: contactNo.trim() || null
    };
  };

  const handleSendOtp = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    // Validations
    if (!username.trim() || !email.trim() || !password.trim() || !role) {
      setErrorMsg('Please fill in all core fields.');
      return;
    }
    if (password.length < 6) {
      setErrorMsg('Password must be at least 6 characters.');
      return;
    }
    if (!rollNo.trim() || !departmentId) {
      setErrorMsg('Roll number and Department selection are required.');
      return;
    }

    setLoadingLocal(true);
    try {
      const payload = getPayload();
      const res = await authService.registerSendOtp(payload);
      if (res.success) {
        setStep(2);
        setTimer(60);
        setCanResend(false);
        setOtpVal(['', '', '', '', '', '']);
        setToast({ show: true, message: 'Verification code sent successfully to your college email.', type: 'success' });
      } else {
        setErrorMsg(res.message);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.message || err.message || 'Error occurred while requesting OTP.');
    } finally {
      setLoadingLocal(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    const otpCode = otpVal.join('');
    if (otpCode.length !== 6) {
      setErrorMsg('Please enter the complete 6-digit verification code.');
      return;
    }

    setLoadingLocal(true);
    try {
      const payload = { ...getPayload(), otp: otpCode };
      const res = await authService.registerVerifyOtp(payload);
      if (res.success) {
        setToast({ show: true, message: 'Verification successful! Account created.', type: 'success' });
        setTimeout(() => {
          navigate('/login?registered=true');
        }, 1500);
      } else {
        setErrorMsg(res.message);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.message || 'Verification failed. Please try again.');
    } finally {
      setLoadingLocal(false);
    }
  };

  const handleResendOtp = async () => {
    if (!canResend) return;
    setErrorMsg('');
    setLoadingLocal(true);

    try {
      const payload = getPayload();
      const res = await authService.registerSendOtp(payload);
      if (res.success) {
        setTimer(60);
        setCanResend(false);
        setOtpVal(['', '', '', '', '', '']);
        setToast({ show: true, message: 'New verification code dispatched to your email.', type: 'success' });
      } else {
        setErrorMsg(res.message);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.message || err.message || 'Failed to resend code.');
    } finally {
      setLoadingLocal(false);
    }
  };

  return (
    <div className="auth-page-container">
      <div className="auth-visual-side">
        <div className="visual-overlay"></div>
        <div className="visual-content">
          <h1>NBKR Assist</h1>
          <p>Student Support, Grievance & Campus Management System. Submit concerns, track status maps, and receive real-time support updates.</p>
          <div className="feature-badges">
            <span className="feat-badge">Grievance Desk</span>
            <span className="feat-badge">Notifications</span>
            <span className="feat-badge">Student Helpdesk</span>
          </div>
          <div style={{ marginTop: '24px', padding: '8px 16px', background: 'rgba(255, 255, 255, 0.12)', borderRadius: '20px', backdropFilter: 'blur(8px)', display: 'inline-block', fontSize: '0.88rem', color: '#ffffff', border: '1px solid rgba(255, 255, 255, 0.25)', letterSpacing: '0.5px' }}>
            Made by <strong>BALAJI NAGELLA</strong>
          </div>
        </div>
      </div>

      <div className="auth-form-side">
        <div className="auth-form-wrapper glass-card registration animate-fade-in">
          {step === 1 ? (
            <>
              <div className="form-header">
                <h2>Create Account</h2>
                <p>Sign up to access student grievances and college support desks</p>
              </div>

              {errorMsg && <div className="auth-error-banner">{errorMsg}</div>}

              <form onSubmit={handleSendOtp} className="auth-form">
                <div className="form-grid">
                  {/* Common Fields */}
                  <div className="form-group">
                    <label htmlFor="username">Full Name <span style={{ color: '#ef4444' }}>*</span></label>
                    <input
                      id="username"
                      type="text"
                      className="form-input"
                      placeholder="e.g. John Doe"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      disabled={loadingLocal}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="email">College Email <span style={{ color: '#ef4444' }}>*</span></label>
                    <input
                      id="email"
                      type="email"
                      className="form-input"
                      placeholder="name@college.edu"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      disabled={loadingLocal}
                      required
                    />
                  </div>

                  <div className="form-group full-width">
                    <label htmlFor="password">Password (min 6 chars) <span style={{ color: '#ef4444' }}>*</span></label>
                    <input
                      id="password"
                      type="password"
                      className="form-input"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      disabled={loadingLocal}
                      required
                    />
                  </div>

                  {/* Student Specific Fields */}
                  <div className="form-group">
                    <label htmlFor="rollNo">Student ID / Roll No <span style={{ color: '#ef4444' }}>*</span></label>
                    <input
                      id="rollNo"
                      type="text"
                      className="form-input"
                      placeholder="e.g. 21CS104"
                      value={rollNo}
                      onChange={(e) => setRollNo(e.target.value)}
                      disabled={loadingLocal}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="departmentId">Academic Department <span style={{ color: '#ef4444' }}>*</span></label>
                    <select
                      id="departmentId"
                      className="form-input"
                      value={departmentId}
                      onChange={(e) => setDepartmentId(e.target.value)}
                      disabled={loadingLocal}
                      required
                    >
                      {departmentsList.map((dept) => (
                        <option key={dept.id} value={dept.id}>
                          {dept.name} ({dept.code})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="hostelNo">Hostel Name (Optional)</label>
                    <input
                      id="hostelNo"
                      type="text"
                      className="form-input"
                      placeholder="e.g. Ramanujan Hall"
                      value={hostelNo}
                      onChange={(e) => setHostelNo(e.target.value)}
                      disabled={loadingLocal}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="roomNo">Room No (Optional)</label>
                    <input
                      id="roomNo"
                      type="text"
                      className="form-input"
                      placeholder="e.g. A-302"
                      value={roomNo}
                      onChange={(e) => setRoomNo(e.target.value)}
                      disabled={loadingLocal}
                    />
                  </div>

                  <div className="form-group full-width">
                    <label htmlFor="contactNo">Contact Number (Optional)</label>
                    <input
                      id="contactNo"
                      type="text"
                      className="form-input"
                      placeholder="e.g. +91 9876543210"
                      value={contactNo}
                      onChange={(e) => setContactNo(e.target.value)}
                      disabled={loadingLocal}
                    />
                  </div>
                </div>

                <button type="submit" className="btn btn-primary btn-block" style={{ marginTop: '24px' }} disabled={loadingLocal}>
                  {loadingLocal ? <Loader size="small" /> : 'Send Verification OTP'}
                </button>
              </form>

              <div className="auth-footer" style={{ marginTop: '24px' }}>
                <p>Already have an account? <Link to="/login">Log In</Link></p>
              </div>
            </>
          ) : (
            <>
              <div className="form-header">
                <h2>Email Verification Required</h2>
                <p>We have sent a 6-digit verification code to your email: <strong style={{ color: 'var(--secondary-hover)' }}>{email}</strong></p>
              </div>

              {errorMsg && <div className="auth-error-banner">{errorMsg}</div>}

              <form onSubmit={handleVerifyOtp} className="auth-form" onPaste={handleOtpPaste}>
                <div className="otp-box-container">
                  {otpVal.map((digit, idx) => (
                    <input
                      key={idx}
                      type="text"
                      className="otp-digit-input"
                      maxLength="1"
                      value={digit}
                      onChange={(e) => handleOtpChange(e, idx)}
                      onKeyDown={(e) => handleOtpKeyDown(e, idx)}
                      ref={(el) => (otpInputsRef.current[idx] = el)}
                      autoFocus={idx === 0}
                      required
                    />
                  ))}
                </div>

                <button 
                  type="submit" 
                  className="btn btn-primary btn-block" 
                  disabled={loadingLocal}
                  style={{ marginTop: '30px' }}
                >
                  {loadingLocal ? <Loader size="small" /> : 'Verify & Create Account'}
                </button>

                <div className="otp-resend-wrapper" style={{ marginTop: '20px', textItems: 'center', textAlign: 'center' }}>
                  {canResend ? (
                    <button 
                      type="button" 
                      onClick={handleResendOtp} 
                      className="btn-link-action"
                      style={{ color: 'var(--secondary-hover)', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}
                    >
                      Resend Verification Code
                    </button>
                  ) : (
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Resend verification code in <strong style={{ color: 'var(--text-secondary)' }}>{timer}s</strong>
                    </p>
                  )}
                </div>

                <button 
                  type="button" 
                  className="btn btn-secondary btn-block"
                  onClick={() => setStep(1)}
                  style={{ marginTop: '16px' }}
                >
                  Back to Registration
                </button>
              </form>
            </>
          )}
        </div>
        <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          Made by <strong style={{ color: 'var(--color-primary)' }}>BALAJI NAGELLA</strong>
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

export default Register;

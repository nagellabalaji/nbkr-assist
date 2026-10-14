import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './AuthPages.css';

export const Login = () => {
  const { login, loginVerifyOtp, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect if already logged in
  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.role === 'admin' || user.role === 'super_admin') navigate('/admin-dashboard');
      else if (user.role === 'staff') navigate('/staff-dashboard');
      else navigate('/student-dashboard');
    }
  }, [isAuthenticated, user, navigate]);

  const [identity, setIdentity] = useState('');
  const [password, setPassword] = useState('');
  
  // Login OTP step states: 1 = username/password, 2 = OTP check
  const [step, setStep] = useState(1);
  const [otpVal, setOtpVal] = useState(['', '', '', '', '', '']);
  const [timer, setTimer] = useState(60);
  const [canResend, setCanResend] = useState(false);
  const otpInputsRef = useRef([]);

  const [loadingLocal, setLoadingLocal] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

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

  // Handle redirection messages
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('expired')) {
      setErrorMsg('Your session has expired. Please sign in again.');
    }
    if (params.get('registered')) {
      setSuccessMsg('Account created successfully! Please log in.');
    }
  }, [location]);

  // Focus transition refs helper
  const handleOtpChange = (e, index) => {
    const val = e.target.value;
    if (isNaN(val)) return;

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
    otpInputsRef.current[5].focus();
  };

  const handleSubmitCredentials = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    
    if (!identity.trim() || !password.trim()) {
      setErrorMsg('Please enter both username/email and password.');
      return;
    }

    setLoadingLocal(true);
    try {
      const result = await login(identity.trim(), password.trim());
      if (result.success) {
        if (result.require_otp) {
          setStep(2);
          setTimer(60);
          setCanResend(false);
          setOtpVal(['', '', '', '', '', '']);
          setSuccessMsg('Verification code sent to your email.');
        } else {
          setSuccessMsg('Access approved! Welcome back.');
        }
      } else {
        setErrorMsg(result.message || 'Authentication failed.');
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.message || 'Invalid username/email or password.');
    } finally {
      setLoadingLocal(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    const otpCode = otpVal.join('');
    if (otpCode.length !== 6) {
      setErrorMsg('Please enter the complete 6-digit verification code.');
      return;
    }

    setLoadingLocal(true);
    try {
      const result = await loginVerifyOtp(identity.trim(), password.trim(), otpCode);
      if (result.success) {
        setSuccessMsg('Access approved! Welcome back.');
      } else {
        setErrorMsg(result.message || 'OTP verification failed.');
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.message || 'Incorrect verification code.');
    } finally {
      setLoadingLocal(false);
    }
  };

  const handleResendOtp = async () => {
    if (!canResend) return;
    setErrorMsg('');
    setSuccessMsg('');
    setLoadingLocal(true);

    try {
      const result = await login(identity.trim(), password.trim());
      if (result.success && result.require_otp) {
        setTimer(60);
        setCanResend(false);
        setOtpVal(['', '', '', '', '', '']);
        setSuccessMsg('New verification code sent to your email.');
      } else {
        setErrorMsg(result.message);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.message || 'Failed to resend code.');
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
          <p>Student Support, Grievance & Campus Management System. Submit academic, facility, or administrative concerns, track resolution status, and receive real-time support updates.</p>
          <div className="feature-badges">
            <span className="feat-badge">Smart Routing</span>
            <span className="feat-badge">Support Desk</span>
            <span className="feat-badge">Student Helpdesk</span>
          </div>
          <div style={{ marginTop: '24px', padding: '8px 16px', background: 'rgba(255, 255, 255, 0.12)', borderRadius: '20px', backdropFilter: 'blur(8px)', display: 'inline-block', fontSize: '0.88rem', color: '#ffffff', border: '1px solid rgba(255, 255, 255, 0.25)', letterSpacing: '0.5px' }}>
            Made by <strong>BALAJI NAGELLA</strong>
          </div>
        </div>
      </div>

      <div className="auth-form-side">
        <div className="auth-form-wrapper glass-card animate-fade-in">
          {step === 1 ? (
            <>
              <div className="form-header">
                <h2>Sign In</h2>
                <p>Access the student support and grievance portal</p>
              </div>

              <form onSubmit={handleSubmitCredentials} className="auth-form">
                <div className="form-group">
                  <label htmlFor="identity">Username or Email</label>
                  <input
                    id="identity"
                    type="text"
                    className="form-input"
                    placeholder="Enter email or username"
                    value={identity}
                    onChange={(e) => setIdentity(e.target.value)}
                    disabled={loadingLocal}
                    required
                  />
                </div>

                <div className="form-group">
                  <div className="label-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <label htmlFor="password">Password</label>
                    <Link to="/forgot-password" style={{ fontSize: '0.8rem', color: 'var(--secondary-hover)', textDecoration: 'none' }}>
                      Forgot Password?
                    </Link>
                  </div>
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

                <button type="submit" className="btn btn-primary btn-block" disabled={loadingLocal}>
                  {loadingLocal ? <Loader size="small" /> : 'Log In'}
                </button>
              </form>

              <div className="form-footer" style={{ marginTop: '24px' }}>
                <p>New to the platform? <Link to="/register" className="auth-link">Create Account</Link></p>
              </div>
            </>
          ) : (
            <>
              <div className="form-header">
                <h2>Two-Step Verification</h2>
                <p>An OTP verification code has been sent to your registered email. Enter it below to unlock access.</p>
              </div>

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
                  {loadingLocal ? <Loader size="small" /> : 'Confirm & Authenticate'}
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
                      Resend code in <strong style={{ color: 'var(--text-secondary)' }}>{timer}s</strong>
                    </p>
                  )}
                </div>

                <button 
                  type="button" 
                  className="btn btn-secondary btn-block"
                  onClick={() => setStep(1)}
                  style={{ marginTop: '16px' }}
                >
                  Back to Login
                </button>
              </form>
            </>
          )}
        </div>
        <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          Made by <strong style={{ color: 'var(--color-primary)' }}>BALAJI NAGELLA</strong>
        </div>
      </div>

      {errorMsg && <Toast message={errorMsg} type="error" onClose={() => setErrorMsg('')} />}
      {successMsg && <Toast message={successMsg} type="success" onClose={() => setSuccessMsg('')} />}
    </div>
  );
};

export default Login;

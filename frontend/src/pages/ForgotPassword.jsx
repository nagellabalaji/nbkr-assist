import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authService } from '../services/auth';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './AuthPages.css';

export const ForgotPassword = () => {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // OTP State Flow
  const [step, setStep] = useState(1); // 1 = Enter Email, 2 = Verify OTP, 3 = Reset Password
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

  // Focus transition refs helper
  const handleOtpChange = (e, index) => {
    const val = e.target.value;
    if (isNaN(val)) return;

    const newOtp = [...otpVal];
    newOtp[index] = val.substring(val.length - 1);
    setOtpVal(newOtp);

    if (val && index < 5) {
      otpInputsRef.current[index + 1].focus();
    }
  };

  const handleOtpKeyDown = (e, index) => {
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

  const handleSendOtp = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!email.trim()) {
      setErrorMsg('Please enter your registered college email.');
      return;
    }

    setLoadingLocal(true);
    try {
      const res = await authService.forgotPasswordSendOtp(email.trim());
      if (res.success) {
        setStep(2);
        setTimer(60);
        setCanResend(false);
        setToast({ show: true, message: 'Verification code dispatched to your email.', type: 'success' });
      } else {
        setErrorMsg(res.message);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.message || 'Error sending code.');
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
      const res = await authService.forgotPasswordVerifyOtp(email.trim(), otpCode);
      if (res.success) {
        setStep(3);
        setToast({ show: true, message: 'OTP verified successfully! Set your new password.', type: 'success' });
      } else {
        setErrorMsg(res.message);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.message || 'Verification failed. Code is invalid.');
    } finally {
      setLoadingLocal(false);
    }
  };

  const handleResendOtp = async () => {
    if (!canResend) return;
    setErrorMsg('');
    setLoadingLocal(true);

    try {
      const res = await authService.forgotPasswordSendOtp(email.trim());
      if (res.success) {
        setTimer(60);
        setCanResend(false);
        setOtpVal(['', '', '', '', '', '']);
        setToast({ show: true, message: 'New verification code sent successfully.', type: 'success' });
      } else {
        setErrorMsg(res.message);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.message || 'Failed to resend code.');
    } finally {
      setLoadingLocal(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!newPassword.trim() || !confirmPassword.trim()) {
      setErrorMsg('Please fill in all password fields.');
      return;
    }

    if (newPassword.length < 6) {
      setErrorMsg('Password must be at least 6 characters.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMsg('Passwords do not match.');
      return;
    }

    setLoadingLocal(true);
    try {
      const otpCode = otpVal.join('');
      const res = await authService.resetPassword(email.trim(), otpCode, newPassword.trim());
      if (res.success) {
        setToast({ show: true, message: 'Password updated successfully! Redirecting...', type: 'success' });
        setTimeout(() => {
          navigate('/login');
        }, 1500);
      } else {
        setErrorMsg(res.message);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.message || 'Password reset failed.');
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
          <p>Secure student support portal. Restore access to your account quickly using a secure multi-factor code sent directly to your registered mail inbox.</p>
          <div className="feature-badges">
            <span className="feat-badge">Hashed OTP Keys</span>
            <span className="feat-badge">Brute-Force Shield</span>
            <span className="feat-badge">Fast Recovery</span>
          </div>
          <div style={{ marginTop: '24px', padding: '8px 16px', background: 'rgba(255, 255, 255, 0.12)', borderRadius: '20px', backdropFilter: 'blur(8px)', display: 'inline-block', fontSize: '0.88rem', color: '#ffffff', border: '1px solid rgba(255, 255, 255, 0.25)', letterSpacing: '0.5px' }}>
            Made by <strong>BALAJI NAGELLA</strong>
          </div>
        </div>
      </div>

      <div className="auth-form-side">
        <div className="auth-form-wrapper glass-card animate-fade-in">
          {step === 1 && (
            <>
              <div className="form-header">
                <h2>Forgot Password</h2>
                <p>Enter your registered college email below, and we will send you a code to reset your password.</p>
              </div>

              {errorMsg && <div className="auth-error-banner">{errorMsg}</div>}

              <form onSubmit={handleSendOtp} className="auth-form">
                <div className="form-group">
                  <label htmlFor="email">College Email Address</label>
                  <input
                    id="email"
                    type="email"
                    className="form-input"
                    placeholder="name@college.edu"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>

                <button type="submit" className="btn btn-primary btn-block" disabled={loadingLocal}>
                  {loadingLocal ? <Loader size="small" /> : 'Send Reset Code'}
                </button>

                <button 
                  type="button" 
                  className="btn btn-secondary btn-block"
                  onClick={() => navigate('/login')}
                  style={{ marginTop: '16px' }}
                >
                  Back to Sign In
                </button>
              </form>
            </>
          )}

          {step === 2 && (
            <>
              <div className="form-header">
                <h2>Verify Reset Code</h2>
                <p>A secure verification code has been dispatched to: <strong style={{ color: 'var(--secondary-hover)' }}>{email}</strong></p>
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
                  {loadingLocal ? <Loader size="small" /> : 'Verify Code'}
                </button>

                <div className="otp-resend-wrapper" style={{ marginTop: '20px', textAlign: 'center' }}>
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
                  Back to Email
                </button>
              </form>
            </>
          )}

          {step === 3 && (
            <>
              <div className="form-header">
                <h2>Reset Password</h2>
                <p>Verification successful! Enter and confirm your new password below.</p>
              </div>

              {errorMsg && <div className="auth-error-banner">{errorMsg}</div>}

              <form onSubmit={handleResetPassword} className="auth-form">
                <div className="form-group">
                  <label htmlFor="newPassword">New Password (min 6 chars)</label>
                  <input
                    id="newPassword"
                    type="password"
                    className="form-input"
                    placeholder="••••••••"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="confirmPassword">Confirm New Password</label>
                  <input
                    id="confirmPassword"
                    type="password"
                    className="form-input"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </div>

                <button type="submit" className="btn btn-primary btn-block" disabled={loadingLocal}>
                  {loadingLocal ? <Loader size="small" /> : 'Update Password'}
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
export default ForgotPassword;

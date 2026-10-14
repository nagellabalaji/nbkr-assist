import React, { useEffect } from 'react';
import { CheckCircle, AlertCircle, X } from 'lucide-react';
import './Common.css';

export const Toast = ({ message, type = 'success', onClose, duration = 4000 }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, duration);
    return () => clearTimeout(timer);
  }, [onClose, duration]);

  return (
    <div className={`toast-alert glass-card ${type}`}>
      {type === 'success' ? (
        <CheckCircle className="toast-icon success" size={18} />
      ) : (
        <AlertCircle className="toast-icon error" size={18} />
      )}
      <span className="toast-message">{message}</span>
      <button onClick={onClose} className="toast-close-btn" aria-label="Close alert">
        <X size={14} />
      </button>
    </div>
  );
};
export default Toast;

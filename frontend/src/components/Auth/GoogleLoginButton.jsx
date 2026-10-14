import React, { useEffect, useRef, useState } from 'react';

export const GoogleLoginButton = ({ onSuccess, onError, disabled = false }) => {
  const googleBtnRef = useRef(null);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [loadError, setLoadError] = useState('');
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  useEffect(() => {
    if (!clientId) {
      return;
    }

    // Check if Google script is already loaded
    if (window.google?.accounts?.id) {
      setScriptLoaded(true);
      return;
    }

    // Dynamically load Google Identity Services SDK
    const existingScript = document.getElementById('google-gsi-script');
    if (!existingScript) {
      const script = document.createElement('script');
      script.id = 'google-gsi-script';
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => setScriptLoaded(true);
      script.onerror = () => {
        setLoadError('Failed to load Google Sign-In SDK. Please check your internet connection.');
        if (onError) onError('Failed to load Google Sign-In SDK.');
      };
      document.body.appendChild(script);
    } else {
      existingScript.addEventListener('load', () => setScriptLoaded(true));
    }
  }, [clientId, onError]);

  useEffect(() => {
    if (!scriptLoaded || !clientId || !googleBtnRef.current || !window.google?.accounts?.id) {
      return;
    }

    try {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => {
          if (response?.credential) {
            if (onSuccess) onSuccess(response.credential);
          } else {
            if (onError) onError('Google did not return a valid credential.');
          }
        },
        auto_select: false,
        cancel_on_tap_outside: true
      });

      // Clear previous buttons if re-rendering
      if (googleBtnRef.current) {
        googleBtnRef.current.innerHTML = '';
        window.google.accounts.id.renderButton(googleBtnRef.current, {
          theme: 'outline',
          size: 'large',
          type: 'standard',
          text: 'continue_with',
          shape: 'pill',
          logo_alignment: 'left',
          width: '100%'
        });
      }
    } catch (err) {
      console.error('Google Sign-In initialization error:', err);
      setLoadError('Error initializing Google Sign-In.');
    }
  }, [scriptLoaded, clientId, onSuccess, onError]);

  // Graceful fallback if VITE_GOOGLE_CLIENT_ID is not configured
  if (!clientId) {
    return (
      <div className="google-auth-notice" title="Set VITE_GOOGLE_CLIENT_ID in your frontend .env file">
        <button
          type="button"
          className="google-btn-custom disabled"
          onClick={() => {
            if (onError) onError('Google OAuth Client ID is not configured. Please add VITE_GOOGLE_CLIENT_ID to your frontend .env file.');
          }}
        >
          <GoogleIcon />
          <span>Continue with Google</span>
        </button>
        <span className="google-config-hint">Configuration required in .env (Click for info)</span>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="google-auth-error">
        <button
          type="button"
          className="google-btn-custom disabled"
          disabled
        >
          <GoogleIcon />
          <span>Continue with Google</span>
        </button>
        <span className="google-config-hint">{loadError}</span>
      </div>
    );
  }

  return (
    <div className={`google-btn-wrapper ${disabled ? 'disabled' : ''}`}>
      <div ref={googleBtnRef} className="google-gis-container"></div>
    </div>
  );
};

// Official Google "G" SVG icon
export const GoogleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" className="google-svg-icon" aria-hidden="true">
    <path
      fill="#4285F4"
      d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17Z"
    />
    <path
      fill="#34A853"
      d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24Z"
    />
    <path
      fill="#FBBC05"
      d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15Z"
    />
    <path
      fill="#EA4335"
      d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.93 6.72-4.93Z"
    />
  </svg>
);

export default GoogleLoginButton;

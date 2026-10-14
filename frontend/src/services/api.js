import axios from 'axios';

// Load backend API url from environment variables for deployment
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 seconds timeout limit
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach JWT token if stored
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle errors globally (e.g. 401 unauthorized/expired tokens)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      
      // If token expired or invalid, auto-logout
      if (status === 401 && (data.error === 'token_expired' || data.error === 'token_invalid' || data.error === 'token_missing')) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        // Force redirect to login page (unless already there)
        if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
          window.location.href = '/login?expired=true';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
export { API_BASE_URL };

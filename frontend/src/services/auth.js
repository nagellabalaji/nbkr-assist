import api from './api';

export const authService = {
  login: async (identity, password) => {
    const response = await api.post('/auth/login', { identity, password });
    if (response.data.success && response.data.data.token) {
      localStorage.setItem('token', response.data.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.data.user));
    }
    return response.data;
  },

  loginVerifyOtp: async (identity, password, otp) => {
    // Verifies credentials and OTP code, then saves token on success
    const response = await api.post('/auth/login/verify-otp', { identity, password, otp });
    if (response.data.success && response.data.data.token) {
      localStorage.setItem('token', response.data.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.data.user));
    }
    return response.data;
  },

  loginWithGoogle: async (credential) => {
    const response = await api.post('/auth/google', { credential });
    if (response.data.success && response.data.data?.token) {
      localStorage.setItem('token', response.data.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.data.user));
    }
    return response.data;
  },

  completeGoogleRegistration: async (registrationData) => {
    const response = await api.post('/auth/google/complete-registration', registrationData);
    if (response.data.success && response.data.data?.token) {
      localStorage.setItem('token', response.data.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.data.user));
    }
    return response.data;
  },


  registerSendOtp: async (userData) => {
    const response = await api.post('/auth/register/send-otp', userData);
    return response.data;
  },

  registerVerifyOtp: async (userData) => {
    // userData contains registration info + otp
    const response = await api.post('/auth/register/verify-otp', userData);
    return response.data;
  },

  forgotPasswordSendOtp: async (email) => {
    const response = await api.post('/auth/forgot-password/send-otp', { email });
    return response.data;
  },

  forgotPasswordVerifyOtp: async (email, otp) => {
    const response = await api.post('/auth/forgot-password/verify-otp', { email, otp });
    return response.data;
  },

  resetPassword: async (email, otp, newPassword) => {
    const response = await api.post('/auth/reset-password', { email, otp, new_password: newPassword });
    return response.data;
  },

  logout: async () => {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      // Ignore logout errors
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  },

  getProfile: async () => {
    const response = await api.get('/auth/profile');
    return response.data;
  },

  updateProfile: async (profileData) => {
    const response = await api.put('/auth/profile', profileData);
    // Update cached user data
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.profile) {
      user.profile = { ...user.profile, ...response.data.data };
      localStorage.setItem('user', JSON.stringify(user));
    }
    return response.data;
  },

  getCurrentUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  getDepartments: async () => {
    const response = await api.get('/departments');
    return response.data;
  }
};

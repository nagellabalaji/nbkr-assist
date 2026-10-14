import React, { createContext, useState, useEffect, useContext } from 'react';
import { authService } from '../services/auth';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Sync state with localStorage on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const storedUser = localStorage.getItem('user');
      const token = localStorage.getItem('token');
      
      if (storedUser && token) {
        try {
          setUser(JSON.parse(storedUser));
          
          // Proactively fetch fresh profile details to sync
          const profileRes = await authService.getProfile();
          if (profileRes.success) {
            const freshUser = {
              ...JSON.parse(storedUser),
              profile: profileRes.data
            };
            setUser(freshUser);
            localStorage.setItem('user', JSON.stringify(freshUser));
          }
        } catch (e) {
          console.error("Token invalid or expired during boot. Logging out.");
          authService.logout();
          setUser(null);
        }
      }
      setLoading(false);
    };
    initializeAuth();
  }, []);

  const login = async (identity, password) => {
    setLoading(true);
    try {
      const res = await authService.login(identity, password);
      if (res.success && res.data && res.data.user) {
        setUser(res.data.user);
      }
      return res;
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.message || 'Invalid username/email or password.' 
      };
    } finally {
      setLoading(false);
    }
  };

  const loginVerifyOtp = async (identity, password, otp) => {
    setLoading(true);
    try {
      const res = await authService.loginVerifyOtp(identity, password, otp);
      if (res.success) {
        setUser(res.data.user);
      }
      return res;
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || 'Verification failed.'
      };
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async (credential) => {
    setLoading(true);
    try {
      const res = await authService.loginWithGoogle(credential);
      if (res.success && res.needs_registration) {
        return res;
      }
      if (res.success && res.data && res.data.user) {
        setUser(res.data.user);
      }
      return res;
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || 'Google authentication failed.'
      };
    } finally {
      setLoading(false);
    }
  };

  const completeGoogleRegistration = async (registrationData) => {
    setLoading(true);
    try {
      const res = await authService.completeGoogleRegistration(registrationData);
      if (res.success && res.data && res.data.user) {
        setUser(res.data.user);
      }
      return res;
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || 'Failed to complete registration.'
      };
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    setLoading(true);
    try {
      const res = await authService.register(userData);
      return res;
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || 'Registration failed.'
      };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
  };

  const updateProfile = async (profileData) => {
    try {
      const res = await authService.updateProfile(profileData);
      if (res.success) {
        setUser((prev) => {
          if (!prev) return null;
          return {
            ...prev,
            profile: res.data
          };
        });
        return { success: true };
      }
      return { success: false, message: res.message };
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || 'Profile update failed.'
      };
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, loginVerifyOtp, loginWithGoogle, completeGoogleRegistration, register, logout, updateProfile, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
export default AuthContext;

import api from './api';

export const adminService = {
  getAnalytics: async () => {
    const response = await api.get('/admin/analytics');
    return response.data;
  },

  getAnalyticsOverview: async () => {
    const response = await api.get('/admin/analytics/overview');
    return response.data;
  },

  getAnalyticsAttendance: async () => {
    const response = await api.get('/admin/analytics/attendance');
    return response.data;
  },

  getAnalyticsModules: async () => {
    const response = await api.get('/admin/analytics/modules');
    return response.data;
  },

  getStaffList: async () => {
    const response = await api.get('/admin/staff');
    return response.data;
  },

  getFacultyList: async () => {
    const response = await api.get('/admin/faculty');
    return response.data;
  },

  getUsersList: async () => {
    const response = await api.get('/admin/users');
    return response.data;
  },

  updateUserStatus: async (userId, status) => {
    const response = await api.put(`/admin/users/${userId}/status`, { status });
    return response.data;
  }
};
export default adminService;

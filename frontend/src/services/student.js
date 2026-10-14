import api from './api';

export const studentService = {
  getSummary: async () => {
    const response = await api.get('/student/dashboard/summary');
    return response.data;
  },
  
  getAttendance: async () => {
    const response = await api.get('/student/dashboard/attendance');
    return response.data;
  },

  getAttendanceDetails: async () => {
    const response = await api.get('/student/dashboard/attendance/details');
    return response.data;
  },

  getExams: async () => {
    const response = await api.get('/student/dashboard/exams');
    return response.data;
  },

  getPlacements: async () => {
    const response = await api.get('/student/dashboard/placements');
    return response.data;
  },

  getGrievances: async () => {
    const response = await api.get('/student/dashboard/grievances');
    return response.data;
  },

  getNotifications: async () => {
    const response = await api.get('/student/dashboard/notifications');
    return response.data;
  }
};

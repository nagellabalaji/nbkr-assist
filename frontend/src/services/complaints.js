import api from './api';

export const complaintService = {
  getComplaints: async (params = {}) => {
    const response = await api.get('/complaints', { params });
    return response.data;
  },

  getComplaintById: async (id) => {
    const response = await api.get(`/complaints/${id}`);
    return response.data;
  },

  getCategories: async () => {
    const response = await api.get('/complaints/categories');
    return response.data;
  },

  getCategoriesSchema: async () => {
    const response = await api.get('/complaints/categories-schema');
    return response.data;
  },

  createComplaint: async (formData, force = false) => {
    const url = force ? '/complaints?force=true' : '/complaints';
    // Override Content-Type for file uploads
    const response = await api.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  updateComplaint: async (id, data) => {
    const response = await api.put(`/complaints/${id}`, data);
    return response.data;
  },

  deleteComplaint: async (id) => {
    const response = await api.delete(`/complaints/${id}`);
    return response.data;
  },

  assignComplaint: async (id, facultyId, branch) => {
    const response = await api.post(`/complaints/${id}/assign`, { 
      faculty_id: facultyId,
      staff_id: facultyId,
      branch 
    });
    return response.data;
  },

  updateStatus: async (id, status, comments = '') => {
    const response = await api.put(`/complaints/${id}/status`, { status, comments });
    return response.data;
  },

  submitFeedback: async (id, rating, comments = '') => {
    const response = await api.post(`/complaints/${id}/feedback`, { rating, comments });
    return response.data;
  }
};
export default complaintService;

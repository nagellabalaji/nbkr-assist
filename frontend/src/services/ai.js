import api from './api';

export const aiService = {
  sendChatMessage: async (message) => {
    const response = await api.post('/ai/chat', { message });
    return response.data;
  },

  getChatHistory: async () => {
    const response = await api.get('/ai/chat/history');
    return response.data;
  },

  dryRunClassify: async (description) => {
    const response = await api.post('/ai/classify', { description });
    return response.data;
  },

  summarizeComplaint: async (complaint_id) => {
    const response = await api.post('/ai/summarize', { complaint_id });
    return response.data;
  }
};
export default aiService;

import axios from 'axios';
import { DEFAULT_API_CONFIG } from '@/types/specs';

export const apiClient = axios.create({
  baseURL: DEFAULT_API_CONFIG.baseUrl,
  timeout: DEFAULT_API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add session ID
apiClient.interceptors.request.use((config) => {
  const sessionId = sessionStorage.getItem('sessionId');
  if (sessionId) {
    config.headers['X-Session-ID'] = sessionId;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const message = error.response.data?.message || error.response.data?.error || 'An error occurred';
      return Promise.reject(new Error(message));
    }
    if (error.request) {
      return Promise.reject(new Error('Network error. Please check your connection.'));
    }
    return Promise.reject(error);
  }
);

export default apiClient;

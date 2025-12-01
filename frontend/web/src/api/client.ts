import axios, { AxiosError, AxiosInstance } from 'axios';

/**
 * Base API URL from environment variables
 * Defaults to localhost:8000 for local development
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Axios instance with base configuration
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor for logging (development only)
 */
apiClient.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, config.data);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for error handling
 */
apiClient.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.config.url}`, response.data);
    }
    return response;
  },
  (error: AxiosError) => {
    // Handle common error scenarios
    if (error.response) {
      // Server responded with error status
      console.error(`[API Error] ${error.response.status}:`, error.response.data);
    } else if (error.request) {
      // Request sent but no response received
      console.error('[API Error] No response received:', error.message);
    } else {
      // Error in request setup
      console.error('[API Error] Request setup error:', error.message);
    }
    return Promise.reject(error);
  }
);

/**
 * Helper to extract error message from API response
 */
export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    if (error.response?.data?.detail) {
      return typeof error.response.data.detail === 'string'
        ? error.response.data.detail
        : JSON.stringify(error.response.data.detail);
    }
    return error.message;
  }
  return 'An unexpected error occurred';
};

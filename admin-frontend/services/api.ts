// services/api.ts - Clean production version
import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';

// Types for API responses
export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface ApiResponse<T = any> {
  data: T;
  status: number;
}

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    // Use environment variable or default to localhost
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 30 seconds timeout
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        // Get token from localStorage
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
        
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error: AxiosError) => {
        this.handleApiError(error);
        return Promise.reject(error);
      }
    );
  }

  private handleApiError(error: AxiosError): void {
    // Handle specific error codes
    if (error.response) {
      const status = error.response.status;

      switch (status) {
        case 401:
          // Unauthorized - clear auth state and redirect to login
          if (typeof window !== 'undefined') {
            localStorage.removeItem('token');
            localStorage.removeItem('active_school_id');
            // Only redirect if not already on auth pages
            if (!window.location.pathname.includes('/login') && 
                !window.location.pathname.includes('/signup') &&
                !window.location.pathname.includes('/public')) {
              window.location.href = '/login';
            }
          }
          break;
        
        case 403:
          // Access forbidden - handled silently
          break;
        
        case 404:
          // Resource not found - handled silently
          break;
        
        case 422:
          // Validation error - handled silently
          break;
        
        case 500:
          // Server error - handled silently
          break;
      }
    }
  }

  // GET request
  async get<T = any>(url: string, params?: any): Promise<AxiosResponse<T>> {
    return this.client.get(url, { params });
  }

  // POST request
  async post<T = any>(url: string, data?: any): Promise<AxiosResponse<T>> {
    return this.client.post(url, data);
  }

  // PUT request
  async put<T = any>(url: string, data?: any): Promise<AxiosResponse<T>> {
    return this.client.put(url, data);
  }

  // PATCH request
  async patch<T = any>(url: string, data?: any): Promise<AxiosResponse<T>> {
    return this.client.patch(url, data);
  }

  // DELETE request
  async delete<T = any>(url: string): Promise<AxiosResponse<T>> {
    return this.client.delete(url);
  }

  // Upload file
  async uploadFile<T = any>(url: string, file: File, additionalData?: any): Promise<AxiosResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);
    
    // Add any additional form data
    if (additionalData) {
      Object.keys(additionalData).forEach(key => {
        formData.append(key, additionalData[key]);
      });
    }

    return this.client.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/healthz');
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  // Get base URL
  getBaseURL(): string {
    return this.baseURL;
  }

  // Set auth token manually (useful for testing)
  setAuthToken(token: string): void {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  // Clear auth token
  clearAuthToken(): void {
    delete this.client.defaults.headers.common['Authorization'];
  }

  // Helper method to check if request was successful
  static isSuccess(response: AxiosResponse): boolean {
    return response.status >= 200 && response.status < 300;
  }

  // Helper method to extract error message
  static getErrorMessage(error: AxiosError): string {
    if (error.response?.data) {
      const data = error.response.data as any;
      return data.detail || data.message || 'An error occurred';
    }
    return error.message || 'Network error';
  }
}

// Create and export a singleton instance
export const apiClient = new ApiClient();

// Export the class for testing or custom instances
export { ApiClient };
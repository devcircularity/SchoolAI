// services/api.ts
import axios from 'axios'

// Single API instance for all backend calls
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
  timeout: 20000,
})

// Attach auth headers automatically
function getToken() {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('token')
}

function getSchoolId() {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('active_school_id')
}

api.interceptors.request.use((config) => {
  const token = getToken()
  const schoolId = getSchoolId()
  
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  if (schoolId) {
    config.headers['X-School-ID'] = schoolId  // Changed from X-School-Id to X-School-ID
  }
  
  return config
})

// Optional: Add response interceptor for global error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // You can add global error handling here if needed
    // For example, automatic logout on 401 errors
    if (error.response?.status === 401) {
      // Handle unauthorized errors globally if desired
      console.error('Unauthorized request detected')
      // Optionally clear tokens and redirect to login
      localStorage.removeItem('token')
      localStorage.removeItem('active_school_id')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
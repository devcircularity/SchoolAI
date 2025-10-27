// services/publicApi.ts - Public API service for unauthenticated requests
import axios from 'axios'

// Separate API instance for public (unauthenticated) calls
export const publicApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
  timeout: 30000, // Longer timeout for chat responses
})

// Public API doesn't need auth headers, but we can add other headers if needed
publicApi.interceptors.request.use((config) => {
  // Add any global headers for public requests
  config.headers['Content-Type'] = 'application/json'
  
  return config
})

// Response interceptor for public API error handling
publicApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Public API error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Public chat service
export const publicChatService = {
  async sendMessage(message: string, sessionId: string) {
    try {
      const response = await publicApi.post('/api/public/chat', {
        message,
        session_id: sessionId
      })
      return response.data
    } catch (error: any) {
      console.error('Failed to send public chat message:', error)
      throw new Error(error.response?.data?.detail || 'Failed to send message')
    }
  },

  async getHealth() {
    try {
      const response = await publicApi.get('/api/public/health')
      return response.data
    } catch (error) {
      console.error('Public health check failed:', error)
      throw error
    }
  }
}
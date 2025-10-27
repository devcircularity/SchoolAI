// services/publicChat.ts - Service for unauthenticated public chat
import axios from 'axios'

// Separate API instance for public (unauthenticated) requests
export const publicApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
})

export type PublicChatMessage = {
  message: string
  session_id: string
}

export type PublicChatResponse = {
  response: string
  session_id: string
  success: boolean
}

export const publicChatService = {
  async sendMessage(message: string, sessionId: string): Promise<PublicChatResponse> {
    try {
      console.log('Sending public chat message:', { message, sessionId })
      
      const { data } = await publicApi.post('/api/public/chat', {
        message,
        session_id: sessionId
      } as PublicChatMessage)
      
      console.log('Public chat response:', data)
      return data
    } catch (error: any) {
      console.error('Public chat error:', error)
      
      // Return a friendly fallback response
      return {
        response: "I'm having some technical difficulties right now. Please try again in a moment, or consider signing up for full access to our school management features!",
        session_id: sessionId,
        success: false
      }
    }
  },

  async checkHealth(): Promise<boolean> {
    try {
      const { data } = await publicApi.get('/api/public/health')
      return data.status === 'healthy'
    } catch (error) {
      console.error('Public chat health check failed:', error)
      return false
    }
  }
}
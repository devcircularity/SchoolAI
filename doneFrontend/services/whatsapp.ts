// services/whatsapp.ts - Fixed to properly handle QR code flow
import { api } from './api'

type WhatsAppStatus = {
  connected: boolean
  ready: boolean
  error?: string
  status?: string
  connection_token?: string
}

type SendMessageRequest = {
  phone_number: string
  message: string
  student_id?: string
}

type SendMessageResponse = {
  success: boolean
  message_id?: string
  phone_number: string
  error?: string
}

type BulkReminderRequest = {
  reminder_type: 'fee_reminder' | 'attendance' | 'announcement'
  message?: string
  student_ids?: string[]
}

type WhatsAppStats = {
  total_sent: number
  by_type: Array<{ type: string; count: number }>
  recent_activity: Array<{ date: string; count: number }>
}

type WhatsAppNotification = {
  id: string
  type: string
  recipient_phone: string
  sent_at?: string
  status: string
  student_name?: string
  admission_no?: string
}

type QRCodeResponse = {
  success: boolean
  qr_code?: string
  status: string
  message?: string
  connection_token?: string
}

export const whatsappService = {
  async getStatus(): Promise<WhatsAppStatus> {
    const { data } = await api.get('/api/whatsapp/status')
    return data
  },

  async initiateConnection(): Promise<{ qr_code?: string; error?: string }> {
    try {
      console.log('=== INITIATING WHATSAPP CONNECTION ===')
      
      // Step 1: Initialize/Connect the instance
      const { data: connectData } = await api.post('/api/whatsapp/connect')
      console.log('Connect response:', connectData)
      
      if (!connectData.success) {
        throw new Error(connectData.error || 'Failed to initialize connection')
      }
      
      // Step 2: Get the QR code
      console.log('Fetching QR code...')
      const { data: qrData } = await api.get('/api/whatsapp/qr')
      console.log('QR response:', qrData)
      
      if (qrData.success && qrData.qr_code) {
        console.log(`QR code received (length: ${qrData.qr_code.length})`)
        return { qr_code: qrData.qr_code }
      } else {
        // If no QR code but connection is ready, user might already be connected
        if (qrData.status === 'already_connected') {
          return { error: 'WhatsApp is already connected' }
        }
        
        throw new Error(qrData.message || 'No QR code received')
      }
      
    } catch (error: any) {
      console.error('=== CONNECTION INITIATION ERROR ===')
      console.error('Error:', error)
      console.error('Response:', error.response?.data)
      
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to initiate connection'
      throw new Error(errorMessage)
    }
  },

  // Alternative method that just gets QR code (for retrying)
  async getQRCode(): Promise<QRCodeResponse> {
    try {
      console.log('Getting QR code directly...')
      const { data } = await api.get('/api/whatsapp/qr')
      console.log('QR response:', data)
      return data
    } catch (error: any) {
      console.error('QR fetch error:', error)
      throw error
    }
  },

  // Check if connection has been established (QR scanned)
  async checkConnection(): Promise<WhatsAppStatus> {
    try {
      const { data } = await api.post('/api/whatsapp/check-connection')
      return data
    } catch (error: any) {
      console.error('Connection check error:', error)
      throw error
    }
  },

  async disconnect(): Promise<void> {
    await api.post('/api/whatsapp/disconnect')
  },

  async sendMessage(phoneNumber: string, message: string, studentId?: string): Promise<SendMessageResponse> {
    const requestData = {
      phone_number: phoneNumber,
      message: message,
      student_id: studentId
    }
    
    console.log('=== WHATSAPP API REQUEST ===')
    console.log('URL: /api/whatsapp/send')
    console.log('Data being sent:', requestData)
    
    try {
      const { data } = await api.post('/api/whatsapp/send', requestData)
      console.log('=== WHATSAPP API SUCCESS ===')
      console.log('Response data:', data)
      return data
    } catch (error: any) {
      console.error('=== WHATSAPP API ERROR ===')
      console.error('Request data that failed:', requestData)
      console.error('Error response:', error.response?.data)
      console.error('Error status:', error.response?.status)
      throw error
    }
  },

  async verifyNumber(phoneNumber: string): Promise<{ valid: boolean; registered: boolean }> {
    const { data } = await api.get(`/api/whatsapp/verify/${encodeURIComponent(phoneNumber)}`)
    return data
  },

  async sendBulkReminder(request: BulkReminderRequest): Promise<{
    summary: {
      total_students: number
      sent_count: number
      failed_count: number
    }
    results: Array<{
      student_name: string
      admission_no: string
      phone: string
      status: string
      error?: string
    }>
  }> {
    const { data } = await api.post('/api/whatsapp/bulk-reminder', request)
    return data
  },

  async getNotifications(): Promise<{ notifications: WhatsAppNotification[] }> {
    const { data } = await api.get('/api/whatsapp/notifications')
    return data
  },

  async getStats(): Promise<WhatsAppStats> {
    const { data } = await api.get('/api/whatsapp/stats')
    return data
  },

  // Debug endpoints
  async debugBridgeTest(): Promise<any> {
    const { data } = await api.get('/api/whatsapp/debug/bridge-test')
    return data
  },

  async debugConnectionInfo(): Promise<any> {
    const { data } = await api.get('/api/whatsapp/debug/connection-info')
    return data
  }
}

export const sendWhatsAppMessage = whatsappService.sendMessage
export const getWhatsAppStatus = whatsappService.getStatus
export const sendBulkReminder = whatsappService.sendBulkReminder
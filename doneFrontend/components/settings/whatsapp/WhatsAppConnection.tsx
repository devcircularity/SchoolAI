// components/whatsapp/WhatsAppConnection.tsx - Fixed QR code handling
'use client'

import { useState, useEffect, useRef } from 'react'
import { whatsappService } from '@/services/whatsapp'

interface WhatsAppConnectionProps {
  schoolId: string
}

export default function WhatsAppConnection({ schoolId }: WhatsAppConnectionProps) {
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'scanning' | 'connected' | 'error'>('disconnected')
  const [qrCode, setQrCode] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<any>(null)
  const [debugInfo, setDebugInfo] = useState<any>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (schoolId) {
      checkConnectionStatus()
    }
  }, [schoolId])

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  const checkConnectionStatus = async () => {
    try {
      console.log('Checking connection status...')
      const statusResult = await whatsappService.getStatus()
      console.log('Status result:', statusResult)
      
      if (statusResult.connected && statusResult.ready) {
        setStatus('connected')
        loadStats()
      } else if (statusResult.status === 'waiting_for_scan') {
        setStatus('disconnected') // Show as disconnected, user needs to initiate
      } else {
        setStatus('disconnected')
      }
    } catch (error) {
      console.error('Failed to check WhatsApp status:', error)
      setStatus('error')
      setError('Failed to check connection status')
    }
  }

  const loadStats = async () => {
    try {
      const statsResult = await whatsappService.getStats()
      setStats(statsResult)
    } catch (error) {
      console.error('Failed to load WhatsApp stats:', error)
    }
  }

  const loadDebugInfo = async () => {
    try {
      const debugResult = await whatsappService.debugBridgeTest()
      setDebugInfo(debugResult)
      console.log('Debug info:', debugResult)
    } catch (error) {
      console.error('Failed to load debug info:', error)
    }
  }

  const initiateConnection = async () => {
    try {
      console.log('=== STARTING CONNECTION PROCESS ===')
      setStatus('connecting')
      setError(null)
      setQrCode(null)
      
      // Load debug info first
      await loadDebugInfo()
      
      // Initiate connection and get QR code
      const result = await whatsappService.initiateConnection()
      console.log('Initiation result:', result)
      
      if (result.error) {
        if (result.error.includes('already connected')) {
          // If already connected, check status
          await checkConnectionStatus()
          return
        }
        throw new Error(result.error)
      }
      
      if (result.qr_code) {
        console.log(`QR code received (${result.qr_code.length} characters)`)
        setQrCode(result.qr_code)
        setStatus('scanning')
        
        // Start polling for connection status
        startConnectionPolling()
      } else {
        throw new Error('No QR code received from server')
      }
    } catch (error: any) {
      console.error('=== CONNECTION INITIATION FAILED ===')
      console.error('Error:', error)
      setStatus('error')
      setError(error.message || 'Failed to initiate connection')
    }
  }

  const startConnectionPolling = () => {
    console.log('Starting connection polling...')
    
    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
    
    // Poll for connection status every 3 seconds
    intervalRef.current = setInterval(async () => {
      try {
        console.log('Polling connection status...')
        const statusResult = await whatsappService.checkConnection()
        console.log('Poll result:', statusResult)
        
        if (statusResult.connected && statusResult.ready) {
          console.log('Connection established!')
          setStatus('connected')
          setQrCode(null)
          loadStats()
          
          if (intervalRef.current) {
            clearInterval(intervalRef.current)
            intervalRef.current = null
          }
        }
      } catch (error) {
        console.error('Status poll failed:', error)
      }
    }, 3000)
    
    // Stop polling after 2 minutes
    setTimeout(() => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
        
        if (status === 'scanning') {
          setStatus('error')
          setError('Connection timeout. QR code may have expired. Please try again.')
          setQrCode(null)
        }
      }
    }, 120000)
  }

  const retryQRCode = async () => {
    try {
      setError(null)
      console.log('Retrying QR code fetch...')
      
      const qrResult = await whatsappService.getQRCode()
      console.log('QR retry result:', qrResult)
      
      if (qrResult.success && qrResult.qr_code) {
        setQrCode(qrResult.qr_code)
        setStatus('scanning')
        startConnectionPolling()
      } else {
        throw new Error(qrResult.message || 'Failed to get QR code')
      }
    } catch (error: any) {
      setError(error.message || 'Failed to retry QR code')
    }
  }

  const disconnect = async () => {
    try {
      await whatsappService.disconnect()
      setStatus('disconnected')
      setStats(null)
      setQrCode(null)
      setError(null)
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    } catch (error: any) {
      setError(error.message || 'Failed to disconnect')
    }
  }

  const testMessage = async () => {
    try {
      const testPhoneNumber = '+254714179051'
      const testMessageText = `Test message from School Management System - ${new Date().toLocaleTimeString()}`
      
      console.log('=== SENDING TEST MESSAGE ===')
      console.log('Phone:', testPhoneNumber)
      console.log('Message:', testMessageText)
      console.log('School ID:', schoolId)
      
      const result = await whatsappService.sendMessage(testPhoneNumber, testMessageText)
      console.log('Result:', result)
      
      if (result.success) {
        alert('Test message sent successfully!')
      } else {
        throw new Error(result.error || 'Message send failed')
      }
    } catch (error: any) {
      console.error('=== TEST MESSAGE ERROR ===')
      console.error('Error:', error)
      
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error'
      alert(`Failed to send test message: ${errorMessage}`)
    }
  }

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className={`p-4 rounded-xl border ${getStatusStyles(status)}`}>
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.890-5.335 11.893-11.893A11.821 11.821 0 0020.885 3.486"/>
            </svg>
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-neutral-900 dark:text-neutral-100">
                WhatsApp Business Connection
              </h4>
              <div className="flex items-center gap-2">
                <StatusIndicator status={status} />
                <span className="text-sm font-medium capitalize">
                  {status === 'disconnected' ? 'Not Connected' : status}
                </span>
              </div>
            </div>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
              Connect your WhatsApp Business account to send automated notifications to parents
            </p>
            
            {status === 'connected' && stats && (
              <div className="grid grid-cols-3 gap-4 mb-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="text-center">
                  <div className="font-semibold text-green-800 dark:text-green-200">
                    {stats.total_sent || 0}
                  </div>
                  <div className="text-xs text-green-600 dark:text-green-300">
                    Messages Sent
                  </div>
                </div>
                <div className="text-center">
                  <div className="font-semibold text-green-800 dark:text-green-200">
                    {stats.by_type?.length || 0}
                  </div>
                  <div className="text-xs text-green-600 dark:text-green-300">
                    Message Types
                  </div>
                </div>
                <div className="text-center">
                  <div className="font-semibold text-green-800 dark:text-green-200">
                    Active
                  </div>
                  <div className="text-xs text-green-600 dark:text-green-300">
                    Status
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                {status === 'error' && (
                  <button
                    onClick={retryQRCode}
                    className="mt-2 text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200 underline"
                  >
                    Retry QR Code
                  </button>
                )}
              </div>
            )}

            {/* Debug Information */}
            {debugInfo && (
              <details className="mb-4 p-3 bg-neutral-50 dark:bg-neutral-900/50 rounded-lg">
                <summary className="text-sm font-medium text-neutral-700 dark:text-neutral-300 cursor-pointer">
                  Debug Information
                </summary>
                <pre className="mt-2 text-xs text-neutral-600 dark:text-neutral-400 overflow-x-auto">
                  {JSON.stringify(debugInfo, null, 2)}
                </pre>
              </details>
            )}
          </div>
        </div>
      </div>

      {/* QR Code Display */}
      {status === 'scanning' && qrCode && (
        <div className="text-center p-6 bg-white dark:bg-neutral-900 border-2 border-dashed border-neutral-300 dark:border-neutral-600 rounded-xl">
          <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-4">
            Scan QR Code with WhatsApp
          </h4>
          <div className="inline-block p-4 bg-white rounded-xl shadow-lg">
            {qrCode.startsWith('data:image') ? (
              <img 
                src={qrCode} 
                alt="WhatsApp QR Code"
                className="w-64 h-64"
                onError={() => {
                  console.error('QR code image failed to load')
                  setError('QR code image failed to load')
                }}
              />
            ) : qrCode.startsWith('<svg') ? (
              <div
                dangerouslySetInnerHTML={{ __html: qrCode }}
                className="w-64 h-64 flex items-center justify-center"
              />
            ) : (
              <div className="w-64 h-64 flex items-center justify-center bg-neutral-100 p-4 rounded">
                <div className="text-xs font-mono break-all text-center text-neutral-700">
                  QR Code: {qrCode.substring(0, 100)}...
                </div>
              </div>
            )}
          </div>
          <div className="mt-4 space-y-2 text-sm text-neutral-600 dark:text-neutral-400">
            <p>1. Open WhatsApp on your phone</p>
            <p>2. Go to Settings → Linked Devices</p>
            <p>3. Tap "Link a Device" and scan this code</p>
          </div>
          <div className="mt-4">
            <div className="flex items-center justify-center gap-2 text-sm text-neutral-500">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-500"></div>
              Waiting for scan...
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        {status === 'disconnected' && (
          <button
            onClick={initiateConnection}
            className="btn-primary"
          >
            Connect WhatsApp Web
          </button>
        )}
        
        {status === 'connecting' && (
          <button disabled className="btn-primary opacity-50 cursor-not-allowed">
            Connecting...
          </button>
        )}
        
        {status === 'scanning' && (
          <>
            <button
              onClick={retryQRCode}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Refresh QR Code
            </button>
            <button
              onClick={() => {
                setStatus('disconnected')
                setQrCode(null)
                setError(null)
                if (intervalRef.current) {
                  clearInterval(intervalRef.current)
                  intervalRef.current = null
                }
              }}
              className="px-4 py-2 bg-neutral-200 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded-lg hover:bg-neutral-300 dark:hover:bg-neutral-600 transition-colors"
            >
              Cancel
            </button>
          </>
        )}
        
        {status === 'connected' && (
          <>
            <button
              onClick={testMessage}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Send Test Message
            </button>
            <button
              onClick={disconnect}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Disconnect
            </button>
          </>
        )}
        
        {status === 'error' && (
          <button
            onClick={() => {
              setStatus('disconnected')
              setError(null)
              setQrCode(null)
            }}
            className="btn-primary"
          >
            Try Again
          </button>
        )}

        {/* Debug Button */}
        <button
          onClick={loadDebugInfo}
          className="px-3 py-2 text-sm bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
        >
          Debug
        </button>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <FeatureCard
          title="Fee Reminders"
          description="Automatically send payment reminders to parents via WhatsApp"
          enabled={status === 'connected'}
        />
        <FeatureCard
          title="Attendance Alerts"
          description="Notify parents when students are absent or late"
          enabled={status === 'connected'}
        />
        <FeatureCard
          title="School Announcements"
          description="Broadcast important school news and events to all parents"
          enabled={status === 'connected'}
        />
        <FeatureCard
          title="Report Cards"
          description="Share student progress reports directly with parents"
          enabled={status === 'connected'}
        />
      </div>
    </div>
  )
}

function getStatusStyles(status: string) {
  switch (status) {
    case 'connected':
      return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
    case 'scanning':
    case 'connecting':
      return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
    case 'error':
      return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
    default:
      return 'bg-neutral-50 dark:bg-neutral-900/20 border-neutral-200 dark:border-neutral-700'
  }
}

function StatusIndicator({ status }: { status: string }) {
  switch (status) {
    case 'connected':
      return <div className="w-2 h-2 bg-green-500 rounded-full"></div>
    case 'scanning':
    case 'connecting':
      return <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
    case 'error':
      return <div className="w-2 h-2 bg-red-500 rounded-full"></div>
    default:
      return <div className="w-2 h-2 bg-neutral-400 rounded-full"></div>
  }
}

function FeatureCard({ title, description, enabled }: { title: string, description: string, enabled: boolean }) {
  return (
    <div className={`p-4 border border-neutral-200 dark:border-neutral-700 rounded-xl ${!enabled ? 'opacity-50' : ''}`}>
      <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-2">
        {title}
        {!enabled && (
          <span className="text-xs bg-neutral-200 dark:bg-neutral-700 px-2 py-1 rounded">
            Requires Connection
          </span>
        )}
      </h4>
      <p className="text-sm text-neutral-600 dark:text-neutral-400">
        {description}
      </p>
    </div>
  )
}
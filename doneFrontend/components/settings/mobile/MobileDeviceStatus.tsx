'use client'

import { useState, useEffect } from 'react'
import { schoolService } from '@/services/schools'
import { 
  Smartphone, 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  RefreshCw, 
  Trash2,
  Clock,
  Wifi,
  WifiOff,
  MessageSquare
} from 'lucide-react'

type MobileDeviceStatusProps = {
  schoolId: string
}

type DeviceStatus = {
  device_id: string
  app_version?: string
  device_model?: string
  android_version?: string
  notification_access: boolean
  sms_permission: boolean
  listener_connected: boolean
  last_forward_ok: boolean
  last_error?: string
  network_status?: string
  battery_optimized?: boolean
  last_sms_received_at?: string
  first_seen_at: string
  last_update_at: string
  last_heartbeat_at: string
  is_online: boolean
  is_healthy: boolean
  status_summary: 'connected' | 'issues' | 'offline'
}

export default function MobileDeviceStatus({ schoolId }: MobileDeviceStatusProps) {
  const [devices, setDevices] = useState<DeviceStatus[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [connectedCount, setConnectedCount] = useState(0)
  const [healthyCount, setHealthyCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadDevices = async () => {
    try {
      const response = await schoolService.getMobileDevices(schoolId)
      setDevices(response.devices)
      setTotalCount(response.total_count)
      setConnectedCount(response.connected_count)
      setHealthyCount(response.healthy_count)
      setError(null)
    } catch (err) {
      console.error('Failed to load mobile devices:', err)
      setError('Failed to load device status')
    }
  }

  const refreshStatus = async () => {
    setRefreshing(true)
    await loadDevices()
    setRefreshing(false)
  }

  const removeDevice = async (deviceId: string) => {
    try {
      await schoolService.removeMobileDevice(schoolId, deviceId)
      await loadDevices() // Reload after removal
    } catch (err) {
      console.error('Failed to remove device:', err)
    }
  }

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      await loadDevices()
      setLoading(false)
    }

    if (schoolId) {
      load()
      
      // Auto-refresh every 2 minutes
      const interval = setInterval(loadDevices, 120000)
      return () => clearInterval(interval)
    }
  }, [schoolId])

  const getStatusBadge = (device: DeviceStatus) => {
    switch (device.status_summary) {
      case 'connected':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded-full">
            <CheckCircle size={12} />
            Connected
          </span>
        )
      case 'issues':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 rounded-full">
            <AlertTriangle size={12} />
            Issues
          </span>
        )
      case 'offline':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded-full">
            <XCircle size={12} />
            Offline
          </span>
        )
    }
  }

  const getIssuesList = (device: DeviceStatus) => {
    const issues = []
    if (!device.notification_access) issues.push('Notification access disabled')
    if (!device.sms_permission) issues.push('SMS permission missing')
    if (!device.listener_connected) issues.push('Listener disconnected')
    if (!device.last_forward_ok && device.last_error) issues.push(`Last forward failed: ${device.last_error}`)
    if (!device.is_online) issues.push('No heartbeat in last 5 minutes')
    return issues
  }

  const formatLastSeen = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffMinutes < 1) return 'Just now'
    if (diffMinutes < 60) return `${diffMinutes}m ago`
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`
    return `${Math.floor(diffMinutes / 1440)}d ago`
  }

  if (!schoolId) {
    return null
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100">
          SMS Forwarder Devices
        </h3>
        <button
          onClick={refreshStatus}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 border border-neutral-200 dark:border-neutral-700 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">Loading device status...</p>
        </div>
      ) : error ? (
        <div className="text-center py-8">
          <p className="text-red-600 dark:text-red-400">{error}</p>
          <button
            onClick={refreshStatus}
            className="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            Try again
          </button>
        </div>
      ) : devices.length === 0 ? (
        <div className="text-center py-8 border-2 border-dashed border-neutral-200 dark:border-neutral-700 rounded-xl">
          <Smartphone size={48} className="mx-auto text-neutral-400 mb-4" />
          <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-2">
            No mobile devices connected
          </h4>
          <p className="text-neutral-600 dark:text-neutral-400 max-w-md mx-auto">
            Install the Olaji Helper Android app and log in to see your SMS forwarder devices here.
          </p>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div className="bg-neutral-50 dark:bg-neutral-900 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">Total Devices</p>
                  <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">{totalCount}</p>
                </div>
                <Smartphone size={24} className="text-neutral-400" />
              </div>
            </div>
            
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-green-600 dark:text-green-400">Connected</p>
                  <p className="text-2xl font-bold text-green-700 dark:text-green-300">{healthyCount}</p>
                </div>
                <CheckCircle size={24} className="text-green-500" />
              </div>
            </div>
            
            <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-yellow-600 dark:text-yellow-400">With Issues</p>
                  <p className="text-2xl font-bold text-yellow-700 dark:text-yellow-300">{totalCount - healthyCount}</p>
                </div>
                <AlertTriangle size={24} className="text-yellow-500" />
              </div>
            </div>
          </div>

          {/* Device List */}
          <div className="space-y-3">
            {devices.map((device) => {
              const issues = getIssuesList(device)
              
              return (
                <div
                  key={device.device_id}
                  className="border border-neutral-200 dark:border-neutral-700 rounded-xl p-4 hover:border-neutral-300 dark:hover:border-neutral-600 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-neutral-100 dark:bg-neutral-800 rounded-lg">
                        <Smartphone size={20} className="text-neutral-600 dark:text-neutral-400" />
                      </div>
                      
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-neutral-900 dark:text-neutral-100">
                            {device.device_model || device.device_id}
                          </h4>
                          {getStatusBadge(device)}
                        </div>
                        
                        <div className="flex items-center gap-4 text-sm text-neutral-600 dark:text-neutral-400 mb-2">
                          <span>ID: {device.device_id}</span>
                          {device.app_version && (
                            <span>v{device.app_version}</span>
                          )}
                          <span className="flex items-center gap-1">
                            <Clock size={12} />
                            Last seen {formatLastSeen(device.last_heartbeat_at)}
                          </span>
                        </div>

                        {/* Permissions Status */}
                        <div className="flex items-center gap-3 text-xs mb-2">
                          <div className={`flex items-center gap-1 ${device.notification_access ? 'text-green-600' : 'text-red-600'}`}>
                            {device.notification_access ? <CheckCircle size={12} /> : <XCircle size={12} />}
                            Notifications
                          </div>
                          <div className={`flex items-center gap-1 ${device.sms_permission ? 'text-green-600' : 'text-red-600'}`}>
                            {device.sms_permission ? <CheckCircle size={12} /> : <XCircle size={12} />}
                            SMS
                          </div>
                          <div className={`flex items-center gap-1 ${device.listener_connected ? 'text-green-600' : 'text-red-600'}`}>
                            {device.listener_connected ? <Wifi size={12} /> : <WifiOff size={12} />}
                            Listener
                          </div>
                          {device.last_sms_received_at && (
                            <div className="flex items-center gap-1 text-blue-600">
                              <MessageSquare size={12} />
                              Last SMS {formatLastSeen(device.last_sms_received_at)}
                            </div>
                          )}
                        </div>

                        {/* Issues */}
                        {issues.length > 0 && (
                          <div className="mt-2">
                            <ul className="text-sm text-red-600 dark:text-red-400 space-y-1">
                              {issues.map((issue, index) => (
                                <li key={index} className="flex items-center gap-1">
                                  <span className="w-1 h-1 bg-red-500 rounded-full flex-shrink-0"></span>
                                  {issue}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <button
                      onClick={() => removeDevice(device.device_id)}
                      className="p-1.5 text-neutral-400 hover:text-red-600 dark:hover:text-red-400 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
                      title="Remove device"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}

      <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-4">
        Device status updates automatically every 2 minutes. 
        Devices are considered "Connected" when they report within the last 5 minutes with all permissions granted.
      </div>
    </div>
  )
}
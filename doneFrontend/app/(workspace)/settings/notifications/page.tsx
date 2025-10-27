// app/settings/notifications/page.tsx
'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import SettingsLayout from '@/components/settings/SettingsLayout'

type NotificationSetting = {
  id: string
  title: string
  description: string
  enabled: boolean
  category: 'email' | 'push' | 'sms'
}

export default function NotificationsSettings() {
  const { isAuthenticated } = useAuth()
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState(false)
  
  const [notifications, setNotifications] = useState<NotificationSetting[]>([
    // Email Notifications
    {
      id: 'email-student-updates',
      title: 'Student Updates',
      description: 'Get notified when student records are updated or new students are enrolled',
      enabled: true,
      category: 'email'
    },
    {
      id: 'email-fee-reminders',
      title: 'Fee Reminders',
      description: 'Receive notifications about upcoming fee payments and overdue accounts',
      enabled: true,
      category: 'email'
    },
    {
      id: 'email-system-updates',
      title: 'System Updates',
      description: 'Get notified about system maintenance, new features, and important updates',
      enabled: false,
      category: 'email'
    },
    {
      id: 'email-weekly-reports',
      title: 'Weekly Reports',
      description: 'Receive weekly summary reports of school activities and statistics',
      enabled: true,
      category: 'email'
    },
    
    // Push Notifications
    {
      id: 'push-chat-messages',
      title: 'Chat Messages',
      description: 'Get instant notifications for new chat messages and responses',
      enabled: true,
      category: 'push'
    },
    {
      id: 'push-urgent-alerts',
      title: 'Urgent Alerts',
      description: 'Receive immediate notifications for critical school matters',
      enabled: true,
      category: 'push'
    },
    {
      id: 'push-class-updates',
      title: 'Class Updates',
      description: 'Get notified about class schedule changes and announcements',
      enabled: false,
      category: 'push'
    },
    
    // SMS Notifications
    {
      id: 'sms-security-alerts',
      title: 'Security Alerts',
      description: 'Receive SMS notifications for login attempts and security events',
      enabled: true,
      category: 'sms'
    },
    {
      id: 'sms-payment-confirmations',
      title: 'Payment Confirmations',
      description: 'Get SMS confirmations when payments are received',
      enabled: false,
      category: 'sms'
    }
  ])

  const toggleNotification = (id: string) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === id
          ? { ...notification, enabled: !notification.enabled }
          : notification
      )
    )
  }

  const handleSave = async () => {
    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (error) {
      console.error('Failed to save notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const getCategoryNotifications = (category: 'email' | 'push' | 'sms') => {
    return notifications.filter(n => n.category === category)
  }

  const getCategoryTitle = (category: 'email' | 'push' | 'sms') => {
    switch (category) {
      case 'email': return 'Email Notifications'
      case 'push': return 'Push Notifications'
      case 'sms': return 'SMS Notifications'
    }
  }

  const getCategoryDescription = (category: 'email' | 'push' | 'sms') => {
    switch (category) {
      case 'email': return 'Receive notifications via email'
      case 'push': return 'Get browser and mobile push notifications'
      case 'sms': return 'Receive text message notifications'
    }
  }

  if (!isAuthenticated) {
    return (
      <SettingsLayout>
        <div className="text-center py-8">
          <p className="text-neutral-600 dark:text-neutral-400">
            Please log in to access your notification settings.
          </p>
        </div>
      </SettingsLayout>
    )
  }

  return (
    <SettingsLayout>
      <div className="space-y-8">
        <div>
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
            Notifications
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            Choose what notifications you want to receive and how
          </p>
        </div>

        {/* Email Notifications */}
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100">
              {getCategoryTitle('email')}
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              {getCategoryDescription('email')}
            </p>
          </div>
          
          <div className="space-y-3">
            {getCategoryNotifications('email').map((notification) => (
              <div
                key={notification.id}
                className="flex items-start justify-between p-4 border border-neutral-200 dark:border-neutral-700 rounded-xl"
              >
                <div className="flex-1">
                  <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                    {notification.title}
                  </h4>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {notification.description}
                  </p>
                </div>
                
                <label className="relative inline-flex items-center cursor-pointer ml-4">
                  <input
                    type="checkbox"
                    checked={notification.enabled}
                    onChange={() => toggleNotification(notification.id)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-neutral-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-neutral-600 peer-checked:bg-blue-600"></div>
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Push Notifications */}
        <div className="space-y-4 border-t border-neutral-200 dark:border-neutral-700 pt-8">
          <div>
            <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100">
              {getCategoryTitle('push')}
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              {getCategoryDescription('push')}
            </p>
          </div>
          
          <div className="space-y-3">
            {getCategoryNotifications('push').map((notification) => (
              <div
                key={notification.id}
                className="flex items-start justify-between p-4 border border-neutral-200 dark:border-neutral-700 rounded-xl"
              >
                <div className="flex-1">
                  <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                    {notification.title}
                  </h4>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {notification.description}
                  </p>
                </div>
                
                <label className="relative inline-flex items-center cursor-pointer ml-4">
                  <input
                    type="checkbox"
                    checked={notification.enabled}
                    onChange={() => toggleNotification(notification.id)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-neutral-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-neutral-600 peer-checked:bg-blue-600"></div>
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* SMS Notifications */}
        <div className="space-y-4 border-t border-neutral-200 dark:border-neutral-700 pt-8">
          <div>
            <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100">
              {getCategoryTitle('sms')}
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              {getCategoryDescription('sms')}
            </p>
          </div>
          
          <div className="space-y-3">
            {getCategoryNotifications('sms').map((notification) => (
              <div
                key={notification.id}
                className="flex items-start justify-between p-4 border border-neutral-200 dark:border-neutral-700 rounded-xl"
              >
                <div className="flex-1">
                  <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                    {notification.title}
                  </h4>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {notification.description}
                  </p>
                </div>
                
                <label className="relative inline-flex items-center cursor-pointer ml-4">
                  <input
                    type="checkbox"
                    checked={notification.enabled}
                    onChange={() => toggleNotification(notification.id)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-neutral-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-neutral-600 peer-checked:bg-blue-600"></div>
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center gap-4 pt-4 border-t border-neutral-200 dark:border-neutral-700">
          <button
            onClick={handleSave}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Saving...' : 'Save Preferences'}
          </button>
          
          {saved && (
            <span className="text-green-600 dark:text-green-400 text-sm font-medium">
              Notification preferences saved!
            </span>
          )}
        </div>
      </div>
    </SettingsLayout>
  )
}
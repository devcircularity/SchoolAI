// app/settings/profile/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import SettingsLayout from '@/components/settings/SettingsLayout'

// Reuse the JWT decoding logic
function decodeJwt(token?: string) {
  if (!token) return null
  try {
    const base = token.split('.')[1]?.replace(/-/g, '+').replace(/_/g, '/')
    const json = atob(base)
    return JSON.parse(json) as { 
      email?: string
      full_name?: string
      active_school_id?: number | string
    }
  } catch { 
    return null 
  }
}

export default function ProfileSettings() {
  const { token, isAuthenticated } = useAuth()
  const [fullName, setFullName] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [workFunction, setWorkFunction] = useState('')
  const [personalPreferences, setPersonalPreferences] = useState('')
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState(false)

  // Load current user data from token
  useEffect(() => {
    if (token) {
      const claims = decodeJwt(token)
      if (claims) {
        setFullName(claims.full_name || '')
        setDisplayName(claims.full_name || '')
      }
    }
  }, [token])

  const handleSave = async () => {
    setLoading(true)
    
    // Simulate API call
    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (error) {
      console.error('Failed to save profile:', error)
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <SettingsLayout>
        <div className="text-center py-8">
          <p className="text-neutral-600 dark:text-neutral-400">
            Please log in to access your profile settings.
          </p>
        </div>
      </SettingsLayout>
    )
  }

  return (
    <SettingsLayout>
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
            Profile
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            Update your personal information and preferences
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Full Name */}
          <div>
            <label className="label">Full name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="input"
              placeholder="Enter your full name"
            />
          </div>

          {/* Display Name */}
          <div>
            <label className="label">What should Olaji call you?</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="input"
              placeholder="Enter your preferred name"
            />
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center gap-4 pt-4">
          <button
            onClick={handleSave}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
          
          {saved && (
            <span className="text-green-600 dark:text-green-400 text-sm font-medium">
              Changes saved successfully!
            </span>
          )}
        </div>
      </div>
    </SettingsLayout>
  )
}
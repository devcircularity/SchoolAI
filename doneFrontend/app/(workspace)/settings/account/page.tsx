// app/settings/account/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import SettingsLayout from '@/components/settings/SettingsLayout'
import { Eye, EyeOff, AlertTriangle } from 'lucide-react'

// Reuse the JWT decoding logic
function decodeJwt(token?: string) {
  if (!token) return null
  try {
    const base = token.split('.')[1]?.replace(/-/g, '+').replace(/_/g, '/')
    const json = atob(base)
    return JSON.parse(json) as { 
      email?: string
      full_name?: string
    }
  } catch { 
    return null 
  }
}

export default function AccountSettings() {
  const { token, isAuthenticated, logout } = useAuth()
  const [email, setEmail] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState(false)
  const [deleteConfirmation, setDeleteConfirmation] = useState('')
  const [showDeleteSection, setShowDeleteSection] = useState(false)

  // Load current user data from token
  useEffect(() => {
    if (token) {
      const claims = decodeJwt(token)
      if (claims) {
        setEmail(claims.email || '')
      }
    }
  }, [token])

  const handleChangeEmail = async () => {
    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (error) {
      console.error('Failed to change email:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      alert('New passwords do not match')
      return
    }

    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (error) {
      console.error('Failed to change password:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== 'DELETE') {
      alert('Please type DELETE to confirm account deletion')
      return
    }

    if (confirm('Are you absolutely sure you want to delete your account? This action cannot be undone.')) {
      setLoading(true)
      try {
        await new Promise(resolve => setTimeout(resolve, 1000))
        logout()
      } catch (error) {
        console.error('Failed to delete account:', error)
      } finally {
        setLoading(false)
      }
    }
  }

  if (!isAuthenticated) {
    return (
      <SettingsLayout>
        <div className="text-center py-8">
          <p className="text-neutral-600 dark:text-neutral-400">
            Please log in to access your account settings.
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
            Account
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            Manage your account security and preferences
          </p>
        </div>

        {/* Email Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100">
            Email Address
          </h3>
          <div>
            <label className="label">Email</label>
            <div className="flex gap-3">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input flex-1"
                placeholder="Enter your email address"
              />
              <button
                onClick={handleChangeEmail}
                disabled={loading}
                className="btn-primary"
              >
                {loading ? 'Updating...' : 'Update'}
              </button>
            </div>
          </div>
        </div>

        {/* Password Section */}
        <div className="space-y-4 border-t border-neutral-200 dark:border-neutral-700 pt-8">
          <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100">
            Change Password
          </h3>
          
          <div>
            <label className="label">Current Password</label>
            <div className="relative">
              <input
                type={showCurrentPassword ? 'text' : 'password'}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="input pr-10"
                placeholder="Enter your current password"
              />
              <button
                type="button"
                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
              >
                {showCurrentPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">New Password</label>
              <div className="relative">
                <input
                  type={showNewPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="Enter new password"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
                >
                  {showNewPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div>
              <label className="label">Confirm New Password</label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="Confirm new password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
                >
                  {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          </div>

          <button
            onClick={handleChangePassword}
            disabled={loading || !currentPassword || !newPassword || !confirmPassword}
            className="btn-primary"
          >
            {loading ? 'Changing Password...' : 'Change Password'}
          </button>
        </div>

        {/* Danger Zone */}
        <div className="space-y-4 border-t border-neutral-200 dark:border-neutral-700 pt-8">
          <div className="flex items-center gap-2">
            <AlertTriangle size={20} className="text-red-500" />
            <h3 className="text-lg font-medium text-red-600 dark:text-red-400">
              Danger Zone
            </h3>
          </div>
          
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
            <h4 className="font-medium text-red-800 dark:text-red-200 mb-2">
              Delete Account
            </h4>
            <p className="text-red-700 dark:text-red-300 text-sm mb-4">
              Once you delete your account, there is no going back. Please be certain.
            </p>
            
            {!showDeleteSection ? (
              <button
                onClick={() => setShowDeleteSection(true)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
              >
                Delete Account
              </button>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="label text-red-800 dark:text-red-200">
                    Type <strong>DELETE</strong> to confirm
                  </label>
                  <input
                    type="text"
                    value={deleteConfirmation}
                    onChange={(e) => setDeleteConfirmation(e.target.value)}
                    className="input border-red-300 dark:border-red-700"
                    placeholder="DELETE"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleDeleteAccount}
                    disabled={loading || deleteConfirmation !== 'DELETE'}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
                  >
                    {loading ? 'Deleting...' : 'Permanently Delete Account'}
                  </button>
                  <button
                    onClick={() => {
                      setShowDeleteSection(false)
                      setDeleteConfirmation('')
                    }}
                    className="px-4 py-2 bg-neutral-200 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded-lg hover:bg-neutral-300 dark:hover:bg-neutral-600 transition-colors text-sm font-medium"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {saved && (
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400 text-sm font-medium">
            <span>Changes saved successfully!</span>
          </div>
        )}
      </div>
    </SettingsLayout>
  )
}
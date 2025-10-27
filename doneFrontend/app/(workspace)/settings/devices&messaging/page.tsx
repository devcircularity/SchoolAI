'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import SettingsLayout from '@/components/settings/SettingsLayout'
import WhatsAppConnection from '@/components/settings/whatsapp/WhatsAppConnection'
import MobileDeviceStatus from '@/components/settings/mobile/MobileDeviceStatus'
import { schoolService } from '@/services/schools'
import { ExternalLink, Plus } from 'lucide-react'

// Reuse the JWT decoding logic
function decodeJwt(token?: string) {
  if (!token) return null
  try {
    const base = token.split('.')[1]?.replace(/-/g, '+').replace(/_/g, '/')
    const json = atob(base)
    return JSON.parse(json) as { 
      email?: string
      full_name?: string
      active_school_id?: string
    }
  } catch { 
    return null 
  }
}

type SchoolInfo = {
  id: string
  name: string
  role: string
}

export default function SchoolSettings() {
  const { token, isAuthenticated, active_school_id, setSchoolId } = useAuth()
  const [schools, setSchools] = useState<SchoolInfo[]>([])
  const [currentSchool, setCurrentSchool] = useState<SchoolInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [switchingSchool, setSwitchingSchool] = useState<string | null>(null)

  // Load user's schools
  useEffect(() => {
    const loadSchools = async () => {
      if (!isAuthenticated) return
      
      try {
        setLoading(true)
        const userSchools = await schoolService.mine()
        setSchools(userSchools)
        
        // Find current active school
        const activeSchool = userSchools.find(school => school.id === active_school_id)
        setCurrentSchool(activeSchool || null)
      } catch (error) {
        console.error('Failed to load schools:', error)
      } finally {
        setLoading(false)
      }
    }

    loadSchools()
  }, [isAuthenticated, active_school_id])

  const handleSwitchSchool = async (schoolId: string) => {
    setSwitchingSchool(schoolId)
    try {
      setSchoolId(schoolId)
      const newCurrentSchool = schools.find(school => school.id === schoolId)
      setCurrentSchool(newCurrentSchool || null)
    } catch (error) {
      console.error('Failed to switch school:', error)
    } finally {
      setSwitchingSchool(null)
    }
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role.toUpperCase()) {
      case 'OWNER':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'ADMIN':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
      case 'TEACHER':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      default:
        return 'bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200'
    }
  }

  if (!isAuthenticated) {
    return (
      <SettingsLayout title="Settings" subtitle="Manage your account and preferences">
        <div className="text-center py-8">
          <p className="text-neutral-600 dark:text-neutral-400">
            Please log in to access your school settings.
          </p>
        </div>
      </SettingsLayout>
    )
  }

  if (loading) {
    return (
      <SettingsLayout title="Settings" subtitle="Manage your account and preferences">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">Loading schools...</p>
        </div>
      </SettingsLayout>
    )
  }

  const settingsTitle = currentSchool ? currentSchool.name : 'Settings'
  const settingsSubtitle = currentSchool ? 'Manage your school settings and preferences' : 'Manage your account and preferences'

  return (
    <SettingsLayout title={settingsTitle} subtitle={settingsSubtitle}>
      <div className="space-y-8">


        {/* SMS Mobile Devices - Only show for current school */}
        {currentSchool && (
          <div className="border-t border-neutral-200 dark:border-neutral-700 pt-6">
            <MobileDeviceStatus schoolId={currentSchool.id} />
          </div>
        )}

        {/* WhatsApp Integration */}
        {currentSchool && (
          <div className="border-t border-neutral-200 dark:border-neutral-700 pt-6">
            <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-4">
              WhatsApp Integration
            </h3>
            <WhatsAppConnection schoolId={currentSchool.id} />
          </div>
        )}

      </div>
    </SettingsLayout>
  )
}
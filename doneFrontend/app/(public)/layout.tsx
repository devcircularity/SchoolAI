// app/(public)/layout.tsx - Layout for public routes with auth guard
'use client'

import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { isAuthenticated, isLoading, active_school_id } = useAuth()

  useEffect(() => {
    if (isLoading) return // Wait for auth check

    // Redirect authenticated users away from public routes
    if (isAuthenticated) {
      if (active_school_id) {
        router.replace('/workspace')
      } else {
        router.replace('/onboarding/school')
      }
    }
  }, [isAuthenticated, isLoading, active_school_id, router])

  // Show loading while checking auth
  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-semibold mb-2">Loading...</div>
          <div className="text-neutral-600 dark:text-neutral-400">Checking authentication...</div>
        </div>
      </div>
    )
  }

  // Show redirecting message if authenticated
  if (isAuthenticated) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-semibold mb-2">Redirecting...</div>
          <div className="text-neutral-600 dark:text-neutral-400">Taking you to your workspace...</div>
        </div>
      </div>
    )
  }

  // Only render children for unauthenticated users
  return <>{children}</>
}
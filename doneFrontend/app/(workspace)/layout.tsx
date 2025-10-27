// app/(workspace)/layout.tsx
'use client'

import React from 'react'
import WorkspaceShell from '@/components/layout/WorkspaceShell'
import { useAuthGuard } from '@/hooks/useAuthGuard'

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthGuard()

  // Show loading while checking authentication
  if (isLoading) {
    return (
      <div className="h-svh flex items-center justify-center">
        <div className="text-neutral-500">Loading...</div>
      </div>
    )
  }

  // Show redirecting message while redirecting to public
  if (!isAuthenticated) {
    return (
      <div className="h-svh flex items-center justify-center">
        <div className="text-neutral-500">Redirecting...</div> {/* Removed "to login" */}
      </div>
    )
  }

  return (
    <WorkspaceShell>
      {children}
    </WorkspaceShell>
  )
}
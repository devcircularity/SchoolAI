// hooks/useAuthGuard.ts
'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

export function useAuthGuard(redirectTo: string = '/public') { // Changed default from '/login' to '/public'
  const { token, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    // Don't redirect while still loading
    if (isLoading) return
    
    if (!token) {
      // Redirect to public instead of login with next parameter
      router.replace(redirectTo)
    }
  }, [token, isLoading, router, redirectTo])

  return { 
    isAuthenticated: !!token && !isLoading,
    isLoading 
  }
}
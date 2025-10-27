// contexts/AuthContext.tsx
'use client'
import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

type AuthState = { 
  token: string | null
  active_school_id: string | null
  isLoading: boolean // Add loading state
}

type AuthContextType = AuthState & {
  login: (data: { token: string }) => Promise<void>
  logout: () => void
  setSchoolId: (schoolId: string) => void
  isAuthenticated: boolean
}

const AuthCtx = createContext<AuthContextType>({
  token: null,
  active_school_id: null,
  isLoading: true,
  login: async () => {},
  logout: () => {},
  setSchoolId: () => {},
  isAuthenticated: false
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ 
    token: null, 
    active_school_id: null,
    isLoading: true // Start with loading true
  })
  const router = useRouter()

  useEffect(() => {
    // Load auth state from localStorage
    const token = localStorage.getItem('token')
    const sid = localStorage.getItem('active_school_id')
    
    setState({ 
      token, 
      active_school_id: sid,
      isLoading: false // Set loading to false after loading from localStorage
    })
  }, [])

  const login = async (data: { token: string }) => {
    localStorage.setItem('token', data.token)
    setState(prev => ({ ...prev, token: data.token, isLoading: false }))
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('active_school_id')
    setState({ token: null, active_school_id: null, isLoading: false })
    // Redirect to login page
    router.replace('/')
  }

  const setSchoolId = (schoolId: string) => {
    localStorage.setItem('active_school_id', schoolId)
    setState(prev => ({ ...prev, active_school_id: schoolId }))
  }

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    setSchoolId,
    isAuthenticated: !!state.token && !state.isLoading
  }

  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
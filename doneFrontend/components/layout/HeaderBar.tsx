'use client'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'
import { Menu } from 'lucide-react'
import UserControlsModal from './UserControlsModal'
import { SidebarBus } from './WorkspaceShell'

// Header title bus for dynamic title updates
type HeaderTitleCommand = { type: 'set', title: string, subtitle?: string } | { type: 'clear' }
type HeaderTitleListener = (cmd: HeaderTitleCommand) => void

const headerTitleListeners = new Set<HeaderTitleListener>()
export const HeaderTitleBus = {
  send(cmd: HeaderTitleCommand) { headerTitleListeners.forEach(l => l(cmd)) },
  on(l: HeaderTitleListener) { 
    headerTitleListeners.add(l); 
    return () => { 
      headerTitleListeners.delete(l) 
    } 
  }
}

function decodeJwt(token?: string) {
  if (!token) return null
  try {
    const base = token.split('.')[1]?.replace(/-/g, '+').replace(/_/g, '/')
    const json = atob(base)
    return JSON.parse(json) as { email?: string; full_name?: string; active_school_id?: number | string }
  } catch { return null }
}

function initialsFrom(name?: string, email?: string) {
  const n = (name || '').trim()
  if (n) {
    const parts = n.split(/\s+/).slice(0,2)
    return parts.map(p => p[0]?.toUpperCase() || '').join('') || 'U'
  }
  if (email) return email[0]?.toUpperCase() || 'U'
  return 'U'
}

export default function HeaderBar() {
  const { token, active_school_id, logout } = useAuth()
  const [openModal, setOpenModal] = useState(false)
  const [showTip, setShowTip] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [pageTitle, setPageTitle] = useState<string>('')
  const [pageSubtitle, setPageSubtitle] = useState<string>('')
  const tipRef = useRef<HTMLDivElement>(null)

  const claims = useMemo(() => decodeJwt(token || undefined), [token])
  const name = claims?.full_name
  const email = claims?.email
  const userLabel = name || email || 'Guest'
  const avatarTxt = initialsFrom(name, email)
  const schoolId = active_school_id ?? claims?.active_school_id

  // Check mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 1024 // lg breakpoint
      setIsMobile(mobile)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Listen for header title updates
  useEffect(() => {
    const unsubscribe = HeaderTitleBus.on((cmd) => {
      if (cmd.type === 'set') {
        setPageTitle(cmd.title)
        setPageSubtitle(cmd.subtitle || '')
      } else if (cmd.type === 'clear') {
        setPageTitle('')
        setPageSubtitle('')
      }
    })
    
    return unsubscribe
  }, [])

  // Hover tooltip hide on outside click
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (!tipRef.current) return
      if (!tipRef.current.contains(e.target as Node)) setShowTip(false)
    }
    document.addEventListener('click', onClick)
    return () => document.removeEventListener('click', onClick)
  }, [])

  const handleSidebarToggle = () => {
    SidebarBus.send({ type: 'toggle' })
  }

  return (
    <header className="flex items-center justify-between px-4 py-3 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
      {/* Left side - Hamburger menu and title */}
      <div className="flex items-center gap-3 min-w-0 flex-1">
        {isMobile && (
          <button
            onClick={handleSidebarToggle}
            className="p-2 -ml-2 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
            aria-label="Toggle sidebar"
          >
            <Menu size={20} className="text-neutral-600 dark:text-neutral-400" />
          </button>
        )}
        
        {/* Dynamic page title */}
        {pageTitle && (
          <div className="min-w-0 flex-1">
            <h1 className="text-base sm:text-lg font-semibold text-neutral-900 dark:text-neutral-100 truncate">
              {pageTitle}
            </h1>
            {pageSubtitle && (
              <p className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 truncate">
                {pageSubtitle}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Right side - User controls */}
      <div className="flex items-center flex-shrink-0">
        {!token ? (
          <div className="flex items-center gap-3 text-sm">
            <Link className="link-subtle" href="/login">Login</Link>
            <Link className="link-subtle" href="/signup">Sign up</Link>
          </div>
        ) : (
          <div className="relative" ref={tipRef}>
            {/* Enhanced Avatar with ring and shadow */}
            <button
              onMouseEnter={() => setShowTip(true)}
              onMouseLeave={() => setShowTip(false)}
              onClick={() => setOpenModal(true)}
              className="inline-flex h-10 w-10 items-center justify-center 
                         rounded-full bg-[--color-brand] text-white font-semibold text-sm
                         shadow-lg hover:shadow-xl
                         ring-2 ring-[--color-brand]/30 dark:ring-[--color-brand]/40
                         border-2 border-[--color-brand-light]/50
                         hover:scale-105 active:scale-95
                         transition-all duration-200 ease-out"
              aria-label="User menu"
              title={userLabel}
            >
              {avatarTxt}
            </button>

            {/* Hover tooltip (name + email) */}
            {showTip && (
              <div
                className="absolute right-0 mt-2 card px-3 py-2 text-xs min-w-[200px] z-50"
                onMouseEnter={() => setShowTip(true)}
                onMouseLeave={() => setShowTip(false)}
              >
                <div className="font-medium truncate">{userLabel}</div>
                {email && <div className="text-neutral-600 dark:text-neutral-400 truncate">{email}</div>}
              </div>
            )}

            {/* Controls modal on click */}
            <UserControlsModal
              open={openModal}
              onClose={() => setOpenModal(false)}
              onLogout={logout}
              userLabel={userLabel}
              email={email || undefined}
              schoolId={schoolId as any}
            />
          </div>
        )}
      </div>
    </header>
  )
}
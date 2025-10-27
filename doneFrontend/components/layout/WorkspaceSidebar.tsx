// components/layout/WorkspaceSidebar - Enhanced with auto-collapse on navigation and reduced spacing
'use client'

import { useEffect, useState, useMemo, useRef, useCallback } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { chatService, type Conversation } from '@/services/chats'
import { useAuth } from '@/contexts/AuthContext'
import { useAutoRefreshChats } from '@/hooks/useChatSync'
import Link from 'next/link'
import { Plus, ChevronLeft, LogOut, Settings, Star, RefreshCw, GraduationCap } from 'lucide-react'
import Logo, { LogoIcon } from "@/components/ui/Logo"
import ChatOptionsMenu from '@/components/chat/ChatOptionsMenu'

// Reuse the same JWT decoding logic from HeaderBar
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

// Updated interface to match backend structure
interface Chat {
  id: string  // UUID string instead of number
  title: string
  is_starred?: boolean  // Optional since backend doesn't support starring yet
  last_activity: string
  message_count: number
  is_archived: boolean
}

export default function Sidebar({
  collapsed,
  onCollapse,
  isMobile = false,
}: {
  collapsed: boolean
  onCollapse: (v: boolean) => void
  isMobile?: boolean
}) {
  const [chats, setChats] = useState<Chat[]>([])
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const { token, logout, isAuthenticated } = useAuth()
  const pathname = usePathname()
  const router = useRouter()

  // Extract current chat ID from pathname - now handles UUIDs
  const currentChatId = useMemo(() => {
    const match = pathname.match(/\/chat\/([^/]+)/)
    return match ? match[1] : null
  }, [pathname])

  // Use the same user decoding logic as HeaderBar for consistency
  const claims = useMemo(() => decodeJwt(token || undefined), [token])
  const name = claims?.full_name
  const email = claims?.email
  const schoolId = claims?.active_school_id
  const userLabel = name || email || 'Guest'
  const avatarTxt = initialsFrom(name, email)

  // Auto-collapse helper function
  const handleNavigation = useCallback(() => {
    // Always collapse after navigation to show content
    // This is especially important on mobile to clear the overlay
    if (!collapsed) {
      onCollapse(true)
    }
  }, [collapsed, onCollapse])

  // Close user menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const loadChats = useCallback(async (showRefreshingIndicator = false) => {
    if (!isAuthenticated) return
    
    try {
      if (showRefreshingIndicator) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }
      setError(null)
      
      // Use the new backend method
      const result = await chatService.getConversations(1, 50, false) // Load more chats
      
      // Convert backend conversations to Chat format
      const chatList: Chat[] = result.conversations.map(conv => ({
        id: conv.id,
        title: conv.title,
        is_starred: false, // Backend doesn't support starring yet
        last_activity: conv.last_activity,
        message_count: conv.message_count,
        is_archived: conv.is_archived
      }))
      
      setChats(chatList)
    } catch (error) {
      console.error('Failed to load chats:', error)
      setError('Failed to load chats')
      setChats([])
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [isAuthenticated])

  // Set up auto-refresh using the new hook
  useAutoRefreshChats(
    useCallback(() => loadChats(true), [loadChats]),
    30000 // Refresh every 30 seconds
  )

  // Load chats when component mounts or auth state changes
  useEffect(() => {
    loadChats()
  }, [loadChats])

  // Refresh chats when pathname changes (after creating new chat)
  useEffect(() => {
    if (pathname.includes('/chat/') && currentChatId && currentChatId !== 'new') {
      // Delay to allow backend to save the conversation
      const timer = setTimeout(() => loadChats(true), 1000)
      return () => clearTimeout(timer)
    }
  }, [currentChatId, loadChats])

  // Add periodic refresh to sync across browser sessions
  useEffect(() => {
    if (!isAuthenticated) return

    // Refresh every 30 seconds when user is active
    const interval = setInterval(() => {
      // Only refresh if document is visible (user is actively using the tab)
      if (!document.hidden) {
        loadChats(true)
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [isAuthenticated, loadChats])

  // Listen for focus events to refresh when user switches back to tab
  useEffect(() => {
    const handleFocus = () => {
      if (isAuthenticated) {
        loadChats(true)
      }
    }

    const handleVisibilityChange = () => {
      if (!document.hidden && isAuthenticated) {
        loadChats(true)
      }
    }

    window.addEventListener('focus', handleFocus)
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      window.removeEventListener('focus', handleFocus)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [isAuthenticated, loadChats])

  const handleChatUpdate = (chatId: string, updates: Partial<Conversation>) => {
    setChats(prevChats => 
      prevChats.map(chat => 
        chat.id === chatId ? { 
          ...chat, 
          title: updates.title || chat.title,
          is_starred: updates.is_archived !== undefined ? false : chat.is_starred, // Keep is_starred as is
          is_archived: updates.is_archived !== undefined ? updates.is_archived : chat.is_archived
        } : chat
      ).sort((a, b) => {
        // Sort starred chats first, then by last activity
        if (a.is_starred !== b.is_starred) {
          return (b.is_starred ? 1 : 0) - (a.is_starred ? 1 : 0)
        }
        return new Date(b.last_activity).getTime() - new Date(a.last_activity).getTime()
      })
    )
  }

  const handleChatDelete = (chatId: string) => {
    setChats(prevChats => prevChats.filter(chat => chat.id !== chatId))
    
    // If we're currently viewing the deleted chat, redirect to new chat
    if (currentChatId === chatId) {
      router.replace('/chat/new')
      handleNavigation() // Collapse after navigation
    }
  }

  const handleManualRefresh = () => {
    loadChats(true)
  }

  // Enhanced navigation handlers with auto-collapse
  const handleNewChat = () => {
    router.push('/')
    handleNavigation()
  }

  const handleSchoolNavigation = () => {
    router.push(`/school/${schoolId}`)
    handleNavigation()
  }

  const handleChatNavigation = (chatId: string) => {
    router.push(`/chat/${chatId}`)
    handleNavigation()
  }

  const handleSettingsNavigation = () => {
    setShowUserMenu(false)
    router.push('/settings/profile')
    handleNavigation()
  }

  const handleLogout = () => {
    logout()
    setShowUserMenu(false)
    // No need to call handleNavigation as user will be redirected to login
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <aside 
      className={`
        border-r border-neutral-200/70 dark:border-white/10 
        bg-white/70 dark:bg-neutral-900/60 backdrop-blur 
        flex flex-col h-full transition-all duration-300
        ${collapsed ? 'w-[70px] cursor-pointer' : 'w-[260px]'}
      `}
      onClick={collapsed ? () => onCollapse(false) : undefined}
    >
      {/* Header with logo/brand - Aligned with other elements */}
      <div className="px-2 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center ml-2">
            {collapsed ? (
              <LogoIcon size="sm" />
            ) : (
              <Logo size="sm" href="/" />
            )}
          </div>
          {!collapsed && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => onCollapse(true)}
                className="p-1 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800"
                title="Collapse sidebar"
              >
                <ChevronLeft size={18} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* New Chat Button - Better alignment with chat items */}
      <div className="px-2 pb-2" onClick={collapsed ? (e) => e.stopPropagation() : undefined}>
        <button
          className="w-full rounded-xl py-2 px-1 flex items-center font-medium transition-colors duration-200 hover:bg-neutral-100 dark:hover:bg-neutral-800"
          style={{ color: 'var(--color-brand)' }}
          onClick={handleNewChat}
          title="New Chat"
        >
          <div 
            className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ml-2"
            style={{ backgroundColor: 'var(--color-brand)' }}
          >
            <Plus size={14} className="text-white" />
          </div>
          {!collapsed && (
            <div className="ml-3 overflow-hidden">
              <span className="whitespace-nowrap block">New Chat</span>
            </div>
          )}
        </button>
      </div>

      {/* My School Navigation - Better alignment with chat items */}
      {schoolId && (
        <div className="px-2 pb-2" onClick={collapsed ? (e) => e.stopPropagation() : undefined}>
          <button
            onClick={handleSchoolNavigation}
            className="w-full flex items-center px-1 py-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors text-neutral-700 dark:text-neutral-200"
            title={collapsed ? "My School" : undefined}
          >
            <GraduationCap size={18} className="flex-shrink-0 ml-2" />
            {!collapsed && (
              <div className="ml-3 overflow-hidden">
                <span className="text-sm font-medium whitespace-nowrap block">My School</span>
              </div>
            )}
          </button>
        </div>
      )}

      {/* Chat History - only show when expanded */}
      {!collapsed && (
        <>
          <div className="px-2 py-1 flex items-center justify-between">
            <h3 className="text-xs uppercase tracking-wide text-neutral-500 dark:text-neutral-400 font-medium">
              Recents
            </h3>
            {(refreshing || loading) && (
              <div className="w-3 h-3 border border-neutral-300 dark:border-neutral-600 border-t-transparent rounded-full animate-spin"></div>
            )}
          </div>

          <div className="flex-1 overflow-auto px-2">
            <div className="space-y-0.5">
              {loading && !refreshing ? (
                <div className="px-3 py-2 text-sm text-neutral-500">Loading chats...</div>
              ) : error ? (
                <div className="px-3 py-2 text-sm text-red-500">
                  {error}
                  <button 
                    onClick={handleManualRefresh}
                    className="block mt-1 text-xs text-blue-500 hover:underline"
                  >
                    Retry
                  </button>
                </div>
              ) : chats.length === 0 ? (
                <div className="px-3 py-2 text-sm text-neutral-500">
                  No chats yet.
                  <button 
                    onClick={handleManualRefresh}
                    className="block mt-1 text-xs text-blue-500 hover:underline"
                  >
                    Refresh
                  </button>
                </div>
              ) : (
                chats.map(chat => {
                  const isActive = currentChatId === chat.id
                  
                  return (
                    <div 
                      key={chat.id}
                      className={`
                        group flex items-center rounded-lg transition-colors
                        ${isActive 
                          ? 'bg-neutral-200 dark:bg-neutral-700 hover:bg-neutral-250 dark:hover:bg-neutral-650' 
                          : 'hover:bg-neutral-100 dark:hover:bg-neutral-800'
                        }
                      `}
                    >
                      {/* Enhanced chat link with auto-collapse and reduced padding */}
                      <button
                        onClick={() => handleChatNavigation(chat.id)}
                        className="flex items-center flex-1 px-3 py-1.5 min-w-0 text-left rounded-lg hover:bg-transparent"
                      >
                        {chat.is_starred && (
                          <Star size={14} className="mr-2 text-yellow-400 fill-yellow-400 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <span className="block truncate text-sm text-neutral-700 dark:text-neutral-200">
                            {chat.title}
                          </span>
                        </div>
                      </button>
                      <div className="flex-shrink-0">
                        <ChatOptionsMenu 
                          chat={{
                            id: chat.id,
                            title: chat.title,
                            first_message: '',
                            last_activity: chat.last_activity,
                            message_count: chat.message_count,
                            is_archived: chat.is_archived,
                            created_at: chat.last_activity
                          }}
                          onUpdate={(chatId, updates) => handleChatUpdate(chatId, updates)}
                          onDelete={handleChatDelete}
                          forceVisible={isActive}
                        />
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        </>
      )}

      {/* Spacer to push user section to bottom when collapsed */}
      {collapsed && <div className="flex-1" />}

      {/* User Section at Bottom - Enhanced with auto-collapse navigation */}
      {token && (
        <div 
          className="border-t border-neutral-200/70 dark:border-white/10 p-3 mt-auto" 
          onClick={collapsed ? (e) => e.stopPropagation() : undefined}
        >
          <div className="relative" ref={userMenuRef}>
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className={`
                w-full flex items-center gap-3 p-2 rounded-lg 
                hover:bg-neutral-100 dark:hover:bg-neutral-800 
                transition-all duration-200 ease-out
                ${collapsed ? 'justify-center' : ''}
              `}
              title={collapsed ? `${userLabel}${email ? ` - ${email}` : ''}` : undefined}
              aria-label="User menu"
            >
              {/* Avatar - Enhanced to match HeaderBar styling */}
              <div className="
                inline-flex h-8 w-8 items-center justify-center 
                rounded-full text-white font-semibold text-sm
                shadow-md hover:shadow-lg
                ring-2 ring-blue-500/20 dark:ring-blue-400/30
                border border-blue-300/30
                hover:scale-105 active:scale-95
                transition-all duration-200 ease-out
                flex-shrink-0
              "
              style={{ backgroundColor: 'var(--color-brand)' }}
              >
                {avatarTxt}
              </div>
              
              {/* User info - only show when expanded */}
              {!collapsed && (
                <div className="flex-1 text-left min-w-0">
                  <div className="text-sm font-medium truncate">{userLabel}</div>
                  {email && (
                    <div className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
                      {email}
                    </div>
                  )}
                </div>
              )}
            </button>

            {/* User Menu Dropdown - Enhanced with auto-collapse navigation */}
            {showUserMenu && (
              <div 
                className={`
                  absolute bottom-full mb-2 bg-white dark:bg-neutral-900 rounded-lg 
                  shadow-xl border border-neutral-200 dark:border-neutral-700 py-1 z-50
                  backdrop-blur-sm
                  ${collapsed 
                    ? 'left-full ml-2 w-48' 
                    : 'left-0 right-0'
                  }
                `}
              >
                {/* User info header in dropdown when collapsed */}
                {collapsed && (
                  <div className="px-3 py-2 border-b border-neutral-200 dark:border-neutral-700">
                    <div className="font-medium text-sm truncate">{userLabel}</div>
                    {email && (
                      <div className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
                        {email}
                      </div>
                    )}
                  </div>
                )}
                
                <button
                  onClick={() => {
                    setShowUserMenu(false);
                    handleManualRefresh();
                  }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-700 flex items-center gap-2 transition-colors"
                >
                  <RefreshCw size={16} />
                  Refresh Chats
                </button>
                
                <button
                  onClick={handleSettingsNavigation}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-700 flex items-center gap-2 transition-colors"
                >
                  <Settings size={16} />
                  Settings
                </button>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-700 flex items-center gap-2 text-red-600 dark:text-red-400 transition-colors"
                >
                  <LogOut size={16} />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </aside>
  )
}
'use client'

import { useEffect, useState, useMemo, useRef, useCallback } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'
import { 
  ChevronLeft, LogOut, Settings, RefreshCw, Menu,
  LayoutDashboard, Users, MessageSquare, Activity, 
  FileText, Database, TestTube, TrendingUp,
  GraduationCap, User, Shield, AlertCircle, 
  BarChart3, Clock, Eye
} from 'lucide-react'
import Logo, { LogoIcon } from "@/components/ui/Logo"

// Reuse the same JWT decoding logic from HeaderBar
function decodeJwt(token?: string) {
  if (!token) return null
  try {
    const base = token.split('.')[1]?.replace(/-/g, '+').replace(/_/g, '/')
    const json = atob(base)
    return JSON.parse(json) as { 
      email?: string; 
      full_name?: string; 
      active_school_id?: number | string;
      roles?: string[];
      permissions?: any;
    }
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

// Navigation item interface
interface NavItem {
  id: string
  label: string
  href: string
  icon: React.ReactNode
  badge?: string | number
  requiredRoles?: string[]
  requiredPermissions?: string[]
  section?: 'main' | 'admin' | 'tester' | 'tools'
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
  const [showUserMenu, setShowUserMenu] = useState(false)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const { token, logout, isAuthenticated, user } = useAuth()
  const pathname = usePathname()
  const router = useRouter()

  // Extract user info from token and auth context
  const claims = useMemo(() => decodeJwt(token || undefined), [token])
  const name = claims?.full_name || user?.full_name
  const email = claims?.email || user?.email
  const schoolId = claims?.active_school_id || user?.active_school_id
  const userRoles = claims?.roles || user?.roles || []
  const userPermissions = claims?.permissions || user?.permissions || {}
  const userLabel = name || email || 'Guest'
  const avatarTxt = initialsFrom(name, email)

  // Check user permissions
  const isAdmin = userRoles.includes('ADMIN') || userRoles.includes('SUPER_ADMIN') || 
                  userPermissions.is_admin || userPermissions.is_super_admin
  const isTester = userRoles.includes('TESTER') || userPermissions.is_tester
  const canManageUsers = userPermissions.can_manage_users
  const canManageIntentConfig = userPermissions.can_manage_intent_config
  const canViewLogs = userPermissions.can_view_logs || isAdmin

  // Auto-collapse helper function for mobile
  const handleNavigation = useCallback(() => {
    if (isMobile && !collapsed) {
      onCollapse(true)
    }
  }, [collapsed, onCollapse, isMobile])

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

  // Define navigation items based on user permissions and current route
  const navigationItems: NavItem[] = useMemo(() => {
    const items: NavItem[] = []
    
    // Determine if we're in admin or tester context based on the current route
    const isInAdminContext = pathname.startsWith('/admin')
    const isInTesterContext = pathname.startsWith('/tester')

    // Admin section - only show when in admin context AND user is admin
    if (isAdmin && isInAdminContext) {
      items.push(
        {
          id: 'admin-dashboard',
          label: 'Admin Dashboard',
          href: '/admin',
          icon: <Shield size={18} />,
          section: 'admin'
        },
        {
          id: 'admin-configuration',
          label: 'Configuration',
          href: '/admin/configuration',
          icon: <Database size={18} />,
          section: 'admin'
        },
        {
          id: 'admin-monitoring',
          label: 'Chat Monitoring',
          href: '/admin/monitoring',
          icon: <Activity size={18} />,
          section: 'admin'
        }
      )

      if (canManageUsers) {
        items.push({
          id: 'admin-users',
          label: 'Users',
          href: '/admin/users',
          icon: <Users size={18} />,
          section: 'admin'
        })
      }

      if (canViewLogs) {
        items.push({
          id: 'admin-logs',
          label: 'Logs',
          href: '/admin/logs',
          icon: <FileText size={18} />,
          section: 'admin'
        })
      }

      // Admin can see tester suggestions management
      items.push({
        id: 'admin-suggestions',
        label: 'Manage Suggestions',
        href: '/admin/suggestions',
        icon: <MessageSquare size={18} />,
        section: 'admin'
      })

      // Admin can view tester performance
      items.push({
        id: 'admin-testers',
        label: 'Tester Performance',
        href: '/admin/testers',
        icon: <TrendingUp size={18} />,
        section: 'admin'
      })
    }

    // Tester section - only show when in tester context AND user is tester
    if (isTester && isInTesterContext) {
      items.push(
        {
          id: 'tester-dashboard',
          label: 'Tester Dashboard',
          href: '/tester',
          icon: <TestTube size={18} />,
          section: 'tester'
        },
        {
          id: 'tester-queue',
          label: 'Problem Queue',
          href: '/tester/queue',
          icon: <AlertCircle size={18} />,
          section: 'tester'
        },
        {
          id: 'tester-suggestions',
          label: 'My Suggestions',
          href: '/tester/suggestions',
          icon: <MessageSquare size={18} />,
          section: 'tester'
        }
      )
    }

    return items
  }, [isAdmin, isTester, canManageUsers, canViewLogs, pathname])

  // Group navigation items by section
  const groupedNavItems = useMemo(() => {
    const groups = navigationItems.reduce((acc, item) => {
      const section = item.section || 'main'
      if (!acc[section]) acc[section] = []
      acc[section].push(item)
      return acc
    }, {} as Record<string, NavItem[]>)

    return groups
  }, [navigationItems])

  // Navigation handlers
  const handleNavItemClick = (href: string) => {
    router.push(href)
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
  }

  // Handle sidebar click to expand when collapsed
  const handleSidebarClick = () => {
    if (collapsed) {
      onCollapse(false)
    }
  }

  // Toggle hamburger handler
  const handleHamburgerToggle = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    console.log('Hamburger clicked from sidebar')
    onCollapse(!collapsed)
  }, [collapsed, onCollapse])

  // Render navigation section
  const renderNavSection = (title: string, items: NavItem[]) => {
    return (
      <div className="mb-6">
        <h3 className="text-xs uppercase tracking-wide text-neutral-500 dark:text-neutral-400 font-medium px-4 mb-3">
          {title}
        </h3>
        <div className="space-y-1">
          {items.map((item) => {
            // Fixed active state logic
            const isActive = (() => {
              // For dashboard routes that should only match exactly
              if (item.href === '/admin' || item.href === '/tester' || item.href === '/dashboard') {
                return pathname === item.href
              }
              
              // For all other routes - exact match OR sub-route
              return pathname === item.href || pathname.startsWith(item.href + '/')
            })()
            
            return (
              <button
                key={item.id}
                onClick={() => handleNavItemClick(item.href)}
                className={`
                  w-full flex items-center px-4 py-3 text-left transition-all duration-200
                  ${isActive 
                    ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-r-2 border-blue-500' 
                    : 'text-neutral-700 dark:text-neutral-200 hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
                  }
                `}
              >
                <div className="flex-shrink-0 mr-3">
                  {item.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-sm font-medium">
                    {item.label}
                  </span>
                </div>
                {item.badge && (
                  <div className="flex-shrink-0">
                    <span className="bg-red-500 text-white text-xs rounded-full px-2 py-0.5">
                      {item.badge}
                    </span>
                  </div>
                )}
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  // Drawer-style sidebar - always shows content, just changes width
  return (
    <aside 
      className={`
        border-r border-neutral-200/70 dark:border-white/10 
        bg-white dark:bg-neutral-900 
        flex flex-col h-full transition-all duration-300 ease-in-out
        ${collapsed ? 'w-16 cursor-pointer' : 'w-72'}
        ${isMobile ? 'shadow-2xl' : ''}
      `}
      onClick={handleSidebarClick}
    >
      {/* Header with logo/brand and hamburger menu */}
      <div className="px-4 py-4 border-b border-neutral-200/50 dark:border-neutral-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center min-w-0">
            {collapsed ? (
              <div className="flex items-center justify-center">
                <LogoIcon size="sm" />
              </div>
            ) : (
              <Link href="/dashboard" className="flex items-center">
                <Logo size="sm" asLink={false} />
              </Link>
            )}
          </div>
          {/* Hamburger menu - always visible */}
          <button
            onClick={handleHamburgerToggle}
            className="
              p-1.5 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 
              transition-colors cursor-pointer z-50
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1
            "
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {!isMobile && collapsed ? (
              <Menu size={18} className="text-neutral-600 dark:text-neutral-400" />
            ) : (
              <ChevronLeft 
                size={18} 
                className={`text-neutral-600 dark:text-neutral-400 transition-transform ${
                  collapsed ? 'rotate-180' : ''
                }`} 
              />
            )}
          </button>
        </div>
      </div>

      {/* Navigation Content */}
      <div className="flex-1 overflow-y-auto py-6">
        {collapsed ? (
          // Collapsed view - icons only with tooltips
          <div className="space-y-2 px-2">
            {navigationItems.map((item) => {
              // Fixed active state logic - consistent with expanded view
              const isActive = (() => {
                // For dashboard routes that should only match exactly
                if (item.href === '/admin' || item.href === '/tester' || item.href === '/dashboard') {
                  return pathname === item.href
                }
                
                // For all other routes - exact match OR sub-route
                return pathname === item.href || pathname.startsWith(item.href + '/')
              })()
              
              return (
                <div key={item.id} className="relative group">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleNavItemClick(item.href)
                    }}
                    className={`
                      w-full flex items-center justify-center p-3 rounded-lg transition-all duration-200
                      ${isActive 
                        ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' 
                        : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-neutral-100'
                      }
                    `}
                  >
                    {item.icon}
                    {item.badge && (
                      <div className="absolute -top-1 -right-1">
                        <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      </div>
                    )}
                  </button>
                  
                  {/* Tooltip */}
                  <div className="
                    absolute left-full ml-2 px-3 py-2 bg-neutral-900 dark:bg-neutral-100 
                    text-white dark:text-neutral-900 text-sm rounded-md 
                    opacity-0 invisible group-hover:opacity-100 group-hover:visible 
                    transition-all duration-200 pointer-events-none z-50 whitespace-nowrap
                    top-1/2 transform -translate-y-1/2
                  ">
                    {item.label}
                    <div className="absolute right-full top-1/2 transform -translate-y-1/2">
                      <div className="border-4 border-transparent border-r-neutral-900 dark:border-r-neutral-100"></div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          // Expanded view - full navigation with sections
          <div>
            {/* Admin Section */}
            {groupedNavItems.admin && renderNavSection('Administration', groupedNavItems.admin)}
            
            {/* Tester Section */}
            {groupedNavItems.tester && renderNavSection('Testing', groupedNavItems.tester)}
          </div>
        )}
      </div>

      {/* User Section at Bottom */}
      {token && (
        <div className="border-t border-neutral-200/50 dark:border-neutral-700/50 p-4">
          <div className="relative" ref={userMenuRef}>
            <button
              onClick={(e) => {
                e.stopPropagation()
                setShowUserMenu(!showUserMenu)
              }}
              className={`
                w-full flex items-center gap-3 p-3 rounded-lg 
                hover:bg-neutral-100 dark:hover:bg-neutral-800 
                transition-all duration-200
                ${collapsed ? 'justify-center' : ''}
              `}
              title={collapsed ? `${userLabel}${email ? ` - ${email}` : ''}` : undefined}
            >
              {/* Avatar */}
              <div 
                className="
                  inline-flex h-9 w-9 items-center justify-center 
                  rounded-full text-white font-semibold text-sm
                  shadow-md hover:shadow-lg
                  ring-2 ring-blue-500/20 dark:ring-blue-400/30
                  transition-all duration-200
                  flex-shrink-0
                "
                style={{ backgroundColor: 'var(--color-brand)' }}
              >
                {avatarTxt}
              </div>
              
              {/* User info - only show when expanded */}
              {!collapsed && (
                <div className="flex-1 text-left min-w-0">
                  <div className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 truncate">
                    {userLabel}
                  </div>
                  <div className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
                    {userRoles.length > 0 ? userRoles.join(', ') : 'User'}
                  </div>
                </div>
              )}
            </button>

            {/* User Menu Dropdown */}
            {showUserMenu && (
              <div 
                className={`
                  absolute bg-white dark:bg-neutral-900 rounded-xl 
                  shadow-2xl border border-neutral-200 dark:border-neutral-700 py-2 z-50
                  ${collapsed 
                    ? 'bottom-0 left-full ml-2 w-56' 
                    : 'bottom-full mb-2 left-0 right-0'
                  }
                `}
              >
                {/* User info header when collapsed */}
                {collapsed && (
                  <div className="px-4 py-3 border-b border-neutral-200 dark:border-neutral-700">
                    <div className="font-semibold text-sm text-neutral-900 dark:text-neutral-100 truncate">
                      {userLabel}
                    </div>
                    {email && (
                      <div className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
                        {email}
                      </div>
                    )}
                    <div className="text-xs text-neutral-500 dark:text-neutral-400 truncate mt-1">
                      {userRoles.length > 0 ? userRoles.join(', ') : 'User'}
                    </div>
                  </div>
                )}
                
                <button
                  onClick={handleSettingsNavigation}
                  className="w-full text-left px-4 py-3 text-sm hover:bg-neutral-50 dark:hover:bg-neutral-800 flex items-center gap-3 transition-colors"
                >
                  <Settings size={16} />
                  Settings
                </button>
                
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-3 text-sm hover:bg-neutral-50 dark:hover:bg-neutral-800 flex items-center gap-3 text-red-600 dark:text-red-400 transition-colors"
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
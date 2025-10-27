'use client'

import React, { useEffect, useState } from 'react'
import Sidebar from './WorkspaceSidebar'
import HeaderBar from './HeaderBar'

// Sidebar toggle bus for header integration and auto-collapse
type SidebarCommand = { type: 'toggle' | 'open' | 'close' | 'auto-collapse' }
type SidebarListener = (cmd: SidebarCommand) => void

const sidebarListeners = new Set<SidebarListener>()
export const SidebarBus = {
  send(cmd: SidebarCommand) { 
    console.log('🚌 SidebarBus sending command:', cmd)
    sidebarListeners.forEach(l => l(cmd)) 
  },
  on(l: SidebarListener) { 
    sidebarListeners.add(l); 
    return () => { 
      sidebarListeners.delete(l) 
    } 
  }
}

export default function WorkspaceShell({ children }: { children: React.ReactNode }) {
  // Sidebar collapsed state (persist) - responsive defaults
  const [collapsed, setCollapsed] = useState<boolean>(true)
  const [isMobile, setIsMobile] = useState(false)
  
  // Check mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 1024 // lg breakpoint
      const wasMobile = isMobile
      setIsMobile(mobile)
      
      console.log('📱 Mobile check:', { mobile, wasMobile, width: window.innerWidth })
      
      // Auto-collapse on mobile, restore saved preference on desktop
      if (mobile && !wasMobile) {
        // Switching to mobile - collapse
        console.log('📱 Switching to mobile - collapsing sidebar')
        setCollapsed(true)
      } else if (!mobile && wasMobile) {
        // Switching to desktop - restore saved preference
        const saved = localStorage.getItem('sidebar_collapsed')
        console.log('🖥️ Switching to desktop - saved preference:', saved)
        if (saved === '0') {
          setCollapsed(false)
        }
      }
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [isMobile])
  
  // Load initial sidebar state
  useEffect(() => {
    const saved = localStorage.getItem('sidebar_collapsed')
    console.log('💾 Loading saved sidebar state:', saved)
    // Only expand on desktop if user previously chose to expand
    if (saved === '0' && !isMobile) {
      setCollapsed(false)
    }
  }, [])

  // Dispatch sidebar state changes to header
  useEffect(() => {
    // Dispatch custom event so header can track sidebar state
    const event = new CustomEvent('sidebarStateChange', {
      detail: { collapsed, isMobile }
    })
    window.dispatchEvent(event)
    console.log('📡 Dispatching sidebar state:', { collapsed, isMobile })
  }, [collapsed, isMobile])
  
  const toggleSidebar = (newState?: boolean) => {
    setCollapsed(prev => {
      const next = newState !== undefined ? newState : !prev
      console.log('🔄 Toggling sidebar:', { prev, next, isMobile })
      
      // Only persist on desktop
      if (!isMobile) {
        localStorage.setItem('sidebar_collapsed', next ? '1' : '0')
      }
      return next
    })
  }

  // Listen for sidebar toggle commands from header and auto-collapse
  useEffect(() => {
    console.log('👂 Setting up sidebar bus listener')
    const unsubscribe = SidebarBus.on((cmd) => {
      console.log('📨 Received sidebar command:', cmd)
      if (cmd.type === 'toggle') toggleSidebar()
      if (cmd.type === 'open') toggleSidebar(false)
      if (cmd.type === 'close') toggleSidebar(true)
      if (cmd.type === 'auto-collapse' && !isMobile && !collapsed) {
        // Auto-collapse only on desktop when sidebar is expanded
        toggleSidebar(true)
      }
    })
    
    return unsubscribe
  }, [isMobile, collapsed])

  console.log('🏗️ WorkspaceShell render:', { collapsed, isMobile })

  return (
    <div className="h-svh w-full overflow-hidden">
      <div className="flex-1 overflow-hidden relative h-full">
        {/* Mobile overlay backdrop when sidebar is open */}
        {isMobile && !collapsed && (
          <div 
            className="fixed inset-0 bg-black/50 z-30"
            onClick={() => toggleSidebar(true)}
          />
        )}
        
        {/* Content row: sidebar | main - Fixed height flow */}
        <div className="relative flex overflow-hidden h-full">
          {/* Sidebar - Always visible on desktop, overlay on mobile */}
          <div className={`
            transition-all duration-300 ease-in-out
            ${isMobile 
              ? `fixed left-0 top-0 h-full w-80 z-40 ${collapsed ? '-translate-x-full' : 'translate-x-0'}` 
              : `relative z-10 ${collapsed ? 'w-16' : 'w-auto'}`
            }
          `}>
            <Sidebar 
              collapsed={collapsed && !isMobile}
              onCollapse={toggleSidebar} 
              isMobile={isMobile}
            />
          </div>

          {/* Main content area with header - Fixed flex layout */}
          <div className="flex-1 min-w-0 flex flex-col h-full overflow-hidden">
            <div className="flex-shrink-0">
              <HeaderBar />
            </div>
            {/* Main content area - proper height constraints */}
            <div className="flex-1 min-h-0 overflow-hidden">
              {children}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
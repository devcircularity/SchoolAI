// utils/chatEventBus.ts - Event bus for cross-tab chat synchronization
import { useState, useEffect } from 'react'

type ChatEventType = 
  | 'conversation_created'
  | 'conversation_updated' 
  | 'conversation_deleted'
  | 'message_sent'
  | 'force_refresh'

interface ChatEvent {
  type: ChatEventType
  conversationId?: string
  data?: any
  timestamp: number
  userId?: string
}

class ChatEventBus {
  private listeners: Map<string, ((event: ChatEvent) => void)[]> = new Map()
  private lastEventTimestamp = 0

  constructor() {
    // Listen for storage events from other tabs
    if (typeof window !== 'undefined') {
      window.addEventListener('storage', this.handleStorageEvent.bind(this))
      
      // Also listen for focus events to check for missed events
      window.addEventListener('focus', this.handleWindowFocus.bind(this))
      document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this))
    }
  }

  private handleStorageEvent = (e: StorageEvent) => {
    if (e.key === 'chat_event' && e.newValue) {
      try {
        const event: ChatEvent = JSON.parse(e.newValue)
        
        // Ignore old events
        if (event.timestamp <= this.lastEventTimestamp) {
          return
        }
        
        this.lastEventTimestamp = event.timestamp
        this.notifyListeners(event)
      } catch (error) {
        console.error('Error parsing chat event:', error)
      }
    }
  }

  private handleWindowFocus = () => {
    // When window gains focus, broadcast a force refresh to sync state
    this.broadcast('force_refresh')
  }

  private handleVisibilityChange = () => {
    if (!document.hidden) {
      // When tab becomes visible, broadcast a force refresh
      this.broadcast('force_refresh')
    }
  }

  private notifyListeners(event: ChatEvent) {
    const typeListeners = this.listeners.get(event.type) || []
    const allListeners = this.listeners.get('*') || []
    
    const allEventListeners = typeListeners.concat(allListeners)
    
    allEventListeners.forEach(listener => {
      try {
        listener(event)
      } catch (error) {
        console.error('Error in chat event listener:', error)
      }
    })
  }

  // Subscribe to specific event types or '*' for all events
  subscribe(eventType: ChatEventType | '*', callback: (event: ChatEvent) => void): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, [])
    }
    
    this.listeners.get(eventType)!.push(callback)
    
    // Return unsubscribe function
    return () => {
      const listeners = this.listeners.get(eventType) || []
      const index = listeners.indexOf(callback)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  // Broadcast an event to all tabs
  broadcast(type: ChatEventType, conversationId?: string, data?: any, userId?: string) {
    if (typeof window === 'undefined') return

    const event: ChatEvent = {
      type,
      conversationId,
      data,
      timestamp: Date.now(),
      userId
    }

    try {
      // Store event in localStorage to trigger storage event in other tabs
      localStorage.setItem('chat_event', JSON.stringify(event))
      
      // Update our local timestamp
      this.lastEventTimestamp = event.timestamp
      
      // Remove after a short delay to allow other tabs to read it
      setTimeout(() => {
        try {
          const currentEvent = localStorage.getItem('chat_event')
          if (currentEvent) {
            const parsedEvent = JSON.parse(currentEvent)
            if (parsedEvent.timestamp === event.timestamp) {
              localStorage.removeItem('chat_event')
            }
          }
        } catch (e) {
          // Ignore cleanup errors
        }
      }, 100)
    } catch (error) {
      console.error('Error broadcasting chat event:', error)
    }
  }

  // Convenience methods for common events
  conversationCreated(conversationId: string, data?: any, userId?: string) {
    this.broadcast('conversation_created', conversationId, data, userId)
  }

  conversationUpdated(conversationId: string, data?: any, userId?: string) {
    this.broadcast('conversation_updated', conversationId, data, userId)
  }

  conversationDeleted(conversationId: string, userId?: string) {
    this.broadcast('conversation_deleted', conversationId, undefined, userId)
  }

  messageSent(conversationId: string, data?: any, userId?: string) {
    this.broadcast('message_sent', conversationId, data, userId)
  }

  forceRefresh(userId?: string) {
    this.broadcast('force_refresh', undefined, undefined, userId)
  }

  // Clean up event listeners
  destroy() {
    if (typeof window !== 'undefined') {
      window.removeEventListener('storage', this.handleStorageEvent)
      window.removeEventListener('focus', this.handleWindowFocus)
      document.removeEventListener('visibilitychange', this.handleVisibilityChange)
    }
    this.listeners.clear()
  }
}

// Create a singleton instance
export const chatEventBus = new ChatEventBus()

// Hook for React components
export function useChatEvents() {
  const [, forceUpdate] = useState({})

  useEffect(() => {
    const unsubscribe = chatEventBus.subscribe('*', () => {
      // Force a re-render when any chat event occurs
      forceUpdate({})
    })

    return unsubscribe
  }, [])

  return chatEventBus
}

// Utility to get current user ID from token
export function getCurrentUserId(): string | null {
  if (typeof window === 'undefined') return null
  
  try {
    const token = localStorage.getItem('token')
    if (!token) return null
    
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.sub || null
  } catch {
    return null
  }
}
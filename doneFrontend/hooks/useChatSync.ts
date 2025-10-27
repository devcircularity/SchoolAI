// hooks/useChatSync.ts - Hook for chat synchronization across tabs
import { useEffect, useCallback, useRef } from 'react'
import { chatEventBus, getCurrentUserId } from '@/utils/chatEventBus'

interface UseChatSyncOptions {
  onConversationCreated?: (conversationId: string, data?: any) => void
  onConversationUpdated?: (conversationId: string, data?: any) => void
  onConversationDeleted?: (conversationId: string) => void
  onMessageSent?: (conversationId: string, data?: any) => void
  onForceRefresh?: () => void
  enableAutoRefresh?: boolean
  refreshInterval?: number // in milliseconds
}

export function useChatSync(options: UseChatSyncOptions = {}) {
  const {
    onConversationCreated,
    onConversationUpdated,
    onConversationDeleted,
    onMessageSent,
    onForceRefresh,
    enableAutoRefresh = true,
    refreshInterval = 30000 // 30 seconds
  } = options

  const currentUserId = getCurrentUserId() ?? undefined
  const refreshTimeoutRef = useRef<NodeJS.Timeout>()

  // Set up auto-refresh interval
  useEffect(() => {
    if (!enableAutoRefresh) return

    const scheduleRefresh = () => {
      refreshTimeoutRef.current = setTimeout(() => {
        if (!document.hidden && onForceRefresh) {
          onForceRefresh()
        }
        scheduleRefresh() // Schedule next refresh
      }, refreshInterval)
    }

    scheduleRefresh()

    return () => {
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current)
      }
    }
  }, [enableAutoRefresh, refreshInterval, onForceRefresh])

  // Subscribe to chat events
  useEffect(() => {
    const unsubscribers: (() => void)[] = []

    // Only respond to events from other users/tabs to avoid double-handling our own events
    const shouldHandleEvent = (userId?: string) => {
      return !userId || userId !== currentUserId
    }

    if (onConversationCreated) {
      unsubscribers.push(
        chatEventBus.subscribe('conversation_created', (event) => {
          if (shouldHandleEvent(event.userId) && event.conversationId) {
            onConversationCreated(event.conversationId, event.data)
          }
        })
      )
    }

    if (onConversationUpdated) {
      unsubscribers.push(
        chatEventBus.subscribe('conversation_updated', (event) => {
          if (shouldHandleEvent(event.userId) && event.conversationId) {
            onConversationUpdated(event.conversationId, event.data)
          }
        })
      )
    }

    if (onConversationDeleted) {
      unsubscribers.push(
        chatEventBus.subscribe('conversation_deleted', (event) => {
          if (shouldHandleEvent(event.userId) && event.conversationId) {
            onConversationDeleted(event.conversationId)
          }
        })
      )
    }

    if (onMessageSent) {
      unsubscribers.push(
        chatEventBus.subscribe('message_sent', (event) => {
          if (shouldHandleEvent(event.userId) && event.conversationId) {
            onMessageSent(event.conversationId, event.data)
          }
        })
      )
    }

    if (onForceRefresh) {
      unsubscribers.push(
        chatEventBus.subscribe('force_refresh', (event) => {
          if (shouldHandleEvent(event.userId)) {
            onForceRefresh()
          }
        })
      )
    }

    return () => {
      unsubscribers.forEach(unsubscribe => unsubscribe())
    }
  }, [
    currentUserId,
    onConversationCreated,
    onConversationUpdated,
    onConversationDeleted,
    onMessageSent,
    onForceRefresh
  ])

  // Utility functions to manually trigger events
  const triggerRefresh = useCallback(() => {
    chatEventBus.forceRefresh(currentUserId)
  }, [currentUserId])

  const notifyConversationCreated = useCallback((conversationId: string, data?: any) => {
    chatEventBus.conversationCreated(conversationId, data, currentUserId)
  }, [currentUserId])

  const notifyConversationUpdated = useCallback((conversationId: string, data?: any) => {
    chatEventBus.conversationUpdated(conversationId, data, currentUserId)
  }, [currentUserId])

  const notifyConversationDeleted = useCallback((conversationId: string) => {
    chatEventBus.conversationDeleted(conversationId, currentUserId)
  }, [currentUserId])

  const notifyMessageSent = useCallback((conversationId: string, data?: any) => {
    chatEventBus.messageSent(conversationId, data, currentUserId)
  }, [currentUserId])

  return {
    triggerRefresh,
    notifyConversationCreated,
    notifyConversationUpdated,
    notifyConversationDeleted,
    notifyMessageSent
  }
}

// Simplified hook for components that just need to refresh on any chat event
export function useAutoRefreshChats(refreshCallback: () => void, interval = 30000) {
  return useChatSync({
    onConversationCreated: refreshCallback,
    onConversationUpdated: refreshCallback,
    onConversationDeleted: refreshCallback,
    onMessageSent: refreshCallback,
    onForceRefresh: refreshCallback,
    enableAutoRefresh: true,
    refreshInterval: interval
  })
}
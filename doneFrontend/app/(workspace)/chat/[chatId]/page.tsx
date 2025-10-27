// app/(workspace)/chat/[chatId]/page.tsx - Updated with message ID support for immediate rating buttons
'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { chatService, type ConversationDetail, type DisplayMessage } from '@/services/chats'
import ChatMessages from '@/components/chat/ChatMessages'
import ChatInput from '@/components/chat/ChatInput'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { Action } from '@/components/chat/tools/types'
import { HeaderTitleBus } from '@/components/layout/HeaderBar'

export default function ChatDetail() {
  const { isAuthenticated } = useAuthGuard()
  const params = useParams<{ chatId: string }>()
  const router = useRouter()
  const chatId = params.chatId
  
  const [conversation, setConversation] = useState<ConversationDetail | null>(null)
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Check if chatId is a valid UUID
  const isValidUUID = (str: string) => {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
    return uuidRegex.test(str)
  }

  // Handle actions from blocks
  const handleBlockAction = useCallback(async (action: Action) => {
    switch (action.type) {
      case 'query':
        if (action.payload && 'message' in action.payload) {
          await onSend(action.payload.message)
        }
        break
      
      case 'route':
        if (action.target) {
          const [section, view] = action.target.split(':')
          router.push(`/${section}${view ? `/${view}` : ''}`)
        }
        break
      
      case 'download':
        if (action.endpoint) {
          window.open(action.endpoint, '_blank')
        }
        break
      
      case 'mutation':
        if (action.endpoint) {
          console.log('Mutation action:', action)
        }
        break
      
      case 'confirm':
        console.log('Confirm action:', action)
        break
      
      default:
        console.warn('Unhandled action type:', action)
    }
  }, [router])

  // Load conversation data from backend
  const loadConversation = useCallback(async () => {
    if (!chatId || chatId === 'new') {
      setLoading(false)
      setConversation(null)
      setMessages([])
      
      const initialMessage = sessionStorage.getItem(`chat-new-initial`) || sessionStorage.getItem(`chat-${chatId}-initial`)
      if (initialMessage) {
        sessionStorage.removeItem(`chat-new-initial`)
        sessionStorage.removeItem(`chat-${chatId}-initial`)
        await onSend(initialMessage)
      }
      return
    }

    if (!isValidUUID(chatId)) {
      setLoading(false)
      setConversation(null)
      setMessages([])
      return
    }

    try {
      setLoading(true)
      setError(null)
      
      const conversationData = await chatService.getConversation(chatId)
      setConversation(conversationData)
      setMessages(conversationData.displayMessages)
      
    } catch (err: any) {
      console.error('Failed to load conversation:', err)
      
      if (err?.response?.status === 404) {
        router.replace('/chat/new')
        return
      } else if (err?.response?.status === 401 || err?.response?.status === 403) {
        const currentPath = window.location.pathname + window.location.search
        router.replace('/public')        
      } else {
        setError('Failed to load conversation')
      }
    } finally {
      setLoading(false)
    }
  }, [chatId, router])

  useEffect(() => {
    if (isAuthenticated) {
      loadConversation()
    }
  }, [isAuthenticated, loadConversation])

  // Update header title when conversation changes
  useEffect(() => {
    const title = conversation?.title || 'New Chat'
    HeaderTitleBus.send({ 
      type: 'set', 
      title, 
      subtitle: 'Ask me anything about your school management' 
    })

    // Clean up header title when component unmounts
    return () => {
      HeaderTitleBus.send({ type: 'clear' })
    }
  }, [conversation?.title])

  const broadcastConversationUpdate = useCallback((conversationId: string) => {
    const updateEvent = {
      type: 'conversation_updated',
      conversationId,
      timestamp: Date.now()
    }
    localStorage.setItem('chat_update_event', JSON.stringify(updateEvent))
    
    setTimeout(() => {
      localStorage.removeItem('chat_update_event')
    }, 100)
  }, [])

  // Get current conversation ID for use in handlers
  const getCurrentConversationId = useCallback(() => {
    return conversation?.id || (chatId !== 'new' && isValidUUID(chatId) ? chatId : undefined)
  }, [conversation, chatId])

  // Regular text message handler - UPDATED: Include message ID in assistant response
  const onSend = async (text: string) => {
    if (busy) return
    setBusy(true)
    
    console.log('=== SENDING TEXT MESSAGE ===')
    console.log('Message:', text)
    console.log('Current conversation ID:', getCurrentConversationId())
    
    // Add user message optimistically
    const userMessage: DisplayMessage = { role: 'user', content: text }
    setMessages(prev => [...prev, userMessage])

    try {
      const currentConversationId = getCurrentConversationId()
      
      const response = await chatService.sendMessage(text, currentConversationId)
      
      console.log('Text message response:', {
        conversation_id: response.conversation_id,
        message_id: response.message_id,
        intent: response.intent,
        blocks_count: response.blocks?.length || 0
      })
      
      // Add assistant response WITH message ID for immediate rating buttons
      const assistantMessage: DisplayMessage = {
        role: 'assistant',
        content: response.response,
        blocks: response.blocks,
        id: response.message_id // ✅ CRITICAL: Include message ID from backend response
      }
      setMessages(prev => [...prev, assistantMessage])

      // Handle new conversation redirect
      if (!conversation && response.conversation_id && (chatId === 'new' || !isValidUUID(chatId))) {
        console.log('New conversation created, redirecting to:', response.conversation_id)
        broadcastConversationUpdate(response.conversation_id)
        router.replace(`/chat/${response.conversation_id}`)
        return
      }

      // Update conversation if needed
      if (response.conversation_id && !conversation) {
        try {
          const newConversation = await chatService.getConversation(response.conversation_id)
          setConversation(newConversation)
          broadcastConversationUpdate(response.conversation_id)
        } catch (err) {
          console.error('Failed to load new conversation:', err)
        }
      } else if (conversation?.id) {
        broadcastConversationUpdate(conversation.id)
      }

    } catch (error: any) {
      console.error('Failed to send message:', error)
      
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        const currentPath = window.location.pathname + window.location.search
        router.replace('/public')        
      }

      // Remove optimistic message and show error
      setMessages(prev => prev.slice(0, -1))
      
      const errorMessage: DisplayMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your message. Please try again.'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setBusy(false)
    }
  }

  // File message handler - UPDATED: Include message ID in assistant response
  const handleSendWithFiles = async (message: string, files: File[], providedConversationId?: string) => {
    if (busy) return
    setBusy(true)
    
    console.log('=== SENDING MESSAGE WITH FILES ===')
    console.log('Message:', message)
    console.log('Files count:', files.length)
    console.log('Provided conversation ID:', providedConversationId)
    console.log('Current conversation ID:', getCurrentConversationId())
    
    // Add user message optimistically
    const userMessage: DisplayMessage = { role: 'user', content: message }
    setMessages(prev => [...prev, userMessage])

    try {
      // Use provided conversation ID or current one
      const currentConversationId = providedConversationId || getCurrentConversationId()
      
      console.log('Using conversation ID for files:', currentConversationId)
      
      const response = await chatService.sendMessageWithFiles(message, files, currentConversationId)
      
      console.log('File message response:', {
        conversation_id: response.conversation_id,
        message_id: response.message_id,
        intent: response.intent,
        attachment_processed: response.attachment_processed,
        blocks_count: response.blocks?.length || 0
      })
      
      // Add assistant response WITH message ID for immediate rating buttons
      const assistantMessage: DisplayMessage = {
        role: 'assistant',
        content: response.response,
        blocks: response.blocks,
        id: response.message_id // ✅ CRITICAL: Include message ID from backend response
      }
      setMessages(prev => [...prev, assistantMessage])

      // Handle new conversation redirect
      if (!conversation && response.conversation_id && (chatId === 'new' || !isValidUUID(chatId))) {
        console.log('New conversation created with files, redirecting to:', response.conversation_id)
        broadcastConversationUpdate(response.conversation_id)
        router.replace(`/chat/${response.conversation_id}`)
        return
      }

      // Update conversation if needed
      if (response.conversation_id && !conversation) {
        try {
          const newConversation = await chatService.getConversation(response.conversation_id)
          setConversation(newConversation)
          broadcastConversationUpdate(response.conversation_id)
        } catch (err) {
          console.error('Failed to load new conversation:', err)
        }
      } else if (conversation?.id) {
        broadcastConversationUpdate(conversation.id)
      }

    } catch (error: any) {
      console.error('Failed to send message with files:', error)
      
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        const currentPath = window.location.pathname + window.location.search
        router.replace('/public')       
      }

      // Remove optimistic message and show error
      setMessages(prev => prev.slice(0, -1))
      
      const errorMessage: DisplayMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your files. Please try again.'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setBusy(false)
    }
  }

  // Handle file processing completion (for alternative flow)
  const handleFileProcessingComplete = async (conversationId: string) => {
    console.log('=== FILE PROCESSING COMPLETE ===')
    console.log('File processing complete for conversation:', conversationId)
    console.log('Current chat ID:', chatId)
    console.log('Current conversation ID:', conversation?.id)
    
    // If this is a new conversation, redirect to it
    if (!conversation && conversationId && (chatId === 'new' || !isValidUUID(chatId))) {
      console.log('Redirecting to new conversation:', conversationId)
      broadcastConversationUpdate(conversationId)
      router.replace(`/chat/${conversationId}`)
      return
    }
    
    // Reload the conversation to show new messages
    if (conversationId === conversation?.id || conversationId === chatId) {
      console.log('Reloading conversation:', conversationId)
      await loadConversation()
      broadcastConversationUpdate(conversationId)
    }
  }

  // Handle new message from file processing (for alternative flow)
  const handleNewMessage = (response: any) => {
    console.log('=== NEW MESSAGE FROM FILE PROCESSING ===')
    console.log('New message received from file processing:', {
      conversation_id: response.conversation_id,
      message_id: response.message_id,
      intent: response.intent,
      response_preview: response.response?.substring(0, 100)
    })
    // The conversation will be reloaded by handleFileProcessingComplete
  }

  // Listen for storage events
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'chat_update_event' && e.newValue) {
        try {
          const updateEvent = JSON.parse(e.newValue)
          if (updateEvent.type === 'conversation_updated' && updateEvent.conversationId === chatId) {
            loadConversation()
          }
        } catch (error) {
          console.error('Error parsing storage event:', error)
        }
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [chatId, loadConversation])

  if (!isAuthenticated) {
    return null
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center px-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">Loading conversation...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center px-4">
        <div className="text-center max-w-sm">
          <p className="text-red-600 dark:text-red-400 mb-4 text-sm">{error}</p>
          <div className="flex flex-col gap-2 sm:flex-row sm:gap-3 justify-center">
            <button
              onClick={() => loadConversation()}
              className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              Retry
            </button>
            <button
              onClick={() => router.push('/chat/new')}
              className="px-4 py-2 bg-neutral-600 text-white rounded text-sm hover:bg-neutral-700"
            >
              New Chat
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Messages area - CRITICAL: Fixed height allocation */}
      {messages.length === 0 ? (
        <div className="flex-1 flex items-center justify-center px-3 sm:px-6 overflow-y-auto">
          <div className="text-center py-6 sm:py-10 max-w-md mx-auto">
            <h3 className="text-base sm:text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-2">
              Welcome to School Chat
            </h3>
            <p className="text-neutral-600 dark:text-neutral-400 mb-4 text-sm sm:text-base">
              I can help you manage students, classes, fees, and more. Try asking:
            </p>
            <div className="space-y-2 text-sm">
              <button
                onClick={() => onSend("Show me school overview")}
                disabled={busy}
                className="block w-full bg-neutral-100 dark:bg-neutral-800 rounded-lg p-3 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50 text-left"
              >
                "Show me school overview"
              </button>
              <button
                onClick={() => onSend("List all students")}
                disabled={busy}
                className="block w-full bg-neutral-100 dark:bg-neutral-800 rounded-lg p-3 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50 text-left"
              >
                "List all students"
              </button>
              <button
                onClick={() => onSend("Create class P4 East")}
                disabled={busy}
                className="block w-full bg-neutral-100 dark:bg-neutral-800 rounded-lg p-3 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50 text-left"
              >
                "Create class P4 East"
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 min-h-0 overflow-hidden">
          <ChatMessages messages={messages} isLoading={busy} onAction={handleBlockAction} />
        </div>
      )}

      {/* Input - CRITICAL: Fixed positioning */}
      <div className="flex-none">
        <ChatInput 
          onSend={onSend}
          onSendWithFiles={handleSendWithFiles}
          onFileProcessingComplete={handleFileProcessingComplete}
          onNewMessage={handleNewMessage}
          busy={busy}
          conversationId={getCurrentConversationId()}
        />
      </div>
    </div>
  )
}
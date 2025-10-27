// app/(public)/page.tsx - Fixed with proper viewport height and fixed positioning
'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import ChatMessages from '@/components/chat/ChatMessages'
import ChatInput from '@/components/chat/ChatInput'
import { publicChatService } from '@/services/publicApi'
import { Action } from '@/components/chat/tools/types'

type DisplayMessage = {
  role: 'user' | 'assistant'
  content: string
  blocks?: any[]
}

export default function PublicChatPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading, active_school_id } = useAuth()
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Redirect authenticated users to workspace
  useEffect(() => {
    if (isLoading) return

    if (isAuthenticated) {
      if (active_school_id) {
        router.replace('/workspace')
      } else {
        router.replace('/onboarding/school')
      }
    }
  }, [isAuthenticated, isLoading, active_school_id, router])

  // Don't render anything while loading or if authenticated
  if (isLoading || isAuthenticated) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-semibold mb-2">
            {isLoading ? 'Loading...' : 'Redirecting...'}
          </div>
          <div className="text-neutral-600 dark:text-neutral-400">
            {isLoading ? 'Checking authentication...' : 'Taking you to your workspace...'}
          </div>
        </div>
      </div>
    )
  }

  // Handle actions from blocks (simplified for public)
  const handleBlockAction = useCallback(async (action: Action) => {
    switch (action.type) {
      case 'query':
        if (action.payload && 'message' in action.payload) {
          await onSend(action.payload.message)
        }
        break
      
      case 'route':
        // For public users, suggest signing up instead of routing
        const signupMessage: DisplayMessage = {
          role: 'assistant',
          content: 'To access that feature, please sign up for full access to Olaji school management!'
        }
        setMessages(prev => [...prev, signupMessage])
        break
      
      default:
        console.log('Public action:', action)
    }
  }, [])

  const getOrCreateSessionId = useCallback(() => {
    let sessionId = localStorage.getItem('public_chat_session')
    if (!sessionId) {
      sessionId = 'pub_' + Date.now() + '_' + Math.random().toString(36).substring(2)
      localStorage.setItem('public_chat_session', sessionId)
    }
    return sessionId
  }, [])

  // Regular text message handler (similar to workspace chat)
  const onSend = async (text: string) => {
    if (busy) return
    setBusy(true)
    
    // Add user message optimistically
    const userMessage: DisplayMessage = { role: 'user', content: text }
    setMessages(prev => [...prev, userMessage])

    try {
      const sessionId = getOrCreateSessionId()
      const response = await publicChatService.sendMessage(text, sessionId)
      
      // Add assistant response
      const assistantMessage: DisplayMessage = {
        role: 'assistant',
        content: response.response,
        blocks: response.blocks || undefined
      }
      setMessages(prev => [...prev, assistantMessage])

    } catch (error: any) {
      console.error('Failed to send message:', error)
      
      // Remove optimistic message and show error
      setMessages(prev => prev.slice(0, -1))
      
      const errorMessage: DisplayMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setBusy(false)
    }
  }

  // File handling for public (show upgrade message)
  const handleSendWithFiles = async (message: string, files: File[]) => {
    const upgradeMessage: DisplayMessage = {
      role: 'assistant',
      content: 'File uploads are available with a full Olaji account. Sign up to access file processing, document analysis, and complete school management features!'
    }
    setMessages(prev => [...prev, upgradeMessage])
  }

  const QuickBtn = ({ label, prompt }: { label: string; prompt: string }) => (
    <button
      onClick={() => onSend(prompt)}
      className="block w-full bg-neutral-100 dark:bg-neutral-800 rounded-lg p-3 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50 text-left text-sm"
      disabled={busy}
    >
      {prompt}
    </button>
  )

  return (
    <div className="h-screen w-full overflow-hidden bg-white dark:bg-neutral-900">
      {messages.length === 0 ? (
        // Welcome screen layout - uses flex layout, no fixed positioning needed
        <>
          {/* Header */}
          <div className="flex-none flex justify-between items-center p-4 border-b border-neutral-200 dark:border-neutral-800">
            <div className="text-2xl font-semibold">
              <span className="text-neutral-900 dark:text-neutral-100">Olaji</span>{' '}
              <span style={{ color: 'var(--color-brand)' }}>Chat</span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => router.push('/login')}
                className="px-4 py-2 text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100 transition-colors"
              >
                Sign In
              </button>
              <button
                onClick={() => router.push('/signup')}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
              >
                Sign Up
              </button>
            </div>
          </div>

          {/* Welcome content */}
          <div className="flex-1 flex items-center justify-center px-3 sm:px-6 overflow-y-auto">
            <div className="text-center py-6 sm:py-10 max-w-md mx-auto">
              <div className="mb-8">
                <div className="text-4xl font-semibold tracking-tight mb-3">
                  Try Olaji Chat
                </div>
                <div className="text-lg text-neutral-600 dark:text-neutral-400">
                  Experience our AI-powered school management assistant
                </div>
              </div>

              <div className="mb-6">
                <ChatInput 
                  onSend={onSend}
                  onSendWithFiles={handleSendWithFiles}
                  busy={busy}
                />
              </div>

              <div className="space-y-2 text-sm">
                <QuickBtn label="What can you do?" prompt="What can you help me with?" />
                <QuickBtn label="School Features" prompt="Tell me about school management features" />
                <QuickBtn label="How it works" prompt="How does Olaji Chat work?" />
                <QuickBtn label="Pricing" prompt="What are your pricing plans?" />
              </div>
            </div>
          </div>
        </>
      ) : (
        // Chat layout with proper fixed positioning
        <>
          {/* Fixed Header */}
          <div className="fixed top-0 left-0 right-0 z-30 flex justify-between items-center p-4 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
            <div className="text-2xl font-semibold">
              <span className="text-neutral-900 dark:text-neutral-100">Olaji</span>{' '}
              <span style={{ color: 'var(--color-brand)' }}>Chat</span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => router.push('/login')}
                className="px-4 py-2 text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100 transition-colors"
              >
                Sign In
              </button>
              <button
                onClick={() => router.push('/register')}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
              >
                Sign Up
              </button>
            </div>
          </div>

          {/* Scrollable Messages Area */}
          <div className="fixed top-16 bottom-32 left-0 right-0 overflow-y-auto">
            <div className="pb-6">
              <ChatMessages 
                messages={messages} 
                isLoading={busy} 
                onAction={handleBlockAction}
              />
            </div>
          </div>

          {/* Fixed Input at Bottom */}
          <div className="fixed bottom-0 left-0 right-0 z-30 bg-white dark:bg-neutral-900 p-4">
            <ChatInput 
              onSend={onSend}
              onSendWithFiles={handleSendWithFiles}
              busy={busy}
            />
          </div>
        </>
      )}
    </div>
  )
}
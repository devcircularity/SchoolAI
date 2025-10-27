'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import ChatInput from '@/components/chat/ChatInput'
import { Message, ChatResponse } from '@/services/chats'  // Changed MessageResponse to Message

export default function PublicLanding() {
  const router = useRouter()
  const [busy, setBusy] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])  // Changed MessageResponse to Message
  const [anonymousSessionId, setAnonymousSessionId] = useState<string>('')

  useEffect(() => {
    // Generate or retrieve anonymous session ID
    let sessionId = localStorage.getItem('anonymous_session_id')
    if (!sessionId) {
      sessionId = `anon_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      localStorage.setItem('anonymous_session_id', sessionId)
    }
    setAnonymousSessionId(sessionId)

    // Load existing messages for this session
    loadAnonymousMessages(sessionId)
  }, [])

  const loadAnonymousMessages = async (sessionId: string) => {
    try {
      const response = await fetch(`/api/chat/anonymous/messages?session_id=${sessionId}`)
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages || [])
      }
    } catch (error) {
      console.error('Failed to load anonymous messages:', error)
    }
  }

  const submit = async (text?: string, context?: any) => {
    const message = text?.trim()
    if (!message || busy) return
    setBusy(true)
    
    try {
      // Add user message to UI immediately
      const userMessage: Message = {  // Changed MessageResponse to Message
        id: `temp_${Date.now()}`,
        conversation_id: anonymousSessionId,
        message_type: 'USER',
        content: message,
        created_at: new Date().toISOString(),  // Changed to string format
        intent: undefined,  // Changed from null to undefined
        context_data: undefined,  // Changed from null to undefined
        response_data: undefined,  // Changed from null to undefined
        processing_time_ms: undefined  // Changed from null to undefined
        // Removed attachments property as it's not in the Message type
      }
      setMessages(prev => [...prev, userMessage])
      
      // Send to anonymous chat endpoint
      const response = await fetch('/api/chat/anonymous/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: anonymousSessionId,
          context
        })
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const chatResponse: ChatResponse = await response.json()
      
      // Add AI response to UI
      const aiMessage: Message = {  // Changed MessageResponse to Message
        id: `ai_${Date.now()}`,
        conversation_id: anonymousSessionId,
        message_type: 'ASSISTANT',
        content: chatResponse.response,
        created_at: new Date().toISOString(),  // Changed to string format
        intent: chatResponse.intent,
        context_data: undefined,  // Changed from null to undefined
        response_data: chatResponse.data,
        processing_time_ms: undefined  // Changed from null to undefined
        // Removed attachments property
      }
      setMessages(prev => [...prev, aiMessage])
      
    } catch (error) {
      console.error('Failed to send message:', error)
      // Add error message
      const errorMessage: Message = {  // Changed MessageResponse to Message
        id: `error_${Date.now()}`,
        conversation_id: anonymousSessionId,
        message_type: 'ASSISTANT',
        content: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString(),  // Changed to string format
        intent: 'error',
        context_data: undefined,  // Changed from null to undefined
        response_data: undefined,  // Changed from null to undefined
        processing_time_ms: undefined  // Changed from null to undefined
        // Removed attachments property
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setBusy(false)
    }
  }

  const handleSuggestionClick = (prompt: string) => {
    submit(prompt)
  }

  const QuickBtn = ({ label, prompt }: { label: string; prompt: string }) => (
    <button
      onClick={() => handleSuggestionClick(prompt)}
      className="rounded-xl bg-neutral-200/70 px-4 py-2 text-sm dark:bg-neutral-800/80 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition disabled:opacity-60"
      disabled={busy}
    >
      {label}
    </button>
  )

  return (
    <div className="h-full flex flex-col">
      {/* Header with sign-in prompt */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-3 text-center">
        <p className="text-sm">
          You're chatting anonymously. 
          <button 
            onClick={() => router.push('/auth/login')}
            className="ml-2 underline hover:no-underline font-semibold"
          >
            Sign in
          </button>
          {' '}or{' '}
          <button 
            onClick={() => router.push('/auth/register')}
            className="underline hover:no-underline font-semibold"
          >
            create an account
          </button>
          {' '}to save your conversations and access full features.
        </p>
      </div>

      <div className="flex-1 flex flex-col">
        {messages.length === 0 ? (
          // Landing view when no messages
          <div className="flex-1 flex items-center justify-center">
            <div className="w-full max-w-3xl px-4 sm:px-6 lg:px-8">
              {/* Logo */}
              <div className="text-center select-none mb-8">
                <div className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-semibold tracking-tight">
                  <span className="text-neutral-900 dark:text-neutral-100">Olaji</span>{' '}
                  <span style={{ color: 'var(--color-brand)' }}>Chat</span>
                </div>
                <div className="mt-3 text-base sm:text-lg text-neutral-600 dark:text-neutral-400">
                  Your AI assistant for school management
                </div>
              </div>

              {/* Chat Input */}
              <div className="mx-auto max-w-2xl mb-6">
                <ChatInput 
                  onSend={submit}
                  busy={busy}
                  placeholder="Ask me anything about school management..."
                />
              </div>

              {/* Primary buttons */}
              <div className="mb-6 flex flex-col sm:flex-row items-center justify-center gap-3">
                <button
                  onClick={() => handleSuggestionClick('What can you help me with for school management?')}
                  className="w-full sm:w-auto rounded-xl bg-neutral-200/70 px-6 py-3 text-sm font-medium dark:bg-neutral-800/80 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition disabled:opacity-60"
                  disabled={busy}
                >
                  Explore Features
                </button>
                <button
                  onClick={() => handleSuggestionClick('Tell me about Olaji Chat capabilities')}
                  className="w-full sm:w-auto rounded-xl bg-neutral-200/70 px-6 py-3 text-sm font-medium dark:bg-neutral-800/80 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition disabled:opacity-60"
                  disabled={busy}
                >
                  Learn More
                </button>
              </div>

              {/* Shortcut "chips" */}
              <div className="flex flex-wrap items-center justify-center gap-2 max-w-2xl mx-auto">
                <QuickBtn label="School Management Demo" prompt="Show me how to manage a school with Olaji" />
                <QuickBtn label="Student Enrollment" prompt="How do I enroll students?" />
                <QuickBtn label="Fee Management" prompt="How does fee management work?" />
                <QuickBtn label="Academic Reports" prompt="What kind of reports can I generate?" />
              </div>
            </div>
          </div>
        ) : (
          // Chat view when messages exist
          <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
            {/* Chat messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message, index) => (
                <div
                  key={message.id}
                  className={`flex ${message.message_type === 'USER' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 ${
                      message.message_type === 'USER'
                        ? 'bg-blue-500 text-white'
                        : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    {message.message_type === 'ASSISTANT' && message.intent === 'encourage_signup' && (
                      <div className="mt-3 pt-3 border-t border-neutral-300 dark:border-neutral-600">
                        <div className="flex gap-2">
                          <button
                            onClick={() => router.push('/auth/register')}
                            className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600 transition"
                          >
                            Sign Up Free
                          </button>
                          <button
                            onClick={() => router.push('/auth/login')}
                            className="bg-neutral-200 dark:bg-neutral-700 px-3 py-1 rounded text-sm hover:bg-neutral-300 dark:hover:bg-neutral-600 transition"
                          >
                            Sign In
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Chat input at bottom */}
            <div className="border-t border-neutral-200 dark:border-neutral-700 p-4">
              <div className="max-w-2xl mx-auto">
                <ChatInput 
                  onSend={submit}
                  busy={busy}
                  placeholder="Continue the conversation..."
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
// app/(workspace)/page.tsx - Fixed suggestions integration and ref issue
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import ChatInput from '@/components/chat/ChatInput'

export default function Landing() {
  const { isAuthenticated } = useAuthGuard()
  const router = useRouter()
  const [busy, setBusy] = useState(false)

  // Enhanced submit handler that properly handles file processing context
  const submit = async (text?: string, context?: any) => {
    const message = text?.trim()
    if (!message || busy) return
    setBusy(true)
    
    try {
      console.log('=== LANDING PAGE SUBMIT ===')
      console.log('Message:', message)
      console.log('Context:', context)
      
      // SPECIAL CASE: Handle file processing completion context
      if (context?.type === 'file_processing_complete') {
        console.log('File processing completed, redirecting to conversation:', context.conversation_id)
        // Files were processed and a new conversation was created
        // Navigate directly to the new conversation
        router.push(`/chat/${context.conversation_id}`)
        return
      }
      
      // REGULAR CASE: Store the initial message and navigate to new chat
      console.log('Storing initial message for new chat')
      sessionStorage.setItem(`chat-new-initial`, message)
      if (context && context.type !== 'file_processing_complete') {
        sessionStorage.setItem(`chat-new-context`, JSON.stringify(context))
      }
      
      // Navigate to the new chat route
      router.push(`/chat/new`)
      
    } catch (error) {
      console.error('Failed to create chat:', error)
    } finally {
      setBusy(false)
    }
  }

  const handleSuggestionClick = (prompt: string) => {
    // Send the suggestion directly
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

  // Don't render the page content if not authenticated
  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="h-full flex items-center justify-center">
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

        {/* Chat Input - FIXED: Removed ref prop */}
        <div className="mx-auto max-w-2xl mb-6">
          <ChatInput 
            onSend={submit}
            busy={busy}
            // No onSendWithFiles handler - let ChatInput handle files directly
            // No conversationId - this is a new chat
          />
        </div>

        {/* Primary buttons like Google */}
        <div className="mb-6 flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={() => handleSuggestionClick('help me get started with school management')}
            className="w-full sm:w-auto rounded-xl bg-neutral-200/70 px-6 py-3 text-sm font-medium dark:bg-neutral-800/80 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition disabled:opacity-60"
            disabled={busy}
          >
            School Chat Search
          </button>
          <button
            onClick={() => handleSuggestionClick('help')}
            className="w-full sm:w-auto rounded-xl bg-neutral-200/70 px-6 py-3 text-sm font-medium dark:bg-neutral-800/80 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition disabled:opacity-60"
            disabled={busy}
          >
            I'm Feeling Curious
          </button>
        </div>

        {/* Shortcut "chips" */}
        <div className="flex flex-wrap items-center justify-center gap-2 max-w-2xl mx-auto">
          <QuickBtn label="Create Class" prompt="create class P4 East" />
          <QuickBtn label="List Students" prompt="list students" />
          <QuickBtn label="Enroll Student" prompt="enroll student John Doe admission 123 into P4 East" />
          <QuickBtn label="Create Invoice" prompt="create invoice for student 123 amount 15000" />
          <QuickBtn label="Record Payment" prompt="record payment invoice 1 amount 15000" />
        </div>
      </div>
    </div>
  )
}
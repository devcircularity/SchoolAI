// app/(workspace)/new/page.tsx
'use client'

import { useRouter } from 'next/navigation'
import { chatService } from '@/services/chats'
import { useAuthGuard } from '@/hooks/useAuthGuard'

export default function NewPage() {
  const { isAuthenticated } = useAuthGuard()
  const router = useRouter()

  const open = async () => {
    try {
      const c = await chatService.create()
      router.push(`/chat/${c.id}`)
    } catch (error) {
      console.error('Failed to create chat:', error)
      // If error is 401/403, redirect to login
      if ((error as any)?.response?.status === 401 || (error as any)?.response?.status === 403) {
        const currentPath = window.location.pathname + window.location.search
        router.replace('/public')      }
    }
  }

  // Don't render if not authenticated
  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="card">
      <h2>Start a new chat</h2>
      <button onClick={open}>Create</button>
    </div>
  )
}
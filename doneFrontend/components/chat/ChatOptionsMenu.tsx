// components/ChatOptionsMenu.tsx - Updated with custom confirmation modal
'use client'

import { useState, useRef, useEffect } from 'react'
import { MoreHorizontal, Archive, ArchiveRestore, Edit2, Trash2 } from 'lucide-react'
import { chatService, type Conversation } from '@/services/chats'
import ConfirmationModal from '@/components/ui/ConfirmationModal'

interface ChatOptionsMenuProps {
  chat: Conversation
  onUpdate: (chatId: string, updates: Partial<Conversation>) => void
  onDelete: (chatId: string) => void
  forceVisible?: boolean // New prop to control visibility
}

export default function ChatOptionsMenu({ chat, onUpdate, onDelete, forceVisible = false }: ChatOptionsMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isRenaming, setIsRenaming] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [newTitle, setNewTitle] = useState(chat.title)
  const [isLoading, setIsLoading] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Focus input when renaming starts
  useEffect(() => {
    if (isRenaming && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isRenaming])

  const handleArchive = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (isLoading) return
    setIsLoading(true)
    
    try {
      const updatedChat = await chatService.updateConversation(chat.id, { 
        is_archived: !chat.is_archived 
      })
      onUpdate(chat.id, updatedChat)
    } catch (error) {
      console.error('Failed to toggle archive:', error)
    } finally {
      setIsLoading(false)
      setIsOpen(false)
    }
  }

  const handleRename = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsRenaming(true)
    setIsOpen(false)
  }

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (isLoading) return
    
    const trimmedTitle = newTitle.trim()
    if (trimmedTitle && trimmedTitle !== chat.title) {
      setIsLoading(true)
      try {
        const updatedChat = await chatService.updateConversation(chat.id, { 
          title: trimmedTitle 
        })
        onUpdate(chat.id, updatedChat)
      } catch (error) {
        console.error('Failed to rename chat:', error)
        setNewTitle(chat.title) // Reset on error
      } finally {
        setIsLoading(false)
      }
    }
    setIsRenaming(false)
  }

  const handleRenameCancel = () => {
    setNewTitle(chat.title)
    setIsRenaming(false)
  }

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsOpen(false)
    setShowDeleteModal(true)
  }

  const handleDeleteConfirm = async () => {
    if (isLoading) return
    
    setIsLoading(true)
    try {
      await chatService.deleteConversation(chat.id)
      onDelete(chat.id)
    } catch (error) {
      console.error('Failed to delete chat:', error)
    } finally {
      setIsLoading(false)
      setShowDeleteModal(false)
    }
  }

  const handleDeleteCancel = () => {
    setShowDeleteModal(false)
  }

  if (isRenaming) {
    return (
      <form onSubmit={handleRenameSubmit} className="flex-1 mr-2">
        <input
          ref={inputRef}
          type="text"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          onBlur={handleRenameCancel}
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              handleRenameCancel()
            }
          }}
          className="w-full px-2 py-1 text-sm bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          onClick={(e) => e.stopPropagation()}
          disabled={isLoading}
          maxLength={255}
        />
      </form>
    )
  }

  return (
    <>
      <div className="relative" ref={menuRef}>
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            setIsOpen(!isOpen)
          }}
          className={`p-1 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-opacity disabled:opacity-50 ${
            forceVisible ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
          }`}
          title="Chat options"
          disabled={isLoading}
        >
          <MoreHorizontal size={16} />
        </button>

        {isOpen && (
          <div className="absolute right-0 top-full mt-1 bg-white dark:bg-neutral-800 rounded-lg shadow-xl border border-neutral-200 dark:border-neutral-700 py-1 z-50 min-w-[160px]">
            <button
              onClick={handleArchive}
              disabled={isLoading}
              className="w-full text-left px-3 py-2 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-700 flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              {chat.is_archived ? (
                <>
                  <ArchiveRestore size={16} />
                  Unarchive
                </>
              ) : (
                <>
                  <Archive size={16} />
                  Archive
                </>
              )}
            </button>
            
            <button
              onClick={handleRename}
              disabled={isLoading}
              className="w-full text-left px-3 py-2 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-700 flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              <Edit2 size={16} />
              Rename
            </button>
            
            <button
              onClick={handleDeleteClick}
              disabled={isLoading}
              className="w-full text-left px-3 py-2 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-700 flex items-center gap-2 text-red-600 dark:text-red-400 transition-colors disabled:opacity-50"
            >
              <Trash2 size={16} />
              Delete
            </button>
          </div>
        )}
      </div>

      {/* Custom Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={showDeleteModal}
        title="Delete chat"
        message="Are you sure you want to delete this chat?"
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
      />
    </>
  )
}
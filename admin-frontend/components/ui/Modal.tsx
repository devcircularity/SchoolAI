// components/ui/Modal.tsx
'use client'

import { useEffect, ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  showCloseButton?: boolean
  closeOnBackdropClick?: boolean
  closeOnEscape?: boolean
  zIndex?: number
}

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  showCloseButton = true,
  closeOnBackdropClick = true,
  closeOnEscape = true,
  zIndex = 9999
}: ModalProps) {
  // Handle escape key
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose, closeOnEscape])

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }

    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  if (!isOpen) return null

  // Get modal size classes
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'max-w-md'
      case 'md':
        return 'max-w-lg'
      case 'lg':
        return 'max-w-2xl'
      case 'xl':
        return 'max-w-4xl'
      case 'full':
        return 'max-w-[95vw] max-h-[95vh]'
      default:
        return 'max-w-lg'
    }
  }

  const modalContent = (
    <div className="fixed inset-0 flex items-center justify-center p-4" style={{ zIndex }}>
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={closeOnBackdropClick ? onClose : undefined}
      />
      
      {/* Modal */}
      <div className={`relative bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl w-full ${getSizeClasses()} 
                      border border-neutral-200 dark:border-neutral-700 flex flex-col max-h-[90vh]`}>
        
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-4 sm:p-6 border-b border-neutral-200 dark:border-neutral-700">
            {title && (
              <h3 className="text-lg sm:text-xl font-semibold text-neutral-900 dark:text-neutral-100">
                {title}
              </h3>
            )}
            {showCloseButton && (
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 
                         text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200
                         transition-colors flex-shrink-0"
                aria-label="Close modal"
              >
                <X size={20} />
              </button>
            )}
          </div>
        )}
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          {children}
        </div>
      </div>
    </div>
  )

  // Use createPortal to render at document.body level
  if (typeof document !== 'undefined') {
    return createPortal(modalContent, document.body)
  }

  return null
}
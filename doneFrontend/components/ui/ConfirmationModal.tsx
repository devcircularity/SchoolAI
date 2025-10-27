// components/ui/ConfirmationModal.tsx - Modal using theme colors
'use client'

import { useEffect } from 'react'
import { createPortal } from 'react-dom'

interface ConfirmationModalProps {
  isOpen: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void
  onCancel: () => void
  variant?: 'danger' | 'warning' | 'success' | 'default'
}

export default function ConfirmationModal({
  isOpen,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  variant = 'default'
}: ConfirmationModalProps) {
  // Handle escape key
  useEffect(() => {
    if (!isOpen) return

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onCancel])

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

  // Use theme colors for button variants
  const getConfirmButtonStyle = () => {
    switch (variant) {
      case 'danger':
        return {
          backgroundColor: 'var(--color-error)',
          color: 'white',
          onHover: 'var(--color-error-dark)'
        }
      case 'warning':
        return {
          backgroundColor: 'var(--color-warning)',
          color: 'white',
          onHover: 'var(--color-warning-dark)'
        }
      case 'success':
        return {
          backgroundColor: 'var(--color-success)',
          color: 'white',
          onHover: 'var(--color-success-dark)'
        }
      default:
        return {
          backgroundColor: 'var(--color-brand)',
          color: 'white',
          onHover: 'var(--color-brand-dark)'
        }
    }
  }

  const buttonStyle = getConfirmButtonStyle()

  const modalContent = (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onCancel}
      />
      
      {/* Modal */}
      <div className="relative bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-md w-full p-6 border border-neutral-200 dark:border-neutral-700">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
            {title}
          </h3>
          <p className="text-neutral-600 dark:text-neutral-400">
            {message}
          </p>
        </div>
        
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg border border-neutral-300 dark:border-neutral-600 
                     bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300
                     hover:bg-neutral-50 dark:hover:bg-neutral-700 
                     transition-colors font-medium"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 rounded-lg transition-colors font-medium"
            style={{ 
              backgroundColor: buttonStyle.backgroundColor,
              color: buttonStyle.color
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = buttonStyle.onHover
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = buttonStyle.backgroundColor
            }}
          >
            {confirmText}
          </button>
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
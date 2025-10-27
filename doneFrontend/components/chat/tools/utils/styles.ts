// components/chat/tools/utils/styles.ts
import { BadgeVariant, StatusState } from '../types'

export function getVariantClasses(variant: BadgeVariant) {
  const variants = {
    primary: {
      bg: 'bg-blue-100 dark:bg-blue-900/30',
      text: 'text-blue-700 dark:text-blue-300',
      badge: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
    },
    secondary: {
      bg: 'bg-gray-100 dark:bg-gray-800',
      text: 'text-gray-700 dark:text-gray-300',
      badge: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
    },
    success: {
      bg: 'bg-green-100 dark:bg-green-900/30',
      text: 'text-green-700 dark:text-green-300',
      badge: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
    },
    warning: {
      bg: 'bg-yellow-100 dark:bg-yellow-900/30',
      text: 'text-yellow-700 dark:text-yellow-300',
      badge: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
    },
    danger: {
      bg: 'bg-red-100 dark:bg-red-900/30',
      text: 'text-red-700 dark:text-red-300',
      badge: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
    },
    info: {
      bg: 'bg-cyan-100 dark:bg-cyan-900/30',
      text: 'text-cyan-700 dark:text-cyan-300',
      badge: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-300'
    }
  }
  
  return variants[variant] || variants.primary
}

export function getStatusClasses(status: StatusState) {
  const statuses = {
    ok: {
      bg: 'bg-green-100 dark:bg-green-900/30',
      text: 'text-green-700 dark:text-green-300',
      dot: 'bg-green-500'
    },
    warning: {
      bg: 'bg-yellow-100 dark:bg-yellow-900/30', 
      text: 'text-yellow-700 dark:text-yellow-300',
      dot: 'bg-yellow-500'
    },
    error: {
      bg: 'bg-red-100 dark:bg-red-900/30',
      text: 'text-red-700 dark:text-red-300', 
      dot: 'bg-red-500'
    },
    unknown: {
      bg: 'bg-gray-100 dark:bg-gray-800',
      text: 'text-gray-700 dark:text-gray-300',
      dot: 'bg-gray-500'
    }
  }
  
  return statuses[status] || statuses.unknown
}

export function getAlignmentClass(align?: 'left' | 'center' | 'right') {
  switch (align) {
    case 'center': return 'text-center'
    case 'right': return 'text-right'
    default: return 'text-left'
  }
}
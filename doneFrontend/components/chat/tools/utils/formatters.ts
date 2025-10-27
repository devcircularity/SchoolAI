// components/chat/tools/utils/formatters.ts
import { FormatType } from '../types'

export function formatValue(value: number | string, format?: FormatType): string {
  if (typeof value === 'string') return value
  
  switch (format) {
    case 'integer':
      return Math.round(value).toLocaleString()
      
    case 'decimal':
      return value.toLocaleString('en-US', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      })
      
    case 'currency:KES':
      return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES',
        minimumFractionDigits: 0
      }).format(value)
      
    case 'percent':
      return `${(value * 100).toFixed(1)}%`
      
    case 'date':
      if (typeof value === 'string') {
        return new Date(value).toLocaleDateString('en-KE')
      }
      return new Date(value).toLocaleDateString('en-KE')
      
    default:
      return value.toLocaleString()
  }
}

export function formatDate(dateString: string, format?: 'short' | 'long'): string {
  const date = new Date(dateString)
  
  if (format === 'long') {
    return date.toLocaleDateString('en-KE', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }
  
  return date.toLocaleDateString('en-KE')
}

export function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString('en-KE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
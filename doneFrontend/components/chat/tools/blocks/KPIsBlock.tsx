// components/chat/tools/blocks/KPIsBlock.tsx - Fixed TypeScript types
'use client'
import { KPIsBlock as KPIsBlockType, Action, FormatType } from '../types'
import { formatValue } from '../utils/formatters'
import { getVariantClasses } from '../utils/styles'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

// Extended KPI item interface to include all properties used
interface ExtendedKPIItem {
  label: string
  value: string | number
  format?: FormatType
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info'
  action?: Action
  trend?: 'up' | 'down' | 'neutral'
  change?: string
  period?: string
  icon?: string
  subtitle?: string
  status?: 'good' | 'bad' | 'warning' | 'up' | 'down' | string
  progress?: number
}

// Extended KPIs block type
interface ExtendedKPIsBlockType {
  type: 'kpis'
  items: ExtendedKPIItem[]
}

interface Props {
  block: ExtendedKPIsBlockType
  onAction?: (action: Action) => void
}

export function KPIsBlock({ block, onAction }: Props) {
  const handleItemClick = (action: Action | undefined) => {
    if (action && onAction) {
      onAction(action)
    }
  }

  const renderTrendIcon = (trend?: 'up' | 'down' | 'neutral') => {
    if (!trend) return null
    
    const iconClass = "w-4 h-4"
    switch (trend) {
      case 'up':
        return <TrendingUp className={`${iconClass} text-green-500`} />
      case 'down':
        return <TrendingDown className={`${iconClass} text-red-500`} />
      case 'neutral':
        return <Minus className={`${iconClass} text-neutral-500`} />
      default:
        return null
    }
  }

  const getResponsiveGrid = (itemCount: number) => {
    // Smart responsive grid based on number of items
    if (itemCount === 1) return 'grid-cols-1'
    if (itemCount === 2) return 'grid-cols-1 sm:grid-cols-2'
    if (itemCount === 3) return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
    if (itemCount === 4) return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'
    // For 5+ items, use a flexible layout
    return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
  }

  return (
    <div className={`grid gap-3 sm:gap-4 ${getResponsiveGrid(block.items.length)}`}>
      {block.items.map((item, index) => {
        const isClickable = !!item.action
        const variantClasses = getVariantClasses(item.variant || 'primary')
        
        return (
          <div
            key={index}
            className={`
              bg-white dark:bg-neutral-900 
              border border-neutral-200 dark:border-neutral-700 
              rounded-lg sm:rounded-xl p-4 sm:p-5
              transition-all duration-200 shadow-sm hover:shadow-md
              ${isClickable 
                ? 'cursor-pointer hover:border-neutral-300 dark:hover:border-neutral-600 hover:scale-[1.02] active:scale-[0.98]' 
                : ''
              }
            `}
            onClick={() => handleItemClick(item.action)}
            role={isClickable ? 'button' : undefined}
            tabIndex={isClickable ? 0 : undefined}
            onKeyDown={(e) => {
              if (isClickable && (e.key === 'Enter' || e.key === ' ')) {
                e.preventDefault()
                handleItemClick(item.action)
              }
            }}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                {/* Label */}
                <p className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 mb-1 sm:mb-2 font-medium uppercase tracking-wide truncate">
                  {item.label}
                </p>
                
                {/* Value */}
                <div className="flex items-baseline gap-2 mb-2">
                  <p className="text-xl sm:text-2xl lg:text-3xl font-bold text-neutral-900 dark:text-neutral-100 leading-none">
                    {formatValue(item.value, item.format)}
                  </p>
                  {renderTrendIcon(item.trend)}
                </div>
                
                {/* Change indicator */}
                {item.change && (
                  <div className="flex items-center gap-1 text-xs sm:text-sm">
                    <span className={`
                      font-medium
                      ${item.change.startsWith('+') || (!item.change.startsWith('-') && parseFloat(item.change) > 0)
                        ? 'text-green-600 dark:text-green-400'
                        : item.change.startsWith('-') || parseFloat(item.change) < 0
                        ? 'text-red-600 dark:text-red-400'
                        : 'text-neutral-600 dark:text-neutral-400'
                      }
                    `}>
                      {item.change}
                    </span>
                    <span className="text-neutral-500 dark:text-neutral-400">
                      {item.period || 'vs last period'}
                    </span>
                  </div>
                )}
              </div>
              
              {/* Icon */}
              {item.icon && (
                <div className={`
                  p-2 sm:p-2.5 rounded-lg sm:rounded-xl flex-shrink-0 ml-3
                  ${variantClasses.bg}
                `}>
                  <div className={`w-4 h-4 sm:w-5 sm:h-5 ${variantClasses.text}`}>
                    {/* Icon placeholder - replace with your icon library */}
                    <svg viewBox="0 0 20 20" fill="currentColor" className="w-full h-full">
                      <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              )}
            </div>
            
            {/* Additional info */}
            {item.subtitle && (
              <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 mt-2 line-clamp-2">
                {item.subtitle}
              </p>
            )}
            
            {/* Status badge */}
            {item.status && (
              <div className="mt-2 sm:mt-3">
                <span className={`
                  inline-flex px-2 py-1 rounded-full text-xs font-medium
                  ${item.status === 'good' || item.status === 'up'
                    ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                    : item.status === 'bad' || item.status === 'down'
                    ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                    : item.status === 'warning'
                    ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                    : 'bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-300'
                  }
                `}>
                  {item.status}
                </span>
              </div>
            )}
            
            {/* Progress bar (if applicable) */}
            {item.progress !== undefined && (
              <div className="mt-3">
                <div className="flex justify-between text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                  <span>Progress</span>
                  <span>{item.progress}%</span>
                </div>
                <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-1.5 sm:h-2">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${variantClasses.bg.replace('bg-', 'bg-').replace('/30', '')}`}
                    style={{ width: `${Math.min(100, Math.max(0, item.progress))}%` }}
                  />
                </div>
              </div>
            )}
            
            {/* Click indicator */}
            {isClickable && (
              <div className="mt-2 sm:mt-3 text-xs text-neutral-400 dark:text-neutral-500 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <span>Click for details</span>
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
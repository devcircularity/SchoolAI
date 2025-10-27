// components/chat/tools/blocks/TimelineBlock.tsx
'use client'
import { TimelineBlock as TimelineBlockType } from '../types'
import { formatDateTime } from '../utils/formatters'

interface Props {
  block: TimelineBlockType
}

export function TimelineBlock({ block }: Props) {
  return (
    <div className="card p-6">
      <div className="space-y-4">
        {block.items.map((item, index) => (
          <div key={index} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                <div className="w-4 h-4 text-blue-600 dark:text-blue-400">
                  {/* Icon placeholder */}
                  <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                  </svg>
                </div>
              </div>
              {index < block.items.length - 1 && (
                <div className="w-px h-8 bg-neutral-200 dark:bg-neutral-700 mt-2" />
              )}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium text-neutral-900 dark:text-neutral-100">
                    {item.title}
                  </p>
                  {item.subtitle && (
                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                      {item.subtitle}
                    </p>
                  )}
                </div>
                <time className="text-xs text-neutral-500 dark:text-neutral-500 whitespace-nowrap ml-4">
                  {formatDateTime(item.time)}
                </time>
              </div>
              
              {item.meta && (
                <div className="mt-2 text-xs text-neutral-400">
                  {Object.entries(item.meta).map(([key, value]) => (
                    <span key={key} className="mr-3">
                      {key}: {String(value)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}


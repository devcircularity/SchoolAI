
// components/chat/tools/blocks/ErrorBlock.tsx
'use client'
import { ErrorBlock as ErrorBlockType } from '../types'

interface Props {
  block: ErrorBlockType
}

export function ErrorBlock({ block }: Props) {
  return (
    <div className="card p-6 border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10">
      <div className="flex gap-3">
        <div className="w-6 h-6 text-red-500 flex-shrink-0">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-6 h-6">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-medium text-red-900 dark:text-red-100 mb-1">
            {block.title}
          </h3>
          {block.detail && (
            <p className="text-red-700 dark:text-red-300">
              {block.detail}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}


// components/chat/tools/blocks/EmptyBlock.tsx
'use client'
import { EmptyBlock as EmptyBlockType } from '../types'

interface Props {
  block: EmptyBlockType
}

export function EmptyBlock({ block }: Props) {
  return (
    <div className="card p-8 text-center">
      <div className="w-16 h-16 mx-auto bg-neutral-100 dark:bg-neutral-800 rounded-full flex items-center justify-center mb-4">
        <svg className="w-8 h-8 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-2">
        {block.title}
      </h3>
      {block.hint && (
        <p className="text-neutral-600 dark:text-neutral-400">
          {block.hint}
        </p>
      )}
    </div>
  )
}

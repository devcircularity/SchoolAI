// components/chat/tools/blocks/StatusBlock.tsx
'use client'
import { StatusBlock as StatusBlockType } from '../types'
import { getStatusClasses } from '../utils/styles'

interface Props {
  block: StatusBlockType
}

export function StatusBlock({ block }: Props) {
  return (
    <div className="card p-6">
      <div className="space-y-4">
        {block.items.map((item, index) => {
          const statusClasses = getStatusClasses(item.state)
          
          return (
            <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${statusClasses.dot}`} />
                <div>
                  <p className="font-medium text-neutral-900 dark:text-neutral-100">
                    {item.label}
                  </p>
                  {item.detail && (
                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                      {item.detail}
                    </p>
                  )}
                </div>
              </div>
              
              <div className={`px-2 py-1 rounded text-xs font-medium ${statusClasses.bg} ${statusClasses.text}`}>
                {item.state}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

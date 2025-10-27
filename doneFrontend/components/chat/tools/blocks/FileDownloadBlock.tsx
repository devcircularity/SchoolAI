// components/chat/tools/blocks/FileDownloadBlock.tsx
'use client'
import { FileDownloadBlock as FileDownloadBlockType } from '../types'

interface Props {
  block: FileDownloadBlockType
}

export function FileDownloadBlock({ block }: Props) {
  const handleDownload = () => {
    // Create a temporary link to trigger download
    const link = document.createElement('a')
    link.href = block.endpoint
    link.download = block.fileName
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const isExpired = Boolean(block.expiresAt && new Date(block.expiresAt) < new Date())

  return (
    <div className="card p-4">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
          <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        
        <div className="flex-1">
          <p className="font-medium text-neutral-900 dark:text-neutral-100">
            {block.fileName}
          </p>
          {block.expiresAt && (
            <p className="text-sm text-neutral-500 dark:text-neutral-500">
              Expires: {new Date(block.expiresAt).toLocaleString()}
            </p>
          )}
        </div>
        
        <button 
          onClick={handleDownload}
          disabled={isExpired}
          className="btn-primary disabled:opacity-50"
        >
          {isExpired ? 'Expired' : 'Download'}
        </button>
      </div>
    </div>
  )
}